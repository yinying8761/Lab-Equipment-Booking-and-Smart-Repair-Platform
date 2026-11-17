package com.labcare.domain;

/**
 * 报修工单状态机：
 * PENDING -> PROCESSING（受理）
 * PROCESSING -> COMPLETED（填写处理结果）
 * PENDING / PROCESSING -> CLOSED（无效或重复工单）
 */
public enum RepairStatus {
    PENDING("待受理"),
    PROCESSING("处理中"),
    COMPLETED("已完成"),
    CLOSED("已关闭");

    private final String label;

    RepairStatus(String label) {
        this.label = label;
    }

    public String getLabel() {
        return label;
    }

    public boolean isFinal() {
        return this == COMPLETED || this == CLOSED;
    }
}
