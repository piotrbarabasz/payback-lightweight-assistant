"""Entity extraction for the deterministic intent detector."""

from __future__ import annotations

from collections.abc import Iterable

from app.retrieval.normalizer import QueryAnalysis, normalize_text
from app.schemas import Partner, QueryEntities


PARTNER_HINTS: dict[str, Partner] = {
    "amazon": Partner.AMAZON,
    "dm": Partner.DM,
    "edeka": Partner.EDEKA,
}


PRODUCT_CATEGORY_RULES: tuple[tuple[str, set[str]], ...] = (
    ("baby care", {"baby", "diapers", "windeln"}),
    ("pasta and grains", {"nudeln", "pasta", "spaghetti"}),
    ("dairy", {"dairy", "milch", "milk"}),
    ("electronics", {"headphones", "kopfhoerer", "kopfhorer", "kopfh\u00f6rer"}),
    ("electronics", {"maus", "mouse"}),
    ("oral care", {"toothpaste", "zahnpasta"}),
    ("hair care", {"haarpflege", "shampoo"}),
    ("fresh produce", {"tomaten", "tomato", "tomatoes"}),
)

PRICE_PREFERENCE_RULES: tuple[tuple[str, set[str]], ...] = (
    (
        "cheap",
        {
            "affordable",
            "billig",
            "budget",
            "cheap",
            "cheaper",
            "guenstig",
            "guenstige",
            "gunstig",
            "gunstige",
            "g\u00fcnstig",
            "g\u00fcnstige",
            "preiswert",
        },
    ),
    ("premium", {"best", "beste", "hochwertig", "premium"}),
)

PREMIUM_PHRASE_RULES = {"high quality"}

OCCASION_RULES: tuple[tuple[str, set[str]], ...] = (
    ("dinner", {"abendessen", "dinner"}),
    ("breakfast", {"breakfast", "fruehstueck", "fruhstuck", "fr\u00fchst\u00fcck"}),
    ("lunch", {"lunch", "mittagessen"}),
    ("party", {"party"}),
    ("baby care", {"baby", "child", "kind"}),
)

DIETARY_PREFERENCE_RULES: tuple[tuple[str, set[str]], ...] = (
    ("organic", {"bio", "organic"}),
    ("vegetarian", {"vegetarian", "vegetarisch"}),
    ("vegan", {"vegan"}),
)

DEFAULT_BRAND_HINTS = (
    "pampers",
    "nivea",
    "colgate",
    "barilla",
    "samsung",
    "apple",
    "sony",
)


def extract_entities(query: str) -> QueryEntities:
    """Extract basic structured entities from a raw user query."""

    normalized_query = normalize_text(query)
    tokens = frozenset(normalized_query.split()) if normalized_query else frozenset()

    return QueryEntities(
        product_category=_first_matching_rule(tokens, PRODUCT_CATEGORY_RULES),
        price_preference=_detect_price_preference(normalized_query, tokens),
        occasion=_first_matching_rule(tokens, OCCASION_RULES),
        dietary_preference=_first_matching_rule(tokens, DIETARY_PREFERENCE_RULES),
        brand=_detect_brand_from_normalized_query(normalized_query, DEFAULT_BRAND_HINTS),
    )


def detect_partner_hint(query: str) -> Partner | None:
    """Detect supported partner names from raw query text."""

    normalized_query = normalize_text(query)
    if not normalized_query:
        return None

    tokens = normalized_query.split()
    for token in tokens:
        partner = PARTNER_HINTS.get(token)
        if partner is not None:
            return partner
    return None


def extract_query_entities(
    analysis: QueryAnalysis,
    known_brands: Iterable[str] | None = None,
) -> QueryEntities:
    """Compatibility adapter for callers that already normalized the query."""

    return QueryEntities(
        product_category=_first_matching_rule(
            analysis.expanded_tokens,
            PRODUCT_CATEGORY_RULES,
        ),
        price_preference=_detect_price_preference(
            analysis.normalized_query,
            analysis.expanded_tokens,
        ),
        occasion=_first_matching_rule(analysis.expanded_tokens, OCCASION_RULES),
        dietary_preference=_first_matching_rule(
            analysis.expanded_tokens,
            DIETARY_PREFERENCE_RULES,
        ),
        brand=_detect_brand_from_normalized_query(
            analysis.normalized_query,
            known_brands or DEFAULT_BRAND_HINTS,
        ),
    )


def detect_occasion(analysis: QueryAnalysis) -> str | None:
    """Return a normalized meal or occasion hint when one is present."""

    return _first_matching_rule(analysis.expanded_tokens, OCCASION_RULES)


def detect_dietary_preference(analysis: QueryAnalysis) -> str | None:
    """Return a normalized dietary preference when one is present."""

    return _first_matching_rule(analysis.expanded_tokens, DIETARY_PREFERENCE_RULES)


def detect_brand(
    analysis: QueryAnalysis,
    known_brands: Iterable[str] | None = None,
) -> str | None:
    """Detect explicit brand mentions from a configured deterministic list."""

    return _detect_brand_from_normalized_query(
        analysis.normalized_query,
        known_brands or DEFAULT_BRAND_HINTS,
    )


def _detect_price_preference(
    normalized_query: str,
    tokens: Iterable[str],
) -> str | None:
    if _contains_phrase(normalized_query, PREMIUM_PHRASE_RULES):
        return "premium"
    return _first_matching_rule(tokens, PRICE_PREFERENCE_RULES)


def _first_matching_rule(
    tokens: Iterable[str],
    rules: tuple[tuple[str, set[str]], ...],
) -> str | None:
    token_set = set(tokens)
    for value, rule_tokens in rules:
        if token_set & rule_tokens:
            return value
    return None


def _detect_brand_from_normalized_query(
    normalized_query: str,
    known_brands: Iterable[str],
) -> str | None:
    padded_query = f" {normalized_query} "
    for brand in sorted(known_brands, key=lambda value: (-len(value), value.casefold())):
        normalized_brand = normalize_text(brand)
        if normalized_brand and f" {normalized_brand} " in padded_query:
            return normalized_brand
    return None


def _contains_phrase(normalized_query: str, phrase_rules: set[str]) -> bool:
    padded_query = f" {normalized_query} "
    return any(f" {phrase} " in padded_query for phrase in phrase_rules)
