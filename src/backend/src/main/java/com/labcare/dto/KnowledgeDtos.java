package com.labcare.dto;

import java.time.LocalDateTime;

/**
 * 知识库 DTO。
 */
public final class KnowledgeDtos {

    private KnowledgeDtos() {
    }

    public record DocView(Long id, String title, String sourceName, String fileType, Long fileSize,
                          String status, String statusLabel, Integer chunkCount, String errorMessage,
                          String uploadedBy, LocalDateTime createdAt) {
    }

    public record IndexResult(int documents, int chunks, boolean degraded, String message) {
    }
}
