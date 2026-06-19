# Architecture Decisions: Stage 1

This document records the initial architecture decisions for the Stage 1 lightweight assistant backend.

## 1. Backend Framework

**Decision:** FastAPI

**Reason:**

- Simple API development.
- Built-in OpenAPI docs.
- Strong Pydantic integration.
- Good fit for Cloud Run container deployment later.

## 2. Schema Validation

**Decision:** Pydantic v2

**Reason:**

- Explicit request and response models.
- Easy validation.
- Strong typing.
- Useful for a stable API contract.

## 3. Stage 1 Response Behavior

**Decision:** The assistant endpoint returns a stubbed response that follows the final response schema.

**Reason:** This allows API contract validation before implementing retrieval and AI logic.

## 4. Intent Detection

**Decision:**

- Not implemented in Stage 1.
- Future implementation may use a rule-based detector and optional LLM/Vertex AI provider.

**Reason:** This keeps Stage 1 focused and prevents premature complexity.

## 5. Product Retrieval

**Decision:**

- Not implemented in Stage 1.
- Future implementation may use hybrid keyword + vector retrieval.

**Reason:** Retrieval requires a product catalog and embeddings, which belong to later stages.

## 6. Cloud Deployment

**Decision:**

- Not implemented in Stage 1.
- Future target is Cloud Run, with optional Vertex AI and BigQuery Vector Search.

**Reason:** Stage 1 should define the contract first, then deployment will follow.
