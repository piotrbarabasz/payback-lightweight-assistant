import pytest

from scripts.gcp.verify_bigquery_catalog import (
    BigQueryVerifyConfig,
    CatalogVerificationResult,
    build_verification_sql,
    load_config,
    main,
    parse_args,
    print_result,
    query_catalog_verification,
    quote_table_id,
)


class FakeQueryJob:
    def __init__(self, rows):
        self.rows = rows

    def result(self):
        return self.rows


class FakeClient:
    def __init__(self, results_by_sql):
        self.results_by_sql = results_by_sql
        self.queries = []

    def query(self, sql):
        self.queries.append(sql)
        return FakeQueryJob(self.results_by_sql[sql])


def test_parse_args_supports_sql_only_and_dry_run_alias() -> None:
    assert parse_args(["--sql-only"]).sql_only is True
    assert parse_args(["--dry-run"]).dry_run is True


def test_load_config_reads_required_environment_values() -> None:
    config = load_config(
        {
            "GCP_PROJECT_ID": " payback-dev ",
            "BIGQUERY_DATASET": " catalog ",
            "BIGQUERY_PRODUCTS_TABLE": " products ",
        }
    )

    assert config.project_id == "payback-dev"
    assert config.dataset_id == "catalog"
    assert config.table_id == "products"
    assert config.table_fqn == "payback-dev.catalog.products"


def test_load_config_fails_clearly_for_missing_values() -> None:
    with pytest.raises(
        ValueError,
        match="Missing required environment variables: GCP_PROJECT_ID, BIGQUERY_DATASET",
    ):
        load_config(
            {
                "GCP_PROJECT_ID": "",
                "BIGQUERY_PRODUCTS_TABLE": "products",
            }
        )


def test_quote_table_id_wraps_valid_fqn() -> None:
    assert quote_table_id("project.dataset.table") == "`project.dataset.table`"


def test_quote_table_id_rejects_backticks() -> None:
    with pytest.raises(ValueError, match="must not contain backticks"):
        quote_table_id("project.dataset.`table`")


def test_build_verification_sql_uses_expected_table_and_checks() -> None:
    config = BigQueryVerifyConfig("payback-dev", "catalog", "products")

    sql = build_verification_sql(config)

    assert sql["total_count"] == (
        "SELECT COUNT(*) AS total_count FROM `payback-dev.catalog.products`"
    )
    assert "GROUP BY partner" in sql["count_by_partner"]
    assert "LIMIT 5" in sql["sample_rows"]
    assert "TRIM(embedding_text) = ''" in sql["missing_embedding_text_count"]


def test_query_catalog_verification_runs_all_queries() -> None:
    config = BigQueryVerifyConfig("payback-dev", "catalog", "products")
    sql = build_verification_sql(config)
    client = FakeClient(
        {
            sql["total_count"]: [{"total_count": 150}],
            sql["count_by_partner"]: [
                {"partner": "dm", "product_count": 50},
                {"partner": "edeka", "product_count": 50},
                {"partner": "amazon", "product_count": 50},
            ],
            sql["sample_rows"]: [
                {
                    "product_id": "dm-001",
                    "partner": "dm",
                    "name": "Penaten Baby Diapers",
                    "category": "baby care",
                    "price": 9.6,
                    "currency": "EUR",
                }
            ],
            sql["missing_embedding_text_count"]: [
                {"missing_embedding_text_count": 0}
            ],
        }
    )

    result = query_catalog_verification(client, config)

    assert result.total_count == 150
    assert result.count_by_partner[0] == {"partner": "dm", "product_count": 50}
    assert result.sample_rows[0]["product_id"] == "dm-001"
    assert result.missing_embedding_text_count == 0
    assert client.queries == [
        sql["total_count"],
        sql["count_by_partner"],
        sql["sample_rows"],
        sql["missing_embedding_text_count"],
    ]


def test_query_catalog_verification_fails_when_table_is_empty() -> None:
    config = BigQueryVerifyConfig("payback-dev", "catalog", "products")
    sql = build_verification_sql(config)
    client = FakeClient({sql["total_count"]: [{"total_count": 0}]})

    with pytest.raises(ValueError, match="table is empty"):
        query_catalog_verification(client, config)


def test_main_sql_only_prints_sql_without_importing_google_cloud(
    monkeypatch,
    capsys,
) -> None:
    monkeypatch.setenv("GCP_PROJECT_ID", "payback-dev")
    monkeypatch.setenv("BIGQUERY_DATASET", "catalog")
    monkeypatch.setenv("BIGQUERY_PRODUCTS_TABLE", "products")

    result = main(["--sql-only"])

    output = capsys.readouterr().out
    assert result == 0
    assert "Target table: payback-dev.catalog.products" in output
    assert "SQL only: no GCP calls made." in output
    assert "SELECT COUNT(*) AS total_count" in output
    assert "missing_embedding_text_count" in output


def test_print_result_formats_copyable_summary(capsys) -> None:
    print_result(
        CatalogVerificationResult(
            table_fqn="payback-dev.catalog.products",
            total_count=150,
            count_by_partner=[{"partner": "dm", "product_count": 50}],
            sample_rows=[
                {
                    "product_id": "dm-001",
                    "partner": "dm",
                    "name": "Penaten Baby Diapers",
                    "category": "baby care",
                    "price": 9.6,
                    "currency": "EUR",
                }
            ],
            missing_embedding_text_count=0,
        )
    )

    output = capsys.readouterr().out
    assert "Stage 8A BigQuery Catalog Verification" in output
    assert "Total product count: 150" in output
    assert "- dm: 50" in output
    assert "- dm-001 | dm | Penaten Baby Diapers | baby care | 9.6 EUR" in output
