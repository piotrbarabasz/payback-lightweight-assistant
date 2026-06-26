from __future__ import annotations

import json

import pytest

from app.intent.vertex_llm import (
    VertexLLMIntentConfig,
    VertexLLMIntentDetector,
)
from app.config import get_settings
from app.schemas import Intent, Language, NextBestAction, Partner, Specificity


CONFIG = VertexLLMIntentConfig(
    project_id="payback-test",
    location="europe-west1",
    model="gemini-test",
    timeout_seconds=1,
)


class FakeResponse:
    def __init__(self, text: str) -> None:
        self.text = text


class FakeModels:
    def __init__(
        self,
        response: FakeResponse | None = None,
        *,
        error: Exception | None = None,
    ) -> None:
        self.response = response
        self.error = error
        self.calls: list[dict[str, object]] = []

    def generate_content(self, **kwargs: object) -> FakeResponse:
        self.calls.append(kwargs)
        if self.error is not None:
            raise self.error
        if self.response is None:
            raise RuntimeError("missing fake response")
        return self.response


class FakeClient:
    def __init__(self, models: FakeModels) -> None:
        self.models = models


def payload_json(**overrides: object) -> str:
    payload = {
        "language": "en",
        "intent": "search",
        "specificity": "specific",
        "next_best_action": "search_catalog",
        "partner_hint": "unknown",
        "entities": {
            "product_category": "baby care",
            "price_preference": None,
            "occasion": None,
            "dietary_preference": None,
            "brand": None,
        },
        "clarifying_question": None,
    }
    payload.update(overrides)
    return json.dumps(payload)


def detector_for(response_text: str | None = None, *, error: Exception | None = None):
    models = FakeModels(
        response=FakeResponse(response_text or payload_json()),
        error=error,
    )
    detector = VertexLLMIntentDetector(
        CONFIG,
        client=FakeClient(models),
        generate_config_factory=lambda config: {
            "temperature": 0,
            "model": config.model,
        },
    )
    return detector, models


def test_valid_json_response_is_parsed_correctly() -> None:
    detector, models = detector_for()

    result = detector.analyze("Show me baby diapers")

    assert result.query == "Show me baby diapers"
    assert result.language == Language.EN
    assert result.intent == Intent.SEARCH
    assert result.specificity == Specificity.SPECIFIC
    assert result.next_best_action == NextBestAction.SEARCH_CATALOG
    assert result.partner_hint == Partner.UNKNOWN
    assert result.entities.product_category == "baby care"
    assert result.confidence == pytest.approx(0.8)
    assert models.calls[0]["model"] == "gemini-test"
    assert "Show me baby diapers" in str(models.calls[0]["contents"])


def test_invalid_json_falls_back_to_rules() -> None:
    detector, _ = detector_for("not json")

    result = detector.analyze("dm g\u00fcnstige Windeln")

    assert result.language == Language.DE
    assert result.intent == Intent.SEARCH
    assert result.partner_hint == Partner.DM
    assert result.entities.product_category == "baby care"
    assert result.entities.price_preference == "cheap"


def test_missing_fields_fall_back_to_rules() -> None:
    response_text = json.dumps(
        {
            "language": "en",
            "intent": "search",
            "specificity": "specific",
            "next_best_action": "search_catalog",
            "partner_hint": "unknown",
            "entities": {
                "product_category": "baby care",
            },
        }
    )
    detector, _ = detector_for(response_text)

    result = detector.analyze("Something nice")

    assert result.specificity == Specificity.VAGUE
    assert result.next_best_action == NextBestAction.ASK_CLARIFYING_QUESTION
    assert result.clarifying_question is not None


def test_timeout_error_falls_back_to_rules() -> None:
    detector, _ = detector_for(error=TimeoutError("upstream timed out"))

    result = detector.analyze("Meine PAYBACK Punkte fehlen")

    assert result.language == Language.DE
    assert result.intent == Intent.CUSTOMER_SUPPORT
    assert result.next_best_action == NextBestAction.ROUTE_TO_SUPPORT


def test_missing_vertex_config_falls_back_to_rules(monkeypatch) -> None:
    monkeypatch.delenv("GCP_PROJECT_ID", raising=False)
    get_settings.cache_clear()

    result = VertexLLMIntentDetector().analyze("Show me baby diapers")

    assert result.intent == Intent.SEARCH
    assert result.next_best_action == NextBestAction.SEARCH_CATALOG
    assert result.entities.product_category == "baby care"
    get_settings.cache_clear()


def test_german_diaper_query_detects_de_search_dm_and_baby_care() -> None:
    detector, _ = detector_for(
        payload_json(
            language="de",
            intent="search",
            specificity="navigational",
            next_best_action="partner_specific_search",
            partner_hint="dm",
            entities={
                "product_category": "baby care",
                "price_preference": "cheap",
                "occasion": "baby care",
                "dietary_preference": None,
                "brand": None,
            },
        )
    )

    result = detector.analyze("dm g\u00fcnstige Windeln")

    assert result.language == Language.DE
    assert result.intent == Intent.SEARCH
    assert result.partner_hint == Partner.DM
    assert result.entities.product_category == "baby care"
    assert result.entities.price_preference == "cheap"


def test_support_query_routes_to_support() -> None:
    detector, _ = detector_for(
        payload_json(
            language="de",
            intent="customer_support",
            specificity="specific",
            next_best_action="route_to_support",
            partner_hint="unknown",
            entities={
                "product_category": None,
                "price_preference": None,
                "occasion": None,
                "dietary_preference": None,
                "brand": None,
            },
        )
    )

    result = detector.analyze("Meine PAYBACK Punkte fehlen")

    assert result.intent == Intent.CUSTOMER_SUPPORT
    assert result.next_best_action == NextBestAction.ROUTE_TO_SUPPORT


def test_vague_query_generates_clarifying_question_when_llm_omits_one() -> None:
    detector, _ = detector_for(
        payload_json(
            language="en",
            intent="unknown",
            specificity="vague",
            next_best_action="ask_clarifying_question",
            partner_hint="unknown",
            entities={
                "product_category": None,
                "price_preference": None,
                "occasion": None,
                "dietary_preference": None,
                "brand": None,
            },
            clarifying_question=None,
        )
    )

    result = detector.analyze("Something nice")

    assert result.next_best_action == NextBestAction.ASK_CLARIFYING_QUESTION
    assert result.requires_clarification is True
    assert result.clarifying_question is not None
    assert result.clarifying_question.strip()


def test_comparison_query_maps_to_compare_products() -> None:
    detector, _ = detector_for(
        payload_json(
            language="en",
            intent="comparison",
            specificity="specific",
            next_best_action="compare_products",
            partner_hint="unknown",
            entities={
                "product_category": "electronics",
                "price_preference": None,
                "occasion": None,
                "dietary_preference": None,
                "brand": None,
            },
        )
    )

    result = detector.analyze("compare wireless headphones")

    assert result.intent == Intent.COMPARISON
    assert result.next_best_action == NextBestAction.COMPARE_PRODUCTS


def test_inconsistent_llm_action_falls_back_to_rules() -> None:
    detector, _ = detector_for(
        payload_json(
            intent="customer_support",
            next_best_action="search_catalog",
            entities={
                "product_category": None,
                "price_preference": None,
                "occasion": None,
                "dietary_preference": None,
                "brand": None,
            },
        )
    )

    result = detector.analyze("Meine PAYBACK Punkte fehlen")

    assert result.intent == Intent.CUSTOMER_SUPPORT
    assert result.next_best_action == NextBestAction.ROUTE_TO_SUPPORT
