package com.labcare.controller;

import com.labcare.common.ApiResponse;
import com.labcare.common.BusinessException;
import com.labcare.repository.EquipmentRepository;
import com.labcare.repository.RepairTicketRepository;
import com.labcare.repository.ReservationRepository;
import com.labcare.domain.RepairStatus;
import com.labcare.domain.ReservationStatus;
import com.labcare.security.CurrentUser;
import com.labcare.security.UserContext;
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

    /**
     * 管理员全局大盘：设备总数与全部预约/工单计数。
     */
    @GetMapping("/stats/overview")
    public ApiResponse<Map<String, Object>> overview() {
        CurrentUser user = UserContext.require();
        if (!user.isAdmin()) {
            throw BusinessException.forbidden("无权访问全局统计");
        }
        Map<String, Object> data = new LinkedHashMap<>();
        data.put("equipmentTotal", equipmentRepository.count());
        data.put("reservationPending", reservationRepository.countByStatus(ReservationStatus.PENDING));
        data.put("reservationApproved", reservationRepository.countByStatus(ReservationStatus.APPROVED));
        data.put("repairPending", repairRepository.countByStatus(RepairStatus.PENDING));
        data.put("repairProcessing", repairRepository.countByStatus(RepairStatus.PROCESSING));
        return ApiResponse.ok(data);
    }

    /**
     * 普通用户个人工作台：只统计当前登录用户自己的预约与工单。
     */
    @GetMapping("/stats/my-overview")
    public ApiResponse<Map<String, Object>> myOverview() {
        CurrentUser user = UserContext.require();
        Map<String, Object> data = new LinkedHashMap<>();
        data.put("myReservationPending",
                reservationRepository.countByUserIdAndStatus(user.id(), ReservationStatus.PENDING));
        data.put("myReservationApproved",
                reservationRepository.countByUserIdAndStatus(user.id(), ReservationStatus.APPROVED));
        data.put("myReservationRejected",
                reservationRepository.countByUserIdAndStatus(user.id(), ReservationStatus.REJECTED));
        data.put("myRepairPending",
                repairRepository.countByUserIdAndStatus(user.id(), RepairStatus.PENDING));
        data.put("myRepairProcessing",
                repairRepository.countByUserIdAndStatus(user.id(), RepairStatus.PROCESSING));
        return ApiResponse.ok(data);
    }
}
