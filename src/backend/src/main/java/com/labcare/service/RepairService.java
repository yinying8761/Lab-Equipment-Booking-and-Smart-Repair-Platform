package com.labcare.service;

import com.labcare.common.BusinessException;
import com.labcare.common.PageResult;
import com.labcare.domain.*;
import com.labcare.dto.RepairDtos;
import com.labcare.repository.EquipmentRepository;
import com.labcare.repository.RepairTicketRepository;
import com.labcare.repository.UserRepository;
import com.labcare.security.CurrentUser;
import jakarta.persistence.criteria.Predicate;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Sort;
import org.springframework.data.jpa.domain.Specification;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.security.SecureRandom;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;

/**
 * 报修工单：提交、受理、处理、完成、关闭，以及用户侧进度查询。
 * 状态流转严格校验，非法跳转返回 409。
 */
@Service
public class RepairService {

    private static final DateTimeFormatter DAY = DateTimeFormatter.ofPattern("yyyyMMdd");
    private static final SecureRandom RANDOM = new SecureRandom();

    private final RepairTicketRepository repository;
    private final EquipmentRepository equipmentRepository;
    private final UserRepository userRepository;
    private final OperationLogService operationLogService;

    public RepairService(RepairTicketRepository repository, EquipmentRepository equipmentRepository,
                         UserRepository userRepository, OperationLogService operationLogService) {
        this.repository = repository;
        this.equipmentRepository = equipmentRepository;
        this.userRepository = userRepository;
        this.operationLogService = operationLogService;
    }

    @Transactional
    public RepairDtos.RepairView create(RepairDtos.CreateRequest request, CurrentUser user, String source) {
        Equipment equipment = equipmentRepository.findById(request.equipmentId())
                .orElseThrow(() -> BusinessException.notFound("设备不存在"));
        if (equipment.getStatus() == EquipmentStatus.DISABLED) {
            throw BusinessException.badRequest("设备已停用，暂不受理新工单");
        }
        RepairTicket ticket = new RepairTicket();
        ticket.setCode(nextCode());
        ticket.setEquipmentId(equipment.getId());
        ticket.setUserId(user.id());
        ticket.setContact(request.contact());
        ticket.setDescription(request.description().trim());
        ticket.setStatus(RepairStatus.PENDING);
        ticket.setSource(source == null ? "MANUAL" : source);
        repository.save(ticket);

        operationLogService.record(user, "REPAIR", ticket.getCode(), "CREATE",
                ("AGENT".equals(ticket.getSource()) ? "智能助手创建工单：" : "提交报修：")
                        + equipment.getCode() + " " + equipment.getName());
        return toView(ticket);
    }

    @Transactional
    public RepairDtos.RepairView accept(Long id, CurrentUser admin) {
        RepairTicket ticket = require(id);
        if (ticket.getStatus() != RepairStatus.PENDING) {
            throw BusinessException.conflict("只有「待受理」工单可以受理，当前为「" + ticket.getStatus().getLabel() + "」");
        }
        ticket.setStatus(RepairStatus.PROCESSING);
        ticket.setHandlerId(admin.id());
        ticket.setAcceptedAt(LocalDateTime.now());
        repository.save(ticket);
        operationLogService.record(admin, "REPAIR", ticket.getCode(), "ACCEPT", "受理工单，状态更新为处理中");
        return toView(ticket);
    }

    @Transactional
    public RepairDtos.RepairView updateProgress(Long id, RepairDtos.UpdateRequest request, CurrentUser admin) {
        RepairTicket ticket = require(id);
        if (ticket.getStatus() != RepairStatus.PROCESSING) {
            throw BusinessException.conflict("只有「处理中」工单可以更新处理记录，当前为「" + ticket.getStatus().getLabel() + "」");
        }
        if (request.resolution() == null || request.resolution().isBlank()) {
            throw BusinessException.badRequest("处理记录不能为空");
        }
        ticket.setResolution(request.resolution().trim());
        repository.save(ticket);
        operationLogService.record(admin, "REPAIR", ticket.getCode(), "PROGRESS",
                "更新处理记录：" + abbreviate(request.resolution()));
        return toView(ticket);
    }

    @Transactional
    public RepairDtos.RepairView complete(Long id, RepairDtos.UpdateRequest request, CurrentUser admin) {
        RepairTicket ticket = require(id);
        if (ticket.getStatus() != RepairStatus.PROCESSING && ticket.getStatus() != RepairStatus.PENDING) {
            throw BusinessException.conflict("当前状态为「" + ticket.getStatus().getLabel() + "」，不能标记完成");
        }
        if (request.resolution() == null || request.resolution().isBlank()) {
            throw BusinessException.badRequest("完成工单必须填写处理结果");
        }
        if (ticket.getStatus() == RepairStatus.PENDING) {
            ticket.setHandlerId(admin.id());
            ticket.setAcceptedAt(LocalDateTime.now());
        }
        ticket.setResolution(request.resolution().trim());
        ticket.setStatus(RepairStatus.COMPLETED);
        ticket.setCompletedAt(LocalDateTime.now());
        repository.save(ticket);
        operationLogService.record(admin, "REPAIR", ticket.getCode(), "COMPLETE",
                "工单完成，处理结果：" + abbreviate(request.resolution()));
        return toView(ticket);
    }

    @Transactional
    public RepairDtos.RepairView close(Long id, RepairDtos.CloseRequest request, CurrentUser admin) {
        RepairTicket ticket = require(id);
        if (ticket.getStatus().isFinal()) {
            throw BusinessException.conflict("工单已「" + ticket.getStatus().getLabel() + "」，不能再关闭");
        }
        ticket.setStatus(RepairStatus.CLOSED);
        ticket.setResolution("关闭原因：" + request.reason().trim());
        ticket.setCompletedAt(LocalDateTime.now());
        repository.save(ticket);
        operationLogService.record(admin, "REPAIR", ticket.getCode(), "CLOSE",
                "关闭工单，原因：" + request.reason().trim());
        return toView(ticket);
    }

    @Transactional(readOnly = true)
    public PageResult<RepairDtos.RepairView> mine(CurrentUser user, RepairStatus status, int page, int size) {
        Specification<RepairTicket> spec = (root, query, cb) -> {
            List<Predicate> predicates = new ArrayList<>();
            predicates.add(cb.equal(root.get("userId"), user.id()));
            if (status != null) {
                predicates.add(cb.equal(root.get("status"), status));
            }
            return cb.and(predicates.toArray(new Predicate[0]));
        };
        Page<RepairTicket> result = repository.findAll(spec,
                PageRequest.of(Math.max(page - 1, 0), clamp(size), Sort.by(Sort.Direction.DESC, "id")));
        return PageResult.of(result.getContent().stream().map(this::toView).toList(),
                result.getTotalElements(), page, clamp(size));
    }

    @Transactional(readOnly = true)
    public PageResult<RepairDtos.RepairView> adminSearch(RepairStatus status, String keyword, int page, int size) {
        Specification<RepairTicket> spec = (root, query, cb) -> {
            List<Predicate> predicates = new ArrayList<>();
            if (status != null) {
                predicates.add(cb.equal(root.get("status"), status));
            }
            if (keyword != null && !keyword.isBlank()) {
                String like = "%" + keyword.trim() + "%";
                predicates.add(cb.or(cb.like(root.get("code"), like), cb.like(root.get("description"), like)));
            }
            return cb.and(predicates.toArray(new Predicate[0]));
        };
        Page<RepairTicket> result = repository.findAll(spec,
                PageRequest.of(Math.max(page - 1, 0), clamp(size), Sort.by(Sort.Direction.DESC, "id")));
        return PageResult.of(result.getContent().stream().map(this::toView).toList(),
                result.getTotalElements(), page, clamp(size));
    }

    @Transactional(readOnly = true)
    public RepairDtos.RepairView detail(Long id, CurrentUser user) {
        RepairTicket ticket = require(id);
        if (!user.isAdmin() && !Objects.equals(ticket.getUserId(), user.id())) {
            throw BusinessException.forbidden("无权查看他人的报修工单");
        }
        return toView(ticket);
    }

    @Transactional(readOnly = true)
    public RepairTicket require(Long id) {
        return repository.findById(id).orElseThrow(() -> BusinessException.notFound("报修工单不存在"));
    }

    private RepairDtos.RepairView toView(RepairTicket t) {
        Equipment equipment = equipmentRepository.findById(t.getEquipmentId()).orElse(null);
        User applicant = userRepository.findById(t.getUserId()).orElse(null);
        User handler = t.getHandlerId() == null ? null : userRepository.findById(t.getHandlerId()).orElse(null);
        List<RepairDtos.LogItem> logs = operationLogService.findByTarget("REPAIR", t.getCode()).stream()
                .map(l -> new RepairDtos.LogItem(l.getAction(), l.getSummary(), l.getOperatorName(), l.getCreatedAt()))
                .toList();
        return new RepairDtos.RepairView(
                t.getId(), t.getCode(),
                t.getEquipmentId(),
                equipment == null ? "-" : equipment.getCode(),
                equipment == null ? "（设备已移除）" : equipment.getName(),
                equipment == null ? "-" : equipment.getLaboratory(),
                t.getUserId(), applicant == null ? "-" : applicant.getDisplayName(), t.getContact(),
                t.getDescription(), t.getStatus().name(), t.getStatus().getLabel(),
                handler == null ? null : handler.getDisplayName(), t.getResolution(),
                t.getAcceptedAt(), t.getCompletedAt(), t.getSource(),
                t.getCreatedAt(), t.getUpdatedAt(), logs);
    }

    private String nextCode() {
        String prefix = "RP" + LocalDate.now().format(DAY);
        for (int i = 0; i < 20; i++) {
            String code = prefix + String.format("%04d", RANDOM.nextInt(10000));
            if (!repository.existsByCode(code)) {
                return code;
            }
        }
        throw new BusinessException(500, "生成工单编号失败，请重试");
    }

    private static String abbreviate(String text) {
        return text.length() <= 60 ? text : text.substring(0, 60) + "…";
    }

    private static int clamp(int size) {
        return Math.min(Math.max(size, 1), 100);
    }
}
