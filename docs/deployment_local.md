# Local Deployment

## 1. Purpose

Stage 5 prepares the FastAPI application for containerized deployment and Cloud Run-compatible runtime behavior. This stage focuses on local runtime readiness, Docker packaging, health checks, and smoke testing.

## 2. Run Locally Without Docker

Unix/macOS:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app/data/generate_synthetic_catalog.py
uvicorn app.main:app --reload
```

The command above uses Uvicorn's default port `8000`. To run on the same port
used by the Docker and smoke-test defaults:

```bash
uvicorn app.main:app --host 127.0.0.1 --port 8080 --reload
```

Windows PowerShell activation:

```powershell
.\.venv\Scripts\Activate.ps1
```

## 3. Run With Docker

```bash
docker build -t payback-lightweight-assistant .
docker run --rm -p 8080:8080 -e PORT=8080 payback-lightweight-assistant
```

## 4. Run With Docker Compose

```bash
docker compose up --build
```

## 5. Smoke Test

Run this after the API is available on `http://localhost:8080`:

```bash
python scripts/smoke_test_api.py
```

If the API is running on `http://127.0.0.1:8000`, pass that base URL:

```bash
API_BASE_URL=http://127.0.0.1:8000 python scripts/smoke_test_api.py
```

## 6. Health Check

```text
GET http://localhost:8080/health
```

## 7. Main Endpoint

```text
POST http://localhost:8080/assistant/query
```

## 8. Cloud Run Compatibility

- Cloud Run will provide the `PORT` environment variable.
- The container already listens on `0.0.0.0` and uses a configurable `PORT`.
- GCP deployment scripts are documented in [deployment_gcp_cloud_run.md](deployment_gcp_cloud_run.md).
