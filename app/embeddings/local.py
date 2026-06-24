"""Local deterministic embedding providers."""

from __future__ import annotations

import hashlib
import math
import re


TOKEN_PATTERN = re.compile(r"\w+", flags=re.UNICODE)
DEFAULT_EMBEDDING_DIMENSIONS = 64


class LocalHashEmbeddingProvider:
    """Small deterministic feature-hashing embedding provider."""

    def __init__(self, dimensions: int = DEFAULT_EMBEDDING_DIMENSIONS) -> None:
        if dimensions < 1:
            raise ValueError("dimensions must be at least 1")
        self.dimensions = dimensions

    def embed_text(self, text: str) -> list[float]:
        """Embed text locally using normalized token feature hashing."""

        vector = [0.0] * self.dimensions
        for token in _tokens(text):
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            bucket = int.from_bytes(digest[:4], "big") % self.dimensions
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            vector[bucket] += sign

        return _l2_normalize(vector)


def _tokens(text: str) -> list[str]:
    if not text:
        return []
    return TOKEN_PATTERN.findall(text.casefold())


def _l2_normalize(vector: list[float]) -> list[float]:
    norm = math.sqrt(sum(value * value for value in vector))
    if norm == 0:
        return vector
    return [value / norm for value in vector]
