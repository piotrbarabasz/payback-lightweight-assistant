"""Helpers for mapping ranked catalog products into API result objects."""

from __future__ import annotations

from app.retrieval.normalizer import normalize_text
from app.schemas import Product, ProductResult


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
