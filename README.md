# PAYBACK Lightweight Assistant

A lightweight backend assistant API that receives a user query, detects the intended action, and returns either product recommendations or a clarifying question.

## Current Stage

This repository is currently at Stage 2. Stage 1 established the backend foundation; Stage 2 adds a synthetic product catalog and a clean local data layer for future retrieval work.

## Implemented

- MVP scope definition.
- API contract.
- Pydantic API schemas.
- FastAPI health endpoint and assistant stub endpoint.
- Tests for API stubs, schemas, catalog generation, loading, validation, and filters.

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

## Not Implemented Yet

- Real retrieval engine.
- Embeddings.
- Vector search.
- LLM-based intent detection.
- GCP deployment.

## Local Setup

Requires Python 3.11+.

Unix/macOS:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Run the app:

```bash
uvicorn app.main:app --reload
```

## Running Tests

```bash
pytest
```

## API Endpoints

- `GET /health`: health check for local development and future deployment.
- `POST /assistant/query`: main assistant endpoint. It returns deterministic Stage 1-style behavior with catalog-based mock product results for search-like queries.
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

## Planned Next Stages

- Stage 3: retrieval engine using the validated catalog.
- Stage 4: intent detection module.
- Stage 5: Docker and Cloud Run.
- Stage 6: Vertex AI and BigQuery Vector Search.
