package com.labcare.config;

import com.labcare.service.KnowledgeService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.boot.context.event.ApplicationReadyEvent;
import org.springframework.context.event.EventListener;
import org.springframework.stereotype.Component;

import java.util.concurrent.CompletableFuture;

/**
 * 启动后异步尝试同步知识库索引（AI 服务可能稍后才启动，失败不阻塞后端）。
 */
@Component
public class KnowledgeBootstrap {

    private static final Logger log = LoggerFactory.getLogger(KnowledgeBootstrap.class);

    private final KnowledgeService knowledgeService;

    public KnowledgeBootstrap(KnowledgeService knowledgeService) {
        this.knowledgeService = knowledgeService;
    }

    @EventListener(ApplicationReadyEvent.class)
    public void onReady() {
        CompletableFuture.runAsync(() -> {
            try {
                knowledgeService.syncOnStartup();
            } catch (Exception e) {
                log.warn("启动时知识库同步跳过：{}", e.getMessage());
            }
        });
    }
}
