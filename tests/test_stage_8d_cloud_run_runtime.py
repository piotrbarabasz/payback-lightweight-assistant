from pathlib import Path


DEPLOY_SCRIPT = Path("infra/gcp/deploy_cloud_run.sh")
SETUP_PROJECT_SCRIPT = Path("infra/gcp/setup_project.sh")
SETUP_SA_SCRIPT = Path("infra/gcp/setup_cloud_run_service_account.sh")
STAGE_8D_DOC = Path("docs/stage_8d_cloud_run_gcp_runtime.md")


def test_setup_project_enables_bigquery_vertex_and_iam_apis() -> None:
    script = SETUP_PROJECT_SCRIPT.read_text(encoding="utf-8")

    assert "bigquery.googleapis.com" in script
    assert "aiplatform.googleapis.com" in script
    assert "iam.googleapis.com" in script


def test_service_account_script_grants_expected_runtime_roles() -> None:
    script = SETUP_SA_SCRIPT.read_text(encoding="utf-8")

    assert "gcloud iam service-accounts create" in script
    assert "roles/bigquery.jobUser" in script
    assert "roles/bigquery.dataViewer" in script
    assert "roles/aiplatform.user" in script
    assert "CLOUD_RUN_SERVICE_ACCOUNT" in script
    assert "BIGQUERY_DATASET" in script
    assert "GRANT \\`roles/bigquery.dataViewer\\` ON SCHEMA" in script
    assert "ALLOW_PROJECT_BIGQUERY_DATA_VIEWER" in script
    assert "bq add-iam-policy-binding" not in script
    assert "continuing without failing the script" in script


def test_deploy_script_keeps_keyword_default_and_supports_bigquery_vector() -> None:
    script = DEPLOY_SCRIPT.read_text(encoding="utf-8")

    assert 'RETRIEVAL_BACKEND="${RETRIEVAL_BACKEND:-keyword}"' in script
    assert 'RETRIEVAL_BACKEND=${RETRIEVAL_BACKEND}' in script
    assert 'if [[ "${RETRIEVAL_BACKEND}" == "bigquery_vector" ]]' in script
    assert '"GCP_PROJECT_ID=${GCP_PROJECT_ID}"' in script
    assert '"GCP_REGION=${GCP_REGION}"' in script
    assert "CLOUD_RUN_SERVICE_ACCOUNT" in script
    assert "GCP_LOCATION" in script
    assert "BIGQUERY_DATASET" in script
    assert "BIGQUERY_PRODUCTS_TABLE" in script
    assert "BIGQUERY_LOCATION" in script
    assert "BIGQUERY_VECTOR_TOP_K" in script
    assert "VERTEX_AI_LOCATION" in script
    assert "VERTEX_EMBEDDING_MODEL" in script
    assert "DEFAULT_TOP_K" in script
    assert "MAX_TOP_K" in script
    assert "--service-account" in script


def test_stage_8d_docs_include_required_operational_commands() -> None:
    doc = STAGE_8D_DOC.read_text(encoding="utf-8")

    assert "bash infra/gcp/setup_cloud_run_service_account.sh" in doc
    assert 'export RETRIEVAL_BACKEND="keyword"' in doc
    assert 'export RETRIEVAL_BACKEND="bigquery_vector"' in doc
    assert "gcloud run services update" in doc
    assert "gcloud run services logs tail" in doc
    assert "gcloud logging read" in doc
    assert "Frontend -> Cloud Run HTTPS API -> BigQuery / Vertex AI" in doc
    assert "Billing must be enabled" in doc
    assert "ALLOW_PROJECT_BIGQUERY_DATA_VIEWER" in doc
    assert "Manual validation evidence" in doc
