from __future__ import annotations

import hashlib
import math
from functools import cached_property

from app.core.config import get_settings


class EmbeddingService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.dimension = 64
        self.provider = "hashing-fallback"

    @cached_property
    def _model(self):  # noqa: ANN202
        try:
            from sentence_transformers import SentenceTransformer

            model = SentenceTransformer(self.settings.sentence_transformer_model)
            self.provider = self.settings.sentence_transformer_model
            vector = model.encode(["健康检查"], normalize_embeddings=True)
            self.dimension = len(vector[0])
            return model
        except Exception:
            return None

    def embed(self, texts: list[str]) -> list[list[float]]:
        if self._model is not None:
            vectors = self._model.encode(texts, normalize_embeddings=True)
            return [list(map(float, vector)) for vector in vectors]
        return [self._hash_vector(text) for text in texts]

    def _hash_vector(self, text: str) -> list[float]:
        digest = hashlib.sha256(text.encode("utf-8")).digest()
        vector: list[float] = []
        while len(vector) < self.dimension:
            for byte in digest:
                vector.append((byte / 255.0) * 2 - 1)
                if len(vector) == self.dimension:
                    break
            digest = hashlib.sha256(digest).digest()
        norm = math.sqrt(sum(value * value for value in vector)) or 1.0
        return [value / norm for value in vector]
