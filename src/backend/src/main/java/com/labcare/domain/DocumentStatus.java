package com.labcare.domain;

/**
 * 知识文档处理状态。
 */
public enum DocumentStatus {
    PENDING("待处理"),
    INDEXING("索引中"),
    READY("可检索"),
    FAILED("处理失败");

    private final String label;

    DocumentStatus(String label) {
        this.label = label;
    }

    public String getLabel() {
        return label;
    }
}
