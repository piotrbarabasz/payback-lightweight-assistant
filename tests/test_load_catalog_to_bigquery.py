import json
from pathlib import Path

import pytest

from scripts.gcp.create_bigquery_catalog import (
    BigQueryCatalogConfig,
    load_schema_fields,
)
from scripts.gcp.load_catalog_to_bigquery import (
    build_load_job_config,
    build_embedding_text,
    load_catalog_payload,
    load_rows_to_bigquery,
    main,
    parse_args,
    transform_products,
    validate_product_record,
    validate_products,
)


SCHEMA_FIELDS = [
    {"name": "product_id", "type": "STRING", "mode": "REQUIRED"},
    {"name": "partner", "type": "STRING", "mode": "REQUIRED"},
    {"name": "name", "type": "STRING", "mode": "REQUIRED"},
    {"name": "category", "type": "STRING", "mode": "REQUIRED"},
    {"name": "description", "type": "STRING", "mode": "REQUIRED"},
    {"name": "brand", "type": "STRING", "mode": "REQUIRED"},
    {"name": "price", "type": "FLOAT", "mode": "REQUIRED"},
    {"name": "currency", "type": "STRING", "mode": "REQUIRED"},
    {"name": "tags", "type": "STRING", "mode": "REPEATED"},
    {"name": "availability", "type": "BOOLEAN", "mode": "NULLABLE"},
    {"name": "is_promotion", "type": "BOOLEAN", "mode": "NULLABLE"},
    {"name": "embedding_text", "type": "STRING", "mode": "NULLABLE"},
    {"name": "embedding", "type": "FLOAT", "mode": "REPEATED"},
    {"name": "updated_at", "type": "TIMESTAMP", "mode": "NULLABLE"},
]


PRODUCT = {
    "product_id": "dm-001",
    "partner": "dm",
    "name": "Penaten Baby Diapers",
    "category": "baby care",
    "description": "Soft diapers for daytime and overnight use.",
    "brand": "Penaten",
    "price": 9.6,
    "tags": ["diapers", "baby care"],
    "availability": True,
    "is_promotion": False,
}


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


class FakeLoadJobConfig:
    def __init__(self, **kwargs) -> None:
        self.source_format = kwargs.get("source_format")
        self.write_disposition = kwargs.get("write_disposition")
        self.schema = kwargs.get("schema")
        self.autodetect = kwargs.get("autodetect")


class FakeWriteDisposition:
    WRITE_TRUNCATE = "WRITE_TRUNCATE"
    WRITE_APPEND = "WRITE_APPEND"


class FakeSourceFormat:
    NEWLINE_DELIMITED_JSON = "NEWLINE_DELIMITED_JSON"


class FakeBigQueryModule:
    SchemaField = FakeSchemaField
    LoadJobConfig = FakeLoadJobConfig
    WriteDisposition = FakeWriteDisposition
    SourceFormat = FakeSourceFormat


class FakeLoadJob:
    def __init__(self, output_rows: int) -> None:
        self.output_rows = output_rows
        self.result_called = False

    def result(self) -> None:
        self.result_called = True


class FakeClient:
    def __init__(self) -> None:
        self.loaded_rows: list[dict[str, object]] = []
        self.loaded_table = ""
        self.job_config: FakeLoadJobConfig | None = None
        self.load_job = FakeLoadJob(output_rows=0)

    def load_table_from_json(
        self,
        rows: list[dict[str, object]],
        table_fqn: str,
        job_config: FakeLoadJobConfig,
    ) -> FakeLoadJob:
        self.loaded_rows = rows
        self.loaded_table = table_fqn
        self.job_config = job_config
        self.load_job.output_rows = len(rows)
        return self.load_job


def test_parse_args_defaults_to_append_mode() -> None:
    args = parse_args([])

    assert args.mode == "append"
    assert args.dry_run is False


def test_validate_product_record_accepts_valid_product() -> None:
    validate_product_record(PRODUCT, 0)


def test_validate_product_record_accepts_title_as_name() -> None:
    product = dict(PRODUCT)
    product.pop("name")
    product["title"] = "Fallback title"

    validate_product_record(product, 0)


def test_validate_product_record_rejects_missing_required_fields() -> None:
    with pytest.raises(
        ValueError,
        match=(
            "Invalid product at index 0: product_id is required; "
            "partner is required; name or title is required; category is required"
        ),
    ):
        validate_product_record(
            {
                "price": 1.99,
            },
            0,
        )


def test_validate_product_record_rejects_non_numeric_price() -> None:
    product = dict(PRODUCT, price="free")

    with pytest.raises(ValueError, match="price must be numeric"):
        validate_product_record(product, 0)


def test_validate_products_rejects_duplicate_product_ids() -> None:
    with pytest.raises(ValueError, match="duplicate product_id"):
        validate_products([PRODUCT, dict(PRODUCT)])


def test_transform_products_maps_catalog_to_schema_and_defaults_currency() -> None:
    rows = transform_products([PRODUCT], SCHEMA_FIELDS)

    assert rows == [
        {
            "product_id": "dm-001",
            "partner": "dm",
            "name": "Penaten Baby Diapers",
            "category": "baby care",
            "description": "Soft diapers for daytime and overnight use.",
            "brand": "Penaten",
            "price": 9.6,
            "currency": "EUR",
            "tags": ["diapers", "baby care"],
            "availability": True,
            "is_promotion": False,
            "embedding_text": (
                "Penaten Baby Diapers Penaten dm baby care "
                "Soft diapers for daytime and overnight use. diapers, baby care"
            ),
            "embedding": [],
            "updated_at": None,
        }
    ]


def test_schema_file_keeps_embedding_as_repeated_float_and_text_as_string() -> None:
    schema = load_schema_fields(Path("infra/gcp/bigquery_products_schema.json"))

    embedding = next(field for field in schema if field["name"] == "embedding")
    embedding_text = next(
        field for field in schema if field["name"] == "embedding_text"
    )

    assert embedding["type"] == "FLOAT"
    assert embedding["mode"] == "REPEATED"
    assert embedding_text["type"] == "STRING"


def test_build_load_job_config_uses_explicit_schema_for_replace_mode() -> None:
    job_config = build_load_job_config(
        SCHEMA_FIELDS,
        "replace",
        FakeBigQueryModule,
    )

    embedding = next(field for field in job_config.schema if field.name == "embedding")
    embedding_text = next(
        field for field in job_config.schema if field.name == "embedding_text"
    )

    assert job_config.source_format == "NEWLINE_DELIMITED_JSON"
    assert job_config.write_disposition == "WRITE_TRUNCATE"
    assert job_config.autodetect is False
    assert embedding.field_type == "FLOAT"
    assert embedding.mode == "REPEATED"
    assert embedding_text.field_type == "STRING"


def test_build_load_job_config_uses_explicit_schema_for_append_mode() -> None:
    job_config = build_load_job_config(
        SCHEMA_FIELDS,
        "append",
        FakeBigQueryModule,
    )

    assert job_config.write_disposition == "WRITE_APPEND"
    assert job_config.autodetect is False
    assert any(field.name == "embedding" for field in job_config.schema)


def test_load_rows_to_bigquery_passes_schema_to_replace_job() -> None:
    config = BigQueryCatalogConfig(
        project_id="payback-dev",
        dataset_id="catalog",
        table_id="products",
        location="EU",
    )
    client = FakeClient()
    rows = transform_products([PRODUCT], SCHEMA_FIELDS)

    loaded = load_rows_to_bigquery(
        config,
        rows,
        "replace",
        SCHEMA_FIELDS,
        client=client,
        bigquery_module=FakeBigQueryModule,
    )

    assert loaded == 1
    assert client.loaded_table == "payback-dev.catalog.products"
    assert client.loaded_rows == rows
    assert client.load_job.result_called is True
    assert client.job_config is not None
    assert client.job_config.write_disposition == "WRITE_TRUNCATE"
    assert client.job_config.autodetect is False
    embedding = next(
        field for field in client.job_config.schema if field.name == "embedding"
    )
    assert embedding.field_type == "FLOAT"
    assert embedding.mode == "REPEATED"


def test_build_embedding_text_combines_searchable_catalog_fields() -> None:
    embedding_text = build_embedding_text(PRODUCT)

    assert "Penaten Baby Diapers" in embedding_text
    assert "Penaten" in embedding_text
    assert "dm" in embedding_text
    assert "baby care" in embedding_text
    assert "Soft diapers" in embedding_text
    assert "diapers, baby care" in embedding_text


def test_load_catalog_payload_rejects_non_array_json() -> None:
    catalog_path = Path("tmp/invalid_catalog_payload.json")
    catalog_path.parent.mkdir(exist_ok=True)
    catalog_path.write_text(json.dumps({"product_id": "dm-001"}), encoding="utf-8")

    try:
        with pytest.raises(ValueError, match="must be an array"):
            load_catalog_payload(catalog_path)
    finally:
        catalog_path.unlink(missing_ok=True)


def test_main_dry_run_validates_and_prints_sample_rows(monkeypatch, capsys) -> None:
    monkeypatch.setenv("GCP_PROJECT_ID", "payback-dev")
    monkeypatch.setenv("BIGQUERY_DATASET", "payback_catalog")
    monkeypatch.setenv("BIGQUERY_PRODUCTS_TABLE", "products")
    monkeypatch.setenv("BIGQUERY_LOCATION", "europe-west1")

    result = main(["--dry-run", "--sample-size", "1"])

    output = capsys.readouterr().out
    assert result == 0
    assert "Source file: app/data/products.json" in output.replace("\\", "/")
    assert "Products read: 150" in output
    assert "Products loaded: 0" in output
    assert "Target table: payback-dev.payback_catalog.products" in output
    assert "Dry run: validated and transformed rows; no GCP calls made." in output
    assert '"embedding_text"' in output
