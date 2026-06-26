from scripts.load_test_api import LoadTestResult, parse_args, percentile, print_summary


def test_parse_args_defaults_to_local_base_url(monkeypatch) -> None:
    monkeypatch.delenv("API_BASE_URL", raising=False)
    monkeypatch.delenv("LOAD_TEST_REQUESTS", raising=False)
    monkeypatch.delenv("LOAD_TEST_DELAY_SECONDS", raising=False)

    args = parse_args([])

    assert args.base_url == "http://localhost:8080"
    assert args.requests == 50
    assert args.delay_seconds == 0


def test_percentile_uses_nearest_rank() -> None:
    values = [10.0, 20.0, 30.0, 40.0]

    assert percentile(values, 50) == 20.0
    assert percentile(values, 95) == 40.0


def test_print_summary_includes_status_and_exception_breakdowns(capsys) -> None:
    result = LoadTestResult(
        latency_ms=[10.0, 20.0],
        success_count=1,
        error_count=1,
        status_counts={200: 1, 500: 1},
        exception_counts={"TimeoutError": 1},
    )

    print_summary("http://localhost:8080", 2, result)

    output = capsys.readouterr().out
    assert "Status breakdown:" in output
    assert "  200: 1" in output
    assert "  500: 1" in output
    assert "Exception breakdown:" in output
    assert "  TimeoutError: 1" in output
