# Stage 1 Scope

## 1. Project Goal

The lightweight assistant is a backend API for a PAYBACK-like shopping assistant. It receives a raw user query and returns either structured product recommendations or a clarifying question when the query is too vague to route confidently.

## 2. Stage 1 Goal

Stage 1 focuses only on defining the MVP scope, API contract, data schemas, and a stubbed FastAPI service. The implementation should prove the shape of the backend without adding real product retrieval, AI model calls, vector search, or deployment infrastructure.

## 3. In Scope for MVP

- Raw query input.
- Basic German and English language fields with deterministic stub handling.
- Intent categories represented in the API contract: `search`, `discovery`, `comparison`, `customer_support`.
- Specificity categories represented in the API contract: `specific`, `vague`, `navigational`.
- Next best action decision types represented in the API contract.
- Structured JSON response.
- Three partner types represented in the API contract: `dm`, `EDEKA`, `Amazon`.
- Stubbed assistant endpoint.
- Demo scenarios defined but not fully implemented.

## 4. Out of Scope for Stage 1

- Real product retrieval.
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

- Synthetic product catalog will be created in a later stage.
- Cold start will be handled by query context in later stages.
- The API contract should remain stable across later stages.

## 6. Success Criteria

- Documentation is clear.
- API schemas are defined.
- Stub endpoint returns a valid response.
- Tests validate the basic contract.
