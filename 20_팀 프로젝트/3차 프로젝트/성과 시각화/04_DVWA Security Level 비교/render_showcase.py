from __future__ import annotations

import html
import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
CONTENT_PATH = ROOT / "content.json"
TEMPLATE_PATH = ROOT / "template.html"
OUTPUT_PATH = ROOT / "운호_Low부터_Impossible까지_무엇이_달라지는가.html"
VENDOR = ROOT / "vendor"


def e(value: Any) -> str:
    return html.escape(str(value), quote=True)


def read_text(path: Path) -> str:
    if not path.is_file():
        raise FileNotFoundError(f"Required file is missing: {path}")
    return path.read_text(encoding="utf-8")


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


def render_levels(items: list[dict[str, Any]]) -> str:
    cards: list[str] = []
    for index, item in enumerate(items, start=1):
        cards.append(
            f"""
            <article class="level-card level-{e(item['tone'])}">
              <div class="level-index">0{index}</div>
              <div class="level-name">{e(item['name'])}</div>
              <div class="level-eyebrow">{e(item['eyebrow'])}</div>
              <p>{e(item['summary'])}</p>
              <div class="level-signal">{e(item['signal'])}</div>
            </article>
            """
        )
    return "\n".join(cards)


def render_cell(cell: dict[str, Any], level: str) -> str:
    return f"""
      <td class="level-cell cell-{e(level)}" data-label="{e(level.title())}">
        <strong>{e(cell['lead'])}</strong>
        <span>{e(cell['detail'])}</span>
      </td>
    """


def render_matrix(items: list[dict[str, Any]]) -> str:
    rows: list[str] = []
    for item in items:
        rows.append(
            f"""
            <tr>
              <th scope="row" class="module-cell">
                <span class="business-name">{e(item['business'])}</span>
                <span class="module-name">{e(item['module'])}</span>
                <code>{e(item['route'])}</code>
              </th>
              {render_cell(item['low'], 'low')}
              {render_cell(item['medium'], 'medium')}
              {render_cell(item['high'], 'high')}
              {render_cell(item['impossible'], 'impossible')}
              <td class="lesson-cell" data-label="핵심 교훈">{e(item['lesson'])}</td>
            </tr>
            """
        )
    return "\n".join(rows)


def render_patterns(items: list[dict[str, Any]]) -> str:
    cards: list[str] = []
    for index, item in enumerate(items, start=1):
        cards.append(
            f"""
            <article class="pattern-card">
              <div class="pattern-number">{index:02d}</div>
              <div class="pattern-copy">
                <div class="pattern-modules">{e(item['modules'])}</div>
                <h3>{e(item['title'])}</h3>
                <div class="pattern-compare">
                  <div class="pattern-weak">
                    <span>부분 방어</span>
                    <p>{e(item['weak'])}</p>
                  </div>
                  <div class="pattern-arrow" aria-hidden="true">→</div>
                  <div class="pattern-strong">
                    <span>근본 조치</span>
                    <p>{e(item['strong'])}</p>
                  </div>
                </div>
                <div class="pattern-verdict">{e(item['verdict'])}</div>
              </div>
            </article>
            """
        )
    return "\n".join(cards)


def render_list(items: list[str], css_class: str) -> str:
    return (
        f'<ul class="{e(css_class)}">'
        + "".join(f"<li>{e(item)}</li>" for item in items)
        + "</ul>"
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
        "{{LEVELS}}": render_levels(data["levels"]),
        "{{MATRIX_ROWS}}": render_matrix(data["matrix"]),
        "{{PATTERNS}}": render_patterns(data["patterns"]),
        "{{VERIFIED_LIST}}": render_list(
            boundaries["verified"], "boundary-list verified-list"
        ),
        "{{CAUTION_LIST}}": render_list(
            boundaries["cautions"], "boundary-list caution-list"
        ),
        "{{SOURCES}}": render_sources(data["sources"]),
        "{{GENERATED_AT}}": e(
            datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S %Z")
        ),
        "{{TABLER_CSS}}": read_text(VENDOR / "tabler.min.css"),
    }

    page = template
    for marker, value in replacements.items():
        page = page.replace(marker, value)

    leftovers = sorted(set(part for part in page.split() if part.startswith("{{")))
    if leftovers:
        raise RuntimeError(f"Unresolved template markers: {leftovers}")
    return page


def main() -> None:
    data = json.loads(read_text(CONTENT_PATH))
    page = build_page(data, read_text(TEMPLATE_PATH))
    OUTPUT_PATH.write_text(page, encoding="utf-8")
    print(f"Generated: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
