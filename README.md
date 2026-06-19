# PAYBACK Lightweight Assistant

A lightweight backend assistant API that receives a user query, detects the intended action, and returns either product recommendations or a clarifying question.

## Current Stage

This repository is currently at Stage 1. The focus is on the backend foundation:

- MVP scope definition.
- API contract.
- Pydantic schemas.
- FastAPI stub.
- Basic tests.

## Stage 1 Coverage

Stage 1 covers the contract and scaffolding for the challenge requirements:

- Structured API response.
- Intent categories planned: search, discovery, comparison, customer support, and unknown.
- German and English planned.
- Partner ecosystems planned: dm-like drugstore, EDEKA-like grocery, and Amazon-like general merchandise.
- Clarifying question flow planned.
- Cloud-native path planned for later stages.

## Not Implemented Yet

- Real product catalog.
- Recommendation engine.
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

## Running Tests

```bash
pytest
```

## API Endpoints

- `GET /health`: health check for local development and future deployment.
- `POST /assistant/query`: main assistant endpoint. Accepts a raw query and returns the Stage 1 response schema with stubbed behavior.

Interactive OpenAPI docs are available at `/docs` when the app is running.

## Example Request

```bash
curl -X POST "http://127.0.0.1:8000/assistant/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Bitte zeige mir Angebote für günstige Windeln",
    "top_k": 5
  }'
```

## Planned Next Stages

- Stage 2: synthetic product catalog.
- Stage 3: retrieval engine.
- Stage 4: intent detection module.
- Stage 5: Docker and Cloud Run.
- Stage 6: Vertex AI and BigQuery Vector Search.
