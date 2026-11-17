"""LabCare AI 服务入口：RAG 知识问答 + Agent 业务助手。

启动：python -m uvicorn app.main:app --host 127.0.0.1 --port 8100
"""
from __future__ import annotations

import logging

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.agent import runner
from app.agent.tools import ToolError
from app.config import settings
from app.llm import llm_status
from app.rag.pipeline import RagPipeline
from app.schemas import (
    AgentRequest,
    AgentResponse,
    DeleteRequest,
    IndexRequest,
    IndexResponse,
    RagChatRequest,
    RagChatResponse,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-5s [%(name)s] %(message)s",
)
log = logging.getLogger("labcare.ai")

app = FastAPI(title="LabCare AI Service", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

pipeline = RagPipeline()


@app.on_event("startup")
def _startup() -> None:
    status = llm_status()
    log.info("AI 服务启动：模型=%s, 向量库=%s, 分片=%d",
             status["model"] or "未配置（降级模式）", settings.chroma_dir, pipeline.store.count)
    if not status["enabled"]:
        log.warning("未检测到 LAB_LLM_API_KEY，RAG/Agent 将以降级模式运行（检索真实、回答为抽取式）")


@app.get("/health")
def health() -> dict:
    status = llm_status()
    return {
        "status": "ok",
        "service": "labcare-ai",
        "degraded": not status["enabled"],
        "llm": status,
        "chunks": pipeline.store.count,
        "chunk_size": settings.chunk_size,
        "top_k": settings.top_k,
    }


@app.post("/rag/index", response_model=IndexResponse)
def index(request: IndexRequest) -> dict:
    if not request.documents:
        raise HTTPException(status_code=400, detail="documents 不能为空")
    return pipeline.index([doc.model_dump() for doc in request.documents], rebuild=request.rebuild)


@app.post("/rag/delete")
def delete(request: DeleteRequest) -> dict:
    pipeline.delete(request.document_id)
    return {"deleted": request.document_id, "chunks": pipeline.store.count}


@app.post("/rag/chat", response_model=RagChatResponse)
def rag_chat(request: RagChatRequest) -> dict:
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="question 不能为空")
    try:
        return pipeline.answer(request.question, [item.model_dump() for item in request.history])
    except Exception as exc:  # 检索异常不伪装成"无答案"
        log.exception("RAG 问答失败")
        raise HTTPException(status_code=500, detail=f"检索服务异常：{exc}") from exc


@app.post("/agent/chat", response_model=AgentResponse)
def agent_chat(request: AgentRequest) -> dict:
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="message 不能为空")
    try:
        result = runner.run(
            request.message,
            [item.model_dump() for item in request.history],
            request.user.model_dump(),
        )
        return result
    except ToolError as exc:
        raise HTTPException(status_code=503, detail=f"业务工具不可用：{exc}") from exc
    except Exception as exc:
        log.exception("Agent 执行失败")
        raise HTTPException(status_code=500, detail=f"智能助手执行失败：{exc}") from exc


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="127.0.0.1", port=8100, reload=False)
