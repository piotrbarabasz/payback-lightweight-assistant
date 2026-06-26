"""Legacy placeholder for the pre-Stage 9 Vertex intent boundary."""

from __future__ import annotations

from app.schemas import IntentDetectionResult


class VertexIntentDetector:
    """Obsolete skeleton kept only for import compatibility.

    This class intentionally makes no Google Cloud, Vertex AI, Gemini, or other
    external API calls. The supported optional Vertex/Gemini backend is
    ``INTENT_BACKEND=vertex_llm`` through ``VertexLLMIntentDetector``.
    """

    def analyze(self, query: str) -> IntentDetectionResult:
        raise NotImplementedError(
            "INTENT_BACKEND=vertex_placeholder is obsolete and unsupported. "
            "Use INTENT_BACKEND=rules for the default deterministic backend "
            "or INTENT_BACKEND=vertex_llm for optional Vertex/Gemini intent parsing."
        )


FutureVertexIntentDetector = VertexIntentDetector
