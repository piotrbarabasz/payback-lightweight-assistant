# Cloud Run Demo Results

This document summarizes the deployed API smoke test results for the `payback-lightweight-assistant` service.

The goal of this demo is to verify that the lightweight assistant API works correctly after deployment to Google Cloud Run and can handle multiple user intents, languages, partner hints, and response types.

## Deployment Summary

The application was containerized, built with Google Cloud Build, pushed to Artifact Registry, and deployed to Google Cloud Run.

## Cloud Run Service

Service name:

```text
payback-lightweight-assistant
```

Region:

```text
europe-west1
```

Cloud Run URL:

```text
https://payback-lightweight-assistant-62esvjlc2q-ew.a.run.app
```

## Verified Endpoints

The deployed service was verified using the smoke test script:

```bash
bash infra/gcp/smoke_test_deployed_api.sh
```

The following endpoints were tested successfully:

| Endpoint           | Method | Result |
| ------------------ | -----: | -----: |
| `/health`          |    GET | 200 OK |
| `/assistant/query` |   POST | 200 OK |

## Health Check Result

Request:

```http
GET /health
```

Response:

```json
{
  "status": "ok",
  "service": "payback-lightweight-assistant",
  "environment": "gcp-cloud-run"
}
```

## Demo Query 1: German Search Query

User query:

```text
Bitte zeige mir Angebote für günstige Windeln
```

Expected behavior:

The assistant should detect a German search intent, understand that the user is looking for cheap baby care products, and route the query to the most relevant partner catalog.

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

Result:

```text
PASSED
```

## Demo Query 2: English Discovery Query

User query:

```text
I need stuff for a pasta dinner
```

Expected behavior:

The assistant should detect a discovery-style query, infer the dinner occasion, identify the relevant grocery/pasta category, and search the EDEKA catalog.

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

Result:

```text
PASSED
```

## Demo Query 3: Navigational Partner-Specific Query

User query:

```text
Show me headphones on Amazon
```

Expected behavior:

The assistant should detect a partner-specific navigational query and route the search to the Amazon catalog.

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

Result:

```text
PASSED
```

## Demo Query 4: Customer Support Intent

User query:

```text
Meine PAYBACK Punkte fehlen
```

Expected behavior:

The assistant should detect a German customer support intent and avoid returning product recommendations.

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

Result:

```text
PASSED
```

## Demo Query 5: Vague Query Requiring Clarification

User query:

```text
Something nice
```

Expected behavior:

The assistant should detect that the request is vague and ask a clarifying question instead of returning weak or random recommendations.

Observed response summary:

```json
{
  "language": "unknown",
  "intent": "unknown",
  "specificity": "vague",
  "next_best_action": "ask_clarifying_question",
  "clarifying_question": "Are you looking for groceries, drugstore items, or general products?",
  "partner_hint": "unknown",
  "results": []
}
```

Result:

```text
PASSED
```

## Final Smoke Test Result

The deployed API smoke test completed successfully.

```text
Deployed API smoke test passed
```

## Conclusion

The deployed Cloud Run service successfully handles:

* health check verification,
* German search intent,
* English discovery intent,
* partner-specific routing,
* customer support routing,
* vague query clarification,
* structured JSON responses,
* cross-partner recommendation behavior.

The Cloud Run deployment is therefore verified as working for the current MVP scope.
