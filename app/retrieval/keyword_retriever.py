"""Keyword-based product retrieval backend."""

from __future__ import annotations

from app.retrieval.keyword_search import search_products_by_keywords
from app.retrieval.normalizer import QueryAnalysis, normalize_query
from app.retrieval.results import product_to_result
from app.retrieval.scorer import (
    build_recommendation_reason,
    calculate_final_score,
)
from app.schemas import Product, ProductResult


class KeywordProductRetriever:
    """Deterministic product retriever backed by keyword matching and scoring."""

    def retrieve(
        self,
        query: str,
        products: list[Product],
        top_k: int = 5,
        intent_analysis: QueryAnalysis | None = None,
    ) -> list[ProductResult]:
        """Return deterministic ranked ProductResult objects for a raw query."""

        if top_k < 1:
            return []

        analysis = intent_analysis or normalize_query(query)
        partner_hint = analysis.partner_hint
        category_hints = list(analysis.category_hints)
        price_preference = analysis.price_preference

        keyword_results = search_products_by_keywords(
            query=query,
            products=products,
            top_k=len(products) or top_k,
            partner_hint=partner_hint,
            category_hints=None,
            available_only=True,
        )

        ranked_results = [
            (
                product,
                final_score,
                build_recommendation_reason(
                    product=product,
                    query=query,
                    final_score=final_score,
                    partner_hint=partner_hint,
                    category_hints=category_hints,
                    price_preference=price_preference,
                ),
            )
            for product, keyword_score in keyword_results
            if (
                final_score := calculate_final_score(
                    keyword_score=keyword_score,
                    product=product,
                    query=query,
                    partner_hint=partner_hint,
                    category_hints=category_hints,
                    price_preference=price_preference,
                )
            )
            > 0
        ]
        ranked_results.sort(
            key=lambda item: (
                -item[1],
                -item[0].popularity_score,
                item[0].price,
                item[0].product_id,
            )
        )

        return [
            product_to_result(product, score, reason)
            for product, score, reason in ranked_results[:top_k]
        ]
