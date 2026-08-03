---
type: project-doc
status: draft
created: 2026-08-02
project: 3차 프로젝트
project_moc: "[[20_팀 프로젝트/3차 프로젝트/00_3차프로젝트_목차]]"
---

# 관측성 As-built 및 Runtime 검증

> [!important] 판정 경계
> 이 문서는 2026-08-02 Cold Up Runtime과 현재 Source에서 직접 확인한 관측 경로를 기록한다. 로그 목적지가 존재한다는 사실과 공격·탐지 시나리오가 검증됐다는 주장은 구분한다.

## 1. 현재 요청·로그 흐름

```mermaid
flowchart LR
    User["사용자·통제된 실험 요청"]
    CF["CloudFront"]
    WAF["AWS WAF<br/>Managed Rule COUNT 관찰"]
    ALB["Primary ALB"]
    SVC["EKS Service"]
    APP["BANK DVWA Pod"]
    RDS["Primary RDS"]

    User --> CF --> WAF --> ALB --> SVC --> APP --> RDS

    CF -. "Standard Access Log" .-> S3["Foundation Security Log S3<br/>30일"]
    ALB -. "Access Log" .-> S3
    VPC["Primary VPC"] -. "REJECT Flow Log" .-> S3
    CT["CloudTrail Management Event"] -.-> S3

    WAF -. "COUNT·BLOCK만" .-> CW["Foundation CloudWatch Logs<br/>30일"]
    EKS["EKS api·audit·authenticator"] -.-> CW
    FB["Fluent Bit DaemonSet"] --> CW
    APP -. "stdout·stderr<br/>구조화 Audit Event" .-> FB
    CT -.-> CW

    S3 --> EC["Local Evidence Collector"]
    CW --> EC
    EC --> BUNDLE["Evidence Bundle<br/>Manifest·Query·SHA-256"]
```

## 2. Log Source Runtime 표

| Log Source | 현재 수집 | 저장 위치 | 보존 | Daily Down 후 | 2026-08-02 Runtime 증거 | 판정 |
|---|---:|---|---:|---:|---|---|
| CloudTrail Management Event | 예 | Foundation S3·CloudWatch | 30일 | 보존 | 최종 Post-Down Bundle 106개 Object | 전달·Down 후 보존 확인 |
| CloudFront Standard Access Log | 예 | Foundation S3 | 30일 | 보존 | 최종 Post-Down Bundle 5개 Object | 전달·Down 후 보존 확인 |
| WAF Web ACL Log | 조건부 | Foundation CloudWatch | 30일 | 보존 | 최종 Post-Down Bundle 3건, `COUNT` Match 2건 | 전달 확인. `BLOCK` 효과는 미검증 |
| ALB Access Log | 예 | Foundation S3 | 30일 | 보존 | 최종 Post-Down Bundle 7개 Object | 전달·Down 후 보존 확인 |
| EKS api·audit·authenticator | 예 | Foundation CloudWatch | 30일 | 보존 | 최종 Post-Down Bundle 67,688건 | Primary 전달·Down 후 보존 확인, 정상 Controller Noise 분류 필요 |
| DVWA stdout·stderr·Audit | 예 | Foundation CloudWatch | 30일 | 보존 | 최종 Post-Down Bundle 940건 | Primary 전달·Down 후 보존 확인 |
| DR DVWA stdout·stderr·Audit | 예 | Foundation CloudWatch | 30일 | 보존 | 구조화 Probe Event 1건, 최종 Post-Down Bundle 1건 | DR 전달·Down 후 보존 확인 |
| Primary VPC Flow `REJECT` | 예 | Foundation S3 | 30일 | 보존 | 최종 Post-Down Bundle 35개 Object | 전달·Down 후 보존 확인 |

## 3. Cold Up 회귀 증거

- AWS API 보존 확인: CloudTrail·Primary/DR DVWA·EKS·WAF Log Group 모두 30일, Security Log S3의 Current·Noncurrent Object Lifecycle 모두 30일
- Daily Terraform Apply: `256 added / 0 changed / 0 destroyed`
- 소요 시간: 32.9분
- Primary·DR EKS와 RDS 생성 완료
- Primary Node 2개 `Ready`
- Primary Fluent Bit DaemonSet `2/2 Ready`
- Argo CD `Synced / Healthy`
- DVWA Pod `1/1 Running / Ready`
- 배포 Image: `sha-8a0099aa5fe8dda94ef15ac803bdd6ee73cfd413`
- GitOps·Argo Revision: `3be7f3bc43d8f058749909dd9d925722c0ef2256`

같은 Source의 최신 Daily Session `observability-20260802T131345Z`에서도
`250 added / 0 changed / 0 destroyed`, 34.1분으로 Cold Up을 완료했다.
Primary Node 2개와 DR Node 1개, 양쪽 Fluent Bit, Argo CD
`Synced / Healthy`, BANK DVWA Ready, 같은 immutable Image를 다시 확인했다.
또한 `enable_web_s3_pod_identity=false`와 BANK Workload용 Pod Identity
Association 부재를 Runtime에서 확인했다.

## 4. Evidence Bundle 검증

### `observability-cold-up-smoke-20260802`

- 범위: `2026-08-01T19:10:00Z`부터 `19:38:58Z`
- Scenario ID: `WEB-01`
- 성격: 공격 실행이 아닌 정상 관측 Pipeline Baseline
- Collector: CloudTrail·CloudFront·ALB·VPC·EKS·DVWA 성공, WAF·DR DVWA는 0건
- WEB Query 3개: 실행 성공, 결과 0행
- Manifest 등록 파일: 69개
- 파일별 SHA-256 불일치: 0
- 초기 Manifest의 `ArgoRevision` 누락을 발견해 Collector Context를 보정함

### `evidence-context-smoke-20260802`

- Live Argo Revision 기록 확인
- `MissingContext`: 없음
- AWS 변경 없이 Evidence Context만 재검증

### `observability-20260802T131345Z-*`

- WEB-01 `before/count/block` 3개, Athena Query 4개, DR Event 1개 Bundle의 SHA-256 490개 불일치 0
- Final Pre-Down Bundle: SHA-256 155개 불일치 0
- Final Post-Down Bundle: SHA-256 180개 불일치 0
- JSON Depth 보정 회귀 Bundle: SHA-256 57개 불일치 0
- Post-Down Collector는 CloudTrail 106·CloudFront 5·ALB 7·VPC REJECT 35개 Object와 EKS 67,688·WAF 3·Primary DVWA 940·DR DVWA 1건을 수집했다.
- Daily Down 뒤 Daily State·태그 기반 Runtime·Terraform Process·Watchdog·활성 Session은 0이었고 Foundation State 27개와 30일 로그 계층은 유지됐다.
- DR EKS Control Plane Log Group의 Down 후 존속은 확인되지 않았다. 이번에 확인한 DR 지속 Log는 DR DVWA Application Log Group이다.

### 정상 요청 1건의 계층 간 추적

`2026-08-01T19:28:12Z`의 `GET /login.php` 요청을 Sanitized Evidence에서 다음처럼 연결했다.

| 계층 | 확인된 기록 |
|---|---|
| CloudFront | `19:28:12`, `/login.php`, Viewer 응답 `200`, Client IP와 Edge Request ID 기록 |
| WAF | 0건. 정상 `ALLOW`는 현행 Filter의 저장 대상이 아님 |
| ALB | `19:28:12.824266Z`, `/login.php?[REDACTED_QUERY]`, ALB·Target 응답 `200`, ALB Trace ID 기록 |
| DVWA | `19:28:12.824145Z`, `/login.php?[REDACTED_QUERY]`, 응답 `200`, `Amazon CloudFront` User-Agent 기록 |

이 `GET /login.php`는 Audit Event를 만들지 않아 CloudFront부터 Application까지
하나의 ID로 이어지지는 않지만 UTC 시각, Method, Path, 응답 상태와 요청
흐름이 일치한다. Query String은 Evidence Sanitizer가 의도적으로
제거했으므로 Marker 원문을 보존하지 않았다.

## 5. BANK Audit Event Coverage

현재 Source에서 정적 확인한 Event Type은 다음과 같다.

| 영역 | Event Type | 현재 경계 |
|---|---|---|
| 로그인 | `auth.login.succeeded`, `auth.login.failed` | Primary Runtime에서 실패 Event 전달 확인 |
| 로그아웃 | `auth.logout.succeeded` | Source·Test 확인, 이번 Runtime의 개별 Event 미확인 |
| 회원가입 | `auth.registration.succeeded`, `auth.registration.failed` | 성공·여러 검증 실패 경로에 배치됨 |
| 접근통제 | `authorization.access.denied` | Runtime 전달 확인. 기존 `/` Health Check Noise와 실제 접근 거부를 분류해야 함 |
| CSRF | `security.csrf.failed` | Source 확인, 본편 Runtime 미검증 |
| 보안 수준 | `security.level.changed` | Source 확인, 본편 Runtime 미검증 |

`request_id`는 ALB가 전달한 `X-Amzn-Trace-Id`를 형식 검증 후 우선 사용하고,
없으면 `app-*` ID를 생성한다. 기존 Sanitized Bundle에서
`authorization.access.denied` 2건을 ALB Log와 다시 대조한 결과는 다음과 같다.

| BANK Audit 시각 | ALB 시각 | Path | 결과 | Correlation |
|---|---|---|---|---|
| `19:14:01.095372Z` | `19:14:01.095829Z` | `/` | Application `denied`, ALB `302` | 동일 `Root=...` Trace ID |
| `19:16:27.480619Z` | `19:16:27.481179Z` | `/` | Application `denied`, ALB `302` | 동일 `Root=...` Trace ID |

따라서 **ALB → BANK Audit Event의 직접 1:1 Correlation은 Runtime으로
확인됐다.** CloudFront `x-edge-request-id`는 별도 ID이므로 Edge부터 ALB까지는
여전히 시각·Source IP·Method·Path를 함께 사용한다.

현재 BANK Source에는 실제 계좌 잔액·이체 업무가 구현됐다는 근거가 없어
계좌 조회·이체 Event도 존재하지 않는다. 팀이 해당 기능을 추가하면 기능
성공·실패와 접근 거부를 같은 Audit Helper로 계측해야 하며, 지금 이를
구현 완료라고 표현하지 않는다.

## 6. 확인된 자동화 결함과 보정

### 새 Bastion과 stale `bas` Alias

Daily Up은 새 Bastion을 만들었지만 로컬 SSH Config의 `Host bas`는 이전 Public IP를 유지했다. AWS Runtime은 정상이어도 `argocd-ui.ps1`과 다음 SSH 작업이 Timeout되는 결함이다.

보정 후 Daily Up은 다음을 수행한다.

1. Terraform Output에서 현재 Bastion IPv4를 확인한다.
2. SSH Config의 정확한 단일 `Host bas` Block만 교체한다.
3. 다른 Host Block은 보존한다.
4. Block이 없으면 새로 추가한다.
5. 같은 값으로 재실행해도 파일이 다시 변하지 않는다.

PowerShell Parser와 회귀 Self-test 통과 후 실제 `bas` Alias로 Node 2개와 DVWA Pod Ready를 다시 확인했다.

## 7. 현재 Noise와 미검증

- 현재 Runtime의 ALB Health Check가 `/`에 반복 접근하면서 `authorization.access.denied` Audit Event를 다량 만든다. Terraform 기본 경로를 비인증 `/login.php`로 보정하고 정적 검증은 통과했으나, 실제 Noise 감소는 다음 Daily Up에서 확인해야 한다.
- WAF 정상 `ALLOW` 요청은 비용 통제 Filter 때문에 저장하지 않는다. CloudFront·ALB·Application Log로 정상 요청을 추적하고, WAF는 `COUNT`·`BLOCK` Event에 사용한다.
- ALB `trace_id`와 BANK `request_id`의 직접 연결은 2건 확인했다. CloudFront `x-edge-request-id`는 별도이므로 Edge 구간은 시간·Source IP·Method·Path와 함께 연결해야 한다.
- DR Application Log Group에 비민감 구조화 Probe Event 1건이 실제 전달됐고 Evidence 수집 뒤 Probe Pod를 삭제했다. 실제 BANK DR Workload Event의 업무 의미 검증은 별도다.
- `WEB-01`의 `auth.login.failed`를 집계하는 Metric Filter, 5분 동안 5건 이상이면 전환되는 Alarm, SNS Topic을 Foundation에 적용했다. 이번 Runtime에서 `OK → ALARM → OK` 전체 전환을 확인했다. SNS Subscription은 0건이므로 외부 알림 수신은 미검증이다.
- `WEB-01`·`IAM-01`은 팀이 확정한 공격 주제가 아니라 관측 Pipeline 검증 후보다.
- Athena External Table과 제한 실행기로 승인된 Query 4개를 실제 실행했다. `alb-errors` 0행·37,091B, `vpc-reject` 534행·584,542B, `cloudfront-trace` 180행·26,537B, `alb-trace` 1행·37,091B로 모두 `SUCCEEDED`였고 총 Scan은 약 685KB다. ALB Trace 1건은 Sanitized BANK `request_id`와 연결됐다.

### 2026-08-02 관측 검증 후보 실행

- `WEB-01`: `before/count/block`에서 로그인 실패를 각 20회 실행했고 BANK Audit Log는 각 단계 20건을 기록했다. 세 단계 모두 HTTP 200이었다. `COUNT`는 마지막 2건만 `bank-login-rate` Match, `BLOCK`은 Match 0건·HTTP 403 0건이었다.
- 이번 재실행은 Web ACL 변경 뒤 90초를 기다리고 각 단계 요청을 약 57초 동안 보냈다. 따라서 이전의 짧은 실행시간만으로 실패를 설명할 수 없다. Rate 집계·평가 지연·Rule 설정과 실제 WAF Event를 다시 분리 진단해야 하며, 현재 판정은 **관측 성공·차단 미검증**이다.
- 실험 뒤 WAF Mode는 Fresh Plan으로 기본값 `disabled`에 복구했다.
- `IAM-01`: 조치 전 Pod Identity Role Assume과 Canary S3 Put/Get/Delete·정리를 확인했다. 관련 IAM Role·Policy·Association 6개를 제거한 뒤 같은 실행에서 Credential을 얻지 못했고 S3 Object API Event도 0건이었다.
- IAM 조치가 다음 Up에서 되돌아가지 않도록 `enable_web_s3_pod_identity` 기본값을 `false`로 변경했고, 최신 Cold Up에서 값과 BANK Workload Association 부재를 Runtime으로 재확인했다.
- WEB·Athena·DR와 Final Down Evidence는 위 Bundle별 SHA-256 대조에서 모두 불일치 0이다.
- 실험 종료 후 Daily Runtime 250개를 제거했다. 독립 확인 결과 Daily State·태그 기반 Runtime·Terraform Process·Watchdog·활성 Session은 0이고 Foundation State 27개와 로그 보존 계층은 유지됐다.

Final Post-Down Evidence를 생성할 때 깊이 30을 넘는 AWS JSON이 PowerShell에서 경고와 함께 잘리는 결함을 발견했다. Evidence JSON 직렬화 깊이를 100으로 통일하고 40단계 Nested JSON의 최하위 값 보존·민감값 Redaction을 PowerShell 5.1과 7에서 검증했다. 별도 Foundation-only 회귀 Bundle도 경고 없이 생성되고 SHA-256 57개가 일치했다.

## 8. 다음 Gate

1. WAF Rate Rule이 90초 전파 대기와 약 57초 요청에서도 `COUNT` 2건·`BLOCK` 0건이었던 원인을 집계·평가 지연, Rule 설정과 실제 WAF Event로 나눠 진단한다.
2. 다음 Daily Up에서 ALB Health Check `/login.php`의 Audit Noise 감소를 Runtime으로 확인한다.
3. 팀이 본편 대표 공격·이상행위 시나리오를 선택하고 조치 전·후 동일 조건 실험을 수행한다.
4. 실제 알림이 필요하면 확인된 SNS 수신자를 구독하고 전달을 검증한다.
5. 개인 Account 구현을 팀 Account와 다른 노트북에서 Credential·State 복사 없이 재생성할 수 있는지 검증한다.

## 9. Goal 진행 경계

| Phase | 현재 상태 | 완료로 보지 않는 이유·다음 조건 |
|---|---|---|
| 0. Baseline | Runtime 확인 | 현재 표와 Source·State 대조 완료 |
| 1. 시나리오 후보 | 후보 2개 정의 | 팀·멘토의 본편 선택이 아님 |
| 2. 최소 Observability | Primary·DR Runtime 전달 확인 | DR 업무 Event 의미와 Health Check Noise 감소는 미검증 |
| 3. BANK Audit Log | Primary Runtime 확인 | 실제 본편 시나리오의 Event 완전성은 미검증 |
| 4. Evidence Collector | WEB·IAM·Athena·DR·Final Down Bundle과 Hash 확인 | WEB 조치 성공 증거는 없음 |
| 5. Query·탐지·알림 | CWLI·Athena 4개 Query와 Alarm `OK → ALARM → OK` Runtime 확인 | SNS Subscription 0으로 실제 외부 알림 수신은 미검증 |
| 6. 통제된 보안 실험 | 관측 후보 2개 부분 실행 | IAM 전·후 차이는 확인했지만 WEB 차단과 팀 확정 본편은 없음 |
| 7. Daily Lifecycle | 최신 Cold Up·Down, Pod Identity 기본 비활성, Foundation·Evidence 보존, Watchdog 제거 확인 | 이 Session 범위 충족 |
| 8. 보고서 산출물 | As-built·멘토 초안 갱신 | 팀 확정 시나리오와 WEB 성공 조치 증거가 없음 |

따라서 현재 성과는 **배포·로그 전달·증거 수집 기반의 Runtime 검증**이며 Goal 전체 완료가 아니다.

## 10. Goal 완료 조건 증거 감사

| # | 완료 조건 | 현재 증거 | 판정·남은 일 |
|---:|---|---|---|
| 1 | 기존 CI/CD·GitOps 무회귀 | 현재 immutable Image, Argo `Synced / Healthy`, Pod Ready | 부분 충족. Observability 변경 뒤 새 Source Push End-to-End는 재실행하지 않음 |
| 2 | 필요한 Log Source 실제 도착 | CloudTrail·CloudFront·ALB·VPC·EKS·Primary/DR DVWA Runtime 전달, WAF `COUNT` Event | 기반 충족. WAF `BLOCK` Event와 확정 시나리오별 Source 완전성은 후속 검증 |
| 3 | 구조화 보안 Event와 Secret 제외 | BANK Audit JSON, 금지 Context Allowlist, Sanitized Bundle Secret Pattern 0 | 부분 충족. 로그인·회원가입·접근통제·Security Event는 있으나 계좌·이체 기능 자체가 없음 |
| 4 | 정상 요청 Edge→Application 추적 | `/login.php`의 CloudFront→ALB→DVWA 추적, ALB Trace→BANK Request ID 2건 직접 일치 | 충족 |
| 5 | 대표 시나리오 2개 조치 전 실행 | WEB-01 20회×3단계, IAM-01 허용 상태 Canary | 부분 충족. 관측 후보 실행이며 팀이 본편으로 확정하지 않음 |
| 6 | 각 시나리오 차단·통과와 Log 설명 | WEB Application 도달 20건씩·WAF Match 0, IAM 허용·Credential 부재와 S3 Event 차이 | 부분 충족. IAM은 설명 가능하지만 WEB 차단 지점이 만들어지지 않음 |
| 7 | 조치 후 동일 조건 결과 차이 | IAM Role·Policy·Association 제거 전 S3 성공, 제거 후 Credential 없음 | 부분 충족. IAM은 충족, WEB은 미충족 |
| 8 | Query Pack과 최소 탐지 규칙 | CWLI Runtime, Athena 4개 Query `SUCCEEDED`, WEB-01 Alarm `OK → ALARM → OK` | 부분 충족. 실제 SNS 알림 수신과 확정 본편 탐지 규칙은 미검증 |
| 9 | 실험별 Local Evidence Bundle·Hash | WEB·IAM·Athena·DR·Final Down Bundle의 SHA-256 불일치 0 | 부분 충족. WEB 성공 조치 Bundle은 없음 |
| 10 | Down 뒤 AWS Log 30일·Local Evidence 보존 | Daily State·태그 Runtime 0, Foundation 27·ECR 24·로그·탐지 계층·Local Bundle 보존 | 충족 |
| 11 | 다음 Up에서 Collector·Application 자동 복원 | 최신 Cold Up에서 Primary·DR Fluent Bit, BANK DVWA, Argo `Synced / Healthy`, Pod Identity 기본 비활성 확인 | Runtime 충족 |
| 12 | 비용·미구현·미검증·False Positive 공개 | As-built의 Noise·미검증, Query Metadata, 후보 경계 | 충족 |
| 13 | 멘토 비교 평가용 보고서 초안 | [[20_팀 프로젝트/3차 프로젝트/멘토 상담용 관측성 진행 보고 초안]] | 초안 충족. 본편 시나리오 전후 결과는 비어 있음 |
| 14 | 개인 Account와 팀 이식 구분 | 문서에서 개인 Account Runtime과 팀 이식 미검증을 분리 | 부분 충족. 다른 Account·노트북 재생성 Runtime 없음 |

현재 확정 충족은 4·10·11·12이며, 13은 본편 결과 전의 진행 초안이다. 나머지를
검증하지 않고 Goal을 완료 처리하지 않는다.
