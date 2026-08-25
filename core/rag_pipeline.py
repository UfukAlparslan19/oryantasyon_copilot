"""Onboarding RAG servisinin ana orkestratörü."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from .config import Settings, settings
from .llm import OllamaClient, answer_question
from .models import AssistantAnswer, SearchResult
from .vector_store import LocalVectorStore


class OnboardingRAG:
    """Yerel PDF indeksleme, retrieval ve cevap üretimini tek arayüzde toplar."""

    def __init__(self, app_settings: Settings = settings) -> None:
        self.settings = app_settings
        self.store = LocalVectorStore(app_settings)
        self.llm_client = OllamaClient(app_settings)

    def index_documents(self, *, clear_existing: bool = False) -> dict[str, Any]:
        return self.store.index_pdf_directory(
            self.settings.pdf_dir, clear_existing=clear_existing
        )

    def search(self, question: str, top_k: int | None = None) -> list[SearchResult]:
        return self.store.search(question, top_k=top_k)

    def ask(self, question: str, *, allow_llm: bool = True, chat_history: list[dict[str, str]] = None) -> AssistantAnswer:
        question = question.strip()
        if len(question) < 3:
            return AssistantAnswer(
                answer="Lütfen en az birkaç kelimelik, daha açık bir soru yazın.", sources=[]
            )
        results = self.search(question)
        return answer_question(
            question, results, self.llm_client, allow_llm=allow_llm, chat_history=chat_history
        )

    def status(self) -> dict[str, Any]:
        return {
            "indexed_chunks": self.store.count,
            "embedding_backend": self.store.embedding_backend,
            "ollama_url": self.settings.ollama_base_url,
            "ollama_model": self.settings.ollama_model,
            "pdf_dir": str(self.settings.pdf_dir),
        }
