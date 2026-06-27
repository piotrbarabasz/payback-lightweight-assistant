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

INTENT_BACKEND="${INTENT_BACKEND:-rules}"
RETRIEVAL_BACKEND="${RETRIEVAL_BACKEND:-keyword}"
ENV_VARS=(
  "ENVIRONMENT=gcp-cloud-run"
  "LOG_LEVEL=info"
  "CATALOG_PATH=app/data/products.json"
  "GCP_PROJECT_ID=${GCP_PROJECT_ID}"
  "GCP_REGION=${GCP_REGION}"
  "DEFAULT_TOP_K=${DEFAULT_TOP_K:-5}"
  "MAX_TOP_K=${MAX_TOP_K:-20}"
  "INTENT_BACKEND=${INTENT_BACKEND}"
  "RETRIEVAL_BACKEND=${RETRIEVAL_BACKEND}"
)

if [[ "${RETRIEVAL_BACKEND}" == "bigquery_vector" ]]; then
  REQUIRED_BIGQUERY_VECTOR_ENV_VARS=(
    CLOUD_RUN_SERVICE_ACCOUNT
    GCP_LOCATION
    BIGQUERY_DATASET
    BIGQUERY_PRODUCTS_TABLE
    BIGQUERY_LOCATION
    VERTEX_AI_LOCATION
    VERTEX_EMBEDDING_MODEL
  )
  for var_name in "${REQUIRED_BIGQUERY_VECTOR_ENV_VARS[@]}"; do
    if [[ -z "${!var_name:-}" ]]; then
      echo "Missing required environment variable for RETRIEVAL_BACKEND=bigquery_vector: ${var_name}" >&2
      exit 1
    fi
  done

  ENV_VARS+=(
    "GCP_LOCATION=${GCP_LOCATION}"
    "BIGQUERY_DATASET=${BIGQUERY_DATASET}"
    "BIGQUERY_PRODUCTS_TABLE=${BIGQUERY_PRODUCTS_TABLE}"
    "BIGQUERY_LOCATION=${BIGQUERY_LOCATION}"
    "BIGQUERY_VECTOR_TOP_K=${BIGQUERY_VECTOR_TOP_K:-25}"
    "BIGQUERY_QUERY_EMBEDDING_CACHE_SIZE=${BIGQUERY_QUERY_EMBEDDING_CACHE_SIZE:-128}"
    "VERTEX_AI_LOCATION=${VERTEX_AI_LOCATION}"
    "VERTEX_EMBEDDING_MODEL=${VERTEX_EMBEDDING_MODEL}"
  )

  if [[ -n "${VERTEX_EMBEDDING_DIMENSIONS:-}" ]]; then
    ENV_VARS+=("VERTEX_EMBEDDING_DIMENSIONS=${VERTEX_EMBEDDING_DIMENSIONS}")
  fi
else
  echo "Deploying with local/default retrieval backend: ${RETRIEVAL_BACKEND}"
fi

if [[ "${INTENT_BACKEND}" == "vertex_llm" ]]; then
  REQUIRED_VERTEX_INTENT_ENV_VARS=(
    CLOUD_RUN_SERVICE_ACCOUNT
    VERTEX_AI_LOCATION
  )
  for var_name in "${REQUIRED_VERTEX_INTENT_ENV_VARS[@]}"; do
    if [[ -z "${!var_name:-}" ]]; then
      echo "Missing required environment variable for INTENT_BACKEND=vertex_llm: ${var_name}" >&2
      exit 1
    fi
  done

  if [[ "${RETRIEVAL_BACKEND}" != "bigquery_vector" ]]; then
    ENV_VARS+=("VERTEX_AI_LOCATION=${VERTEX_AI_LOCATION}")
  fi

  ENV_VARS+=(
    "VERTEX_INTENT_MODEL=${VERTEX_INTENT_MODEL:-gemini-2.5-flash}"
    "INTENT_LLM_TIMEOUT_SECONDS=${INTENT_LLM_TIMEOUT_SECONDS:-3}"
  )
elif [[ "${INTENT_BACKEND}" != "rules" ]]; then
  echo "Unsupported INTENT_BACKEND: ${INTENT_BACKEND}. Supported values: rules, vertex_llm" >&2
  exit 1
else
  echo "Deploying with deterministic intent backend: ${INTENT_BACKEND}"
fi

if [[ -n "${CLOUD_RUN_SERVICE_ACCOUNT:-}" ]]; then
  SERVICE_ACCOUNT_ARGS=(--service-account "${CLOUD_RUN_SERVICE_ACCOUNT}")
  echo "Using Cloud Run service account: ${CLOUD_RUN_SERVICE_ACCOUNT}"
else
  SERVICE_ACCOUNT_ARGS=()
  echo "Using Cloud Run default service account"
fi

ENV_VARS_CSV="$(IFS=,; echo "${ENV_VARS[*]}")"

echo "Deploying Cloud Run service: ${SERVICE_NAME}"
echo "Region: ${GCP_REGION}"
echo "Image URI: ${IMAGE_URI}"
echo "Intent backend: ${INTENT_BACKEND}"
echo "Retrieval backend: ${RETRIEVAL_BACKEND}"
echo "Default top_k: ${DEFAULT_TOP_K:-5}"
echo "Max top_k: ${MAX_TOP_K:-20}"

gcloud run deploy "${SERVICE_NAME}" \
  --image "${IMAGE_URI}" \
  --region "${GCP_REGION}" \
  --platform managed \
  "${SERVICE_ACCOUNT_ARGS[@]}" \
  --allow-unauthenticated \
  --port 8080 \
  --memory 512Mi \
  --cpu 1 \
  --min-instances 0 \
  --max-instances 3 \
  --set-env-vars "${ENV_VARS_CSV}" \
  --project="${GCP_PROJECT_ID}"

SERVICE_URL="$(gcloud run services describe "${SERVICE_NAME}" \
  --region="${GCP_REGION}" \
  --format='value(status.url)' \
  --project="${GCP_PROJECT_ID}")"

echo "${SERVICE_URL}" > "${CLOUD_RUN_URL_FILE}"

echo "Cloud Run deployment complete"
echo "Service URL: ${SERVICE_URL}"
echo "Saved service URL to ${CLOUD_RUN_URL_FILE}"
