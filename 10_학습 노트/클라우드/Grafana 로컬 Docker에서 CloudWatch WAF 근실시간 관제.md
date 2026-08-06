---
type: lab-note
status: verified
created: 2026-08-06
updated: 2026-08-06
scope: Grafana, CloudWatch Logs Insights, AWS WAF, XSS 탐지, 근실시간 관제
parent_moc: "[[10_학습 노트/클라우드/00_클라우드_목차]]"
related:
  - "[[10_학습 노트/클라우드/Grafana 로컬 Docker에서 Athena 연결]]"
---

# Grafana 로컬 Docker에서 CloudWatch WAF 근실시간 관제

## 1. 목적

S3와 Athena를 이용한 분석은 로그가 S3에 도착한 뒤 조회하는 사후 분석 경로다. 공격 재현 중 화면이 바로 변하는 관제 화면을 만들기 위해, 로컬 Docker Grafana에서 Amazon CloudWatch Data Source를 직접 연결하고 CloudFront WAF 로그를 조회했다.

현재 역할 분리는 다음과 같다.

```text
근실시간 관제
WAF·애플리케이션·EKS 로그
→ CloudWatch Logs
→ Local Docker Grafana

사후 분석·증거 수집
CloudFront·ALB·VPC 로그
→ S3
→ Athena
→ Grafana 또는 .\daily-down.ps1 -EvidenceOnly
```

---

## 2. 전제 환경

| 항목 | 확인값 |
|---|---|
| Grafana | 로컬 Docker Grafana |
| 접속 주소 | `http://127.0.0.1:3000` |
| AWS 인증 | Windows AWS Credentials file을 컨테이너에 Read-only Mount |
| Credentials Profile | `terra-user` |
| 기본 Region | `ap-northeast-2` |
| WAF Region | `us-east-1` |
| WAF Log Group | `aws-waf-logs-aws-topology-edge` |
| 대상 Domain | `unoh.click` |

CloudFront 범위 WAF는 `us-east-1`에서 관리되므로, Grafana의 기본 Region이 서울이어도 WAF Query에서는 Region을 `us-east-1`로 변경해야 한다.

---

## 3. Amazon CloudWatch Data Source 연결

Grafana에서 다음 경로로 이동했다.

```text
Connections
→ Add new connection
→ Amazon CloudWatch
→ Add new data source
```

설정값:

| 필드 | 값 |
|---|---|
| Authentication Provider | `Credentials file` |
| Credentials Profile Name | `terra-user` |
| Assume Role ARN | 비움 |
| External ID | 비움 |
| Endpoint | 비움 |
| Default Region | `ap-northeast-2` |
| Namespaces of Custom Metrics | 비움 |
| Default Log Groups | 비움 |
| Application Signals | 연결하지 않음 |

`Save & test` 결과:

```text
Successfully queried the CloudWatch metrics API
Successfully queried the CloudWatch logs API
```

> [!note]
> `Query Result Timeout: 30m`은 자동 새로고침 주기가 아니다. CloudWatch Logs Insights Query가 완료되기를 Grafana가 기다리는 최대 시간이다.

---

## 4. WAF Log Group 조회

Grafana에서 다음 경로로 이동했다.

```text
Explore
→ Data source: cloudwatch
```

Query 설정:

| 항목 | 값 |
|---|---|
| Region | `us-east-1` |
| Query type | `CloudWatch Logs` |
| Logs Mode | `Logs Insights` |
| Query language | `Logs Insights QL` |
| Query scope | `Log group name` |
| Log Group | `aws-waf-logs-aws-topology-edge` |

처음 사용한 Query:

```sql
fields @timestamp, @message
| sort @timestamp desc
| limit 20
```

오른쪽 위 `Run queries` 버튼을 누르면 현재 Query를 실행한다.

> [!troubleshooting]
> 처음 `No data`가 표시된 직접 원인은 Log Group을 아직 선택하지 않은 상태였다. `Region: us-east-1`과 WAF Log Group을 모두 선택한 뒤 Query를 실행해야 한다.

---

## 5. 통제된 XSS 탐지 요청

새 Browser Tab에서 다음 URL로 요청했다.

```text
https://unoh.click/?q=%3Cscript%3Ealert(1)%3C%2Fscript%3E
```

URL Decode 결과:

```text
q=<script>alert(1)</script>
```

이 요청은 Query Argument `q`에 XSS Pattern을 넣어 AWS Managed Common Rule Set의 탐지 여부를 확인하기 위한 통제된 Test다.

---

## 6. Grafana에서 확인된 WAF Event

Query 실행 결과 WAF Event 1건이 표시됐다.

![[10_학습 노트/클라우드/_assets/Grafana 로컬 Docker에서 CloudWatch WAF 근실시간 관제/01_WAF_XSS_COUNT_로그_수신.jpg]]

**그림 1. Grafana Explore에서 CloudWatch WAF XSS 탐지 로그를 조회한 화면**

화면에서 확인된 Event 시각:

```text
2026-08-06 15:51:41.035
```

핵심 Field:

| Field | 확인값 | 의미 |
|---|---|---|
| `action` | `ALLOW` | Web ACL의 최종 처리 결과는 허용 |
| `terminatingRuleId` | `Default_Action` | 차단 Rule이 최종 종료 Rule이 되지 않음 |
| Managed Rule Group | `AWSManagedRulesCommonRuleSet` | AWS 관리형 공통 Rule Set이 검사 |
| 내부 Matching Rule | `CrossSiteScripting_QUERYARGUMENTS` | Query Argument의 XSS Pattern 탐지 |
| Web ACL Rule | `aws-managed-common-count` | 현재 Web ACL에서 관리형 Rule을 COUNT Mode로 사용 |
| `nonTerminatingMatchingRules[].action` | `COUNT` | 탐지만 기록하고 요청 처리는 계속 진행 |
| `conditionType` | `XSS` | 탐지 유형은 Cross-site scripting |
| `location` | `ALL_QUERY_ARGS` | 전체 Query Argument를 검사해 탐지 |
| `matchedFieldName` | `q` | `q` Parameter에서 Match |
| `matchedData` | `<`, `script` | XSS Pattern의 일부가 일치 |
| `httpRequest.uri` | `/` | 요청 Path |
| `httpRequest.args` | `q=%3Cscript%3Ealert(1)%3C%2Fscript%3E` | 실제 Query String |
| `httpRequest.httpMethod` | `GET` | HTTP Method |
| `httpRequest.host` | `unoh.click` | 요청 Host |
| Cookie | `REDACTED` | WAF Logging 설정에서 Cookie가 가려짐 |

공개 Repository에 기록하므로 Client IP, Request ID, JA3·JA4 Fingerprint 전체 값은 본문에서 제외했다.

---

## 7. `ALLOW`인데 XSS가 탐지된 이유

로그에는 서로 다른 계층의 Action이 함께 나온다.

```text
AWS Managed Rule 원래 동작
CrossSiteScripting_QUERYARGUMENTS → BLOCK

현재 Web ACL Override
aws-managed-common-count → COUNT

최종 Web ACL 처리
Default_Action → ALLOW
```

따라서 로그의 의미는 다음과 같다.

> XSS Pattern은 정상적으로 탐지됐지만, Training Application을 계속 접근할 수 있도록 해당 Managed Rule Group을 COUNT Mode로 실행했기 때문에 최종 요청은 허용됐다.

이는 탐지 실패가 아니다. 현재 실습 목적에 맞게 **탐지만 수행하고 차단하지 않는 상태**다.

SQLi 전용 Managed Rule Set도 Log에 포함됐지만 이번 Request에서는 SQL Injection Match가 확인되지 않았다.

---

## 8. Grafana Explore 화면 읽는 법

### `Run queries`

현재 Logs Insights Query를 AWS에서 실행한다.

### `Logs volume`

이번 Query Response에 포함된 Log Event를 시간대별로 간단히 표시한다. 화면에는 총 1건이 표시됐다.

### `Logs`

각 Event의 Raw JSON을 시간순으로 확인한다. 현재 화면에서 WAF Rule, HTTP Request, Match Detail을 직접 확인했다.

### `Table`

Raw Log 대신 Field를 열 형태로 비교할 때 사용한다. 이후 `parse` 또는 JSON Field Query를 정리하면 관제 화면에서 더 읽기 쉬워진다.

### 오른쪽 위 원형 화살표

현재 Explore Query를 다시 실행한다. Browser Reload와는 다르다.

---

## 9. 이번 단계에서 직접 확인된 것

```text
통제된 XSS Request
→ CloudFront WAF
→ AWS Managed Common Rule Set Match
→ COUNT Event 생성
→ CloudWatch Logs 저장
→ Local Grafana Explore에서 조회
```

직접 확인된 범위:

- Local Grafana의 CloudWatch Metrics API 연결 성공
- Local Grafana의 CloudWatch Logs API 연결 성공
- `us-east-1` WAF Log Group 조회 성공
- 통제된 XSS Query Argument 탐지 성공
- WAF Managed Rule가 XSS로 분류한 Match Detail 확인
- Cookie Redaction 확인
- CloudWatch → Grafana 관제 경로가 실제 Event를 반환함

---

## 10. 아직 확인하지 않은 것

- 공격 Request 발생 시각과 Grafana 표시 시각의 정확한 차이
- Dashboard Auto Refresh 설정
- WAF Event를 보기 좋은 Field별 Panel로 표현
- `COUNT`, `BLOCK`, Rule ID, Source Country 등의 집계 Panel
- DVWA Application Log와 같은 Request의 상관관계
- EKS Audit·CloudTrail 관제 Panel
- Grafana Alert Rule 또는 외부 알림

이번 화면은 CloudWatch 관제 경로의 **첫 Runtime 성공 증거**이며, 완성된 Dashboard는 아니다.

---

## 11. 다음 단계

다음 단계는 Explore Raw JSON을 그대로 보는 상태에서 WAF 전용 Dashboard로 전환하는 것이다.

우선순위:

```text
1. WAF Event Field를 읽기 쉬운 Query로 정리
2. 최근 XSS·SQLi Match Table
3. 시간대별 COUNT·BLOCK 추이
4. Rule별 탐지 건수
5. Dashboard Auto Refresh
6. Test Request 발생 시각과 표시 시각 측정
```

이후 S3·Athena는 같은 공격 구간을 상세 조사하고 Evidence로 보존하는 사후 분석 계층으로 사용한다.

---

## 12. 근거

### 직접 Runtime Evidence

- 2026-08-06 Local Grafana CloudWatch Data Source `Save & test` 성공
- 2026-08-06 Grafana Explore WAF Event Screenshot
- 사용자가 제공한 해당 WAF Event JSON

### Repository Source

- `bank-security-lab-infra/observability.tf`
  - AWS Managed Common Rule Set COUNT Mode
  - AWS Managed SQLi Rule Set COUNT Mode
  - WAF Logging Filter
  - Authorization·Cookie Redaction
- `bank-security-lab-infra/foundation/observability.tf`
  - `aws-waf-logs-aws-topology-edge` Log Group

### 관련 노트

- [[10_학습 노트/클라우드/Grafana 로컬 Docker에서 Athena 연결]]
