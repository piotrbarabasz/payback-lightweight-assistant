from __future__ import annotations

from dataclasses import dataclass

import pytest

from app.embeddings.vertex_ai import (
    VertexAIEmbeddingConfig,
    VertexAIEmbeddingProvider,
)


@dataclass
class FakeEmbedding:
    values: list[float]


@dataclass
class FakeResponse:
    embeddings: list[FakeEmbedding]


class FakeModels:
    def __init__(self, response: FakeResponse | None = None) -> None:
        self.response = response or FakeResponse(
            embeddings=[
                FakeEmbedding([0.1, 0.2]),
                FakeEmbedding([0.3, 0.4]),
            ]
        )
        self.calls: list[dict[str, object]] = []

    def embed_content(self, **kwargs: object) -> FakeResponse:
        self.calls.append(kwargs)
        return self.response


class FakeClient:
    def __init__(self, models: FakeModels | None = None) -> None:
        self.models = models or FakeModels()


def test_vertex_embedding_config_requires_project_location_and_model(
    monkeypatch,
) -> None:
    monkeypatch.delenv("GCP_PROJECT_ID", raising=False)
    monkeypatch.delenv("GCP_LOCATION", raising=False)
    monkeypatch.delenv("VERTEX_AI_LOCATION", raising=False)
    monkeypatch.delenv("VERTEX_EMBEDDING_MODEL", raising=False)
    monkeypatch.delenv("VERTEX_EMBEDDING_DIMENSIONS", raising=False)

    with pytest.raises(
        ValueError,
        match=(
            "GCP_PROJECT_ID, GCP_LOCATION or VERTEX_AI_LOCATION, "
            "VERTEX_EMBEDDING_MODEL"
        ),
    ):
        VertexAIEmbeddingConfig.from_env()


def test_vertex_embedding_config_reads_env_and_prefers_vertex_location(
    monkeypatch,
) -> None:
    monkeypatch.setenv("GCP_PROJECT_ID", "payback-test")
    monkeypatch.setenv("GCP_LOCATION", "europe-west1")
    monkeypatch.setenv("VERTEX_AI_LOCATION", "us-central1")
    monkeypatch.setenv("VERTEX_EMBEDDING_MODEL", "text-embedding-005")
    monkeypatch.setenv("VERTEX_EMBEDDING_DIMENSIONS", "128")

    config = VertexAIEmbeddingConfig.from_env()

    assert config.project_id == "payback-test"
    assert config.location == "us-central1"
    assert config.model == "text-embedding-005"
    assert config.dimensions == 128


def test_vertex_embedding_config_rejects_invalid_dimensions(monkeypatch) -> None:
    monkeypatch.setenv("GCP_PROJECT_ID", "payback-test")
    monkeypatch.setenv("GCP_LOCATION", "europe-west1")
    monkeypatch.setenv("VERTEX_EMBEDDING_MODEL", "text-embedding-005")
    monkeypatch.setenv("VERTEX_EMBEDDING_DIMENSIONS", "0")

    with pytest.raises(
        ValueError,
        match="VERTEX_EMBEDDING_DIMENSIONS must be at least 1",
    ):
        VertexAIEmbeddingConfig.from_env()


def test_embed_text_rejects_empty_text_without_calling_vertex() -> None:
    client = FakeClient()
    provider = VertexAIEmbeddingProvider(
        VertexAIEmbeddingConfig(
            project_id="payback-test",
            location="europe-west1",
            model="text-embedding-005",
        ),
        client=client,
    )

    with pytest.raises(ValueError, match="text at index 0 must not be empty"):
        provider.embed_text("   ")

    assert client.models.calls == []


def test_embed_texts_returns_empty_batch_without_calling_vertex() -> None:
    client = FakeClient()
    provider = VertexAIEmbeddingProvider(
        VertexAIEmbeddingConfig(
            project_id="payback-test",
            location="europe-west1",
            model="text-embedding-005",
        ),
        client=client,
    )

    assert provider.embed_texts([]) == []
    assert client.models.calls == []


def test_embed_texts_calls_vertex_once_for_batch() -> None:
    client = FakeClient()
    config = VertexAIEmbeddingConfig(
        project_id="payback-test",
        location="europe-west1",
        model="text-embedding-005",
    )
    provider = VertexAIEmbeddingProvider(config, client=client)

    embeddings = provider.embed_texts([" diapers ", "coffee beans"])

    assert embeddings == [[0.1, 0.2], [0.3, 0.4]]
    assert client.models.calls == [
        {
            "model": "text-embedding-005",
            "contents": ["diapers", "coffee beans"],
        }
    ]


def test_embed_texts_passes_output_dimensions_when_configured() -> None:
    client = FakeClient()
    provider = VertexAIEmbeddingProvider(
        VertexAIEmbeddingConfig(
            project_id="payback-test",
            location="europe-west1",
            model="text-embedding-005",
            dimensions=128,
        ),
        client=client,
        embed_config_factory=lambda dimensions: {
            "output_dimensionality": dimensions,
        },
    )

    provider.embed_texts(["wireless headphones", "pasta dinner"])

    assert client.models.calls[0]["config"] == {"output_dimensionality": 128}


def test_embed_text_wraps_vertex_errors() -> None:
    class FailingModels:
        def embed_content(self, **_: object) -> FakeResponse:
            raise RuntimeError("upstream unavailable")

    provider = VertexAIEmbeddingProvider(
        VertexAIEmbeddingConfig(
            project_id="payback-test",
            location="europe-west1",
            model="text-embedding-005",
        ),
        client=FakeClient(models=FailingModels()),
    )

    with pytest.raises(RuntimeError, match="Vertex AI embedding request failed") as exc:
        provider.embed_text("wireless headphones")

    assert isinstance(exc.value.__cause__, RuntimeError)
