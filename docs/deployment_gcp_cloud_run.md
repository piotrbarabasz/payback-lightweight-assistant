# GCP Cloud Run Deployment

## 1. Purpose

Stage 6 deploys the Dockerized FastAPI assistant API to Google Cloud Run using Artifact Registry as the container image repository. By default this deploys the deterministic rules intent backend and local keyword retrieval backend. Stage 8D adds optional BigQuery and Vertex AI runtime configuration for `RETRIEVAL_BACKEND=bigquery_vector`; Stage 9B adds optional Vertex/Gemini structured intent parsing with `INTENT_BACKEND=vertex_llm`. See [stage_8d_cloud_run_gcp_runtime.md](stage_8d_cloud_run_gcp_runtime.md).

## 2. Architecture

```text
Local machine
-> Docker build
-> Artifact Registry
-> Cloud Run service
-> public HTTPS endpoint
-> smoke test
```

## 3. Prerequisites

- Google Cloud account.
- Billing enabled for the selected project.
- `gcloud` CLI installed and authenticated.
- Docker installed and running locally.
- Required permissions to enable APIs, create Artifact Registry repositories, and deploy Cloud Run services.
- For optional BigQuery Vector Search retrieval, a Cloud Run service account with BigQuery and Vertex AI IAM access.
- For optional Vertex/Gemini intent parsing, a Cloud Run service account with Vertex AI IAM access.

## 4. Environment Variables

Set these variables before running the deployment scripts:

```bash
export GCP_PROJECT_ID="your-project-id"
export GCP_REGION="europe-west1"
export ARTIFACT_REPOSITORY="payback-assistant"
export IMAGE_NAME="payback-lightweight-assistant"
export IMAGE_TAG="latest"
export SERVICE_NAME="payback-lightweight-assistant"
# Optional, defaults to rules if unset.
export INTENT_BACKEND="rules"
# Optional, defaults to keyword if unset.
export RETRIEVAL_BACKEND="keyword"
```

Optional Vertex/Gemini intent parsing:

```bash
export INTENT_BACKEND="vertex_llm"
export CLOUD_RUN_SERVICE_ACCOUNT="payback-assistant-runtime@your-project-id.iam.gserviceaccount.com"
export VERTEX_AI_LOCATION="europe-west1"
export VERTEX_INTENT_MODEL="gemini-2.5-flash"
export INTENT_LLM_TIMEOUT_SECONDS="3"
```

The optional LLM backend only parses intent JSON and falls back to rules on Vertex/Gemini failures, invalid JSON, missing fields, timeout, or missing credentials. It does not change retrieval behavior or introduce autonomous planning.

## 5. Deployment Commands

Run from the repository root:

```bash
bash infra/gcp/setup_project.sh
bash infra/gcp/create_artifact_registry.sh
bash infra/gcp/build_and_push_image.sh
bash infra/gcp/deploy_cloud_run.sh
bash infra/gcp/smoke_test_deployed_api.sh
```

## 6. Manual Verification

After deployment, either export the printed Cloud Run URL or read it from `.cloud_run_url`:

```bash
export CLOUD_RUN_URL="$(cat .cloud_run_url)"
```

Check health:

```bash
curl "$CLOUD_RUN_URL/health"
```

Check the assistant endpoint:

```bash
curl -X POST "$CLOUD_RUN_URL/assistant/query" \
  -H "Content-Type: application/json" \
  -d '{"query":"Bitte zeige mir Angebote fuer guenstige Windeln","top_k":5}'
```

## 7. Cloud Run Configuration

The deployment script configures Cloud Run with:

- Memory: `512Mi`
- CPU: `1`
- Minimum instances: `0`
- Maximum instances: `3`
- Port: `8080`
- Unauthenticated access enabled for the recruitment demo

## 8. Limitations

- The default deployment still uses the local synthetic catalog packaged in the container.
- BigQuery and Vertex AI are optional Stage 8 runtime integrations and must be configured explicitly.
- Vertex/Gemini intent parsing is optional and must be configured explicitly with `INTENT_BACKEND=vertex_llm`.
- No real partner API integrations yet.

## 9. Future Improvements

- Cloud Build.
- GitHub Actions deployment.
- Secret Manager.
- Production IAM hardening.
- Managed retrieval fallback monitoring.
- Authenticated endpoints.
