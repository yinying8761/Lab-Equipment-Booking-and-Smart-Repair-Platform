package com.labcare.domain;

import jakarta.persistence.*;
import lombok.Getter;
import lombok.Setter;

import java.time.LocalDateTime;

/**
 * Agent 写操作待确认动作：确认前不产生任何业务写入。
 */
@Entity
@Table(name = "pending_action")
@Getter
@Setter
public class PendingAction {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false, unique = true, length = 64)
    private String token;

    @Column(nullable = false)
    private Long userId;

    private Long sessionId;

    @Column(nullable = false, length = 40)
    private String actionType;

    @Column(nullable = false, columnDefinition = "JSON")
    private String payload;

    @Column(length = 1000)
    private String preview;

    @Column(nullable = false, length = 20)
    private String status = "PENDING";

    @Column(length = 64)
    private String resultRef;

    private LocalDateTime createdAt;

    @Column(nullable = false)
    private LocalDateTime expiresAt;

    @PrePersist
    void prePersist() {
        createdAt = LocalDateTime.now();
    }
}
