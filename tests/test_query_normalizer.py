from app.retrieval.normalizer import (
    detect_basic_category_hints,
    detect_partner_hint,
    detect_price_preference,
    is_support_query,
    normalize_query,
    normalize_text,
    tokenize,
)
from app.schemas import Language, Partner


def test_normalize_text_handles_case_punctuation_spacing_and_umlauts() -> None:
    normalized_text = normalize_text("  Show me CHEAP diapers!!!  ")

    assert "show me cheap diapers" in normalized_text
    assert normalized_text == "show me cheap diapers"


def test_tokenize_returns_non_empty_german_and_english_tokens() -> None:
    assert tokenize("  Show me CHEAP diapers!!!  ") == [
        "show",
        "me",
        "cheap",
        "diapers",
    ]


def test_detect_price_preference_detects_cheap_words() -> None:
    assert detect_price_preference("cheap diapers") == "cheap"
    assert detect_price_preference("affordable shampoo") == "cheap"
    assert detect_price_preference("g\u00fcnstig zahnpasta") == "cheap"
    assert detect_price_preference("billig windeln") == "cheap"


def test_detect_price_preference_detects_premium_words() -> None:
    assert detect_price_preference("premium headphones") == "premium"
    assert detect_price_preference("hochwertig zahnpasta") == "premium"
    assert detect_price_preference("pasta") is None


def test_detect_partner_hint_detects_supported_partners() -> None:
    assert detect_partner_hint("Angebote bei dm") == Partner.DM
    assert detect_partner_hint("Show me EDEKA pasta") == Partner.EDEKA
    assert detect_partner_hint("Amazon headphones") == Partner.AMAZON
    assert detect_partner_hint("Show me pasta") is None


def test_detect_basic_category_hints_detects_required_examples() -> None:
    assert detect_basic_category_hints("Windeln") == ["baby care"]
    assert detect_basic_category_hints("pasta") == ["pasta and grains"]
    assert detect_basic_category_hints("Kopfh\u00f6rer") == ["electronics"]
    assert detect_basic_category_hints("Zahnpasta") == ["oral care"]


def test_normalize_query_detects_german_partner_and_price_preference() -> None:
    analysis = normalize_query("G\u00fcnstige Kopfh\u00f6rer bei Amazon bitte")

    assert analysis.language == Language.DE
    assert analysis.partner_hint == Partner.AMAZON
    assert analysis.price_preference == "cheap"
    assert "headphones" in analysis.expanded_tokens
    assert "cheap" in analysis.expanded_tokens
    assert analysis.category_hints == ("electronics",)


def test_support_query_requires_account_or_points_context() -> None:
    support_analysis = normalize_query("Meine PAYBACK Punkte fehlen")
    shopping_analysis = normalize_query("PAYBACK Angebote fuer Windeln")

    assert is_support_query(support_analysis) is True
    assert is_support_query(shopping_analysis) is False
