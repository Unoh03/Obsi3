---
type: project-doc
status: draft
study_status: project-mapped
created: 2026-08-04
updated: 2026-08-05
project: 3차 프로젝트
project_moc: "[[20_팀 프로젝트/3차 프로젝트/00_3차프로젝트_목차]]"
---

# AWS WAF

> [!abstract]- 프로젝트 로그·관측성 MOC
> ![[00_로그 인프라 전체 흐름#전체 흐름]]

> [!info] 이 노트의 위치
> CloudFront Edge에서 HTTP 요청을 Rule로 검사하고, 이 프로젝트에서는 `COUNT`·`BLOCK` 결과만 CloudWatch Logs에 남기는 보안 관측 계층이다.

## 한 줄 정의

AWS WAF는 Web ACL과 Rule을 이용해 HTTP·HTTPS 요청을 검사하고 `ALLOW`, `COUNT`, `BLOCK` 등의 Action을 적용하는 Web Application Firewall이다.

## 로그 관점의 역할

WAF Log로 확인할 수 있는 것:

- 어떤 Web ACL·Rule이 요청과 Match했는가
- 최종 Action 또는 Rule Action이 무엇인가
- Client IP, URI, Method, Header 등 요청의 검사 대상 정보
- Managed Rule의 Label과 Match 세부정보

WAF Log만으로는 요청이 ALB·Pod에서 최종적으로 어떻게 처리됐는지, 로그인에 성공했는지 알 수 없다.

## 우리 프로젝트에서의 역할

현재 `observability.tf`에서 확인된 구성:

- Scope: `CLOUDFRONT`
- Web ACL: `aws_wafv2_web_acl.edge`
- Default Action: `ALLOW`
- `AWSManagedRulesCommonRuleSet`: `COUNT`
- `AWSManagedRulesSQLiRuleSet`: `COUNT`
- `/login.php`의 `POST` 요청 대상 Rate Rule:
  - 기본 `disabled`
  - 실험 시 `count` 또는 `block`
- Log Destination: `aws-waf-logs-aws-topology-edge`
- Region: CloudFront Scope이므로 `us-east-1`
- `authorization`, `cookie` Header Redaction
- Logging Filter:
  - 기본 `DROP`
  - `COUNT`, `BLOCK` Event만 `KEEP`

> [!important] COUNT의 의미
> Rule에 Match했다는 관측은 남기지만 요청을 막지는 않는다. 취약한 교육용 Application의 접근성을 유지하면서 어떤 Rule이 반응하는지 먼저 확인하기 위한 단계다.

## 흐름

```text
CloudFront 요청
→ WAF Rule 평가
├─ COUNT: 요청 계속 진행 + Log 보존
├─ BLOCK: Edge에서 종료 + Log 보존
└─ ALLOW: 현재 Logging Filter에서는 기본적으로 저장하지 않음
```

## 저장·분석 흐름

```text
WAF COUNT·BLOCK Log
→ CloudWatch Logs(us-east-1)
→ Logs Insights
→ Rule Match·Rate Limit 조사
```

관련 Query:

- `02_waf_count_matches.cwli`
- `06_waf_login_rate_limit.cwli`
- `09_review_waf_requests.cwli`
- `10_t1_waf_requests.cwli`

## 저장소에서 찾을 곳

- Web ACL·Logging: `observability.tf`
- Log Group: `foundation/observability.tf`
- Query: `observability/queries/cloudwatch/`
- Scenario: `observability/scenarios/Invoke-WEB01.ps1`, `Invoke-T1.ps1`

## 직접 확인하는 방법

```powershell
# CloudFront Scope WAF는 us-east-1 사용
aws wafv2 list-web-acls --scope CLOUDFRONT --region us-east-1
aws wafv2 get-logging-configuration `
  --resource-arn <WEB_ACL_ARN> `
  --region us-east-1

aws logs describe-log-groups `
  --region us-east-1 `
  --log-group-name-prefix aws-waf-logs-aws-topology-edge

aws logs filter-log-events `
  --region us-east-1 `
  --log-group-name aws-waf-logs-aws-topology-edge `
  --start-time <EPOCH_MS> `
  --end-time <EPOCH_MS>
```

## 현재 확인 수준

- Rule·Logging Filter·Redaction Source: 확인
- Logs Insights Query Pack: 확인
- 기존 WEB-01 Evidence에는 `COUNT` Match 2건이 기록돼 있음
- 기존 기록에서 `BLOCK` Event와 HTTP 403은 0건이므로 차단 성공은 검증되지 않음
- 최신 Runtime: 재확인 필요

## 한계와 주의점

- WAF Rule Match는 공격 성공을 의미하지 않는다.
- `COUNT`는 탐지·관측이지 차단이 아니다.
- 현재 Logging Filter는 ALLOW Event를 대부분 버리므로 전체 Traffic 원본은 CloudFront·ALB Log와 함께 봐야 한다.
- Sensitive Header Redaction은 Log 노출을 줄이지만 Request Body·다른 Header까지 자동으로 모두 비식별화하는 것은 아니다.
- Rate Rule 설정 변경은 추적 Counter에 영향을 줄 수 있으므로 실험 단계 전환 시각을 기록한다.

## 근거

- 현재 저장소: `observability.tf`, CloudWatch Query Pack
- 공식 문서: https://docs.aws.amazon.com/waf/latest/developerguide/logging.html
- Runtime Evidence: 최신 실행 재확인 필요
