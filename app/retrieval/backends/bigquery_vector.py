"""BigQuery Vector Search product retrieval backend."""

from __future__ import annotations

import os
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Any

from app.config import get_settings
from app.embeddings.vertex_ai import VertexAIEmbeddingProvider
from app.retrieval.base import ProductRetriever
from app.retrieval.normalizer import QueryAnalysis, normalize_query
from app.schemas import Partner, Product, ProductResult


DEFAULT_VECTOR_TOP_K = 25


@dataclass(frozen=True)
class BigQueryVectorConfig:
    """Configuration required for BigQuery Vector Search retrieval."""

    project_id: str
    dataset_id: str
    table_id: str
    location: str = "europe-west1"
    vector_top_k: int = DEFAULT_VECTOR_TOP_K

    @property
    def table_fqn(self) -> str:
        return f"{self.project_id}.{self.dataset_id}.{self.table_id}"

    @property
    def quoted_table(self) -> str:
        return quote_table_id(self.table_fqn)

    @classmethod
    def from_env(cls) -> BigQueryVectorConfig:
        settings = get_settings()
        project_id = _env_optional("GCP_PROJECT_ID") or settings.GCP_PROJECT_ID
        dataset_id = _env_optional("BIGQUERY_DATASET") or settings.BIGQUERY_DATASET
        table_id = (
            _env_optional("BIGQUERY_PRODUCTS_TABLE")
            or settings.BIGQUERY_PRODUCTS_TABLE
        )
        location = _env_optional("BIGQUERY_LOCATION") or settings.BIGQUERY_LOCATION
        vector_top_k = _env_optional_int(
            "BIGQUERY_VECTOR_TOP_K",
            settings.BIGQUERY_VECTOR_TOP_K,
        )

        missing = []
        if not project_id:
            missing.append("GCP_PROJECT_ID")
        if not dataset_id:
            missing.append("BIGQUERY_DATASET")
        if not table_id:
            missing.append("BIGQUERY_PRODUCTS_TABLE")
        if missing:
            names = ", ".join(missing)
            raise ValueError(
                "BigQuery Vector Search retrieval requires environment variables: "
                f"{names}. The default local retrieval backend remains keyword."
            )
        if vector_top_k < 1:
            raise ValueError("BIGQUERY_VECTOR_TOP_K must be at least 1")

        return cls(
            project_id=project_id,
            dataset_id=dataset_id,
            table_id=table_id,
            location=location,
            vector_top_k=vector_top_k,
        )


ClientFactory = Callable[[BigQueryVectorConfig], Any]


class BigQueryVectorProductRetriever(ProductRetriever):
    """Product retriever backed by Vertex query embeddings and BigQuery SQL."""

    def __init__(
        self,
        config: BigQueryVectorConfig | None = None,
        *,
        client: Any | None = None,
        client_factory: ClientFactory | None = None,
        embedding_provider: Any | None = None,
        bigquery_module: Any | None = None,
    ) -> None:
        self._config = config
        self._client = client
        self._client_factory = client_factory or _default_client_factory
        self._embedding_provider = embedding_provider
        self._bigquery = bigquery_module

    def retrieve(
        self,
        query: str,
        products: list[Product],
        top_k: int = 5,
        intent_analysis: QueryAnalysis | None = None,
    ) -> list[ProductResult]:
        """Return product results from BigQuery Vector Search."""

        if top_k < 1:
            return []

        analysis = intent_analysis or normalize_query(query)
        config = self._get_config()
        query_embedding = self._embed_query(query)
        if not query_embedding:
            raise RuntimeError("Vertex AI query embedding was empty")

        vector_top_k = max(top_k, config.vector_top_k)
        sql = build_vector_search_sql(
            config,
            vector_top_k=vector_top_k,
            result_limit=top_k,
            partner_hint=analysis.partner_hint,
            category_hints=analysis.category_hints,
        )
        job_config = self._build_query_job_config(
            query_embedding=query_embedding,
            vector_top_k=vector_top_k,
            result_limit=top_k,
            partner_hint=analysis.partner_hint,
            category_hints=analysis.category_hints,
        )

        try:
            rows = self._get_client().query(sql, job_config=job_config).result()
        except Exception as exc:
            raise RuntimeError(
                "BigQuery Vector Search query failed. "
                "Check BigQuery permissions, vector index/table setup, "
                "and product embeddings."
            ) from exc

        results = [row_to_product_result(row) for row in rows]
        if not results:
            raise RuntimeError(
                "BigQuery Vector Search returned no products. "
                "Check that product embeddings exist and match the query filters."
            )
        return results[:top_k]

    def _get_config(self) -> BigQueryVectorConfig:
        if self._config is None:
            self._config = BigQueryVectorConfig.from_env()
        return self._config

    def _get_client(self) -> Any:
        if self._client is None:
            self._client = self._client_factory(self._get_config())
        return self._client

    def _get_embedding_provider(self) -> Any:
        if self._embedding_provider is None:
            self._embedding_provider = VertexAIEmbeddingProvider()
        return self._embedding_provider

    def _get_bigquery_module(self) -> Any:
        if self._bigquery is None:
            try:
                from google.cloud import bigquery
            except ImportError as exc:
                raise RuntimeError(
                    "google-cloud-bigquery is required for BigQuery Vector Search. "
                    "Install dependencies with `pip install -r requirements.txt`."
                ) from exc
            self._bigquery = bigquery
        return self._bigquery

    def _embed_query(self, query: str) -> list[float]:
        try:
            return self._get_embedding_provider().embed_text(query)
        except Exception as exc:
            raise RuntimeError("Vertex AI query embedding failed") from exc

    def _build_query_job_config(
        self,
        *,
        query_embedding: Sequence[float],
        vector_top_k: int,
        result_limit: int,
        partner_hint: Partner | None,
        category_hints: Sequence[str],
    ) -> Any:
        bigquery = self._get_bigquery_module()
        parameters: list[Any] = [
            bigquery.ArrayQueryParameter(
                "query_embedding",
                "FLOAT64",
                [float(value) for value in query_embedding],
            ),
            bigquery.ScalarQueryParameter("vector_top_k", "INT64", vector_top_k),
            bigquery.ScalarQueryParameter("result_limit", "INT64", result_limit),
        ]
        if _is_concrete_partner(partner_hint):
            parameters.append(
                bigquery.ScalarQueryParameter(
                    "partner",
                    "STRING",
                    partner_hint.value,
                )
            )
        if category_hints:
            parameters.append(
                bigquery.ArrayQueryParameter(
                    "categories",
                    "STRING",
                    list(category_hints),
                )
            )
        return bigquery.QueryJobConfig(query_parameters=parameters)


def build_vector_search_sql(
    config: BigQueryVectorConfig,
    *,
    vector_top_k: int,
    result_limit: int,
    partner_hint: Partner | None = None,
    category_hints: Sequence[str] = (),
) -> str:
    if vector_top_k < 1:
        raise ValueError("vector_top_k must be at least 1")
    if result_limit < 1:
        raise ValueError("result_limit must be at least 1")

    filters = ["availability = TRUE"]
    if _is_concrete_partner(partner_hint):
        filters.append("partner = @partner")
    if category_hints:
        filters.append("category IN UNNEST(@categories)")

    where_clause = "\n          AND ".join(filters)
    return (
        "SELECT\n"
        "  base.product_id AS product_id,\n"
        "  base.partner AS partner,\n"
        "  base.name AS name,\n"
        "  base.category AS category,\n"
        "  base.price AS price,\n"
        "  base.currency AS currency,\n"
        "  distance AS vector_distance\n"
        "FROM VECTOR_SEARCH(\n"
        "  (\n"
        "    SELECT product_id, partner, name, category, price, currency, "
        "availability, embedding\n"
        f"    FROM {config.quoted_table}\n"
        f"    WHERE {where_clause}\n"
        "  ),\n"
        "  'embedding',\n"
        "  query_value => @query_embedding,\n"
        "  top_k => @vector_top_k,\n"
        "  distance_type => 'COSINE'\n"
        ")\n"
        "ORDER BY vector_distance ASC, product_id\n"
        "LIMIT @result_limit"
    )


def row_to_product_result(row: Any) -> ProductResult:
    row_dict = _row_to_dict(row)
    distance = _optional_float(
        row_dict.get("vector_distance", row_dict.get("distance")),
    )
    return ProductResult(
        product_id=_required_text(row_dict.get("product_id"), "product_id"),
        partner=Partner(_required_text(row_dict.get("partner"), "partner")),
        name=_required_text(row_dict.get("name"), "name"),
        category=_required_text(row_dict.get("category"), "category"),
        price=_required_float(row_dict.get("price"), "price"),
        currency=_optional_text(row_dict.get("currency")) or "EUR",
        score=_score_from_distance(distance),
        reason=_reason_from_distance(distance),
    )


def quote_table_id(table_fqn: str) -> str:
    if "`" in table_fqn:
        raise ValueError("BigQuery table id must not contain backticks")
    parts = table_fqn.split(".")
    if len(parts) != 3 or any(not part.strip() for part in parts):
        raise ValueError("BigQuery table id must be project.dataset.table")
    return f"`{table_fqn}`"


def _default_client_factory(config: BigQueryVectorConfig) -> Any:
    try:
        from google.cloud import bigquery
    except ImportError as exc:
        raise RuntimeError(
            "google-cloud-bigquery is required for BigQuery Vector Search. "
            "Install dependencies with `pip install -r requirements.txt`."
        ) from exc
    return bigquery.Client(project=config.project_id, location=config.location)


def _is_concrete_partner(partner: Partner | None) -> bool:
    return partner is not None and partner != Partner.UNKNOWN


def _score_from_distance(distance: float | None) -> float:
    if distance is None:
        return 0.0
    return max(0.0, min(1.0, 1.0 - distance))


def _reason_from_distance(distance: float | None) -> str:
    if distance is None:
        return "Matched by BigQuery Vector Search using Vertex AI query embedding."
    return (
        "Matched by BigQuery Vector Search using Vertex AI query embedding "
        f"(cosine distance {distance:.4f})."
    )


def _row_to_dict(row: Any) -> dict[str, Any]:
    if isinstance(row, dict):
        return dict(row)
    if hasattr(row, "items"):
        return dict(row.items())
    return dict(row)


def _required_text(value: Any, field_name: str) -> str:
    text = _optional_text(value)
    if text is None:
        raise ValueError(f"BigQuery Vector Search row is missing {field_name}")
    return text


def _optional_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _required_float(value: Any, field_name: str) -> float:
    if value is None:
        raise ValueError(f"BigQuery Vector Search row is missing {field_name}")
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(
            f"BigQuery Vector Search row has invalid {field_name}: {value!r}"
        ) from exc


def _optional_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(
            f"BigQuery Vector Search row has invalid vector_distance: {value!r}"
        ) from exc


def _env_optional(name: str) -> str:
    value = os.getenv(name)
    if value is None:
        return ""
    return value.strip()


def _env_optional_int(name: str, default: int) -> int:
    value = _env_optional(name)
    if not value:
        return default
    try:
        return int(value)
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer") from exc
