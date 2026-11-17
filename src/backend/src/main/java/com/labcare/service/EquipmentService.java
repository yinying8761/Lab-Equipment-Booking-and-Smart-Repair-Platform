package com.labcare.service;

import com.labcare.common.BusinessException;
import com.labcare.common.PageResult;
import com.labcare.domain.Equipment;
import com.labcare.domain.EquipmentStatus;
import com.labcare.dto.EquipmentDtos;
import com.labcare.repository.EquipmentRepository;
import com.labcare.security.CurrentUser;
import jakarta.persistence.criteria.Predicate;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Sort;
import org.springframework.data.jpa.domain.Specification;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.ArrayList;
import java.util.List;

/**
 * 设备台账：查询、维护与状态变更。
 */
@Service
public class EquipmentService {

    private final EquipmentRepository repository;
    private final OperationLogService operationLogService;

    public EquipmentService(EquipmentRepository repository, OperationLogService operationLogService) {
        this.repository = repository;
        this.operationLogService = operationLogService;
    }

    @Transactional(readOnly = true)
    public PageResult<EquipmentDtos.EquipmentView> search(String keyword, String category, String laboratory,
                                                          EquipmentStatus status, int page, int size) {
        Specification<Equipment> spec = buildSpec(keyword, category, laboratory, status);
        Page<Equipment> result = repository.findAll(spec,
                PageRequest.of(Math.max(page - 1, 0), clampSize(size), Sort.by(Sort.Direction.ASC, "code")));
        List<EquipmentDtos.EquipmentView> list = result.getContent().stream().map(EquipmentService::toView).toList();
        return PageResult.of(list, result.getTotalElements(), page, clampSize(size));
    }

    @Transactional(readOnly = true)
    public List<EquipmentDtos.EquipmentOption> options(String keyword) {
        Specification<Equipment> spec = buildSpec(keyword, null, null, null);
        return repository.findAll(spec, Sort.by(Sort.Direction.ASC, "code")).stream()
                .map(e -> new EquipmentDtos.EquipmentOption(e.getId(), e.getCode(), e.getName(),
                        e.getLaboratory(), e.getStatus().name(), e.getStatus().getLabel()))
                .toList();
    }

    @Transactional(readOnly = true)
    public EquipmentDtos.EquipmentView detail(Long id) {
        return toView(require(id));
    }

    @Transactional(readOnly = true)
    public Equipment require(Long id) {
        return repository.findById(id)
                .orElseThrow(() -> BusinessException.notFound("设备不存在"));
    }

    @Transactional
    public EquipmentDtos.EquipmentView create(EquipmentDtos.EquipmentRequest request, CurrentUser operator) {
        if (repository.existsByCode(request.code().trim())) {
            throw BusinessException.conflict("设备编号 " + request.code() + " 已存在");
        }
        Equipment equipment = new Equipment();
        apply(equipment, request);
        repository.save(equipment);
        operationLogService.record(operator, "EQUIPMENT", equipment.getCode(), "CREATE",
                "新增设备：" + equipment.getCode() + " " + equipment.getName());
        return toView(equipment);
    }

    @Transactional
    public EquipmentDtos.EquipmentView update(Long id, EquipmentDtos.EquipmentRequest request, CurrentUser operator) {
        Equipment equipment = require(id);
        if (!equipment.getCode().equals(request.code().trim()) && repository.existsByCode(request.code().trim())) {
            throw BusinessException.conflict("设备编号 " + request.code() + " 已存在");
        }
        apply(equipment, request);
        repository.save(equipment);
        operationLogService.record(operator, "EQUIPMENT", equipment.getCode(), "UPDATE",
                "编辑设备：" + equipment.getCode() + " " + equipment.getName());
        return toView(equipment);
    }

    @Transactional
    public EquipmentDtos.EquipmentView changeStatus(Long id, EquipmentStatus status, CurrentUser operator) {
        Equipment equipment = require(id);
        EquipmentStatus before = equipment.getStatus();
        equipment.setStatus(status);
        repository.save(equipment);
        operationLogService.record(operator, "EQUIPMENT", equipment.getCode(), "STATUS",
                "设备状态 " + before.getLabel() + " -> " + status.getLabel());
        return toView(equipment);
    }

    private void apply(Equipment equipment, EquipmentDtos.EquipmentRequest request) {
        equipment.setCode(request.code().trim());
        equipment.setName(request.name().trim());
        equipment.setCategory(request.category().trim());
        equipment.setLaboratory(request.laboratory().trim());
        equipment.setLocation(request.location());
        equipment.setStatus(request.status());
        equipment.setDescription(request.description());
        equipment.setUsageNote(request.usageNote());
    }

    private Specification<Equipment> buildSpec(String keyword, String category, String laboratory,
                                               EquipmentStatus status) {
        return (root, query, cb) -> {
            List<Predicate> predicates = new ArrayList<>();
            if (keyword != null && !keyword.isBlank()) {
                String like = "%" + keyword.trim() + "%";
                predicates.add(cb.or(
                        cb.like(root.get("name"), like),
                        cb.like(root.get("code"), like),
                        cb.like(root.get("laboratory"), like)));
            }
            if (category != null && !category.isBlank()) {
                predicates.add(cb.equal(root.get("category"), category.trim()));
            }
            if (laboratory != null && !laboratory.isBlank()) {
                predicates.add(cb.equal(root.get("laboratory"), laboratory.trim()));
            }
            if (status != null) {
                predicates.add(cb.equal(root.get("status"), status));
            }
            return cb.and(predicates.toArray(new Predicate[0]));
        };
    }

    private static int clampSize(int size) {
        return Math.min(Math.max(size, 1), 100);
    }

    public static EquipmentDtos.EquipmentView toView(Equipment e) {
        return new EquipmentDtos.EquipmentView(e.getId(), e.getCode(), e.getName(), e.getCategory(),
                e.getLaboratory(), e.getLocation(), e.getStatus().name(), e.getStatus().getLabel(),
                e.getDescription(), e.getUsageNote(), e.getUpdatedAt());
    }
}
