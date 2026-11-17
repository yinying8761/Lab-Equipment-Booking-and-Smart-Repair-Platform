package com.labcare.controller;

import com.labcare.common.ApiResponse;
import com.labcare.dto.EquipmentDtos;
import com.labcare.security.UserContext;
import com.labcare.service.EquipmentService;
import jakarta.validation.Valid;
import org.springframework.web.bind.annotation.*;

/**
 * 设备维护（仅管理员）。
 */
@RestController
@RequestMapping("/admin/equipments")
public class AdminEquipmentController {

    private final EquipmentService equipmentService;

    public AdminEquipmentController(EquipmentService equipmentService) {
        this.equipmentService = equipmentService;
    }

    @PostMapping
    public ApiResponse<EquipmentDtos.EquipmentView> create(@Valid @RequestBody EquipmentDtos.EquipmentRequest request) {
        return ApiResponse.ok(equipmentService.create(request, UserContext.require()));
    }

    @PutMapping("/{id}")
    public ApiResponse<EquipmentDtos.EquipmentView> update(@PathVariable Long id,
                                                           @Valid @RequestBody EquipmentDtos.EquipmentRequest request) {
        return ApiResponse.ok(equipmentService.update(id, request, UserContext.require()));
    }

    @PatchMapping("/{id}/status")
    public ApiResponse<EquipmentDtos.EquipmentView> changeStatus(@PathVariable Long id,
                                                                 @Valid @RequestBody EquipmentDtos.StatusRequest request) {
        return ApiResponse.ok(equipmentService.changeStatus(id, request.status(), UserContext.require()));
    }
}
