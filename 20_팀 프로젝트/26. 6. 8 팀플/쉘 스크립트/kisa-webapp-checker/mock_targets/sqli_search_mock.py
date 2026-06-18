#!/usr/bin/env python3
"""Small local target for DB-less SQLi checker verification.

This server is not CARE evidence. It only verifies that checker.py can:

- keep a healthy baseline separate from SQLi payload responses;
- produce request/response evidence for payload probes;
- avoid marking baseline-wide 500 failures as SQLi vulnerabilities.
"""

from __future__ import annotations

import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse


SQLI_MARKERS = ("'", '"', " or ", " union ", "--", "/*", "*/")


class SQLiSearchMockHandler(BaseHTTPRequestHandler):
    server_version = "KisaSQLiMock/1.0"

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path != "/center/list.php":
            self.send_text(404, "not found\n")
            return

        params = parse_qs(parsed.query)
        data = params.get("data", [""])[0]

        if self.server.mode == "db-down":  # type: ignore[attr-defined]
            self.send_text(
                500,
                "simulated database outage before SQLi comparison\n",
            )
            return

        if self.server.mode == "vulnerable" and looks_like_sqli(data):  # type: ignore[attr-defined]
            self.send_text(
                500,
                "mysqli_sql_exception: You have an error in your SQL syntax near payload\n",
            )
            return

        self.send_text(
            200,
            "<html><body><h1>CARE board search mock</h1>"
            f"<p>search={html_escape(data)}</p>"
            "<p>rows=2</p></body></html>\n",
            content_type="text/html; charset=utf-8",
        )

    def log_message(self, fmt: str, *args: object) -> None:
        if self.server.verbose:  # type: ignore[attr-defined]
            super().log_message(fmt, *args)

    def send_text(
        self, status: int, body: str, content_type: str = "text/plain; charset=utf-8"
    ) -> None:
        encoded = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)


def looks_like_sqli(value: str) -> bool:
    lowered = f" {value.lower()} "
    return any(marker in lowered for marker in SQLI_MARKERS)


def html_escape(value: str) -> str:
    return (
        value.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#x27;")
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=18080)
    parser.add_argument(
        "--mode",
        choices=("vulnerable", "safe", "db-down"),
        default="vulnerable",
        help=(
            "vulnerable: SQLi-like payloads return 500 with SQL error text; "
            "safe: all searches return 200; "
            "db-down: baseline and payloads return 500"
        ),
    )
    parser.add_argument("--verbose", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    server = ThreadingHTTPServer((args.host, args.port), SQLiSearchMockHandler)
    server.mode = args.mode  # type: ignore[attr-defined]
    server.verbose = args.verbose  # type: ignore[attr-defined]
    print(f"[OK] mock target listening on http://{args.host}:{args.port}")
    print(f"[OK] mode={args.mode}")
    print("[INFO] Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[INFO] stopping mock target")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
