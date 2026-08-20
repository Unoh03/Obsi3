#!/usr/bin/env python3
"""Verify that the current organized mentor-note corpus is append-only.

The protected baseline is the exact byte content stored at one Git commit.
A protected file passes only when its current committed bytes are:

    baseline_bytes + optional_suffix_bytes

Any edit, deletion, reordering, whitespace change, line-ending change, rename,
or truncation inside the baseline region fails.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any


DEFAULT_MANIFEST = Path(
    "20_팀 프로젝트/3차 프로젝트/append-only-audit/"
    "mentor-note-append-only-manifest.json"
)


@dataclass(frozen=True)
class Check:
    name: str
    passed: bool
    detail: str


def run_git(root: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[bytes]:
    proc = subprocess.run(
        ["git", *args],
        cwd=root,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if check and proc.returncode != 0:
        raise RuntimeError(
            f"git {' '.join(args)} failed ({proc.returncode}):\n"
            f"{proc.stderr.decode('utf-8', errors='replace')}"
        )
    return proc


def git_text(root: Path, *args: str) -> str:
    return run_git(root, *args).stdout.decode("utf-8", errors="strict").strip()


def resolve_blob(root: Path, commit: str, path: str) -> str:
    return git_text(root, "rev-parse", f"{commit}:{path}")


def read_blob(root: Path, sha: str) -> bytes:
    return run_git(root, "cat-file", "blob", sha).stdout


def tree_mode(root: Path, commit: str, path: str) -> str:
    output = git_text(root, "ls-tree", commit, "--", path)
    if not output:
        raise FileNotFoundError(f"missing path at {commit}: {path}")
    return output.split(maxsplit=1)[0]


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument(
        "--check-working-tree",
        action="store_true",
        help=(
            "Also compare raw working-tree bytes. This is stricter than Git's "
            "committed-object check and can detect local edits before commit."
        ),
    )
    parser.add_argument("--json", action="store_true", help="Print JSON only")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = Path(git_text(Path.cwd(), "rev-parse", "--show-toplevel"))
    manifest_path = args.manifest
    if not manifest_path.is_absolute():
        manifest_path = root / manifest_path

    manifest: dict[str, Any] = json.loads(manifest_path.read_text(encoding="utf-8"))
    baseline_commit = str(manifest["baseline"]["commit"])
    head = git_text(root, "rev-parse", "HEAD")

    checks: list[Check] = []

    ancestor_proc = run_git(
        root, "merge-base", "--is-ancestor", baseline_commit, head, check=False
    )
    checks.append(
        Check(
            "baseline commit is ancestor of HEAD",
            ancestor_proc.returncode == 0,
            f"baseline={baseline_commit} head={head}",
        )
    )

    file_results: list[dict[str, Any]] = []

    for item in manifest["protected_files"]:
        path = str(item["path"])
        expected_blob = str(item["baseline_git_blob_sha1"])
        expected_size = int(item["baseline_size_bytes"])
        expected_mode = str(item["mode"])

        result: dict[str, Any] = {
            "path": path,
            "baseline_blob": expected_blob,
            "baseline_size": expected_size,
        }

        try:
            actual_baseline_blob = resolve_blob(root, baseline_commit, path)
            checks.append(
                Check(
                    f"baseline blob pin: {path}",
                    actual_baseline_blob == expected_blob,
                    f"actual={actual_baseline_blob} expected={expected_blob}",
                )
            )

            baseline_mode = tree_mode(root, baseline_commit, path)
            checks.append(
                Check(
                    f"baseline mode: {path}",
                    baseline_mode == expected_mode,
                    f"actual={baseline_mode} expected={expected_mode}",
                )
            )

            baseline_bytes = read_blob(root, actual_baseline_blob)
            checks.append(
                Check(
                    f"baseline size: {path}",
                    len(baseline_bytes) == expected_size,
                    f"actual={len(baseline_bytes)} expected={expected_size}",
                )
            )

            current_blob = resolve_blob(root, "HEAD", path)
            current_mode = tree_mode(root, "HEAD", path)
            current_bytes = read_blob(root, current_blob)

            same_mode = current_mode == expected_mode
            not_truncated = len(current_bytes) >= len(baseline_bytes)
            exact_prefix = not_truncated and current_bytes.startswith(baseline_bytes)
            suffix = current_bytes[len(baseline_bytes) :] if exact_prefix else b""

            checks.append(
                Check(
                    f"protected path exists and mode unchanged: {path}",
                    same_mode,
                    f"actual_mode={current_mode} expected_mode={expected_mode}",
                )
            )
            checks.append(
                Check(
                    f"not truncated: {path}",
                    not_truncated,
                    f"current={len(current_bytes)} baseline={len(baseline_bytes)}",
                )
            )
            checks.append(
                Check(
                    f"baseline bytes remain exact prefix: {path}",
                    exact_prefix,
                    (
                        f"baseline_sha256={sha256(baseline_bytes)} "
                        f"current_prefix_sha256="
                        f"{sha256(current_bytes[:len(baseline_bytes)]) if not_truncated else 'N/A'}"
                    ),
                )
            )

            if args.check_working_tree:
                working_path = root / path
                exists = working_path.is_file()
                working_bytes = working_path.read_bytes() if exists else b""
                working_not_truncated = exists and len(working_bytes) >= len(baseline_bytes)
                working_prefix = working_not_truncated and working_bytes.startswith(baseline_bytes)
                checks.append(
                    Check(
                        f"working-tree exact prefix: {path}",
                        working_prefix,
                        (
                            f"exists={exists} working_size={len(working_bytes)} "
                            f"baseline_size={len(baseline_bytes)}"
                        ),
                    )
                )

            result.update(
                {
                    "current_blob": current_blob,
                    "current_size": len(current_bytes),
                    "appended_bytes": len(suffix),
                    "appended_sha256": sha256(suffix) if suffix else None,
                    "passed": same_mode and not_truncated and exact_prefix,
                }
            )
        except Exception as exc:  # noqa: BLE001 - audit must report every file
            checks.append(Check(f"protected file readable: {path}", False, str(exc)))
            result.update({"passed": False, "error": str(exc)})

        file_results.append(result)

    failures = [asdict(check) for check in checks if not check.passed]
    report = {
        "schema_version": 1,
        "policy": manifest["policy"],
        "baseline_commit": baseline_commit,
        "head": head,
        "protected_file_count": len(file_results),
        "files": file_results,
        "checks": [asdict(check) for check in checks],
        "failures": failures,
        "passed": not failures,
    }

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        for file_result in file_results:
            state = "PASS" if file_result.get("passed") else "FAIL"
            appended = file_result.get("appended_bytes", "N/A")
            print(f"[{state}] {file_result['path']} (appended_bytes={appended})")
        print()
        if failures:
            print("Append-only verification: FAIL")
            for failure in failures:
                print(f"- {failure['name']}: {failure['detail']}")
        else:
            print("Append-only verification: PASS")
            print("All baseline bytes remain unchanged and in the same order.")
            print("Any differences are suffix-only additions.")

    return 0 if report["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
