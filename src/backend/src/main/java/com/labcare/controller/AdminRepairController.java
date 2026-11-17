package com.labcare.controller;

import com.labcare.common.ApiResponse;
import com.labcare.common.PageResult;
import com.labcare.domain.RepairStatus;
import com.labcare.dto.RepairDtos;
import com.labcare.security.UserContext;
import com.labcare.service.RepairService;
import jakarta.validation.Valid;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/admin/repairs")
public class AdminRepairController {

    private final RepairService repairService;

    public AdminRepairController(RepairService repairService) {
        this.repairService = repairService;
    }

    @GetMapping
    public ApiResponse<PageResult<RepairDtos.RepairView>> list(
            @RequestParam(required = false) RepairStatus status,
            @RequestParam(required = false) String keyword,
            @RequestParam(defaultValue = "1") int page,
            @RequestParam(defaultValue = "10") int size) {
        return ApiResponse.ok(repairService.adminSearch(status, keyword, page, size));
    }

    @PostMapping("/{id}/accept")
    public ApiResponse<RepairDtos.RepairView> accept(@PathVariable Long id) {
        return ApiResponse.ok(repairService.accept(id, UserContext.require()));
    }

    @PostMapping("/{id}/progress")
    public ApiResponse<RepairDtos.RepairView> progress(@PathVariable Long id,
                                                       @Valid @RequestBody RepairDtos.UpdateRequest request) {
        return ApiResponse.ok(repairService.updateProgress(id, request, UserContext.require()));
    }

    @PostMapping("/{id}/complete")
    public ApiResponse<RepairDtos.RepairView> complete(@PathVariable Long id,
                                                       @Valid @RequestBody RepairDtos.UpdateRequest request) {
        return ApiResponse.ok(repairService.complete(id, request, UserContext.require()));
    }

    @PostMapping("/{id}/close")
    public ApiResponse<RepairDtos.RepairView> close(@PathVariable Long id,
                                                    @Valid @RequestBody RepairDtos.CloseRequest request) {
        return ApiResponse.ok(repairService.close(id, request, UserContext.require()));
    }
}
