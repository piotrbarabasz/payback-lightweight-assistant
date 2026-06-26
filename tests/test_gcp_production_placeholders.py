from app.config import get_settings
from app.retrieval.backends.bigquery_vector import BigQueryVectorProductRetriever
from app.retrieval.factory import get_product_retriever
from app.retrieval.keyword_retriever import KeywordProductRetriever


def test_bigquery_vector_retriever_can_be_constructed_without_gcp_calls() -> None:
    retriever = BigQueryVectorProductRetriever()

    assert isinstance(retriever, BigQueryVectorProductRetriever)


def test_bigquery_vector_backend_selection_returns_retriever() -> None:
    retriever = get_product_retriever("bigquery_vector")

    assert isinstance(retriever, BigQueryVectorProductRetriever)


def test_default_local_retrieval_backend_still_uses_keyword(monkeypatch) -> None:
    monkeypatch.delenv("RETRIEVAL_BACKEND", raising=False)
    get_settings.cache_clear()

    retriever = get_product_retriever()

    assert isinstance(retriever, KeywordProductRetriever)
