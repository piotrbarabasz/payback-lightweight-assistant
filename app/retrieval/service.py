"""API-independent retrieval service for ranked product recommendations."""

from __future__ import annotations

from app.retrieval.keyword_retriever import KeywordProductRetriever
from app.retrieval.results import category_hint_from_results, product_to_result
from app.schemas import Product, ProductResult


_DEFAULT_RETRIEVER = KeywordProductRetriever()


def retrieve_products(
    query: str,
    products: list[Product],
    top_k: int = 5,
) -> list[ProductResult]:
    """Return deterministic ranked ProductResult objects for a raw query."""

    return _DEFAULT_RETRIEVER.retrieve(query, products, top_k=top_k)


__all__ = [
    "category_hint_from_results",
    "product_to_result",
    "retrieve_products",
]
