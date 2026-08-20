---
type: learning-note
status: active
created: 2026-08-20
topic: AWS Security Telemetry
project: 3차 프로젝트
parent: "[[8.19 멘토님과 상담]]"
---

# AWS 보안 Telemetry Route 비교

> [!IMPORTANT]
> 기본 비교 단위는 `서비스`가 아니라 **Resource × Telemetry signal × Logging mechanism × Initial destination × SIEM Route**다.  
> 같은 AWS 서비스라도 Legacy/Vended, Standard/Real-time, Audit/Event Notification처럼 mechanism이 다르면 별도 행으로 본다.

## 출처와 판정 구분

| 표기 | 의미 |
|---|---|
| 공식 수치·정성 표현 | AWS 공식 문서가 명시한 내용 |
| 현재 Route | Terraform Repository와 현재 Runtime에서 확인된 As-built |
| 프로젝트 관측 | 이 프로젝트에서 직접 측정한 값. AWS 일반 보장값이 아님 |
| Target Candidate | 공식 지원과 설계 요구를 바탕으로 한 프로젝트 판단. 구현·Runtime 비교 전에는 최적 확정이 아님 |

`권장`, `최적`을 AWS 공식 권고처럼 쓰지 않는다. 미구현 후보에는 **우선 평가 후보**, **Target Candidate**, **Runtime 비교 필요**를 붙인다.

## Latency 용어

이 표의 핵심 열은:

> **Telemetry 사용 가능 지연 (A+B) = 실제 Event 발생부터 AWS의 Initial destination에서 Consumer가 Record를 사용할 수 있게 될 때까지**

다.

```text
A = Event → Record 생성·집계
B = Record → AWS Destination에서 Consumer-visible
C = Destination → Wazuh 입력
D = Wazuh 입력 → Alert / Integratord
E = Alert → Shuffle terminal result
```

AWS가 A와 B를 분리 공개하지 않으면 임의로 나누지 않는다. 프로젝트가 A+B+C+D를 합쳐 측정한 경우에는 해당 값을 이 열의 공식 A+B 값처럼 쓰지 않고 **하위 경로 총지연**으로 별도 표시한다.

---

# 프로젝트 5-Source와 대체 mechanism

| 서비스 / Telemetry mechanism | Telemetry 사용 가능 지연(A+B) / 공식 상태 | 현재 Route | 가장 빠른 공식 후보 | 프로젝트 판단 | 검증 상태 |
|---|---|---|---|---|---|
| **DVWA Custom Audit → CloudWatch Logs** | 공식 A+B 수치 미공개. 프로젝트가 측정한 값은 **A+B+C+D 합계**인 DVWA→Wazuh 하위 경로 총지연 `6.439 / 3.427 / 3.761초` | DVWA → CWL → Subscription → Lambda → SQS → Local Bridge → Wazuh | Application에서 Wazuh 직접 전송도 가능하지만 강결합·Inbound·Buffer 부재 | **현재 Route 유지 후보.** 속도·보존·보안 경계의 균형이 좋음 | Rule `100102` 무해 검증 N=3. Rule `100103` G4는 별도 미완료 |
| **AWS WAF Web ACL Logs → CloudWatch Logs** | 공식 정량 수치 미공개 | WAF → CWL → Wazuh `GetLogEvents` 10분 Poll 계열 | WAF → CWL → Subscription → Lambda/SQS → Bridge → Wazuh | **Event-driven 전환 우선 후보.** CWL 이후 Poll 대기 제거 효과가 큼 | Target Candidate, A+B 실측 필요 |
| **ALB Legacy Access Logs → S3** | 공식: 노드별 5분마다 Log file 발행 + eventual consistency | ALB → S3 → Wazuh S3 List/Get 10분 Poll | 같은 Legacy 유지 시 S3 `ObjectCreated` → SQS → Consumer → Wazuh | Archive·Replay에는 유효. 저지연 주 탐지 Source로는 제약이 큼 | As-built 확인, Event-driven Object route는 미완료 |
| **ALB Vended Logs → CloudWatch Logs / Firehose / S3** | 공식 정량 latency 미공개. CWL Live Tail로 실시간 관찰 가능하다고 설명 | 미사용 | ALB Vended Logs → CWL → Subscription → Lambda/SQS → Bridge → Wazuh | **저지연 SIEM 수집의 우선 평가 후보.** Legacy보다 실제 얼마나 빠른지는 Runtime 비교 전 확정 금지 | Target Candidate. latency·누락·중복·비용 검증 필요 |
| **CloudFront Standard Logging v2** | 공식: 일반적으로 Event 후 1시간 이내, 일부 Entry 최대 24시간 지연 | Standard v2 → S3 Archive + Wazuh용 CWL Destination → Poll 계열 | 같은 Standard를 유지하면 CWL/Firehose/S3 Delivery 후 Event-driven 소비 가능하지만 앞단 지연은 남음 | 저지연 Trigger보다 Evidence·Archive·Historical analysis 역할 | 현재 Terraform 적용. 저지연 Trigger로는 비채택 |
| **CloudFront Real-time Access Logs** | 공식: 요청 수신 후 수초 내 Kinesis 전달. Best-effort, 지연·누락 가능 | 미사용 | CloudFront Real-time → Kinesis → Consumer → SQS/Bridge → Wazuh | CloudFront 고유 Edge field가 수초 단위 대응에 필요할 때 **조건부 후보**. 비용·Sampling·Consumer 운영 부담 고려 | Target Candidate, 현재 Route 아님 |
| **CloudTrail S3 Data Event (`GetObject`) → CWL/S3** | 공식: API 호출 후 평균 약 5분, 보장값 아님 | CloudTrail → Security Log S3 → Wazuh S3 List/Get 10분 Poll | CloudTrail → CWL → Subscription → Lambda/SQS → Bridge → Wazuh | Transport Poll은 제거 가능하지만 Event availability 약 5분 특성은 남음. Confirmation/Audit에 적합 | As-built S3 확인. CWL Event-driven Target 미완료 |

## 이 표의 핵심

```text
DVWA
→ 확인된 3.427~6.439초는 A+B 공식값이 아니라
  DVWA Event부터 Wazuh Alert까지의 A+B+C+D 하위 경로 총지연

WAF
→ AWS Destination에 도착한 뒤 불필요한 Poll을 제거할 가치가 큼

ALB
→ `ALB=5분`이 아니라 Legacy S3 Logging이 5분 단위
→ Vended Logs는 우선 평가 후보이지만 정량 우월성은 Runtime 검증 전 확정 금지

CloudFront
→ Standard와 Real-time은 같은 Resource의 다른 Logging mechanism
→ Real-time은 저지연 상위호환이 아니라 비용·Sampling·Destination·운영 복잡도가 다른 선택지

CloudTrail
→ Event-driven Transport로 C를 줄일 수 있음
→ API Event가 Destination에 사용 가능해지는 A+B 평균 약 5분은 남음
```

---

# 공통 AWS 보안 Telemetry 참고표

| 서비스 / Telemetry mechanism | 공식 Telemetry 사용 가능 지연(A+B) 또는 해당 mechanism 지연 | 저지연 SIEM Route 후보 | 중요한 제한·용도 |
|---|---|---|---|
| **CloudWatch Logs Subscription Filter** | **원본 Source A+B와 별도:** CWL ingest 후 수신 Resource 전달은 보통 3분 미만 | CWL → Subscription → Lambda/Kinesis/Firehose → SIEM | 원래 Source A+B를 없애지 않음. Retry 가능한 오류는 최대 24시간 재시도 후 실패분 유실 가능. Throttle·AccessDenied 모니터링 필요 |
| **Lambda Function Logs → CloudWatch Logs** | 공식: 함수 호출 후 로그가 표시되기까지 **5~10분 걸릴 수 있음** | 일반 Route: Lambda → CWL → Subscription → SIEM | `real-time`이라고 단정하지 않음. 더 저지연이 필요하면 Lambda Logs API Extension을 별도 mechanism으로 검토 |
| **Lambda Logs API Extension** | 실행 환경에서 Telemetry stream을 Extension이 직접 구독하는 별도 mechanism | Lambda Extension → 외부/내부 Collector → SIEM | 일반 CWL 경로와 동일하지 않음. Extension 운영·실패·Backpressure 설계 필요 |
| **S3 Event Notifications / EventBridge Object Events** | 공식: 보통 수초, 때때로 1분 이상. At-least-once | S3 Event → SQS/EventBridge → Consumer → SIEM | `ObjectCreated/Deleted` 상태 Event. `GetObject` 접근 감사 Evidence를 대체하지 않음 |
| **S3 Server Access Logging** | 공식: 대부분 수시간 내, best-effort | Archive / Athena 중심 | 완전성·적시성 보장 없음. 즉시 탐지 Source로 부적합 |
| **S3 CloudTrail Data Events** | 평균 약 5분 계열, 보장값 아님 | CloudTrail → CWL → Subscription → SIEM | `GetObject/PutObject` API 감사. Data Event Selector·대상 Prefix가 활성화돼야 함 |
| **VPC Flow Logs → CWL** | 최대 집계 1분 또는 10분 + 집계 후 CWL 전달 지연. 공식 예시는 보통 약 5분, best-effort | `maxAggregationInterval=60` → CWL → Subscription → SIEM | 패킷 단위 실시간 로그가 아니라 Flow 집계. ENI·플랫폼 특성에 따라 집계 창 차이 |
| **VPC Flow Logs → S3** | 최대 집계 1/10분 + S3 전달 지연, best-effort | Archive / Athena | CWL Route보다 후행 분석 성격이 강함 |
| **Route 53 Public DNS Query Logs** | 공식 정성 표현: near real-time | Route 53 → CWL → Subscription → SIEM | Public Hosted Zone 질의용 |
| **Route 53 Resolver Query Logs** | 공식 정량 수치 미공개. CWL/S3/Firehose 지원 | Resolver → CWL → Subscription 또는 Firehose → SIEM | Resolver Cache 특성 때문에 반복 질의가 모두 동일하게 기록되지 않을 수 있음 |
| **EKS Control Plane / Audit Logs** | 공식: CWL에 수분 내 전달 | EKS → CWL → Subscription → SIEM | Kubernetes API/Audit 분석에 중요. 활성화한 Log type만 수집 |
| **API Gateway Access / Execution Logs** | 공식 정량 수치 미공개 | API Gateway → CWL → Subscription → SIEM | Access Log와 Execution Log의 정보·민감정보 범위가 다름. Data tracing 운영환경 주의 |
| **EC2 OS/Application Logs + CloudWatch Agent** | Agent Buffer/flush 설정 의존 | Agent → CWL → Subscription → SIEM | Source 고유 latency보다 Agent 설정 영향이 큼 |
| **RDS/Aurora Engine/Audit Logs → CWL** | 공식 정성 표현: continuously streams, 정량 미공개 | RDS/Aurora → CWL → Subscription → SIEM | Engine별 지원 로그와 Audit plugin 차이 확인 필요 |
| **ElastiCache Slow/Engine Logs** | 공식 정량 수치 미공개, Engine에서 주기적으로 전달 | ElastiCache → CWL/Firehose → SIEM | Slow Log buffer 길이·전달 주기 때문에 일부 Entry 누락 가능 |
| **NLB Legacy Access Logs → S3** | 공식: 노드별 5분마다 S3 Log file 발행, eventual consistency | S3 ObjectCreated → SQS → SIEM | TLS Listener의 TLS 요청 중심, best-effort |
| **NLB Vended Logs** | 공식 정량 latency 미공개. CWL/Firehose/S3 지원 | NLB Vended → CWL → Subscription → SIEM | **Legacy보다 빠르다고 확정하지 않음.** 우선 평가 후보이며 Runtime 비교 필요 |
| **GuardDuty 신규 Finding → EventBridge** | 공식 정성 표현: near real-time | GuardDuty → EventBridge → SQS/Lambda → SIEM/SOAR | 동일 Finding 후속 발생은 15분/1시간/6시간 집계 설정 영향 |
| **Security Hub Finding → EventBridge** | 공식 정성 표현: 신규/업데이트 Finding near real-time | Security Hub → EventBridge → SQS/Lambda → SIEM/SOAR | 최종 속도는 GuardDuty 등 Upstream Finding 생성 시간에 좌우 |
| **AWS Config Configuration Change** | 변경 후 수분 내 계열, EventBridge Delivery는 best-effort | Config → EventBridge → SQS/Lambda → SIEM | Configuration recording 범위·빈도 확인 필요 |
| **EFS API Activity** | 주로 CloudTrail API Event에 의존 → 약 5분 계열 | CloudTrail → CWL → Subscription → SIEM | File content read/write의 상세 File-level Access Log와 동일하지 않음 |

---

# Route 선택 기준

## 기술적 평가 기준

- Telemetry 사용 가능 지연(A+B)
- SIEM Transport 지연(C)
- 공식 지원 여부
- Event 유실·중복·순서 특성
- Buffer / Retry / DLQ
- 원본 보존·Replay
- Wazuh Inbound 노출 여부
- IAM 최소 권한
- 민감정보 전달 범위
- Wazuh Decoder·Rule 연동 안정성
- 구현·운영 복잡도
- 비용
- 보안 분석 정보 가치
- 기존 Archive / Investigation 경로와 역할 중복

**프로젝트 남은 일정은 기술적 최적 Route 평가 기준에 넣지 않는다.**

## 프로젝트 Scope 결정은 별도

기술적으로 더 유력한 후보가 있어도:

```text
구조 변경
→ Terraform / Delivery / Wazuh Input / Rule 변경
→ 중복·누락·장애복구 재검증
→ 기존 Runtime Evidence 재생성
```

이 필요하다. 프로젝트 후반에 이 재검증을 완료하지 못하면 As-built를 동결하고 Target Candidate로 분리한다. 이것은 기술적 최적성 판정과 일정·검증 Scope 결정을 섞지 않기 위한 조치다.

## 최종 원칙

1. 같은 Resource에 더 빠른 Logging mechanism이 있는지 먼저 비교한다.
2. 더 빠른 mechanism이 없으면 A+B는 받아들이고 C의 불필요한 Poll을 제거한다.
3. 가장 빠른 Route와 가장 좋은 Route는 다를 수 있다.
4. 현재 로컬 Wazuh에서는 다음 구조가 기본적으로 강하다.

```text
AWS-native Destination
→ Event-driven Forwarding
→ SQS Buffer / Retry / DLQ
→ Local Bridge Outbound
→ Wazuh
```

5. Archive/Poll은 실패 구조가 아니라 주 탐지 경로에서 **Evidence/Replay/Fallback** 역할로 낮춘다.

## 공식 근거

- [CloudWatch Logs — Subscriptions](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/Subscriptions.html)
- [AWS Lambda — Sending function logs to CloudWatch Logs](https://docs.aws.amazon.com/lambda/latest/dg/monitoring-cloudwatchlogs.html)
- [AWS Lambda — Logs API](https://docs.aws.amazon.com/lambda/latest/dg/runtimes-logs-api.html)
- [ALB — Legacy access logs](https://docs.aws.amazon.com/elasticloadbalancing/latest/application/load-balancer-access-logs.html)
- [ALB — CloudWatch Logs integration](https://docs.aws.amazon.com/elasticloadbalancing/latest/application/load-balancer-cloudwatch-logs.html)
- [CloudFront — Standard logging reference](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/standard-logs-reference.html)
- [CloudFront — Standard logging v2](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/standard-logging.html)
- [CloudFront — Real-time access logs](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/real-time-logs.html)
- [CloudTrail — Send events to CloudWatch Logs](https://docs.aws.amazon.com/awscloudtrail/latest/userguide/send-cloudtrail-events-to-cloudwatch-logs.html)
- [Amazon S3 — Logging options](https://docs.aws.amazon.com/AmazonS3/latest/userguide/logging-with-S3.html)
- [Amazon VPC — Flow log records](https://docs.aws.amazon.com/vpc/latest/userguide/flow-log-records.html)
- [Amazon EKS — Control plane logs](https://docs.aws.amazon.com/eks/latest/userguide/control-plane-logs.html)
