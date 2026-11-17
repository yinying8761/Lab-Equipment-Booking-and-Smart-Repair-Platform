"""全局配置：全部来自环境变量，仓库中不保存任何真实密钥。"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


def _env(name: str, default: str = "") -> str:
    return os.environ.get(name, default).strip()


def _project_root() -> Path:
    # app/config.py -> app/ -> ai-service/ -> src/ -> 项目根
    return Path(__file__).resolve().parents[3]


@dataclass
class Settings:
    # 大模型（OpenAI 兼容接口，默认 DeepSeek）
    llm_api_key: str = field(default_factory=lambda: _env("LAB_LLM_API_KEY") or _env("DEEPSEEK_API_KEY"))
    llm_base_url: str = field(default_factory=lambda: _env("LAB_LLM_BASE_URL", "https://api.deepseek.com/v1"))
    llm_model: str = field(default_factory=lambda: _env("LAB_LLM_MODEL", "deepseek-flash"))
    llm_temperature: float = field(default_factory=lambda: float(_env("LAB_LLM_TEMPERATURE", "0.2")))
    llm_timeout: int = field(default_factory=lambda: int(_env("LAB_LLM_TIMEOUT", "45")))

    # 业务后端
    backend_base_url: str = field(default_factory=lambda: _env("LAB_BACKEND_BASE_URL", "http://127.0.0.1:8080/api"))
    internal_token: str = field(default_factory=lambda: _env("LAB_INTERNAL_TOKEN", "labcare-internal-token-2026"))
    backend_timeout: int = field(default_factory=lambda: int(_env("LAB_BACKEND_TIMEOUT", "15")))

    # 向量库与知识库
    chroma_dir: Path = field(default_factory=lambda: Path(_env("LAB_CHROMA_DIR") or (_project_root() / "data" / "chroma")))
    knowledge_dir: Path = field(default_factory=lambda: Path(_env("LAB_KNOWLEDGE_DIR") or (_project_root() / "data" / "知识库")))
    collection_name: str = field(default_factory=lambda: _env("LAB_CHROMA_COLLECTION", "labcare_knowledge"))

    # 检索与切分参数
    chunk_size: int = field(default_factory=lambda: int(_env("LAB_CHUNK_SIZE", "320")))
    chunk_overlap: int = field(default_factory=lambda: int(_env("LAB_CHUNK_OVERLAP", "60")))
    top_k: int = field(default_factory=lambda: int(_env("LAB_TOP_K", "4")))
    min_score: float = field(default_factory=lambda: float(_env("LAB_MIN_SCORE", "0.05")))

    @property
    def llm_enabled(self) -> bool:
        return bool(self.llm_api_key)


settings = Settings()
