---
type: project-doc
status: active
created: "2026-08-20"
project: "3차 프로젝트"
project_moc: "[[00_3차프로젝트_목차]]"
---

> [!NOTE] 분해 문서 안내
> 원문은 `3a6b45ec37f9be01f41ddd66ae20511fe2264f9a`의 정정 완료 단일 노트에서 블록 단위로 이동했다. SOURCE-BLOCK 내부는 원문 그대로이며, 안내문과 링크만 신규 내용이다. 이 문서는 공식 검증 후 현재 채택한 Incident 처리 구조와 프로젝트 적용 판단을 담는다.

<!-- 8.19-MENTOR-CONTEXT-BRIDGE CBR02 -->
> [!NOTE] 원문 선행 문맥
> B005 첫 문장의 `앞에서 적어둔 해석 A/B`는 [[8.19 멘토 상담 원문과 검토 이력#현재 잠정 해석 — UNRESOLVED]]의 해석 A/B를 가리킨다.

<!-- 8.19-MENTOR-SOURCE-BLOCK B005 START -->
# 후속 공식 검증 결과 — RESOLVED

## 결론

앞에서 적어둔 해석 A/B는 둘 중 하나만 고르는 문제가 아니었음.

가장 정확한 해석은 다음과 같음.

> **하나의 Incident Detection/Response 흐름 안에서 Source 특성에 따라 수집 경로와 도착 지연은 달라도 된다. 가능한 Source는 저지연·Event-driven 방식으로 중앙 SIEM에 보내고, 원본 Archive/Poll은 보존·재분석·보완 조사 역할로 유지한다.**

따라서 다음 표현은 버리는 편이 맞음.

```text
빠른 관제 vs 느린 관제
실시간 관제 vs 사후 관제
모든 Source가 반드시 동일한 하나의 Transport를 사용해야 한다는 해석
```

대신 다음처럼 이해함.

```text
하나의 보안관제 / Incident 흐름
├─ Source별 특성에 맞는 저지연 수집
├─ Wazuh SIEM 중앙 수집·분석
├─ 초기 고신뢰 신호 → 필요 시 제한적 대응
├─ 추가 Source 도착 → 범위·영향·확신도 보강
└─ 원본 Archive → 보존·재조사·재분석
```

### 현재 As-built와 Target Correlation

현재는 5개 Source가 자동으로 하나의 Incident Object에 합쳐지는 구조가 아니다.

```text
현재 As-built
→ Wazuh 중앙 수집
→ Dashboard / Query / Script 기반 후행 Evidence 연계
→ 일부 상관 판단은 운영자가 수행

Target
→ 공통 Correlation Key와 시간 창을 이용한
  자동 Incident Enrichment / Correlation
```

가능한 상관 키:

- `event_id` / `request_id` / Trace ID
- Principal / Role Session
- Source IP
- URI / Route
- Bucket / Key
- Event time window
- WAF Label / Action

공통 Stable ID가 없는 Source끼리는 완전한 일대일 대응이 아니라 다중 Evidence 기반 추론일 수 있다.

### 공식 자료 대조에서 확인한 핵심

- NIST SP 800-61r3는 보안 Event를 지속적으로 수집·분석하고 여러 Source의 정보를 상관분석해 Incident 여부를 판단하는 방향을 제시함.
- 모든 Source가 같은 속도나 같은 Transport로 들어와야 한다고 요구하지는 않음.
- AWS Security Incident Response는 `confirmed`뿐 아니라 충분히 `suspected`인 위협에도 사전 정의된 Containment를 적용하고, 이후 Investigation을 계속하는 흐름을 허용함.
- 다만 초기 자동 조치는 신뢰도, 좁은 범위, 가역성, 증거 보존, 서비스 영향 통제가 전제돼야 함.
- Microsoft Sentinel도 NRT Analytics Rule과 Scheduled Analytics Rule을 함께 사용하고, Alert/Incident 생성·갱신에 따라 Automation Rule/Playbook을 실행할 수 있으므로 **빠른 신호와 더 깊은 후속 분석이 하나의 SIEM Incident 흐름에서 공존하는 운영 패턴** 자체는 이상하지 않음.

`SUSPECTED → CONFIRMED`는 NIST나 Sentinel의 표준 상태명이라고 주장하면 안 되지만, 프로젝트 내부의 Incident confidence 모델로 사용하는 것은 타당함.

## 현재 프로젝트에 적용할 시나리오

먼저 현재 Codex G4는 그대로 끝낸다.

```text
Rule 100103 Alert
→ Wazuh Integrator
→ custom-shuffle-soc
→ 인증된 Shuffle Webhook
→ Execution
→ repeat_back_to_me
```

이 단계에서는 실제 격리 로직을 섞지 않고 Alert ↔ Execution 일대일 Runtime Evidence부터 닫음.

그 다음 시나리오를 다음처럼 보정하는 것이 좋음.

```text
DVWA 저지연 Push Event
→ Wazuh Rule 100103

IMDS 대상 명령 실행 성공 탐지
→ Incident: SUSPECTED
→ 임시 자격증명 탈취 및 S3 접근 위험 판단

즉시 Containment
├─ DVWA Workload 격리
└─ validation/* 추가 접근 차단
   또는 향후 DVWA 전용 IAM Principal 격리

기존 5-Source Evidence로 후행 조사
├─ WAF: Edge 검사·Action·Label
├─ CloudFront: 외부 요청 진입
├─ ALB: Target까지 전달된 경로
├─ DVWA: 실제 명령 실행
└─ CloudTrail: S3 GetObject 성공 여부

조사 결과
├─ 공격 문맥과 상관 가능한 GetObject 성공 Evidence → CONFIRMED
├─ 정상 Coverage + 동일 문맥의 명시적 실패 Evidence → REJECTED / NOT CONFIRMED
└─ 로그 부재 또는 Coverage·Delivery 불확실 → INCONCLUSIVE

추가 조치
├─ IAM 영향·자격증명 대응
├─ DVWA low → impossible 보안 설정 패치
├─ IAM 최소 권한
├─ IMDSv2·Hop Limit 보강
└─ 정상 기능 및 재공격 검증
```

### `S3가 털릴 위기`라는 표현의 정확한 의미

Rule `100103` 하나만으로 `S3가 실제로 털렸다`고 판단하면 안 됨.

Rule `100103`이 주는 의미는 대략 다음 수준임.

```text
IMDS를 겨냥한 명령 실행이 성공함
→ 임시 자격증명 탈취 가능성이 생김
→ 그 자격증명을 이용한 S3 접근 위험이 커짐
```

실제 S3 `GetObject` 성공 여부는 CloudTrail 등 후속 Evidence로 확인.

### Incident 판정 기준

#### CONFIRMED

다음처럼 공격 문맥과 연결되는 성공 Evidence가 존재해야 한다.

- 동일하거나 상관 가능한 Principal / Role Session
- 대상 Bucket·Key 또는 승인 Prefix 일치
- 공격 시간 창 일치
- 성공 응답
- Source IP·User-Agent·Request ID 등 보조 문맥 일치

#### REJECTED / NOT CONFIRMED

단순히 로그가 보이지 않는다는 이유가 아니라 다음 조건을 확인한다.

- CloudTrail Data Event Coverage 정상
- 대상 Bucket·Prefix·Region·시간 창 정확
- 충분한 Delivery 대기 후 조회
- 동일 공격 문맥의 명시적 AccessDenied / 실패 Evidence
- 다른 Source에도 성공 경로 없음

#### INCONCLUSIVE

다음 경우에는 기각하지 않는다.

- 대상 Event가 조회되지 않음
- Data Event 활성화·Selector·Prefix 불확실
- 조사 시간 창 또는 Delivery 완료 불확실
- Telemetry 누락·best-effort·보존 상태 불확실

> **Telemetry Coverage가 검증되지 않았다면 로그의 부재를 행위 부재의 증거로 취급하지 않는다.**

따라서 발표에서는 다음처럼 말하는 것이 정확함.

> **S3 접근으로 이어질 수 있는 고신뢰 위험 신호를 저지연으로 탐지해 먼저 제한적 Containment를 수행하고, 이후 여러 Source의 Evidence를 연계해 실제 데이터 접근 여부와 영향 범위를 확인한다.**

## `S3는 중요하니 일단 격리 쎄게`의 보정

방향은 맞지만 `쎄게`를 `넓게 다 막는다`로 이해하면 안 됨.

> **강한 격리 = 공격 경로는 확실히 끊되 Blast Radius는 사전에 고정한 격리**

현재 프로젝트에서는 다음이 가장 방어하기 쉬움.

```text
DVWA Workload Quarantine
+
validation/* Lab 범위의 추가 접근 차단
```

### Containment는 세 축으로 분리한다

#### 1. Workload / Network Containment

- DVWA Pod / Workload 격리
- 공격 실행 지점의 추가 통신 차단
- 정상 서비스 영향과 복구 절차 확인

#### 2. Resource / Permission Containment

- `validation/*` Lab 범위 Explicit Deny
- 필요 시 Bucket Policy·IAM Policy 제한
- 공유 Node Role 전체 `DenyAll`은 다른 Workload 영향 때문에 자동 실행하지 않음

#### 3. Credential / Session Response

- 실제 사용 Principal과 Role Session 식별
- 탈취·재사용 가능성 및 다른 Resource 권한 조사
- 가능한 범위에서 세션·권한 영향 제한
- 장기적으로 DVWA 전용 Pod Identity / IAM Role로 Blast Radius 축소

Workload 격리만으로 이미 탈취된 STS Credential이 자동 폐기되는 것은 아니다. 세 축을 함께 조사한다.

현재처럼 공유 Karpenter Node Role을 사용하는 동안에는 Role 전체 `DenyAll`을 자동 실행하면 다른 Workload까지 영향이 갈 수 있으므로 피함.

향후 DVWA 전용 Pod Identity/IAM Role이 생기면 전용 Principal Containment까지 자동화할 수 있음.

## Microsoft Sentinel을 발표에서 부가 설명하는 방법

넣어도 좋음. 단 **동일한 구현**이라고 말하지 않고 **유사한 운영 패턴을 지원한다**고 설명해야 함.

발표용 예시:

> Microsoft Sentinel도 NRT 분석 규칙으로 빠른 탐지를 수행하고, Scheduled 분석 규칙과 추가 Alert를 같은 Incident에 연결해 후속 분석을 보강하며, Alert나 Incident의 생성·갱신 시 Playbook을 실행할 수 있습니다. 저희도 이와 유사하게 초기 고신뢰 신호로 제한적 대응을 시작하고, 이후 여러 Source의 Evidence로 사건을 확인하도록 구성했습니다.

Sentinel의 NRT/Scheduled Rule이 프로젝트의 `DVWA Push / 5-Source Poll`과 기술적으로 같은 구현이라는 뜻은 아님. **운영 원리가 유사하다는 비교**임.


<!-- 8.19-MENTOR-SOURCE-BLOCK B005 END -->

<!-- 8.19-MENTOR-SOURCE-BLOCK B008 START -->
## 5-Source Poll의 현재 역할과 장기 역할

### 현재 As-built

```text
DVWA Push
→ 초기 탐지·Containment Trigger

5-Source Poll
→ Investigation / Confirmation / Evidence
```

현재 As-built와 이미 확보한 Runtime Evidence 범위를 유지하는 동안에는 이 역할 분담을 사용한다.

### 장기 Target

```text
각 Source에 맞는 Event-driven 수집
→ 하나의 Wazuh Incident 흐름에서 Correlation

기존 Poll / Archive
→ 원본 보존
→ 누락 보완
→ Replay / 재분석
→ Historical Investigation
```

모든 Source의 Event-driven 전달이 완성된 뒤에는 5-Source Poll을 주 탐지 경로로 두기보다 **원본 Evidence·Replay·Fallback·과거 조사 경로**로 이동시키는 것이 자연스러움.

## 최종 추천

프로젝트는 다음 순서로 진행.

```text
1. 현재 G4 Goal 그대로 완료
2. Rule 100103 Alert ↔ Shuffle Execution Runtime Evidence 보존
3. 그 상태를 Checkpoint로 고정
4. Containment 시나리오 보정
5. DVWA Push 위험 신호 → SUSPECTED
6. 좁고 강한 Containment
7. 기존 5-Source Evidence로 실제 GetObject·공격 경로·영향 조사
8. CONFIRMED / REJECTED / INCONCLUSIVE
9. 추가 대응·Remediation·Recovery
```

최종 발표에서는 다음처럼 설명하는 것이 가장 안전함.

> **현재 구현은 DVWA 저지연 Push를 초기 Trigger로 사용하고, 5개 Source의 후행 Evidence를 연계해 실제 침해 여부와 영향 범위를 확인합니다. 향후에는 Source별 특성에 맞는 Event-driven 수집을 확대하고, 기존 Poll은 원본 보존과 재분석 경로로 유지할 계획입니다.**

---


<!-- 8.19-MENTOR-SOURCE-BLOCK B008 END -->
