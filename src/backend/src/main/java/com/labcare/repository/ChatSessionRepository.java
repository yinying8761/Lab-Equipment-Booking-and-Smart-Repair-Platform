package com.labcare.repository;

import com.labcare.domain.ChatMode;
import com.labcare.domain.ChatSession;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;
import java.util.Optional;

public interface ChatSessionRepository extends JpaRepository<ChatSession, Long> {

    List<ChatSession> findByUserIdAndModeOrderByIdDesc(Long userId, ChatMode mode);

    Optional<ChatSession> findByIdAndUserId(Long id, Long userId);
}
