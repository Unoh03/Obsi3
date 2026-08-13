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

### 0건 조사 결과

`Last 7 days`에서 대표 Key·`GetObject` 조건으로 검색했지만 결과는 0건이었다. 이를 과거 CloudTrail 수집 실패로 바로 판정하지 않고 Manager의 로컬 저장 파일과 설치된 Ruleset을 대조했다.

![[Pasted image 20260813141350.png]]

검색식과 `Last 7 days` 범위를 적용했지만 `No results match your search criteria`가 표시됐다. 이 화면만으로 과거 CloudTrail 미수집을 결론내리지 않고 아래의 기본 Rule·Archive 설정을 추가로 조사했다.

확인 결과:

- 8월 12일·13일 Wazuh Alert JSON은 실제로 보존돼 있다.
- 두 날짜 Alert에서 `GetObject`는 0건이다.
- 다른 S3 관리 Event는 Rule `80202` Alert로 저장돼 있어 CloudTrail 수집 자체는 동작했다.
- 기본 CloudTrail Rule `80202`는 `etc/lists/amazon/aws-eventnames` 목록에 있는 API만 Alert로 만든다.
- 해당 목록에는 `CreateBucket`은 있지만 `GetObject`는 없다.
- Manager의 `<logall_json>`은 `no`, Filebeat의 `archives.enabled`도 `false`여서 기본 Rule에 걸리지 않은 원본 Event는 Archive Index에 남지 않았다.

따라서 이번 0건의 원인은 다음과 같다.

```text
CloudTrail Object 수집
→ GetObject는 Wazuh 기본 Event 목록 밖
→ 기본 Alert 미생성
→ Raw Archive도 비활성
→ Dashboard 검색 결과 0건
```

이는 검색 비용이나 날짜 범위 문제가 아니다. **프로젝트가 원하는 Event를 보존·탐지하려면 원본 Archive와 Custom Rule을 직접 구성해야 한다는 확인 결과**다.

다행히 Gate 3 Evidence Bundle에는 다음 자료가 남아 있다.

```text
results/cloudwatch/capital-one-validation-getobject.json
→ 실제 GetObject 1행의 시간·Role·IP·Bucket·Key·Request ID

sanitized/cloudtrail/...20260812T0255Z....json
→ 대표 Key를 포함한 Sanitized CloudTrail 원본 Event 1건
```

Sanitized Event에서는 `sessionContext`가 마스킹됐으므로 Role 중첩 구조는 Gate 3 Query 결과와 Terraform의 예상 Role 이름을 함께 사용한다. 이를 실제 Runtime Event라고 다시 주장하지 않고, Custom Rule의 오프라인 입력을 만드는 근거로 사용한다.

다음 순서:

```text
Sanitized Event + Gate 3 Role Evidence로 Custom Rule 작성
→ wazuh-logtest 오프라인 검증
→ logall_json과 Archive Index 활성화
→ 새 통제 Event 1회
→ 실제 Custom Alert와 Raw Event 동시 확인
```

과거 전체 `reparse`와 새 공격 반복은 위 준비가 끝나기 전에는 실행하지 않는다.

## 2. Capital One Custom Rule 작성

Wazuh 기본 목록에서 빠진 대표 `GetObject`를 프로젝트 문맥으로 판정하기 위해 별도 `capital_one_rules.xml`을 만들었다. 기존 예제 `local_rules.xml`과 섞지 않아 프로젝트 Rule의 목적과 변경 범위를 분리했다.

![[Pasted image 20260813141811.png]]

Rule `100100`은 CloudTrail의 S3 `GetObject` 중 Primary Karpenter Node Role이 지정된 Primary Bucket의 `validation/capital-one-demo.csv`를 HTTP 200으로 읽은 경우만 Level 12 Alert 후보로 만든다. 일반적인 S3 읽기 전체를 공격으로 판정하지 않는다.

### Ruleset 정적 검사

저장 뒤 Manager를 재시작하기 전에 다음 명령으로 전체 Ruleset의 XML 문법과 Rule 참조를 검사했다.

```powershell
docker compose exec wazuh.manager /var/ossec/bin/wazuh-analysisd -t
$LASTEXITCODE
```

![[Pasted image 20260813141824.png]]

종료 코드 `0`을 확인했으므로 `capital_one_rules.xml`을 포함한 Ruleset의 정적 로드는 성공했다. 이는 실제 Event 정탐·정상 대조군과 Runtime Alert까지 증명하는 결과는 아니다.

### `wazuh-logtest` 오프라인 검증

저장한 Rule을 합성 CloudTrail JSON으로 검사했다. `wazuh-logtest`는 현재 Rules 파일을 별도로 읽어 판정하므로 이 단계에서는 실행 중인 Manager를 재시작하지 않았다.

| 입력 | Rule `100100` |
|---|---|
| Karpenter Node Role·대상 Bucket·대상 Key·HTTP 200 | **발생 — Level 12** |
| 정상 IAM User의 같은 Object 읽기 | 발생하지 않음 |
| 같은 Role·대상 Key지만 HTTP 403 | 발생하지 않음 |
| 같은 Role·HTTP 200이지만 다른 Object | 발생하지 않음 |

양성 입력의 Phase 3 결과:

```text
id: 100100
level: 12
description: CAPITAL-ONE: Karpenter node role successfully read the protected validation object.
Alert to be generated.
```

처음 `-q` 옵션으로 출력을 숨긴 뒤 문자열을 찾은 자동 검사에서는 네 입력 모두 `NOT_FIRED`로 잘못 판정했다. 상세 출력으로 다시 실행하자 양성은 Rule `100100`, 세 음성 대조군은 부모 Rule `80200` Level 0에서 끝났다. 따라서 최초 결과는 Rule 결함이 아니라 **검사 출력 수집 방식의 오류**로 폐기한다.

> [!todo]
> Dashboard의 `Ruleset Test`에서 동일 양성 JSON을 실행하고 Phase 3의 Rule `100100`·Level 12가 보이는 화면을 캡처한다.

> [!warning] 공개본 스크린샷
> 현재 Dashboard 캡처에는 AWS Account ID가 보인다. 내부 학습 Evidence로는 보존하되 보고서·발표·영상 공개본에서는 해당 영역을 Crop 또는 Mask한다. Account ID 자체가 Credential은 아니지만 프로젝트의 공개 범위를 최소화한다.
