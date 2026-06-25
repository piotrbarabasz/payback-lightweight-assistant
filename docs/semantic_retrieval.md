# Semantic Retrieval

## Purpose

Stage 7A introduced a retrieval backend abstraction and a local hybrid retrieval prototype. Stage 7B keeps that implementation as a local-only prototype and documents the boundary before future Stage 8 GCP work.

The goal is to prepare the codebase for future semantic retrieval without claiming that production vector search, Vertex AI, or BigQuery Vector Search is already implemented.

The public API response schema is unchanged. Retrieval still returns `ProductResult` objects through the existing assistant response.

The current Stage 7B runtime does not use Vertex AI, BigQuery, BigQuery Vector Search, real partner APIs, or an autonomous LLM agent loop.

## Why Retrieval Backends Were Introduced

The original retrieval flow was keyword-only and directly coupled to the assistant orchestration. That worked for the first MVP, but it made future retrieval experiments harder to isolate.

The backend abstraction makes retrieval pluggable:

- `KeywordProductRetriever` keeps the existing deterministic behavior.
- `HybridProductRetriever` can be selected locally for semantic-like experiments.
- Future production backends can be added behind the same interface.

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

## Local Embedding Provider

The local embedding provider is `LocalHashEmbeddingProvider`.

It is designed for tests and local experiments:

- deterministic,
- standard-library only,
- no network calls,
- no external model dependency,
- suitable for simple cosine-similarity experiments.

It is not a production embedding model and should not be treated as equivalent to Vertex AI embeddings or another trained semantic embedding model. Its purpose is to exercise the retrieval interface and ranking flow before Stage 8.

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

This gives future embedding backends a stable product text input while keeping catalog schema and API responses unchanged.

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

## Future Stage 8 Production Extensions

Vertex AI embeddings, BigQuery product storage, and BigQuery Vector Search remain future Stage 8 production extensions.

A future production architecture could:

1. Generate product embeddings offline during catalog ingestion.
2. Store product metadata and embeddings in BigQuery.
3. Generate query embeddings at request time with Vertex AI.
4. Retrieve candidates with BigQuery Vector Search.
5. Apply business-rule reranking in the API.

That production path is not implemented in Stage 7A or Stage 7B.
