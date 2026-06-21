from pathlib import Path

import pytest

from app.catalog.loader import (
    get_available_products,
    get_default_catalog_path,
    get_products_by_partner,
    load_products,
)
from app.schemas import Partner, Product


def test_load_products_loads_default_products_json_file() -> None:
    products = load_products()

    assert get_default_catalog_path().name == "products.json"
    assert isinstance(products, list)
    assert products
    assert all(isinstance(product, Product) for product in products)


def test_load_products_raises_clear_error_when_file_does_not_exist() -> None:
    missing_path = Path("tests/.missing-products.json")

    with pytest.raises(FileNotFoundError, match="Product catalog file does not exist"):
        load_products(missing_path)


def test_get_products_by_partner_returns_only_requested_partner() -> None:
    products = load_products()

    dm_products = get_products_by_partner(Partner.DM, products)

    assert dm_products
    assert all(product.partner == Partner.DM for product in dm_products)


def test_get_available_products_returns_only_available_products() -> None:
    products = load_products()

    available_products = get_available_products(products)

    assert available_products
    assert all(product.availability is True for product in available_products)


def test_load_products_returns_150_products_when_generated_catalog_is_present() -> None:
    products = load_products()

    assert len(products) == 150
