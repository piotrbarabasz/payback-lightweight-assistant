"""Local semantic product retrieval prototype."""

from __future__ import annotations

from app.embeddings import (
    EmbeddingProvider,
    LocalHashEmbeddingProvider,
    build_product_embedding_text,
    cosine_similarity,
)
from app.retrieval.normalizer import QueryAnalysis
from app.retrieval.results import product_to_result
from app.schemas import Product, ProductResult


class SemanticProductRetriever:
    """Product retriever based on local deterministic embedding similarity."""

    def __init__(self, embedding_provider: EmbeddingProvider | None = None) -> None:
        self.embedding_provider = embedding_provider or LocalHashEmbeddingProvider()

    def retrieve(
        self,
        query: str,
        products: list[Product],
        top_k: int = 5,
        intent_analysis: QueryAnalysis | None = None,
    ) -> list[ProductResult]:
        """Return product recommendations ranked by local semantic similarity."""

        if top_k < 1 or not products:
            return []

        query_embedding = self.embedding_provider.embed_text(query)
        ranked_products = [
            (
                product,
                max(
                    0.0,
                    cosine_similarity(
                        query_embedding,
                        self.embedding_provider.embed_text(
                            build_product_embedding_text(product)
                        ),
                    ),
                ),
            )
            for product in products
        ]
        ranked_products.sort(
            key=lambda item: (
                -item[1],
                -item[0].popularity_score,
                item[0].price,
                item[0].product_id,
            )
        )

        return [
            product_to_result(
                product,
                score,
                f"Ranked by local semantic similarity score {score:.2f}.",
            )
            for product, score in ranked_products[:top_k]
        ]
