"""Yerel metin embedding'i.

Öncelik SentenceTransformers ile gerçek anlamsal embedding'dedir. Model ilk
çalıştırmada indirilebilir; sonrasında embedding çıkarımı yerel yapılır.
Kurumsal ağ veya model kurulumu olmayan ortamlarda uygulamanın açılabilmesi
ve test edilebilmesi için TF-benzeri deterministik hashing yedeği bulunur.
"""
from __future__ import annotations

import hashlib
import re
from typing import Sequence

import numpy as np


class LocalEmbeddingFunction:
    """ChromaDB ile uyumlu, yerel embedding fonksiyonu."""

    def __init__(self, model_name: str, dimensions: int = 384) -> None:
        self.model_name = model_name
        self.dimensions = dimensions
        self._model = None
        self.backend = "hashing"
        try:
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(model_name)
            self.backend = "sentence-transformers"
        except Exception:
            # Model indirilememesi uygulamayı durdurmamalıdır. Hashing yedeği
            # tamamen yerel ve dış servissiz çalışır.
            self._model = None

    def name(self) -> str:
        """ChromaDB v1.x embedding function kimliği."""
        return f"local-{self.backend}-{self.model_name}"

    def get_config(self) -> dict[str, str | int]:
        """ChromaDB tarafından teşhis ve yapılandırma için kullanılabilir ayarlar."""
        return {
            "model_name": self.model_name,
            "dimensions": self.dimensions,
            "backend": self.backend,
        }

    def __call__(self, input: Sequence[str]) -> list[list[float]]:
        texts = [str(item) for item in input]
        if self._model is not None:
            vectors = self._model.encode(
                texts,
                normalize_embeddings=True,
                show_progress_bar=False,
            )
            return np.asarray(vectors, dtype=np.float32).tolist()
        return [self._hash_embedding(text) for text in texts]

    def embed_query(self, input: str) -> list[list[float]]:
        return self([input])

    def _hash_embedding(self, text: str) -> list[float]:
        vector = np.zeros(self.dimensions, dtype=np.float32)
        tokens = re.findall(r"[\wçğıöşüÇĞİÖŞÜ@./:-]+", text.lower())
        if not tokens:
            return vector.tolist()
        for token in tokens:
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            index = int.from_bytes(digest[:4], "big") % self.dimensions
            sign = 1.0 if digest[4] % 2 else -1.0
            vector[index] += sign
        norm = float(np.linalg.norm(vector))
        if norm:
            vector /= norm
        return vector.tolist()
