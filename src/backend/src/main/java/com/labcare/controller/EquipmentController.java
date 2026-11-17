package com.labcare.controller;

import com.labcare.common.ApiResponse;
import com.labcare.common.PageResult;
import com.labcare.domain.EquipmentStatus;
import com.labcare.dto.EquipmentDtos;
import com.labcare.service.EquipmentService;
import org.springframework.web.bind.annotation.*;

import java.util.List;

/**
 * 设备查询（普通用户与管理员共用）。
 */
@RestController
public class EquipmentController {

    private final EquipmentService equipmentService;

    public EquipmentController(EquipmentService equipmentService) {
        this.equipmentService = equipmentService;
    }

    @GetMapping("/equipments")
    public ApiResponse<PageResult<EquipmentDtos.EquipmentView>> list(
            @RequestParam(required = false) String keyword,
            @RequestParam(required = false) String category,
            @RequestParam(required = false) String laboratory,
            @RequestParam(required = false) EquipmentStatus status,
            @RequestParam(defaultValue = "1") int page,
            @RequestParam(defaultValue = "10") int size) {
        return ApiResponse.ok(equipmentService.search(keyword, category, laboratory, status, page, size));
    }

    @GetMapping("/equipments/{id}")
    public ApiResponse<EquipmentDtos.EquipmentView> detail(@PathVariable Long id) {
        return ApiResponse.ok(equipmentService.detail(id));
    }

    @GetMapping("/equipments/options")
    public ApiResponse<List<EquipmentDtos.EquipmentOption>> options(
            @RequestParam(required = false) String keyword) {
        return ApiResponse.ok(equipmentService.options(keyword));
    }
}
