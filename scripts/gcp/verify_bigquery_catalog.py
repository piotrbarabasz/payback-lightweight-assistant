"""Verify the Stage 8A BigQuery product catalog table."""

from __future__ import annotations

import argparse
import os
from dataclasses import dataclass
from typing import Any, Mapping, Sequence


REQUIRED_ENV_VARS = (
    "GCP_PROJECT_ID",
    "BIGQUERY_DATASET",
    "BIGQUERY_PRODUCTS_TABLE",
)


@dataclass(frozen=True)
class BigQueryVerifyConfig:
    project_id: str
    dataset_id: str
    table_id: str

    @property
    def table_fqn(self) -> str:
        return f"{self.project_id}.{self.dataset_id}.{self.table_id}"

    @property
    def quoted_table(self) -> str:
        return quote_table_id(self.table_fqn)


@dataclass(frozen=True)
class CatalogVerificationResult:
    table_fqn: str
    total_count: int
    count_by_partner: list[dict[str, Any]]
    sample_rows: list[dict[str, Any]]
    missing_embedding_text_count: int


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Verify the Stage 8A BigQuery catalog table.",
    )
    parser.add_argument(
        "--sql-only",
        action="store_true",
        help="Print verification SQL without calling GCP.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Alias for --sql-only.",
    )
    return parser.parse_args(argv)


def load_config(env: Mapping[str, str] | None = None) -> BigQueryVerifyConfig:
    values = env if env is not None else os.environ
    missing = [
        name
        for name in REQUIRED_ENV_VARS
        if not values.get(name) or not values[name].strip()
    ]
    if missing:
        names = ", ".join(missing)
        raise ValueError(f"Missing required environment variables: {names}")

    return BigQueryVerifyConfig(
        project_id=values["GCP_PROJECT_ID"].strip(),
        dataset_id=values["BIGQUERY_DATASET"].strip(),
        table_id=values["BIGQUERY_PRODUCTS_TABLE"].strip(),
    )


def quote_table_id(table_fqn: str) -> str:
    if "`" in table_fqn:
        raise ValueError("BigQuery table id must not contain backticks")
    parts = table_fqn.split(".")
    if len(parts) != 3 or any(not part.strip() for part in parts):
        raise ValueError("BigQuery table id must be project.dataset.table")
    return f"`{table_fqn}`"


def build_verification_sql(config: BigQueryVerifyConfig) -> dict[str, str]:
    table = config.quoted_table
    return {
        "total_count": f"SELECT COUNT(*) AS total_count FROM {table}",
        "count_by_partner": (
            "SELECT partner, COUNT(*) AS product_count\n"
            f"FROM {table}\n"
            "GROUP BY partner\n"
            "ORDER BY product_count DESC, partner"
        ),
        "sample_rows": (
            "SELECT product_id, partner, name, category, brand, price, currency, "
            "availability, is_promotion, embedding_text\n"
            f"FROM {table}\n"
            "ORDER BY partner, product_id\n"
            "LIMIT 5"
        ),
        "missing_embedding_text_count": (
            "SELECT COUNT(*) AS missing_embedding_text_count\n"
            f"FROM {table}\n"
            "WHERE embedding_text IS NULL OR TRIM(embedding_text) = ''"
        ),
    }


def query_catalog_verification(
    client: Any,
    config: BigQueryVerifyConfig,
) -> CatalogVerificationResult:
    sql = build_verification_sql(config)
    total_count = _single_int_query(client, sql["total_count"], "total_count")
    if total_count <= 0:
        raise ValueError(f"BigQuery catalog table is empty: {config.table_fqn}")

    return CatalogVerificationResult(
        table_fqn=config.table_fqn,
        total_count=total_count,
        count_by_partner=_rows_to_dicts(client.query(sql["count_by_partner"]).result()),
        sample_rows=_rows_to_dicts(client.query(sql["sample_rows"]).result()),
        missing_embedding_text_count=_single_int_query(
            client,
            sql["missing_embedding_text_count"],
            "missing_embedding_text_count",
        ),
    )


def print_sql(config: BigQueryVerifyConfig) -> None:
    print(f"Target table: {config.table_fqn}")
    print("SQL only: no GCP calls made.")
    for label, statement in build_verification_sql(config).items():
        print()
        print(f"-- {label}")
        print(statement)


def print_result(result: CatalogVerificationResult) -> None:
    print("Stage 8A BigQuery Catalog Verification")
    print(f"Target table: {result.table_fqn}")
    print(f"Total product count: {result.total_count}")
    print(f"Missing embedding_text count: {result.missing_embedding_text_count}")
    print()
    print("Count by partner:")
    if result.count_by_partner:
        for row in result.count_by_partner:
            print(f"- {row.get('partner')}: {row.get('product_count')}")
    else:
        print("- none")
    print()
    print("Sample rows:")
    for row in result.sample_rows:
        print(
            "- "
            f"{row.get('product_id')} | "
            f"{row.get('partner')} | "
            f"{row.get('name')} | "
            f"{row.get('category')} | "
            f"{row.get('price')} {row.get('currency')}"
        )


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    config = load_config()

    if args.sql_only or args.dry_run:
        print_sql(config)
        return 0

    try:
        from google.api_core.exceptions import NotFound
        from google.cloud import bigquery
    except ImportError as exc:
        raise RuntimeError(
            "google-cloud-bigquery is required. Install dependencies with "
            "`pip install -r requirements.txt`."
        ) from exc

    client = bigquery.Client(project=config.project_id)
    try:
        client.get_table(config.table_fqn)
    except NotFound as exc:
        raise ValueError(f"BigQuery catalog table does not exist: {config.table_fqn}") from exc

    result = query_catalog_verification(client, config)
    print_result(result)
    return 0


def _single_int_query(client: Any, sql: str, field_name: str) -> int:
    rows = list(client.query(sql).result())
    if not rows:
        raise ValueError(f"Query returned no rows for {field_name}")
    value = _row_to_dict(rows[0]).get(field_name)
    if value is None:
        raise ValueError(f"Query result is missing {field_name}")
    return int(value)


def _rows_to_dicts(rows: Any) -> list[dict[str, Any]]:
    return [_row_to_dict(row) for row in rows]


def _row_to_dict(row: Any) -> dict[str, Any]:
    if isinstance(row, dict):
        return dict(row)
    if hasattr(row, "items"):
        return dict(row.items())
    return dict(row)


if __name__ == "__main__":
    raise SystemExit(main())
