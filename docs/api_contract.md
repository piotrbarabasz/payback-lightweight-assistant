# API Contract

This document defines the API contract for the lightweight assistant backend. The current MVP uses deterministic intent detection and local retrieval over the synthetic catalog. It does not use Vertex AI, BigQuery, BigQuery Vector Search, Gemini, or real partner APIs.

Base URL for local development:

```text
http://127.0.0.1:8000
```

## GET /health

### Purpose

- Health check endpoint for local development and Cloud Run deployment.

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
- Returns keyword-ranked product results, a clarifying question, a support routing decision, or a comparison response.
- Performs deterministic query normalization, language detection, intent detection, specificity classification, partner hint detection, entity extraction, next-best-action selection, keyword matching, filtering, scoring, and ranking.
- Does not perform managed semantic search, Vertex AI embeddings, BigQuery retrieval, or LLM-based intent detection in the current MVP.

### Request Body

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
| `top_k` | integer | no | Requested number of product results. Defaults to `5`. Minimum `1`, maximum `20`. |

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
      "score": 0.4396,
      "reason": "Matched query terms in product tags and description."
    }
  ],
  "comparison_summary": null,
  "comparison_criteria": []
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
| `clarifying_question` | string or null | Present when the assistant should ask for more detail. Required when `next_best_action` is `ask_clarifying_question`. |
| `partner_hint` | enum or null | Partner inferred from the query, or `unknown` when no single partner is clear. |
| `entities` | object | Structured entities extracted from the query. |
| `results` | array | Ranked product result objects. Empty for support, clarification, and fallback responses. |
| `comparison_summary` | string or null | Present for `compare_products` responses. Summarizes the returned products using available catalog fields. |
| `comparison_criteria` | array | Present for `compare_products` responses. Lists compared fields such as `price`, `partner`, `category`, `promotion_status`, and `relevance_score`. Empty for non-comparison responses. |

### Intent Values

- `search`
- `discovery`
- `comparison`
- `customer_support`
- `unknown`

### Next Best Action Values

- `search_catalog`
- `ask_clarifying_question`
- `partner_specific_search`
- `compare_products`
- `route_to_support`
- `fallback`

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

### Comparison Behavior

- Comparison words such as `compare`, `comparison`, `vergleich`, or `vergleiche` return `intent: comparison` and `next_best_action: compare_products`.
- Comparison questions such as `Which partner has cheaper ...` also return `compare_products`.
- Comparison retrieval stays broad enough to compare partners. If a query names multiple partners, the response does not collapse to only the first partner hint.
- Comparison results are annotated with partner, category, price, promotion status when available, and relevance score.
- `comparison_summary` explains the cheapest returned option, partner-level result counts, categories, top relevance scores, promotion counts, and any requested partners that had no returned matches.

### Clarifying Question Behavior

- Vague queries such as `Something nice` return `ask_clarifying_question`.
- Support queries return `route_to_support`.
- When the assistant asks for clarification, `clarifying_question` is populated and `results` is empty.

### Retrieval Behavior

- Search-like queries are normalized and matched against English and German product names, descriptions, categories, and tags.
- Explicit partner tokens such as `dm`, `edeka`, or `amazon` restrict retrieval to that partner when possible.
- German and English keyword variants are handled by deterministic token normalization and a small synonym map.
- Simple price preferences are exposed in `entities.price_preference`, for example `cheap` or `premium`.
- Basic query entities are exposed in `entities`, including product category, price preference, occasion, dietary preference, and brand when detected.
- Scores are deterministic values in the `0..1` range.
- Result `reason` values explain which catalog fields matched and whether a price preference affected ranking.
- Meal, occasion, inspiration, or recommendation words such as `dinner`, `breakfast`, `lunch`, `abendessen`, `fruehstueck`, `ideas`, or `recommend` usually return `intent: discovery`.
- Explicit partner mentions return `specificity: navigational` and `next_best_action: partner_specific_search`, unless comparison routing applies.

### Error Behavior

- Invalid request bodies return `422 Unprocessable Entity`.
- Blank or missing `query` values are invalid.
- `top_k` must be between `1` and `20`.
- Unknown enum outcomes use `unknown` or `fallback` instead of omitting required fields.
- Unexpected server failures return `5xx` responses as normal HTTP errors; the API does not mask them as successful assistant responses.

## Development Endpoints

These endpoints are intended for local development and demos only. They expose the synthetic catalog so retrieval behavior can be inspected without adding embeddings or cloud integrations.

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
