package com.labcare.repository;

import com.labcare.domain.OperationLog;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface OperationLogRepository extends JpaRepository<OperationLog, Long> {

    List<OperationLog> findByTargetTypeAndTargetIdOrderByIdAsc(String targetType, String targetId);
}
