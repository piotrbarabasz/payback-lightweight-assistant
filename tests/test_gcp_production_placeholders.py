import pytest

from app.config import get_settings
from app.embeddings.vertex_ai import VertexAIEmbeddingProvider
from app.retrieval.backends.bigquery_vector import BigQueryVectorProductRetriever
from app.retrieval.factory import get_product_retriever
from app.retrieval.keyword_retriever import KeywordProductRetriever


def test_google_cloud_dependencies_are_not_required() -> None:
    with open("requirements.txt", encoding="utf-8") as requirements_file:
        requirements = requirements_file.read()

    assert "google-cloud-aiplatform" not in requirements
    assert "google-cloud-bigquery" not in requirements


def test_vertex_ai_embedding_provider_fails_clearly() -> None:
    provider = VertexAIEmbeddingProvider()

    with pytest.raises(
        NotImplementedError,
        match="Vertex AI embeddings are not implemented in the MVP.*Stage 8",
    ):
        provider.embed_text("wireless headphones")


def test_bigquery_vector_retriever_fails_clearly() -> None:
    retriever = BigQueryVectorProductRetriever()

    with pytest.raises(
        NotImplementedError,
        match=(
            "BigQuery Vector Search retrieval is not implemented "
            "in the MVP.*Stage 8"
        ),
    ):
        retriever.retrieve(
            query="show me cheap pasta",
            products=[],
            top_k=3,
        )


def test_bigquery_vector_backend_selection_fails_clearly_when_used() -> None:
    retriever = get_product_retriever("bigquery_vector")

    assert isinstance(retriever, BigQueryVectorProductRetriever)
    with pytest.raises(
        NotImplementedError,
        match=(
            "BigQuery Vector Search retrieval is not implemented "
            "in the MVP.*Stage 8"
        ),
    ):
        retriever.retrieve(
            query="show me cheap pasta",
            products=[],
            top_k=3,
        )


def test_default_local_retrieval_backend_still_uses_keyword(monkeypatch) -> None:
    monkeypatch.delenv("RETRIEVAL_BACKEND", raising=False)
    get_settings.cache_clear()

    retriever = get_product_retriever()

    assert isinstance(retriever, KeywordProductRetriever)
