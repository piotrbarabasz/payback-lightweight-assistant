"""Placeholder for a future Vertex AI embedding provider."""

from __future__ import annotations

from app.embeddings.base import EmbeddingProvider


class VertexAIEmbeddingProvider(EmbeddingProvider):
    """Unavailable skeleton for a future managed embedding provider.

    This class intentionally makes no Vertex AI, Gemini, or other external API
    calls. It exists only to make the future architecture boundary explicit.
    """

    def __init__(self, *_: object, **__: object) -> None:
        self._unused_placeholder = None

    def embed_text(self, text: str) -> list[float]:
        raise NotImplementedError(
            "Vertex AI embeddings are not implemented in the MVP. "
            "Use the local deterministic embedding provider instead."
        )
