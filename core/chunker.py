"""Metin parçalama ve doküman kimliği üretimi."""
from __future__ import annotations

import hashlib
import re
from pathlib import Path

from .models import DocumentChunk


_WHITESPACE_RE = re.compile(r"\s+")


def normalize_text(text: str) -> str:
    """PDF çıkarımındaki gereksiz boşlukları normalize eder."""
    text = text.replace("\u00ad", "")
    text = re.sub(r"-\n(?=\w)", "", text)
    return _WHITESPACE_RE.sub(" ", text).strip()


def split_text(text: str, chunk_size: int = 900, overlap: int = 120) -> list[str]:
    """Metni kelime sınırlarını koruyarak örtüşmeli parçalara böler."""
    if chunk_size <= 0:
        raise ValueError("chunk_size pozitif olmalıdır")
    if overlap < 0 or overlap >= chunk_size:
        raise ValueError("overlap, 0 <= overlap < chunk_size koşulunu sağlamalıdır")

    normalized = normalize_text(text)
    if not normalized:
        return []

    words = normalized.split(" ")
    chunks: list[str] = []
    current: list[str] = []
    current_len = 0
    for word in words:
        additional = len(word) + (1 if current else 0)
        if current and current_len + additional > chunk_size:
            chunks.append(" ".join(current))
            overlap_words: list[str] = []
            overlap_len = 0
            for previous in reversed(current):
                candidate_len = len(previous) + (1 if overlap_words else 0)
                if overlap_len + candidate_len > overlap:
                    break
                overlap_words.insert(0, previous)
                overlap_len += candidate_len
            current = overlap_words
            current_len = overlap_len
        current.append(word)
        current_len += additional
    if current:
        chunks.append(" ".join(current))
    return chunks


def make_chunk_id(source: str, page: int, ordinal: int, text: str) -> str:
    digest = hashlib.sha1(text.encode("utf-8")).hexdigest()[:10]
    stem = Path(source).stem.lower().replace(" ", "-")
    return f"{stem}-p{page:03d}-c{ordinal:03d}-{digest}"


def build_chunks(
    source_path: Path, pages: list[tuple[int, str]], chunk_size: int = 900, overlap: int = 120
) -> list[DocumentChunk]:
    """PDF sayfalarından kaynak ve sayfa metadatası olan parçalar oluşturur."""
    chunks: list[DocumentChunk] = []
    for page_number, raw_text in pages:
        for ordinal, text in enumerate(split_text(raw_text, chunk_size, overlap), start=1):
            chunks.append(
                DocumentChunk(
                    chunk_id=make_chunk_id(source_path.name, page_number, ordinal, text),
                    text=text,
                    source=source_path.name,
                    page=page_number,
                    metadata={"file_path": str(source_path)},
                )
            )
    return chunks
