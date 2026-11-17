"""RAG 管道：文档索引、混合检索、带引用的回答生成。"""
from __future__ import annotations

import logging
import re
from pathlib import Path

import jieba
from langchain_core.messages import HumanMessage, SystemMessage
from rank_bm25 import BM25Okapi

from app.config import settings
from app.llm import get_llm
from app.rag.store import Hit, VectorStore
from app.rag.text import load_text, split_text

log = logging.getLogger("labcare.rag")

_STOPWORDS = {
    "的", "了", "是", "在", "和", "与", "及", "或", "我", "你", "他", "它", "这", "那", "个", "怎么",
    "如何", "什么", "为什么", "请问", "一下", "可以", "需要", "应该", "是否", "吗", "呢", "啊", "呀",
    "有", "没有", "要", "会", "能", "把", "被", "对", "为", "以", "于", "并", "但", "如果", "然后",
}

_ILLEGAL = re.compile(r"[^\w\u4e00-\u9fff]+")

SYSTEM_PROMPT = """你是「实验室设备预约与智能报修平台」的知识问答助手。
请严格依据【资料】回答用户关于设备使用、操作规范与常见故障的问题，规则如下：
1. 只使用【资料】中的信息，不得编造型号、参数、维修步骤或安全结论。
2. 回答用中文，简洁分点，关键结论后用 [1][2] 标注来源编号。
3. 如果【资料】不足以回答，或问题涉及人身安全、危险操作，必须明确说明"现有资料无法确认"，
   并建议联系实验室管理员，不得给出未经证实的操作步骤。
4. 不要提及"资料片段""上下文"等技术用语，直接以助手身份回答。"""


def tokenize(text: str) -> list[str]:
    text = _ILLEGAL.sub(" ", (text or "").lower())
    tokens = []
    for token in jieba.lcut(text):
        token = token.strip()
        if not token or token in _STOPWORDS:
            continue
        if len(token) == 1 and not token.isalnum():
            continue
        tokens.append(token)
    return tokens


class RagPipeline:
    def __init__(self) -> None:
        self.store = VectorStore()

    # ------------------------------------------------------------------
    # 索引
    # ------------------------------------------------------------------
    def index(self, documents: list[dict], rebuild: bool = False) -> dict:
        if rebuild:
            self.store.reset()
        results = []
        total = 0
        for item in documents:
            doc_id = int(item["id"])
            title = str(item.get("title") or "")
            path = Path(item["path"])
            source_name = path.name
            try:
                text = load_text(path)
                chunks = split_text(text)
                if not chunks:
                    results.append({"id": doc_id, "title": title, "chunks": [], "error": "未能解析出有效文本"})
                    continue
                self.store.add_document(doc_id, title, source_name, chunks)
                total += len(chunks)
                results.append({
                    "id": doc_id,
                    "title": title,
                    "chunks": [{"index": i, "content": c} for i, c in enumerate(chunks)],
                    "error": None,
                })
            except Exception as exc:  # 单篇失败不影响其它文档
                log.exception("索引文档失败 %s", path)
                results.append({"id": doc_id, "title": title, "chunks": [], "error": str(exc)[:300]})
        return {
            "documents": results,
            "totalChunks": total,
            "degraded": not settings.llm_enabled,
            "message": f"已索引 {len(documents)} 篇文档，共 {total} 个分片",
        }

    def delete(self, document_id: int) -> None:
        self.store.delete_document(document_id)

    # ------------------------------------------------------------------
    # 检索
    # ------------------------------------------------------------------
    def search(self, question: str, top_k: int | None = None) -> list[Hit]:
        top_k = top_k or settings.top_k
        candidates = self.store.query(question, max(top_k * 3, 10))
        corpus = self.store.all_chunks()
        if not corpus:
            return []

        query_tokens = tokenize(question)
        bm25 = BM25Okapi([tokenize(hit.content) for hit in corpus]) if corpus else None
        lexical: dict[str, float] = {}
        if bm25 is not None and query_tokens:
            scores = bm25.get_scores(query_tokens)
            for hit, score in zip(corpus, scores):
                lexical[f"{hit.document_id}-{hit.chunk_index}"] = float(score)
        max_lexical = max(lexical.values(), default=0.0) or 1.0

        def key(hit: Hit) -> str:
            return f"{hit.document_id}-{hit.chunk_index}"

        for hit in candidates:
            hit.lexical_score = lexical.get(key(hit), 0.0)
            normalised_lexical = hit.lexical_score / max_lexical
            hit.score = round(0.45 * hit.vector_score + 0.55 * normalised_lexical, 4)

        candidates.sort(key=lambda h: h.score, reverse=True)
        return candidates[:top_k]

    def coverage(self, question: str, hit: Hit) -> float:
        query_tokens = set(tokenize(question))
        if not query_tokens:
            return 0.0
        chunk_tokens = set(tokenize(hit.content))
        return len(query_tokens & chunk_tokens) / len(query_tokens)

    # ------------------------------------------------------------------
    # 回答
    # ------------------------------------------------------------------
    def answer(self, question: str, history: list[dict] | None = None) -> dict:
        history = history or []
        if self.store.count == 0:
            return self._insufficient("知识库尚未建立索引")

        hits = self.search(question)
        if not hits:
            return self._insufficient("未检索到相关资料")

        best = hits[0]
        best_coverage = self.coverage(question, best)
        if best_coverage < 0.34 and best.lexical_score <= 0:
            return self._insufficient("检索到的资料与问题不匹配")

        citations = [
            {
                "documentId": hit.document_id,
                "title": hit.title,
                "sourceName": hit.source_name,
                "chunkIndex": hit.chunk_index,
                "snippet": self._clean(hit.content)[:180],
                "score": hit.score,
            }
            for hit in hits[:3]
        ]

        llm = get_llm()
        if llm is None:
            return {
                "answer": self._extractive_answer(hits),
                "citations": citations,
                "degraded": True,
                "notice": "当前未配置大模型 API Key，回答为检索原文摘要（检索与来源均真实）",
            }

        context = "\n\n".join(
            f"[{index + 1}] 《{hit.title}》第 {hit.chunk_index + 1} 段：\n{hit.content}"
            for index, hit in enumerate(hits)
        )
        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=f"【资料】\n{context}\n\n【问题】\n{question}"),
        ]
        try:
            response = llm.invoke(messages)
            answer = self._content_to_text(response.content)
            if not answer.strip():
                raise ValueError("模型返回空内容")
            return {"answer": answer.strip(), "citations": citations, "degraded": False, "notice": ""}
        except Exception as exc:
            log.warning("调用大模型失败，回退为检索摘要: %s", exc)
            return {
                "answer": self._extractive_answer(hits),
                "citations": citations,
                "degraded": True,
                "notice": "模型服务暂不可用，已回退为检索原文摘要",
            }

    def _insufficient(self, reason: str) -> dict:
        return {
            "answer": f"现有资料无法确认该问题（{reason}）。建议联系实验室管理员或查阅设备说明书后再操作。",
            "citations": [],
            "degraded": not settings.llm_enabled,
            "notice": "证据不足，未生成推测性结论",
        }

    @staticmethod
    def _clean(text: str) -> str:
        """把 Markdown 片段整理成适合直接阅读的纯文本（去掉表格线、井号等标记）。"""
        lines = []
        for raw in (text or "").splitlines():
            line = raw.strip()
            if not line:
                continue
            if line.startswith("|---") or set(line) <= set("|-: "):
                continue
            if line.startswith("|"):
                line = " / ".join(part.strip() for part in line.strip("|").split("|") if part.strip())
            line = line.lstrip("#").strip()
            if line:
                lines.append(line)
        return " ".join(lines)

    def _extractive_answer(self, hits: list[Hit]) -> str:
        lines = ["根据知识库检索到的资料："]
        for index, hit in enumerate(hits[:2]):
            snippet = self._clean(hit.content)
            if len(snippet) > 200:
                snippet = snippet[:200] + "…"
            lines.append(f"[{index + 1}] 《{hit.title}》第 {hit.chunk_index + 1} 段：{snippet}")
        lines.append("以上为原文依据，具体操作请以设备说明书与管理员要求为准。")
        return "\n".join(lines)

    @staticmethod
    def _content_to_text(content) -> str:
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            parts = []
            for item in content:
                if isinstance(item, dict) and item.get("type") == "text":
                    parts.append(item.get("text", ""))
                elif isinstance(item, str):
                    parts.append(item)
            return "".join(parts)
        return str(content)
