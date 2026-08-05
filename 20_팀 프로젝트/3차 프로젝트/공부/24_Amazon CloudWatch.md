---
type: project-doc
status: draft
study_status: project-mapped
created: 2026-08-04
updated: 2026-08-05
project: 3차 프로젝트
project_moc: "[[20_팀 프로젝트/3차 프로젝트/00_3차프로젝트_목차]]"
---

# Amazon CloudWatch

> [!abstract]- 프로젝트 로그·관측성 MOC
> ![[00_로그 인프라 전체 흐름#전체 흐름]]

> [!info] 이 노트의 위치
> WAF·EKS·DVWA·CloudTrail·GuardDuty Event를 저장·검색하고, Log Pattern을 Metric과 Alarm으로 연결하는 실시간 관측 계층이다.

## 한 줄 정의

Amazon CloudWatch는 AWS Resource와 Application의 Metric, Log, Alarm을 수집·조회하고 상태 변화를 탐지하는 Observability 서비스다.

## 이 프로젝트에서 사용하는 기능

### CloudWatch Logs

```text
Log Event → Log Stream → Log Group
```

- **Log Event**: Timestamp와 Message를 가진 개별 기록
- **Log Stream**: 같은 Source 또는 실행 단위에서 이어지는 Event 묶음
- **Log Group**: Retention·권한·Metric Filter 등을 공유하는 Stream 묶음

### CloudWatch Logs Insights

여러 Log Event를 시간창·Field·Pattern으로 조회한다. Query 성공은 탐지 성공이 아니라 **해당 Log Group에서 문법과 Field가 동작했다는 사실**만 의미할 수 있다.

### Metric Filter·Metric·Alarm

```text
DVWA JSON Log
→ event_type = auth.login.failed
→ Metric Filter
→ DVWALoginFailures Metric
→ 5분 Sum Alarm
→ SNS
```

## 현재 Log Group

| Source | Region | Log Group |
|---|---|---|
| EKS Control Plane | `ap-northeast-2` | `/aws/eks/aws-topology-primary/cluster` |
| BANK DVWA | `ap-northeast-2` | `/aws/eks/aws-topology-primary/dvwa` |
| AWS WAF | `us-east-1` | `aws-waf-logs-aws-topology-edge` |
| CloudTrail | `ap-northeast-2` | `/aws/cloudtrail/aws-topology-security` |
| GuardDuty Finding | `ap-northeast-2` | `/aws/events/aws-topology-guardduty-findings` |

Foundation에서 Log Group을 미리 생성하고 공통 `security_log_retention_days`를 적용한다. `prevent_destroy`가 설정된 Persistent 관측 Resource다.

## Source별 유입 경로

```text
WAF → WAF Logging → CloudWatch Logs
EKS Control Plane → EKS Log Delivery → CloudWatch Logs
DVWA stdout·stderr → Fluent Bit → CloudWatch Logs
CloudTrail → CloudWatch Logs
GuardDuty Finding → EventBridge → CloudWatch Logs
```

## 저장소에서 찾을 곳

- Log Groups·CloudTrail Delivery: `foundation/observability.tf`
- Metric Filter·Alarm·GuardDuty Finding Log Group: `foundation/detection.tf`
- EKS Log Type: `eks.tf`
- Fluent Bit Output: `templates/install-cluster-addons.sh.tpl`
- Query Pack: `observability/queries/cloudwatch/`
- 범용 Review: `Review-SecurityWindow.ps1`

## 직접 확인하는 방법

```powershell
aws logs describe-log-groups --region ap-northeast-2
aws logs describe-log-groups --region us-east-1 `
  --log-group-name-prefix aws-waf-logs-

# 특정 Log Group의 최근 Stream
aws logs describe-log-streams `
  --log-group-name /aws/eks/aws-topology-primary/dvwa `
  --order-by LastEventTime `
  --descending `
  --region ap-northeast-2

# Metric Filter·Alarm
aws logs describe-metric-filters `
  --log-group-name /aws/eks/aws-topology-primary/dvwa `
  --region ap-northeast-2
aws cloudwatch describe-alarms `
  --alarm-name-prefix aws-topology-dvwa-login-failures `
  --region ap-northeast-2
```

Logs Insights는 실험 UTC 시작·종료 시각을 먼저 고정하고, 필요한 Log Group만 선택해 실행한다.

## 현재 확인 수준

- Log Group·Retention·전달 Source: 확인
- Logs Insights Query Pack: 확인
- 기존 Evidence:
  - CloudTrail 변경 Query 76행 기록
  - WEB-01 Application·WAF Query와 Alarm `OK → ALARM → OK` 기록
  - GuardDuty Finding Query 준비 및 Sample Finding 전달 기록
- 최신 Runtime의 Stream·Event·Alarm 상태: 재확인 필요

## 알려주는 것과 한계

### 확인할 수 있는 것

- 구조화된 Application Event와 AWS Service Log
- 특정 시간창의 사용자·관리자·Controller 행위
- Pattern 발생 횟수와 Alarm 상태 변화

### 이것만으로 확인할 수 없는 것

- S3에 직접 저장되는 CloudFront·ALB·VPC Flow 원본 전체
- Query 결과가 실제 공격인지 여부
- Best Effort Delivery에서 Event가 0건일 때 행위가 절대 없었다는 사실

## 비용·운영 주의점

- 수집량·보존량·Logs Insights Scan 범위가 비용에 영향을 준다.
- Query 시간창과 Log Group을 좁혀 불필요한 Scan을 줄인다.
- WAF Log는 `us-east-1`, 나머지 주요 Log Group은 `ap-northeast-2`이므로 Region 혼동에 주의한다.
- Password, Cookie, Authorization, Session, Token을 Query 결과로 반출하지 않는다.

## 근거

- 현재 저장소: `foundation/observability.tf`, `foundation/detection.tf`, Query Pack
- 공식 문서: https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/CloudWatchLogsConcepts.html
- 공식 문서: https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/AnalyzingLogData.html
- Runtime Evidence: 최신 실행 재확인 필요
