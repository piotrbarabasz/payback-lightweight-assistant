"""Catalog loading helpers."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from pydantic import TypeAdapter

from app.schemas import Partner, Product


DEFAULT_CATALOG_PATH = Path(__file__).resolve().parents[1] / "data" / "products.json"


def get_default_catalog_path() -> Path:
    """Return the default path to the synthetic product catalog."""

    return DEFAULT_CATALOG_PATH


def load_products(path: Path | None = None) -> list[Product]:
    """Load and validate products from the synthetic catalog JSON file."""

    catalog_path = path or get_default_catalog_path()
    if not catalog_path.exists():
        raise FileNotFoundError(f"Product catalog file does not exist: {catalog_path}")

    with catalog_path.open("r", encoding="utf-8") as catalog_file:
        payload = json.load(catalog_file)

    products = TypeAdapter(list[Product]).validate_python(payload)
    _validate_unique_product_ids(products)
    return products


def get_products_by_partner(
    partner: Partner,
    products: list[Product],
) -> list[Product]:
    """Return products that belong to a specific partner."""

    return [product for product in products if product.partner == partner]


def get_available_products(products: list[Product]) -> list[Product]:
    """Return products that are currently available."""

    return [product for product in products if product.availability]


def load_catalog(path: str | Path | None = None) -> list[Product]:
    """Compatibility wrapper for loading product records."""

    catalog_path = Path(path) if path is not None else None
    return load_products(catalog_path)


@lru_cache(maxsize=1)
def load_default_catalog() -> list[Product]:
    """Load the checked-in synthetic catalog once per process."""

    return load_products()


def get_product_by_id(
    products: list[Product],
    product_id: str,
) -> Product | None:
    """Find a product by exact product id."""

    normalized_id = product_id.strip()
    for product in products:
        if product.product_id == normalized_id:
            return product
    return None


def _validate_unique_product_ids(products: list[Product]) -> None:
    product_ids = [product.product_id for product in products]
    duplicate_ids = {
        product_id for product_id in product_ids if product_ids.count(product_id) > 1
    }
    if duplicate_ids:
        duplicates = ", ".join(sorted(duplicate_ids))
        raise ValueError(f"duplicate product_id values: {duplicates}")
