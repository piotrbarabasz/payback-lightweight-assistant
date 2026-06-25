import pytest

from app.config import get_settings


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


def test_intent_backend_accepts_vertex_placeholder(monkeypatch) -> None:
    clear_config_env(monkeypatch)
    monkeypatch.setenv("INTENT_BACKEND", "vertex_placeholder")
    get_settings.cache_clear()

    assert get_settings().INTENT_BACKEND == "vertex_placeholder"


def test_intent_backend_accepts_llm_placeholder(monkeypatch) -> None:
    clear_config_env(monkeypatch)
    monkeypatch.setenv("INTENT_BACKEND", "llm_placeholder")
    get_settings.cache_clear()

    assert get_settings().INTENT_BACKEND == "llm_placeholder"


def test_intent_backend_rejects_unknown_value(monkeypatch) -> None:
    clear_config_env(monkeypatch)
    monkeypatch.setenv("INTENT_BACKEND", "external_llm")
    get_settings.cache_clear()

    with pytest.raises(
        ValueError,
        match=(
            "INTENT_BACKEND must be one of: "
            "llm_placeholder, rules, vertex_placeholder"
        ),
    ):
        get_settings()


def test_retrieval_backend_accepts_hybrid(monkeypatch) -> None:
    clear_config_env(monkeypatch)
    monkeypatch.setenv("RETRIEVAL_BACKEND", "hybrid")
    get_settings.cache_clear()

    assert get_settings().RETRIEVAL_BACKEND == "hybrid"


def test_retrieval_backend_accepts_bigquery_vector_placeholder(monkeypatch) -> None:
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
