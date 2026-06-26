#!/usr/bin/env bash
set -euo pipefail

# Optional Stage 8D service account setup for Cloud Run managed retrieval.
#
# This script creates or reuses a runtime service account and grants the minimum
# project-level roles needed to call Vertex AI and run BigQuery jobs. BigQuery
# table read access should be granted at the narrowest practical scope. If
# BIGQUERY_DATASET is provided and the `bq` CLI is available, this script grants
# dataset-level roles/bigquery.dataViewer. Otherwise it falls back to a
# project-level grant and prints a warning.

REQUIRED_ENV_VARS=(
  GCP_PROJECT_ID
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

CLOUD_RUN_SERVICE_ACCOUNT_NAME="${CLOUD_RUN_SERVICE_ACCOUNT_NAME:-payback-assistant-runtime}"
CLOUD_RUN_SERVICE_ACCOUNT="${CLOUD_RUN_SERVICE_ACCOUNT:-${CLOUD_RUN_SERVICE_ACCOUNT_NAME}@${GCP_PROJECT_ID}.iam.gserviceaccount.com}"
SERVICE_ACCOUNT_MEMBER="serviceAccount:${CLOUD_RUN_SERVICE_ACCOUNT}"

echo "Configuring Cloud Run runtime service account"
echo "Project: ${GCP_PROJECT_ID}"
echo "Service account: ${CLOUD_RUN_SERVICE_ACCOUNT}"

if gcloud iam service-accounts describe "${CLOUD_RUN_SERVICE_ACCOUNT}" \
  --project="${GCP_PROJECT_ID}" >/dev/null 2>&1; then
  echo "Service account already exists"
else
  echo "Creating service account: ${CLOUD_RUN_SERVICE_ACCOUNT_NAME}"
  gcloud iam service-accounts create "${CLOUD_RUN_SERVICE_ACCOUNT_NAME}" \
    --display-name="PAYBACK Assistant Cloud Run runtime" \
    --project="${GCP_PROJECT_ID}"
fi

echo "Granting BigQuery job execution role"
gcloud projects add-iam-policy-binding "${GCP_PROJECT_ID}" \
  --member="${SERVICE_ACCOUNT_MEMBER}" \
  --role="roles/bigquery.jobUser" \
  --condition=None \
  --quiet

echo "Granting Vertex AI user role"
gcloud projects add-iam-policy-binding "${GCP_PROJECT_ID}" \
  --member="${SERVICE_ACCOUNT_MEMBER}" \
  --role="roles/aiplatform.user" \
  --condition=None \
  --quiet

if [[ -n "${BIGQUERY_DATASET:-}" ]] && command -v bq >/dev/null 2>&1; then
  echo "Granting dataset-level BigQuery read role on ${GCP_PROJECT_ID}:${BIGQUERY_DATASET}"
  bq add-iam-policy-binding \
    --member="${SERVICE_ACCOUNT_MEMBER}" \
    --role="roles/bigquery.dataViewer" \
    "${GCP_PROJECT_ID}:${BIGQUERY_DATASET}"
else
  echo "BIGQUERY_DATASET or bq CLI is unavailable; granting project-level BigQuery read role." >&2
  echo "For least privilege, prefer dataset-level roles/bigquery.dataViewer when possible." >&2
  gcloud projects add-iam-policy-binding "${GCP_PROJECT_ID}" \
    --member="${SERVICE_ACCOUNT_MEMBER}" \
    --role="roles/bigquery.dataViewer" \
    --condition=None \
    --quiet
fi

echo "Cloud Run service account setup complete"
echo "Set this before deploy:"
echo "export CLOUD_RUN_SERVICE_ACCOUNT=\"${CLOUD_RUN_SERVICE_ACCOUNT}\""
