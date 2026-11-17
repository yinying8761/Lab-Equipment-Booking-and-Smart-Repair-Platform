"""向量化：本地哈希向量（无需下载模型），用于 Chroma 语义召回。

说明：课程环境无法保证能下载句向量模型，这里用字符 n-gram 哈希向量保证
"可离线重建、可复现"；检索质量由 BM25 词法重排补足，见 pipeline.rerank。
"""
from __future__ import annotations

from chromadb.api.types import Documents, EmbeddingFunction, Embeddings
from sklearn.feature_extraction.text import HashingVectorizer


class HashingEmbeddingFunction(EmbeddingFunction[Documents]):
    def __init__(self, n_features: int = 2048) -> None:
        self.n_features = n_features
        self._vectorizer = HashingVectorizer(
            n_features=n_features,
            analyzer="char_wb",
            ngram_range=(2, 3),
            alternate_sign=False,
            norm="l2",
            lowercase=True,
        )

    def __call__(self, input: Documents) -> Embeddings:  # noqa: A002 - chroma 协议签名
        matrix = self._vectorizer.transform([text or "" for text in input])
        return matrix.astype("float32").toarray().tolist()

    def name(self) -> str:
        return f"labcare-hashing-{self.n_features}"
