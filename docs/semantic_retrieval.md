# Semantic Retrieval

## Purpose

Stage 7A introduced a retrieval backend abstraction and a local hybrid retrieval prototype. Stage 8 keeps the local prototype while adding an optional managed BigQuery Vector Search backend.

The goal is to keep retrieval pluggable: local keyword retrieval remains the default, local hybrid remains a prototype, and managed vector retrieval can be enabled explicitly.

The public API response schema is unchanged. Retrieval still returns `ProductResult` objects through the existing assistant response.

The default runtime does not use Vertex AI, BigQuery, BigQuery Vector Search, real partner APIs, or an autonomous LLM agent loop. The optional `bigquery_vector` backend uses Vertex AI and BigQuery when configured.

## Why Retrieval Backends Were Introduced

The original retrieval flow was keyword-only and directly coupled to the assistant orchestration. That worked for the first MVP, but it made future retrieval experiments harder to isolate.

The backend abstraction makes retrieval pluggable:

- `KeywordProductRetriever` keeps the existing deterministic behavior.
- `HybridProductRetriever` can be selected locally for semantic-like experiments.
- Managed production-oriented backends can be added behind the same interface.

This keeps the FastAPI endpoint and assistant response builder stable while allowing retrieval internals to evolve.

## Available Backends

### `keyword`

`keyword` is the default backend.

It uses the existing deterministic retrieval signals:

- keyword overlap,
- partner hints,
- category hints,
- price preference,
- promotion boost,
- popularity boost.

This is the backend used when `RETRIEVAL_BACKEND` is not set, including the low-cost Cloud Run deployment.

### `hybrid`

`hybrid` is a deterministic local prototype backend.

It combines:

- keyword score,
- local semantic-like similarity,
- existing business boosts such as partner hint, category hint, price preference, promotion, and popularity.

The hybrid backend uses local deterministic hash embeddings only. It does not call external APIs, does not require ML model downloads, and does not create or query a vector index.

### `bigquery_vector`

`bigquery_vector` is the optional managed semantic retrieval backend.

It uses:

- Vertex AI to embed the user query,
- BigQuery `VECTOR_SEARCH` over stored product embeddings,
- existing partner and category hints as metadata filters,
- the existing `ProductResult` response schema.

It requires Stage 8 GCP environment variables, product embeddings, and service
account permissions. It is not enabled by default.

## Local Embedding Provider

The local embedding provider is `LocalHashEmbeddingProvider`.

It is designed for tests and local experiments:

- deterministic,
- standard-library only,
- no network calls,
- no external model dependency,
- suitable for simple cosine-similarity experiments.

It is not a production embedding model and should not be treated as equivalent to Vertex AI embeddings or another trained semantic embedding model. Its purpose is to exercise the retrieval interface and ranking flow locally.

## Product Text

Products are converted into deterministic natural-language text before local embedding.

The product text includes fields such as:

- product name,
- German product name,
- partner,
- category,
- brand,
- description,
- German description,
- tags,
- German tags,
- price and currency,
- availability,
- promotion information.

This gives both local and managed embedding backends a stable product text input while keeping catalog schema and API responses unchanged.

## Running Hybrid Retrieval Locally

Use the `RETRIEVAL_BACKEND` environment variable.

Unix/macOS:

```bash
RETRIEVAL_BACKEND=hybrid uvicorn app.main:app --reload
```

Windows PowerShell:

```powershell
$env:RETRIEVAL_BACKEND = "hybrid"
uvicorn app.main:app --reload
```

Docker:

```bash
docker run --rm -p 8080:8080 -e PORT=8080 -e RETRIEVAL_BACKEND=hybrid payback-lightweight-assistant
```

To return to the default behavior, unset `RETRIEVAL_BACKEND` or set it to `keyword`.

## Cloud Run Cost Posture

The low-cost Cloud Run deployment does not require any new environment variables.

By default:

- `RETRIEVAL_BACKEND=keyword`,
- no Vertex AI calls are made,
- no BigQuery or BigQuery Vector Search calls are made,
- the synthetic catalog remains packaged in the container,
- retrieval remains in-process and deterministic.

This keeps the Stage 6 Cloud Run deployment path unchanged.

## Stage 8 Managed Retrieval Path

Stage 8 adds a managed retrieval path that can:

1. Generate product embeddings offline during catalog ingestion.
2. Store product metadata and embeddings in BigQuery.
3. Generate query embeddings at request time with Vertex AI.
4. Retrieve candidates with BigQuery Vector Search.
5. Return results through the existing assistant response schema.

Remaining production hardening includes observability, fallback behavior, IAM review, and ingestion scheduling.
