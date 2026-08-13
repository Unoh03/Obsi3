---
type: project-doc
status: active
created: 2026-08-13
project: 3차 프로젝트
project_moc: "[[20_팀 프로젝트/3차 프로젝트/00_3차프로젝트_목차]]"
---

# Wazuh SIEM 로그 분석과 대응

> [!important] 시작 경계
> [[와주 설치]]에서 CloudTrail이 Wazuh Dashboard에 실제로 집계되는 것까지 확인했다. 로그 수집은 단순 준비가 아니라 Wazuh의 첫 핵심 기능이다. 이 문서는 수집된 Event를 **읽고, 탐지하고, 사람이 이해할 사건으로 바꾸고, 대응으로 연결하는 단계**부터 기록한다.

## 왜 Wazuh를 도입했는가

프로젝트의 AWS 로그는 CloudTrail, WAF, CloudWatch Logs, S3 등 여러 위치에 분산되어 있다. 원본 JSON을 서비스별 Console에서 각각 찾는 방식으로는 하나의 사건을 빠르게 이해하고 대응하기 어렵다.

Wazuh를 통해 해결하려는 문제는 다음과 같다.

1. 흩어진 로그를 한곳에 모은다.
2. 원본 로그에서 사용자·행위·대상·IP·시각 같은 필드를 뽑는다.
3. 규칙에 맞는 중요한 행위를 Alert로 만든다.
4. 검색과 Dashboard를 통해 사건을 조사한다.
5. 필요한 정보를 Shuffle로 넘겨 사람이 읽을 사건 설명과 대응 Workflow로 연결한다.

## 역할 분담

| 구성요소 | 맡는 일 |
|---|---|
| Wazuh | 로그 수집, 필드 추출, Rule 판정, Alert 생성, 검색·시각화 |
| Shuffle | Alert 전달, 사건 정보 정리, 승인 또는 자동 대응 Workflow 실행 |

Wazuh가 원본 Event를 자동으로 구조화하고 기본 Rule 설명을 붙여주지만, 프로젝트 상황을 완전한 한국어 사건 보고서로 자동 해석해주는 것은 아니다. 프로젝트용 탐지 조건과 사람이 읽을 출력 형식은 직접 설계해야 한다.

## 현재 출발점

`Cloud security → Amazon Web Services`, 시간 범위 `Last 24 hours`에서 다음 Runtime 결과를 확인했다.

- Source: `cloudtrail`
- Account: `433048100798`
- Bucket: 프로젝트 Security Log Bucket
- Region: `ap-northeast-2`
- 시간대별 Amazon Rule Event 집계 표시

이는 다음 경로가 실제로 이어졌다는 증거다.

```text
CloudTrail
→ Security Log S3 Bucket
→ Wazuh Manager 수집·분석
→ Indexer 저장
→ Dashboard 검색·시각화
```

Dashboard의 Geolocation Map은 CloudTrail Event에 포함된 Source IP 위치 집계다. 이를 공격 발생 지역이나 공격자 위치로 단정하지 않는다.

### 과거 공격 Event를 먼저 찾는 이유

Wazuh는 공격 시점에 실행 중이어야만 Event를 받는 실시간 Push 전용 구조가 아니다. 현재 구성은 Wazuh Manager가 Security Log S3의 CloudTrail Object를 Polling하며, 실제 수집 경계도 다음처럼 적용돼 있다.

```text
only_logs_after = 2026-AUG-12
account = 프로젝트 AWS Account
region = ap-northeast-2
```

따라서 Wazuh를 설치하기 전에 실행한 `capital-one-20260812T025054Z` Baseline도 해당 날짜의 CloudTrail Object가 보존돼 있다면 최초 Polling 때 수집 대상이었다. Dashboard의 시간 범위를 넓혀 이미 Indexer에 저장된 Event를 검색하는 작업은 로컬 Docker의 Wazuh Indexer를 조회하므로 AWS Logs Insights·Athena Query 비용을 발생시키지 않는다.

반대로 `reparse` 또는 수집 DB 초기화 후 S3 Object를 다시 읽으면 S3 LIST·GET 요청과 중복 Alert가 발생할 수 있으므로 현재 단계에서는 실행하지 않는다. 다음 순서를 지킨다.

```text
기존 Wazuh Index에서 Baseline GetObject를 정확한 조건으로 검색
→ 없으면 해당 시간대 CloudTrail Object가 Wazuh에 수집됐는지 확인
→ 수집 누락이 확인된 경우에만 재수집 또는 새 TAKE 결정
```

처음 열어본 Karpenter `RunInstances` Dry Run Event는 Wazuh Field를 읽는 연습에는 유용하지만 대표 공격 Event가 아니다. Karpenter 비용 Guardrail은 별도 보강 목록으로 보내고, 이 문서에서는 Capital One Baseline의 S3 `GetObject`를 우선한다.

> [!todo]
> 보고서용으로 브라우저의 개인 탭이 보이지 않게 Dashboard 영역만 다시 캡처해 이곳에 추가한다.

## 완료 기준

- [ ] CloudTrail Event 한 건에서 행위자·API·대상·IP·시각·Rule을 해석
- [ ] 프로젝트 대표 공격 행위를 판정하는 Wazuh Rule 검증
- [ ] Alert를 사람이 바로 이해할 수 있는 사건 형식으로 정리
- [ ] Wazuh Alert를 Shuffle Workflow로 전달
- [ ] 승인 또는 자동 조치 후 재공격 차단 Evidence 확인

## 1. CloudTrail Event 읽기

`Events` 탭에서 Event 하나를 열고 다음 키워드에 해당하는 필드를 먼저 확인한다. 정확한 Field Path는 실제 Event를 펼친 뒤 확정한다.

| 질문 | 먼저 찾을 키워드 |
|---|---|
| 누가 했는가? | `userIdentity` |
| 무엇을 했는가? | `eventName` |
| 어떤 AWS 서비스인가? | `eventSource` |
| 어디에서 요청했는가? | `sourceIPAddress` |
| 언제 발생했는가? | `eventTime` |
| Wazuh가 어떻게 판정했는가? | `rule.id`, `rule.description`, `rule.level` |
| 원본은 어디에 있는가? | `aws.log_info.log_file`, `aws.log_info.s3bucket` |

모든 필드를 외우지 않고, 첫 Event 한 건을 위 질문에 맞춰 한국어로 해석하는 것부터 시작한다.

### 첫 검색 대상

새 공격을 실행하기 전에 기존 Baseline에서 다음 의미 조건을 모두 만족하는 Event를 찾는다. 실제 Dashboard Field Path는 검색 결과 JSON에서 확정한다.

```text
eventSource = s3.amazonaws.com
eventName = GetObject
actor = Primary Karpenter Node Role
object key = validation/capital-one-demo.csv
result = success
time window = capital-one-20260812T025054Z
```

이 Event가 확인되면 새 공격 없이 Custom Rule 작성으로 진행한다. 확인되지 않을 때만 수집 범위와 Marker를 먼저 조사하고, 그 뒤 새 `TAKE_ID`로 통제된 재실행 여부를 결정한다.
