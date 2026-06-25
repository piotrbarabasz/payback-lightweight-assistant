"""EDEKA partner adapter backed by the local synthetic catalog."""

from __future__ import annotations

from app.partners.base import PartnerMetadata
from app.schemas import Partner, Product


class EdekaPartnerAdapter:
    metadata = PartnerMetadata(
        partner_id=Partner.EDEKA,
        display_name="EDEKA",
        ecosystem_type="grocery",
    )

    def list_products(self, products: list[Product]) -> list[Product]:
        return [product for product in products if product.partner == Partner.EDEKA]
