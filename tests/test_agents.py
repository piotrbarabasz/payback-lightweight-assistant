from __future__ import annotations

import pytest

from app.agents import AssistantAgent, IntentDetectionAgent
from app.config import get_settings
from app.retrieval.backends.bigquery_vector import (
    BigQueryVectorConfig,
    BigQueryVectorProductRetriever,
)
from app.schemas import (
    AssistantQueryRequest,
    Intent,
    Language,
    NextBestAction,
    Partner,
)


CONFIG = BigQueryVectorConfig(
    project_id="payback-dev",
    dataset_id="catalog",
    table_id="products",
    location="europe-west1",
    vector_top_k=25,
)


class FakeQueryJob:
    def __init__(self, rows):
        self.rows = rows

    def result(self):
        return self.rows


class FakeClient:
    def __init__(self, rows):
        self.rows = rows
        self.queries = []
        self.job_configs = []

    def query(self, sql, job_config=None):
        self.queries.append(sql)
        self.job_configs.append(job_config)
        return FakeQueryJob(self.rows)


class FakeEmbeddingProvider:
    def __init__(self, embedding):
        self.embedding = embedding
        self.calls = []

    def embed_text(self, text):
        self.calls.append(text)
        return self.embedding


class FakeBigQuery:
    class QueryJobConfig:
        def __init__(self, query_parameters):
            self.query_parameters = query_parameters

    class ScalarQueryParameter:
        def __init__(self, name, parameter_type, value):
            self.name = name
            self.parameter_type = parameter_type
            self.value = value

    class ArrayQueryParameter:
        def __init__(self, name, array_type, values):
            self.name = name
            self.array_type = array_type
            self.values = values


@pytest.fixture(autouse=True)
def deterministic_backends(monkeypatch):
    monkeypatch.delenv("INTENT_BACKEND", raising=False)
    monkeypatch.delenv("RETRIEVAL_BACKEND", raising=False)
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def parameter_map(job_config):
    return {parameter.name: parameter for parameter in job_config.query_parameters}


def response_for(query: str, top_k: int = 5):
    payload = AssistantQueryRequest(query=query, top_k=top_k)
    intent_result = IntentDetectionAgent().analyze(payload.query)
    return AssistantAgent().respond(payload, intent_result)


def test_search_query_still_routes_to_catalog_search() -> None:
    response = response_for("Show me baby diapers", top_k=3)

    assert response.intent == Intent.SEARCH
    assert response.next_best_action == NextBestAction.SEARCH_CATALOG
    assert response.results


def test_german_dm_query_detects_german_search_dm_and_baby_care() -> None:
    result = IntentDetectionAgent().analyze("dm g\u00fcnstige Windeln")

    assert result.language == Language.DE
    assert result.intent == Intent.SEARCH
    assert result.partner_hint == Partner.DM
    assert result.entities.product_category == "baby care"
    assert result.entities.price_preference == "cheap"


def test_vague_query_still_asks_clarifying_question() -> None:
    response = response_for("Something nice")

    assert response.next_best_action == NextBestAction.ASK_CLARIFYING_QUESTION
    assert response.clarifying_question is not None
    assert response.results == []


def test_support_query_still_routes_to_support() -> None:
    response = response_for("Meine PAYBACK Punkte fehlen")

    assert response.intent == Intent.CUSTOMER_SUPPORT
    assert response.next_best_action == NextBestAction.ROUTE_TO_SUPPORT
    assert response.results == []


def test_comparison_query_still_returns_summary_and_criteria() -> None:
    response = response_for("compare wireless headphones", top_k=3)

    assert response.intent == Intent.COMPARISON
    assert response.next_best_action == NextBestAction.COMPARE_PRODUCTS
    assert response.comparison_summary is not None
    assert response.comparison_summary.strip()
    assert response.comparison_criteria == [
        "price",
        "partner",
        "category",
        "promotion_status",
        "relevance_score",
    ]


def test_assistant_agent_preserves_bigquery_vector_retriever_behavior() -> None:
    client = FakeClient(
        rows=[
            {
                "product_id": "dm-001",
                "partner": "dm",
                "name": "Penaten Baby Diapers",
                "category": "baby care",
                "price": 9.6,
                "currency": "EUR",
                "vector_distance": 0.12,
            }
        ]
    )
    provider = FakeEmbeddingProvider(embedding=[0.1, 0.2])
    retriever = BigQueryVectorProductRetriever(
        CONFIG,
        client=client,
        embedding_provider=provider,
        bigquery_module=FakeBigQuery,
    )
    agent = AssistantAgent(
        product_loader=lambda: [],
        retriever_factory=lambda: retriever,
    )
    payload = AssistantQueryRequest(query="cheap diapers", top_k=2)
    intent_result = IntentDetectionAgent().analyze(payload.query)

    response = agent.respond(payload, intent_result)

    assert provider.calls == ["cheap diapers"]
    assert "FROM VECTOR_SEARCH(" in client.queries[0]
    assert "category IN UNNEST(@categories)" in client.queries[0]
    params = parameter_map(client.job_configs[0])
    assert params["query_embedding"].values == [0.1, 0.2]
    assert params["vector_top_k"].value == 25
    assert params["result_limit"].value == 2
    assert params["categories"].values == ["baby care"]
    assert response.results[0].product_id == "dm-001"
    assert response.results[0].score == pytest.approx(0.88)
    assert "BigQuery Vector Search" in (response.results[0].reason or "")
