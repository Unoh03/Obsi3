#!/usr/bin/env python3
"""Small local target for DB-less SSRF checker verification.

This server is not CARE evidence. It only verifies that checker.py can:

- keep a normal fetch baseline separate from a loopback-only proof request;
- mark proof disclosure as vulnerable;
- mark configured SSRF blocking evidence as not_vulnerable.
"""

from __future__ import annotations

import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse


INTERNAL_PROOF_URL = "http://127.0.0.1/vuln/ssrf/internal-proof.php"
PROOF_BODY = (
    "[SSRF_INTERNAL_PROOF]\n"
    "proof=care-ssrf-local-only-proof\n"
    "remote_addr=127.0.0.1\n"
    "message=This response is visible only when the CARE server requests its own localhost address.\n"
)


class SSRFFetchMockHandler(BaseHTTPRequestHandler):
    server_version = "KisaSSRFMock/1.0"

    def do_GET(self) -> None:
        parsed = urlparse(self.path)

        if parsed.path == "/":
            self.send_text(
                200,
                "<html><body><h1>CARE SSRF baseline mock</h1></body></html>\n",
                content_type="text/html; charset=utf-8",
            )
            return

        if parsed.path == "/vuln/ssrf/internal-proof.php":
            self.send_text(403, "[DENIED]\nThis proof page is only available from localhost.\n")
            return

        if parsed.path != "/vuln/ssrf/fetch.php":
            self.send_text(404, "not found\n")
            return

        params = parse_qs(parsed.query)
        target_url = params.get("url", [""])[0]
        mode = self.server.mode  # type: ignore[attr-defined]

        if target_url == INTERNAL_PROOF_URL:
            if mode == "vulnerable":
                self.send_text(200, mock_fetch_response(target_url, PROOF_BODY))
                return
            self.send_text(
                200,
                mock_fetch_response(target_url, "허용되지 않은 요청 대상입니다.\n"),
            )
            return

        self.send_text(
            200,
            mock_fetch_response(
                target_url,
                "<html><body><h1>CARE main mock</h1><p>baseline fetch ok</p></body></html>\n",
            ),
            content_type="text/plain; charset=utf-8",
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


def mock_fetch_response(url: str, response: str) -> str:
    return f"[URL]\n{url}\n\n[HTTP_CODE]\n200\n\n[ERROR]\n\n\n[RESPONSE]\n{response}"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=18081)
    parser.add_argument(
        "--mode",
        choices=("vulnerable", "safe"),
        default="vulnerable",
        help=(
            "vulnerable: loopback internal proof is returned through fetch.php; "
            "safe: loopback internal proof is blocked by fetch.php"
        ),
    )
    parser.add_argument("--verbose", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    server = ThreadingHTTPServer((args.host, args.port), SSRFFetchMockHandler)
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
