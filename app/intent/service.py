"""Pure intent detection service for raw assistant queries."""

from __future__ import annotations

from app.intent.decision import build_clarifying_question, decide_next_best_action
from app.intent.detector import detect_intent, detect_specificity
from app.intent.entities import detect_partner_hint, extract_entities
from app.intent.language import detect_language
from app.schemas import (
    Intent,
    IntentDetectionResult,
    NextBestAction,
    Partner,
    Specificity,
)


def analyze_query_intent(query: str) -> IntentDetectionResult:
    """Analyze a raw query and return deterministic internal intent output."""

    language = detect_language(query)
    entities = extract_entities(query)
    partner_hint = detect_partner_hint(query)
    intent = detect_intent(query)
    specificity = detect_specificity(
        query,
        partner_hint=partner_hint,
        entities=entities,
    )
    next_best_action = decide_next_best_action(
        intent=intent,
        specificity=specificity,
        partner_hint=partner_hint,
        entities=entities,
    )
    requires_clarification = (
        next_best_action == NextBestAction.ASK_CLARIFYING_QUESTION
    )

    return IntentDetectionResult(
        query=query,
        language=language,
        intent=intent,
        specificity=specificity,
        next_best_action=next_best_action,
        partner_hint=partner_hint or Partner.UNKNOWN,
        entities=entities,
        confidence=_confidence_for_result(intent, specificity, next_best_action),
        requires_clarification=requires_clarification,
        clarifying_question=(
            build_clarifying_question(intent, entities, language)
            if requires_clarification
            else None
        ),
    )


def _confidence_for_result(
    intent: Intent,
    specificity: Specificity,
    next_best_action: NextBestAction,
) -> float:
    if next_best_action == NextBestAction.FALLBACK or intent == Intent.UNKNOWN:
        if specificity == Specificity.VAGUE:
            return 0.6
        return 0.4
    if specificity == Specificity.VAGUE:
        return 0.6
    if specificity == Specificity.NAVIGATIONAL:
        return 0.9
    if intent in {Intent.CUSTOMER_SUPPORT, Intent.COMPARISON, Intent.SEARCH}:
        return 0.9
    if intent == Intent.DISCOVERY:
        return 0.75
    return 0.4
