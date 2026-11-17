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
@RequestMapping("/repairs")
public class RepairController {

    private final RepairService repairService;

    public RepairController(RepairService repairService) {
        this.repairService = repairService;
    }

    @PostMapping
    public ApiResponse<RepairDtos.RepairView> create(@Valid @RequestBody RepairDtos.CreateRequest request) {
        return ApiResponse.ok(repairService.create(request, UserContext.require(), "MANUAL"));
    }

    @GetMapping("/mine")
    public ApiResponse<PageResult<RepairDtos.RepairView>> mine(
            @RequestParam(required = false) RepairStatus status,
            @RequestParam(defaultValue = "1") int page,
            @RequestParam(defaultValue = "10") int size) {
        return ApiResponse.ok(repairService.mine(UserContext.require(), status, page, size));
    }

    @GetMapping("/{id}")
    public ApiResponse<RepairDtos.RepairView> detail(@PathVariable Long id) {
        return ApiResponse.ok(repairService.detail(id, UserContext.require()));
    }
}
