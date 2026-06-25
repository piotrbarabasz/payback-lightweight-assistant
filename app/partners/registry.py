"""Partner adapter registry for local catalog-backed partner routing."""

from __future__ import annotations

from app.partners.amazon import AmazonPartnerAdapter
from app.partners.base import PartnerAdapter, PartnerMetadata
from app.partners.dm import DmPartnerAdapter
from app.partners.edeka import EdekaPartnerAdapter
from app.schemas import Partner, Product


_PARTNER_ADAPTERS: dict[Partner, PartnerAdapter] = {
    Partner.DM: DmPartnerAdapter(),
    Partner.EDEKA: EdekaPartnerAdapter(),
    Partner.AMAZON: AmazonPartnerAdapter(),
}


def list_partner_adapters() -> list[PartnerAdapter]:
    """Return all configured concrete partner adapters."""

    return list(_PARTNER_ADAPTERS.values())


def list_partner_metadata() -> list[PartnerMetadata]:
    """Return metadata for all configured concrete partner ecosystems."""

    return [adapter.metadata for adapter in list_partner_adapters()]


def get_partner_adapter(partner: Partner | None) -> PartnerAdapter | None:
    """Return a partner adapter for concrete partners, or None for unknown."""

    if partner is None or partner == Partner.UNKNOWN:
        return None
    return _PARTNER_ADAPTERS.get(partner)


def products_for_partner_hint(
    products: list[Product],
    partner_hint: Partner | None,
) -> list[Product]:
    """Return products scoped to a hinted partner when an adapter exists."""

    adapter = get_partner_adapter(partner_hint)
    if adapter is None:
        return list(products)
    return adapter.list_products(products)
