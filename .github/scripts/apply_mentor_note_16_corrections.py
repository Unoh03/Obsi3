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


def sub_once(text: str, pattern: str, replacement: str, label: str, flags: int = 0) -> str:
    updated, count = re.subn(pattern, replacement, text, count=1, flags=flags)
    if count != 1:
        raise RuntimeError(f"{label}: expected exactly one regex match, found {count}")
    return updated


def main() -> None:
    original_bytes = NOTE.read_bytes()
    text = original_bytes.decode("utf-8")

    # 16. 원메모 상단 경고 + Q2 답변의 사용 범위
    if not text.startswith("PPT 발표\n"):
        raise RuntimeError("C16: unexpected file start")
    text = (
        "> [!WARNING] 상담 중 원메모\n"
        "> 아래 첫 구역은 상담 중 작성한 원메모로, 음성인식 오류·불완전한 답변·미검증 주장이 포함될 수 있다.\n"
        "> 외부 발표와 보고서의 사실 근거로 직접 사용하지 않으며, 뒤의 `상담 후 재정리`와 `후속 공식 검증 결과 — RESOLVED`를 최신 판정으로 본다.\n"
        ">\n"
        "> 특히 Q2의 DDoS 답변은 Alert 분리·Deduplication·Incident grouping의 핵심을 충분히 다루지 못했으므로 해당 설계의 근거로 사용하지 않는다.\n\n"
        + text
    )

    # 15. UNRESOLVED와 잠정 표를 강하게 SUPERSEDED 처리
    text = replace_once(
        text,
        "## 현재 잠정 해석 — UNRESOLVED\n",
        "> [!WARNING] SUPERSEDED\n"
        "> 아래 A/B는 당시 검토 중이던 가설이다. 최신 판정은 뒤의 `후속 공식 검증 결과 — RESOLVED`를 따른다.\n\n"
        "## 현재 잠정 해석 — UNRESOLVED\n",
        "C15 unresolved warning",
    )
    text = replace_once(
        text,
        "> [!NOTE]\n"
        "> 아래 기존 5-Source 표는 당시의 잠정 정리다. ALB의 CloudWatch Logs Vended Logs 같은 최신 공식 경로를 포함해 Source별 Route와 latency를 다시 검증한 뒤 최종 표로 교체한다.\n",
        "> [!WARNING] SUPERSEDED\n"
        "> 아래 5-Source 표는 당시의 잠정 정리이며 최신 판정으로 사용하지 않는다. 뒤의 `로그 Source × Telemetry × Route 비교 — 공식 문서 재검증` 표가 이를 대체한다.\n",
        "C15 provisional table warning",
    )

    # 1. G4 미완료 상태를 Gate별로 정정
    text = replace_once(
        text,
        "현재 검증 범위\n"
        "- DVWA 저지연 Push → Wazuh Rule 100103\n"
        "- Wazuh → Shuffle 전달 및 Runtime Evidence\n"
        "- 기존 5-Source 수집·조사 Evidence",
        "현재 검증 범위\n\n"
        "- DVWA→Wazuh 하위 경로 Runtime:\n"
        "  - 무해 Event 3건 → Rule 100102 Alert 3건\n"
        "  - 총지연 6.439 / 3.427 / 3.761초\n"
        "  - 누락 0건\n"
        "  - Shuffle은 포함하지 않음\n\n"
        "- G0~G2:\n"
        "  - Shuffle Workflow / Webhook 구조 검증\n"
        "  - 인증된 합성 Payload의 Webhook 왕복\n"
        "  - wrong/missing Header 거절\n"
        "  - 인증 실패 요청의 신규 Execution 0건\n\n"
        "- G3:\n"
        "  - Rule 100103 대상 Wazuh Integrator·Rule·Sanitizer·Secret 경계\n"
        "  - Manager 적용 및 strict Runtime PASS\n\n"
        "- G4:\n"
        "  - 실제 Rule 100103 Alert ↔ Shuffle Execution 일대일 Evidence\n"
        "  - 현재 미완료",
        "C01 validation scope",
    )
    text = replace_once(
        text,
        "완료하지 않은 Target을 현재 구현처럼 쓰지 않는다.",
        "완료하지 않은 Target을 현재 구현처럼 쓰지 않는다. G4 완료 전에는 `실제 Wazuh Alert → Shuffle Execution Runtime Evidence 확보` 또는 `자동 대응 완료`라고 쓰지 않으며, G4가 완료된 뒤 Evidence 경로와 SHA-256을 붙여 승격한다.",
        "C01 completion wording",
    )

    # 2. Lambda Function Logs 지연과 Logs API 분리
    text = replace_once(
        text,
        "| **Lambda Function Logs** | **공식 정성 표현:** CloudWatch Logs에서 real-time 조회/분석. 정량 latency 미공개 | Lambda → CWL → Subscription → SIEM | 애플리케이션·플랫폼 로그. Lambda Logs API Extension으로 직접 소비하는 고급 방식도 가능 |",
        "| **Lambda Function Logs → CloudWatch Logs** | **공식 수치:** 함수 호출 후 로그가 표시되기까지 **5~10분 걸릴 수 있음** | Lambda → CWL → Subscription → SIEM | 일반 CloudWatch Logs 경로를 `real-time`이라고 단정하지 않음. 더 저지연이 필요하면 Lambda Logs API Extension을 별도 메커니즘으로 검토 |\n"
        "| **Lambda Logs API Extension** | **별도 메커니즘:** 실행 환경에서 Telemetry stream을 Extension이 직접 구독 | Lambda Extension → Collector / SIEM | 일반 CWL 경로와 동일하지 않음. Extension 운영·실패·Backpressure 설계 필요 |",
        "C02 lambda rows",
    )

    # 3. GetObject 판정을 CONFIRMED / REJECTED / INCONCLUSIVE로 분리
    text = replace_once(
        text,
        "조사 결과\n"
        "├─ 실제 GetObject 성공 → CONFIRMED\n"
        "└─ 접근 성공 없음 → 미확정 또는 기각",
        "조사 결과\n"
        "├─ 공격 문맥과 상관 가능한 GetObject 성공 Evidence → CONFIRMED\n"
        "├─ 정상 Coverage + 동일 문맥의 명시적 AccessDenied/실패 Evidence → REJECTED / NOT CONFIRMED\n"
        "└─ 로그 부재 또는 Data Event Coverage·Delivery 불확실 → INCONCLUSIVE",
        "C03 incident tree",
    )
    text = replace_once(
        text,
        "실제 S3 `GetObject` 성공 여부는 CloudTrail 등 후속 Evidence로 확인.\n\n따라서 발표에서는 다음처럼 말하는 것이 정확함.",
        "실제 S3 `GetObject` 성공 여부는 CloudTrail 등 후속 Evidence로 확인.\n\n"
        "### `GetObject` 판정의 3분기\n\n"
        "#### CONFIRMED\n\n"
        "공격 문맥과 연결되는 성공 Evidence가 있어야 한다.\n\n"
        "- 동일하거나 상관 가능한 Principal / Role Session\n"
        "- 대상 Bucket·Key 또는 승인 Prefix 일치\n"
        "- 공격 시간 창 일치\n"
        "- 성공 응답\n"
        "- Source IP·User-Agent·Request ID 등 보조 문맥 일치\n\n"
        "#### REJECTED / NOT CONFIRMED\n\n"
        "단순히 로그가 안 보인다는 이유가 아니라 다음 조건을 확인해야 한다.\n\n"
        "- CloudTrail Data Event Coverage 정상\n"
        "- 대상 Bucket·Prefix·Region·시간 창 정확\n"
        "- 충분한 Delivery 대기 후 조회\n"
        "- 동일 공격 문맥의 명시적 AccessDenied 또는 실패 Evidence\n"
        "- 다른 Source에도 성공 경로 없음\n\n"
        "#### INCONCLUSIVE\n\n"
        "다음 경우는 기각하지 않는다.\n\n"
        "- 대상 Event가 조회되지 않음\n"
        "- Data Event 활성화·Selector·Prefix 불확실\n"
        "- 조사 시간 창 또는 Delivery 완료 불확실\n"
        "- Telemetry 누락·best-effort·보존 상태 불확실\n\n"
        "> **Evidence 부재는 Telemetry Coverage가 검증되지 않았다면 행위 부재의 증거가 아니다.**\n\n"
        "따라서 발표에서는 다음처럼 말하는 것이 정확함.",
        "C03 three-way explanation",
    )
    text = replace_once(
        text,
        "8. CONFIRMED 또는 기각",
        "8. CONFIRMED / REJECTED / INCONCLUSIVE 판정",
        "C03 final recommendation",
    )

    # 4. ALB/NLB Vended Logs를 확정 최적이 아닌 우선 평가 후보로 하향
    text = replace_once(
        text,
        "Legacy를 주 탐지 Source로 유지하지 말고 **ALB Vended Logs를 주 SIEM Source로 전환**, Legacy/S3는 Archive 역할",
        "Legacy/S3는 Archive·Replay 역할로 유지하고, **ALB Vended Logs는 저지연 SIEM 수집을 위해 우선 평가할 후보**로 둠. 실제 우월성은 Runtime 비교 전 확정하지 않음",
        "C04 ALB legacy judgment",
    )
    text = replace_once(
        text,
        "**현재 기준 ALB의 권장 SIEM Route.** CWL에서 Event-driven으로 빼고 필요 시 S3 Archive 병행",
        "**저지연 SIEM 수집의 우선 평가 후보.** Legacy보다 실제 얼마나 빠른지는 latency·누락·중복·비용 Runtime 비교 전 확정 금지. 필요 시 S3 Archive 병행",
        "C04 ALB vended judgment",
    )
    text = replace_once(
        text,
        "Legacy 5분 파일보다 우선 검토할 신규 경로",
        "저지연 SIEM 수집의 우선 평가 후보. Legacy보다 빠르다고 확정하지 않으며 Runtime 비교 필요",
        "C04 NLB vended judgment",
    )
    text = replace_once(
        text,
        "→ Vended Logs라는 더 빠른 Telemetry 선택지가 있음",
        "→ Vended Logs라는 별도 저지연 후보가 있으나 실제 우월성은 Runtime 비교 전 확정하지 않음",
        "C04 ALB summary",
    )
    text = replace_once(
        text,
        "1. **같은 서비스에 더 빠른 Telemetry가 있으면 먼저 비교한다.**",
        "1. **같은 서비스에 다른 Logging/Telemetry 메커니즘이 있으면 latency와 운영 특성을 먼저 비교한다.**",
        "C04 route principle",
    )

    # 5. DVWA 3건 측정의 범위, Evidence, Hash, Clock skew 상태 명시
    text = replace_once(
        text,
        "| **DVWA Custom Audit (`command.execution`)** | **프로젝트 관측:** 무해 E2E 검증은 약 3.4~6.4초. A/B/C 구간별 분리는 아직 측정하지 않음 | DVWA → CloudWatch Logs → Subscription → Lambda Allowlist → SQS → Local Bridge → Wazuh | 애플리케이션이 Wazuh로 직접 전송하도록 만들 수도 있으나 강결합·Inbound·유실 대응 문제가 생김 | **현재 Route 유지.** CWL + SQS Buffer를 거치는 저지연 Event-driven Route가 속도·보존·보안 경계의 균형이 가장 좋음 | 현재 저지연 기준선 |",
        "| **DVWA Custom Audit → CloudWatch Logs** | **프로젝트 관측:** 무해 Validation Event → Wazuh Rule `100102` Alert, N=3, 총지연 `6.439 / 3.427 / 3.761초`, 누락 0건. A/B/C/D 개별 분리와 Clock skew 별도 확인 기록은 현재 Evidence에서 확인되지 않음. Shuffle은 포함하지 않음 | DVWA → CloudWatch Logs → Subscription → Lambda Allowlist → SQS → Local Bridge → Wazuh | 애플리케이션이 Wazuh로 직접 전송하도록 만들 수도 있으나 강결합·Inbound·유실 대응 문제가 생김 | **현재 Route 유지 후보.** CWL + SQS Buffer를 거치는 저지연 Event-driven Route가 속도·보존·보안 경계의 균형이 좋음 | Rule `100102` 무해 하위 경로 기준선. 실제 `command.execution` Rule `100103`과 Shuffle G4는 별도 미완료 |",
        "C05 DVWA measurement row",
    )
    text = replace_once(
        text,
        "### 프로젝트 표에서 얻는 핵심\n",
        "#### DVWA→Wazuh 측정 Evidence\n\n"
        "- 측정 경로: `DVWA → CloudWatch Logs → Lambda → SQS → Local Bridge → Wazuh localfile(JSONL) → Rule 100102 Alert`\n"
        "- Validation ID: `wazuh-push-20260817T102046747Z`, `wazuh-push-20260817T102127824Z`, `wazuh-push-20260817T102209527Z`\n"
        "- 총지연: `6.439초`, `3.427초`, `3.761초`\n"
        "- 표본 수: `N=3`\n"
        "- 누락: `0건`\n"
        "- Evidence: `[[20_팀 프로젝트/3차 프로젝트/일일 로그/RAW/2026-08-17_RAW]]`\n"
        "- Git Blob SHA: `03da5c96de1ff4b7275c2eec6e09afd9bc9c4cea`\n"
        "- 파일 SHA-256: `ac5fe00bf0c9abca8e8d0751407840ae18f23074151e5e443ba573794c5607dd`\n"
        "- Clock skew: 별도 확인 기록은 현재 RAW에서 확인되지 않음\n"
        "- 해석 범위: **DVWA Event부터 Wazuh Rule 100102 Alert까지의 하위 경로 E2E**이며 Shuffle terminal Execution은 포함하지 않음\n\n"
        "### 프로젝트 표에서 얻는 핵심\n",
        "C05 evidence section",
    )

    # 6. Source latency 열을 한국어 Telemetry 사용 가능 지연(A+B)로 정정
    text = replace_once(
        text,
        "| 서비스 / Telemetry | Source latency / 공식 상태 | 현재 프로젝트 Route | 가능한 가장 빠른 Route | 이 프로젝트에서의 최적 Route | 판정 |",
        "| 서비스 / Telemetry | Telemetry 사용 가능 지연 (Event → AWS 소비 지점, A+B) / 공식 상태 | 현재 프로젝트 Route | 가능한 가장 빠른 Route | 프로젝트 판단 / Target Candidate | 판정 |",
        "C06 project table header",
    )
    text = replace_once(
        text,
        "## 자주 쓰이는 AWS 보안 Telemetry의 Source latency 참고표",
        "## 자주 쓰이는 AWS 보안 Telemetry의 사용 가능 지연 참고표",
        "C06 common table heading",
    )
    text = replace_once(
        text,
        "| 서비스 / Telemetry | 공식 Source/Delivery latency | 저지연 SIEM Route 후보 | 중요한 제한 / 용도 |",
        "| 서비스 / Telemetry | 공식 Telemetry 사용 가능 지연(A+B) 또는 해당 메커니즘 지연 | 저지연 SIEM Route 후보 | 중요한 제한 / 용도 |",
        "C06 common table header",
    )
    text = replace_once(
        text,
        "Source latency\n≠ Transport latency",
        "Telemetry 사용 가능 지연(A+B)\n≠ SIEM Transport 지연(C)",
        "C06 distinction block",
    )
    text = replace_once(
        text,
        "- Source latency\n- Transport latency",
        "- Telemetry 사용 가능 지연(A+B)\n- SIEM Transport 지연(C)",
        "C06 evaluation list",
    )
    text = replace_once(
        text,
        "Destination을 바꿔도 Standard의 Source latency는 사라지지 않음",
        "Destination을 바꿔도 Standard의 Telemetry 사용 가능 지연(A+B)은 사라지지 않음",
        "C06 cloudfront wording",
    )
    text = replace_once(
        text,
        "CloudTrail이라는 Audit Source 자체의 평균 약 5분 지연은 남음",
        "CloudTrail Trail 경로에서 API Event가 CloudWatch Logs 또는 S3에 사용 가능해지기까지의 평균 약 5분 지연은 남음",
        "C06 cloudtrail wording",
    )
    text = replace_once(
        text,
        "CloudTrail 자체 약 5분 Source/Delivery 지연은 제거할 수 없음",
        "CloudTrail Trail 경로의 Telemetry 사용 가능 지연(A+B) 평균 약 5분은 제거할 수 없음",
        "C06 cloudtrail row wording",
    )
    text = replace_once(
        text,
        "Source latency와 Transport latency 구분",
        "Telemetry 사용 가능 지연(A+B)과 SIEM Transport 지연(C) 구분",
        "C06 report story wording",
    )
    text = replace_once(
        text,
        "2. 더 빠른 Telemetry가 없으면 **Source latency는 받아들이고, B/C 구간의 불필요한 Poll만 제거한다.**",
        "2. 더 빠른 메커니즘이 없으면 **Telemetry 사용 가능 지연(A+B)은 받아들이고, C 구간의 불필요한 Poll만 제거한다.**",
        "C06 route principle wording",
    )
    text = replace_once(
        text,
        "- **프로젝트 관측**: 이 프로젝트 Runtime에서 직접 측정한 값. AWS의 SLA나 일반 보장값으로 확대하지 않음.\n",
        "- **프로젝트 관측**: 이 프로젝트 Runtime에서 직접 측정한 값. AWS의 SLA나 일반 보장값으로 확대하지 않음.\n\n"
        "> **Telemetry 사용 가능 지연(A+B)**은 실제 Event 발생부터 AWS의 Initial destination에서 Consumer가 Record를 사용할 수 있게 될 때까지다. AWS가 A와 B를 분리 공개하지 않으면 임의로 나누지 않는다.\n",
        "C06 latency definition",
    )

    # 7. Source와 Logging mechanism 혼용 정정
    text = replace_once(
        text,
        "→ Standard와 Real-time은 같은 서비스지만 전혀 다른 latency 특성을 가진 Source",
        "→ 같은 CloudFront Resource와 Viewer Request를 관찰하지만 Standard와 Real-time은 서로 다른 Logging mechanism·Delivery path·Telemetry 사용 가능 지연(A+B)을 가짐",
        "C07 cloudfront source wording",
    )

    # 8. CloudFront Standard와 Real-time의 장단점과 비상위호환성 보충
    text = replace_once(
        text,
        "## 8. 현재 프로젝트의 구성요소를 이 개념에 매핑하면\n",
        "### Standard와 Real-time은 완전한 상위·하위 관계인가?\n\n"
        "**아니다. Real-time이 Standard의 완벽한 상위호환은 아니다.** 같은 Viewer Request Log 계열이지만 목적·지연·비용·전달 구조가 다르다.\n\n"
        "| 항목 | Standard Logging v2 | Real-time Access Logging |\n"
        "|---|---|---|\n"
        "| Telemetry 사용 가능 지연(A+B) | 일반적으로 Event 후 1시간 이내, 일부 Entry 최대 24시간 | 요청 수신 후 수초 내 Kinesis 전달 |\n"
        "| 주 목적 | 장기 보존, Historical analysis, Audit, 대량 분석 | 저지연 Monitoring, Alert, 즉시 대응 Trigger |\n"
        "| Destination | CloudWatch Logs, Firehose, S3 | Kinesis Data Streams |\n"
        "| 출력·분석 | JSON/plain/W3C/raw 및 S3 Parquet 등 Archive 분석에 유리 | Kinesis Consumer가 선택한 필드 순서에 맞춰 Record를 해석 |\n"
        "| Sampling | 별도 사용자 Sampling이 핵심 기능은 아님 | 1~100% Sampling 설정 가능 |\n"
        "| 범위 선택 | Distribution Logging 설정 | 특정 Cache Behavior에 연결 가능 |\n"
        "| 비용 | Destination ingest·storage 비용 | CloudFront Real-time Logs 요금 + Kinesis 비용 |\n"
        "| 운영 복잡도 | Archive·분석 경로가 비교적 단순 | Kinesis capacity, Consumer, Schema order, throttle 처리 필요 |\n"
        "| 완전성 | Best-effort, 지연·누락 가능 | Best-effort, 지연·누락 가능. Sampling <100이면 의도적 미수집 |\n\n"
        "#### Standard가 나은 경우\n\n"
        "- 즉시 대응보다 장기 보존과 전체 기간 분석이 중요함\n"
        "- S3 / Parquet / Athena 같은 Archive 분석이 핵심임\n"
        "- Kinesis Consumer 운영 복잡도와 Real-time 비용을 정당화할 Use Case가 없음\n\n"
        "#### Real-time이 나은 경우\n\n"
        "- 수초 단위 Edge Request 신호가 실제 대응 결정에 필요함\n"
        "- 특정 Cache Behavior만 선택적으로 관찰하고 싶음\n"
        "- Sampling으로 비용과 분석량을 통제하고 Kinesis Consumer를 운영할 수 있음\n\n"
        "> **동일한 활동 유형을 관찰한다는 뜻이지, 두 경로가 반드시 동일한 Record 집합을 일대일로 제공한다는 뜻은 아니다.** Sampling·best-effort 전달·필드 구성·활성화 시점·Cache Behavior 범위가 다를 수 있다.\n\n"
        "## 8. 현재 프로젝트의 구성요소를 이 개념에 매핑하면\n",
        "C08 cloudfront tradeoffs",
    )

    # 9. A/B/C를 프로젝트 분석 모델로 선언하고 D/E 추가
    text = replace_once(
        text,
        "## 11. A/B/C 지연 모델 정밀화 — Real-time Logs와 Kinesis\n\n"
        "A/B/C는 서비스나 AWS 구성요소의 이름이 아니라 **두 상태 사이의 지연 구간**이다. 즉 `점(Node)`과 `선(Interval)`을 분리해서 이해한다.\n",
        "## 11. A/B/C/D/E 지연 모델 정밀화 — Real-time Logs와 Kinesis\n\n"
        "> [!NOTE]\n"
        "> A/B/C/D/E는 AWS가 공식적으로 명명한 표준 구간이나 SLA가 아니라, 이 프로젝트에서 latency 원인을 분리하기 위해 정의한 **분석 모델**이다.\n\n"
        "A/B/C/D/E는 서비스나 AWS 구성요소의 이름이 아니라 **두 상태 사이의 지연 구간**이다. 즉 `점(Node)`과 `선(Interval)`을 분리해서 이해한다.\n\n"
        "```text\n"
        "실제 Event\n"
        "   │ A. Source 생성·집계\n"
        "   ▼\n"
        "Log / Event Record\n"
        "   │ B. Source-native Delivery\n"
        "   ▼\n"
        "AWS Destination에서 Consumer-visible\n"
        "   │ C. SIEM Transport\n"
        "   ▼\n"
        "Wazuh 입력\n"
        "   │ D. Decoder·Rule 평가·Alert 생성·Integratord 호출\n"
        "   ▼\n"
        "Wazuh Alert / Integratord\n"
        "   │ E. SOAR 전달·실행\n"
        "   ▼\n"
        "Shuffle terminal Execution / Action result\n"
        "```\n\n"
        "전체 Event-to-Action latency를 말하려면 `A + B + C + D + E`가 필요하다. A+B+C만 측정하고 Shuffle까지 포함한 전체 E2E라고 부르지 않는다.\n",
        "C09 model declaration",
    )
    text = replace_once(
        text,
        "A/B/C = 선(지연 구간)\nEvent / Log Record / Kinesis / Wazuh = 점(상태·구성요소)\n\nA = Event → Log Record\nB = Log Record → AWS Destination에서 Consumer-visible\nC = Consumer-visible → Wazuh Rule 평가 시작",
        "A/B/C/D/E = 선(지연 구간)\nEvent / Log Record / Kinesis / Wazuh / Alert / Shuffle Result = 점(상태·구성요소)\n\nA = Event → Log Record\nB = Log Record → AWS Destination에서 Consumer-visible\nC = Consumer-visible → Wazuh 입력\nD = Wazuh 입력 → Rule 평가·Alert 생성·Integratord 호출\nE = Alert 전달 → Shuffle terminal Execution / Action result",
        "C09 final memory block",
    )

    # 10. 공식 사실, 현재 Route, 프로젝트 판단을 시각적으로 분리
    text = replace_once(
        text,
        "## Latency 표기 규칙\n",
        "## 출처와 판정 구분\n\n"
        "| 표기 | 의미 |\n"
        "|---|---|\n"
        "| 공식 수치·정성 표현 | AWS 공식 문서가 명시한 내용 |\n"
        "| 현재 Route | Terraform Repository와 현재 Runtime에서 확인된 As-built |\n"
        "| 프로젝트 관측 | 이 프로젝트에서 직접 측정한 값. AWS 일반 보장값이 아님 |\n"
        "| 프로젝트 판단 / Target Candidate | 공식 지원과 설계 요구를 바탕으로 한 판단. 구현·Runtime 비교 전에는 최적 확정이 아님 |\n\n"
        "`권장`, `최적`을 AWS 공식 권고처럼 쓰지 않는다. 미구현 후보에는 **우선 평가 후보**, **Target Candidate**, **Runtime 비교 필요**를 붙인다.\n\n"
        "## Latency 표기 규칙\n",
        "C10 provenance legend",
    )

    # 11. CloudWatch Logs Subscription을 공통 표와 설명에 추가
    text = replace_once(
        text,
        "## 자주 쓰이는 AWS 보안 Telemetry의 사용 가능 지연 참고표\n\n"
        "| 서비스 / Telemetry | 공식 Telemetry 사용 가능 지연(A+B) 또는 해당 메커니즘 지연 | 저지연 SIEM Route 후보 | 중요한 제한 / 용도 |\n"
        "|---|---|---|---|\n",
        "## 자주 쓰이는 AWS 보안 Telemetry의 사용 가능 지연 참고표\n\n"
        "### CloudWatch Logs Subscription은 어디에 해당하는가?\n\n"
        "CloudWatch Logs Subscription Filter는 CloudWatch Logs에 이미 수집된 Log Event를 Lambda, Kinesis, Firehose 등으로 지속 전달하는 Forwarding mechanism이다. 원래 Source의 A+B를 없애는 기능이 아니라 **CloudWatch Logs ingest 이후의 Poll 대기를 제거하는 연결 계층**이다.\n\n"
        "- Log Event가 CloudWatch Logs에 ingest된 뒤 대상 Resource로의 전달은 보통 3분 미만으로 설명됨\n"
        "- Retry 가능한 전송 오류는 최대 24시간 재시도하지만 그 뒤 실패분은 유실될 수 있음\n"
        "- Throttle·AccessDenied·Destination 장애를 별도로 모니터링해야 함\n"
        "- Subscription 이후 Payload 변환·Queue·Local Bridge·Wazuh 전달은 별도 C 구간임\n\n"
        "| 서비스 / Telemetry | 공식 Telemetry 사용 가능 지연(A+B) 또는 해당 메커니즘 지연 | 저지연 SIEM Route 후보 | 중요한 제한 / 용도 |\n"
        "|---|---|---|---|\n"
        "| **CloudWatch Logs Subscription Filter** | **원본 Source A+B와 별도:** CWL ingest 후 대상 Resource 전달은 보통 3분 미만 | CWL → Subscription → Lambda/Kinesis/Firehose → SIEM | 원래 Source A+B를 없애지 않음. Retry 가능한 오류는 최대 24시간 재시도 후 실패분 유실 가능. Throttle·AccessDenied 모니터링 필요 |\n",
        "C11 subscription section and row",
    )

    # 12. 현재 수동 Evidence 연계와 Target 자동 Correlation 구분
    text = replace_once(
        text,
        "├─ Wazuh SIEM 중앙 분석·Correlation",
        "├─ Wazuh SIEM 중앙 수집·탐지",
        "C12 resolved flow wording",
    )
    text = replace_once(
        text,
        "### 공식 자료 대조에서 확인한 핵심\n",
        "### 현재 Evidence 연계와 Target Correlation 구분\n\n"
        "```text\n"
        "현재 As-built\n"
        "→ 5개 Source 중앙 수집\n"
        "→ Dashboard / Query / Script 기반 후행 Evidence 연계\n"
        "→ 일부 상관 판단은 운영자가 수행\n\n"
        "Target\n"
        "→ 공통 Correlation Key와 시간 창을 이용한\n"
        "  자동 Incident Enrichment / Correlation\n"
        "```\n\n"
        "가능한 상관 키:\n\n"
        "- `event_id` / `request_id` / Trace ID\n"
        "- Principal / Role Session\n"
        "- Source IP\n"
        "- URI / Route\n"
        "- Bucket / Key\n"
        "- 시간 창\n"
        "- WAF Label / Action\n\n"
        "공통 Stable ID가 없는 Source끼리는 완전한 일대일 대응이 아니라 다중 Evidence 기반 추론일 수 있다.\n\n"
        "### 공식 자료 대조에서 확인한 핵심\n",
        "C12 correlation section",
    )

    # 13. Containment를 세 축으로 분리하고 STS 자격증명 한계 명시
    text = replace_once(
        text,
        "향후 DVWA 전용 Pod Identity/IAM Role이 생기면 전용 Principal Containment까지 자동화할 수 있음.\n\n## Microsoft Sentinel을 발표에서 부가 설명하는 방법",
        "향후 DVWA 전용 Pod Identity/IAM Role이 생기면 전용 Principal Containment까지 자동화할 수 있음.\n\n"
        "### Containment는 세 축으로 분리한다\n\n"
        "#### 1. Workload / Network Containment\n\n"
        "- DVWA Pod / Workload 격리\n"
        "- 공격 실행 지점의 추가 통신 차단\n"
        "- 정상 서비스 영향과 복구 절차 확인\n\n"
        "#### 2. Resource / Permission Containment\n\n"
        "- `validation/*` Lab 범위 Explicit Deny\n"
        "- 필요 시 Bucket Policy·IAM Policy 제한\n"
        "- 공유 Node Role 전체 `DenyAll`은 다른 Workload 영향 때문에 자동 실행하지 않음\n\n"
        "#### 3. Credential / Session Response\n\n"
        "- 실제 사용 Principal과 Role Session 식별\n"
        "- 탈취·재사용 가능성과 다른 Resource 권한 조사\n"
        "- 가능한 범위에서 세션·권한 영향 제한\n"
        "- 장기적으로 DVWA 전용 Pod Identity / IAM Role로 Blast Radius 축소\n\n"
        "> Workload 격리만으로 이미 탈취된 STS Credential이 자동 폐기되거나 다른 Network 위치의 재사용이 모두 차단되는 것은 아니다. 세 축을 함께 조사한다.\n\n"
        "## Microsoft Sentinel을 발표에서 부가 설명하는 방법",
        "C13 containment axes",
    )

    # 14. 기술적 최적성과 프로젝트 Scope 결정을 분리
    text = replace_once(
        text,
        "현재 프로젝트 일정에서는 이 역할 분담을 그대로 활용하는 것이 현실적임.",
        "현재 As-built와 이미 확보한 Runtime Evidence 범위를 유지하는 동안에는 이 역할 분담을 사용한다.",
        "C14 as-built wording",
    )
    text = replace_once(
        text,
        "`프로젝트 남은 일정`은 최적 Route의 기술적 평가 기준에서 제외한다.\n",
        "`프로젝트 남은 일정`은 최적 Route의 기술적 평가 기준에서 제외한다.\n\n"
        "#### 기술적 최적성과 프로젝트 Scope 결정을 분리\n\n"
        "```text\n"
        "기술적 평가\n"
        "→ latency, 신뢰성, Buffer, 보안 경계, 비용, 운영 복잡도, 정보 가치\n\n"
        "프로젝트 Scope 결정\n"
        "→ 구조 변경 후 기존과 같은 수준의 Runtime 재검증을 완료할 수 있는가\n"
        "```\n\n"
        "프로젝트 후반에는 구조 변경 후 전체 Runtime 재검증까지 완료할 수 없어 Target Candidate를 As-built에 반영하지 않았다. 이는 기존 구조가 기술적으로 최적이라는 뜻이 아니라, 미검증 구조를 완료 결과에 섞지 않기 위한 Scope 결정이다.\n",
        "C14 scope distinction",
    )

    # 10과 연계: 보고서·발표의 '최적' 표현을 후보로 낮춤
    text = text.replace("Source별 최적 Telemetry 전환", "Source별 적합한 Telemetry 후보 전환")
    text = text.replace("Source별 가장 적합한 Telemetry를 Event-driven 방식으로", "Source별 적합한 Telemetry 후보를 Event-driven 방식으로")

    # 최종 검증 Anchor: 16개 교정의 핵심 문구가 모두 있어야 함.
    required = {
        "C01": "실제 Rule 100103 Alert ↔ Shuffle Execution 일대일 Evidence",
        "C02": "5~10분 걸릴 수 있음",
        "C03": "INCONCLUSIVE",
        "C04": "Legacy보다 실제 얼마나 빠른지는",
        "C05": "ac5fe00bf0c9abca8e8d0751407840ae18f23074151e5e443ba573794c5607dd",
        "C06": "Telemetry 사용 가능 지연 (Event → AWS 소비 지점, A+B)",
        "C07": "서로 다른 Logging mechanism·Delivery path",
        "C08": "Real-time이 Standard의 완벽한 상위호환은 아니다",
        "C09": "A/B/C/D/E는 AWS가 공식적으로 명명한",
        "C10": "프로젝트 판단 / Target Candidate",
        "C11": "CloudWatch Logs Subscription은 어디에 해당하는가?",
        "C12": "현재 Evidence 연계와 Target Correlation 구분",
        "C13": "Containment는 세 축으로 분리한다",
        "C14": "기술적 최적성과 프로젝트 Scope 결정을 분리",
        "C15": "[!WARNING] SUPERSEDED",
        "C16": "[!WARNING] 상담 중 원메모",
    }
    missing = [key for key, marker in required.items() if marker not in text]
    if missing:
        raise RuntimeError(f"missing correction anchors: {missing}")

    # 아직 분해하지 않는다: 대상 단일 파일만 수정.
    if text == original_bytes.decode("utf-8"):
        raise RuntimeError("no changes produced")

    with NOTE.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)

    print(f"Updated {NOTE}")
    print(f"Original bytes: {len(original_bytes)}")
    print(f"Updated bytes: {len(text.encode('utf-8'))}")
    print("Applied corrections C01-C16; no document split performed.")


if __name__ == "__main__":
    main()
