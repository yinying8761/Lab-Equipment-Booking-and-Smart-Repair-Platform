package com.labcare.controller;

import com.labcare.common.ApiResponse;
import com.labcare.common.BusinessException;
import com.labcare.domain.Equipment;
import com.labcare.domain.EquipmentStatus;
import com.labcare.dto.EquipmentDtos;
import com.labcare.service.EquipmentService;
import org.springframework.web.bind.annotation.*;

import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/**
 * 供 AI 服务调用的受控业务工具（服务间令牌保护，不对浏览器开放）。
 * 注意：这里只提供"查询"与"建单前校验"，不提供任何写接口，
 * 工单写入必须由用户在页面上确认后走 /ai/agent/confirm。
 */
@RestController
@RequestMapping("/internal/tools")
public class InternalToolController {

    private final EquipmentService equipmentService;

    public InternalToolController(EquipmentService equipmentService) {
        this.equipmentService = equipmentService;
    }

    @GetMapping("/equipments")
    public ApiResponse<List<EquipmentDtos.EquipmentOption>> search(@RequestParam(required = false) String keyword) {
        return ApiResponse.ok(equipmentService.options(keyword));
    }

    @GetMapping("/equipments/{id}")
    public ApiResponse<EquipmentDtos.EquipmentView> detail(@PathVariable Long id) {
        return ApiResponse.ok(equipmentService.detail(id));
    }

    /**
     * 校验拟创建的工单参数并生成确认文案，不产生任何写入。
     */
    @PostMapping("/repairs/prepare")
    public ApiResponse<Map<String, Object>> prepare(@RequestBody Map<String, Object> body) {
        Long equipmentId = body.get("equipmentId") == null ? null : Long.valueOf(String.valueOf(body.get("equipmentId")));
        String description = body.get("description") == null ? "" : String.valueOf(body.get("description")).trim();
        String contact = body.get("contact") == null ? "" : String.valueOf(body.get("contact")).trim();

        if (equipmentId == null) {
            throw BusinessException.badRequest("请提供设备 id");
        }
        if (description.isBlank()) {
            throw BusinessException.badRequest("故障描述不能为空");
        }
        Equipment equipment = equipmentService.require(equipmentId);
        if (equipment.getStatus() == EquipmentStatus.DISABLED) {
            throw BusinessException.badRequest("设备已停用，暂不受理新工单");
        }
        Map<String, Object> data = new LinkedHashMap<>();
        data.put("equipmentId", equipment.getId());
        data.put("equipmentCode", equipment.getCode());
        data.put("equipmentName", equipment.getName());
        data.put("laboratory", equipment.getLaboratory());
        data.put("description", description);
        data.put("contact", contact);
        data.put("preview", "拟为「" + equipment.getCode() + " " + equipment.getName() + "」创建报修工单，故障描述："
                + description + "。确认后才会真正提交。");
        return ApiResponse.ok(data);
    }
}
