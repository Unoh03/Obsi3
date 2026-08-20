---
type: project-doc
status: active
created: "2026-08-20"
project: "3차 프로젝트"
project_moc: "[[00_3차프로젝트_목차]]"
---

# 8.19 멘토 노트 무손실 분해 검증 보고서

## 판정

```text
RESULT: PASS
Original blocks: 11
Mapped blocks: 11
Unmapped blocks: 0
Duplicate source blocks: 0
Hash mismatches: 0
Original bytes: 82820
Reconstructed bytes: 82820
SHA-256: f957d0b12b69c1ee570aa0fc6bcc6ab7a09f7c9c12c9ceab991c6eeba9905f69
```

## 기준

- 기준 커밋: `3a6b45ec37f9be01f41ddd66ae20511fe2264f9a`
- 기준 경로: `20_팀 프로젝트/3차 프로젝트/8.19 멘토님과 상담.md`
- 기준 Git Blob SHA: `d0e953424eb87c9c26bc98b64c65364eaa275044`
- 기준 SHA-256: `f957d0b12b69c1ee570aa0fc6bcc6ab7a09f7c9c12c9ceab991c6eeba9905f69`
- 기준 바이트 수: `82820`
- 원문 블록 수: `11`

검증은 5개 문서에 배치된 SOURCE-BLOCK 내부를 `source_order` 순으로 역조립한 뒤, 기준 커밋의 단일 노트와 바이트 단위로 비교한다. 안내문·Frontmatter·링크는 신규 내용이므로 역조립 대상에서 제외한다.

## Block Mapping

| Block | 원문 순서 | 내용 | 목적지 | Bytes | SHA-256 |
|---|---:|---|---|---:|---|
| `B001` | 1 | 상담 원메모와 최상단 경고 | `20_팀 프로젝트/3차 프로젝트/8.19 멘토 상담 원문과 검토 이력.md` | 4849 | `2817f8013f6862cd…` |
| `B002` | 2 | 상담 후 핵심 재정리 | `20_팀 프로젝트/3차 프로젝트/8.19 멘토 상담 원문과 검토 이력.md` | 3252 | `b138e9c6c4df66db…` |
| `B003` | 3 | 초기 발표·포트폴리오 반영 메모 | `20_팀 프로젝트/3차 프로젝트/멘토 상담 후 보고서·발표 반영.md` | 1276 | `50bdd31cde58e0e3…` |
| `B004` | 4 | 빠른/느린 경로 논쟁과 검토 이력 | `20_팀 프로젝트/3차 프로젝트/8.19 멘토 상담 원문과 검토 이력.md` | 10335 | `333fabdbc1d47bd0…` |
| `B005` | 5 | 후속 공식 검증의 최종 해석과 Incident 시나리오 | `20_팀 프로젝트/3차 프로젝트/DVWA Push와 5-Source Poll 최종 해석.md` | 8691 | `527ba20f73b4d09c…` |
| `B006` | 6 | 프로젝트 지연 구간과 A/B/C/D/E 적용 설명 | `20_팀 프로젝트/3차 프로젝트/Telemetry와 로그 지연 모델.md` | 5050 | `dcca62f6450bba90…` |
| `B007` | 7 | 5개 Source의 Event-driven 전환 가능성 | `20_팀 프로젝트/3차 프로젝트/AWS 보안 Telemetry Route 비교.md` | 2129 | `0e299d65135459e9…` |
| `B008` | 8 | 5-Source Poll 역할과 최종 진행 순서 | `20_팀 프로젝트/3차 프로젝트/DVWA Push와 5-Source Poll 최종 해석.md` | 1664 | `20c01ba8bf04b560…` |
| `B009` | 9 | AWS 보안 Telemetry Route 공식 재검증 표 | `20_팀 프로젝트/3차 프로젝트/AWS 보안 Telemetry Route 비교.md` | 14763 | `27cb31e51eafd7d1…` |
| `B010` | 10 | 보고서·발표 반영 문구와 Q&A | `20_팀 프로젝트/3차 프로젝트/멘토 상담 후 보고서·발표 반영.md` | 9438 | `ffcd81a5f0c6a9a2…` |
| `B011` | 11 | Telemetry 개념과 CloudFront/Kinesis 지연 모델 | `20_팀 프로젝트/3차 프로젝트/Telemetry와 로그 지연 모델.md` | 21373 | `972186ad5b7ec096…` |

## 완료 조건

- 누락 블록: `0`
- 예상하지 못한 중복 블록: `0`
- 블록 해시 불일치: `0`
- 역조립 바이트 불일치: `0`
- 원문과 역조립 SHA-256: 동일

## 문맥 연결 검토

SOURCE-BLOCK의 글자를 수정하지 않고, 분리로 위치 관계가 끊긴 상대 참조에만 신규 안내를 추가했다.

| Bridge | 문서 | 보존할 원문 참조 | 명시한 대상 |
|---|---|---|---|
| `CBR01` | `20_팀 프로젝트/3차 프로젝트/8.19 멘토 상담 원문과 검토 이력.md` | B001: 뒤의 2026-08-19 상담 후 재정리<br>B001/B004: 뒤의 후속 공식 검증 결과 — RESOLVED | same file B002<br>[[DVWA Push와 5-Source Poll 최종 해석#후속 공식 검증 결과 — RESOLVED]] |
| `CBR02` | `20_팀 프로젝트/3차 프로젝트/DVWA Push와 5-Source Poll 최종 해석.md` | B005: 앞에서 적어둔 해석 A/B | [[8.19 멘토 상담 원문과 검토 이력#현재 잠정 해석 — UNRESOLVED]] |
| `CBR03` | `20_팀 프로젝트/3차 프로젝트/Telemetry와 로그 지연 모델.md` | B011: 위의 로그 Source × Telemetry × Route 비교 | [[AWS 보안 Telemetry Route 비교#로그 Source × Telemetry × Route 비교 — 공식 문서 재검증]] |
| `CBR04` | `20_팀 프로젝트/3차 프로젝트/Telemetry와 로그 지연 모델.md` | B006: 아래 기존 5-Source 표<br>B006: 뒤의 로그 Source × Telemetry × Route 비교 — 공식 문서 재검증 | [[AWS 보안 Telemetry Route 비교#5개 Source를 전부 DVWA처럼 빠르게 Push할 수 있는가?]]<br>[[AWS 보안 Telemetry Route 비교#로그 Source × Telemetry × Route 비교 — 공식 문서 재검증]] |
| `CBR05` | `20_팀 프로젝트/3차 프로젝트/AWS 보안 Telemetry Route 비교.md` | B009: 위의 잠정 5-Source 표 | same file B007 immediately before B009 |
| `CBR06` | `20_팀 프로젝트/3차 프로젝트/멘토 상담 후 보고서·발표 반영.md` | B010 heading: 그래서 보고서, 발표엔 어떻게 넣어야하는가! | [[DVWA Push와 5-Source Poll 최종 해석]]<br>[[Telemetry와 로그 지연 모델]]<br>[[AWS 보안 Telemetry Route 비교]] |

- 상대 참조 감사 항목: `8`
- 문맥 연결 Bridge: `6`
- 원문 블록 내부 수정: `0`
- B007 → B009 순서로 잠정 표와 최신 대체 표의 선후관계 유지

