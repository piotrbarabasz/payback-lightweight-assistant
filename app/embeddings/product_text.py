"""Deterministic product text construction for future embedding retrieval."""

from __future__ import annotations

from app.schemas import Product


def build_product_embedding_text(product: Product) -> str:
    """Build a stable natural-language representation of a catalog product."""

    parts = [
        _sentence("Product", _first_text(product, "name")),
        _sentence("German product name", _first_text(product, "name_de")),
        _sentence("Partner", _partner_value(product)),
        _sentence("Category", _first_text(product, "category")),
        _sentence("Brand", _first_text(product, "brand")),
        _sentence("Description", _first_text(product, "description")),
        _sentence("German description", _first_text(product, "description_de")),
        _sentence("Tags", _joined_values(product, "tags")),
        _sentence("German tags", _joined_values(product, "tags_de")),
        _sentence("Price", _price_text(product)),
        _sentence("Availability", _availability_text(product)),
        _sentence("Promotion", _promotion_text(product)),
    ]
    return " ".join(part for part in parts if part)


def _sentence(label: str, value: str | None) -> str | None:
    if value is None:
        return None

    normalized_value = " ".join(value.strip().split())
    if not normalized_value:
        return None
    normalized_value = normalized_value.rstrip(".")
    return f"{label}: {normalized_value}."


def _first_text(product: Product, field_name: str) -> str | None:
    value = getattr(product, field_name, None)
    if not isinstance(value, str):
        return None
    return value


def _joined_values(product: Product, field_name: str) -> str | None:
    values = getattr(product, field_name, None)
    if not values:
        return None

    normalized_values = [
        " ".join(value.strip().split())
        for value in values
        if isinstance(value, str) and value.strip()
    ]
    if not normalized_values:
        return None
    return ", ".join(normalized_values)


def _partner_value(product: Product) -> str | None:
    partner = getattr(product, "partner", None)
    value = getattr(partner, "value", partner)
    if not isinstance(value, str):
        return None
    return value


def _price_text(product: Product) -> str | None:
    price = getattr(product, "price", None)
    currency = getattr(product, "currency", None)
    if not isinstance(price, int | float) or not isinstance(currency, str):
        return None
    return f"{price:.2f} {currency.upper()}"


def _availability_text(product: Product) -> str | None:
    availability = getattr(product, "availability", None)
    if availability is True:
        return "available"
    if availability is False:
        return "unavailable"
    return None


def _promotion_text(product: Product) -> str | None:
    is_promotion = getattr(product, "is_promotion", None)
    if is_promotion is True:
        return "active promotion"
    return None
