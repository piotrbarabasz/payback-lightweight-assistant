"""Intent detection agent abstraction."""

from __future__ import annotations

from app.intent.base import BaseIntentDetector
from app.intent.factory import get_intent_detector
from app.schemas import IntentDetectionResult


class IntentDetectionAgent:
    """Deterministic intent detection agent by default.

    The agent delegates to the configured intent backend. The default backend is
    still the existing rule-based detector, so this class adds an explicit agent
    boundary without adding an autonomous LLM loop.
    """

    def __init__(
        self,
        detector: BaseIntentDetector | None = None,
        *,
        backend_name: str | None = None,
    ) -> None:
        if detector is not None and backend_name is not None:
            raise ValueError("Pass either detector or backend_name, not both")
        self._detector = detector
        self._backend_name = backend_name

    def analyze(self, query: str) -> IntentDetectionResult:
        """Analyze a raw query through the configured intent detector."""

        return self._get_detector().analyze(query)

    def _get_detector(self) -> BaseIntentDetector:
        if self._detector is None:
            self._detector = get_intent_detector(self._backend_name)
        return self._detector
