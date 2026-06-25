"""Base interfaces for pluggable intent detection."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from app.schemas import IntentDetectionResult


@runtime_checkable
class BaseIntentDetector(Protocol):
    """Protocol implemented by intent detector backends."""

    def analyze(self, query: str) -> IntentDetectionResult:
        """Analyze a raw user query and return structured intent output."""
