"""Offline evidence, filtering, diff and anonymous replay primitives."""
from __future__ import annotations

import base64
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qsl, urlsplit

SENSITIVE = re.compile(r"authorization|cookie|token|secret|password|passwd|api[-_]?key|apikey|csrf|xsrf|session|credential", re.I)
VALUE_SECRET = re.compile(r"(?:Bearer\s+\S+|eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+|-----BEGIN .*PRIVATE KEY-----)", re.I)
SAFE_HEADERS = {
    "accept", "accept-language", "accept-encoding", "content-type", "content-length",
    "origin", "referer", "user-agent", "cache-control", "pragma", "date", "expires",
    "etag", "last-modified", "vary", "server", "age", "retry-after", "location",
    "access-control-allow-origin", "access-control-allow-methods", "access-control-allow-headers",
    "access-control-allow-credentials", "access-control-expose-headers", "content-encoding",
}
TRANSPORT_HEADERS = {"host", "content-length", "connection", "transfer-encoding", "accept-encoding", "cookie"}


class EvidenceError(ValueError):
    """Safe message, never includes captured values."""


def now():
    return datetime.now(timezone.utc).isoformat()


def sha256(data: bytes):
    return hashlib.sha256(data).hexdigest()


def reject_constant(_):
    raise EvidenceError("non_standard_json_number")


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise EvidenceError("duplicate_json_key")
        result[key] = value
    return result


def parse_json(text):
    return json.loads(text, parse_constant=reject_constant, object_pairs_hook=unique_object)


def read_json(path):
    return parse_json(Path(path).read_text(encoding="utf-8-sig"))


def check_sensitive(value):
    if isinstance(value, dict):
        for key, child in value.items():
            if SENSITIVE.search(str(key)):
                raise EvidenceError("sensitive_field_detected")
            check_sensitive(child)
    elif isinstance(value, list):
        for child in value:
            check_sensitive(child)
    elif isinstance(value, str):
        if VALUE_SECRET.search(value):
            raise EvidenceError("credential_pattern_detected")


def safe_url(value):
    parsed = urlsplit(value)
    if parsed.username or parsed.password or parsed.scheme not in {"https", "http"}:
        raise EvidenceError("unsafe_url")
    if VALUE_SECRET.search(value):
        raise EvidenceError("sensitive_url")
    for key, val in parse_qsl(parsed.query, keep_blank_values=True):
        if SENSITIVE.search(key):
            raise EvidenceError("sensitive_url_parameter")
        check_sensitive(val)
    # URL fragments may contain auth state and are not transmitted to the server.
    if parsed.fragment:
        raise EvidenceError("url_fragment_requires_review")
    return value


def filter_headers(headers, reviewed=()):
    kept, excluded = {}, []
    allowed = {h.lower() for h in reviewed}
    for name, value in headers.items():
        key = name.lower()
        reason = None
        if SENSITIVE.search(key):
            reason = "sensitive_header"
        elif key not in SAFE_HEADERS and key not in allowed and not key.startswith(("sec-ch-", "sec-fetch-", "x-ratelimit-")):
            reason = "unreviewed_header"
        else:
            try:
                check_sensitive(str(value))
                if key in {"referer", "origin", "location"} and str(value).startswith(("http://", "https://")):
                    safe_url(str(value))
            except EvidenceError:
                reason = "sensitive_value"
        if reason:
            excluded.append({"name": name, "reason": reason})
        else:
            kept[key] = str(value)
    return {"kept": kept, "excluded": excluded}


def write_json(path, value):
    with Path(path).open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write("\n")


def write_bytes(path, value):
    with Path(path).open("xb") as stream:
        stream.write(value)


def decoded_body(reply, field="body"):
    value = reply[field]
    if reply.get("base64Encoded", False):
        return base64.b64decode(value, validate=True)
    return value.encode("utf-8")


def text_encoding(headers):
    value = headers.get("content-type", "")
    match = re.search(r"charset\s*=\s*[\"']?([^;\s\"']+)", value, re.I)
    return match.group(1) if match else "utf-8"


def inspect_body(data: bytes, encoding="utf-8"):
    # JSON body only: unknown text formats require manual review before persistence.
    text = data.decode(encoding)
    parsed = parse_json(text)
    check_sensitive(parsed)
    return parsed


def freeze_snapshot(source, out):
    source, out = Path(source).resolve(), Path(out)
    data = source.read_bytes()
    parsed = parse_json(data.decode("utf-8-sig"))
    check_sensitive(parsed)
    metadata = parsed.get("metadata", {})
    identity = {
        "source_path": str(source), "frozen_file": "nexon.raw.json", "sha256": sha256(data),
        "collected_at": metadata.get("collected_at"), "frozen_at": now(),
        "character": metadata.get("character_name"),
        "data_dates": {k: v.get("date") for k, v in parsed.items() if isinstance(v, dict) and "date" in v},
        "error_sections": [k for k, v in parsed.items() if isinstance(v, dict) and v.get("error") is True],
        "same_time_as_scouter": "unverified",
    }
    out.mkdir(parents=True, exist_ok=False)
    write_bytes(out / "nexon.raw.json", data)
    write_json(out / "identity.json", identity)
    return identity


def verify_snapshot(bundle):
    bundle = Path(bundle)
    identity = read_json(bundle / "identity.json")
    data = (bundle / "nexon.raw.json").read_bytes()
    if sha256(data) != identity["sha256"]:
        raise EvidenceError("snapshot_hash_mismatch")
    return identity, data


def json_diff(before, after):
    from deepdiff import DeepDiff
    result = DeepDiff(
        before, after, ignore_order=False, zip_ordered_iterables=True,
        ignore_numeric_type_changes=False, ignore_string_type_changes=False,
        ignore_private_variables=False, threshold_to_diff_deeper=0, verbose_level=2,
    )
    return json.loads(result.to_json())


def replay(fixture, out, mode, header_names=(), transport=None):
    import httpx
    fixture, out = Path(fixture), Path(out)
    manifest = read_json(fixture / "request-meta.json")
    url = safe_url(manifest["url"])
    if urlsplit(url).scheme != "https" and transport is None:
        raise EvidenceError("replay_requires_https")
    if manifest.get("request_body_status") != "captured":
        raise EvidenceError("incomplete_request_body")
    captured = read_json(fixture / "headers.json")["request"]
    available = captured["kept"]
    # Conservative default; custom headers must be selected explicitly after review.
    selected = {"content-type", "accept", "origin", "referer"} | {h.lower() for h in header_names}
    if selected & TRANSPORT_HEADERS or any(SENSITIVE.search(h) for h in selected):
        raise EvidenceError("prohibited_replay_header")
    if any(h.lower() not in available for h in header_names):
        raise EvidenceError("selected_header_not_captured")
    headers = {k: v for k, v in available.items() if k in selected}
    filtered = filter_headers(headers, selected)
    if filtered["excluded"]:
        raise EvidenceError("unsafe_replay_headers")
    observed = (fixture / "request.postdata.txt").read_bytes()
    if sha256(observed) != manifest["request_body_sha256"]:
        raise EvidenceError("request_hash_mismatch")
    encoding = manifest.get("encoding", "utf-8")
    parsed = inspect_body(observed, encoding)
    saved = read_json(fixture / "request.json")
    if json_diff(parsed, saved):
        raise EvidenceError("parsed_request_mismatch")
    if mode == "observed":
        kwargs = {"content": observed.decode(encoding).encode(encoding)}
    elif mode == "json":
        if encoding.lower().replace("_", "-") not in {"utf-8", "utf8"}:
            raise EvidenceError("json_mode_requires_utf8_content_type")
        kwargs = {"json": saved}
    else:
        raise EvidenceError("invalid_replay_mode")
    out.mkdir(parents=True, exist_ok=False)
    report = {"mode": mode, "started_at": now(), "method": manifest["method"], "url": url,
              "request_headers": headers, "captured_headers_not_replayed": sorted(set(available) - set(headers)),
              "encoding": encoding, "trust_env": False, "follow_redirects": False,
              "authentication": "none", "timeout_seconds": 30, "assessment": "unclassified"}
    try:
        with httpx.Client(follow_redirects=False, timeout=30.0, trust_env=False, transport=transport) as client:
            response = client.request(manifest["method"], url, headers=headers, **kwargs)
        report["status"] = response.status_code
        report["response_headers"] = filter_headers(dict(response.headers))
        response_data = inspect_body(response.content, text_encoding(report["response_headers"]["kept"]))
        write_bytes(out / "response.body.txt", response.content)
        write_json(out / "response.json", response_data)
        report["body_status"] = "captured"
        if (fixture / "response.json").exists():
            difference = json_diff(read_json(fixture / "response.json"), response_data)
            write_json(out / "response-diff.json", difference)
            report["parsed_response_equal"] = not difference
            captured_body = fixture / "response.body.txt"
            report["body_bytes_equal"] = response.content == captured_body.read_bytes() if captured_body.exists() else None
    except Exception as exc:
        report["error"] = str(exc) if isinstance(exc, EvidenceError) else type(exc).__name__
        report["body_status"] = "not_saved"
    report["finished_at"] = now()
    write_json(out / "replay.json", report)
    return report
