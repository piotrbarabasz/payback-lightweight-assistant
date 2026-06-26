#!/usr/bin/env bash
set -euo pipefail

# Optional Stage 8D service account setup for Cloud Run managed retrieval.
#
# This script creates or reuses a runtime service account and grants the minimum
# project-level roles needed to call Vertex AI and run BigQuery jobs. BigQuery
# table read access should be granted at the narrowest practical scope. If
# BIGQUERY_DATASET is provided and the `bq` CLI is available, this script tries
# a BigQuery SQL GRANT on that dataset. Set ALLOW_PROJECT_BIGQUERY_DATA_VIEWER=true
# only when you accept a project-level roles/bigquery.dataViewer fallback.

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

grant_project_bigquery_data_viewer() {
  echo "Granting project-level BigQuery read role"
  gcloud projects add-iam-policy-binding "${GCP_PROJECT_ID}" \
    --member="${SERVICE_ACCOUNT_MEMBER}" \
    --role="roles/bigquery.dataViewer" \
    --condition=None \
    --quiet
}

if [[ -n "${BIGQUERY_DATASET:-}" ]] && command -v bq >/dev/null 2>&1; then
  echo "Granting dataset-level BigQuery read role on ${GCP_PROJECT_ID}:${BIGQUERY_DATASET}"
  BQ_QUERY_ARGS=(
    "--project_id=${GCP_PROJECT_ID}"
    "--use_legacy_sql=false"
    "--quiet"
  )
  if [[ -n "${BIGQUERY_LOCATION:-}" ]]; then
    BQ_QUERY_ARGS+=("--location=${BIGQUERY_LOCATION}")
  fi
  GRANT_SQL="GRANT \`roles/bigquery.dataViewer\` ON SCHEMA \`${GCP_PROJECT_ID}.${BIGQUERY_DATASET}\` TO \"${SERVICE_ACCOUNT_MEMBER}\";"
  if bq query "${BQ_QUERY_ARGS[@]}" "${GRANT_SQL}"; then
    echo "Granted dataset-level BigQuery read role"
  else
    echo "Dataset-level BigQuery SQL GRANT failed; continuing without failing the script." >&2
    echo "If project-level read access is acceptable, rerun with ALLOW_PROJECT_BIGQUERY_DATA_VIEWER=true." >&2
    if [[ "${ALLOW_PROJECT_BIGQUERY_DATA_VIEWER:-false}" == "true" ]]; then
      grant_project_bigquery_data_viewer
    fi
  fi
else
  echo "BIGQUERY_DATASET or bq CLI is unavailable; dataset-level read grant was not attempted." >&2
  echo "For least privilege, prefer dataset-level roles/bigquery.dataViewer when possible." >&2
  if [[ "${ALLOW_PROJECT_BIGQUERY_DATA_VIEWER:-false}" == "true" ]]; then
    grant_project_bigquery_data_viewer
  else
    echo "Set ALLOW_PROJECT_BIGQUERY_DATA_VIEWER=true to grant project-level roles/bigquery.dataViewer." >&2
  fi
fi

echo "Cloud Run service account setup complete"
echo "Set this before deploy:"
echo "export CLOUD_RUN_SERVICE_ACCOUNT=\"${CLOUD_RUN_SERVICE_ACCOUNT}\""
