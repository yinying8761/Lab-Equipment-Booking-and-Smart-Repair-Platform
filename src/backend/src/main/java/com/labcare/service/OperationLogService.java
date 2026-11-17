package com.labcare.service;

import com.labcare.domain.OperationLog;
import com.labcare.repository.OperationLogRepository;
import com.labcare.security.CurrentUser;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Propagation;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

/**
 * 关键操作留痕：审核、状态变更、Agent 建单等都能在工单详情中回溯。
 */
@Service
public class OperationLogService {

    private final OperationLogRepository repository;

    public OperationLogService(OperationLogRepository repository) {
        this.repository = repository;
    }

    @Transactional(propagation = Propagation.REQUIRED)
    public void record(CurrentUser operator, String targetType, String targetId, String action, String summary) {
        OperationLog log = new OperationLog();
        if (operator != null) {
            log.setOperatorId(operator.id());
            log.setOperatorName(operator.displayName());
        }
        log.setTargetType(targetType);
        log.setTargetId(targetId);
        log.setAction(action);
        log.setSummary(summary);
        repository.save(log);
    }

    @Transactional(readOnly = true)
    public List<OperationLog> findByTarget(String targetType, String targetId) {
        return repository.findByTargetTypeAndTargetIdOrderByIdAsc(targetType, targetId);
    }
}
