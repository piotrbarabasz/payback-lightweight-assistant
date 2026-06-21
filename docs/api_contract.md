# API Contract

This document defines the API contract for the lightweight assistant backend. Stage 2 still uses deterministic stub behavior for the assistant endpoint, but search-like queries can now return catalog-based mock results from the local synthetic catalog.

Base URL for local development:

```text
http://127.0.0.1:8000
```

## GET /health

### Purpose

- Health check endpoint for local development and future Cloud Run deployment.

### Response 200

```json
{
  "status": "ok",
  "service": "payback-lightweight-assistant"
}
```

## POST /assistant/query

### Purpose

- Main assistant endpoint.
- Accepts a raw user query.
- Returns either catalog-based mock product results, a clarifying question, or a support routing decision.
- Does not perform semantic search, ranking, embeddings, or LLM-based intent detection in Stage 2.

### Request Schema

```json
{
  "query": "Bitte zeige mir Angebote fuer guenstige Windeln",
  "user_id": null,
  "top_k": 5
}
```

### Request Fields

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `query` | string | yes | Raw user query. Must contain at least one non-whitespace character. |
| `user_id` | string or null | no | Reserved for future personalization. |
| `top_k` | integer | no | Number of product results requested. Defaults to `5`. Minimum `1`, maximum `20`. |

### Response Schema

```json
{
  "query": "Show me baby diapers",
  "language": "en",
  "intent": "search",
  "specificity": "specific",
  "next_best_action": "search_catalog",
  "clarifying_question": null,
  "partner_hint": "dm",
  "entities": {
    "product_category": "baby care",
    "price_preference": null,
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
      "score": 0.75,
      "reason": "Catalog-based mock result for Stage 2; no semantic retrieval or ranking applied."
    }
  ]
}
```

### Response Fields

| Field | Type | Notes |
| --- | --- | --- |
| `query` | string | Normalized query from the request. |
| `language` | enum | Detected or inferred query language. |
| `intent` | enum | User intent category. |
| `specificity` | enum | Whether the query is specific, vague, navigational, or unknown. |
| `next_best_action` | enum | Recommended downstream action for the backend or client. |
| `clarifying_question` | string or null | Present when the assistant should ask for more detail. |
| `partner_hint` | enum or null | Partner inferred from the query, `unknown`, or null. |
| `entities` | object | Structured entities extracted or mocked from the query. |
| `results` | array | Product result objects. Stage 2 results are catalog-based mock results, not ranked retrieval output. |

### QueryEntities Object

```json
{
  "product_category": null,
  "price_preference": null,
  "occasion": null,
  "dietary_preference": null,
  "brand": null
}
```

### Result Object

```json
{
  "product_id": "dm-001",
  "name": "Penaten Baby Diapers Size 4 42 pcs",
  "partner": "dm",
  "category": "baby care",
  "price": 9.6,
  "currency": "EUR",
  "score": 0.75,
  "reason": "Catalog-based mock result for Stage 2; no semantic retrieval or ranking applied."
}
```

## Development Endpoints

These endpoints are intended for local development and demos only. They expose the synthetic Stage 2 catalog so later retrieval work can be inspected without adding semantic search, ranking, embeddings, or cloud integrations.

## GET /catalog/products

### Purpose

- Preview products from the local synthetic catalog.
- Apply simple deterministic filters.
- Return raw catalog `Product` objects.

### Query Parameters

| Parameter | Type | Required | Default | Notes |
| --- | --- | --- | --- | --- |
| `partner` | enum or null | no | null | Optional partner filter: `dm`, `edeka`, or `amazon`. |
| `category` | string or null | no | null | Optional case-insensitive category filter. |
| `available_only` | boolean | no | `true` | When true, only products with `availability: true` are returned. |
| `limit` | integer | no | `20` | Minimum `1`, maximum `100`. |

### Response 200

```json
[
  {
    "product_id": "dm-001",
    "partner": "dm",
    "name": "Penaten Baby Diapers Size 4 42 pcs",
    "name_de": "Penaten Babywindeln Groesse 4 42 Stueck",
    "category": "baby care",
    "description": "Soft absorbent diapers for babies from 9 to 14 kg...",
    "description_de": "Weiche saugfaehige Windeln fuer Babys von 9 bis 14 kg...",
    "brand": "Penaten",
    "price": 9.6,
    "currency": "EUR",
    "tags": ["dm", "baby care", "42 pcs", "drugstore", "baby diapers"],
    "tags_de": ["dm", "babypflege", "42 stueck", "drogerie", "babywindeln"],
    "availability": true,
    "popularity_score": 0.96,
    "is_promotion": true,
    "product_url": "https://www.dm.example/product/dm-001"
  }
]
```

## Enum Values

### language

- `de`
- `en`
- `unknown`

### intent

- `search`
- `discovery`
- `comparison`
- `customer_support`
- `unknown`

### specificity

- `specific`
- `vague`
- `navigational`
- `unknown`

### next_best_action

- `search_catalog`
- `ask_clarifying_question`
- `partner_specific_search`
- `compare_products`
- `route_to_support`
- `fallback`

### partner

- `dm`
- `edeka`
- `amazon`
- `unknown`

## Validation Notes

- Invalid request bodies should return `422 Unprocessable Entity`.
- Blank or missing `query` values are invalid.
- `top_k` must be between `1` and `20`.
- `/catalog/products` `limit` must be between `1` and `100`.
- Unknown enum outcomes should use `unknown` or `fallback` instead of omitting required response fields.
