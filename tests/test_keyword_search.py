from app.retrieval.keyword_search import (
    keyword_match_score,
    product_search_text,
    search_products_by_keywords,
)
from app.schemas import Partner, Product


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
        price=4.99,
        tags=tags,
        tags_de=tags_de,
        availability=availability,
        popularity_score=popularity_score,
    )


def diaper_product(
    product_id: str = "dm-001",
    partner: Partner = Partner.DM,
    *,
    availability: bool = True,
    popularity_score: float = 0.5,
) -> Product:
    return product(
        product_id,
        partner,
        name="Baby Diapers Size 4",
        name_de="Babywindeln Groesse 4",
        category="baby care",
        description="Soft absorbent diapers for daily baby care.",
        description_de="Weiche saugfaehige Windeln fuer taegliche Babypflege.",
        brand="Babylove",
        tags=["diapers", "baby", "cheap"],
        tags_de=["g\u00fcnstig", "windeln"],
        availability=availability,
        popularity_score=popularity_score,
    )


def test_product_search_text_includes_all_searchable_fields() -> None:
    catalog_product = product(
        "dm-001",
        Partner.DM,
        name="Sensitive Toothpaste",
        name_de="Sensitiv-Zahnpasta",
        category="oral care",
        description="Fluoride toothpaste for sensitive teeth.",
        description_de="Zahnpasta fuer empfindliche Zaehne.",
        brand="Dontodent",
        tags=["toothpaste", "oral care"],
        tags_de=["zahnpasta", "mundpflege"],
    )

    search_text = product_search_text(catalog_product)

    assert "sensitive toothpaste" in search_text
    assert "sensitiv zahnpasta" in search_text
    assert "oral care" in search_text
    assert "fluoride toothpaste" in search_text
    assert "zahnpasta fuer empfindliche zaehne" in search_text
    assert "dontodent" in search_text
    assert "toothpaste" in search_text
    assert "mundpflege" in search_text


def test_keyword_match_score_returns_positive_score_for_matching_english_query() -> None:
    score = keyword_match_score("cheap diapers", diaper_product())

    assert score > 0
    assert score <= 1


def test_keyword_match_score_returns_positive_score_for_matching_german_query() -> None:
    score = keyword_match_score("g\u00fcnstige Windeln", diaper_product())

    assert score > 0
    assert score <= 1


def test_keyword_match_score_returns_zero_for_unrelated_product() -> None:
    milk = product(
        "edeka-001",
        Partner.EDEKA,
        name="Fresh Milk",
        name_de="Frische Milch",
        category="dairy",
        description="Low fat milk for breakfast.",
        description_de="Fettarme Milch fuer das Fruehstueck.",
        brand="EDEKA",
        tags=["milk", "dairy"],
        tags_de=["milch", "molkerei"],
    )

    assert keyword_match_score("cheap diapers", milk) == 0


def test_search_products_by_keywords_returns_top_k_sorted_by_score_descending() -> None:
    products = [
        diaper_product("dm-001", popularity_score=0.2),
        product(
            "dm-002",
            Partner.DM,
            name="Baby Lotion",
            name_de="Baby Pflegelotion",
            category="baby care",
            description="Mild lotion for babies.",
            description_de="Milde Lotion fuer Babys.",
            brand="Babylove",
            tags=["baby"],
            tags_de=["baby"],
            popularity_score=0.9,
        ),
        product(
            "edeka-001",
            Partner.EDEKA,
            name="Fresh Milk",
            name_de="Frische Milch",
            category="dairy",
            description="Low fat milk for breakfast.",
            description_de="Fettarme Milch fuer das Fruehstueck.",
            brand="EDEKA",
            tags=["milk"],
            tags_de=["milch"],
        ),
    ]

    results = search_products_by_keywords("cheap baby diapers", products, top_k=2)

    assert [catalog_product.product_id for catalog_product, _score in results] == [
        "dm-001",
        "dm-002",
    ]
    assert [score for _catalog_product, score in results] == sorted(
        [score for _catalog_product, score in results],
        reverse=True,
    )


def test_search_products_by_keywords_partner_hint_restricts_results() -> None:
    products = [
        diaper_product("dm-001", Partner.DM),
        diaper_product("amazon-001", Partner.AMAZON),
    ]

    results = search_products_by_keywords(
        "cheap diapers",
        products,
        partner_hint=Partner.AMAZON,
    )

    assert [catalog_product.product_id for catalog_product, _score in results] == [
        "amazon-001"
    ]
    assert all(catalog_product.partner == Partner.AMAZON for catalog_product, _ in results)


def test_search_products_by_keywords_available_only_excludes_unavailable_products() -> None:
    products = [
        diaper_product("dm-001", availability=False, popularity_score=0.9),
        diaper_product("dm-002", availability=True, popularity_score=0.1),
    ]

    results = search_products_by_keywords(
        "cheap diapers",
        products,
        available_only=True,
    )

    assert [catalog_product.product_id for catalog_product, _score in results] == [
        "dm-002"
    ]
