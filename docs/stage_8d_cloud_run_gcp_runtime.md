# Stage 8D Cloud Run GCP Runtime

Stage 8D updates the Cloud Run deployment path so the backend can optionally
call BigQuery and Vertex AI through a Cloud Run service account. The frontend
must call the Cloud Run HTTP API only. Browser or frontend code should never
call BigQuery or Vertex AI directly.

The default deployment remains the local keyword backend:

```text
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
export BIGQUERY_DATASET="payback_catalog"
export CLOUD_RUN_SERVICE_ACCOUNT_NAME="payback-assistant-runtime"

bash infra/gcp/setup_cloud_run_service_account.sh
```

The script grants:

- `roles/bigquery.jobUser` on the project so Cloud Run can run query jobs.
- `roles/aiplatform.user` on the project so Cloud Run can call Vertex AI.
- `roles/bigquery.dataViewer` on the configured dataset when `bq` is available,
  otherwise at project scope with a warning.

After it runs, export the printed service account:

```bash
export CLOUD_RUN_SERVICE_ACCOUNT="payback-assistant-runtime@${GCP_PROJECT_ID}.iam.gserviceaccount.com"
```

Prefer dataset-level BigQuery read access in production. Avoid broad owner or
editor roles for the Cloud Run runtime identity.

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
export RETRIEVAL_BACKEND="keyword"

bash infra/gcp/deploy_cloud_run.sh
bash infra/gcp/smoke_test_deployed_api.sh
```

Unset `RETRIEVAL_BACKEND` for the same default behavior.

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
export CLOUD_RUN_SERVICE_ACCOUNT="payback-assistant-runtime@${GCP_PROJECT_ID}.iam.gserviceaccount.com"

export RETRIEVAL_BACKEND="bigquery_vector"
export BIGQUERY_DATASET="payback_catalog"
export BIGQUERY_PRODUCTS_TABLE="products"
export BIGQUERY_LOCATION="europe-west1"
export BIGQUERY_VECTOR_TOP_K="25"

export GCP_LOCATION="europe-west1"
export VERTEX_AI_LOCATION="europe-west1"
export VERTEX_EMBEDDING_MODEL="text-embedding-005"

bash infra/gcp/deploy_cloud_run.sh
```

Optional, only for models that support output dimensionality:

```bash
export VERTEX_EMBEDDING_DIMENSIONS="256"
```

## Update Env Vars On Existing Service

Update an already deployed Cloud Run service without rebuilding the image:

```bash
gcloud run services update "$SERVICE_NAME" \
  --region="$GCP_REGION" \
  --service-account="$CLOUD_RUN_SERVICE_ACCOUNT" \
  --update-env-vars="RETRIEVAL_BACKEND=bigquery_vector,GCP_PROJECT_ID=$GCP_PROJECT_ID,GCP_LOCATION=$GCP_LOCATION,BIGQUERY_DATASET=$BIGQUERY_DATASET,BIGQUERY_PRODUCTS_TABLE=$BIGQUERY_PRODUCTS_TABLE,BIGQUERY_LOCATION=$BIGQUERY_LOCATION,BIGQUERY_VECTOR_TOP_K=$BIGQUERY_VECTOR_TOP_K,VERTEX_AI_LOCATION=$VERTEX_AI_LOCATION,VERTEX_EMBEDDING_MODEL=$VERTEX_EMBEDDING_MODEL" \
  --project="$GCP_PROJECT_ID"
```

Return to the keyword backend:

```bash
gcloud run services update "$SERVICE_NAME" \
  --region="$GCP_REGION" \
  --update-env-vars="RETRIEVAL_BACKEND=keyword" \
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
