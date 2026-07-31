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
