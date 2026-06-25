"""Environment-based application configuration."""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache


def _env_str(name: str, default: str) -> str:
    raw_value = os.getenv(name)
    if raw_value is None or not raw_value.strip():
        return default
    return raw_value.strip()


def _env_int(name: str, default: int) -> int:
    raw_value = os.getenv(name)
    if raw_value is None or not raw_value.strip():
        return default
    try:
        return int(raw_value)
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer") from exc


def _env_choice(name: str, default: str, allowed_values: set[str]) -> str:
    value = _env_str(name, default).lower()
    if value not in allowed_values:
        allowed = ", ".join(sorted(allowed_values))
        raise ValueError(f"{name} must be one of: {allowed}")
    return value


SUPPORTED_INTENT_BACKENDS = {"llm_placeholder", "rules", "vertex_placeholder"}
SUPPORTED_RETRIEVAL_BACKENDS = {"bigquery_vector", "hybrid", "keyword"}


@dataclass(frozen=True)
class Settings:
    APP_NAME: str = "PAYBACK Lightweight Assistant"
    APP_VERSION: str = "0.6.0"
    ENVIRONMENT: str = "local"
    HOST: str = "0.0.0.0"
    PORT: int = 8080
    LOG_LEVEL: str = "info"
    CATALOG_PATH: str = "app/data/products.json"
    INTENT_BACKEND: str = "rules"
    RETRIEVAL_BACKEND: str = "keyword"
    DEFAULT_TOP_K: int = 5
    MAX_TOP_K: int = 20

    @classmethod
    def from_env(cls) -> Settings:
        return cls(
            APP_NAME=_env_str("APP_NAME", cls.APP_NAME),
            APP_VERSION=_env_str("APP_VERSION", cls.APP_VERSION),
            ENVIRONMENT=_env_str("ENVIRONMENT", cls.ENVIRONMENT),
            HOST=_env_str("HOST", cls.HOST),
            PORT=_env_int("PORT", cls.PORT),
            LOG_LEVEL=_env_str("LOG_LEVEL", cls.LOG_LEVEL),
            CATALOG_PATH=_env_str("CATALOG_PATH", cls.CATALOG_PATH),
            INTENT_BACKEND=_env_choice(
                "INTENT_BACKEND",
                cls.INTENT_BACKEND,
                SUPPORTED_INTENT_BACKENDS,
            ),
            RETRIEVAL_BACKEND=_env_choice(
                "RETRIEVAL_BACKEND",
                cls.RETRIEVAL_BACKEND,
                SUPPORTED_RETRIEVAL_BACKENDS,
            ),
            DEFAULT_TOP_K=_env_int("DEFAULT_TOP_K", cls.DEFAULT_TOP_K),
            MAX_TOP_K=_env_int("MAX_TOP_K", cls.MAX_TOP_K),
        )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings.from_env()
