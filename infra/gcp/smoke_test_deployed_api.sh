#!/usr/bin/env bash
set -euo pipefail

if ! command -v curl >/dev/null 2>&1; then
  echo "Missing required command: curl" >&2
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
CLOUD_RUN_URL_FILE="${REPO_ROOT}/.cloud_run_url"

if [[ -n "${CLOUD_RUN_URL:-}" ]]; then
  API_BASE_URL="${CLOUD_RUN_URL}"
  echo "Using CLOUD_RUN_URL from environment"
elif [[ -f "${CLOUD_RUN_URL_FILE}" ]]; then
  API_BASE_URL="$(tr -d '[:space:]' < "${CLOUD_RUN_URL_FILE}")"
  echo "Using Cloud Run URL from ${CLOUD_RUN_URL_FILE}"
else
  echo "Missing Cloud Run URL. Set CLOUD_RUN_URL or run infra/gcp/deploy_cloud_run.sh to create .cloud_run_url." >&2
  exit 1
fi

API_BASE_URL="${API_BASE_URL%/}"

if [[ -z "${API_BASE_URL}" ]]; then
  echo "Cloud Run URL is empty" >&2
  exit 1
fi

request() {
  local method="$1"
  local path="$2"
  local payload="${3:-}"
  local response_file
  local status_code

  response_file="$(mktemp)"
  if [[ -n "${payload}" ]]; then
    status_code="$(curl -sS -o "${response_file}" -w "%{http_code}" \
      -X "${method}" \
      -H "Content-Type: application/json" \
      -H "Accept: application/json" \
      -d "${payload}" \
      "${API_BASE_URL}${path}")"
  else
    status_code="$(curl -sS -o "${response_file}" -w "%{http_code}" \
      -X "${method}" \
      -H "Accept: application/json" \
      "${API_BASE_URL}${path}")"
  fi

  echo
  echo "${method} ${path}"
  echo "HTTP status: ${status_code}"
  echo "Response body:"
  cat "${response_file}"
  echo

  rm -f "${response_file}"
  LAST_STATUS_CODE="${status_code}"
}

echo "Running deployed API smoke test against: ${API_BASE_URL}"

request "GET" "/health"
if [[ "${LAST_STATUS_CODE}" != "200" ]]; then
  echo "Health check failed: expected HTTP 200, got ${LAST_STATUS_CODE}" >&2
  exit 1
fi

request "POST" "/assistant/query" '{"query":"Bitte zeige mir Angebote für günstige Windeln","top_k":5}'
request "POST" "/assistant/query" '{"query":"I need stuff for a pasta dinner","top_k":5}'
request "POST" "/assistant/query" '{"query":"Show me headphones on Amazon","top_k":5}'
request "POST" "/assistant/query" '{"query":"Meine PAYBACK Punkte fehlen","top_k":5}'
request "POST" "/assistant/query" '{"query":"Something nice","top_k":5}'

echo "Deployed API smoke test passed"
