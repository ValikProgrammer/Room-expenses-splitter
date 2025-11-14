"""Simple client to verify Flask endpoints using the requests library."""

from __future__ import annotations

import argparse
import sys
from typing import List

import requests


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Check Room Expense Tracker endpoints."
    )
    parser.add_argument(
        "--base-url",
        default="http://localhost:80800",
        help="Base URL where the Flask app is running.",
    )
    args = parser.parse_args(argv)

    base = args.base_url.rstrip("/")
    endpoints = ["/health", "/api/members", "/api/transactions"]

    for endpoint in endpoints:
        url = f"{base}{endpoint}"
        try:
            response = requests.get(url, timeout=5)
            response.raise_for_status()
        except requests.RequestException as exc:
            print(f"{endpoint}: failed ({exc})")
            return 1
        print(f"{endpoint}: OK ({len(response.content)} bytes)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

