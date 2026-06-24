from types import SimpleNamespace

from app.embeddings.product_text import build_product_embedding_text
from app.schemas import Partner, Product


def product(
    *,
    tags: list[str] | None = None,
    tags_de: list[str] | None = None,
    is_promotion: bool = False,
    product_url: str | None = None,
) -> Product:
    return Product(
        product_id="dm-001",
        partner=Partner.DM,
        name="Sensitive Toothpaste",
        name_de="Sensitiv-Zahnpasta",
        category="oral care",
        description="Fluoride toothpaste for sensitive teeth.",
        description_de="Zahnpasta fuer empfindliche Zaehne.",
        brand="Dontodent",
        price=1.95,
        currency="EUR",
        tags=tags or ["toothpaste", "oral care"],
        tags_de=tags_de or ["zahnpasta", "mundpflege"],
        availability=True,
        popularity_score=0.7,
        is_promotion=is_promotion,
        product_url=product_url,
    )


def test_build_product_embedding_text_includes_normal_product_fields() -> None:
    text = build_product_embedding_text(product(is_promotion=True))

    assert text == (
        "Product: Sensitive Toothpaste. "
        "German product name: Sensitiv-Zahnpasta. "
        "Partner: dm. "
        "Category: oral care. "
        "Brand: Dontodent. "
        "Description: Fluoride toothpaste for sensitive teeth. "
        "German description: Zahnpasta fuer empfindliche Zaehne. "
        "Tags: toothpaste, oral care. "
        "German tags: zahnpasta, mundpflege. "
        "Price: 1.95 EUR. "
        "Availability: available. "
        "Promotion: active promotion."
    )


def test_build_product_embedding_text_handles_missing_optional_fields() -> None:
    partial_product = SimpleNamespace(
        partner=Partner.AMAZON,
        name="Wireless Mouse",
        category="electronics",
        description="Compact mouse for home office.",
        price=None,
        tags=[],
        availability=None,
        is_promotion=False,
    )

    text = build_product_embedding_text(partial_product)

    assert "Product: Wireless Mouse." in text
    assert "Partner: amazon." in text
    assert "Category: electronics." in text
    assert "Description: Compact mouse for home office." in text
    assert "Brand:" not in text
    assert "Price:" not in text
    assert "Promotion:" not in text


def test_build_product_embedding_text_includes_tags_in_stable_order() -> None:
    text = build_product_embedding_text(
        product(
            tags=["sensitive teeth", "fluoride", "fresh breath"],
            tags_de=["zahnpasta", "atem"],
        )
    )

    assert "Tags: sensitive teeth, fluoride, fresh breath." in text
    assert "German tags: zahnpasta, atem." in text


def test_build_product_embedding_text_contains_searchable_fields() -> None:
    text = build_product_embedding_text(product())

    for expected_text in [
        "Sensitive Toothpaste",
        "Sensitiv-Zahnpasta",
        "dm",
        "oral care",
        "Dontodent",
        "Fluoride toothpaste for sensitive teeth",
        "Zahnpasta fuer empfindliche Zaehne",
        "toothpaste",
        "zahnpasta",
    ]:
        assert expected_text in text
