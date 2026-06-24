"""Utilities for future embedding-based retrieval."""

from app.embeddings.base import EmbeddingProvider
from app.embeddings.local import LocalHashEmbeddingProvider
from app.embeddings.product_text import build_product_embedding_text
from app.embeddings.similarity import cosine_similarity

__all__ = [
    "EmbeddingProvider",
    "LocalHashEmbeddingProvider",
    "build_product_embedding_text",
    "cosine_similarity",
]
