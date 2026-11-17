package com.labcare.service;

import com.fasterxml.jackson.databind.JsonNode;
import com.labcare.common.BusinessException;
import com.labcare.domain.DocumentStatus;
import com.labcare.domain.KnowledgeChunk;
import com.labcare.domain.KnowledgeDocument;
import com.labcare.dto.KnowledgeDtos;
import com.labcare.repository.KnowledgeChunkRepository;
import com.labcare.repository.KnowledgeDocumentRepository;
import com.labcare.security.CurrentUser;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.nio.file.StandardCopyOption;
import java.time.format.DateTimeFormatter;
import java.util.*;

/**
 * 知识库管理：文件上传、解析入库、索引重建、文档删除。
 * 文本分片与向量由 AI 服务（LangChain）完成，分片原文回存 MySQL 用于引用溯源。
 */
@Service
public class KnowledgeService {

    private static final Logger log = LoggerFactory.getLogger(KnowledgeService.class);
    private static final Set<String> ALLOWED_EXT = Set.of("txt", "md", "pdf", "docx");
    private static final long MAX_SIZE = 10L * 1024 * 1024;

    private final KnowledgeDocumentRepository documentRepository;
    private final KnowledgeChunkRepository chunkRepository;
    private final AiClient aiClient;
    private final Path knowledgeDir;

    public KnowledgeService(KnowledgeDocumentRepository documentRepository,
                            KnowledgeChunkRepository chunkRepository,
                            AiClient aiClient,
                            @Value("${labcare.storage.knowledge-dir}") String knowledgeDir) {
        this.documentRepository = documentRepository;
        this.chunkRepository = chunkRepository;
        this.aiClient = aiClient;
        this.knowledgeDir = Paths.get(knowledgeDir).toAbsolutePath().normalize();
    }

    @Transactional(readOnly = true)
    public List<KnowledgeDtos.DocView> list() {
        return documentRepository.findAll().stream()
                .sorted(Comparator.comparing(KnowledgeDocument::getId))
                .map(this::toView)
                .toList();
    }

    @Transactional
    public KnowledgeDtos.DocView upload(MultipartFile file, String title, CurrentUser operator) {
        if (file == null || file.isEmpty()) {
            throw BusinessException.badRequest("请选择要上传的文件");
        }
        String original = Optional.ofNullable(file.getOriginalFilename()).orElse("未命名");
        String ext = original.contains(".")
                ? original.substring(original.lastIndexOf('.') + 1).toLowerCase(Locale.ROOT)
                : "";
        if (!ALLOWED_EXT.contains(ext)) {
            throw BusinessException.badRequest("仅支持 txt / md / pdf / docx 格式");
        }
        if (file.getSize() > MAX_SIZE) {
            throw BusinessException.badRequest("文件不能超过 10MB");
        }

        Path uploadDir = knowledgeDir.resolve("uploads");
        try {
            Files.createDirectories(uploadDir);
            String storedName = DateTimeFormatter.ofPattern("yyyyMMddHHmmss").format(java.time.LocalDateTime.now())
                    + "_" + sanitize(original);
            Path target = uploadDir.resolve(storedName);
            Files.copy(file.getInputStream(), target, StandardCopyOption.REPLACE_EXISTING);

            KnowledgeDocument document = new KnowledgeDocument();
            document.setTitle(title == null || title.isBlank() ? stripExt(original) : title.trim());
            document.setSourceName(original);
            document.setFileType(ext);
            document.setFileSize(file.getSize());
            document.setStatus(DocumentStatus.INDEXING);
            document.setUploadedBy(operator.id());
            documentRepository.save(document);

            indexDocuments(List.of(new IndexTarget(document.getId(), document.getTitle(), target.toString())), false);
            return toView(documentRepository.findById(document.getId()).orElseThrow());
        } catch (IOException e) {
            throw new BusinessException(500, "保存文件失败：" + e.getMessage());
        }
    }

    @Transactional
    public void delete(Long id, CurrentUser operator) {
        KnowledgeDocument document = documentRepository.findById(id)
                .orElseThrow(() -> BusinessException.notFound("文档不存在"));
        chunkRepository.deleteByDocumentId(id);
        documentRepository.delete(document);
        deleteFileQuietly(document.getSourceName());
        try {
            aiClient.post("/rag/delete", Map.of("document_id", id));
        } catch (Exception e) {
            log.warn("通知 AI 服务删除向量失败（可稍后重建索引）: {}", e.getMessage());
        }
    }

    /** 重建全部索引：把知识库目录下仍在使用的文档重新解析、切分、向量化。 */
    @Transactional
    public KnowledgeDtos.IndexResult reindex(CurrentUser operator) {
        List<IndexTarget> targets = new ArrayList<>();
        for (KnowledgeDocument document : documentRepository.findAll()) {
            Path path = resolvePath(document);
            if (path != null && Files.exists(path)) {
                targets.add(new IndexTarget(document.getId(), document.getTitle(), path.toString()));
            }
        }
        if (targets.isEmpty()) {
            throw BusinessException.badRequest("知识库目录中没有可用文档");
        }
        return indexDocuments(targets, true);
    }

    /** 启动时尝试同步一次，失败不影响后端启动（AI 服务可能尚未就绪）。 */
    @Transactional
    public void syncOnStartup() {
        try {
            if (!aiClient.healthy()) {
                log.info("AI 服务未就绪，跳过知识库自动索引（可在管理端手动重建）");
                return;
            }
            List<IndexTarget> targets = new ArrayList<>();
            for (KnowledgeDocument document : documentRepository.findAll()) {
                Path path = resolvePath(document);
                if (path != null && Files.exists(path)) {
                    targets.add(new IndexTarget(document.getId(), document.getTitle(), path.toString()));
                }
            }
            if (!targets.isEmpty()) {
                KnowledgeDtos.IndexResult result = indexDocuments(targets, true);
                log.info("知识库自动索引完成：{} 篇文档，{} 个分片", result.documents(), result.chunks());
            }
        } catch (Exception e) {
            log.warn("知识库自动索引失败（可稍后手动重建）: {}", e.getMessage());
        }
    }

    // ------------------------------------------------------------------
    private KnowledgeDtos.IndexResult indexDocuments(List<IndexTarget> targets, boolean rebuild) {
        List<Map<String, Object>> documents = new ArrayList<>();
        for (IndexTarget target : targets) {
            Map<String, Object> item = new LinkedHashMap<>();
            item.put("id", target.id());
            item.put("title", target.title());
            item.put("path", target.path());
            documents.add(item);
        }
        JsonNode response;
        try {
            response = aiClient.post("/rag/index", Map.of("documents", documents, "rebuild", rebuild));
        } catch (BusinessException e) {
            targets.forEach(t -> markFailed(t.id(), e.getMessage()));
            throw e;
        }

        int totalChunks = 0;
        for (JsonNode doc : response.path("documents")) {
            long documentId = doc.path("id").asLong();
            KnowledgeDocument entity = documentRepository.findById(documentId).orElse(null);
            if (entity == null) {
                continue;
            }
            chunkRepository.deleteByDocumentId(documentId);
            int count = 0;
            for (JsonNode chunk : doc.path("chunks")) {
                KnowledgeChunk entity2 = new KnowledgeChunk();
                entity2.setDocumentId(documentId);
                entity2.setChunkIndex(chunk.path("index").asInt(count));
                entity2.setContent(chunk.path("content").asText(""));
                chunkRepository.save(entity2);
                count++;
            }
            entity.setChunkCount(count);
            entity.setStatus(count > 0 ? DocumentStatus.READY : DocumentStatus.FAILED);
            entity.setErrorMessage(count > 0 ? null : "未能解析出有效文本");
            documentRepository.save(entity);
            totalChunks += count;
        }
        return new KnowledgeDtos.IndexResult(targets.size(), totalChunks,
                response.path("degraded").asBoolean(false),
                response.path("message").asText("索引完成"));
    }

    private void markFailed(long id, String message) {
        documentRepository.findById(id).ifPresent(doc -> {
            doc.setStatus(DocumentStatus.FAILED);
            doc.setErrorMessage(message == null ? "索引失败" : message.substring(0, Math.min(400, message.length())));
            documentRepository.save(doc);
        });
    }

    private Path resolvePath(KnowledgeDocument document) {
        Path direct = knowledgeDir.resolve(document.getSourceName());
        if (Files.exists(direct)) {
            return direct;
        }
        Path uploads = knowledgeDir.resolve("uploads");
        if (Files.isDirectory(uploads)) {
            try (var stream = Files.list(uploads)) {
                return stream.filter(p -> p.getFileName().toString().endsWith("_" + document.getSourceName()))
                        .findFirst()
                        .orElse(null);
            } catch (IOException e) {
                return null;
            }
        }
        return null;
    }

    private void deleteFileQuietly(String fileName) {
        Path path = knowledgeDir.resolve(fileName);
        try {
            Files.deleteIfExists(path);
        } catch (IOException e) {
            log.warn("删除知识库文件失败: {}", e.getMessage());
        }
    }

    private KnowledgeDtos.DocView toView(KnowledgeDocument document) {
        String uploader = document.getUploadedBy() == null ? "-" : String.valueOf(document.getUploadedBy());
        return new KnowledgeDtos.DocView(document.getId(), document.getTitle(), document.getSourceName(),
                document.getFileType(), document.getFileSize(), document.getStatus().name(),
                document.getStatus().getLabel(), document.getChunkCount(), document.getErrorMessage(),
                uploader, document.getCreatedAt());
    }

    private static String stripExt(String name) {
        return name.contains(".") ? name.substring(0, name.lastIndexOf('.')) : name;
    }

    private static String sanitize(String name) {
        return name.replaceAll("[\\\\/:*?\"<>|\\s]", "_");
    }

    private record IndexTarget(Long id, String title, String path) {
    }
}
