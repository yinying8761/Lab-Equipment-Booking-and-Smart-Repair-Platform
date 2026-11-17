package com.labcare.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;

import java.time.LocalDateTime;
import java.util.List;

/**
 * 报修工单 DTO。
 */
public final class RepairDtos {

    private RepairDtos() {
    }

    public record CreateRequest(
            @NotNull(message = "不能为空") Long equipmentId,
            @NotBlank(message = "不能为空") @Size(max = 1000) String description,
            @Size(max = 50) String contact) {
    }

    public record UpdateRequest(@Size(max = 1000) String resolution) {
    }

    public record CloseRequest(@NotBlank(message = "不能为空") @Size(max = 200) String reason) {
    }

    public record LogItem(String action, String summary, String operator, LocalDateTime time) {
    }

    public record RepairView(Long id, String code,
                             Long equipmentId, String equipmentCode, String equipmentName, String laboratory,
                             Long userId, String applicantName, String contact,
                             String description, String status, String statusLabel,
                             String handlerName, String resolution,
                             LocalDateTime acceptedAt, LocalDateTime completedAt,
                             String source, LocalDateTime createdAt, LocalDateTime updatedAt,
                             List<LogItem> logs) {
    }
}
