"""API-independent assistant response orchestration."""

from __future__ import annotations

from app.catalog.loader import load_products
from app.intent.detector import with_clarifying_action
from app.intent.decision import build_clarifying_question
from app.retrieval import category_hint_from_results, retrieve_products
from app.schemas import (
    AssistantQueryRequest,
    AssistantQueryResponse,
    IntentDetectionResult,
    NextBestAction,
    Partner,
    ProductResult,
    QueryEntities,
)


def build_assistant_response(
    payload: AssistantQueryRequest,
    intent_result: IntentDetectionResult,
) -> AssistantQueryResponse:
    """Build a deterministic assistant response from intent and retrieval."""

    if _should_return_without_retrieval(intent_result.next_best_action):
        if intent_result.next_best_action == NextBestAction.FALLBACK:
            intent_result = _with_fallback_question(intent_result)
        return _response_from_intent_result(intent_result, results=[])

    results = retrieve_products(
        payload.query,
        load_products(),
        top_k=payload.top_k,
    )

    if not results:
        return _response_from_intent_result(
            with_clarifying_action(intent_result),
            results=[],
        )

    return _response_from_intent_result(
        intent_result.model_copy(
            update={
                "partner_hint": _partner_hint_from_results(
                    intent_result.partner_hint,
                    results,
                ),
                "entities": _entities_from_intent_and_results(
                    intent_result.entities,
                    results,
                ),
            }
        ),
        results=results,
    )


def _should_return_without_retrieval(next_best_action: NextBestAction) -> bool:
    return next_best_action in {
        NextBestAction.ASK_CLARIFYING_QUESTION,
        NextBestAction.ROUTE_TO_SUPPORT,
        NextBestAction.FALLBACK,
    }


def _with_fallback_question(
    intent_result: IntentDetectionResult,
) -> IntentDetectionResult:
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


def _response_from_intent_result(
    intent_result: IntentDetectionResult,
    results: list[ProductResult],
) -> AssistantQueryResponse:
    return AssistantQueryResponse(
        query=intent_result.query,
        language=intent_result.language,
        intent=intent_result.intent,
        specificity=intent_result.specificity,
        next_best_action=intent_result.next_best_action,
        clarifying_question=intent_result.clarifying_question,
        partner_hint=intent_result.partner_hint,
        entities=intent_result.entities,
        results=results,
    )


def _partner_hint_from_results(
    query_partner_hint: Partner | None,
    results: list[ProductResult],
) -> Partner:
    if query_partner_hint is not None and query_partner_hint != Partner.UNKNOWN:
        return query_partner_hint
    if not results:
        return Partner.UNKNOWN

    first_partner = results[0].partner
    if all(result.partner == first_partner for result in results):
        return first_partner
    return Partner.UNKNOWN


def _entities_from_intent_and_results(
    entities: QueryEntities,
    results: list[ProductResult],
) -> QueryEntities:
    if entities.product_category is not None:
        return entities

    category_hint = category_hint_from_results(results)
    if category_hint is None:
        return entities

    return entities.model_copy(update={"product_category": category_hint})
