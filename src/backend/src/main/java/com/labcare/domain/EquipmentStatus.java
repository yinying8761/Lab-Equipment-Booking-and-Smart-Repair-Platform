package com.labcare.domain;

/**
 * 设备状态。只有 AVAILABLE 的设备可以提交新预约。
 */
public enum EquipmentStatus {
    AVAILABLE("可用"),
    MAINTENANCE("维修中"),
    DISABLED("停用");

    private final String label;

    EquipmentStatus(String label) {
        this.label = label;
    }

    public String getLabel() {
        return label;
    }
}
