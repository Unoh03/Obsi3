#!/usr/bin/env python3
from __future__ import annotations

import re
from pathlib import Path

NOTE = Path("20_팀 프로젝트/3차 프로젝트/8.19 멘토님과 상담.md")


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected exactly one match, found {count}")
    return text.replace(old, new, 1)


def replace_count(text: str, old: str, new: str, expected: int, label: str) -> str:
    count = text.count(old)
    if count != expected:
        raise RuntimeError(f"{label}: expected {expected} matches, found {count}")
    return text.replace(old, new)


def sub_once(text: str, pattern: str, replacement: str, label: str) -> str:
    updated, count = re.subn(pattern, replacement, text, count=1, flags=re.MULTILINE)
    if count != 1:
        raise RuntimeError(f"{label}: expected exactly one regex match, found {count}")
    return updated


def main() -> None:
    original = NOTE.read_text(encoding="utf-8")
    text = original

    # C01: 발표 슬라이드의 검증 상태도 Gate별 실제 범위와 일치시킨다.
    text = replace_once(
        text,
        "**현재 Runtime 검증**\n\n"
        "```text\n"
        "DVWA Push → Wazuh → Shuffle\n"
        "+\n"
        "5-Source Evidence 조사\n"
        "```",
        "**현재 Runtime 검증**\n\n"
        "```text\n"
        "DVWA → Wazuh Rule 100102 무해 하위 경로 N=3\n"
        "Rule 100103 Wazuh Integrator / Sanitizer G3 strict PASS\n"
        "Shuffle 인증·합성 Payload 왕복 G0~G2 PASS\n"
        "5-Source Evidence 조사\n\n"
        "실제 Rule 100103 Alert ↔ Shuffle Execution G4\n"
        "→ 현재 미완료\n"
        "```",
        "C01 slide runtime scope",
    )

    # C06/C09: 앞단 A/B/C 설명과 뒤의 A/B/C/D/E 모델 경계를 일치시킨다.
    text = replace_once(
        text,
        "정확히는 보통 다음 2~3개 구간으로 나눠 보는 것이 좋다.\n",
        "정확히는 보통 다음 2~3개 구간으로 나눠 보는 것이 좋다. 여기서는 Event부터 Wazuh 입력까지의 앞단 A/B/C를 설명하며, 전체 Event-to-Action은 뒤의 D/E까지 포함한다.\n",
        "C09 front-stage scope",
    )
    text = sub_once(
        text,
        r"^\| C\. SIEM Transport 지연.*$",
        "| C. SIEM Transport 지연 | AWS Destination에서 소비 가능한 Event를 실제 Wazuh 입력까지 전달하는 시간 | 10분 Poll 또는 Subscription → Lambda → SQS → Bridge → Wazuh | 프로젝트에서 가장 직접적으로 줄일 수 있는 구간 |",
        "C09 C interval table row",
    )
    text = replace_once(
        text,
        "[C] Wazuh Transport\n   ↓\nWazuh Rule 평가",
        "[C] Wazuh Transport\n   ↓\nWazuh 입력",
        "C09 front-stage diagram",
    )
    text = replace_once(
        text,
        "Event-driven\n≠ Source latency 0",
        "Event-driven\n≠ Telemetry 사용 가능 지연(A+B) 0",
        "C06 deprecated source latency wording",
    )
    text = replace_once(
        text,
        "Wazuh Rule 평가 시작                  ← Point",
        "Wazuh 입력                            ← Point",
        "C09 CloudFront diagram endpoint",
    )
    text = replace_count(
        text,
        "→ [C]\n→ Wazuh",
        "→ [C]\n→ Wazuh 입력",
        2,
        "C09 Standard/Real-time endpoint",
    )

    # C04/C10: 미구현 Vended/Real-time 경로를 확정 최적으로 표현하지 않는다.
    text = replace_once(
        text,
        "| Legacy보다 우선 검토 |",
        "| Target Candidate / Runtime 비교 필요 |",
        "C04 ALB vended final judgment",
    )
    text = replace_once(
        text,
        "| 조건부 최적 |",
        "| 조건부 Target Candidate |",
        "C10 CloudFront real-time final judgment",
    )

    # C10/C14: 보고서·발표용 축약 표현도 후보/경로별 검증 범위와 맞춘다.
    text = replace_once(
        text,
        "→ 현재 Runtime Baseline 유지",
        "→ 현재 검증된 경로별 Runtime Baseline 유지",
        "C14 slide baseline wording",
    )
    text = replace_once(
        text,
        "현재 구현은 Runtime으로 검증된 As-built다.",
        "현재 구현은 경로별 Runtime 검증 범위를 명시한 As-built다.",
        "C01 recommended As-built wording",
    )
    text = replace_once(
        text,
        "> `Source별 최적 Telemetry를 선택한다.`",
        "> `Source별 적합한 Telemetry 후보를 선택한다.`",
        "C10 shorthand candidate wording",
    )

    required = {
        "C01": "실제 Rule 100103 Alert ↔ Shuffle Execution G4\n→ 현재 미완료",
        "C04": "Target Candidate / Runtime 비교 필요",
        "C06": "Event-driven\n≠ Telemetry 사용 가능 지연(A+B) 0",
        "C09": "Wazuh 입력                            ← Point",
        "C10": "조건부 Target Candidate",
        "C14": "현재 검증된 경로별 Runtime Baseline 유지",
    }
    missing = [key for key, marker in required.items() if marker not in text]
    if missing:
        raise RuntimeError(f"missing final consistency anchors: {missing}")
    if text == original:
        raise RuntimeError("no changes produced")

    with NOTE.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)

    print(f"Finalized {NOTE}")
    print(f"Original bytes: {len(original.encode('utf-8'))}")
    print(f"Updated bytes: {len(text.encode('utf-8'))}")
    print("No document split performed.")


if __name__ == "__main__":
    main()
