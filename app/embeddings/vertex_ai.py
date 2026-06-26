"""Optional Vertex AI text embedding provider."""

from __future__ import annotations

import os
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from app.embeddings.base import EmbeddingProvider


DEFAULT_VERTEX_EMBEDDING_MODEL = "text-embedding-005"


@dataclass(frozen=True)
class VertexAIEmbeddingConfig:
    """Configuration required to call Vertex AI text embeddings."""

    project_id: str
    location: str
    model: str = DEFAULT_VERTEX_EMBEDDING_MODEL
    dimensions: int | None = None

    @classmethod
    def from_env(cls) -> VertexAIEmbeddingConfig:
        project_id = _env_optional("GCP_PROJECT_ID")
        location = _env_optional("VERTEX_AI_LOCATION") or _env_optional("GCP_LOCATION")
        model = _env_optional("VERTEX_EMBEDDING_MODEL")
        dimensions = _env_optional_int("VERTEX_EMBEDDING_DIMENSIONS")

        missing = []
        if not project_id:
            missing.append("GCP_PROJECT_ID")
        if not location:
            missing.append("GCP_LOCATION or VERTEX_AI_LOCATION")
        if not model:
            missing.append("VERTEX_EMBEDDING_MODEL")

        if missing:
            required = ", ".join(missing)
            raise ValueError(
                "Vertex AI embeddings require environment variables: "
                f"{required}. The provider is optional and is not used by the "
                "default local retrieval backend."
            )

        return cls(
            project_id=project_id,
            location=location,
            model=model,
            dimensions=dimensions,
        )


ClientFactory = Callable[[VertexAIEmbeddingConfig], Any]
EmbedConfigFactory = Callable[[int], Any]


class VertexAIEmbeddingProvider(EmbeddingProvider):
    """Vertex AI embedding provider backed by the official Google Gen AI SDK.

    The SDK import and client creation are lazy so importing the application and
    running the default local backend do not require Vertex AI credentials.
    """

    def __init__(
        self,
        config: VertexAIEmbeddingConfig | None = None,
        *,
        client: Any | None = None,
        client_factory: ClientFactory | None = None,
        embed_config_factory: EmbedConfigFactory | None = None,
    ) -> None:
        self.config = config or VertexAIEmbeddingConfig.from_env()
        self._client = client
        self._client_factory = client_factory or _default_client_factory
        self._embed_config_factory = (
            embed_config_factory or _default_embed_config_factory
        )

    def embed_text(self, text: str) -> list[float]:
        """Embed one non-empty text value."""

        return self.embed_texts([text])[0]

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Embed a batch of non-empty text values with one Vertex AI call."""

        if not texts:
            return []

        normalized_texts = [
            _validate_text(text, index) for index, text in enumerate(texts)
        ]
        request: dict[str, Any] = {
            "model": self.config.model,
            "contents": normalized_texts,
        }
        if self.config.dimensions is not None:
            request["config"] = self._embed_config_factory(self.config.dimensions)

        try:
            response = self._get_client().models.embed_content(**request)
        except Exception as exc:  # pragma: no cover - exercised with mock tests.
            raise RuntimeError("Vertex AI embedding request failed") from exc

        return _extract_embeddings(response, expected_count=len(normalized_texts))

    def _get_client(self) -> Any:
        if self._client is None:
            self._client = self._client_factory(self.config)
        return self._client


def _env_optional(name: str) -> str:
    value = os.getenv(name)
    if value is None:
        return ""
    return value.strip()


def _env_optional_int(name: str) -> int | None:
    value = _env_optional(name)
    if not value:
        return None
    try:
        parsed = int(value)
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer") from exc
    if parsed < 1:
        raise ValueError(f"{name} must be at least 1")
    return parsed


def _validate_text(text: str, index: int) -> str:
    if not isinstance(text, str):
        raise TypeError(f"text at index {index} must be a string")
    normalized = text.strip()
    if not normalized:
        raise ValueError(f"text at index {index} must not be empty")
    return normalized


def _default_client_factory(config: VertexAIEmbeddingConfig) -> Any:
    try:
        from google import genai
    except ImportError as exc:
        raise RuntimeError(
            "google-genai is required to use VertexAIEmbeddingProvider. "
            "Install it with `pip install google-genai`."
        ) from exc

    return genai.Client(
        vertexai=True,
        project=config.project_id,
        location=config.location,
    )


def _default_embed_config_factory(dimensions: int) -> Any:
    try:
        from google.genai import types
    except ImportError as exc:
        raise RuntimeError(
            "google-genai is required to configure Vertex embedding dimensions. "
            "Install it with `pip install google-genai`."
        ) from exc

    return types.EmbedContentConfig(output_dimensionality=dimensions)


def _extract_embeddings(response: Any, *, expected_count: int) -> list[list[float]]:
    response_embeddings = getattr(response, "embeddings", None)
    if response_embeddings is None and isinstance(response, dict):
        response_embeddings = response.get("embeddings")
    if response_embeddings is None:
        raise RuntimeError("Vertex AI embedding response did not include embeddings")

    embeddings = [_embedding_values(embedding) for embedding in response_embeddings]
    if len(embeddings) != expected_count:
        raise RuntimeError(
            "Vertex AI embedding response count did not match request count: "
            f"expected {expected_count}, received {len(embeddings)}"
        )
    return embeddings


def _embedding_values(embedding: Any) -> list[float]:
    values = getattr(embedding, "values", None)
    if values is None and isinstance(embedding, dict):
        values = embedding.get("values")
    if values is None:
        raise RuntimeError("Vertex AI embedding item did not include values")
    return [float(value) for value in values]
