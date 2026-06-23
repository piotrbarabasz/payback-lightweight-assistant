#!/usr/bin/env bash
set -euo pipefail

REQUIRED_ENV_VARS=(
  GCP_PROJECT_ID
  GCP_REGION
  ARTIFACT_REPOSITORY
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

REPOSITORY_HOST="${GCP_REGION}-docker.pkg.dev/${GCP_PROJECT_ID}/${ARTIFACT_REPOSITORY}"

echo "Configuring gcloud project: ${GCP_PROJECT_ID}"
gcloud config set project "${GCP_PROJECT_ID}"

echo "Checking Artifact Registry repository: ${ARTIFACT_REPOSITORY}"
if gcloud artifacts repositories describe "${ARTIFACT_REPOSITORY}" \
  --location="${GCP_REGION}" \
  --project="${GCP_PROJECT_ID}" >/dev/null 2>&1; then
  echo "Artifact Registry repository already exists: ${REPOSITORY_HOST}"
else
  echo "Creating Artifact Registry Docker repository: ${ARTIFACT_REPOSITORY}"
  gcloud artifacts repositories create "${ARTIFACT_REPOSITORY}" \
    --repository-format=docker \
    --location="${GCP_REGION}" \
    --description="Docker repository for PAYBACK Lightweight Assistant" \
    --project="${GCP_PROJECT_ID}"
fi

echo "Configuring Docker authentication for ${GCP_REGION}-docker.pkg.dev"
gcloud auth configure-docker "${GCP_REGION}-docker.pkg.dev" --quiet

echo "Artifact Registry repository is ready"
echo "${REPOSITORY_HOST}"
