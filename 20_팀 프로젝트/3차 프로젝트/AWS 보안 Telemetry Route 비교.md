---
type: project-doc
status: active
created: "2026-08-20"
project: "3차 프로젝트"
project_moc: "[[00_3차프로젝트_목차]]"
---

> [!NOTE] 분해 문서 안내
> 원문은 `3a6b45ec37f9be01f41ddd66ae20511fe2264f9a`의 정정 완료 단일 노트에서 블록 단위로 이동했다. SOURCE-BLOCK 내부는 원문 그대로이며, 안내문과 링크만 신규 내용이다. 이 문서는 AWS 서비스별 Telemetry mechanism, 지연과 Wazuh 전달 Route를 비교한다.

# AWS 보안 Telemetry Route 비교

<!-- 8.19-MENTOR-CONTEXT-BRIDGE CBR05 -->
> [!NOTE] 원문 문맥 연결
> 먼저 잠정 5-Source 분석인 B007을 보존하고, 이어서 이를 대체한 최신 공식 재검증 B009를 배치한다.  
> B009의 `위의 잠정 5-Source 표`는 바로 앞 B007의 표를 가리킨다.

<!-- 8.19-MENTOR-SOURCE-BLOCK B007 START -->
## 5개 Source를 전부 DVWA처럼 빠르게 Push할 수 있는가?

핵심:

> **5개 Source 모두 Event-driven 전달로 바꾸는 것은 가능하지만, 모두 DVWA와 같은 속도로 전달할 수 있는 것은 아니다.**

Event-driven과 low-latency는 같은 말이 아님. Push로 줄일 수 있는 것은 주로 **우리 전달 계층의 Poll 지연**이고, 각 AWS Source가 원본 Log를 생성·전달하는 고유 지연은 그대로 남을 수 있음.

| Source | Event-driven 전달 | DVWA 수준 속도 | 이유 |
|---|---|---|---|
| DVWA | CloudWatch Logs Subscription → Lambda/SQS | 가능 | 애플리케이션이 Event를 즉시 기록하고 현재 경로도 구현됨 |
| WAF | WAF → CloudWatch Logs → Subscription | 근접 가능 | CloudWatch Logs에 들어온 뒤 Subscription으로 바로 전달 가능 |
| CloudTrail | CloudTrail → CloudWatch Logs → Subscription | 같은 속도는 어려움 | Event-driven 전달은 가능하지만 CloudTrail 자체 원본 전달 지연이 존재 |
| ALB | S3 Access Log 생성 → ObjectCreated → SQS | 같은 속도는 어려움 | Access Log Object 생성 자체가 수분 단위라 앞단 지연이 남음 |
| CloudFront | Real-time Logs → Kinesis 등 | 가능하지만 별도 구조 | 실시간 Log 기능은 가능하지만 별도 비용·구성·전달 특성이 있음 |

즉 최종 Target은 모든 Source를 억지로 동일 Transport에 태우는 것이 아니라:

```text
Source별 가장 적합한 Event-driven Transport
→ Wazuh에서 하나의 Incident/Correlation 흐름으로 통합
```

하는 것.

현재 Repository의 `WAZUH-PUSH-TRANSPORT-DESIGN.md`도 이미 이 방향에 가까움.

- 최종 범위는 CloudFront·WAF·ALB·DVWA·CloudTrail 5개 Source.
- 현재 Runtime 구현 범위는 DVWA 1개 Source.
- WAF/CloudTrail/ALB/CloudFront는 각 Source 특성에 맞는 Event-driven 경로를 Target으로 둠.
- 기존 CloudWatch/S3 원본과 Poll은 보존·재분석 경로로 유지.

즉 현재는 **Target Architecture 전체가 틀린 것이 아니라 DVWA부터 먼저 구현된 과도기**로 보는 편이 맞음.


<!-- 8.19-MENTOR-SOURCE-BLOCK B007 END -->

<!-- 8.19-MENTOR-SOURCE-BLOCK B009 START -->
# 로그 Source × Telemetry × Route 비교 — 공식 문서 재검증

> 이 섹션이 위의 **잠정 5-Source 표를 대체하는 최신 판정**이다.  
> 기본 단위는 `서비스`가 아니라 **서비스 × Telemetry/로그 종류 × 전달 방식**이다. 같은 AWS 서비스라도 Standard/Real-time, Legacy/Vended, CloudTrail/Event Notification처럼 로그 시스템이 다르면 별도 행으로 본다.

## 출처와 판정 구분

| 구분 | 이 섹션에서의 취급 |
|---|---|
| 공식 상태·latency | AWS 공식 문서가 명시한 수치 또는 정성 표현 |
| 현재 Route·Runtime 상태 | Terraform Repository와 Runtime Evidence에서 확인된 As-built |
| 프로젝트 판단 | 공식 사실과 Runtime을 바탕으로 한 설계 해석. 미구현 항목은 Target Candidate로 표시 |

`권장`, `최적`을 AWS 공식 권고처럼 쓰지 않는다. 구현·비교 검증 전 후보에는 `우선 평가 후보`, `Target Candidate`, `Runtime 비교 필요`를 사용한다.

## Latency 표기 규칙

- **공식 수치**: AWS가 분/초 단위 값을 직접 명시한 경우.
- **공식 정성 표현**: `real-time`, `near real-time`, `within a few minutes`, `continuously streams`처럼 AWS가 성격은 명시했지만 정확한 숫자는 공개하지 않은 경우.
- **공식 수치 미공개**: 공식 문서에서 이벤트별 전달 시간을 확인할 수 없는 경우. 임의 추정하지 않음.
- **프로젝트 관측**: 이 프로젝트 Runtime에서 직접 측정한 값. AWS의 SLA나 일반 보장값으로 확대하지 않음.

## 프로젝트 5-Source와 대체 Telemetry

| 서비스 / Telemetry mechanism | Telemetry 사용 가능 지연 (Event → AWS 소비 지점, A+B) / 공식 상태 | 현재 프로젝트 Route | 가능한 가장 빠른 공식 후보 | 프로젝트 판단 / Target Candidate | 검증 상태 |
|---|---|---|---|---|---|
| **DVWA Custom Audit → CloudWatch Logs** | **공식 A+B 수치 미공개. 프로젝트 하위 경로 관측:** DVWA Event → Wazuh Rule `100102` Alert, N=3, `6.439 / 3.427 / 3.761초`, 누락 0. 이는 A+B+C+D 합계이며 Shuffle(E)은 포함하지 않음 | DVWA → CloudWatch Logs → Subscription → Lambda Allowlist → SQS → Local Bridge → Wazuh | 애플리케이션이 Wazuh로 직접 전송하도록 만들 수도 있으나 강결합·Inbound·Buffer 부재 문제가 생김 | **현재 Route 유지 후보.** 속도·보존·보안 경계의 균형이 좋음 | Evidence: `[[20_팀 프로젝트/3차 프로젝트/일일 로그/RAW/2026-08-17_RAW]]`. 구간별 측정·Clock skew·SHA-256은 이 노트에 별도 기록되지 않음 |
| **AWS WAF Web ACL Logs** | **공식 수치 미공개.** 요청별 로그를 CloudWatch Logs/S3/Firehose로 전송 가능 | WAF → CloudWatch Logs → Wazuh `GetLogEvents` 10분 Poll | WAF → CloudWatch Logs → Subscription → Lambda → SQS → Bridge → Wazuh | **CWL Subscription 기반 Event-driven 전환 후보.** 장기 보존이 필요하면 별도 Archive 유지 | Poll 대기 제거 효과 큼, A+B 실측 필요 |
| **ALB Legacy Access Logs → S3** | **공식 수치:** 노드별 5분마다 Log file 게시 + eventual consistency | ALB → S3 → Wazuh S3 List/Get 10분 Poll | 같은 Legacy를 유지한다면 S3 `ObjectCreated` → SQS → Bridge → Wazuh | Archive·Replay에는 유효. 저지연 주 탐지 Source로는 제약이 크며 Vended Logs와 Runtime 비교가 필요 | `ALB=5분 고정`은 Legacy에만 해당 |
| **ALB Vended Access/Connection/Health Logs** | **공식 정성 표현:** CloudWatch Logs에서 Live Tail로 관찰 가능. 이벤트별 정량 latency·상한·SLA는 미공개 | 현재 미사용 | ALB Vended Logs → CloudWatch Logs → Subscription → Lambda → SQS → Bridge → Wazuh | **ALB 저지연 SIEM 수집을 위한 우선 평가 후보.** Legacy S3 5분 파일 제약을 피할 가능성은 있지만 실제 latency·누락·중복·비용은 Runtime 비교 전 확정 금지 | Target Candidate / Runtime 비교 필요 |
| **CloudFront Standard Logs (v2/legacy)** | **공식 수치:** 일반적으로 이벤트 후 1시간 이내, 일부 항목은 최대 24시간 지연 가능 | 현재 CloudFront CloudWatch Logs → Wazuh `GetLogEvents` Poll 계열 | 같은 Standard를 유지하면 CWL/Firehose 직접 전달 후 Event-driven 소비 가능하지만 **Standard의 A+B 지연은 남음** | 저지연 Trigger보다 Evidence/Archive/Historical analysis 용도 | Destination을 바꿔도 Standard의 A+B 지연은 사라지지 않음 |
| **CloudFront Real-time Access Logs** | **공식 수치:** 요청 수신 후 수초 내 Kinesis Data Streams 전달. Best-effort이며 드물게 지연/누락 가능 | Native Real-time Logs는 현재 주 경로가 아님 | CloudFront Real-time Logs → Kinesis → Consumer/Lambda → SQS → Bridge → Wazuh | **CloudFront 고유 필드가 저지연 탐지에 필요할 때의 조건부 후보.** 비용·Sampling·Consumer 운영·WAF 중복을 비교해야 함 | Target Candidate / Runtime 비교 필요 |
| **CloudTrail S3 Data Event (`GetObject`)** | **공식 수치:** API 호출 후 CloudWatch Logs/S3에서 사용 가능해지기까지 평균 약 5분(A+B), 보장값 아님 | CloudTrail → Security Log S3 → Wazuh S3 List/Get 10분 Poll | CloudTrail → CloudWatch Logs → Subscription → Lambda → SQS → Bridge → Wazuh | CWL Event-driven은 C의 Poll 대기를 줄이는 후보이고 Trail S3는 Audit/Archive로 유지. A+B 평균 약 5분은 남음 | `GetObject` Confirmation에는 여전히 유효 |

### 프로젝트 표에서 얻는 핵심

```text
DVWA/WAF
→ Source가 Log를 내놓는 즉시 Event-driven으로 Wazuh에 보낼 가치가 큼

ALB
→ `ALB=5분`이 아니라 Legacy S3 Logging이 5분 단위임
→ Vended Logs는 저지연 SIEM 수집의 우선 평가 후보지만 정량 우월성은 Runtime 검증 전 확정하지 않음

CloudFront
→ 같은 Resource와 Viewer Request 활동을 관찰하지만 Standard Logging과 Real-time Logging은 서로 다른 Telemetry mechanism·Delivery path·A+B 지연을 가짐

CloudTrail
→ C의 Transport는 Event-driven으로 개선 가능
→ CloudTrail Trail에서 API Event가 AWS 소비 지점에 사용 가능해지기까지의 A+B 평균 약 5분은 남음
```

따라서 앞으로 `ALB는 5분`, `CloudFront는 1시간`처럼 **서비스 이름만으로 latency를 말하지 않는다.** 반드시 어떤 Telemetry인지 같이 말한다.

## 자주 쓰이는 AWS 보안 Telemetry의 사용 가능 지연(A+B) 참고표

| 서비스 / Telemetry mechanism | 공식 Telemetry 사용 가능 지연(A+B) 또는 해당 mechanism 지연 | 저지연 SIEM Route 후보 | 중요한 제한 / 용도 |
|---|---|---|---|
| **CloudWatch Logs Subscription Filter** | **원본 Source A+B와 별도:** CloudWatch Logs ingest 후 수신 Resource 전달은 일반적으로 3분 미만 | CWL → Subscription → Lambda/Kinesis/Firehose → SIEM | 원래 Source의 A+B 지연을 없애지 않고 CWL 이후 Poll 대기를 줄임. Retry 가능한 오류는 최대 24시간 재시도 후 실패분이 유실될 수 있으므로 Throttle·AccessDenied·중복·실패를 모니터링해야 함 |
| **S3 Event Notifications / EventBridge Object Events** | **공식 수치:** 보통 수초, 때때로 1분 이상. At-least-once | S3 Event → EventBridge 또는 SQS → Wazuh 수집 계층 | `ObjectCreated/Deleted` 등 상태 Event용. **GetObject 접근 감사 로그를 대체하지 않음** |
| **S3 Server Access Logs** | **공식 수치:** 대부분 수시간 내, best-effort. 완전성·적시성 보장 없음 | 실시간 관제용으로 비추천; S3/CWL Archive·분석 | 요청 성격 파악/사후 분석용. 중요한 즉시 탐지 Source로 부적합 |
| **S3 CloudTrail Data Events** | **공식 수치:** 약 5분 계열 | CloudTrail → CWL → Subscription → SIEM | `GetObject`, `PutObject` 등 API 감사. 실시간보다 Confirmation/Audit에 강함 |
| **VPC Flow Logs → CloudWatch Logs** | **공식 수치:** 최대 집계 1분 또는 10분 + 집계 후 CWL 약 5분. Best-effort | `maxAggregationInterval=1m` → CWL → Subscription → SIEM | Nitro ENI는 1분 이하 집계. 패킷 단위 실시간 로그가 아니라 Flow 집계임 |
| **VPC Flow Logs → S3** | **공식 수치:** 최대 집계 1/10분 + S3 약 10분, best-effort | 실시간보다 Archive/Athena | CWL보다 지연 큼 |
| **Route 53 Public DNS Query Logs** | **공식 정성 표현:** CloudWatch Logs에서 near real-time 조회 | Route 53 → CWL → Subscription → SIEM | Public Hosted Zone 질의 분석에 유용 |
| **Route 53 Resolver Query Logs** | **공식 수치 미공개.** CWL/S3/Firehose 지원, AWS는 S3가 일반적으로 더 높은 latency라고 명시 | Resolver → CWL → Subscription 또는 Firehose → SIEM | Resolver cache에서 응답한 반복 질의는 모두 기록되지 않음 |
| **EKS Control Plane / Audit Logs** | **공식 수치:** CloudWatch Logs에 수분 내 전달 | EKS → CWL → Subscription → SIEM | Kubernetes API/Audit 분석에 중요 |
| **API Gateway Access/Execution Logs** | **공식 수치 미공개.** CloudWatch Logs 직접 기록 | API Gateway → CWL → Subscription → SIEM | 요청 ID, Source IP, 응답 상태 등. Data tracing은 민감정보 위험 때문에 운영환경 주의 |
| **Lambda Function Logs → CloudWatch Logs** | **공식 수치:** 함수 호출 후 로그가 표시되기까지 5~10분 걸릴 수 있음 | Lambda → CWL → Subscription → SIEM | 일반 CWL 경로를 real-time이라고 단정하지 않음. 더 저지연이 필요하면 Lambda Logs API Extension을 별도 mechanism으로 검토 |
| **Lambda Logs API Extension** | 실행 환경에서 Telemetry stream을 Extension이 직접 구독하는 별도 mechanism | Lambda Extension → Collector → SIEM | 일반 CWL 경로와 동일하지 않으며 Extension 운영·실패·Backpressure 설계가 필요 |
| **EC2 OS/Application Logs + CloudWatch Agent** | **설정 의존.** Agent Buffer/flush 설정에 따라 달라짐; 구형 Logs Agent의 기본 batch buffer는 5초 | EC2 → CloudWatch Agent → CWL → Subscription → SIEM | 서비스 고유 지연보다 Agent 설정 영향이 큼 |
| **RDS/Aurora DB Logs** | **공식 정성 표현:** RDS가 Log record를 CloudWatch Logs로 continuously streams, real-time 분석 가능. 정량 미공개 | RDS/Aurora → CWL → Subscription → SIEM | Engine마다 Audit/Error/General/Slow Query 등 지원 로그가 다름 |
| **ElastiCache Redis/Valkey Slow/Engine Logs** | **공식 수치 미공개.** Slow Log entry는 엔진에서 주기적으로 가져와 전달 | ElastiCache → CWL 또는 Firehose → SIEM | Slow Log는 `slowlog-max-len` 등에 따라 일부 Entry가 목적지에 도착하지 않을 수 있음 |
| **NLB Legacy Access Logs** | **공식 수치:** 노드별 5분마다 S3 Log file 게시, eventual consistency | 같은 Legacy라면 S3 ObjectCreated → SQS → SIEM | TLS Listener의 TLS 요청만 기록, best-effort |
| **NLB Vended Access Logs** | **공식 수치 미공개.** CWL/Firehose/S3 직접 전달 지원 | NLB Vended → CWL → Subscription → SIEM | 저지연 수집의 우선 평가 후보이지만 Legacy보다 빠르다고 확정하지 않음. Runtime 비교 필요 |
| **GuardDuty 신규 Finding → EventBridge** | **공식 정성 표현:** near real-time | GuardDuty → EventBridge → SQS/Lambda → SIEM/SOAR | 동일 Finding의 후속 발생은 설정에 따라 15분/1시간/6시간 집계 가능 |
| **Security Hub Finding → EventBridge** | **공식 정성 표현:** 신규/업데이트 Finding을 near real-time EventBridge 전송 | Security Hub → EventBridge → SQS/Lambda → SIEM/SOAR | 최종 속도는 GuardDuty 등 **Upstream Finding 생성 시간**에도 좌우됨 |
| **AWS Config Configuration Item Change** | **공식 정성/수치:** Configuration change notification은 변경 후 수분 내. Continuous recording의 CI는 사용 가능해지는 즉시 기록되는 것으로 설명됨 | Config → EventBridge → SQS/Lambda → SIEM | Config service event는 EventBridge로 직접 전송되며 delivery type은 best-effort |
| **EFS API Activity** | 별도 File-level Access Log가 아니라 주로 **CloudTrail API Event**에 의존 → 약 5분 계열 | CloudTrail → CWL → Subscription → SIEM | EFS 파일 내용 read/write 자체를 CloudTrail API 감사처럼 볼 수 있는 구조는 아님. Mount helper 로컬 로그는 별도 |

## Route 선택의 최종 원칙

1. **같은 Resource에 더 저지연일 가능성이 있는 다른 Telemetry mechanism이 있으면 먼저 비교한다.**
   - ALB Legacy S3 vs ALB Vended Logs
   - CloudFront Standard vs CloudFront Real-time
   - S3 Server Access Logs vs CloudTrail Data Events vs S3 Event Notifications
2. 더 저지연인 mechanism이 없거나 우월성이 검증되지 않았다면 **공식 A+B 특성은 받아들이고, C 구간의 불필요한 Poll을 제거한다.**
   - 대표적으로 CloudTrail.
3. `가장 빠른 Route`와 `가장 좋은 Route`는 다를 수 있다.
   - 직접 Wazuh 전송이 몇 Hop 더 짧더라도 Local Wazuh Inbound 노출, 재시도, Buffer 부재가 생기면 최적이 아닐 수 있음.
4. 현재 로컬 Wazuh 구조에서는 다음 형태가 기본적으로 강함.

```text
빠른 AWS-native Source/Destination
→ Event-driven Forwarding
→ SQS Buffer / Retry / DLQ
→ Local Bridge (Outbound)
→ Wazuh
```

5. Archive/Poll은 없애야 할 실패 구조가 아니라 **주 탐지 경로에서 보조 Evidence/Replay/사후 분석 경로로 역할을 낮추는 것**이 핵심이다.

## 공식 확인 근거

- AWS CloudTrail — *Sending events to CloudWatch Logs*, *Getting and viewing your CloudTrail log files*
- Elastic Load Balancing — *Access logs for your Application Load Balancer*, *CloudWatch Logs for your Application Load Balancer*
- Amazon CloudFront — *Standard logging reference*, *Use real-time access logs*
- AWS WAF — *Logging AWS WAF traffic*
- Amazon VPC — *Flow log records*
- Amazon S3 — *Amazon S3 Event Notifications*, *Logging requests with server access logging*, *Logging options for Amazon S3*
- Amazon Route 53 — *Public DNS query logging*, *Resolver query logging*
- Amazon EKS — *Send control plane logs to CloudWatch Logs*
- AWS Lambda — *Working with Lambda function logs*
- Amazon RDS — *Publishing database logs to Amazon CloudWatch Logs*
- Amazon ElastiCache — *Log delivery*
- Amazon GuardDuty — *Processing GuardDuty findings with Amazon EventBridge*
- AWS Security Hub — *Using EventBridge for automated response and remediation*
- AWS Config — *How AWS Config Works*, *AWS Config events*

---


<!-- 8.19-MENTOR-SOURCE-BLOCK B009 END -->
