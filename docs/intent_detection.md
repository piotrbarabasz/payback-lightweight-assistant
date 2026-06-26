# Intent Detection

## 1. Purpose

Stage 7B keeps deterministic rule-based intent detection as the default behavior and wraps it in a small pluggable backend interface. Stage 9A exposes this behavior through a lightweight deterministic `IntentDetectionAgent`, with `DecisionAgent` and `AssistantAgent` making the routing and orchestration boundaries explicit. Stage 9B adds an optional Vertex/Gemini backend for strict JSON intent parsing.

This is not an autonomous LLM loop by default. The default `rules` backend is deterministic, single-pass, and local. `vertex_llm` is optional and uses Vertex AI / Gemini only to classify a raw query into the existing structured intent format.

The module returns an internal `IntentDetectionResult` with language, entities, partner hints, intent, specificity, next best action, confidence, and optional clarification text. The API response remains `AssistantQueryResponse`.

## 2. Detection Flow

```text
query
-> IntentDetectionAgent
-> configured intent backend
-> language detection
-> entity extraction
-> partner hint detection
-> intent classification
-> specificity classification
-> DecisionAgent next best action policy
-> optional clarifying question
```

The public intent service lives in `app/intent/service.py`. It delegates to `app/agents/intent_detection.py`, which delegates to the configured backend through `app/intent/factory.py`. Retrieval-aware response assembly remains outside the route handler in `app/assistant/service.py`, which delegates to `app/agents/assistant.py`.

## 3. Agent Layer

The agent layer is intentionally small and deterministic:

| Agent | Responsibility |
| --- | --- |
| `IntentDetectionAgent` | Calls the configured intent detector backend. Defaults to the existing rule-based detector. |
| `DecisionAgent` | Wraps the existing next-best-action and clarifying-question rules. |
| `AssistantAgent` | Coordinates intent results, no-retrieval actions, catalog retrieval, comparison summaries, and final `AssistantQueryResponse` assembly. |

The layer does not introduce LangChain, CrewAI, AutoGen, tool planning, recursive reasoning, memory, or autonomous multi-step execution.

## 4. Intent Backends

The backend is selected with `INTENT_BACKEND`.

| Backend | Default | Behavior |
| --- | --- | --- |
| `rules` | yes | Uses local deterministic language, entity, intent, specificity, and next-best-action rules. |
| `vertex_llm` | no | Calls Vertex AI / Gemini through `google-genai`, requires strict JSON output, validates it with Pydantic/domain rules, and falls back to `rules` on any failure. |

`vertex_llm` does not call retrieval tools, does not generate final assistant answers, and does not perform multi-step planning. It only produces fields for `IntentDetectionResult`.

## 5. Vertex LLM JSON Contract

The optional LLM backend accepts only a single JSON object with this contract:

```json
{
  "language": "de | en | unknown",
  "intent": "search | discovery | comparison | customer_support | unknown",
  "specificity": "specific | vague | navigational",
  "next_best_action": "search_catalog | ask_clarifying_question | partner_specific_search | compare_products | route_to_support",
  "partner_hint": "dm | edeka | amazon | unknown",
  "entities": {
    "product_category": null,
    "price_preference": null,
    "occasion": null,
    "dietary_preference": null,
    "brand": null
  },
  "clarifying_question": null
}
```

Extra fields, missing fields, invalid enum values, invalid JSON, unsupported fallback actions, or inconsistent `next_best_action` values are rejected.

If a vague classification omits `clarifying_question`, the backend generates the existing deterministic clarifying question. If validation or the Vertex call fails, the backend logs a warning and returns the deterministic rules result.

## 6. Supported Languages

- `de`: German
- `en`: English
- `unknown`: fallback when language signals are unclear

## 7. Supported Intents

- `search`
- `discovery`
- `comparison`
- `customer_support`
- `unknown`

## 8. Specificity Types

- `specific`
- `vague`
- `navigational`
- `unknown`

## 9. Next Best Actions

- `search_catalog`
- `ask_clarifying_question`
- `partner_specific_search`
- `compare_products`
- `route_to_support`
- `fallback`

## 10. Comparison Response Behavior

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

No LLM calls are used for retrieval scoring or comparison response generation.

## 11. Example Outputs

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

## 12. Limitations

- Default backend is rule-based.
- `vertex_llm` is optional and requires Vertex AI configuration.
- Vertex/Gemini output is accepted only if it validates against the strict JSON contract.
- No autonomous LLM loop or multi-agent framework.
- Limited German and English language detection.
- Limited entity extraction.
- No personalization.
- No context memory.

## 13. Future Improvements

- More intent examples and evaluation cases for `vertex_llm`.
- Confidence calibration.
- Multilingual expansion.
- More robust entity extraction.
