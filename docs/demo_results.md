# Demo Results

This document summarizes the current API demo behavior for the lightweight assistant.

The default demo is local-first and deterministic. Stage 8 also includes an optional BigQuery/Vertex AI retrieval path, and Stage 9B includes an optional Vertex/Gemini intent backend. Both managed paths are enabled only through explicit environment variables.

## Demo Environment

- These examples are generated from the deterministic local keyword behavior.
- The same containerized code path can be smoke-tested locally or on Cloud Run.
- A default Cloud Run deployment still relies on the packaged synthetic catalog and local retrieval.
- The optional `bigquery_vector` demo calls Vertex AI and BigQuery from the backend only.
- The optional `vertex_llm` intent backend calls Vertex/Gemini only to parse structured intent JSON and falls back to rules on failure.

Example Cloud Run service name:

```text
payback-lightweight-assistant
```

Example Cloud Run region:

```text
europe-west1
```

## Verified Endpoints

| Endpoint | Method | Result |
| --- | ---: | ---: |
| `/health` | GET | 200 OK |
| `/assistant/query` | POST | 200 OK |

## Local Keyword Demo

Start the API with the default backend:

```bash
uvicorn app.main:app --host 127.0.0.1 --port 8080 --reload
```

Run the smoke test:

```bash
python scripts/smoke_test_api.py
```

This path does not call Vertex AI, BigQuery, BigQuery Vector Search, or partner
APIs. It is the recommended reviewer demo when no GCP project is configured.

## Optional BigQuery / Vertex Demo

Use this only after the Stage 8 setup has been completed:

1. BigQuery catalog table exists.
2. Catalog rows are loaded.
3. `embedding_text` is populated.
4. Product embeddings have been generated.
5. The runtime identity has BigQuery and Vertex AI IAM access.

Example local environment:

```bash
export RETRIEVAL_BACKEND="bigquery_vector"
export GCP_PROJECT_ID="your-project-id"
export BIGQUERY_DATASET="payback_catalog"
export BIGQUERY_PRODUCTS_TABLE="products"
export BIGQUERY_LOCATION="europe-west1"
export BIGQUERY_VECTOR_TOP_K="25"
export VERTEX_AI_LOCATION="europe-west1"
export VERTEX_EMBEDDING_MODEL="text-embedding-005"
```

Then run:

```bash
uvicorn app.main:app --host 127.0.0.1 --port 8080 --reload
python scripts/smoke_test_api.py
```

## Verified GCP Managed Demo

Manual validation has been completed against Cloud Run with the final stable managed GCP path enabled:

- Final stable demo configuration used `INTENT_BACKEND=rules` and `RETRIEVAL_BACKEND=bigquery_vector`.
- `GET /health` returned `200 OK`.
- Five smoke-test `POST /assistant/query` calls returned `200 OK`.
- `RETRIEVAL_BACKEND=bigquery_vector` used Vertex AI query embeddings and BigQuery Vector Search.
- Product results included BigQuery Vector Search reason text.
- `INTENT_BACKEND=vertex_llm` was also validated separately as an optional intent backend, but it is not the default final demo mode.
- Rules fallback was observed and preserved for invalid or inconsistent optional LLM output.

Validated smoke-test query set:

| Query | Expected route | Result |
| --- | --- | --- |
| `Bitte zeige mir Angebote fuer guenstige Windeln` | German catalog search | 200 OK |
| `I need stuff for a pasta dinner` | Discovery/catalog search | 200 OK |
| `Show me headphones on Amazon` | Partner-specific Amazon search | 200 OK |
| `Meine PAYBACK Punkte fehlen` | Support routing | 200 OK |
| `Something nice` | Clarifying question | 200 OK |

For catalog-search queries, managed product results contained reason strings indicating BigQuery Vector Search with Vertex AI query embeddings. Exact scores and product ordering can vary with the BigQuery table contents, embeddings, and model version, so the deterministic examples below remain the stable local reviewer baseline.

## Query 1: German Specific Search

User query:

```text
Bitte zeige mir Angebote fuer guenstige Windeln
```

Observed response summary:

```json
{
  "language": "de",
  "intent": "search",
  "specificity": "specific",
  "next_best_action": "search_catalog",
  "partner_hint": "dm",
  "entities": {
    "product_category": "baby care",
    "price_preference": "cheap"
  }
}
```

Top recommendation:

```json
{
  "product_id": "dm-001",
  "partner": "dm",
  "name": "Penaten Baby Diapers Size 4 42 pcs",
  "category": "baby care",
  "price": 9.6,
  "currency": "EUR"
}
```

## Query 2: English Discovery / Broad Query

User query:

```text
I need stuff for a pasta dinner
```

Observed response summary:

```json
{
  "language": "en",
  "intent": "discovery",
  "specificity": "specific",
  "next_best_action": "search_catalog",
  "partner_hint": "edeka",
  "entities": {
    "product_category": "pasta and grains",
    "occasion": "dinner"
  }
}
```

Top recommendation:

```json
{
  "product_id": "edeka-043",
  "partner": "edeka",
  "name": "Oryza Spaghetti Pasta family pack",
  "category": "pasta and grains",
  "price": 2.43,
  "currency": "EUR"
}
```

Note:

```text
This wording is close to the vague boundary. Shortening it to "Something nice" returns a clarifying question instead of catalog results.
```

## Query 3: German Support Query

User query:

```text
Meine PAYBACK Punkte fehlen
```

Observed response summary:

```json
{
  "language": "de",
  "intent": "customer_support",
  "specificity": "specific",
  "next_best_action": "route_to_support",
  "partner_hint": "unknown",
  "results": []
}
```

## Query 4: Partner-Specific Navigational Query

User query:

```text
Show me headphones on Amazon
```

Observed response summary:

```json
{
  "language": "en",
  "intent": "search",
  "specificity": "navigational",
  "next_best_action": "partner_specific_search",
  "partner_hint": "amazon",
  "entities": {
    "product_category": "electronics"
  }
}
```

Top recommendation:

```json
{
  "product_id": "amazon-022",
  "partner": "amazon",
  "name": "Anker Wireless Headphones noise cancelling",
  "category": "electronics",
  "price": 93.35,
  "currency": "EUR"
}
```

## Query 5: Comparison Query

User query:

```text
Compare cheap diapers from dm and Amazon
```

Observed response summary:

```json
{
  "language": "en",
  "intent": "comparison",
  "specificity": "navigational",
  "next_best_action": "compare_products",
  "partner_hint": "unknown",
  "comparison_summary": "Compared returned products by partner using price, category, promotion status, and relevance score. Cheapest returned option is Pampers Sensitive Wet Wipes 80 pcs from dm at 1.62 EUR. dm: 5 result(s), cheapest 1.62 EUR, top score 0.46, categories baby care, promotions 1. No returned matches for requested partner(s): amazon.",
  "comparison_criteria": [
    "price",
    "partner",
    "category",
    "promotion_status",
    "relevance_score"
  ]
}
```

## Conclusion

The current API demo covers:

- German product search,
- English discovery,
- German customer support routing,
- partner-specific navigational search,
- comparison routing with summary fields,
- clarification behavior for vague queries.

This is a lightweight MVP demo, not a managed production benchmark. The detailed response examples above are the stable local deterministic baseline. The verified managed Cloud Run results are summarized separately in this document because exact product ordering can vary with BigQuery table contents, embeddings, and model version.
