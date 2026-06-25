from fastapi.testclient import TestClient

from app.main import app
from app.retrieval.keyword_retriever import KeywordProductRetriever
from app.schemas import Partner, Product


client = TestClient(app)


def product(
    product_id: str,
    partner: Partner,
    *,
    name: str,
    tags: list[str],
    popularity_score: float = 0.5,
) -> Product:
    return Product(
        product_id=product_id,
        partner=partner,
        name=name,
        name_de=name,
        category="electronics",
        description=f"{name} test product.",
        description_de=f"{name} Testprodukt.",
        brand="Test Brand",
        price=10.0,
        tags=tags,
        tags_de=tags,
        popularity_score=popularity_score,
    )


def test_keyword_retriever_scopes_navigational_query_to_partner_adapter() -> None:
    products = [
        product(
            "dm-001",
            Partner.DM,
            name="Drugstore Headphones",
            tags=["headphones"],
            popularity_score=0.99,
        ),
        product(
            "amazon-001",
            Partner.AMAZON,
            name="Amazon Headphones",
            tags=["headphones"],
            popularity_score=0.1,
        ),
    ]

    results = KeywordProductRetriever().retrieve(
        "Show me headphones on Amazon",
        products,
        top_k=5,
    )

    assert results
    assert {result.partner for result in results} == {Partner.AMAZON}


def test_unknown_partner_behavior_keeps_cross_partner_retrieval() -> None:
    products = [
        product("dm-001", Partner.DM, name="Baby Diapers", tags=["diapers"]),
        product("amazon-001", Partner.AMAZON, name="Headphones", tags=["headphones"]),
    ]

    results = KeywordProductRetriever().retrieve(
        "diapers headphones",
        products,
        top_k=5,
    )

    assert {result.partner for result in results} == {Partner.DM, Partner.AMAZON}


def test_assistant_partner_specific_search_stays_amazon_scoped() -> None:
    response = client.post(
        "/assistant/query",
        json={"query": "Show me headphones on Amazon", "top_k": 5},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["next_best_action"] == "partner_specific_search"
    assert payload["partner_hint"] == "amazon"
    assert payload["results"]
    assert {result["partner"] for result in payload["results"]} == {"amazon"}


def test_existing_non_partner_retrieval_still_returns_results() -> None:
    response = client.post(
        "/assistant/query",
        json={"query": "Bitte zeige mir Angebote fuer guenstige Windeln", "top_k": 3},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["next_best_action"] == "search_catalog"
    assert payload["results"]
