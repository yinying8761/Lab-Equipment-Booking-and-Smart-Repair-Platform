package com.labcare.service;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.labcare.common.BusinessException;
import com.labcare.domain.*;
import com.labcare.dto.AiDtos;
import com.labcare.dto.RepairDtos;
import com.labcare.repository.*;
import com.labcare.security.CurrentUser;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.UUID;

/**
 * AI 能力编排：
 * 1. RAG 问答：转发到 LangChain 服务，落库答案与引用；
 * 2. Agent 助手：转发工具调用，把执行轨迹写入 agent_run；
 * 3. 写操作确认：Agent 只产生"待确认动作"，用户确认后由本服务调用业务接口建单，
 *    保证 AI 无法绕过权限与业务规则直接写库。
 */
@Service
public class AiService {

    private static final int HISTORY_LIMIT = 6;

    private final ChatSessionRepository sessionRepository;
    private final ChatMessageRepository messageRepository;
    private final AgentRunRepository agentRunRepository;
    private final PendingActionRepository pendingActionRepository;
    private final RepairService repairService;
    private final AiClient aiClient;
    private final ObjectMapper mapper = new ObjectMapper();
    private final int confirmTimeoutMinutes;

    public AiService(ChatSessionRepository sessionRepository,
                     ChatMessageRepository messageRepository,
                     AgentRunRepository agentRunRepository,
                     PendingActionRepository pendingActionRepository,
                     RepairService repairService,
                     AiClient aiClient,
                     @Value("${labcare.agent.confirm-timeout-minutes:10}") int confirmTimeoutMinutes) {
        this.sessionRepository = sessionRepository;
        this.messageRepository = messageRepository;
        this.agentRunRepository = agentRunRepository;
        this.pendingActionRepository = pendingActionRepository;
        this.repairService = repairService;
        this.aiClient = aiClient;
        this.confirmTimeoutMinutes = confirmTimeoutMinutes;
    }

    // ------------------------------------------------------------------
    // RAG 知识问答
    // ------------------------------------------------------------------
    @Transactional
    public AiDtos.ChatResponse chat(Long sessionId, String question, CurrentUser user) {
        ChatSession session = resolveSession(sessionId, user, ChatMode.RAG, question);
        List<Map<String, String>> history = history(session.getId());
        saveMessage(session.getId(), "user", question, null, false);

        JsonNode response = aiClient.post("/rag/chat", Map.of(
                "question", question,
                "history", history,
                "top_k", 4,
                "user_id", user.id()));

        String answer = response.path("answer").asText("未能生成回答");
        boolean degraded = response.path("degraded").asBoolean(false);
        String notice = response.path("notice").asText("");
        JsonNode citationsNode = response.path("citations");
        List<AiDtos.Citation> citations = parseCitations(citationsNode);

        saveMessage(session.getId(), "assistant", answer, citationsNode.isMissingNode() ? null : citationsNode.toString(), degraded);
        return new AiDtos.ChatResponse(session.getId(), answer, citations, degraded, notice, List.of(), null);
    }

    // ------------------------------------------------------------------
    // Agent 工具调用
    // ------------------------------------------------------------------
    @Transactional
    public AiDtos.ChatResponse agentChat(Long sessionId, String message, CurrentUser user) {
        ChatSession session = resolveSession(sessionId, user, ChatMode.AGENT, message);
        List<Map<String, String>> history = history(session.getId());
        saveMessage(session.getId(), "user", message, null, false);

        JsonNode response = aiClient.post("/agent/chat", Map.of(
                "message", message,
                "history", history,
                "session_id", session.getId(),
                "user", Map.of("id", user.id(), "displayName", user.displayName())));

        String reply = response.path("reply").asText("智能助手暂时无法回复");
        boolean degraded = response.path("degraded").asBoolean(false);
        String notice = response.path("notice").asText("");
        List<AiDtos.TraceItem> trace = parseTrace(response.path("trace"));
        saveTrace(session.getId(), user.id(), trace);
        saveMessage(session.getId(), "assistant", reply, null, degraded);

        AiDtos.PendingConfirm confirm = null;
        JsonNode proposal = response.path("proposal");
        if (proposal.isObject() && "CREATE_REPAIR".equals(proposal.path("actionType").asText())) {
            confirm = createPendingAction(session.getId(), user, proposal);
        }
        return new AiDtos.ChatResponse(session.getId(), reply, List.of(), degraded, notice, trace, confirm);
    }

    /**
     * 用户确认/取消 Agent 拟创建的工单。重复确认不会重复建单。
     */
    @Transactional
    public AiDtos.ConfirmResponse confirm(String token, boolean approved, CurrentUser user) {
        PendingAction action = pendingActionRepository.findByToken(token)
                .orElseThrow(() -> BusinessException.notFound("确认信息不存在或已失效"));
        if (!action.getUserId().equals(user.id())) {
            throw BusinessException.forbidden("无权操作他人的确认请求");
        }
        if ("CONFIRMED".equals(action.getStatus())) {
            return new AiDtos.ConfirmResponse("CONFIRMED", action.getResultRef(), null,
                    "该工单已创建，请勿重复提交");
        }
        if (!"PENDING".equals(action.getStatus())) {
            throw BusinessException.conflict("该确认已失效，请重新发起");
        }
        if (action.getExpiresAt().isBefore(LocalDateTime.now())) {
            action.setStatus("EXPIRED");
            pendingActionRepository.save(action);
            throw BusinessException.conflict("确认已超时，请重新发起报修");
        }
        if (!approved) {
            action.setStatus("CANCELLED");
            pendingActionRepository.save(action);
            return new AiDtos.ConfirmResponse("CANCELLED", null, null, "已取消，未创建任何工单");
        }

        RepairDtos.RepairView view;
        try {
            JsonNode payload = mapper.readTree(action.getPayload());
            RepairDtos.CreateRequest request = new RepairDtos.CreateRequest(
                    payload.path("equipmentId").asLong(),
                    payload.path("description").asText(),
                    payload.path("contact").asText(null));
            view = repairService.create(request, user, "AGENT");
        } catch (BusinessException e) {
            throw e;
        } catch (Exception e) {
            throw new BusinessException(500, "创建工单失败：" + e.getMessage());
        }

        action.setStatus("CONFIRMED");
        action.setResultRef(view.code());
        pendingActionRepository.save(action);
        return new AiDtos.ConfirmResponse("CONFIRMED", view.code(), String.valueOf(view.id()),
                "已创建报修工单 " + view.code());
    }

    // ------------------------------------------------------------------
    // 会话查询
    // ------------------------------------------------------------------
    @Transactional(readOnly = true)
    public List<AiDtos.SessionView> sessions(ChatMode mode, CurrentUser user) {
        return sessionRepository.findByUserIdAndModeOrderByIdDesc(user.id(), mode).stream()
                .map(s -> new AiDtos.SessionView(s.getId(), s.getTitle(), s.getMode().name(), s.getUpdatedAt()))
                .toList();
    }

    @Transactional(readOnly = true)
    public AiDtos.SessionDetail sessionDetail(Long id, CurrentUser user) {
        ChatSession session = sessionRepository.findByIdAndUserId(id, user.id())
                .orElseThrow(() -> BusinessException.notFound("会话不存在"));
        List<AiDtos.MessageView> messages = messageRepository.findBySessionIdOrderByIdAsc(id).stream()
                .map(m -> new AiDtos.MessageView(m.getId(), m.getRole(), m.getContent(), m.getCitations(),
                        m.getDegraded() != null && m.getDegraded() == 1, m.getCreatedAt()))
                .toList();
        return new AiDtos.SessionDetail(session.getId(), session.getTitle(), session.getMode().name(), messages);
    }

    @Transactional(readOnly = true)
    public List<AiDtos.TraceItem> trace(Long sessionId, CurrentUser user) {
        sessionRepository.findByIdAndUserId(sessionId, user.id())
                .orElseThrow(() -> BusinessException.notFound("会话不存在"));
        return agentRunRepository.findBySessionIdOrderByIdAsc(sessionId).stream()
                .map(r -> new AiDtos.TraceItem(r.getStepNo(), r.getToolName(), r.getInputSummary(),
                        r.getOutputSummary(), r.getSuccess() != null && r.getSuccess() == 1))
                .toList();
    }

    public boolean aiHealthy() {
        return aiClient.healthy();
    }

    // ------------------------------------------------------------------
    // 内部工具
    // ------------------------------------------------------------------
    private ChatSession resolveSession(Long sessionId, CurrentUser user, ChatMode mode, String firstQuestion) {
        if (sessionId != null) {
            return sessionRepository.findByIdAndUserId(sessionId, user.id())
                    .orElseThrow(() -> BusinessException.notFound("会话不存在或不属于当前用户"));
        }
        ChatSession session = new ChatSession();
        session.setUserId(user.id());
        session.setMode(mode);
        String title = firstQuestion.length() > 20 ? firstQuestion.substring(0, 20) : firstQuestion;
        session.setTitle(title.isBlank() ? "新会话" : title);
        return sessionRepository.save(session);
    }

    private List<Map<String, String>> history(Long sessionId) {
        List<ChatMessage> messages = messageRepository.findBySessionIdOrderByIdAsc(sessionId);
        int from = Math.max(0, messages.size() - HISTORY_LIMIT);
        List<Map<String, String>> history = new ArrayList<>();
        for (ChatMessage message : messages.subList(from, messages.size())) {
            history.add(Map.of("role", message.getRole(), "content", message.getContent()));
        }
        return history;
    }

    private void saveMessage(Long sessionId, String role, String content, String citations, boolean degraded) {
        ChatMessage message = new ChatMessage();
        message.setSessionId(sessionId);
        message.setRole(role);
        message.setContent(content);
        message.setCitations(citations);
        message.setDegraded(degraded ? 1 : 0);
        messageRepository.save(message);
    }

    private void saveTrace(Long sessionId, Long userId, List<AiDtos.TraceItem> trace) {
        for (AiDtos.TraceItem item : trace) {
            AgentRun run = new AgentRun();
            run.setSessionId(sessionId);
            run.setUserId(userId);
            run.setStepNo(item.step() == null ? 1 : item.step());
            run.setToolName(item.tool());
            run.setInputSummary(abbreviate(item.input()));
            run.setOutputSummary(abbreviate(item.output()));
            run.setSuccess(Boolean.TRUE.equals(item.success()) ? 1 : 0);
            agentRunRepository.save(run);
        }
    }

    private AiDtos.PendingConfirm createPendingAction(Long sessionId, CurrentUser user, JsonNode proposal) {
        String token = UUID.randomUUID().toString().replace("-", "");
        PendingAction action = new PendingAction();
        action.setToken(token);
        action.setUserId(user.id());
        action.setSessionId(sessionId);
        action.setActionType("CREATE_REPAIR");
        action.setPayload(proposal.toString());
        action.setPreview(proposal.path("preview").asText("请确认是否创建报修工单"));
        action.setStatus("PENDING");
        action.setExpiresAt(LocalDateTime.now().plusMinutes(confirmTimeoutMinutes));
        pendingActionRepository.save(action);

        return new AiDtos.PendingConfirm(token, action.getPreview(), "CREATE_REPAIR",
                proposal.path("equipmentId").asLong(),
                proposal.path("equipmentCode").asText(""),
                proposal.path("equipmentName").asText(""),
                proposal.path("description").asText(""),
                proposal.path("contact").asText(""),
                action.getExpiresAt());
    }

    private List<AiDtos.Citation> parseCitations(JsonNode node) {
        List<AiDtos.Citation> citations = new ArrayList<>();
        if (node == null || !node.isArray()) {
            return citations;
        }
        for (JsonNode item : node) {
            citations.add(new AiDtos.Citation(
                    item.path("documentId").asLong(),
                    item.path("title").asText(""),
                    item.path("sourceName").asText(""),
                    item.path("chunkIndex").asInt(0),
                    item.path("snippet").asText(""),
                    item.path("score").asDouble(0)));
        }
        return citations;
    }

    private List<AiDtos.TraceItem> parseTrace(JsonNode node) {
        List<AiDtos.TraceItem> trace = new ArrayList<>();
        if (node == null || !node.isArray()) {
            return trace;
        }
        for (JsonNode item : node) {
            trace.add(new AiDtos.TraceItem(
                    item.path("step").asInt(1),
                    item.path("tool").asText(""),
                    item.path("input").asText(""),
                    item.path("output").asText(""),
                    item.path("success").asBoolean(true)));
        }
        return trace;
    }

    private static String abbreviate(String text) {
        if (text == null) {
            return null;
        }
        return text.length() <= 500 ? text : text.substring(0, 500);
    }
}
