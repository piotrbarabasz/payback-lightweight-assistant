"""Placeholder for a future Vertex AI or LLM-backed intent detector."""

from __future__ import annotations

from app.schemas import IntentDetectionResult


class VertexIntentDetector:
    """Unavailable skeleton for a future external intent detector.

    This class intentionally makes no Google Cloud, Vertex AI, Gemini, or other
    external API calls. It exists only to make the backend boundary explicit.
    """

    def __init__(self, backend_name: str = "vertex_placeholder") -> None:
        self.backend_name = backend_name

    def analyze(self, query: str) -> IntentDetectionResult:
        raise NotImplementedError(
            f"INTENT_BACKEND={self.backend_name} is not implemented. "
            "External Vertex AI or LLM intent detection is planned for Stage 8. "
            "Use INTENT_BACKEND=rules for the local deterministic MVP."
        )


FutureVertexIntentDetector = VertexIntentDetector
