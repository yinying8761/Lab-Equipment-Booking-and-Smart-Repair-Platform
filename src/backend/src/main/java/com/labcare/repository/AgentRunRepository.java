package com.labcare.repository;

import com.labcare.domain.AgentRun;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface AgentRunRepository extends JpaRepository<AgentRun, Long> {

    List<AgentRun> findBySessionIdOrderByIdAsc(Long sessionId);
}
