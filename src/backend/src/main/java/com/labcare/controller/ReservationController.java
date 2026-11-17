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
