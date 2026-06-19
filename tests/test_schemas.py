import pytest
from pydantic import ValidationError

from app.schemas import (
    AssistantQueryRequest,
    AssistantQueryResponse,
    Intent,
    Language,
    NextBestAction,
    Partner,
    ProductResult,
    QueryEntities,
    Specificity,
)


def test_assistant_query_request_accepts_valid_query() -> None:
    request = AssistantQueryRequest(
        query="Show me cheap diapers",
        top_k=5,
    )

    assert request.query == "Show me cheap diapers"
    assert request.top_k == 5


def test_assistant_query_request_rejects_empty_query() -> None:
    with pytest.raises(ValidationError):
        AssistantQueryRequest(query="")


def test_assistant_query_request_rejects_top_k_above_twenty() -> None:
    with pytest.raises(ValidationError):
        AssistantQueryRequest(
            query="Show me products",
            top_k=100,
        )


def test_product_result_accepts_valid_product() -> None:
    product = ProductResult(
        product_id="dm-001",
        partner="dm",
        name="Baby Diapers Size 4",
        category="baby care",
        price=8.99,
        currency="EUR",
        score=0.91,
        reason="Matches the query.",
    )

    assert product.product_id == "dm-001"
    assert product.partner == Partner.DM
    assert product.score == 0.91


def test_product_result_rejects_score_greater_than_one() -> None:
    with pytest.raises(ValidationError):
        ProductResult(
            product_id="dm-001",
            partner="dm",
            name="Baby Diapers Size 4",
            category="baby care",
            price=8.99,
            currency="EUR",
            score=1.5,
            reason="Matches the query.",
        )


def test_assistant_query_response_accepts_clarifying_question_response() -> None:
    response = AssistantQueryResponse(
        query="Something nice",
        language=Language.EN,
        intent=Intent.DISCOVERY,
        specificity=Specificity.VAGUE,
        next_best_action=NextBestAction.ASK_CLARIFYING_QUESTION,
        clarifying_question="Are you looking for groceries, drugstore items, or general products?",
        partner_hint=Partner.UNKNOWN,
        entities=QueryEntities(),
        results=[],
    )

    assert response.next_best_action == NextBestAction.ASK_CLARIFYING_QUESTION
    assert response.clarifying_question is not None
    assert response.results == []
