from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_product_query_returns_stage_1_contract_shape() -> None:
    query = "Bitte zeige mir Angebote f\u00fcr g\u00fcnstige Windeln"

    response = client.post(
        "/assistant/query",
        json={"query": query, "top_k": 5},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["query"] == query
    assert "language" in data
    assert "intent" in data
    assert "next_best_action" in data
    assert isinstance(data["results"], list)


def test_product_query_returns_ranked_catalog_results_with_top_k() -> None:
    response = client.post(
        "/assistant/query",
        json={"query": "Show me useful household products", "top_k": 3},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["next_best_action"] == "search_catalog"
    assert len(data["results"]) == 3
    assert [result["score"] for result in data["results"]] == sorted(
        [result["score"] for result in data["results"]],
        reverse=True,
    )
    assert all(
        result["reason"] is not None
        and "Matched query terms" in result["reason"]
        for result in data["results"]
    )
    assert all(0 < result["score"] <= 1 for result in data["results"])


def test_diaper_query_prefers_dm_catalog_products() -> None:
    response = client.post(
        "/assistant/query",
        json={"query": "Show me baby diapers", "top_k": 5},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["partner_hint"] == "dm"
    assert data["results"]
    assert all(result["partner"] == "dm" for result in data["results"])


def test_pasta_query_prefers_edeka_catalog_products() -> None:
    response = client.post(
        "/assistant/query",
        json={"query": "Nudeln fuer Abendessen bitte", "top_k": 4},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["intent"] == "discovery"
    assert data["specificity"] == "specific"
    assert data["next_best_action"] == "search_catalog"
    assert data["partner_hint"] == "edeka"
    assert data["language"] == "de"
    assert data["entities"]["occasion"] == "dinner"
    assert data["results"]
    assert all(result["partner"] == "edeka" for result in data["results"])


def test_headphones_query_prefers_amazon_catalog_products() -> None:
    response = client.post(
        "/assistant/query",
        json={"query": "kabellose Kopfh\u00f6rer bitte kaufen", "top_k": 4},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["partner_hint"] == "amazon"
    assert data["language"] == "de"
    assert data["results"]
    assert all(result["partner"] == "amazon" for result in data["results"])


def test_comparison_query_uses_compare_products_action() -> None:
    response = client.post(
        "/assistant/query",
        json={"query": "compare wireless headphones", "top_k": 3},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["intent"] == "comparison"
    assert data["specificity"] == "specific"
    assert data["next_best_action"] == "compare_products"
    assert data["results"]


def test_explicit_partner_query_uses_partner_specific_search() -> None:
    response = client.post(
        "/assistant/query",
        json={"query": "amazon headphones", "top_k": 3},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["intent"] == "search"
    assert data["specificity"] == "navigational"
    assert data["next_best_action"] == "partner_specific_search"
    assert data["partner_hint"] == "amazon"
    assert data["results"]
    assert all(result["partner"] == "amazon" for result in data["results"])


def test_query_with_price_preference_sets_entity_and_explainable_reason() -> None:
    response = client.post(
        "/assistant/query",
        json={"query": "Bitte guenstige Zahnpasta", "top_k": 3},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["entities"]["price_preference"] == "cheap"
    assert data["results"]
    assert all("cheap price preference" in result["reason"] for result in data["results"])


def test_vague_query_returns_clarifying_question() -> None:
    response = client.post(
        "/assistant/query",
        json={"query": "Something nice"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["specificity"] == "vague"
    assert data["next_best_action"] == "ask_clarifying_question"
    assert data["clarifying_question"] is not None
    assert data["results"] == []


def test_support_query_routes_to_support() -> None:
    response = client.post(
        "/assistant/query",
        json={"query": "Meine PAYBACK Punkte fehlen"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["intent"] == "customer_support"
    assert data["next_best_action"] == "route_to_support"
    assert data["results"] == []


def test_payback_brand_context_does_not_force_support_route() -> None:
    response = client.post(
        "/assistant/query",
        json={"query": "PAYBACK Angebote fuer Windeln", "top_k": 3},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["next_best_action"] == "search_catalog"
    assert data["results"]


def test_empty_query_is_rejected() -> None:
    response = client.post(
        "/assistant/query",
        json={"query": ""},
    )

    assert response.status_code == 422
