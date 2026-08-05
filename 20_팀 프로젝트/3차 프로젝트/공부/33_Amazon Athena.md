---
type: project-doc
status: draft
study_status: project-mapped
created: 2026-08-05
project: 3차 프로젝트
project_moc: "[[20_팀 프로젝트/3차 프로젝트/00_3차프로젝트_목차]]"
---

# Amazon Athena

> [!abstract]- 프로젝트 로그·관측성 MOC
> ![[00_로그 인프라 전체 흐름#전체 흐름]]

> [!info] 이 노트의 위치
> Security Log S3의 CloudFront·ALB·VPC Flow 원본에 External Table Schema를 부여하고 SQL로 조회하는 분석 계층이다.

## 한 줄 정의

Amazon Athena는 S3에 저장된 Data를 별도 Server 구축 없이 SQL로 조회하는 Serverless Query 서비스다.

## 왜 S3 다음에 Athena가 필요한가

S3는 Object를 보관하지만 Log Record의 Column과 Type을 이해하지 않는다.

```text
S3 Object
→ Athena Database·External Table
→ Schema·LOCATION 지정
→ SQL Query
→ Result Object + Query Metadata
```

External Table은 Log를 Athena 내부로 복사하는 것이 아니라, S3의 어느 경로를 어떤 Schema로 읽을지 Catalog에 등록한다.

## 우리 프로젝트의 Schema

기본 Database:

```text
aws_topology_security
```

| Source | Table | Format | S3 LOCATION |
|---|---|---|---|
| CloudFront | `cloudfront_access` | JSON SerDe | `AWSLogs/<account>/CloudFront/` |
| Primary ALB | `alb_primary_access` | Regex SerDe | `alb/primary/AWSLogs/<account>/elasticloadbalancing/ap-northeast-2/` |
| Primary VPC REJECT | `vpc_reject` | Space-delimited | `vpc-flow/AWSLogs/<account>/vpcflowlogs/ap-northeast-2/` |

CloudTrail은 S3에 저장되지만 현재 Grafana 1차 Table·Panel 범위에는 포함하지 않는다.

## Query Pack

`Invoke-AthenaQueryPack.ps1`이 허용하는 Query:

| QueryName | 목적 |
|---|---|
| `alb-errors` | Source별 ALB 4xx·5xx 확인 |
| `vpc-reject` | Source IP별 REJECT Flow 확인 |
| `cloudfront-trace` | Edge 요청 시간창 추적 |
| `alb-trace` | ALB `trace_id`와 Application `request_id` 상관관계 |
| `alb-window` | 지정 시간창의 ALB 요청 검토 |

기본 WorkGroup은 현재 `primary`다. 이후 Grafana 구현에서는 전용 WorkGroup과 Query Result Bucket을 추가할 계획이지만 아직 구성되지 않았다.

## 안전한 실행 순서

### 1. Local DDL Rendering

AWS를 변경하지 않고 Placeholder만 치환한다.

```powershell
$bucket = terraform -chdir=foundation output -raw security_log_bucket_name
$account = aws sts get-caller-identity --query Account --output text

.\observability\render-athena-schema.ps1 `
  -SecurityLogBucket $bucket `
  -AccountId $account `
  -PrimaryRegion ap-northeast-2 `
  -OutputPath "$env:TEMP\aws-topology-athena-schema.sql"
```

### 2. Preview

```powershell
.\observability\Invoke-AthenaQueryPack.ps1 `
  -QueryName cloudfront-trace `
  -StartUtc <UTC_START> `
  -EndUtc <UTC_END> `
  -CreateSchema
```

### 3. 승인 후 실행

DDL은 Glue/Athena Catalog를 변경하고 SELECT는 Scan 비용을 발생시킨다. Preview의 Account, Bucket, Region, SQL, 시간창을 확인한 뒤 승인 문구를 추가한다.

```powershell
-ConfirmRun 'RUN ATHENA QUERY PACK'
```

## Result와 Evidence

Runner는 다음을 보존하도록 작성돼 있다.

- 실행 SQL
- Query Execution ID·Status
- Scan Byte
- 최대 1,000행 Result
- Foundation S3의 `athena-results/<experiment-id>/`
- Local Evidence Directory

Query `SUCCEEDED`는 SQL 실행 성공을 뜻한다. 공격 정탐이나 충분한 Log Coverage를 자동으로 의미하지 않는다.

## 저장소에서 찾을 곳

- DDL: `observability/queries/athena/00_create_security_log_tables.sql`
- SQL Query: `observability/queries/athena/`
- Runner: `observability/Invoke-AthenaQueryPack.ps1`
- Local Renderer: `observability/render-athena-schema.ps1`
- Test: `tests/test-athena-query-pack.ps1`
- 설계 결정: `OBSERVABILITY-IAM-DECISIONS.md`

## 직접 확인하는 방법

```powershell
aws athena list-work-groups --region ap-northeast-2
aws glue get-databases --region ap-northeast-2
aws glue get-tables `
  --database-name aws_topology_security `
  --region ap-northeast-2
aws athena list-query-executions `
  --work-group primary `
  --region ap-northeast-2
aws athena get-query-execution `
  --query-execution-id <QUERY_ID> `
  --region ap-northeast-2
```

## 현재 확인 수준

- DDL·Table·LOCATION·Query Runner Source: 확인
- 기존 2026-08-02 Evidence:
  - `alb-errors`
  - `vpc-reject`
  - `cloudfront-trace`
  - `alb-trace`
  - 네 Query가 `SUCCEEDED`
  - `alb-trace` 1행이 Sanitized BANK `request_id`와 연결
- 최신 Catalog·Table·WorkGroup·Object Coverage: 재확인 필요
- Grafana 전용 WorkGroup·Result Bucket: 아직 미구성

## 오류를 해석하는 순서

```text
0행
→ 시간창이 맞는가
→ Source Object가 실제 존재하는가
→ Table LOCATION이 정확한가
→ Log Format과 Schema가 맞는가
→ Partition·Region·Account 경로가 맞는가

NULL Field·Parse 오류
→ SerDe·Regex와 실제 Log Format 비교

ACCESS_DENIED
→ Athena·Glue·Result Bucket·원본 Prefix 권한 분리 확인
```

## 비용·보안 주의점

- Scan 범위를 줄이기 위해 시간 조건과 필요한 Column만 사용한다.
- 원본 Security Log Bucket과 Query Result Bucket의 역할을 분리한다.
- Query Result에도 IP·식별자가 포함될 수 있으므로 Evidence 반출 시 Masking한다.
- DDL의 `IF NOT EXISTS`는 기존 Table Schema가 올바르다는 보장이 아니다.

## 근거

- 현재 저장소: Athena DDL·Query Pack·Runner
- 공식 문서: https://docs.aws.amazon.com/athena/latest/ug/querying-AWS-service-logs.html
- 공식 문서: https://docs.aws.amazon.com/athena/latest/ug/create-cloudfront-table-manual-json.html
- Runtime Evidence: 최신 실행 재확인 필요
