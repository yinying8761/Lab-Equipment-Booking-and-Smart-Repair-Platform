package com.labcare.repository;

import com.labcare.domain.PendingAction;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;
import java.util.Optional;

public interface PendingActionRepository extends JpaRepository<PendingAction, Long> {

    Optional<PendingAction> findByToken(String token);

    List<PendingAction> findByUserIdAndStatusOrderByIdDesc(Long userId, String status);
}
