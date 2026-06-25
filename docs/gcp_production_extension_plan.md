# GCP Production Extension Plan

This document describes the intended GCP production path for the project without claiming it is already implemented.

## Current Deployment Path

The current MVP is Cloud Run-ready and can be deployed as a Cloud Run service backed by the local FastAPI application, synthetic catalog data, deterministic intent rules, and local retrieval backends.

Current deployment-related scripts cover:

- Docker image build and push.
- Artifact Registry image storage.
- Cloud Run deployment.
- Smoke testing against the deployed HTTP endpoint.

No managed GCP retrieval or embedding services are active in the current MVP.

Current deployment environment variables:

- `GCP_PROJECT_ID`
- `GCP_REGION`
- `ARTIFACT_REPOSITORY`
- `IMAGE_NAME`
- `IMAGE_TAG`
- `SERVICE_NAME`
- `CLOUD_RUN_URL` for post-deploy smoke tests

## Future Production Extensions

### Future BigQuery Product Catalog

Planned direction:

- store partner products in BigQuery instead of a checked-in JSON file,
- support scheduled ingestion and validation,
- keep the application API unchanged while switching the data source.

Expected environment variables:

- `GCP_PROJECT_ID`
- `GCP_REGION`
- `BIGQUERY_DATASET`
- `BIGQUERY_TABLE_PRODUCTS`

### Future BigQuery Vector Search

Planned direction:

- store product embeddings alongside catalog records,
- use BigQuery Vector Search for semantic candidate retrieval,
- keep keyword and business-rule ranking as a re-ranking layer.

Expected environment variables:

- `BIGQUERY_VECTOR_INDEX`
- `BIGQUERY_VECTOR_ENDPOINT`
- `BIGQUERY_EMBEDDING_COLUMN`

### Future Vertex AI Embeddings

Planned direction:

- generate embeddings for product titles, descriptions, and tags,
- generate query embeddings at request time,
- use embeddings for candidate retrieval and semantic ranking.

Expected environment variables:

- `VERTEX_AI_PROJECT_ID`
- `VERTEX_AI_LOCATION`
- `VERTEX_EMBEDDING_MODEL`

### Future Vertex or LLM Intent Detector

Planned direction:

- replace the current rule-based detector with a managed model-backed classifier only if it improves accuracy and maintainability,
- keep the intent API contract stable,
- preserve the existing local rule-based fallback for development and evaluation.

Expected environment variables:

- `INTENT_BACKEND=vertex_placeholder` for the current non-functional placeholder,
- future model configuration variables if a real model is introduced.

## Expected Data Flow

Future production flow:

```text
User query
-> FastAPI
-> Intent detection
-> Query embedding
-> BigQuery Vector Search over catalog embeddings
-> Retrieval reranking
-> Structured response
```

For catalog management:

```text
Partner source data
-> Ingestion job
-> BigQuery product table
-> Embedding generation
-> Vector index update
```

## Why This Is Not Implemented Yet

This plan is intentionally separate from the current MVP because the repository is focused on a lightweight, deterministic assistant that can be reviewed and run locally without external infrastructure.

The GCP extension is not implemented because it would require:

- external cloud dependencies,
- infrastructure setup and billing,
- operational concerns that are outside the lightweight MVP scope,
- additional implementation and validation work before it can be considered production ready.

The current codebase keeps the future architecture explicit through documentation and placeholder modules only. Those placeholders raise `NotImplementedError` and do not call external services.
