from __future__ import annotations

import pytest

from app.config import get_settings
from app.retrieval.backends.bigquery_vector import (
    BigQueryVectorConfig,
    BigQueryVectorProductRetriever,
    build_vector_search_sql,
    row_to_product_result,
)
from app.retrieval.normalizer import normalize_query
from app.schemas import Partner


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
    def __init__(self, rows=None, *, fail=False):
        self.rows = rows if rows is not None else []
        self.fail = fail
        self.queries = []
        self.job_configs = []

    def query(self, sql, job_config=None):
        self.queries.append(sql)
        self.job_configs.append(job_config)
        if self.fail:
            raise RuntimeError("upstream query failed")
        return FakeQueryJob(self.rows)


class FakeEmbeddingProvider:
    def __init__(self, embedding=None, *, fail=False):
        self.embedding = embedding or [0.1, 0.2, 0.3]
        self.fail = fail
        self.calls = []

    def embed_text(self, text):
        self.calls.append(text)
        if self.fail:
            raise RuntimeError("embedding failed")
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


def parameter_map(job_config):
    return {parameter.name: parameter for parameter in job_config.query_parameters}


def test_build_vector_search_sql_uses_vector_search_function() -> None:
    sql = build_vector_search_sql(
        CONFIG,
        vector_top_k=25,
        result_limit=5,
    )

    assert "FROM VECTOR_SEARCH(" in sql
    assert "FROM `payback-dev.catalog.products`" in sql
    assert "query_value => @query_embedding" in sql
    assert "top_k => @vector_top_k" in sql
    assert "distance_type => 'COSINE'" in sql
    assert "LIMIT @result_limit" in sql
    assert "partner = @partner" not in sql
    assert "category IN UNNEST(@categories)" not in sql


def test_build_vector_search_sql_includes_partner_filter() -> None:
    sql = build_vector_search_sql(
        CONFIG,
        vector_top_k=25,
        result_limit=5,
        partner_hint=Partner.DM,
    )

    assert "partner = @partner" in sql


def test_build_vector_search_sql_includes_category_filter() -> None:
    sql = build_vector_search_sql(
        CONFIG,
        vector_top_k=25,
        result_limit=5,
        category_hints=("baby care",),
    )

    assert "category IN UNNEST(@categories)" in sql


def test_row_to_product_result_maps_bigquery_row() -> None:
    result = row_to_product_result(
        {
            "product_id": "dm-001",
            "partner": "dm",
            "name": "Penaten Baby Diapers",
            "category": "baby care",
            "price": 9.6,
            "currency": "EUR",
            "vector_distance": 0.12,
        }
    )

    assert result.product_id == "dm-001"
    assert result.partner == Partner.DM
    assert result.name == "Penaten Baby Diapers"
    assert result.category == "baby care"
    assert result.price == 9.6
    assert result.score == pytest.approx(0.88)
    assert "BigQuery Vector Search" in (result.reason or "")


def test_retrieve_embeds_query_and_queries_bigquery() -> None:
    client = FakeClient(
        rows=[
            {
                "product_id": "amazon-001",
                "partner": "amazon",
                "name": "Wireless Headphones",
                "category": "electronics",
                "price": 39.99,
                "currency": "EUR",
                "vector_distance": 0.2,
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

    results = retriever.retrieve("Show me headphones on Amazon", products=[], top_k=3)

    assert provider.calls == ["Show me headphones on Amazon"]
    assert len(results) == 1
    assert results[0].product_id == "amazon-001"
    assert len(client.queries) == 1
    params = parameter_map(client.job_configs[0])
    assert params["query_embedding"].values == [0.1, 0.2]
    assert params["vector_top_k"].value == 25
    assert params["result_limit"].value == 3


def test_retrieve_applies_partner_filter_from_query_analysis() -> None:
    client = FakeClient(
        rows=[
            {
                "product_id": "amazon-001",
                "partner": "amazon",
                "name": "Wireless Headphones",
                "category": "electronics",
                "price": 39.99,
                "currency": "EUR",
                "vector_distance": 0.2,
            }
        ]
    )
    retriever = BigQueryVectorProductRetriever(
        CONFIG,
        client=client,
        embedding_provider=FakeEmbeddingProvider(),
        bigquery_module=FakeBigQuery,
    )

    retriever.retrieve("Show me headphones on Amazon", products=[], top_k=3)

    assert "partner = @partner" in client.queries[0]
    params = parameter_map(client.job_configs[0])
    assert params["partner"].value == "amazon"


def test_retrieve_applies_category_filter_from_query_analysis() -> None:
    client = FakeClient(
        rows=[
            {
                "product_id": "dm-001",
                "partner": "dm",
                "name": "Penaten Baby Diapers",
                "category": "baby care",
                "price": 9.6,
                "currency": "EUR",
                "vector_distance": 0.1,
            }
        ]
    )
    retriever = BigQueryVectorProductRetriever(
        CONFIG,
        client=client,
        embedding_provider=FakeEmbeddingProvider(),
        bigquery_module=FakeBigQuery,
    )

    retriever.retrieve(
        "cheap diapers",
        products=[],
        top_k=3,
        intent_analysis=normalize_query("cheap diapers"),
    )

    assert "category IN UNNEST(@categories)" in client.queries[0]
    params = parameter_map(client.job_configs[0])
    assert params["categories"].values == ["baby care"]


def test_retrieve_fails_clearly_when_config_is_missing(monkeypatch) -> None:
    monkeypatch.delenv("GCP_PROJECT_ID", raising=False)
    get_settings.cache_clear()
    retriever = BigQueryVectorProductRetriever(
        client=FakeClient(),
        embedding_provider=FakeEmbeddingProvider(),
        bigquery_module=FakeBigQuery,
    )

    with pytest.raises(
        ValueError,
        match="BigQuery Vector Search retrieval requires environment variables",
    ):
        retriever.retrieve("cheap pasta", products=[], top_k=3)
    get_settings.cache_clear()


def test_retrieve_wraps_embedding_errors() -> None:
    retriever = BigQueryVectorProductRetriever(
        CONFIG,
        client=FakeClient(),
        embedding_provider=FakeEmbeddingProvider(fail=True),
        bigquery_module=FakeBigQuery,
    )

    with pytest.raises(RuntimeError, match="Vertex AI query embedding failed"):
        retriever.retrieve("cheap pasta", products=[], top_k=3)


def test_retrieve_wraps_bigquery_errors() -> None:
    retriever = BigQueryVectorProductRetriever(
        CONFIG,
        client=FakeClient(fail=True),
        embedding_provider=FakeEmbeddingProvider(),
        bigquery_module=FakeBigQuery,
    )

    with pytest.raises(RuntimeError, match="BigQuery Vector Search query failed"):
        retriever.retrieve("cheap pasta", products=[], top_k=3)


def test_retrieve_fails_clearly_when_no_products_returned() -> None:
    retriever = BigQueryVectorProductRetriever(
        CONFIG,
        client=FakeClient(rows=[]),
        embedding_provider=FakeEmbeddingProvider(),
        bigquery_module=FakeBigQuery,
    )

    with pytest.raises(RuntimeError, match="returned no products"):
        retriever.retrieve("cheap pasta", products=[], top_k=3)
