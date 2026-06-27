# Performance and Cost Notes

This document summarizes the main performance and cost-related decisions behind the current `payback-lightweight-assistant` MVP.

The system was designed as a lightweight backend API for a recruitment challenge. The goal was to provide a working end-to-end solution that can understand user intent, search across multiple partner catalogs, return structured JSON responses, and run on Google Cloud Run with minimal operational overhead.

## Current Runtime Model

The current version runs as a containerized FastAPI application and is ready to deploy to Google Cloud Run using the included scripts.

The default request path is intentionally lightweight:

```text
User query
-> FastAPI endpoint
-> rules intent backend
-> keyword retrieval backend
-> rule-based scoring and ranking
-> structured JSON response
```

The default MVP path uses the `keyword` retrieval backend and does not call external LLMs, embedding APIs, BigQuery, or vector search during request processing.

Stage 7A also includes an optional `hybrid` backend for local experiments. It uses deterministic local hash embeddings and in-process cosine similarity only; it does not call Vertex AI, BigQuery, BigQuery Vector Search, or external model APIs.

Stage 8 adds an optional `bigquery_vector` backend. That backend embeds the user query with Vertex AI and queries BigQuery Vector Search. It is not enabled by default and should be evaluated separately from the local MVP path. Stage 10B adds resilience to this managed path: if the managed embedding or BigQuery query fails at request time, the service logs a warning and falls back to local keyword retrieval when the packaged catalog is available.

Stage 9B adds an optional `vertex_llm` intent backend. That backend uses Vertex/Gemini only to classify the raw query into the existing structured intent fields. It is not enabled by default and falls back to deterministic rules on timeout, missing credentials, invalid JSON, missing fields, unsupported values, or inconsistent policy output.

The three common modes are:

| Mode | Intent backend | Retrieval backend | Cost profile |
| --- | --- | --- | --- |
| Default local | `rules` | `keyword` | Lowest cost; no managed model or database calls. |
| Managed retrieval | `rules` | `bigquery_vector` | Adds Vertex AI query embedding calls and BigQuery Vector Search jobs, with local keyword fallback for transient managed-service failures. |
| Optional LLM intent + managed retrieval | `vertex_llm` | `bigquery_vector` | Adds a Gemini JSON intent classification call before retrieval decisions. |

## Performance-Oriented Design Decisions

### 1. No LLM Call in the Default Request Path

The default MVP uses deterministic intent detection instead of an LLM-based classifier.

This reduces:

* network latency,
* inference latency,
* request cost,
* dependency on model availability,
* debugging complexity.

This is suitable for the MVP because the supported intent set is limited and the expected query patterns are known.

When `INTENT_BACKEND=vertex_llm` is configured, the LLM is limited to strict JSON intent parsing. It does not retrieve products, write final answers, plan tool calls, use memory, or run an autonomous loop. The rules backend remains the reliability fallback.

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
* `bigquery_vector`: optional managed backend using Vertex AI query embeddings and BigQuery Vector Search.

This allows local experimentation and managed retrieval testing without making either path mandatory for Cloud Run.

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

### 2. Vertex AI Is Optional

Vertex AI is not enabled in the default request path.

Reason:

* no per-request model inference cost,
* lower latency,
* fewer IAM and quota dependencies,
* simpler reproducibility for the reviewer.

Stage 8 includes a real Vertex AI text embedding provider and product embedding generation script. Costs are introduced when those scripts or the `bigquery_vector` backend call Vertex AI.

The local `hybrid` backend does not change this. It uses a deterministic local embedding provider and makes no Vertex AI calls.

Vertex embedding calls add:

* external network latency,
* model request cost,
* quota and regional availability considerations,
* IAM and credential requirements.

Product embeddings should be generated offline or in a controlled refresh job. Request-time Vertex calls should be limited to the user query embedding when managed vector retrieval is enabled.

Optional `INTENT_BACKEND=vertex_llm` also uses Vertex AI / Gemini, but only for structured intent classification. It adds one managed model call before retrieval decisions and should be enabled only when the additional latency, IAM dependency, and model request cost are acceptable.

The `bigquery_vector` runtime path depends on Vertex AI online prediction quota for query embeddings. If quota is exhausted, for example `429 RESOURCE_EXHAUSTED` on the embedding model, the retriever treats the managed path as unavailable for that request and falls back to local keyword retrieval. Fallback product reasons are prefixed with text such as `Fallback keyword retrieval used because managed vector retrieval was unavailable.`

### 3. BigQuery Vector Search Is Optional

BigQuery Vector Search is not used in the default MVP.

Reason:

* the synthetic catalog is small,
* in-memory retrieval is sufficient for the current scope,
* avoiding BigQuery keeps the demo cheaper and easier to run,
* no need to manage embedding generation and vector indexes for the MVP.

Stage 8 includes a real optional BigQuery Vector Search backend. It becomes useful when the product catalog grows beyond the size where simple in-memory search is appropriate.

The local `hybrid` backend does not use BigQuery. It computes product embeddings and cosine similarity inside the FastAPI process for prototype-scale experiments.

BigQuery costs and performance depend on:

* table storage size,
* embedding column size,
* query volume,
* whether vector search uses brute-force search or a vector index,
* metadata filters such as partner and category,
* selected candidate pool size such as `BIGQUERY_VECTOR_TOP_K`.

For the tiny synthetic catalog, a vector index is not required. At production scale, an index can reduce latency and scanned work, but introduces index build and maintenance overhead.

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

The default implementation is expected to have low latency because it avoids:

* LLM inference,
* external embedding generation,
* external API calls,
* database queries,
* vector index calls.

The main processing steps are local Python function calls over a small product catalog.

When `RETRIEVAL_BACKEND=hybrid` is enabled locally, the service performs additional in-process hash embedding and cosine similarity work. This is acceptable for the small synthetic catalog but is not intended as a production vector search substitute.

When `RETRIEVAL_BACKEND=bigquery_vector` is enabled, latency includes Vertex AI query embedding and BigQuery Vector Search. When `INTENT_BACKEND=vertex_llm` is also enabled, latency additionally includes Gemini JSON classification. Timeouts and fallback behavior protect reliability, but managed calls should be measured separately from the local default path.

Repeated identical managed-retrieval queries can reuse a small in-memory query embedding cache. The cache stores only successful embeddings, uses normalized query text as the key, and defaults to roughly 128 entries. This reduces repeated Vertex embedding calls during demos and smoke tests, but it is not a substitute for realistic quota planning.

For the current MVP, this is a reasonable trade-off between capability, cost, and simplicity.

## Load Test Results

No formal production load-test result is committed with the repository. Manual validation has confirmed the Cloud Run managed path returns `200 OK` for `/health` and the five smoke-test assistant queries.

Use the local/API load-test script below to record environment-specific numbers before presenting benchmark claims. Results depend on local hardware, Cloud Run cold starts, region, BigQuery table size, Vertex model latency, online prediction quota, network path, and request mix.

For the managed GCP path, use realistic pacing or intentionally repeated cached queries. A high-rate load test with many unique search queries can exhaust Vertex AI embedding quota and trigger fallback retrieval. The script reports status-code and exception breakdowns so `500` responses remain visible.

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

Then run the load test with the default local base URL, `http://localhost:8080`:

```bash
python scripts/load_test_api.py
```

Or point it at a specific endpoint:

```bash
python scripts/load_test_api.py --base-url http://127.0.0.1:8080 --requests 100
```

Add a delay between sequential requests when testing quota-sensitive managed services:

```bash
python scripts/load_test_api.py --base-url https://your-service-url.a.run.app --requests 50 --delay-seconds 0.5
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
- status-code breakdown,
- exception breakdown,
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

## Stage 8 Managed Retrieval Cost And Performance

The optional Stage 8 GCP-native retrieval path uses:

```text
Cloud Run API
-> Vertex AI Text Embeddings
-> BigQuery product table with embeddings
-> BigQuery Vector Search
-> hybrid reranking
-> JSON response
```

This can improve semantic retrieval quality, especially for vague or natural language discovery queries.

It also introduces:

* embedding generation cost,
* BigQuery storage cost,
* BigQuery query cost,
* additional IAM configuration,
* additional latency from external service calls,
* more complex deployment and monitoring.

Cloud Run runtime notes:

* The default keyword backend can scale to zero and does not require GCP data/model calls.
* The `bigquery_vector` backend should run under a Cloud Run service account with least-privilege BigQuery and Vertex AI access.
* Cold starts may add latency before Vertex AI and BigQuery clients are initialized.
* Frontend clients should call Cloud Run only; BigQuery and Vertex AI access should remain server-side.

## Recommended Production Optimization Strategy

When using Vertex AI and BigQuery Vector Search, the recommended approach is:

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

The optional local `hybrid` backend improves experimentation with semantic-like signals, but it is deliberately not the default Cloud Run path. The optional `bigquery_vector` backend is the managed semantic retrieval path and should be enabled only when the BigQuery catalog, embeddings, IAM, and environment variables are ready.

This is acceptable for the current lightweight MVP because the challenge focuses on demonstrating the backend core, intent routing, recommendation behavior, and cloud deployment readiness.

## Summary

The current MVP is optimized for a cost-efficient recruitment demo:

* Cloud Run-ready FastAPI backend,
* no expensive model calls in the request path,
* no database dependency,
* deterministic intent detection,
* default deterministic keyword retrieval and ranking,
* optional local hybrid retrieval for experiments,
* optional Vertex/Gemini JSON intent parsing with rules fallback,
* explainable recommendation reasons,
* local and deployed smoke-test scripts.

Vertex AI, BigQuery Vector Search, and Vertex/Gemini intent parsing are implemented as optional integrations, not mandatory dependencies for the lightweight MVP.
