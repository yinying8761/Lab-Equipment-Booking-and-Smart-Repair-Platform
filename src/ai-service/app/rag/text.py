"""文档解析与切分。"""
from __future__ import annotations

from pathlib import Path

from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.config import settings

SUPPORTED = {".txt", ".md", ".pdf", ".docx"}

_SEPARATORS = ["\n\n", "\n", "。", "！", "？", "；", "，", " ", ""]


def load_text(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix not in SUPPORTED:
        raise ValueError(f"不支持的文件类型：{suffix}")
    if suffix in {".txt", ".md"}:
        return _read_text_auto(path)
    if suffix == ".pdf":
        return _read_pdf(path)
    if suffix == ".docx":
        return _read_docx(path)
    raise ValueError(f"不支持的文件类型：{suffix}")


def _read_text_auto(path: Path) -> str:
    raw = path.read_bytes()
    for encoding in ("utf-8-sig", "utf-8", "gb18030"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="ignore")


def _read_pdf(path: Path) -> str:
    from pypdf import PdfReader

    reader = PdfReader(str(path))
    parts = []
    for page in reader.pages:
        parts.append(page.extract_text() or "")
    return "\n".join(parts)


def _read_docx(path: Path) -> str:
    from docx import Document

    document = Document(str(path))
    parts = [p.text for p in document.paragraphs]
    for table in document.tables:
        for row in table.rows:
            parts.append(" | ".join(cell.text.strip() for cell in row.cells))
    return "\n".join(part for part in parts if part.strip())


def split_text(text: str) -> list[str]:
    text = (text or "").replace("\r\n", "\n").strip()
    if not text:
        return []
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
        separators=_SEPARATORS,
        keep_separator=True,
    )
    chunks = [chunk.strip() for chunk in splitter.split_text(text)]
    return [chunk for chunk in chunks if len(chunk) >= 10]
