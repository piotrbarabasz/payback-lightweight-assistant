# PAYBACK Lightweight Assistant

A lightweight backend assistant API for a recruitment challenge.
It accepts a raw user query and routes it deterministically.
The current MVP returns product recommendations, comparison responses, support routing, or a clarifying question.
It uses a local synthetic catalog instead of real partner integrations.
It runs locally with FastAPI and includes scripts for a minimal Cloud Run container deployment.
The code is intentionally scoped for reproducibility, reviewability, and low operational overhead.

## Current Stage

This repository is currently at **Stage 9B / final candidate**.

The default local path is intentionally simple: `INTENT_BACKEND=rules`, `RETRIEVAL_BACKEND=keyword`, and the checked-in synthetic catalog. It runs without Google Cloud credentials, Vertex AI, BigQuery, or Gemini.

The optional managed GCP path is explicit: Cloud Run can run the same FastAPI service with `RETRIEVAL_BACKEND=bigquery_vector` for Vertex AI query embeddings and BigQuery Vector Search, and can optionally use `INTENT_BACKEND=vertex_llm` for Gemini JSON intent parsing. Neither managed retrieval nor LLM intent parsing is enabled by default.

The project has a lightweight deterministic agent layer for intent detection, decision policy, and assistant orchestration. It is not an autonomous LLM agent loop.

Stage history:

- Stage 1 established the backend foundation.
- Stage 2 added a synthetic product catalog.
- Stage 3 added deterministic keyword retrieval.
- Stage 4 added modular deterministic intent detection.
- Stage 5 added Docker and local deployment readiness.
- Stage 6 added minimal Cloud Run deployment scripts.
- Stage 7A added a retrieval backend abstraction with a local hybrid retrieval prototype.
- Stage 7B completes documentation cleanup, production-readiness hygiene, pluggable architecture clarity, and evaluation readiness before Stage 8.
- Stage 8A added BigQuery catalog setup, loading, and verification scripts.
- Stage 8B added a Vertex AI embedding provider and product embedding generation script.
- Stage 8C added an optional BigQuery Vector Search retriever and optional vector index setup.
- Stage 8D added Cloud Run service account and environment configuration for the managed backend.
- Stage 9A added lightweight deterministic intent, decision, and assistant orchestration agents.
- Stage 9B added an optional Vertex/Gemini JSON intent backend with deterministic rules fallback.

## Implementation Status

### Implemented

- FastAPI backend.
- Local synthetic product catalog.
- Lightweight deterministic `IntentDetectionAgent`, `DecisionAgent`, and `AssistantAgent` abstractions.
- Pluggable intent detector backend with rule-based detection as the default.
- Rule-based language and intent detection.
- Local keyword retrieval.
- Optional Vertex/Gemini structured intent backend with rules fallback.
- Optional Vertex AI text embedding provider.
- Optional BigQuery catalog foundation scripts.
- Optional BigQuery product embedding generation script.
- Optional BigQuery Vector Search retrieval backend.
- Optional Cloud Run runtime configuration for BigQuery and Vertex AI.
- Docker and Docker Compose support.
- Minimal Cloud Run deployment scripts for the existing containerized FastAPI app.
- Demo script and smoke tests.
- Pydantic API schemas, health checks, and catalog preview endpoints.
- Product search, discovery, comparison, support routing, and clarifying-question responses.

### Local / Optional

- Synthetic in-repository catalog instead of real partner APIs.
- Local in-memory retrieval instead of a managed database or vector index.
- Optional `hybrid` retrieval backend using deterministic local hash embeddings.
- Optional `vertex_llm` intent backend using Vertex AI / Gemini only for structured intent parsing.
- Optional `bigquery_vector` backend using Vertex AI query embeddings and BigQuery Vector Search.
- Cloud Run scripts that deploy the current containerized app with either the default keyword backend or the optional managed backend.

### Not Implemented

- Vertex AI and BigQuery Vector Search are optional and not enabled by default.
- Real partner API integrations.
- Autonomous LLM agent loop.
- Conversation memory.
- Production authentication, rate limiting, and monitoring.

### Stage 8 Optional GCP Integration

Stage 8 is implemented as optional production-integration plumbing. The default local retrieval path remains unchanged.

Stage 8A BigQuery catalog setup and load instructions are documented in [docs/stage_8a_bigquery_catalog.md](docs/stage_8a_bigquery_catalog.md). These scripts are manual utilities only and do not change the default local API behavior.

Stage 8B Vertex AI embedding provider setup is documented in [docs/stage_8b_vertex_embeddings.md](docs/stage_8b_vertex_embeddings.md).

Stage 8C BigQuery Vector Search setup is documented in [docs/stage_8c_bigquery_vector_search.md](docs/stage_8c_bigquery_vector_search.md). Enable it explicitly with `RETRIEVAL_BACKEND=bigquery_vector` after product embeddings exist.

Stage 8D Cloud Run runtime setup for BigQuery and Vertex AI service-account access is documented in [docs/stage_8d_cloud_run_gcp_runtime.md](docs/stage_8d_cloud_run_gcp_runtime.md).

Stage 8 reviewer checklist is documented in [docs/stage_8_final_checklist.md](docs/stage_8_final_checklist.md).

## Design Trade-offs

- A lightweight deterministic agent layer is used instead of an autonomous LLM-based agent loop to keep latency low, costs predictable, and behavior reproducible.
- A local synthetic catalog is used instead of real partner APIs to keep the challenge self-contained and easy to run.
- Cloud Run deployment scripts are included instead of a full GCP-native data stack so the repository stays lightweight while still showing deployment competence.
- The retrieval and intent layers are pluggable so optional Vertex AI or BigQuery-backed components can be enabled without changing the public API contract.
- The optional Vertex/Gemini intent backend is used only for structured intent parsing. It does not retrieve products, generate final answers, or run autonomous planning.
- The Vertex/Gemini intent backend falls back to the deterministic `rules` backend on invalid JSON, missing fields, unsupported output, timeout, missing credentials, or upstream errors.

## Known Limitations

- No real partner API integrations are implemented.
- Vertex AI and BigQuery Vector Search require explicit Stage 8 configuration and are not used by default API retrieval.
- Vertex/Gemini intent detection requires explicit `INTENT_BACKEND=vertex_llm` and Vertex AI configuration; the default remains `rules`.
- No conversation memory, production authentication, rate limiting, or monitoring is implemented.
- The catalog is synthetic and intentionally small.
- The current assistant is deterministic rather than generative.

## Architecture Overview

```text
User query
-> Intent Detection Agent
-> Optional rules or vertex_llm intent backend
-> Decision Agent
-> Assistant Agent
-> Retrieval Engine
-> Product Results or Clarifying Question
```

## Stage 7B: Documentation and Production-Readiness Cleanup

Stage 7B aligned the docs and repository narrative with the local MVP implementation and prepared the project for Stage 8.

This stage focuses on:

- honest implementation status in the documentation,
- a clear split between the local MVP and future production work,
- pluggable architecture language that matches the code,
- evaluation-ready setup instructions and commands,
- reviewer-friendly scope boundaries.

The default runtime remains local-first and deterministic. Stage 8 adds optional GCP integration paths, but they are not used unless configured with the relevant environment variables and cloud credentials.

The GCP extension plan and remaining production hardening notes are documented in [docs/gcp_production_extension_plan.md](docs/gcp_production_extension_plan.md).

## How to Evaluate This Challenge

### Default Local Quickstart

Install dependencies:

```bash
pip install -r requirements.txt
```

Run tests:

```bash
pytest
```

Run the API locally:

```bash
uvicorn app.main:app --host 127.0.0.1 --port 8080 --reload
```

Run the local demo / smoke test:

```bash
python scripts/smoke_test_api.py
```

This is the recommended reviewer path when no GCP project is configured. It uses `INTENT_BACKEND=rules` and `RETRIEVAL_BACKEND=keyword`.

Optionally run the lightweight local/API load test after the API is running:

```bash
python scripts/load_test_api.py --base-url http://127.0.0.1:8080 --requests 50
```

Optionally build the Docker image:

```bash
docker build -t payback-lightweight-assistant .
```

### Cloud Run Demo

The default Cloud Run deployment keeps the low-cost local behavior:

```bash
export GCP_PROJECT_ID="your-project-id"
export GCP_REGION="europe-west1"
export ARTIFACT_REPOSITORY="payback-assistant"
export IMAGE_NAME="payback-lightweight-assistant"
export IMAGE_TAG="latest"
export SERVICE_NAME="payback-lightweight-assistant"
export INTENT_BACKEND="rules"
export RETRIEVAL_BACKEND="keyword"

bash infra/gcp/setup_project.sh
bash infra/gcp/create_artifact_registry.sh
bash infra/gcp/build_and_push_image.sh
bash infra/gcp/deploy_cloud_run.sh
bash infra/gcp/smoke_test_deployed_api.sh
```

The optional managed retrieval path requires Stage 8 BigQuery and Vertex AI setup before deployment:

```bash
export RETRIEVAL_BACKEND="bigquery_vector"
export CLOUD_RUN_SERVICE_ACCOUNT="payback-assistant-runtime@your-project-id.iam.gserviceaccount.com"
export GCP_LOCATION="europe-west1"
export BIGQUERY_DATASET="payback_catalog"
export BIGQUERY_PRODUCTS_TABLE="products"
export BIGQUERY_LOCATION="europe-west1"
export BIGQUERY_VECTOR_TOP_K="25"
export VERTEX_AI_LOCATION="europe-west1"
export VERTEX_EMBEDDING_MODEL="text-embedding-005"
bash infra/gcp/deploy_cloud_run.sh
```

Enable the optional Vertex/Gemini intent backend only when Vertex AI access is configured:

```bash
export INTENT_BACKEND="vertex_llm"
export VERTEX_AI_LOCATION="europe-west1"
export VERTEX_INTENT_MODEL="gemini-3.5-flash"
export INTENT_LLM_TIMEOUT_SECONDS="3"
bash infra/gcp/deploy_cloud_run.sh
```

The LLM backend only parses the query into the existing structured intent fields. On timeout, missing credentials, invalid JSON, missing fields, unsupported values, or inconsistent policy output, the service logs a warning and falls back to `rules`.

## Stage 2: Synthetic Product Catalog

Stage 2 adds a local synthetic catalog and data layer for development and later retrieval work.

What was added:

- Synthetic product catalog across three partner ecosystems.
- Deterministic generator script.
- `Product` schema.
- Catalog loader.
- Simple filters.
- Optional catalog preview endpoint.

Dataset size:

The checked-in catalog lives at `app/data/products.json` and contains 150 validated products:

- 150 products total.
- 50 `dm` products.
- 50 `edeka` products.
- 50 `amazon` products.

Generate the catalog:

```bash
python app/data/generate_synthetic_catalog.py
```

Preview products:

```text
GET /catalog/products
GET /catalog/products?partner=dm
GET /catalog/products?partner=edeka&limit=10
```

## Stage 3: Retrieval Engine

Stage 3 added local deterministic retrieval for `POST /assistant/query`.

What was added:

- Query normalization.
- Keyword search.
- Partner, category, and price hint detection.
- Deterministic scoring.
- Ranking.
- `Product` to `ProductResult` conversion.
- Integration with `POST /assistant/query`.

Retrieval details are documented in [docs/retrieval_engine.md](docs/retrieval_engine.md).

## Stage 7A: Retrieval Backend Abstraction

Stage 7A adds a pluggable retrieval backend architecture while keeping the public API response schema unchanged.

Available backends:

- `keyword`: default backend, using the existing deterministic keyword and business-rule scoring.
- `hybrid`: local prototype that combines keyword scoring, local semantic-like similarity, and existing business boosts.

The hybrid backend uses a deterministic local hash embedding provider. It does not call Vertex AI, BigQuery, BigQuery Vector Search, or any external model service.

Semantic retrieval details are documented in [docs/semantic_retrieval.md](docs/semantic_retrieval.md).

## Stage 4: Intent Detection Module

Stage 4 moves temporary route-level intent rules into a testable `app/intent/` package and keeps HTTP handlers thin.
The current code also exposes those deterministic rules through `app/agents/intent_detection.py`, with `DecisionAgent` and `AssistantAgent` making the decision and orchestration boundaries explicit.

What was added:

- Language detection.
- Entity extraction.
- Partner hint detection.
- Intent classification.
- Specificity classification.
- Next best action decision.
- Clarifying question generation.
- Integration with `POST /assistant/query`.
- Lightweight deterministic agent abstractions without LangChain, CrewAI, AutoGen, or an autonomous LLM loop.
- Optional `vertex_llm` backend for strict JSON intent parsing with rules fallback.

Intent detection details are documented in [docs/intent_detection.md](docs/intent_detection.md).

## Stage 5: Docker and Local Deployment Readiness

Stage 5 prepared the FastAPI service for local container execution and Cloud Run-compatible runtime behavior.

What was added:

- `Dockerfile` based on Python 3.11 slim.
- Non-root container user.
- `.dockerignore` for clean Docker build context.
- `docker-compose.yml` for local container development.
- Environment-based configuration in `app/config.py`.
- Production startup command that binds to `0.0.0.0` and reads `PORT`.
- `/health` endpoint updated for deployment readiness.
- Local smoke test script in `scripts/smoke_test_api.py`.
- Container health check.
- Cloud Run runtime compatibility prepared.
- Local deployment documentation in [docs/deployment_local.md](docs/deployment_local.md).

At Stage 5, no GCP deployment, Cloud Run scripts, BigQuery, Vertex AI, embeddings, FAISS, or external LLM calls were included.

## Stage 6: GCP Cloud Run Deployment

Stage 6 adds scripts for a minimal deployment path from the existing Dockerized FastAPI app to Artifact Registry and Cloud Run.

What was added:

- Artifact Registry setup and Docker image push scripts.
- Cloud Run deployment script.
- Deployed API smoke test script.
- Deployment documentation in [docs/deployment_gcp_cloud_run.md](docs/deployment_gcp_cloud_run.md).
- Cost-control documentation in [docs/cost_control.md](docs/cost_control.md).

Deployment path:

```text
Local Dockerized FastAPI app
-> Artifact Registry image
-> Cloud Run service
-> public HTTPS endpoint
-> smoke test
```

When deployed with default settings, the service still uses the synthetic catalog packaged inside the container. The deployment script configures minimum instances as `0` for cost efficiency. Stage 8D can also deploy the same container with `RETRIEVAL_BACKEND=bigquery_vector`, BigQuery environment variables, Vertex AI environment variables, and a Cloud Run runtime service account.

If `RETRIEVAL_BACKEND` is not set, the service uses the default `keyword` backend and continues to run without Vertex AI or BigQuery.

Quick deployment flow:

```bash
export GCP_PROJECT_ID="your-project-id"
export GCP_REGION="europe-west1"
export ARTIFACT_REPOSITORY="payback-assistant"
export IMAGE_NAME="payback-lightweight-assistant"
export IMAGE_TAG="latest"
export SERVICE_NAME="payback-lightweight-assistant"

bash infra/gcp/setup_project.sh
bash infra/gcp/create_artifact_registry.sh
bash infra/gcp/build_and_push_image.sh
bash infra/gcp/deploy_cloud_run.sh
bash infra/gcp/smoke_test_deployed_api.sh
```

## Configuration

Runtime configuration is environment-based:

| Variable | Default | Description |
| --- | --- | --- |
| `APP_NAME` | `PAYBACK Lightweight Assistant` | FastAPI application title. |
| `APP_VERSION` | `0.6.0` | FastAPI application version. |
| `ENVIRONMENT` | `local` | Runtime environment label. |
| `HOST` | `0.0.0.0` | Bind host used by the container startup command. |
| `PORT` | `8080` in Docker | Bind port used by container runtimes. |
| `LOG_LEVEL` | `info` | Uvicorn log level. |
| `CATALOG_PATH` | `app/data/products.json` | Local catalog JSON path. |
| `INTENT_BACKEND` | `rules` | Intent detector selector. Supported values: `rules`, `vertex_llm`. `vertex_llm` is optional and falls back to rules on any Vertex/Gemini failure or invalid output. |
| `RETRIEVAL_BACKEND` | `keyword` | Retrieval backend selector. Supported values: `keyword`, `hybrid`, `bigquery_vector`. The `bigquery_vector` backend is optional and requires Stage 8C GCP configuration. |
| `DEFAULT_TOP_K` | `5` | Default assistant result count. |
| `MAX_TOP_K` | `20` | Maximum assistant result count. |
| `GCP_PROJECT_ID` | empty | Google Cloud project for optional Stage 8 utilities. Required when constructing the Vertex embedding provider. |
| `GCP_LOCATION` | `europe-west1` | Google Cloud location for optional Stage 8 utilities. Can be used by the Vertex embedding provider. |
| `GCP_REGION` | `europe-west1` | Google Cloud region for optional Cloud Run deployment scripts. |
| `BIGQUERY_DATASET` | `payback_catalog` | BigQuery dataset for optional Stage 8 catalog and vector retrieval. |
| `BIGQUERY_PRODUCTS_TABLE` | `products` | BigQuery products table for optional Stage 8 catalog and vector retrieval. |
| `BIGQUERY_LOCATION` | `europe-west1` | BigQuery job and dataset location. |
| `BIGQUERY_VECTOR_TOP_K` | `25` | Candidate pool size for optional BigQuery Vector Search retrieval. |
| `BIGQUERY_QUERY_EMBEDDING_CACHE_SIZE` | `128` | In-memory query embedding cache size for optional BigQuery Vector Search retrieval. Set `0` to disable. |
| `BIGQUERY_VECTOR_INDEX` | `products_embedding_idx` | Optional BigQuery vector index name used by the Stage 8C index setup script. |
| `VERTEX_AI_LOCATION` | empty | Optional Vertex AI location override for embeddings. Takes precedence over `GCP_LOCATION`. |
| `VERTEX_EMBEDDING_MODEL` | empty | Vertex text embedding model id. Required when constructing the Vertex embedding provider. |
| `VERTEX_EMBEDDING_DIMENSIONS` | empty | Optional output dimensionality for models that support it. |
| `VERTEX_INTENT_MODEL` | `gemini-3.5-flash` | Optional Vertex/Gemini model id for `INTENT_BACKEND=vertex_llm`. |
| `INTENT_LLM_TIMEOUT_SECONDS` | `3.0` | Request timeout for optional Vertex/Gemini intent classification before falling back to rules. |

Enable optional Vertex/Gemini intent parsing locally:

```bash
export INTENT_BACKEND="vertex_llm"
export GCP_PROJECT_ID="your-project-id"
export VERTEX_AI_LOCATION="europe-west1"
export VERTEX_INTENT_MODEL="gemini-3.5-flash"
export INTENT_LLM_TIMEOUT_SECONDS="3"
uvicorn app.main:app --host 127.0.0.1 --port 8080 --reload
```

Unset `INTENT_BACKEND` or set it back to `rules` for the default deterministic backend.

## Local Setup

Requires Python 3.11+.

Unix/macOS:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app/data/generate_synthetic_catalog.py
uvicorn app.main:app --reload
```

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app/data/generate_synthetic_catalog.py
uvicorn app.main:app --reload
```

Run the app:

```bash
uvicorn app.main:app --reload
```

Run the app with the local hybrid retrieval prototype:

Unix/macOS:

```bash
RETRIEVAL_BACKEND=hybrid uvicorn app.main:app --reload
```

Windows PowerShell:

```powershell
$env:RETRIEVAL_BACKEND = "hybrid"
uvicorn app.main:app --reload
```

Production-style startup:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8080 --log-level info
```

## Docker

Build the image:

```bash
docker build -t payback-lightweight-assistant .
```

Run the container locally:

```bash
docker run --rm -p 8080:8080 -e PORT=8080 payback-lightweight-assistant
```

Use Docker Compose:

```bash
docker compose up --build
```

Check health and readiness:

```bash
curl http://127.0.0.1:8080/health
curl http://127.0.0.1:8080/ready
```

Smoke test:

```bash
python scripts/smoke_test_api.py
```

The smoke test defaults to `http://localhost:8080`. If the API is running on
the default Uvicorn development port, run:

```bash
API_BASE_URL=http://127.0.0.1:8000 python scripts/smoke_test_api.py
```

## Cloud Run

Use the Cloud Run demo flow above for the default `rules` + `keyword` backend. For the optional BigQuery/Vertex runtime path, follow [docs/stage_8d_cloud_run_gcp_runtime.md](docs/stage_8d_cloud_run_gcp_runtime.md). Cost-control notes are in [docs/cost_control.md](docs/cost_control.md).

## Running Tests

```bash
pytest
```

## Command Reminders

Generate catalog:

```bash
python app/data/generate_synthetic_catalog.py
```

Run API:

```bash
uvicorn app.main:app --reload
```

Run tests:

```bash
pytest
```

## API Endpoints

- `GET /health`: health check for local development and future deployment.
- `GET /ready`: readiness check for container and Cloud Run deployment.
- `POST /assistant/query`: main assistant endpoint. It returns configured intent detection, catalog results, support routing, comparison responses, or a clarifying question.
- `GET /catalog/products`: development-only catalog preview endpoint.

Interactive OpenAPI docs are available at `/docs` when the app is running.

## Example Request

```bash
curl -X POST "http://127.0.0.1:8080/assistant/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Bitte zeige mir Angebote fuer guenstige Windeln",
    "top_k": 5
  }'
```

Example queries:

- `Bitte zeige mir Angebote fuer guenstige Windeln`
- `Compare cheap diapers from dm and Amazon`
- `Which partner has cheaper pasta dinner products?`
- `I need stuff for a pasta dinner`
- `Show me headphones on Amazon`
- `Meine PAYBACK Punkte fehlen`
- `Something nice`

Example response:

```json
{
  "query": "Bitte zeige mir Angebote fuer guenstige Windeln",
  "language": "de",
  "intent": "search",
  "specificity": "specific",
  "next_best_action": "search_catalog",
  "clarifying_question": null,
  "partner_hint": "dm",
  "entities": {
    "product_category": "baby care",
    "price_preference": "cheap",
    "occasion": null,
    "dietary_preference": null,
    "brand": null
  },
  "results": [
    {
      "product_id": "dm-001",
      "partner": "dm",
      "name": "Penaten Baby Diapers Size 4 42 pcs",
      "category": "baby care",
      "price": 9.6,
      "currency": "EUR",
      "score": 0.4396,
      "reason": "Matched query terms in product tags and description. Boosted for category hint, cheap price preference, promotion, popularity."
    }
  ],
  "comparison_summary": null,
  "comparison_criteria": []
}
```

Comparison queries return `intent: comparison` and
`next_best_action: compare_products`. Their results keep the normal product
result shape and add comparison-oriented reasons plus response-level
`comparison_summary` and `comparison_criteria` fields. The summary uses only
available catalog fields such as price, partner, category, promotion status,
and relevance score.

## Stage 8 Status

Stage 8 currently includes:

- BigQuery catalog foundation scripts.
- Vertex AI text embedding provider.
- BigQuery product embedding generation script.
- Optional BigQuery Vector Search retrieval backend.
- Optional BigQuery vector index setup.
- Cloud Run runtime service-account and environment configuration for the managed backend.

Remaining production work includes managed ingestion scheduling, fallback monitoring, observability, authentication, rate limiting, and production IAM review. The detailed GCP plan is in [docs/gcp_production_extension_plan.md](docs/gcp_production_extension_plan.md).

The local deterministic API contract remains the default and should remain available as a fallback while managed integrations are hardened.
