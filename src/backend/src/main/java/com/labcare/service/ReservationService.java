package com.labcare.service;

import com.labcare.common.BusinessException;
import com.labcare.common.PageResult;
import com.labcare.domain.*;
import com.labcare.dto.ReservationDtos;
import com.labcare.repository.EquipmentRepository;
import com.labcare.repository.ReservationRepository;
import com.labcare.repository.UserRepository;
import com.labcare.security.CurrentUser;
import jakarta.persistence.criteria.Predicate;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Sort;
import org.springframework.data.jpa.domain.Specification;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.security.SecureRandom;
import java.time.Duration;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;

/**
 * 预约业务：时间规则校验、冲突检测、审核与状态流转。
 * <p>
 * 冲突规则（与需求文档 2.2.1 一致）：
 * 提交时校验时间合法性与"已通过"预约的冲突；待审核申请不占用时段；
 * 管理员批准时在设备行锁保护下再次校验，先批准者先占用。
 */
@Service
public class ReservationService {

    private static final DateTimeFormatter DAY = DateTimeFormatter.ofPattern("yyyyMMdd");
    private static final SecureRandom RANDOM = new SecureRandom();

    private final ReservationRepository reservationRepository;
    private final EquipmentRepository equipmentRepository;
    private final UserRepository userRepository;
    private final OperationLogService operationLogService;

    private final int slotMinutes;
    private final int minAdvanceMinutes;
    private final int maxAdvanceDays;
    private final int maxDurationHours;

    public ReservationService(ReservationRepository reservationRepository,
                              EquipmentRepository equipmentRepository,
                              UserRepository userRepository,
                              OperationLogService operationLogService,
                              @Value("${labcare.reservation.slot-minutes:30}") int slotMinutes,
                              @Value("${labcare.reservation.min-advance-minutes:30}") int minAdvanceMinutes,
                              @Value("${labcare.reservation.max-advance-days:7}") int maxAdvanceDays,
                              @Value("${labcare.reservation.max-duration-hours:4}") int maxDurationHours) {
        this.reservationRepository = reservationRepository;
        this.equipmentRepository = equipmentRepository;
        this.userRepository = userRepository;
        this.operationLogService = operationLogService;
        this.slotMinutes = slotMinutes;
        this.minAdvanceMinutes = minAdvanceMinutes;
        this.maxAdvanceDays = maxAdvanceDays;
        this.maxDurationHours = maxDurationHours;
    }

    @Transactional
    public ReservationDtos.ReservationView create(ReservationDtos.CreateRequest request, CurrentUser user) {
        Equipment equipment = equipmentRepository.findByIdForUpdate(request.equipmentId())
                .orElseThrow(() -> BusinessException.notFound("设备不存在"));
        if (equipment.getStatus() != EquipmentStatus.AVAILABLE) {
            throw BusinessException.badRequest("设备当前状态为「" + equipment.getStatus().getLabel() + "」，不可预约");
        }
        validateTimeWindow(request.startTime(), request.endTime());

        List<Reservation> conflicts = reservationRepository.findConflicts(equipment.getId(),
                ReservationStatus.APPROVED, request.startTime(), request.endTime(), null);
        if (!conflicts.isEmpty()) {
            throw BusinessException.conflict("所选时段与已有预约冲突（" + conflicts.get(0).getCode() + "），请调整时间");
        }

        Reservation reservation = new Reservation();
        reservation.setCode(nextCode());
        reservation.setEquipmentId(equipment.getId());
        reservation.setUserId(user.id());
        reservation.setStartTime(request.startTime());
        reservation.setEndTime(request.endTime());
        reservation.setPurpose(request.purpose());
        reservation.setStatus(ReservationStatus.PENDING);
        reservationRepository.save(reservation);

        operationLogService.record(user, "RESERVATION", reservation.getCode(), "CREATE",
                "提交预约：" + equipment.getCode() + " " + equipment.getName()
                        + " " + format(request.startTime()) + " ~ " + format(request.endTime()));
        return toView(reservation);
    }

    @Transactional
    public ReservationDtos.ReservationView cancel(Long id, CurrentUser user) {
        Reservation reservation = require(id);
        if (!Objects.equals(reservation.getUserId(), user.id())) {
            throw BusinessException.forbidden("只能取消本人的预约申请");
        }
        if (reservation.getStatus() != ReservationStatus.PENDING) {
            throw BusinessException.conflict("当前状态为「" + reservation.getStatus().getLabel() + "」，不可取消");
        }
        reservation.setStatus(ReservationStatus.CANCELLED);
        reservationRepository.save(reservation);
        operationLogService.record(user, "RESERVATION", reservation.getCode(), "CANCEL", "申请人取消预约");
        return toView(reservation);
    }

    /** 管理员审核：批准前在设备行锁下再次检测冲突。 */
    @Transactional
    public ReservationDtos.ReservationView review(Long id, ReservationDtos.ReviewRequest request, CurrentUser admin) {
        Reservation reservation = require(id);
        if (reservation.getStatus() != ReservationStatus.PENDING) {
            throw BusinessException.conflict("当前状态为「" + reservation.getStatus().getLabel() + "」，不可重复审核");
        }
        boolean approve = Boolean.TRUE.equals(request.approve());
        Equipment equipment = equipmentRepository.findByIdForUpdate(reservation.getEquipmentId())
                .orElseThrow(() -> BusinessException.notFound("设备不存在"));

        if (approve) {
            if (equipment.getStatus() != EquipmentStatus.AVAILABLE) {
                throw BusinessException.conflict("设备当前不可用，无法批准该预约");
            }
            List<Reservation> conflicts = reservationRepository.findConflicts(reservation.getEquipmentId(),
                    ReservationStatus.APPROVED, reservation.getStartTime(), reservation.getEndTime(), reservation.getId());
            if (!conflicts.isEmpty()) {
                throw BusinessException.conflict("该时段已被预约 " + conflicts.get(0).getCode() + " 占用，不能批准");
            }
            reservation.setStatus(ReservationStatus.APPROVED);
        } else {
            if (request.comment() == null || request.comment().isBlank()) {
                throw BusinessException.badRequest("驳回时必须填写审核意见");
            }
            reservation.setStatus(ReservationStatus.REJECTED);
        }
        reservation.setReviewerId(admin.id());
        reservation.setReviewComment(request.comment());
        reservation.setReviewedAt(LocalDateTime.now());
        reservationRepository.save(reservation);

        operationLogService.record(admin, "RESERVATION", reservation.getCode(),
                approve ? "APPROVE" : "REJECT",
                (approve ? "审核通过，" : "审核驳回，") + "意见：" + (request.comment() == null ? "（无）" : request.comment()));
        return toView(reservation);
    }

    /** 预约结束后标记完成。 */
    @Transactional
    public ReservationDtos.ReservationView complete(Long id, CurrentUser admin) {
        Reservation reservation = require(id);
        if (reservation.getStatus() != ReservationStatus.APPROVED) {
            throw BusinessException.conflict("只有「已通过」的预约才能标记完成");
        }
        if (reservation.getEndTime().isAfter(LocalDateTime.now())) {
            throw BusinessException.badRequest("预约尚未结束，不能标记完成");
        }
        reservation.setStatus(ReservationStatus.COMPLETED);
        reservationRepository.save(reservation);
        operationLogService.record(admin, "RESERVATION", reservation.getCode(), "COMPLETE", "预约已标记完成");
        return toView(reservation);
    }

    /**
     * 查询某设备在指定时间范围内已被占用的时段。
     * <p>
     * 仅返回已通过（APPROVED）的预约：待审核申请尚未生效，不作为占用展示，避免误判。
     */
    @Transactional(readOnly = true)
    public List<ReservationDtos.ReservedTimeView> reservedSlots(Long equipmentId, LocalDateTime start, LocalDateTime end) {
        if (start == null || end == null || !start.isBefore(end)) {
            throw BusinessException.badRequest("开始时间必须早于结束时间");
        }
        if (end.isAfter(start.plusDays(31))) {
            throw BusinessException.badRequest("查询范围不能超过 31 天");
        }
        equipmentRepository.findById(equipmentId)
                .orElseThrow(() -> BusinessException.notFound("设备不存在"));
        return reservationRepository.findOccupiedInRange(equipmentId, ReservationStatus.APPROVED, start, end)
                .stream()
                .map(r -> new ReservationDtos.ReservedTimeView(r.getId(), r.getStartTime(), r.getEndTime()))
                .toList();
    }

    @Transactional(readOnly = true)
    public PageResult<ReservationDtos.ReservationView> mine(CurrentUser user, ReservationStatus status,
                                                            int page, int size) {
        Specification<Reservation> spec = (root, query, cb) -> {
            List<Predicate> predicates = new ArrayList<>();
            predicates.add(cb.equal(root.get("userId"), user.id()));
            if (status != null) {
                predicates.add(cb.equal(root.get("status"), status));
            }
            return cb.and(predicates.toArray(new Predicate[0]));
        };
        Page<Reservation> result = reservationRepository.findAll(spec,
                PageRequest.of(Math.max(page - 1, 0), clamp(size), Sort.by(Sort.Direction.DESC, "id")));
        return PageResult.of(result.getContent().stream().map(this::toView).toList(),
                result.getTotalElements(), page, clamp(size));
    }

    @Transactional(readOnly = true)
    public PageResult<ReservationDtos.ReservationView> adminSearch(ReservationStatus status, String keyword,
                                                                   int page, int size) {
        Specification<Reservation> spec = (root, query, cb) -> {
            List<Predicate> predicates = new ArrayList<>();
            if (status != null) {
                predicates.add(cb.equal(root.get("status"), status));
            }
            if (keyword != null && !keyword.isBlank()) {
                String like = "%" + keyword.trim() + "%";
                predicates.add(cb.or(cb.like(root.get("code"), like), cb.like(root.get("purpose"), like)));
            }
            return cb.and(predicates.toArray(new Predicate[0]));
        };
        Page<Reservation> result = reservationRepository.findAll(spec,
                PageRequest.of(Math.max(page - 1, 0), clamp(size), Sort.by(Sort.Direction.DESC, "id")));
        return PageResult.of(result.getContent().stream().map(this::toView).toList(),
                result.getTotalElements(), page, clamp(size));
    }

    @Transactional(readOnly = true)
    public ReservationDtos.ReservationView detail(Long id, CurrentUser user) {
        Reservation reservation = require(id);
        if (!user.isAdmin() && !Objects.equals(reservation.getUserId(), user.id())) {
            throw BusinessException.forbidden("无权查看他人的预约记录");
        }
        return toView(reservation);
    }

    @Transactional(readOnly = true)
    public Reservation require(Long id) {
        return reservationRepository.findById(id)
                .orElseThrow(() -> BusinessException.notFound("预约记录不存在"));
    }

    private void validateTimeWindow(LocalDateTime start, LocalDateTime end) {
        if (!start.isBefore(end)) {
            throw BusinessException.badRequest("开始时间必须早于结束时间");
        }
        if (start.getMinute() % slotMinutes != 0 || end.getMinute() % slotMinutes != 0
                || start.getSecond() != 0 || end.getSecond() != 0) {
            throw BusinessException.badRequest("预约时间需按 " + slotMinutes + " 分钟为粒度选择");
        }
        LocalDateTime now = LocalDateTime.now();
        if (start.isBefore(now.plusMinutes(minAdvanceMinutes))) {
            throw BusinessException.badRequest("预约需至少提前 " + minAdvanceMinutes + " 分钟提交");
        }
        if (start.isAfter(now.plusDays(maxAdvanceDays))) {
            throw BusinessException.badRequest("最多只能预约 " + maxAdvanceDays + " 天内的时段");
        }
        long minutes = Duration.between(start, end).toMinutes();
        if (minutes > maxDurationHours * 60L) {
            throw BusinessException.badRequest("单次预约不能超过 " + maxDurationHours + " 小时");
        }
        if (minutes < slotMinutes) {
            throw BusinessException.badRequest("单次预约不能短于 " + slotMinutes + " 分钟");
        }
    }

    private String nextCode() {
        String prefix = "RS" + LocalDate.now().format(DAY);
        for (int i = 0; i < 20; i++) {
            String code = prefix + String.format("%04d", RANDOM.nextInt(10000));
            if (!reservationRepository.existsByCode(code)) {
                return code;
            }
        }
        throw new BusinessException(500, "生成预约编号失败，请重试");
    }

    private static String format(LocalDateTime time) {
        return time.format(DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm"));
    }

    private static int clamp(int size) {
        return Math.min(Math.max(size, 1), 100);
    }

    public ReservationDtos.ReservationView toView(Reservation r) {
        Equipment equipment = equipmentRepository.findById(r.getEquipmentId()).orElse(null);
        User applicant = userRepository.findById(r.getUserId()).orElse(null);
        User reviewer = r.getReviewerId() == null ? null : userRepository.findById(r.getReviewerId()).orElse(null);
        return new ReservationDtos.ReservationView(
                r.getId(), r.getCode(),
                r.getEquipmentId(),
                equipment == null ? "-" : equipment.getCode(),
                equipment == null ? "（设备已移除）" : equipment.getName(),
                equipment == null ? "-" : equipment.getLaboratory(),
                r.getUserId(), applicant == null ? "-" : applicant.getDisplayName(),
                r.getStartTime(), r.getEndTime(), r.getPurpose(),
                r.getStatus().name(), r.getStatus().getLabel(),
                reviewer == null ? null : reviewer.getDisplayName(),
                r.getReviewComment(), r.getReviewedAt(), r.getCreatedAt());
    }
}
