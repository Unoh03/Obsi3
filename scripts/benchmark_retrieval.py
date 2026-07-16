#!/usr/bin/env python3
"""Validate and score evidence-first Vault retrieval traces.

The script deliberately does not simulate an LLM or invent a search ranking.
It validates a fixed gold set, then scores traces produced by real blind agent
runs.  Character counts cover only literal file slices recorded in a trace;
they are not token counts or total model-context measurements.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


WIKI_LINK = re.compile(r"\[\[([^\]]+)\]\]")
HEADING = re.compile(r"^(#{1,6})\s+(.+?)\s*$")


@dataclass(frozen=True)
class HeadingRange:
    title: str
    level: int
    start_line: int
    end_line: int
    chars: int


def normalize_path(value: str) -> str:
    return value.replace("\\", "/").lstrip("./")


def read_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"{path}: JSON을 읽을 수 없음: {exc}") from exc


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def markdown_headings(path: Path) -> list[HeadingRange]:
    lines = read_text(path).splitlines(keepends=True)
    found: list[tuple[str, int, int]] = []
    in_fence = False

    for index, line in enumerate(lines):
        stripped = line.rstrip("\r\n")
        if stripped.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        match = HEADING.match(stripped)
        if match:
            found.append((match.group(2).strip(), len(match.group(1)), index))

    ranges: list[HeadingRange] = []
    for position, (title, level, start) in enumerate(found):
        end = len(lines)
        for _, next_level, next_start in found[position + 1 :]:
            if next_level <= level:
                end = next_start
                break
        ranges.append(
            HeadingRange(
                title=title,
                level=level,
                start_line=start + 1,
                end_line=end,
                chars=len("".join(lines[start:end])),
            )
        )
    return ranges


def heading_range(path: Path, title: str) -> HeadingRange:
    matches = [item for item in markdown_headings(path) if item.title == title]
    if len(matches) != 1:
        raise ValueError(
            f"{path}: heading {title!r} 개수가 {len(matches)}개임 (정확히 1개 필요)"
        )
    return matches[0]


def wiki_targets(path: Path) -> list[str]:
    targets: list[str] = []
    for raw in WIKI_LINK.findall(read_text(path)):
        target = raw.split("|", 1)[0].split("#", 1)[0].strip()
        if target:
            targets.append(normalize_path(target))
    return targets


def path_variants(value: str) -> set[str]:
    normalized = normalize_path(value)
    variants = {normalized}
    if normalized.lower().endswith(".md"):
        variants.add(normalized[:-3])
    else:
        variants.add(f"{normalized}.md")
    return variants


def link_matches(link: str, target: str) -> bool:
    link_set = path_variants(link)
    target_set = path_variants(target)
    if link_set & target_set:
        return True
    if "/" not in link:
        target_name = Path(normalize_path(target)).name
        return bool(path_variants(link) & path_variants(target_name))
    return False


def validate_cases(root: Path, data: dict[str, Any]) -> tuple[list[dict[str, Any]], list[str]]:
    errors: list[str] = []
    cases = data.get("cases")
    if data.get("schema_version") != 1:
        errors.append("schema_version은 1이어야 함")
    if not isinstance(cases, list):
        return [], errors + ["cases는 배열이어야 함"]

    seen: set[str] = set()
    checked: list[dict[str, Any]] = []

    for case in cases:
        case_id = str(case.get("id", ""))
        if not case_id:
            errors.append("id가 없는 case가 있음")
            continue
        if case_id in seen:
            errors.append(f"{case_id}: 중복 id")
            continue
        seen.add(case_id)

        gold = case.get("gold", {})
        target_rel = normalize_path(str(gold.get("target", "")))
        target = root / target_rel
        if not target_rel or not target.is_file():
            errors.append(f"{case_id}: target 없음: {target_rel}")
            continue

        route = [normalize_path(str(item)) for item in gold.get("route", [])]
        route_paths = [root / item for item in route]
        for item, route_path in zip(route, route_paths):
            if not route_path.is_file():
                errors.append(f"{case_id}: route 파일 없음: {item}")
            elif route_path.suffix.lower() != ".md":
                errors.append(f"{case_id}: route는 Markdown이어야 함: {item}")

        if all(path.is_file() for path in route_paths):
            for source_rel, source, destination in zip(route, route_paths, route[1:]):
                if not any(link_matches(link, destination) for link in wiki_targets(source)):
                    errors.append(
                        f"{case_id}: route hop wiki link 없음: {source_rel} -> {destination}"
                    )

            locator = gold.get("locator", "direct")
            if route_paths and locator == "wiki":
                if not any(
                    link_matches(link, target_rel) for link in wiki_targets(route_paths[-1])
                ):
                    errors.append(
                        f"{case_id}: 마지막 route가 target을 wiki link하지 않음: "
                        f"{route[-1]} -> {target_rel}"
                    )
            elif route_paths and locator == "literal":
                hint = str(gold.get("target_hint", Path(target_rel).name))
                if hint not in read_text(route_paths[-1]):
                    errors.append(
                        f"{case_id}: 마지막 route에 literal target hint 없음: {hint}"
                    )
            elif locator not in {"direct", "wiki", "literal"}:
                errors.append(f"{case_id}: 알 수 없는 locator: {locator}")

        headings = gold.get("headings", [])
        if headings is None:
            headings = []
        if not isinstance(headings, list):
            errors.append(f"{case_id}: headings는 배열이어야 함")
            headings = []

        heading_info: list[dict[str, Any]] = []
        if headings and target.suffix.lower() != ".md":
            errors.append(f"{case_id}: 비 Markdown target에 headings가 있음")
        else:
            for title in headings:
                try:
                    item = heading_range(target, str(title))
                except ValueError as exc:
                    errors.append(f"{case_id}: {exc}")
                else:
                    heading_info.append(
                        {
                            "title": item.title,
                            "level": item.level,
                            "start_line": item.start_line,
                            "end_line": item.end_line,
                            "chars": item.chars,
                        }
                    )

        checked.append(
            {
                "id": case_id,
                "kind": case.get("kind"),
                "target": target_rel,
                "route": route,
                "target_chars": len(read_text(target)) if target.suffix.lower() == ".md" else None,
                "route_chars": sum(len(read_text(path)) for path in route_paths if path.is_file()),
                "heading_ranges": heading_info,
            }
        )

    return checked, errors


def normalized_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [normalize_path(value)]
    return [normalize_path(str(item)) for item in value]


def slice_chars(root: Path, item: dict[str, Any]) -> int:
    path = root / normalize_path(str(item.get("path", "")))
    if not path.is_file():
        raise ValueError(f"read range 파일 없음: {path}")
    lines = read_text(path).splitlines(keepends=True)
    start = int(item.get("start_line", item.get("start", 0)))
    end = int(item.get("end_line", item.get("end", 0)))
    if start < 1 or end < start or end > len(lines):
        raise ValueError(
            f"잘못된 read range: {path} {start}-{end} (전체 {len(lines)}줄)"
        )
    return len("".join(lines[start - 1 : end]))


def union_slice_chars(root: Path, path_value: str, items: list[dict[str, Any]]) -> int:
    path = root / normalize_path(path_value)
    lines = read_text(path).splitlines(keepends=True)
    selected: set[int] = set()
    for item in items:
        start = int(item.get("start_line", item.get("start", 0)))
        end = int(item.get("end_line", item.get("end", 0)))
        if start < 1 or end < start or end > len(lines):
            raise ValueError(
                f"잘못된 read range: {path} {start}-{end} (전체 {len(lines)}줄)"
            )
        selected.update(range(start - 1, end))
    return sum(len(lines[index]) for index in selected)


def score_run(root: Path, data: dict[str, Any], run: dict[str, Any]) -> dict[str, Any]:
    cases = {str(item["id"]): item for item in data["cases"]}
    results = run.get("results")
    if not isinstance(results, list):
        raise ValueError("run.results는 배열이어야 함")

    seen: set[str] = set()
    scored: list[dict[str, Any]] = []
    totals = {
        "cases": len(cases),
        "observed": 0,
        "final_hit": 0,
        "hit_at_1": 0,
        "hit_at_3": 0,
        "heading_hit": 0,
        "boundary_errors": 0,
        "budget_pass": 0,
        "recorded_slice_chars": 0,
    }

    for result in results:
        case_id = str(result.get("id", ""))
        if case_id not in cases:
            raise ValueError(f"run에 알 수 없는 case id가 있음: {case_id}")
        if case_id in seen:
            raise ValueError(f"run에 중복 case id가 있음: {case_id}")
        seen.add(case_id)
        case = cases[case_id]
        gold = case["gold"]
        target = normalize_path(str(gold["target"]))

        chosen = normalize_path(
            str(result.get("chosen_path") or result.get("chosen_evidence", {}).get("path") or "")
        )
        first = normalize_path(
            str(result.get("first_candidate") or result.get("first_leaf") or "")
        )
        candidates = normalized_list(result.get("candidate_paths"))
        leaf_reads = normalized_list(result.get("leaf_reads") or result.get("content_reads"))
        nav_reads = normalized_list(result.get("nav_reads"))
        if not candidates:
            candidates = leaf_reads.copy()
        if first and first not in candidates:
            candidates.insert(0, first)
        if not first and candidates:
            first = candidates[0]

        chosen_headings = result.get("chosen_headings")
        if chosen_headings is None:
            chosen_headings = result.get("chosen_evidence", {}).get("headings", [])
        if isinstance(chosen_headings, str):
            chosen_headings = [chosen_headings]
        chosen_headings = [str(item).lstrip("# ").strip() for item in chosen_headings or []]
        gold_headings = [str(item) for item in gold.get("headings", [])]

        acceptable_targets = {
            target,
            *(
                normalize_path(str(item))
                for item in gold.get("acceptable_evidence_targets", [])
            ),
        }
        final_hit = chosen in acceptable_targets
        hit_at_1 = first == target
        hit_at_3 = target in candidates[:3]
        heading_hit = final_hit and all(item in chosen_headings for item in gold_headings)

        forbidden = {normalize_path(str(item)) for item in case.get("forbidden_targets", [])}
        boundary_error = chosen in forbidden or any(item in forbidden for item in candidates[:1])

        target_before = 0
        if target in leaf_reads:
            target_before = leaf_reads.index(target)
        elif target not in nav_reads and target != chosen:
            target_before = len(leaf_reads)

        range_items = result.get("read_ranges", [])
        recorded_chars = sum(slice_chars(root, item) for item in range_items)
        target_ranges = [
            item
            for item in range_items
            if normalize_path(str(item.get("path", ""))) == target
        ]
        target_line_count = None
        full_target_read = False
        target_slice_chars = 0
        target_read_ratio = None
        target_path = root / target
        if target_path.suffix.lower() == ".md":
            target_line_count = len(read_text(target_path).splitlines())
            target_slice_chars = union_slice_chars(root, target, target_ranges)
            target_chars = len(read_text(target_path))
            target_read_ratio = target_slice_chars / target_chars if target_chars else 0.0
            full_target_read = any(
                int(item.get("start_line", item.get("start", 0))) == 1
                and int(item.get("end_line", item.get("end", 0))) >= target_line_count
                for item in target_ranges
            )

        budget = case.get("budget", {})
        budget_pass = (
            len(nav_reads) <= int(budget.get("max_nav_reads", 999))
            and target_before <= int(budget.get("max_leaf_reads_before_target", 999))
            and (
                not budget.get("section_required", False)
                or (bool(target_ranges) and not full_target_read)
            )
            and (
                "max_target_read_ratio" not in budget
                or (
                    target_read_ratio is not None
                    and target_read_ratio <= float(budget["max_target_read_ratio"])
                )
            )
        )

        totals["observed"] += 1
        totals["final_hit"] += int(final_hit)
        totals["hit_at_1"] += int(hit_at_1)
        totals["hit_at_3"] += int(hit_at_3)
        totals["heading_hit"] += int(heading_hit)
        totals["boundary_errors"] += int(boundary_error)
        totals["budget_pass"] += int(budget_pass)
        totals["recorded_slice_chars"] += recorded_chars

        scored.append(
            {
                "id": case_id,
                "final_hit": final_hit,
                "hit_at_1": hit_at_1,
                "hit_at_3": hit_at_3,
                "heading_hit": heading_hit,
                "boundary_error": boundary_error,
                "budget_pass": budget_pass,
                "nav_reads": len(nav_reads),
                "leaf_reads_before_target": target_before,
                "recorded_slice_chars": recorded_chars,
                "target_slice_chars": target_slice_chars,
                "target_read_ratio": (
                    round(target_read_ratio, 4) if target_read_ratio is not None else None
                ),
                "full_target_read": full_target_read,
            }
        )

    totals["missing_observations"] = sorted(set(cases) - seen)
    return {
        "run_id": run.get("run_id"),
        "strategy": run.get("strategy"),
        "commit": run.get("commit"),
        "totals": totals,
        "results": scored,
        "measurement_note": (
            "recorded_slice_chars는 trace에 기록된 실제 파일 범위의 문자 수이며 "
            "token 수나 전체 tool/context 비용이 아니다."
        ),
    }


def find_heading_start(path: Path, title: str) -> int:
    return heading_range(path, title).start_line


def build_prototype(root: Path, data: dict[str, Any], output: Path) -> list[Path]:
    spec = data.get("prototype")
    if not isinstance(spec, dict):
        raise ValueError("cases 파일에 prototype 정의가 없음")

    resolved_root = root.resolve()
    resolved_output = output.resolve()
    if resolved_output == resolved_root or resolved_root in resolved_output.parents:
        raise ValueError("prototype output은 저장소 밖의 임시 경로여야 함")

    source_rel = normalize_path(str(spec["source"]))
    source = root / source_rel
    raw = source.read_bytes()
    actual_hash = hashlib.sha256(raw).hexdigest().upper()
    expected_hash = str(spec["source_sha256"]).upper()
    if actual_hash != expected_hash:
        raise ValueError(
            f"prototype source SHA-256 불일치: expected={expected_hash}, actual={actual_hash}"
        )

    output.mkdir(parents=True, exist_ok=True)
    lines = read_text(source).splitlines(keepends=True)
    created: list[Path] = []
    part_links: list[str] = []
    previous: str | None = None

    for part in spec.get("parts", []):
        start = find_heading_start(source, str(part["start_heading"]))
        end_before = part.get("end_before_heading")
        end = find_heading_start(source, str(end_before)) - 1 if end_before else len(lines)
        name = str(part["file"])
        title = str(part["title"])
        next_name = None
        capsule = [
            f"> retrieval prototype only; canonical source: `{source_rel}`",
            f"> source_sha256: `{actual_hash}`",
            f"> source_range: `{start}-{end}`",
            f"> segment_role: `{part['role']}`",
            f"> previous_segment: `{previous or 'none'}`",
            f"> latest_verified_segment: `{spec['latest_verified_segment']}`",
            "",
        ]
        body = "\n".join(capsule) + "\n" + "".join(lines[start - 1 : end])
        destination = output / name
        destination.write_text(body, encoding="utf-8", newline="\n")
        created.append(destination)
        part_links.append(f"- [[{Path(name).stem}|{title}]] — `{start}-{end}`")
        previous = name

    hub_name = str(spec.get("hub_file", "v15-part8-prototype-hub.md"))
    hub = output / hub_name
    hub_text = "\n".join(
        [
            "# Terraform v15 Part 8 retrieval prototype",
            "",
            "> 비교 실험용 임시 라우터다. canonical 본문이 아니며 저장소에 넣지 않는다.",
            f"> source: `{source_rel}`",
            f"> source_sha256: `{actual_hash}`",
            "",
            "## 구간",
            "",
            *part_links,
            "",
        ]
    )
    hub.write_text(hub_text, encoding="utf-8", newline="\n")
    created.insert(0, hub)
    return created


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--cases",
        default="scripts/retrieval_cases_v1.json",
        help="gold case JSON path (default: scripts/retrieval_cases_v1.json)",
    )
    parser.add_argument("--run", help="blind agent trace JSON to score")
    parser.add_argument(
        "--build-prototype",
        metavar="DIR",
        help="build the temporary v15 split prototype outside the repository",
    )
    args = parser.parse_args()

    root = Path.cwd()
    cases_path = root / normalize_path(args.cases)
    try:
        data = read_json(cases_path)
        checked, errors = validate_cases(root, data)
        if errors:
            for error in errors:
                print(f"ERROR: {error}", file=sys.stderr)
            print(f"Checked {len(checked)} case(s): {len(errors)} error(s)", file=sys.stderr)
            return 1

        print(
            json.dumps(
                {
                    "checked_cases": len(checked),
                    "categories": {
                        kind: sum(1 for item in checked if item["kind"] == kind)
                        for kind in sorted({str(item["kind"]) for item in checked})
                    },
                    "route_chars": sum(item["route_chars"] for item in checked),
                    "gold_section_chars": sum(
                        section["chars"]
                        for item in checked
                        for section in item["heading_ranges"]
                    ),
                },
                ensure_ascii=False,
                indent=2,
            )
        )

        if args.build_prototype:
            created = build_prototype(root, data, Path(args.build_prototype))
            print(
                json.dumps(
                    {"prototype_files": [str(path) for path in created]},
                    ensure_ascii=False,
                    indent=2,
                )
            )

        if args.run:
            report = score_run(root, data, read_json(Path(args.run)))
            print(json.dumps(report, ensure_ascii=False, indent=2))
    except (KeyError, OSError, TypeError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
