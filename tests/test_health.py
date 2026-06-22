from fastapi.testclient import TestClient

import app.main as main_module
from app.main import app


client = TestClient(app)
EXPECTED_HEALTH_KEYS = {"status", "service", "environment"}


def test_app_metadata_uses_settings() -> None:
    assert app.title == "PAYBACK Lightweight Assistant"
    assert app.version == "0.5.0"


def test_health_endpoint_returns_ok() -> None:
    response = client.get("/health")

    assert response.status_code == 200


def test_health_endpoint_returns_expected_fields() -> None:
    response = client.get("/health")
    payload = response.json()

    assert payload["status"] == "ok"
    assert payload["service"] == "payback-lightweight-assistant"
    assert payload["environment"] == "local"


def test_health_endpoint_shape_is_stable_for_cloud_run() -> None:
    response = client.get("/health")

    assert set(response.json()) == EXPECTED_HEALTH_KEYS


def test_health_endpoint_does_not_return_catalog_data_or_results(monkeypatch) -> None:
    def fail_if_catalog_loads() -> None:
        raise AssertionError("/health must not load the product catalog")

    monkeypatch.setattr(main_module, "load_products", fail_if_catalog_loads)

    response = client.get("/health")
    payload = response.json()

    assert response.status_code == 200
    assert "results" not in payload
    assert "products" not in payload
    assert "catalog" not in payload


def test_readiness_endpoint_returns_ok() -> None:
    response = client.get("/ready")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "payback-lightweight-assistant",
        "environment": "local",
    }
