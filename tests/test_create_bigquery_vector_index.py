import pytest

from scripts.gcp.create_bigquery_vector_index import (
    DEFAULT_INDEX_NAME,
    build_create_vector_index_sql,
    create_vector_index,
    load_vector_index_config,
    main,
    parse_args,
    parse_stored_columns,
)


ENV = {
    "GCP_PROJECT_ID": "payback-dev",
    "BIGQUERY_DATASET": "catalog",
    "BIGQUERY_PRODUCTS_TABLE": "products",
    "BIGQUERY_LOCATION": "europe-west1",
}


class FakeQueryJob:
    def __init__(self) -> None:
        self.result_called = False

    def result(self) -> None:
        self.result_called = True


class FakeClient:
    def __init__(self) -> None:
        self.queries: list[str] = []
        self.jobs: list[FakeQueryJob] = []

    def query(self, sql: str) -> FakeQueryJob:
        self.queries.append(sql)
        job = FakeQueryJob()
        self.jobs.append(job)
        return job


def test_parse_args_supports_dry_run_and_sql_only() -> None:
    dry_run_args = parse_args(["--dry-run"])
    sql_only_args = parse_args(["--sql-only"])

    assert dry_run_args.dry_run is True
    assert sql_only_args.sql_only is True


def test_load_vector_index_config_uses_safe_defaults() -> None:
    config = load_vector_index_config(env=ENV)

    assert config.catalog.table_fqn == "payback-dev.catalog.products"
    assert config.index_name == DEFAULT_INDEX_NAME
    assert config.index_type == "IVF"
    assert config.distance_type == "COSINE"
    assert "product_id" in config.stored_columns
    assert config.num_lists is None


def test_load_vector_index_config_reads_env_index_name() -> None:
    config = load_vector_index_config(
        env={**ENV, "BIGQUERY_VECTOR_INDEX": "custom_embedding_idx"}
    )

    assert config.index_name == "custom_embedding_idx"


def test_load_vector_index_config_rejects_unsafe_index_name() -> None:
    with pytest.raises(ValueError, match="Invalid index name"):
        load_vector_index_config(env=ENV, index_name="bad-index;DROP")


def test_load_vector_index_config_rejects_invalid_num_lists() -> None:
    with pytest.raises(ValueError, match="--num-lists must be at least 1"):
        load_vector_index_config(env=ENV, num_lists=0)


def test_parse_stored_columns_normalizes_csv() -> None:
    assert parse_stored_columns(" product_id, partner ,, name ") == (
        "product_id",
        "partner",
        "name",
    )


def test_build_create_vector_index_sql_contains_comments_and_options() -> None:
    config = load_vector_index_config(env=ENV, num_lists=32)

    sql = build_create_vector_index_sql(config)

    assert "Optional Stage 8C vector index" in sql
    assert "CREATE VECTOR INDEX IF NOT EXISTS products_embedding_idx" in sql
    assert "ON `payback-dev.catalog.products`(embedding)" in sql
    assert "STORING (product_id, partner, name" in sql
    assert "index_type = 'IVF'" in sql
    assert "distance_type = 'COSINE'" in sql
    assert 'ivf_options = \'{"num_lists": 32}\'' in sql


def test_create_vector_index_executes_sql_with_fake_client() -> None:
    client = FakeClient()
    config = load_vector_index_config(env=ENV)

    sql = create_vector_index(client, config)

    assert client.queries == [sql]
    assert client.jobs[0].result_called is True


def test_main_dry_run_prints_sql_without_importing_bigquery(monkeypatch, capsys) -> None:
    for name, value in ENV.items():
        monkeypatch.setenv(name, value)

    result = main(["--dry-run", "--index-name", "test_embedding_idx"])

    output = capsys.readouterr().out
    assert result == 0
    assert "Stage 8C BigQuery Vector Index" in output
    assert "Target table: payback-dev.catalog.products" in output
    assert "CREATE VECTOR INDEX IF NOT EXISTS test_embedding_idx" in output
    assert "Dry run: SQL rendered; no BigQuery calls made." in output
