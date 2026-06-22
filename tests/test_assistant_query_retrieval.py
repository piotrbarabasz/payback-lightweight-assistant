from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_german_diaper_query_returns_retrieval_results() -> None:
    response = client.post(
        "/assistant/query",
        json={
            "query": "Bitte zeige mir Angebote f\u00fcr g\u00fcnstige Windeln",
            "top_k": 5,
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["language"] in {"de", "unknown"}
    assert data["intent"] == "search"
    assert data["next_best_action"] in {
        "search_catalog",
        "partner_specific_search",
    }
    assert data["results"]
    assert any(
        result["partner"] == "dm" or result["category"] == "baby care"
        for result in data["results"]
    )


def test_pasta_dinner_query_returns_discovery_results() -> None:
    response = client.post(
        "/assistant/query",
        json={"query": "I need stuff for a pasta dinner", "top_k": 5},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["intent"] == "discovery"
    assert data["results"]
    assert any(
        result["partner"] == "edeka"
        or result["category"] in {"pasta and grains", "grocery", "pantry"}
        for result in data["results"]
    )


def test_amazon_headphones_query_returns_navigational_amazon_results() -> None:
    response = client.post(
        "/assistant/query",
        json={"query": "Show me headphones on Amazon", "top_k": 5},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["specificity"] == "navigational"
    assert data["partner_hint"] == "amazon"
    assert data["results"]
    assert any(result["partner"] == "amazon" for result in data["results"])


def test_support_query_routes_to_support_without_results() -> None:
    response = client.post(
        "/assistant/query",
        json={"query": "Meine PAYBACK Punkte fehlen"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["intent"] == "customer_support"
    assert data["next_best_action"] == "route_to_support"
    assert data["results"] == []


def test_vague_query_returns_clarifying_question_without_results() -> None:
    response = client.post(
        "/assistant/query",
        json={"query": "Something nice"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["next_best_action"] == "ask_clarifying_question"
    assert data["clarifying_question"] is not None
    assert data["results"] == []
