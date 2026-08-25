"""ChromaDB kalıcı vektör deposu."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from .chunker import build_chunks
from .config import Settings, settings
from .embeddings import LocalEmbeddingFunction
from .models import DocumentChunk, SearchResult
from .pdf_loader import load_pdf


class LocalVectorStore:
    """PDF parçalarını ChromaDB'de yerel olarak saklar ve arar."""

    def __init__(self, app_settings: Settings = settings) -> None:
        self.settings = app_settings
        self.settings.chroma_dir.mkdir(parents=True, exist_ok=True)
        try:
            import chromadb
        except ImportError as exc:  # pragma: no cover - kurulum testi için açıklayıcı hata
            raise RuntimeError(
                "chromadb kurulu değil. Önce 'pip install -r requirements.txt' çalıştırın."
            ) from exc

        self.embedding_function = LocalEmbeddingFunction(self.settings.embedding_model)
        self.client = chromadb.PersistentClient(path=str(self.settings.chroma_dir))
        self.collection = self.client.get_or_create_collection(
            name=self.settings.collection_name,
            embedding_function=self.embedding_function,
            metadata={"hnsw:space": "cosine"},
        )

    @property
    def count(self) -> int:
        return int(self.collection.count())

    @property
    def embedding_backend(self) -> str:
        return self.embedding_function.backend

    def clear(self) -> None:
        """Mevcut koleksiyonu silip boş koleksiyon oluşturur."""
        self.client.delete_collection(self.settings.collection_name)
        self.collection = self.client.get_or_create_collection(
            name=self.settings.collection_name,
            embedding_function=self.embedding_function,
            metadata={"hnsw:space": "cosine"},
        )

    def add_chunks(self, chunks: list[DocumentChunk], batch_size: int = 64) -> int:
        """Parçaları idempotent biçimde koleksiyona ekler."""
        added = 0
        for start in range(0, len(chunks), batch_size):
            batch = chunks[start : start + batch_size]
            if not batch:
                continue
            self.collection.upsert(
                ids=[chunk.chunk_id for chunk in batch],
                documents=[chunk.text for chunk in batch],
                metadatas=[chunk.as_metadata() for chunk in batch],
            )
            added += len(batch)
        return added

    def index_pdf_directory(
        self,
        pdf_dir: Path | None = None,
        *,
        clear_existing: bool = False,
    ) -> dict[str, Any]:
        """Klasördeki tüm PDF'leri indeksler ve özet istatistik döndürür."""
        target_dir = pdf_dir or self.settings.pdf_dir
        target_dir.mkdir(parents=True, exist_ok=True)
        pdfs = sorted(target_dir.glob("*.pdf"))
        if clear_existing:
            self.clear()

        all_chunks: list[DocumentChunk] = []
        errors: list[str] = []
        for pdf_path in pdfs:
            try:
                pages = load_pdf(pdf_path)
                all_chunks.extend(
                    build_chunks(
                        pdf_path,
                        pages,
                        chunk_size=self.settings.chunk_size,
                        overlap=self.settings.chunk_overlap,
                    )
                )
            except (OSError, ValueError, RuntimeError) as exc:
                errors.append(str(exc))

        added = self.add_chunks(all_chunks)
        return {
            "pdf_count": len(pdfs),
            "chunk_count": len(all_chunks),
            "added_count": added,
            "total_count": self.count,
            "errors": errors,
            "embedding_backend": self.embedding_backend,
        }

    def search(self, query: str, top_k: int | None = None) -> list[SearchResult]:
        """Kullanıcı sorusuna en yakın parçaları kaynak bilgisiyle getirir."""
        clean_query = query.strip()
        if not clean_query or self.count == 0:
            return []
        result = self.collection.query(
            query_texts=[clean_query],
            n_results=min(top_k or self.settings.top_k, self.count),
            include=["documents", "metadatas", "distances"],
        )
        ids = result.get("ids", [[]])[0]
        documents = result.get("documents", [[]])[0]
        metadatas = result.get("metadatas", [[]])[0]
        distances = result.get("distances", [[]])[0]
        matches: list[SearchResult] = []
        for chunk_id, text, metadata, distance in zip(
            ids, documents, metadatas, distances
        ):
            metadata = metadata or {}
            matches.append(
                SearchResult(
                    chunk_id=chunk_id,
                    text=text,
                    source=str(metadata.get("source", "Bilinmeyen kaynak")),
                    page=int(metadata.get("page", 0)) or None,
                    distance=float(distance),
                    metadata=metadata,
                )
            )
        return matches
