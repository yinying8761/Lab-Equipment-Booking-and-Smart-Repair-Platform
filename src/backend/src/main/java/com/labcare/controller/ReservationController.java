package com.labcare.controller;

import com.labcare.common.ApiResponse;
import com.labcare.common.PageResult;
import com.labcare.domain.ReservationStatus;
import com.labcare.dto.ReservationDtos;
import com.labcare.security.UserContext;
import com.labcare.service.ReservationService;
import jakarta.validation.Valid;
import org.springframework.format.annotation.DateTimeFormat;
import org.springframework.web.bind.annotation.*;

import java.time.LocalDateTime;
import java.util.List;

@RestController
@RequestMapping("/reservations")
public class ReservationController {

    private final ReservationService reservationService;

    public ReservationController(ReservationService reservationService) {
        this.reservationService = reservationService;
    }

    @PostMapping
    public ApiResponse<ReservationDtos.ReservationView> create(@Valid @RequestBody ReservationDtos.CreateRequest request) {
        return ApiResponse.ok(reservationService.create(request, UserContext.require()));
    }

    /**
     * 查询某台设备在指定时间区间内已被预约占用的时段（预约日历/时间轴展示）。
     * 仅返回已审核通过（APPROVED）的预约，待审核申请不占用时段。
     */
    @GetMapping("/equipment/{equipmentId}/reserved-time")
    public ApiResponse<List<ReservationDtos.ReservedTimeView>> reservedTime(
            @PathVariable Long equipmentId,
            @RequestParam @DateTimeFormat(pattern = "yyyy-MM-dd HH:mm:ss") LocalDateTime start,
            @RequestParam @DateTimeFormat(pattern = "yyyy-MM-dd HH:mm:ss") LocalDateTime end) {
        return ApiResponse.ok(reservationService.reservedSlots(equipmentId, start, end));
    }

    @GetMapping("/mine")
    public ApiResponse<PageResult<ReservationDtos.ReservationView>> mine(
            @RequestParam(required = false) ReservationStatus status,
            @RequestParam(defaultValue = "1") int page,
            @RequestParam(defaultValue = "10") int size) {
        return ApiResponse.ok(reservationService.mine(UserContext.require(), status, page, size));
    }

    @GetMapping("/{id}")
    public ApiResponse<ReservationDtos.ReservationView> detail(@PathVariable Long id) {
        return ApiResponse.ok(reservationService.detail(id, UserContext.require()));
    }

    @PostMapping("/{id}/cancel")
    public ApiResponse<ReservationDtos.ReservationView> cancel(@PathVariable Long id) {
        return ApiResponse.ok(reservationService.cancel(id, UserContext.require()));
    }
}
