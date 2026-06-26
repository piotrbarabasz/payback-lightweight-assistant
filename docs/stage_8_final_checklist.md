# Stage 8 Final Checklist

This checklist is for reviewer-facing validation. Run only the commands that
match the environment you actually have configured. Do not claim BigQuery,
Vertex AI, or deployed Cloud Run results unless the relevant command was run
successfully against a real GCP project.

## 1. Unit And Integration Tests

```bash
pytest
```

Expected local result: the test suite passes without calling GCP.

## 2. Local Keyword Smoke Test

Start the API with the default backend:

```bash
uvicorn app.main:app --host 127.0.0.1 --port 8080 --reload
```

Run:

```bash
python scripts/smoke_test_api.py
```

This validates the default local path:

```text
FastAPI -> rule-based intent -> keyword retrieval -> AssistantQueryResponse
```

## 3. BigQuery Catalog Verification

Requires Stage 8A BigQuery table setup and GCP credentials:

```bash
python scripts/gcp/verify_bigquery_catalog.py --sql-only
```

Run against BigQuery only when the GCP environment is configured:

```bash
python scripts/gcp/verify_bigquery_catalog.py
```

## 4. Embedding Generation Dry Run

Requires Stage 8B environment variables for config validation. Dry run prints
the SQL and does not call Vertex AI or BigQuery:

```bash
python scripts/gcp/generate_product_embeddings.py --dry-run
```

Run real embedding generation only when costs, IAM, and target table are
confirmed:

```bash
python scripts/gcp/generate_product_embeddings.py --limit 10 --batch-size 5
```

## 5. Optional Vector Index Dry Run

The index is optional for the small synthetic catalog. Render SQL without
calling BigQuery:

```bash
python scripts/gcp/create_bigquery_vector_index.py --dry-run
```

Create the index only for larger catalogs where latency or scan cost justifies
index build and maintenance overhead.

## 6. Optional BigQuery Vector Backend Smoke Test

Use only when the BigQuery catalog contains embeddings and the runtime has
Vertex AI and BigQuery permissions:

```bash
export RETRIEVAL_BACKEND="bigquery_vector"
export GCP_PROJECT_ID="your-project-id"
export BIGQUERY_DATASET="payback_catalog"
export BIGQUERY_PRODUCTS_TABLE="products"
export BIGQUERY_LOCATION="europe-west1"
export BIGQUERY_VECTOR_TOP_K="25"
export VERTEX_AI_LOCATION="europe-west1"
export VERTEX_EMBEDDING_MODEL="text-embedding-005"

uvicorn app.main:app --host 127.0.0.1 --port 8080 --reload
python scripts/smoke_test_api.py
```

## 7. Deployed Cloud Run Smoke Test

Requires an already deployed service:

```bash
export CLOUD_RUN_URL="https://your-service-url.a.run.app"
python scripts/smoke_test_api.py
```

Or use the repository wrapper:

```bash
bash infra/gcp/smoke_test_deployed_api.sh
```

For the Stage 8D managed runtime path, confirm Cloud Run uses a service account
with BigQuery and Vertex AI permissions. The frontend should call Cloud Run
only; it should not call BigQuery or Vertex AI directly.

## Known Remaining Limitations

- No real partner API integrations.
- No autonomous LLM agent loop.
- No production authentication or rate limiting.
- Managed-to-local fallback depends on the packaged local catalog and should be monitored in production.
- No published benchmark numbers.
- GCP costs depend on the project, region, query volume, embedding model, table
  size, and vector index usage.
