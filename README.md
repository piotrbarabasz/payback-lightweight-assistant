# PAYBACK Lightweight Assistant

A lightweight backend assistant API that receives a user query, detects the intended action, and returns either product recommendations or a clarifying question.

## Current Stage

This repository is currently at Stage 3. Stage 1 established the backend foundation, Stage 2 added a synthetic product catalog, and Stage 3 adds deterministic keyword retrieval over that catalog.

## Implemented

- MVP scope definition.
- API contract.
- Pydantic API schemas.
- FastAPI health endpoint and assistant endpoint.
- Deterministic keyword retrieval engine.
- Tests for API behavior, schemas, catalog generation, loading, validation, filters, and retrieval.

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

Stage 3 adds local deterministic retrieval for `POST /assistant/query`.

What was added:

- Query normalization.
- Keyword search.
- Partner, category, and price hint detection.
- Deterministic scoring.
- Ranking.
- `Product` to `ProductResult` conversion.
- Integration with `POST /assistant/query`.

Retrieval details are documented in [docs/retrieval_engine.md](docs/retrieval_engine.md).

## Not Implemented Yet

- Embeddings.
- Semantic search.
- FAISS.
- BigQuery Vector Search.
- Vertex AI.
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
- `POST /assistant/query`: main assistant endpoint. It returns deterministic keyword-ranked catalog results, support routing, or a clarifying question.
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
  ]
}
```

## Planned Next Stages

- Stage 4: intent detection module.
- Stage 5: Docker and Cloud Run.
- Stage 6: Vertex AI and BigQuery Vector Search.
