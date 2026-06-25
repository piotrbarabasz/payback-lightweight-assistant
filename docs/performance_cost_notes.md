# Performance and Cost Notes

This document summarizes the main performance and cost-related decisions behind the current `payback-lightweight-assistant` MVP.

The system was designed as a lightweight backend API for a recruitment challenge. The goal was to provide a working end-to-end solution that can understand user intent, search across multiple partner catalogs, return structured JSON responses, and run on Google Cloud Run with minimal operational overhead.

## Current Runtime Model

The current version runs as a containerized FastAPI application and is ready to deploy to Google Cloud Run using the included scripts.

The request path is intentionally lightweight:

```text
User query
-> FastAPI endpoint
-> deterministic intent detection
-> configured in-memory retrieval backend
-> rule-based scoring and ranking
-> structured JSON response
```

The default MVP path uses the `keyword` retrieval backend and does not call external LLMs or embedding APIs during request processing.

Stage 7A also includes an optional `hybrid` backend for local experiments. It uses deterministic local hash embeddings and in-process cosine similarity only; it does not call Vertex AI, BigQuery, BigQuery Vector Search, or external model APIs.

## Performance-Oriented Design Decisions

### 1. No LLM Call in the Request Path

The current MVP uses deterministic intent detection instead of an LLM-based classifier.

This reduces:

* network latency,
* inference latency,
* request cost,
* dependency on model availability,
* debugging complexity.

This is suitable for the MVP because the supported intent set is limited and the expected query patterns are known.

### 2. In-Memory Product Catalog

The synthetic partner catalogs are loaded and searched in-process.

This avoids:

* database round trips,
* connection management,
* query engine latency,
* external service dependencies.

For the current dataset size, in-memory search is faster and simpler than using a managed database or vector store.

### 3. Deterministic Scoring

The default `keyword` retrieval backend uses deterministic scoring based on:

* product name matches,
* category matches,
* tag matches,
* description matches,
* partner hints,
* price preferences,
* promotion boosts,
* popularity boosts.

This makes the system predictable and explainable.

Each recommendation can include a reason explaining why the product was selected.

### 4. Pluggable Retrieval Backends

Stage 7A introduced a retrieval backend factory controlled by `RETRIEVAL_BACKEND`.

Supported values:

* `keyword`: default, low-cost deterministic keyword retrieval.
* `hybrid`: local prototype combining keyword score, deterministic local semantic-like similarity, and existing business boosts.

This allows local experimentation without making hybrid retrieval mandatory for Cloud Run.

### 5. Lightweight Container

The service is packaged as a Docker container based on Python 3.11 slim.

The container runs only the FastAPI application and its required dependencies.

This keeps the runtime simple and suitable for Cloud Run.

### 6. Serverless Deployment on Cloud Run

Cloud Run was selected because it is well suited for lightweight HTTP APIs.

Important configuration choices:

* no always-on virtual machine,
* no Kubernetes cluster,
* no GPU,
* no separate model serving infrastructure,
* no external database required for the MVP,
* service can scale down when not in use.

This keeps the demo deployment simple and cost-efficient.

## Cost-Oriented Design Decisions

### 1. Cloud Run Instead of GKE or VM

The MVP uses Cloud Run instead of GKE or Compute Engine.

Reason:

* lower operational overhead,
* no cluster management,
* no idle VM management,
* easier deployment,
* better fit for a small stateless HTTP API.

### 2. No Vertex AI in the Default MVP

Vertex AI is not enabled in the default request path.

Reason:

* no per-request model inference cost,
* lower latency,
* fewer IAM and quota dependencies,
* simpler reproducibility for the reviewer.

Vertex AI is a good candidate for a production extension, especially for text embeddings and LLM-based intent detection, but it is intentionally not required for the current lightweight version.

The local `hybrid` backend does not change this. It uses a deterministic local embedding provider and makes no Vertex AI calls.

### 3. No BigQuery Vector Search in the Default MVP

BigQuery Vector Search is not used in the default MVP.

Reason:

* the synthetic catalog is small,
* in-memory retrieval is sufficient for the current scope,
* avoiding BigQuery keeps the demo cheaper and easier to run,
* no need to manage embedding generation and vector indexes for the MVP.

BigQuery Vector Search would become useful when the product catalog grows beyond the size where simple in-memory search is appropriate.

The local `hybrid` backend does not use BigQuery. It computes product embeddings and cosine similarity inside the FastAPI process for prototype-scale experiments.

### 4. No Persistent Database

The current MVP does not require a persistent database.

Reason:

* product data is synthetic,
* catalog content is stable for the demo,
* no user accounts or user history are stored,
* no personalization state is required.

This reduces both cost and complexity.

## Cloud Deployment Verification Flow

The repository includes a Cloud Run deployment path and smoke-test script for verifying a deployed service.

Example service URL format:

```text
https://<cloud-run-service-url>
```

Expected smoke test result:

```text
Deployed API smoke test passed
```

Verified behaviors:

* health endpoint returns `200 OK`,
* German product search works,
* English discovery query works,
* partner-specific Amazon query works,
* German customer support query is routed to support,
* vague query returns a clarifying question.

## Latency Considerations

The current implementation is expected to have low latency because it avoids:

* LLM inference,
* external embedding generation,
* external API calls,
* database queries,
* vector index calls.

The main processing steps are local Python function calls over a small product catalog.

When `RETRIEVAL_BACKEND=hybrid` is enabled locally, the service performs additional in-process hash embedding and cosine similarity work. This is acceptable for the small synthetic catalog but is not intended as a production vector search substitute.

For the current MVP, this is a reasonable trade-off between capability, cost, and simplicity.

## Optional Local/API Load Test

A lightweight sequential load test is available at [`scripts/load_test_api.py`](scripts/load_test_api.py).

It can target:

- a local FastAPI instance on the default `uvicorn` port,
- a deployed Cloud Run URL,
- any other HTTP endpoint that exposes `POST /assistant/query`.

The script uses only the Python standard library. It is intentionally sequential and conservative by default so it does not overwhelm a local development server.

Run the API locally:

```bash
uvicorn app.main:app --reload
```

Then run the load test with the default local base URL, `http://localhost:8000`:

```bash
python scripts/load_test_api.py
```

Or point it at a specific endpoint:

```bash
python scripts/load_test_api.py --base-url http://127.0.0.1:8000 --requests 100
```

For a Cloud Run deployment, pass the deployed service URL explicitly:

```bash
python scripts/load_test_api.py --base-url https://your-service-url.a.run.app --requests 50
```

You can also set environment variables:

Windows PowerShell:

```powershell
$env:API_BASE_URL = "https://your-service-url"
$env:LOAD_TEST_REQUESTS = "100"
python scripts/load_test_api.py
```

The script reports:

- request count,
- success count,
- error count,
- average latency,
- p50 latency,
- p95 latency,
- p99 latency.

Interpretation:

- lower latency is better,
- a non-zero error count means the service failed some requests,
- p50 is the median observed request latency,
- p95 and p99 show slower tail responses,
- compare results only within similar environments and request mixes,
- use local and Cloud Run runs as directional checks, not as a formal benchmark.

This repository does not include a managed benchmark service or a published production load test result. Real benchmark numbers depend on the machine, network, Python runtime, container settings, Cloud Run cold starts, and request mix where the script is run.

## Scalability Considerations

The current architecture is stateless.

This means Cloud Run can scale horizontally by creating more container instances.

However, the current in-memory catalog approach is best suited for small or medium synthetic datasets.

For larger production-scale catalogs, the retrieval layer should be moved to a managed search or vector retrieval backend.

The current `hybrid` backend is a local prototype. It prepares the code structure for semantic retrieval, but it does not provide production-grade vector indexing or approximate nearest-neighbor search.

## Production Cost and Performance Extension

A production-grade version could use the following GCP-native architecture:

```text
Cloud Run API
-> Vertex AI Text Embeddings
-> BigQuery product table with embeddings
-> BigQuery Vector Search
-> hybrid reranking
-> JSON response
```

This would improve semantic retrieval quality, especially for vague or natural language discovery queries.

However, it would also introduce:

* embedding generation cost,
* BigQuery storage cost,
* BigQuery query cost,
* additional IAM configuration,
* additional latency from external service calls,
* more complex deployment and monitoring.

## Recommended Production Optimization Strategy

If the system is extended with Vertex AI and BigQuery Vector Search, the recommended approach is:

1. Generate product embeddings offline during catalog ingestion.
2. Store embeddings in BigQuery together with product metadata.
3. Generate query embeddings at request time.
4. Run vector search in BigQuery.
5. Apply business-rule reranking in the API.
6. Cache frequent query results if needed.
7. Keep deterministic fallback retrieval for resilience.

This allows the service to combine semantic search quality with predictable business logic.

## Current MVP Trade-Off

The current implementation prioritizes:

* working end-to-end delivery,
* low cost,
* low latency,
* simple deployment,
* explainable behavior,
* easy local and cloud testing.

It intentionally does not maximize semantic retrieval quality yet.

The optional local `hybrid` backend improves experimentation with semantic-like signals, but it is deliberately not the default Cloud Run path.

This is acceptable for the current lightweight MVP because the challenge focuses on demonstrating the backend core, intent routing, recommendation behavior, and cloud deployment readiness.

## Summary

The current MVP is optimized for a cost-efficient recruitment demo:

* Cloud Run-ready FastAPI backend,
* no expensive model calls in the request path,
* no database dependency,
* deterministic intent detection,
* default deterministic keyword retrieval and ranking,
* optional local hybrid retrieval for experiments,
* explainable recommendation reasons,
* local and deployed smoke-test scripts.

Vertex AI and BigQuery Vector Search are recommended as future production extensions, not as mandatory dependencies for the lightweight MVP.
