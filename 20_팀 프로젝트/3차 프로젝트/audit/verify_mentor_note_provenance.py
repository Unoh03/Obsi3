#!/usr/bin/env python3
"""Verify provenance invariants for the 2026-08-19 mentor note.

The authoritative model is:
    immutable source Git blob + explicit correction ledger C01..C16

Derived Markdown files are pinned convenience views, not lossless replacements.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Iterable


DEFAULT_MANIFEST = Path(
    "20_팀 프로젝트/3차 프로젝트/audit/8.19-mentor-note-provenance.json"
)


@dataclass(frozen=True)
class Check:
    name: str
    passed: bool
    detail: str


@dataclass(frozen=True)
class MarkdownBlock:
    id: str
    start_line: int
    end_line: int
    type: str
    canonical_text_sha256: str
    first_line: str
    verbatim_in: tuple[str, ...]


def run_git(repo_root: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[bytes]:
    proc = subprocess.run(
        ["git", *args],
        cwd=repo_root,
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


def git_text(repo_root: Path, *args: str) -> str:
    return run_git(repo_root, *args).stdout.decode("utf-8").strip()


def git_blob_bytes(repo_root: Path, blob_sha: str) -> bytes:
    return run_git(repo_root, "cat-file", "blob", blob_sha).stdout


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def classify_block(first_line: str) -> str:
    stripped = first_line.lstrip()
    if stripped.startswith("#"):
        return "heading-section"
    if stripped.startswith(("```", "~~~")):
        return "fenced-code"
    if stripped.startswith("> [!"):
        return "callout"
    if stripped.startswith("|"):
        return "table"
    if stripped.startswith(("- ", "* ", "+ ")):
        return "list"
    if len(stripped) >= 3 and stripped[0].isdigit() and ". " in stripped[:5]:
        return "list"
    return "paragraph"


def split_markdown_blocks(text: str) -> list[tuple[int, int, str]]:
    """Return (start_line, end_line, canonical_text) blocks.

    Blank lines and headings delimit blocks outside fenced code. Full-file byte
    identity is checked separately; block hashes use UTF-8 text joined with LF.
    """

    lines = text.split("\n")
    blocks: list[tuple[int, int, str]] = []
    current: list[str] = []
    start_line = 1
    in_fence = False

    def flush(end_line: int) -> None:
        nonlocal current, start_line
        if not current:
            return
        block_text = "\n".join(current).rstrip("\r\n")
        if block_text.strip():
            blocks.append((start_line, end_line, block_text))
        current = []

    for index, raw_line in enumerate(lines, start=1):
        line = raw_line.rstrip("\r")
        stripped = line.lstrip()
        is_fence = stripped.startswith(("```", "~~~"))
        is_heading = (not in_fence) and stripped.startswith("#") and " " in stripped
        is_blank = (not in_fence) and not line.strip()

        if is_heading and current:
            flush(index - 1)
            start_line = index

        if is_blank:
            if current:
                flush(index - 1)
            start_line = index + 1
            continue

        if not current:
            start_line = index
        current.append(line)

        if is_fence:
            in_fence = not in_fence
            if not in_fence:
                flush(index)
                start_line = index + 1

    if current:
        flush(len(lines))

    return blocks


def read_utf8(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def build_block_manifest(
    source_text: str,
    derived_texts: dict[str, str],
) -> list[MarkdownBlock]:
    result: list[MarkdownBlock] = []
    for number, (start, end, block_text) in enumerate(
        split_markdown_blocks(source_text), start=1
    ):
        verbatim = tuple(
            path for path, content in derived_texts.items() if block_text in content
        )
        first_line = block_text.split("\n", 1)[0]
        result.append(
            MarkdownBlock(
                id=f"O-{number:04d}",
                start_line=start,
                end_line=end,
                type=classify_block(first_line),
                canonical_text_sha256=sha256_hex(block_text.encode("utf-8")),
                first_line=first_line,
                verbatim_in=verbatim,
            )
        )
    return result


def add_check(checks: list[Check], name: str, passed: bool, detail: str) -> None:
    checks.append(Check(name=name, passed=passed, detail=detail))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--write-generated", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    discovery = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if discovery.returncode != 0:
        print(discovery.stderr.decode("utf-8", errors="replace"), file=sys.stderr)
        return 2

    repo_root = Path(discovery.stdout.decode("utf-8").strip())
    manifest_path = repo_root / args.manifest
    manifest: dict[str, Any] = json.loads(read_utf8(manifest_path))
    checks: list[Check] = []

    source = manifest["source"]
    source_spec = f"{source['commit']}:{source['path']}"
    source_blob = git_text(repo_root, "rev-parse", source_spec)
    add_check(
        checks,
        "source blob pin",
        source_blob == source["expected_git_blob_sha1"],
        f"actual={source_blob} expected={source['expected_git_blob_sha1']}",
    )

    preserved = manifest["preserved_copy"]
    preserved_blob = git_text(repo_root, "rev-parse", f"HEAD:{preserved['path']}")
    add_check(
        checks,
        "preserved blob equals source",
        preserved_blob == source_blob == preserved["expected_git_blob_sha1"],
        f"source={source_blob} preserved={preserved_blob}",
    )

    source_bytes = git_blob_bytes(repo_root, source_blob)
    preserved_bytes = git_blob_bytes(repo_root, preserved_blob)
    source_sha256 = sha256_hex(source_bytes)
    preserved_sha256 = sha256_hex(preserved_bytes)
    add_check(
        checks,
        "source and preserved SHA-256",
        source_sha256 == preserved_sha256,
        f"source={source_sha256} preserved={preserved_sha256}",
    )

    derived_texts: dict[str, str] = {}
    for view in manifest["derived_views"]:
        path = view["path"]
        actual_blob = git_text(repo_root, "rev-parse", f"HEAD:{path}")
        add_check(
            checks,
            f"derived view blob pin: {path}",
            actual_blob == view["expected_git_blob_sha1"],
            f"actual={actual_blob} expected={view['expected_git_blob_sha1']}",
        )
        worktree_clean = run_git(repo_root, "diff", "--quiet", "--", path, check=False).returncode == 0
        index_clean = run_git(repo_root, "diff", "--cached", "--quiet", "--", path, check=False).returncode == 0
        add_check(checks, f"derived working tree clean: {path}", worktree_clean, str(worktree_clean))
        add_check(checks, f"derived index clean: {path}", index_clean, str(index_clean))
        derived_texts[path] = read_utf8(repo_root / path)

    preserved_worktree_clean = (
        run_git(repo_root, "diff", "--quiet", "--", preserved["path"], check=False).returncode
        == 0
    )
    preserved_index_clean = (
        run_git(
            repo_root,
            "diff",
            "--cached",
            "--quiet",
            "--",
            preserved["path"],
            check=False,
        ).returncode
        == 0
    )
    add_check(checks, "preserved working tree clean", preserved_worktree_clean, str(preserved_worktree_clean))
    add_check(checks, "preserved index clean", preserved_index_clean, str(preserved_index_clean))

    actual_ids = sorted(item["id"] for item in manifest["corrections"])
    expected_ids = [f"C{number:02d}" for number in range(1, 17)]
    add_check(
        checks,
        "correction ID set C01-C16",
        actual_ids == expected_ids,
        f"actual={','.join(actual_ids)}",
    )
    add_check(
        checks,
        "correction IDs unique",
        len(actual_ids) == len(set(actual_ids)),
        f"count={len(actual_ids)} unique={len(set(actual_ids))}",
    )

    for correction in manifest["corrections"]:
        for anchor in correction["anchors"]:
            target = repo_root / anchor["path"]
            exists = target.is_file()
            if not exists:
                add_check(
                    checks,
                    f"anchor {correction['id']}: {anchor['path']}",
                    False,
                    "missing file",
                )
                continue
            content = read_utf8(target)
            found = anchor["contains"] in content
            add_check(
                checks,
                f"anchor {correction['id']}: {anchor['path']}",
                found,
                f"contains={anchor['contains']}",
            )

    source_text = source_bytes.decode("utf-8")
    blocks = build_block_manifest(source_text, derived_texts)
    add_check(
        checks,
        "source block manifest generated",
        bool(blocks),
        f"blocks={len(blocks)}",
    )

    failures = [asdict(item) for item in checks if not item.passed]
    result = {
        "schema_version": 1,
        "repository": manifest["repository"],
        "head": git_text(repo_root, "rev-parse", "HEAD"),
        "source_blob_sha1": source_blob,
        "preserved_blob_sha1": preserved_blob,
        "source_sha256": source_sha256,
        "preserved_sha256": preserved_sha256,
        "source_block_count": len(blocks),
        "checks": [asdict(item) for item in checks],
        "failures": failures,
        "passed": not failures,
    }

    if args.write_generated:
        generated_dir = manifest_path.parent / "generated"
        generated_dir.mkdir(parents=True, exist_ok=True)
        block_manifest = {
            "schema_version": 1,
            "source_commit": source["commit"],
            "source_path": source["path"],
            "source_blob_sha1": source_blob,
            "source_sha256": source_sha256,
            "block_hash_definition": (
                "UTF-8 of canonical block text joined with LF; full byte identity "
                "is verified separately"
            ),
            "blocks": [asdict(item) for item in blocks],
        }
        (generated_dir / "8.19-original-blocks.json").write_text(
            json.dumps(block_manifest, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        (generated_dir / "8.19-provenance-result.json").write_text(
            json.dumps(result, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
