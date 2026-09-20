---
type: moc
status: active
created: 2026-09-20
project: Agent Handoff
parent_moc: "[[20_팀 프로젝트/00_프로젝트_목차]]"
---

# Agent Handoff

## 목적

Chat에서 탐색·설계를 진행한 뒤 Codex/Astra 같은 실행 Agent로 작업을 넘길 때 발생하는 상태 손실, 재탐색, 잘못된 상태 승격, 범위 이탈을 줄이는 **Agent-to-Agent task handoff 방법론과 Skill**을 설계한다.

이 프로젝트의 핵심 질문은 단순히 “좋은 요약문을 어떻게 만들까?”가 아니다.

> 원래 대화 전체를 다시 읽지 않고도 후속 Agent가 동일한 작업 의도·현재 상태·판정 기준을 복원하려면 어떤 최소 실행 상태를 전달해야 하는가?

## 현재 단계

**Research / Design**

아직 10-field schema를 최종 확정하거나 Skill 구현을 시작한 단계가 아니다.

현재 10-field 구조는 강한 후보이며, 기술적 근거와 실제 handoff/context-engineering 패턴을 학습하면서 유지·통합·삭제·추가 여부를 검증한다.

## 연구 기록

- [[20_팀 프로젝트/Agent Handoff/01_연구 로그|연구 로그]] - handoff 개념 학습, schema 공격, 사용자 경험에서 나온 아이디어와 개선 후보를 누적 기록한다.

## 현재 기준 초안

- [[20_팀 프로젝트/Agent Handoff/HANDOFF_SKILL_DRAFT|HANDOFF Skill Draft]]
  - 현재까지의 설계 가설과 구현 요구사항
  - English canonical draft
  - 최종 명세가 아니라 연구 중인 기준점

## 현재 후보 Schema

1. WHY
2. GOAL
3. CURRENT STATE
4. SCOPE
5. INPUTS & ASSETS
6. HOW
7. CONSTRAINTS
8. EVIDENCE
9. DONE
10. FIRST ACTION

추가 원칙:

- 주요 단계는 WHAT뿐 아니라 WHY를 보존한다.
- FACT / VERIFIED or OBSERVED / ASSUMPTION / PLAN을 구분한다.
- DECISIONS, REJECTED ALTERNATIVES, OPEN QUESTIONS / BLOCKERS는 필요 시 하위 구조로 보존한다.

## 연구 질문

- Agent handoff는 summary, task brief, runbook, checkpoint, memory와 기술적으로 어떻게 다른가?
- 10개 필드가 실제로 최소 집합인가, 중복되거나 빠진 항목은 없는가?
- WHY와 GOAL은 언제 분리해야 하고 언제 합쳐도 되는가?
- EVIDENCE와 DONE을 분리하는 것이 실제 재개 정확도를 높이는가?
- FIRST ACTION을 독립 필드로 두는 것이 resume latency를 유의미하게 줄이는가?
- HOW가 너무 구체적이면 후속 Agent의 적응성을 해치지 않는가?
- epistemic state를 어떤 수준으로 명시해야 비용 대비 효과가 좋은가?
- HANDOFF가 원본 Source와 AGENTS.md를 어디까지 참조하고 어디까지 복제해야 하는가?
- 전체 대화 대비 HANDOFF만 제공했을 때 실제 token/rework/오판 비용이 얼마나 줄어드는가?
- 짧은 작업과 장기 작업에 같은 10-field schema를 강제해도 되는가?

## 검증 방향

최종 평가는 문서의 문장 품질보다 **state restoration 성능**으로 한다.

후속 Agent에게 원본 대화 없이 HANDOFF만 제공했을 때 다음을 확인한다.

- 같은 목적을 이해하는가
- 현재 지점에서 시작하는가
- 완료된 일을 반복하지 않는가
- 폐기한 접근을 되살리지 않는가
- Scope와 Constraints를 보존하는가
- Evidence와 Done을 같은 기준으로 해석하는가
- 첫 생산적 행동까지의 재탐색 비용이 줄어드는가

## 버전 관리 원칙

- HANDOFF_SKILL_DRAFT.md는 현재 baseline으로 보존한다.
- 세부 변경 이력은 Git commit/diff로 추적한다.
- schema나 설계 철학이 의미 있게 바뀔 때만 HANDOFF_SKILL_DRAFT_v0.x.md 형태의 비교용 복사본을 만든다.
- 연구가 안정되면 별도 canonical spec을 만든다.

## 현재 재시작 지점

Skill 구현 전에 먼저 Agent handoff 자체를 공부하고, 현재 10-field schema를 비판적으로 재평가한다.

학습 순서:

1. 현재 10-field 초안이 왜 좋아 보였는지 기술적 근거 해부
2. Agent handoff / context engineering / checkpoint / runbook 등 인접 개념 비교
3. 공개된 실제 handoff 패턴과 현재 schema 대조
4. schema를 유지 / 통합 / 삭제 / 추가 항목으로 재판정
5. 실제 Chat → Astra 사례로 비교 테스트 설계
6. 이후 Skill 구현 여부와 최종 명세 결정
