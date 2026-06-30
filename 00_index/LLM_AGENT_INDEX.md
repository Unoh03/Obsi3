# LLM Agent Index

이 파일은 사람용 목차가 아니라 Codex, Claude, Gemini 같은 LLM/agent가 이 vault를 탐색할 때 먼저 읽는 운영 인덱스다.

이 파일은 `00_index/Home.md`를 대체하지 않는다. 실제 탐색 구조의 기준은 여전히 `Home → 영역 목차 → 주제/프로젝트 목차 → 실제 노트`다.

## Agent read order

1. `AGENTS.md`
2. `00_index/LLM_AGENT_INDEX.md`
3. `00_index/Home.md`
4. 관련 영역 MOC
5. 관련 주제/프로젝트 MOC
6. 대상 노트
7. RAW, source, PDF, 캡처, 로그는 근거 확인이 필요할 때만 읽는다.

## Operating rules

| Rule | Agent behavior |
|---|---|
| Local evidence first | vault 작업은 실제 파일, git 상태, 명령 출력, MOC를 먼저 확인한다. |
| MOC is navigation, not inventory | MOC에 없는 파일도 누락이라고 단정하지 않는다. 전체 파일 추적은 별도 inventory나 `rg --files`로 확인한다. |
| RAW is not stable knowledge | RAW 메모, 원문 로그, PDF, 캡처는 근거이거나 재료다. 정리본·개념 노트와 같은 위상으로 취급하지 않는다. |
| Preserve user work | dirty target file은 사용자 작업으로 보고, 충돌 가능성을 먼저 보고한다. |
| No placeholder links | 존재 확인 없이 wiki link를 만들지 않는다. |
| Verify before claiming | 링크, 상태, 완료 여부는 실제 파일이나 명령 출력으로 확인한 뒤 말한다. |

## Canonical entry points

| Domain | Entry file | Role | Agent note |
|---|---|---|---|
| Vault home | [[00_index/Home|Home]] | 최상위 진입점 | 전체 구조와 빠른 진입만 확인한다. 세부 파일 목록으로 쓰지 않는다. |
| Study notes | [[10_학습 노트/00_학습노트_목차|학습노트 목차]] | 학습 영역 MOC | 주제별 MOC로 라우팅한다. |
| Projects | [[20_팀 프로젝트/00_프로젝트_목차|프로젝트 목차]] | 프로젝트 영역 MOC | 프로젝트별 최상위 MOC로 라우팅한다. |
| Certifications | [[30_자격증/00_자격증_목차|자격증 목차]] | 자격증 영역 MOC | 시험/오답/복습 노트 확인 시 시작한다. |
| Materials | [[40_자료/00_자료_목차|자료 목차]] | source/materials MOC | PDF, 캡처, 강의자료, 실습 자산 위치 확인에 사용한다. |
| Templates | [[90_템플릿/00_템플릿_목차|템플릿 목차]] | 템플릿 MOC | 새 노트 형식이 필요할 때만 확인한다. |

## High-value routing

| Task intent | Start here | Then inspect | Avoid |
|---|---|---|---|
| AWS 학습·실습 재개 | [[10_학습 노트/클라우드/AWS/00_AWS_목차|AWS 목차]] | 현재 재시작 지점, RAW 메모, 관련 실습 노트 | 오래된 PDF 기준만 보고 현재 Console 동작을 단정하지 말 것 |
| 웹보안 개념·실습 정리 | [[10_학습 노트/시스템보안/웹보안/00_웹보안_목차|웹보안 목차]] | 정리 지도, 개념 노트, 실습 기록, 현재 재시작 지점 | RAW/source를 핵심 개념 노트로 오인하지 말 것 |
| 시스템보안 전체 라우팅 | [[10_학습 노트/시스템보안/00_시스템보안_목차|시스템보안 목차]] | 웹보안, 네트워크보안 하위 MOC | 네트워크 장비 학습과 공격·방어 실습을 섞지 말 것 |
| KISA 웹 서비스 진단 프로젝트 | [[20_팀 프로젝트/26. 6. 8 팀플/00_팀플_목차|26. 6. 8 팀플 목차]] | 웹 서비스 보안 모음, 웹 앱 보안 모음, 결과/스크립트/원문 구분 | 진단 원문 로그를 최종 결과로 취급하지 말 것 |
| 인프라 운영·복구 프로젝트 | [[20_팀 프로젝트/26. 4. 22 팀플/00_팀플_목차|26. 4. 22 팀플 목차]] | 웹/DB/NFS/이중화/복구 문서 | 오래된 작업 상태를 최신 운영 상태로 단정하지 말 것 |

## Type classification

| Type | Meaning | Agent behavior |
|---|---|---|
| `moc` | 목차, 지도, 진입점 | 탐색 경로와 현재 분류를 확인한다. 완전한 파일 목록으로 취급하지 않는다. |
| `concept` | 안정화된 개념 노트 | 설명·요약·학습 답변의 우선 근거로 사용한다. |
| `lab` | 실습 기록 | 명령, 오류, 검증 결과를 확인한다. 개념 일반화는 주의한다. |
| `raw` | 수업 중 빠른 메모, 원문 출력, 휘갈긴 기록 | 원자료로만 사용한다. 정리본 여부를 먼저 확인한다. |
| `source` | PDF, 캡처, 강의자료, 외부 원문 | 범위와 출처 확인에 사용한다. 최신성은 별도로 확인한다. |
| `project` | 팀 프로젝트 문서, 결과, 운영 기록 | 프로젝트 MOC를 통해 범위와 최신 상태를 확인한다. |
| `template` | Obsidian 템플릿 | 새 노트를 만들 때만 참조한다. |
| `stale` | 구버전 가능성이 있는 문서나 상태 | 현재 파일·MOC·사용자 지시로 재검증한다. |

## Status vocabulary

| Status | Meaning | Agent behavior |
|---|---|---|
| `stable` | 현재 정리본으로 사용 가능 | 일반 답변 근거로 사용 가능하되, 바뀌는 기술은 최신성 확인 |
| `active` | 진행 중 | 완료로 단정하지 말고 RAW와 최근 diff를 확인 |
| `raw` | 아직 흡수되지 않은 원자료 | 요약 또는 정리 전용 근거 |
| `draft` | 초안 | 누락·오류 가능성을 열어두고 확인 |
| `archived` | 완료되었거나 과거 상태 보존 | 현재 상태로 단정하지 않음 |
| `stale` | 오래되었거나 구버전 가능 | 현재 기준 재검증 필요 |

## Source and RAW policy

| Material | Expected location | Agent rule |
|---|---|---|
| PDF, 강의자료 | `40_자료/` | 원문 범위 확인용. 학습 노트에 없는 내용을 자동 확장하지 않는다. |
| 캡처 이미지 | `40_자료/캡쳐 창고/` 또는 더 구체적인 자료 폴더 | 시각 증거가 필요할 때만 확인한다. |
| 수업 RAW 메모 | 관련 주제 폴더 또는 `RAW 메모` 파일 | 사용자의 질문, 표현, 관찰을 삭제·왜곡하지 않는다. |
| 진단 원문 로그 | 프로젝트 하위 evidence/source/RAW 성격 위치 | 최종 결과나 조치안과 구분한다. |
| 스크립트·명령 기록 | 프로젝트 또는 실습 노트 | 실행 여부와 출력 여부를 분리해서 말한다. |

## Known context and risk markers

| Marker | Evidence to check | Agent behavior |
|---|---|---|
| AWS class split | `Home.md`, `10_학습 노트/00_학습노트_목차.md`, AWS MOC | 학원 AWS 수업 완료분과 AWS 공식 강사 수업을 섞지 않는다. |
| Old AWS material | AWS MOC의 `AWS기초.pdf` 기준 시점 경고 | Console UI, 비용, Free Tier, 보안 기본값은 현재 기준으로 재확인한다. |
| RAW promoted into core path | MOC 섹션명과 링크 대상 파일 성격 | RAW를 제거하기보다 RAW/source 섹션으로 분리한다. |
| MOC overgrowth | 긴 MOC가 파일 목록처럼 변한 경우 | 핵심 경로, 재시작 지점, source catalog, inventory를 분리한다. |
| Unlinked file | `rg --files`, nearby MOC, file content | 누락이라고 단정하지 말고 의도적 비노출 가능성을 판단한다. |

## Agent verification checklist

Before editing:

- `git status --short --untracked-files=all`
- 대상 파일 존재 여부 확인
- 대상 파일이 dirty면 충돌 가능성 보고
- 새 wiki link는 target 존재 확인

After editing:

- `git diff --check`
- 대상 diff 확인
- 새 wiki link target 확인
- 검증 수준을 `Static review`, `Command executed`, `Runtime verified`, `Not verified` 중 하나로 보고

## Open index issues

| Issue | Evidence | Next action |
|---|---|---|
| 전체 AI inventory 미작성 | 현재 이 파일은 운영 인덱스 MVP이며 전체 파일 목록이 아님 | 다음 루프에서 `rg --files` 기반 inventory 초안을 만들지 결정 |
| frontmatter 통일 안 됨 | 기존 vault 전반에 `type`, `status`, `parent_moc`, `source`가 일관되지 않을 가능성 높음 | 핵심 MOC와 stable concept/lab 노트부터 표본 적용 |
| AWS 공식 강사 수업 범위 미분리 | Home/학습목차에는 재점검 TODO가 있으나 AWS MOC는 구자료 흐름 중심 | AWS MOC를 실제 현재 수업 흐름 기준으로 재검토 |
| source/RAW catalog 미분리 | PDF, 캡처, RAW, 진단 원문이 영역별로 섞여 있을 수 있음 | `40_자료`와 프로젝트 evidence 계층을 분리 검토 |
