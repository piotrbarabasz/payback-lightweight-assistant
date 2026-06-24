from types import SimpleNamespace

from app.retrieval.base import ProductRetriever
from app.retrieval.semantic import SemanticProductRetriever
from app.schemas import Partner, Product, ProductResult


def product(
    product_id: str,
    partner: Partner,
    *,
    name: str,
    name_de: str,
    category: str,
    description: str,
    description_de: str,
    brand: str,
    price: float,
    tags: list[str],
    tags_de: list[str],
    availability: bool = True,
    popularity_score: float = 0.5,
) -> Product:
    return Product(
        product_id=product_id,
        partner=partner,
        name=name,
        name_de=name_de,
        category=category,
        description=description,
        description_de=description_de,
        brand=brand,
        price=price,
        tags=tags,
        tags_de=tags_de,
        availability=availability,
        popularity_score=popularity_score,
    )


def small_catalog() -> list[Product]:
    return [
        product(
            "dm-001",
            Partner.DM,
            name="Baby Diapers Size 4",
            name_de="Babywindeln Groesse 4",
            category="baby care",
            description="Affordable diapers for daily baby care.",
            description_de="Guenstige Windeln fuer taegliche Babypflege.",
            brand="Babylove",
            price=7.99,
            tags=["diapers", "baby", "cheap"],
            tags_de=["guenstig", "windeln", "baby"],
            popularity_score=0.8,
        ),
        product(
            "edeka-001",
            Partner.EDEKA,
            name="Spaghetti Pasta",
            name_de="Spaghetti Nudeln",
            category="pasta and grains",
            description="Pasta for dinner with tomato sauce.",
            description_de="Nudeln fuer Abendessen mit Tomatensauce.",
            brand="EDEKA",
            price=1.49,
            tags=["pasta", "dinner", "grocery"],
            tags_de=["nudeln", "abendessen", "lebensmittel"],
            popularity_score=0.75,
        ),
        product(
            "amazon-001",
            Partner.AMAZON,
            name="Wireless Headphones",
            name_de="Kabellose Kopfhoerer",
            category="electronics",
            description="Bluetooth headphones for music and calls.",
            description_de="Bluetooth Kopfhoerer fuer Musik und Anrufe.",
            brand="Anker",
            price=49.99,
            tags=["headphones", "wireless", "electronics"],
            tags_de=["kopfhoerer", "kabellos", "elektronik"],
            popularity_score=0.9,
        ),
    ]


def test_semantic_product_retriever_implements_product_retriever_protocol() -> None:
    assert isinstance(SemanticProductRetriever(), ProductRetriever)


def test_semantic_product_retriever_returns_top_k_results() -> None:
    results = SemanticProductRetriever().retrieve(
        "wireless bluetooth headphones",
        small_catalog(),
        top_k=2,
    )

    assert len(results) == 2
    assert all(isinstance(result, ProductResult) for result in results)
    assert all("semantic similarity" in (result.reason or "") for result in results)
    assert all(0 <= result.score <= 1 for result in results)


def test_semantic_product_retriever_returns_deterministic_results() -> None:
    retriever = SemanticProductRetriever()
    products = small_catalog()

    first_results = retriever.retrieve("pasta dinner", products, top_k=3)
    second_results = retriever.retrieve("pasta dinner", products, top_k=3)

    assert second_results == first_results


def test_semantic_product_retriever_handles_empty_or_unknown_query_gracefully() -> None:
    results = SemanticProductRetriever().retrieve("", small_catalog(), top_k=2)

    assert len(results) == 2
    assert all(isinstance(result, ProductResult) for result in results)
    assert all(result.score == 0 for result in results)


def test_semantic_product_retriever_does_not_crash_on_missing_optional_fields() -> None:
    sparse_product = SimpleNamespace(
        product_id="amazon-999",
        partner=Partner.AMAZON,
        name="Wireless Mouse",
        category="electronics",
        description="Compact mouse for home office.",
        price=9.99,
        currency="EUR",
        tags=[],
        availability=True,
        popularity_score=0.1,
    )

    results = SemanticProductRetriever().retrieve(
        "home office mouse",
        [sparse_product],
        top_k=1,
    )

    assert len(results) == 1
    assert results[0].product_id == "amazon-999"
    assert "semantic similarity" in (results[0].reason or "")
