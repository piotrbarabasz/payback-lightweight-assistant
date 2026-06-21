import json
from collections import Counter
from pathlib import Path

from pydantic import TypeAdapter

from app.data.generate_synthetic_catalog import build_catalog, write_catalog
from app.schemas import Partner, Product


def test_generator_creates_exactly_150_products() -> None:
    products = build_catalog()

    assert len(products) == 150


def test_generator_creates_50_products_per_partner() -> None:
    products = build_catalog()
    counts_by_partner = Counter(product.partner for product in products)

    assert counts_by_partner[Partner.DM] == 50
    assert counts_by_partner[Partner.EDEKA] == 50
    assert counts_by_partner[Partner.AMAZON] == 50


def test_generated_product_ids_are_unique() -> None:
    products = build_catalog()
    product_ids = [product.product_id for product in products]

    assert len(product_ids) == len(set(product_ids))


def test_generated_product_ids_are_stable_partner_prefixed_sequences() -> None:
    products = build_catalog()
    product_ids = {product.product_id for product in products}

    assert {f"dm-{index:03d}" for index in range(1, 51)} <= product_ids
    assert {f"edeka-{index:03d}" for index in range(1, 51)} <= product_ids
    assert {f"amazon-{index:03d}" for index in range(1, 51)} <= product_ids


def test_generated_products_validate_against_product_schema() -> None:
    products = build_catalog()
    dumped_products = [product.model_dump(mode="json") for product in products]

    validated_products = TypeAdapter(list[Product]).validate_python(dumped_products)

    assert validated_products == products


def test_generated_products_have_required_text_and_tags() -> None:
    products = build_catalog()

    assert all(product.name for product in products)
    assert all(product.name_de for product in products)
    assert all(product.description for product in products)
    assert all(product.description_de for product in products)
    assert all(product.tags for product in products)
    assert all(product.tags_de for product in products)


def test_generated_prices_are_non_negative() -> None:
    products = build_catalog()

    assert all(product.price >= 0 for product in products)


def test_generated_popularity_scores_are_between_zero_and_one() -> None:
    products = build_catalog()

    assert all(0 <= product.popularity_score <= 1 for product in products)


def test_write_catalog_can_generate_json_without_overwriting_real_catalog() -> None:
    output_path = Path("tests/.generated-products.json")

    try:
        written_path = write_catalog(output_path)
        payload = json.loads(written_path.read_text(encoding="utf-8"))
        products = TypeAdapter(list[Product]).validate_python(payload)

        assert written_path == output_path
        assert len(products) == 150
    finally:
        output_path.unlink(missing_ok=True)
