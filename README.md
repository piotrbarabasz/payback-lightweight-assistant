# PAYBACK Lightweight Assistant

A lightweight backend assistant API for a recruitment challenge.
It accepts a raw user query and routes it deterministically.
The current MVP returns product recommendations, comparison responses, support routing, or a clarifying question.
It uses a local synthetic catalog instead of real partner integrations.
It runs locally with FastAPI and can be deployed to Cloud Run.
The code is intentionally scoped for reproducibility, reviewability, and low operational overhead.

## Current Stage

This repository is currently at Stage 7B. Stage 1 established the backend foundation, Stage 2 added a synthetic product catalog, Stage 3 added deterministic keyword retrieval, Stage 4 added a modular deterministic intent detection layer, Stage 5 added Docker and local deployment readiness, Stage 6 added minimal GCP Cloud Run deployment readiness, Stage 7A added retrieval backend abstraction with a local hybrid retrieval prototype, and Stage 7B focuses on documentation cleanup, production-readiness hygiene, pluggable architecture clarity, and evaluation readiness.

## Implemented vs Not Implemented

### Implemented

- FastAPI backend.
- Local synthetic product catalog.
- Pluggable intent detector backend with rule-based detection as the default.
- Rule-based language and intent detection.
- Local keyword retrieval.
- Optional local hybrid retrieval prototype.
- Docker and Docker Compose support.
- Cloud Run deployment scripts.
- Demo script and smoke tests.
- Pydantic API schemas, health checks, and catalog preview endpoints.

### Not Implemented

- Vertex AI embeddings.
- BigQuery product catalog.
- BigQuery Vector Search.
- Real partner API integrations.
- Real LLM-based agent loop.
- Conversation memory.
- Production authentication, rate limiting, and monitoring.

## Design Trade-offs

- Deterministic routing is used instead of an LLM-based agent loop to keep latency low, costs predictable, and behavior reproducible.
- A local synthetic catalog is used instead of real partner APIs to keep the challenge self-contained and easy to run.
- Cloud Run readiness is implemented instead of a full GCP-native data stack so the repository stays lightweight while still showing deployment competence.
- The retrieval and intent layers are pluggable so future Vertex AI or BigQuery-backed components can be added without changing the public API contract.

## Known Limitations

- No real partner API integrations are implemented.
- No Vertex AI embeddings or managed LLM calls are implemented.
- No BigQuery product catalog or BigQuery Vector Search is implemented.
- No conversation memory, production authentication, rate limiting, or monitoring is implemented.
- The catalog is synthetic and intentionally small.
- The current assistant is deterministic rather than generative.

## Architecture Overview

```text
User query
-> Intent Detection Service
-> Decision Layer
-> Retrieval Engine
-> Product Results or Clarifying Question
```

## Stage 7B: Documentation and Production-Readiness Cleanup

Stage 7B does not add new product capabilities. It aligns the docs and repository narrative with the actual implementation and prepares the project for review.

This stage focuses on:

- honest implementation status in the documentation,
- a clear split between the local MVP and future production work,
- pluggable architecture language that matches the code,
- evaluation-ready setup instructions and commands,
- reviewer-friendly scope boundaries.

The current runtime remains local-first and deterministic. The service uses a FastAPI backend, synthetic catalog data, rule-based intent handling, and local retrieval backends. Production GCP components such as Vertex AI, BigQuery, and real partner integrations are future work only.

The future GCP extension plan is documented in [docs/gcp_production_extension_plan.md](docs/gcp_production_extension_plan.md).

## How to Evaluate This Challenge

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
uvicorn app.main:app --reload
```

Run the demo / smoke test:

```bash
python scripts/smoke_test_api.py
```

Optionally build the Docker image:

```bash
docker build -t payback-lightweight-assistant .
```

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

What was added:

- Language detection.
- Entity extraction.
- Partner hint detection.
- Intent classification.
- Specificity classification.
- Next best action decision.
- Clarifying question generation.
- Integration with `POST /assistant/query`.

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

Stage 6 adds a minimal deployment path from the existing Dockerized FastAPI app to Artifact Registry and Cloud Run.

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

When deployed to Cloud Run, the current service still uses the synthetic catalog packaged inside the container. The deployment script configures minimum instances as `0` for cost efficiency. Vertex AI and BigQuery Vector Search are planned for later stages and are not included in Stage 6.

Stage 7A does not require changing the Cloud Run deployment. If `RETRIEVAL_BACKEND` is not set, the service uses the default `keyword` backend and continues to run without Vertex AI or BigQuery.

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
| `INTENT_BACKEND` | `rules` | Intent detector selector. Supported values: `rules`, `vertex_placeholder`. The placeholder makes no external calls and raises `NotImplementedError` if used. |
| `RETRIEVAL_BACKEND` | `keyword` | Retrieval backend selector. Supported values: `keyword`, `hybrid`. |
| `DEFAULT_TOP_K` | `5` | Default assistant result count. |
| `MAX_TOP_K` | `20` | Maximum assistant result count. |

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

## Cloud Run

Use the Stage 6 quick deployment flow above for the Bash script sequence. Detailed instructions are in [docs/deployment_gcp_cloud_run.md](docs/deployment_gcp_cloud_run.md), and cost-control notes are in [docs/cost_control.md](docs/cost_control.md).

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
- `POST /assistant/query`: main assistant endpoint. It returns deterministic intent detection, keyword-ranked catalog results, support routing, or a clarifying question.
- `GET /catalog/products`: development-only catalog preview endpoint.

Interactive OpenAPI docs are available at `/docs` when the app is running.

## Example Request

```bash
curl -X POST "http://127.0.0.1:8000/assistant/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Bitte zeige mir Angebote fuer guenstige Windeln",
    "top_k": 5
  }'
```

Example queries:

- `Bitte zeige mir Angebote für günstige Windeln`
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

## Planned Next Stages

- Optional production hardening and observability.
