---
type: project-doc
status: draft
study_status: project-mapped
created: 2026-08-04
updated: 2026-08-05
project: 3차 프로젝트
project_moc: "[[20_팀 프로젝트/3차 프로젝트/00_3차프로젝트_목차]]"
---

# Amazon S3

> [!abstract]- 프로젝트 로그·관측성 MOC
> ![[00_로그 인프라 전체 흐름#전체 흐름]]

> [!info] 이 노트의 위치
> CloudFront·ALB·VPC Flow·CloudTrail 원본을 지속 보존하고, Athena Query의 Data Source가 되는 장기 저장 계층이다.

## 한 줄 정의

Amazon S3는 Object를 Bucket과 Object Key로 저장하는 관리형 Object Storage다.

## 이 프로젝트에서 구분할 두 종류의 Bucket

### Application Data Bucket

- Daily Runtime의 Primary·DR Bucket
- 애플리케이션 데이터와 Pod Identity 실험 대상
- `force_destroy = true`
- DR 활성 시 Replication 구성

### Security Log Bucket

- Foundation의 Persistent Bucket
- Bucket Prefix: `aws-topology-security-logs-...`
- `force_destroy = false`
- `prevent_destroy = true`
- Public Access Block
- Versioning
- SSE-S3 `AES256`
- Retention Lifecycle

> [!important] 분리 이유
> Application Data와 Security Evidence는 작성 주체, 접근 권한, 수명주기, 삭제 위험이 다르다. 이 프로젝트는 별도 Security Log Bucket을 사용한다.

## Source별 Object Key 구분

S3의 Prefix는 실제 Directory가 아니라 Object Key의 공통 앞부분이다.

| Source | 현재 Prefix·경로 기준 | 분석 |
|---|---|---|
| CloudFront | `AWSLogs/<account>/CloudFront/` | Athena `cloudfront_access` |
| Primary ALB | `alb/primary/AWSLogs/<account>/elasticloadbalancing/ap-northeast-2/` | Athena `alb_primary_access` |
| Primary VPC REJECT | `vpc-flow/AWSLogs/<account>/vpcflowlogs/ap-northeast-2/` | Athena `vpc_reject` |
| CloudTrail | `AWSLogs/<account>/CloudTrail/` 계열 | 감사 원본 보존 |
| Athena Result | `athena-results/<experiment-id>/` | Query 실행 결과 |

현재 요구사항은 **서비스별 Bucket을 늘리는 방식이 아니라 Security Log Bucket 하나에서 Source별 Prefix를 분리하는 방식**으로 해석한다.

## Write Principal과 경계

Bucket Policy는 Source별 AWS Service Principal과 Object 경로를 제한한다.

- CloudTrail: `cloudtrail.amazonaws.com`
- Vended Log Delivery: `delivery.logs.amazonaws.com`
- ALB Log Delivery: `logdelivery.elasticloadbalancing.amazonaws.com`

ALB는 `alb/primary/`, VPC Flow Logs는 `vpc-flow/`, CloudTrail은 AWS 기본 경로를 사용한다.

## 저장소에서 찾을 곳

- Security Log Bucket·Policy·Lifecycle: `foundation/observability.tf`
- Application Data Bucket·DR Replication: `storage-observability.tf`
- CloudFront·VPC Destination: `observability.tf`
- ALB Prefix: `edge.tf`
- Athena Schema: `observability/queries/athena/00_create_security_log_tables.sql`

## 직접 확인하는 방법

```powershell
$bucket = terraform -chdir=foundation output -raw security_log_bucket_name

aws s3api get-bucket-versioning --bucket $bucket
aws s3api get-bucket-encryption --bucket $bucket
aws s3api get-public-access-block --bucket $bucket
aws s3api get-bucket-lifecycle-configuration --bucket $bucket

# Source별 Object 존재 확인
aws s3api list-objects-v2 --bucket $bucket --prefix alb/primary/ --max-items 10
aws s3api list-objects-v2 --bucket $bucket --prefix vpc-flow/ --max-items 10
aws s3api list-objects-v2 --bucket $bucket --prefix AWSLogs/ --max-items 20
```

Object 하나를 확인할 때는 Key, Size, LastModified를 기록하되 Log 원문에 포함된 IP·식별자는 보고서 반출 전에 필요한 범위만 Masking한다.

## 현재 확인 수준

- Security Log Bucket 보안 설정과 Bucket Policy Source: 확인
- Source별 Prefix와 Athena LOCATION: 확인
- 기존 Evidence에는 CloudFront·ALB·VPC Log를 읽는 Athena Query 성공 기록이 있음
- 최신 Object 도착, Retention 적용 결과, CloudTrail File Validation: 재확인 필요

## 알려주는 것과 한계

### 확인할 수 있는 것

- Log Object가 실제로 전달됐는지
- Source·Account·Region·날짜별 Object 경로
- 장기 보존 원본과 Athena Scan 대상

### 이것만으로 확인할 수 없는 것

- Object 내용이 공격을 의미하는지
- Log 전달이 누락 없이 완전한지
- CloudWatch Logs의 실시간 Alarm 상태

## 운영 주의점

- Bucket 하나를 사용하더라도 IAM Policy와 Athena `LOCATION`은 Source별 Prefix로 제한한다.
- `AWSLogs/` 아래에서 CloudFront와 CloudTrail이 공존할 수 있으므로 Table LOCATION을 너무 넓게 잡지 않는다.
- Versioning과 Lifecycle이 함께 있으므로 Current·Noncurrent Object 수명주기를 모두 본다.
- `prevent_destroy`는 Terraform 삭제 방어이지 Account 탈취나 수동 삭제 전체를 막는 절대 통제가 아니다.

## 근거

- 현재 저장소: `foundation/observability.tf`, `storage-observability.tf`, Athena DDL
- 공식 문서: https://docs.aws.amazon.com/AmazonS3/latest/userguide/using-prefixes.html
- Runtime Evidence: 최신 실행 재확인 필요
