from app.retrieval.scorer import (
    build_recommendation_reason,
    calculate_final_score,
)
from app.schemas import Partner, Product


def product(
    product_id: str,
    *,
    partner: Partner = Partner.DM,
    category: str = "oral care",
    price: float = 2.99,
    popularity_score: float = 0.5,
    is_promotion: bool = False,
) -> Product:
    return Product(
        product_id=product_id,
        partner=partner,
        name="Sensitive Toothpaste",
        name_de="Sensitiv-Zahnpasta",
        category=category,
        description="Toothpaste for sensitive teeth.",
        description_de="Zahnpasta fuer sensible Zaehne.",
        brand="Test Brand",
        price=price,
        tags=["toothpaste", "oral care"],
        tags_de=["zahnpasta", "mundpflege"],
        popularity_score=popularity_score,
        is_promotion=is_promotion,
    )


def test_calculate_final_score_returns_value_between_zero_and_one() -> None:
    catalog_product = product("dm-001")

    score = calculate_final_score(
        keyword_score=0.5,
        product=catalog_product,
        query="toothpaste",
    )

    assert 0 <= score <= 1


def test_partner_match_increases_score_when_partner_hint_matches() -> None:
    catalog_product = product("dm-001", partner=Partner.DM)

    score_without_partner = calculate_final_score(
        0.4,
        catalog_product,
        "toothpaste",
    )
    score_with_partner = calculate_final_score(
        0.4,
        catalog_product,
        "toothpaste",
        partner_hint=Partner.DM,
    )

    assert score_with_partner > score_without_partner


def test_category_hint_increases_score_when_product_category_matches() -> None:
    catalog_product = product("dm-001", category="oral care")

    score_without_category = calculate_final_score(
        0.4,
        catalog_product,
        "toothpaste",
    )
    score_with_category = calculate_final_score(
        0.4,
        catalog_product,
        "toothpaste",
        category_hints=["oral care"],
    )

    assert score_with_category > score_without_category


def test_cheap_price_preference_boosts_cheaper_products() -> None:
    cheap_product = product("dm-001", price=1.49)
    expensive_product = product("dm-002", price=49.99)

    cheap_score = calculate_final_score(
        0.4,
        cheap_product,
        "cheap toothpaste",
        price_preference="cheap",
    )
    expensive_score = calculate_final_score(
        0.4,
        expensive_product,
        "cheap toothpaste",
        price_preference="cheap",
    )

    assert cheap_score > expensive_score


def test_promotion_gives_small_score_boost() -> None:
    regular_product = product("dm-001", is_promotion=False)
    promoted_product = product("dm-002", is_promotion=True)

    regular_score = calculate_final_score(0.4, regular_product, "toothpaste")
    promoted_score = calculate_final_score(0.4, promoted_product, "toothpaste")

    assert promoted_score > regular_score


def test_popularity_affects_score_slightly() -> None:
    unpopular_product = product("dm-001", popularity_score=0.1)
    popular_product = product("dm-002", popularity_score=0.9)

    unpopular_score = calculate_final_score(0.4, unpopular_product, "toothpaste")
    popular_score = calculate_final_score(0.4, popular_product, "toothpaste")

    assert popular_score > unpopular_score
    assert popular_score - unpopular_score < 0.05


def test_build_recommendation_reason_returns_non_empty_string() -> None:
    reason = build_recommendation_reason(
        product("dm-001"),
        "toothpaste",
        0.5,
    )

    assert isinstance(reason, str)
    assert reason


def test_recommendation_reason_mentions_relevant_boosts_when_applicable() -> None:
    reason = build_recommendation_reason(
        product("dm-001", is_promotion=True),
        "cheap toothpaste",
        0.75,
        partner_hint=Partner.DM,
        category_hints=["oral care"],
        price_preference="cheap",
    )

    assert "dm partner" in reason
    assert "category hint" in reason
    assert "cheap price preference" in reason
    assert "promotion" in reason
