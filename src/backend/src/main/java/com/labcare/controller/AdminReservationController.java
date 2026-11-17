package com.labcare.controller;

import com.labcare.common.ApiResponse;
import com.labcare.common.PageResult;
import com.labcare.domain.ReservationStatus;
import com.labcare.dto.ReservationDtos;
import com.labcare.security.UserContext;
import com.labcare.service.ReservationService;
import jakarta.validation.Valid;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/admin/reservations")
public class AdminReservationController {

    private final ReservationService reservationService;

    public AdminReservationController(ReservationService reservationService) {
        this.reservationService = reservationService;
    }

    @GetMapping
    public ApiResponse<PageResult<ReservationDtos.ReservationView>> list(
            @RequestParam(required = false) ReservationStatus status,
            @RequestParam(required = false) String keyword,
            @RequestParam(defaultValue = "1") int page,
            @RequestParam(defaultValue = "10") int size) {
        return ApiResponse.ok(reservationService.adminSearch(status, keyword, page, size));
    }

    @PostMapping("/{id}/review")
    public ApiResponse<ReservationDtos.ReservationView> review(@PathVariable Long id,
                                                               @Valid @RequestBody ReservationDtos.ReviewRequest request) {
        return ApiResponse.ok(reservationService.review(id, request, UserContext.require()));
    }

    @PostMapping("/{id}/complete")
    public ApiResponse<ReservationDtos.ReservationView> complete(@PathVariable Long id) {
        return ApiResponse.ok(reservationService.complete(id, UserContext.require()));
    }
}
