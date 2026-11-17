package com.labcare.dto;

import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;

import java.time.LocalDateTime;

/**
 * 预约 DTO。
 */
public final class ReservationDtos {

    private ReservationDtos() {
    }

    public record CreateRequest(
            @NotNull(message = "不能为空") Long equipmentId,
            @NotNull(message = "不能为空") LocalDateTime startTime,
            @NotNull(message = "不能为空") LocalDateTime endTime,
            @Size(max = 200) String purpose) {
    }

    public record ReviewRequest(
            @NotNull(message = "不能为空") Boolean approve,
            @Size(max = 200) String comment) {
    }

    public record ReservationView(Long id, String code,
                                  Long equipmentId, String equipmentCode, String equipmentName, String laboratory,
                                  Long userId, String applicantName,
                                  LocalDateTime startTime, LocalDateTime endTime, String purpose,
                                  String status, String statusLabel,
                                  String reviewerName, String reviewComment, LocalDateTime reviewedAt,
                                  LocalDateTime createdAt) {
    }
}
