package com.labcare.domain;

import jakarta.persistence.*;
import lombok.Getter;
import lombok.Setter;

import java.time.LocalDateTime;

@Entity
@Table(name = "repair_ticket")
@Getter
@Setter
public class RepairTicket {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false, unique = true, length = 32)
    private String code;

    @Column(nullable = false)
    private Long equipmentId;

    @Column(nullable = false)
    private Long userId;

    @Column(length = 50)
    private String contact;

    @Column(nullable = false, length = 1000)
    private String description;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false, length = 20)
    private RepairStatus status = RepairStatus.PENDING;

    private Long handlerId;

    @Column(length = 1000)
    private String resolution;

    private LocalDateTime acceptedAt;
    private LocalDateTime completedAt;

    @Column(nullable = false, length = 20)
    private String source = "MANUAL";

    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;

    @PrePersist
    void prePersist() {
        LocalDateTime now = LocalDateTime.now();
        createdAt = now;
        updatedAt = now;
    }

    @PreUpdate
    void preUpdate() {
        updatedAt = LocalDateTime.now();
    }
}
