---
type: project-doc
status: draft
study_status: project-mapped
created: 2026-08-04
updated: 2026-08-05
project: 3차 프로젝트
project_moc: "[[20_팀 프로젝트/3차 프로젝트/00_3차프로젝트_목차]]"
---

# AWS CloudTrail

> [!abstract]- 프로젝트 로그·관측성 MOC
> ![[00_로그 인프라 전체 흐름#전체 흐름]]

> [!info] 이 노트의 위치
> Console·AWS CLI·Terraform·AWS Service가 수행한 AWS API 행위를 기록해 CloudWatch Logs와 Security Log S3로 전달하는 감사 계층이다.

## 한 줄 정의

AWS CloudTrail은 AWS Account에서 누가, 언제, 어디서, 어떤 API를 어떤 Resource에 호출했는지 기록하는 감사 서비스다.

## 무엇을 기록하는가

대표 Field:

- `eventTime`
- `eventSource`
- `eventName`
- `awsRegion`
- `sourceIPAddress`
- `userAgent`
- `userIdentity`
- `requestParameters`
- `responseElements`
- `errorCode`, `errorMessage`

CloudTrail은 DVWA 사용자의 일반 HTTP 요청을 기록하지 않는다. AWS API 호출이 대상이다.

## Event 종류

- **Management Event**: IAM, EC2, EKS, CloudFront 등의 Control Plane 작업
- **Data Event**: S3 Object, Lambda Invoke 등 Data Plane 작업
- **Insights Event**: API 호출량·오류율의 이상 변화

Data Event는 기본 Trail에 자동으로 모두 포함되지 않으며 별도 Selector와 비용을 고려해야 한다.

## 우리 프로젝트에서의 역할

Foundation Trail 설정:

- Trail Name: `aws-topology-security-trail`
- Multi-Region
- Global Service Event 포함
- Log File Validation 활성화
- Security Log S3로 전달
- CloudWatch Logs로도 전달
- 기본값: Management Event `ReadWriteType=All`
- 선택적 S3 Data Event:
  - Primary·DR Application Bucket Prefix만 대상
  - `GetObject`, `PutObject`, `DeleteObject`
  - `enable_project_s3_data_events`로 명시적 활성화

## 흐름

```text
운영자·Terraform·Controller
→ AWS API
→ CloudTrail Event
├─ CloudWatch Logs → Logs Insights
└─ Security Log S3 → 장기 보존·Athena 확장 가능
```

EKS Controller가 AWS API를 호출한 기록은 CloudTrail에서 볼 수 있지만, `kubectl exec` 같은 Kubernetes API 행위는 EKS Audit Log에서 확인해야 한다.

## 저장소에서 찾을 곳

- Trail·S3·CloudWatch Delivery: `foundation/observability.tf`
- Query:
  - `observability/queries/cloudwatch/04_cloudtrail_security_changes.cwli`
  - `07_pod_identity_and_s3_activity.cwli`
- IAM-01 Scenario: `observability/scenarios/Invoke-IAM01.ps1`
- Evidence 수집: `automation/Evidence.Collection.psm1`

## 직접 확인하는 방법

```powershell
aws cloudtrail describe-trails --include-shadow-trails false --region ap-northeast-2
aws cloudtrail get-trail-status `
  --name aws-topology-security-trail `
  --region ap-northeast-2
aws cloudtrail get-event-selectors `
  --trail-name aws-topology-security-trail `
  --region ap-northeast-2

# 최근 Management Event 간단 조회
aws cloudtrail lookup-events `
  --lookup-attributes AttributeKey=EventName,AttributeValue=PutRolePolicy `
  --region ap-northeast-2
```

S3 Log File Validation은 Validation Chain과 Digest File을 사용하므로 단순히 Object가 존재하는 것과 별개로 검증한다.

## 현재 확인 수준

- Multi-Region Trail·S3·CloudWatch·Validation Source: 확인
- 기본 Management Event와 선택적 S3 Data Event Selector: 확인
- 기존 Evidence:
  - `04_cloudtrail_security_changes.cwli` 76행
  - `terra-user` 72행, EKS Service Role 4행으로 Infrastructure 변경 Baseline 판정
  - IAM-01 Canary S3 Object API 기록 확인 이력
- 최신 Trail Status·Delivery Error·Selector: 재확인 필요

## 알려주는 것과 한계

### 확인할 수 있는 것

- AWS API 호출 Principal과 Session
- API 성공·실패와 대상 Resource
- Terraform·Controller·사용자 행위의 감사 추적

### 이것만으로 확인할 수 없는 것

- 일반 웹 사용자의 URL 요청과 로그인 결과
- Kubernetes API의 세부 Audit 행위
- API 호출이 악의적인지 여부 — Context와 Baseline이 필요

## 주의점

- Event History는 Trail의 장기 저장소가 아니라 최근 Management Event 조회 기능이다.
- Data Event를 켜면 기록량과 비용이 증가할 수 있으므로 실험 범위를 Prefix와 Event Name으로 제한한다.
- `AssumedRole` Event는 원본 IAM Role과 Session Name을 함께 해석한다.
- CloudTrail Event가 존재한다고 해서 변경이 실제 원하는 상태로 완료됐다는 뜻은 아니다. 후속 Resource 상태를 확인한다.

## 근거

- 현재 저장소: `foundation/observability.tf`, CloudWatch Query Pack
- 공식 문서: https://docs.aws.amazon.com/awscloudtrail/latest/userguide/cloudtrail-concepts.html
- 공식 문서: https://docs.aws.amazon.com/awscloudtrail/latest/userguide/cloudtrail-log-file-validation-intro.html
- Runtime Evidence: 최신 실행 재확인 필요
