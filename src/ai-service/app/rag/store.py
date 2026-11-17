"""Chroma 向量库封装：索引写入、检索与删除。"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import chromadb
from chromadb.api.types import EmbeddingFunction, Documents

from app.config import settings
from app.rag.embeddings import HashingEmbeddingFunction


@dataclass
class Hit:
    document_id: int
    title: str
    source_name: str
    chunk_index: int
    content: str
    vector_score: float = 0.0
    lexical_score: float = 0.0
    score: float = 0.0


class VectorStore:
    def __init__(self) -> None:
        settings.chroma_dir.mkdir(parents=True, exist_ok=True)
        self._client = chromadb.PersistentClient(path=str(settings.chroma_dir))
        self._ef: EmbeddingFunction[Documents] = HashingEmbeddingFunction()
        self._collection = self._open()

    def _open(self):
        return self._client.get_or_create_collection(
            name=settings.collection_name,
            embedding_function=self._ef,
            metadata={"hnsw:space": "cosine"},
        )

    def reset(self) -> None:
        try:
            self._client.delete_collection(settings.collection_name)
        except Exception:
            pass
        self._collection = self._open()

    def add_document(self, document_id: int, title: str, source_name: str, chunks: list[str]) -> None:
        if not chunks:
            return
        self.delete_document(document_id)
        ids = [f"{document_id}-{index}" for index in range(len(chunks))]
        metadatas = [
            {
                "document_id": document_id,
                "document_title": title,
                "source_name": source_name,
                "chunk_index": index,
            }
            for index in range(len(chunks))
        ]
        self._collection.add(ids=ids, documents=chunks, metadatas=metadatas)

    def delete_document(self, document_id: int) -> None:
        self._collection.delete(where={"document_id": document_id})

    def query(self, text: str, top_k: int) -> list[Hit]:
        total = self._collection.count()
        if total == 0 or not text.strip():
            return []
        result = self._collection.query(
            query_texts=[text],
            n_results=min(max(top_k, 1), total),
            include=["documents", "metadatas", "distances"],
        )
        hits: list[Hit] = []
        documents = result.get("documents") or [[]]
        metadatas = result.get("metadatas") or [[]]
        distances = result.get("distances") or [[]]
        for content, metadata, distance in zip(documents[0], metadatas[0], distances[0]):
            metadata = metadata or {}
            hits.append(
                Hit(
                    document_id=int(metadata.get("document_id", 0)),
                    title=str(metadata.get("document_title", "")),
                    source_name=str(metadata.get("source_name", "")),
                    chunk_index=int(metadata.get("chunk_index", 0)),
                    content=content or "",
                    vector_score=max(0.0, 1.0 - float(distance)),
                )
            )
        return hits

    def all_chunks(self) -> list[Hit]:
        if self._collection.count() == 0:
            return []
        result = self._collection.get(include=["documents", "metadatas"])
        hits: list[Hit] = []
        for content, metadata in zip(result.get("documents") or [], result.get("metadatas") or []):
            metadata = metadata or {}
            hits.append(
                Hit(
                    document_id=int(metadata.get("document_id", 0)),
                    title=str(metadata.get("document_title", "")),
                    source_name=str(metadata.get("source_name", "")),
                    chunk_index=int(metadata.get("chunk_index", 0)),
                    content=content or "",
                )
            )
        return hits

    @property
    def count(self) -> int:
        return self._collection.count()
