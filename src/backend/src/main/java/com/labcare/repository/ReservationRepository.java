package com.labcare.repository;

import com.labcare.domain.Reservation;
import com.labcare.domain.ReservationStatus;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.JpaSpecificationExecutor;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.time.LocalDateTime;
import java.util.List;

public interface ReservationRepository extends JpaRepository<Reservation, Long>,
        JpaSpecificationExecutor<Reservation> {

    Page<Reservation> findByUserIdOrderByIdDesc(Long userId, Pageable pageable);

    List<Reservation> findByUserIdAndStatusOrderByIdDesc(Long userId, ReservationStatus status);

    /**
     * 时间冲突检测：同一设备下已通过的预约，只要与 [start, end) 有交集即冲突。
     */
    @Query("""
            select r from Reservation r
             where r.equipmentId = :equipmentId
               and r.status = :status
               and r.startTime < :endTime
               and r.endTime > :startTime
               and (:excludeId is null or r.id <> :excludeId)
            """)
    List<Reservation> findConflicts(@Param("equipmentId") Long equipmentId,
                                    @Param("status") ReservationStatus status,
                                    @Param("startTime") LocalDateTime startTime,
                                    @Param("endTime") LocalDateTime endTime,
                                    @Param("excludeId") Long excludeId);

    long countByStatus(ReservationStatus status);

    boolean existsByCode(String code);
}
