"""Uygulama yapılandırması.

Tüm dosya yolları proje köküne göre çözülür; böylece uygulama farklı
klasörlerden çalıştırılsa da aynı şekilde davranır.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")


@dataclass(frozen=True)
class Settings:
    project_root: Path = PROJECT_ROOT
    data_dir: Path = PROJECT_ROOT / "data"
    pdf_dir: Path = PROJECT_ROOT / "data" / "pdfs"
    chroma_dir: Path = PROJECT_ROOT / "chroma_db"
    collection_name: str = os.getenv("CHROMA_COLLECTION", "onboarding_documents")
    ollama_base_url: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    ollama_model: str = os.getenv("OLLAMA_MODEL", "phi3:mini")
    embedding_model: str = os.getenv(
        "EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"
    )
    top_k: int = int(os.getenv("TOP_K", "5"))
    chunk_size: int = int(os.getenv("CHUNK_SIZE", "900"))
    chunk_overlap: int = int(os.getenv("CHUNK_OVERLAP", "120"))
    retrieval_min_score: float = float(os.getenv("RETRIEVAL_MIN_SCORE", "0.12"))
    request_timeout: float = float(os.getenv("OLLAMA_TIMEOUT", "90"))


settings = Settings()


def ensure_directories() -> None:
    """Uygulamanın ihtiyaç duyduğu yerel klasörleri oluşturur."""
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    settings.pdf_dir.mkdir(parents=True, exist_ok=True)
    settings.chroma_dir.mkdir(parents=True, exist_ok=True)
