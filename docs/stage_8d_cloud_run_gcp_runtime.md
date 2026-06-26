# Stage 8D Cloud Run GCP Runtime

Stage 8D updates the Cloud Run deployment path so the backend can optionally
call BigQuery and Vertex AI through a Cloud Run service account. The frontend
must call the Cloud Run HTTP API only. Browser or frontend code should never
call BigQuery or Vertex AI directly.

The default deployment remains the local keyword backend:

```text
INTENT_BACKEND=rules
RETRIEVAL_BACKEND=keyword
```

## Safety Prerequisites

- Billing must be enabled for the Google Cloud project.
- Required APIs must be enabled.
- Use a dedicated Cloud Run runtime service account for managed retrieval.
- Grant least-privilege IAM: BigQuery job execution, BigQuery product table read
  access, and Vertex AI embedding access.
- Do not commit credentials, service account keys, API keys, or secret values.
- Keep frontend traffic pointed at Cloud Run, not directly at Google data/model
  APIs.

## Required APIs

`infra/gcp/setup_project.sh` enables:

- Cloud Run API.
- Artifact Registry API.
- Cloud Build API.
- Cloud Logging API.
- IAM API.
- BigQuery API.
- Vertex AI API.

Run:

```bash
export GCP_PROJECT_ID="your-project-id"
export GCP_REGION="europe-west1"

bash infra/gcp/setup_project.sh
```

## Service Account And IAM

Create or reuse a runtime service account:

```bash
export GCP_PROJECT_ID="your-project-id"
export BIGQUERY_LOCATION="europe-west1"
export BIGQUERY_DATASET="payback_catalog"
export CLOUD_RUN_SERVICE_ACCOUNT_NAME="payback-assistant-runtime"

bash infra/gcp/setup_cloud_run_service_account.sh
```

The script grants:

- `roles/bigquery.jobUser` on the project so Cloud Run can run query jobs.
- `roles/aiplatform.user` on the project so Cloud Run can call Vertex AI.
- `roles/bigquery.dataViewer` on the configured dataset by attempting a
  BigQuery SQL `GRANT`.

The script no longer uses `bq add-iam-policy-binding` for dataset IAM because
that command can fail in some Cloud Shell environments with an allowlisting
error. If dataset-level `GRANT` is not available, the script prints a warning
and continues after creating the service account and project-level job/model
roles.

If project-level BigQuery table read access is acceptable for your project,
opt into the fallback explicitly:

```bash
export ALLOW_PROJECT_BIGQUERY_DATA_VIEWER="true"
bash infra/gcp/setup_cloud_run_service_account.sh
```

Prefer dataset-level BigQuery read access in production. Use project-level
`roles/bigquery.dataViewer` only when dataset-level IAM is blocked and the
broader read scope has been reviewed.

After it runs, export the printed service account:

```bash
export CLOUD_RUN_SERVICE_ACCOUNT="payback-assistant-runtime@${GCP_PROJECT_ID}.iam.gserviceaccount.com"
```

Avoid broad owner or editor roles for the Cloud Run runtime identity.

## Build Image

Use the existing Artifact Registry flow:

```bash
export GCP_PROJECT_ID="your-project-id"
export GCP_REGION="europe-west1"
export ARTIFACT_REPOSITORY="payback-assistant"
export IMAGE_NAME="payback-lightweight-assistant"
export IMAGE_TAG="latest"
export SERVICE_NAME="payback-lightweight-assistant"

bash infra/gcp/create_artifact_registry.sh
bash infra/gcp/build_and_push_image.sh
```

## Deploy With Keyword Backend

This keeps Cloud Run on the low-cost local retrieval path. It does not require
BigQuery, Vertex AI, or the Stage 8 runtime service account.

```bash
export GCP_PROJECT_ID="your-project-id"
export GCP_REGION="europe-west1"
export SERVICE_NAME="payback-lightweight-assistant"
export DEFAULT_TOP_K="5"
export MAX_TOP_K="20"
export INTENT_BACKEND="rules"
export RETRIEVAL_BACKEND="keyword"

bash infra/gcp/deploy_cloud_run.sh
bash infra/gcp/smoke_test_deployed_api.sh
```

Unset `INTENT_BACKEND` and `RETRIEVAL_BACKEND` for the same default behavior.

## Deploy With BigQuery Vector Backend

Run this only after:

1. Stage 8A created and loaded the BigQuery catalog.
2. Stage 8B generated product embeddings.
3. Stage 8C vector retrieval has been configured and tested.
4. The Cloud Run service account has the IAM access described above.

```bash
export GCP_PROJECT_ID="your-project-id"
export GCP_REGION="europe-west1"
export SERVICE_NAME="payback-lightweight-assistant"
export IMAGE_URI="europe-west1-docker.pkg.dev/${GCP_PROJECT_ID}/payback-assistant/payback-lightweight-assistant:latest"
export CLOUD_RUN_SERVICE_ACCOUNT="payback-assistant-runtime@${GCP_PROJECT_ID}.iam.gserviceaccount.com"

export RETRIEVAL_BACKEND="bigquery_vector"
export DEFAULT_TOP_K="5"
export MAX_TOP_K="20"

export GCP_LOCATION="europe-west1"
export BIGQUERY_DATASET="payback_catalog"
export BIGQUERY_PRODUCTS_TABLE="products"
export BIGQUERY_LOCATION="europe-west1"
export BIGQUERY_VECTOR_TOP_K="25"

export VERTEX_AI_LOCATION="europe-west1"
export VERTEX_EMBEDDING_MODEL="text-embedding-005"

bash infra/gcp/deploy_cloud_run.sh
```

For `RETRIEVAL_BACKEND=bigquery_vector`, `deploy_cloud_run.sh` requires the
runtime service account and the BigQuery/Vertex environment variables above.
The keyword backend remains the default when `RETRIEVAL_BACKEND` is unset.

Optional, only for models that support output dimensionality:

```bash
export VERTEX_EMBEDDING_DIMENSIONS="256"
```

## Deploy With Optional Vertex LLM Intent Backend

This changes only intent parsing. It does not change retrieval scoring, BigQuery
Vector Search behavior, response schema, or assistant orchestration. The backend
uses Vertex AI / Gemini to return strict JSON intent fields and falls back to
the deterministic `rules` backend on timeout, missing credentials, invalid JSON,
missing fields, unsupported output, or inconsistent actions.

```bash
export GCP_PROJECT_ID="your-project-id"
export GCP_REGION="europe-west1"
export SERVICE_NAME="payback-lightweight-assistant"
export IMAGE_URI="europe-west1-docker.pkg.dev/${GCP_PROJECT_ID}/payback-assistant/payback-lightweight-assistant:latest"
export CLOUD_RUN_SERVICE_ACCOUNT="payback-assistant-runtime@${GCP_PROJECT_ID}.iam.gserviceaccount.com"

export INTENT_BACKEND="vertex_llm"
export VERTEX_AI_LOCATION="europe-west1"
export VERTEX_INTENT_MODEL="gemini-3.5-flash"
export INTENT_LLM_TIMEOUT_SECONDS="3"

# Retrieval remains independent; keyword is still the default.
export RETRIEVAL_BACKEND="keyword"

bash infra/gcp/deploy_cloud_run.sh
```

Enable both optional managed retrieval and optional LLM intent parsing by
combining `INTENT_BACKEND=vertex_llm` with the `RETRIEVAL_BACKEND=bigquery_vector`
environment variables from the previous section.

## Update Env Vars On Existing Service

Update an already deployed Cloud Run service without rebuilding the image:

```bash
gcloud run services update "$SERVICE_NAME" \
  --region="$GCP_REGION" \
  --service-account="$CLOUD_RUN_SERVICE_ACCOUNT" \
  --update-env-vars="ENVIRONMENT=gcp-cloud-run,INTENT_BACKEND=rules,RETRIEVAL_BACKEND=bigquery_vector,GCP_PROJECT_ID=$GCP_PROJECT_ID,GCP_REGION=$GCP_REGION,GCP_LOCATION=$GCP_LOCATION,DEFAULT_TOP_K=$DEFAULT_TOP_K,MAX_TOP_K=$MAX_TOP_K,BIGQUERY_DATASET=$BIGQUERY_DATASET,BIGQUERY_PRODUCTS_TABLE=$BIGQUERY_PRODUCTS_TABLE,BIGQUERY_LOCATION=$BIGQUERY_LOCATION,BIGQUERY_VECTOR_TOP_K=$BIGQUERY_VECTOR_TOP_K,VERTEX_AI_LOCATION=$VERTEX_AI_LOCATION,VERTEX_EMBEDDING_MODEL=$VERTEX_EMBEDDING_MODEL" \
  --project="$GCP_PROJECT_ID"
```

Enable optional Vertex/Gemini intent parsing on an existing service:

```bash
gcloud run services update "$SERVICE_NAME" \
  --region="$GCP_REGION" \
  --service-account="$CLOUD_RUN_SERVICE_ACCOUNT" \
  --update-env-vars="INTENT_BACKEND=vertex_llm,GCP_PROJECT_ID=$GCP_PROJECT_ID,VERTEX_AI_LOCATION=$VERTEX_AI_LOCATION,VERTEX_INTENT_MODEL=${VERTEX_INTENT_MODEL:-gemini-3.5-flash},INTENT_LLM_TIMEOUT_SECONDS=${INTENT_LLM_TIMEOUT_SECONDS:-3}" \
  --project="$GCP_PROJECT_ID"
```

Return to the keyword backend:

```bash
gcloud run services update "$SERVICE_NAME" \
  --region="$GCP_REGION" \
  --update-env-vars="INTENT_BACKEND=rules,RETRIEVAL_BACKEND=keyword" \
  --project="$GCP_PROJECT_ID"
```

## View Logs

Stream recent Cloud Run logs:

```bash
gcloud run services logs tail "$SERVICE_NAME" \
  --region="$GCP_REGION" \
  --project="$GCP_PROJECT_ID"
```

Read logs through Cloud Logging:

```bash
gcloud logging read \
  "resource.type=cloud_run_revision AND resource.labels.service_name=$SERVICE_NAME" \
  --limit=50 \
  --project="$GCP_PROJECT_ID"
```

Useful things to look for:

- missing environment variable errors,
- Vertex/Gemini intent fallback warnings,
- Vertex AI embedding failures,
- BigQuery query permission errors,
- BigQuery Vector Search no-result errors,
- cold start latency.

## Runtime Boundary

The Cloud Run backend is the only component that should call BigQuery and
Vertex AI. The frontend should call:

```text
Frontend -> Cloud Run HTTPS API -> BigQuery / Vertex AI
```

Do not expose BigQuery table names, service account credentials, or model access
from frontend code.

## Manual validation evidence

The Stage 8D Cloud Run deployment has been manually validated with:

- Cloud Run service running with `RETRIEVAL_BACKEND=bigquery_vector`.
- Vertex AI query embeddings enabled through the backend service account.
- BigQuery Vector Search reading a product table with 150 products and 150
  embeddings.
- `/health` returning HTTP 200 with `environment=gcp-cloud-run`.
- German dm diaper, EDEKA pasta dinner, and Amazon headphones queries returning
  product results from BigQuery Vector Search.
- PAYBACK support queries routing to support.
- Vague queries returning a clarifying question.
