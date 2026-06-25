"""dm partner adapter backed by the local synthetic catalog."""

from __future__ import annotations

from app.partners.base import PartnerMetadata
from app.schemas import Partner, Product


class DmPartnerAdapter:
    metadata = PartnerMetadata(
        partner_id=Partner.DM,
        display_name="dm",
        ecosystem_type="drugstore",
        description=(
            "Local synthetic drugstore catalog for personal care, baby care, "
            "beauty, and household essentials."
        ),
    )

    def list_products(self, products: list[Product]) -> list[Product]:
        return [product for product in products if product.partner == Partner.DM]
