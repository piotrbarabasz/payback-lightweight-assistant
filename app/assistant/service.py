"""API-independent assistant response orchestration."""

from __future__ import annotations

from app.agents.assistant import AssistantAgent, COMPARISON_CRITERIA
from app.schemas import (
    AssistantQueryRequest,
    AssistantQueryResponse,
    IntentDetectionResult,
)


def build_assistant_response(
    payload: AssistantQueryRequest,
    intent_result: IntentDetectionResult,
) -> AssistantQueryResponse:
    """Build a deterministic assistant response through the assistant agent."""

    return AssistantAgent().respond(payload, intent_result)


__all__ = [
    "COMPARISON_CRITERIA",
    "build_assistant_response",
]
