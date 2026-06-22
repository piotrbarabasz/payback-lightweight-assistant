from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_assistant_query_german_search_returns_results() -> None:
    response = client.post(
        "/assistant/query",
        json={
            "query": "Bitte zeige mir Angebote f\u00fcr g\u00fcnstige Windeln",
            "top_k": 5,
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["language"] == "de"
    assert data["intent"] == "search"
    assert data["next_best_action"] == "search_catalog"
    assert data["results"]


def test_assistant_query_english_discovery_returns_results() -> None:
    response = client.post(
        "/assistant/query",
        json={"query": "I need stuff for a pasta dinner", "top_k": 5},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["intent"] == "discovery"
    assert data["results"]


def test_assistant_query_navigational_partner_search_returns_results() -> None:
    response = client.post(
        "/assistant/query",
        json={"query": "Show me headphones on Amazon", "top_k": 5},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["specificity"] == "navigational"
    assert data["partner_hint"] == "amazon"
    assert data["next_best_action"] == "partner_specific_search"
    assert data["results"]


def test_assistant_query_support_routes_without_results() -> None:
    response = client.post(
        "/assistant/query",
        json={"query": "Meine PAYBACK Punkte fehlen"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["intent"] == "customer_support"
    assert data["next_best_action"] == "route_to_support"
    assert data["results"] == []


def test_assistant_query_vague_asks_clarifying_question_without_results() -> None:
    response = client.post(
        "/assistant/query",
        json={"query": "Something nice"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["next_best_action"] == "ask_clarifying_question"
    assert data["clarifying_question"] is not None
    assert data["results"] == []
