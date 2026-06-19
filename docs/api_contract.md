# API Contract

This document defines the planned API contract for Stage 1 and later stages of the lightweight assistant backend. It is a contract document, not implementation logic. Stage 1 may return stubbed values, but the response shape should remain stable as retrieval and AI components are added.

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
- Returns either recommended products or a clarifying question.

### Request Schema

```json
{
  "query": "Bitte zeige mir Angebote für günstige Windeln",
  "user_id": null,
  "top_k": 5
}
```

### Request Fields

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `query` | string | yes | Raw user query. Must contain at least one non-whitespace character. |
| `user_id` | string or null | no | Reserved for future personalization. |
| `top_k` | integer | no | Number of results requested. Defaults to `5`. Minimum `1`, maximum `20`. |

### Response Schema

```json
{
  "query": "Bitte zeige mir Angebote für günstige Windeln",
  "language": "de",
  "intent": "search",
  "specificity": "specific",
  "next_best_action": "search_catalog",
  "clarifying_question": null,
  "partner_hint": "unknown",
  "entities": {
    "product_category": "drugstore",
    "price_preference": null,
    "occasion": null,
    "dietary_preference": null,
    "brand": null
  },
  "results": [
    {
      "product_id": "mock-dm-001",
      "partner": "dm",
      "name": "Mock Drugstore Product",
      "category": "drugstore",
      "price": 4.99,
      "currency": "EUR",
      "score": 0.87,
      "reason": "Mock result for Stage 1 API contract validation."
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
| `entities` | object | Structured entities extracted from the query. Stage 1 may return null fields. |
| `results` | array | Product recommendation results. Stage 1 may return an empty array. |

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

Future retrieval stages should populate `results` with objects shaped like:

```json
{
  "product_id": "dm-windeln-001",
  "name": "Babylove Windeln Größe 4",
  "partner": "dm",
  "category": "Baby",
  "price": 9.95,
  "currency": "EUR",
  "score": 0.92,
  "reason": "Matches requested product and price preference."
}
```

Stage 1 does not perform real product retrieval, so `results` can be an empty array or contain clearly stubbed demo data.

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

## Example A: Product Recommendation Response

Request:

```json
{
  "query": "Bitte zeige mir Angebote für günstige Windeln",
  "user_id": null,
  "top_k": 5
}
```

Response:

```json
{
  "query": "Bitte zeige mir Angebote für günstige Windeln",
  "language": "de",
  "intent": "search",
  "specificity": "specific",
  "next_best_action": "search_catalog",
  "clarifying_question": null,
  "partner_hint": "unknown",
  "entities": {
    "product_category": "drugstore",
    "price_preference": null,
    "occasion": null,
    "dietary_preference": null,
    "brand": null
  },
  "results": [
    {
      "product_id": "mock-dm-001",
      "partner": "dm",
      "name": "Mock Drugstore Product",
      "category": "drugstore",
      "price": 4.99,
      "currency": "EUR",
      "score": 0.87,
      "reason": "Mock result for Stage 1 API contract validation."
    }
  ]
}
```

## Example B: Clarifying Question Response

Request:

```json
{
  "query": "Something nice",
  "user_id": null,
  "top_k": 5
}
```

Response:

```json
{
  "query": "Something nice",
  "language": "en",
  "intent": "discovery",
  "specificity": "vague",
  "next_best_action": "ask_clarifying_question",
  "clarifying_question": "Are you looking for groceries, drugstore items, or general products?",
  "partner_hint": "unknown",
  "entities": {
    "product_category": null,
    "price_preference": null,
    "occasion": null,
    "dietary_preference": null,
    "brand": null
  },
  "results": []
}
```

## Validation Notes

- Invalid request bodies should return `422 Unprocessable Entity`.
- Blank or missing `query` values are invalid.
- `top_k` must be between `1` and `20`.
- Unknown enum outcomes should use `unknown` or `fallback` instead of omitting required response fields.
