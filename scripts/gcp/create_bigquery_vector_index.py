"""Create an optional BigQuery vector index for product embeddings."""

from __future__ import annotations

import argparse
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.gcp.create_bigquery_catalog import BigQueryCatalogConfig, load_config
from scripts.gcp.verify_bigquery_catalog import quote_table_id


DEFAULT_INDEX_NAME = "products_embedding_idx"
DEFAULT_STORED_COLUMNS = (
    "product_id",
    "partner",
    "name",
    "category",
    "price",
    "currency",
    "availability",
)
SUPPORTED_INDEX_TYPES = {"IVF"}
IDENTIFIER_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


@dataclass(frozen=True)
class VectorIndexConfig:
    catalog: BigQueryCatalogConfig
    index_name: str = DEFAULT_INDEX_NAME
    index_type: str = "IVF"
    distance_type: str = "COSINE"
    stored_columns: tuple[str, ...] = DEFAULT_STORED_COLUMNS
    num_lists: int | None = None


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create an optional BigQuery vector index on product embeddings.",
    )
    parser.add_argument(
        "--index-name",
        default=None,
        help=(
            "Vector index name. Defaults to BIGQUERY_VECTOR_INDEX or "
            f"{DEFAULT_INDEX_NAME}."
        ),
    )
    parser.add_argument(
        "--index-type",
        choices=sorted(SUPPORTED_INDEX_TYPES),
        default="IVF",
        help="BigQuery vector index type.",
    )
    parser.add_argument(
        "--distance-type",
        default="COSINE",
        choices=["COSINE", "DOT_PRODUCT", "EUCLIDEAN"],
        help="Distance type used by the index.",
    )
    parser.add_argument(
        "--stored-columns",
        default=",".join(DEFAULT_STORED_COLUMNS),
        help="Comma-separated columns to store in the vector index.",
    )
    parser.add_argument(
        "--num-lists",
        type=int,
        default=None,
        help=(
            "Optional IVF num_lists setting. Leave unset until catalog scale "
            "and recall/latency targets are known."
        ),
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print SQL without calling BigQuery.",
    )
    parser.add_argument(
        "--sql-only",
        action="store_true",
        help="Alias for --dry-run.",
    )
    return parser.parse_args(argv)


def load_vector_index_config(
    env: Mapping[str, str] | None = None,
    *,
    index_name: str | None = None,
    index_type: str = "IVF",
    distance_type: str = "COSINE",
    stored_columns: str | Sequence[str] = DEFAULT_STORED_COLUMNS,
    num_lists: int | None = None,
) -> VectorIndexConfig:
    values = env if env is not None else os.environ
    catalog = load_config(env=values)
    selected_index_name = (
        index_name
        or values.get("BIGQUERY_VECTOR_INDEX", "").strip()
        or DEFAULT_INDEX_NAME
    )
    columns = (
        parse_stored_columns(stored_columns)
        if isinstance(stored_columns, str)
        else tuple(stored_columns)
    )

    validate_identifier(selected_index_name, "index name")
    validate_identifier_list(columns, "stored column")
    if num_lists is not None and num_lists < 1:
        raise ValueError("--num-lists must be at least 1")

    return VectorIndexConfig(
        catalog=catalog,
        index_name=selected_index_name,
        index_type=index_type.upper(),
        distance_type=distance_type.upper(),
        stored_columns=columns,
        num_lists=num_lists,
    )


def build_create_vector_index_sql(config: VectorIndexConfig) -> str:
    table = quote_table_id(config.catalog.table_fqn)
    stored_columns = ", ".join(config.stored_columns)
    options = [
        f"index_type = '{config.index_type}'",
        f"distance_type = '{config.distance_type}'",
    ]
    if config.num_lists is not None:
        options.append(f"ivf_options = '{{\"num_lists\": {config.num_lists}}}'")

    options_sql = ",\n  ".join(options)
    return (
        "-- Optional Stage 8C vector index for production-scale catalogs.\n"
        "-- VECTOR_SEARCH can work without this index on small tables, but may be slower.\n"
        "-- The index improves search latency at the cost of build and maintenance work.\n"
        f"CREATE VECTOR INDEX IF NOT EXISTS {config.index_name}\n"
        f"ON {table}(embedding)\n"
        f"STORING ({stored_columns})\n"
        "OPTIONS (\n"
        f"  {options_sql}\n"
        ");"
    )


def create_vector_index(client: Any, config: VectorIndexConfig) -> str:
    sql = build_create_vector_index_sql(config)
    job = client.query(sql)
    job.result()
    return sql


def print_plan(config: VectorIndexConfig) -> None:
    print("Stage 8C BigQuery Vector Index")
    print(f"Target table: {config.catalog.table_fqn}")
    print(f"Index name: {config.index_name}")
    print(f"Index type: {config.index_type}")
    print(f"Distance type: {config.distance_type}")
    print(f"Stored columns: {', '.join(config.stored_columns)}")
    print(f"Num lists: {config.num_lists if config.num_lists is not None else 'default'}")
    print()
    print(build_create_vector_index_sql(config))


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    config = load_vector_index_config(
        index_name=args.index_name,
        index_type=args.index_type,
        distance_type=args.distance_type,
        stored_columns=args.stored_columns,
        num_lists=args.num_lists,
    )

    if args.dry_run or args.sql_only:
        print_plan(config)
        print()
        print("Dry run: SQL rendered; no BigQuery calls made.")
        return 0

    try:
        from google.cloud import bigquery
    except ImportError as exc:
        raise RuntimeError(
            "google-cloud-bigquery is required. Install dependencies with "
            "`pip install -r requirements.txt`."
        ) from exc

    client = bigquery.Client(
        project=config.catalog.project_id,
        location=config.catalog.location,
    )
    create_vector_index(client, config)
    print_plan(config)
    print()
    print("Vector index creation submitted. BigQuery may populate it asynchronously.")
    return 0


def parse_stored_columns(value: str) -> tuple[str, ...]:
    columns = tuple(column.strip() for column in value.split(",") if column.strip())
    if not columns:
        raise ValueError("--stored-columns must contain at least one column")
    return columns


def validate_identifier(value: str, label: str) -> None:
    if not IDENTIFIER_PATTERN.fullmatch(value):
        raise ValueError(
            f"Invalid {label}: {value!r}. Use letters, numbers, and underscores, "
            "starting with a letter or underscore."
        )


def validate_identifier_list(values: Sequence[str], label: str) -> None:
    for value in values:
        validate_identifier(value, label)


if __name__ == "__main__":
    raise SystemExit(main())
