"""Placeholder for a future BigQuery Vector Search retrieval backend."""

from __future__ import annotations

from app.retrieval.base import ProductRetriever
from app.retrieval.normalizer import QueryAnalysis
from app.schemas import Product, ProductResult


class BigQueryVectorProductRetriever(ProductRetriever):
    """Unavailable skeleton for a future BigQuery-backed retriever.

    This class intentionally makes no BigQuery, Vertex AI, or external API
    calls. It exists only to define the future architecture boundary.
    """

    def __init__(self, *_: object, **__: object) -> None:
        self._unused_placeholder = None

    def retrieve(
        self,
        query: str,
        products: list[Product],
        top_k: int = 5,
        intent_analysis: QueryAnalysis | None = None,
    ) -> list[ProductResult]:
        raise NotImplementedError(
            "BigQuery Vector Search retrieval is not implemented in the MVP. "
            "It is planned for Stage 8. "
            "Use the local keyword or hybrid retrievers instead."
        )
