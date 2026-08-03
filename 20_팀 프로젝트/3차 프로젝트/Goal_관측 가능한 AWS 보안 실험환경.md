---
type: project-doc
status: active
created: 2026-07-31
project: 3차 프로젝트
project_moc: "[[20_팀 프로젝트/3차 프로젝트/00_3차프로젝트_목차]]"
---

# Goal — 저비용 Daily Runtime과 관측 가능한 AWS 보안 실험환경

이 문서는 다음 세 작업공간을 이용해 3차 프로젝트를 발전시키기 위한 canonical Goal이자 실행 프롬프트다.

- Application: `D:\DVWA`
- Infrastructure: `D:\terraform\aws_terraform_build_code`
- Project records: `D:\Obsidian\Vault\Obsi2\20_팀 프로젝트\3차 프로젝트`

이 문서에 계획이 적혀 있다는 사실은 구현이나 Runtime 검증의 증거가 아니다. 현재 Source·State·AWS Runtime·Kubernetes Runtime·Git Diff를 다시 확인하고, 실제 결과에 따라 완료 여부를 판정한다.

## 목적

> 평상시에는 비용을 줄인 재현 가능한 BANK 웹서비스 환경을 사용하고, 통제된 보안 시나리오에서 `관측 → 탐지 → 알림 → 조치 → 동일 조건 재검증 → Evidence 보존` 흐름을 증명한다.

이 Goal은 기존 CI/CD·GitOps·Observability를 처음부터 다시 만드는 작업이 아니다. 이미 작동하는 기반을 보존하면서 다음 두 문제를 해결한다.

1. Daily Runtime에 불필요한 DR·고가용성·미사용 Resource가 포함돼 비용과 생성 시간을 늘리는 문제
2. 로그는 수집하지만 사건을 Finding으로 발견하고 조사하는 흐름이 부족한 문제

## 확정한 선택

| 코드 | 확정 선택 | 운영 의미 |
|---|---|---|
| H1 | 기존 Public Hosted Zone을 `data`로 조회 | Hosted Zone은 외부에서 계속 유지하며 Daily Terraform이 생성·삭제하지 않음 |
| E2 | Hosted Zone + ACM 수명주기 분리 | ACM Certificate와 DNS Validation은 Foundation에서 유지하고 CloudFront·WAF는 Daily에 유지 |
| N1 | Primary EKS Node 1대부터 시험 | 안정성 검증에 실패하면 2대를 실제 최소값으로 확정 |
| V1 | Valkey·EFS 기본 비활성 | 실제 Application 의존성이 증명될 때만 활성화 |
| T1 | HTTPS Redirect 안전 기본값 | 명시적인 보안 실험에서만 HTTP 허용 |
| F2 | AWS Native Finding + Custom Finding | GuardDuty·EventBridge·SNS와 기존 로그 기반 Finding까지만 구현 |
| W1 | Watchdog 예약 자동 Down을 `On/Off`로 선택 | Session 안전 규칙은 유지하고 Task Scheduler 자동 Down만 토글 |

> [!important] F2 범위 선언
> 이 Goal은 **F3가 아니다.** Security Hub, Detective, OpenSearch, 완전한 SIEM, 상시 SOC Platform, 대규모 SOAR를 구축하지 않는다. 멘토 요구나 검증된 필요가 새로 생기기 전에는 범위를 F2 밖으로 확장하지 않는다.

## Task Frame

| Field | Current framing |
|---|---|
| Intended outcome | 평상시 저비용 `minimal` Runtime과 필요 시 재현 가능한 `dr-test`, 그리고 조사 가능한 Finding·Evidence 흐름 |
| Scope | Terraform 수명주기, Daily Wrapper, Watchdog Toggle, 최소 Observability, Finding F2, Runtime 검증, 운영 문서 |
| Explicit exclusions | F3 SIEM/SOC, 상시 OpenSearch, Security Hub·Detective, 무제한 Lambda 분석, 무단 공격, 기존 CI/CD 재작성 |
| Evidence needed | 현재 Source·State·Plan, AWS/Kubernetes Runtime, Log Delivery, Finding, Evidence Bundle, 비용·잔존 Resource |
| Known constraints | 개인 AWS Account 우선 검증, Daily Down 필요, 현재 Terraform과 보안 검토 작업 보존, Secret·State 비공개 |
| Reversible assumptions | Node 1대, Valkey·EFS 미사용, Domain 입력 방식, Watchdog 기본 On |
| Material decisions | H1·E2·N1·V1·T1·F2·W1 확정 |
| Definition of done | `minimal` Cold Start·Down, Finding F2, Evidence, DR 선택 실행, CI/CD 회귀 없음이 실제 Runtime에서 확인됨 |
| Verification method | 정적 Test와 실제 Runtime Test를 분리하고 Plan·Log·Query·Finding·Evidence로 증명 |
| First safe action | 현재 Git Diff·State·Runtime·Foundation/Daily 소유권을 읽기 전용으로 고정 |

## 증거 우선순위

판단은 다음 순서를 따른다.

1. 현재 Runtime 출력과 실제 AWS·Kubernetes 동작
2. 현재 Source, Terraform State, Plan, Git Diff와 Test 결과
3. 현재 공식 AWS·Kubernetes·Terraform·GitHub·Argo CD 문서
4. 프로젝트 기록과 사용자 설명
5. AI 제안과 Parametric Knowledge

Terraform 정의나 문서가 존재한다는 이유만으로 배포·로그 전달·탐지·복구가 검증됐다고 판정하지 않는다.

## 현재 출발점

작업 시작 시 실제 파일과 Runtime으로 다시 확인하되 다음을 초기 기준으로 사용한다.

- BANK DVWA의 기존 배포 흐름은 `GitHub Actions → ECR immutable image → GitOps Commit → Argo CD → EKS`다.
- Foundation과 Daily Runtime은 별도 Terraform Root·State로 분리돼 있다.
- `daily-up.ps1`, `daily-down.ps1`, DB Bootstrap, Evidence Collector와 독립 Watchdog이 존재한다.
- Foundation 로그 보존 기본값은 30일이다.
- CloudTrail·CloudFront·WAF·ALB·EKS·Application·VPC Flow Log와 Query·Evidence 관련 구현이 존재한다.
- SNS·Alarm 기반 Detection 기초와 WEB-01·IAM-01 시나리오가 존재한다.
- 현재 보안 시간창 검토 기능의 미커밋 변경이 있을 수 있으므로 덮어쓰거나 되돌리지 않는다.
- 현재 Source에는 통합 `runtime_profile`이 없다.
- `enable_dr_compute`는 DR 전체 수명주기를 통제하지 못한다.
- Primary RDS는 Multi-AZ, Primary EKS Node는 기본 2대다.
- DR VPC·RDS Replica와 Primary·DR Valkey·EFS는 Profile 없이 생성되는 범위가 있다.
- 기존 Route 53 Hosted Zone을 조회하는 경로가 있지만 ACM·CloudFront·WAF는 Daily Root에 있다.
- GuardDuty Resource는 현재 Source와 Runtime에서 다시 확인해야 한다.
- 개인 Account Apply 성공을 팀 Account·다른 노트북 이식 완료로 표현하지 않는다.

현재 Source가 이 초기 기준보다 새로우면 현재 Source와 Runtime을 우선하고 차이를 기록한다.

## 목표 수명주기

### 외부에서 지속 유지

- Domain 등록
- Public Hosted Zone
- Registrar 또는 상위 Zone의 NS 위임

Hosted Zone은 Daily Terraform이 생성·삭제하지 않고 `data.aws_route53_zone`으로 조회한다. 다른 Terraform State가 Hosted Zone을 소유하고 있다면 이중으로 관리하지 않는다.

### Foundation에서 지속 유지

- ECR Repository와 immutable Image
- GitHub Actions OIDC Provider·최소권한 IAM Role
- CloudTrail 및 보안 로그 저장 계층
- CloudWatch Log Group·S3 Lifecycle 30일
- Evidence 조회에 필요한 Output
- SNS·Alarm 등 이미 승인된 Detection 기반
- CloudFront용 ACM Certificate와 DNS Validation Record

CloudFront용 ACM Certificate는 `us-east-1`에서 관리하고, Daily Root는 Foundation Output의 Certificate ARN을 소비한다.

### Daily Runtime에서 생성·삭제

- Primary VPC·Subnet·NAT·Security Group
- ALB·Target Group
- EKS·Node·Add-on·Argo CD
- RDS와 Application Runtime
- CloudFront Distribution·WAF Web ACL
- Domain Alias Record
- Runtime Log Source와 Collector
- `dr-test`에서만 생성되는 DR Runtime

E2를 선택했으므로 CloudFront·WAF 생성 시간은 Daily Up에 남는다. 이번 단계에서 이를 Foundation으로 옮기지 않는다.

## Runtime Profile

사용자가 여러 Boolean을 직접 조합하지 않고 하나의 Profile로 통제한다.

```hcl
runtime_profile = "minimal"
```

| 구성 | `minimal` | `dr-test` | `full` |
|---|---:|---:|---:|
| Primary VPC·NAT·ALB | 사용 | 사용 | 사용 |
| Primary EKS | 사용 | 사용 | 사용 |
| Primary Node | 1대 시험 | 1대 시험 | 2대 |
| Primary RDS | Single-AZ | Single-AZ | Multi-AZ |
| DR VPC·NAT | 미생성 | 생성 | 생성 |
| DR EKS·ALB | 미생성 | 생성 | 생성 |
| DR RDS Replica | 미생성 | 생성 | 생성 |
| Valkey | 미생성 | 기본 미생성 | 명시적으로 필요한 경우만 |
| EFS | 미생성 | 기본 미생성 | 명시적으로 필요한 경우만 |
| Primary 로그 | 유지 | 유지 | 유지 |
| DR 로그 | 미생성 | 유지 | 유지 |
| Finding Foundation | 유지 | 유지 | 유지 |

### Profile 구현 규칙

- `locals`가 Profile별 내부 Feature Flag를 계산한다.
- DR VPC부터 모든 DR 의존 Resource에 같은 생명주기 조건을 적용한다.
- Valkey·EFS와 관련 Security Group·Subnet Group·IAM·Output도 함께 조건부로 만든다.
- 조건부 Resource가 없을 때 Output은 `null`을 반환한다.
- Terraform Output과 Session 상태에 실제 적용 Profile을 기록한다.
- 살아 있는 Runtime을 다른 Profile로 즉석 변경하지 않는다.
- Profile 전환은 원칙적으로 `daily-down → daily-up`으로 수행한다.
- 정상 운영에서 `terraform -target`을 사용하지 않는다.

### N1 성공·실패 기준

Node 1대는 비용 절감을 위한 시험값이다.

성공 조건:

- CoreDNS, Fluent Bit, AWS Load Balancer Controller, Argo CD, DVWA가 모두 Ready
- Scheduling 불가 Pod가 없음
- OOMKilled·Eviction·지속적인 ResourcePressure가 없음
- CI/CD Rolling Update와 Evidence 수집을 동시에 수행할 수 있음

하나라도 실패하면 Node 2대를 실제 최소값으로 확정한다. 실패를 숨기거나 자동으로 2대로 올린 뒤 1대 성공으로 기록하지 않는다.

## Watchdog Toggle

현재 `SessionSafety.Enabled`는 Daily Apply 허용과 Deadline 안전 규칙을 통제하므로 Watchdog Toggle로 사용하지 않는다.

새 인터페이스:

```powershell
.\daily-up.ps1 -RuntimeProfile minimal -WatchdogMode On
.\daily-up.ps1 -RuntimeProfile minimal -WatchdogMode Off
```

### 공통 규칙

- `SessionSafety.Enabled`는 계속 `true`로 유지한다.
- Soft Deadline·Hard Deadline·Session 상태·중복 실행 방지는 두 Mode에서 모두 유지한다.
- 기본값은 비용 사고 방지를 위해 `On`이다.
- 실행 결과에 Watchdog Mode와 Deadline을 명확히 출력한다.
- Mode는 Session 시작 뒤 몰래 바꾸지 않고 다음 Session부터 적용한다.

### `On`

- Windows Task Scheduler에 해당 Session 전용 자동 Down 작업을 등록한다.
- Hard Deadline에 Fresh Destroy Plan과 Foundation 보호 검사를 거쳐 Daily Down을 수행한다.
- 성공한 수동 Daily Down은 예약 작업과 Session 상태를 제거한다.

### `Off`

- 예약 자동 Down 작업을 등록하지 않는다.
- 콘솔과 Session Log에 `WATCHDOG DISABLED — MANUAL DAILY DOWN REQUIRED`를 출력한다.
- Session 상태와 Deadline 기록은 유지한다.
- 비용 Runtime을 사용자가 직접 Down해야 한다.
- `daily-down.ps1`은 예약 작업이 없어도 정상 완료돼야 한다.

노트북 전원 종료, Credential 만료, Terraform Process·State Lock이 있으면 `On`도 자동 Down을 절대 보장하지 않는다. 기존 Process를 임의로 Kill하거나 Lock을 강제 해제하지 않고 제한된 재시도 뒤 실패와 잔존 과금 가능 Resource를 기록한다.

## 최소 Observability 계약

`minimal`에서도 다음 Log Source를 유지한다.

- CloudFront Standard Access Log
- WAF Web ACL Log
- Primary ALB Access Log
- Primary EKS `api`, `audit`, `authenticator`
- DVWA Container stdout/stderr
- BANK Application 구조화 Audit Log
- CloudTrail Management Event
- Primary VPC `REJECT` Flow Log

`dr-test`에서는 다음을 추가한다.

- DR ALB Access Log
- DR EKS Control Plane Log
- DR Application Log
- DR VPC Flow Log
- Primary·DR 비교 Evidence

비용 통제:

- AWS 로그 보존 기본값 30일
- Application Log는 DVWA Namespace만 수집
- VPC Flow Log는 우선 `REJECT`만 수집
- Cookie, Session ID, Authorization Header, Password, Token, 전체 Request Body를 저장하지 않음
- 전체 Container Insights와 모든 System Log를 무조건 활성화하지 않음

## Finding F2 계약

### AWS Native Finding

```text
GuardDuty
→ EventBridge
→ SNS
→ 원본 Finding 또는 Evidence Pointer 보존
```

- 기존 Detector·Topic·Rule이 있는지 먼저 조회한다.
- 중복 Detector와 중복 알림을 만들지 않는다.
- Sample Finding으로 전달 흐름을 검증한다.
- 고비용 GuardDuty 부가기능은 시나리오 필요가 확인될 때만 검토한다.

### Custom Finding

기존 로그에서 다음 사건을 공통 Finding 형식으로 변환한다.

- 반복 로그인 실패
- WAF Rule Match·차단
- `kubectl exec`
- Secret 조회·거부
- IAM·Security Group 변경
- Application 중요 기능 실패·접근 거부
- ALB 4xx·5xx 이상

```json
{
  "finding_id": "...",
  "timestamp": "UTC ISO-8601",
  "runtime_profile": "minimal",
  "region": "ap-northeast-2",
  "source": "GuardDuty | WAF | EKS | Application | CloudTrail",
  "severity": "...",
  "entities": [],
  "evidence_pointer": "...",
  "scenario_id": null
}
```

조사는 공격자 IP나 공격 유형을 미리 알고 시작하는 방식에 의존하지 않는다. Finding이 시간창, Source IP, 사용자, Resource, 관련 Evidence Pointer를 제공해야 한다.

### 명시적으로 하지 않는 F3

- Security Hub 중심 통합
- Detective 조사 Graph
- OpenSearch 상시 Cluster
- 완전한 SIEM Dashboard
- 전사 SOC Workflow
- 대규모 SOAR·무인 자동 차단
- 로그가 있다는 이유만으로 경보를 대량 생성하는 작업

Lambda는 Finding 정규화·중복 제거·Incident ID 생성이 실제로 필요하다는 증거가 생길 때만 별도 승인을 받아 검토한다.

## HTTPS 실험 T1

- `enable_https_redirect = true`가 안전 기본값이다.
- `false`는 승인된 HTTP 보안 실험에서만 사용한다.
- HTTP 허용 상태에서는 Wrapper가 강한 경고를 출력한다.
- Redirect On/Off 모두 WAF·CloudFront·ALB·Application Log가 유지돼야 한다.
- 실험 종료 후 같은 Session에서 HTTPS Redirect를 복원하고 재검증한다.

## 실행 Phase

### Phase 0 — 기준선 고정

- DVWA와 Terraform Git 상태·Diff 확인
- 현재 Foundation/Daily State와 AWS Account·Region 확인
- 현재 Runtime과 과금 Resource 확인
- 기존 CI/CD·GitOps·Observability 정상 기준 기록
- 현재 미커밋 보안 검토 작업의 범위·Test 상태 확인

읽기 전용으로 수행하며 기존 변경을 되돌리지 않는다.

### Phase 1 — 현재 변경분 안정화

- 보안 시간창 검토 기능의 Targeted Diff 확인
- 관련 Test와 Secret Scan 수행
- 완성된 변경과 후속 작업을 구분
- Runtime Profile 작업과 섞이지 않도록 기준 Commit 또는 명시적 Start Ref 확보

### Phase 2 — H1·E2 수명주기 적용

- Hosted Zone의 실제 Domain, Zone ID, AWS Account와 NS 위임 확인
- Daily의 `aws_route53_zone` 생성 경로를 정상 운영에서 사용하지 않음
- Foundation에서 기존 Hosted Zone을 `data`로 조회
- `us-east-1` ACM Certificate와 DNS Validation을 Foundation이 소유
- Certificate ARN을 Foundation Output으로 제공
- Daily CloudFront가 Foundation Certificate ARN을 소비
- CloudFront·WAF·Domain Alias는 Daily 소유로 유지
- Hosted Zone이 Daily Destroy Plan에 들어가면 즉시 실패

ACM·DNS Validation의 State 이전은 Daily State와 실제 Resource를 확인한 뒤 계획한다. 동일 Certificate나 DNS Validation Record를 중복 생성하지 않는다.

### Phase 3 — Runtime Profile 정적 구현

- `runtime_profile` Variable·Validation·locals 추가
- DR VPC·NAT·EKS·ALB·RDS·Security Group·KMS·Output 조건부 처리
- Primary RDS Single-AZ 선택
- Node 수 Profile화
- Valkey·EFS와 모든 의존 Resource 선택화
- Wrapper에 `-RuntimeProfile` 추가
- Profile 전환 안전 검사와 실제 적용 Profile 출력

### Phase 4 — Watchdog Toggle 구현

- `-WatchdogMode On|Off` 추가
- Session 안전과 예약 자동 Down을 분리
- `On`, `Off`, 수동 Down, 등록 실패, 기존 Session 재사용 Test
- `Off`일 때 명시적 경고와 Log 확인
- 기존 기본 `On` 동작 회귀 방지

### Phase 5 — 정적 검증

- `terraform fmt -check`
- `terraform validate`
- `minimal`, `dr-test`, `full` Plan 비교
- Foundation Resource의 Daily Destroy 포함 여부 검사
- PowerShell Parser·Daily Automation·Watchdog Test
- Shell `bash -n`
- Helm `lint`, `template`
- GitHub Workflow YAML 검사
- Evidence Redaction·Log Injection·Retry·Partial Failure Test
- `git diff --check`
- Secret Scan

정적 검증을 Runtime 성공으로 표현하지 않는다.

### Phase 6 — 수명주기 이전 Gate

- 현재 Runtime이 Up이면 Fresh Destroy Plan 확인
- Foundation Resource가 포함되지 않았는지 검사
- 승인된 Daily Down 수행
- Daily State 0과 실제 AWS 잔존 Resource 확인
- Foundation State·ECR·OIDC·로그 계층 보존 확인
- H1·E2 Foundation Plan 검토 후 승인된 Apply 수행

### Phase 7 — `minimal` Cold Start

```text
daily-up minimal
→ BANK DVWA·DB Bootstrap
→ Argo CD Synced/Healthy
→ CloudFront·WAF·ALB 접근
→ Log Delivery
→ Finding Test Event
→ Evidence Bundle
```

검증:

- DVWA와 DB 정상
- Browser 수동 DB Setup 불필요
- Pod Ready와 CI/CD Rolling Update 정상
- Node 1대의 N1 기준 통과 또는 2대 필요 증거 확보
- Valkey·EFS 없이 기능 회귀 없음
- DR VPC·NAT·RDS Replica가 생성되지 않음
- ACM이 Daily에서 재생성되지 않음
- CloudFront·WAF는 E2 선택대로 Daily에서 생성됨
- 모든 필수 Primary Log 도착
- Daily Down 뒤 Foundation 로그와 Local Evidence 보존

### Phase 8 — T1 HTTP/HTTPS 검증

- HTTPS Redirect 기본 상태 확인
- 승인된 실험에서만 HTTP 허용
- HTTP와 HTTPS의 Log·WAF·Application Event 비교
- Redirect 복원과 동일 조건 재검증

### Phase 9 — Finding F2 구현·검증

- GuardDuty·EventBridge·SNS 최소 흐름
- Sample Finding 전달
- 기존 Query·Alarm·Evidence를 공통 Finding에 연결
- Custom Finding별 정상·공격 예상 결과와 False Positive 기록
- 실제 시나리오에서 Finding → Evidence 조사 흐름 검증
- F3 Resource가 생성되지 않았음을 Plan과 State에서 확인

### Phase 10 — `dr-test`

평상시에는 실행하지 않는다.

```powershell
.\daily-up.ps1 -RuntimeProfile dr-test -WatchdogMode On
```

- Primary·DR Runtime 생성
- DR RDS Replica 확인
- 양쪽 Log Delivery와 Evidence 비교
- 승인된 장애·복구 실험
- 실험 종료 후 Daily Down
- 다음 Session은 다시 `minimal`

### Phase 11 — 멘토·보고서 산출물

- 현재 As-built Architecture
- Foundation·Daily·외부 DNS 소유권 표
- Runtime Profile별 Resource·비용 차이
- CI/CD·GitOps 흐름도
- Log Source → Finding → Evidence → 대응 흐름도
- 시나리오별 조치 전·후 비교표
- 시행착오·복구 Timeline
- Evidence Bundle 목록과 SHA-256
- 개인 Account 검증과 팀 Account 적용 차이
- 미검증 항목과 멘토 결정 질문
- F2 범위와 F3 제외 근거

## 변경·승인 경계

승인 없이 가능:

- 읽기 전용 Baseline 조사
- Source·Diff 검토
- Local Code·Test·문서 수정
- Query·Finding Schema·Evidence Collector 작성
- 정적 검증
- 민감정보 없는 RAW 기록

실행 전 Target·영향을 보고하고 승인 필요:

- Terraform Apply·Destroy
- Foundation State 이전·Import
- GitHub Repository Settings 변경
- 비용이 지속되는 AWS Service 추가
- WAF 차단 모드 전환
- 통제된 공격·Misconfiguration
- 운영 Data 삭제
- 팀원 작업에 영향을 주는 구조 변경

사용자가 하나의 Daily Session을 승인하면 명시된 Up·실험·Evidence와 같은 Session의 안전한 Down까지 포함할 수 있다. 승인 범위를 넘어 다른 Profile·공격·AWS 변경을 임의로 추가하지 않는다.

## Git·Secret 안전

- 기존 사용자·팀원 변경을 보존한다.
- 과거 ZIP이나 Backup을 현재 Source 위에 통째로 덮어쓰지 않는다.
- Terraform Folder를 임의의 새 Remote에 연결하지 않는다.
- `.terraform`, State, Plan, Credential, Private Key, kubeconfig를 Git·Vault·Evidence에 넣지 않는다.
- Force Push와 History Rewrite를 하지 않는다.
- Commit 전 Targeted Diff와 Secret Scan을 수행한다.
- 실제 Secret 값은 Console, Log, Query, RAW, Goal에 기록하지 않는다.
- Account·Region·Role·Hosted Zone·Key Pair·OIDC Subject를 외부 입력으로 분리한다.

## 완료 판정

다음을 모두 충족해야 Goal을 완료로 표시한다.

1. 기존 BANK DVWA CI/CD·GitOps 배포가 회귀하지 않았다.
2. H1에 따라 Hosted Zone이 Daily 생성·삭제 대상에서 제외됐다.
3. E2에 따라 ACM·DNS Validation은 Foundation에 남고 CloudFront·WAF는 Daily에서 재현된다.
4. `minimal`에서 DR·Valkey·EFS·RDS Replica가 생성되지 않는다.
5. N1이 실제 Runtime에서 통과했거나 Node 2대가 필요한 증거가 남았다.
6. T1의 HTTPS 기본값과 HTTP 실험 후 복원이 검증됐다.
7. Watchdog `On`과 `Off`가 각각 계약대로 작동한다.
8. Watchdog `Off`에서도 수동 Daily Down과 Session 정리가 정상이다.
9. 필요한 Log Source가 실제 Destination에 도착한다.
10. GuardDuty·EventBridge·SNS와 Custom Finding F2가 실제 Event로 검증됐다.
11. F3 Resource가 Plan·State에 존재하지 않는다.
12. Finding에서 사전 IP·공격 유형 없이 조사 시간창과 Evidence를 찾을 수 있다.
13. Evidence Bundle과 SHA-256 Manifest가 생성된다.
14. Daily Down 뒤 Foundation·30일 AWS 로그·Local Evidence가 보존된다.
15. `dr-test`는 필요 시 재현되고 종료 후 `minimal`로 복귀할 수 있다.
16. 비용·미구현·미검증·False Positive를 숨기지 않는다.
17. 멘토가 목표·선택·비목표·증거·남은 질문을 평가할 수 있다.

코드와 정적 Test만 완성한 상태, Log가 생성됐지만 조회하지 않은 상태, Finding Schema만 작성한 상태, 공격을 한 번 성공시킨 상태는 완료가 아니다.

## 작업 방식과 토큰 절약

- 최초 Baseline 뒤에는 변경된 파일과 관련 Runtime만 다시 확인한다.
- 같은 Repository·공식 문서·AWS 상태를 반복해서 전체 스캔하지 않는다.
- Sub-agent는 사용자가 명시적으로 요청한 경우에만 사용한다.
- 중간 보고는 Phase 완료, 승인 필요, 실제 실패 때만 짧게 한다.
- 긴 실행 증거는 파일에 저장하고 대화에 반복 복사하지 않는다.
- Apply·Destroy 대기 중 같은 상태를 계속 출력하지 않는다.
- 승인 Gate에서는 안전하게 멈추고 무한히 다른 작업을 찾지 않는다.
- 완료 조건을 충족하지 못했으면 시간·예산 때문에 Goal을 완료로 표시하지 않는다.

## 첫 번째 안전 작업

어떠한 AWS·GitHub 변경도 하지 않고 Phase 0을 수행한다.

그 결과 다음만 먼저 보고한다.

1. 현재 Git Diff와 보존해야 할 작업
2. Foundation·Daily·외부 Hosted Zone의 실제 소유권
3. `minimal` Profile에서 제거될 Resource와 유지될 Log
4. H1·E2 State 이전 방식과 실행 Gate
5. Watchdog Toggle 구현 범위
6. 예상 비용 변화와 Runtime 검증 순서

그 뒤 승인된 Phase부터 순서대로 진행한다.
