from pathlib import Path


README = Path("README.md")
API_CONTRACT_DOC = Path("docs/api_contract.md")
DEMO_RESULTS_DOC = Path("docs/demo_results.md")
GCP_PLAN_DOC = Path("docs/gcp_production_extension_plan.md")
PERFORMANCE_DOC = Path("docs/performance_cost_notes.md")


def test_readme_presents_final_candidate_and_default_path() -> None:
    readme = README.read_text(encoding="utf-8")

    assert "Stage 10C / final candidate" in readme
    assert "`INTENT_BACKEND=rules`, `RETRIEVAL_BACKEND=keyword`" in readme
    assert "`INTENT_BACKEND=rules` with `RETRIEVAL_BACKEND=bigquery_vector`" in readme
    assert 'export INTENT_BACKEND="vertex_llm"' in readme
    assert "fall back to local keyword retrieval" in readme
    assert "It is not an autonomous LLM agent loop." in readme


def test_demo_results_include_verified_managed_gcp_validation() -> None:
    doc = DEMO_RESULTS_DOC.read_text(encoding="utf-8")

    assert "## Verified GCP Managed Demo" in doc
    assert "`GET /health` returned `200 OK`" in doc
    assert "`INTENT_BACKEND=rules` and `RETRIEVAL_BACKEND=bigquery_vector`" in doc
    assert "Five smoke-test `POST /assistant/query` calls returned `200 OK`" in doc
    assert "`RETRIEVAL_BACKEND=bigquery_vector`" in doc
    assert "`INTENT_BACKEND=vertex_llm`" in doc
    assert "BigQuery Vector Search with Vertex AI query embeddings" in doc


def test_gcp_plan_is_post_stage_8_and_9_hardening_doc() -> None:
    doc = GCP_PLAN_DOC.read_text(encoding="utf-8")

    assert "# GCP Production Hardening And Future Work" in doc
    assert "Stage 8 and Stage 9 are no longer only a plan." in doc
    assert "Manual GCP validation has confirmed Cloud Run deployment" in doc
    assert "Stage 8 remains a plan only" not in doc
    assert "Target Stage 8 Architecture" not in doc


def test_performance_notes_distinguish_cost_modes_and_load_test_status() -> None:
    doc = PERFORMANCE_DOC.read_text(encoding="utf-8")

    assert "| Default local | `rules` | `keyword` |" in doc
    assert "| Managed retrieval | `rules` | `bigquery_vector` |" in doc
    assert "| Optional LLM intent + managed retrieval | `vertex_llm` |" in doc
    assert "## Load Test Results" in doc
    assert "No formal production load-test result is committed" in doc


def test_api_contract_allows_optional_vertex_llm_without_schema_change() -> None:
    doc = API_CONTRACT_DOC.read_text(encoding="utf-8")

    assert "optional Stage 9B configuration can use Vertex/Gemini" in doc
    assert "The public response schema remains the same." in doc
    assert "Does not use an autonomous LLM loop" in doc
