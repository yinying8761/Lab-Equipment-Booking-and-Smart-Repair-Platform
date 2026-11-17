package com.labcare.controller;

import com.labcare.common.ApiResponse;
import com.labcare.domain.ChatMode;
import com.labcare.dto.AiDtos;
import com.labcare.security.UserContext;
import com.labcare.service.AiService;
import jakarta.validation.Valid;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

/**
 * AI 能力入口：知识问答（RAG）、智能助手（Agent）与写操作确认。
 */
@RestController
@RequestMapping("/ai")
public class AiController {

    private final AiService aiService;

    public AiController(AiService aiService) {
        this.aiService = aiService;
    }

    @PostMapping("/chat")
    public ApiResponse<AiDtos.ChatResponse> chat(@Valid @RequestBody AiDtos.ChatRequest request) {
        return ApiResponse.ok(aiService.chat(request.sessionId(), request.question(), UserContext.require()));
    }

    @PostMapping("/agent/chat")
    public ApiResponse<AiDtos.ChatResponse> agentChat(@Valid @RequestBody AiDtos.AgentChatRequest request) {
        return ApiResponse.ok(aiService.agentChat(request.sessionId(), request.message(), UserContext.require()));
    }

    @PostMapping("/agent/confirm")
    public ApiResponse<AiDtos.ConfirmResponse> confirm(@Valid @RequestBody AiDtos.ConfirmRequest request) {
        return ApiResponse.ok(aiService.confirm(request.token(), Boolean.TRUE.equals(request.approved()),
                UserContext.require()));
    }

    @GetMapping("/sessions")
    public ApiResponse<List<AiDtos.SessionView>> sessions(@RequestParam(defaultValue = "RAG") ChatMode mode) {
        return ApiResponse.ok(aiService.sessions(mode, UserContext.require()));
    }

    @GetMapping("/sessions/{id}")
    public ApiResponse<AiDtos.SessionDetail> sessionDetail(@PathVariable Long id) {
        return ApiResponse.ok(aiService.sessionDetail(id, UserContext.require()));
    }

    @GetMapping("/sessions/{id}/trace")
    public ApiResponse<List<AiDtos.TraceItem>> trace(@PathVariable Long id) {
        return ApiResponse.ok(aiService.trace(id, UserContext.require()));
    }

    @GetMapping("/health")
    public ApiResponse<Map<String, Object>> health() {
        return ApiResponse.ok(Map.of("available", aiService.aiHealthy()));
    }
}
