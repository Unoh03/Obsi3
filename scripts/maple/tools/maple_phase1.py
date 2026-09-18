"""Maple Bridge Phase 1 command line. Run --help for commands."""
from __future__ import annotations

import argparse
import asyncio
import inspect
import json
import sys
from importlib.metadata import version
from pathlib import Path
from urllib.parse import urlsplit

from phase1_core import (EvidenceError, SENSITIVE, check_sensitive, freeze_snapshot,
                        json_diff, now, parse_json, read_json, replay, safe_url,
                        verify_snapshot, write_bytes, write_json)
from phase1_cdp import Capture


def versions():
    return {name: version(name) for name in ("playwright", "httpx", "deepdiff")}


def check_endpoint(endpoint):
    parsed = urlsplit(endpoint)
    if parsed.scheme != "http" or parsed.hostname not in {"localhost", "127.0.0.1", "::1"} or parsed.username or parsed.password:
        raise EvidenceError("CDP_endpoint_must_be_loopback_http")


async def connect(pw, endpoint, page_url):
    check_endpoint(endpoint)
    browser = await pw.chromium.connect_over_cdp(endpoint, is_local=True, no_defaults=True)
    pages = [p for ctx in browser.contexts for p in ctx.pages if p.url == page_url]
    if len(pages) != 1:
        raise EvidenceError("exact_page_url_must_match_one_tab")
    safe_url(page_url)
    return browser, pages[0]


async def page_assets(page):
    urls = await page.evaluate("() => [...new Set([...document.scripts].map(s => s.src).filter(Boolean))]")
    result = []
    for url in urls:
        try:
            result.append({"url": safe_url(url), "sha256": None, "identity": "loaded_script_url_only"})
        except EvidenceError:
            result.append({"url": None, "status": "sensitive_url_excluded"})
    return result


async def capture_command(args):
    from playwright.async_api import async_playwright
    context = read_json(args.context)
    check_sensitive(context)
    identity, raw = verify_snapshot(args.snapshot)
    if context.get("character") != identity.get("character"):
        raise EvidenceError("context_snapshot_character_mismatch")
    if args.kind != "exploratory" and context.get("settings_confirmed") is not True:
        raise EvidenceError("confirm_settings_before_baseline")
    if args.kind.startswith("perturb"):
        backup = context.get("backup_path")
        if not backup or not Path(backup).is_file() or not context.get("changed_setting"):
            raise EvidenceError("perturbation_requires_backup_and_change_description")
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=False)
    context.update({"started_at": now(), "kind": args.kind, "nexon": identity,
                    "versions": versions(), "cache_mode": "disabled" if args.forced_network else "unmodified",
                    "buffer_mb": args.buffer_mb, "page_url": args.page_url,
                    "observation_scope": "selected_page_CDP; worker_OOPIF_coverage_unverified"})
    write_json(out / "context-start.json", context)
    write_bytes(out / "nexon.raw.json", raw)
    failure = None
    capture = None
    count = 0
    async with async_playwright() as pw:
        cdp = None
        try:
            browser, page = await connect(pw, args.cdp, args.page_url)
            cdp = await page.context.new_cdp_session(page)
            context["browser_version"] = browser.version
            context["assets_at_start"] = await page_assets(page)
            capture = Capture(cdp, args.host or [urlsplit(args.page_url).hostname], args.allow_header)
            if args.seconds is None:
                await asyncio.to_thread(input, "Press Enter to ARM capture, then calculate in Brave. ")
            await capture.start(args.forced_network, args.buffer_mb)
            print("ARMED: calculate in the selected Brave tab.", flush=True)
            if args.seconds is None:
                await asyncio.to_thread(input, "After calculation completes, press Enter to STOP. ")
            else:
                deadline = asyncio.get_running_loop().time() + args.seconds
                while asyncio.get_running_loop().time() < deadline:
                    if args.stop_file and Path(args.stop_file).exists():
                        break
                    await asyncio.sleep(0.25)
            await capture.finish()
            index = capture.save(out)
            count = len(index)
            context["assets_captured"] = capture.asset_identity
            context["event_errors"] = capture.event_errors
            context["request_count"] = count
            context["site_build_id"] = "unknown"
            context["capture_status"] = "captured_unreviewed" if count else "no_candidate_requests_observed"
            if page.url == args.page_url:
                # One evidence screenshot, never a polling loop.
                await page.screenshot(path=str(out / "ui.png"), full_page=False)
                context["screenshot"] = "captured; UI_mapping_requires_review"
            else:
                context["screenshot"] = "skipped_page_changed"
        except Exception as exc:
            failure = str(exc) if isinstance(exc, EvidenceError) else type(exc).__name__
            context["capture_status"] = "incomplete"
            context["error"] = failure
        finally:
            if cdp:
                try:
                    if args.forced_network:
                        await cdp.send("Network.setCacheDisabled", {"cacheDisabled": False})
                    await cdp.detach()
                except Exception:
                    context["detach_status"] = "unverified"
    context["finished_at"] = now()
    write_json(out / "context.json", context)
    print(json.dumps({"output": str(out), "requests": count, "status": context["capture_status"]}, ensure_ascii=False))
    return 2 if failure else 0


async def storage_command(args):
    from playwright.async_api import async_playwright
    async with async_playwright() as pw:
        _, page = await connect(pw, args.cdp, args.page_url)
        if args.action == "list":
            keys = await page.evaluate("() => Object.keys(localStorage)")
            print(json.dumps({"keys": keys}, ensure_ascii=False, indent=2))
            return 0
        if not args.key or not args.out:
            raise EvidenceError("export_requires_explicit_keys_and_out")
        for key in args.key:
            if SENSITIVE.search(key):
                raise EvidenceError("sensitive_storage_key")
        values = await page.evaluate("keys => Object.fromEntries(keys.map(k => [k, localStorage.getItem(k)]))", args.key)
        for value in values.values():
            if value is not None:
                check_sensitive(parse_json(value))
        write_json(args.out, {"origin": urlsplit(args.page_url).scheme + "://" + urlsplit(args.page_url).netloc,
                              "captured_at": now(), "keys": values, "restore_method": "same_origin_setItem_verbatim_then_reload",
                              "restore_verified": False})
        print(json.dumps({"output": args.out, "keys": list(values)}, ensure_ascii=False))
        return 0


async def probe_command(args):
    from playwright.async_api import async_playwright
    check_endpoint(args.cdp)
    async with async_playwright() as pw:
        browser = await pw.chromium.connect_over_cdp(args.cdp, is_local=True, no_defaults=True)
        pages = []
        for ctx in browser.contexts:
            for page in ctx.pages:
                try:
                    pages.append(safe_url(page.url))
                except EvidenceError:
                    pages.append("URL omitted")
        print(json.dumps({"browser_version": browser.version, "pages": pages, "versions": versions()}, ensure_ascii=False))
    return 0


def parser():
    root = argparse.ArgumentParser(description=__doc__)
    sub = root.add_subparsers(dest="command", required=True)
    sub.add_parser("doctor")
    p = sub.add_parser("probe")
    p.add_argument("--cdp", default="http://127.0.0.1:9222")
    p = sub.add_parser("snapshot")
    p.add_argument("source")
    p.add_argument("--out", required=True)
    p = sub.add_parser("context-template")
    p.add_argument("--out", required=True)
    p = sub.add_parser("capture")
    p.add_argument("--cdp", default="http://127.0.0.1:9222")
    p.add_argument("--page-url", required=True)
    p.add_argument("--snapshot", required=True)
    p.add_argument("--context", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--host", action="append", help="Additional reviewed API host scope; default selected page hostname")
    p.add_argument("--allow-header", action="append", default=[])
    p.add_argument("--kind", choices=["exploratory", "baseline-normal", "baseline-forced-network", "perturb-stat", "perturb-special", "restore-check"], default="exploratory")
    p.add_argument("--forced-network", action="store_true")
    p.add_argument("--buffer-mb", type=int, choices=range(1, 129))
    p.add_argument("--seconds", type=int, choices=range(1, 1801))
    p.add_argument("--stop-file")
    p = sub.add_parser("storage")
    p.add_argument("action", choices=["list", "export"])
    p.add_argument("--cdp", default="http://127.0.0.1:9222")
    p.add_argument("--page-url", required=True)
    p.add_argument("--key", action="append")
    p.add_argument("--out")
    p = sub.add_parser("replay")
    p.add_argument("fixture")
    p.add_argument("--mode", choices=["observed", "json"], required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--header", action="append", default=[])
    p = sub.add_parser("diff")
    p.add_argument("before")
    p.add_argument("after")
    p.add_argument("--out")
    return root


def main():
    args = parser().parse_args()
    try:
        if args.command == "doctor":
            from playwright.async_api import BrowserType
            parameters = inspect.signature(BrowserType.connect_over_cdp).parameters
            if not {"is_local", "no_defaults"}.issubset(parameters):
                raise EvidenceError("playwright_CDP_options_unsupported")
            print(json.dumps({"python": sys.version, "versions": versions(), "CDP_options": "supported"}))
        elif args.command == "snapshot":
            print(json.dumps(freeze_snapshot(args.source, args.out), ensure_ascii=False, indent=2))
        elif args.command == "context-template":
            write_json(args.out, {"character": "우노03", "settings_confirmed": False,
                                  "character_preset": "unknown", "equipment_preset": "unknown",
                                  "ring_setting": "unknown", "doping": "unknown", "boss_setting": "unknown",
                                  "manual_overrides": {}, "ui_values": {}, "backup_path": None,
                                  "changed_setting": None, "notes": "새 프로필과 평소 설정의 일치 확인 필요"})
        elif args.command == "capture":
            if (args.kind == "baseline-normal" and args.forced_network) or (args.kind == "baseline-forced-network" and not args.forced_network):
                raise EvidenceError("baseline_cache_label_mismatch")
            return asyncio.run(capture_command(args))
        elif args.command == "storage":
            return asyncio.run(storage_command(args))
        elif args.command == "probe":
            return asyncio.run(probe_command(args))
        elif args.command == "replay":
            report = replay(args.fixture, args.out, args.mode, args.header)
            print(json.dumps(report, ensure_ascii=False, indent=2))
            return 2 if "error" in report else 0
        elif args.command == "diff":
            difference = json_diff(read_json(args.before), read_json(args.after))
            if args.out:
                write_json(args.out, difference)
            print(json.dumps(difference, ensure_ascii=False, indent=2))
            return 1 if difference else 0
        return 0
    except KeyboardInterrupt:
        print("Interrupted; inspect incomplete output before reuse.", file=sys.stderr)
        return 130
    except Exception as exc:
        message = str(exc) if isinstance(exc, EvidenceError) else type(exc).__name__
        print(f"ERROR: {message}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
