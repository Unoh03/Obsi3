import asyncio
import base64
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from phase1_core import (EvidenceError, decoded_body, filter_headers, freeze_snapshot,
                        inspect_body, json_diff, parse_json, replay, safe_url,
                        sha256, verify_snapshot, write_bytes, write_json)
from phase1_cdp import Capture, NetworkLedger


def event(url="https://api.maplescouter.com/observed", **extra):
    return {"requestId": "r1", "type": "Fetch", "request": {"url": url, "method": "POST", "hasPostData": True, "headers": {"Content-Type": "application/json"}}, **extra}


class DiffTests(unittest.TestCase):
    def test_insert_is_index_based(self):
        diff = json_diff(["a", "b", "c"], ["a", "x", "b", "c"])
        self.assertEqual(diff["values_changed"]["root[1]"]["new_value"], "x")
        self.assertEqual(diff["values_changed"]["root[2]"]["new_value"], "b")
        self.assertEqual(diff["iterable_item_added"]["root[3]"], "c")

    def test_swap(self):
        self.assertEqual(len(json_diff(["a", "b"], ["b", "a"])["values_changed"]), 2)

    def test_types_null_missing_empty(self):
        for left, right in [([1], ["1"]), (1, True), (1, 1.0), (None, {}), ({}, {"x": None}), ([], {}), ({"__x": 1}, {"__x": 2})]:
            with self.subTest(left=left, right=right):
                self.assertTrue(json_diff(left, right))

    def test_ambiguous_json_rejected(self):
        for text in ['{"x":1,"x":2}', '{"x":NaN}']:
            with self.assertRaises(EvidenceError):
                parse_json(text)


class EvidenceTests(unittest.TestCase):
    def test_headers_review_and_secrets(self):
        headers = {"Cookie": "private", "Authorization": "private", "X-Client-Version": "1", "Content-Type": "application/json", "X-Api-Key": "private", "Referer": "https://example.com/?token=private"}
        filtered = filter_headers(headers)
        self.assertEqual(filtered["kept"], {"content-type": "application/json"})
        self.assertNotIn("private", json.dumps(filtered))
        reviewed = filter_headers(headers, ["X-Client-Version", "X-Api-Key"])
        self.assertEqual(reviewed["kept"]["x-client-version"], "1")
        self.assertNotIn("x-api-key", reviewed["kept"])

    def test_sensitive_body_url(self):
        for value in [b'{"userStat":{"access_token":"private"}}', b'{"value":"Bearer private"}']:
            with self.assertRaises(EvidenceError):
                inspect_body(value)
        for url in ["https://name:password@example.com/", "https://example.com/?api_key=private", "https://example.com/#token=private"]:
            with self.assertRaises(EvidenceError):
                safe_url(url)

    def test_base64(self):
        data = '{"한글":1}'.encode()
        self.assertEqual(decoded_body({"body": base64.b64encode(data).decode(), "base64Encoded": True}), data)

    def test_snapshot_hash_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "raw.json"
            source.write_text('{"metadata":{"character_name":"우노03","collected_at":"T"},"ring_exchange":{"error":true}}', encoding="utf-8")
            identity = freeze_snapshot(source, root / "frozen")
            self.assertEqual(verify_snapshot(root / "frozen")[0], identity)
            self.assertEqual(identity["error_sections"], ["ring_exchange"])
            with self.assertRaises(FileExistsError):
                freeze_snapshot(source, root / "frozen")
            (root / "frozen" / "nexon.raw.json").write_text("{}")
            with self.assertRaises(EvidenceError):
                verify_snapshot(root / "frozen")


class LedgerTests(unittest.TestCase):
    def test_extra_before_and_after_with_redirect(self):
        ledger = NetworkLedger()
        ledger.extra("request", {"requestId": "r1", "headers": {"Accept": "first", "Cookie": "private"}, "associatedCookies": ["private"]})
        first = ledger.request(event())
        second = ledger.request(event(url="https://api.maplescouter.com/next", redirectHasExtraInfo=True, redirectResponse={"status": 302, "headers": {}}))
        ledger.extra("response", {"requestId": "r1", "statusCode": 302, "headers": {"Set-Cookie": "private"}})
        ledger.received({"requestId": "r1", "hasExtraInfo": True, "response": {"status": 200, "headers": {}, "fromDiskCache": True}})
        ledger.extra("request", {"requestId": "r1", "headers": {"Accept": "second"}})
        ledger.extra("response", {"requestId": "r1", "statusCode": 304, "headers": {}})
        ledger.correlate()
        self.assertEqual(first["completion"], "redirect")
        self.assertEqual(first["request_headers"]["kept"]["accept"], "first")
        self.assertEqual(second["request_headers"]["kept"]["accept"], "second")
        self.assertEqual(second["status"], 200)
        self.assertEqual(second["network_status"], 304)
        self.assertTrue(second["cache"]["fromDiskCache"])
        self.assertNotIn("private", json.dumps(ledger.chains))

    def test_ambiguous_extra_is_not_misattributed(self):
        ledger = NetworkLedger()
        first = ledger.request(event())
        ledger.extra("request", {"requestId": "r1", "headers": {"Accept": "unknown"}})
        ledger.correlate()
        self.assertEqual(first["request_extra_status"], "missing_or_ambiguous")
        self.assertNotIn("accept", first["request_headers"]["kept"])


class FakeCDP:
    def __init__(self):
        self.calls = []
        self.handlers = {}

    def on(self, name, fn):
        self.handlers[name] = fn

    async def send(self, name, params=None):
        self.calls.append((name, params))
        if name == "Network.getRequestPostData":
            return {"postData": '{ "value": 1 }'}
        if name == "Network.getResponseBody":
            return {"body": base64.b64encode(b'{"result":2}').decode(), "base64Encoded": True}
        return {}


class CaptureTests(unittest.IsolatedAsyncioTestCase):
    async def test_normal_cache_untouched_and_body_after_finished(self):
        session = FakeCDP()
        capture = Capture(session, ["maplescouter.com"])
        await capture.start()
        self.assertNotIn("Network.setCacheDisabled", [c[0] for c in session.calls])
        capture.on_request(event())
        await asyncio.sleep(0)
        capture.on_cache({"requestId": "r1"})
        capture.on_response({"requestId": "r1", "hasExtraInfo": False, "response": {"status": 200, "headers": {}, "fromServiceWorker": True}})
        self.assertNotIn("Network.getResponseBody", [c[0] for c in session.calls])
        capture.on_finished({"requestId": "r1"})
        await capture.finish()
        hop = capture.ledger.current("r1")
        self.assertEqual(hop["_response_json"], {"result": 2})
        self.assertTrue(hop["cache"]["fromServiceWorker"])
        self.assertTrue(hop["cache"]["requestServedFromCache"])

    async def test_failed_and_missing_body(self):
        class FailedCDP(FakeCDP):
            async def send(self, name, params=None):
                if "Body" in name or "PostData" in name:
                    raise RuntimeError("private value must not leak")
                return await super().send(name, params)
        session = FailedCDP()
        capture = Capture(session, ["maplescouter.com"])
        capture.on_request(event())
        await asyncio.sleep(0)
        capture.on_failed({"requestId": "r1", "blockedReason": "csp", "errorText": "private"})
        await capture.finish()
        hop = capture.ledger.current("r1")
        self.assertEqual(hop["completion"], "failed")
        self.assertEqual(hop["request_body_status"], "RuntimeError")
        self.assertNotIn("private", json.dumps(hop))


class ReplayTests(unittest.TestCase):
    def fixture(self, root):
        root.mkdir()
        body = '{  "한글": [1, null] }\n'.encode()
        write_bytes(root / "request.postdata.txt", body)
        write_json(root / "request.json", parse_json(body.decode()))
        write_json(root / "response.json", {"result": 2})
        write_json(root / "request-meta.json", {"url": "https://api.maplescouter.com/observed", "method": "POST", "encoding": "utf-8", "request_body_status": "captured", "request_body_sha256": sha256(body)})
        write_json(root / "headers.json", {"request": {"kept": {"content-type": "application/json", "x-client-version": "1"}, "excluded": []}})
        return body

    def test_modes_headers_and_client_configuration(self):
        import httpx
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            observed = self.fixture(root / "fixture")
            requests = []
            def handle(request):
                requests.append(request)
                return httpx.Response(200, json={"result": 2}, headers={"Set-Cookie": "private"})
            real_client = httpx.Client
            with patch.dict(os.environ, {"HTTPS_PROXY": "http://127.0.0.1:1"}), patch("httpx.Client", wraps=real_client) as client:
                for mode in ("observed", "json"):
                    result = replay(root / "fixture", root / mode, mode, ["x-client-version"], transport=httpx.MockTransport(handle))
                    self.assertTrue(result["parsed_response_equal"])
                for call in client.call_args_list:
                    self.assertFalse(call.kwargs["trust_env"])
                    self.assertFalse(call.kwargs["follow_redirects"])
                    self.assertEqual(call.kwargs["timeout"], 30.0)
            self.assertEqual(requests[0].content, observed)
            self.assertNotEqual(requests[1].content, observed)
            self.assertEqual(parse_json(requests[1].content.decode()), parse_json(observed.decode()))
            self.assertEqual(requests[0].headers["x-client-version"], "1")
            self.assertNotIn("cookie", requests[1].headers)
            self.assertNotIn("private", (root / "observed" / "replay.json").read_text())
            with self.assertRaises(FileExistsError):
                replay(root / "fixture", root / "observed", "observed", transport=httpx.MockTransport(handle))

    def test_redirect_and_non_json_are_not_followed_or_saved(self):
        import httpx
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.fixture(root / "fixture")
            requests = []
            def handle(request):
                requests.append(request)
                return httpx.Response(302, headers={"Location": "https://example.com/"}, text="not JSON")
            result = replay(root / "fixture", root / "run", "observed", transport=httpx.MockTransport(handle))
            self.assertEqual(len(requests), 1)
            self.assertEqual(result["status"], 302)
            self.assertEqual(result["body_status"], "not_saved")
            self.assertFalse((root / "run" / "response.body.txt").exists())


if __name__ == "__main__":
    unittest.main()
