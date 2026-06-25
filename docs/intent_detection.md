# Intent Detection

## 1. Purpose

Stage 7B keeps deterministic rule-based intent detection as the default behavior and wraps it in a small pluggable backend interface. This makes the current design explicit while leaving room for a future Vertex AI or LLM-backed detector.

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

The public intent service lives in `app/intent/service.py`. It delegates to the configured backend through `app/intent/factory.py`. Retrieval-aware response assembly remains outside the route handler in `app/assistant/service.py`.

## 3. Intent Backends

The backend is selected with `INTENT_BACKEND`.

| Backend | Default | Behavior |
| --- | --- | --- |
| `rules` | yes | Uses local deterministic language, entity, intent, specificity, and next-best-action rules. |
| `vertex_placeholder` | no | Future backend skeleton only. It makes no external API calls and raises `NotImplementedError` if selected. |

The current service does not call Vertex AI, Gemini, external LLM APIs, LangChain, or Google Cloud client libraries for intent detection.

## 4. Supported Languages

- `de`: German
- `en`: English
- `unknown`: fallback when language signals are unclear

## 5. Supported Intents

- `search`
- `discovery`
- `comparison`
- `customer_support`
- `unknown`

## 6. Specificity Types

- `specific`
- `vague`
- `navigational`
- `unknown`

## 7. Next Best Actions

- `search_catalog`
- `ask_clarifying_question`
- `partner_specific_search`
- `compare_products`
- `route_to_support`
- `fallback`

## 8. Comparison Response Behavior

Comparison intent uses `next_best_action: compare_products`. Retrieval remains
deterministic and local, but the assistant response is comparison-oriented:

- explicit multi-partner comparison queries are not narrowed to only the first
  partner mention,
- returned product reasons include the compared partner, category, price,
  promotion status when available, and relevance score,
- `comparison_summary` explains the cheapest returned option, partner-level
  result counts, categories, top scores, promotion counts, and requested
  partners with no returned matches,
- `comparison_criteria` lists the fields used for comparison.

No LLM calls are used for this behavior.

## 9. Example Outputs

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

## 10. Limitations

- Default backend is rule-based.
- Vertex/LLM backend is a placeholder only.
- No Vertex AI, Gemini, or external LLM calls.
- Limited German and English language detection.
- Limited entity extraction.
- No personalization.
- No context memory.

## 11. Future Improvements

- Optional LLM provider.
- Vertex AI / Gemini structured output.
- Confidence calibration.
- Multilingual expansion.
- More robust entity extraction.
