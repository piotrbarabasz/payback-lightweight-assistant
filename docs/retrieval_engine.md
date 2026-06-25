# Retrieval Engine

## 1. Purpose

Stage 3 introduced the first deterministic catalog retrieval layer. It searches the local synthetic product catalog with transparent keyword logic before semantic retrieval, embeddings, or vector search are added.

The goal is to keep retrieval explainable, testable, and API-compatible through `ProductResult` objects.

## 2. Retrieval Flow

```text
User query
-> Stage 4 intent detection
-> normalization
-> partner, category, and price hint detection
-> keyword search
-> scoring
-> ranking
-> ProductResult conversion
```

The FastAPI route stays thin. Pure intent analysis lives in `app/intent/service.py`; assistant orchestration lives in `app/assistant/service.py`, which combines Stage 4 intent detection with retrieval results when retrieval is appropriate.

For `compare_products` actions, assistant orchestration keeps retrieval broad
enough to compare partners instead of applying only the first partner hint. The
returned `ProductResult` objects remain lightweight, while their `reason`
fields and the response-level `comparison_summary` explain the comparison using
available fields: price, partner, category, promotion status, and relevance
score.

## 3. Searchable Product Fields

Keyword search uses these `Product` fields:

- `name`
- `name_de`
- `category`
- `description`
- `description_de`
- `brand`
- `tags`
- `tags_de`

## 4. Scoring Formula

The final score is normalized to `0..1` and combines:

- keyword match as the main signal
- partner match boost
- category hint boost
- price preference boost, for example `cheap` or `premium`
- promotion boost
- small popularity boost

The exact weights are intentionally simple and deterministic so tests can verify relative ranking behavior.

## 5. Multilingual Support

German and English matching is supported through multilingual product fields (`name_de`, `description_de`, `tags_de`) and deterministic query term mappings. No translation service or LLM is used.

## 6. Limitations

- No semantic search yet.
- No embeddings yet.
- No typo tolerance yet.
- No personalization yet.
- No real-time inventory.
- No LLM-based query understanding yet.

## 7. Future Improvements

- Embeddings.
- Vector search.
- Hybrid retrieval.
- BigQuery Vector Search.
- Vertex AI embeddings.
- Reranking.
- LLM-backed intent detection provider.
