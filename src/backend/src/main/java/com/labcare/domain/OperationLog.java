package com.labcare.domain;

import jakarta.persistence.*;
import lombok.Getter;
import lombok.Setter;

import java.time.LocalDateTime;

@Entity
@Table(name = "operation_log")
@Getter
@Setter
public class OperationLog {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    private Long operatorId;

    @Column(length = 50)
    private String operatorName;

    @Column(nullable = false, length = 30)
    private String targetType;

    @Column(length = 64)
    private String targetId;

    @Column(nullable = false, length = 40)
    private String action;

    @Column(length = 500)
    private String summary;

    private LocalDateTime createdAt;

    @PrePersist
    void prePersist() {
        createdAt = LocalDateTime.now();
    }
}
