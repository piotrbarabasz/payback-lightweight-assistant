import pytest
from pydantic import ValidationError

from app.schemas import (
    AssistantQueryRequest,
    AssistantQueryResponse,
    Intent,
    Language,
    NextBestAction,
    Partner,
    Product,
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


def test_product_accepts_valid_catalog_product() -> None:
    product = Product(
        product_id="dm-baby-diapers-001",
        partner="dm",
        name="Baby Diapers Size 4",
        name_de="Baby Windeln Groesse 4",
        category="baby care",
        description="Soft absorbent diapers.",
        description_de="Weiche saugfaehige Windeln.",
        brand="Babylove",
        price=8.99,
        currency="eur",
        tags=["Baby", "Diapers", "baby"],
        tags_de=["Baby", "Windeln"],
        product_url=" https://example.test/products/dm-baby-diapers-001 ",
    )

    assert product.partner == Partner.DM
    assert product.currency == "EUR"
    assert product.tags == ["baby", "diapers"]
    assert product.tags_de == ["baby", "windeln"]
    assert product.popularity_score == 0.5
    assert product.availability is True
    assert product.product_url == "https://example.test/products/dm-baby-diapers-001"


def test_product_rejects_negative_price() -> None:
    with pytest.raises(ValidationError):
        Product(
            product_id="edeka-produce-apples-001",
            partner="edeka",
            name="Gala Apples",
            name_de="Gala Aepfel",
            category="fresh produce",
            description="Fresh apples.",
            description_de="Frische Aepfel.",
            brand="Fresh Farms",
            price=-0.01,
            tags=["fruit"],
            tags_de=["obst"],
        )


def test_product_rejects_api_result_score_field() -> None:
    with pytest.raises(ValidationError):
        Product(
            product_id="amazon-electronics-cable-001",
            partner="amazon",
            name="USB-C Cable",
            name_de="USB-C Kabel",
            category="electronics",
            description="Charging cable.",
            description_de="Ladekabel.",
            brand="Amazon Basics",
            price=7.99,
            tags=["electronics"],
            tags_de=["elektronik"],
            score=0.9,
        )


def test_product_rejects_unknown_partner() -> None:
    with pytest.raises(ValidationError):
        Product(
            product_id="unknown-product-001",
            partner="unknown",
            name="Unknown Product",
            name_de="Unbekanntes Produkt",
            category="unknown",
            description="Invalid catalog item.",
            description_de="Ungueltiger Katalogartikel.",
            brand="Unknown",
            price=1.0,
            tags=["unknown"],
            tags_de=["unbekannt"],
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
