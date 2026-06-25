"""Lightweight local/API load test for the assistant service."""

from __future__ import annotations

import argparse
import json
import math
import os
import random
import statistics
import sys
import time
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


DEFAULT_QUERIES = (
    "Bitte zeige mir Angebote fuer guenstige Windeln",
    "Ich suche preiswerte Snacks fuer den Abend",
    "Show me headphones on Amazon",
    "I need stuff for a pasta dinner",
    "Meine PAYBACK Punkte fehlen",
    "Compare cheap diapers from dm and Amazon",
)


@dataclass(frozen=True)
class LoadTestResult:
    latency_ms: list[float]
    success_count: int
    error_count: int


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a lightweight sequential load test against the assistant API."
    )
    parser.add_argument(
        "--base-url",
        default=os.getenv("API_BASE_URL", "http://localhost:8000"),
        help="API base URL, for example http://localhost:8000 or a Cloud Run URL.",
    )
    parser.add_argument(
        "--requests",
        type=int,
        default=int(os.getenv("LOAD_TEST_REQUESTS", "50")),
        help="Total number of requests to send. Default: 50.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=float(os.getenv("LOAD_TEST_TIMEOUT", "10")),
        help="Per-request timeout in seconds. Default: 10.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=int(os.getenv("LOAD_TEST_SEED", "7")),
        help="Random seed used to choose representative queries. Default: 7.",
    )
    return parser.parse_args(argv)


def build_request(base_url: str, query: str) -> Request:
    payload = json.dumps({"query": query, "top_k": 5}).encode("utf-8")
    return Request(
        f"{base_url.rstrip('/')}/assistant/query",
        data=payload,
        headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
        },
        method="POST",
    )


def percentile(values: list[float], percentile_value: float) -> float:
    if not values:
        return 0.0
    if percentile_value <= 0:
        return min(values)
    if percentile_value >= 100:
        return max(values)

    ordered = sorted(values)
    index = math.ceil((percentile_value / 100.0) * len(ordered)) - 1
    index = max(0, min(index, len(ordered) - 1))
    return ordered[index]


def run_load_test(
    base_url: str,
    request_count: int,
    timeout: float,
    seed: int,
) -> LoadTestResult:
    rng = random.Random(seed)
    latency_ms: list[float] = []
    success_count = 0
    error_count = 0

    for _ in range(request_count):
        query = rng.choice(DEFAULT_QUERIES)
        request = build_request(base_url, query)
        started_at = time.perf_counter()

        try:
            with urlopen(request, timeout=timeout) as response:
                response.read()
                if 200 <= response.status < 300:
                    success_count += 1
                else:
                    error_count += 1
        except (HTTPError, URLError, TimeoutError, ValueError):
            error_count += 1
        finally:
            latency_ms.append((time.perf_counter() - started_at) * 1000.0)

    return LoadTestResult(
        latency_ms=latency_ms,
        success_count=success_count,
        error_count=error_count,
    )


def print_summary(base_url: str, request_count: int, result: LoadTestResult) -> None:
    total = len(result.latency_ms)
    average_ms = statistics.mean(result.latency_ms) if result.latency_ms else 0.0
    p50 = percentile(result.latency_ms, 50)
    p95 = percentile(result.latency_ms, 95)
    p99 = percentile(result.latency_ms, 99)

    print(f"Load test target: {base_url.rstrip('/')}")
    print(f"Requests sent: {request_count}")
    print(f"Success count: {result.success_count}")
    print(f"Error count: {result.error_count}")
    print(f"Average latency (ms): {average_ms:.2f}")
    print(f"p50 latency (ms): {p50:.2f}")
    print(f"p95 latency (ms): {p95:.2f}")
    print(f"p99 latency (ms): {p99:.2f}")
    print(f"Samples recorded: {total}")


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    base_url = args.base_url.strip().rstrip("/")

    if args.requests < 1:
        print("--requests must be at least 1", file=sys.stderr)
        return 2
    if not base_url:
        print("API base URL must not be empty", file=sys.stderr)
        return 2

    print(
        f"Running sequential load test against {base_url} "
        f"({args.requests} requests, timeout {args.timeout:.1f}s)"
    )
    result = run_load_test(base_url, args.requests, args.timeout, args.seed)
    print_summary(base_url, args.requests, result)

    return 0 if result.error_count == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
