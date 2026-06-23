#!/usr/bin/env bash
set -euo pipefail

REQUIRED_ENV_VARS=(
  GCP_PROJECT_ID
  GCP_REGION
  ARTIFACT_REPOSITORY
  IMAGE_NAME
)

for var_name in "${REQUIRED_ENV_VARS[@]}"; do
  if [[ -z "${!var_name:-}" ]]; then
    echo "Missing required environment variable: ${var_name}" >&2
    exit 1
  fi
done

if ! command -v docker >/dev/null 2>&1; then
  echo "Missing required command: docker" >&2
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
IMAGE_TAG="${IMAGE_TAG:-latest}"
IMAGE_URI="${GCP_REGION}-docker.pkg.dev/${GCP_PROJECT_ID}/${ARTIFACT_REPOSITORY}/${IMAGE_NAME}:${IMAGE_TAG}"
IMAGE_URI_FILE="${REPO_ROOT}/.gcp_image_uri"

echo "Building local Docker image"
echo "Image URI: ${IMAGE_URI}"

cd "${REPO_ROOT}"
docker build -t "${IMAGE_URI}" .

echo "Pushing Docker image to Artifact Registry"
docker push "${IMAGE_URI}"

echo "${IMAGE_URI}" > "${IMAGE_URI_FILE}"

echo "Image build and push complete"
echo "Saved image URI to ${IMAGE_URI_FILE}"
echo "${IMAGE_URI}"
