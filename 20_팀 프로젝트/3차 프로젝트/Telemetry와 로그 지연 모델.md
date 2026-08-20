---
type: project-doc
status: active
created: "2026-08-20"
project: "3차 프로젝트"
project_moc: "[[00_3차프로젝트_목차]]"
---

> [!NOTE] 분해 문서 안내
> 원문은 `3a6b45ec37f9be01f41ddd66ae20511fe2264f9a`의 정정 완료 단일 노트에서 블록 단위로 이동했다. SOURCE-BLOCK 내부는 원문 그대로이며, 안내문과 링크만 신규 내용이다. 이 문서는 Telemetry·Observability·Instrumentation과 A/B/C/D/E 지연 모델을 설명한다.

<!-- 8.19-MENTOR-CONTEXT-BRIDGE CBR03 -->
> [!NOTE] 원문 선행 문맥
> B011 제목과 첫 문장의 `위의 로그 Source × Telemetry × Route 비교`는 [[AWS 보안 Telemetry Route 비교#로그 Source × Telemetry × Route 비교 — 공식 문서 재검증]]을 가리킨다.

<!-- 8.19-MENTOR-SOURCE-BLOCK B011 START -->
# Telemetry 개념 정리 — 위의 로그/Route 표를 읽기 위한 선행 개념

> 이 섹션은 위의 `로그 Source × Telemetry × Route 비교`를 정확히 읽기 위한 개념 정리다.  
> 결론부터 말하면 **Telemetry는 로그의 다른 이름이 아니다. 로그는 Telemetry의 한 종류다.**

## 1. Telemetry란 무엇인가?

한 줄로 정의하면:

> **Telemetry = 시스템이나 서비스가 자신의 상태·행위·성능·발생 사건을 외부에서 관찰하고 분석할 수 있도록 생성·노출하는 관측 데이터 또는 운영 신호의 총칭.**

Microsoft Azure Well-Architected Framework는 Telemetry를 `logs, metrics, traces, events`의 집합적 용어로 정의하고, 이 데이터가 Observability의 기반이라고 설명한다. OpenTelemetry 역시 Signal을 운영체제와 애플리케이션의 내부 활동을 설명하는 시스템 출력으로 정의하고 Trace, Metric, Log 등을 핵심 Signal로 다룬다. AWS Well-Architected Framework도 Application Telemetry가 Observability의 기반이며 Metrics, Logs, Traces가 세 가지 주요 축이라고 설명한다.

즉 다음 관계로 이해하면 된다.

```text
Telemetry
├─ Logs
├─ Metrics
├─ Traces
└─ Events  ← 분류 체계에 따라 Log와 겹치기도 함
```

### 분류가 문서마다 조금 다른 이유

Telemetry의 큰 의미는 거의 같지만 **하위 분류를 어디까지 독립 Signal로 볼지는 프레임워크마다 조금 다르다.**

- Microsoft는 Logs / Metrics / Traces / Events를 별도로 열거한다.
- AWS Well-Architected는 현재 Metrics / Logs / Traces를 Observability의 세 주요 축으로 설명한다.
- OpenTelemetry의 현재 Signals 문서는 Traces / Metrics / Logs를 핵심으로 다루며, `Events`는 특정 종류의 Log로 설명한다.

따라서 `Event는 무조건 Log와 완전히 별개다` 또는 `Telemetry는 오직 세 종류뿐이다`처럼 분류 체계를 절대적인 표준으로 외울 필요는 없다. 중요한 것은 **Telemetry가 시스템을 외부에서 관찰하기 위한 데이터/신호의 상위 개념**이라는 점이다.

## 2. Log / Metric / Trace / Event 차이

| 종류 | 무엇을 표현하는가 | 예시 | 보안 관제에서의 용도 |
|---|---|---|---|
| **Log** | 특정 시점에 무엇이 발생했는지 기록 | HTTP 요청, 로그인 실패, WAF 검사 결과, 애플리케이션 오류 | 탐지 Rule, 조사, 포렌식 Evidence |
| **Metric** | 시간에 따른 수치 상태·성능 | CPU 75%, 초당 요청 수, 5xx 비율 | 이상 징후·임계치·추세 탐지 |
| **Trace** | 하나의 요청/트랜잭션이 여러 컴포넌트를 통과한 경로 | Client → API → Service A → DB | 분산 환경의 병목·실패 지점·요청 흐름 분석 |
| **Event** | 상태 변화나 특정 사건을 나타내는 이산적 신호 | S3 ObjectCreated, EC2 State Change, GuardDuty Finding | Event-driven 자동화·탐지 Trigger |

로그와 Event는 겹칠 수 있다. 예를 들어 `사용자가 로그인에 실패했다`는 사건을 한 줄의 Log record로 남길 수 있다. 반대로 EventBridge의 `EC2 Instance State-change Notification`처럼 **상태 변화 자체를 이벤트 메시지로 전달**하는 형태도 있다.

## 3. Telemetry와 Observability는 다르다

```text
Telemetry
= 우리가 관찰하기 위해 얻는 데이터

Observability
= 그 데이터를 이용해 시스템 내부 상태를 이해할 수 있는 능력/실천
```

Telemetry가 재료라면 Observability는 그 재료를 이용해 시스템을 이해하는 능력에 가깝다.

예를 들어 로그를 S3에 쌓아두기만 했다고 해서 자동으로 높은 Observability가 생기는 것은 아니다. 필요한 Telemetry가 수집되고, 서로 연계되고, 검색·상관분석·시각화되어 실제 상태를 설명할 수 있어야 한다.

## 4. Instrumentation은 또 다른 개념이다

**Instrumentation**은 Telemetry를 만들어내거나 캡처할 수 있도록 애플리케이션·인프라에 관측 기능을 넣는 과정이다.

예:

```text
DVWA 코드에 command.execution 감사 로그 추가
→ 애플리케이션 Instrumentation

EKS Control Plane Logging 활성화
→ 관리형 서비스의 Telemetry 수집 설정

CloudFront Real-time Logs 활성화
→ AWS 관리형 Telemetry 기능 설정
```

관리형 AWS 서비스에서는 직접 코드를 삽입하지 않고 `Enable Logging`, `Create Log Configuration` 같은 설정만으로 Telemetry를 활성화하는 경우가 많다. 넓은 의미에서는 이것도 관측 데이터를 얻기 위한 Instrumentation/Telemetry configuration으로 볼 수 있다.

## 5. 가장 중요한 구분: 서비스 ≠ Telemetry ≠ Logging Mode ≠ Destination ≠ Route

이 프로젝트에서는 아래 계층을 분리해서 봐야 한다.

| 계층 | 의미 | CloudFront 예시 |
|---|---|---|
| **Resource / Service** | 우리가 관찰하려는 대상 | CloudFront Distribution |
| **Observed activity** | 그 대상에서 알고 싶은 행위 | Viewer Request |
| **Telemetry signal family** | 어떤 종류의 관측 데이터인가 | Log |
| **Telemetry mechanism / Logging mode** | 그 Log를 어떤 방식·빈도·정책으로 생성/전달하는가 | Standard Logging / Real-time Access Logging |
| **Record / Schema** | 실제 Log record에 어떤 필드가 있는가 | timestamp, URI, status, client 정보 등 |
| **Initial destination** | AWS에서 Telemetry가 처음 전달되는 소비 지점 | Standard v2: CloudWatch Logs / Firehose / S3, Real-time: Kinesis Data Streams |
| **SIEM transport / pipeline** | 목적지에서 Wazuh까지 어떻게 이동하는가 | Subscription → Lambda → SQS → Bridge → Wazuh |
| **Backend / Analysis** | 도착한 Telemetry를 저장·검색·분석하는 곳 | Wazuh SIEM |
| **Detection logic** | Telemetry에서 위협을 판정하는 규칙 | Wazuh Rule |
| **Derived detection output** | Rule 평가 결과 새로 생성된 탐지 결과 | Wazuh Alert |

여기서 `Telemetry mechanism / Logging mode`는 이 노트에서 구조를 이해하기 위해 사용하는 분석 용어다. 모든 Vendor가 동일한 이름의 계층을 공식 표준으로 사용하는 것은 아니다.

### Source와 Logging mechanism을 혼동하지 않는다

다음 표현은 부정확하다.

```text
CloudFront Standard와 Real-time은 서로 다른 Source다.
```

더 정확한 표현은 다음과 같다.

> **같은 CloudFront Resource의 Viewer Request를 관찰하지만, Standard Logging과 Real-time Logging은 서로 다른 Telemetry mechanism·Delivery path·사용 가능 지연(A+B)을 가진다.**

마찬가지로 `ALB는 5분짜리다`가 아니라 `ALB Legacy S3 Access Logging은 5분 단위 Log file 발행 특성이 있고, Vended Logs는 별도의 Delivery mechanism이다`라고 말한다.

### 그래서 `서비스 × Telemetry × Route`는 축약 표현이다

이 노트에서 편의를 위해:

```text
서비스 × Telemetry × Route
```

라고 적었지만, 더 엄밀하게 풀면 다음에 가깝다.

```text
Resource / Service
× Telemetry signal family
× Telemetry mechanism / logging mode
× Initial destination
× SIEM transport
× Analysis backend
```

## 6. CloudFront 예제로 완전히 이해하기

같은 CloudFront Distribution에 같은 Viewer Request가 들어왔다고 가정한다.

```text
Viewer
  ↓ HTTP Request
CloudFront Distribution
  ├─ Standard Access Logging
  │    ↓
  │   Log Telemetry
  │    ↓
  │   CloudWatch Logs / Firehose / S3 (v2)
  │
  └─ Real-time Access Logging
       ↓
      Log Telemetry
       ↓
      Kinesis Data Streams
```

둘 다 **CloudFront Viewer Request를 기록하는 Log Telemetry**다.

차이는 `Telemetry 종류가 Log냐 아니냐`가 아니라 **같은 Log Telemetry를 어떤 Logging mechanism으로 만들어 전달하느냐**다.

| 항목 | Standard Access Logging | Real-time Access Logging |
|---|---|---|
| 관찰 대상 | CloudFront Viewer Request | CloudFront Viewer Request |
| Signal family | Log | Log |
| Logging mechanism | Standard | Real-time |
| 전달 시점 | 일반적으로 Event 후 1시간 이내, 일부 Entry는 최대 24시간 지연 가능 | 요청 수신 후 수초 내 |
| 주요 Destination | v2: CloudWatch Logs / Firehose / S3, Legacy: S3 | Kinesis Data Streams |
| Sampling | 일반 Access Log 방식 | 1~100% Sampling 설정 가능 |
| 주요 용도 | Historical analysis, Audit, Compliance, 장기 보존 | 실시간 Monitoring, Alert, Live Dashboard |
| 전달 특성 | Best-effort, 지연/누락 가능 | Best-effort, 지연/누락 가능 |

### Standard와 Real-time은 완전한 상위·하위 관계가 아니다

Real-time Access Logging이 더 빠르지만 Standard Logging의 모든 목적을 완전히 대체하지는 않는다.

| 비교 항목 | Standard Logging | Real-time Access Logging |
|---|---|---|
| 강점 | 장기 보존, Historical analysis, Audit/Compliance, S3·Parquet·Athena 연계 | 수초 단위 Monitoring·Alert, 특정 Cache Behavior 선택, 1~100% Sampling |
| 비용·운영 | Destination ingest/storage 비용 중심, Kinesis Consumer 불필요 | CloudFront Real-time Logs 비용 + Kinesis 비용, Capacity·Consumer·Throttle 운영 필요 |
| 수집 범위 | 일반 Access Log 방식, 활성화 시점·필드 구성에 따른 차이 | Sampling과 Cache Behavior 범위에 따라 의도적으로 일부 요청만 수집 가능 |
| 완전성 | Best-effort, 지연·누락 가능 | Best-effort, 지연·누락 가능. Sampling <100이면 동일 Record 집합이 아님 |

> **같은 활동 유형을 관찰한다는 뜻이지, 두 경로가 반드시 동일한 Record 집합을 일대일로 제공한다는 뜻은 아니다.**

즉 저지연 Trigger가 필요하면 Real-time을, 장기 보존·전체 기간 분석이 중요하면 Standard를 사용하며 필요하면 역할을 나누어 병행한다.

따라서 다음 문장은 **뜻은 통하지만 조금 축약된 표현**이다.

> `CloudFront Standard Access Log Telemetry는 느리지만, Real-time Log Telemetry는 수초 단위다.`

더 정확하게 말하면:

> **CloudFront의 Viewer Request에 대한 Log Telemetry에는 Standard Logging과 Real-time Access Logging이라는 서로 다른 Logging mechanism이 있고, Standard Logging은 일반적으로 Event 후 1시간 이내에 전달되지만 일부 Entry는 최대 24시간 지연될 수 있는 반면, Real-time Access Logging은 Kinesis Data Streams로 수초 내 전달된다.**

즉 `CloudFront라는 서비스 자체가 느리다/빠르다`가 아니라 **어떤 Telemetry mechanism을 선택했는지가 latency 특성을 크게 바꾼다.**

## 7. 왜 같은 서비스의 Telemetry인데 속도가 달라질 수 있는가?

같은 Resource의 같은 행위를 관찰하더라도 Telemetry mechanism마다 다음이 다를 수 있다.

- 생성 시점
- Buffering / Batching 여부
- Sampling 여부
- 기록 필드
- 집계 방식
- Delivery destination
- Delivery 보장 특성
- 비용
- 장기 보존 목적 여부

그래서:

```text
CloudFront가 느리다
```

가 아니라:

```text
CloudFront Standard Access Logging의 Delivery 특성이 느리다
CloudFront Real-time Access Logging은 수초 단위다
```

처럼 말해야 한다.

ALB도 같은 이유로:

```text
ALB는 5분짜리다
```

가 아니라:

```text
ALB Legacy S3 Access Logging은 5분 단위 Log file 발행 특성이 있다
ALB Vended Logs는 다른 Telemetry delivery mechanism이다
```

라고 구분해야 한다.

## 8. 현재 프로젝트의 구성요소를 이 개념에 매핑하면

| 프로젝트 구성요소 | 무엇인가? |
|---|---|
| DVWA | 관찰 대상 Application / Resource |
| DVWA `command.execution` 감사 Record | Source Log Telemetry |
| WAF Web ACL | 관찰 대상 Security Resource |
| WAF Request Log | Source Log Telemetry |
| ALB | 관찰 대상 Resource |
| ALB Access Log | Source Log Telemetry |
| CloudFront | 관찰 대상 Resource |
| CloudFront Standard / Real-time Access Log | 같은 Viewer Request를 다르게 제공하는 Log Telemetry mechanism |
| S3 | 경우에 따라 관찰 대상 Resource이기도 하고, Log Archive/Destination이기도 함 |
| CloudTrail | AWS API 활동을 기록하는 Audit Telemetry Service |
| CloudTrail Data Event | API Activity에 대한 Audit Log/Event Telemetry |
| CloudWatch Logs | Log Telemetry를 수집·저장·조회하는 Destination/Backend 서비스 |
| Kinesis Data Streams | Streaming Destination / Transport 계층 |
| SQS | Queue / Buffer / Retry를 담당하는 Transport 계층 |
| Lambda Forwarder | Telemetry 변환·필터·전달 Processing 계층 |
| Local Bridge | AWS에서 Local Wazuh까지 연결하는 Transport/Consumer 계층 |
| Wazuh | SIEM / Analysis Backend |
| Wazuh Rule | Telemetry를 평가하는 Detection Logic |
| Wazuh Alert | 원본 Telemetry를 Rule로 평가한 뒤 생성되는 Derived Detection Result |
| Shuffle | Alert 이후 대응을 Orchestrate하는 SOAR |

특히 아래를 혼동하지 않는다.

```text
SQS는 Telemetry가 아니다.
→ Telemetry를 운반·버퍼링하는 Queue다.

Wazuh는 Telemetry가 아니다.
→ Telemetry를 수집·검색·탐지하는 SIEM이다.

Wazuh Rule은 Telemetry가 아니다.
→ Telemetry를 판정하는 Logic이다.

Wazuh Alert는 원본 Source Telemetry 그 자체가 아니다.
→ Telemetry를 Rule로 평가한 결과 생성된 탐지 결과다.
```

## 9. 이 노트에서 앞으로 문장을 읽는 법

예를 들어:

> `ALB에 더 빠른 Telemetry가 있다.`

라는 문장은 엄밀히는:

> `ALB라는 동일 Resource에 대해 Legacy S3 Access Logging보다 SIEM용 저지연 관측에 더 적합할 가능성이 있는 다른 Logging/Telemetry delivery mechanism이 있다.`

라는 뜻으로 읽는다.

또:

> `Source별 최적 Telemetry를 선택한다.`

는:

> `각 Resource에서 어떤 Signal을 볼지, 어떤 Logging/Telemetry mechanism으로 생성할지, 어디로 전달할지, 그리고 그 데이터를 어떤 Route로 SIEM까지 운반할지를 함께 선택한다.`

는 뜻이다.

## 10. 한 줄 암기

> **Telemetry는 시스템이 자기 상태와 행위를 밖으로 말해주는 데이터이고, Logging mode는 그 말을 어떤 방식과 빈도로 내보낼지, Destination은 처음 어디에 받을지, Route는 그 데이터를 SIEM까지 어떻게 옮길지, SIEM은 도착한 데이터를 분석하는 곳이다.**

CloudFront에 적용하면:

```text
CloudFront Distribution
= 관찰 대상 Resource

Viewer Request Access Log
= Log Telemetry

Standard / Real-time
= Logging mechanism

CloudWatch Logs / S3 / Firehose / Kinesis
= Initial destination

Subscription / Lambda / SQS / Bridge
= SIEM transport

Wazuh
= Analysis backend / SIEM

Rule
= Detection logic

Alert
= Detection result
```

## 공식 근거

- [OpenTelemetry — Signals](https://opentelemetry.io/docs/concepts/signals/)
- [OpenTelemetry — What is OpenTelemetry?](https://opentelemetry.io/docs/what-is-opentelemetry/)
- [Microsoft Azure Well-Architected — Architecture strategies for designing a monitoring system](https://learn.microsoft.com/en-us/azure/well-architected/operational-excellence/observability)
- [Microsoft Azure Well-Architected — Build a monitoring system](https://learn.microsoft.com/en-us/azure/well-architected/design-guides/monitoring)
- [AWS Well-Architected — Implement application telemetry](https://docs.aws.amazon.com/wellarchitected/latest/framework/ops_observability_application_telemetry.html)
- [AWS Well-Architected — Implement observability](https://docs.aws.amazon.com/wellarchitected/latest/operational-excellence-pillar/implement-observability.html)
- [Amazon CloudFront — CloudFront and edge function logging](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/logging.html)
- [Amazon CloudFront — Standard logging reference](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/standard-logs-reference.html)
- [Amazon CloudFront — Use real-time access logs](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/real-time-logs.html)

## 11. A/B/C/D/E 지연 모델 정밀화 — Real-time Logs와 Kinesis

A/B/C/D/E는 서비스나 AWS 구성요소의 이름이 아니라 **두 상태 사이의 지연 구간**이다. 아래 CloudFront 예시는 Wazuh 입력까지의 A/B/C 경계에 집중하고, 전체 Event-to-Action E2E에는 D/E가 추가된다. 즉 `점(Node)`과 `선(Interval)`을 분리해서 이해한다.

```text
Viewer Request                         ← Point
      │
      │ A. Source 생성·집계 지연       ← Interval
      ▼
Real-time Log Record                  ← Point
      │
      │ B. Source-native Delivery 지연 ← Interval
      ▼
Kinesis Data Streams에서 Consumer가
Record를 읽을 수 있는 상태            ← Point
      │
      │ C. SIEM Transport 지연         ← Interval
      ▼
Wazuh 입력                            ← Point
```

### Kinesis는 B인가?

엄밀히는 **Kinesis 자체가 B는 아니다.** Kinesis는 B의 Destination이다.

이 노트에서 B를:

> `생성된 Record가 CloudWatch Logs, S3, EventBridge, Kinesis 등의 소비 가능한 AWS 목적지에 나타날 때까지`

로 정의했기 때문에, Kinesis의 경우에는 **CloudFront가 Record를 Kinesis로 보내고 Consumer가 읽을 수 있게 될 때까지가 B**다.

AWS는 Kinesis Data Streams에서 Record가 Stream에 들어간 뒤 Consumer가 검색할 수 있게 되기까지의 `put-to-get delay`가 일반적으로 1초 미만이라고 설명한다. 따라서 이 노트의 정의를 유지하면 그 내부 지연도 B의 일부로 보는 것이 가장 일관적이다.

즉 다음처럼 이해한다.

```text
[A]
Viewer Request
→ Real-time Log Record 생성

[B]
Real-time Log Record
→ CloudFront가 Kinesis로 전달
→ Kinesis 내부에서 Consumer-visible 상태가 됨

[C]
Consumer가 Record를 읽음
→ 필요 시 Lambda / SQS / Local Bridge
→ Wazuh 입력

[D]
Wazuh 입력
→ Decoder / Rule 평가
→ Alert 생성·Integratord 호출

[E]
Wazuh Alert
→ Shuffle 전달·Execution
→ Action terminal result
```

### 그러면 `Real-time Logging이 A를 빠르게 하고, Kinesis가 B를 빠르게 한다`고 말해도 되는가?

**직관적인 설명으로는 상당히 가깝지만, 공식 근거상 A/B 각각을 분리해서 수치화할 수는 없다.**

CloudFront 공식 문서가 공개하는 것은:

```text
Viewer Request
→ [A + B]
→ Kinesis에서 Real-time Log 사용 가능

전체: 요청 수신 후 수초 내
```

라는 End-to-End 성격의 수치다. AWS는 `A는 몇 ms, B는 몇 ms`처럼 내부 구간을 따로 공개하지 않는다.

따라서 발표나 보고서에서 가장 안전한 표현은:

> **CloudFront Real-time Logging은 요청으로부터 Log Record를 생성해 Kinesis Data Streams에서 사용할 수 있게 될 때까지의 A+B 전체를 수초 단위로 제공한다. Kinesis Data Streams 자체도 실시간 Streaming을 위해 설계되어 Record의 put-to-get 지연이 일반적으로 1초 미만이므로, B를 저지연으로 유지하는 데 적합한 Destination이다.**

이다.

더 쉽게 외우면:

> **Real-time Logging이 앞단 A+B를 수초 단위로 만들고, 그 안에서 Kinesis가 B의 저지연 Streaming Destination 역할을 한다.**

`Kinesis는 B를 짧게 하려고 만들어졌다`라고 표현하기보다는:

> **Kinesis는 실시간 Streaming을 위해 만들어졌기 때문에, 우리 모델에서 B를 짧게 유지하는 데 적합하다.**

라고 하는 것이 정확하다.

### Standard Logging과 비교

```text
CloudFront Standard Logging
Request
→ [A + B: 일반적으로 1시간 이내, 일부 Entry 최대 24시간]
→ Destination
→ [C]
→ Wazuh

CloudFront Real-time Logging
Request
→ [A + B: 수초 내]
→ Kinesis에서 Consumer-visible
→ [C]
→ Wazuh
```

핵심은 **Destination만 Kinesis로 바꾸면 Real-time이 되는 것이 아니라는 것**이다. Standard Logging의 A/B 특성이 이미 느리다면 뒤쪽 Destination이나 C만 빠르게 만들어도 앞단 지연은 남는다.

## 이 정밀화의 최종 암기

```text
A/B/C/D/E = 선(지연 구간)
Event / Log Record / Kinesis / Wazuh 입력 / Alert / Shuffle result = 점(상태·구성요소)

A = Event → Log Record
B = Log Record → AWS Destination에서 Consumer-visible
C = Consumer-visible → Wazuh 입력
D = Wazuh 입력 → Rule 평가·Alert 생성·Integratord 호출
E = Alert 전달 → Shuffle terminal Execution / Action result

전체 Event-to-Action E2E = A + B + C + D + E
```

- CloudFront Real-time Logs는 공식적으로 **요청 → Kinesis 전달까지 수초 내**.
- Kinesis Data Streams의 `put-to-get delay`는 일반적으로 **1초 미만**.
- 하지만 AWS가 A/B를 따로 수치화해 공개하지 않으므로 `A가 몇 초, B가 몇 초`라고 임의 분해하지 않는다.

### 추가 공식 근거

- [Amazon CloudFront — Use real-time access logs](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/real-time-logs.html)
- [Amazon Kinesis Data Streams — What is Amazon Kinesis Data Streams?](https://docs.aws.amazon.com/streams/latest/dev/introduction.html)

<!-- 8.19-MENTOR-SOURCE-BLOCK B011 END -->

<!-- 8.19-MENTOR-CONTEXT-BRIDGE CBR04 -->
> [!NOTE] 원문 후속 문맥
> B006 끝의 `아래 기존 5-Source 표`는 [[AWS 보안 Telemetry Route 비교#5개 Source를 전부 DVWA처럼 빠르게 Push할 수 있는가?]]를 가리킨다.  
> 같은 경고의 `뒤의 로그 Source × Telemetry × Route 비교 — 공식 문서 재검증`은 [[AWS 보안 Telemetry Route 비교#로그 Source × Telemetry × Route 비교 — 공식 문서 재검증]]을 가리킨다.

<!-- 8.19-MENTOR-SOURCE-BLOCK B006 START -->
## 로그 지연을 나눠서 봐야 하는 이유

`로그가 느리다`고 할 때는 하나의 지연만 있는 것이 아니다.

정확히는 다음 5개 지연 구간으로 나눠 보는 것이 좋다.

> [!NOTE]
> A/B/C/D/E는 AWS가 공식적으로 명명한 표준 구간이나 SLA가 아니라, 이 프로젝트에서 latency 원인을 분리하기 위해 정의한 분석 모델이다.

| 구간 | 의미 | 예시 | 우리가 줄일 수 있는가? |
|---|---|---|---|
| A. Source 생성·집계 지연 | 실제 Event가 발생한 뒤 Log/Event Record를 만들어내기까지의 시간 | VPC Flow Logs aggregation, 애플리케이션 감사 Record 작성 | 대개 직접 줄이기 어렵지만 더 빠른 Logging mechanism을 선택할 수 있음 |
| B. Source-native Delivery 지연 | 생성된 Record가 CloudWatch Logs, S3, EventBridge, Kinesis 등 AWS 소비 지점에서 사용 가능해지기까지의 시간 | CloudTrail → CloudWatch Logs/S3, CloudFront → Kinesis | 서비스가 지원하는 Delivery mechanism 선택으로 줄일 수 있는 경우가 있음 |
| C. SIEM Transport 지연 | AWS 소비 지점의 Event를 Wazuh 입력까지 전달하는 시간 | 10분 Poll 또는 Subscription → Lambda → SQS → Bridge → Wazuh | 프로젝트가 가장 직접적으로 줄일 수 있는 구간 |
| D. SIEM 분석·Alert 지연 | Wazuh 입력부터 Decoder/Rule 평가, Alert 생성, Integratord 호출까지의 시간 | Wazuh Decoder·Rule·Integratord | Rule·Decoder·처리 경로와 부하를 검증·최적화할 수 있음 |
| E. SOAR 전달·실행 지연 | Wazuh Alert부터 Shuffle terminal Execution / Action result까지의 시간 | Webhook 전달 → Workflow → Action | Workflow·Action·재시도·외부 API 경로를 검증·최적화할 수 있음 |

```text
실제 Event
   ↓
[A] Source 생성·집계
   ↓
Log/Event Record
   ↓
[B] AWS-native Delivery (필요한 경우)
   ↓
CloudWatch Logs / S3 / EventBridge / Kinesis / ...
   ↓
[C] Wazuh Transport
   ↓
Wazuh 입력
   ↓
[D] Decoder / Rule 평가·Alert 생성·Integratord
   ↓
Wazuh Alert
   ↓
[E] Shuffle 전달·Execution·Action result
   ↓
Shuffle terminal result
```

전체 Event-to-Action latency를 말하려면 `A + B + C + D + E`를 모두 포함해야 한다. A+B+C 또는 A+B+C+D만 측정하고 Shuffle까지 포함한 전체 E2E라고 부르지 않는다.

B는 항상 필요한 단계가 아니다.

Source가 Wazuh가 받을 수 있는 형식과 네트워크 경로로 Event를 직접 전달할 수 있다면 다음처럼 단축할 수 있다.

```text
Event
→ [A] Source가 Event 생성
→ Wazuh
```

즉 **A가 끝난 뒤 바로 Wazuh로 보내는 것 자체는 가능할 수 있다.**

다만 AWS 관리형 서비스는 일반적으로 임의의 SIEM Endpoint보다 CloudWatch Logs, S3, EventBridge, Kinesis, Firehose, Lambda 같은 AWS-native Destination을 먼저 제공하는 경우가 많다.

현재 프로젝트의 Wazuh는 로컬 환경이며 Internet Inbound Port를 열지 않는 보안 경계를 사용한다. 따라서 다음처럼 내구성 있는 AWS 중간 계층을 두는 것이 실용적이다.

```text
AWS Source
→ Event-driven AWS Destination
→ SQS 등 Buffer
→ Local Bridge
→ Wazuh
```

이 구조는 단순히 빠르게 보내기 위한 것만이 아니라 다음 역할도 가진다.

- 노트북/Wazuh가 꺼져 있어도 Event 보존
- 일시 장애 시 Retry
- DLQ를 통한 실패 격리
- 중복·순서 문제 통제
- AWS에서 로컬 Wazuh로 Internet Inbound를 열지 않아도 됨

따라서 목표는 무조건 Hop을 최소화하는 것이 아니라:

> **각 Source가 Event를 제공하는 즉시, 불필요한 Poll 대기를 제거하면서도 필요한 신뢰성·보안 경계를 유지해 Wazuh까지 전달하는 것**

으로 보는 것이 정확하다.

### 특히 구분할 것

```text
Telemetry 사용 가능 지연(A+B)
≠ SIEM Transport 지연(C)

Event-driven
≠ Telemetry 사용 가능 지연(A+B) 0

Push
≠ 무조건 Event 발생 즉시 Wazuh 도착

Poll 제거
= 주로 C 구간의 불필요한 Poll 대기 시간을 제거하는 것

전체 Event-to-Action E2E
= A + B + C + D + E
```

### 이후 서비스별 `최적 Route` 평가 기준

- Telemetry 사용 가능 지연(A+B)
- SIEM Transport 지연(C)
- 공식 지원 여부
- Event 유실·중복·순서 특성
- 장애 시 Buffer / Retry / DLQ 가능 여부
- 원본 로그 보존성
- 보안 경계
  - Wazuh Inbound 노출 여부
  - IAM 최소 권한
  - 민감정보 전달 범위
- Wazuh 연동 난이도와 안정성
- 구현·운영 복잡도
- 비용
- 해당 Source가 보안 분석에 제공하는 정보 가치
- 기존 Archive / Replay / Investigation 경로와의 역할 중복

`프로젝트 남은 일정`은 최적 Route의 기술적 평가 기준에서 제외한다.

> [!WARNING] SUPERSEDED
> 아래 기존 5-Source 표는 당시의 잠정 정리다. 최신 판정은 뒤의 `로그 Source × Telemetry × Route 비교 — 공식 문서 재검증`을 따른다.


<!-- 8.19-MENTOR-SOURCE-BLOCK B006 END -->
