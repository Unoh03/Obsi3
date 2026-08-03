from __future__ import annotations

import html
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
CONTENT_PATH = ROOT / "content.json"
TEMPLATE_PATH = ROOT / "template.html"
OUTPUT_PATH = ROOT / "운호_BANK는_어디서_공격받을_수_있는가.html"
VENDOR = ROOT / "vendor"


def e(value: Any) -> str:
    return html.escape(str(value), quote=True)


def read_text(path: Path) -> str:
    if not path.is_file():
        raise FileNotFoundError(f"Required file is missing: {path}")
    return path.read_text(encoding="utf-8")


def safe_script(source: str) -> str:
    return source.replace("</script>", r"<\/script>")


def status_badge(status: str, label: str | None = None) -> str:
    labels = {
        "runtime": ("Runtime 근거", "status-runtime"),
        "verified": ("확인", "status-runtime"),
        "partial": ("부분 검증", "status-partial"),
        "implemented": ("구현 확인", "status-implemented"),
        "pending": ("미검증", "status-pending"),
        "na": ("해당 없음", "status-neutral"),
    }
    default_label, css_class = labels.get(status, (status, "status-neutral"))
    return (
        f'<span class="status-chip {css_class}"><span></span>'
        f"{e(label or default_label)}</span>"
    )


def render_metrics(items: list[dict[str, Any]]) -> str:
    return "\n".join(
        f"""
        <article class="metric-card tone-{e(item['tone'])}">
          <div class="metric-value">{e(item['value'])}</div>
          <div class="metric-label">{e(item['label'])}</div>
          <div class="metric-detail">{e(item['detail'])}</div>
        </article>
        """
        for item in items
    )


def render_list(items: list[str], css_class: str) -> str:
    return (
        f'<ul class="{e(css_class)}">'
        + "".join(f"<li>{e(item)}</li>" for item in items)
        + "</ul>"
    )


def render_surfaces(items: list[dict[str, Any]]) -> str:
    cards: list[str] = []
    for item in items:
        log_chips = "".join(
            f'<span class="log-chip">{e(log)}</span>' for log in item["logs"]
        )
        cards.append(
            f"""
            <article class="surface-card surface-{e(item['status'])}">
              <div class="surface-head">
                <div>
                  <span class="surface-group">{e(item['group'])}</span>
                  <h3>{e(item['business'])}</h3>
                </div>
                {status_badge(item['status'])}
              </div>
              <div class="engine-name">{e(item['engine'])}</div>
              <code class="route-path">{e(item['route'])}</code>
              <dl class="surface-detail">
                <div>
                  <dt>정상 업무</dt>
                  <dd>{e(item['normal'])}</dd>
                </div>
                <div>
                  <dt>공격 표면</dt>
                  <dd>{e(item['abuse'])}</dd>
                </div>
              </dl>
              <div class="log-row">{log_chips}</div>
              <p class="runtime-note">{e(item['runtime'])}</p>
            </article>
            """
        )
    return "\n".join(cards)


def render_journey(label: str, data: dict[str, Any], tone: str) -> str:
    steps = "".join(
        f"""
        <li>
          <span class="journey-number">{index:02d}</span>
          <span>{e(step)}</span>
        </li>
        """
        for index, step in enumerate(data["steps"], start=1)
    )
    return f"""
      <article class="journey-column journey-{tone}">
        <div class="journey-kicker">{e(label)}</div>
        <h3>{e(data['label'])}</h3>
        <ol>{steps}</ol>
      </article>
    """


def render_coverage(items: list[dict[str, Any]]) -> str:
    status_labels = {
        "verified": "확인",
        "partial": "부분",
        "pending": "미검증",
        "na": "N/A",
    }
    rows: list[str] = []
    for item in items:
        columns = (
            ("route", "Route"),
            ("execution", "행위 실행"),
            ("edge", "Edge 탐지"),
            ("application", "Application"),
            ("remediation", "조치 후"),
        )
        cells = "".join(
            f'<td data-label="{e(label)}">'
            f'{status_badge(item[key], status_labels.get(item[key]))}</td>'
            for key, label in columns
        )
        rows.append(
            f"""
            <tr>
              <th scope="row">{e(item['scenario'])}</th>
              {cells}
              <td class="coverage-note" data-label="판정 경계">{e(item['note'])}</td>
            </tr>
            """
        )
    return "\n".join(rows)


def render_extension_steps(items: list[str]) -> str:
    return "".join(
        f"""
        <li>
          <span>{index:02d}</span>
          <p>{e(item)}</p>
        </li>
        """
        for index, item in enumerate(items, start=1)
    )


def render_sources(items: list[dict[str, Any]]) -> str:
    return "\n".join(
        f"""
        <div class="source-row">
          <span class="source-type">{e(item['type'])}</span>
          <span class="source-label">{e(item['label'])}</span>
          <code>{e(item['value'])}</code>
        </div>
        """
        for item in items
    )


def build_page(data: dict[str, Any], template: str) -> str:
    meta = data["meta"]
    transformation = data["transformation"]
    atlas = data["atlas"]
    journeys = data["journeys"]
    extension = data["cloud_extension"]
    boundaries = data["boundaries"]

    replacements = {
        "{{TITLE}}": e(meta["title"]),
        "{{SUBTITLE}}": e(meta["subtitle"]),
        "{{AUTHOR}}": e(meta["author"]),
        "{{PROJECT}}": e(meta["project"]),
        "{{AS_OF}}": e(meta["as_of"]),
        "{{STATUS}}": e(meta["status"]),
        "{{ONE_LINER}}": e(meta["one_liner"]),
        "{{METRICS}}": render_metrics(data["metrics"]),
        "{{TRANSFORMATION_EYEBROW}}": e(transformation["eyebrow"]),
        "{{TRANSFORMATION_TITLE}}": e(transformation["title"]),
        "{{TRANSFORMATION_DESCRIPTION}}": e(transformation["description"]),
        "{{TRANSFORMATION_BEFORE}}": render_list(
            transformation["before"], "comparison-list before-list"
        ),
        "{{TRANSFORMATION_AFTER}}": render_list(
            transformation["after"], "comparison-list after-list"
        ),
        "{{ATLAS_TITLE}}": e(atlas["title"]),
        "{{ATLAS_CAPTION}}": e(atlas["caption"]),
        "{{ATLAS_MERMAID}}": e(atlas["mermaid"]),
        "{{SURFACES}}": render_surfaces(data["surfaces"]),
        "{{JOURNEY_TITLE}}": e(journeys["title"]),
        "{{JOURNEY_NORMAL}}": render_journey(
            "NORMAL PATH", journeys["normal"], "normal"
        ),
        "{{JOURNEY_ABUSE}}": render_journey(
            "ABUSE PATH", journeys["abuse"], "abuse"
        ),
        "{{COVERAGE_ROWS}}": render_coverage(data["coverage"]),
        "{{EXTENSION_TITLE}}": e(extension["title"]),
        "{{EXTENSION_DESCRIPTION}}": e(extension["description"]),
        "{{EXTENSION_STEPS}}": render_extension_steps(extension["steps"]),
        "{{EXTENSION_BOUNDARY}}": e(extension["boundary"]),
        "{{VERIFIED_LIST}}": render_list(
            boundaries["verified"], "boundary-list verified-list"
        ),
        "{{UNVERIFIED_LIST}}": render_list(
            boundaries["unverified"], "boundary-list unverified-list"
        ),
        "{{SOURCES}}": render_sources(data["sources"]),
        "{{GENERATED_AT}}": e(
            datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S %Z")
        ),
        "{{TABLER_CSS}}": read_text(VENDOR / "tabler.min.css"),
        "{{MERMAID_JS}}": safe_script(read_text(VENDOR / "mermaid.min.js")),
    }

    page = template
    for marker, value in replacements.items():
        page = page.replace(marker, value)

    unresolved = sorted(set(re.findall(r"\{\{[A-Z][A-Z0-9_]*\}\}", page)))
    if unresolved:
        raise RuntimeError(f"Unresolved template markers: {unresolved}")
    return page


def main() -> None:
    data = json.loads(read_text(CONTENT_PATH))
    template = read_text(TEMPLATE_PATH)
    page = build_page(data, template)
    OUTPUT_PATH.write_text(page, encoding="utf-8", newline="\n")
    print(f"Generated: {OUTPUT_PATH}")
    print(f"Bytes: {OUTPUT_PATH.stat().st_size:,}")


if __name__ == "__main__":
    main()
