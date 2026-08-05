---
type: project-doc
status: draft
study_status: project-mapped
created: 2026-08-04
updated: 2026-08-05
project: 3차 프로젝트
project_moc: "[[20_팀 프로젝트/3차 프로젝트/00_3차프로젝트_목차]]"
---

# Amazon CloudFront

> [!abstract]- 프로젝트 로그·관측성 MOC
> ![[00_로그 인프라 전체 흐름#전체 흐름]]

> [!info] 이 노트의 위치
> 외부 사용자의 HTTP 요청이 처음 처리·관측되는 Edge 지점이며, 선택한 Access Log Field를 Security Log S3로 전달한다.

## 한 줄 정의

CloudFront는 전 세계 Edge Location에서 요청을 받아 Cache·전송 정책에 따라 Origin으로 전달하는 CDN 서비스다.

## 요청 흐름

```text
사용자
→ Route 53 DNS 해석
→ CloudFront Distribution
→ AWS WAF Web ACL 검사
→ Primary ALB Origin
```

Route 53은 HTTP 요청을 Proxy하지 않는다. 이 프로젝트에서 실제 HTTP 요청을 처음 받는 구성요소는 CloudFront이며, WAF는 CloudFront Distribution에 연결돼 같은 Edge 경계에서 요청을 검사한다.

## 로그 관점의 역할

CloudFront Access Log로 주로 확인할 수 있는 것:

- 요청 시각과 Edge Location
- Client IP와 국가
- HTTP Method, Host, URI Path
- 응답 Status와 Edge 처리 결과
- `x-edge-request-id`
- 전송 Byte와 처리 시간
- TLS Protocol·Cipher

CloudFront Log만으로는 ALB가 어느 Pod로 전달했는지, DVWA 로그인이 성공했는지 알 수 없다.

## 우리 프로젝트에서의 역할

`edge.tf`와 `observability.tf`에서 다음 구성이 확인된다.

- Distribution: `aws_cloudfront_distribution.this`
- Origin: Primary ALB
- WAF 연결: `enable_waf_observation`이 활성화된 경우
- HTTPS Redirect: 변수로 제어
- Query String과 Cookie는 Origin으로 전달
- Standard Logging v2 Source·Delivery 사용
- Destination: Foundation Security Log S3
- Output Format: JSON
- Log Record에서는 Cookie·Query String Field를 의도적으로 제외

주요 기록 Field:

```text
date, time, x-edge-location, c-ip, cs-method, cs(Host), cs-uri-stem,
sc-status, x-edge-request-id, cs-protocol, time-taken,
x-forwarded-for, ssl-protocol, ssl-cipher, c-country
```

## 저장·분석 흐름

```text
CloudFront Access Log
→ CloudWatch Log Delivery v2
→ Security Log S3
→ AWSLogs/<account>/CloudFront/
→ Athena Table cloudfront_access
→ cloudfront-trace Query
→ Grafana 예정
```

## 저장소에서 찾을 곳

- Distribution·Origin·Route 53 Alias: `edge.tf`
- Log Delivery: `observability.tf`
- Persistent S3 Destination: `foundation/observability.tf`
- Athena Schema: `observability/queries/athena/00_create_security_log_tables.sql`
- Query: `observability/queries/athena/03_cloudfront_request_trace.sql`

## 직접 확인하는 방법

```powershell
aws cloudfront list-distributions
aws cloudfront get-distribution --id <DISTRIBUTION_ID>

# Standard Logging v2 Delivery 확인은 us-east-1 기준
aws logs describe-delivery-sources --region us-east-1
aws logs describe-deliveries --region us-east-1

aws s3api list-objects-v2 `
  --bucket <SECURITY_LOG_BUCKET> `
  --prefix AWSLogs/<ACCOUNT_ID>/CloudFront/ `
  --max-items 10
```

## 현재 확인 수준

- Distribution·ALB Origin·WAF 연결 Source: 확인
- Standard Logging v2와 Field 목록: 확인
- Athena Schema·Trace Query: 확인
- 기존 Evidence에는 CloudFront Athena Query 성공 기록이 있음
- 최신 Runtime Object 도착과 요청 추적: 재확인 필요

## 한계와 주의점

- Access Log는 요청의 Edge 관점 기록이며 Application Audit Log가 아니다.
- 로그 전달은 즉시·완전성을 보장하는 Transaction 기록으로 취급하지 않는다.
- Origin으로 Cookie·Query String을 전달하는 것과 Log에 해당 값을 남기는 것은 별개다.
- `x-edge-request-id`만으로 ALB `trace_id`나 DVWA `request_id`가 자동 연결되지는 않는다. 시간창·Client IP·URI 등 추가 조건이 필요하다.

## 근거

- 현재 저장소: `edge.tf`, `observability.tf`, Athena Query Pack
- 공식 문서: https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/standard-logging.html
- Runtime Evidence: 최신 실행 재확인 필요
