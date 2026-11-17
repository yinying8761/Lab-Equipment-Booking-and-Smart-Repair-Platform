package com.labcare.repository;

import com.labcare.domain.KnowledgeDocument;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.Optional;

public interface KnowledgeDocumentRepository extends JpaRepository<KnowledgeDocument, Long> {

    Optional<KnowledgeDocument> findBySourceName(String sourceName);
}
