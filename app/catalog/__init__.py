"""Synthetic product catalog data layer."""

from app.catalog.filters import (
    filter_available,
    filter_by_category,
    filter_by_partner,
    filter_by_price_range,
    filter_by_tag,
    filter_products,
    filter_promotions,
)
from app.catalog.loader import (
    DEFAULT_CATALOG_PATH,
    get_available_products,
    get_default_catalog_path,
    get_product_by_id,
    get_products_by_partner,
    load_catalog,
    load_default_catalog,
    load_products,
)

__all__ = [
    "DEFAULT_CATALOG_PATH",
    "filter_available",
    "filter_by_category",
    "filter_by_partner",
    "filter_by_price_range",
    "filter_by_tag",
    "filter_products",
    "filter_promotions",
    "get_available_products",
    "get_default_catalog_path",
    "get_product_by_id",
    "get_products_by_partner",
    "load_catalog",
    "load_default_catalog",
    "load_products",
]
