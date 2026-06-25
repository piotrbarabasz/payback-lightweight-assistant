"""Partner ecosystem adapters backed by the local synthetic catalog."""

from app.partners.amazon import AmazonPartnerAdapter
from app.partners.base import PartnerAdapter, PartnerMetadata
from app.partners.dm import DmPartnerAdapter
from app.partners.edeka import EdekaPartnerAdapter
from app.partners.registry import (
    get_partner_adapter,
    list_partner_adapters,
    list_partner_metadata,
    products_for_partner_hint,
)

__all__ = [
    "AmazonPartnerAdapter",
    "DmPartnerAdapter",
    "EdekaPartnerAdapter",
    "PartnerAdapter",
    "PartnerMetadata",
    "get_partner_adapter",
    "list_partner_adapters",
    "list_partner_metadata",
    "products_for_partner_hint",
]
