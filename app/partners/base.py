"""Base partner adapter interfaces for local catalog-backed ecosystems."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from app.schemas import Partner, Product


@dataclass(frozen=True)
class PartnerMetadata:
    partner_id: Partner
    display_name: str
    ecosystem_type: str
    description: str


@runtime_checkable
class PartnerAdapter(Protocol):
    """Protocol implemented by partner ecosystem adapters."""

    metadata: PartnerMetadata

    def list_products(self, products: list[Product]) -> list[Product]:
        """Return this partner's products from the local synthetic catalog."""
