"""Amazon partner adapter backed by the local synthetic catalog."""

from __future__ import annotations

from app.partners.base import PartnerMetadata
from app.schemas import Partner, Product


class AmazonPartnerAdapter:
    metadata = PartnerMetadata(
        partner_id=Partner.AMAZON,
        display_name="Amazon",
        ecosystem_type="general_merchandise",
        description=(
            "Local synthetic general-merchandise catalog for electronics, "
            "home office, books, toys, sport, and household items."
        ),
    )

    def list_products(self, products: list[Product]) -> list[Product]:
        return [product for product in products if product.partner == Partner.AMAZON]
