import json
from pathlib import Path

import pytest

from scripts.gcp.create_bigquery_catalog import (
    BigQueryCatalogConfig,
    ensure_dataset,
    ensure_table,
    load_config,
    load_schema_fields,
    main,
    parse_args,
    to_bigquery_schema,
)


class FakeNotFound(Exception):
    pass


class FakeDataset:
    def __init__(self, dataset_id: str) -> None:
        self.dataset_id = dataset_id
        self.location = None


class FakeTable:
    def __init__(self, table_id: str, schema: list[object]) -> None:
        self.table_id = table_id
        self.schema = schema


class FakeSchemaField:
    def __init__(
        self,
        name: str,
        field_type: str,
        mode: str = "NULLABLE",
        description: str | None = None,
    ) -> None:
        self.name = name
        self.field_type = field_type
        self.mode = mode
        self.description = description


class FakeBigQueryModule:
    Dataset = FakeDataset
    Table = FakeTable
    SchemaField = FakeSchemaField


class FakeClient:
    def __init__(self, existing_datasets=None, existing_tables=None) -> None:
        self.existing_datasets = set(existing_datasets or [])
        self.existing_tables = set(existing_tables or [])
        self.created_datasets: list[FakeDataset] = []
        self.created_tables: list[FakeTable] = []

    def get_dataset(self, dataset_id: str) -> object:
        if dataset_id not in self.existing_datasets:
            raise FakeNotFound(dataset_id)
        return object()

    def create_dataset(self, dataset: FakeDataset) -> FakeDataset:
        self.created_datasets.append(dataset)
        self.existing_datasets.add(dataset.dataset_id)
        return dataset

    def get_table(self, table_id: str) -> object:
        if table_id not in self.existing_tables:
            raise FakeNotFound(table_id)
        return object()

    def create_table(self, table: FakeTable) -> FakeTable:
        self.created_tables.append(table)
        self.existing_tables.add(table.table_id)
        return table


def test_parse_args_supports_dry_run() -> None:
    args = parse_args(["--dry-run", "--schema-path", "schema.json"])

    assert args.dry_run is True
    assert args.schema_path == "schema.json"


def test_load_config_reads_required_environment_values() -> None:
    config = load_config(
        {
            "GCP_PROJECT_ID": " payback-dev ",
            "BIGQUERY_DATASET": " catalog ",
            "BIGQUERY_PRODUCTS_TABLE": " products ",
            "BIGQUERY_LOCATION": " EU ",
        },
        schema_path="infra/gcp/bigquery_products_schema.json",
    )

    assert config.project_id == "payback-dev"
    assert config.dataset_id == "catalog"
    assert config.table_id == "products"
    assert config.location == "EU"
    assert config.dataset_fqn == "payback-dev.catalog"
    assert config.table_fqn == "payback-dev.catalog.products"


def test_load_config_fails_clearly_for_missing_values() -> None:
    with pytest.raises(
        ValueError,
        match=(
            "Missing required environment variables: "
            "GCP_PROJECT_ID, BIGQUERY_PRODUCTS_TABLE"
        ),
    ):
        load_config(
            {
                "GCP_PROJECT_ID": " ",
                "BIGQUERY_DATASET": "catalog",
                "BIGQUERY_PRODUCTS_TABLE": "",
                "BIGQUERY_LOCATION": "EU",
            }
        )


def test_load_schema_fields_validates_bigquery_schema_file() -> None:
    schema = load_schema_fields(Path("infra/gcp/bigquery_products_schema.json"))

    field_names = {field["name"] for field in schema}
    embedding_field = next(field for field in schema if field["name"] == "embedding")

    assert "product_id" in field_names
    assert "embedding_text" in field_names
    assert embedding_field["type"] == "FLOAT"
    assert embedding_field["mode"] == "REPEATED"


def test_load_schema_fields_rejects_invalid_json_shape() -> None:
    schema_path = Path("tmp/invalid_bigquery_schema.json")
    schema_path.parent.mkdir(exist_ok=True)
    schema_path.write_text(json.dumps({"name": "product_id"}), encoding="utf-8")

    try:
        with pytest.raises(ValueError, match="non-empty JSON array"):
            load_schema_fields(schema_path)
    finally:
        schema_path.unlink(missing_ok=True)


def test_to_bigquery_schema_uses_schema_field_objects() -> None:
    schema = to_bigquery_schema(
        [
            {
                "name": "product_id",
                "type": "STRING",
                "mode": "REQUIRED",
                "description": "Stable id.",
            }
        ],
        FakeBigQueryModule,
    )

    assert schema[0].name == "product_id"
    assert schema[0].field_type == "STRING"
    assert schema[0].mode == "REQUIRED"
    assert schema[0].description == "Stable id."


def test_ensure_dataset_creates_missing_dataset() -> None:
    client = FakeClient()
    config = BigQueryCatalogConfig(
        project_id="payback-dev",
        dataset_id="catalog",
        table_id="products",
        location="EU",
    )

    status = ensure_dataset(client, config, FakeBigQueryModule, FakeNotFound)

    assert status == "created"
    assert client.created_datasets[0].dataset_id == "payback-dev.catalog"
    assert client.created_datasets[0].location == "EU"


def test_ensure_dataset_is_idempotent_when_dataset_exists() -> None:
    client = FakeClient(existing_datasets={"payback-dev.catalog"})
    config = BigQueryCatalogConfig("payback-dev", "catalog", "products", "EU")

    status = ensure_dataset(client, config, FakeBigQueryModule, FakeNotFound)

    assert status == "already exists"
    assert client.created_datasets == []


def test_ensure_table_creates_missing_table() -> None:
    client = FakeClient()
    config = BigQueryCatalogConfig("payback-dev", "catalog", "products", "EU")
    schema = [object()]

    status = ensure_table(client, config, schema, FakeBigQueryModule, FakeNotFound)

    assert status == "created"
    assert client.created_tables[0].table_id == "payback-dev.catalog.products"
    assert client.created_tables[0].schema == schema


def test_ensure_table_is_idempotent_when_table_exists() -> None:
    client = FakeClient(existing_tables={"payback-dev.catalog.products"})
    config = BigQueryCatalogConfig("payback-dev", "catalog", "products", "EU")

    status = ensure_table(client, config, [], FakeBigQueryModule, FakeNotFound)

    assert status == "already exists"
    assert client.created_tables == []


def test_main_dry_run_validates_without_importing_google_cloud(
    monkeypatch,
    capsys,
) -> None:
    monkeypatch.setenv("GCP_PROJECT_ID", "payback-dev")
    monkeypatch.setenv("BIGQUERY_DATASET", "catalog")
    monkeypatch.setenv("BIGQUERY_PRODUCTS_TABLE", "products")
    monkeypatch.setenv("BIGQUERY_LOCATION", "EU")

    result = main(["--dry-run"])

    output = capsys.readouterr().out
    assert result == 0
    assert "Selected project: payback-dev" in output
    assert "Dry run: configuration and schema are valid; no GCP calls made." in output
