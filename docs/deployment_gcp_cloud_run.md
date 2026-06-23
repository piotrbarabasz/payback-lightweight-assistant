# GCP Cloud Run Deployment

## 1. Purpose

Stage 6 deploys the existing Dockerized FastAPI assistant API to Google Cloud Run using Artifact Registry as the container image repository.

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

## 4. Environment Variables

Set these variables before running the deployment scripts:

```bash
export GCP_PROJECT_ID="your-project-id"
export GCP_REGION="europe-west1"
export ARTIFACT_REPOSITORY="payback-assistant"
export IMAGE_NAME="payback-lightweight-assistant"
export IMAGE_TAG="latest"
export SERVICE_NAME="payback-lightweight-assistant"
```

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
  -d '{"query":"Bitte zeige mir Angebote für günstige Windeln","top_k":5}'
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

- The API still uses the local synthetic catalog packaged in the container.
- No BigQuery yet.
- No Vertex AI yet.
- No embeddings yet.
- No real partner API integrations yet.

## 9. Future Improvements

- Cloud Build.
- GitHub Actions deployment.
- Secret Manager.
- BigQuery product catalog.
- Vertex AI embeddings.
- BigQuery Vector Search.
- Authenticated endpoints.
