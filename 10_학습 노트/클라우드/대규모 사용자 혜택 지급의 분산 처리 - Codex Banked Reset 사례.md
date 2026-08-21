---
type: concept
status: draft
created: 2026-08-22
topic: 대규모 사용자 혜택 지급, 분산 처리, 점진적 롤아웃
parent_moc: "[[10_학습 노트/클라우드/00_클라우드_목차]]"
source: https://x.com/thsottiaux/status/2090766694897619318
reviewed_on: 2026-08-22
---

# 대규모 사용자 혜택 지급의 분산 처리 - Codex Banked Reset 사례

> 수백만 사용자에게 같은 혜택을 지급하는 작업은 단순한 `+1` 갱신이 아니라, **대상 선정·분할 처리·중복 방지·재시도·감사·전파·최종 대사(reconciliation)**까지 포함하는 분산 시스템 문제로 볼 수 있다.

> [!warning] 사례와 일반화의 경계
> 2026-08-21 Tibo Sottiaux가 Codex 활성 사용자 2천만 명을 언급하며 Codex/ChatGPT Work 사용자에게 `banked reset` 1회를 당일 중 지급한다고 공개했다.  
> **OpenAI 내부 구현은 공개되지 않았다.** 아래의 Queue, Worker, DynamoDB, EventBridge 등의 구조는 실제 OpenAI 아키텍처를 설명하는 것이 아니라, 이 사례를 바탕으로 일반적인 클라우드·분산 시스템 설계를 학습하기 위한 참조 모델이다.

## 1. 왜 그냥 모든 계정에 `reset += 1`을 하지 않는가

대상 계정이 매우 많아지면 단순한 대량 갱신도 운영 위험이 된다.

- 같은 시점에 Write가 몰리면 DB·Entitlement Service에 부하가 집중될 수 있다.
- 일부 계정만 실패했을 때 전체 작업을 처음부터 다시 돌리면 중복 지급 위험이 생긴다.
- 혜택 지급 사실을 Usage Service, Cache, 다른 Region, Client UI까지 전파해야 할 수 있다.
- 정지·탈퇴·부정 사용 플래그·플랜 차이 등 대상 정책을 적용해야 할 수 있다.
- 나중에 `누가 / 어떤 캠페인으로 / 언제 / 무엇을 받았는가`를 감사할 수 있어야 한다.
- 운영자가 잘못된 대상을 지정하거나 잘못된 수량을 지급했을 때 Blast Radius가 매우 크다.

따라서 핵심은 **빠르게 쓰는 것보다, 누락과 중복 없이 안전하게 완료 여부를 증명하는 것**이다.

## 2. 개념적 처리 흐름

```text
[Campaign 생성]
      ↓
[대상 사용자 Snapshot]
      ↓
[Canary / Batch / Shard 분할]
      ↓
[Queue]
      ↓
[Worker Pool]
      ↓
[Idempotent Grant]
      ↓
[Entitlement + Audit Ledger]
      ↓
[Event / Cache Invalidation / Replica 전파]
      ↓
[Usage API / Client UI]
      ↓
[Reconciliation]
```

이 구조에서 사용자가 혜택을 보는 시점이 다른 것은 반드시 `계정마다 지급 버튼을 따로 눌렀다`는 뜻이 아니다.

예를 들어 다음 세 경우는 사용자 화면에서는 모두 순차 지급처럼 보일 수 있다.

1. 실제 Grant 작업 자체가 Batch/Queue로 순차 처리됨.
2. Grant는 끝났지만 Region·Cache·Replica 전파가 지연됨.
3. 서버 반영은 끝났지만 Client가 다음 Refresh까지 이전 값을 보여줌.

즉 **순차 지급과 순차 표시를 구분해야 한다.**

## 3. 핵심 개념

### Entitlement

사용자가 특정 기능·용량·혜택을 사용할 권리 또는 할당량을 의미한다.

이번 사례의 `banked reset 1회`를 추상화하면 다음과 같은 Entitlement 변경으로 볼 수 있다.

```text
account A
banked_reset: 0 → 1
```

하지만 운영 시스템에서는 단순 숫자 하나보다 **어떤 이벤트 때문에 증가했는지**를 추적할 수 있어야 한다.

### 멱등성(Idempotency)

같은 작업을 여러 번 실행해도 최종 결과가 한 번 실행한 것과 같아야 한다.

위험한 방식:

```text
retry 1 → reset +1
retry 2 → reset +1
retry 3 → reset +1

결과: +3
```

안전한 방식의 개념:

```text
idempotency_key = campaign_id + account_id

이미 이 key로 지급됨?
YES → 성공으로 간주하고 종료
NO  → Grant 기록 + Entitlement 변경
```

분산 시스템에서는 Network Timeout 때문에 **서버는 성공했지만 Worker는 실패로 인식하는 상황**이 생길 수 있다. 이때 재시도를 안전하게 만들기 위해 멱등성이 필요하다.

> [!important]
> `Exactly once`를 네트워크 전송 자체가 완벽히 보장한다고 가정하기보다, 실제 애플리케이션에서는 **At-least-once 전달 + Idempotency/Deduplication**으로 의미상 한 번만 처리되게 만드는 경우가 많다.

### Batch와 Sharding

전체 대상을 한 번에 처리하지 않고 작은 단위로 나눈다.

```text
5,000,000 accounts
→ 10,000 accounts × 500 batches
```

장점:

- Write Burst 완화
- 실패 범위 축소
- 특정 Batch만 재시도 가능
- 진행률 측정 가능
- Canary → 점진 확대 가능

### Queue와 Backpressure

Producer가 처리 요청을 빠르게 생성해도 Consumer가 감당 가능한 속도로 가져가도록 완충한다.

```text
Grant Controller
    ↓ 빠르게 생성
   Queue
    ↓ Worker 처리량만큼 소비
Worker Pool
```

DB가 느려지면 Worker 동시성을 낮추거나 Queue에 요청을 쌓아 **Downstream이 무너지는 것을 방지**할 수 있다.

### Retry와 DLQ

일시적인 네트워크 오류나 서비스 장애는 재시도로 복구할 수 있다.

반복 실패한 메시지는 Dead Letter Queue(DLQ)로 보내 별도로 조사한다.

```text
SUCCESS → 완료
RETRYABLE ERROR → Backoff 후 재시도
PERMANENT ERROR → DLQ
```

DLQ가 존재하는 것만으로 충분하지 않다. **DLQ 적재량에 대한 Alert와 재처리 절차**가 있어야 한다.

### 최종적 일관성(Eventual Consistency)

원본 데이터는 이미 바뀌었지만 모든 조회 지점에서 즉시 같은 값이 보장되지 않을 수 있다.

```text
Entitlement DB     banked_reset = 1
Usage API Cache    banked_reset = 0   ← 아직 이전 값
Mobile Client      banked_reset = 0   ← Refresh 전
```

이 경우 사용자는 `아직 지급되지 않았다`고 느끼지만 실제 Grant 자체는 이미 끝났을 수 있다.

### Reconciliation

대규모 작업은 `Job이 끝났다`는 신호만 믿지 않고 **기대한 결과와 실제 결과를 다시 맞춘다.**

예:

```text
Target accounts : 4,821,331
Succeeded       : 4,817,902
Pending         :     2,901
Failed          :       528
Duplicate skip  :         0
```

최종 완료 조건은 단순히 Worker가 멈춘 것이 아니라, 대상 집합과 결과가 대사되어 **누락 계정을 설명할 수 있는 상태**여야 한다.

## 4. 점진적 롤아웃과 Blast Radius

대규모 Entitlement 변경은 잘못되면 피해 범위가 매우 크다.

예를 들어 코드 버그로 `+1` 대신 `+10`이 적용되거나, 주간 Reset Timer까지 의도치 않게 변경되면 전체 사용자에게 즉시 영향을 줄 수 있다.

따라서 다음과 같은 점진적 롤아웃을 사용할 수 있다.

```text
Internal/Test accounts
        ↓
0.1%
        ↓
1%
        ↓
10%
        ↓
50%
        ↓
100%
```

각 단계에서 오류율·Latency·중복 지급·DB 부하·사용자 문의 등을 보고 다음 단계로 확대한다.

이때 필요한 운영 장치:

- Kill Switch
- Batch Pause/Resume
- Canary Group
- Rate Limit / Worker Concurrency 제어
- 자동 Rollback 또는 추가 지급 중단
- 실시간 Metric과 Alert

## 5. 보안 관점에서 필요한 통제

대규모 혜택 지급 API는 공격자에게도 가치가 큰 기능이다.

### 최소 권한

Grant Worker는 필요한 Entitlement만 수정할 수 있어야 한다.

```text
허용: banked_reset grant
불필요: 계정 삭제, 결제 정보 수정, 관리자 권한 변경
```

### 감사 로그

최소한 다음을 추적할 수 있어야 한다.

```text
campaign_id
account_id
requested_at
grant_type
quantity
result
worker/request id
granted_at
```

### Replay 방지

동일 Campaign Event를 다시 보내도 같은 혜택이 반복 지급되지 않도록 Idempotency Key 또는 Unique Constraint를 둔다.

### 대상 집합 검증

운영자의 잘못된 Query 하나가 전 계정에 영향을 줄 수 있으므로 다음 같은 절차가 유효하다.

```text
Target Query
→ 예상 대상 수 확인
→ Dry Run
→ Sample 검증
→ 승인
→ Canary
→ 전체 Rollout
```

### 역할 분리

고위험 운영이라면 Campaign 생성, 승인, 실행 권한을 분리하는 것도 고려할 수 있다.

## 6. AWS로 설계한다면 - 참조 아키텍처

> 아래는 OpenAI의 실제 구현이 아니라 AWS 서비스로 같은 문제를 설계하는 예시다.

```text
EventBridge / 운영 Trigger
          ↓
Step Functions
  - 대상 Snapshot
  - Canary
  - Batch 진행 상태
          ↓
SQS
          ↓
Lambda 또는 ECS Worker
          ↓
DynamoDB / Entitlement Service
  - Conditional Write
  - Idempotency Record
          ↓
EventBridge 또는 Event Stream
          ↓
Usage Service / Cache Invalidation
          ↓
Client

실패 메시지 → SQS DLQ
운영 지표   → CloudWatch
```

DynamoDB를 사용한다면 개념적으로 다음과 같은 Unique Grant Record를 둘 수 있다.

```text
PK = CAMPAIGN#CODEX_20M_RESET
SK = ACCOUNT#12345
```

그리고 `attribute_not_exists(PK/SK)` 같은 조건을 이용해 이미 성공한 지급을 다시 적용하지 않도록 설계할 수 있다.

Entitlement 변경과 Grant Ledger 기록이 반드시 함께 성공해야 한다면 `TransactWriteItems` 같은 트랜잭션 단위를 검토할 수 있다.

## 7. 장애 시나리오와 방어 설계

| 장애/실수 | 사용자에게 보이는 현상 | 방어 설계 |
|---|---|---|
| Worker Timeout 후 재시도 | Reset 중복 지급 가능 | Idempotency / Deduplication |
| 일부 Batch 실패 | 특정 사용자만 못 받음 | Retry + DLQ + Reconciliation |
| Cache 갱신 지연 | 받은 사람과 못 받은 사람이 섞여 보임 | Cache invalidation + TTL + 상태 구분 |
| DB 처리량 초과 | 전체 Rollout 지연 | Queue + Backpressure + Concurrency 제어 |
| 잘못된 대상 Query | 비대상 계정에 지급 | Snapshot + Dry Run + Approval + Canary |
| 잘못된 Grant 수량 | 대규모 과지급 | Canary + Kill Switch + Validation |
| DLQ 방치 | 일부 계정 영구 누락 | DLQ Alert + 재처리 Runbook |
| Region/Replica 지연 | 지역별 표시 시간 차이 | Replication 관측 + Eventual Consistency 고려 |

## 8. Runtime Evidence 관점

대규모 비동기 작업에서는 다음을 구분해야 한다.

```text
운영자가 버튼을 눌렀다
≠
Campaign이 생성됐다
≠
모든 메시지가 처리됐다
≠
모든 Entitlement가 반영됐다
≠
모든 Cache/Replica에 전파됐다
≠
사용자가 UI에서 확인했다
```

따라서 Evidence도 계층별로 나누는 편이 좋다.

### Control-plane Evidence

- Campaign 생성 기록
- 실행 승인
- 대상 수
- Rollout 시작/종료 시각

### Processing Evidence

- Queue 처리량
- Worker 성공/실패
- Retry/DLQ
- Grant Ledger
- Entitlement DB 변경

### User-plane Evidence

- Usage API 반환값
- 실제 Client UI의 `banked reset available`

> [!important]
> **Source/설정/Job 존재와 실제 End-to-End 완료는 다르다.**  
> 이 원리는 현재 프로젝트에서 Rule·Integrator·Webhook 존재만으로 Wazuh→Shuffle Runtime 연동 완료를 선언하지 않고 실제 Alert↔Execution Evidence를 확인하는 것과 같은 사고방식이다.

## 9. 이 사례에서 가져갈 핵심

1. 대규모 사용자 혜택 지급은 단순 DB 갱신이 아니라 **분산 Job**으로 보아야 한다.
2. 대규모 변경에서 가장 중요한 성질 중 하나는 **멱등성**이다.
3. Queue는 단순 메시지 전달뿐 아니라 **부하 완충과 Backpressure** 역할을 한다.
4. 재시도 가능한 시스템은 반드시 **중복 처리 안전성**을 함께 설계해야 한다.
5. Eventual Consistency 때문에 **실제 지급과 UI 표시 시각이 다를 수 있다.**
6. Canary와 점진적 Rollout은 속도를 늦추기 위한 것이 아니라 **Blast Radius를 통제하기 위한 장치**다.
7. 완료 판정에는 **Reconciliation과 End-to-End Runtime Evidence**가 필요하다.
8. 실제 제품 사례를 볼 때는 `관찰된 현상`과 `내부 구현에 대한 추정`을 분리해야 한다.

## 10. 스스로 설명할 수 있어야 할 질문

- 왜 수백만 계정을 한 번에 Update하지 않고 Batch/Queue로 나누는가?
- Worker가 성공 직후 Timeout되어 같은 Message가 다시 들어오면 어떻게 중복 지급을 막는가?
- Queue가 At-least-once라면 애플리케이션 수준의 Exactly-once 효과를 어떻게 만드는가?
- `서버에서는 지급됐는데 내 화면에는 없다`는 현상을 어떤 계층에서 진단해야 하는가?
- 일부 계정만 누락되었는지 어떻게 검출하는가?
- 잘못된 Grant 로직의 Blast Radius를 어떻게 줄이는가?
- Campaign 전체 완료를 어떤 Evidence로 증명할 것인가?
- 보안상 Grant Worker에는 어떤 최소 권한만 주어야 하는가?

## 관련 노트

- [[10_학습 노트/클라우드/00_클라우드_목차|클라우드 목차]]
- [[20_팀 프로젝트/3차 프로젝트/8.19 멘토님과 상담|8.19 멘토님과 상담]] - Source/설정 존재와 실제 Runtime Evidence를 구분하는 현재 프로젝트 사례
