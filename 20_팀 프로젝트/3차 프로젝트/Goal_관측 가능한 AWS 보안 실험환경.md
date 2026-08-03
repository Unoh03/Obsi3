---
type: project-doc
status: active
created: 2026-07-31
project: 3차 프로젝트
project_moc: "[[20_팀 프로젝트/3차 프로젝트/00_3차프로젝트_목차]]"
---

# Goal — 관측 가능한 AWS 보안 실험환경과 검증 가능한 공격·대응 시나리오 구축

다음 세 작업공간을 이용해 3차 프로젝트를 단순 배포 단계에서
`관측 → 공격·이상행위 → 탐지 → 조치 → 동일 조건 재검증 → 보고서 증거`
단계로 발전시킨다.

- Application: `D:\DVWA`
- Infrastructure: `D:\terraform\aws_terraform_build_code`
- Project records: `D:\Obsidian\Vault\Obsi2\20_팀 프로젝트\3차 프로젝트`

이 Goal의 목적은 로그 서비스를 많이 설치하거나 화려한 SOC를 만드는 것이 아니다.

> 재현 가능한 BANK 웹서비스 환경에서 실제 보안 시나리오를 통제된 방식으로 수행하고, 어떤 계층에서 차단·통과됐으며 어떤 로그가 남았는지 확인한 뒤, 조치와 동일 조건 재실행으로 통제 효과를 증명한다.

## 사용자에게 제공해야 할 최종 경험

1. BANK 형태로 개조한 DVWA가 기존 CI/CD·GitOps 흐름으로 배포된다.
2. 정상 이용과 공격·이상행위가 Edge, Network, Kubernetes, Application, AWS API 계층 중 어디까지 도달했는지 추적할 수 있다.
3. 한 사건의 관련 로그를 시간·요청·사용자·Source IP 기준으로 연결할 수 있다.
4. 조치 전과 후에 같은 행위를 실행하여 결과 차이를 증명한다.
5. 관련 로그·Query 결과·설정 Snapshot을 로컬 Evidence Bundle로 보존한다.
6. Daily Destroy 후에도 AWS 로그는 30일간, 선택한 실험 증거는 로컬에 남는다.
7. 다음 Daily Up에서 로그 수집기와 Application이 자동으로 복원된다.
8. 결과를 멘토 상담과 최종 보고서에서 바로 평가할 수 있다.

## 현재 출발점

작업 시작 시 반드시 실제 파일과 Runtime으로 재확인하되 다음을 초기 기준으로 사용한다.

- 사용자 확인상 BANK DVWA와 기존 배포 흐름은 현재 작동한다.
- 기존 배포 흐름: `GitHub Actions → ECR immutable image → GitOps Commit → Argo CD → EKS`
- Foundation과 Daily Runtime이 별도 Terraform Root·State로 분리돼 있다.
- Daily Up/Down 자동화와 DB Bootstrap이 존재한다.
- 기존 CloudTrail Management Event는 CloudWatch·S3에 30일 보존하도록 구현·검증됐다.
- 2026-07-30 일일 로그 기준으로 다음은 미완성이었다.
  - CloudFront·WAF·ALB 접근 로그
  - Pod/Application 중앙 로그
  - VPC Flow Logs
  - 대표 시나리오별 탐지 Query
  - 경보·대응·동일 조건 재검증
- 현재 Source나 Runtime이 이 기록보다 새로우면 최신 증거를 우선한다.
- Project MOC의 진행 상태는 오래됐을 수 있으므로 완료 판단의 근거로 사용하지 않는다.
- 기존 Daily 자동화와 CI/CD를 회귀시키지 않는 것을 필수 조건으로 둔다.

## 증거 우선순위

판단은 다음 순서를 따른다.

1. 현재 Runtime 출력과 실제 AWS·Kubernetes 동작
2. 현재 Source, State, Git Diff와 테스트 결과
3. 현재 공식 AWS·Kubernetes·Terraform·GitHub·Argo CD 문서
4. 프로젝트 기록과 사용자 설명
5. AI 제안과 Parametric Knowledge

계획 또는 Terraform 정의가 존재한다는 이유만으로 실제 로그 전달·탐지·복구가 검증됐다고 판정하지 않는다.

## Daily Session Timebox

하나의 Daily Session은 `daily-up.ps1` 실행을 시작한 시각부터 계산한다.

- Session 최대 시간: 6시간
- Soft Deadline: 시작 후 5시간
- Hard Deadline: 시작 후 6시간
- 재시도 유예: Hard Deadline 이후 최대 2시간
- 재확인 간격: 15분
- 무한 재시도 금지

Session마다 다른 제한이 필요하면 실행 전에 명시적으로 변경한다. 별도 지정이 없으면 위 기본값을 사용한다.

### Soft Deadline

시작 후 5시간이 되면 다음 규칙을 적용한다.

1. 새로운 공격·변경·Terraform Apply를 시작하지 않는다.
2. 현재 실행 중인 원자적 작업만 안전한 지점까지 마무리한다.
3. 현재 Git Diff, Runtime 상태, 실험 시간창과 미완료 항목을 기록한다.
4. 필수 Evidence 수집을 시작한다.
5. Daily Down을 준비한다.
6. Goal 완료 조건이 남았더라도 다음 날 이어서 할 재시작 지점을 기록한다.

### Hard Deadline

시작 후 6시간이 되면 Goal 진행보다 Daily Runtime 종료를 우선한다.

1. 현재 AWS Account·Region·Daily State 확인
2. 실행 중인 Terraform Process와 State Lock 확인
3. 진행 중인 공격·부하 요청 중단
4. 현재 시간창의 Evidence 수집
5. Fresh Terraform Destroy Plan 생성
6. Foundation Resource 포함 여부 검사
7. 안전할 경우 `daily-down.ps1 -ConfirmDestroy 'DESTROY DAILY'` 실행
8. Daily State와 실제 AWS 잔존 Resource 확인
9. Foundation과 Local Evidence 보존 확인
10. RAW에 실제 결과 기록

Goal이 완료되지 않았더라도 Daily Down을 수행한다. 미완료 Goal은 다음 Session에서 재개한다.

## 독립 Watchdog

시간 제한은 Codex Goal의 Active·Blocked·Complete 상태에만 의존하지 않는다. Windows Task Scheduler를 이용하는 독립 Watchdog을 구현한다.

- Daily Up 시작 시 해당 Session만을 위한 일회성 예약 작업 생성
- 기본 실행 시각은 Session 시작 후 6시간
- 현재 사용자와 작업 경로를 명시적으로 고정
- AWS Credential, Private Key, Secret을 Task 인수나 상태 파일에 기록하지 않음
- `WakeToRun`, Network 사용 가능 조건, 늦은 시작 처리를 명시
- Account, Region, Terraform Root, 시작 시각, Deadline, Experiment ID와 Watchdog 동작 상태만 비민감 Session 상태로 저장
- Daily Down 성공 시 예약 작업과 활성 Session 상태를 제거
- 조기 Daily Down에도 예약 작업과 활성 Session 상태를 제거
- 실패를 성공으로 보고하지 않으며 Watchdog Log에도 Secret을 남기지 않음

노트북이 꺼져 있거나 AWS Credential을 사용할 수 없으면 자동 Down을 절대 보장할 수 없다. 이 경우 실패 원인과 남은 과금 가능 Resource를 명확히 기록한다. Codex Heartbeat는 보조 알림으로 사용할 수 있지만 핵심 안전장치로 의존하지 않는다.

## Terraform Process·Lock 처리

Terraform Apply·Destroy가 진행 중인 상태에서 다른 Destroy를 동시에 실행하지 않는다. Hard Deadline에 Process 또는 Lock이 존재하면 다음을 따른다.

1. 기존 Process를 임의로 Kill하지 않는다.
2. State Lock을 강제로 해제하지 않는다.
3. 15분 간격으로 상태를 재확인한다.
4. 최대 2시간 동안 제한적으로 재시도한다.
5. Process와 Lock이 해제되면 Fresh Destroy Plan부터 다시 수행한다.
6. 2시간 뒤에도 해제되지 않으면 반복을 중단한다.
7. 현재 Process, Lock, State, 확인 가능한 과금 Resource를 기록하고 사용자에게 알린다.

중단된 Apply의 일부 Resource가 존재할 수 있으므로 State가 비었다는 사실만으로 AWS Runtime이 없다고 판정하지 않는다.

## Daily Session 승인 의미

Terraform Apply·Destroy, 공격, WAF 차단 등 기존 승인 경계는 유지한다. 다만 사용자가 정확한 Target·시나리오·요청량·영향을 확인하고 하나의 Daily Session 시작을 승인하면, 그 승인은 해당 Session에 한해 다음을 포함할 수 있다.

- 승인된 `daily-up.ps1`
- 명시된 통제 실험
- 명시된 임시 조치와 동일 조건 재검증
- Evidence 수집
- 조기 종료 또는 Deadline 도달 시의 안전한 Daily Down

Daily Up 승인에는 같은 Session의 안전한 Daily Down 승인을 함께 포함한다. 따라서 사용자가 자리를 비웠다는 이유로 Deadline의 Down을 다시 묻지 않는다.

## Phase 0 — 현재 상태와 회귀 기준 고정

읽기 전용으로 다음을 확인한다.

- DVWA Git 상태, 현재 배포 Image SHA, Helm values
- Terraform Foundation/Daily 소유권과 State
- 현재 AWS Account·Region·실행 중 Resource
- CloudFront → WAF → ALB → EKS → DVWA → RDS 실제 요청 경로
- GitHub Actions → ECR → Argo CD → EKS 배포 경로
- 현재 활성화된 CloudTrail·EKS·WAF·ALB·CloudFront·VPC·Application 로그
- CloudWatch Log Group별 Retention
- EKS의 로그 수집 DaemonSet 또는 Sidecar 유무
- `daily-up.ps1`, `daily-down.ps1`과 Evidence Collector의 현재 기능
- 로그와 Evidence에 Secret·Cookie·개인정보가 들어갈 가능성

결과는 다음 표로 먼저 고정한다.

| Log Source | 현재 수집 | 저장 위치 | 보존 기간 | 조회 방법 | Daily Destroy 후 보존 | 검증 |
|---|---:|---|---:|---|---:|---:|

전체 Repository를 반복 스캔하지 말고 관련 파일·Diff·Runtime만 확인한다.

## Phase 1 — 보호 대상과 시나리오 후보 확정

다음 Data Flow를 As-built 기준으로 작성한다.

```text
사용자
→ CloudFront
→ WAF
→ ALB
→ EKS Service
→ BANK DVWA
→ RDS
```

관리 경로도 별도로 작성한다.

```text
개발자 Push
→ GitHub Actions OIDC
→ ECR
→ GitOps Commit
→ Argo CD
→ Kubernetes API
```

그 뒤 대표 시나리오 후보를 비교한다.

- 웹 계층:
  - 로그인 실패·Credential 공격
  - SQL Injection
  - XSS 또는 비정상 입력
- Kubernetes 계층:
  - `kubectl exec`
  - Secret 조회 시도
  - RBAC 과권한 또는 거부
- AWS·Infrastructure 계층:
  - CloudFront/WAF 우회 가능성
  - Security Group 또는 IAM 변경
  - 공개 설정·권한 오용

바로 모든 공격을 구현하지 않는다. 다음 기준으로 본편 시나리오 2개를 선정하고, 필요하면 후보 1개를 보류한다.

- BANK 서비스의 보호 자산과 직접 연결되는가
- 차단 또는 성공 결과를 안전하게 재현할 수 있는가
- 서로 다른 계층의 로그를 연결할 수 있는가
- 조치 전·후 비교가 가능한가
- 멘토와 보고서에서 설명 가치가 있는가
- 같은 웹 공격의 변형 두 개로만 구성되지 않는가

각 시나리오는 다음 계약을 갖는다.

```text
보호 자산
정상 Baseline
공격·이상행위
예상 통제
필요 로그
성공·차단 판정 기준
조치
동일 조건 재검증
중단·복구 조건
```

## Phase 2 — 최소 Observability Architecture 구현

로그 목적지를 Daily Destroy에서 보존되는 Foundation에 둔다. 로그를 발생시키는 Resource와 수집 Agent는 Daily Runtime에 둘 수 있다.

### Foundation에 둘 대상

- 기존 CloudTrail CloudWatch·S3 보존 계층
- Edge·Network 로그를 위한 S3 Prefix 또는 전용 Bucket
- 장기 실행 Compute가 필요 없는 CloudWatch Log Group
- 30일 Lifecycle·Retention
- 필요한 최소 IAM Policy
- Evidence 조회에 필요한 Output

Foundation Resource가 일반 `daily-down.ps1`의 Destroy Plan에 포함되면 실패로 처리한다.

### Daily Runtime에서 활성화할 로그

우선순위대로 구현한다.

1. CloudFront Standard Access Log
2. WAF Web ACL Log
3. ALB Access Log
4. EKS `api`, `audit`, `authenticator`
5. DVWA Container stdout/stderr
6. BANK Application 구조화 Audit Log
7. VPC Flow Log의 `REJECT` Traffic

비용 통제 원칙:

- 보존 기간은 기본 30일
- Application Log는 DVWA Namespace만 수집
- VPC Flow Logs는 우선 `REJECT`만 수집
- WAF는 필요한 필드와 규칙을 중심으로 필터링
- Cookie, Authorization Header, Password, Session ID와 불필요한 Request Body를 저장하지 않음
- EKS의 모든 System Log나 전체 Container Insights를 무조건 활성화하지 않음
- Loki, OpenSearch, Security Lake, 완전한 SIEM은 현재 필수 범위에서 제외
- Edge·Network 대량 로그는 S3와 Athena를 우선 검토
- 즉시 조회가 필요한 EKS Audit·Application·WAF 로그는 CloudWatch Logs를 우선 검토
- 현재 AWS Provider Version과 공식 문서에서 실제 지원되는 전달 방식을 확인한 뒤 구현

WAF는 최초에 `COUNT`와 Logging으로 관찰하고, 검증 증거 없이 전체 차단 모드로 전환하지 않는다.

## Phase 3 — BANK Application Audit Log 구현

Apache Access Log만으로는 “은행 업무에서 무엇이 일어났는가”를 설명하기 부족하다.

BANK Application에서 다음과 같은 보안 의미 Event를 구조화 JSON으로 기록한다.

- 로그인 성공·실패
- 회원가입 성공·실패
- 계좌 또는 중요 정보 조회
- 이체 요청·성공·실패
- 관리자 기능 사용
- Security Level 변경
- 접근 거부
- 입력 검증 실패
- 중요한 설정 변경

최소 필드:

```json
{
  "timestamp": "UTC ISO-8601",
  "event_type": "auth.login.failed",
  "result": "denied",
  "user_id": "pseudonymous-id",
  "source_ip": "validated-client-ip",
  "route": "/login.php",
  "request_id": "correlation-id"
}
```

금지 항목:

- Password와 Password Hash
- Cookie·Session ID
- Authorization Header
- DB Credential
- 실제 Access Key·Token
- 전체 개인정보
- 길이 제한 없는 사용자 입력·Request Body

사용자 입력을 그대로 로그 문자열에 결합하지 말고 JSON Encoding, 길이 제한, 개행 제거 등으로 Log Injection을 방지한다.

팀원이 수정한 BANK 기능과 기존 DVWA 동작을 보존하고, 관련 변경 전체를 덮어쓰거나 Upstream으로 임의 초기화하지 않는다.

## Phase 4 — 확장 가능한 Evidence Collector

현재 Daily Script를 거대한 단일 Script로 만들지 않는다.

Evidence Source를 선언형 Configuration으로 관리하고, Collector Type별 Handler를 분리한다.

최소 Collector Type:

- `S3Prefix`
  - CloudTrail
  - CloudFront
  - ALB
  - VPC Flow
- `CloudWatchLogs`
  - EKS Audit/API/Authenticator
  - WAF
  - DVWA Access·Application Audit

각 Source는 최소한 다음을 정의한다.

```text
Name
Type
Region
Source
Time Window
Output Format
Required/Optional
Redaction Rule
```

Evidence Bundle 구조:

```text
evidence/<experiment-id>/
├─ manifest.json
├─ source/
├─ queries/
├─ results/
├─ screenshots/
├─ sanitized/
└─ SHA256SUMS.txt
```

Bundle Manifest에는 다음을 기록한다.

- Experiment ID
- UTC/KST 시작·종료 시각
- AWS Account와 Region
- Git Commit과 Image SHA
- Argo Revision
- Scenario ID
- 수집 Source와 Query
- 누락 또는 실패 Source
- 파일별 SHA-256

`daily-down.ps1`과 연결하되 다음 모드를 구분한다.

- 일반 Daily Down:
  - Evidence 수집 실패를 경고하고 결과에 기록
- 보안 실험 종료:
  - `-RequireEvidence`와 같은 Strict Mode
  - 필수 Source가 누락되면 실험 완료로 판정하지 않음

Evidence 수집 실패 때문에 비용 Resource가 무한히 살아 있거나 Script가 끝없이 재시도하지 않도록 Bounded Retry와 명확한 복구 지점을 둔다.

## Phase 5 — Query·탐지·알림

CloudWatch Logs Insights와 Athena를 사용하여 재사용 가능한 Query Pack을 만든다.

최소 Query 후보:

- 동일 Source IP의 반복 로그인 실패
- WAF Rule Match와 Application 응답의 시간 상관관계
- 4xx·5xx 급증과 ALB Target 응답
- 특정 Source IP의 CloudFront → ALB → DVWA 요청 추적
- `kubectl exec`와 Secret 접근·거부
- Security Group·IAM·EKS 설정 변경
- 동일 Request ID의 Access Log와 Application Audit 연결

각 Query는 다음을 갖는다.

```text
목적
대상 Log Group 또는 S3 Table
실행 Query
정상 예상 결과
공격 예상 결과
False Positive 가능성
검증된 Runtime
```

Metric Filter·Alarm·SNS는 실제 시나리오와 연결되는 최소 항목만 추가한다. 단순히 로그가 존재한다는 이유로 경보를 대량 생성하지 않는다.

자동 조치는 다음 순서로 단계화한다.

1. 기록
2. 탐지
3. 알림
4. 사람 승인
5. 제한된 자동 조치
6. 동일 조건 재검증

자동 차단이 실험 증거를 없애거나 운영 복구를 방해하지 않도록 초기에는 사람 승인 경계를 유지한다.

## Phase 6 — 통제된 보안 실험

실제 공격 실행은 사용자 소유의 격리된 프로젝트 환경만 대상으로 한다.

각 시나리오는 다음 순서로 실행한다.

```text
정상 Baseline
→ 조치 전 공격·이상행위
→ 차단·통과 결과 확인
→ 관련 로그 수집
→ 탐지 Query 실행
→ 원인 분석
→ 최소 조치
→ 같은 입력·조건으로 재실행
→ 결과 차이 확인
→ Evidence Bundle 생성
```

외부 서비스, 팀원이 허가하지 않은 계정, 불특정 Internet 대상에는 공격을 수행하지 않는다.

공격 성공만을 프로젝트 성공으로 보지 않는다.

- WAF가 차단했다면 어떤 Rule이 왜 작동했는지 증명
- Application까지 도달했다면 Edge·ALB·Application Log를 연결
- 탐지되지 않았다면 어떤 Log Source 또는 Rule이 부족했는지 기록
- 조치 후 같은 조건으로 결과가 달라져야 함

## Phase 7 — Daily Lifecycle 회귀 검증

Observability 변경 후 다음을 검증한다.

1. Daily Session Watchdog 등록
2. `daily-up.ps1`로 Runtime 생성
3. Log Collector와 Application 자동 복원
4. 정상 요청 및 Test Event 생성
5. 각 Destination에 Log 도착
6. Evidence Bundle 생성
7. 조기 완료 또는 Deadline의 `daily-down.ps1` 실행
8. Daily Runtime 제거
9. Foundation Log와 로컬 Bundle 보존
10. Watchdog 예약 작업 제거
11. 다음 Up에서 Collector 재생성
12. 기존 CI/CD·GitOps 배포가 계속 작동

장시간이 걸리는 완전한 Down→Up Cycle은 예상 시간·비용과 현재 Runtime 상태를 먼저 보고한다. 정적 검증만 통과한 상태를 Cold Start 성공으로 표시하지 않는다.

## Phase 8 — 멘토·보고서용 산출물

다음 산출물을 만든다.

- 현재 As-built Architecture
- 정상 요청 흐름도
- CI/CD·GitOps 흐름도
- Log Source → 저장 → Query → 탐지 → 대응 흐름도
- 시나리오별 조치 전·후 비교표
- `행위 → 차단 → 로그 → 탐지 → 알림 → 조치 → 재검증` Matrix
- 중요한 시행착오와 복구 Timeline
- Evidence Bundle 목록과 Hash
- 아직 미검증인 항목
- 멘토에게 물어볼 결정 질문
- Daily Session 시작·Soft Deadline·Hard Deadline·Down 결과

Raw Log 전체를 Vault나 Git에 복사하지 않는다.

- 원본 Evidence: 사용자 로컬 Evidence Directory
- 보고서·Vault: 민감정보를 제거한 표, Query 결과, Screenshot, 해석
- Git: Source, Query, Rule, 비민감 설정만 보관

실제 작업·명령·오류·보안 발견은 다음에 민감값 없이 간결하게 기록한다.

`20_팀 프로젝트/3차 프로젝트/RAW_메모.md`

Phase 종료 시에는 일일 로그로 이관한다. MOC Routing 변경이 필요하면 작업 도중 여러 번 요청하지 말고 Phase 종료 시 Vault Manager에 한 번만 검토 요청한다.

## 변경·승인 경계

다음은 승인 없이 진행할 수 있다.

- 읽기 전용 Baseline 조사
- Source·Diff 검토
- Local Code 수정
- 정적 검증과 Test
- Query·문서·Evidence Collector 작성
- 기존 DVWA Repository의 검증된 변경 Commit·Push
- 민감정보가 없는 RAW 기록
- Watchdog Source와 Test 작성

다음은 실행 전 정확한 Target과 영향을 보고하고 사용자 승인을 받는다.

- Terraform Apply·Destroy
- Daily Session 시작
- GitHub Repository Settings 변경
- 비용이 지속되는 AWS Service 추가
- WAF의 실제 차단 모드 전환
- 통제된 공격·Misconfiguration 실행
- 운영 Data 삭제
- 여러 팀원 작업을 바꾸는 구조 변경

사용자가 자리를 비운 동안 승인이 없으면 해당 Gate에서 멈춘다. 같은 실패를 무한 재시도하거나 다른 변경으로 우회하지 않는다.

승인된 Daily Session의 안전 Down은 다시 묻지 않는다.

## Git·Secret 안전

- 기존 사용자·팀원 변경을 보존한다.
- Backup ZIP이나 과거 보관본을 현재 Source 위에 통째로 덮어쓰지 않는다.
- Terraform Folder를 임의로 새 Git Repository에 연결하지 않는다.
- `.terraform`, State, Plan, Credential, Private Key, kubeconfig를 Git·Vault·Evidence에 넣지 않는다.
- Force Push와 History Rewrite를 하지 않는다.
- Commit 전 Targeted Diff와 Secret Scan을 수행한다.
- 개인 Account 검증을 팀 Account와 다른 노트북 이식 완료로 과장하지 않는다.
- Account·Region·Role·Hosted Zone·Key Pair·OIDC Subject의 외부 입력을 분리한다.

## 검증

변경 유형에 맞게 최소한 다음을 수행한다.

- Terraform `fmt -check`, `validate`, 저장된 Plan 검토
- Foundation Resource의 Daily Destroy 포함 여부 검사
- PowerShell Parser와 Automation Test
- Watchdog 등록·취소·Deadline·Lock Test
- Shell `bash -n`
- Helm `lint`, `template`
- Kubernetes Manifest Dry Run
- GitHub Workflow YAML 검사
- Application Lint·Test·Docker Build
- Log Redaction Test
- Log Injection Test
- Collector Time Window·Retry·Partial Failure Test
- Evidence Manifest·SHA-256 Self-test
- `git diff --check`
- Secret Scan

Static Test와 실제 Runtime 검증을 구분해서 보고한다.

## 완료 판정

다음을 모두 충족해야 Goal을 완료로 표시한다.

1. BANK DVWA의 기존 CI/CD·GitOps 배포가 회귀하지 않았다.
2. CloudFront·WAF·ALB·EKS·Application·CloudTrail 중 시나리오에 필요한 Log Source가 실제 Destination에 도착한다.
3. Application에서 보안 의미 Event가 구조화되고 Secret이 기록되지 않는다.
4. 정상 사용자 요청 하나를 Edge부터 Application까지 추적할 수 있다.
5. 대표 보안 시나리오 최소 2개가 조치 전 상태로 수행됐다.
6. 각 시나리오에서 차단·통과 지점과 관련 로그를 설명할 수 있다.
7. 조치 후 동일 조건 재실행에서 결과 차이를 증명했다.
8. 재사용 가능한 Query Pack과 최소 탐지 규칙이 존재한다.
9. 각 실험에 Local Evidence Bundle과 SHA-256 Manifest가 생성된다.
10. Daily Destroy 뒤에도 30일 AWS 로그와 선택한 Local Evidence가 보존된다.
11. 다음 Daily Up에서 수집기와 Application이 자동 복원된다.
12. 비용·미구현·미검증·False Positive를 숨기지 않았다.
13. 멘토가 방향·범위·증거를 비교 평가할 수 있는 보고서 초안이 있다.
14. 개인 Account 검증과 팀 Account 이식 가능성을 분리해 표현했다.

추가로 다음 안전 조건도 충족해야 한다.

1. Daily Up 시작 시 독립 Watchdog이 등록된다.
2. 조기 Daily Down 시 Watchdog이 제거된다.
3. Soft Deadline 뒤 새로운 변경이나 공격을 시작하지 않는다.
4. Hard Deadline에 Evidence와 Down 절차가 실행된다.
5. Foundation이 Destroy Plan에 포함되면 Down을 중단한다.
6. Terraform Process·Lock 상태에서 동시 Destroy하지 않는다.
7. 재시도는 제한적이며 무한히 반복하지 않는다.
8. Down 성공 후 Daily State와 실제 과금 Runtime이 비어 있다.
9. Foundation Log와 Local Evidence가 보존된다.
10. Down 실패를 성공으로 보고하지 않고 잔존 Resource와 원인을 남긴다.

Goal 완료 여부와 Daily Runtime 종료 여부는 분리한다. Goal이 미완성이어도 Session Deadline에는 Runtime을 내린다.

코드와 정적 설계만 완성한 상태, 로그가 생성되지만 조회하지 않은 상태, 공격을 한 번 성공시킨 상태, 보고서 문장만 작성한 상태는 완료가 아니다.

## 작업 방식과 토큰 절약

- 최초 Baseline 뒤에는 변경된 파일과 해당 Runtime만 다시 확인한다.
- 같은 Repository·공식 문서·AWS 상태를 반복해서 전체 스캔하지 않는다.
- Sub-agent는 사용자가 명시적으로 요청한 경우에만 사용한다.
- 중간 보고는 Phase 완료, 사용자 승인 필요, 실제 실패 발생 때만 짧게 한다.
- 긴 조사 결과와 실행 증거는 파일에 저장하고 대화에 반복 복사하지 않는다.
- Apply·Destroy 대기 중 같은 상태를 계속 출력하지 않는다.
- 사용자 입력이 필요한 Gate에서는 안전하게 멈추며 Goal을 계속 Active 상태로 두고 무한히 다른 일을 찾지 않는다.
- Soft Deadline 이후 다른 일을 찾지 않는다.
- Hard Deadline 이후 Goal 작업보다 Down을 우선한다.
- 완료 조건이 충족되지 않았으면 예산이나 시간 때문에 Goal을 완료로 표시하지 않는다.

## 첫 번째 안전 작업

현재 Daily Runtime이 Down인 상태에서 AWS 변경 없이 다음을 먼저 수행한다.

1. canonical Goal 문서에 Daily Session Timebox 규칙 반영
2. 현재 Daily Script 구조와 충돌 여부 확인
3. 독립 Watchdog과 비민감 Session 상태 설계
4. Watchdog Source 구현
5. PowerShell Parser·등록·취소·Deadline·Lock Test
6. 기존 Daily Automation Test
7. Foundation이 Daily Destroy와 분리됐는지 정적 재검증
8. 변경 파일·Test 결과·남은 Runtime 위험 보고

이 안전장치의 정적 검증이 끝나기 전에는 새 Daily Up을 실행하지 않는다. 검증 뒤 사용자가 정확한 Target·시나리오·요청량·비용 영향을 확인하고 Daily Session을 승인하면 승인된 범위 안에서 Observability 실험을 진행한다.
