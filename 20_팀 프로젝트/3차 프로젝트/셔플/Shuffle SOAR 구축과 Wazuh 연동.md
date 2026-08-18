---
type: project-doc
status: active
created: 2026-08-18
project: 3차 프로젝트
project_moc: "[[20_팀 프로젝트/3차 프로젝트/00_3차프로젝트_목차]]"
---

# Shuffle SOAR 구축과 Wazuh 연동

## 구축 목표

Wazuh가 탐지한 대표 공격 Alert를 사람이 일일이 복사하지 않아도, Shuffle이 사전에 정한 대응 절차에 따라 검증하고 후속 조치를 실행하게 한다.

이번 프로젝트에서 목표로 하는 닫힌 흐름은 다음과 같다.

```text
DVWA Command Injection
→ Wazuh Rule 100103
→ Shuffle Webhook
→ 입력 검증·TAKE_ID 중복 차단
→ 승인된 GitHub Workflow 호출
→ values.yaml의 low → impossible
→ Argo CD가 EKS에 배포
→ 동일 공격 차단 확인
```

이 과정은 알 수 없는 공격을 Shuffle이 스스로 분석해 코드를 고치는 구조가 아니다. **이미 검증한 공격 유형에 사전 승인된 대응 Playbook을 실행하는 실습**이다. `low → impossible`은 영구 패치가 아니라 취약 기능을 잠시 닫는 긴급 격리 조치에 가깝다.

관련 Wazuh 수집·탐지 과정은 [[Wazuh SIEM 로그 분석과 대응]]에서 이어진다.

## Shuffle Core와 Shuffle Security

| 구성 | 역할 |
|---|---|
| Shuffle Core | Webhook, 조건, App, API 호출로 실제 자동화 Workflow를 실행한다. |
| Shuffle Security | Core 위에서 Alert를 사건으로 정리하고 조사·담당·상태·호스트·취약점을 관리하는 SOC 화면이다. |

둘 중 하나만 영구적으로 선택하는 구조가 아니다. 이번 단계에서는 Wazuh Alert를 받아 고정된 GitHub 대응을 실행하는 것이 우선이므로 **Core Workflow부터 구축**한다. 사건관리 화면이 필요하면 나중에 Security를 Core 위에 연결할 수 있다.

## 비밀값 기록 금지

> [!danger] 채팅·노트·Git·스크린샷에 남기지 않을 값
> - Shuffle API Key
> - 전체 Webhook URL
> - `X-SOC-Webhook-Key`의 실제 값
> - GitHub PAT
> - Wazuh Credential
>
> 이 문서에는 이름과 입력 위치만 기록한다. 실제 값은 로컬 DPAPI 보호 저장소와 Shuffle의 인증 입력란에만 둔다.

## 1. Shuffle Cloud와 Core 진입

1. `https://shuffler.io`에 로그인한다.
2. 시작 제품에서 `Shuffle Core`를 선택한다.
3. `Find your apps`와 `Usecases`는 추천 온보딩 화면이다.
4. 이번 프로젝트는 일반 템플릿 대신 고정 계약을 직접 만들기 때문에 `Automate → Workflows`로 이동한다.

`Wazuh ticket handler`, `Shuffle Enrichment`, `Wazuh → Jira` 같은 Community Workflow는 실무 패턴을 이해하는 참고자료로만 사용한다. 작성자·권한·외부 전송·Credential 사용을 검토하지 않은 Workflow를 그대로 실행하지 않는다.

## 2. Private Workflow 생성

`Create Workflow`에서 다음처럼 입력했다.

| 항목 | 값 |
|---|---|
| Name | `CAPITAL-ONE-SOC-CONTAINMENT-v1` |
| Description | `Lab-only deterministic containment workflow. Receives sanitized Wazuh Rule 100103 alerts, validates and deduplicates by TAKE_ID, then dispatches the approved GitHub containment workflow.` |
| Usecase | `SIEM alerts` |
| Tags | `wazuh`, `soar`, `containment`, `github` |

`Generate Workflow from Flowchart (beta)`는 사용하지 않았다. 생성형 결과가 현재 고정 Schema·Allowlist·중복 차단 계약과 일치한다고 보장할 수 없기 때문이다.

생성하면 별도의 공유 범위 선택창 없이 빈 Workflow Canvas로 바로 이동했다. Community 게시 동작은 하지 않았으며, 최종 공유 상태가 `private`인지는 나중에 Workflow Export/API로 다시 검증한다.

> [!todo] 보고서용 화면
> Workflow 생성 화면은 브라우저 개인 정보와 다른 탭을 제외해 다시 캡처한다.

## 3. 빈 Canvas 이해

처음에는 `Change Me`라는 기본 Shuffle Tools Action 하나가 있다.

- 지금 삭제하지 않는다.
- Gate B5에서는 이 Action을 실제 GitHub 호출 대신 안전한 Stub으로 사용할 수 있다.
- 왼쪽의 `Wazuh` App은 Shuffle이 Wazuh API를 호출할 때 사용한다.
- 이번 입력 방향은 `Wazuh → Shuffle`이므로 시작점은 Wazuh App이 아니라 **Webhook Trigger**다.

## 4. Wazuh Alert Webhook 생성

왼쪽 `Triggers`의 하늘색 `Webhook`을 Canvas에 끌어 놓았다. 기본 Action과 선이 연결된 상태로 추가됐다.

설정은 다음과 같다.

| 항목 | 값·판정 |
|---|---|
| Name | `Wazuh Alerts Webhook` |
| Associated App | 비움 |
| Authentication headers | `X-SOC-Webhook-Key=<runtime-only secret>` |
| Custom Response | `OK` 유지 |
| Wait For Response | 사용하지 않음 |
| 동작 | `Start` 후 Workflow `Save` |

Webhook URL만 아는 사람이 Workflow를 실행하지 못하도록 Required Header를 추가한다. 비밀값은 직접 출력하지 않고 다음 Helper로 잠시 Clipboard에 복사한다.

```powershell
Set-Location 'D:\terraform\aws_terraform_build_code'

.\tools\Copy-SocLabWebhookHeader.ps1 `
  -ConfirmCopy 'COPY SOC HEADER TO CLIPBOARD'
```

`Authentication headers`에는 다음 형식으로 입력한다.

```text
X-SOC-Webhook-Key=<Clipboard로 복사된 값>
```

- `=` 앞뒤에 공백을 넣지 않는다.
- 따옴표를 넣지 않는다.
- Helper는 실제 값을 출력하거나 파일에 저장하지 않는다.
- Clipboard 값은 조건이 맞으면 120초 뒤 비워진다.
- 입력 중에는 스크린샷을 찍지 않는다.
- 캡처가 필요하면 빈 Canvas를 눌러 비밀값이 표시된 오른쪽 패널을 닫는다.

## 현재 Checkpoint

2026-08-18 사용자가 다음 작업을 완료했다고 보고했다.

- Shuffle Cloud 로그인
- `CAPITAL-ONE-SOC-CONTAINMENT-v1` 생성
- Webhook Trigger 추가
- Required Header 입력
- Webhook `Start`와 Workflow `Save`

아직 API/Export와 실제 요청으로 검증하지 않았으므로 현재 판정은 **화면 구성 완료 보고, Runtime 검증 대기**다. 구성요소가 보인다는 사실만으로 Wazuh Alert 전달이나 중복 차단 성공으로 판정하지 않는다.

## 다음 구축 순서

1. Webhook URL을 보안 입력으로 로컬 DPAPI 저장소에 저장한다.
2. Organization ID, Workflow ID, Webhook ID와 Shuffle Cloud Origin을 공개 설정에 기록한다.
3. Shuffle API Key를 보안 입력으로 저장한다.
4. 사전에 Test하고 Hash를 남긴 Private App 두 개를 Upload한다.
   - `AWS Topology SOC Validator 1.0.0`
   - `AWS Topology SOC GitHub Dispatcher 1.0.0`
5. Validator·Allowlist·TAKE 조회·분기·Dedupe 노드를 고정 계약대로 조립한다.
6. GitHub Credential 없이 `GATE_B5_GITHUB_STUB`으로 동시 10회 중복 차단을 검증한다.
7. 신규 Claim 1개·중복 9개·Stub 1회·실제 GitHub 0회를 확인한 뒤에만 제한된 GitHub PAT을 등록한다.
8. Stub을 고정 Dispatcher로 교체하고 최종 E2E를 검증한다.

## 이 단계가 긴 이유

Webhook 하나만 연결하면 Alert 전달은 가능하지만, 다음 문제를 막을 수 없다.

- 위조된 요청이 대응을 실행함
- 같은 사건이 반복 전달돼 GitHub Workflow가 여러 번 실행됨
- 다른 Account·Scenario·Rule이 잘못된 대응을 호출함
- 비밀값이나 원본 공격 명령이 외부로 전달됨
- Shuffle이 허용하지 않은 Repository나 파일을 변경함

따라서 이번 구축은 단순 연결이 아니라 **입력 인증 → Schema 검증 → Allowlist → 중복 차단 → 고정된 조치 → Runtime Evidence** 순서로 진행한다.

## 기준 문서

현재 구현의 Source of Truth는 다음 로컬 문서와 계약 파일이다.

```text
D:\terraform\aws_terraform_build_code\SOC-LAB-OPERATOR-HANDOFF.md
D:\terraform\aws_terraform_build_code\observability\shuffle\SHUFFLE-CLOUD-SETUP.md
D:\terraform\aws_terraform_build_code\observability\shuffle\shuffle-soc-workflow-contract.json
D:\terraform\aws_terraform_build_code\CAPITAL-ONE-SOC-E2E-BLUEPRINT.md
```

이 노트는 학습과 재현을 위한 설명서이며, 완료 여부는 위 계약과 실제 Runtime Evidence로 판정한다.
