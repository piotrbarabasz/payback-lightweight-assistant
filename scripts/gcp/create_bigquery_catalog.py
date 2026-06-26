"""Create the BigQuery dataset and products table for the catalog foundation."""

from __future__ import annotations

import argparse
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence


DEFAULT_SCHEMA_PATH = Path("infra/gcp/bigquery_products_schema.json")
REQUIRED_ENV_VARS = (
    "GCP_PROJECT_ID",
    "BIGQUERY_DATASET",
    "BIGQUERY_PRODUCTS_TABLE",
    "BIGQUERY_LOCATION",
)


@dataclass(frozen=True)
class BigQueryCatalogConfig:
    project_id: str
    dataset_id: str
    table_id: str
    location: str
    schema_path: Path = DEFAULT_SCHEMA_PATH

    @property
    def dataset_fqn(self) -> str:
        return f"{self.project_id}.{self.dataset_id}"

    @property
    def table_fqn(self) -> str:
        return f"{self.project_id}.{self.dataset_id}.{self.table_id}"


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create the BigQuery catalog dataset and products table.",
    )
    parser.add_argument(
        "--schema-path",
        default=str(DEFAULT_SCHEMA_PATH),
        help="Path to the BigQuery JSON schema file.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate configuration and schema without creating GCP resources.",
    )
    return parser.parse_args(argv)


def load_config(
    env: Mapping[str, str] | None = None,
    schema_path: str | Path = DEFAULT_SCHEMA_PATH,
) -> BigQueryCatalogConfig:
    values = env if env is not None else os.environ
    missing = [
        name
        for name in REQUIRED_ENV_VARS
        if not values.get(name) or not values[name].strip()
    ]
    if missing:
        names = ", ".join(missing)
        raise ValueError(f"Missing required environment variables: {names}")

    return BigQueryCatalogConfig(
        project_id=values["GCP_PROJECT_ID"].strip(),
        dataset_id=values["BIGQUERY_DATASET"].strip(),
        table_id=values["BIGQUERY_PRODUCTS_TABLE"].strip(),
        location=values["BIGQUERY_LOCATION"].strip(),
        schema_path=Path(schema_path),
    )


def load_schema_fields(schema_path: Path) -> list[dict[str, Any]]:
    if not schema_path.exists():
        raise FileNotFoundError(f"BigQuery schema file does not exist: {schema_path}")

    with schema_path.open("r", encoding="utf-8") as schema_file:
        payload = json.load(schema_file)

    if not isinstance(payload, list) or not payload:
        raise ValueError("BigQuery schema must be a non-empty JSON array")

    fields: list[dict[str, Any]] = []
    for index, raw_field in enumerate(payload):
        if not isinstance(raw_field, dict):
            raise ValueError(f"Schema field at index {index} must be an object")

        field = dict(raw_field)
        for key in ("name", "type"):
            value = field.get(key)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"Schema field at index {index} is missing {key}")
            field[key] = value.strip()

        mode = field.get("mode", "NULLABLE")
        if not isinstance(mode, str) or not mode.strip():
            raise ValueError(f"Schema field at index {index} has invalid mode")
        field["mode"] = mode.strip()

        description = field.get("description")
        if description is not None and not isinstance(description, str):
            raise ValueError(
                f"Schema field {field['name']} has non-string description"
            )

        fields.append(field)

    return fields


def to_bigquery_schema(
    raw_schema: Sequence[Mapping[str, Any]],
    bigquery_module: Any,
) -> list[Any]:
    return [
        bigquery_module.SchemaField(
            field["name"],
            field["type"],
            mode=field.get("mode", "NULLABLE"),
            description=field.get("description"),
        )
        for field in raw_schema
    ]


def ensure_dataset(
    client: Any,
    config: BigQueryCatalogConfig,
    bigquery_module: Any,
    not_found_error: type[Exception],
) -> str:
    try:
        client.get_dataset(config.dataset_fqn)
        return "already exists"
    except not_found_error:
        dataset = bigquery_module.Dataset(config.dataset_fqn)
        dataset.location = config.location
        client.create_dataset(dataset)
        return "created"


def ensure_table(
    client: Any,
    config: BigQueryCatalogConfig,
    schema: Sequence[Any],
    bigquery_module: Any,
    not_found_error: type[Exception],
) -> str:
    try:
        client.get_table(config.table_fqn)
        return "already exists"
    except not_found_error:
        table = bigquery_module.Table(config.table_fqn, schema=schema)
        client.create_table(table)
        return "created"


def print_selection(config: BigQueryCatalogConfig) -> None:
    print(f"Selected project: {config.project_id}")
    print(f"Dataset id: {config.dataset_fqn}")
    print(f"Table id: {config.table_fqn}")
    print(f"BigQuery location: {config.location}")
    print(f"Schema path: {config.schema_path}")


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    config = load_config(schema_path=args.schema_path)
    raw_schema = load_schema_fields(config.schema_path)

    print_selection(config)
    print(f"Schema fields: {len(raw_schema)}")

    if args.dry_run:
        print("Dry run: configuration and schema are valid; no GCP calls made.")
        return 0

    try:
        from google.api_core.exceptions import NotFound
        from google.cloud import bigquery
    except ImportError as exc:
        raise RuntimeError(
            "google-cloud-bigquery is required. Install dependencies with "
            "`pip install -r requirements.txt`."
        ) from exc

    client = bigquery.Client(project=config.project_id, location=config.location)
    schema = to_bigquery_schema(raw_schema, bigquery)

    dataset_status = ensure_dataset(client, config, bigquery, NotFound)
    print(f"Dataset {config.dataset_fqn}: {dataset_status}")

    table_status = ensure_table(client, config, schema, bigquery, NotFound)
    print(f"Table {config.table_fqn}: {table_status}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
