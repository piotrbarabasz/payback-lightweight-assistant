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
