---
type: learning-note
status: active
created: 2026-08-20
topic: Telemetry
project: 3차 프로젝트
parent: "[[8.19 멘토님과 상담]]"
---

# Telemetry와 로그 지연 모델

> [!NOTE]
> 이 문서는 `[[8.19 멘토님과 상담]]`에서 분리한 개념 정본이다.  
> A/B/C/D/E는 AWS 공식 표준 구간명이나 SLA가 아니라, 이 프로젝트에서 latency 원인을 분리하기 위해 정의한 **분석 모델**이다.

## 1. Telemetry란 무엇인가?

한 줄 정의:

> **Telemetry = 시스템이나 서비스가 자신의 상태·행위·성능·발생 사건을 외부에서 관찰하고 분석할 수 있도록 생성·노출하는 관측 데이터 또는 운영 신호의 총칭.**

로그는 Telemetry의 한 종류다.

```text
Telemetry
├─ Logs
├─ Metrics
├─ Traces
└─ Events  ← 프레임워크에 따라 Log와 별도 또는 중첩 분류
```

| 종류 | 무엇을 표현하는가 | 예시 | 보안 관제 용도 |
|---|---|---|---|
| Log | 특정 시점의 행위·결과 기록 | HTTP 요청, 로그인 실패, WAF 검사 결과 | 탐지 Rule, 조사, 포렌식 Evidence |
| Metric | 시간에 따른 수치 | CPU, 요청 수, 5xx 비율 | 임계치·추세·이상 징후 탐지 |
| Trace | 하나의 요청이 여러 컴포넌트를 통과한 경로 | Client → API → Service → DB | 분산 요청 경로·병목·실패 지점 분석 |
| Event | 상태 변화나 특정 사건을 나타내는 이산적 신호 | S3 ObjectCreated, EC2 State Change | Event-driven Trigger·자동화 |

공식 프레임워크마다 하위 분류는 조금 다르다.

- Microsoft는 Logs / Metrics / Traces / Events를 함께 열거한다.
- AWS Well-Architected는 Metrics / Logs / Traces를 Observability의 주요 축으로 설명한다.
- OpenTelemetry는 Traces / Metrics / Logs를 핵심 Signal로 다루고 Event를 특정 형태의 Log와 연결해 설명한다.

중요한 것은 개수 암기가 아니라 **Telemetry가 관찰 데이터의 상위 개념**이라는 점이다.

## 2. Telemetry와 Observability

```text
Telemetry
= 관찰을 위해 얻는 데이터와 신호

Observability
= 그 데이터를 이용해 시스템 내부 상태를 이해할 수 있는 능력과 실천
```

로그를 S3에 쌓아두기만 했다고 높은 Observability가 생기는 것은 아니다.

```text
필요한 Telemetry 수집
→ 검색 가능
→ Source 간 상관분석
→ 시각화
→ 내부 상태와 Incident를 설명 가능
```

해야 한다.

## 3. Instrumentation

**Instrumentation**은 Telemetry를 생성·캡처할 수 있도록 애플리케이션이나 인프라에 관측 기능을 넣는 과정이다.

```text
DVWA 코드에 command.execution 감사 Record 추가
→ Application Instrumentation

EKS Control Plane Logging 활성화
→ 관리형 Telemetry 설정

CloudFront Real-time Logs 활성화
→ 관리형 Logging mechanism 설정
```

## 4. 가장 중요한 계층 구분

```text
Resource / Service
≠ Telemetry signal
≠ Logging mechanism
≠ Initial destination
≠ SIEM transport
≠ SIEM / Analysis backend
≠ Detection logic
≠ Detection result
```

CloudFront에 대입하면:

| 계층 | CloudFront 예시 |
|---|---|
| Resource / Service | CloudFront Distribution |
| Observed activity | Viewer Request |
| Telemetry signal family | Log |
| Logging mechanism | Standard Logging / Real-time Access Logging |
| Record / Schema | timestamp, URI, status, client 정보 등 |
| Initial destination | CloudWatch Logs / Firehose / S3 / Kinesis Data Streams |
| SIEM transport | Subscription / Consumer / Lambda / SQS / Local Bridge |
| Analysis backend | Wazuh SIEM |
| Detection logic | Wazuh Rule |
| Detection result | Wazuh Alert |

따라서 이 프로젝트에서 쓰는:

```text
서비스 × Telemetry × Route
```

는 편의상 축약이고, 엄밀히는 다음에 가깝다.

```text
Resource
× Signal family
× Logging mechanism
× Destination
× SIEM transport
× Analysis backend
```

## 5. Source와 Logging mechanism을 혼동하지 않는다

다음 표현은 부정확하다.

```text
CloudFront Standard와 Real-time은 서로 다른 Source다.
```

더 정확한 표현:

> **같은 CloudFront Resource의 Viewer Request를 관찰하지만, Standard Logging과 Real-time Logging은 서로 다른 Telemetry mechanism·Delivery path·availability latency를 가진다.**

마찬가지로:

```text
ALB는 5분짜리다.  X
```

보다:

```text
ALB Legacy S3 Access Logging은 노드별 5분 단위 Log file 발행 특성이 있다.
ALB Vended Logs는 별도의 Delivery mechanism이다.  O
```

라고 말한다.

---

# 6. A/B/C/D/E 지연 모델

## 핵심

A/B/C/D/E는 구성요소가 아니라 **두 상태 사이의 지연 구간**이다.

```text
실제 Event                                ← Point
   │
   │ A. Source 생성·집계 지연             ← Interval
   ▼
Log / Event Record                        ← Point
   │
   │ B. Source-native Delivery 지연        ← Interval
   ▼
AWS Destination에서 Consumer-visible      ← Point
   │
   │ C. SIEM Transport 지연                ← Interval
   ▼
Wazuh 입력                                ← Point
   │
   │ D. SIEM 분석·Alert 생성 지연          ← Interval
   ▼
Wazuh Alert / Integratord 호출             ← Point
   │
   │ E. SOAR 전달·실행 지연                ← Interval
   ▼
Shuffle terminal Execution / Action result ← Point
```

### A — Source 생성·집계

```text
Event
→ Log/Event Record 생성
```

예:

- VPC Flow Logs aggregation
- Legacy ALB Log file 생성
- 애플리케이션 감사 Record 작성

### B — Source-native Delivery

```text
Record
→ CloudWatch Logs / S3 / EventBridge / Kinesis 등에서 소비 가능
```

예:

- CloudFront → Kinesis
- CloudTrail → CloudWatch Logs / S3
- ALB Legacy → S3 Object

### C — SIEM Transport

```text
AWS Destination에서 소비 가능
→ Wazuh 입력
```

예:

- 10분 Poll
- Subscription → Lambda → SQS → Local Bridge
- S3 ObjectCreated → SQS → Consumer

### D — SIEM 분석

```text
Wazuh 입력
→ Decoder / Rule 평가
→ Alert 생성
→ Integratord 호출
```

### E — SOAR

```text
Wazuh Alert
→ Webhook 전달
→ Shuffle Execution
→ Action terminal result
```

전체 Event-to-Action latency를 말하려면:

```text
전체 E2E = A + B + C + D + E
```

다. A+B+C만 측정하고 Shuffle까지 포함한 전체 E2E라고 부르지 않는다.

## A가 끝난 뒤 바로 Wazuh로 보낼 수 있는가?

가능한 Source라면 이론적으로 가능하다.

```text
Event
→ [A] Record 생성
→ Wazuh
```

다만 AWS 관리형 서비스는 일반적으로 임의 SIEM Endpoint보다 CloudWatch Logs, S3, EventBridge, Kinesis, Firehose, Lambda 같은 AWS-native Destination을 먼저 제공한다.

현재 프로젝트의 Wazuh는 로컬이며 Internet Inbound를 열지 않는다. 따라서 다음 구조가 보안·복구 측면에서 더 적합하다.

```text
AWS Source
→ Event-driven AWS Destination
→ SQS 등 Buffer
→ Local Bridge Outbound Consumer
→ Wazuh
```

Hop이 적다고 항상 최적 Route는 아니다.

- 노트북·Wazuh 중단 중 Event 보존
- Retry / DLQ
- 중복·순서 통제
- Local Wazuh Inbound 미노출

을 함께 봐야 한다.

---

# 7. CloudFront Standard와 Real-time은 완전한 상위·하위 관계인가?

**아니다. Real-time이 무조건 Standard의 완벽한 상위호환은 아니다.** 같은 Viewer Request Log 계열이지만 목적·지연·비용·전달 구조가 다르다.

| 항목 | Standard Logging v2 | Real-time Access Logging |
|---|---|---|
| 사용 가능 지연(A+B) | 일반적으로 Event 후 1시간 이내, 일부 Entry 최대 24시간 | 요청 수신 후 수초 내 Kinesis 전달 |
| 주 목적 | 장기 보존, Historical analysis, Audit, 대량 분석 | 저지연 Monitoring, Alert, 즉시 대응 Trigger |
| Destination | CloudWatch Logs, Firehose, S3 | Kinesis Data Streams |
| 출력 형식 | JSON, plain, W3C, raw, S3의 Parquet 등 | Kinesis Consumer가 고정 순서 Record를 해석 |
| Sampling | 별도 사용자 Sampling 설정이 핵심 기능은 아님 | 1~100% Sampling 설정 가능 |
| 범위 선택 | Distribution Logging 설정 | 특정 Cache Behavior에 연결 가능 |
| 필드 | Legacy field와 Standard v2에서 선택 가능한 추가 field | 필요한 field를 선택, 최대 field 수·순서 고려 |
| 비용 | CloudFront 자체 활성화 추가요금은 없지만 Destination ingest/storage 비용 발생 | CloudFront Real-time Log 요금 + Kinesis 비용 |
| 운영 복잡도 | Archive·분석에 단순 | Kinesis capacity, Consumer, Schema order, throttle 처리 필요 |
| 완전성 | Best-effort, 지연·누락 가능 | Best-effort, 지연·누락 가능; Sampling <100이면 의도적 미수집 |

### Standard가 나은 경우

- 즉시 대응보다 장기 보존과 전체 기간 분석이 중요
- Kinesis Consumer 운영 복잡도를 피하고 싶음
- S3 / Parquet / Athena 같은 Archive 분석이 핵심
- Real-time 비용을 정당화할 저지연 탐지 Use Case가 없음

### Real-time이 나은 경우

- 수초 단위 Edge Request 신호가 실제 대응 결정에 필요
- 특정 Cache Behavior만 선택적으로 관찰하고 싶음
- Sampling으로 비용과 분석량을 통제하고 싶음
- Kinesis Consumer와 장애·Throttle 처리를 운영할 수 있음

### 중요한 제한

> **같은 활동 유형을 관찰한다는 뜻이지, 두 경로가 동일한 Record 집합을 일대일로 제공한다는 뜻은 아니다.**

- Real-time은 Sampling을 설정할 수 있음
- 둘 다 best-effort
- 지연·누락 가능
- 필드 구성·활성화 시점·Cache Behavior 범위가 다를 수 있음

따라서 Standard와 Real-time을 서로 완전히 대체 가능한 동일 데이터셋으로 가정하지 않는다.

---

# 8. Real-time Logs와 Kinesis의 경계

```text
Viewer Request                         ← Point
      │
      │ A. Log Record 생성             ← Interval
      ▼
Real-time Log Record                  ← Point
      │
      │ B. CloudFront → Kinesis 전달   ← Interval
      ▼
Kinesis에서 Consumer-visible          ← Point
      │
      │ C. Consumer → Wazuh            ← Interval
      ▼
Wazuh 입력                            ← Point
```

Kinesis 자체가 B라는 뜻은 아니다. Kinesis는 B의 Destination이다.

CloudFront 공식 문서가 공개하는 것은:

```text
Viewer Request
→ [A + B]
→ Kinesis에서 Real-time Log 사용 가능

전체: 수초 내
```

이다. AWS는 A와 B를 따로 수치화하지 않는다.

Kinesis Data Streams는 실시간 Streaming을 위해 설계됐고 Record의 `put-to-get delay`는 일반적으로 1초 미만이다. 이 노트에서는 Destination에서 Consumer-visible이 될 때까지를 B로 정의하므로 이 지연도 B에 포함한다.

외우기:

> **Real-time Logging이 A+B 전체를 수초 단위로 만들고, 그 안에서 Kinesis가 B의 저지연 Streaming Destination 역할을 한다.**

`Kinesis는 B를 짧게 하려고 만들어졌다`보다는:

> **Kinesis는 실시간 Streaming을 위해 만들어졌기 때문에 B를 짧게 유지하는 데 적합하다.**

가 정확하다.

Destination만 Kinesis로 바꾼다고 Standard Logging의 A+B가 Real-time으로 변하지 않는다.

---

# 9. CloudWatch Logs Subscription은 어디에 해당하는가?

CloudWatch Logs Subscription Filter는 CloudWatch Logs에 이미 수집된 Event를 Lambda, Kinesis, Firehose 등으로 지속 전달하는 Forwarding mechanism이다.

```text
원래 Source Event
→ [A+B] CloudWatch Logs에 수집
→ Subscription
→ Destination
→ 이후 SIEM Transport
```

공식 문서 기준:

- Log Event가 CloudWatch Logs에 ingest된 뒤 보통 3분 미만에 수신 Resource로 전달
- Retry 가능한 오류는 최대 24시간 재시도
- 24시간 이후 실패분은 유실될 수 있음
- AccessDenied / ResourceNotFound 같은 비재시도 오류는 별도 장애 상태를 유발
- Destination capacity 부족·Throttle을 모니터링해야 함

따라서 Subscription은 원래 Source의 A+B를 없애지 않는다. **CloudWatch Logs 이후의 Poll 대기와 전달 지연을 줄이는 mechanism**이다.

---

# 10. 확인된 DVWA→Wazuh 하위 경로 측정

근거: `[[20_팀 프로젝트/3차 프로젝트/일일 로그/RAW/2026-08-17_RAW]]`

검증 Route:

```text
DVWA
→ CloudWatch Logs
→ Lambda
→ SQS
→ Local Bridge
→ Wazuh localfile(JSONL)
→ Rule 100102 Alert
```

| Validation ID | 총 지연 |
|---|---:|
| `wazuh-push-20260817T102046747Z` | 6.439초 |
| `wazuh-push-20260817T102127824Z` | 3.427초 |
| `wazuh-push-20260817T102209527Z` | 3.761초 |

- 3건 모두 Wazuh Alert 도착
- 누락 0건
- 실제 `command.execution` Rule `100103` 검증 이전의 무해 Runtime 검증
- G4 Shuffle Execution은 포함하지 않음

따라서 가장 정확한 명칭은:

> **DVWA→Wazuh 저지연 하위 경로 Runtime E2E, N=3**

이다.

`전체 프로젝트 E2E` 또는 `Alert→Shuffle E2E`라고 부르지 않는다.

현재 노트에는 실행 ID와 결과가 남아 있지만, 별도 Evidence Bundle 경로·SHA-256이 확인되면 추후 추가한다. 근거가 아직 완전한 Artifact Index로 연결되지 않았다는 이유로 관측값 자체를 삭제하지는 않는다.

---

# 11. 한 줄 암기

> **Telemetry는 시스템이 자기 상태와 행위를 밖으로 말해주는 데이터이고, Logging mechanism은 그 말을 어떤 방식으로 만들고 내보낼지, Destination은 처음 어디에서 소비 가능해질지, Transport는 SIEM까지 어떻게 옮길지, SIEM Rule은 무엇이 위험한지 판정하며, SOAR는 그 Alert 이후의 대응을 실행한다.**

```text
A/B/C/D/E = 선(지연 구간)
Event / Record / Destination / Wazuh / Shuffle = 점(상태·구성요소)
```

## 공식 근거

- [OpenTelemetry — Signals](https://opentelemetry.io/docs/concepts/signals/)
- [OpenTelemetry — What is OpenTelemetry?](https://opentelemetry.io/docs/what-is-opentelemetry/)
- [Azure Well-Architected — Observability](https://learn.microsoft.com/azure/well-architected/operational-excellence/observability)
- [AWS Well-Architected — Implement observability](https://docs.aws.amazon.com/wellarchitected/latest/operational-excellence-pillar/implement-observability.html)
- [CloudFront — Standard logging reference](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/standard-logs-reference.html)
- [CloudFront — Standard logging v2](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/standard-logging.html)
- [CloudFront — Real-time access logs](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/real-time-logs.html)
- [Kinesis Data Streams — Introduction](https://docs.aws.amazon.com/streams/latest/dev/introduction.html)
- [CloudWatch Logs — Subscriptions](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/Subscriptions.html)
