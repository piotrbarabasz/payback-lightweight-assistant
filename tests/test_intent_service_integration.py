from app.intent.service import analyze_query_intent
from app.schemas import (
    Intent,
    Language,
    NextBestAction,
    Partner,
    Specificity,
)


def test_analyze_query_intent_german_diaper_query() -> None:
    result = analyze_query_intent("Bitte zeige mir Angebote f\u00fcr g\u00fcnstige Windeln")

    assert result.language == Language.DE
    assert result.intent == Intent.SEARCH
    assert result.specificity == Specificity.SPECIFIC
    assert result.next_best_action == NextBestAction.SEARCH_CATALOG
    assert result.entities.product_category == "baby care"
    assert result.entities.price_preference == "cheap"


def test_analyze_query_intent_english_pasta_dinner_query() -> None:
    result = analyze_query_intent("I need stuff for a pasta dinner")

    assert result.language == Language.EN
    assert result.intent == Intent.DISCOVERY
    assert result.next_best_action == NextBestAction.SEARCH_CATALOG
    assert result.entities.occasion == "dinner"


def test_analyze_query_intent_amazon_headphones_query() -> None:
    result = analyze_query_intent("Show me headphones on Amazon")

    assert result.partner_hint == Partner.AMAZON
    assert result.specificity == Specificity.NAVIGATIONAL
    assert result.next_best_action == NextBestAction.PARTNER_SPECIFIC_SEARCH


def test_analyze_query_intent_german_support_query_has_no_results_field() -> None:
    result = analyze_query_intent("Meine PAYBACK Punkte fehlen")

    assert result.language == Language.DE
    assert result.intent == Intent.CUSTOMER_SUPPORT
    assert result.next_best_action == NextBestAction.ROUTE_TO_SUPPORT
    assert not hasattr(result, "results")


def test_analyze_query_intent_vague_query_requires_clarification() -> None:
    result = analyze_query_intent("Something nice")

    assert result.specificity == Specificity.VAGUE
    assert result.next_best_action == NextBestAction.ASK_CLARIFYING_QUESTION
    assert result.requires_clarification is True
    assert result.clarifying_question is not None
    assert result.clarifying_question.strip()


def test_analyze_query_intent_unknown_query_does_not_crash() -> None:
    result = analyze_query_intent("xyz abc qwerty")

    assert result.next_best_action in {
        NextBestAction.FALLBACK,
        NextBestAction.ASK_CLARIFYING_QUESTION,
    }
