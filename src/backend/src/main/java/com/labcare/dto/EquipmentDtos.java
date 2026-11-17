package com.labcare.dto;

import com.labcare.domain.EquipmentStatus;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;

import java.time.LocalDateTime;

/**
 * 设备台账 DTO。
 */
public final class EquipmentDtos {

    private EquipmentDtos() {
    }

    public record EquipmentView(Long id, String code, String name, String category, String laboratory,
                                String location, String status, String statusLabel,
                                String description, String usageNote, LocalDateTime updatedAt) {
    }

    public record EquipmentRequest(
            @NotBlank(message = "不能为空") @Size(max = 40) String code,
            @NotBlank(message = "不能为空") @Size(max = 100) String name,
            @NotBlank(message = "不能为空") @Size(max = 50) String category,
            @NotBlank(message = "不能为空") @Size(max = 100) String laboratory,
            @Size(max = 100) String location,
            @NotNull(message = "不能为空") EquipmentStatus status,
            @Size(max = 500) String description,
            @Size(max = 500) String usageNote) {
    }

    public record StatusRequest(@NotNull(message = "不能为空") EquipmentStatus status) {
    }

    /** 供下拉选择与 Agent 工具使用的精简结构。 */
    public record EquipmentOption(Long id, String code, String name, String laboratory,
                                  String status, String statusLabel) {
    }
}
