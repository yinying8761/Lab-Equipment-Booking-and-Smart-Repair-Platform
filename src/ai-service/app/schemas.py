"""请求/响应模型。"""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class HistoryItem(BaseModel):
    role: str = "user"
    content: str = ""


class RagChatRequest(BaseModel):
    question: str
    history: list[HistoryItem] = Field(default_factory=list)
    top_k: int | None = None
    user_id: int | None = None


class Citation(BaseModel):
    documentId: int
    title: str
    sourceName: str
    chunkIndex: int
    snippet: str
    score: float


class RagChatResponse(BaseModel):
    answer: str
    citations: list[Citation] = Field(default_factory=list)
    degraded: bool = False
    notice: str = ""


class IndexDocument(BaseModel):
    id: int
    title: str
    path: str


class IndexRequest(BaseModel):
    documents: list[IndexDocument]
    rebuild: bool = False


class ChunkOut(BaseModel):
    index: int
    content: str


class DocumentOut(BaseModel):
    id: int
    title: str
    chunks: list[ChunkOut] = Field(default_factory=list)
    error: str | None = None


class IndexResponse(BaseModel):
    documents: list[DocumentOut] = Field(default_factory=list)
    totalChunks: int = 0
    degraded: bool = False
    message: str = ""


class DeleteRequest(BaseModel):
    document_id: int


class AgentUser(BaseModel):
    id: int = 0
    displayName: str = ""


class AgentRequest(BaseModel):
    message: str
    history: list[HistoryItem] = Field(default_factory=list)
    session_id: int | None = None
    user: AgentUser = Field(default_factory=AgentUser)


class TraceItem(BaseModel):
    step: int = 1
    tool: str = ""
    input: str = ""
    output: str = ""
    success: bool = True


class Proposal(BaseModel):
    actionType: str = "CREATE_REPAIR"
    equipmentId: int
    equipmentCode: str = ""
    equipmentName: str = ""
    description: str = ""
    contact: str = ""
    preview: str = ""


class AgentResponse(BaseModel):
    reply: str
    trace: list[TraceItem] = Field(default_factory=list)
    proposal: Proposal | None = None
    degraded: bool = False
    notice: str = ""
    meta: dict[str, Any] = Field(default_factory=dict)
