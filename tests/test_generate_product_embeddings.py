from __future__ import annotations

import pytest

from scripts.gcp.create_bigquery_catalog import BigQueryCatalogConfig
from scripts.gcp.generate_product_embeddings import (
    DEFAULT_LIMIT,
    EmbeddingCandidate,
    build_selection_sql,
    build_update_payload,
    generate_product_embeddings,
    main,
    parse_args,
    split_batches,
    update_product_embeddings,
    validate_args,
)


CONFIG = BigQueryCatalogConfig(
    project_id="payback-dev",
    dataset_id="catalog",
    table_id="products",
    location="europe-west1",
)


class FakeQueryJob:
    def __init__(self, rows=None, affected_rows=1):
        self.rows = rows or []
        self.num_dml_affected_rows = affected_rows

    def result(self):
        return self.rows


class FakeClient:
    def __init__(self, rows=None):
        self.rows = rows or []
        self.queries = []
        self.job_configs = []

    def query(self, sql, job_config=None):
        self.queries.append(sql)
        self.job_configs.append(job_config)
        if sql.startswith("SELECT"):
            return FakeQueryJob(self.rows)
        return FakeQueryJob(affected_rows=1)


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


class FakeEmbeddingProvider:
    def __init__(self):
        self.calls = []

    def embed_texts(self, texts):
        self.calls.append(list(texts))
        return [[float(index), float(index + 1)] for index, _ in enumerate(texts)]


def test_parse_args_uses_cost_safe_defaults() -> None:
    args = parse_args([])

    assert args.limit == DEFAULT_LIMIT
    assert args.batch_size == 5
    assert args.refresh is False
    assert args.dry_run is False


def test_validate_args_requires_explicit_full_refresh() -> None:
    args = parse_args(["--limit", "0"])

    with pytest.raises(ValueError, match="requires both --refresh"):
        validate_args(args)

    validate_args(parse_args(["--refresh", "--allow-full-refresh", "--limit", "0"]))


def test_build_selection_sql_selects_missing_embeddings_only_by_default() -> None:
    sql = build_selection_sql(CONFIG, limit=10, refresh=False)

    assert "FROM `payback-dev.catalog.products`" in sql
    assert "embedding_text IS NOT NULL" in sql
    assert "TRIM(embedding_text) != ''" in sql
    assert "(embedding IS NULL OR ARRAY_LENGTH(embedding) = 0)" in sql
    assert "ORDER BY partner, product_id" in sql
    assert sql.endswith("LIMIT 10")


def test_build_selection_sql_refresh_selects_all_embedding_text_rows() -> None:
    sql = build_selection_sql(CONFIG, limit=0, refresh=True)

    assert "  AND TRUE" in sql
    assert "LIMIT" not in sql


def test_build_update_payload_pairs_product_ids_with_embeddings() -> None:
    payload = build_update_payload(
        [
            EmbeddingCandidate("dm-001", "diapers text"),
            EmbeddingCandidate("edeka-001", "pasta text"),
        ],
        [
            [0.1, 0.2],
            [1, 2],
        ],
    )

    assert payload == [
        {"product_id": "dm-001", "embedding": [0.1, 0.2]},
        {"product_id": "edeka-001", "embedding": [1.0, 2.0]},
    ]


def test_build_update_payload_rejects_count_mismatch() -> None:
    with pytest.raises(ValueError, match="Embedding count must match"):
        build_update_payload([EmbeddingCandidate("dm-001", "text")], [])


def test_update_product_embeddings_builds_bigquery_parameter_payloads() -> None:
    client = FakeClient()

    rows_updated = update_product_embeddings(
        client,
        CONFIG,
        [{"product_id": "dm-001", "embedding": [0.1, 0.2]}],
        FakeBigQuery,
    )

    assert rows_updated == 1
    assert client.queries == [
        (
            "UPDATE `payback-dev.catalog.products`\n"
            "SET embedding = @embedding,\n"
            "    updated_at = CURRENT_TIMESTAMP()\n"
            "WHERE product_id = @product_id"
        )
    ]
    query_parameters = client.job_configs[0].query_parameters
    assert query_parameters[0].name == "product_id"
    assert query_parameters[0].value == "dm-001"
    assert query_parameters[1].name == "embedding"
    assert query_parameters[1].values == [0.1, 0.2]


def test_split_batches_chunks_candidates() -> None:
    candidates = [
        EmbeddingCandidate(f"product-{index}", f"text {index}")
        for index in range(5)
    ]

    batches = split_batches(candidates, batch_size=2)

    assert [[candidate.product_id for candidate in batch] for batch in batches] == [
        ["product-0", "product-1"],
        ["product-2", "product-3"],
        ["product-4"],
    ]


def test_generate_product_embeddings_batches_and_updates_with_mocks() -> None:
    rows = [
        {"product_id": "dm-001", "embedding_text": "diapers text"},
        {"product_id": "dm-002", "embedding_text": "shampoo text"},
        {"product_id": "edeka-001", "embedding_text": "pasta text"},
    ]
    client = FakeClient(rows=rows)
    provider = FakeEmbeddingProvider()

    summary = generate_product_embeddings(
        client,
        CONFIG,
        provider,
        FakeBigQuery,
        limit=10,
        refresh=False,
        batch_size=2,
    )

    assert provider.calls == [
        ["diapers text", "shampoo text"],
        ["pasta text"],
    ]
    assert summary.rows_selected == 3
    assert summary.embeddings_generated == 3
    assert summary.rows_updated == 3
    assert summary.failures == 0


def test_main_dry_run_prints_sql_without_bigquery_or_vertex_calls(
    monkeypatch,
    capsys,
) -> None:
    monkeypatch.setenv("GCP_PROJECT_ID", "payback-dev")
    monkeypatch.setenv("BIGQUERY_DATASET", "catalog")
    monkeypatch.setenv("BIGQUERY_PRODUCTS_TABLE", "products")
    monkeypatch.setenv("BIGQUERY_LOCATION", "europe-west1")

    result = main(["--dry-run", "--limit", "7", "--batch-size", "3"])

    output = capsys.readouterr().out
    assert result == 0
    assert "Dry run: no BigQuery or Vertex AI calls made." in output
    assert "Target table: payback-dev.catalog.products" in output
    assert "LIMIT 7" in output
    assert "Rows selected: 0 (dry run)" in output
    assert "Embeddings generated: 0" in output
    assert "Rows updated: 0" in output
    assert "Failures: 0" in output
