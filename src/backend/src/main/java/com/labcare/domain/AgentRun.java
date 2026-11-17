package com.labcare.domain;

import jakarta.persistence.*;
import lombok.Getter;
import lombok.Setter;

import java.time.LocalDateTime;

@Entity
@Table(name = "agent_run")
@Getter
@Setter
public class AgentRun {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    private Long sessionId;
    private Long userId;

    @Column(nullable = false)
    private Integer stepNo = 1;

    @Column(length = 60)
    private String toolName;

    @Column(length = 500)
    private String inputSummary;

    @Column(length = 500)
    private String outputSummary;

    @Column(nullable = false)
    private Integer success = 1;

    @Column(length = 500)
    private String errorMessage;

    private LocalDateTime createdAt;

    @PrePersist
    void prePersist() {
        createdAt = LocalDateTime.now();
    }
}
