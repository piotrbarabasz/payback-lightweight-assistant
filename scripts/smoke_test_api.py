"""Smoke test a running assistant API locally or on Cloud Run."""

from __future__ import annotations

import json
import os
import sys
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8080").rstrip("/")
QUERY_EXAMPLES = (
    "Bitte zeige mir Angebote fuer guenstige Windeln",
    "I need stuff for a pasta dinner",
    "Show me headphones on Amazon",
    "Meine PAYBACK Punkte fehlen",
    "Something nice",
)


def request_json(
    method: str,
    path: str,
    payload: dict[str, Any] | None = None,
) -> tuple[int, Any]:
    body = None
    headers = {"Accept": "application/json"}

    if payload is not None:
        body = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"

    request = Request(
        f"{API_BASE_URL}{path}",
        data=body,
        headers=headers,
        method=method,
    )

    with urlopen(request, timeout=10) as response:
        response_body = response.read().decode("utf-8")
        data = json.loads(response_body) if response_body else None
        return response.status, data


def print_response(label: str, status_code: int, payload: Any) -> None:
    print(f"\n{label}")
    print(f"Status: {status_code}")
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def main() -> int:
    print(f"Testing API base URL: {API_BASE_URL}")

    try:
        status_code, payload = request_json("GET", "/health")
        print_response("GET /health", status_code, payload)
        if status_code != 200:
            print(f"Health check failed with status {status_code}.", file=sys.stderr)
            return 1

        for query in QUERY_EXAMPLES:
            status_code, payload = request_json(
                "POST",
                "/assistant/query",
                {"query": query, "top_k": 5},
            )
            print_response(f"POST /assistant/query - {query}", status_code, payload)

    except HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        print(f"HTTP error {exc.code}: {body}", file=sys.stderr)
        return 1
    except URLError as exc:
        print(f"Connection error: {exc.reason}", file=sys.stderr)
        return 1
    except TimeoutError:
        print("Request timed out.", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
