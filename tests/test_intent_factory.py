import pytest

from app.config import get_settings
from app.intent.base import BaseIntentDetector
from app.intent.factory import get_intent_detector
from app.intent.rule_based import RuleBasedIntentDetector
from app.intent.vertex_placeholder import FutureVertexIntentDetector
from app.schemas import Intent, Language, NextBestAction


@pytest.fixture(autouse=True)
def clear_settings_cache():
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_get_intent_detector_defaults_to_rules(monkeypatch) -> None:
    monkeypatch.delenv("INTENT_BACKEND", raising=False)

    detector = get_intent_detector()

    assert isinstance(detector, RuleBasedIntentDetector)
    assert isinstance(detector, BaseIntentDetector)


def test_get_intent_detector_uses_explicit_rules_config(monkeypatch) -> None:
    monkeypatch.setenv("INTENT_BACKEND", "rules")

    detector = get_intent_detector()

    assert isinstance(detector, RuleBasedIntentDetector)


def test_get_intent_detector_accepts_rules_backend_argument() -> None:
    detector = get_intent_detector("rules")

    assert isinstance(detector, RuleBasedIntentDetector)


def test_get_intent_detector_accepts_vertex_placeholder_backend_argument() -> None:
    detector = get_intent_detector("vertex_placeholder")

    assert isinstance(detector, FutureVertexIntentDetector)
    assert isinstance(detector, BaseIntentDetector)


def test_get_intent_detector_rejects_unsupported_backend() -> None:
    with pytest.raises(ValueError, match="Unsupported intent backend: llm"):
        get_intent_detector("llm")


def test_rule_based_detector_preserves_german_search_behavior() -> None:
    result = RuleBasedIntentDetector().analyze(
        "Bitte zeige mir Angebote fuer guenstige Windeln"
    )

    assert result.language == Language.DE
    assert result.intent == Intent.SEARCH
    assert result.next_best_action == NextBestAction.SEARCH_CATALOG
    assert result.entities.product_category == "baby care"
    assert result.entities.price_preference == "cheap"


def test_rule_based_detector_preserves_english_discovery_behavior() -> None:
    result = RuleBasedIntentDetector().analyze("I need stuff for a pasta dinner")

    assert result.language == Language.EN
    assert result.intent == Intent.DISCOVERY
    assert result.next_best_action == NextBestAction.SEARCH_CATALOG
    assert result.entities.occasion == "dinner"


def test_vertex_placeholder_makes_no_external_call_and_fails_clearly() -> None:
    detector = FutureVertexIntentDetector()

    with pytest.raises(
        NotImplementedError,
        match="INTENT_BACKEND=vertex_placeholder is not implemented",
    ):
        detector.analyze("Show me headphones on Amazon")
