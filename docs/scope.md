# Project Scope

## 1. Project Goal

The lightweight assistant is a backend API for a PAYBACK-like shopping assistant. It receives a raw user query and returns either structured product recommendations or a clarifying question when the query is too vague to route confidently.

The default repository runtime is local-first and deterministic. It does not use Vertex AI, BigQuery, BigQuery Vector Search, Gemini, real partner APIs, or an autonomous LLM agent loop unless an optional managed backend is explicitly configured.

## 2. Stage Goals

- Stage 1 defined the MVP scope, API contract, data schemas, and initial FastAPI service.
- Stage 2 added a validated synthetic product catalog and local catalog utilities.
- Stage 3 added deterministic keyword retrieval over the synthetic catalog without AI model calls, vector search, or deployment infrastructure.
- Stage 4 added deterministic intent detection, language detection, entity extraction, specificity classification, partner hint detection, and next-best-action logic.
- Stage 5 added Docker and local deployment readiness.
- Stage 6 added minimal Cloud Run deployment scripts and smoke-testing support for the existing containerized FastAPI app.
- Stage 7A added a retrieval backend abstraction with a local hybrid prototype.
- Stage 7B was documentation cleanup, production-readiness alignment, and explicit pre-Stage 8 scoping.
- Stage 8 added optional GCP-native retrieval integrations and documents remaining production hardening.
- Stage 9 added lightweight deterministic agent boundaries and optional Vertex/Gemini structured intent parsing with rules fallback.

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
- Optional local hybrid retrieval prototype using deterministic local hash embeddings.
- Support routing and clarifying question behavior.
- Modular deterministic intent detection with an optional Vertex/Gemini provider interface.
- Docker and Docker Compose usage for local runs.
- Cloud Run deployment scripts and smoke-test flow for the current containerized local MVP.
- Optional BigQuery catalog foundation scripts.
- Optional Vertex AI embedding provider and product embedding generation script.
- Optional BigQuery Vector Search retriever.
- Optional Cloud Run runtime service-account configuration for managed retrieval.
- Optional Vertex/Gemini structured intent parser with rules fallback.

## 4. Local / Mock / Prototype Only

- The catalog is synthetic and checked into the repository.
- Retrieval is in-process and uses local data.
- The optional `hybrid` backend is a deterministic local prototype, not managed semantic search.
- Vertex AI and BigQuery Vector Search are optional Stage 8 extensions and are not part of the default runtime path.
- Cloud Run deployment keeps the same local MVP behavior inside a container.

## 5. Out of Scope / Remaining Limitations

- Vertex AI, BigQuery Vector Search, or Gemini in the default local runtime.
- Real partner API integrations.
- Autonomous LLM-based agent loops.
- Conversation memory.
- Production authentication, rate limiting, or monitoring.
- User history.
- Shopping cart.
- Payments.
- Real PAYBACK account integration.

## 6. Assumptions

- The synthetic catalog is sufficient for local deterministic retrieval tests.
- Managed semantic retrieval, external integrations, and personalization require explicit non-default configuration or future production work.
- The API contract should remain stable across later stages.

## 7. Success Criteria

- Documentation is clear.
- API schemas are defined.
- Assistant endpoint returns valid support, clarification, and catalog retrieval responses.
- Tests validate the API contract, catalog utilities, and retrieval behavior.

## 8. Stage 8 Scope

Stage 8 introduces optional production-integration building blocks while preserving the local deterministic fallback:

- Vertex AI text embeddings.
- BigQuery product catalog storage.
- BigQuery Vector Search.
- Catalog ingestion and embedding refresh jobs.
- Cloud Run runtime service-account setup for managed retrieval.

Still future or production-hardening work:

- Secret Manager integration where needed.
- Observability, rate limiting, and authentication.
- Managed ingestion scheduling.
- Production monitoring for managed-to-local fallback behavior.
- Autonomous LLM agent orchestration if required by the product scope.
