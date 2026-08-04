# RAW 메모

<!-- 2026-08-03 11:14까지 일일 로그 반영 완료 -->

### 11:33

- 후순위: Daily 자동화 Script를 손으로 실행하고 Code를 읽으며 동작 원리를 이해한다.
- Application: 은행 Application을 겉에 만들고 DVWA의 취약점 Engine을 내부 부품으로 재조립해 은행다운 화면과 흐름을 구현한다.
- 관측성 문제: Log 수집은 작동하지만 사람이 실시간으로 읽고 해석하는 과정이 어렵다. 보기·검색·판정 방식을 보완해야 한다.

### 19:15

- Phase 0: Daily State 317개와 Foundation State 27개를 확인했다. 현재 Primary·DR EKS/RDS/NAT, 양쪽 Valkey·EFS가 실행 중인 `full` 상태다.
- 수명주기: 기존 Public Hosted Zone은 존재하지만 Global ACM Certificate와 GuardDuty Detector는 없으며, Domain·ACM은 현재 Daily State에도 없다.
- 관제 Review: Windows PowerShell 5.1이 UTF-8 BOM 없는 한글 Module을 해석하지 못한 Parser 오류를 BOM 보정으로 해결했다. 관련 정적 Test 6개와 Secret 서명 검사 통과.
- Git: 관제 시간창 Review 작업을 `5c14d1b`로 Commit하고 `origin/main`에 Push했다.
- Daily Down: 사용자 승인 `DESTROY DAILY`로 Full Runtime 제거를 시작했으며 진행 중이다.

### 19:48

- Daily Down 완료: 250개 제거, Daily State 0, 추적·Tag 기준 Daily 잔존 0. Foundation ECR·OIDC/IAM·보안 로그 보존 계층과 30일 Retention은 유지됐다.
- Evidence: Post-Destroy Bundle에서 CloudTrail 59개, CloudFront 1개, ALB 1개, VPC REJECT 21개, EKS 42,297개, DVWA 628개 Event를 수집했다. WAF·DR Application은 해당 시간창 0건으로 기록됐다.
- 정적 구현: `minimal / dr-test / full` Runtime Profile, Valkey·EFS Opt-in, HTTPS Redirect 안전 기본값과 HTTP 실험 Toggle, Watchdog On/Off를 추가했다.
- 수명주기: 기존 Route 53 Hosted Zone은 Foundation에서 조회하고 CloudFront ACM·DNS 검증을 Foundation이 소유하도록 분리했다. Foundation v2 출력이 없으면 Daily Up이 중단되도록 보강했다.
- 검증: `minimal` Plan 117개 생성에서 DR·Valkey·EFS·복제 0건, `dr-test` Plan 232개 생성에서 Valkey·EFS 0건을 확인했다. Foundation `unoh.click` Plan은 ACM·검증 Record 3개 생성, 변경·삭제 0이며 아직 Apply하지 않았다.
- 회귀 검사: Daily/Foundation `terraform validate`, Runtime·Watchdog·Daily 자동화·관측성 관련 Test와 `git diff --check`를 통과했다.

### 20:06

- 독립 검토: Terra Max 검토자 2명이 Terraform 수명주기와 PowerShell Wrapper를 분리 검토했고 각각 `보정 후 승인`, `승인`으로 판정했다.
- 추가 보정: Foundation 선택 Output을 빈 문자열로 보존해 계약 Key가 누락되지 않게 했고, `setup-foundation.ps1`의 Domain 입력을 필수화해 인자 누락으로 인증서 제거 Plan이 생기는 경로를 차단했다.
- 이식 경계: `count` 주소 전환은 현재 Daily State 0에서만 안전하다고 Runbook에 명시했다. PowerShell Parser 9/9, 핵심 Test 3종, Diff와 신규 파일 Secret 서명 검사를 통과했다.
- 다음 Gate: AWS 변경은 추가하지 않았다. Foundation v2·`unoh.click` Plan을 먼저 승인·Apply한 뒤에만 `minimal` Cold Start Preview와 Runtime 검증으로 진행한다.

### 20:28

- Foundation v2 Apply: 승인된 Plan의 ACM 인증서·Route 53 검증 Record·인증서 검증 3개만 생성했다. 변경·삭제는 0이며 GitHub 후속 설정은 실행하지 않았다.
- Foundation 검증: contract version 2, `unoh.click`, Route 53 Zone ID와 ACM ARN Output을 확인했다. `us-east-1` ACM은 `ISSUED`, 일치하는 Public Hosted Zone은 1개다.
- Minimal Gate: 직접 Terraform Plan 결과 `122 create / 0 change / 0 delete / 0 replace`. Foundation·DR·Valkey·EFS Action은 0이다.
- 비용형 구성: Primary RDS Single-AZ, EKS Node Group `min=1 / desired=1 / max=2`; CloudFront는 `unoh.click`과 Foundation ACM을 사용하고 HTTPS Redirect는 유지한다. Daily State는 0이며 실제 Daily Apply는 아직 하지 않았다.

### 21:21

- Minimal Cold Start: 백그라운드 실행 2회는 PowerShell Module 환경 문제로 Terraform 전에 종료됐고 AWS Resource는 생성되지 않았다. Config Loader와 재현 Test를 보강해 `b1a1d6e`로 Push했다.
- Foreground `daily-up.ps1`: 17분 만에 `122 added / 0 changed / 0 destroyed`. DB·Secret·Argo Bootstrap까지 완료해 `https://unoh.click`에서 BANK DVWA가 동작했다.
- 최소 Runtime: DR·Valkey·EFS는 0. Managed Node 1대에 Application용 Karpenter Node 1대가 추가되어 실제 안정 실행은 Node 2대였다.
- 검증: Argo CD `Synced / Healthy`, DVWA Pod `Running 1/1`, immutable Image SHA 사용, Fluent Bit `2/2`, 최근 DVWA 18건·EKS 20건을 확인했다.
- WAF: 정상 요청은 현재 Filter가 `BLOCK`·`COUNT`만 보존하므로 0건이 정상이다. Logging Destination·Cookie/Authorization Redaction·30일 Retention을 확인했으며 실제 Rule Match Event는 아직 미검증이다.

### 07:18

- Watchdog: 02:57 KST Daily Down을 시작했지만 약 2시간 8분 뒤 `exit code 1`로 종료됐다. EKS·RDS·NAT·Load Balancer는 제거됐으나 Karpenter `t3a.small` Node 1대와 VPC·Subnet·Security Group State 3개가 남았다.
- 원인: Karpenter가 Runtime에 만든 NodeClaim·EC2는 Terraform State 밖에 있다. Destroy 전에 NodePool·NodeClaim을 종료하는 단계가 없어 EKS와 Karpenter Controller가 먼저 사라졌고, 고아 EC2가 Network 의존성 삭제를 막았다.
- Watchdog 한계: 단일 실패 Destroy가 2시간 Retry Window를 소진했고 상세 stdout/stderr를 보존하지 않아 다음 날에는 Exit Code만 남았다.
- 복구: 승인 후 고아 Instance `i-0aabd261ead9ef563`를 종료하고 `daily-down.ps1 -ConfirmDestroy 'DESTROY DAILY'`를 재실행했다. 4.1분 만에 잔여 3개를 제거했다.
- 최종 검증: Daily State·EKS·RDS·EC2·NAT·ELBv2 모두 0. Foundation ECR·GitHub OIDC/IAM·Security Log와 30일 Retention은 보존됐다.

### 08:43

- Daily Down 보정: Terraform Destroy 전에 Primary·DR Karpenter NodePool·NodeClaim을 삭제하고 관련 EC2가 완전히 종료될 때까지 제한 시간만 대기하도록 구현했다.
- 고아 복구 경계: Cluster가 이미 없을 때는 `Project`, Cluster ownership, `karpenter.sh/*`, `ManagedBy=Karpenter` Tag가 모두 일치하는 EC2만 승인된 `DESTROY DAILY` 범위에서 종료한다.
- Watchdog 진단: Down 시도별 Sanitized stdout/stderr, 남은 Terraform State와 Tag 기반 AWS Runtime을 로컬 Log에 보존하고, Retry 만료 뒤에는 자동 재시도를 종료하도록 보강했다.
- 정적 검증: PowerShell Parser, Karpenter·Watchdog·Daily Automation·Runtime Profile Test, Terraform fmt/validate, Helm lint/template, Diff·Secret Scan을 통과했다. AWS Apply·Destroy는 실행하지 않았다.

### 09:33

- T1 정적 구현: 승인된 Session에서만 CloudFront HTTP를 임시 허용하고 `finally`에서 HTTPS Redirect를 복원하는 Scenario, WAF·Application Query, CloudFront `cs-protocol` Athena 조회를 추가했다.
- 안전 경계: 대상 URL은 Terraform `application_url`로 고정하고, Saved Plan이 `aws_cloudfront_distribution.this` 1개 Update 외의 변경을 포함하면 중단한다. HTTP Probe는 Body를 읽지 않고 Status·Path·CloudFront Request ID만 기록한다.
- 검증: PowerShell Parser, Scenario·Athena·Daily Automation·Runtime Profile Test, Terraform fmt/validate, Diff·추가 줄 Secret Scan을 통과했다. Query metadata와 Test 정규식 결함 2건은 보정했다.
- 상태: T1 Source는 `80dbd48`로 Push됐고 보정 4파일은 미커밋이다. AWS Apply·HTTP 허용·공격은 실행하지 않았으며 Karpenter와 T1 실제 Runtime 검증은 승인 Gate에 남아 있다.

### 10:33

- F2 정적 구현: Primary GuardDuty와 `GuardDuty Finding → EventBridge → CloudWatch Logs + SNS` 전달 경로, Finding 조사·Sample 검증 Script, Query·Test를 추가했다. 기본 탐지만 활성화하고 고비용 선택 기능은 명시적으로 비활성화했다.
- Plan 안전 검사: Domain 입력이 누락된 첫 Plan의 `14 create / 3 delete`를 적용 전 폐기했다. `unoh.click`을 보존한 Plan은 `14 create / 0 change / 0 delete`만 포함했다.
- Foundation Apply: 승인된 F2 Resource 14개만 생성했고 변경·삭제는 0이다. GuardDuty, EventBridge Rule, 원본 Finding 30일 Log Group, 기존 SNS 연결이 실제 AWS에서 존재함을 확인했다.
- Drift 보정: AWS가 반환한 `AI_PROTECTION`과 Runtime Agent 관리 3개를 Terraform이 명시적으로 `DISABLED`로 관리하게 보정했다. 후속 Plan은 `No changes`로 수렴했다.
- 검증: `terraform fmt -check`, `terraform validate`, F2 Offline·Detection Test, Diff·추가 줄 Secret Scan을 통과했고 `75c0874`, `fa8c179`로 Push했다. AWS Sample Finding 발생과 실제 SNS·Log 전달 검증은 아직 실행하지 않았다.
