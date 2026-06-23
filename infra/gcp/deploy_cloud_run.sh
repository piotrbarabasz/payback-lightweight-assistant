#!/usr/bin/env bash
set -euo pipefail

REQUIRED_ENV_VARS=(
  GCP_PROJECT_ID
  GCP_REGION
  SERVICE_NAME
)

for var_name in "${REQUIRED_ENV_VARS[@]}"; do
  if [[ -z "${!var_name:-}" ]]; then
    echo "Missing required environment variable: ${var_name}" >&2
    exit 1
  fi
done

if ! command -v gcloud >/dev/null 2>&1; then
  echo "Missing required command: gcloud" >&2
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
IMAGE_URI_FILE="${REPO_ROOT}/.gcp_image_uri"
CLOUD_RUN_URL_FILE="${REPO_ROOT}/.cloud_run_url"

if [[ -n "${IMAGE_URI:-}" ]]; then
  echo "Using IMAGE_URI from environment"
elif [[ -f "${IMAGE_URI_FILE}" ]]; then
  IMAGE_URI="$(tr -d '[:space:]' < "${IMAGE_URI_FILE}")"
  echo "Using IMAGE_URI from ${IMAGE_URI_FILE}"
else
  echo "Missing IMAGE_URI. Set IMAGE_URI or run infra/gcp/build_and_push_image.sh to create .gcp_image_uri." >&2
  exit 1
fi

if [[ -z "${IMAGE_URI}" ]]; then
  echo "IMAGE_URI is empty" >&2
  exit 1
fi

echo "Deploying Cloud Run service: ${SERVICE_NAME}"
echo "Region: ${GCP_REGION}"
echo "Image URI: ${IMAGE_URI}"

gcloud run deploy "${SERVICE_NAME}" \
  --image "${IMAGE_URI}" \
  --region "${GCP_REGION}" \
  --platform managed \
  --allow-unauthenticated \
  --port 8080 \
  --memory 512Mi \
  --cpu 1 \
  --min-instances 0 \
  --max-instances 3 \
  --set-env-vars ENVIRONMENT=gcp-cloud-run,LOG_LEVEL=info,CATALOG_PATH=app/data/products.json,DEFAULT_TOP_K=5,MAX_TOP_K=20 \
  --project="${GCP_PROJECT_ID}"

SERVICE_URL="$(gcloud run services describe "${SERVICE_NAME}" \
  --region="${GCP_REGION}" \
  --format='value(status.url)' \
  --project="${GCP_PROJECT_ID}")"

echo "${SERVICE_URL}" > "${CLOUD_RUN_URL_FILE}"

echo "Cloud Run deployment complete"
echo "Service URL: ${SERVICE_URL}"
echo "Saved service URL to ${CLOUD_RUN_URL_FILE}"
