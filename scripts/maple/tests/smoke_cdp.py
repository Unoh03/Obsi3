"""Opt-in real browser + local HTTP smoke test; no MapleScouter calculations."""
import asyncio
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import sys
from threading import Thread
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import httpx
from playwright.async_api import async_playwright
from phase1_cdp import Capture
from phase1_core import read_json, replay, write_json


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def do_GET(self):
        body = b"<!doctype html><title>Maple CLI local smoke test</title>"
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        data = self.rfile.read(int(self.headers["Content-Length"]))
        parsed = json.loads(data)
        body = json.dumps({"result": parsed["value"] * 2}, separators=(",", ":")).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


async def run(endpoint):
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    worker = Thread(target=server.serve_forever, daemon=True)
    worker.start()
    root = Path(__file__).resolve().parents[1] / ".runtime" / ("smoke-" + uuid.uuid4().hex)
    root.mkdir(parents=True)
    context = None
    try:
        async with async_playwright() as pw:
            browser = await pw.chromium.connect_over_cdp(endpoint, is_local=True, no_defaults=True)
            context = await browser.new_context()
            try:
                page = await context.new_page()
                await page.goto(f"http://127.0.0.1:{server.server_port}/")
                session = await context.new_cdp_session(page)
                capture = Capture(session, ["127.0.0.1"])
                await capture.start()
                await page.evaluate("""async () => {
                    const r = await fetch('/calc', {method:'POST', headers:{'Content-Type':'application/json'}, body:'{ "value": 7 }'});
                    return await r.json();
                }""")
                await capture.finish()
                requests = capture.save(root)
                assert len(requests) == 1, requests
                fixture = root / requests[0]["directory"]
                assert read_json(fixture / "response.json") == {"result": 14}
                assert (fixture / "request.postdata.txt").read_bytes() == b'{ "value": 7 }'
                reports = {}
                for mode in ("observed", "json"):
                    reports[mode] = replay(fixture, root / mode, mode, transport=httpx.HTTPTransport(retries=0))
                    assert reports[mode]["parsed_response_equal"] is True
                    assert reports[mode]["body_bytes_equal"] is True
                write_json(root / "smoke-result.json", {"status": "PASS", "scope": "local HTTP only; NOT MapleScouter", "reports": reports})
                print(json.dumps({"status": "PASS", "scope": "real_CDP_capture_and_local_HTTP_replay", "output": str(root)}, ensure_ascii=False))
                await session.detach()
            finally:
                await context.close()
    finally:
        server.shutdown()
        server.server_close()
        worker.join(timeout=5)


if __name__ == "__main__":
    asyncio.run(run(sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:9222"))
