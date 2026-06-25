# Demo Results

This document summarizes the current API demo behavior for the lightweight assistant.

The service is local-first and deterministic. The same code path is used for local development and the Cloud Run deployment. It does not rely on Vertex AI, BigQuery, BigQuery Vector Search, or real partner API integrations.

## Demo Environment

- These examples are generated from the deterministic local MVP behavior.
- The same containerized code path can be smoke-tested locally or on Cloud Run.
- A Cloud Run deployment, when used, still relies on the packaged synthetic catalog and local retrieval.

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

This is a lightweight MVP demo, not a managed production benchmark. The response behavior comes from the local deterministic backend and the Cloud Run deployment uses the same code path.
