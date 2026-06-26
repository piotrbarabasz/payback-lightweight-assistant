"""Load the local synthetic product catalog into BigQuery."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.config import get_settings
from scripts.gcp.create_bigquery_catalog import (
    DEFAULT_SCHEMA_PATH,
    BigQueryCatalogConfig,
    load_config,
    load_schema_fields,
)


DEFAULT_CURRENCY = "EUR"
SUPPORTED_LOAD_MODES = {"append", "replace"}


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Load the local synthetic catalog into BigQuery.",
    )
    parser.add_argument(
        "--catalog-path",
        default=None,
        help="Path to products JSON. Defaults to CATALOG_PATH/app settings.",
    )
    parser.add_argument(
        "--schema-path",
        default=str(DEFAULT_SCHEMA_PATH),
        help="Path to the BigQuery JSON schema file.",
    )
    parser.add_argument(
        "--mode",
        choices=sorted(SUPPORTED_LOAD_MODES),
        default="append",
        help="append adds rows; replace truncates the table before loading.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate and print sample rows without calling GCP.",
    )
    parser.add_argument(
        "--sample-size",
        type=int,
        default=3,
        help="Number of transformed rows to print in dry-run mode.",
    )
    return parser.parse_args(argv)


def resolve_catalog_path(catalog_path: str | None = None) -> Path:
    if catalog_path:
        return Path(catalog_path)
    return Path(get_settings().CATALOG_PATH)


def load_catalog_payload(catalog_path: Path) -> list[dict[str, Any]]:
    if not catalog_path.exists():
        raise FileNotFoundError(f"Product catalog file does not exist: {catalog_path}")

    with catalog_path.open("r", encoding="utf-8") as catalog_file:
        payload = json.load(catalog_file)

    if not isinstance(payload, list):
        raise ValueError("Product catalog JSON must be an array")

    products: list[dict[str, Any]] = []
    for index, raw_product in enumerate(payload):
        if not isinstance(raw_product, dict):
            raise ValueError(f"Product at index {index} must be an object")
        products.append(raw_product)
    return products


def validate_product_record(product: Mapping[str, Any], index: int) -> None:
    product_id = _optional_text(product.get("product_id"))
    partner = _optional_text(product.get("partner"))
    name = _optional_text(product.get("name")) or _optional_text(product.get("title"))
    category = _optional_text(product.get("category"))

    errors: list[str] = []
    if not product_id:
        errors.append("product_id is required")
    if not partner:
        errors.append("partner is required")
    if not name:
        errors.append("name or title is required")
    if not category:
        errors.append("category is required")

    price = product.get("price")
    if price is None:
        errors.append("price is required")
    elif not _is_numeric(price):
        errors.append("price must be numeric")

    if errors:
        joined = "; ".join(errors)
        raise ValueError(f"Invalid product at index {index}: {joined}")


def validate_products(products: Sequence[Mapping[str, Any]]) -> None:
    seen_ids: set[str] = set()
    for index, product in enumerate(products):
        validate_product_record(product, index)
        product_id = _optional_text(product.get("product_id"))
        if product_id in seen_ids:
            raise ValueError(f"Invalid product at index {index}: duplicate product_id")
        seen_ids.add(product_id)


def transform_products(
    products: Sequence[Mapping[str, Any]],
    schema_fields: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    field_names = [field["name"] for field in schema_fields]
    rows: list[dict[str, Any]] = []

    for product in products:
        row = _base_row(product)
        row["embedding_text"] = build_embedding_text(row)
        row["embedding"] = []
        row["updated_at"] = None
        rows.append({field_name: row.get(field_name) for field_name in field_names})

    return rows


def build_embedding_text(product: Mapping[str, Any]) -> str:
    parts = [
        _optional_text(product.get("name")),
        _optional_text(product.get("brand")),
        _optional_text(product.get("partner")),
        _optional_text(product.get("category")),
        _optional_text(product.get("description")),
        _join_strings(product.get("tags")),
    ]
    return " ".join(part for part in parts if part)


def load_rows_to_bigquery(
    config: BigQueryCatalogConfig,
    rows: Sequence[Mapping[str, Any]],
    mode: str,
) -> int:
    try:
        from google.cloud import bigquery
    except ImportError as exc:
        raise RuntimeError(
            "google-cloud-bigquery is required. Install dependencies with "
            "`pip install -r requirements.txt`."
        ) from exc

    client = bigquery.Client(project=config.project_id, location=config.location)
    write_disposition = (
        bigquery.WriteDisposition.WRITE_TRUNCATE
        if mode == "replace"
        else bigquery.WriteDisposition.WRITE_APPEND
    )
    job_config = bigquery.LoadJobConfig(
        source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON,
        write_disposition=write_disposition,
    )
    load_job = client.load_table_from_json(
        list(rows),
        config.table_fqn,
        job_config=job_config,
    )
    load_job.result()
    return int(load_job.output_rows or len(rows))


def print_summary(
    catalog_path: Path,
    products_read: int,
    rows_loaded: int,
    config: BigQueryCatalogConfig,
) -> None:
    print(f"Source file: {catalog_path}")
    print(f"Products read: {products_read}")
    print(f"Products loaded: {rows_loaded}")
    print(f"Target table: {config.table_fqn}")


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    if args.sample_size < 0:
        raise ValueError("--sample-size must be zero or greater")

    config = load_config(schema_path=args.schema_path)
    schema_fields = load_schema_fields(config.schema_path)
    catalog_path = resolve_catalog_path(args.catalog_path)
    products = load_catalog_payload(catalog_path)
    validate_products(products)
    rows = transform_products(products, schema_fields)

    if args.dry_run:
        print_summary(catalog_path, len(products), 0, config)
        print("Dry run: validated and transformed rows; no GCP calls made.")
        sample_rows = rows[: args.sample_size]
        if sample_rows:
            print("Sample transformed rows:")
            print(json.dumps(sample_rows, indent=2, ensure_ascii=False))
        return 0

    rows_loaded = load_rows_to_bigquery(config, rows, args.mode)
    print_summary(catalog_path, len(products), rows_loaded, config)
    print(f"Load mode: {args.mode}")
    return 0


def _base_row(product: Mapping[str, Any]) -> dict[str, Any]:
    name = _required_text(product.get("name") or product.get("title"), "name")
    currency = _optional_text(product.get("currency")) or DEFAULT_CURRENCY

    return {
        "product_id": _required_text(product.get("product_id"), "product_id"),
        "partner": _required_text(product.get("partner"), "partner"),
        "name": name,
        "name_de": _optional_text(product.get("name_de")),
        "category": _required_text(product.get("category"), "category"),
        "description": _optional_text(product.get("description")) or "",
        "description_de": _optional_text(product.get("description_de")),
        "brand": _optional_text(product.get("brand")) or "",
        "price": float(product["price"]),
        "currency": currency.upper(),
        "tags": _string_list(product.get("tags")),
        "tags_de": _string_list(product.get("tags_de")),
        "availability": _optional_bool(product.get("availability")),
        "popularity_score": _optional_float(product.get("popularity_score")),
        "is_promotion": _optional_bool(product.get("is_promotion")),
        "product_url": _optional_text(product.get("product_url")),
    }


def _required_text(value: Any, field_name: str) -> str:
    text = _optional_text(value)
    if text is None:
        raise ValueError(f"{field_name} is required")
    return text


def _optional_text(value: Any) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        value = str(value)
    normalized = " ".join(value.strip().split())
    return normalized or None


def _is_numeric(value: Any) -> bool:
    if isinstance(value, bool):
        return False
    if isinstance(value, int | float):
        return True
    if isinstance(value, str) and value.strip():
        try:
            float(value)
        except ValueError:
            return False
        return True
    return False


def _optional_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    if not _is_numeric(value):
        raise ValueError(f"Expected numeric value, got {value!r}")
    return float(value)


def _optional_bool(value: Any) -> bool | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().casefold()
        if normalized in {"true", "1", "yes"}:
            return True
        if normalized in {"false", "0", "no"}:
            return False
    raise ValueError(f"Expected boolean value, got {value!r}")


def _string_list(value: Any) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise ValueError(f"Expected list of strings, got {value!r}")
    return [text for item in value if (text := _optional_text(item))]


def _join_strings(value: Any) -> str | None:
    strings = _string_list(value)
    if not strings:
        return None
    return ", ".join(strings)


if __name__ == "__main__":
    raise SystemExit(main())
