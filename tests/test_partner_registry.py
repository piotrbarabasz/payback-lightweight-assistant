from app.partners import (
    PartnerAdapter,
    get_partner_adapter,
    list_partner_adapters,
    list_partner_metadata,
    products_for_partner_hint,
)
from app.schemas import Partner, Product


def product(product_id: str, partner: Partner) -> Product:
    return Product(
        product_id=product_id,
        partner=partner,
        name=f"{partner.value} Product",
        name_de=f"{partner.value} Produkt",
        category="test category",
        description="Synthetic test product.",
        description_de="Synthetisches Testprodukt.",
        brand="Test Brand",
        price=1.99,
        tags=["test"],
        tags_de=["test"],
    )


def test_partner_registry_exposes_three_concrete_adapters() -> None:
    adapters = list_partner_adapters()

    assert len(adapters) == 3
    assert all(isinstance(adapter, PartnerAdapter) for adapter in adapters)
    assert {adapter.metadata.partner_id for adapter in adapters} == {
        Partner.DM,
        Partner.EDEKA,
        Partner.AMAZON,
    }


def test_partner_registry_exposes_expected_metadata() -> None:
    metadata = {item.partner_id: item for item in list_partner_metadata()}

    assert metadata[Partner.DM].display_name == "dm"
    assert metadata[Partner.DM].ecosystem_type == "drugstore"
    assert "synthetic drugstore catalog" in metadata[Partner.DM].description
    assert metadata[Partner.EDEKA].display_name == "EDEKA"
    assert metadata[Partner.EDEKA].ecosystem_type == "grocery"
    assert "synthetic grocery catalog" in metadata[Partner.EDEKA].description
    assert metadata[Partner.AMAZON].display_name == "Amazon"
    assert metadata[Partner.AMAZON].ecosystem_type == "general_merchandise"
    assert "synthetic general-merchandise catalog" in metadata[
        Partner.AMAZON
    ].description


def test_available_partner_metadata_has_required_fields() -> None:
    metadata = list_partner_metadata()

    assert len(metadata) == 3
    assert {item.partner_id for item in metadata} == {
        Partner.DM,
        Partner.EDEKA,
        Partner.AMAZON,
    }
    assert all(item.display_name.strip() for item in metadata)
    assert all(item.ecosystem_type.strip() for item in metadata)
    assert all(item.description.strip() for item in metadata)


def test_get_partner_adapter_returns_none_for_unknown_partner() -> None:
    assert get_partner_adapter(None) is None
    assert get_partner_adapter(Partner.UNKNOWN) is None


def test_partner_adapter_filters_local_catalog_products() -> None:
    products = [
        product("dm-001", Partner.DM),
        product("edeka-001", Partner.EDEKA),
        product("amazon-001", Partner.AMAZON),
    ]

    adapter = get_partner_adapter(Partner.EDEKA)

    assert adapter is not None
    assert [item.product_id for item in adapter.list_products(products)] == [
        "edeka-001"
    ]


def test_products_for_unknown_partner_hint_keeps_full_catalog() -> None:
    products = [
        product("dm-001", Partner.DM),
        product("edeka-001", Partner.EDEKA),
        product("amazon-001", Partner.AMAZON),
    ]

    assert products_for_partner_hint(products, None) == products
    assert products_for_partner_hint(products, Partner.UNKNOWN) == products


def test_products_for_partner_hint_uses_adapter_scope() -> None:
    products = [
        product("dm-001", Partner.DM),
        product("edeka-001", Partner.EDEKA),
        product("amazon-001", Partner.AMAZON),
    ]

    scoped_products = products_for_partner_hint(products, Partner.AMAZON)

    assert [product.product_id for product in scoped_products] == ["amazon-001"]
