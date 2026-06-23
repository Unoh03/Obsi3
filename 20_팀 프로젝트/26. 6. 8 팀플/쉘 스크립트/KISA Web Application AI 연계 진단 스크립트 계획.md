---

type: project-plan
topic: security-project
status: active
created: 2026-06-23
project: KISA Web Application 진단 스크립트
tags:

- 보안교육
- 팀프로젝트
- 웹보안
- KISA
- evidence
- presentation

---
# KISA Web Application AI 연계 진단 스크립트 계획

> 이 문서는 구현을 더 늘리기 위한 계획이 아니라, 현재까지의 구현과 검증 결과를 발표·보고서로 정확하게 제출하기 위한 기준 문서다.

## 1. 출발점과 방향 전환

처음 목표는 KISA Web Application 01~21 항목을 기준으로 CARE 웹 애플리케이션을 자동 또는 반자동으로 진단하는 스크립트를 만드는 것이었다.

이를 위해 `profile -> check -> request -> evidence -> report` 구조를 만들고, 대상별 값은 profile, 항목별 요청과 판정 규칙은 check YAML로 분리했다. 실행 mode, target allowlist, run별 request/response evidence, `result.json`, `report.md` 같은 안전장치와 출력물도 구성했다.

초기에는 항목별 자동 판정을 늘리면 전체 진단기에 가까워질 것으로 예상했다. 그러나 실제 WEB VM에서 실행하면서, 요청을 보내는 일보다 **응답이 정말 취약 증거인지 해석하는 일**이 더 어렵다는 점이 드러났다.

대표 사례는 15번 파일 다운로드다. 기존 규칙은 HTTP 200을 취약으로 처리했지만, CARE의 `download.php`는 비로그인 사용자를 JavaScript 로그인 이동으로 돌려보낼 수 있다. HTTP status만으로는 파일 다운로드 성공, 로그인 이동, 차단 응답을 구분할 수 없었다. 이 결과는 단순한 버그가 아니라, 웹 애플리케이션 진단에서 상태 코드 하나만으로 최종 판정을 내리기 어렵다는 근거가 됐다.

또한 CSRF, 인증 절차, 권한 검증, 비밀번호 복구처럼 DB·세션·임시 계정·업무 흐름이 필요한 항목은 source pattern이나 단일 HTTP 응답만으로 취약 또는 양호를 확정할 수 없었다. 이를 숨기지 않고 `manual_required`, `inconclusive`, `conditions`, `scope`로 남긴 것이 현재 설계의 중요한 판단이다.

따라서 이 프로젝트는 "완전 자동 KISA 취약점 스캐너"를 주장하지 않는다. 현재 구현의 정확한 성격은 다음과 같다.

```text
KISA Web Application 항목별 요청·응답·소스 근거를
재현 가능한 형태로 수집하는 선언형 evidence collector prototype
```

이 제출 계획은 이 시행착오를 실패로 지우지 않는다. 자동 판정의 한계를 실제 실행 결과로 확인했고, 그 한계를 V.db 분류, evidence 범위 표기, 향후 fixture runtime과 human-reviewed AI assistance 설계로 보정했다는 흐름을 발표와 보고서의 중심으로 삼는다.

## 2. 이 문서의 역할

이 문서는 다음 세 가지를 분명히 구분한다.

| 구분 | 의미 |
|---|---|
| 구현됨 | 현재 checker에 존재하는 구조와 기능 |
| WEB VM에서 검증됨 | 실제 실행 로그와 evidence가 있는 결과 |
| 후속 설계 | R4 fixture runtime, AI review, human review처럼 필요성은 확인했지만 이번 제출에서 구현 완료를 주장하지 않는 범위 |

기술적 세부 설계와 작업 이력은 아래 문서에 보존한다.

- [[KISA Web Application 반자동 진단 스크립트 설계]]
- [[KISA Web Application 반자동 진단 스크립트 작업 로그]]
- [[KISA Web Application 진단 스크립트 방향 전환 노트]]

## 3. 이번 제출의 동결 원칙

```text
- kisa-webapp-checker/는 더 이상 수정하거나 실행하지 않는다.
- 현재 코드와 기존 WEB VM evidence는 제출 근거로만 사용한다.
- R4 fixture runtime, AI review 자동화, 신규 KISA check는 후속 계획으로만 다룬다.
- 구현 사실, 실행 검증 사실, 설계 제안을 같은 문장이나 표에서 섞지 않는다.
```
