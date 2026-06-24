from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import app
from app.retrieval.base import ProductRetriever
from app.retrieval.hybrid import HybridProductRetriever
from app.schemas import Partner, Product, ProductResult


client = TestClient(app)


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
    is_promotion: bool = False,
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
        is_promotion=is_promotion,
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
            is_promotion=True,
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
            "edeka-002",
            Partner.EDEKA,
            name="Fresh Milk",
            name_de="Frische Milch",
            category="dairy",
            description="Milk for breakfast and cooking.",
            description_de="Milch fuer Fruehstueck und Kochen.",
            brand="EDEKA",
            price=1.19,
            tags=["milk", "dairy"],
            tags_de=["milch", "molkerei"],
            popularity_score=0.6,
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


def test_hybrid_product_retriever_implements_product_retriever_protocol() -> None:
    assert isinstance(HybridProductRetriever(), ProductRetriever)


def test_hybrid_product_retriever_returns_results() -> None:
    results = HybridProductRetriever().retrieve(
        "wireless bluetooth headphones",
        small_catalog(),
        top_k=3,
    )

    assert results
    assert all(isinstance(result, ProductResult) for result in results)
    assert all("hybrid retrieval" in (result.reason or "") for result in results)
    assert any("keyword score" in (result.reason or "") for result in results)
    assert any("semantic similarity" in (result.reason or "") for result in results)


def test_hybrid_product_retriever_respects_top_k() -> None:
    results = HybridProductRetriever().retrieve("baby pasta headphones", small_catalog(), top_k=2)

    assert len(results) == 2


def test_partner_specific_query_prefers_requested_partner() -> None:
    results = HybridProductRetriever().retrieve(
        "Show me headphones on Amazon",
        small_catalog(),
        top_k=3,
    )

    assert results
    assert results[0].partner == Partner.AMAZON
    assert all(result.partner == Partner.AMAZON for result in results)


def test_cheap_diaper_query_returns_dm_baby_care_products() -> None:
    results = HybridProductRetriever().retrieve(
        "Bitte zeige guenstige Windeln",
        small_catalog(),
        top_k=3,
    )

    assert results[0].product_id == "dm-001"
    assert results[0].partner == Partner.DM
    assert results[0].category == "baby care"


def test_pasta_dinner_query_returns_edeka_pasta_or_grain_products() -> None:
    results = HybridProductRetriever().retrieve(
        "I need stuff for a pasta dinner",
        small_catalog(),
        top_k=3,
    )

    assert results[0].product_id == "edeka-001"
    assert results[0].partner == Partner.EDEKA
    assert results[0].category == "pasta and grains"


def test_vague_query_handling_remains_controlled_by_intent_layer(monkeypatch) -> None:
    monkeypatch.setenv("RETRIEVAL_BACKEND", "hybrid")
    get_settings.cache_clear()

    try:
        response = client.post(
            "/assistant/query",
            json={"query": "Something nice"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["next_best_action"] == "ask_clarifying_question"
        assert data["clarifying_question"] is not None
        assert data["results"] == []
    finally:
        get_settings.cache_clear()
