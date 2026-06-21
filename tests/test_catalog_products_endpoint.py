from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_catalog_products_returns_200() -> None:
    response = client.get("/catalog/products")

    assert response.status_code == 200


def test_catalog_products_response_is_list() -> None:
    response = client.get("/catalog/products")

    assert isinstance(response.json(), list)


def test_catalog_products_limit_parameter_works() -> None:
    response = client.get(
        "/catalog/products",
        params={"limit": 3, "available_only": False},
    )

    assert response.status_code == 200
    assert len(response.json()) == 3


def test_catalog_products_partner_filter_works() -> None:
    response = client.get(
        "/catalog/products",
        params={"partner": "dm", "available_only": False, "limit": 100},
    )

    assert response.status_code == 200
    data = response.json()
    assert data
    assert all(product["partner"] == "dm" for product in data)
