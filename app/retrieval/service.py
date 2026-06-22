"""API-independent retrieval service for ranked product recommendations."""

from __future__ import annotations

from app.retrieval.keyword_search import search_products_by_keywords
from app.retrieval.normalizer import (
    normalize_query,
    normalize_text,
)
from app.retrieval.scorer import (
    build_recommendation_reason,
    calculate_final_score,
)
from app.schemas import Product, ProductResult


def retrieve_products(
    query: str,
    products: list[Product],
    top_k: int = 5,
) -> list[ProductResult]:
    """Return deterministic ranked ProductResult objects for a raw query."""

    if top_k < 1:
        return []

    analysis = normalize_query(query)
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


def product_to_result(
    product: Product,
    score: float,
    reason: str,
) -> ProductResult:
    """Map a catalog Product and retrieval metadata into ProductResult."""

    return ProductResult(
        product_id=product.product_id,
        partner=product.partner,
        name=product.name,
        category=product.category,
        price=product.price,
        currency=product.currency,
        score=max(0.0, min(round(score, 4), 1.0)),
        reason=reason,
    )


def category_hint_from_results(results: list[ProductResult]) -> str | None:
    """Infer a simple category hint from ranked result categories."""

    if not results:
        return None

    first_category = results[0].category
    if all(
        normalize_text(result.category) == normalize_text(first_category)
        for result in results
    ):
        return first_category
    return None
