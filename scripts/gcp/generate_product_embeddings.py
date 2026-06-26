"""Generate Vertex AI embeddings for BigQuery catalog products."""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.embeddings.vertex_ai import VertexAIEmbeddingProvider
from scripts.gcp.create_bigquery_catalog import BigQueryCatalogConfig, load_config
from scripts.gcp.verify_bigquery_catalog import quote_table_id


DEFAULT_LIMIT = 10
DEFAULT_BATCH_SIZE = 5


@dataclass(frozen=True)
class EmbeddingCandidate:
    product_id: str
    embedding_text: str


@dataclass(frozen=True)
class EmbeddingGenerationSummary:
    rows_selected: int
    embeddings_generated: int
    rows_updated: int
    failures: int


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate Vertex AI embeddings for BigQuery product rows.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=DEFAULT_LIMIT,
        help=(
            "Maximum rows to process. Defaults to 10 for cost safety. "
            "Use 0 only with --refresh --allow-full-refresh for no limit."
        ),
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print SQL and configuration without calling BigQuery or Vertex AI.",
    )
    parser.add_argument(
        "--refresh",
        action="store_true",
        help="Regenerate embeddings even when the embedding column is populated.",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=DEFAULT_BATCH_SIZE,
        help="Number of product texts to send to Vertex AI per embedding call.",
    )
    parser.add_argument(
        "--allow-full-refresh",
        action="store_true",
        help="Required with --refresh --limit 0 to process all matching rows.",
    )
    return parser.parse_args(argv)


def validate_args(args: argparse.Namespace) -> None:
    if args.limit < 0:
        raise ValueError("--limit must be zero or greater")
    if args.batch_size < 1:
        raise ValueError("--batch-size must be at least 1")
    if args.limit == 0 and not (args.refresh and args.allow_full_refresh):
        raise ValueError(
            "--limit 0 disables the row cap and requires both --refresh "
            "and --allow-full-refresh"
        )


def build_selection_sql(
    config: BigQueryCatalogConfig,
    *,
    limit: int,
    refresh: bool,
) -> str:
    table = quote_table_id(config.table_fqn)
    embedding_filter = (
        "TRUE"
        if refresh
        else "(embedding IS NULL OR ARRAY_LENGTH(embedding) = 0)"
    )
    limit_clause = "" if limit == 0 else f"\nLIMIT {limit}"
    return (
        "SELECT product_id, embedding_text\n"
        f"FROM {table}\n"
        "WHERE embedding_text IS NOT NULL\n"
        "  AND TRIM(embedding_text) != ''\n"
        f"  AND {embedding_filter}\n"
        "ORDER BY partner, product_id"
        f"{limit_clause}"
    )


def build_update_sql(config: BigQueryCatalogConfig) -> str:
    table = quote_table_id(config.table_fqn)
    return (
        f"UPDATE {table}\n"
        "SET embedding = @embedding,\n"
        "    updated_at = CURRENT_TIMESTAMP()\n"
        "WHERE product_id = @product_id"
    )


def select_embedding_candidates(
    client: Any,
    config: BigQueryCatalogConfig,
    *,
    limit: int,
    refresh: bool,
) -> list[EmbeddingCandidate]:
    sql = build_selection_sql(config, limit=limit, refresh=refresh)
    rows = client.query(sql).result()
    return [_candidate_from_row(row) for row in rows]


def build_update_payload(
    candidates: Sequence[EmbeddingCandidate],
    embeddings: Sequence[Sequence[float]],
) -> list[dict[str, Any]]:
    if len(candidates) != len(embeddings):
        raise ValueError(
            "Embedding count must match selected product count: "
            f"{len(embeddings)} embeddings for {len(candidates)} products"
        )

    payload: list[dict[str, Any]] = []
    for candidate, embedding in zip(candidates, embeddings):
        values = [float(value) for value in embedding]
        if not values:
            raise ValueError(f"Embedding for {candidate.product_id} must not be empty")
        payload.append(
            {
                "product_id": candidate.product_id,
                "embedding": values,
            }
        )
    return payload


def update_product_embeddings(
    client: Any,
    config: BigQueryCatalogConfig,
    payload: Sequence[Mapping[str, Any]],
    bigquery_module: Any,
) -> int:
    sql = build_update_sql(config)
    rows_updated = 0

    for row in payload:
        job_config = bigquery_module.QueryJobConfig(
            query_parameters=[
                bigquery_module.ScalarQueryParameter(
                    "product_id",
                    "STRING",
                    row["product_id"],
                ),
                bigquery_module.ArrayQueryParameter(
                    "embedding",
                    "FLOAT64",
                    list(row["embedding"]),
                ),
            ]
        )
        query_job = client.query(sql, job_config=job_config)
        query_job.result()
        affected_rows = getattr(query_job, "num_dml_affected_rows", None)
        rows_updated += int(affected_rows) if affected_rows is not None else 1

    return rows_updated


def generate_product_embeddings(
    client: Any,
    config: BigQueryCatalogConfig,
    embedding_provider: Any,
    bigquery_module: Any,
    *,
    limit: int,
    refresh: bool,
    batch_size: int,
) -> EmbeddingGenerationSummary:
    candidates = select_embedding_candidates(
        client,
        config,
        limit=limit,
        refresh=refresh,
    )
    embeddings_generated = 0
    rows_updated = 0
    failures = 0

    for batch in split_batches(candidates, batch_size):
        try:
            texts = [candidate.embedding_text for candidate in batch]
            embeddings = embedding_provider.embed_texts(texts)
            payload = build_update_payload(batch, embeddings)
            embeddings_generated += len(embeddings)
            rows_updated += update_product_embeddings(
                client,
                config,
                payload,
                bigquery_module,
            )
        except Exception as exc:
            failures += len(batch)
            print(
                "Failed embedding batch: "
                f"{batch[0].product_id}..{batch[-1].product_id}: {exc}",
                file=sys.stderr,
            )

    return EmbeddingGenerationSummary(
        rows_selected=len(candidates),
        embeddings_generated=embeddings_generated,
        rows_updated=rows_updated,
        failures=failures,
    )


def split_batches(
    candidates: Sequence[EmbeddingCandidate],
    batch_size: int,
) -> list[list[EmbeddingCandidate]]:
    if batch_size < 1:
        raise ValueError("batch_size must be at least 1")
    return [
        list(candidates[index : index + batch_size])
        for index in range(0, len(candidates), batch_size)
    ]


def print_dry_run(config: BigQueryCatalogConfig, args: argparse.Namespace) -> None:
    print("Stage 8B Product Embedding Generation")
    print(f"Target table: {config.table_fqn}")
    print(f"Refresh existing embeddings: {args.refresh}")
    print(f"Limit: {'unlimited' if args.limit == 0 else args.limit}")
    print(f"Batch size: {args.batch_size}")
    print("Dry run: no BigQuery or Vertex AI calls made.")
    print()
    print("-- selection_sql")
    print(build_selection_sql(config, limit=args.limit, refresh=args.refresh))
    print()
    print("Rows selected: 0 (dry run)")
    print("Embeddings generated: 0")
    print("Rows updated: 0")
    print("Failures: 0")


def print_summary(summary: EmbeddingGenerationSummary) -> None:
    print("Stage 8B Product Embedding Generation")
    print(f"Rows selected: {summary.rows_selected}")
    print(f"Embeddings generated: {summary.embeddings_generated}")
    print(f"Rows updated: {summary.rows_updated}")
    print(f"Failures: {summary.failures}")


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    validate_args(args)
    config = load_config()

    if args.dry_run:
        print_dry_run(config, args)
        return 0

    try:
        from google.cloud import bigquery
    except ImportError as exc:
        raise RuntimeError(
            "google-cloud-bigquery is required. Install dependencies with "
            "`pip install -r requirements.txt`."
        ) from exc

    client = bigquery.Client(project=config.project_id, location=config.location)
    provider = VertexAIEmbeddingProvider()
    summary = generate_product_embeddings(
        client,
        config,
        provider,
        bigquery,
        limit=args.limit,
        refresh=args.refresh,
        batch_size=args.batch_size,
    )
    print_summary(summary)
    return 1 if summary.failures else 0


def _candidate_from_row(row: Any) -> EmbeddingCandidate:
    row_dict = _row_to_dict(row)
    product_id = _required_text(row_dict.get("product_id"), "product_id")
    embedding_text = _required_text(row_dict.get("embedding_text"), "embedding_text")
    return EmbeddingCandidate(product_id=product_id, embedding_text=embedding_text)


def _row_to_dict(row: Any) -> dict[str, Any]:
    if isinstance(row, dict):
        return dict(row)
    if hasattr(row, "items"):
        return dict(row.items())
    return dict(row)


def _required_text(value: Any, field_name: str) -> str:
    if value is None:
        raise ValueError(f"{field_name} is required")
    text = str(value).strip()
    if not text:
        raise ValueError(f"{field_name} is required")
    return text


if __name__ == "__main__":
    raise SystemExit(main())
