"""Deterministic decision agent for assistant routing policy."""

from __future__ import annotations

from app.intent.decision import (
    build_clarifying_question,
    decide_next_best_action,
)
from app.intent.detector import with_clarifying_action
from app.schemas import (
    Intent,
    IntentDetectionResult,
    NextBestAction,
    Partner,
    QueryEntities,
    Specificity,
)


class DecisionAgent:
    """Small policy facade around the existing next-best-action rules."""

    def decide_next_best_action(
        self,
        *,
        intent: Intent,
        specificity: Specificity,
        partner_hint: Partner | None,
        entities: QueryEntities,
    ) -> NextBestAction:
        """Return the deterministic next best action for detected query facts."""

        return decide_next_best_action(
            intent=intent,
            specificity=specificity,
            partner_hint=partner_hint,
            entities=entities,
        )

    def should_return_without_retrieval(
        self,
        intent_result: IntentDetectionResult,
    ) -> bool:
        """Return whether the assistant should skip catalog retrieval."""

        return intent_result.next_best_action in {
            NextBestAction.ASK_CLARIFYING_QUESTION,
            NextBestAction.ROUTE_TO_SUPPORT,
            NextBestAction.FALLBACK,
        }

    def prepare_no_retrieval_result(
        self,
        intent_result: IntentDetectionResult,
    ) -> IntentDetectionResult:
        """Add deterministic response details for no-retrieval actions."""

        if intent_result.next_best_action != NextBestAction.FALLBACK:
            return intent_result
        return self.with_fallback_question(intent_result)

    def with_fallback_question(
        self,
        intent_result: IntentDetectionResult,
    ) -> IntentDetectionResult:
        """Ensure fallback responses include a deterministic clarifying question."""

        if intent_result.clarifying_question is not None:
            return intent_result

        return intent_result.model_copy(
            update={
                "clarifying_question": build_clarifying_question(
                    intent_result.intent,
                    intent_result.entities,
                    intent_result.language,
                )
            }
        )

    def with_clarifying_action(
        self,
        intent_result: IntentDetectionResult,
        clarifying_question: str | None = None,
    ) -> IntentDetectionResult:
        """Return a copy of an intent result that asks the user to clarify."""

        return with_clarifying_action(intent_result, clarifying_question)
