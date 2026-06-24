"""Hybrid product retrieval using keyword and local semantic signals."""

from __future__ import annotations

from app.embeddings import (
    EmbeddingProvider,
    LocalHashEmbeddingProvider,
    build_product_embedding_text,
    cosine_similarity,
)
from app.retrieval.keyword_search import search_products_by_keywords
from app.retrieval.normalizer import QueryAnalysis, normalize_query
from app.retrieval.results import product_to_result
from app.retrieval.scorer import calculate_final_score
from app.schemas import Product, ProductResult


KEYWORD_SIGNAL_WEIGHT = 0.45
SEMANTIC_SIGNAL_WEIGHT = 0.25


class HybridProductRetriever:
    """Retriever combining keyword score, semantic similarity, and business boosts."""

    def __init__(self, embedding_provider: EmbeddingProvider | None = None) -> None:
        self.embedding_provider = embedding_provider or LocalHashEmbeddingProvider()

    def retrieve(
        self,
        query: str,
        products: list[Product],
        top_k: int = 5,
        intent_analysis: QueryAnalysis | None = None,
    ) -> list[ProductResult]:
        """Return products ranked by explainable hybrid retrieval signals."""

        if top_k < 1 or not products:
            return []

        analysis = intent_analysis or normalize_query(query)
        partner_hint = analysis.partner_hint
        category_hints = list(analysis.category_hints)
        price_preference = analysis.price_preference
        query_embedding = self.embedding_provider.embed_text(query)

        keyword_results = search_products_by_keywords(
            query=query,
            products=products,
            top_k=len(products) or top_k,
            partner_hint=partner_hint,
            category_hints=None,
            available_only=True,
        )

        ranked_results = []
        for product, keyword_score in keyword_results:
            semantic_score = max(
                0.0,
                cosine_similarity(
                    query_embedding,
                    self.embedding_provider.embed_text(
                        build_product_embedding_text(product)
                    ),
                ),
            )
            business_boost_score = calculate_final_score(
                keyword_score=0.0,
                product=product,
                query=query,
                partner_hint=partner_hint,
                category_hints=category_hints,
                price_preference=price_preference,
            )
            hybrid_score = min(
                1.0,
                round(
                    (keyword_score * KEYWORD_SIGNAL_WEIGHT)
                    + (semantic_score * SEMANTIC_SIGNAL_WEIGHT)
                    + business_boost_score,
                    4,
                ),
            )
            if hybrid_score > 0:
                ranked_results.append(
                    (
                        product,
                        hybrid_score,
                        _build_hybrid_reason(
                            keyword_score,
                            semantic_score,
                            business_boost_score,
                        ),
                    )
                )

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


def _build_hybrid_reason(
    keyword_score: float,
    semantic_score: float,
    business_boost_score: float,
) -> str:
    signals: list[str] = []
    if keyword_score > 0:
        signals.append(f"keyword score {keyword_score:.2f}")
    if semantic_score > 0:
        signals.append(f"semantic similarity {semantic_score:.2f}")
    if business_boost_score > 0:
        signals.append(f"business boosts {business_boost_score:.2f}")

    if not signals:
        return "Ranked by hybrid retrieval with no positive matching signal."
    return f"Ranked by hybrid retrieval using {', '.join(signals)}."
