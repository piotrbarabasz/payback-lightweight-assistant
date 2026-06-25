import pytest

from app.embeddings.vertex_ai import VertexAIEmbeddingProvider
from app.retrieval.backends.bigquery_vector import BigQueryVectorProductRetriever


def test_vertex_ai_embedding_provider_fails_clearly() -> None:
    provider = VertexAIEmbeddingProvider()

    with pytest.raises(
        NotImplementedError,
        match="Vertex AI embeddings are not implemented in the MVP",
    ):
        provider.embed_text("wireless headphones")


def test_bigquery_vector_retriever_fails_clearly() -> None:
    retriever = BigQueryVectorProductRetriever()

    with pytest.raises(
        NotImplementedError,
        match="BigQuery Vector Search retrieval is not implemented in the MVP",
    ):
        retriever.retrieve(
            query="show me cheap pasta",
            products=[],
            top_k=3,
        )
