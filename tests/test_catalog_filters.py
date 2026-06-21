import pytest

from app.catalog.filters import (
    filter_available,
    filter_by_category,
    filter_by_partner,
    filter_by_price_range,
    filter_by_tag,
    filter_promotions,
)
from app.schemas import Partner, Product


@pytest.fixture
def products() -> list[Product]:
    return [
        Product(
            product_id="dm-001",
            partner=Partner.DM,
            name="Sensitive Toothpaste",
            name_de="Sensitiv-Zahnpasta",
            category="oral care",
            description="Fluoride toothpaste for sensitive teeth.",
            description_de="Fluorid-Zahnpasta fuer empfindliche Zaehne.",
            brand="Dontodent",
            price=1.95,
            tags=["toothpaste", "oral care", "sensitive"],
            tags_de=["zahnpasta", "mundpflege", "sensitiv"],
            availability=True,
            popularity_score=0.8,
            is_promotion=True,
        ),
        Product(
            product_id="edeka-001",
            partner=Partner.EDEKA,
            name="Spaghetti Pasta",
            name_de="Spaghetti Nudeln",
            category="pasta and grains",
            description="Durum wheat spaghetti for pasta dishes.",
            description_de="Hartweizen-Spaghetti fuer Pastagerichte.",
            brand="EDEKA",
            price=0.99,
            tags=["pasta", "grocery", "spaghetti"],
            tags_de=["nudeln", "lebensmittel", "spaghetti"],
            availability=True,
            popularity_score=0.7,
            is_promotion=False,
        ),
        Product(
            product_id="amazon-001",
            partner=Partner.AMAZON,
            name="Wireless Headphones",
            name_de="Kabellose Kopfhoerer",
            category="electronics",
            description="Bluetooth headphones for music and calls.",
            description_de="Bluetooth-Kopfhoerer fuer Musik und Anrufe.",
            brand="Anker",
            price=59.99,
            tags=["electronics", "headphones", "bluetooth"],
            tags_de=["elektronik", "kopfhoerer", "bluetooth"],
            availability=False,
            popularity_score=0.9,
            is_promotion=True,
        ),
        Product(
            product_id="amazon-002",
            partner=Partner.AMAZON,
            name="LED Desk Lamp",
            name_de="LED Schreibtischlampe",
            category="Home Office",
            description="Adjustable LED lamp for desks.",
            description_de="Verstellbare LED-Lampe fuer Schreibtische.",
            brand="Amazon Basics",
            price=24.99,
            tags=["home office", "desk lamp", "led"],
            tags_de=["homeoffice", "schreibtischlampe", "led"],
            availability=True,
            popularity_score=0.6,
            is_promotion=False,
        ),
    ]


def test_filter_by_partner_returns_only_products_from_one_partner(
    products: list[Product],
) -> None:
    results = filter_by_partner(products, Partner.AMAZON)

    assert [product.product_id for product in results] == ["amazon-001", "amazon-002"]
    assert all(product.partner == Partner.AMAZON for product in results)


def test_filter_by_category_is_case_insensitive(products: list[Product]) -> None:
    results = filter_by_category(products, "  home   office ")

    assert [product.product_id for product in results] == ["amazon-002"]


def test_filter_by_price_range_with_only_min_price(products: list[Product]) -> None:
    results = filter_by_price_range(products, min_price=20.0)

    assert [product.product_id for product in results] == ["amazon-001", "amazon-002"]


def test_filter_by_price_range_with_only_max_price(products: list[Product]) -> None:
    results = filter_by_price_range(products, max_price=2.0)

    assert [product.product_id for product in results] == ["dm-001", "edeka-001"]


def test_filter_by_price_range_with_min_and_max_price(
    products: list[Product],
) -> None:
    results = filter_by_price_range(products, min_price=1.0, max_price=30.0)

    assert [product.product_id for product in results] == ["dm-001", "amazon-002"]


def test_filter_promotions_returns_only_promotional_products(
    products: list[Product],
) -> None:
    results = filter_promotions(products)

    assert [product.product_id for product in results] == ["dm-001", "amazon-001"]
    assert all(product.is_promotion is True for product in results)


def test_filter_available_returns_only_available_products(
    products: list[Product],
) -> None:
    results = filter_available(products)

    assert [product.product_id for product in results] == [
        "dm-001",
        "edeka-001",
        "amazon-002",
    ]
    assert all(product.availability is True for product in results)


def test_filter_by_tag_checks_english_and_german_tags(
    products: list[Product],
) -> None:
    english_results = filter_by_tag(products, "  HEADPHONES ")
    german_results = filter_by_tag(products, "zahnpasta")

    assert [product.product_id for product in english_results] == ["amazon-001"]
    assert [product.product_id for product in german_results] == ["dm-001"]
