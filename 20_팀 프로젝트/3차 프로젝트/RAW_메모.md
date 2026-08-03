# RAW 메모

<!-- 2026-07-30 21:14까지 일일 로그 반영 완료 -->

### 12:52

- 한 일: 관측성 Goal Phase 0 읽기 전용 기준점 확인. DVWA Git과 배포 Image SHA가 일치하고 Argo CD `Synced / Healthy`, Pod `Ready` 상태를 확인.
- 활성 로그: CloudTrail Management Event는 Foundation의 CloudWatch·S3 7일 보존 구조, EKS는 `api/audit/authenticator` 활성. DVWA Apache Access Log는 Container stdout에만 존재.
- 미수집: WAF 없음, CloudFront·ALB·VPC Flow 중앙 로그 없음, DVWA Namespace Container Log 수집 Agent 없음, BANK 구조화 Audit Log 없음.
- 보안 발견: 공개 정상 요청에서도 Apache·PHP 상세 Version Header와 Session·Security Cookie가 발급됨. 실제 Cookie 값은 기록하지 않음.
- Evidence 경계: 현재 Collector는 `S3Prefix`만 지원하고 Redaction·Time Window·실험별 Strict Mode가 없음. 로컬 보관본은 CloudTrail 원본을 암호화 없이 동기화하므로 접근권한·민감 Metadata 취급 보강 필요.

### 14:15

- 한 일: 관측성 Goal Phase 2 정적 구현. Foundation 7일 S3·CloudWatch 목적지와 Daily의 CloudFront·WAF `COUNT`·ALB·VPC `REJECT`·EKS Control Plane·DVWA Namespace 로그 수집 Source를 구성.
- Application: BANK 보안 Event를 JSON으로 stderr에 기록하도록 로그인·회원가입·로그아웃·Security Level·접근 거부·CSRF 실패 Audit Log 추가. Password·Cookie·Session·Request Body는 제외.
- Evidence: `S3Prefix`·`CloudWatchLogs` Handler, UTC Time Window, Bounded Retry, Redaction, Query Metadata, `manifest.json`·`SHA256SUMS.txt`, Strict Mode를 추가하고 `daily-down.ps1`의 Destroy 전·후 수집과 연결.
- 시행착오: 공식 `aws-for-fluent-bit` Chart에서 `filter.additionalFilters`가 렌더링되지 않는 것을 발견해 `filter.extraFilters`로 보정하고 DVWA Namespace Filter가 실제 Manifest에 들어가는지 검증.
- 정적 검증: 양쪽 Terraform `fmt -check`·`validate`, PowerShell Parser·Self-test, `bash -n`, 공식 Fluent Bit Chart render, Helm lint/template, PHP lint·Audit self-test, Docker build, 대상 Workflow actionlint, 변경 파일 gitleaks 통과.
- 남음: AWS Runtime 전달·Query 결과는 미검증. Apply/Destroy 전 기존 EKS Log Group의 Daily→Foundation State 소유권 이전과 Foundation Plan 검토가 필요. 이번 단계에서 AWS·GitHub 변경과 Commit·Push는 수행하지 않음.

### 14:33

- 확인: Daily State가 `module.primary_eks.aws_cloudwatch_log_group.this[0]`을 소유하고 Foundation State에는 새 Observability Log Group·Delivery Destination이 아직 없음.
- 실행 Gate: 기존 `/aws/eks/aws-topology-primary/cluster`를 Foundation State에 Import한 뒤 Daily State의 기존 주소를 제거하고 Foundation Apply·Daily Plan을 순서대로 검증해야 함.
- 문제: 현재 AWS CLI Credential이 `UnrecognizedClientException`으로 만료되어 실제 Runtime 재조회와 Apply를 진행할 수 없음.
- 결정: 실행 중인 Terraform 작업 없음. State 변경·Foundation Apply는 사용자 승인과 AWS 인증 복구 전까지 중단.

### 14:53

- 한 일: 사용자 승인 후 양쪽 Local State를 민감 백업하고 기존 EKS Log Group을 Daily State에서 Foundation State로 이전.
- Foundation Apply: `3 added / 2 changed / 0 destroyed`. DVWA·WAF 7일 Log Group, CloudFront S3 Delivery Destination 생성, Security Log Bucket Policy 갱신, EKS Log Group 보존기간 `90 → 7`.
- 검증: 실제 EKS·DVWA·WAF Log Group 모두 7일, CloudFront Delivery Destination `S3`, Daily 소유 0·Foundation 소유 1, Foundation 재계획 `No changes`.
- Daily Plan: Observability Runtime `8 create / 6 update / 0 delete`. 기존 EKS Log Group 삭제 회귀 없음.
- 남음: Daily Apply는 별도 승인 전까지 미실행. CloudFront·WAF·ALB·VPC Flow·DVWA Log 전달은 아직 Runtime 미검증.

### 15:28

- 결정 반영: 보안 로그 보존기간을 30일로 변경하고 DR EKS에도 DVWA Namespace Fluent Bit·Pod Identity·Evidence Collector를 준비.
- Foundation Apply: `1 added / 5 changed / 0 destroyed`. DR DVWA Log Group 생성, CloudTrail·Primary EKS·Primary DVWA·WAF·S3 Lifecycle을 `7 → 30일`로 변경.
- 검증: Primary·DR·Global CloudWatch Log Group과 S3 Current/Noncurrent Version 모두 30일, Foundation 재계획 `No changes`.
- Daily Plan: `11 create / 6 update / 0 delete`. Primary·DR Log Forwarder, CloudFront·WAF·ALB·VPC Flow Log 배관 포함.
- 남음: Daily Apply는 별도 승인 전까지 미실행. 실제 Log 전달과 Query 결과는 미검증.

### 16:02

- Daily Apply: 승인된 `11 create / 6 update / 0 delete` Plan 중 16개 반영, `aws_cloudwatch_log_delivery.cloudfront_access[0]` 1개만 실패.
- 오류: `ValidationException: Provided field delimiter is not applicable for delivery destination's output format`.
- 원인·보정: Foundation Destination은 `JSON`인데 Daily Delivery에 `field_delimiter = "\t"`가 있어 충돌. 구분자를 제거하고 같은 조합의 재발을 막는 정적 계약 Test 추가.
- 검증: Terraform `fmt -check`·`validate`, Daily Automation Self-test 통과. 보정 후 Plan은 `1 create / 0 update / 0 delete`.
- 남음: 보정된 CloudFront Log Delivery의 두 번째 Apply와 실제 S3 Log 도착은 별도 승인 전까지 미실행.

### 16:36

- CloudFront Log Delivery 재Apply 성공. 정상 요청 뒤 Security Log Bucket에 실제 CloudFront Object 도착을 확인.
- Runtime: WAF Logging, ALB Access Log, VPC Flow `REJECT`, Primary·DR EKS Control Plane Log는 활성 상태. Primary DVWA CloudWatch Log는 Event 0건.
- 문제: Primary `aws-for-fluent-bit` DaemonSet은 `2 desired / 0 ready`, 두 Pod 모두 `CrashLoopBackOff`. 이전 Container Log에 `fluent-bit.conf:30: undefined value`가 기록됨.
- 원인·보정: Chart의 `filter.extraFilters`는 기존 Kubernetes Filter 내부 Option용인데 새 `[FILTER]` Block을 넣어 설정이 중첩됨. 전체 Filter Section용 최상위 `additionalFilters`로 Local Source와 회귀 Test를 수정.
- 검증: Terraform `fmt -check`·`validate`, Daily Automation Self-test 통과. 저장 Plan은 Primary·DR SSM Document와 Association만 `0 create / 4 update / 0 delete`.
- 남음: 위 4개 Update Apply와 Fluent Bit Ready·Primary/DR DVWA Log 실제 도착 검증은 별도 승인 대기.

### 17:09

- Apply: SSM Document·Association `0 added / 4 changed / 0 destroyed`. Primary·DR Association 모두 `Success`.
- Fluent Bit: Primary `2/2`, DR `1/1` DaemonSet Ready, 새 Pod 모두 `Running`, Restart 0.
- 실제 전달: Primary DVWA 정상 요청 뒤 CloudWatch Access Log 51건 확인. DR은 Application Workload가 없어 임시 Smoke Pod의 Marker 1건 도착을 확인한 뒤 Pod 삭제.
- Edge·Network: CloudFront 실제 Object 2개와 ALB 실제 Access Log 3개가 Security Log Bucket에 도착. VPC Flow `REJECT`·EKS Control Plane Log 활성 상태 유지.
- WAF: XSS 형태의 무해한 Probe가 `CrossSiteScripting_QUERYARGUMENTS`에 Match됐으나 COUNT Override로 최종 `ALLOW`; CloudWatch Event 1건 확인.
- Redaction: 가짜 Authorization·Cookie Header를 사용한 Probe에서 두 Header 값 모두 `REDACTED`로 저장됨을 값 노출 없이 확인.

### 17:50

- Application: 구조화 BANK 보안 Audit Log를 Commit `289c14e`로 Push하고 GitHub Actions→ECR→GitOps→Argo CD 배포를 완료. Runtime은 Argo `Synced / Healthy`, Pod `1/1`, immutable Image `sha-289c14e...`로 확인.
- Runtime 검증: 가짜 Credential을 사용한 로그인 실패에서 `auth.login.failed` JSON Event 도착을 확인. 결과·익명 사용자·Route·사유·Source IP·Request ID가 기록됐고 가짜 Password 값은 Log에서 0건.
- 정적 검증: 변경 PHP 전체 `php -l`, Audit self-test, Helm lint/template, Targeted gitleaks, `git diff --check` 통과.
- CI 시행착오: 외부 참고 URL의 `403/429`와 TLS Timeout을 문서 단절로 오판하던 Pytest를 보정. 임시 Python 환경에서 전체 `4 passed`; Commit `8a0099a`와 GitOps Bot Commit `3be7f3b`가 원격 `main`에 반영됨.
- 종료 경계: Destroy 직전 Runtime은 아직 이전 GitOps Revision `0d85591`과 Image `sha-289c14e...`였음. 최신 선언 `3be7f3b`는 다음 Daily Up에서 Argo CD가 재조정해야 함.
- 결정: 현재까지의 Source·Git·ECR Image·Foundation Log를 보존하고 Daily Runtime만 `daily-down.ps1`로 제거한다.

### 18:21

- Daily Down: Terraform Destroy 완료. Daily State `0`, Tagged Daily Runtime `0`으로 확인.
- Foundation 보존: State 24개, ECR `aws-topology/application`, Security Log Bucket과 30일 CloudWatch Log Group이 실제 API에서 존재함을 확인.
- Evidence: Local `daily-20260731T085159Z-6c0a6831-pre-destroy`·`post-destroy` Bundle 생성. SHA-256 대조는 각각 131개·129개 파일 모두 불일치 0.
- 시행착오: 삭제된 VPC Flow Log가 Resource Groups Tagging API에 잠시 남아 최초 종료 검사가 실패. EC2 `describe-flow-logs`는 실제 0건이어서 삭제 직후 Tagging 오탐으로 판정.
- 보정: `daily-common.ps1`에 VPC Flow Log 실재 API 검증과 회귀 계약 Test를 추가. PowerShell Parser·Daily Automation Self-test 통과 후 종료 검사를 재실행해 정상 완료.

### 23:12

- Goal 검토: 실제 Foundation 설정에 맞춰 AWS Log 보존 기준을 7일에서 30일로 정렬.
- Evidence 보정: Windows `cp949` 때문에 실패한 EKS Control Plane 수집을 UTF-8 고정으로 수정. 과거 시간창 재수집에서 EKS 759건, Bundle Hash 불일치 0 확인.
- 시나리오: `WEB-01 반복 로그인 실패 탐지·제한`, `IAM-01 EKS Pod Identity S3 권한 오용` 실행 계약 작성. 기존 IRSA 계획은 현재 Pod Identity Source에 맞게 보정.
- Query Pack: WAF Login Block, ALB Trace ID, Pod Identity·S3 Object Event Query와 정적 계약 Test 추가.
- Foundation Plan: CloudTrail 1개 `in-place update`, 추가·삭제 0. Management Event를 유지하고 프로젝트 Primary·DR S3의 Get·Put·Delete Data Event만 추가하도록 제한. Apply는 미실행.

### 23:57

- 정정: `WEB-01`·`IAM-01`은 우리 조가 확정한 공격·실습 프로젝트가 아니라 로그·Query·Evidence Pipeline을 점검하기 위한 관측 검증 후보다.
- 보정: S3 Data Event는 팀 결정 전에 비용 설정을 강제하지 않도록 Foundation의 기본 비활성 선택 기능으로 변경. Apply는 미실행.

### 00:30

- 상태: Daily State 0, Primary·DR EKS 0, Foundation State 24로 Down 상태와 보존 계층을 재확인.
- Runtime 증거: 보존된 DVWA CloudWatch Log에서 구조화 `auth.login.failed` Event와 배포 Image를 확인.
- 시행착오: 실제 Logs Insights Query 3개가 결과 0건을 PowerShell `$null`로 처리해 `Count` 오류로 실패.
- 보정·재검증: 결과를 강제 배열화하고 zero-row 회귀 Test 추가. 같은 10분 구간에서 DVWA 181건 수집, Query 3개 모두 성공·0행, Bundle SHA-256 불일치 0. AWS 변경 없음.

### 00:42

- IAM Query Runtime: EKS `pods/exec`·Secret 접근 후보 Query는 44행 성공. Pod Identity·S3 Query는 `strcontains(requestParameters.key, ...)`가 CWLI Compile 오류.
- 보정·재검증: 실제 Compiler에서 확인된 `requestParameters.key like /web\/experiment-/`로 교체. 두 Query가 각각 44행·0행으로 성공했고 Query-only Bundle SHA-256 불일치 0.
- 경계: 44행은 공격 증거가 아니라 Bootstrap·운영 활동이 섞인 검토 후보이며 Actor·Event 분류는 미완료. AWS 변경 없음.

### 00:45

- IAM Query 44행 분류: 전부 `secrets` status 200이며 `watch` 43·`list` 1, Actor는 Argo CD ServiceAccount와 Kubernetes System 구성요소. `pods/exec`는 0건.
- 판정: 공격 흔적이 아니라 Controller의 정상 Secret 감시 Baseline. 향후 탐지에서는 정상 Actor·Verb 기준선과 비정상 `exec`·거부·예상 밖 Secret 접근을 분리해야 함.

### 03:13

- Goal 재개 Preflight: AWS Account `433048100798`, Daily State 0, Foundation State 24 확인. Primary·DR의 EKS·EC2·RDS·Load Balancer는 모두 0.
- `daily-up.ps1` Plan-only 실행: `256 create / 0 update / 0 destroy / 0 replace`, Foundation 금지 자원 검사 통과.
- 결과: 저장 Plan 생성 뒤 승인 문구가 없어 Apply 직전에 정상 중단. AWS 변경 없음.
- 다음 Gate: Daily Up과 관측 Pipeline Smoke Test는 `APPLY DAILY` 명시 승인 필요.

### 04:48

- Daily Up: 승인된 `daily-up.ps1 -ConfirmApply 'APPLY DAILY'`로 Daily Runtime 256개 생성. Primary·DR EKS/RDS, DB Bootstrap, Argo CD `Synced / Healthy`, DVWA Pod Ready와 immutable Image `sha-8a0099aa...`를 확인했으며 총 32.9분 소요.
- 로그 전달: 최근 시간창에서 CloudTrail 193개, CloudFront 4개, ALB 3개, VPC REJECT 23개 S3 Object를 확인. Fresh Marker는 DVWA Container와 `/aws/eks/aws-topology-primary/dvwa`에 1건씩 도착함.
- WAF 경계: 정상 Marker는 WAF Log 0건. 현행 Filter가 `COUNT`·`BLOCK`만 보존하고 정상 `ALLOW`는 버리는 비용 통제 설계이므로 전달 실패가 아닌 예상 결과로 판정.
- Evidence: `observability-cold-up-smoke-20260802` Bundle에서 CloudFront 3·ALB 3·VPC 13·EKS Control Plane 21,453·DVWA 435건 수집, WEB Query 3개 성공·0행, 파일 69개 SHA-256 불일치 0. 정상 Baseline이며 공격 증거로 해석하지 않음.
- 자동화 보정: 새 Bastion 생성 뒤 로컬 `bas` Alias가 과거 IP를 유지하는 결함을 확인. Daily Up이 정확한 `Host bas` Block만 갱신하도록 구현·회귀 Test를 통과했고 실제 Alias로 EKS 2 Node·DVWA Ready를 재확인. Evidence Manifest도 Live Argo Revision을 수집하도록 보정해 `MissingContext` 0을 확인.
- 남은 관찰: ALB/Kubernetes Health Check가 `/`에 반복 접근하며 `authorization.access.denied` Audit Event를 다량 생성해 탐지 Noise 후보로 기록. 의미 변경은 보류하며, 09:00 KST에는 승인된 Daily Down으로 과금 Runtime을 제거할 예정.

### 05:02

- 보존 Runtime 검증: CloudTrail·Primary/DR DVWA·EKS·WAF CloudWatch Log Group 모두 30일, Security Log S3의 Current·Noncurrent Object Lifecycle도 30일로 AWS API에서 확인.
- DR 검증: Tokyo Bastion을 통한 읽기 전용 확인에서 DR Node 1개 `Ready`, Fluent Bit DaemonSet `1/1 Ready`. DR DVWA Log 0건은 수집기 실패가 아니라 Application Event 미발생 경계로 유지.
- 정상 요청 추적: `19:28:12Z GET /login.php`를 CloudFront `200` → ALB·Target `200` → DVWA `200`으로 UTC 시각·Method·Path를 이용해 연결. Query String은 Sanitizer가 제거했고 WAF 정상 `ALLOW`는 저장 Filter 대상이 아님.
- Evidence 안전성: Sanitized Bundle에서 실제 AWS Access Key·Authorization·Cookie·Credential Query Pattern 0건. `관측성_As-built_및_Runtime_검증.md`에 As-built·Log Source 표·Goal 진행 경계를 기록하고 frontmatter 5파일 0/0, `git diff --check` 통과.
- Noise 보정 Source: ALB Health Check 기본 경로를 인증 필요 `/`에서 비인증 `/login.php`로 변경. Terraform `fmt/validate`와 Daily Self-test 통과, 일반 Plan은 Primary·DR Target Group 2개 `update`만 표시. Apply와 Runtime Noise 감소 확인은 미실행.
- Down 사전 Gate: Plan-only에서 `0 create / 0 update / 256 destroy`, Foundation 보존 검사 통과, AWS 변경 없음. 임시 Plan은 삭제했으며 09:00에는 Fresh Plan으로 Daily Down을 실행한다.

### 05:15

- Query Metadata 회귀 Test가 Windows PowerShell 5.1에서만 실패하는 현상을 확인. UTF-8 BOM 없는 Query 파일을 기본 ANSI Code Page로 읽어 한글 주석과 줄 경계가 깨진 것이 원인이었다.
- 보정: Metadata Test의 파일 읽기를 .NET UTF-8 Reader로 통일. 실제 Evidence Query Loader는 이미 `-Encoding UTF8`을 사용함을 확인했다.
- 재검증: Daily Automation Self-test가 Windows PowerShell 5.1과 PowerShell 7에서 모두 통과. AWS 변경 없음.
- 09:00 KST 1회성 Heartbeat가 `ACTIVE`이며, Evidence 수집 → Foundation 보호 검사 → `daily-down.ps1` → Daily 과금 Runtime 잔존 검증 순으로 실행되도록 등록 상태를 확인했다.

### 05:29

- Athena Query 정적 결함: ALB 공식 Schema는 `client_ip`와 숫자형 `client_port`를 분리하지만 기존 Query 2개가 `client_port`를 IP 문자열처럼 분해하고 있었다. `client_ip` 사용과 Target Status 안전한 정수 변환으로 보정했다.
- Athena 준비: 현재 Foundation Prefix용 CloudFront JSON·ALB Regex·VPC 14-Field External Table DDL과 AWS를 호출하지 않는 Local Renderer를 추가. 실제 Sanitized Sample에서 CloudFront 8/8 Field, ALB Regex Match, VPC 14 Field를 확인했으나 Athena Catalog 실행은 미승인·미검증이다.
- 시행착오: Renderer Test가 기존에 없는 Test 변수와 PowerShell Strict Mode의 빈 Pipeline `Count` 차이로 2회 실패. 기존 `$root`, 고유 Temp 파일, 강제 배열화를 사용해 보정했다.
- 재검증: Daily Automation Self-test가 Windows PowerShell 5.1·PowerShell 7에서 모두 통과. AWS 변경 없음.
- 보고서 재료: `멘토 상담용 관측성 진행 보고 초안.md`에 실제 기반, Log 흐름, 후보 시나리오, 전후 Evidence Matrix, 시행착오, 미완료와 멘토 질문을 분리했다. BANK Audit Event의 구현 범위와 계좌·이체 기능 부재 경계도 As-built에 추가했다.

### 05:33

- Correlation 재검증: 기존 Sanitized Bundle의 BANK `authorization.access.denied`와 ALB Access Log에서 동일 `Root=...` Trace ID 2건을 확인. 각 Event의 Application·ALB 시각 차이는 1ms 미만이며 Path `/`, Application `denied`, ALB `302`가 일치했다.
- 판정 보정: ALB `trace_id` → BANK `request_id`의 직접 1:1 연결은 Runtime 확인으로 올림. CloudFront `x-edge-request-id`는 별도이므로 Edge 구간은 시각·Source IP·Method·Path를 함께 사용해야 한다.
- Athena Renderer 실제 입력 검증: Foundation Output과 현재 STS Account로 Temp DDL을 생성해 미치환 Placeholder 0, Database DDL 1개, External Table DDL 3개를 확인하고 Temp 파일을 삭제. Athena·Glue 실행과 AWS 변경은 하지 않았다.

### 05:35

- Goal의 14개 완료 조건을 현재 Runtime·Source·Bundle 증거와 1:1로 대조해 As-built에 감사 표로 고정.
- 확정 충족은 정상 요청 추적과 미구현·False Positive 공개이며, 멘토 보고서는 진행 초안 상태. 대표 시나리오 2개 실행·조치 후 재검증·Alarm·Down 후 보존·팀 Account 이식은 미충족 또는 부분 충족으로 유지.
- 경계: 관측 기반이 작동한다는 사실을 공격·대응 시나리오 완료로 확대하지 않았으며 Goal은 Active 상태를 유지한다.

### 09:31

- Daily Down 사전 확인: Account `433048100798`, Terraform Process·State Lock 없음, Daily State 323개·Foundation State 24개. Fresh Destroy Plan의 Foundation 보호 검사를 통과한 뒤 승인된 `daily-down.ps1 -ConfirmDestroy 'DESTROY DAILY'` 실행.
- 결과: `0 added / 0 changed / 256 destroyed`, 약 27.4분. Daily State 0, 추적 대상 Daily AWS 잔존 0, `Project=aws-topology` 태그 기반 Daily Runtime 잔존 0으로 종료.
- Evidence: `daily-20260802T000320Z-e37547dd-pre-destroy`와 `-post-destroy` Bundle 생성. 각각 105·104개 파일의 SHA-256 불일치 0. 사후 수집에서 CloudTrail 57·VPC REJECT 20·EKS Control Plane 41,545·DVWA 816건을 보존했으며 CloudFront·ALB·WAF·DR DVWA는 해당 사후 Window 0건.
- Foundation 재확인: State 24개, ECR Repository와 Image 24개, GitHub OIDC Provider·Actions IAM Role·Security Log S3가 실재. CloudTrail·Primary/DR DVWA·EKS·WAF Log Group과 S3 보존 설정은 30일 유지.

### 14:19

- Daily Session 안전장치 구현: 시작 후 5시간 Soft Deadline, 6시간 Hard Deadline, 이후 2시간·15분 간격의 제한 재시도와 독립 Windows Scheduled Task Watchdog을 `daily-up.ps1`·`daily-down.ps1`에 연결. AWS 변경 없음.
- 안전 경계: Terraform Process·State Lock이 있으면 Kill·강제 해제·동시 Destroy를 하지 않으며, 성공한 Down에서만 예약 작업과 활성 상태를 제거한다. 상태에는 비민감 Routing·Deadline·동작 상태만 기록한다.
- 시행착오: 첫 Watchdog Entry Point Probe에서 Windows PowerShell이 상위 PowerShell 7 Module Path를 물려받아 `Import-PowerShellDataFile`을 찾지 못했다. Scheduled Task가 등록 시점의 실제 PowerShell Executable을 고정하고 설정 cmdlet을 Module-qualified 호출하도록 보정했다.
- 재검증: PowerShell Parser 8파일, Watchdog 등록·조기 실행·해제·Deadline·Lock Test, 기존 Daily Automation Test, Windows PowerShell 5.1 설정 Import, Daily·Foundation `terraform validate`, Targeted Secret Scan 통과.
- 종료 상태: Terraform Process 0, State Lock 없음, Daily State 0, Foundation State 24, Watchdog Task 0, 활성 Session State 없음. 실제 Hard Deadline Down은 다음 승인된 Daily Session에서 Runtime 검증한다.

### 16:09

- Daily Session Baseline: `daily-up.ps1 -ConfirmApply 'APPLY DAILY'`로 `256 added / 0 changed / 0 destroyed`, 33.1분. Argo CD `Synced / Healthy`, DVWA Pod Ready, Image `sha-8a0099aa5fe8dda94ef15ac803bdd6ee73cfd413`, CloudFront 정상 요청 5건의 `302/200` 응답을 확인했다.
- 최종 Evidence `baseline-20260802-1527-final`: CloudTrail 13개 Object, CloudFront 1개, ALB 2개, VPC REJECT 6개, EKS Control Plane 11,336건, DVWA 129건 수집. Git Commit·Image SHA·Argo Revision을 동일 배포로 연결했다.
- WAF는 `BLOCK/COUNT KEEP`, `ALLOW DROP` Filter라 정상 요청 Window 0건이 예상 결과였으며 실제 WAF Event 전달은 아직 미검증이다. DR DVWA도 Workload 미배포로 0건이다.
- 시행착오: Evidence의 Argo Revision 조회가 새 Bastion Host Key를 비대화식으로 등록하지 못해 실패. `StrictHostKeyChecking=accept-new`를 추가해 실제 Revision 조회와 Automation Self-test를 통과했다.
- 종료: `daily-down.ps1 -ConfirmDestroy 'DESTROY DAILY'`로 25.2분에 256개 Daily Resource를 제거했다. 빈 CloudFront Log Object가 post-destroy Collector를 실패시키는 결함은 Empty String 저장 허용과 회귀 Test로 보정했고 재수집 성공. Daily State·잔존 Runtime·Terraform Process·Watchdog 0, Foundation State 24와 ECR·OIDC/IAM·Security Log 30일 보존을 확인했다.

### 16:43

- 한 일: `WEB-01` 전용 `/login.php` Rate-based WAF Rule을 `disabled/count/block`로 선언하고 기본값은 `disabled`로 고정. 요청 생성 Script는 현재 Terraform의 Application URL만 사용하며 `10~60`회와 정확한 승인 문구로 제한.
- 한 일: `IAM-01` Pod Identity S3 Canary Script와 비민감 Bucket·Data Event 상태 Output 추가. SHA-256 고정 Image, 단일 `web/experiment-<id>/canary.txt`, 임시 Pod·ServiceAccount·Object 정리를 강제.
- 검증: Daily·Foundation `terraform fmt -check`·`validate`, PowerShell Parser, 신규 Scenario 안전 계약 Test 통과. AWS Apply·공격·WAF 전환은 수행하지 않음.
- 남음: 다음 승인된 Daily Session에서 S3 Data Event Apply 여부와 immutable AWS CLI Image를 확정한 뒤 `WEB-01`·`IAM-01` 조치 전·후 Runtime을 실행·수집해야 함.

### 16:55

- Foundation S3 Data Event Plan: `aws_cloudtrail.security` 1개 in-place update, `0 add / 1 change / 0 destroy`. Management Event와 프로젝트 Primary·DR Bucket Prefix의 `GetObject`·`PutObject`·`DeleteObject`만 선택하며 임시 Plan은 검토 후 삭제.
- IAM-01 준비: `enable_web_s3_pod_identity` Toggle을 현재 동작과 같은 기본값 `true`로 추가. Canary의 `allowed/denied` 기대 결과가 실제 Terraform Output과 다르면 실행 전 중단하도록 보정.
- 검증: Daily Terraform `fmt -check`·`validate`, IAM-01 Parser와 Scenario 안전 계약 Test 통과. AWS Apply는 수행하지 않음.
- 남음: IAM-01 조치 후 Toggle을 `false`로 유지할지, 증거 수집 뒤 `true`로 복구할지 사용자 결정 필요.

### 19:35

- Foundation·Up: CloudTrail에 프로젝트 Primary·DR S3의 `GetObject`·`PutObject`·`DeleteObject` Data Event를 1개 in-place Update로 적용. Daily Up은 `256 added / 0 changed / 0 destroyed`, 32.2분이며 Argo `Synced / Healthy`, DVWA Ready·HTTP 200을 확인.
- WEB-01: `before/count/block`에서 로그인 실패 요청을 각 20회 실행했고 모두 HTTP 200. BANK Application은 단계별 20건을 정확히 기록했지만 WAF Match는 모두 0건이어서 관측은 성공, Rate 제한·차단 효과는 미검증으로 유지.
- IAM-01: Canary의 `/dev/null` Body 처리와 stderr 억제로 기술 오류를 권한 거부처럼 판정하던 결함을 보정. 조치 전 Pod Identity Assume과 S3 Put/Get/Delete·정리를 확인하고 관련 6개 Resource 제거 뒤에는 Credential 없음·S3 Object API 0건을 확인. 다음 Up에서 되살아나지 않도록 Source 기본값을 `false`로 보정했으며 Runtime 재확인은 남음.
- Evidence: Client 종료 뒤 5분을 Event Window로 사용해 다음 단계 Log가 섞이던 결함을 `정확한 종료 시각 + Application Tail 2초 + S3 전달 유예 5분`으로 분리. WEB 3개·IAM 2개 Bundle, 총 212파일의 SHA-256 불일치 0.
- Daily Down: IAM 조치 후 남은 `250 destroyed`, 32.7분. 독립 재확인에서 Daily State·태그 기반 Runtime·Terraform Process·Watchdog·활성 Session은 모두 0, Foundation State 24·ECR Image 24개·CI IAM Role·Security Log Bucket·S3 Data Event·30일 보존은 유지.
- 남음: WAF Rate Rule의 실제 Match·Block, Metric Filter·Alarm·SNS, Athena Runtime Query, DR BANK Workload Event 검증. Goal은 Active 유지.

### 20:02

- WEB-01 재진단: CloudFront Evidence상 Count·Block POST는 각각 단일 Client IP 20건이었고 실행시간은 22.8초·22.6초. URI·Method·IP 분산 문제는 확인되지 않음.
- 공식 경계: AWS WAF Rate 제한은 근사 제어이며 완화 지연은 보통 30~50초, Web ACL 변경 전파는 수초~수분이고 Rate 설정 변경은 Count를 Reset해 최대 1분 중단될 수 있음.
- 판정: 이전 20회 실험은 WAF가 Rate를 판정하기 전에 종료됐을 가능성이 가장 높음. WAF 0건·HTTP 200을 구현 실패나 차단 성공으로 확대하지 않음.
- Source 보정: Rule·Metric 이름을 `bank-login-rate`로 고정하고 Count·Block에서 Web ACL 전파 대기 90초와 최소 50초 요청 관찰을 강제. Query도 안정 Rule ID로 제한.
- 검증: Daily Terraform `fmt -check`·`validate`, PowerShell Parser, Observability Scenario Test 통과. AWS 변경·추가 요청 없음; 다음 Runtime 재승인 필요.

### 20:18

- Foundation에 `auth.login.failed` 전용 Metric Filter, 5분·5건 CloudWatch Alarm, SNS Topic의 정적 Source와 회귀 Test를 추가. Source IP별 분석은 기존 Logs Insights Query가 담당하고 고카디널리티 Metric Dimension은 만들지 않음.
- AWS `TestMetricFilter`에서 실패 Event만 1건 Match하고 성공 Event는 제외됨을 확인. Foundation `fmt -check`·`validate`, 신규 Detection Test와 기존 Scenario Test 통과.
- 첫 Plan은 `3 add / 1 change / 0 destroy`로 S3 Data Events를 제거하려 했음. 적용 때 사용한 승인값이 local input에 남지 않은 원인이므로 `foundation/terraform.tfvars`에 `enable_project_s3_data_events = true`를 고정했고 최종 Plan은 `3 add / 0 change / 0 destroy`로 수렴.
- AWS Apply는 수행하지 않음. Email 구독은 기본 비활성이고 수신자 확인이 필요하며, DR Alert은 DR BANK Audit Event의 Runtime 검증 뒤 추가하는 경계로 유지.

### 20:28

- WEB-01에 선택형 Alarm Probe를 추가. 실행 전 Alarm이 이미 `ALARM`이면 중단하고, 현재 실행 시작 이후의 새 상태 전환만 최대 8분 동안 확인해 Client Evidence에 기록한다.
- SNS는 확정 구독 수와 Protocol만 기록하며 Email Endpoint는 출력·Evidence에 남기지 않는다. 실제 수신 여부는 수신자의 별도 확인 증거로 남기는 경계를 유지.
- PowerShell Parser, Observability Detection·Scenario Test, Daily Automation Self-test, Foundation `fmt -check`·`validate`, Credential·Endpoint 비노출 검사 통과. AWS 변경·요청 생성 없음.

### 21:00

- Athena Query Pack 실행기를 추가. `alb-errors`, `vpc-reject`, `cloudfront-trace`, `alb-trace` 네 Query만 허용하고 시간창은 최대 6시간으로 제한한다.
- 안전 경계: Foundation Bucket·Expected Owner·SSE-S3·`primary` Workgroup을 검증하고, 제한된 Polling과 동일 `ExperimentId` 재실행 Token을 사용한다. SQL·상태·Scan Byte·최대 1,000행 결과는 Local Evidence에 기록한다.
- 실제 Account·Foundation Bucket·Workgroup을 읽는 Preview는 정확한 승인 문구 전 Gate에서 중단했다. Glue Catalog 생성·Athena Query·비용 발생 작업은 수행하지 않았다.
- PowerShell Parser, Athena Query Pack Test, DDL 4문장 Renderer 계약과 기존 Daily Automation Test를 통과했다. Athena Runtime은 미검증이며 Goal은 Active 유지.

### 21:05

- 검증 중 Windows PowerShell 5.1에서 ISO-8601 `Z` 시각을 `[datetime]`으로 변환하면 Local Time으로 바뀌어, 정상 Event를 회귀 Test 실패로 오판하는 문제를 확인했다.
- Test가 `DateTimeOffset`과 `AssumeUniversal + AdjustToUniversal`로 UTC를 명시하도록 보정했다. 수집기 Runtime Logic은 변경하지 않았다.
- Windows PowerShell 5.1·PowerShell 7 Daily Automation Test, Athena·Detection·Scenario Test와 Parser가 모두 통과했다.

### 21:17

- Foundation Fresh Plan을 다시 실행해 `Metric Filter + CloudWatch Alarm + SNS Topic`만 `3 add / 0 change / 0 destroy`임을 확인했다.
- Login 실패 Filter는 `/aws/eks/aws-topology-primary/dvwa`의 `auth.login.failed`를 집계하고, Alarm은 5분 동안 5건 이상을 기준으로 한다.
- Email Subscription은 비활성 상태다. Apply는 수행하지 않았으며 정확한 승인 Gate에서 대기한다.

### 22:03

- 승인된 저장 Plan을 적용해 Foundation에 Login 실패 Metric Filter, 5분·5건 Alarm, SNS Topic을 `3 added / 0 changed / 0 destroyed`로 생성했다.
- AWS API 검증: Filter는 `auth.login.failed`만 `aws-topology/Security/DVWALoginFailures` Count로 변환하고, Alarm은 300초·5건·`treat_missing_data=notBreaching`·SNS Action 1개다.
- 생성 직후 Alarm은 `INSUFFICIENT_DATA`, SNS Subscription은 0건이다. 실제 `OK → ALARM → OK` 전이와 알림 수신은 아직 미검증이다.
- Apply 후 Foundation Plan은 `No changes`로 수렴했고 임시 Plan 파일은 삭제했다.

### 22:05

- Alarm이 생성 직후 `INSUFFICIENT_DATA`에서 `OK`로 전환됨을 확인했다. Data가 없는 1개 Period를 `notBreaching`으로 처리한 결과다.
- Foundation State는 27개이며 신규 탐지 리소스 3개가 추적된다. `OK → ALARM → OK` 전체 전이와 실제 알림 수신은 다음 Runtime 검증으로 남긴다.

### 22:07

- Windows PowerShell에서 `terraform plan -out=$planPath`가 변수값이 아닌 `$planPath`라는 파일명으로 전달됐고, 숨김형 파일명 인수도 `Too many command line arguments`로 실패했다.
- AWS Apply 전에 발생한 Local Plan 경로 문제였으며, `terraform plan -out codex-foundation-detection.tfplan`처럼 Option과 파일명을 분리해 해결했다. 잘못 생성된 임시 파일과 적용 완료 Plan은 모두 삭제했다.

### 22:54

- Daily Session `observability-20260802T131345Z`에서 `daily-up.ps1`을 실행해 `250 added / 0 changed / 0 destroyed`, 34.1분으로 Runtime을 복원했다. Argo CD `Synced / Healthy`, BANK DVWA Ready, immutable Image `sha-8a0099aa5fe8dda94ef15ac803bdd6ee73cfd413`을 확인했다.
- `web_s3_pod_identity_enabled = false`이고 Primary EKS Pod Identity Association에는 Fluent Bit·Karpenter·AWS Load Balancer Controller·EFS CSI만 존재해 BANK Web Application용 Association이 다시 생성되지 않았음을 확인했다.
- Primary 2개 Node와 DR 1개 Node에서 Fluent Bit Pod가 모두 Running이었다.
- DR `dvwa` Namespace의 임시 Probe Pod가 비민감 구조화 Event `observability.pipeline.test` 1건을 출력했고, Tokyo `/aws/eks/aws-topology-dr/dvwa` Log Group에 `request_id: dr-probe-20260802T135333Z`로 전달됨을 확인했다. Probe Pod는 확인 직후 삭제했다.
- 남음: WEB-01 20회×3단계, Alarm `OK → ALARM → OK`, Athena 4개 Query, Evidence 최종화와 Daily Down.

### 23:31

- WEB-01 조치 전·COUNT·BLOCK에서 로그인 실패를 각 20회 실행했다. 세 단계 모두 HTTP 200·Application `auth.login.failed` 20건이었고, COUNT는 마지막 2건만 `bank-login-rate` Match, BLOCK Match와 HTTP 403은 0건이었다.
- 판정: Application·WAF 관측은 성공했지만 승인된 `20회 × 3단계` 범위에서 WAF 차단 효과는 입증되지 않았다. 추가 요청으로 범위를 늘리지 않고 임시 Rule을 기본 `disabled`로 복구했다.
- Login 실패 Alarm은 조치 전 실행으로 `OK → ALARM`, 이후 Data가 1건으로 내려가며 `ALARM → OK`로 복귀했다. SNS 확정 Subscription은 0건이므로 실제 외부 알림 수신은 검증 범위 밖이다.
- Athena 4개 Query가 모두 `SUCCEEDED`: ALB 오류 0행·37,091B, VPC REJECT 534행·584,542B, CloudFront Trace 180행·26,537B, ALB Trace 1행·37,091B. ALB Trace는 Sanitized BANK `request_id`와 일치하는 ID를 사용했다.
- WEB-01 3개, Athena 4개, DR Event 1개 등 8개 Local Evidence Bundle에서 SHA-256 490개를 대조해 불일치 0을 확인했다. DR Bundle에는 Tokyo `/aws/eks/aws-topology-dr/dvwa` Event 1건이 포함됐다.
- 남음: 안전한 Daily Down, Daily Runtime 잔존 0·Foundation 27개·30일 Log 보존·Watchdog 제거 확인, 문서와 Goal 완료조건 감사.

### 00:14

- Daily Down: 승인된 `daily-down.ps1 -ConfirmDestroy 'DESTROY DAILY'`로 `250 destroyed`, 31.6분. 독립 확인에서 Daily State·태그 기반 Daily Runtime·Terraform Process·Watchdog·활성 Session은 모두 0이었다.
- Foundation: State 27개, ECR Repository, GitHub Actions IAM Role, Security Log S3와 30일 CloudWatch Log Group이 유지됐다. Primary·DR EKS, 프로젝트 EC2·NAT/EIP·RDS·Load Balancer·CloudFront 잔존은 0이었다.
- Evidence: Final Pre/Post-Down Bundle의 SHA-256 155개·180개가 모두 일치했다. Post-Down 수집은 CloudTrail 106·CloudFront 5·ALB 7·VPC REJECT 35개 Object, EKS 67,688·WAF 3·Primary DVWA 940·DR DVWA 1건이었다.
- 결함·보정: AWS JSON이 PowerShell 직렬화 깊이 30을 넘으면 Evidence가 경고와 함께 잘리는 문제를 발견했다. Depth 100으로 통일하고 40단계 Nested JSON의 최하위 값 보존·민감값 Redaction을 PowerShell 5.1·7에서 검증했다. Foundation-only 회귀 Bundle SHA-256 57개도 불일치 0이다.
- 남음: WEB-01은 90초 전파 대기·약 57초 실행 뒤에도 `COUNT` 2건·`BLOCK` 0건으로 차단 미검증. SNS Subscription 0으로 실제 알림 수신 미검증. 팀 본편 시나리오 확정·조치 전후 재검증과 보고서 보완이 남아 Goal은 Active 유지.

### 00:30

- WAF 재진단: Client Evidence에서 `count`·`block`은 각각 20회·약 60초였고, `COUNT` 2건은 실행 시작 약 58초 뒤 마지막 구간에서만 발생했다. `BLOCK`은 같은 길이의 실행 종료 전 Rate 제한이 활성화됐다는 증거가 없었다.
- 공식 동작 경계: AWS WAF Rate Rule은 정확한 횟수 제한이 아니라 최근 요청률 추정이며 완화가 보통 30~50초, 경우에 따라 수분 지연될 수 있다. `COUNT`도 Scope에 맞는 전체 요청이 아니라 실제 Rate 제한 상태에서 Rule Action이 적용된 요청만 기록한다.
- 판정: Terraform 전체 결함이 아니라 승인된 20회 실행이 WAF의 근사 완화 시작을 안정적으로 관찰하기에 짧았던 것이 현재 가장 강한 설명이다. 확정 원인은 다음 Runtime에서 더 긴 bounded 요청과 WAF Event로 재검증해야 한다.
- Source 문서 보정: Scenario·Query README와 CWLI Runtime 주석을 최신 `COUNT 2 / BLOCK 0`, Athena 완료 상태로 갱신하고 WEB-01 PowerShell Parser·Scenario 회귀 Test를 통과했다. AWS Resource 변경은 수행하지 않았다.

### 10:24

- 비용 최적화는 현재 Daily Runtime을 Down한 뒤 Terraform Plan을 검토하고 반영하기로 했다. 현재 Up·Runtime은 변경하지 않는다.
- Valkey는 통째 주석 처리 대신 `enable_valkey` 선택화를 우선 검토한다. 현재 BANK DVWA Source에서 Valkey Endpoint 사용은 발견되지 않았다.
- Cross-Region DR은 조치 전·후 및 DR 증거 수집에 필요하므로 유지한다. Primary RDS Multi-AZ는 서울 내부 AZ 장애조치용으로 Cross-Region DR과 별개이므로, 시나리오 필요성을 보고 Single-AZ 전환을 따로 판단한다.
- 후보: Primary EKS Worker `t3.medium` 2대→1대 Runtime 검증, Karpenter의 Spot→On-Demand Fallback 허용. DR을 유지하므로 지역별 NAT Gateway 1개는 당장 변경하지 않는다.
