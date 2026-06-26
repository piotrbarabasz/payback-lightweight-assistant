"""Pluggable intent detection package."""

from app.intent.base import BaseIntentDetector

__all__ = [
    "BaseIntentDetector",
    "FutureVertexIntentDetector",
    "RuleBasedIntentDetector",
    "VertexLLMIntentConfig",
    "VertexLLMIntentDetector",
    "VertexIntentDetector",
    "analyze_query_intent",
    "get_intent_detector",
]


def __getattr__(name: str) -> object:
    if name == "get_intent_detector":
        from app.intent.factory import get_intent_detector

        return get_intent_detector
    if name == "RuleBasedIntentDetector":
        from app.intent.rule_based import RuleBasedIntentDetector

        return RuleBasedIntentDetector
    if name == "analyze_query_intent":
        from app.intent.service import analyze_query_intent

        return analyze_query_intent
    if name in {"VertexLLMIntentConfig", "VertexLLMIntentDetector"}:
        from app.intent.vertex_llm import VertexLLMIntentConfig, VertexLLMIntentDetector

        return {
            "VertexLLMIntentConfig": VertexLLMIntentConfig,
            "VertexLLMIntentDetector": VertexLLMIntentDetector,
        }[name]
    if name in {"FutureVertexIntentDetector", "VertexIntentDetector"}:
        from app.intent.vertex_placeholder import (
            FutureVertexIntentDetector,
            VertexIntentDetector,
        )

        return {
            "FutureVertexIntentDetector": FutureVertexIntentDetector,
            "VertexIntentDetector": VertexIntentDetector,
        }[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
