from app.intent.detector import detect_intent, detect_specificity
from app.intent.entities import detect_partner_hint
from app.schemas import Intent, Specificity


def test_detect_intent_customer_support_query() -> None:
    assert detect_intent("Meine PAYBACK Punkte fehlen") == Intent.CUSTOMER_SUPPORT


def test_detect_intent_english_comparison_query() -> None:
    assert detect_intent("Compare cheap organic milk options") == Intent.COMPARISON


def test_detect_intent_german_comparison_query() -> None:
    assert detect_intent("Vergleiche Bio-Milch und normale Milch") == Intent.COMPARISON


def test_detect_intent_discovery_query() -> None:
    assert detect_intent("I need stuff for a pasta dinner") == Intent.DISCOVERY


def test_detect_intent_german_search_query() -> None:
    assert detect_intent("Bitte zeige mir g\u00fcnstige Windeln") == Intent.SEARCH


def test_detect_intent_english_navigational_search_query() -> None:
    assert detect_intent("Show me headphones on Amazon") == Intent.SEARCH


def test_detect_specificity_partner_query_is_navigational() -> None:
    query = "Show me headphones on Amazon"

    assert detect_specificity(
        query,
        partner_hint=detect_partner_hint(query),
    ) == Specificity.NAVIGATIONAL


def test_detect_specificity_vague_query() -> None:
    assert detect_specificity("Something nice") == Specificity.VAGUE


def test_detect_specificity_product_query_is_specific() -> None:
    assert detect_specificity("g\u00fcnstige Windeln") == Specificity.SPECIFIC


def test_detect_specificity_support_query_is_specific() -> None:
    assert detect_specificity("Meine PAYBACK Punkte fehlen") == Specificity.SPECIFIC
