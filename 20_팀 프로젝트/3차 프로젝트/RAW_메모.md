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
