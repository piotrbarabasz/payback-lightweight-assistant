"""Pure catalog filtering utilities."""

from __future__ import annotations

from app.schemas import Partner, Product


def filter_by_partner(products: list[Product], partner: Partner) -> list[Product]:
    """Return products for a specific partner."""

    return [product for product in products if product.partner == partner]


def filter_by_category(products: list[Product], category: str) -> list[Product]:
    """Return products whose category matches exactly after normalization."""

    normalized_category = _normalize(category)
    return [
        product
        for product in products
        if _normalize(product.category) == normalized_category
    ]


def filter_by_price_range(
    products: list[Product],
    min_price: float | None = None,
    max_price: float | None = None,
) -> list[Product]:
    """Return products within an inclusive price range."""

    return [
        product
        for product in products
        if (min_price is None or product.price >= min_price)
        and (max_price is None or product.price <= max_price)
    ]


def filter_promotions(products: list[Product]) -> list[Product]:
    """Return products marked as promotional."""

    return [product for product in products if product.is_promotion]


def filter_available(products: list[Product]) -> list[Product]:
    """Return products that are currently available."""

    return [product for product in products if product.availability]


def filter_by_tag(products: list[Product], tag: str) -> list[Product]:
    """Return products whose English or German tags contain the requested tag."""

    normalized_tag = _normalize(tag)
    return [
        product
        for product in products
        if normalized_tag in {_normalize(value) for value in product.tags}
        or normalized_tag in {_normalize(value) for value in product.tags_de}
    ]


def filter_products(
    products: list[Product],
    *,
    partner: Partner | None = None,
    category: str | None = None,
    min_price: float | None = None,
    max_price: float | None = None,
    tag: str | None = None,
    availability: bool | None = None,
    promotions_only: bool = False,
    limit: int | None = None,
) -> list[Product]:
    """Compatibility helper that composes the simple catalog filters."""

    if limit is not None and limit < 1:
        raise ValueError("limit must be greater than zero")

    results = list(products)
    if partner is not None:
        results = filter_by_partner(results, partner)
    if category is not None:
        results = filter_by_category(results, category)
    if min_price is not None or max_price is not None:
        results = filter_by_price_range(results, min_price, max_price)
    if tag is not None:
        results = filter_by_tag(results, tag)
    if availability is True:
        results = filter_available(results)
    elif availability is False:
        results = [product for product in results if not product.availability]
    if promotions_only:
        results = filter_promotions(results)
    if limit is not None:
        results = results[:limit]
    return results


def _normalize(value: str) -> str:
    return " ".join(value.strip().casefold().split())
