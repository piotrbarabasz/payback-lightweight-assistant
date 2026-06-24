"""Base retrieval interfaces."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from app.retrieval.normalizer import QueryAnalysis
from app.schemas import Product, ProductResult


@runtime_checkable
class ProductRetriever(Protocol):
    """Protocol implemented by product retrieval backends."""

    def retrieve(
        self,
        query: str,
        products: list[Product],
        top_k: int = 5,
        intent_analysis: QueryAnalysis | None = None,
    ) -> list[ProductResult]:
        """Return ranked product recommendations for a raw query."""
