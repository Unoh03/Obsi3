#!/usr/bin/env python3
"""Validate the Obsi2 operational navigation layer.

The validator builds its inventory at run time; it does not maintain a second
catalog of Vault files.  It checks Home reachability, MOC parent reciprocity,
and wiki-link resolution for operational MOC/control notes.  Markdown not
directly linked from an operating MOC body and duplicate basenames are
classified and reported, but they are not errors by themselves because a MOC
is intentionally not a complete inventory.

Exit codes:
    0: no structural navigation error
    1: one or more structural navigation errors
    2: invalid command-line use (argparse)
"""

from __future__ import annotations

import argparse
import json
import os
import posixpath
import re
import sys
from collections import defaultdict, deque
from dataclasses import asdict, dataclass
from pathlib import Path, PurePosixPath
from typing import Iterable


HOME = "00_index/Home.md"
KNOWN_CONTROLS = {
    "00_index/LLM_AGENT_INDEX.md",
    "00_index/Vault_Curation_Checklist.md",
    "00_index/Vault_Retrieval_Architecture_v1.md",
}
ROOT_DOC_EXCEPTIONS = {"AGENTS.md", "README.md"}
OPERATIONAL_STATUSES = {"active", "draft", "stable"}
NON_OPERATIONAL_STATUSES = {"legacy", "stale", "archived"}
CANONICAL_STATUSES = OPERATIONAL_STATUSES | NON_OPERATIONAL_STATUSES
IGNORED_DIRECTORIES = {
    ".git",
    ".obsidian",
    ".trash",
    ".venv",
    "__pycache__",
    "node_modules",
}
REFERENCE_PARTS = {"archive", "archives", "legacy", "reference", "references", "구닥다리"}

WIKI_LINK = re.compile(r"\[\[([^\]\r\n]+)\]\]")
TOP_LEVEL_FIELD = re.compile(r"^([A-Za-z0-9_-]+):(?:\s*(.*))?$")
ATX_HEADING = re.compile(r"^ {0,3}(#{1,6})\s+(.+?)\s*$")
BLOCK_ID = re.compile(r"(?:^|\s)\^([A-Za-z0-9-]+)\s*$")
INLINE_CODE = re.compile(r"`+[^`]*`+")


@dataclass(frozen=True)
class Finding:
    level: str
    code: str
    path: str
    message: str
    line: int | None = None


@dataclass(frozen=True)
class WikiLinkRef:
    raw: str
    file_part: str
    anchor: str
    line: int


@dataclass(frozen=True)
class ResolveResult:
    state: str
    candidates: tuple[str, ...]


@dataclass
class Document:
    path: str
    fields: dict[str, str]
    text: str
    body_start: int


def normalize_rel(value: str) -> str:
    """Normalize a Vault-relative link/path without treating dots as suffixes."""

    value = value.strip().replace("\\", "/")
    while value.startswith("./"):
        value = value[2:]
    return value.lstrip("/")


def is_external_target(value: str) -> bool:
    lowered = value.strip().lower()
    return lowered.startswith(
        ("http://", "https://", "mailto:", "obsidian://", "data:")
    )


def strip_yaml_scalar(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1].strip()
    return value


def parse_frontmatter(text: str) -> tuple[dict[str, str], int]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, 0

    fields: dict[str, str] = {}
    closing: int | None = None
    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            closing = index
            break
        match = TOP_LEVEL_FIELD.match(line)
        if match:
            fields[match.group(1)] = strip_yaml_scalar(match.group(2) or "")
    if closing is None:
        return fields, 0
    return fields, closing + 1


def split_wiki_target(raw: str) -> tuple[str, str]:
    """Return file and anchor, accepting both ``|`` and Markdown ``\\|`` aliases."""

    # A pipe cannot occur in a Windows Vault filename.  In Markdown tables the
    # alias separator is written as \|, so removing the escape before the pipe
    # avoids leaving a false trailing path separator.
    target = raw.split("|", 1)[0]
    if target.endswith("\\"):
        target = target[:-1]
    target = target.strip()
    if "#" in target:
        file_part, anchor = target.split("#", 1)
    else:
        file_part, anchor = target, ""
    # Preserve a leading ./ or ../ so the resolver can apply source-relative
    # semantics before considering Vault-root or basename resolution.
    return file_part.strip().replace("\\", "/").lstrip("/"), anchor.strip()


def iter_body_lines(document: Document) -> Iterable[tuple[int, str]]:
    lines = document.text.splitlines()
    in_fence = False
    fence_marker = ""
    for number, line in enumerate(lines[document.body_start :], start=document.body_start + 1):
        stripped = line.lstrip()
        if stripped.startswith(("```", "~~~")):
            marker = stripped[:3]
            if not in_fence:
                in_fence = True
                fence_marker = marker
            elif marker == fence_marker:
                in_fence = False
                fence_marker = ""
            continue
        if not in_fence:
            yield number, INLINE_CODE.sub("", line)


def wiki_links(document: Document) -> list[WikiLinkRef]:
    links: list[WikiLinkRef] = []
    for line_number, line in iter_body_lines(document):
        for match in WIKI_LINK.finditer(line):
            raw = match.group(1)
            file_part, anchor = split_wiki_target(raw)
            links.append(WikiLinkRef(raw, file_part, anchor, line_number))
    return links


def normalized_heading(value: str) -> str:
    value = value.strip().rstrip("#").strip()
    value = value.replace("\\#", "#")
    value = re.sub(r"[*_`~]", "", value)
    return " ".join(value.split()).casefold()


def markdown_anchors(document: Document) -> tuple[set[str], set[str]]:
    headings: set[str] = set()
    blocks: set[str] = set()
    for _, line in iter_body_lines(document):
        heading_match = ATX_HEADING.match(line)
        if heading_match:
            headings.add(normalized_heading(heading_match.group(2)))
        block_match = BLOCK_ID.search(line)
        if block_match:
            blocks.add(block_match.group(1).casefold())
    return headings, blocks


def iter_files(root: Path) -> Iterable[Path]:
    for directory, dirnames, filenames in os.walk(root):
        dirnames[:] = [name for name in dirnames if name not in IGNORED_DIRECTORIES]
        base = Path(directory)
        for filename in filenames:
            yield base / filename


class VaultIndex:
    def __init__(self, root: Path) -> None:
        self.root = root.resolve()
        self.files: dict[str, Path] = {}
        self.by_name: dict[str, list[str]] = defaultdict(list)
        self.by_stem: dict[str, list[str]] = defaultdict(list)
        self.documents: dict[str, Document] = {}
        self._anchor_cache: dict[str, tuple[set[str], set[str]]] = {}

        for path in iter_files(self.root):
            relative = path.relative_to(self.root).as_posix()
            self.files[relative] = path
            self.by_name[path.name.casefold()].append(relative)
            self.by_stem[path.stem.casefold()].append(relative)

        for relative, path in self.files.items():
            if path.suffix.lower() != ".md":
                continue
            try:
                text = path.read_text(encoding="utf-8-sig")
            except (OSError, UnicodeError):
                continue
            fields, body_start = parse_frontmatter(text)
            self.documents[relative] = Document(relative, fields, text, body_start)

    def _exact(self, value: str) -> list[str]:
        if value in self.files:
            return [value]
        return []

    def resolve(self, source: str, target: str) -> ResolveResult:
        if not target:
            return ResolveResult("resolved", (source,))
        if is_external_target(target):
            return ResolveResult("external", ())

        target_path = target.strip().replace("\\", "/")
        source_relative = target_path.startswith(("./", "../"))
        normalized = normalize_rel(target_path)
        candidates: set[str] = set()

        if source_relative:
            source_parent = PurePosixPath(source).parent.as_posix()
            relative_candidate = posixpath.normpath(
                posixpath.join(source_parent, target_path)
            )
            if relative_candidate != ".." and not relative_candidate.startswith("../"):
                candidates.update(self._exact(relative_candidate))
                candidates.update(self._exact(f"{relative_candidate}.md"))
            ordered = tuple(sorted(candidates))
            if not ordered:
                return ResolveResult("missing", ())
            if len(ordered) > 1:
                return ResolveResult("ambiguous", ordered)
            return ResolveResult("resolved", ordered)

        # Exact Vault paths are authoritative.  Appending .md is attempted even
        # when the title contains a dot, so v6.3 is not mistaken for extension .3.
        candidates.update(self._exact(normalized))
        candidates.update(self._exact(f"{normalized}.md"))

        if not candidates and "/" in normalized:
            # Obsidian accepts unique partial Vault paths.  Match both literal
            # filenames and Markdown paths without the final .md.
            folded = normalized.casefold()
            for relative in self.files:
                rel_folded = relative.casefold()
                markdown_no_ext = (
                    relative[:-3].casefold() if relative.lower().endswith(".md") else rel_folded
                )
                if (
                    rel_folded == folded
                    or markdown_no_ext == folded
                    or rel_folded.endswith(f"/{folded}")
                    or markdown_no_ext.endswith(f"/{folded}")
                ):
                    candidates.add(relative)

        if not candidates and "/" not in normalized:
            folded = normalized.casefold()
            candidates.update(self.by_name.get(folded, []))
            candidates.update(self.by_name.get(f"{folded}.md", []))
            candidates.update(self.by_stem.get(folded, []))

        ordered = tuple(sorted(candidates))
        if not ordered:
            return ResolveResult("missing", ())
        if len(ordered) > 1:
            return ResolveResult("ambiguous", ordered)
        return ResolveResult("resolved", ordered)

    def anchors(self, relative: str) -> tuple[set[str], set[str]]:
        if relative not in self._anchor_cache:
            document = self.documents.get(relative)
            self._anchor_cache[relative] = (
                markdown_anchors(document) if document is not None else (set(), set())
            )
        return self._anchor_cache[relative]


def is_named_moc(relative: str) -> bool:
    path = PurePosixPath(relative)
    if relative == HOME:
        return True
    if relative == "90_템플릿/인덱스_MOC_템플릿.md":
        return False
    return path.name.startswith("00_") and ("목차" in path.name or "MOC" in path.name)


def has_reference_boundary(relative: str) -> bool:
    return any(part.casefold() in REFERENCE_PARTS for part in PurePosixPath(relative).parts)


def inventory_documents(
    index: VaultIndex,
) -> tuple[set[str], set[str], dict[str, str], list[Finding]]:
    mocs: set[str] = set()
    controls: set[str] = set()
    excluded_mocs: dict[str, str] = {}
    findings: list[Finding] = []

    for relative, document in index.documents.items():
        note_type = document.fields.get("type", "")
        status = document.fields.get("status", "")
        named_moc = is_named_moc(relative)
        typed_moc = note_type == "moc"
        known_control = relative in KNOWN_CONTROLS
        typed_control = note_type == "control"

        if relative.startswith("90_템플릿/") and relative != "90_템플릿/00_템플릿_목차.md":
            if typed_moc:
                excluded_mocs[relative] = "template-example"
            continue

        if named_moc or typed_moc:
            if has_reference_boundary(relative):
                excluded_mocs[relative] = "legacy-reference"
                if status in OPERATIONAL_STATUSES:
                    findings.append(
                        Finding(
                            "ERROR",
                            "OPERATIONAL_REFERENCE_MOC",
                            relative,
                            f"reference/legacy 경로의 MOC가 operational status {status!r}를 사용함",
                        )
                    )
                continue
            if status in NON_OPERATIONAL_STATUSES:
                excluded_mocs[relative] = status
                continue
            mocs.add(relative)
            if note_type != "moc":
                findings.append(
                    Finding("ERROR", "MOC_TYPE", relative, "운영 MOC의 type이 moc가 아님")
                )
            if status not in OPERATIONAL_STATUSES:
                findings.append(
                    Finding(
                        "ERROR",
                        "MOC_STATUS",
                        relative,
                        f"운영 MOC의 status가 없거나 비표준임: {status or '(missing)'}",
                    )
                )
            for key in ("created", "scope"):
                if not document.fields.get(key):
                    findings.append(
                        Finding("ERROR", "MOC_METADATA", relative, f"필수 field 없음: {key}")
                    )

        if known_control or typed_control:
            if status in NON_OPERATIONAL_STATUSES and not known_control:
                continue
            controls.add(relative)
            if note_type != "control":
                findings.append(
                    Finding(
                        "ERROR", "CONTROL_TYPE", relative, "운영 control 문서의 type이 control이 아님"
                    )
                )
            if status not in OPERATIONAL_STATUSES:
                findings.append(
                    Finding(
                        "ERROR",
                        "CONTROL_STATUS",
                        relative,
                        f"운영 control의 status가 없거나 비표준임: {status or '(missing)'}",
                    )
                )
            for key in ("created", "scope"):
                if not document.fields.get(key):
                    findings.append(
                        Finding("ERROR", "CONTROL_METADATA", relative, f"필수 field 없음: {key}")
                    )

    for known in sorted(KNOWN_CONTROLS):
        if known not in index.documents:
            findings.append(
                Finding("ERROR", "MISSING_CONTROL", known, "필수 control 문서가 존재하지 않음")
            )

    if HOME not in index.documents:
        findings.append(Finding("ERROR", "MISSING_HOME", HOME, "Home 문서가 존재하지 않음"))
    elif HOME not in mocs:
        findings.append(Finding("ERROR", "HOME_NOT_MOC", HOME, "Home이 운영 MOC로 분류되지 않음"))

    return mocs, controls, excluded_mocs, findings


def validate_links(
    index: VaultIndex, operating: Iterable[str]
) -> tuple[dict[str, set[str]], list[Finding], dict[str, int]]:
    resolved_links: dict[str, set[str]] = defaultdict(set)
    findings: list[Finding] = []
    counters = {"checked": 0, "external_skipped": 0, "asset_targets": 0}

    for source in sorted(operating):
        document = index.documents[source]
        for link in wiki_links(document):
            if is_external_target(link.file_part):
                counters["external_skipped"] += 1
                continue
            counters["checked"] += 1
            result = index.resolve(source, link.file_part)
            if result.state == "missing":
                findings.append(
                    Finding(
                        "ERROR",
                        "BROKEN_WIKI_LINK",
                        source,
                        f"target 없음: [[{link.raw}]]",
                        link.line,
                    )
                )
                continue
            if result.state == "ambiguous":
                findings.append(
                    Finding(
                        "ERROR",
                        "AMBIGUOUS_WIKI_LINK",
                        source,
                        f"target 모호: [[{link.raw}]] -> {', '.join(result.candidates)}",
                        link.line,
                    )
                )
                continue
            if result.state == "external":
                counters["external_skipped"] += 1
                continue

            target = result.candidates[0]
            resolved_links[source].add(target)
            if not target.lower().endswith(".md"):
                counters["asset_targets"] += 1
                continue
            if not link.anchor:
                continue

            headings, blocks = index.anchors(target)
            if link.anchor.startswith("^"):
                block = link.anchor[1:].casefold()
                if block not in blocks:
                    findings.append(
                        Finding(
                            "ERROR",
                            "MISSING_BLOCK",
                            source,
                            f"block 없음: [[{link.raw}]] -> {target}",
                            link.line,
                        )
                    )
            elif normalized_heading(link.anchor) not in headings:
                findings.append(
                    Finding(
                        "ERROR",
                        "MISSING_HEADING",
                        source,
                        f"heading 없음: [[{link.raw}]] -> {target}",
                        link.line,
                    )
                )

    return resolved_links, findings, counters


def frontmatter_target(value: str) -> str:
    match = WIKI_LINK.search(value)
    if match:
        file_part, _ = split_wiki_target(match.group(1))
        return file_part
    return normalize_rel(value)


def validate_parent_reciprocity(
    index: VaultIndex,
    mocs: set[str],
    resolved_links: dict[str, set[str]],
) -> list[Finding]:
    findings: list[Finding] = []
    for child in sorted(mocs):
        document = index.documents[child]
        parent_value = document.fields.get("parent_moc", "").strip()

        if child == HOME:
            if parent_value.casefold() not in {"none", "null"}:
                findings.append(
                    Finding(
                        "ERROR",
                        "HOME_PARENT",
                        child,
                        "Home의 parent_moc는 none이어야 함",
                    )
                )
            continue

        if not parent_value:
            findings.append(
                Finding("ERROR", "MISSING_PARENT_MOC", child, "parent_moc field가 없음")
            )
            continue

        parent_target = frontmatter_target(parent_value)
        result = index.resolve(child, parent_target)
        if result.state == "missing":
            findings.append(
                Finding(
                    "ERROR",
                    "BROKEN_PARENT_MOC",
                    child,
                    f"parent_moc target 없음: {parent_value}",
                )
            )
            continue
        if result.state == "ambiguous":
            findings.append(
                Finding(
                    "ERROR",
                    "AMBIGUOUS_PARENT_MOC",
                    child,
                    f"parent_moc target 모호: {', '.join(result.candidates)}",
                )
            )
            continue

        parent = result.candidates[0]
        if parent not in mocs:
            findings.append(
                Finding(
                    "ERROR",
                    "NON_OPERATIONAL_PARENT",
                    child,
                    f"parent_moc가 운영 MOC가 아님: {parent}",
                )
            )
            continue
        if child not in resolved_links.get(parent, set()):
            findings.append(
                Finding(
                    "ERROR",
                    "PARENT_NOT_RECIPROCAL",
                    child,
                    f"선언된 parent가 child를 body wiki link로 가리키지 않음: {parent}",
                )
            )
    return findings


def validate_reachability(
    mocs: set[str],
    controls: set[str],
    resolved_links: dict[str, set[str]],
) -> tuple[set[str], set[str], list[Finding]]:
    reached_mocs: set[str] = set()
    reached_controls: set[str] = set()
    findings: list[Finding] = []
    queue: deque[str] = deque([HOME] if HOME in mocs else [])

    while queue:
        source = queue.popleft()
        if source in reached_mocs:
            continue
        reached_mocs.add(source)
        for target in resolved_links.get(source, set()):
            if target in mocs and target not in reached_mocs:
                queue.append(target)
            if target in controls:
                reached_controls.add(target)

    for path in sorted(mocs - reached_mocs):
        findings.append(
            Finding("ERROR", "UNREACHABLE_MOC", path, "Home의 MOC route로 도달할 수 없음")
        )
    for path in sorted(controls - reached_controls):
        findings.append(
            Finding(
                "ERROR",
                "UNREACHABLE_CONTROL",
                path,
                "Home에서 운영 MOC route를 통해 도달할 수 없음",
            )
        )
    return reached_mocs, reached_controls, findings


def classify_unlinked(relative: str, document: Document) -> str:
    path = PurePosixPath(relative)
    fields = document.fields
    status = fields.get("status", "")
    note_type = fields.get("type", "")
    folded_parts = {part.casefold() for part in path.parts}
    folded_name = path.name.casefold()

    if relative.startswith("90_템플릿/"):
        return "template-example"
    if status in NON_OPERATIONAL_STATUSES or folded_parts & REFERENCE_PARTS:
        return "legacy-reference"
    if (
        relative.startswith("40_자료/")
        or note_type in {"raw", "source-digest", "project-raw-log"}
        or "rds_note_materials" in folded_parts
        or "coverage map" in folded_name
        or "재료" in path.name
    ):
        return "material-source"
    if status == "draft":
        return "draft"
    if status in {"active", "stable"}:
        return "review-required"
    return "unclassified-review"


def not_directly_linked_from_operating_moc(
    index: VaultIndex,
    mocs: set[str],
    controls: set[str],
    resolved_links: dict[str, set[str]],
) -> dict[str, list[str]]:
    linked_from_moc = {
        target
        for source in mocs
        for target in resolved_links.get(source, set())
        if target.lower().endswith(".md")
    }
    excluded = mocs | controls | ROOT_DOC_EXCEPTIONS
    classified: dict[str, list[str]] = defaultdict(list)
    for relative, document in index.documents.items():
        if relative in excluded or relative in linked_from_moc:
            continue
        classified[classify_unlinked(relative, document)].append(relative)
    return {key: sorted(value) for key, value in sorted(classified.items())}


def duplicate_markdown_basenames(index: VaultIndex) -> list[dict[str, object]]:
    by_stem: dict[str, list[str]] = defaultdict(list)
    display: dict[str, str] = {}
    for relative in index.documents:
        stem = PurePosixPath(relative).stem
        folded = stem.casefold()
        by_stem[folded].append(relative)
        display.setdefault(folded, stem)
    return [
        {"basename": display[key], "paths": sorted(paths)}
        for key, paths in sorted(by_stem.items())
        if len(paths) > 1
    ]


def audit(root: Path) -> dict[str, object]:
    index = VaultIndex(root)
    mocs, controls, excluded_mocs, findings = inventory_documents(index)
    resolved_links, link_findings, link_counts = validate_links(index, mocs | controls)
    findings.extend(link_findings)
    findings.extend(validate_parent_reciprocity(index, mocs, resolved_links))
    reached_mocs, reached_controls, reachability_findings = validate_reachability(
        mocs, controls, resolved_links
    )
    findings.extend(reachability_findings)

    findings.sort(key=lambda item: (item.level != "ERROR", item.path, item.line or 0, item.code))
    errors = sum(item.level == "ERROR" for item in findings)
    warnings = sum(item.level == "WARN" for item in findings)
    not_directly_linked = not_directly_linked_from_operating_moc(
        index, mocs, controls, resolved_links
    )

    return {
        "root": str(index.root),
        "summary": {
            "markdown_files": len(index.documents),
            "operating_mocs": len(mocs),
            "operating_controls": len(controls),
            "excluded_mocs": len(excluded_mocs),
            "home_reachable_mocs": len(reached_mocs),
            "home_reachable_controls": len(reached_controls),
            "wiki_links_checked": link_counts["checked"],
            "asset_targets": link_counts["asset_targets"],
            "external_targets_skipped": link_counts["external_skipped"],
            "not_directly_linked_from_operating_moc": sum(
                len(paths) for paths in not_directly_linked.values()
            ),
            "errors": errors,
            "warnings": warnings,
        },
        "operating_mocs": sorted(mocs),
        "operating_controls": sorted(controls),
        "excluded_mocs": [
            {"path": path, "reason": reason}
            for path, reason in sorted(excluded_mocs.items())
        ],
        "duplicate_markdown_basenames": duplicate_markdown_basenames(index),
        "not_directly_linked_from_operating_moc": not_directly_linked,
        "findings": [asdict(item) for item in findings],
    }


def print_text(report: dict[str, object]) -> None:
    summary = report["summary"]
    assert isinstance(summary, dict)
    print(f"Vault navigation audit: {report['root']}")
    print(
        "Summary: "
        f"{summary['operating_mocs']} operating MOC(s), "
        f"{summary['operating_controls']} control(s), "
        f"Home reach {summary['home_reachable_mocs']}/{summary['operating_mocs']} MOC(s) "
        f"and {summary['home_reachable_controls']}/{summary['operating_controls']} control(s), "
        f"{summary['wiki_links_checked']} wiki link(s), "
        f"{summary['errors']} error(s), {summary['warnings']} warning(s)"
    )

    findings = report["findings"]
    assert isinstance(findings, list)
    if findings:
        print("\nStructural findings:")
        for finding in findings:
            assert isinstance(finding, dict)
            location = finding["path"]
            if finding.get("line"):
                location = f"{location}:{finding['line']}"
            print(
                f"- {finding['level']} {finding['code']} {location}: {finding['message']}"
            )

    duplicates = report["duplicate_markdown_basenames"]
    assert isinstance(duplicates, list)
    print(f"\nDuplicate Markdown basenames (informational): {len(duplicates)}")
    for item in duplicates:
        assert isinstance(item, dict)
        print(f"- {item['basename']}: {', '.join(item['paths'])}")

    not_directly_linked = report["not_directly_linked_from_operating_moc"]
    assert isinstance(not_directly_linked, dict)
    print(
        "\nMarkdown not directly linked from an operating MOC body "
        f"(classified, informational): "
        f"{summary['not_directly_linked_from_operating_moc']}"
    )
    for category, paths in not_directly_linked.items():
        print(f"- {category} ({len(paths)})")
        for path in paths:
            print(f"  - {path}")


def self_test() -> None:
    assert split_wiki_target(r"Folder/Runbook v6.3\|alias") == (
        "Folder/Runbook v6.3",
        "",
    )
    assert split_wiki_target("NFS 4.29.1#Current|alias") == ("NFS 4.29.1", "Current")
    assert split_wiki_target("./Target|alias") == ("./Target", "")

    # Exercise the resolver without writing test fixtures to the repository.
    index = object.__new__(VaultIndex)
    index.root = Path.cwd()
    index.files = {
        "Folder/Runbook v6.3.md": Path("Runbook v6.3.md"),
        "Folder/NFS 4.29.1.pdf": Path("NFS 4.29.1.pdf"),
        "Folder/Target.md": Path("Folder/Target.md"),
        "Other/Target.md": Path("Other/Target.md"),
        "A/Duplicate.md": Path("A/Duplicate.md"),
        "B/Duplicate.md": Path("B/Duplicate.md"),
    }
    index.by_name = defaultdict(list)
    index.by_stem = defaultdict(list)
    for relative in index.files:
        path = PurePosixPath(relative)
        index.by_name[path.name.casefold()].append(relative)
        index.by_stem[path.stem.casefold()].append(relative)
    index.documents = {}
    index._anchor_cache = {}

    assert index.resolve("Folder/Source.md", "Folder/Runbook v6.3").candidates == (
        "Folder/Runbook v6.3.md",
    )
    assert index.resolve("Folder/Source.md", "Runbook v6.3").candidates == (
        "Folder/Runbook v6.3.md",
    )
    assert index.resolve("Folder/Source.md", "Folder/NFS 4.29.1.pdf").candidates == (
        "Folder/NFS 4.29.1.pdf",
    )
    assert index.resolve("Folder/Source.md", "Duplicate").state == "ambiguous"
    assert index.resolve("Folder/Source.md", "./Target").candidates == (
        "Folder/Target.md",
    )
    assert index.resolve("Folder/Sub/Source.md", "../Target").candidates == (
        "Folder/Target.md",
    )
    assert index.resolve("Folder/Source.md", "Target").state == "ambiguous"

    document = Document(
        "Folder/Runbook v6.3.md",
        {},
        "# Runbook\n## Current\nproof ^proof-1\n```text\n## Not a heading\n```\n",
        0,
    )
    headings, blocks = markdown_anchors(document)
    assert normalized_heading("Current") in headings
    assert normalized_heading("Not a heading") not in headings
    assert "proof-1" in blocks

    link_document = Document(
        "Folder/Source.md",
        {},
        r"- [[Folder/Runbook v6.3#Current\|alias]]" + "\n",
        0,
    )
    parsed = wiki_links(link_document)
    assert len(parsed) == 1
    assert parsed[0].file_part == "Folder/Runbook v6.3"
    assert parsed[0].anchor == "Current"

    print(
        "Self-test passed: aliases, relative/dotted paths, headings, blocks, "
        "assets, ambiguity"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".", help="Vault root (default: current directory)")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    parser.add_argument("--self-test", action="store_true", help="Run isolated parser/graph tests")
    args = parser.parse_args()

    if args.self_test:
        self_test()
        return 0

    report = audit(Path(args.root))
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print_text(report)
    summary = report["summary"]
    assert isinstance(summary, dict)
    return 1 if int(summary["errors"]) else 0


if __name__ == "__main__":
    sys.exit(main())
