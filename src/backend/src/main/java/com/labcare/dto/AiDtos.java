package com.labcare.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;

import java.time.LocalDateTime;
import java.util.List;

/**
 * AI 问答与智能助手 DTO。
 */
public final class AiDtos {

    private AiDtos() {
    }

    public record ChatRequest(Long sessionId, @NotBlank(message = "不能为空") String question) {
    }

    /** 智能助手使用 message 字段，与知识问答的 question 区分。 */
    public record AgentChatRequest(Long sessionId, @NotBlank(message = "不能为空") String message) {
    }

    public record Citation(Long documentId, String title, String sourceName, Integer chunkIndex,
                           String snippet, Double score) {
    }

    public record TraceItem(Integer step, String tool, String input, String output, Boolean success) {
    }

    /** Agent 提议的写操作，必须经用户确认后才会落库。 */
    public record PendingConfirm(String token, String preview, String actionType,
                                 Long equipmentId, String equipmentCode, String equipmentName,
                                 String description, String contact, LocalDateTime expiresAt) {
    }

    public record ChatResponse(Long sessionId, String answer, List<Citation> citations,
                               boolean degraded, String notice,
                               List<TraceItem> trace, PendingConfirm confirm) {
    }

    public record ConfirmRequest(@NotBlank(message = "不能为空") String token,
                                 @NotNull(message = "不能为空") Boolean approved) {
    }

    public record ConfirmResponse(String status, String repairCode, String repairId, String message) {
    }

    public record SessionView(Long id, String title, String mode, LocalDateTime updatedAt) {
    }

    public record MessageView(Long id, String role, String content, String citations,
                              boolean degraded, LocalDateTime createdAt) {
    }

    public record SessionDetail(Long id, String title, String mode, List<MessageView> messages) {
    }
}
