# Project Scope

## 1. Project Goal

The lightweight assistant is a backend API for a PAYBACK-like shopping assistant. It receives a raw user query and returns either structured product recommendations or a clarifying question when the query is too vague to route confidently.

## 2. Stage Goals

- Stage 1 defined the MVP scope, API contract, data schemas, and initial FastAPI service.
- Stage 2 added a validated synthetic product catalog and local catalog utilities.
- Stage 3 adds deterministic keyword retrieval over the synthetic catalog without AI model calls, vector search, or deployment infrastructure.

## 3. In Scope

- Raw query input.
- Basic German and English query handling.
- Intent categories represented in the API contract: `search`, `discovery`, `comparison`, `customer_support`.
- Specificity categories represented in the API contract: `specific`, `vague`, `navigational`.
- Next best action decision types represented in the API contract.
- Structured JSON response.
- Three partner types represented in the API contract: `dm`, `EDEKA`, `Amazon`.
- Synthetic catalog data for local retrieval.
- Deterministic keyword retrieval, scoring, and ranking.
- Support routing and clarifying question behavior.

## 4. Out of Scope

- Semantic retrieval.
- Real vector search.
- Embeddings.
- LLM calls.
- GCP deployment.
- Cloud Run.
- Vertex AI.
- BigQuery Vector Search.
- Authentication.
- User history.
- Shopping cart.
- Payments.
- Real PAYBACK account integration.

## 5. Assumptions

- The synthetic catalog is sufficient for local deterministic retrieval tests.
- Semantic retrieval and personalization will be handled in later stages.
- The API contract should remain stable across later stages.

## 6. Success Criteria

- Documentation is clear.
- API schemas are defined.
- Assistant endpoint returns valid support, clarification, and catalog retrieval responses.
- Tests validate the API contract, catalog utilities, and retrieval behavior.
