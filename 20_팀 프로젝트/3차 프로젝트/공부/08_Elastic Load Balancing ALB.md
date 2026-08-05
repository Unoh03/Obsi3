---
type: project-doc
status: draft
study_status: project-mapped
created: 2026-08-04
updated: 2026-08-05
project: 3차 프로젝트
project_moc: "[[20_팀 프로젝트/3차 프로젝트/00_3차프로젝트_목차]]"
---

# Elastic Load Balancing (ALB)

> [!abstract]- 프로젝트 로그·관측성 MOC
> ![[00_로그 인프라 전체 흐름#전체 흐름]]

> [!info] 이 노트의 위치
> Edge에서 허용된 요청을 EKS의 Kubernetes Service·DVWA Pod로 전달하고, 그 전달 결과를 Access Log로 남기는 관측 지점이다.

## 한 줄 정의

Application Load Balancer는 HTTP·HTTPS 요청을 Listener Rule에 따라 Target Group으로 전달하는 Layer 7 Load Balancer다.

## 로그 관점의 역할

ALB Access Log는 다음 질문에 답하는 데 유용하다.

- 어떤 Client가 어떤 URL로 요청했는가
- ALB와 Target이 각각 어떤 Status Code를 반환했는가
- 요청 처리 시간이 어느 구간에서 소비됐는가
- 어느 Target IP·Port로 전달됐는가
- `trace_id`를 이용해 Application Event와 연결할 수 있는가

반대로 ALB는 DVWA의 로그인 성공 여부나 SQL 문장의 의미까지 알지 못한다.

## 우리 프로젝트에서의 역할

```text
CloudFront + WAF
→ Primary ALB
→ Target Group(target_type=ip)
→ TargetGroupBinding
→ Kubernetes Service
→ BANK DVWA Pod
```

현재 `edge.tf`에서 확인된 설정:

- Resource: `aws_lb.primary`
- 인터넷 공개 ALB
- Public Subnet에 배치
- Listener: HTTP 80
- Target Group Protocol: HTTP
- Target Type: `ip`
- Access Logging 조건: `enable_edge_access_logging`
- Log Bucket: Foundation Security Log Bucket
- Prefix: `alb/primary`

DR ALB도 조건부로 존재하지만, 현재 Access Log 설정은 Primary ALB에만 확인된다.

## 저장·분석 흐름

```text
ALB Access Log
→ Security Log S3
→ alb/primary/AWSLogs/<account>/elasticloadbalancing/ap-northeast-2/
→ Athena Table alb_primary_access
→ alb-errors·alb-trace·alb-window Query
→ Grafana 예정
```

## 저장소에서 찾을 곳

- Terraform: `edge.tf`
- TargetGroupBinding: `target-group-binding.tf`, `charts/target-group-binding/`
- Athena Schema: `observability/queries/athena/00_create_security_log_tables.sql`
- Query:
  - `01_alb_4xx_5xx_by_source.sql`
  - `04_alb_trace_id_correlation.sql`
  - `05_alb_security_window.sql`
- Runner: `observability/Invoke-AthenaQueryPack.ps1`

## 직접 확인하는 방법

```powershell
# ALB와 Access Log 속성
aws elbv2 describe-load-balancers --region ap-northeast-2
aws elbv2 describe-load-balancer-attributes `
  --load-balancer-arn <PRIMARY_ALB_ARN> `
  --region ap-northeast-2

# S3 Object 도착 확인
aws s3api list-objects-v2 `
  --bucket <SECURITY_LOG_BUCKET> `
  --prefix alb/primary/ `
  --max-items 10

# Athena Preview 후 승인된 경우에만 실행
.\observability\Invoke-AthenaQueryPack.ps1 `
  -QueryName alb-window `
  -StartUtc <UTC_START> `
  -EndUtc <UTC_END>
```

## 현재 확인 수준

- Terraform Source와 S3 Prefix: 확인
- Athena DDL·Query Pack: 확인
- 기존 Evidence에는 `alb-errors`, `alb-trace` Query 성공과 `trace_id` 1행 상관관계 기록이 있음
- 최신 Runtime의 ALB Object 도착과 Query 결과: 재확인 필요

## 한계와 주의점

- Access Log는 Best Effort 전달이므로 행 부재만으로 요청 부재를 단정하지 않는다.
- ALB Access Log 활성화와 S3 Bucket Policy가 모두 맞아야 Object가 도착한다.
- `elb_status_code`와 `target_status_code`를 구분해야 ALB 자체 오류와 Application 응답을 혼동하지 않는다.
- Sensitive Header나 Request Body 전체를 제공하는 Application Audit Log가 아니다.

## 근거

- 현재 저장소: `edge.tf`, Athena Query Pack
- 공식 문서: https://docs.aws.amazon.com/elasticloadbalancing/latest/application/load-balancer-access-logs.html
- Runtime Evidence: 최신 실행 재확인 필요
