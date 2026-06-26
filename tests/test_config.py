import pytest

from app.config import (
    SUPPORTED_INTENT_BACKENDS,
    SUPPORTED_RETRIEVAL_BACKENDS,
    get_settings,
)


CONFIG_ENV_VARS = (
    "APP_NAME",
    "APP_VERSION",
    "ENVIRONMENT",
    "HOST",
    "PORT",
    "LOG_LEVEL",
    "CATALOG_PATH",
    "INTENT_BACKEND",
    "RETRIEVAL_BACKEND",
    "DEFAULT_TOP_K",
    "MAX_TOP_K",
    "GCP_PROJECT_ID",
    "GCP_LOCATION",
    "GCP_REGION",
    "BIGQUERY_DATASET",
    "BIGQUERY_PRODUCTS_TABLE",
    "BIGQUERY_LOCATION",
    "BIGQUERY_VECTOR_TOP_K",
    "VERTEX_AI_LOCATION",
    "VERTEX_EMBEDDING_MODEL",
    "VERTEX_EMBEDDING_DIMENSIONS",
    "VERTEX_INTENT_MODEL",
    "INTENT_LLM_TIMEOUT_SECONDS",
)


def clear_config_env(monkeypatch) -> None:
    for name in CONFIG_ENV_VARS:
        monkeypatch.delenv(name, raising=False)
    get_settings.cache_clear()


def test_default_settings_load_correctly(monkeypatch) -> None:
    clear_config_env(monkeypatch)

    settings = get_settings()

    assert settings.APP_NAME == "PAYBACK Lightweight Assistant"
    assert settings.APP_VERSION == "0.6.0"
    assert settings.ENVIRONMENT == "local"
    assert settings.HOST == "0.0.0.0"
    assert settings.PORT == 8080
    assert settings.LOG_LEVEL == "info"
    assert settings.CATALOG_PATH == "app/data/products.json"
    assert settings.INTENT_BACKEND == "rules"
    assert settings.RETRIEVAL_BACKEND == "keyword"
    assert settings.DEFAULT_TOP_K == 5
    assert settings.MAX_TOP_K == 20
    assert settings.GCP_PROJECT_ID == ""
    assert settings.GCP_LOCATION == "europe-west1"
    assert settings.GCP_REGION == "europe-west1"
    assert settings.BIGQUERY_DATASET == "payback_catalog"
    assert settings.BIGQUERY_PRODUCTS_TABLE == "products"
    assert settings.BIGQUERY_LOCATION == "europe-west1"
    assert settings.BIGQUERY_VECTOR_TOP_K == 25
    assert settings.VERTEX_AI_LOCATION == ""
    assert settings.VERTEX_EMBEDDING_MODEL == ""
    assert settings.VERTEX_EMBEDDING_DIMENSIONS == 0
    assert settings.VERTEX_INTENT_MODEL == "gemini-3.5-flash"
    assert settings.INTENT_LLM_TIMEOUT_SECONDS == 3.0


def test_app_name_has_non_empty_value(monkeypatch) -> None:
    clear_config_env(monkeypatch)

    assert get_settings().APP_NAME.strip()


def test_port_defaults_to_8080(monkeypatch) -> None:
    clear_config_env(monkeypatch)

    assert get_settings().PORT == 8080


def test_default_top_k_is_between_one_and_max_top_k(monkeypatch) -> None:
    clear_config_env(monkeypatch)

    settings = get_settings()

    assert 1 <= settings.DEFAULT_TOP_K <= settings.MAX_TOP_K


def test_catalog_path_is_set(monkeypatch) -> None:
    clear_config_env(monkeypatch)

    assert get_settings().CATALOG_PATH.strip()


def test_retrieval_backend_defaults_to_keyword(monkeypatch) -> None:
    clear_config_env(monkeypatch)

    assert get_settings().RETRIEVAL_BACKEND == "keyword"


def test_intent_backend_defaults_to_rules(monkeypatch) -> None:
    clear_config_env(monkeypatch)

    assert get_settings().INTENT_BACKEND == "rules"


def test_supported_intent_backends_include_rules_and_optional_vertex_llm() -> None:
    assert SUPPORTED_INTENT_BACKENDS == {
        "rules",
        "vertex_llm",
    }


def test_intent_backend_accepts_vertex_llm(monkeypatch) -> None:
    clear_config_env(monkeypatch)
    monkeypatch.setenv("INTENT_BACKEND", "vertex_llm")
    get_settings.cache_clear()

    assert get_settings().INTENT_BACKEND == "vertex_llm"


def test_intent_backend_rejects_unknown_value(monkeypatch) -> None:
    clear_config_env(monkeypatch)
    monkeypatch.setenv("INTENT_BACKEND", "external_intent")
    get_settings.cache_clear()

    with pytest.raises(
        ValueError,
        match="INTENT_BACKEND must be one of: rules, vertex_llm",
    ):
        get_settings()


def test_retrieval_backend_accepts_hybrid(monkeypatch) -> None:
    clear_config_env(monkeypatch)
    monkeypatch.setenv("RETRIEVAL_BACKEND", "hybrid")
    get_settings.cache_clear()

    assert get_settings().RETRIEVAL_BACKEND == "hybrid"


def test_supported_retrieval_backends_include_local_and_optional_managed() -> None:
    assert SUPPORTED_RETRIEVAL_BACKENDS == {
        "bigquery_vector",
        "hybrid",
        "keyword",
    }


def test_retrieval_backend_accepts_bigquery_vector(monkeypatch) -> None:
    clear_config_env(monkeypatch)
    monkeypatch.setenv("RETRIEVAL_BACKEND", "bigquery_vector")
    get_settings.cache_clear()

    assert get_settings().RETRIEVAL_BACKEND == "bigquery_vector"


def test_retrieval_backend_rejects_unknown_value(monkeypatch) -> None:
    clear_config_env(monkeypatch)
    monkeypatch.setenv("RETRIEVAL_BACKEND", "semantic")
    get_settings.cache_clear()

    with pytest.raises(
        ValueError,
        match="RETRIEVAL_BACKEND must be one of: bigquery_vector, hybrid, keyword",
    ):
        get_settings()


def test_environment_variables_override_port_and_environment(monkeypatch) -> None:
    clear_config_env(monkeypatch)
    monkeypatch.setenv("PORT", "9090")
    monkeypatch.setenv("ENVIRONMENT", "test-docker")
    get_settings.cache_clear()

    settings = get_settings()

    assert settings.PORT == 9090
    assert settings.ENVIRONMENT == "test-docker"


def test_gcp_catalog_environment_variables_override_defaults(monkeypatch) -> None:
    clear_config_env(monkeypatch)
    monkeypatch.setenv("GCP_PROJECT_ID", "payback-prod")
    monkeypatch.setenv("GCP_LOCATION", "europe-west3")
    monkeypatch.setenv("GCP_REGION", "europe-west3")
    monkeypatch.setenv("BIGQUERY_DATASET", "catalog_prod")
    monkeypatch.setenv("BIGQUERY_PRODUCTS_TABLE", "product_catalog")
    monkeypatch.setenv("BIGQUERY_LOCATION", "EU")
    monkeypatch.setenv("BIGQUERY_VECTOR_TOP_K", "50")
    monkeypatch.setenv("VERTEX_AI_LOCATION", "us-central1")
    monkeypatch.setenv("VERTEX_EMBEDDING_MODEL", "text-embedding-005")
    monkeypatch.setenv("VERTEX_EMBEDDING_DIMENSIONS", "256")
    monkeypatch.setenv("VERTEX_INTENT_MODEL", "gemini-test")
    monkeypatch.setenv("INTENT_LLM_TIMEOUT_SECONDS", "4.5")
    get_settings.cache_clear()

    settings = get_settings()

    assert settings.GCP_PROJECT_ID == "payback-prod"
    assert settings.GCP_LOCATION == "europe-west3"
    assert settings.GCP_REGION == "europe-west3"
    assert settings.BIGQUERY_DATASET == "catalog_prod"
    assert settings.BIGQUERY_PRODUCTS_TABLE == "product_catalog"
    assert settings.BIGQUERY_LOCATION == "EU"
    assert settings.BIGQUERY_VECTOR_TOP_K == 50
    assert settings.VERTEX_AI_LOCATION == "us-central1"
    assert settings.VERTEX_EMBEDDING_MODEL == "text-embedding-005"
    assert settings.VERTEX_EMBEDDING_DIMENSIONS == 256
    assert settings.VERTEX_INTENT_MODEL == "gemini-test"
    assert settings.INTENT_LLM_TIMEOUT_SECONDS == 4.5


def test_blank_gcp_catalog_environment_variables_use_safe_defaults(monkeypatch) -> None:
    clear_config_env(monkeypatch)
    monkeypatch.setenv("GCP_PROJECT_ID", "   ")
    monkeypatch.setenv("GCP_LOCATION", "   ")
    monkeypatch.setenv("GCP_REGION", "   ")
    monkeypatch.setenv("BIGQUERY_DATASET", "   ")
    monkeypatch.setenv("BIGQUERY_PRODUCTS_TABLE", "   ")
    monkeypatch.setenv("BIGQUERY_LOCATION", "   ")
    monkeypatch.setenv("BIGQUERY_VECTOR_TOP_K", "   ")
    monkeypatch.setenv("VERTEX_AI_LOCATION", "   ")
    monkeypatch.setenv("VERTEX_EMBEDDING_MODEL", "   ")
    monkeypatch.setenv("VERTEX_EMBEDDING_DIMENSIONS", "   ")
    monkeypatch.setenv("VERTEX_INTENT_MODEL", "   ")
    monkeypatch.setenv("INTENT_LLM_TIMEOUT_SECONDS", "   ")
    get_settings.cache_clear()

    settings = get_settings()

    assert settings.GCP_PROJECT_ID == ""
    assert settings.GCP_LOCATION == "europe-west1"
    assert settings.GCP_REGION == "europe-west1"
    assert settings.BIGQUERY_DATASET == "payback_catalog"
    assert settings.BIGQUERY_PRODUCTS_TABLE == "products"
    assert settings.BIGQUERY_LOCATION == "europe-west1"
    assert settings.BIGQUERY_VECTOR_TOP_K == 25
    assert settings.VERTEX_AI_LOCATION == ""
    assert settings.VERTEX_EMBEDDING_MODEL == ""
    assert settings.VERTEX_EMBEDDING_DIMENSIONS == 0
    assert settings.VERTEX_INTENT_MODEL == "gemini-3.5-flash"
    assert settings.INTENT_LLM_TIMEOUT_SECONDS == 3.0


def test_invalid_vector_top_k_is_rejected(monkeypatch) -> None:
    clear_config_env(monkeypatch)
    monkeypatch.setenv("BIGQUERY_VECTOR_TOP_K", "many")
    get_settings.cache_clear()

    with pytest.raises(ValueError, match="BIGQUERY_VECTOR_TOP_K must be an integer"):
        get_settings()


def test_invalid_intent_llm_timeout_is_rejected(monkeypatch) -> None:
    clear_config_env(monkeypatch)
    monkeypatch.setenv("INTENT_LLM_TIMEOUT_SECONDS", "soon")
    get_settings.cache_clear()

    with pytest.raises(
        ValueError,
        match="INTENT_LLM_TIMEOUT_SECONDS must be a number",
    ):
        get_settings()


def test_non_positive_intent_llm_timeout_is_rejected(monkeypatch) -> None:
    clear_config_env(monkeypatch)
    monkeypatch.setenv("INTENT_LLM_TIMEOUT_SECONDS", "0")
    get_settings.cache_clear()

    with pytest.raises(
        ValueError,
        match="INTENT_LLM_TIMEOUT_SECONDS must be greater than 0",
    ):
        get_settings()
