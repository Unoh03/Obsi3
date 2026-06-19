#!/usr/bin/env python3
"""KISA Web Application semi-automatic checker.

v0 validated the framework pipeline:
profile -> checks -> request -> evidence -> report.
v2 adds the shared foundation for payload-based and state-changing checks
while keeping target-specific values in profiles, checks, and payload files.
"""

from __future__ import annotations

import argparse
import html
import json
import re
import ssl
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl, urlencode, urljoin, urlparse, urlsplit, urlunsplit
from urllib.error import HTTPError
from urllib.request import Request as UrlRequest
from urllib.request import urlopen


MODES = {
    "passive": 0,
    "safe-active": 1,
    "attack-active": 2,
    "state-changing": 3,
    "destructive-risk": 4,
}

VALID_STATUSES = {
    "ready",
    "vulnerable",
    "not_vulnerable",
    "not_applicable",
    "manual_required",
    "skipped_by_mode",
    "inconclusive",
    "error",
}

KNOWN_ACTIONS = {
    "inspect_transport",
    "http_methods",
    "path_probe",
    "inspect_cookies",
    "payload_probe",
    "manual_check",
}


class CheckerError(Exception):
    """Base checker exception."""


class ConfigError(CheckerError):
    """Invalid profile or check configuration."""


class RequestFailed(CheckerError):
    """HTTP request failed after evidence files were written."""

    def __init__(self, message: str, request_path: str, response_path: str) -> None:
        super().__init__(message)
        self.request_path = request_path
        self.response_path = response_path


def load_yaml(path: Path) -> dict[str, Any]:
    try:
        import yaml
    except ImportError as exc:
        try:
            return load_simple_yaml(path)
        except Exception as fallback_exc:
            raise ConfigError(
                "Missing dependency: PyYAML, and the built-in v0 YAML fallback "
                f"could not parse `{path}`: {fallback_exc}"
            ) from exc

    try:
        with path.open("r", encoding="utf-8") as handle:
            data = yaml.safe_load(handle)
    except FileNotFoundError as exc:
        raise ConfigError(f"File not found: {path}") from exc

    if not isinstance(data, dict):
        raise ConfigError(f"YAML root must be a mapping: {path}")
    return data


def load_simple_yaml(path: Path) -> dict[str, Any]:
    """Parse the limited YAML subset used by the v0 profile/check files.

    This fallback exists so v0 can be validated in a bare Python environment.
    Install PyYAML for broader YAML support.
    """

    try:
        raw_lines = path.read_text(encoding="utf-8").splitlines()
    except FileNotFoundError as exc:
        raise ConfigError(f"File not found: {path}") from exc

    lines: list[tuple[int, str]] = []
    for raw_line in raw_lines:
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        indent = len(raw_line) - len(raw_line.lstrip(" "))
        lines.append((indent, raw_line.strip()))

    if not lines:
        return {}

    def parse_block(index: int, indent: int) -> tuple[Any, int]:
        if index >= len(lines):
            return {}, index
        if lines[index][1].startswith("- "):
            return parse_list(index, indent)
        return parse_mapping(index, indent)

    def parse_list(index: int, indent: int) -> tuple[list[Any], int]:
        values: list[Any] = []
        while index < len(lines):
            line_indent, content = lines[index]
            if line_indent < indent:
                break
            if line_indent != indent or not content.startswith("- "):
                break
            item = content[2:].strip()
            if not item:
                nested, index = parse_block(index + 1, indent + 2)
                values.append(nested)
            elif ":" in item and not item.startswith(("'", '"')):
                key, raw_value = item.split(":", 1)
                item_map: dict[str, Any] = {}
                if raw_value.strip():
                    item_map[key.strip()] = parse_scalar(raw_value.strip())
                    index += 1
                else:
                    nested, index = parse_block(index + 1, indent + 2)
                    item_map[key.strip()] = nested
                if index < len(lines) and lines[index][0] > indent:
                    nested, index = parse_mapping(index, lines[index][0])
                    item_map.update(nested)
                values.append(item_map)
            else:
                values.append(parse_scalar(item))
                index += 1
        return values, index

    def parse_mapping(index: int, indent: int) -> tuple[dict[str, Any], int]:
        values: dict[str, Any] = {}
        while index < len(lines):
            line_indent, content = lines[index]
            if line_indent < indent:
                break
            if line_indent != indent or content.startswith("- "):
                break
            if ":" not in content:
                raise ConfigError(f"Invalid YAML line: {content}")
            key, raw_value = content.split(":", 1)
            key = key.strip()
            raw_value = raw_value.strip()
            if raw_value:
                values[key] = parse_scalar(raw_value)
                index += 1
            else:
                nested, index = parse_block(index + 1, indent + 2)
                values[key] = nested
        return values, index

    result, end_index = parse_block(0, lines[0][0])
    if end_index != len(lines):
        raise ConfigError("YAML fallback did not consume all lines")
    if not isinstance(result, dict):
        raise ConfigError("YAML root must be a mapping")
    return result


def parse_scalar(value: str) -> Any:
    if value in {"true", "True"}:
        return True
    if value in {"false", "False"}:
        return False
    if value in {"null", "Null", "~"}:
        return None
    if (value.startswith('"') and value.endswith('"')) or (
        value.startswith("'") and value.endswith("'")
    ):
        return value[1:-1]
    if re.fullmatch(r"-?\d+", value):
        return int(value)
    return html.unescape(value)


def load_requests_module():
    try:
        import requests
    except ImportError:
        return None
    return requests


@dataclass
class SimpleResponse:
    status_code: int
    reason: str
    headers: dict[str, str]
    text: str


def resolve_path(base_dir: Path, value: str) -> Path:
    candidate = Path(value)
    if candidate.is_absolute():
        return candidate
    cwd_candidate = Path.cwd() / candidate
    if cwd_candidate.exists():
        return cwd_candidate
    return base_dir / candidate


def mode_allows(current_mode: str, required_mode: str) -> bool:
    if current_mode not in MODES:
        raise ConfigError(f"Unknown mode: {current_mode}")
    if required_mode not in MODES:
        raise ConfigError(f"Unknown required mode: {required_mode}")
    return MODES[current_mode] >= MODES[required_mode]


def make_url(base_url: str, path: str) -> str:
    return urljoin(base_url.rstrip("/") + "/", path.lstrip("/"))


def add_query_params(url: str, params: dict[str, Any]) -> str:
    if not params:
        return url
    parts = urlsplit(url)
    query_items = parse_qsl(parts.query, keep_blank_values=True)
    for key, value in params.items():
        query_items.append((str(key), str(value)))
    return urlunsplit(
        (parts.scheme, parts.netloc, parts.path, urlencode(query_items), parts.fragment)
    )


def require_allowed_target(profile: dict[str, Any]) -> None:
    base_url = str(profile.get("base_url", "")).strip()
    if not base_url:
        raise ConfigError("profile.base_url is required")

    parsed = urlparse(base_url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ConfigError("profile.base_url must be an http(s) URL")

    allowlist = profile.get("target_allowlist")
    if not isinstance(allowlist, list) or not allowlist:
        raise ConfigError("profile.target_allowlist must be a non-empty list")

    allowed = {str(item).strip().lower() for item in allowlist}
    hostname = parsed.hostname.lower()
    if hostname not in allowed:
        raise ConfigError(
            f"Target host `{hostname}` is not in profile.target_allowlist"
        )


def get_route(profile: dict[str, Any], route_name: str) -> dict[str, Any]:
    routes = profile.get("routes", {})
    if not isinstance(routes, dict):
        raise ConfigError("profile.routes must be a mapping")
    route = routes.get(route_name)
    if not isinstance(route, dict):
        raise ConfigError(f"Unknown route in profile: {route_name}")
    return route


def route_params(route: dict[str, Any], key: str) -> dict[str, Any]:
    values = route.get(key, {})
    if values is None:
        return {}
    if not isinstance(values, dict):
        raise ConfigError(f"route.{key} must be a mapping")
    return dict(values)


def find_form_actions(html: str) -> list[str]:
    # Lightweight v0 extraction; no BeautifulSoup dependency in v0.
    pattern = re.compile(
        r"<form\b[^>]*\baction\s*=\s*(['\"])(.*?)\1",
        re.IGNORECASE | re.DOTALL,
    )
    return [match.group(2).strip() for match in pattern.finditer(html)]


def list_step_routes(step: dict[str, Any], key: str = "routes") -> list[str]:
    route_names = step.get(key, [])
    if not isinstance(route_names, list) or not route_names:
        raise ConfigError(f"{step.get('action', 'step')}.{key} must be a non-empty list")
    return [str(route_name) for route_name in route_names]


def int_set(values: Any, default: list[int] | None = None) -> set[int]:
    if values is None:
        values = default or []
    if not isinstance(values, list):
        raise ConfigError("status lists must be YAML lists")
    return {int(value) for value in values}


def str_list(values: Any, default: list[str] | None = None) -> list[str]:
    if values is None:
        return list(default or [])
    if not isinstance(values, list):
        raise ConfigError("pattern lists must be YAML lists")
    return [str(value) for value in values]


def find_regex_matches(text: str, patterns: list[str]) -> list[str]:
    matches: list[str] = []
    for pattern in patterns:
        try:
            if re.search(pattern, text, re.IGNORECASE | re.MULTILINE):
                matches.append(pattern)
        except re.error as exc:
            raise ConfigError(f"Invalid regex pattern `{pattern}`: {exc}") from exc
    return matches


def header_text(response: Any) -> str:
    return "\n".join(f"{key}: {value}" for key, value in response.headers.items())


def set_cookie_values(response: Any) -> list[str]:
    values = [
        str(value)
        for key, value in response.headers.items()
        if str(key).lower() == "set-cookie"
    ]
    if values:
        return values
    getter = getattr(response.headers, "get", None)
    if getter:
        value = getter("Set-Cookie")
        if value:
            return [str(value)]
    return []


def resolve_checker_path(check: dict[str, Any], value: str) -> Path:
    candidate = Path(value)
    if candidate.is_absolute():
        return candidate
    source = Path(str(check.get("_source", "")))
    if source:
        return source.resolve().parent.parent / candidate
    return Path.cwd() / candidate


def load_payload_values(check: dict[str, Any], step: dict[str, Any]) -> list[str]:
    payloads: list[str] = []
    inline_payloads = step.get("payloads", [])
    if inline_payloads:
        if not isinstance(inline_payloads, list):
            raise ConfigError("payload_probe.payloads must be a list")
        payloads.extend(str(value) for value in inline_payloads)

    payload_file = step.get("payloads_file")
    if payload_file:
        payload_path = resolve_checker_path(check, str(payload_file))
        data = load_yaml(payload_path)
        group_name = str(step.get("payload_group", "default"))
        groups = data.get("groups", {})
        if not isinstance(groups, dict):
            raise ConfigError(f"payload file groups must be a mapping: {payload_path}")
        group = groups.get(group_name)
        if not isinstance(group, list) or not group:
            raise ConfigError(
                f"payload group `{group_name}` must be a non-empty list: {payload_path}"
            )
        payloads.extend(str(value) for value in group)

    if not payloads:
        raise ConfigError("payload_probe requires inline payloads or payloads_file")
    return payloads


def apply_profile_session_to_requests(session: Any, profile: dict[str, Any]) -> None:
    session_cfg = profile.get("session", {})
    if not isinstance(session_cfg, dict):
        raise ConfigError("profile.session must be a mapping when provided")

    cookies = session_cfg.get("cookies", {})
    if cookies:
        if not isinstance(cookies, dict):
            raise ConfigError("profile.session.cookies must be a mapping")
        for key, value in cookies.items():
            session.cookies.set(str(key), str(value))

    headers = session_cfg.get("headers", {})
    if headers:
        if not isinstance(headers, dict):
            raise ConfigError("profile.session.headers must be a mapping")
        session.headers.update({str(key): str(value) for key, value in headers.items()})


def profile_session_headers(profile: dict[str, Any]) -> dict[str, str]:
    session_cfg = profile.get("session", {})
    if not isinstance(session_cfg, dict):
        raise ConfigError("profile.session must be a mapping when provided")
    headers: dict[str, str] = {}
    session_headers = session_cfg.get("headers", {})
    if session_headers:
        if not isinstance(session_headers, dict):
            raise ConfigError("profile.session.headers must be a mapping")
        headers.update({str(key): str(value) for key, value in session_headers.items()})
    cookies = session_cfg.get("cookies", {})
    if cookies:
        if not isinstance(cookies, dict):
            raise ConfigError("profile.session.cookies must be a mapping")
        headers["Cookie"] = "; ".join(
            f"{key}={value}" for key, value in cookies.items()
        )
    return headers


def validate_check_steps(profile: dict[str, Any], check: dict[str, Any]) -> None:
    steps = check.get("steps", [])
    if not isinstance(steps, list) or not steps:
        raise ConfigError(f"check {check.get('id', 'unknown')}: steps must be a non-empty list")

    for step in steps:
        if not isinstance(step, dict):
            raise ConfigError(f"check {check.get('id', 'unknown')}: each step must be a mapping")
        action = step.get("action")
        if action not in KNOWN_ACTIONS:
            raise ConfigError(f"check {check.get('id', 'unknown')}: unknown action `{action}`")
        if action in {"inspect_transport", "path_probe", "inspect_cookies", "payload_probe"}:
            for route_name in list_step_routes(step):
                get_route(profile, route_name)
            if action == "payload_probe":
                load_payload_values(check, step)
        elif action == "http_methods":
            route_name = str(step.get("route", "method_probe"))
            if not isinstance(profile.get(route_name), dict):
                raise ConfigError(f"profile.{route_name} must be a mapping")
        elif action == "manual_check":
            route_names = step.get("routes", [])
            if route_names:
                for route_name in list_step_routes(step):
                    get_route(profile, route_name)
            if step.get("payloads") or step.get("payloads_file"):
                load_payload_values(check, step)


@dataclass
class EvidenceItem:
    label: str
    path: str


@dataclass
class CheckResult:
    id: str
    name: str
    status: str
    required_mode: str
    evidence_dir: str
    summary: str = ""
    findings: list[str] = field(default_factory=list)
    evidence: list[EvidenceItem] = field(default_factory=list)

    def to_json(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "status": self.status,
            "required_mode": self.required_mode,
            "evidence_dir": self.evidence_dir,
            "summary": self.summary,
            "findings": self.findings,
            "evidence": [item.__dict__ for item in self.evidence],
        }


class CheckerRunner:
    def __init__(
        self,
        profile: dict[str, Any],
        checks: list[dict[str, Any]],
        mode: str,
        output_root: Path,
        validate_only: bool = False,
        confirm_state_changing: bool = False,
        confirm_destructive_risk: bool = False,
    ) -> None:
        self.profile = profile
        self.checks = checks
        self.mode = mode
        self.output_root = output_root
        self.validate_only = validate_only
        self.confirm_state_changing = confirm_state_changing
        self.confirm_destructive_risk = confirm_destructive_risk
        self.base_url = str(profile["base_url"]).rstrip("/")
        self.timeout = int(profile.get("timeout_seconds", 5))
        self.verify_tls = bool(profile.get("verify_tls", True))
        self.run_id = datetime.now().strftime("%Y%m%d-%H%M%S")
        self.run_dir = output_root / self.run_id
        self.log_lines: list[str] = []

        self.requests = None
        if not validate_only:
            self.requests = load_requests_module()
            self.session = self.requests.Session() if self.requests else None
            if self.session is not None:
                apply_profile_session_to_requests(self.session, self.profile)
        else:
            self.session = None

    def log(self, message: str) -> None:
        timestamp = datetime.now().isoformat(timespec="seconds")
        self.log_lines.append(f"[{timestamp}] {message}")

    def run(self) -> list[CheckResult]:
        self.enforce_mode_confirmation()
        self.run_dir.mkdir(parents=True, exist_ok=True)
        self.log(f"run_id={self.run_id}")
        self.log(f"profile={self.profile.get('name', 'unnamed')}")
        self.log(f"mode={self.mode}")
        self.log(f"validate_only={self.validate_only}")

        results: list[CheckResult] = []
        for check in self.checks:
            result = self.run_check(check)
            results.append(result)

        self.write_outputs(results)
        return results

    def enforce_mode_confirmation(self) -> None:
        if self.validate_only:
            return
        if mode_allows(self.mode, "destructive-risk") and not self.confirm_destructive_risk:
            raise ConfigError(
                "`destructive-risk` mode requires --confirm-destructive-risk"
            )
        if mode_allows(self.mode, "state-changing") and not self.confirm_state_changing:
            raise ConfigError(
                "`state-changing` mode requires --confirm-state-changing"
            )

    def run_check(self, check: dict[str, Any]) -> CheckResult:
        check_id = str(check.get("id", "unknown"))
        name = str(check.get("name", check_id))
        required_mode = str(check.get("required_mode", "passive"))
        check_dir = self.run_dir / f"{check_id}_{slugify(name)}"
        check_dir.mkdir(parents=True, exist_ok=True)
        validate_check_steps(self.profile, check)

        if not mode_allows(self.mode, required_mode):
            self.log(f"{check_id}: skipped by mode")
            return CheckResult(
                id=check_id,
                name=name,
                status="skipped_by_mode",
                required_mode=required_mode,
                evidence_dir=str(check_dir.relative_to(self.run_dir)),
                summary=f"Requires `{required_mode}`, current mode is `{self.mode}`.",
            )

        if self.validate_only:
            self.log(f"{check_id}: validate-only ready")
            return CheckResult(
                id=check_id,
                name=name,
                status="ready",
                required_mode=required_mode,
                evidence_dir=str(check_dir.relative_to(self.run_dir)),
                summary="Configuration is ready to run in validate-only mode.",
            )

        action_results: list[CheckResult] = []
        for step in check.get("steps", []):
            if not isinstance(step, dict):
                raise ConfigError(f"check {check_id}: each step must be a mapping")
            action = step.get("action")
            if action == "inspect_transport":
                action_results.append(self.inspect_transport(check, step, check_dir))
            elif action == "http_methods":
                action_results.append(self.check_http_methods(check, step, check_dir))
            elif action == "path_probe":
                action_results.append(self.path_probe(check, step, check_dir))
            elif action == "inspect_cookies":
                action_results.append(self.inspect_cookies(check, step, check_dir))
            elif action == "payload_probe":
                action_results.append(self.payload_probe(check, step, check_dir))
            elif action == "manual_check":
                action_results.append(self.manual_check(check, step, check_dir))
            else:
                raise ConfigError(f"check {check_id}: unknown action `{action}`")

        return merge_step_results(check_id, name, required_mode, check_dir, action_results)

    def inspect_transport(
        self, check: dict[str, Any], step: dict[str, Any], check_dir: Path
    ) -> CheckResult:
        findings: list[str] = []
        evidence: list[EvidenceItem] = []
        statuses: list[str] = []

        parsed_base = urlparse(self.base_url)
        if parsed_base.scheme == "http":
            statuses.append("vulnerable")
            findings.append("profile.base_url uses HTTP, so sensitive traffic can be plaintext.")
        elif parsed_base.scheme == "https":
            statuses.append("not_vulnerable")
            findings.append("profile.base_url uses HTTPS.")
        else:
            statuses.append("inconclusive")
            findings.append(f"Unsupported scheme: {parsed_base.scheme}")

        route_names = step.get("routes", [])
        if not isinstance(route_names, list):
            raise ConfigError("inspect_transport.routes must be a list")

        for index, route_name in enumerate(route_names, start=1):
            route = get_route(self.profile, str(route_name))
            method = str(route.get("method", "GET")).upper()
            if method != "GET":
                findings.append(f"Route `{route_name}` is not GET; skipped form inspection.")
                statuses.append("manual_required")
                continue

            url = make_url(self.base_url, str(route.get("path", "/")))
            try:
                response, request_path, response_path = self.send_request(
                    method="GET",
                    url=url,
                    step_id=f"transport_{route_name}_{index}",
                    check_dir=check_dir,
                )
                evidence.append(EvidenceItem("request", request_path))
                evidence.append(EvidenceItem("response", response_path))

                actions = find_form_actions(response.text)
                if actions:
                    for action in actions:
                        if action.startswith("http://"):
                            statuses.append("vulnerable")
                            findings.append(
                                f"Route `{route_name}` has plaintext form action: {action}"
                            )
                        else:
                            statuses.append("not_vulnerable")
                            findings.append(
                                f"Route `{route_name}` form action observed: {action}"
                            )
                else:
                    statuses.append("inconclusive")
                    findings.append(f"Route `{route_name}` returned no form action.")
            except RequestFailed as exc:
                evidence.append(EvidenceItem("failed request", exc.request_path))
                evidence.append(EvidenceItem("error response", exc.response_path))
                statuses.append("error")
                findings.append(f"Route `{route_name}` request failed: {exc}")
                self.log(f"{check.get('id')}: route `{route_name}` failed: {exc}")
            except Exception as exc:  # Keep the run alive for evidence/report output.
                statuses.append("error")
                findings.append(f"Route `{route_name}` request failed: {exc}")
                self.log(f"{check.get('id')}: route `{route_name}` failed: {exc}")

        status = reduce_status(statuses)
        return CheckResult(
            id=str(check["id"]),
            name=str(check["name"]),
            status=status,
            required_mode=str(check.get("required_mode", "passive")),
            evidence_dir=str(check_dir.relative_to(self.run_dir)),
            summary="Transport scheme and form actions inspected.",
            findings=findings,
            evidence=evidence,
        )

    def path_probe(
        self, check: dict[str, Any], step: dict[str, Any], check_dir: Path
    ) -> CheckResult:
        findings: list[str] = []
        evidence: list[EvidenceItem] = []
        statuses: list[str] = []

        route_names = list_step_routes(step)
        vulnerable_statuses = int_set(step.get("vulnerable_statuses"), [200])
        not_vulnerable_statuses = int_set(step.get("not_vulnerable_statuses"), [403, 404])
        vulnerable_body_patterns = str_list(step.get("vulnerable_body_patterns"))
        vulnerable_header_patterns = str_list(step.get("vulnerable_header_patterns"))
        status_only_vulnerable = bool(step.get("status_only_vulnerable", False))
        no_match_status = str(step.get("no_match_status", "inconclusive"))
        if no_match_status not in VALID_STATUSES:
            raise ConfigError(f"Invalid no_match_status: {no_match_status}")

        for index, route_name in enumerate(route_names, start=1):
            route = get_route(self.profile, route_name)
            method = str(route.get("method", "GET")).upper()
            if method != "GET":
                statuses.append("manual_required")
                findings.append(f"Route `{route_name}` uses `{method}`; path_probe only sends GET.")
                continue

            url = make_url(self.base_url, str(route.get("path", "/")))
            try:
                response, request_path, response_path = self.send_request(
                    method="GET",
                    url=url,
                    step_id=f"{slugify(str(step.get('id', 'path_probe')))}_{route_name}_{index}",
                    check_dir=check_dir,
                )
                evidence.append(EvidenceItem(f"{route_name} request", request_path))
                evidence.append(EvidenceItem(f"{route_name} response", response_path))

                body_matches = find_regex_matches(response.text, vulnerable_body_patterns)
                header_matches = find_regex_matches(header_text(response), vulnerable_header_patterns)
                matched = body_matches + header_matches

                if response.status_code in vulnerable_statuses and (
                    status_only_vulnerable or matched
                ):
                    statuses.append("vulnerable")
                    if matched:
                        findings.append(
                            f"Route `{route_name}` returned {response.status_code} and matched: {', '.join(matched)}"
                        )
                    else:
                        findings.append(
                            f"Route `{route_name}` returned {response.status_code}; status is configured as vulnerable."
                        )
                elif response.status_code in not_vulnerable_statuses:
                    statuses.append("not_vulnerable")
                    findings.append(
                        f"Route `{route_name}` returned {response.status_code}; treated as blocked/not found."
                    )
                elif response.status_code in vulnerable_statuses:
                    statuses.append(no_match_status)
                    findings.append(
                        f"Route `{route_name}` returned {response.status_code}, but configured exposure patterns did not match."
                    )
                else:
                    statuses.append("inconclusive")
                    findings.append(
                        f"Route `{route_name}` returned {response.status_code}; manual review required."
                    )
            except RequestFailed as exc:
                evidence.append(EvidenceItem(f"{route_name} failed request", exc.request_path))
                evidence.append(EvidenceItem(f"{route_name} error response", exc.response_path))
                statuses.append("error")
                findings.append(f"Route `{route_name}` request failed: {exc}")
                self.log(f"{check.get('id')}: route `{route_name}` failed: {exc}")

        return CheckResult(
            id=str(check["id"]),
            name=str(check["name"]),
            status=reduce_status(statuses),
            required_mode=str(check.get("required_mode", "passive")),
            evidence_dir=str(check_dir.relative_to(self.run_dir)),
            summary=str(step.get("summary", "Configured routes probed for status and exposure patterns.")),
            findings=findings,
            evidence=evidence,
        )

    def inspect_cookies(
        self, check: dict[str, Any], step: dict[str, Any], check_dir: Path
    ) -> CheckResult:
        findings: list[str] = []
        evidence: list[EvidenceItem] = []
        statuses: list[str] = []

        route_names = list_step_routes(step)
        required_flags = {flag.lower() for flag in str_list(step.get("required_flags"))}
        session_patterns = str_list(
            step.get("session_cookie_patterns"),
            ["phpsessid", "session"],
        )
        base_scheme = urlparse(self.base_url).scheme

        for index, route_name in enumerate(route_names, start=1):
            route = get_route(self.profile, route_name)
            method = str(route.get("method", "GET")).upper()
            if method != "GET":
                statuses.append("manual_required")
                findings.append(f"Route `{route_name}` uses `{method}`; inspect_cookies only sends GET.")
                continue

            url = make_url(self.base_url, str(route.get("path", "/")))
            try:
                response, request_path, response_path = self.send_request(
                    method="GET",
                    url=url,
                    step_id=f"cookie_{route_name}_{index}",
                    check_dir=check_dir,
                )
                evidence.append(EvidenceItem(f"{route_name} request", request_path))
                evidence.append(EvidenceItem(f"{route_name} response", response_path))

                cookies = set_cookie_values(response)
                if not cookies:
                    statuses.append("inconclusive")
                    findings.append(f"Route `{route_name}` returned no Set-Cookie header.")
                    continue

                route_had_session_cookie = False
                for cookie in cookies:
                    lower_cookie = cookie.lower()
                    if session_patterns and not any(
                        re.search(pattern, lower_cookie, re.IGNORECASE)
                        for pattern in session_patterns
                    ):
                        findings.append(
                            f"Route `{route_name}` Set-Cookie observed but does not look session-related: {cookie.split(';', 1)[0]}"
                        )
                        continue

                    route_had_session_cookie = True
                    missing: list[str] = []
                    if "httponly" in required_flags and "httponly" not in lower_cookie:
                        missing.append("HttpOnly")
                    if "samesite" in required_flags and "samesite=" not in lower_cookie:
                        missing.append("SameSite")
                    if "secure" in required_flags and "secure" not in lower_cookie:
                        missing.append("Secure")
                    if (
                        "secure_when_https" in required_flags
                        and base_scheme == "https"
                        and "secure" not in lower_cookie
                    ):
                        missing.append("Secure")

                    if missing:
                        statuses.append("vulnerable")
                        findings.append(
                            f"Route `{route_name}` session cookie missing flags: {', '.join(sorted(set(missing)))}"
                        )
                    else:
                        statuses.append("not_vulnerable")
                        findings.append(
                            f"Route `{route_name}` session cookie includes required flags."
                        )

                if not route_had_session_cookie:
                    statuses.append("inconclusive")
                    findings.append(
                        f"Route `{route_name}` Set-Cookie headers were not matched as session cookies."
                    )
            except RequestFailed as exc:
                evidence.append(EvidenceItem(f"{route_name} failed request", exc.request_path))
                evidence.append(EvidenceItem(f"{route_name} error response", exc.response_path))
                statuses.append("error")
                findings.append(f"Route `{route_name}` request failed: {exc}")
                self.log(f"{check.get('id')}: route `{route_name}` failed: {exc}")

        return CheckResult(
            id=str(check["id"]),
            name=str(check["name"]),
            status=reduce_status(statuses),
            required_mode=str(check.get("required_mode", "passive")),
            evidence_dir=str(check_dir.relative_to(self.run_dir)),
            summary=str(step.get("summary", "Session cookie flags inspected.")),
            findings=findings,
            evidence=evidence,
        )

    def payload_probe(
        self, check: dict[str, Any], step: dict[str, Any], check_dir: Path
    ) -> CheckResult:
        findings: list[str] = []
        evidence: list[EvidenceItem] = []
        statuses: list[str] = []

        route_names = list_step_routes(step)
        payloads = load_payload_values(check, step)
        parameter = str(step.get("parameter", "")).strip()
        if not parameter:
            raise ConfigError("payload_probe.parameter is required")

        baseline_value = str(step.get("baseline_value", "kisa-baseline"))
        vulnerable_statuses = int_set(step.get("vulnerable_statuses"), [500])
        vulnerable_body_patterns = str_list(step.get("vulnerable_body_patterns"))
        vulnerable_header_patterns = str_list(step.get("vulnerable_header_patterns"))
        not_vulnerable_statuses = int_set(step.get("not_vulnerable_statuses"), [])
        not_vulnerable_body_patterns = str_list(step.get("not_vulnerable_body_patterns"))
        not_vulnerable_header_patterns = str_list(step.get("not_vulnerable_header_patterns"))
        no_match_status = str(step.get("no_match_status", "inconclusive"))
        if no_match_status not in VALID_STATUSES:
            raise ConfigError(f"Invalid no_match_status: {no_match_status}")

        for route_index, route_name in enumerate(route_names, start=1):
            route = get_route(self.profile, route_name)
            method = str(route.get("method", "GET")).upper()
            if method not in {"GET", "POST"}:
                statuses.append("manual_required")
                findings.append(
                    f"Route `{route_name}` uses `{method}`; payload_probe supports GET/POST only."
                )
                continue

            base_path = str(route.get("path", "/"))
            base_url = make_url(self.base_url, base_path)
            base_params = route_params(route, "params")
            base_data = route_params(route, "data")

            try:
                request_url, body, headers = self.build_payload_request(
                    method,
                    base_url,
                    base_params,
                    base_data,
                    parameter,
                    baseline_value,
                )
                response, request_path, response_path = self.send_request(
                    method=method,
                    url=request_url,
                    step_id=f"payload_{route_name}_{route_index}_baseline",
                    check_dir=check_dir,
                    body=body,
                    headers=headers,
                )
                evidence.append(EvidenceItem(f"{route_name} baseline request", request_path))
                evidence.append(EvidenceItem(f"{route_name} baseline response", response_path))
                findings.append(
                    f"Route `{route_name}` baseline returned {response.status_code}."
                )
                baseline_body_matches = find_regex_matches(
                    response.text, vulnerable_body_patterns
                )
                baseline_header_matches = find_regex_matches(
                    header_text(response), vulnerable_header_patterns
                )
                baseline_matched = baseline_body_matches + baseline_header_matches
                if response.status_code in vulnerable_statuses or baseline_matched:
                    statuses.append("inconclusive")
                    reason = f"status {response.status_code}"
                    if baseline_matched:
                        reason += f", matched: {', '.join(baseline_matched)}"
                    findings.append(
                        f"Route `{route_name}` baseline already matches exposure indicators ({reason}); payload comparison is not reliable."
                    )
                    continue
            except RequestFailed as exc:
                evidence.append(EvidenceItem(f"{route_name} baseline failed request", exc.request_path))
                evidence.append(EvidenceItem(f"{route_name} baseline error response", exc.response_path))
                statuses.append("error")
                findings.append(f"Route `{route_name}` baseline request failed: {exc}")
                continue

            for payload_index, payload in enumerate(payloads, start=1):
                try:
                    request_url, body, headers = self.build_payload_request(
                        method,
                        base_url,
                        base_params,
                        base_data,
                        parameter,
                        payload,
                    )
                    response, request_path, response_path = self.send_request(
                        method=method,
                        url=request_url,
                        step_id=f"payload_{route_name}_{route_index}_{payload_index}",
                        check_dir=check_dir,
                        body=body,
                        headers=headers,
                    )
                    evidence.append(EvidenceItem(f"{route_name} payload request", request_path))
                    evidence.append(EvidenceItem(f"{route_name} payload response", response_path))

                    body_matches = find_regex_matches(response.text, vulnerable_body_patterns)
                    header_matches = find_regex_matches(header_text(response), vulnerable_header_patterns)
                    matched = body_matches + header_matches
                    if response.status_code in vulnerable_statuses or matched:
                        statuses.append("vulnerable")
                        reason = f"status {response.status_code}"
                        if matched:
                            reason += f", matched: {', '.join(matched)}"
                        findings.append(
                            f"Route `{route_name}` payload #{payload_index} indicates possible exposure: {reason}."
                        )
                    else:
                        not_vulnerable_body_matches = find_regex_matches(
                            response.text, not_vulnerable_body_patterns
                        )
                        not_vulnerable_header_matches = find_regex_matches(
                            header_text(response), not_vulnerable_header_patterns
                        )
                        not_vulnerable_matched = (
                            not_vulnerable_body_matches + not_vulnerable_header_matches
                        )
                        if response.status_code in not_vulnerable_statuses or not_vulnerable_matched:
                            statuses.append("not_vulnerable")
                            reason = f"status {response.status_code}"
                            if not_vulnerable_matched:
                                reason += f", matched: {', '.join(not_vulnerable_matched)}"
                            findings.append(
                                f"Route `{route_name}` payload #{payload_index} indicates configured blocking evidence: {reason}."
                            )
                        else:
                            statuses.append(no_match_status)
                            findings.append(
                                f"Route `{route_name}` payload #{payload_index} returned {response.status_code}; no configured exposure or blocking pattern matched."
                            )
                except RequestFailed as exc:
                    evidence.append(EvidenceItem(f"{route_name} payload failed request", exc.request_path))
                    evidence.append(EvidenceItem(f"{route_name} payload error response", exc.response_path))
                    statuses.append("error")
                    findings.append(f"Route `{route_name}` payload request failed: {exc}")

        return CheckResult(
            id=str(check["id"]),
            name=str(check["name"]),
            status=reduce_status(statuses),
            required_mode=str(check.get("required_mode", "attack-active")),
            evidence_dir=str(check_dir.relative_to(self.run_dir)),
            summary=str(step.get("summary", "Payload probes executed and compared with configured rules.")),
            findings=findings,
            evidence=evidence,
        )

    def manual_check(
        self, check: dict[str, Any], step: dict[str, Any], check_dir: Path
    ) -> CheckResult:
        findings: list[str] = []

        route_names = step.get("routes", [])
        if route_names:
            for route_name in list_step_routes(step):
                route = get_route(self.profile, route_name)
                method = str(route.get("method", "GET")).upper()
                path = str(route.get("path", "/"))
                findings.append(
                    f"Manual route candidate `{route_name}`: {method} {path}"
                )

        if step.get("payloads") or step.get("payloads_file"):
            payload_count = len(load_payload_values(check, step))
            findings.append(f"Manual payload candidates loaded: {payload_count}.")

        for note in str_list(step.get("notes")):
            findings.append(note)

        status = str(step.get("status", "manual_required"))
        if status not in VALID_STATUSES:
            raise ConfigError(f"Invalid manual_check.status: {status}")

        return CheckResult(
            id=str(check["id"]),
            name=str(check["name"]),
            status=status,
            required_mode=str(check.get("required_mode", "state-changing")),
            evidence_dir=str(check_dir.relative_to(self.run_dir)),
            summary=str(
                step.get(
                    "summary",
                    "Manual scaffold only. No HTTP request was sent by this step.",
                )
            ),
            findings=findings,
            evidence=[],
        )

    def build_payload_request(
        self,
        method: str,
        base_url: str,
        base_params: dict[str, Any],
        base_data: dict[str, Any],
        parameter: str,
        value: str,
    ) -> tuple[str, str | None, dict[str, str]]:
        headers: dict[str, str] = {}
        if method == "GET":
            params = dict(base_params)
            params[parameter] = value
            return add_query_params(base_url, params), None, headers

        data = dict(base_data)
        data[parameter] = value
        headers["Content-Type"] = "application/x-www-form-urlencoded"
        return add_query_params(base_url, base_params), urlencode(data), headers

    def check_http_methods(
        self, check: dict[str, Any], step: dict[str, Any], check_dir: Path
    ) -> CheckResult:
        findings: list[str] = []
        evidence: list[EvidenceItem] = []
        statuses: list[str] = []

        route_name = str(step.get("route", "method_probe"))
        probe = self.profile.get(route_name)
        if not isinstance(probe, dict):
            raise ConfigError(f"profile.{route_name} must be a mapping")

        path = str(probe.get("path", "/"))
        body = str(probe.get("body", "kisa-webapp-checker-v1"))
        url = make_url(self.base_url, path)

        methods = step.get("methods", [])
        if not isinstance(methods, list) or not methods:
            raise ConfigError("http_methods.methods must be a non-empty list")

        blocked_statuses = set(int(v) for v in step.get("blocked_statuses", [403, 405, 501]))
        vulnerable_statuses = set(int(v) for v in step.get("vulnerable_statuses", [200, 201, 202, 204]))
        risky_methods = {str(v).upper() for v in step.get("risky_methods", ["TRACE", "PUT", "DELETE", "CONNECT"])}

        for index, raw_method in enumerate(methods, start=1):
            method = str(raw_method).upper()
            request_body = body if method == "PUT" else None
            try:
                response, request_path, response_path = self.send_request(
                    method=method,
                    url=url,
                    step_id=f"method_{method.lower()}_{index}",
                    check_dir=check_dir,
                    body=request_body,
                )
                evidence.append(EvidenceItem(f"{method} request", request_path))
                evidence.append(EvidenceItem(f"{method} response", response_path))

                if method == "OPTIONS":
                    allow_header = response.headers.get("Allow", "")
                    exposed = sorted(risky_methods.intersection(parse_allow_header(allow_header)))
                    if exposed:
                        statuses.append("vulnerable")
                        findings.append(
                            f"OPTIONS exposes risky methods: {', '.join(exposed)}"
                        )
                    else:
                        statuses.append("not_vulnerable")
                        findings.append(
                            f"OPTIONS allowed methods: {allow_header or '(empty)'}"
                        )
                    continue

                if method in risky_methods and response.status_code in vulnerable_statuses:
                    statuses.append("vulnerable")
                    findings.append(
                        f"{method} returned {response.status_code}; risky method may be allowed."
                    )
                elif response.status_code in blocked_statuses:
                    statuses.append("not_vulnerable")
                    findings.append(f"{method} blocked with {response.status_code}.")
                else:
                    statuses.append("inconclusive")
                    findings.append(
                        f"{method} returned {response.status_code}; manual review required."
                    )
            except RequestFailed as exc:
                evidence.append(EvidenceItem(f"{method} failed request", exc.request_path))
                evidence.append(EvidenceItem(f"{method} error response", exc.response_path))
                statuses.append("error")
                findings.append(f"{method} request failed: {exc}")
                self.log(f"{check.get('id')}: {method} failed: {exc}")
            except Exception as exc:
                statuses.append("error")
                findings.append(f"{method} request failed: {exc}")
                self.log(f"{check.get('id')}: {method} failed: {exc}")

        status = reduce_status(statuses)
        return CheckResult(
            id=str(check["id"]),
            name=str(check["name"]),
            status=status,
            required_mode=str(check.get("required_mode", "safe-active")),
            evidence_dir=str(check_dir.relative_to(self.run_dir)),
            summary="HTTP method behavior inspected.",
            findings=findings,
            evidence=evidence,
        )

    def send_request(
        self,
        method: str,
        url: str,
        step_id: str,
        check_dir: Path,
        body: str | None = None,
        headers: dict[str, str] | None = None,
    ):
        if self.requests is None:
            return self.send_request_stdlib(method, url, step_id, check_dir, body, headers)
        assert self.session is not None

        request_headers = {"User-Agent": "kisa-webapp-checker-v2"}
        if headers:
            request_headers.update(headers)
        request = self.requests.Request(
            method=method,
            url=url,
            data=body,
            headers=request_headers,
        )
        prepared = self.session.prepare_request(request)
        request_path = check_dir / f"{step_id}.request.txt"
        response_path = check_dir / f"{step_id}.response.txt"

        request_path.write_text(format_prepared_request(prepared), encoding="utf-8")
        try:
            response = self.session.send(
                prepared,
                timeout=self.timeout,
                verify=self.verify_tls,
                allow_redirects=False,
            )
        except Exception as exc:
            response_path.write_text(
                f"ERROR {type(exc).__name__}: {exc}\n",
                encoding="utf-8",
            )
            raise RequestFailed(
                str(exc),
                str(request_path.relative_to(self.run_dir)),
                str(response_path.relative_to(self.run_dir)),
            ) from exc
        response_path.write_text(format_response(response), encoding="utf-8", errors="replace")
        self.log(f"{method} {url} -> {response.status_code}")
        return (
            response,
            str(request_path.relative_to(self.run_dir)),
            str(response_path.relative_to(self.run_dir)),
        )

    def send_request_stdlib(
        self,
        method: str,
        url: str,
        step_id: str,
        check_dir: Path,
        body: str | None = None,
        headers: dict[str, str] | None = None,
    ):
        request_path = check_dir / f"{step_id}.request.txt"
        response_path = check_dir / f"{step_id}.response.txt"
        request_body = body.encode("utf-8") if body is not None else None
        request_headers = {"User-Agent": "kisa-webapp-checker-v2"}
        request_headers.update(profile_session_headers(self.profile))
        if headers:
            request_headers.update(headers)
        request_path.write_text(
            format_raw_request(method, url, request_headers, body),
            encoding="utf-8",
        )

        request = UrlRequest(url, data=request_body, headers=request_headers, method=method)
        context = None
        if urlparse(url).scheme == "https" and not self.verify_tls:
            context = ssl._create_unverified_context()

        try:
            with urlopen(request, timeout=self.timeout, context=context) as handle:
                raw_body = handle.read()
                response = SimpleResponse(
                    status_code=handle.status,
                    reason=handle.reason,
                    headers=dict(handle.headers.items()),
                    text=raw_body.decode("utf-8", errors="replace"),
                )
        except HTTPError as exc:
            raw_body = exc.read()
            response = SimpleResponse(
                status_code=exc.code,
                reason=exc.reason,
                headers=dict(exc.headers.items()),
                text=raw_body.decode("utf-8", errors="replace"),
            )
        except Exception as exc:
            response_path.write_text(
                f"ERROR {type(exc).__name__}: {exc}\n",
                encoding="utf-8",
            )
            raise RequestFailed(
                str(exc),
                str(request_path.relative_to(self.run_dir)),
                str(response_path.relative_to(self.run_dir)),
            ) from exc

        response_path.write_text(format_simple_response(response), encoding="utf-8")
        self.log(f"{method} {url} -> {response.status_code}")
        return (
            response,
            str(request_path.relative_to(self.run_dir)),
            str(response_path.relative_to(self.run_dir)),
        )

    def write_outputs(self, results: list[CheckResult]) -> None:
        result_json = {
            "run_id": self.run_id,
            "profile": self.profile.get("name", "unnamed"),
            "base_url": self.base_url,
            "mode": self.mode,
            "validate_only": self.validate_only,
            "checks": [result.to_json() for result in results],
        }
        (self.run_dir / "result.json").write_text(
            json.dumps(result_json, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        (self.run_dir / "report.md").write_text(
            render_report(result_json),
            encoding="utf-8",
        )
        (self.run_dir / "rollback_checklist.md").write_text(
            render_rollback_checklist(self.profile, results),
            encoding="utf-8",
        )
        (self.run_dir / "run.log").write_text("\n".join(self.log_lines) + "\n", encoding="utf-8")


def slugify(value: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9._-]+", "_", value.strip())
    return slug.strip("_") or "check"


def parse_allow_header(value: str) -> set[str]:
    return {part.strip().upper() for part in value.split(",") if part.strip()}


def reduce_status(statuses: list[str]) -> str:
    if not statuses:
        return "inconclusive"
    for status in statuses:
        if status not in VALID_STATUSES:
            return "error"
    priority = [
        "vulnerable",
        "error",
        "manual_required",
        "inconclusive",
        "not_applicable",
        "not_vulnerable",
        "ready",
    ]
    for status in priority:
        if status in statuses:
            return status
    return "inconclusive"


def merge_step_results(
    check_id: str,
    name: str,
    required_mode: str,
    check_dir: Path,
    results: list[CheckResult],
) -> CheckResult:
    statuses = [result.status for result in results]
    findings: list[str] = []
    evidence: list[EvidenceItem] = []
    for result in results:
        findings.extend(result.findings)
        evidence.extend(result.evidence)

    return CheckResult(
        id=check_id,
        name=name,
        status=reduce_status(statuses),
        required_mode=required_mode,
        evidence_dir=check_dir.name,
        summary="; ".join(result.summary for result in results if result.summary),
        findings=findings,
        evidence=evidence,
    )


def format_prepared_request(prepared: Any) -> str:
    lines = [f"{prepared.method} {prepared.url} HTTP/1.1"]
    for key, value in prepared.headers.items():
        lines.append(f"{key}: {value}")
    lines.append("")
    if prepared.body:
        body = prepared.body
        if isinstance(body, bytes):
            body = body.decode("utf-8", errors="replace")
        lines.append(str(body))
    return "\n".join(lines) + "\n"


def format_response(response: Any) -> str:
    lines = [f"HTTP {response.status_code} {response.reason}"]
    for key, value in response.headers.items():
        lines.append(f"{key}: {value}")
    lines.append("")
    lines.append(response.text)
    return "\n".join(lines)


def format_raw_request(
    method: str, url: str, headers: dict[str, str], body: str | None = None
) -> str:
    lines = [f"{method} {url} HTTP/1.1"]
    for key, value in headers.items():
        lines.append(f"{key}: {value}")
    lines.append("")
    if body:
        lines.append(body)
    return "\n".join(lines) + "\n"


def format_simple_response(response: SimpleResponse) -> str:
    lines = [f"HTTP {response.status_code} {response.reason}"]
    for key, value in response.headers.items():
        lines.append(f"{key}: {value}")
    lines.append("")
    lines.append(response.text)
    return "\n".join(lines)


def render_report(result_json: dict[str, Any]) -> str:
    lines = [
        "# KISA Web Application Checker v2 Report",
        "",
        f"- run_id: `{result_json['run_id']}`",
        f"- profile: `{result_json['profile']}`",
        f"- base_url: `{result_json['base_url']}`",
        f"- mode: `{result_json['mode']}`",
        f"- validate_only: `{result_json['validate_only']}`",
        "",
        "## Summary",
        "",
        "| ID | Name | Status | Evidence |",
        "|---|---|---|---|",
    ]
    for check in result_json["checks"]:
        lines.append(
            f"| {check['id']} | {check['name']} | {check['status']} | `{check['evidence_dir']}` |"
        )

    lines.extend(["", "## Findings", ""])
    for check in result_json["checks"]:
        lines.extend([f"### {check['id']} {check['name']}", ""])
        lines.append(f"- status: `{check['status']}`")
        lines.append(f"- summary: {check.get('summary') or '-'}")
        if check.get("findings"):
            for finding in check["findings"]:
                lines.append(f"- {finding}")
        else:
            lines.append("- No findings recorded.")
        lines.append("")
    return "\n".join(lines)


def render_rollback_checklist(profile: dict[str, Any], results: list[CheckResult]) -> str:
    base_url = str(profile.get("base_url", "")).rstrip("/")
    method_probe = profile.get("method_probe", {})
    probe_path = method_probe.get("path", "") if isinstance(method_probe, dict) else ""
    probe_url = make_url(base_url, str(probe_path)) if probe_path else ""

    lines = [
        "# Rollback Checklist",
        "",
        "v2 does not perform automatic cleanup.",
        "Review this checklist after state-changing or method checks.",
        "",
        "- [ ] Review `result.json` for `vulnerable`, `error`, and `inconclusive` checks.",
        "- [ ] Preserve evidence needed for the report before deleting test artifacts.",
    ]
    if probe_url:
        lines.append(f"- [ ] If PUT created a file, check and remove: `{probe_url}`")

    fixtures = profile.get("fixtures", {})
    if isinstance(fixtures, dict) and fixtures:
        lines.extend(["", "## Profile Fixtures", ""])
        for name, value in fixtures.items():
            lines.append(f"- [ ] Review fixture `{name}`: `{value}`")

    rollback_items = profile.get("rollback", [])
    if isinstance(rollback_items, list) and rollback_items:
        lines.extend(["", "## Profile Rollback Notes", ""])
        for item in rollback_items:
            lines.append(f"- [ ] {item}")
    return "\n".join(lines) + "\n"


def load_checks(checks_dir: Path) -> list[dict[str, Any]]:
    if not checks_dir.exists():
        raise ConfigError(f"Checks directory not found: {checks_dir}")
    checks: list[dict[str, Any]] = []
    for path in sorted(checks_dir.glob("*.yml")):
        data = load_yaml(path)
        data["_source"] = str(path)
        if "id" not in data or "name" not in data:
            raise ConfigError(f"Check must include id and name: {path}")
        checks.append(data)
    if not checks:
        raise ConfigError(f"No check files found in: {checks_dir}")
    return checks


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="KISA Web Application semi-automatic checker v2"
    )
    parser.add_argument("--profile", required=True, help="Path to target profile YAML")
    parser.add_argument("--checks", required=True, help="Directory containing check YAML files")
    parser.add_argument(
        "--mode",
        choices=list(MODES.keys()),
        default="passive",
        help="Execution mode. Default: passive",
    )
    parser.add_argument(
        "--output",
        default="evidence",
        help="Output evidence directory. Default: evidence",
    )
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Validate profile/check parsing without HTTP requests",
    )
    parser.add_argument(
        "--confirm-state-changing",
        action="store_true",
        help="Required to execute state-changing or higher modes.",
    )
    parser.add_argument(
        "--confirm-destructive-risk",
        action="store_true",
        help="Required to execute destructive-risk mode.",
    )
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    base_dir = Path(__file__).resolve().parent
    args = parse_args(argv)

    try:
        profile_path = resolve_path(base_dir, args.profile)
        checks_dir = resolve_path(base_dir, args.checks)
        output_root = resolve_path(base_dir, args.output)

        profile = load_yaml(profile_path)
        checks = load_checks(checks_dir)
        require_allowed_target(profile)

        runner = CheckerRunner(
            profile=profile,
            checks=checks,
            mode=args.mode,
            output_root=output_root,
            validate_only=args.validate_only,
            confirm_state_changing=args.confirm_state_changing,
            confirm_destructive_risk=args.confirm_destructive_risk,
        )
        results = runner.run()
        print(f"[OK] run_id={runner.run_id}")
        print(f"[OK] evidence={runner.run_dir}")
        for result in results:
            print(f"[{result.status}] {result.id} {result.name}")
        return 0
    except CheckerError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
