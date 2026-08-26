---
type: project-doc
status: draft
created: 2026-08-26
project: "3차 프로젝트"
project_moc: "[[20_팀 프로젝트/3차 프로젝트/보고서/5장_보안관제/00_5장 보안관제 목차]]"
---

# Canva 복붙용 5장 보안관제 재구성 원고

## 이 원고의 목적

기존 5장은 구현 근거와 개별 기능은 충분하지만, 같은 내용을 제품·Rule·Workflow 단위로 반복하면서 **왜 이런 구조를 선택했고 각 판단이 다음 단계로 어떻게 이어졌는지**가 여러 페이지에 흩어져 있다.

이 재구성안은 Chapter 5를 다음 한 문장으로 설명할 수 있도록 다시 배열한다.

> 하나의 Capital One 재구성 시나리오에서 수집 지연과 신호의 확실성 차이를 구분하고, 각 Alert를 민감정보가 제한된 검증 절차와 고정 GitOps 대응으로 연결하여 탐지·대응·증적·복구의 폐쇄루프를 구현하였다.

기존 Canva, PDF, Notion 원본은 수정하지 않는다. 아래의 `P01`~`P17`은 실제 보고서 전체 페이지 번호가 아니라 **Chapter 5 내부 편집 순서**다.

## 재구성 원칙

1. 제품 소개보다 `문제 → 판단 → 구현 → 결과 → 한계`를 먼저 보여준다.
2. 한 페이지는 한 가지 질문에 답한다.
3. Rule의 모든 필드를 본문에서 설명하지 않고, 그 필드가 다음 판단을 가능하게 한 이유를 설명한다.
4. 같은 코드와 절차를 여러 페이지에서 반복하지 않는다.
5. 상세 Rule XML과 실행 증적은 앞선 설계 주장을 입증하는 근거로 배치한다.
6. `low → impossible`은 실제 운영 Patch가 아니라 교육 환경에서 선택한 고정·가역 Playbook임을 명확히 한다.

---

## P01 — 결론 먼저: 보안관제 구현 결과

### Canva 본문

> **여러 AWS·EKS 로그에서 공격의 서로 다른 단계를 식별하고, 검증된 Alert만 실제 격리와 취약 경로 완화로 연결하는 추적·복구 가능한 보안관제 체계를 구현하였다.**

| 설계 과제 | 구현 결과 |
|---|---|
| 수집 범위와 대응 속도의 충돌 | 여러 AWS Source의 5분 정기 수집은 유지하고, 대응에 필요한 DVWA Audit Event만 별도 저지연 경로로 전달하였다. |
| 신호마다 다른 확실성 | `100102`는 전달 건전성, `100110`은 IMDS 자격증명 탈취 단계의 고위험 행위, `100111`은 보호 S3 Object의 실제 바이트 반환으로 분리하였다. |
| 자동화의 오작동 위험 | Wazuh가 원문 문맥을 로컬 검증하고, Shuffle은 최소 Payload와 고정 계약을 통과한 경우에만 승인된 Workflow를 호출하도록 제한하였다. |
| 대응의 추적과 복구 | 변경을 GitHub Actions Run·Git Commit·Argo CD Revision으로 남기고 Reset 절차로 재촬영·재검증 기준선을 복구하였다. |

### 한 줄 결론

> 핵심 성과는 보안 도구를 많이 연결한 것이 아니라, **서로 다른 증거의 의미와 신뢰 수준에 맞춰 탐지·판단·대응의 경계를 설계한 것**이다.

### Canva 편집 메모

- 기존 `보안관제 구현 결과 및 핵심 성과` 페이지를 재사용한다.
- 이 페이지에서는 세부 필드와 코드명을 늘리지 않는다.
- Chapter 5의 첫 내용 페이지로 배치한다.

---

## P02 — 문제 정의: 하나의 공격을 끝까지 연결한다

### Canva 본문

본 프로젝트는 여러 공격 유형을 얕게 나열하는 대신, Capital One 사건의 핵심 흐름을 실습 환경에 맞게 재구성한 하나의 시나리오를 선택하였다.

```text
DVWA Command Injection
→ EC2 IMDS Node Role 자격증명 접근
→ 보호 S3 Object 조회
→ Wazuh 탐지
→ Shuffle 검증
→ Workload 격리와 취약 경로 완화
→ GitOps 증적과 기준선 복구
```

### 왜 하나의 시나리오에 집중했는가

| 선택 | 이유 |
|---|---|
| 여러 공격을 각각 탐지 | 제품 기능은 많이 보이지만 Alert 이후의 실제 결과와 복구까지 검증하기 어렵다. |
| 하나의 사건을 끝까지 추적 | 실제 Event, Rule, Alert, SOAR 판단, Runtime 변경, 증적과 복구의 인과관계를 일대일로 설명할 수 있다. |

### 강조 문장

> 평가 대상은 공격 종류의 수가 아니라, **실제 Event가 어떤 Rule과 판단을 거쳐 어떤 Runtime 결과를 만들었는지 설명하고 증명할 수 있는가**였다.

### Canva 편집 메모

- 제품 로고 목록보다 공격 흐름을 크게 배치한다.
- `시간이 부족해서 하나만 했다`가 아니라 `한 사건의 전체 폐쇄루프를 검증 범위로 선택했다`고 설명한다.

---

## P03 — 5.1 수집 경로 설계: 왜 두 경로가 필요한가

### Canva 본문

초기 정기 수집 경로는 여러 AWS Log Source를 한곳에서 조회하고 장기 보존·재분석하기에 적합했다. 그러나 Rule `100111`의 입력이 되는 CloudTrail Event는 5분 주기로 조회되므로, 공격이 진행되는 동안 먼저 관제를 시작하기에는 지연이 있었다.

이에 전체 수집 구조를 교체하지 않고 역할을 분리하였다.

| 경로 | 담당 역할 | 선택 이유 |
|---|---|---|
| 정기·광범위 수집 | Wazuh AWS Module이 S3와 CloudWatch Logs를 5분 주기로 조회 | 여러 Source의 지속적인 수집, 보존 및 사후 분석 |
| 저지연·선별 전달 | CloudWatch Subscription → Lambda → SQS → Local Bridge → Wazuh | 대응에 필요한 DVWA Audit Event를 먼저 가시화 |

### 핵심 판단

> 두 경로 중 하나를 선택한 것이 아니다. **정기 수집은 관제 범위를 유지하고, 저지연 경로는 고위험 Event의 대응 시점을 앞당기는 역할**을 맡는다.

### 사용할 이미지

![[20_팀 프로젝트/3차 프로젝트/노션_내보낸거/관제 올인원-1_탐지 경로.png]]

### 캡션

> 같은 공격에서 생성된 Event가 서로 다른 수집 경로를 거쳐 Wazuh에 도착한다. 두 Alert의 도착 순서는 보장하지 않으며, Timeline에서 시각과 대상 문맥을 비교한다.

---

## P04 — 5.1 수집 경로의 역할과 범위

### Canva 본문

| 구분 | 현재 입력 | Wazuh에서의 활용 |
|---|---|---|
| DVWA 저지연 Event | 선별된 서버 Audit Event | Rule `100102`, `100110` |
| CloudTrail CloudWatch Logs | AWS API 및 S3 Data Event | Rule `100111`과 AWS 활동 조사 |
| ALB S3 Log | Load Balancer Access Log | 정기 수집과 재분석 |
| WAF·CloudFront·DVWA CloudWatch Logs | 최근 보안·애플리케이션 Event | Dashboard 검색과 시계열 조사 |
| Security S3 | 장기 보존 사본 | Athena 기반 사후 분석과 Evidence 보관 |

### 오해 방지 문장

> Rule `100111`의 현재 입력은 CloudTrail CloudWatch Log Group을 조회하는 5분 Polling이며, S3 사본은 장기 보존과 재분석에 사용한다.

> Rule `100102` Probe는 CloudWatch Log Group에 합성 Event를 직접 기록하므로, DVWA 애플리케이션이 아니라 **CloudWatch 이후 저지연 전달 구간**의 건전성을 확인한다.

### Canva 편집 메모

- 기존 제품별 로그 목록 표를 이 페이지 하나로 통합한다.
- 서비스 이름을 늘어놓기보다 `어떤 입력이 어떤 판단에 사용되는가`를 보여준다.

---

## P05 — 5.2 탐지 신호 설계: 왜 세 Rule로 분리했는가

### Canva 본문

같은 공격 흐름에서 생성됐더라도 모든 Event가 같은 사실을 증명하지는 않는다. 따라서 전달 상태, 고위험 행위, 실제 침해 결과를 서로 다른 Rule로 분리하였다.

| Rule | 증거 수준 | 의미 | 자동 대응 |
|---|---|---|---|
| `100102` | 전달 상태 | 합성 Validation Event가 저지연 경로를 거쳐 Wazuh에 도착 | 없음 |
| `100110` | 고위험 행위 | IMDS 자격증명 탈취 단계의 복합 명령이 실행되고 출력이 발생 | 대상 Pod 격리·보존 |
| `100111` | 침해 결과 | 승인된 Node Role로 보호 S3 Object의 실제 바이트가 반환 | DVWA 방어 프로필 전환 |

### 핵심 판단

> 하나의 Rule로 합치면 `전달 경로가 살아 있음`, `공격이 진행 중일 가능성이 높음`, `보호 데이터가 실제 반환됨`이라는 서로 다른 보안 사실을 구분할 수 없다.

### 짧은 설명

- `100110`은 공격 완료 전 차단을 보장하지 않는다. 5분 Polling 기반 `100111`보다 먼저 관제와 대응을 시작할 가능성을 만든 저지연 경보다.
- `100111`은 `100110`의 발생 여부와 무관하게 CloudTrail Event 자체의 조건으로 판정한다.
- 두 Rule이 같은 사건인지는 관제자가 Timeline에서 시각과 대상 문맥을 비교해 조사한다.

---

## P06 — 5.2 독립 Alert를 하나의 사건으로 조사하는 방법

### Canva 본문

Rule `100110`과 Rule `100111`은 Wazuh에서 자동 AND 상관분석하지 않는다. 서로 다른 Source와 수집 지연을 가진 독립 증거이기 때문이다.

관제자는 Incident Timeline에서 다음 문맥을 비교한다.

| 비교 대상 | Rule 100110 | Rule 100111 |
|---|---|---|
| 시각 | DVWA Audit Event 시각 | CloudTrail Event 시각 |
| 실행 주체·대상 | Pod 이름·UID, IMDS 단계 | Node Role, Bucket, Object |
| 사건 식별 | `take_id`, Event Hash | CloudTrail `eventID` Hash |
| 의미 | 고위험 Workload 행위 | 보호 데이터의 실제 반환 |

### 핵심 판단

> 자동 상관을 구현한 것처럼 포장하지 않고, **각 Alert가 증명하는 사실과 사람이 연결해야 하는 조사 영역을 분리**하였다.

### 사용할 증거

- Wazuh Incident Timeline Dashboard
- Rule `100110`, `100111`의 원문 필드 분해 표

### 캡션

> 두 Alert의 발생 시각과 실행 주체·대상 문맥을 함께 비교하여 하나의 공격 흐름인지 조사한다.

---

## P07 — 5.3 판단 경계: 왜 Wazuh가 먼저 검증하는가

### Canva 본문

Wazuh Alert가 발생했다는 사실만으로 외부 SOAR에 쓰기 권한을 부여하지 않았다. 원문 로그에는 Account·Role·Bucket·Object와 같은 조사 문맥이 포함되며, Workload Event에는 Pod 식별 정보가 포함된다.

따라서 역할을 다음과 같이 분리하였다.

| 계층 | 담당 판단 |
|---|---|
| Wazuh Rule | 수집된 Event가 탐지 조건을 만족하는지 판정 |
| Wazuh Integration | 전체 로컬 문맥을 다시 검증하고 민감정보를 제거 |
| Shuffle | 최소 Payload가 Rule별 실행 계약을 만족하는지 검증 |
| GitHub Actions | 허용된 Repository·Branch·파일·값만 변경 |
| Argo CD | 승인된 Git Revision을 EKS에 동기화 |

### 핵심 판단

> **Wazuh는 사건의 근거를 검증하고, Shuffle은 그 근거가 자동 대응을 실행할 계약을 만족하는지 판단한다.** 두 검증은 중복이 아니라 서로 다른 신뢰 경계를 담당한다.

---

## P08 — 5.3 외부 SOAR에는 무엇을 전달하는가

### Canva 본문

Wazuh Integration은 원문 Alert를 그대로 전달하지 않고, Rule별 전체 조건을 로컬에서 확인한 뒤 대응에 필요한 최소 정보만 Shuffle로 전송한다.

| Rule | 로컬에서 확인 | Shuffle로 전달 |
|---|---|---|
| `100110` | Rule·Level·Source·Account·Region·Event 단계·Pod 이름·UID | 정제된 Schema v3, Alert ID, 시각, `take_id`, Pod 이름·UID, Event·원문 Hash |
| `100111` | Account·Region·Role·Bucket·Object·GetObject·HTTP 200·반환 바이트 | Rule ID, Event 시각, Alert ID, Event ID SHA-256, 원문 SHA-256 |

Credential, Cookie, Command 원문과 응답 및 CloudTrail 원문은 Shuffle Payload에 포함하지 않는다.

### Shuffle 검증 범위

- `100110`: exact Schema, 고정값, Timestamp 신선도, `body_sha256` 재계산·일치 확인, Pod·Event 형식
- `100111`: 정확한 5필드, Timestamp 신선도, 두 SHA-256의 형식 확인, 전달 Payload의 새 Body Hash 생성

### 핵심 판단

> 외부 SOAR에는 사건 원문이 아니라 **승인 여부를 판단하는 데 필요한 최소 계약**만 전달하였다.

---

## P09 — 5.4 대응 설계: 왜 두 Alert에 다른 조치를 연결했는가

### Canva 본문

Rule의 Level 차이만으로 대응을 결정하지 않았다. 각 Alert가 증명하는 사실과 그 시점에 필요한 조치의 목적을 연결하였다.

| Alert | 판단 가능한 사실 | 대응 목적 | 선택한 조치 |
|---|---|---|---|
| `100110` | 특정 DVWA Pod에서 IMDS 자격증명 탈취 단계의 고위험 명령 실행·출력 | 추가 접근 제한, 공격 실행 지점 보존, 정상 서비스 유지 | 해당 Pod의 네트워크 격리·보존 |
| `100111` | 보호 S3 Object의 실제 바이트 반환 | 같은 웹 취약 경로의 반복 사용 제한 | DVWA `low → impossible` 방어 프로필 전환 |

### 핵심 판단

> `100110`에는 **대상과 영향 범위를 좁힌 가역적 격리**, `100111`에는 **공격 진입점의 재사용을 제한하는 설정 강화**를 연결하였다.

### 대응의 한계

두 조치 모두 이미 반환된 S3 바이트를 회수하거나 발급된 Node Role 자격증명을 무효화하지는 않는다. 실제 운영환경에서는 IAM Session 폐기, Node 격리·교체, S3/IAM 정책 수정과 취약 코드 Patch가 후속되어야 한다.

---

## P10 — 5.4 Rule 100110: 침해 Pod 격리·보존

### Canva 본문

1. Wazuh Integration이 Alert의 Rule·시각·`take_id`·Pod 이름·UID를 로컬 검증한다.
2. Shuffle은 고정 계약을 통과한 경우에만 `soc-contain-dvwa.yml`을 호출한다.
3. Workflow는 `values.yaml`에 격리 대상 Pod 이름·UID와 Event Hash만 기록한다.
4. Argo CD가 해당 Git Revision을 EKS에 동기화한다.
5. 격리 Job은 실제 Pod UID, DVWA Label, ReplicaSet·Deployment 소유 관계를 다시 확인한다.
6. 일치한 Pod만 OwnerReference에서 분리하고 `quarantined` Label과 deny-all NetworkPolicy를 적용한다.
7. 정상 ReplicaSet은 서비스 제공을 위한 대체 Pod를 유지한다.

### 왜 이름만 사용하지 않았는가

> Kubernetes Pod 이름은 재사용될 수 있으므로 Alert 시점의 UID와 배포 시점의 실제 UID를 다시 비교하였다. 이름·UID·Label·소유 관계가 모두 일치하는 Pod만 조치한다.

### 사용할 이미지

![[20_팀 프로젝트/3차 프로젝트/노션_내보낸거/관제 올인원-3_100110 저지연 격리 상세.png]]

### 캡션

> 고위험 Workload Alert를 즉시 삭제가 아닌 증거 보존과 통신 차단으로 연결하고, 정상 대체 Pod로 서비스를 유지한다.

---

## P11 — 5.4 Rule 100111: 취약 경로 완화

### Canva 본문

1. Wazuh Integration이 CloudTrail 원문의 Account·Region·Role·Bucket·Object·HTTP 상태·반환 바이트를 로컬에서 검증한다.
2. Shuffle에는 Rule ID, Event 시각, Alert ID와 두 SHA-256만 전달한다.
3. Shuffle은 정확한 5필드 계약과 Timestamp·Hash 형식을 확인한다.
4. 검증된 경우에만 고정 `soc-harden-dvwa.yml`을 호출한다.
5. Workflow는 `deploy/dvwa/values.yaml`의 `defaultSecurityLevel` 한 값만 `low → impossible`로 변경한다.
6. Git Commit이 `main`에 반영되면 Argo CD가 새 Revision을 EKS에 배포한다.
7. 새 DVWA Pod와 Session에서 `security=impossible`을 확인한다.

### `low → impossible`의 정확한 의미

> 취약 소스코드를 자동 생성·수정한 것이 아니다. DVWA에 이미 구현된 안전 프로필을 **변경 대상이 고정되고 추적·복구 가능한 교육용 Playbook**으로 배포하였다.

### 사용할 이미지

![[20_팀 프로젝트/3차 프로젝트/노션_내보낸거/관제 올인원-4_100111 정기 수집·강화 상세.png]]

### 캡션

> 실제 S3 바이트 반환을 확인한 뒤 같은 DVWA 명령 실행 경로의 반복 사용을 제한한다.

---

## P12 — 5.4 왜 직접 명령이 아니라 GitOps인가

### Canva 본문

Shuffle이 AWS나 Kubernetes API를 직접 호출하도록 만들면 대응은 짧아지지만, 외부 SOAR가 넓은 쓰기 권한을 갖고 변경 대상·이력·복구 경로가 분산될 수 있다.

본 프로젝트는 자동 대응을 GitHub Actions와 Argo CD를 거치도록 제한하였다.

| 직접 실행 방식의 위험 | GitOps 방식의 통제 |
|---|---|
| Alert 값이 임의 대상이나 명령으로 이어질 수 있음 | Repository·Branch·Workflow·변경 파일·허용 값을 고정 |
| 어떤 설정이 바뀌었는지 추적하기 어려움 | Git Diff·Commit SHA·Workflow Run으로 변경 기록 |
| 실행 결과와 배포 상태가 분리됨 | Argo CD exact Revision과 Runtime Read-back으로 연결 |
| 실패 후 복구 절차가 별도 | 같은 GitOps 경로와 Reset 절차로 기준선 복구 |

### 핵심 판단

> 자동 대응의 목표를 단순한 실행 속도가 아니라 **변경 범위의 통제, 사후 추적, 재현과 복구 가능성**으로 정의하였다.

---

## P13 — 5.4 전체 자동 대응 폐쇄루프

### 사용할 이미지

![[20_팀 프로젝트/3차 프로젝트/노션_내보낸거/관제 올인원-2_대응 폐쇄루프.png]]

### Canva 본문

```text
Wazuh Alert
→ Wazuh Integration의 로컬 원문 검증·정제
→ Shuffle의 실행 계약 검증
→ Rule별 고정 GitHub Workflow
→ Git Commit과 Argo CD 배포
→ EKS Runtime 상태 확인
→ Workflow Run·Commit·Revision 증적
→ 기준선 복구
```

### 캡션

> Alert가 곧바로 인프라 변경으로 이어지지 않는다. 각 계층이 서로 다른 검증과 통제를 담당하며, 승인된 Git Revision만 Runtime에 반영된다.

### 다이어그램 문구 교정

기존 `Reset Workflow` 박스는 다음처럼 수정한다.

> **기준선 복구 — GitHub Workflow + 로컬 Reset**
>
> GitHub: 격리 요청 정리·low 복원 / Local: UID 검증 후 격리 Pod 삭제 / Argo: Synced·Healthy 확인

---

## P14 — 5.5 구현 근거: Rule 조건이 공격의 무엇을 뜻하는가

### Canva 본문

#### Rule 100110

| 핵심 필드 | 공격 흐름에서의 의미 |
|---|---|
| `source=dvwa`, `transport=push` | DVWA 서버 Audit Event가 저지연 경로로 도착 |
| `route=/vulnerabilities/exec/` | Command Injection 실습 경로에서 발생 |
| `resource=ec2_imds` | 요청 대상이 EC2 IMDS |
| `stage=imds_credential_fetch` | 특정 Role의 Credential URI를 대상으로 함 |
| `status=output_returned` | 복합 명령 전체에 비어 있지 않은 출력이 발생 |
| `security_level=low` | 취약 프로필에서 실행 |

> Rule `100110`은 자격증명 원문 탈취나 S3 접근 완료를 단독으로 증명하지 않는다.

#### Rule 100111

| 핵심 필드 | 공격 흐름에서의 의미 |
|---|---|
| `GetObject`, `Data`, `readOnly=true` | S3 Object Data Read Event |
| 승인 Account·Region·AssumedRole | 실습 시나리오의 허용된 호출 주체 |
| 고정 Bucket 패턴·Object Key | 보호 대상으로 지정한 검증용 Object |
| `httpStatusCode=200` | API 요청 성공 |
| `bytesTransferredOut>0` | Object의 실제 바이트 반환 |

> Rule `100111`은 단순 시도나 `AccessDenied`가 아니라 보호 Object의 실제 데이터 반환을 탐지한다.

### Canva 편집 메모

- 전체 XML 앞에 이 페이지를 둔다.
- 코드를 먼저 보여주지 말고 `필드 → 공격 의미`를 먼저 설명한다.

---

## P15 — 5.5 구현 근거: 핵심 Rule 코드

### Canva 본문

#### Rule 100102·100110

```xml
<rule id="100102" level="3">
  <field name="transport" type="pcre2">^push$</field>
  <field name="source" type="pcre2">^dvwa$</field>
  <field name="payload.event_type" type="pcre2">^wazuh\.push\.validation$</field>
  <field name="payload.training_marker" type="pcre2">^SAFE_VALIDATION_EVENT$</field>
</rule>

<rule id="100110" level="12">
  <field name="payload.event_type" type="pcre2">^command\.execution$</field>
  <field name="payload.context.resource" type="pcre2">^ec2_imds$</field>
  <field name="payload.context.stage" type="pcre2">^imds_credential_fetch$</field>
  <field name="payload.context.status" type="pcre2">^output_returned$</field>
  <field name="payload.context.security_level" type="pcre2">^low$</field>
</rule>
```

### 코드 아래 설명

> `100102`는 합성 Marker로 전달 경로를 확인하고, `100110`은 실제 DVWA Audit Event의 공격 대상·단계·출력 상태를 함께 평가한다.

---

## P16 — 5.5 구현 근거: Rule 100111 코드

### Canva 본문

```xml
<rule id="100111" level="14">
  <field name="eventSource" type="pcre2">^s3\.amazonaws\.com$</field>
  <field name="eventName" type="pcre2">^GetObject$</field>
  <field name="eventCategory" type="pcre2">^Data$</field>
  <field name="userIdentity.type" type="pcre2">^AssumedRole$</field>
  <field name="requestParameters.key" type="pcre2">^validation/capital-one-demo\.csv$</field>
  <field name="additionalEventData.httpStatusCode" type="pcre2">^200$</field>
  <field name="additionalEventData.bytesTransferredOut" type="pcre2">^[1-9][0-9]*$</field>
</rule>
```

### 코드 아래 설명

> 여러 조건을 동시에 요구하여 `GetObject` 호출 흔적이 아니라, 승인된 시나리오 대상에서 실제 바이트가 반환된 결과를 고신뢰 Alert로 정의하였다.

### Canva 편집 메모

- 기존 전체 XML은 글자가 작고 연결 의미가 약하다.
- 위 핵심 조건만 본문에 두고 전체 Rule 파일 경로는 각주나 부록으로 남긴다.

---

## P17 — 5.5 Runtime 증적·복구·한계

### Canva 본문

| 주장 | 확인할 증적 |
|---|---|
| Rule `100110`, `100111` 탐지 | Wazuh Dashboard의 Alert와 원문 필드 |
| `100110` 자동 격리 | Shuffle Execution, GitHub Containment Run, Argo CD의 격리 Pod·정상 대체 Pod |
| `100111` 방어 프로필 전환 | Shuffle Execution, GitHub Run `32637113392`, Commit SHA, Argo Revision, 새 Session의 `impossible` |
| 기준선 복구 | Reset Run `32643206492`, Argo `Synced·Healthy`, 새 Session의 `low`, UID 검증 격리 Pod 삭제 결과 |

### 증적 Chain

```text
Wazuh Alert ID·Source Event Hash
→ Shuffle Execution
→ GitHub Workflow Run·Commit SHA
→ Argo CD exact Revision
→ 실제 Pod·Session 상태
```

### 구현 범위와 한계

- Rule `100110`은 공격 스크립트 완료 전 차단을 보장하지 않는다.
- 두 Rule은 독립적으로 발생하며 동일 사건 여부는 관제자가 Timeline에서 조사한다.
- Pod 격리는 이미 유출된 Node Role 자격증명을 폐기하지 못한다.
- `low → impossible`은 실제 운영 Patch가 아니라 교육 환경의 고정·가역 대응이다.
- 실제 운영에서는 취약 코드 수정, 새 Image 배포, IAM Session 무효화, Node 격리·교체와 재공격 회귀 검증이 필요하다.

### 마지막 문장

> 구현의 의미는 모든 침해를 자동 해결했다는 데 있지 않다. **서로 다른 증거를 구분하고, 각 증거가 허용하는 범위 안에서 제한된 조치를 실행하며, 그 변경을 추적하고 되돌릴 수 있는 관제 폐쇄루프를 검증했다는 데 있다.**

---

## 기존 Canva 페이지 재사용·통합 지침

| 기존 내용 | 처리 |
|---|---|
| 보안관제 구현 결과 및 핵심 성과 | P01로 재작성 |
| 제품·구성요소 소개 | P03·P04·P07로 통합 |
| Log Source 목록 | P04 한 페이지로 통합 |
| Wazuh·Shuffle·GitOps 역할 설명 | P07·P08·P12로 재배치 |
| Rule 100110·100111 관계 | P05·P06로 재작성 |
| 자동 대응 절차 | P09~P13으로 재구성 |
| 반복되는 Workflow 코드 | P12의 설계 이유와 P17 증적으로 축소 |
| Rule 전체 XML | P14 설명 뒤 P15·P16 핵심 코드만 사용 |
| 현재 PDF의 공백·중복 Diagram 페이지 | P10·P11 상세 이미지로 교체 |
| `asdf` 복붙 양식 | Canva에는 유지하되 최종 PDF 내보내기에서 제외 |

## 구현 근거 파일

- `D:\Wazuh\wazuh-docker\single-node\config\wazuh_cluster\rules\capital_one_rules.xml`
- `D:\Wazuh\wazuh-docker\single-node\config\wazuh_cluster\wazuh_manager.conf`
- `D:\terraform\aws_terraform_build_code\foundation\wazuh-push.tf`
- `D:\terraform\aws_terraform_build_code\foundation\lambda\wazuh_push_forwarder.py`
- `D:\terraform\aws_terraform_build_code\tools\Start-WazuhPushShadowBridge.ps1`
- `D:\terraform\aws_terraform_build_code\observability\wazuh\integrations\custom-shuffle-soc`
- `D:\terraform\aws_terraform_build_code\observability\shuffle\apps\aws-topology-soc-rule100110-auto-containment\1.0.1\src\autocontainment.py`
- `D:\DVWA\.github\workflows\soc-contain-dvwa.yml`
- `D:\DVWA\.github\workflows\soc-harden-dvwa.yml`
- `D:\DVWA\.github\workflows\soc-reset-dvwa.yml`
- `D:\DVWA\deploy\dvwa\templates\quarantine-job.yaml`
- `D:\DVWA\deploy\dvwa\templates\networkpolicy-quarantined-pod.yaml`
- `D:\DVWA\vulnerabilities\exec\source\low.php`
- `D:\DVWA\vulnerabilities\exec\source\impossible.php`
- `D:\terraform\aws_terraform_build_code\observability\scenarios\Invoke-SocLabReset.ps1`
