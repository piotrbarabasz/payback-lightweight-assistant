# GCP Production Extension Plan

This document started as a future Stage 8 plan. Stage 8A, Stage 8B, and Stage
8C have since added the BigQuery catalog foundation, Vertex AI embedding
generation, and an optional BigQuery Vector Search retrieval backend.

The default app remains a local-first deterministic MVP. The FastAPI service can run locally, in Docker, or on Cloud Run through the existing deployment scripts. In default mode it still uses:

- the synthetic product catalog in `app/data/products.json`,
- rule-based intent detection,
- local keyword retrieval by default,
- optional deterministic local hybrid retrieval,
- local reranking and response formatting.

The default runtime does not use Vertex AI, BigQuery, BigQuery Vector Search, real partner APIs, managed embeddings, or an autonomous LLM agent loop. Managed retrieval is enabled only with explicit Stage 8 configuration.

## Remaining Production Work

The following production capabilities still need hardening or remain future work:

- BigQuery vector index creation and maintenance automation.
- Cloud Run configuration for BigQuery or Vertex AI calls.
- Catalog ingestion jobs.
- Managed IAM/service-account setup for data and model access.
- Production observability, rate limiting, authentication, or secret management.

## Target Stage 8 Architecture

```text
Product JSON / partner ingestion source
-> Catalog ingestion and validation job
-> BigQuery product table
-> Vertex AI product embedding generation job
-> BigQuery embedding column and vector index

User query
-> FastAPI POST /assistant/query on Cloud Run
-> Rule-based or future model-backed intent detection
-> Vertex AI query embedding
-> BigQuery Vector Search candidate retrieval
-> Local business-rule reranking
-> Existing response formatter
-> Structured AssistantQueryResponse
```

The public API response shape should stay backward compatible. Stage 8 should replace the retrieval data source and candidate generation layer, not force clients to consume a different response contract.

## BigQuery Product Catalog

Stage 8 can move the catalog from checked-in JSON to a managed BigQuery table.

Planned table fields:

- `product_id`
- `partner`
- `name`
- `name_de`
- `category`
- `description`
- `description_de`
- `brand`
- `price`
- `currency`
- `tags`
- `tags_de`
- `availability`
- `popularity_score`
- `is_promotion`
- `product_url`
- `embedding_text`
- `embedding`
- `updated_at`

The first ingestion source can still be the existing product JSON. Later, partner-specific ingestion adapters can replace or augment that source without changing the assistant API.

## Vertex AI Embeddings

Stage 8 can add Vertex AI text embeddings in two places:

- offline product embeddings during ingestion or refresh,
- request-time query embeddings for semantic retrieval.

Product embedding text should be built from stable catalog fields such as product name, category, brand, descriptions, tags, partner, price, availability, and promotion status. Query embedding should happen only after intent detection decides retrieval is needed.

The current local hash embedding provider remains a development/prototype tool and should not be treated as equivalent to Vertex AI embeddings.

## BigQuery Vector Search

Stage 8 can store product embeddings in BigQuery and create a vector index for candidate retrieval.

Expected retrieval flow:

1. Cloud Run receives `POST /assistant/query`.
2. The service detects intent, language, partner hints, category hints, and price preference.
3. For catalog-search actions, the service generates a query embedding with Vertex AI.
4. The service queries BigQuery Vector Search for candidate products.
5. The service applies existing business-rule reranking for partner hints, category hints, price preference, promotion status, and popularity.
6. The service formats the existing `AssistantQueryResponse`.

Keyword retrieval should remain available as a fallback and as a local development mode.

## Cloud Run Service Calls

In Stage 8, Cloud Run would remain the HTTP entry point and orchestration layer.

Cloud Run would call:

- Vertex AI for request-time query embeddings,
- BigQuery for product lookup and vector search,
- optionally Secret Manager for non-secret configuration references or future partner credentials.

The service should keep timeouts, retries, and clear error handling around all managed service calls. If managed retrieval fails, the API should fall back to local keyword retrieval when a local catalog is available, or return a controlled fallback response instead of masking infrastructure errors as successful semantic retrieval.

## Expected Environment Variables

Current deployment variables can remain:

```bash
export GCP_PROJECT_ID="your-project-id"
export GCP_REGION="europe-west1"
export SERVICE_NAME="payback-lightweight-assistant"
```

Stage 8 managed retrieval uses:

```bash
export RETRIEVAL_BACKEND="bigquery_vector"
export BIGQUERY_DATASET="payback_assistant"
export BIGQUERY_PRODUCTS_TABLE="products"
export BIGQUERY_VECTOR_INDEX="products_embedding_idx"
export BIGQUERY_EMBEDDING_COLUMN="embedding"
export VERTEX_AI_LOCATION="europe-west1"
export VERTEX_EMBEDDING_MODEL="text-embedding-model-id"
export ENABLE_LOCAL_RETRIEVAL_FALLBACK="true"
```

`RETRIEVAL_BACKEND=bigquery_vector` enables the optional Stage 8C BigQuery
Vector Search retriever when the required BigQuery and Vertex AI environment
variables, credentials, and product embeddings are available. The default
backend remains `keyword`.

## IAM And Service Account Permissions

Stage 8 should use a dedicated Cloud Run service account with least-privilege access.

Likely permissions:

- BigQuery job execution for vector/search queries.
- BigQuery read access to the product table and vector index.
- Vertex AI user permission for embedding generation.
- Logging and monitoring writer permissions.
- Secret Manager secret accessor only if future integrations require secrets.

The ingestion or embedding refresh job may need a separate service account with:

- BigQuery data editor permissions for the target dataset/table,
- Vertex AI embedding access,
- read access to the ingestion source,
- logging permissions.

Avoid using broad project-owner roles for either Cloud Run or ingestion jobs.

## Fallback Strategy

Stage 8 should preserve deterministic local retrieval as a fallback path:

- `RETRIEVAL_BACKEND=keyword` should continue to run without GCP services.
- A BigQuery/Vertex backend should fail clearly during startup or request handling if required configuration is missing.
- If `ENABLE_LOCAL_RETRIEVAL_FALLBACK=true`, managed retrieval failures can fall back to local keyword retrieval over the packaged synthetic catalog.
- Responses should make no false claim that semantic/vector retrieval was used when fallback retrieval handled the request.

This keeps local demos, tests, and reviewer evaluation reproducible while allowing production deployments to use managed GCP retrieval.

## Implementation Sequence

Recommended Stage 8 order:

1. Define BigQuery schema and migration/creation scripts.
2. Add a catalog ingestion job from the existing JSON into BigQuery.
3. Add product embedding text generation and offline Vertex AI embedding generation.
4. Store embeddings in BigQuery and create the vector index.
5. Add a real retrieval backend behind the existing retrieval interface.
6. Add query embedding and BigQuery Vector Search calls from Cloud Run.
7. Keep keyword retrieval as local fallback.
8. Add integration tests against a controlled GCP test project.
9. Add observability, cost controls, IAM documentation, and failure-mode tests.

Until those steps are implemented and tested, Stage 8 remains a plan only.
