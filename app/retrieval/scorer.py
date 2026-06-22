"""Deterministic scoring for product recommendations."""

from __future__ import annotations

from app.retrieval.normalizer import normalize_text, tokenize
from app.schemas import Partner, Product


KEYWORD_SCORE_WEIGHT = 0.60
PARTNER_MATCH_BOOST = 0.15
CATEGORY_HINT_BOOST = 0.10
PRICE_PREFERENCE_BOOST = 0.10
PROMOTION_BOOST = 0.03
POPULARITY_BOOST = 0.02
CHEAP_PRICE_REFERENCE_EUR = 100.0
PREMIUM_PRICE_REFERENCE_EUR = 150.0


def calculate_final_score(
    keyword_score: float,
    product: Product,
    query: str,
    partner_hint: Partner | None = None,
    category_hints: list[str] | None = None,
    price_preference: str | None = None,
) -> float:
    """Combine transparent ranking signals into a deterministic 0..1 score."""

    bounded_keyword_score = _clamp(keyword_score)
    final_score = bounded_keyword_score * KEYWORD_SCORE_WEIGHT

    if partner_hint is not None and product.partner == partner_hint:
        final_score += PARTNER_MATCH_BOOST

    if _matches_category_hint(product, category_hints):
        final_score += CATEGORY_HINT_BOOST

    final_score += _final_price_preference_boost(product, price_preference)

    if product.is_promotion:
        final_score += PROMOTION_BOOST

    final_score += _clamp(product.popularity_score) * POPULARITY_BOOST

    if not product.availability:
        final_score *= 0.5

    return round(_clamp(final_score), 4)


def build_recommendation_reason(
    product: Product,
    query: str,
    final_score: float,
    partner_hint: Partner | None = None,
    category_hints: list[str] | None = None,
    price_preference: str | None = None,
) -> str:
    """Build a short deterministic explanation for a recommendation."""

    matched_fields = _query_matched_fields(product, query)
    if matched_fields:
        field_reason = f"Matched query terms in {_format_fields(matched_fields)}."
    else:
        field_reason = "No direct keyword match; ranked by available catalog signals."

    boosts: list[str] = []
    if partner_hint is not None and product.partner == partner_hint:
        boosts.append(f"{product.partner.value} partner")
    if _matches_category_hint(product, category_hints):
        boosts.append("category hint")
    if price_preference == "cheap":
        boosts.append("cheap price preference")
    elif price_preference == "premium":
        boosts.append("premium preference")
    if product.is_promotion:
        boosts.append("promotion")
    if product.popularity_score > 0:
        boosts.append("popularity")

    if boosts:
        return f"{field_reason} Boosted for {', '.join(boosts)}."
    return f"{field_reason} Final score {final_score:.2f}."


def _final_price_preference_boost(
    product: Product,
    price_preference: str | None,
) -> float:
    if price_preference == "cheap":
        relative_cheapness = 1.0 - min(product.price, CHEAP_PRICE_REFERENCE_EUR) / (
            CHEAP_PRICE_REFERENCE_EUR
        )
        return round(max(0.0, relative_cheapness) * PRICE_PREFERENCE_BOOST, 4)
    if price_preference == "premium":
        price_signal = min(product.price, PREMIUM_PRICE_REFERENCE_EUR) / (
            PREMIUM_PRICE_REFERENCE_EUR
        )
        premium_signal = max(price_signal, _clamp(product.popularity_score))
        return round(premium_signal * PRICE_PREFERENCE_BOOST, 4)
    return 0.0


def _matches_category_hint(
    product: Product,
    category_hints: list[str] | None,
) -> bool:
    if not category_hints:
        return False

    normalized_category = normalize_text(product.category)
    normalized_hints = {
        normalize_text(category_hint) for category_hint in category_hints
    }
    return normalized_category in normalized_hints


def _query_matched_fields(product: Product, query: str) -> list[str]:
    query_tokens = set(tokenize(query))
    if not query_tokens:
        return []

    fields = [
        ("product name", f"{product.name} {product.name_de}"),
        ("category", product.category),
        ("product tags", " ".join([*product.tags, *product.tags_de])),
        ("description", f"{product.description} {product.description_de}"),
        ("brand", product.brand),
    ]
    matched_fields: list[str] = []
    for field_name, value in fields:
        if query_tokens & set(tokenize(value)):
            matched_fields.append(field_name)
    return matched_fields


def _format_fields(fields: list[str]) -> str:
    if len(fields) == 1:
        return fields[0]
    if len(fields) == 2:
        return f"{fields[0]} and {fields[1]}"
    return f"{', '.join(fields[:-1])}, and {fields[-1]}"


def _clamp(value: float) -> float:
    return max(0.0, min(value, 1.0))
