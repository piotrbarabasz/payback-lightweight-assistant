"""Factory for selecting intent detector backends."""

from __future__ import annotations

from app.config import get_settings
from app.intent.base import BaseIntentDetector
from app.intent.rule_based import RuleBasedIntentDetector
from app.intent.vertex_placeholder import VertexIntentDetector


def get_intent_detector(backend_name: str | None = None) -> BaseIntentDetector:
    """Return the configured intent detector backend."""

    selected_backend = (backend_name or get_settings().INTENT_BACKEND).strip().lower()
    if selected_backend == "rules":
        return RuleBasedIntentDetector()
    if selected_backend in {"llm_placeholder", "vertex_placeholder"}:
        return VertexIntentDetector(backend_name=selected_backend)
    raise ValueError(f"Unsupported intent backend: {selected_backend}")
