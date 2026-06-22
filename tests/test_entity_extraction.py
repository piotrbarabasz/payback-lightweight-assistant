from app.intent.entities import detect_partner_hint, extract_entities
from app.schemas import Partner


def test_extract_entities_detects_german_diaper_query() -> None:
    entities = extract_entities("Bitte zeige mir g\u00fcnstige Windeln")

    assert entities.product_category == "baby care"
    assert entities.price_preference == "cheap"


def test_extract_entities_detects_pasta_dinner_query() -> None:
    entities = extract_entities("I need stuff for a pasta dinner")

    assert entities.product_category == "pasta and grains"
    assert entities.occasion == "dinner"


def test_extract_entities_and_partner_hint_detect_premium_sony_amazon_query() -> None:
    query = "Show me premium Sony headphones on Amazon"
    entities = extract_entities(query)

    assert entities.product_category == "electronics"
    assert entities.price_preference == "premium"
    assert entities.brand == "sony"
    assert detect_partner_hint(query) == Partner.AMAZON


def test_extract_entities_detects_bio_milk_query() -> None:
    entities = extract_entities("Ich suche Bio Milch")

    assert entities.product_category == "dairy"
    assert entities.dietary_preference == "organic"


def test_extract_entities_and_partner_hint_detect_dm_toothpaste_query() -> None:
    query = "Zahnpasta bei dm"
    entities = extract_entities(query)

    assert entities.product_category == "oral care"
    assert detect_partner_hint(query) == Partner.DM
