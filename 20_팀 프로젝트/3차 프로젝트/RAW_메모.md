# RAW 메모

<!-- 2026-07-30 21:14까지 일일 로그 반영 완료 -->

### 12:52

- 한 일: 관측성 Goal Phase 0 읽기 전용 기준점 확인. DVWA Git과 배포 Image SHA가 일치하고 Argo CD `Synced / Healthy`, Pod `Ready` 상태를 확인.
- 활성 로그: CloudTrail Management Event는 Foundation의 CloudWatch·S3 7일 보존 구조, EKS는 `api/audit/authenticator` 활성. DVWA Apache Access Log는 Container stdout에만 존재.
- 미수집: WAF 없음, CloudFront·ALB·VPC Flow 중앙 로그 없음, DVWA Namespace Container Log 수집 Agent 없음, BANK 구조화 Audit Log 없음.
- 보안 발견: 공개 정상 요청에서도 Apache·PHP 상세 Version Header와 Session·Security Cookie가 발급됨. 실제 Cookie 값은 기록하지 않음.
- Evidence 경계: 현재 Collector는 `S3Prefix`만 지원하고 Redaction·Time Window·실험별 Strict Mode가 없음. 로컬 보관본은 CloudTrail 원본을 암호화 없이 동기화하므로 접근권한·민감 Metadata 취급 보강 필요.
