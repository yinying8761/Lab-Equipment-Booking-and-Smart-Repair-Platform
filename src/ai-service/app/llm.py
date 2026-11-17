"""大模型客户端：OpenAI 兼容接口（默认 DeepSeek）。

未配置 API Key 时返回 None，业务流程自动进入"降级模式"：
检索仍然真实执行，回答改为抽取式摘要并在界面上明确标注。
"""
from __future__ import annotations

from langchain_openai import ChatOpenAI

from app.config import settings

_llm: ChatOpenAI | None = None


def get_llm() -> ChatOpenAI | None:
    global _llm
    if not settings.llm_enabled:
        return None
    if _llm is None:
        _llm = ChatOpenAI(
            model=settings.llm_model,
            api_key=settings.llm_api_key,
            base_url=settings.llm_base_url,
            temperature=settings.llm_temperature,
            timeout=settings.llm_timeout,
            max_retries=1,
        )
    return _llm


def llm_status() -> dict:
    return {
        "enabled": settings.llm_enabled,
        "model": settings.llm_model if settings.llm_enabled else None,
        "base_url": settings.llm_base_url if settings.llm_enabled else None,
    }
