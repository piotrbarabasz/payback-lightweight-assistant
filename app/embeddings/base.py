"""Base embedding provider interfaces."""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class EmbeddingProvider(Protocol):
    """Protocol implemented by text embedding providers."""

    def embed_text(self, text: str) -> list[float]:
        """Return a deterministic embedding vector for text."""

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Return embedding vectors for a batch of texts."""
