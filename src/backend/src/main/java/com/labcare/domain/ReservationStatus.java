package com.labcare.domain;

/**
 * 预约状态机：
 * PENDING -> APPROVED / REJECTED（管理员审核）
 * PENDING -> CANCELLED（申请人取消）
 * APPROVED -> COMPLETED（结束后管理员标记）
 * APPROVED -> CANCELLED（管理员撤销，仅在开始前允许）
 */
public enum ReservationStatus {
    PENDING("待审核"),
    APPROVED("已通过"),
    REJECTED("已驳回"),
    CANCELLED("已取消"),
    COMPLETED("已完成");

    private final String label;

    ReservationStatus(String label) {
        this.label = label;
    }

    public String getLabel() {
        return label;
    }

    public boolean isFinal() {
        return this == REJECTED || this == CANCELLED || this == COMPLETED;
    }
}
