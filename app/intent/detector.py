"""Deterministic intent and specificity detection helpers."""

from __future__ import annotations

from app.intent.decision import build_clarifying_question
from app.intent.entities import extract_entities
from app.retrieval.normalizer import QueryAnalysis, normalize_text
from app.schemas import (
    Intent,
    IntentDetectionResult,
    NextBestAction,
    Partner,
    QueryEntities,
    Specificity,
)


VAGUE_QUERIES = {
    "angebot",
    "angebote",
    "anything good",
    "co\u015b fajnego",
    "deals",
    "etwas sch\u00f6nes",
    "etwas schoenes",
    "i need something",
    "i need something nice",
    "ich brauche etwas",
    "offers",
    "products",
    "produkte",
    "something nice",
}

VAGUE_WORD_LIMIT = 3

COMPARISON_WORDS = {
    "compare",
    "comparison",
    "versus",
    "vs",
    "vergleiche",
    "vergleich",
}

COMPARISON_PHRASES = {
    "better than",
    "besser als",
    "cheaper than",
    "guenstiger als",
    "gunstiger als",
    "g\u00fcnstiger als",
}

DISCOVERY_WORDS = {
    "abendessen",
    "breakfast",
    "dinner",
    "fruehstueck",
    "fruhstuck",
    "fr\u00fchst\u00fcck",
    "gift",
    "geschenk",
    "idea",
    "ideas",
    "idee",
    "ideen",
    "inspiration",
    "lunch",
    "meal",
    "party",
    "recipe",
    "meals",
    "recommend",
    "recommendation",
    "suggest",
}

DISCOVERY_PHRASES = {
    "i need something for",
    "i need stuff for",
    "ich brauche etwas fuer",
    "ich brauche etwas fur",
    "ich brauche etwas f\u00fcr",
}

SUPPORT_WORDS = {
    "account",
    "erstattung",
    "fehlen",
    "hilfe",
    "konto",
    "login",
    "missing",
    "points",
    "problem",
    "punkte",
    "refund",
    "return",
    "rueckgabe",
    "r\u00fcckgabe",
    "support",
}

SUPPORT_PHRASES = {
    "help with account",
    "missing points",
}

SEARCH_WORDS = {
    "angebote",
    "cheap",
    "diapers",
    "find",
    "guenstige",
    "gunstige",
    "g\u00fcnstige",
    "headphones",
    "kopfhoerer",
    "kopfhorer",
    "kopfh\u00f6rer",
    "search",
    "show",
    "suche",
    "toothpaste",
    "windeln",
    "zahnpasta",
}

SEARCH_PHRASES = {
    "cheap diapers",
    "guenstige windeln",
    "gunstige windeln",
    "g\u00fcnstige windeln",
    "show me",
    "zeige mir",
}


def detect_intent(query: str) -> Intent:
    """Classify a raw query into the public intent enum.

    Priority is deliberate: support requests must not be handled as shopping
    searches, comparisons are more specific than discovery, discovery captures
    broad need/occasion queries, and search is the product-seeking fallback.
    """

    normalized_query = normalize_text(query)
    tokens = frozenset(normalized_query.split()) if normalized_query else frozenset()

    if _matches(tokens, normalized_query, SUPPORT_WORDS, SUPPORT_PHRASES):
        return Intent.CUSTOMER_SUPPORT
    if _matches(tokens, normalized_query, COMPARISON_WORDS, COMPARISON_PHRASES):
        return Intent.COMPARISON
    if _matches(tokens, normalized_query, DISCOVERY_WORDS, DISCOVERY_PHRASES):
        return Intent.DISCOVERY
    if _matches(tokens, normalized_query, SEARCH_WORDS, SEARCH_PHRASES):
        return Intent.SEARCH
    return Intent.UNKNOWN


def determine_specificity(
    analysis: QueryAnalysis,
    intent: Intent | None = None,
    partner_hint: Partner | None = None,
) -> Specificity:
    """Compatibility adapter for callers with precomputed query analysis."""

    return detect_specificity(
        analysis.raw_query,
        partner_hint=partner_hint,
        entities=extract_entities(analysis.raw_query),
    )


def detect_specificity(
    query: str,
    partner_hint: Partner | None = None,
    entities: QueryEntities | None = None,
) -> Specificity:
    """Classify whether a raw query is specific, vague, or navigational."""

    if partner_hint is not None:
        return Specificity.NAVIGATIONAL

    query_entities = entities or extract_entities(query)
    intent = detect_intent(query)

    if intent == Intent.CUSTOMER_SUPPORT:
        return Specificity.SPECIFIC
    if _has_specific_entity(query_entities):
        return Specificity.SPECIFIC
    if _has_clear_search_term(query):
        return Specificity.SPECIFIC
    if _is_vague_query_text(query):
        return Specificity.VAGUE
    if intent == Intent.DISCOVERY and not _has_discovery_context(query_entities):
        return Specificity.VAGUE
    if intent in {Intent.COMPARISON, Intent.SEARCH}:
        return Specificity.SPECIFIC
    if intent == Intent.UNKNOWN:
        return Specificity.UNKNOWN
    return Specificity.SPECIFIC


def with_clarifying_action(
    result: IntentDetectionResult,
    clarifying_question: str | None = None,
) -> IntentDetectionResult:
    """Return a copy of an intent result that asks the user to clarify."""

    question = clarifying_question or build_clarifying_question(
        result.intent,
        result.entities,
        result.language,
    )
    return result.model_copy(
        update={
            "specificity": Specificity.VAGUE,
            "next_best_action": NextBestAction.ASK_CLARIFYING_QUESTION,
            "requires_clarification": True,
            "clarifying_question": question,
        }
    )


def _is_vague_query(analysis: QueryAnalysis) -> bool:
    if analysis.normalized_query in VAGUE_QUERIES:
        return True
    return not analysis.search_tokens


def _is_vague_query_text(query: str) -> bool:
    normalized_query = normalize_text(query)
    if normalized_query in VAGUE_QUERIES:
        return True
    tokens = normalized_query.split() if normalized_query else []
    if len(tokens) <= VAGUE_WORD_LIMIT:
        entities = extract_entities(query)
        return not _has_specific_entity(entities) and not _has_clear_search_term(query)
    return False


def _has_specific_entity(entities: QueryEntities) -> bool:
    return any(
        (
            entities.product_category,
            entities.brand,
            entities.dietary_preference,
        )
    )


def _has_discovery_context(entities: QueryEntities) -> bool:
    return any(
        (
            entities.occasion,
            entities.product_category,
            entities.dietary_preference,
        )
    )


def _has_clear_search_term(query: str) -> bool:
    normalized_query = normalize_text(query)
    tokens = frozenset(normalized_query.split()) if normalized_query else frozenset()
    return _matches(tokens, normalized_query, SEARCH_WORDS, SEARCH_PHRASES)


def _matches(
    tokens: frozenset[str],
    normalized_query: str,
    word_rules: set[str],
    phrase_rules: set[str],
) -> bool:
    return bool(tokens & word_rules) or _contains_phrase(normalized_query, phrase_rules)


def _contains_phrase(normalized_query: str, phrase_rules: set[str]) -> bool:
    padded_query = f" {normalized_query} "
    return any(f" {phrase} " in padded_query for phrase in phrase_rules)
