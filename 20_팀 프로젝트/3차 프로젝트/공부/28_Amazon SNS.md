---
type: project-doc
status: draft
study_status: project-mapped
created: 2026-08-04
updated: 2026-08-05
project: 3차 프로젝트
project_moc: "[[20_팀 프로젝트/3차 프로젝트/00_3차프로젝트_목차]]"
---

# Amazon SNS

> [!abstract]- 프로젝트 로그·관측성 MOC
> ![[00_로그 인프라 전체 흐름#전체 흐름]]

> [!info] 이 노트의 위치
> CloudWatch Alarm과 GuardDuty EventBridge Target이 만든 보안 신호를 구독자에게 전달하는 최종 알림 계층이다.

## 한 줄 정의

Amazon SNS는 Publisher가 Topic에 Message를 보내면 연결된 Subscription으로 전달하는 Pub/Sub Messaging 서비스다.

## 핵심 구조

```text
Publisher
→ SNS Topic
→ Subscription
→ Email·SMS·HTTP·SQS 등의 Endpoint
```

이 프로젝트에서 SNS는 Log를 장기 저장하거나 공격을 판정하지 않는다. 이미 만들어진 Alarm·Finding 알림을 전달한다.

## 우리 프로젝트에서의 역할

Persistent Topic:

```text
aws-topology-security-alerts
```

Publisher 1 — CloudWatch Alarm:

```text
DVWA auth.login.failed
→ Metric Filter
→ DVWALoginFailures
→ CloudWatch Alarm
→ SNS
```

- Alarm 진입 시 `alarm_actions`
- 정상 복귀 시 `ok_actions`

Publisher 2 — EventBridge:

```text
GuardDuty Finding
→ EventBridge
→ Input Transformer
→ SNS
```

GuardDuty 알림은 Finding 전체 JSON이 아니라 다음 초기 대응 Field로 축약된다.

- Severity
- Finding Type
- Region
- Resource Type
- Finding ID
- Time

## Subscription

Email Subscription은 다음 조건에서만 생성한다.

- `enable_security_alert_email_subscription = true`
- 유효한 `security_alert_email` 입력
- 수신자가 별도 Confirmation Mail 승인

Terraform이 Subscription을 생성해도 수신자가 확인하지 않으면 최종 전달 준비가 끝난 것이 아니다.

## 저장소에서 찾을 곳

- Topic·Subscription·Alarm Action·EventBridge Target: `foundation/detection.tf`
- WEB-01 Scenario: `observability/scenarios/Invoke-WEB01.ps1`
- GuardDuty F2: `observability/findings/Invoke-F2.ps1`

## 직접 확인하는 방법

```powershell
aws sns list-topics --region ap-northeast-2

aws sns get-topic-attributes `
  --topic-arn <SECURITY_ALERT_TOPIC_ARN> `
  --region ap-northeast-2

aws sns list-subscriptions-by-topic `
  --topic-arn <SECURITY_ALERT_TOPIC_ARN> `
  --region ap-northeast-2

# 구독 상태에서 PendingConfirmation 여부 확인
```

테스트 Publish는 실제 구독자에게 메시지를 보내는 Side Effect가 있으므로 수신자·문구·시각을 확인한 뒤 실행한다.

## 현재 확인 수준

- Topic·선택적 Email Subscription·두 Publisher Source: 확인
- 기존 Evidence에는 WEB-01 Alarm 상태 전환과 GuardDuty Sample Finding 알림 기록이 있음
- 최신 Subscription Confirmation·실제 수신·Delivery 상태: 재확인 필요

## 알려주는 것과 한계

### 확인할 수 있는 것

- 어떤 Topic과 Subscription이 있는가
- 어떤 서비스가 Topic에 Publish하도록 구성됐는가
- Subscription이 `Confirmed` 또는 `PendingConfirmation`인지

### 이것만으로 확인할 수 없는 것

- 메시지가 실제 Incident인지
- 수신자가 읽고 대응했는지
- 원본 Log와 전체 조사 Context

## 주의점

- Topic 생성과 구독 확인은 별개다.
- Alarm의 `ALARM`과 `OK` Message를 구분한다.
- SNS Message에 Password, Token, Cookie, Session, 긴 AWS Session Metadata를 넣지 않는다.
- Sample Finding 알림을 실제 공격 알림으로 보고하지 않는다.
- 알림이 너무 많으면 운영자가 무시하게 되므로 Metric·Rule Threshold와 Message 내용을 별도로 검토한다.

## 근거

- 현재 저장소: `foundation/detection.tf`
- 공식 문서: https://docs.aws.amazon.com/sns/latest/dg/welcome.html
- Runtime Evidence: 최신 실행 재확인 필요
