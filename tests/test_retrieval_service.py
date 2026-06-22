import pytest

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


@pytest.fixture
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
            tags_de=["g\u00fcnstig", "windeln", "baby"],
            popularity_score=0.8,
        ),
        product(
            "dm-002",
            Partner.DM,
            name="Baby Lotion",
            name_de="Baby Pflegelotion",
            category="baby care",
            description="Mild lotion for babies.",
            description_de="Milde Lotion fuer Babys.",
            brand="Babylove",
            price=3.99,
            tags=["baby lotion"],
            tags_de=["babypflege"],
            popularity_score=0.4,
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


def test_retrieve_products_returns_product_result_objects(
    small_catalog: list[Product],
) -> None:
    results = retrieve_products("g\u00fcnstige Windeln", small_catalog, top_k=3)

    assert results
    assert all(isinstance(result, ProductResult) for result in results)


def test_retrieve_products_respects_top_k(small_catalog: list[Product]) -> None:
    results = retrieve_products("electronics", small_catalog, top_k=1)

    assert len(results) == 1


def test_german_diaper_query_returns_dm_baby_care_near_top(
    small_catalog: list[Product],
) -> None:
    results = retrieve_products("g\u00fcnstige Windeln", small_catalog, top_k=3)

    assert results[0].product_id == "dm-001"
    assert results[0].partner == Partner.DM
    assert results[0].category == "baby care"


def test_pasta_dinner_query_returns_edeka_pasta_near_top(
    small_catalog: list[Product],
) -> None:
    results = retrieve_products(
        "I need stuff for a pasta dinner",
        small_catalog,
        top_k=3,
    )

    assert results[0].product_id == "edeka-001"
    assert results[0].partner == Partner.EDEKA
    assert results[0].category == "pasta and grains"


def test_amazon_headphones_query_returns_amazon_electronics_near_top(
    small_catalog: list[Product],
) -> None:
    results = retrieve_products("Amazon headphones", small_catalog, top_k=3)

    assert results[0].product_id == "amazon-001"
    assert results[0].partner == Partner.AMAZON
    assert results[0].category == "electronics"


def test_no_good_match_does_not_crash(small_catalog: list[Product]) -> None:
    results = retrieve_products("accordion repair manual", small_catalog, top_k=3)

    assert isinstance(results, list)
    assert len(results) <= 3
    assert all(isinstance(result, ProductResult) for result in results)


def test_scores_are_between_zero_and_one(small_catalog: list[Product]) -> None:
    results = retrieve_products("electronics headphones", small_catalog, top_k=5)

    assert results
    assert all(0 <= result.score <= 1 for result in results)


def test_results_are_sorted_by_score_descending(small_catalog: list[Product]) -> None:
    results = retrieve_products("baby electronics pasta", small_catalog, top_k=5)
    scores = [result.score for result in results]

    assert scores == sorted(scores, reverse=True)
