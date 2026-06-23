#!/usr/bin/env bash
set -euo pipefail

# Usage:
# export GCP_PROJECT_ID="your-project-id"
# export GCP_REGION="europe-west1"
# bash infra/gcp/setup_project.sh

REQUIRED_ENV_VARS=(
  GCP_PROJECT_ID
  GCP_REGION
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

echo "Configuring gcloud project: ${GCP_PROJECT_ID}"
gcloud config set project "${GCP_PROJECT_ID}"

echo "Enabling required Google Cloud APIs"
gcloud services enable \
  run.googleapis.com \
  artifactregistry.googleapis.com \
  cloudbuild.googleapis.com \
  logging.googleapis.com \
  --project="${GCP_PROJECT_ID}"

echo "Project setup complete for region ${GCP_REGION}"
