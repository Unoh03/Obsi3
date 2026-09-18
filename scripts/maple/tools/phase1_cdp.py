"""CDP event correlation. Never retain full events or cookie structures."""
from __future__ import annotations

import asyncio
from pathlib import Path
from urllib.parse import urlsplit

from phase1_core import (EvidenceError, decoded_body, filter_headers, inspect_body,
                        now, safe_url, sha256, text_encoding, write_bytes, write_json)


class NetworkLedger:
    def __init__(self, reviewed=()):
        self.reviewed = reviewed
        self.chains = {}
        self.extras = {}

    def current(self, request_id):
        return self.chains.get(request_id, [None])[-1]

    def response(self, hop, response):
        hop["response_headers"] = filter_headers(response.get("headers", {}), self.reviewed)
        hop["status"] = response.get("status")
        hop["mime_type"] = response.get("mimeType")
        hop["cache"].update({k: response[k] for k in ("fromDiskCache", "fromServiceWorker", "fromPrefetchCache", "serviceWorkerResponseSource") if k in response})

    def request(self, event):
        request_id = event["requestId"]
        chain = self.chains.setdefault(request_id, [])
        if chain and "redirectResponse" in event:
            previous = chain[-1]
            self.response(previous, event["redirectResponse"])
            previous["has_extra"] = event.get("redirectHasExtraInfo")
            previous["completion"] = "redirect"
            previous["response_body_status"] = "unavailable_redirect"
        request = event["request"]
        try:
            url = safe_url(request["url"])
        except EvidenceError:
            url = None
        hop = {"request_id": request_id, "hop": len(chain), "url": url,
               "url_status": "safe" if url else "blocked", "method": request["method"],
               "resource_type": event.get("type"), "wall_time": event.get("wallTime"),
               "request_headers": filter_headers(request.get("headers", {}), self.reviewed),
               "request_header_source": "requestWillBeSent", "response_header_source": "responseReceived",
               "has_extra": None, "completion": "pending", "request_body_status": "not_requested",
               "response_body_status": "pending", "has_post_data": request.get("hasPostData", False),
               "initiator_type": event.get("initiator", {}).get("type"), "cache": {}}
        chain.append(hop)
        return hop

    def received(self, event):
        hop = self.current(event["requestId"])
        if hop:
            served = hop["cache"].get("requestServedFromCache")
            self.response(hop, event["response"])
            if served:
                hop["cache"]["requestServedFromCache"] = True
            hop["has_extra"] = event.get("hasExtraInfo")

    def extra(self, kind, event):
        # Drop associatedCookies, blockedCookies and headersText at the event boundary.
        entry = {"headers": filter_headers(event.get("headers", {}), self.reviewed)}
        if "statusCode" in event:
            entry["status"] = event["statusCode"]
        self.extras.setdefault((event["requestId"], kind), []).append(entry)

    def correlate(self):
        for request_id, chain in self.chains.items():
            expected = [h for h in chain if h["has_extra"] is True]
            unknown = any(h["has_extra"] is None for h in chain)
            for kind in ("request", "response"):
                extras = self.extras.get((request_id, kind), [])
                if not unknown and len(expected) == len(extras):
                    for hop, extra in zip(expected, extras):
                        hop[f"{kind}_headers"] = extra["headers"]
                        hop[f"{kind}_header_source"] = f"{kind}ExtraInfo"
                        if "status" in extra:
                            hop["network_status"] = extra["status"]
                else:
                    for hop in chain:
                        hop[f"{kind}_extra_status"] = "missing_or_ambiguous" if extras or expected else "not_observed"


class Capture:
    def __init__(self, session, hosts, reviewed=()):
        self.session = session
        self.hosts = set(hosts)
        self.ledger = NetworkLedger(reviewed)
        self.tasks = set()
        self.asset_identity = []
        self.event_errors = []
        self.active = True

    def in_scope(self, hop):
        if not hop or not hop["url"]:
            return False
        host = urlsplit(hop["url"]).hostname or ""
        return any(host == h or host.endswith("." + h) for h in self.hosts)

    def candidate(self, hop):
        return self.in_scope(hop) and hop["resource_type"] in {"Fetch", "XHR"}

    def schedule(self, coroutine):
        async def guarded():
            try:
                await coroutine
            except Exception as exc:
                self.event_errors.append(type(exc).__name__)
        task = asyncio.create_task(guarded())
        self.tasks.add(task)
        task.add_done_callback(self.tasks.discard)

    def on_request(self, event):
        if not self.active:
            return
        hop = self.ledger.request(event)
        if self.candidate(hop) and (hop["has_post_data"] or event["request"].get("postData") is not None):
            self.schedule(self.post_body(hop, event["request"].get("postData")))

    async def post_body(self, hop, inline):
        try:
            reply = await self.session.send("Network.getRequestPostData", {"requestId": hop["request_id"]})
            if self.ledger.current(hop["request_id"]) is not hop:
                raise EvidenceError("request_body_redirect_race")
            encoding = text_encoding(hop["request_headers"]["kept"])
            if reply.get("base64Encoded"):
                data = decoded_body(reply, "postData")
            else:
                data = reply["postData"].encode(encoding)
            source = "Network.getRequestPostData"
        except Exception as exc:
            if inline is None:
                hop["request_body_status"] = str(exc) if isinstance(exc, EvidenceError) else type(exc).__name__
                return
            encoding = text_encoding(hop["request_headers"]["kept"])
            data = inline.encode(encoding)
            source = "requestWillBeSent.postData"
        try:
            parsed = inspect_body(data, encoding)
            hop["_request_body"] = data
            hop["_request_json"] = parsed
            hop["request_body_status"] = "captured"
            hop["request_body_source"] = source
            hop["encoding"] = encoding
            hop["request_body_sha256"] = sha256(data)
        except Exception as exc:
            hop["request_body_status"] = str(exc) if isinstance(exc, EvidenceError) else type(exc).__name__

    def on_response(self, event):
        if self.active:
            self.ledger.received(event)

    def on_cache(self, event):
        hop = self.ledger.current(event["requestId"])
        if self.active and hop:
            hop["cache"]["requestServedFromCache"] = True

    def on_failed(self, event):
        hop = self.ledger.current(event["requestId"])
        if self.active and hop:
            hop["completion"] = "failed"
            hop["response_body_status"] = "loadingFailed"
            hop["failure"] = {k: event[k] for k in ("canceled", "blockedReason") if k in event}

    def on_finished(self, event):
        hop = self.ledger.current(event["requestId"])
        if self.active and hop:
            hop["completion"] = "finished"
            if self.candidate(hop) or (self.in_scope(hop) and hop["resource_type"] == "Script"):
                self.schedule(self.response_body(hop))

    async def response_body(self, hop):
        try:
            reply = await self.session.send("Network.getResponseBody", {"requestId": hop["request_id"]})
            data = decoded_body(reply)
            if self.ledger.current(hop["request_id"]) is not hop:
                raise EvidenceError("response_body_redirect_race")
            if hop["resource_type"] == "Script":
                self.asset_identity.append({"url": hop["url"], "sha256": sha256(data), "identity": "CDP_decoded_content"})
                return
            # CDP non-base64 bodies are already decoded Unicode strings.
            encoding = text_encoding(hop.get("response_headers", {"kept": {}})["kept"]) if reply.get("base64Encoded") else "utf-8"
            parsed = inspect_body(data, encoding)
            hop["_response_body"] = data
            hop["_response_json"] = parsed
            hop["response_body_status"] = "captured"
            hop["response_body_base64_encoded"] = reply.get("base64Encoded", False)
            hop["response_body_encoding"] = encoding
        except Exception as exc:
            hop["response_body_status"] = str(exc) if isinstance(exc, EvidenceError) else type(exc).__name__

    async def start(self, forced=False, buffer_mb=None):
        self.session.on("Network.requestWillBeSent", self.on_request)
        self.session.on("Network.responseReceived", self.on_response)
        self.session.on("Network.requestWillBeSentExtraInfo", lambda e: self.active and self.ledger.extra("request", e))
        self.session.on("Network.responseReceivedExtraInfo", lambda e: self.active and self.ledger.extra("response", e))
        self.session.on("Network.requestServedFromCache", self.on_cache)
        self.session.on("Network.loadingFinished", self.on_finished)
        self.session.on("Network.loadingFailed", self.on_failed)
        options = {} if not buffer_mb else {"maxTotalBufferSize": buffer_mb * 1024**2, "maxResourceBufferSize": buffer_mb * 1024**2}
        await self.session.send("Network.enable", options)
        if forced:
            await self.session.send("Network.setCacheDisabled", {"cacheDisabled": True})

    async def finish(self):
        # Allow queued completion/ExtraInfo events a bounded drain window.
        await asyncio.sleep(1)
        self.active = False
        pending = list(self.tasks)
        if pending:
            done, remaining = await asyncio.wait(pending, timeout=10)
            for task in remaining:
                task.cancel()
            if remaining:
                await asyncio.gather(*remaining, return_exceptions=True)
                self.event_errors.append("body_capture_timeout")
        self.ledger.correlate()

    def save(self, out):
        out = Path(out)
        index = []
        number = 0
        for chain in self.ledger.chains.values():
            if not any(h["resource_type"] in {"XHR", "Fetch"} for h in chain):
                continue
            for hop in chain:
                number += 1
                name = f"request-{number:04d}-hop-{hop['hop']}"
                meta = {k: v for k, v in hop.items() if not k.startswith("_") and k not in {"request_headers", "response_headers"}}
                meta["in_scope"] = self.in_scope(hop)
                index.append({"directory": name, **meta})
                folder = out / name
                folder.mkdir()
                write_json(folder / "request-meta.json", meta)
                write_json(folder / "headers.json", {"request": hop["request_headers"], "response": hop.get("response_headers", {"kept": {}, "excluded": []})})
                for kind, filename in (("request", "request.postdata.txt"), ("response", "response.body.txt")):
                    if f"_{kind}_body" in hop:
                        write_bytes(folder / filename, hop[f"_{kind}_body"])
                        write_json(folder / f"{kind}.json", hop[f"_{kind}_json"])
        write_json(out / "requests.json", index)
        return index
