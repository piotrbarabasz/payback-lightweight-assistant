"""Optional Vertex/Gemini intent detector with deterministic rules fallback."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from collections.abc import Callable
from dataclasses import dataclass
import json
import logging
from typing import Any

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from app.config import get_settings
from app.intent.decision import build_clarifying_question, decide_next_best_action
from app.intent.rule_based import RuleBasedIntentDetector
from app.schemas import (
    Intent,
    IntentDetectionResult,
    Language,
    NextBestAction,
    Partner,
    QueryEntities,
    Specificity,
)


DEFAULT_VERTEX_INTENT_MODEL = "gemini-3.5-flash"
DEFAULT_INTENT_LLM_TIMEOUT_SECONDS = 3.0
LLM_CONFIDENCE = 0.8

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class VertexLLMIntentConfig:
    """Configuration required for optional Vertex/Gemini intent classification."""

    project_id: str
    location: str
    model: str = DEFAULT_VERTEX_INTENT_MODEL
    timeout_seconds: float = DEFAULT_INTENT_LLM_TIMEOUT_SECONDS

    @classmethod
    def from_env(cls) -> VertexLLMIntentConfig:
        settings = get_settings()
        project_id = settings.GCP_PROJECT_ID.strip()
        location = (settings.VERTEX_AI_LOCATION or settings.GCP_LOCATION).strip()
        model = settings.VERTEX_INTENT_MODEL.strip()
        timeout_seconds = settings.INTENT_LLM_TIMEOUT_SECONDS

        missing = []
        if not project_id:
            missing.append("GCP_PROJECT_ID")
        if not location:
            missing.append("GCP_LOCATION or VERTEX_AI_LOCATION")
        if missing:
            required = ", ".join(missing)
            raise ValueError(
                "Vertex LLM intent detection requires environment variables: "
                f"{required}. The backend is optional; use INTENT_BACKEND=rules "
                "for deterministic local intent detection."
            )

        return cls(
            project_id=project_id,
            location=location,
            model=model,
            timeout_seconds=timeout_seconds,
        )


ClientFactory = Callable[[VertexLLMIntentConfig], Any]
GenerateConfigFactory = Callable[[VertexLLMIntentConfig], Any]


class VertexLLMIntentDetector:
    """Structured Vertex/Gemini intent classifier with rules fallback.

    The model is used only to classify a single query into the existing
    `IntentDetectionResult` schema. Any upstream, parsing, validation, timeout,
    or consistency failure falls back to the deterministic rule-based detector.
    """

    def __init__(
        self,
        config: VertexLLMIntentConfig | None = None,
        *,
        client: Any | None = None,
        client_factory: ClientFactory | None = None,
        generate_config_factory: GenerateConfigFactory | None = None,
        fallback_detector: RuleBasedIntentDetector | None = None,
    ) -> None:
        self._config = config
        self._client = client
        self._client_factory = client_factory or _default_client_factory
        self._generate_config_factory = (
            generate_config_factory or _default_generate_config_factory
        )
        self._fallback_detector = fallback_detector or RuleBasedIntentDetector()

    def analyze(self, query: str) -> IntentDetectionResult:
        """Analyze a raw query with Vertex/Gemini, falling back to rules."""

        try:
            return self._analyze_with_llm(query)
        except Exception as exc:  # pragma: no cover - exact failures are mocked.
            logger.warning(
                "Vertex LLM intent detection failed; falling back to rules: %s",
                exc,
            )
            return self._fallback_detector.analyze(query)

    def _analyze_with_llm(self, query: str) -> IntentDetectionResult:
        normalized_query = query.strip()
        if not normalized_query:
            raise ValueError("query must not be empty")

        config = self._get_config()
        response = _run_with_timeout(
            lambda: self._get_client().models.generate_content(
                model=config.model,
                contents=_build_prompt(normalized_query),
                config=self._generate_config_factory(config),
            ),
            timeout_seconds=config.timeout_seconds,
        )
        payload = VertexLLMIntentPayload.model_validate(
            _load_json_object(_response_text(response))
        )
        return _payload_to_intent_result(normalized_query, payload)

    def _get_config(self) -> VertexLLMIntentConfig:
        if self._config is None:
            self._config = VertexLLMIntentConfig.from_env()
        return self._config

    def _get_client(self) -> Any:
        if self._client is None:
            self._client = self._client_factory(self._get_config())
        return self._client


class VertexLLMEntities(BaseModel):
    """Strict entity contract expected from the LLM JSON response."""

    model_config = ConfigDict(extra="forbid")

    product_category: str | None
    price_preference: str | None
    occasion: str | None
    dietary_preference: str | None
    brand: str | None

    @field_validator(
        "product_category",
        "price_preference",
        "occasion",
        "dietary_preference",
        "brand",
        mode="before",
    )
    @classmethod
    def normalize_optional_text(cls, value: object) -> object:
        if value is None:
            return None
        if isinstance(value, str):
            normalized = value.strip()
            return normalized or None
        return value

    def to_query_entities(self) -> QueryEntities:
        return QueryEntities(
            product_category=self.product_category,
            price_preference=self.price_preference,
            occasion=self.occasion,
            dietary_preference=self.dietary_preference,
            brand=self.brand,
        )


class VertexLLMIntentPayload(BaseModel):
    """Strict top-level JSON contract expected from Vertex/Gemini."""

    model_config = ConfigDict(extra="forbid")

    language: Language
    intent: Intent
    specificity: Specificity
    next_best_action: NextBestAction
    partner_hint: Partner
    entities: VertexLLMEntities
    clarifying_question: str | None

    @model_validator(mode="before")
    @classmethod
    def normalize_partner_specific_search(cls, data: object) -> object:
        if not isinstance(data, dict):
            return data

        normalized_data = dict(data)
        if _is_normalizable_partner_specific_search(normalized_data):
            normalized_data["specificity"] = Specificity.NAVIGATIONAL.value
        return normalized_data

    @field_validator("specificity")
    @classmethod
    def reject_unknown_specificity(cls, value: Specificity) -> Specificity:
        if value == Specificity.UNKNOWN:
            raise ValueError("LLM specificity must not be unknown")
        return value

    @field_validator("next_best_action")
    @classmethod
    def reject_fallback_action(cls, value: NextBestAction) -> NextBestAction:
        if value == NextBestAction.FALLBACK:
            raise ValueError("LLM next_best_action must not be fallback")
        return value

    @field_validator("clarifying_question", mode="before")
    @classmethod
    def normalize_clarifying_question(cls, value: object) -> object:
        if value is None:
            return None
        if isinstance(value, str):
            normalized = value.strip()
            return normalized or None
        return value

    @model_validator(mode="after")
    def require_consistent_action(self) -> VertexLLMIntentPayload:
        expected_action = decide_next_best_action(
            intent=self.intent,
            specificity=self.specificity,
            partner_hint=self.partner_hint,
            entities=self.entities.to_query_entities(),
        )
        if expected_action == NextBestAction.FALLBACK:
            raise ValueError("LLM output maps to unsupported fallback action")
        if self.next_best_action != expected_action:
            raise ValueError(
                "LLM next_best_action is inconsistent with intent facts: "
                f"expected {expected_action}, received {self.next_best_action}"
            )
        return self


def _is_normalizable_partner_specific_search(data: dict[str, Any]) -> bool:
    return (
        data.get("intent") == Intent.SEARCH.value
        and data.get("next_best_action") == NextBestAction.PARTNER_SPECIFIC_SEARCH.value
        and data.get("partner_hint") in _CONCRETE_PARTNER_VALUES
        and data.get("specificity")
        in {Specificity.SPECIFIC.value, Specificity.NAVIGATIONAL.value}
    )


_CONCRETE_PARTNER_VALUES = {
    Partner.DM.value,
    Partner.EDEKA.value,
    Partner.AMAZON.value,
}


def _payload_to_intent_result(
    query: str,
    payload: VertexLLMIntentPayload,
) -> IntentDetectionResult:
    entities = payload.entities.to_query_entities()
    clarifying_question = (
        payload.clarifying_question
        if payload.next_best_action == NextBestAction.ASK_CLARIFYING_QUESTION
        else None
    )
    if payload.next_best_action == NextBestAction.ASK_CLARIFYING_QUESTION:
        clarifying_question = clarifying_question or build_clarifying_question(
            payload.intent,
            entities,
            payload.language,
        )

    return IntentDetectionResult(
        query=query,
        language=payload.language,
        intent=payload.intent,
        specificity=payload.specificity,
        next_best_action=payload.next_best_action,
        partner_hint=payload.partner_hint,
        entities=entities,
        confidence=LLM_CONFIDENCE,
        requires_clarification=(
            payload.next_best_action == NextBestAction.ASK_CLARIFYING_QUESTION
        ),
        clarifying_question=clarifying_question,
    )


def _run_with_timeout(call: Callable[[], Any], *, timeout_seconds: float) -> Any:
    executor = ThreadPoolExecutor(max_workers=1)
    future = executor.submit(call)
    try:
        return future.result(timeout=timeout_seconds)
    except FutureTimeoutError as exc:
        future.cancel()
        raise TimeoutError("Vertex LLM intent request timed out") from exc
    finally:
        executor.shutdown(wait=False, cancel_futures=True)


def _load_json_object(text: str) -> dict[str, Any]:
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError("Vertex LLM response was not valid JSON") from exc
    if not isinstance(parsed, dict):
        raise ValueError("Vertex LLM response must be a JSON object")
    return parsed


def _response_text(response: Any) -> str:
    text = getattr(response, "text", None)
    if text is None and isinstance(response, dict):
        text = response.get("text")
    if isinstance(text, str) and text.strip():
        return text.strip()

    candidates = getattr(response, "candidates", None)
    if candidates is None and isinstance(response, dict):
        candidates = response.get("candidates")
    candidate_text = _text_from_candidates(candidates)
    if candidate_text:
        return candidate_text

    raise ValueError("Vertex LLM response did not include text")


def _text_from_candidates(candidates: Any) -> str | None:
    if not candidates:
        return None
    for candidate in candidates:
        content = _get_value(candidate, "content")
        parts = _get_value(content, "parts") if content is not None else None
        if not parts:
            continue
        for part in parts:
            text = _get_value(part, "text")
            if isinstance(text, str) and text.strip():
                return text.strip()
    return None


def _get_value(value: Any, key: str) -> Any:
    if isinstance(value, dict):
        return value.get(key)
    return getattr(value, key, None)


def _build_prompt(query: str) -> str:
    return (
        "Classify the user query for a lightweight PAYBACK shopping assistant. "
        "Return only one valid JSON object. Do not include markdown, prose, "
        "comments, or extra fields.\n\n"
        "Allowed JSON schema:\n"
        "{\n"
        '  "language": "de" | "en" | "unknown",\n'
        '  "intent": "search" | "discovery" | "comparison" | '
        '"customer_support" | "unknown",\n'
        '  "specificity": "specific" | "vague" | "navigational",\n'
        '  "next_best_action": "search_catalog" | '
        '"ask_clarifying_question" | "partner_specific_search" | '
        '"compare_products" | "route_to_support",\n'
        '  "partner_hint": "dm" | "edeka" | "amazon" | "unknown",\n'
        '  "entities": {\n'
        '    "product_category": string | null,\n'
        '    "price_preference": string | null,\n'
        '    "occasion": string | null,\n'
        '    "dietary_preference": string | null,\n'
        '    "brand": string | null\n'
        "  },\n"
        '  "clarifying_question": string | null\n'
        "}\n\n"
        "Action policy:\n"
        "- customer_support -> route_to_support.\n"
        "- vague -> ask_clarifying_question.\n"
        "- comparison -> compare_products.\n"
        "- explicit partner navigation -> partner_specific_search.\n"
        "- search or discovery -> search_catalog.\n"
        "- Do not return fallback.\n"
        "- For vague queries, include a short clarifying_question in the "
        "detected language.\n"
        "- Known partners are dm, edeka, and amazon.\n"
        "- Common categories include baby care, pasta and grains, dairy, "
        "electronics, oral care, hair care, and fresh produce.\n\n"
        f"User query: {query!r}"
    )


def _default_client_factory(config: VertexLLMIntentConfig) -> Any:
    try:
        from google import genai
    except ImportError as exc:
        raise RuntimeError(
            "google-genai is required for INTENT_BACKEND=vertex_llm. "
            "Install it with `pip install google-genai`."
        ) from exc

    return genai.Client(
        vertexai=True,
        project=config.project_id,
        location=config.location,
    )


def _default_generate_config_factory(config: VertexLLMIntentConfig) -> Any:
    try:
        from google.genai import types
    except ImportError as exc:
        raise RuntimeError(
            "google-genai is required for INTENT_BACKEND=vertex_llm. "
            "Install it with `pip install google-genai`."
        ) from exc

    return types.GenerateContentConfig(
        temperature=0,
        max_output_tokens=512,
        response_mime_type="application/json",
    )


__all__ = [
    "DEFAULT_INTENT_LLM_TIMEOUT_SECONDS",
    "DEFAULT_VERTEX_INTENT_MODEL",
    "VertexLLMIntentConfig",
    "VertexLLMIntentDetector",
]
