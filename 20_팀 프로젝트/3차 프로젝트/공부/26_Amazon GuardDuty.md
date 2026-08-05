---
type: project-doc
status: draft
study_status: project-mapped
created: 2026-08-04
updated: 2026-08-05
project: 3차 프로젝트
project_moc: "[[20_팀 프로젝트/3차 프로젝트/00_3차프로젝트_목차]]"
---

# Amazon GuardDuty

> [!abstract]- 프로젝트 로그·관측성 MOC
> ![[00_로그 인프라 전체 흐름#전체 흐름]]

> [!info] 이 노트의 위치
> AWS의 위협 신호를 분석해 Finding을 만들고, Finding을 EventBridge로 전달하는 탐지 계층이다.

## 한 줄 정의

Amazon GuardDuty는 AWS Account와 Workload의 활동을 분석해 의심스러운 행위를 Finding으로 제공하는 관리형 Threat Detection 서비스다.

## Log Source와 다른 점

GuardDuty는 CloudTrail이나 VPC Flow Logs처럼 원본 Event를 장기 저장하는 Log Repository가 아니다.

```text
AWS의 관측 신호
→ GuardDuty 분석
→ Finding
```

Finding에는 다음과 같은 조사 요약이 들어간다.

- Finding Type
- Severity
- 영향을 받은 Resource
- Account·Region
- 탐지 시각
- 관련 Network·API 정보

원본 증거는 CloudTrail, VPC Flow Logs, EKS Audit Log 등에서 별도로 확인해야 한다.

## 우리 프로젝트에서의 역할

현재 `foundation/detection.tf`의 Detector 설정:

- Primary Account Detector 활성화
- Finding Publishing Frequency: `FIFTEEN_MINUTES`
- 1차 범위는 Foundational Threat Detection
- 다음 Optional Protection Plan은 명시적으로 비활성:
  - S3 Data Events
  - EKS Audit Logs Protection
  - EBS Malware Protection
  - RDS Login Events
  - Lambda Network Logs
  - Runtime Monitoring
  - AI Protection

> [!important] 범위 해석
> 현재 GuardDuty가 EKS Runtime Monitoring까지 수행한다고 설명하면 틀린다. Source에서는 Optional 기능을 꺼 두고 Foundational Detection만 사용한다.

## Finding 전달 흐름

```text
GuardDuty Finding
→ EventBridge Rule
├─ CloudWatch Logs: 전체 Event 보존
└─ SNS: Severity·Type·Resource·Finding ID 중심 축약 알림
```

## 저장소에서 찾을 곳

- Detector·Feature 상태: `foundation/detection.tf`
- EventBridge·Log Group·SNS Target: `foundation/detection.tf`
- Query: `observability/queries/cloudwatch/12_guardduty_findings.cwli`
- F2 검증: `observability/findings/`, `tests/test-finding-f2.ps1`

## 직접 확인하는 방법

```powershell
$detector = aws guardduty list-detectors `
  --region ap-northeast-2 `
  --query 'DetectorIds[0]' `
  --output text

aws guardduty get-detector `
  --detector-id $detector `
  --region ap-northeast-2

aws guardduty list-findings `
  --detector-id $detector `
  --region ap-northeast-2

aws guardduty get-findings `
  --detector-id $detector `
  --finding-ids <FINDING_ID> `
  --region ap-northeast-2
```

## 현재 확인 수준

- Detector와 비활성 Optional Feature Source: 확인
- EventBridge·CloudWatch Logs·SNS Routing Source: 확인
- 기존 F2 Evidence는 AWS Sample Finding으로 전달 Pipeline을 검증한 기록
- Sample Finding은 실제 공격 증거가 아님
- 최신 Detector Status와 실제 Finding: 재확인 필요

## 알려주는 것과 한계

### 확인할 수 있는 것

- AWS가 탐지한 의심 활동의 Type·Severity·Resource
- 우선 조사할 Finding ID와 관련 Metadata

### 이것만으로 확인할 수 없는 것

- 모든 공격의 존재 여부
- Application 내부 로그인 성공·실패
- 원본 Event 전체
- Finding이 실제 Incident인지 여부

## 분석 원칙

1. Finding ID를 고정한다.
2. Finding의 Resource·Account·Region·Time Window를 확인한다.
3. CloudTrail·VPC Flow Logs·EKS·Application Log에서 원본 근거를 찾는다.
4. Sample Finding과 실제 Detection을 분리한다.
5. Severity만 보고 사고를 확정하지 않는다.

## 근거

- 현재 저장소: `foundation/detection.tf`, F2 Query·Script
- 공식 문서: https://docs.aws.amazon.com/guardduty/latest/ug/guardduty_data-sources.html
- 공식 문서: https://docs.aws.amazon.com/guardduty/latest/ug/guardduty_findings.html
- Runtime Evidence: 최신 실행 재확인 필요
