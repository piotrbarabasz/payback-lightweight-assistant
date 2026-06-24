import pytest

from app.embeddings.base import EmbeddingProvider
from app.embeddings.local import LocalHashEmbeddingProvider
from app.embeddings.similarity import cosine_similarity


def test_local_hash_embedding_provider_implements_embedding_provider_protocol() -> None:
    assert isinstance(LocalHashEmbeddingProvider(), EmbeddingProvider)


def test_local_hash_embedding_provider_is_deterministic() -> None:
    provider = LocalHashEmbeddingProvider(dimensions=16)

    first_vector = provider.embed_text("Sensitive toothpaste for oral care")
    second_vector = provider.embed_text("Sensitive toothpaste for oral care")

    assert first_vector == second_vector
    assert len(first_vector) == 16


def test_same_text_gives_same_vector() -> None:
    provider = LocalHashEmbeddingProvider()

    assert provider.embed_text("wireless headphones") == provider.embed_text(
        "wireless headphones"
    )


def test_different_text_gives_different_vector() -> None:
    provider = LocalHashEmbeddingProvider(dimensions=32)

    assert provider.embed_text("baby diapers") != provider.embed_text(
        "wireless headphones"
    )


def test_cosine_similarity_returns_expected_values() -> None:
    assert cosine_similarity([1.0, 0.0], [1.0, 0.0]) == 1.0
    assert cosine_similarity([1.0, 0.0], [0.0, 1.0]) == 0.0
    assert cosine_similarity([1.0, 1.0], [1.0, 1.0]) == pytest.approx(1.0)


def test_cosine_similarity_handles_invalid_or_empty_vectors_safely() -> None:
    assert cosine_similarity([], []) == 0.0
    assert cosine_similarity([0.0, 0.0], [1.0, 0.0]) == 0.0
    assert cosine_similarity([1.0], [1.0, 0.0]) == 0.0


def test_empty_text_returns_zero_vector() -> None:
    provider = LocalHashEmbeddingProvider(dimensions=8)

    assert provider.embed_text("") == [0.0] * 8
    assert provider.embed_text("   ") == [0.0] * 8


def test_local_hash_embedding_provider_rejects_invalid_dimensions() -> None:
    with pytest.raises(ValueError, match="dimensions must be at least 1"):
        LocalHashEmbeddingProvider(dimensions=0)
