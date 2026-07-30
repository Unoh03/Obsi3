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
OUTPUT_PATH = ROOT / "운호_매일_지워도_다시_살아나는_AWS_실험환경.html"
VENDOR = ROOT / "vendor"


def e(value: Any) -> str:
    return html.escape(str(value), quote=True)


def safe_script(source: str) -> str:
    return source.replace("</script>", r"<\/script>")


def read_text(path: Path) -> str:
    if not path.is_file():
        raise FileNotFoundError(f"Required file is missing: {path}")
    return path.read_text(encoding="utf-8")


def status_badge(status: str) -> str:
    labels = {
        "verified": ("검증 완료", "status-verified"),
        "pending": ("미검증", "status-pending"),
        "partial": ("부분 검증", "status-partial"),
    }
    label, css_class = labels.get(status, (status, "status-neutral"))
    return f'<span class="status-chip {css_class}"><span></span>{e(label)}</span>'


def render_metrics(items: list[dict[str, Any]]) -> str:
    cards = []
    for item in items:
        cards.append(
            f"""
            <article class="metric-card tone-{e(item['tone'])}">
              <div class="metric-value">{e(item['value'])}</div>
              <div class="metric-label">{e(item['label'])}</div>
              <div class="metric-detail">{e(item['detail'])}</div>
            </article>
            """
        )
    return "\n".join(cards)


def render_list(items: list[str], css_class: str = "check-list") -> str:
    return (
        f'<ul class="{css_class}">'
        + "".join(f"<li>{e(item)}</li>" for item in items)
        + "</ul>"
    )


def render_delivery_steps(items: list[dict[str, Any]]) -> str:
    rendered = []
    for item in items:
        rendered.append(
            f"""
            <article class="delivery-step">
              <div class="step-index">{e(item['index'])}</div>
              <div class="step-content">
                <div class="step-title">{e(item['title'])}</div>
                <code class="step-value">{e(item['value'])}</code>
                <p>{e(item['detail'])}</p>
              </div>
            </article>
            """
        )
    return "\n".join(rendered)


def render_decisions(items: list[dict[str, Any]]) -> str:
    cards = []
    for item in items:
        cards.append(
            f"""
            <article class="decision-card">
              <div class="decision-head">
                <h3>{e(item['title'])}</h3>
                {status_badge(item['status'])}
              </div>
              <dl class="decision-grid">
                <div>
                  <dt>문제</dt>
                  <dd>{e(item['problem'])}</dd>
                </div>
                <div>
                  <dt>판단</dt>
                  <dd>{e(item['decision'])}</dd>
                </div>
                <div>
                  <dt>효과</dt>
                  <dd>{e(item['effect'])}</dd>
                </div>
              </dl>
            </article>
            """
        )
    return "\n".join(cards)


def render_automation_column(
    title: str, data: dict[str, Any], tone: str
) -> str:
    steps = "".join(
        f"""
        <li>
          <span class="automation-dot"></span>
          <span>{e(step)}</span>
        </li>
        """
        for step in data["steps"]
    )
    return f"""
      <article class="automation-column automation-{tone}">
        <div class="automation-kicker">{e(title)}</div>
        <pre class="command-block"><code class="language-powershell">{e(data['command'])}</code></pre>
        <ol class="automation-list">{steps}</ol>
      </article>
    """


def render_troubleshooting(items: list[dict[str, Any]]) -> str:
    rows = []
    for index, item in enumerate(items, start=1):
        rows.append(
            f"""
            <article class="incident-row">
              <div class="incident-number">{index:02d}</div>
              <div class="incident-main">
                <h3>{e(item['symptom'])}</h3>
                <div class="incident-grid">
                  <div>
                    <span class="cell-label">원인</span>
                    <p>{e(item['cause'])}</p>
                  </div>
                  <div>
                    <span class="cell-label">조치</span>
                    <p>{e(item['action'])}</p>
                  </div>
                  <div>
                    <span class="cell-label">재검증</span>
                    <p class="proof-text">{e(item['proof'])}</p>
                  </div>
                </div>
              </div>
            </article>
            """
        )
    return "\n".join(rows)


def render_verification(items: list[dict[str, Any]]) -> str:
    rows = []
    for item in items:
        result_class = (
            "result-pass" if item["status"] == "verified" else "result-pending"
        )
        rows.append(
            f"""
            <tr>
              <td class="verification-item">{e(item['item'])}</td>
              <td><span class="result-pill {result_class}">{e(item['result'])}</span></td>
              <td>{e(item['evidence'])}</td>
              <td>{status_badge(item['status'])}</td>
            </tr>
            """
        )
    return "\n".join(rows)


def render_open_items(items: list[dict[str, Any]]) -> str:
    return "\n".join(
        f"""
        <article class="open-card">
          <span class="open-marker">NEXT</span>
          <h3>{e(item['title'])}</h3>
          <p>{e(item['detail'])}</p>
        </article>
        """
        for item in items
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
    problem = data["problem"]
    architecture = data["architecture"]
    delivery = data["delivery_flow"]
    automation = data["automation"]
    contribution = data["contribution"]

    replacements = {
        "{{TITLE}}": e(meta["title"]),
        "{{SUBTITLE}}": e(meta["subtitle"]),
        "{{AUTHOR}}": e(meta["author"]),
        "{{PROJECT}}": e(meta["project"]),
        "{{AS_OF}}": e(meta["as_of"]),
        "{{STATUS}}": e(meta["status"]),
        "{{STATUS_DETAIL}}": e(meta["status_detail"]),
        "{{ONE_LINER}}": e(meta["one_liner"]),
        "{{METRICS}}": render_metrics(data["metrics"]),
        "{{PROBLEM_EYEBROW}}": e(problem["eyebrow"]),
        "{{PROBLEM_TITLE}}": e(problem["title"]),
        "{{PROBLEM_DESCRIPTION}}": e(problem["description"]),
        "{{PROBLEM_BEFORE}}": render_list(problem["before"], "problem-list before-list"),
        "{{PROBLEM_AFTER}}": render_list(problem["after"], "problem-list after-list"),
        "{{ARCHITECTURE_TITLE}}": e(architecture["title"]),
        "{{ARCHITECTURE_CAPTION}}": e(architecture["caption"]),
        "{{ARCHITECTURE_MERMAID}}": e(architecture["mermaid"]),
        "{{DELIVERY_TITLE}}": e(delivery["title"]),
        "{{DELIVERY_CAPTION}}": e(delivery["caption"]),
        "{{DELIVERY_STEPS}}": render_delivery_steps(delivery["steps"]),
        "{{DECISIONS}}": render_decisions(data["decisions"]),
        "{{AUTOMATION_UP}}": render_automation_column(
            "DAILY UP", automation["up"], "up"
        ),
        "{{AUTOMATION_DOWN}}": render_automation_column(
            "DAILY DOWN", automation["down"], "down"
        ),
        "{{TROUBLESHOOTING}}": render_troubleshooting(
            data["troubleshooting"]
        ),
        "{{VERIFICATION}}": render_verification(data["verification"]),
        "{{TEAM_BASE}}": render_list(contribution["team_base"], "boundary-list"),
        "{{USER_LED}}": render_list(contribution["user_led"], "boundary-list"),
        "{{AI_ASSISTED}}": render_list(
            contribution["ai_assisted"], "boundary-list"
        ),
        "{{CONTRIBUTION_BOUNDARY}}": e(contribution["boundary"]),
        "{{OPEN_ITEMS}}": render_open_items(data["open_items"]),
        "{{SOURCES}}": render_sources(data["sources"]),
        "{{GENERATED_AT}}": e(
            datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S %Z")
        ),
        "{{TABLER_CSS}}": read_text(VENDOR / "tabler.min.css"),
        "{{PRISM_CSS}}": read_text(VENDOR / "prism-tomorrow.min.css"),
        "{{MERMAID_JS}}": safe_script(read_text(VENDOR / "mermaid.min.js")),
        "{{PRISM_JS}}": safe_script(read_text(VENDOR / "prism.min.js")),
        "{{PRISM_POWERSHELL_JS}}": safe_script(
            read_text(VENDOR / "prism-powershell.min.js")
        ),
        "{{PRISM_HCL_JS}}": safe_script(
            read_text(VENDOR / "prism-hcl.min.js")
        ),
    }

    page = template
    for marker, value in replacements.items():
        page = page.replace(marker, value)

    # Bundled third-party JavaScript can legitimately contain "{{...}}".
    # Only our all-caps template marker convention is treated as unresolved.
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
