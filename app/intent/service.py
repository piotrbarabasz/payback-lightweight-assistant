"""Public intent detection service for raw assistant queries."""

from __future__ import annotations

from app.intent.factory import get_intent_detector
from app.schemas import IntentDetectionResult


def analyze_query_intent(query: str) -> IntentDetectionResult:
    """Analyze a raw query with the configured intent detector backend."""

    return get_intent_detector().analyze(query)
