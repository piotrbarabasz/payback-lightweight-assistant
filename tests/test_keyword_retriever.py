from app.retrieval.base import ProductRetriever
from app.retrieval.keyword_retriever import KeywordProductRetriever
from app.retrieval.normalizer import normalize_query
from app.retrieval.service import retrieve_products
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
        product(
            "amazon-002",
            Partner.AMAZON,
            name="USB-C Cable",
            name_de="USB-C Kabel",
            category="electronics",
            description="Charging cable for phones.",
            description_de="Ladekabel fuer Smartphones.",
            brand="Amazon Basics",
            price=6.99,
            tags=["electronics", "cable"],
            tags_de=["elektronik", "kabel"],
            availability=False,
            popularity_score=0.95,
        ),
    ]


def test_keyword_product_retriever_implements_product_retriever_protocol() -> None:
    assert isinstance(KeywordProductRetriever(), ProductRetriever)


def test_keyword_product_retriever_returns_ranked_product_results() -> None:
    results = KeywordProductRetriever().retrieve(
        "Bitte zeige guenstige Windeln",
        small_catalog(),
        top_k=2,
    )

    assert results
    assert all(isinstance(result, ProductResult) for result in results)
    assert results[0].product_id == "dm-001"
    assert all(0 <= result.score <= 1 for result in results)


def test_keyword_product_retriever_accepts_precomputed_intent_analysis() -> None:
    query = "Show me headphones on Amazon"
    retriever = KeywordProductRetriever()

    results_without_analysis = retriever.retrieve(query, small_catalog(), top_k=2)
    results_with_analysis = retriever.retrieve(
        query,
        small_catalog(),
        top_k=2,
        intent_analysis=normalize_query(query),
    )

    assert results_with_analysis == results_without_analysis
    assert results_with_analysis[0].product_id == "amazon-001"


def test_keyword_product_retriever_returns_empty_list_for_invalid_top_k() -> None:
    results = KeywordProductRetriever().retrieve("headphones", small_catalog(), top_k=0)

    assert results == []


def test_retrieve_products_preserves_keyword_retriever_behavior() -> None:
    query = "Show me headphones on Amazon"
    products = small_catalog()

    assert retrieve_products(query, products, top_k=2) == KeywordProductRetriever().retrieve(
        query,
        products,
        top_k=2,
    )
