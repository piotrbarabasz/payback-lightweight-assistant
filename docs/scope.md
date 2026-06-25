# Project Scope

## 1. Project Goal

The lightweight assistant is a backend API for a PAYBACK-like shopping assistant. It receives a raw user query and returns either structured product recommendations or a clarifying question when the query is too vague to route confidently.

## 2. Stage Goals

- Stage 1 defined the MVP scope, API contract, data schemas, and initial FastAPI service.
- Stage 2 added a validated synthetic product catalog and local catalog utilities.
- Stage 3 added deterministic keyword retrieval over the synthetic catalog without AI model calls, vector search, or deployment infrastructure.
- Stage 4 added deterministic intent detection, language detection, entity extraction, specificity classification, partner hint detection, and next-best-action logic.
- Stage 5 added Docker and local deployment readiness.
- Stage 6 added Cloud Run deployment scripts and smoke-testing support.
- Stage 7A added a retrieval backend abstraction with a local hybrid prototype.
- Stage 7B is documentation cleanup and production-readiness alignment only.

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
- Optional local hybrid retrieval prototype.
- Support routing and clarifying question behavior.
- Modular deterministic intent detection with a future provider interface.
- Docker and Docker Compose usage for local runs.
- Cloud Run deployment scripts and smoke-test flow.

## 4. Out of Scope

- Vertex AI embeddings.
- BigQuery product catalog.
- BigQuery Vector Search.
- Real partner API integrations.
- Real LLM-based agent loops.
- Conversation memory.
- Production authentication, rate limiting, or monitoring.
- User history.
- Shopping cart.
- Payments.
- Real PAYBACK account integration.

## 5. Assumptions

- The synthetic catalog is sufficient for local deterministic retrieval tests.
- Semantic retrieval, external integrations, and personalization will be handled in later stages.
- The API contract should remain stable across later stages.

## 6. Success Criteria

- Documentation is clear.
- API schemas are defined.
- Assistant endpoint returns valid support, clarification, and catalog retrieval responses.
- Tests validate the API contract, catalog utilities, and retrieval behavior.
