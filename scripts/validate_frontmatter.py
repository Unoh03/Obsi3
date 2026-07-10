#!/usr/bin/env python3
"""Validate canonical frontmatter for new/changed Obsidian notes.

Existing legacy notes are reported as warnings. New notes and templates are
strict so the validator prevents new vocabulary drift without forcing a
repository-wide migration.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


CANONICAL_TYPES = {
    "moc",
    "concept",
    "lab",
    "command-note",
    "troubleshooting",
    "source-digest",
    "raw",
    "project-raw-log",
    "project-daily-log",
    "project-doc",
    "meeting",
    "wrong-answer",
    "security-policy",
}

CANONICAL_STATUSES = {
    "draft",
    "active",
    "stable",
    "legacy",
    "stale",
    "archived",
}

REQUIRED_KEYS = {
    "moc": {"scope", "parent_moc"},
    "concept": {"topic", "parent_moc"},
    "lab": {"topic", "parent_moc"},
    "command-note": {"topic", "parent_moc"},
    "troubleshooting": {"topic", "parent_moc"},
    "source-digest": {"parent_moc", "source", "source_pages"},
    "raw": {"topic", "parent_moc"},
    "project-raw-log": {"project", "project_moc"},
    "project-daily-log": {"project", "project_moc", "source_raw"},
    "project-doc": {"project", "project_moc"},
    "meeting": {"project", "project_moc"},
    "wrong-answer": {"topic", "parent_moc"},
    "security-policy": {"topic", "parent_moc"},
}

CONTENT_ROOTS = {
    "00_index",
    "10_학습 노트",
    "20_팀 프로젝트",
    "30_자격증",
    "40_자료",
    "90_템플릿",
}

TOP_LEVEL_KEY = re.compile(r"^([A-Za-z0-9_-]+):(?:\s*(.*))?$")
DATE_VALUE = re.compile(r'^"?(?:\{\{date(?::[^}]+)?\}\}|\d{4}-\d{2}-\d{2})"?$')
STATUS_TAG = re.compile(r"(?:🏷️)?상태/[^\s,\]]+")


@dataclass
class Finding:
    level: str
    path: str
    message: str


def git_paths(*args: str) -> set[str]:
    result = subprocess.run(
        ["git", *args],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return {
        item.decode("utf-8", errors="surrogateescape")
        for item in result.stdout.split(b"\0")
        if item
    }


def changed_paths() -> tuple[set[str], set[str]]:
    changed = git_paths(
        "diff", "--name-only", "-z", "--diff-filter=ACMR", "HEAD", "--", "*.md"
    )
    added = git_paths(
        "diff", "--name-only", "-z", "--diff-filter=A", "HEAD", "--", "*.md"
    )
    untracked = git_paths(
        "ls-files", "--others", "--exclude-standard", "-z", "--", "*.md"
    )
    return changed | untracked, added | untracked


def all_paths() -> set[str]:
    tracked = git_paths("ls-files", "-z", "--", "*.md")
    untracked = git_paths(
        "ls-files", "--others", "--exclude-standard", "-z", "--", "*.md"
    )
    return tracked | untracked


def parse_frontmatter(path: Path) -> tuple[dict[str, str], list[str], str | None]:
    text = path.read_text(encoding="utf-8-sig")
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, [], "frontmatter 없음"

    closing = None
    for index in range(1, len(lines)):
        if lines[index].strip() == "---":
            closing = index
            break
    if closing is None:
        return {}, [], "frontmatter 닫는 구분자 없음"

    fields: dict[str, str] = {}
    duplicates: list[str] = []
    for line in lines[1:closing]:
        match = TOP_LEVEL_KEY.match(line)
        if not match:
            continue
        key = match.group(1)
        value = (match.group(2) or "").strip().strip('"').strip("'")
        if key in fields:
            duplicates.append(key)
        fields[key] = value

    return fields, duplicates, None


def validate(path_string: str, *, is_new: bool) -> list[Finding]:
    path = Path(path_string)
    findings: list[Finding] = []
    if not path.is_file() or path.suffix.lower() != ".md":
        return findings

    parts = path.parts
    in_template_folder = bool(parts and parts[0] == "90_템플릿")
    strict = is_new or in_template_folder
    fields, duplicates, parse_error = parse_frontmatter(path)

    if parse_error:
        if strict and parts and parts[0] in CONTENT_ROOTS:
            findings.append(Finding("ERROR", path_string, parse_error))
        return findings

    for key in duplicates:
        findings.append(Finding("ERROR" if strict else "WARN", path_string, f"중복 key: {key}"))

    for key in ("type", "status", "created"):
        if not fields.get(key):
            findings.append(
                Finding("ERROR" if strict else "WARN", path_string, f"필수 field 누락/빈 값: {key}")
            )

    note_type = fields.get("type", "")
    status = fields.get("status", "")
    if note_type and note_type not in CANONICAL_TYPES:
        findings.append(
            Finding("ERROR" if strict else "WARN", path_string, f"비표준 type: {note_type}")
        )
    if status and status not in CANONICAL_STATUSES:
        findings.append(
            Finding("ERROR" if strict else "WARN", path_string, f"비표준 status: {status}")
        )

    missing = sorted(REQUIRED_KEYS.get(note_type, set()) - fields.keys())
    for key in missing:
        findings.append(
            Finding("ERROR" if strict else "WARN", path_string, f"{note_type} 필수 key 없음: {key}")
        )

    if is_new and not in_template_folder:
        for key in sorted(REQUIRED_KEYS.get(note_type, set())):
            if not fields.get(key):
                findings.append(Finding("ERROR", path_string, f"새 노트의 필수 field가 비어 있음: {key}"))

    created = fields.get("created", "")
    if created and not DATE_VALUE.match(created):
        findings.append(
            Finding("ERROR" if strict else "WARN", path_string, f"created 형식 확인 필요: {created}")
        )

    text = path.read_text(encoding="utf-8-sig")
    status_tag = STATUS_TAG.search(text.split("---", 2)[1] if text.startswith("---") else "")
    if status_tag:
        findings.append(
            Finding(
                "ERROR" if strict else "WARN",
                path_string,
                "status 중복 태그 금지",
            )
        )

    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--changed", action="store_true", help="HEAD 대비 변경 Markdown 검사")
    group.add_argument("--all", action="store_true", help="모든 추적·미추적 Markdown 감사")
    parser.add_argument("paths", nargs="*", help="직접 검사할 Markdown 경로")
    args = parser.parse_args()

    if args.paths:
        paths = set(args.paths)
        _, added = changed_paths()
    elif args.all:
        paths = all_paths()
        _, added = changed_paths()
    else:
        paths, added = changed_paths()

    markdown_paths = sorted(path for path in paths if path.lower().endswith(".md"))
    findings: list[Finding] = []
    for path in markdown_paths:
        findings.extend(validate(path, is_new=path in added))

    for finding in findings:
        print(f"{finding.level}: {finding.path}: {finding.message}")

    errors = sum(finding.level == "ERROR" for finding in findings)
    warnings = sum(finding.level == "WARN" for finding in findings)
    print(f"Checked {len(markdown_paths)} Markdown file(s): {errors} error(s), {warnings} warning(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
