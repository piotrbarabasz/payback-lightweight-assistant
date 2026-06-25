"""Placeholder for a future Vertex AI or LLM-backed intent detector."""

from __future__ import annotations

from app.schemas import IntentDetectionResult


class VertexIntentDetector:
    """Unavailable skeleton for a future external intent detector.

    This class intentionally makes no Google Cloud, Vertex AI, Gemini, or other
    external API calls. It exists only to make the backend boundary explicit.
    """

    def analyze(self, query: str) -> IntentDetectionResult:
        raise NotImplementedError(
            "INTENT_BACKEND=vertex_placeholder is not implemented. "
            "Use INTENT_BACKEND=rules for the local deterministic MVP."
        )


FutureVertexIntentDetector = VertexIntentDetector
