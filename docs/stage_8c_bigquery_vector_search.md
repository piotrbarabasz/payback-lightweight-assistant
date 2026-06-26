# Stage 8C BigQuery Vector Search

Stage 8C adds an optional BigQuery Vector Search retrieval backend. The default
local backend remains unchanged:

```text
RETRIEVAL_BACKEND=keyword
```

Enable the managed vector backend only after Stage 8A has loaded products into
BigQuery and Stage 8B has generated product embeddings.

## What Was Added

- `BigQueryVectorProductRetriever` in
  `app/retrieval/backends/bigquery_vector.py`.
- Vertex AI query embedding through `VertexAIEmbeddingProvider`.
- BigQuery `VECTOR_SEARCH` SQL against the configured products table.
- Optional vector index setup through
  `scripts/gcp/create_bigquery_vector_index.py` and
  `infra/gcp/create_vector_index.sql`.
- Partner and category filter support from the existing query analysis layer.
- Mapping from BigQuery rows back to the existing `ProductResult` response
  schema.
- Mock-only tests for SQL generation, query embedding calls, row mapping,
  filters, and error paths.

## Required APIs And Auth

Enable these APIs in the target Google Cloud project:

- Vertex AI API.
- BigQuery API.

The runtime identity needs:

- permission to call the configured Vertex AI embedding model,
- permission to run BigQuery jobs,
- permission to read the configured products table.

Use local Application Default Credentials for manual testing:

```powershell
gcloud auth application-default login
```

For deployed or scheduled workloads, use a dedicated service account with only
the required Vertex AI and BigQuery permissions.

## Environment Variables

Required:

```powershell
$env:GCP_PROJECT_ID = "your-project-id"
$env:BIGQUERY_DATASET = "payback_catalog"
$env:BIGQUERY_PRODUCTS_TABLE = "products"
$env:VERTEX_EMBEDDING_MODEL = "text-embedding-005"
```

Location:

```powershell
$env:BIGQUERY_LOCATION = "europe-west1"
$env:VERTEX_AI_LOCATION = "europe-west1"
```

`VERTEX_AI_LOCATION` is preferred for Vertex embeddings. If unset, the Vertex
provider can fall back to `GCP_LOCATION`.

Optional candidate pool size:

```powershell
$env:BIGQUERY_VECTOR_TOP_K = "25"
```

`BIGQUERY_VECTOR_TOP_K` controls how many BigQuery vector candidates are
requested before the API returns the requested `top_k` results. Keep it modest
until latency and cost are measured.

Optional vector index name:

```powershell
$env:BIGQUERY_VECTOR_INDEX = "products_embedding_idx"
```

## Optional Vector Index

BigQuery `VECTOR_SEARCH` can work without a vector index. For the tiny synthetic
catalog, brute-force vector search is simpler and usually sufficient. A vector
index becomes useful when the product table is large enough that latency,
scanned work, or concurrency makes brute-force search too expensive.

Tradeoff:

- Without an index: simpler setup and no index maintenance cost, but slower at
  larger scale.
- With an index: better production-scale latency and reduced search work, but
  BigQuery must build and maintain the index.

Render the SQL without calling BigQuery:

```powershell
.\.venv312\Scripts\python.exe scripts\gcp\create_bigquery_vector_index.py --dry-run
```

Create the index:

```powershell
.\.venv312\Scripts\python.exe scripts\gcp\create_bigquery_vector_index.py
```

Use a custom index name:

```powershell
.\.venv312\Scripts\python.exe scripts\gcp\create_bigquery_vector_index.py --index-name products_embedding_idx
```

Optionally tune IVF `num_lists` after measuring catalog size, latency, and
recall:

```powershell
.\.venv312\Scripts\python.exe scripts\gcp\create_bigquery_vector_index.py --num-lists 100 --dry-run
```

The checked-in SQL template is available at:

```text
infra/gcp/create_vector_index.sql
```

The index is optional. It is not required for unit tests, local smoke tests, or
the default `keyword` backend. BigQuery may populate a new vector index
asynchronously after the DDL job completes.

## Enable The Backend

Run the local API with BigQuery Vector Search:

```powershell
$env:RETRIEVAL_BACKEND = "bigquery_vector"
uvicorn app.main:app --host 127.0.0.1 --port 8080 --reload
```

Example request:

```powershell
curl -X POST "http://127.0.0.1:8080/assistant/query" `
  -H "Content-Type: application/json" `
  -d "{\"query\":\"Show me headphones on Amazon\",\"top_k\":5}"
```

Unset `RETRIEVAL_BACKEND` or set it back to `keyword` to return to the local
default backend.

## Query Shape

The backend embeds the user query with Vertex AI and then runs BigQuery
`VECTOR_SEARCH` against the products table. It selects product fields from the
catalog row and maps them into the existing response shape:

```text
ProductResult(product_id, partner, name, category, price, currency, score, reason)
```

The BigQuery vector distance is converted to a bounded score with:

```text
score = clamp(1 - distance, 0, 1)
```

Partner and category hints are applied as metadata filters when the existing
query analysis detects them.

## Graceful Failures

The backend fails clearly when:

- required environment values are missing,
- Vertex AI query embedding fails,
- the query embedding is empty,
- BigQuery query execution fails,
- no product rows are returned, which usually means embeddings are missing or
  filters are too narrow.

These failures affect only the explicitly enabled `bigquery_vector` backend.
The default local `keyword` backend remains available.

## Current Limitations

- No deployment is performed by this stage.
- Vector index setup is optional and not required for the small synthetic
  catalog.
- No automatic fallback to keyword retrieval is performed inside the backend.
- Product result details are limited to the existing public response schema.
- Performance, quota, and cost should be measured before production use.
