"""Deterministic keyword matching over catalog products."""

from __future__ import annotations

from app.retrieval.normalizer import (
    STOP_WORDS,
    normalize_query,
    normalize_text,
    tokenize,
)
from app.schemas import Partner, Product


STRONG_FIELD_WEIGHT = 1.0
BRAND_FIELD_WEIGHT = 0.7
DESCRIPTION_FIELD_WEIGHT = 0.35
CATEGORY_HINT_BOOST = 0.15


def product_search_text(product: Product) -> str:
    """Return normalized searchable text for all retrieval-relevant fields."""

    return normalize_text(
        " ".join(
            [
                product.name,
                product.name_de,
                product.category,
                product.description,
                product.description_de,
                product.brand,
                *product.tags,
                *product.tags_de,
            ]
        )
    )


def keyword_match_score(query: str, product: Product) -> float:
    """Return a deterministic 0..1 keyword overlap score for one product."""

    query_tokens = _query_tokens_for_keyword_score(query)
    if not query_tokens:
        return 0.0

    field_token_weights = _field_token_weights(product)
    matched_weight = sum(
        field_token_weights.get(token, 0.0) for token in query_tokens
    )
    return min(round(matched_weight / len(query_tokens), 4), 1.0)


def search_products_by_keywords(
    query: str,
    products: list[Product],
    top_k: int = 5,
    partner_hint: Partner | None = None,
    category_hints: list[str] | None = None,
    available_only: bool = True,
) -> list[tuple[Product, float]]:
    """Search products with deterministic keyword overlap scoring."""

    if top_k < 1:
        return []

    candidates = list(products)
    if available_only:
        candidates = [product for product in candidates if product.availability]
    if partner_hint is not None:
        candidates = [product for product in candidates if product.partner == partner_hint]

    scored_products = [
        (
            product,
            _score_with_category_boost(
                keyword_match_score(query, product),
                product,
                category_hints or [],
            ),
        )
        for product in candidates
    ]
    positive_matches = [
        (product, score) for product, score in scored_products if score > 0
    ]
    results = positive_matches or scored_products
    results.sort(
        key=lambda item: (
            -item[1],
            -item[0].popularity_score,
            item[0].price,
            item[0].product_id,
        )
    )
    return results[:top_k]


def _query_tokens_for_keyword_score(query: str) -> frozenset[str]:
    analysis = normalize_query(query)
    tokens = analysis.search_tokens or tuple(tokenize(query))
    return frozenset(token for token in tokens if token not in STOP_WORDS)


def _field_token_weights(product: Product) -> dict[str, float]:
    token_weights: dict[str, float] = {}
    for token in _tokens_for_fields(
        product.name,
        product.name_de,
        product.category,
        *product.tags,
        *product.tags_de,
    ):
        token_weights[token] = max(
            token_weights.get(token, 0.0),
            STRONG_FIELD_WEIGHT,
        )
    for token in _tokens_for_fields(product.brand):
        token_weights[token] = max(
            token_weights.get(token, 0.0),
            BRAND_FIELD_WEIGHT,
        )
    for token in _tokens_for_fields(product.description, product.description_de):
        token_weights[token] = max(
            token_weights.get(token, 0.0),
            DESCRIPTION_FIELD_WEIGHT,
        )
    return token_weights


def _tokens_for_fields(*values: str) -> frozenset[str]:
    return frozenset(token for value in values for token in tokenize(value))


def _score_with_category_boost(
    base_score: float,
    product: Product,
    category_hints: list[str],
) -> float:
    if not category_hints:
        return base_score

    normalized_category = normalize_text(product.category)
    normalized_hints = {
        normalize_text(category_hint) for category_hint in category_hints
    }
    if normalized_category in normalized_hints:
        return min(round(base_score + CATEGORY_HINT_BOOST, 4), 1.0)
    return base_score
