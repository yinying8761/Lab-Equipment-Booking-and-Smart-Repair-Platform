package com.labcare.controller;

import com.labcare.common.ApiResponse;
import com.labcare.repository.EquipmentRepository;
import com.labcare.repository.RepairTicketRepository;
import com.labcare.repository.ReservationRepository;
import com.labcare.domain.RepairStatus;
import com.labcare.domain.ReservationStatus;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.LinkedHashMap;
import java.util.Map;

/**
 * 首页统计与健康检查。
 */
@RestController
public class StatsController {

    private final EquipmentRepository equipmentRepository;
    private final ReservationRepository reservationRepository;
    private final RepairTicketRepository repairRepository;

    public StatsController(EquipmentRepository equipmentRepository,
                           ReservationRepository reservationRepository,
                           RepairTicketRepository repairRepository) {
        this.equipmentRepository = equipmentRepository;
        this.reservationRepository = reservationRepository;
        this.repairRepository = repairRepository;
    }

    @GetMapping("/health")
    public ApiResponse<Map<String, Object>> health() {
        return ApiResponse.ok(Map.of("status", "ok", "service", "labcare-backend"));
    }

    @GetMapping("/stats/overview")
    public ApiResponse<Map<String, Object>> overview() {
        Map<String, Object> data = new LinkedHashMap<>();
        data.put("equipmentTotal", equipmentRepository.count());
        data.put("reservationPending", reservationRepository.countByStatus(ReservationStatus.PENDING));
        data.put("reservationApproved", reservationRepository.countByStatus(ReservationStatus.APPROVED));
        data.put("repairPending", repairRepository.countByStatus(RepairStatus.PENDING));
        data.put("repairProcessing", repairRepository.countByStatus(RepairStatus.PROCESSING));
        return ApiResponse.ok(data);
    }
}
