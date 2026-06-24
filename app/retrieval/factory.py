"""Factory for selecting product retrieval backends."""

from __future__ import annotations

from app.config import get_settings
from app.retrieval.base import ProductRetriever
from app.retrieval.keyword_retriever import KeywordProductRetriever


def get_product_retriever(backend_name: str | None = None) -> ProductRetriever:
    """Return the configured product retriever backend."""

    selected_backend = (backend_name or get_settings().RETRIEVAL_BACKEND).strip().lower()
    if selected_backend == "keyword":
        return KeywordProductRetriever()
    if selected_backend == "hybrid":
        raise NotImplementedError("Hybrid retrieval backend is not implemented yet.")
    raise ValueError(f"Unsupported retrieval backend: {selected_backend}")
