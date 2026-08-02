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
