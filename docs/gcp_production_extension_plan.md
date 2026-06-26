# GCP Production Hardening And Future Work

This document captures production hardening work after the implemented Stage 8 and Stage 9 paths.

Stage 8 and Stage 9 are no longer only a plan. The repository now includes:

- BigQuery catalog setup and load scripts.
- Vertex AI product embedding generation.
- Optional BigQuery Vector Search retrieval through `RETRIEVAL_BACKEND=bigquery_vector`.
- Cloud Run service-account and runtime environment configuration for managed retrieval.
- Lightweight deterministic intent, decision, and assistant agents.
- Optional Vertex/Gemini JSON intent parsing through `INTENT_BACKEND=vertex_llm`.
- Rules fallback for the optional LLM intent backend.

Manual GCP validation has confirmed Cloud Run deployment, Vertex AI query embeddings, BigQuery Vector Search product results, optional Vertex/Gemini intent parsing, and rules fallback.

## Current Runtime Modes

| Mode | Intent backend | Retrieval backend | Notes |
| --- | --- | --- | --- |
| Default local | `rules` | `keyword` | No GCP credentials, Vertex AI, Gemini, BigQuery, or partner APIs required. |
| Local prototype | `rules` | `hybrid` | Uses deterministic local hash embeddings only. |
| Managed retrieval | `rules` | `bigquery_vector` | Uses Vertex AI query embeddings and BigQuery Vector Search. |
| Optional LLM intent + managed retrieval | `vertex_llm` | `bigquery_vector` | Uses Gemini only for structured intent JSON, then the normal retrieval path. |

The public API response schema is unchanged across these modes.

## Implemented Managed Architecture

```text
User query
-> Cloud Run FastAPI service
-> IntentDetectionAgent
-> rules or optional Vertex/Gemini JSON intent backend
-> DecisionAgent
-> AssistantAgent
-> keyword, hybrid, or BigQuery Vector Search retriever
-> existing AssistantQueryResponse schema
```

For `RETRIEVAL_BACKEND=bigquery_vector`, the retrieval path is:

```text
Assistant search decision
-> Vertex AI query embedding
-> BigQuery product table with embeddings
-> BigQuery Vector Search
-> existing business-rule reranking
-> product results with vector-search reason text
```

The frontend or API client still calls only the Cloud Run HTTPS API. BigQuery and Vertex AI calls remain server-side.

## Environment Variables

Default local mode:

```bash
export INTENT_BACKEND="rules"
export RETRIEVAL_BACKEND="keyword"
```

Managed retrieval mode:

```bash
export RETRIEVAL_BACKEND="bigquery_vector"
export GCP_PROJECT_ID="your-project-id"
export GCP_REGION="europe-west1"
export GCP_LOCATION="europe-west1"
export BIGQUERY_DATASET="payback_catalog"
export BIGQUERY_PRODUCTS_TABLE="products"
export BIGQUERY_LOCATION="europe-west1"
export BIGQUERY_VECTOR_TOP_K="25"
export VERTEX_AI_LOCATION="europe-west1"
export VERTEX_EMBEDDING_MODEL="text-embedding-005"
```

Optional Vertex/Gemini intent parsing:

```bash
export INTENT_BACKEND="vertex_llm"
export GCP_PROJECT_ID="your-project-id"
export VERTEX_AI_LOCATION="europe-west1"
export VERTEX_INTENT_MODEL="gemini-3.5-flash"
export INTENT_LLM_TIMEOUT_SECONDS="3"
```

`INTENT_BACKEND=rules` and `RETRIEVAL_BACKEND=keyword` remain the defaults. The LLM backend is used only to produce the existing structured intent fields; it does not perform retrieval, answer generation, memory, planning, or tool execution.

## IAM And Service Accounts

Cloud Run should use a dedicated runtime service account.

Required managed-path permissions:

- BigQuery job execution for vector/search queries.
- BigQuery read access to the product dataset or table.
- Vertex AI user permission for embeddings and optional Gemini intent parsing.
- Logging writer permissions through the normal Cloud Run runtime path.

Prefer dataset-level BigQuery read access. The setup script attempts a dataset-level SQL `GRANT` when `BIGQUERY_DATASET` and the `bq` CLI are available. It does not fail the whole setup if that narrow grant cannot be applied.

Project-level `roles/bigquery.dataViewer` is a fallback only when explicitly requested:

```bash
export ALLOW_PROJECT_BIGQUERY_DATA_VIEWER="true"
bash infra/gcp/setup_cloud_run_service_account.sh
```

Avoid broad owner/editor roles for Cloud Run or ingestion jobs.

## Fallback Strategy

The deterministic local path must remain available:

- `INTENT_BACKEND=rules` runs without GCP services.
- `RETRIEVAL_BACKEND=keyword` runs without GCP services.
- `INTENT_BACKEND=vertex_llm` falls back to rules on missing credentials, timeout, invalid JSON, missing fields, unsupported response shape, or inconsistent action policy.
- `RETRIEVAL_BACKEND=bigquery_vector` fails clearly if required BigQuery configuration is missing.
- Runtime Vertex query embedding failures, quota exhaustion, BigQuery transient errors, or empty managed results fall back to local keyword retrieval when the packaged catalog is available.
- Fallback result reasons are prefixed so responses do not falsely claim that vector retrieval handled the request.

This keeps local demos, tests, and reviewer evaluation reproducible while allowing managed retrieval to be enabled explicitly.

## Remaining Production Hardening

The following work is intentionally left outside the lightweight challenge scope:

- Automated catalog ingestion from real partner sources.
- Scheduled product embedding refresh jobs.
- Vector index maintenance and monitoring.
- More granular IAM and organization-policy review.
- Production authentication and rate limiting.
- Structured request tracing and latency dashboards.
- Error-budget and alerting setup.
- Load testing under expected production traffic.
- Cost budgets and per-environment quota controls.
- Managed retrieval fallback monitoring for partial BigQuery or Vertex outages.
- Real partner API adapters and secret management.
- CI/CD promotion flow across dev, staging, and production projects.

## Verification Checklist

Before presenting a managed deployment as production-like, verify:

- Cloud Run `/health` returns `200 OK`.
- The smoke-test assistant queries return `200 OK`.
- Search responses include product results from the expected backend.
- BigQuery Vector Search responses include vector-search reason text.
- `INTENT_BACKEND=vertex_llm` returns valid structured intent when enabled.
- Invalid or unavailable LLM responses fall back to rules.
- Default `INTENT_BACKEND=rules` and `RETRIEVAL_BACKEND=keyword` still pass the test suite.
- IAM grants are least-privilege or any project-level fallback is explicitly documented.
