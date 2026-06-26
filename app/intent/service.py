"""Public intent detection service for raw assistant queries."""

from __future__ import annotations

from app.agents.intent_detection import IntentDetectionAgent
from app.schemas import IntentDetectionResult


def analyze_query_intent(query: str) -> IntentDetectionResult:
    """Analyze a raw query with the configured intent detection agent."""

    return IntentDetectionAgent().analyze(query)
