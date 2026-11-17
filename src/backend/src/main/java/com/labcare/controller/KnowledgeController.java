package com.labcare.controller;

import com.labcare.common.ApiResponse;
import com.labcare.dto.KnowledgeDtos;
import com.labcare.security.UserContext;
import com.labcare.service.KnowledgeService;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import java.util.List;

/**
 * 知识库管理（仅管理员）。
 */
@RestController
@RequestMapping("/admin/knowledge")
public class KnowledgeController {

    private final KnowledgeService knowledgeService;

    public KnowledgeController(KnowledgeService knowledgeService) {
        this.knowledgeService = knowledgeService;
    }

    @GetMapping
    public ApiResponse<List<KnowledgeDtos.DocView>> list() {
        return ApiResponse.ok(knowledgeService.list());
    }

    @PostMapping("/upload")
    public ApiResponse<KnowledgeDtos.DocView> upload(@RequestParam("file") MultipartFile file,
                                                     @RequestParam(required = false) String title) {
        return ApiResponse.ok(knowledgeService.upload(file, title, UserContext.require()));
    }

    @DeleteMapping("/{id}")
    public ApiResponse<Void> delete(@PathVariable Long id) {
        knowledgeService.delete(id, UserContext.require());
        return ApiResponse.ok();
    }

    @PostMapping("/reindex")
    public ApiResponse<KnowledgeDtos.IndexResult> reindex() {
        return ApiResponse.ok(knowledgeService.reindex(UserContext.require()));
    }
}
