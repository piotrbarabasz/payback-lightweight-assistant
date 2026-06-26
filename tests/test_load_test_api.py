from scripts.load_test_api import parse_args, percentile


def test_parse_args_defaults_to_local_base_url(monkeypatch) -> None:
    monkeypatch.delenv("API_BASE_URL", raising=False)
    monkeypatch.delenv("LOAD_TEST_REQUESTS", raising=False)

    args = parse_args([])

    assert args.base_url == "http://localhost:8080"
    assert args.requests == 50


def test_percentile_uses_nearest_rank() -> None:
    values = [10.0, 20.0, 30.0, 40.0]

    assert percentile(values, 50) == 20.0
    assert percentile(values, 95) == 40.0
