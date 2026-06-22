from app.intent.language import detect_language
from app.schemas import Language


def test_detect_language_identifies_german_product_query() -> None:
    assert detect_language("Bitte zeige mir g\u00fcnstige Windeln") == Language.DE


def test_detect_language_identifies_german_support_query() -> None:
    assert detect_language("Meine PAYBACK Punkte fehlen") == Language.DE


def test_detect_language_identifies_english_product_query() -> None:
    assert detect_language("Show me cheap diapers") == Language.EN


def test_detect_language_identifies_english_discovery_query() -> None:
    assert detect_language("I need stuff for a pasta dinner") == Language.EN


def test_detect_language_returns_unknown_for_ambiguous_query() -> None:
    assert detect_language("xyz abc") == Language.UNKNOWN
