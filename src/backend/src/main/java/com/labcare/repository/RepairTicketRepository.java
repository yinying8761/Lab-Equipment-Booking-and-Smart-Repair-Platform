package com.labcare.repository;

import com.labcare.domain.RepairStatus;
import com.labcare.domain.RepairTicket;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.JpaSpecificationExecutor;

public interface RepairTicketRepository extends JpaRepository<RepairTicket, Long>,
        JpaSpecificationExecutor<RepairTicket> {

    Page<RepairTicket> findByUserIdOrderByIdDesc(Long userId, Pageable pageable);

    boolean existsByCode(String code);

    long countByStatus(RepairStatus status);

    long countByUserIdAndStatus(Long userId, RepairStatus status);

    long countByEquipmentIdAndStatusIn(Long equipmentId, java.util.List<RepairStatus> statuses);
}
