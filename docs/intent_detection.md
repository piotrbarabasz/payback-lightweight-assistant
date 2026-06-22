# Intent Detection

## 1. Purpose

Stage 4 adds a deterministic intent detection module that converts a raw user query into structured intent information used by the assistant.

The module returns an internal `IntentDetectionResult` with language, entities, partner hints, intent, specificity, next best action, confidence, and optional clarification text. The API response remains `AssistantQueryResponse`.

## 2. Detection Flow

```text
query
-> language detection
-> entity extraction
-> partner hint detection
-> intent classification
-> specificity classification
-> next best action decision
-> optional clarifying question
```

The pure intent service lives in `app/intent/service.py`. Retrieval-aware response assembly remains outside the route handler in `app/assistant/service.py`.

## 3. Supported Languages

- `de`: German
- `en`: English
- `unknown`: fallback when language signals are unclear

## 4. Supported Intents

- `search`
- `discovery`
- `comparison`
- `customer_support`
- `unknown`

## 5. Specificity Types

- `specific`
- `vague`
- `navigational`
- `unknown`

## 6. Next Best Actions

- `search_catalog`
- `ask_clarifying_question`
- `partner_specific_search`
- `compare_products`
- `route_to_support`
- `fallback`

## 7. Example Outputs

German diaper search:

```json
{
  "query": "Bitte zeige mir Angebote fuer guenstige Windeln",
  "language": "de",
  "intent": "search",
  "specificity": "specific",
  "next_best_action": "search_catalog",
  "partner_hint": "unknown",
  "entities": {
    "product_category": "baby care",
    "price_preference": "cheap",
    "occasion": null,
    "dietary_preference": null,
    "brand": null
  },
  "requires_clarification": false
}
```

English pasta dinner discovery:

```json
{
  "query": "I need stuff for a pasta dinner",
  "language": "en",
  "intent": "discovery",
  "specificity": "specific",
  "next_best_action": "search_catalog",
  "partner_hint": "unknown",
  "entities": {
    "product_category": "pasta and grains",
    "occasion": "dinner"
  },
  "requires_clarification": false
}
```

Amazon navigational search:

```json
{
  "query": "Show me headphones on Amazon",
  "language": "en",
  "intent": "search",
  "specificity": "navigational",
  "next_best_action": "partner_specific_search",
  "partner_hint": "amazon",
  "entities": {
    "product_category": "electronics"
  },
  "requires_clarification": false
}
```

German PAYBACK support query:

```json
{
  "query": "Meine PAYBACK Punkte fehlen",
  "language": "de",
  "intent": "customer_support",
  "specificity": "specific",
  "next_best_action": "route_to_support",
  "partner_hint": "unknown",
  "requires_clarification": false
}
```

Vague query:

```json
{
  "query": "Something nice",
  "language": "unknown",
  "intent": "unknown",
  "specificity": "vague",
  "next_best_action": "ask_clarifying_question",
  "requires_clarification": true,
  "clarifying_question": "Are you looking for groceries, drugstore items, or general products?"
}
```

## 8. Limitations

- Rule-based only.
- No LLM yet.
- Limited German and English language detection.
- Limited entity extraction.
- No personalization.
- No context memory.

## 9. Future Improvements

- Optional LLM provider.
- Vertex AI / Gemini structured output.
- Confidence calibration.
- Multilingual expansion.
- More robust entity extraction.
