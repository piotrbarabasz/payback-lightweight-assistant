# Stage 8B Vertex AI Embeddings

Stage 8B adds a real optional Vertex AI text embedding provider. It does not
change the default local app behavior, does not change `RETRIEVAL_BACKEND`, and
does not implement BigQuery Vector Search.

The default retrieval backend remains:

```text
RETRIEVAL_BACKEND=keyword
```

## What Was Added

- `VertexAIEmbeddingProvider` in `app/embeddings/vertex_ai.py`.
- `scripts/gcp/generate_product_embeddings.py` for BigQuery product embedding
  generation.
- Single-text embedding with `embed_text(text: str) -> list[float]`.
- Batch embedding with `embed_texts(texts: list[str]) -> list[list[float]]`.
- Environment validation for Vertex AI configuration.
- Mock-only unit tests for config validation, empty text handling, batch calls,
  configured output dimensions, and upstream error handling.

The provider uses the official Google Gen AI SDK client in Vertex AI mode:

```python
from google import genai

client = genai.Client(vertexai=True, project=project_id, location=location)
```

## Required APIs And Auth

Enable the required Google Cloud APIs in the target project:

- Vertex AI API.
- BigQuery API, when using `generate_product_embeddings.py` to read and update
  product rows.

Use one of the normal Google Cloud authentication paths:

- local Application Default Credentials from `gcloud auth application-default login`,
- a service account attached to the runtime,
- another credential source supported by Google client libraries.

The caller needs IAM permission to call Vertex AI embedding models in the target
project. The embedding generation script also needs permission to query and
update the configured BigQuery products table. For a deployed service or batch
job, prefer a dedicated service account with only the permissions required for
embedding generation and table updates.

## Environment Variables

Set these variables before constructing `VertexAIEmbeddingProvider`:

```powershell
$env:GCP_PROJECT_ID = "your-project-id"
$env:GCP_LOCATION = "europe-west1"
$env:VERTEX_EMBEDDING_MODEL = "text-embedding-005"
```

The BigQuery embedding generation script also uses the Stage 8A table variables:

```powershell
$env:BIGQUERY_DATASET = "payback_catalog"
$env:BIGQUERY_PRODUCTS_TABLE = "products"
$env:BIGQUERY_LOCATION = "europe-west1"
```

`VERTEX_AI_LOCATION` can be used instead of `GCP_LOCATION`, and takes precedence
when both are set:

```powershell
$env:VERTEX_AI_LOCATION = "us-central1"
```

Optional output dimensionality:

```powershell
$env:VERTEX_EMBEDDING_DIMENSIONS = "256"
```

Only set `VERTEX_EMBEDDING_DIMENSIONS` for models that support configurable
output dimensionality. If unset, the provider lets the model return its default
embedding size.

Do not commit real project-specific secrets or service account material.

## Usage

```python
from app.embeddings.vertex_ai import VertexAIEmbeddingProvider

provider = VertexAIEmbeddingProvider()
query_embedding = provider.embed_text("cheap diapers at dm")
product_embeddings = provider.embed_texts(
    [
        "dm diapers baby care promotion",
        "edeka pasta dinner pantry",
    ]
)
```

The provider validates empty strings before making a Vertex AI call. An empty
batch returns an empty list and makes no API call.

## Generate Product Embeddings

After Stage 8A has created and loaded the BigQuery catalog, generate embeddings
for rows that have `embedding_text` but do not yet have an `embedding` value:

```powershell
.\.venv312\Scripts\python.exe scripts\gcp\generate_product_embeddings.py --dry-run
```

The dry run prints the target table and selection SQL without calling BigQuery
or Vertex AI.

Run a small safe batch:

```powershell
.\.venv312\Scripts\python.exe scripts\gcp\generate_product_embeddings.py --limit 10 --batch-size 5
```

The script prints:

- rows selected,
- embeddings generated,
- rows updated,
- failures.

By default, the script processes only 10 rows to keep costs controlled. Increase
the limit deliberately when testing a larger catalog:

```powershell
.\.venv312\Scripts\python.exe scripts\gcp\generate_product_embeddings.py --limit 25 --batch-size 5
```

To regenerate existing embeddings, use `--refresh`:

```powershell
.\.venv312\Scripts\python.exe scripts\gcp\generate_product_embeddings.py --refresh --limit 10 --batch-size 5
```

An uncapped refresh requires explicit confirmation:

```powershell
.\.venv312\Scripts\python.exe scripts\gcp\generate_product_embeddings.py --refresh --limit 0 --allow-full-refresh --batch-size 5
```

The script updates the BigQuery `embedding` column and sets `updated_at` for
each updated product row. It does not create a vector index and does not change
the assistant retrieval backend.

## Cost And Latency Tradeoff

Vertex AI embeddings improve semantic matching quality compared with the local
hash embedding prototype, but every request to the provider is an external model
call. That adds:

- per-call and per-token embedding cost,
- network latency,
- dependency on Google Cloud availability and credentials,
- quota and rate-limit considerations.

Batching with `embed_texts` is preferred for offline product embedding jobs
because it reduces request overhead. Request-time query embeddings should be
limited to paths that actually need semantic retrieval.

For product catalogs, the cost-efficient production shape is still:

1. Build stable `embedding_text` during catalog ingestion.
2. Generate product embeddings offline or in a refresh job.
3. Store the vectors beside product metadata.
4. Generate only the user query embedding at request time.

## Current Boundary

Stage 8B stops at embedding generation. It does not:

- create or query a BigQuery vector index,
- change `/assistant/query` retrieval behavior,
- deploy any GCP resources.

BigQuery Vector Search remains a separate future stage.
