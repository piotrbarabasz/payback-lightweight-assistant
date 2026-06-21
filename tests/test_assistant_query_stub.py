from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_product_query_returns_stage_1_contract_shape() -> None:
    query = "Bitte zeige mir Angebote für günstige Windeln"

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


def test_product_query_returns_catalog_based_mock_results_with_top_k() -> None:
    response = client.post(
        "/assistant/query",
        json={"query": "Show me useful household products", "top_k": 3},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["next_best_action"] == "search_catalog"
    assert len(data["results"]) == 3
    assert all(result["score"] == 0.75 for result in data["results"])
    assert all(
        result["reason"]
        == "Catalog-based mock result for Stage 2; no semantic retrieval or ranking applied."
        for result in data["results"]
    )


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
    assert data["partner_hint"] == "edeka"
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
    assert data["results"]
    assert all(result["partner"] == "amazon" for result in data["results"])


def test_vague_query_returns_clarifying_question() -> None:
    response = client.post(
        "/assistant/query",
        json={"query": "Something nice"},
    )

    assert response.status_code == 200
    data = response.json()
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


def test_empty_query_is_rejected() -> None:
    response = client.post(
        "/assistant/query",
        json={"query": ""},
    )

    assert response.status_code == 422
