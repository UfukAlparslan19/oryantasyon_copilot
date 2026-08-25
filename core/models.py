"""RAG veri modelleri."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class DocumentChunk:
    chunk_id: str
    text: str
    source: str
    page: int | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def as_metadata(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "page": self.page if self.page is not None else 0,
            **self.metadata,
        }


@dataclass
class SearchResult:
    chunk_id: str
    text: str
    source: str
    page: int | None
    distance: float
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def relevance(self) -> float:
        """Chroma distance değerini 0-1 arası okunabilir skora çevirir."""
        return max(0.0, min(1.0, 1.0 - self.distance))


@dataclass
class AssistantAnswer:
    answer: Any
    sources: list[SearchResult]
    used_llm: bool = False
    fallback_reason: str | None = None
