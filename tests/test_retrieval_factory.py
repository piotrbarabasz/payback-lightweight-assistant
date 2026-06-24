import pytest

from app.config import get_settings
from app.retrieval.factory import get_product_retriever
from app.retrieval.keyword_retriever import KeywordProductRetriever


def test_get_product_retriever_defaults_to_keyword(monkeypatch) -> None:
    monkeypatch.delenv("RETRIEVAL_BACKEND", raising=False)
    get_settings.cache_clear()

    retriever = get_product_retriever()

    assert isinstance(retriever, KeywordProductRetriever)


def test_get_product_retriever_uses_explicit_keyword_config(monkeypatch) -> None:
    monkeypatch.setenv("RETRIEVAL_BACKEND", "keyword")
    get_settings.cache_clear()

    retriever = get_product_retriever()

    assert isinstance(retriever, KeywordProductRetriever)


def test_get_product_retriever_accepts_keyword_backend_argument() -> None:
    retriever = get_product_retriever("keyword")

    assert isinstance(retriever, KeywordProductRetriever)


def test_get_product_retriever_rejects_unsupported_backend() -> None:
    with pytest.raises(ValueError, match="Unsupported retrieval backend: semantic"):
        get_product_retriever("semantic")


def test_get_product_retriever_marks_hybrid_as_not_implemented() -> None:
    with pytest.raises(
        NotImplementedError,
        match="Hybrid retrieval backend is not implemented yet.",
    ):
        get_product_retriever("hybrid")
