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

## 3. Raw Archive 활성화 전 비용·보존 경계

여기서 말하는 **모든 Event**는 AWS 계정에서 생성되는 모든 로그가 아니라, 현재 설정된 수집 경로를 거쳐 **Wazuh Server까지 들어온 Event 전체**를 뜻한다.

```text
CloudTrail → S3 → Wazuh AWS Module
                        ↓
              이미 수집된 Event만 대상
                        ↓
        archives.json → Local Filebeat → Local Indexer
```

`logall_json`과 Filebeat Archive를 켜도 Wazuh의 S3 Polling 주기나 다운로드 범위가 자동으로 확대되지는 않는다. 따라서 이 변경 자체가 S3에서 새로운 대량 다운로드를 만드는 것은 아니다.

비용과 저장공간은 다음처럼 구분한다.

| 구분 | 이번 변경의 영향 |
|---|---|
| CloudTrail Data Event 기록 | 기존 AWS 비용 경로이며 이번 Archive 설정과 별개 |
| S3 저장·LIST·GET·인터넷 전송 | 기존 Wazuh Polling에서 발생하며 이번 설정으로 호출 범위가 자동 확대되지 않음 |
| `archives.json` | Local Docker의 `wazuh_logs` 사용량 증가 |
| `wazuh-archives-*` | Local Docker의 Indexer 저장공간과 CPU·메모리 사용량 증가 |

Wazuh 공식 문서도 Raw Archive가 Rule 발생 여부와 관계없이 Wazuh가 받은 Event를 저장하므로 디스크 사용량이 커질 수 있다고 경고한다. AWS 측 비용은 [CloudTrail Pricing](https://aws.amazon.com/cloudtrail/pricing/)과 [Amazon S3 Pricing](https://aws.amazon.com/s3/pricing/)을 별도로 본다.

### 프로젝트 보존 원칙

- Wazuh 입력은 프로젝트의 분석·탐지에 필요한 보안 로그로 제한한다.
- `wazuh-archives-*`의 목표 보존 기간은 **7일**로 둔다.
- Alert는 Raw Event보다 오래 보관하되, 실제 증가량을 확인한 뒤 기간을 확정한다.
- S3 원본의 Lifecycle은 이번 Local Wazuh 변경과 섞지 않고 별도로 검토한다.
- `docker compose down -v`, Volume 삭제, 과거 전체 `reparse`는 실행하지 않는다.

### 영구 설정 구성

Raw Archive를 Dashboard에서 검색하려면 서로 다른 두 스위치가 모두 필요하다.

| 설정 | 역할 |
|---|---|
| Manager `<logall_json>yes</logall_json>` | Wazuh가 받은 모든 Event를 `archives.json`으로 기록 |
| Filebeat `archives.enabled: true` | `archives.json`을 Local Wazuh Indexer의 `wazuh-archives-*`로 전달 |

Manager 설정은 기존 파일의 다른 내용을 유지하고 `<logall_json>` 값만 `no`에서 `yes`로 변경했다. 일반 텍스트 중복 저장을 피하기 위해 `<logall>`은 `no`로 유지했다.

![[Pasted image 20260813145759.png]]

Filebeat는 Docker 내부 파일을 직접 고치지 않았다. 컨테이너를 다시 만들 때 설정이 초기값으로 돌아가는 것을 막기 위해 Wazuh 4.14.7 기본 파일을 Host의 `single-node/config/filebeat.yml`로 복사하고 Archive만 활성화했다.

![[Pasted image 20260813150146.png]]

Compose에는 두 Host 설정을 시작 시 사용하는 Bind Mount를 구성했다.

```text
config/wazuh_cluster/wazuh_manager.conf
→ /wazuh-config-mount/etc/ossec.conf
→ 시작 과정에서 /var/ossec/etc/ossec.conf에 반영

config/filebeat.yml
→ /var/ossec/data_tmp/exclusion/etc/filebeat/filebeat.yml
→ 시작 과정에서 /etc/filebeat/filebeat.yml에 반영
```

AWS Credential Mount, `wazuh_etc`, `wazuh_logs`, `filebeat_etc`, Indexer Data Volume은 그대로 유지했다. Compose 문법 검사와 최종 Mount 해석을 통과한 뒤 다음 명령으로 Manager만 재생성했다.

```powershell
docker compose up -d --no-deps --force-recreate wazuh.manager
```

`--no-deps`는 Indexer와 Dashboard를 재생성하지 않고, `--force-recreate`는 변경한 Bind Mount를 Manager Container에 적용한다. 이 작업은 Named Volume을 삭제하지 않는다.

### 첫 적용 실패와 원인

첫 번째 재생성 명령은 `Started`로 끝났지만 Runtime을 확인하자 완전한 성공이 아니었다.

```text
Host wazuh_manager.conf: logall_json=yes
Runtime ossec.conf:      logall_json=no
Runtime Filebeat:        archives.enabled=true
archives.json:           없음
```

`Started`는 Container Process가 시작됐다는 뜻일 뿐, 의도한 두 설정이 모두 반영됐다는 증거는 아니었다. `docker inspect`와 Compose를 대조한 결과, 편집 과정에서 기존 Manager 설정 Bind 한 줄이 빠져 있었다.

```yaml
- ./config/wazuh_cluster/wazuh_manager.conf:/wazuh-config-mount/etc/ossec.conf
```

그 결과 Filebeat 설정만 연결되고 Manager는 `wazuh_etc` Volume에 남아 있던 이전 `logall_json=no` 설정으로 시작했다. 누락된 Bind를 복구하고 Compose 문법과 두 Mount를 다시 확인한 뒤 Manager를 한 번 더 재생성했다.

### 복구 후 Runtime 검증

두 번째 재생성 뒤 Host 파일이 아니라 **실행 중 Container와 Local Indexer**를 직접 확인했다.

| 검증 항목 | 실제 결과 |
|---|---|
| `wazuh.manager` 상태 | `Up` |
| Runtime `<logall_json>` | `yes` |
| Runtime `archives.enabled` | `true` |
| 전체 Ruleset 정적 검사 | `analysisd_exit=0` |
| Filebeat → Local Indexer 연결 | TLS·Connection·Server 응답 `OK`, `filebeat_exit=0` |
| Local Raw 파일 | `archives.json` 생성, 적용 직후 `732,248 bytes` |
| 일반 텍스트 Raw 파일 | `archives.log`는 `0 bytes` — 의도한 중복 방지 결과 |
| Local Archive Index | `wazuh-archives-4.x-2026.08.13` 생성 |
| 적용 직후 Index 상태 | `195 documents`, `673 KB` |

따라서 다음 경로는 Runtime으로 확인됐다.

```text
Wazuh가 받은 Event
→ archives.json 기록
→ Filebeat 전달
→ Local wazuh-archives-* 색인
```

> [!important] 증명 범위
> 이 결과는 Raw Archive 저장·색인 경로가 실제로 열렸다는 증거다. 현재 195건이 Capital One 대표 공격 Event이거나 Rule `100100` Alert라는 뜻은 아니다. 대표 시나리오의 Runtime 증명은 새 통제 Event를 한 번 발생시켜 Raw Event와 Custom Alert를 함께 확인해야 완성된다.

### Archive Index Pattern 생성·조회 검증

Raw Archive가 Local Indexer에 생성된 뒤, Dashboard에서 직접 검색할 수 있도록
`Dashboard management → Index patterns`로 이동했다.

![[Pasted image 20260813153941.png]]

Index Pattern 목록에서 `wazuh-archives-*`가 생성된 것을 확인했다.

![[Pasted image 20260813154017.png]]

Pattern의 시간 필드는 `timestamp`로 설정됐다. 생성 직후 791개 Field가 인식됐으므로,
Archive 문서를 시간 범위와 구조화 Field로 검색할 준비가 됐다.

![[Pasted image 20260813154057.png]]

`Explore → Discover`에서 `wazuh-archives-*`를 선택한 뒤 실제 Archive 문서가 조회되는지
확인했다.

![[Pasted image 20260813154205.png]]

![[Pasted image 20260813154234.png]]

| 검증 항목 | 실제 결과 |
|---|---|
| Index Pattern | `wazuh-archives-*` 생성 |
| 시간 필드 | `timestamp` |
| Discover Source | `wazuh-archives-*` 선택 |
| 캡처 당시 조회 결과 | 최근 24시간 `950 hits` |

> [!important] 증명 범위
> 이 결과는 Wazuh가 받은 Raw Event를 Dashboard에서 검색할 수 있다는 증거다. `950 hits`가 Capital One 대표 공격 Event이거나 Rule `100100` Alert라는 뜻은 아니다. 공격과 탐지의 연결은 새 통제 Event의 동일한 CloudTrail `eventID`를 Raw Index와 Alert Index에서 함께 확인해야 증명된다.

## 4. 새 통제 Event 실행 준비

### 4.1 왜 새 Event가 필요한가

기존 대표 공격은 Wazuh Archive 수집을 활성화하기 전에 실행했다. CloudTrail 원본이 S3에
남아 있더라도, 지금 만들려는 증거는 **같은 한 번의 공격이 Wazuh에서 Raw Event와
Alert로 함께 보이는지**를 확인하는 것이다. 따라서 현재 구성에서 새 통제 Event를 한 번
실행하고, 실제 CloudTrail `eventID`를 기준으로 두 결과를 연결한다.

```text
통제 공격 1회
→ CloudTrail이 S3 GetObject 기록
→ Wazuh가 CloudTrail 원본 수집
→ Raw Event를 Archive Index에 보존
→ Custom Rule 100100이 같은 Event를 Level 12 Alert로 판정
→ 동일한 eventID로 원본과 경보를 대조
```

`ExperimentId`와 `TakeId`는 실행 기록을 구분하기 위한 프로젝트용 이름이다. 이 값이
CloudTrail Event에 자동으로 들어가는 것은 아니므로, 먼저 실행 시각으로 범위를 좁힌 뒤
CloudTrail의 실제 `eventID`를 찾아야 한다.

### 4.2 두 스크립트의 역할

| 스크립트 | 역할 | 실제 공격 여부 |
|---|---|---|
| `Prepare-CapitalOneDemoData.ps1` | 탈취 대상으로 사용할 고정된 가짜 CSV를 S3에 준비하고 내용·메타데이터를 검증 | 공격 아님 |
| `Invoke-CapitalOneBaseline.ps1` | DVWA에서 시작해 IMDS 자격 증명을 얻고 고정된 S3 객체를 읽는 통제 공격을 실행 | 정확한 승인 문구를 넣었을 때만 실행 |

첫 번째 스크립트는 **안전한 실습용 데이터 준비**, 두 번째 스크립트는 **탐지 경로를
검증할 공격 Event 생성**을 담당한다. 둘을 나눈 이유는 공격을 다시 촬영하더라도 매번
같은 가짜 데이터와 같은 판정 기준을 사용할 수 있게 하기 위해서다.

### 4.3 `Prepare-CapitalOneDemoData.ps1`

이 스크립트는 다음 조건을 먼저 확인한다.

- 현재 AWS Account와 `capital-one-lab` Security Profile이 맞는지
- Foundation의 S3 Data Event 기록이 활성화됐는지
- Terraform이 만든 대상 S3 Bucket을 찾을 수 있는지
- 외부에서 주입된 임시 AWS Credential 환경 변수가 없는지

조건이 맞으면 `validation/capital-one-demo.csv`에 `FAKE_TRAINING_DATA` Marker가 포함된
5행짜리 가짜 CSV를 올린다. 업로드 후에는 Row 수와 SHA-256, S3 Object Metadata를 다시
읽어 예상한 파일이 맞는지 검증한다. 실제 Bucket 이름과 Credential은 기록 파일에
남기지 않는다.

처음 실행은 Preview만 보여주고 중단된다. 출력 내용을 확인한 뒤 정확한
`-ConfirmRun 'PREPARE CAPITAL ONE DATA'`를 넣어야 실제 업로드가 수행된다.

#### 이번 실행 결과

| 항목 | 결과 |
|---|---|
| 고정 Object Key | `validation/capital-one-demo.csv` |
| Training Marker | `FAKE_TRAINING_DATA` |
| Row 수 | 5 |
| Content SHA-256 | `625dad237e31a1ba4c6de1b0bf0153c2f62e56f5b6a18d97242d4c41665a4d9e` |
| Sanitized Record | `C:\Users\Unoh\Documents\aws-topology-evidence\preparation\capital-one-demo-data.json` |

### 4.4 `Invoke-CapitalOneBaseline.ps1`

이 스크립트가 만드는 통제 공격 흐름은 다음과 같다.

```text
DVWA Command Injection
→ DVWA Server가 IMDS에 요청
→ Node Role 이름과 임시 Credential 획득
→ 획득한 Role로 호출자 확인
→ 고정된 가짜 S3 Object GetObject
→ CloudWatch Alarm 전환 대기
→ 민감정보를 제외한 실행 결과 저장
```

실행 전에는 Active Daily Session, `minimal + capital-one-lab`, 남은 실습 시간, IMDS Hop
Limit, Node Role 경로, Pod Identity 비활성 상태, S3 Data Event, 탐지기와 Alarm 상태,
가짜 Object의 Marker·Hash를 검사한다. 하나라도 실습 계약과 다르면 공격 전에 중단한다.

첫 실행은 대상과 조건을 보여주는 Preview다. 실제 통제 공격은 정확한
`-ConfirmRun 'RUN CAPITAL ONE BASELINE'`을 넣어야 시작된다. 획득한 임시 Credential과
DVWA Cookie, 명령 응답은 출력하거나 Evidence에 저장하지 않으며, 종료 시 임시 파일과
환경 변수를 정리한다.

> [!warning] 시나리오의 정확한 표현
> DVWA에는 별도의 SSRF 실습 Module이 없으므로, 이 스크립트는 **Command Injection을 진입점으로 서버에서 IMDS 요청을 실행**한다. 따라서 Capital One 사고를 그대로 재현한 SSRF 공격이 아니라, `웹 취약점 → IMDS Credential 탈취 → S3 접근` 경로를 프로젝트 환경에 맞게 각색한 **Capital One 기반 검증 시나리오**라고 설명한다.

> [!tip] 핵심 증거 구성
> `공격 성공`, `Alarm 전환`, `같은 eventID의 Raw Event`, `Rule 100100·Level 12 Alert`를 차례로 연결한다. 한 화면만으로 모든 단계를 증명했다고 표현하지 않는다.

### 4.5 Runtime 실행 및 Alarm 확인

2026-08-13에 새 TAKE `capital-one-20260813T082735Z`를 실행했다. Preview에서 Runtime,
가짜 Object, Hash, Alarm의 시작 상태가 모두 계약과 일치한 뒤 정확한 승인 문구로 통제
공격을 실행했다.

![[Pasted image 20260813174238.png]]

| 검증 항목 | 실제 결과 |
|---|---|
| Runtime | `minimal + capital-one-lab` |
| IMDS Role 발견 | `aws-topology-primary-karpenter-node` 일치 |
| 임시 Credential 획득 | 성공, 값은 출력·저장하지 않음 |
| 고정 가짜 S3 Object 읽기 | 성공 |
| Marker / Row | `FAKE_TRAINING_DATA` / 5 |
| Content SHA-256 | 준비 단계의 고정 Hash와 일치 |
| CloudWatch Alarm | `OK`에서 새 `ALARM`으로 전환 |
| Alarm 전환 시각 | `2026-08-13 17:34:53 KST` |
| Sanitized Record | `C:\Users\Unoh\Documents\aws-topology-evidence\capital-one-20260813T082735Z\source\client\capital-one-baseline.json` |

> [!important] 이 화면이 증명하는 것
> Runner가 의도한 공격 경로로 가짜 S3 데이터를 읽고 CloudWatch Alarm 전환까지 확인했다. Wazuh가 같은 Event를 수집·판정했다는 증거는 다음 Alert 결과로 별도 확인한다.

### 4.6 Wazuh Custom Alert 확인

CloudTrail 파일 전달 뒤 Wazuh가 같은 `GetObject` Event를 수집했고, Custom Rule
`100100`이 Level 12 Alert로 판정했다. 첨부한 Alert JSON의 안전한 핵심 Field만 대조한
결과는 다음과 같다.

| Field | 확인값 |
|---|---|
| Alert Index | `wazuh-alerts-4.x-2026.08.13` |
| Wazuh Alert 시각 | `2026-08-13 17:37:28 KST` |
| Rule | `100100` |
| Level | 12 |
| Description | `CAPITAL-ONE: Karpenter node role successfully read the protected validation object.` |
| Event | `GetObject` |
| CloudTrail `eventID` | `ca03bf0a-35bb-46b8-a587-21626c8ada4e` |
| Actor Role | `aws-topology-primary-karpenter-node` |
| Object Key | `validation/capital-one-demo.csv` |
| HTTP Status | 200 |
| Location | `Wazuh-AWS` |

`wazuh-alerts-*`에서 `rule.id: 100100`으로 좁힌 결과는 정확히 1건이었고, 펼친 문서에서
Rule과 원본 AWS Field를 함께 확인했다.

![[Pasted image 20260813175953.png]]

Manager의 `archives.json`과 `alerts.json`에서도 동일한 `eventID`가 각각 확인됐다.
Dashboard의 `wazuh-archives-*`에서도 같은 시각·Rule·`eventID`의 Raw Event 1건을 직접
열었다.

![[Pasted image 20260813180904.png]]

따라서 다음 연결은 실제 Runtime과 Dashboard 화면에서 닫혔다.

```text
DVWA 통제 공격
→ IMDS Credential 획득
→ S3 GetObject 성공
→ CloudTrail 기록
→ Wazuh Raw Archive 수집
→ Rule 100100·Level 12 Alert 생성
```

Alert 화면과 Raw Event 화면은 각각 캡처했다. 다만 전체 JSON과 펼친 문서에는 Account,
Bucket, IP, 임시 Access Key ID 같은 운영 식별자가 포함될 수 있으므로 외부 보고서에는
원문 전체가 아니라 Rule·Level·Actor·Object·시각 등 필요한 Field만 선별한다.

### 4.7 찾기 어려웠던 이유와 영구 개선

이번 Alert가 없었던 것이 아니라 기본 화면과 Custom Rule의 분류가 맞지 않았다.

1. `TakeId`는 프로젝트 실행 기록에만 존재하며 CloudTrail과 Wazuh Event에는 자동으로
   들어가지 않으므로 Wazuh에서 `TakeId`로 검색할 수 없다.
2. `Amazon Web Services → Events` 화면은 `rule.groups: amazon`을 고정 적용한다.
3. 현재 Rule `100100`의 Group에는 `aws`, `aws_cloudtrail`, `capital_one` 등이 있지만
   `amazon`은 없어 AWS 전용 화면에서 숨겨진다.
4. 일반 사용자는 Field 이름과 검색 문법을 알아야 해서 기본 UI만으로 사건을 찾기 어렵다.

따라서 다음 두 개선을 Wazuh 사용성 작업으로 진행한다.

- [x] Rule `100100`에 `amazon` Group 추가 및 적용
- [ ] 향후 새 Alert가 AWS 전용 화면에도 나타나는지 검증
- [ ] `Capital One 탐지 현황` Saved View 또는 Dashboard를 만들어 검색식 없이 사건을 확인

![[Pasted image 20260813181144.png]]

#### `amazon` Group 적용 결과

| 항목 | 결과 |
|---|---|
| 수정 파일 | `/var/ossec/etc/rules/capital_one_rules.xml` |
| 변경 | Rule `100100` Group에 `amazon` 추가 |
| Rule 문법 검사 | `wazuh-analysisd -t` 성공, Exit Code 0 |
| 적용 | Wazuh Manager 재시작 완료 |
| 재시작 후 상태 | Manager·Dashboard 모두 `Up` |
| 탐지 조건 변경 | 없음. Event·Role·Object·HTTP Status 조건 유지 |

기존 Alert 문서는 이미 Index에 저장됐으므로 `amazon` Group이 소급 추가되지 않는다.
따라서 AWS 전용 화면 노출 여부는 **다음에 생성되는 새 Alert**로 검증하며, 이 확인만을
위해 오늘 공격을 다시 실행하지 않는다.

초보자용 화면에는 최소한 다음 정보만 한글로 먼저 보여준다.

```text
무슨 일?    보호된 S3 실습 파일을 Node Role이 읽음
위험도      높음
공격 경로   웹 취약점 → IMDS → Node Role → S3
탐지 상태   Rule 100100 경보 생성
다음 조치   승인된 대응 Playbook 실행
```

> [!note] Rule 파일의 지속성
> 2026-08-15에 `capital_one_rules.xml`을 Host의 `config/wazuh_cluster/rules/`로 복사하고 `docker-compose.yml`에서 Container Rule 경로에 Bind Mount했다. Manager 재생성 뒤 Mount Type `bind`, Host·Container SHA-256 일치, `wazuh-analysisd -t` Exit Code 0을 확인했다. 이제 `down -v`로 Named Volume을 지워도 Host Rule은 남지만, Host 장애까지 대비하려면 별도 Git 버전 관리가 필요하다.

### 4.8 현재 위치와 다음 작업

- [x] Dashboard에 `wazuh-archives-*` Index Pattern 생성
- [x] `timestamp` 시간 필드와 Discover 조회 확인
- [x] `minimal + capital-one-lab` Runtime Apply 및 사전 조건 확인
- [x] 고정된 가짜 S3 Object 준비 및 검증
- [x] `Invoke-CapitalOneBaseline.ps1` Preview 확인
- [x] 새 통제 공격 Event 1회 실행
- [x] Rule `100100`·Level 12 Alert 확인
- [x] Manager Local Raw·Alert에서 동일한 CloudTrail `eventID` 확인
- [x] Dashboard에서 Alert와 같은 `eventID`의 Raw 문서 화면 캡처
- [ ] 정상적인 S3 조회가 같은 Rule에 걸리지 않는지 오탐 확인
- [x] Rule `100100`에 `amazon` Group 추가·문법 검사·재시작
- [x] Rule `100100` Host 원본·Bind Mount·Hash 일치 검증
- [x] DVWA Command Injection 안전 감사 Event 구현·정적 테스트
- [x] 새 DVWA Image 배포 뒤 CloudWatch Logs·Wazuh Raw Archive·Index Runtime Event 확인
- [x] WAF·DVWA CloudWatch Logs를 Wazuh 입력으로 연결
- [x] WAF 실제 요청 Record와 DVWA 실제 Pod Record를 Raw Archive에서 확인
- [ ] WAF·DVWA Event를 사건으로 좁히는 Custom Rule·Filter 구현
- [x] ALB S3 Access Log를 Wazuh 입력으로 연결하고 실제 Record·주요 Field 검증
- [x] CloudFront 병렬 CloudWatch Logs를 3일 보존·`capital-one-lab` 전용으로 결정하고 Terraform Plan 검증
- [x] CloudFront Log를 Wazuh 입력으로 연결·검증
- [ ] 새 Alert의 AWS 전용 화면 노출 검증
- [ ] 초보자용 Saved View·Dashboard 구현
- [ ] Archive Index의 하루 증가량 기록
- [ ] 7일 Retention 적용 및 검증

기존 `minimal + hardened` Session에서는 Capital One Runner의 사전 검사가 공격 전에
실행을 거부했다. 이후 `minimal + capital-one-lab` Runtime에서 새 TAKE를 수행해 공격,
AWS Alarm, Wazuh 수집과 Custom Alert까지 확인했다.

Retention부터 먼저 만들지 않는다. 실제 하루 증가량을 확인한 뒤 적용해, 잘못된 조건으로
실습 Evidence를 먼저 삭제하는 일을 막는다.

### 4.9 Command Injection·IMDS 관측 공백 보강

WAF·Apache Access Log만으로는 Command Injection의 실행 결과와 IMDS 접근을 직접
설명할 수 없다. VPC Flow Logs도 IMDS `169.254.169.254` 트래픽을 수집하지 않는다.
우선 기존 DVWA JSON Audit 함수를 `low` Command Injection 경로에 연결해 다음 고정
정보만 `stderr`에 기록하도록 구현했다.

```text
event_type    command.execution
result        succeeded 또는 failed
resource      ec2_imds 또는 other
action        shell_command
status        output_returned 또는 no_output_returned
validation    request_target_classification
```

Request Body, 실제 Command, Command 출력, Cookie, Session, Credential은 기록하지 않는다.
`resource=ec2_imds`는 입력 문자열의 대상 분류이며 독립된 네트워크 접속 증거가 아니다.
독립 관측이 필요하면 Amazon VPC CNI Network Policy Event Log 같은 Runtime Sensor를
별도로 검증한다.

`command.execution`은 의도적으로 중립적인 이름이다. 이 `low` 화면은 정상적인 Ping을
실행해도 같은 감사 Event를 만들기 때문에, 원본 Event 이름부터 Command Injection
탐지라고 부르면 정상 요청까지 공격으로 단정하게 된다. Wazuh에서는
`event_type=command.execution`, `context.resource=ec2_imds`, `route`, 시간대와 다른 Source를
조합해 대표 공격을 판정한다.

또한 `result=succeeded`와 `status=output_returned`는 PHP `shell_exec`가 비어 있지 않은
출력을 돌려줬다는 뜻이다. IMDS가 실제 Credential을 반환했다거나 S3 `GetObject`가
성공했다는 뜻은 아니다. 전자는 고정 Marker 검증, 후자는 CloudTrail Event로 따로
증명한다.

배포 전 판정은 **DVWA Working Tree 구현·PHP 문법·비밀정보 차단 단위 테스트 완료**였다.
아래 Runtime 검증과 후속 Mapping 보정을 수행해 `Container stderr → Fluent Bit →
CloudWatch Logs → Wazuh Raw Archive → Index`까지 닫았다. Wazuh GUI 화면 캡처는 남아 있다.

#### 2026-08-16 배포 전 코드 검토 Evidence

수정 범위와 각 파일의 역할을 다음처럼 대조했다.

| 파일 | 변경 내용 | 배포 전 증명 범위 |
|---|---|---|
| `dvwa/includes/dvwaAudit.inc.php` | Command 대상에 고정 IMDS IPv4 URL이 있는지 `ec2_imds\|other`로 분류 | 원본 입력을 저장하지 않는 안전 분류 함수 |
| `vulnerabilities/exec/source/low.php` | Command 실행 뒤 `command.execution` JSON Audit Event 생성 | Source 연결 완료, 실제 Pod 출력은 당시 미검증 |
| `tests/test_audit_log.php` | 정상 대상·IMDS Root·Credential 경로 분류, 원본 Body·주소·비밀 표식 제외 검증 | Helper와 Event 계약의 정적 단위 테스트 |

테스트는 기존 로컬 Image `uns-dvwa:local`의 PHP를 사용하되 현재 Working Tree를 읽기
전용으로 Mount했다. `--network none`, `--read-only`, 임시 `/tmp` 조건으로 외부 통신과
Repository 쓰기를 막았다.

```text
PHP 8.5.9
dvwaAudit.inc.php: No syntax errors
low.php: No syntax errors
test_audit_log.php: No syntax errors
Audit log self-test passed.
```

`low.php`는 원래 CRLF 줄바꿈을 사용하므로 불필요한 전체 파일 변경을 피하기 위해 이를
보존했다. `git -c core.whitespace=cr-at-eol diff --check`로 실제 줄끝 공백 오류가 없음을
확인했다.

> [!info]- 재현·무결성 식별값
> - 검증 시각: `2026-08-16T13:50:55.7037878Z`
> - 기준 Commit: `f04458ef32c67d6fc495d73c3773ef0b95204d34`
> - Working Tree Diff Hash: `a7a4764594b68a2405c77a0da00ccfda54ee207f`
> - 테스트 Runtime Image ID: `sha256:6534ba1a2b23ebd4cfca9ad896ac42722621e6dddf331d29540bfb75890cae22`
> - `dvwaAudit.inc.php`: `8F97B364C4849BBF056CE2025EDC1C07FC049DEA9C0972DFEEE4B0C151EE4DF8`
> - `low.php`: `895024D15154CA3C0378A39436E04BE2F0A6470223D199B8AB253776A5B95131`
> - `test_audit_log.php`: `C47E5DB727F0880C6AB9B5AE8400AFF8363198DA3CF08E3AAA626A14BFCFD982`

이 Evidence는 **Source와 정적 테스트 완료**를 증명한다. 당시 미검증이던 Image
Build·ECR Push·Argo CD 배포와 실제 Log 도착은 다음 Runtime Evidence로 분리했다.

#### 2026-08-16 Build·Deploy·Runtime Evidence

##### Commit에서 새 Pod까지

| 단계 | 검증값 | 판정 |
|---|---|---|
| DVWA Source Commit | `a361cd6fb138a315c4591b87990f05048ac0a4db` | Audit 코드 3개 파일 Commit·`origin/main` Push |
| GitHub Actions | Run `31951154040` | `build_image`, `update_gitops` 모두 Success |
| ECR Image | `sha-a361cd6fb138a315c4591b87990f05048ac0a4db` | Immutable Tag 생성 |
| ECR Digest | `sha256:4219a56a3b6d1a091d24d29cf210271c5a4df7fd6a5da5d051e14eebbb98c219` | ECR·실행 Pod `imageID` 일치 |
| GitOps Commit | `8dfefe2f2e2cf0bec82e9f6077e59049b735c190` | `values.yaml` Image Tag 자동 갱신 |
| Argo CD | `Synced`, `Healthy`, Revision `8dfefe2...` | Automated Sync·Rollout 완료 |
| 실행 Pod | `dvwa-54d45864d4-dgwjg` | 새 Tag·Digest, Ready `true` |

[GitHub Actions Run 31951154040](https://github.com/Unoh03/Uns-DVWA/actions/runs/31951154040)은
`2026-08-16T13:54:24Z`에 시작해 `13:56:08Z`에 끝났다. Argo CD는 처음에는 새 Pod
Init 때문에 `Synced / Progressing`이었고, Rollout 뒤 `Synced / Healthy`가 됐다. 기존 Pod는
새 Pod가 준비될 때까지 Running 상태였으므로 검증 중 Service 중단은 관측되지 않았다.

##### 통제된 대표 공격과 Audit Event

Take `capital-one-20260816T140148Z`를 고정 Runner로 한 번 실행했다. Daily Runtime 재생성으로
가짜 S3 Object가 없어서 `Prepare-CapitalOneDemoData.ps1`로 `FAKE_TRAINING_DATA` 5행을
다시 준비했다. 이후 다음 결과를 확인했다.

```text
IMDS Role 발견                 성공
단기 Credential 획득           성공, 값 숨김
고정 가짜 S3 Object 읽기       성공, 5행·SHA-256 일치
CloudWatch Alarm 전이          성공
Credential 저장·출력           없음
```

CloudWatch Log Group `/aws/eks/aws-topology-primary/dvwa`에는 새 Pod가 만든 Audit Event가
정확히 2건 들어왔다.

| CloudWatch Event UTC | Event | Resource | Result | Image |
|---|---|---|---|---|
| `2026-08-16T14:03:40.042Z` | `command.execution` | `ec2_imds` | `succeeded` | `sha-a361cd6...` |
| `2026-08-16T14:03:43.243Z` | `command.execution` | `ec2_imds` | `succeeded` | `sha-a361cd6...` |

두 Event 모두 `route=/vulnerabilities/exec/`, `status=output_returned`,
`validation=request_target_classification`이며 원본 Command·Request Body·Credential은 없다.
정제된 DVWA Evidence에도 IMDS 주소 문자열, `SecretAccessKey`, `SessionToken` Label이 없다.

##### Wazuh Raw 도착과 첫 Index 실패

Wazuh는 10분 주기로 AWS Source를 Poll한다. 공격 Event가 마지막 Poll 직후 생성돼 다음
Poll `14:11:49Z`에서 수집됐고 Raw Archive에는 `14:11:57.227Z`에 들어왔다. 수집 지연은
각각 약 `497.227초`, `494.227초`다.

단순히 `command.execution` 문자열을 Grep하면 4건이 나왔다. 이 중 2건은 CloudWatch를
검증하려고 실행한 `FilterLogEvents` API의 `filterPattern`이 CloudTrail에 다시 기록된
**관측 행위 자체의 Log**였다. Raw Archive에서는 다음 구조로 좁히면 실제 DVWA Audit
Event 2건만 남았다.

```text
data.data.event_type: "command.execution"
data.data.context.resource: "ec2_imds"
```

하지만 이 조건으로 GUI에서 검색되지 않았다. 검색식이나 시간 범위 문제가 아니라 Filebeat가
두 문서를 Index에 넣으려다 다음 오류로 거부된 것이 직접 원인이었다.

```text
status=400
mapper_parsing_exception
failed to parse field [data.data] of type [keyword]
actual value: object
```

Fluent Bit은 Container의 JSON Log를 `mergeLogKey: "data"` 아래에 넣었다. Wazuh는
CloudWatch Record 전체를 다시 자신의 `data` 아래에 넣었고 최종 경로가 `data.data`가 됐다.
그런데 Wazuh 4.14.7 기본 Filebeat Template은 `data.data`를 `keyword`로 고정한다. 실제 값은
`event_type`, `result`, `context`를 가진 Object라서 문서 전체가 거부됐다. 같은 Raw `id`가
관측된 것은 사실이지만, 이번 GUI 미노출의 원인은 ID 충돌이 아니라 그보다 앞선 Mapping
거부였다. `auth.login.succeeded`, `authorization.access.denied`도 같은 구조라 함께 거부됐다.

##### `data.data` 충돌 보정과 Index Runtime 재검증

기존 Index를 삭제하거나 Mapping을 억지로 바꾸지 않았다. 애플리케이션 JSON을 넣는 Fluent
Bit Key만 다음처럼 구분했다.

```text
변경 전  Fluent Bit mergeLogKey=data      → Wazuh data.data      → keyword/Object 충돌
변경 후  Fluent Bit mergeLogKey=app_event → Wazuh data.app_event → 새 Object로 동적 Mapping
```

영구 원본 `templates/install-cluster-addons.sh.tpl`을 `app_event`로 수정하고
`tests/test-daily-automation.ps1`에 `data` 회귀 방지 계약을 추가했다. Test는 통과했다. 현재
서울 Cluster에도 Helm Release Revision `2`로 같은 값을 반영했고, Fluent Bit DaemonSet
2개 Pod의 Rollout과 실제 `/fluent-bit/etc/fluent-bit.conf`의
`Merge_Log_Key app_event`를 확인했다. CloudTrail·WAF·ALB·CloudFront 입력과 DVWA Pod는
변경하지 않았다.

새 Take `capital-one-indexfix-20260816T143645Z`를 실행해 가짜 S3 5행 읽기와 새 Alarm
전이를 다시 검증했다. Wazuh Poll `14:41:49Z~14:42:09Z` 뒤 다음 결과를 얻었다.

| 검증 지점 | 결과 |
|---|---|
| Raw Archive `app_event + command.execution + ec2_imds` | 2건 |
| 같은 Poll 구간 `mapper_parsing_exception` | 0건 |
| `wazuh-archives-4.x-2026.08.16` Index 직접 조회 | 2건, 서로 다른 Document ID |
| 두 문서의 Result·Resource | `succeeded`·`ec2_imds` |

따라서 **Raw Archive뿐 아니라 Wazuh Index 등록까지 Runtime 검증 완료**다. GUI에서는 기존
`data.data`가 아니라 다음 조건을 사용한다.

```text
data.app_event.event_type: "command.execution"
AND data.app_event.context.resource: "ec2_imds"
```

Data View는 `wazuh-archives-*`, 시간 범위는 `Last 24 hours`로 뒀다.

**캡처 — Mapping 보정 뒤 Wazuh Archives Index 2건**

![[Pasted image 20260816235516.png]]

화면 상단의 `2 hits`와 펼친 문서에서 `event_type=command.execution`,
`context.resource=ec2_imds`, `result=succeeded`, `route=/vulnerabilities/exec/`를 확인했다.
Wazuh `@timestamp=2026-08-16 23:41:55.898 KST`와 애플리케이션
`data.app_event.timestamp=2026-08-16T14:37:00Z`도 함께 보여 Source Event와 Poll 뒤
Index 도착 시각을 구분할 수 있다.

> [!warning] 내부 원본 Evidence
> 이 캡처에는 Client IP, Request ID, 내부 Pod IP, Container ID, Image Hash가 보인다.
> 내부 원본은 그대로 보존하되 보고서·발표본에는 필요한 Field만 Column으로 선택하거나
> 해당 값을 가린 별도 캡처를 사용한다.

이 결과는 **수집·구조화·중앙 검색 성공**이지 전용 Wazuh 탐지 Rule이나 Alert 완료를
뜻하지 않는다.

##### Evidence Bundle

원본 Bundle은 다음 위치에 있다.

```text
C:\Users\Unoh\Documents\aws-topology-evidence\capital-one-20260816T140148Z\
```

Manifest에는 CloudTrail 11 Object, CloudFront 1 Object, ALB 2 Object, WAF 2 Event,
DVWA 72 Event와 성공한 `GetObject` 검증 1행이 기록됐다. DR DVWA 0건은 서울 Primary
시나리오이므로 예상된 `Empty`다. `MissingContext=0`이며 Manifest SHA-256
`e2246afcd89798fd9e14dee6aea18eff72c6091304807b7f9fee8d3fa5ef3fc6`은 Sidecar와 일치한다.

첫 수집에서는 SSH의 정상 Host Key 안내가 `ArgoRevision` 앞에 섞였다. `daily-down.ps1`에
`LogLevel=ERROR`와 40자리 Commit SHA 검사를 추가하고 `test-daily-automation.ps1`을
보강한 뒤 Bundle을 다시 만들었다. 수정 후 `GitCommit=8dfefe2...`,
`ArgoRevision=8dfefe2...`, `ImageSha=sha-a361cd6...`이 서로 일치한다. 이 Terraform
Working Tree 수정은 아직 Commit 전이다.

> [!warning] 정제본 시간 Field 주의
> `sanitized/dvwa/events.json`의 중첩 Audit `timestamp`는 정제 과정에서 지역화된 문자열이
> 되어 Timezone 표식이 없다. Timeline에는 원본 CloudWatch Event의 Epoch Millisecond를
> UTC로 변환한 위 시각을 사용한다. 이는 Source Event 누락이 아니라 정제본 표현의 남은
> 보완점이다.

### 4.10 분산 Source 수집 확장 결과

2026-08-16 기준 Wazuh에 들어오는 로그 Source는 CloudTrail 하나에서 다섯 개로 늘었다.

| 사건 단계 | Source | Wazuh 도착 상태 | 지금 알 수 있는 것 |
|---|---|---|---|
| AWS API 사용 | CloudTrail S3 | 수집·Custom Alert 검증 완료 | 어떤 Role이 보호된 S3 Object를 읽었는가 |
| 외부 HTTP 요청 | WAF CloudWatch Logs | Raw Archive 수집 완료 | Edge에서 어떤 요청을 허용·차단했는가 |
| 애플리케이션 실행 | DVWA CloudWatch Logs | Raw Archive·안전 Audit Index 등록 검증 | 어떤 Pod에서 어떤 구조화 Event가 발생했는가 |
| Load Balancer 요청 | ALB S3 Access Log | Raw Archive·Field Parsing 확인 | 어떤 경로·상태 코드로 ALB를 통과했는가 |
| CDN 요청 | CloudFront S3 + 병렬 CloudWatch Logs | Raw Archive·JSON Field·Indexer 검색 확인 | 사용자 요청이 Edge에서 어떻게 처리됐는가 |

최초 연결 직후 Archive에서 실제 WAF 요청 4건과 `dvwa-*` Pod Record 13,817건을
확인했다. 특히 DVWA의 큰 수치는 공격 횟수가 아니라 과거 시점부터 Backfill된 일반
stdout·PHP Warning까지 포함한 Raw Event 양이다.

ALB 입력은 2026-08-16 Wazuh Manager가 `bucket type="alb"`, `path=alb/primary`를
주기적으로 실행하고 오류 없이 종료하는 것을 먼저 확인했다. 이어 Raw Archive에서
`source=alb` Record와 Request·ELB/Target Status·Client/Target IP·`trace_id`가 구조화된
Field로 저장된 것을 확인했다. 이는 **ALB 로그 수집·해석 성공**이며 전용 탐지 Rule이나
사건 Alert까지 완료됐다는 뜻은 아니다.

CloudFront는 Foundation의 기존 S3 장기 Evidence를 유지한 채, 같은 Delivery Source를
3일 CloudWatch Logs Hot Copy에도 병렬 연결했다. Foundation Apply는 `2 added, 1 changed,
0 destroyed`, 같은 입력의 Post-Apply Fresh Plan은 `0 change`였다. Daily
`minimal + capital-one-lab` Apply 뒤 `cloudfront_wazuh_logging_enabled=true`와 S3·CWL 두
Delivery를 확인했다.

검증 요청 `GET /wazuh-cloudfront-probe-20260816T094015835Z.txt`는 의도한 `404`를 반환했고,
CloudWatch Logs에 약 9초 뒤 도착했다. Wazuh 재수집 뒤 같은 시각·경로가
`wazuh-archives-4.x-2026.08.16`에서 두 건 검색됐다. 한 건은 CloudFront Edge JSON, 다른
한 건은 DVWA Pod Access Log다. 따라서 **CloudFront → CloudWatch Logs → Wazuh**와
**DVWA → CloudWatch Logs → Wazuh**가 같은 무해 요청으로 Runtime 검증됐다.

> [!note]- CloudFront Hot Copy 비용 경계
> CloudFront Standard Logging 자체에는 별도 활성화 요금이 없고, CloudWatch Logs 전송은
> 요청당 750바이트의 전달 크레딧이 적용된다. 이를 넘는 수집량과 저장량은 CloudWatch
> Vended Logs·Storage 요금 대상이므로 비용이 무조건 0원이라는 뜻은 아니다. 이 프로젝트는
> `capital-one-lab`에서만 Delivery를 만들고 전용 Log Group을 3일 보존해 범위를 줄였다.
> 공식 근거: [CloudWatch Pricing](https://aws.amazon.com/cloudwatch/pricing/),
> [CloudFront Standard Logging](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/standard-logging.html)

```text
로그가 여러 곳에 흩어짐
→ Wazuh가 한 Archive로 수집
→ 아직 Event가 너무 많고 의미가 섞여 있음
→ 프로젝트 Rule·Filter로 사건 후보를 좁힘
→ 초보자용 Dashboard에서 원인과 다음 조치를 보여줌
→ Shuffle Playbook으로 승인된 대응 실행
```

현재는 프로젝트의 첫 번째 문제인 **분산 로그 수집**을 필수 5-Source 범위에서 해결했고,
Capital One 관련 Event를 별도 Filter와 Dashboard로 좁혔다. 다만 전용 Custom Alert는
CloudTrail `GetObject` 하나이며 WAF·ALB·DVWA·CloudFront의 관련 Event는 사건을 해석하는
보조 Evidence다. Shuffle 자동 대응과 실제 사용자 검증은 아직 닫히지 않았다.

#### 현재 보이는 범위와 공백

- CloudTrail의 `GetObject`는 Rule `100100`으로 탐지·경보까지 확인했다.
- WAF 요청과 DVWA Pod Log는 한곳에서 검색할 수 있지만 아직 전용 탐지 규칙이 없다.
- DVWA 안전 감사 Image의 Build·Push·Argo CD 배포와 CloudWatch·Wazuh Raw·Index Runtime을 확인했다.
- ALB Record로 WAF와 애플리케이션 사이의 요청 경로·상태 코드를 보강할 수 있다.
- 이번 확인 Record는 `user_agent=Amazon CloudFront`였고 `client_ip`도 CloudFront 측
  주소였다. 따라서 CloudFront를 거친 요청의 실제 요청자 IP는 CloudFront·WAF 로그와
  함께 해석해야 한다.
- CloudFront S3 JSON은 Wazuh `custom` Loader 형식과 맞지 않고 Wazuh 4.14.7에 전용
  CloudFront Bucket Type도 없다. 기존 S3·Athena 경로는 유지하고, 같은 Delivery Source에
  `us-east-1` JSON CloudWatch Logs Destination을 추가하는 방식으로 확정했다.
- CloudFront Wazuh Log Group은 3일 보존하고 `capital-one-lab`에서만 Delivery한다.
  2026-08-16 Foundation·Daily Apply, 로컬 Reader 최소 권한, Wazuh 영구 입력과 실제
  CloudFront Record의 Raw Archive·Indexer 도착까지 확인했다.
- CloudFront Standard Log는 지연되거나 누락될 수 있으므로 실시간 탐지 Trigger가 아니라
  Edge 보조 Evidence로 사용한다. 주 탐지는 CloudTrail Custom Alert를 유지한다.
- `resource=ec2_imds` 감사 값은 요청 대상 분류이지, Pod에서 IMDS까지의 독립 네트워크
  증거는 아니다.

#### 다음 작업 순서

1. **완료:** AWS에서 ALB Prefix Reader Policy가 실제 저장됐는지 재조회한다.
2. **완료:** Wazuh에 공식 `alb` Bucket 입력을 추가하고 실제 ALB Record를 확인한다.
3. **완료:** CloudFront 병렬 CloudWatch Logs를 Apply하고 실제 요청의 Wazuh Raw Archive·Indexer 도착을 확인한다.
4. **완료:** 새 DVWA Image를 배포해 안전 감사 Event의 CloudWatch Logs·Wazuh Raw·Index 도착을 확인한다.
5. **완료:** Capital One 사건용 CloudFront·WAF·ALB·DVWA·CloudTrail Filter와 한글 Dashboard를 만든다.
6. **다음:** [[Wazuh 대시보드 미니 실습]]으로 운호가 보존 Event를 조사한다.
7. 다른 조원이 검색식 없이 3분 안에 사건을 설명하는지 사용성 Test를 한다.
8. 탐지 결과를 Shuffle의 승인형 대응 Playbook으로 넘긴다.

### 4.11 중간정리 — 시연 로그의 범위와 Gate 4 완료 기준

2026-08-16에 “모든 로그를 모은다”는 표현의 범위를 다시 정리했다. 목표는 AWS 계정의
모든 로그를 무작정 Wazuh에 넣는 것이 아니다.

> **서울 Primary에서 수행하는 Capital One 기반 대표 시나리오가 만드는 공격·탐지
> Evidence를 빠짐없이 수집하고, 초보자도 검색식 없이 사건을 이해하게 만드는 것**이
> Gate 4의 목표다.

#### Gate 4 필수 Source 다섯 개

| 순서 | Source | 시연에서 답하는 질문 | 현재 Wazuh 상태 |
|---:|---|---|---|
| 1 | CloudFront Access Log | 공격 요청이 CDN Edge에 도착했는가 | Raw Archive·JSON Field·Indexer 검색 확인 |
| 2 | WAF Log | 어떤 Rule로 검사했고 허용·차단했는가 | Raw Archive 실제 요청 확인 |
| 3 | Primary ALB Access Log | 요청이 Load Balancer를 거쳐 DVWA에 도달했는가 | Raw Archive·주요 Field Parsing 확인 |
| 4 | DVWA·Apache·안전 Audit Log | 애플리케이션에서 무엇이 실행됐는가 | 새 Audit Image·CloudWatch·Wazuh Raw·Index Runtime 확인 |
| 5 | CloudTrail STS·S3 Event | 탈취 Role로 어떤 AWS API를 성공시켰는가 | Raw·Rule `100100` Alert 확인 |

따라서 현재는 **5/5 Source의 Wazuh Runtime 수집을 확인한 상태**다. 다섯 Source의 Raw
Event 도착은 수집 성공이지, 하나의 공격 Timeline이나 탐지·해석 완료를 뜻하지 않는다.

#### EKS는 왜 여섯 번째 공격 Source가 아닌가

DVWA Pod·Apache Log가 이미 EKS 위에서 실행되는 **워크로드 로그**다. 별도로 활성화된
EKS Control Plane의 `api`·`audit`·`authenticator` Log는 Command Injection이나
Pod→IMDS 요청을 직접 기록하지 않는다.

```text
공격 단계
CloudFront → WAF → ALB → DVWA → CloudTrail
                         └─ Pod→IMDS는 직접 네트워크 Evidence 없음

대응·배포 단계
Shuffle → GitHub → Argo CD → EKS API Audit → Deployment → 새 Pod
```

따라서 EKS Control Plane Log는 Gate 4의 공격 Source가 아니라 **Gate 7의 Argo CD
배포·대응 Evidence**로 검증한다. VPC Flow Logs도 IMDS `169.254.169.254` Traffic을
수집하지 않으므로 이 공백을 메우지 못한다. GuardDuty Finding은 이번 공격에서 0건이며,
DR DVWA는 서울 Primary 시나리오 밖이다.

#### 수집 완료와 관제 완료의 차이

각 Source는 다음 단계를 따로 판정한다.

```text
설정 존재
→ IAM 접근 성공
→ 실제 Raw Event 수집
→ 필요한 Field 파싱
→ 같은 사건 Timeline에서 사용
→ 탐지 Rule·오탐 검증
```

CloudTrail은 Custom Alert까지 닫혔고, WAF·ALB·DVWA·CloudFront는 관련 Raw Event와 필요한
Filter를 Dashboard에서 사용한다. CloudFront JSON의 Method·Path·Status·Edge Request ID와
새 DVWA 안전 Audit Event의 Runtime도 확인했다. 다만 이 네 Source에 대표 시나리오 전용
Custom Alert가 생긴 것은 아니다. CloudFront 경유 ALB Record의 Client는 CloudFront 측
주소였으므로 실제 요청자와 Edge 처리는 CloudFront·WAF Event로 보강해야 한다.

#### 초보자용 Dashboard의 합격 기준

Dashboard는 Raw JSON을 나열하는 화면이 아니라 다음 질문에 답하는 사건 화면이어야 한다.

```text
무슨 일이 발생했는가
언제 발생했고 위험도는 무엇인가
어떤 요청·Role·Resource가 관련됐는가
어느 계층에서 보였고 어디는 보이지 않는가
왜 Alert가 됐는가
현재 대응 상태와 다음 조치는 무엇인가
```

다른 조원이 WQL·DQL 검색식을 입력하지 않고 3분 안에 사건 내용, 영향 대상, 탐지 근거,
관측 공백, 다음 조치를 설명할 수 있어야 Gate 4를 통과한다. 화면에는 사건 요약, 공격
경로, 시간순 Timeline, 탐지 근거, 대응 상태, 다음 조치와 원본 Drill-down을 둔다.

#### 현재 Checkpoint와 다음 순서

```text
[완료] CloudTrail Raw·Rule 100100 Alert
[완료] WAF Raw 요청 Record
[완료] ALB Raw 요청 Record·주요 Field Parsing
[완료] DVWA Raw Pod Record
[완료] CloudFront 3일 Hot Copy Foundation·Daily Apply·Wazuh 실제 Record 확인
[완료] 새 DVWA 안전 Audit Image Build·Argo 배포·CloudWatch·Wazuh Raw·Index Runtime 확인
[완료] Wazuh GUI Evidence·필수 5-Source Filter·한글 Dashboard·Saved Object 읽기 검증
[다음] 보존 Event 기반 운호 안내형 미니 실습
[대기] 다른 조원의 3분 무검색 사용성 Test와 동일 실행 5-Source 시간창 검증
[이후] Wazuh Alert → Shuffle Gate 5
```

### 4.12 GUI에서 직접 확인할 출발점

2026-08-16 Runtime 검증으로 `wazuh-archives-4.x-2026.08.16`에 아래 Probe가 두 건
Index된 것을 확인했다.

```text
/wazuh-cloudfront-probe-20260816T094015835Z.txt
```

공통 조회 조건은 Wazuh Dashboard의 `Explore → Discover`, Data View
`wazuh-archives-*`, 시간 범위 `Last 24 hours`다.

#### CloudFront Edge 원본

```text
data.cs-uri-stem: "/wazuh-cloudfront-probe-20260816T094015835Z.txt"
```

**캡처 1 — CloudFront Edge JSON 1건**

![[Pasted image 20260816185628.png]]

`data.cs-method=GET`, `data.cs-uri-stem=<Probe 경로>`, `data.sc-status=404`,
`data.x-edge-response-result-type=Error`를 확인했다. 이는 요청이 CloudFront Edge에
도착해 Origin으로 전달됐고 최종 `404` 응답을 반환했다는 원본 Evidence다.

화면의 Rule `1002`·Level 2 `Unknown problem somewhere in the system`은 CloudFront의
`Error` 값을 Wazuh 기본 Rule이 일반 오류로 분류한 결과다. 프로젝트가 의도한 전용
탐지 Rule은 아니므로 **수집 성공을 탐지 완료로 해석하지 않는다.**

#### DVWA Pod 원본

```text
data.log: *wazuh-cloudfront-probe-20260816T094015835Z.txt*
```

`data.log`는 `keyword` Field다. 와일드카드 `*`를 따옴표 안에 넣으면 문자 그대로
해석되어 0건이 되므로, 부분 일치 검색에서는 위처럼 따옴표 밖에 둔다. 실제 Archives
Index에서 기존 검색식은 0건, 수정한 검색식은 1건으로 대조했다.

**캡처 2 — DVWA Pod Access Log 1건**

![[Pasted image 20260816185928.png]]

`data.log`에서 같은 Probe 경로의 `GET`, HTTP `404`, User-Agent `Amazon CloudFront`를
확인했다. `data.kubernetes.namespace_name=dvwa`와 `data.kubernetes.pod_name`은 이 요청이
서울 EKS의 DVWA Pod까지 도달했음을 보여준다.

#### 두 화면을 함께 읽는 법

| 비교 항목 | CloudFront 원본 | DVWA Pod 원본 | 판정 |
|---|---|---|---|
| 원본 요청 시각 | `09:40:39 UTC` | `09:40:39 UTC` | 일치 |
| Method | `GET` | `GET` | 일치 |
| Path | 동일 Probe 경로 | 동일 Probe 경로 | 일치 |
| HTTP Status | `404` | `404` | 일치 |
| 관측 위치 | CDN Edge | EKS의 DVWA Pod | 서로 다른 계층 |

Wazuh의 Archive 시각은 DVWA가 `18:42:00 KST`, CloudFront가 `18:42:09 KST`로 약 9초
차이 난다. 이는 서로 다른 요청이라는 뜻이 아니라, DVWA CloudWatch Logs와 CloudFront
CloudWatch Logs를 Wazuh가 읽어 들인 시점이 달랐기 때문이다.

따라서 이번 Probe는 다음 범위를 Runtime으로 증명한다.

```text
사용자 요청
→ CloudFront Edge에서 관측
→ Origin·ALB를 거쳐 DVWA Pod에서 관측
→ 서로 다른 두 로그가 Wazuh Archives Index에서 중앙 조회됨
```

> [!warning] 공개 Screenshot 주의
> 현재 캡처에는 Client IP, Edge Request ID, 내부 Host·Pod IP, Image·Container Hash처럼
> 공개본에서 불필요한 값이 보인다. 보고서·발표용으로 사용할 때는 해당 값을 가리거나
> 필요한 Field만 Column으로 선택해 다시 캡처한다. Credential·Cookie·Command 응답은
> 화면에 포함하지 않는다.

#### 현재 판정

- **완료:** CloudFront·WAF·ALB·DVWA·CloudTrail 5개 Source의 실제 Wazuh 수집
- **완료:** 같은 무해 Probe의 CloudFront Edge·DVWA Pod 원본을 GUI에서 비교
- **완료:** 새 DVWA 안전 Audit Image의 Build·Push·Argo CD 배포와 CloudWatch·Wazuh Raw Runtime Event
- **완료:** `data.data` Mapping 충돌 보정과 새 `command.execution` 2건의 Wazuh Index 등록
- **완료:** `command.execution` 2건의 Wazuh GUI 확인·내부 원본 캡처
- **미완료:** 보고서용 Field 선택·민감 운영 식별자 마스킹 캡처
- **미완료:** 대표 공격 5-Source Timeline과 Source별 전용 Filter·탐지 의미 정리
- **미완료:** 검색식 없이 읽는 한글 Saved View·Dashboard와 다른 조원의 3분 사용성 Test
- **이후:** Wazuh Alert를 Shuffle Gate 5로 전달

이 검색식은 **현재 수집 성공을 배우고 증명하기 위한 임시 출발점**이다. 최종 Gate 4는
검색식을 사용자가 직접 입력하지 않아도 되는 Saved View·한글 Dashboard와 3분 사용성
Test까지 별도로 구현해야 한다.
![[Pasted image 20260817005126.png]]![[Pasted image 20260817005130.png]]![[Pasted image 20260817005134.png]]

## 5. 초보자용 AWS 보안관제 Dashboard 구축

### 왜 별도 Dashboard를 만드는가

`Discover`는 원본 Event를 조사하는 화면이라 Field와 검색식을 알아야 한다. 반대로
Metric만 여러 개 놓으면 숫자는 잘 보이지만 평소 흐름과 변화가 보이지 않는다. 최종 화면은
다른 조원이 DQL을 직접 입력하지 않아도 다음 순서로 환경과 사건을 읽게 만드는 것이
목적이다.

```text
평상시: 전체 웹 요청·AWS API 활동의 추세와 분포 확인
→ 이상 징후 또는 중요 경보 발견
→ 사건 상세 화면에서 관련 계층과 근거 확인
→ 현재 대응 상태와 다음 조치 확인
→ 필요할 때만 원본 Event로 Drill-down
```

이를 위해 Dashboard를 다음 두 화면으로 분리한다.

1. **`AWS 보안관제 현황`**: 평상시 웹 요청·응답·AWS API 활동과 중요 경보를 함께 보는
   Overview
2. **`AWS 보안 사건 상세`**: 경보 발생 뒤 관련 Event·탐지 근거·대응 상태를 조사하는
   Incident View

두 화면의 겉모습과 이름은 특정 사고에 종속되지 않게 유지한다. Capital One이라는 이름은
보고서의 검증 시나리오와 상세 Evidence에서만 밝힌다. Incident View의 내부 Filter는
우선 현재 Runtime으로 검증 가능한 Capital One 기반 대표 시나리오를 사용한다.

여기서 **전체 트래픽**은 현재 Wazuh에 연결된 Source로 볼 수 있는 웹 요청 흐름과 AWS API
활동을 뜻한다. VPC Flow Logs를 이용한 전체 Network Flow나 Packet 관측을 뜻하지 않는다.

### 이번에 배운 Wazuh 화면 구성

| 구성 요소 | 역할 | 이번 프로젝트에서의 사용 |
|---|---|---|
| `wazuh-archives-*` | Wazuh가 받은 Raw Event 조회 | CloudFront·WAF·ALB·DVWA·CloudTrail 근거 |
| `wazuh-alerts-*` | Rule이 경보로 판정한 Event 조회 | Rule `100100`과 중요 경보 |
| Saved Search | Data View·검색식·Filter·선택 Field 저장 | 사용자가 검색식을 다시 입력하지 않는 조사 화면 |
| Visualization | Count·시계열·표·안내문을 Panel로 저장 | Metric, Line·Area, Markdown |
| Dashboard | 여러 Saved Object를 한 화면에 배치 | 사건 요약에서 원본 Drill-down까지 제공 |

Wazuh의 Rule Level 체계 자체는 제품 기능이다. 다만 Custom Rule `100100`을
`level="12"`로 정한 것은 프로젝트 결정이며, 다음 조건을 모두 만족한 성공 Event만 높은
신뢰도의 Alert로 판정한다.

```text
지정된 Karpenter Node Role
+ 지정된 Primary Bucket
+ validation/capital-one-demo.csv
+ S3 GetObject 성공
```

모든 WAF·CloudFront·ALB·DVWA Event를 Level 12로 올린 것이 아니다. Dashboard에서
`rule.level >= 10`을 **중요 경보**로 보여주는 기준도 이번 Dashboard에서 정한 표시 기준이다.

### Source별 역할과 화면 배치 원칙

| Source | Overview에서의 역할 | Incident View에서의 역할 |
|---|---|---|
| WAF | 검사한 웹 요청 수, `ALLOW`·`BLOCK` 추세 | 요청 URI·판정·Rule 근거 |
| ALB | Origin 응답 상태 `2xx`·`3xx`·`4xx`·`5xx` 분포 | 실제 Backend 전달·응답 근거 |
| CloudTrail | AWS API 활동량과 주요 AWS Service | Role·API·Resource 접근 근거 |
| DVWA 안전 Audit | 일반 트래픽이 아니라 Workload의 의심 행위 | `command.execution`·`ec2_imds` 근거 |
| CloudFront | 전달 지연이 있어 실시간 Overview의 기준으로 사용하지 않음 | 가장 바깥 Edge 요청의 보조 Evidence |

같은 요청이 CloudFront·WAF·ALB·DVWA에 각각 기록되므로 이 수치를 더해 `전체 요청`으로
표현하지 않는다. Overview의 웹 요청 기준은 WAF가 실제 검사한 Request로 통일한다.
CloudFront는 3일 Hot Copy와 전달 지연이라는 조건이 있으므로 Incident View의 보조
Evidence로 둔다.

### Dashboard A — `AWS 보안관제 현황`

#### 화면 배치

```text
1행: 요약 Metric 4개
     WAF 검사 요청 | WAF 차단 요청 | ALB 오류 응답 | 중요 경보

2행: 웹 트래픽
     WAF 요청 추이(넓게) | ALB 응답 상태 분포

3행: AWS 활동
     CloudTrail API 활동 추이(넓게) | 주요 AWS Service

4행: 최근 중요 경보 Saved Search
```

#### Saved Object 계획

| 순서 | Saved Object 이름 | 종류·Data View | 조건·표현 | 상태 |
|---:|---|---|---|---|
| 01 | `[AWS-SOC] 01 중요 경보` | Metric · `wazuh-alerts-*` | `rule.level >= 10`, Count | 완료 |
| 02 | `[AWS-SOC] 02 WAF 검사 요청` | Metric · `wazuh-archives-*` | `data.webaclId:*`, Count | 완료 |
| 03 | `[AWS-SOC] 03 WAF 차단 요청` | Metric · `wazuh-archives-*` | `data.action: "BLOCK"`, Count | 완료 |
| 04 | `[AWS-SOC] 04 ALB 오류 응답` | Metric · `wazuh-archives-*` | ALB `4xx`·`5xx`, Count | 완료 |
| 10 | `[AWS-SOC] 10 웹 요청 추이` | Line · `wazuh-archives-*` | WAF Event Count / `timestamp`, `data.action`으로 분리 | 완료 |
| 11 | `[AWS-SOC] 11 ALB 응답 상태` | Vertical Bar · `wazuh-archives-*` | `data.aws.elb_status_code`별 Count | 완료 |
| 12 | `[AWS-SOC] 12 AWS API 활동 추이` | Line · `wazuh-archives-*` | CloudTrail Count / `timestamp` | 완료 |
| 13 | `[AWS-SOC] 13 주요 AWS Service` | Horizontal Bar · `wazuh-archives-*` | `data.aws.eventSource` 상위 10개 | 완료 |
| 20 | `[AWS-SOC] 20 최근 중요 경보` | Saved Search · `wazuh-alerts-*` | `rule.level >= 10`, 안전한 Field만 표시 | 완료 |

첫 Panel은 시간 범위 `Last 7 days`, DQL `rule.level >= 10`에서 Count `1`을 확인하고
`[AWS-SOC] 01 중요 경보`로 저장했다. 현재 이 1건은 Rule `100100`의 Level 12 Alert다.

### Dashboard B — `AWS 보안 사건 상세`

#### 화면 배치

```text
1행: 중요 경보 | Workload 의심 행위 | 보호 데이터 접근 | 대응 연결 상태
2행: 사건 단계별 Evidence 수를 하나의 Horizontal Bar로 표현
3행: 5개 Source의 Wazuh 수집 시각 흐름
4행: 탐지 근거 Saved Search | 분석 결론·다음 조치 Markdown
```

5개 공격 단계를 Metric 5개로 늘어놓지 않는다. 하나의 `Filters` 기반 Horizontal Bar로
묶어 서로 비교하고, 아래 시계열에서 언제 Wazuh에 도착했는지 확인한다.

| 순서 | Saved Object 이름 | 종류·Data View | 조건·표현 | 상태 |
|---:|---|---|---|---|
| 01 | `[AWS-SOC] 01 중요 경보` | 기존 Metric 재사용 | `rule.level >= 10` | 완료 |
| 31 | `[AWS-SOC] 31 Workload 의심 행위` | Metric · `wazuh-archives-*` | `command.execution` + `ec2_imds` | 완료 |
| 32 | `[AWS-SOC] 32 보호 데이터 접근` | Metric · `wazuh-alerts-*` | `rule.id: "100100"` | 완료 |
| 33 | `[AWS-SOC] 33 대응 연결 상태` | Markdown | 현재 수동 분석, Shuffle 미연결을 명시 | 완료 |
| 40 | `[AWS-SOC] 40 사건 단계별 Evidence` | Horizontal Bar · `wazuh-archives-*` | CloudFront·WAF·ALB·DVWA·CloudTrail 5개 Filter | 완료 |
| 41 | `[AWS-SOC] 41 관련 Event 수집 흐름` | Line · `wazuh-archives-*` | 5개 Filter / `timestamp` | 완료 |
| 50 | `[AWS-SOC] 50 탐지 근거` | Saved Search · `wazuh-alerts-*` | Rule `100100`, 안전한 Field만 표시 | 완료 |
| 51 | `[AWS-SOC] 51 분석과 다음 조치` | Markdown | 발생 내용·영향·관측 공백·다음 조치 | 완료 |

### 구현 완료와 사용성 실습의 분리

2026-08-17에 Wazuh 내부 Saved Object를 읽기 전용으로 검사해 Dashboard 2개,
Visualization 14개, Saved Search 2개를 확인했다. 두 Dashboard의 Panel 구성과 저장된
`Last 15 minutes`, Saved Search의 안전한 6개 Field·최신순 정렬·불필요한 Exists Filter
0개, ALB 응답 코드 오름차순을 확인했다.

화면 구현과 사람이 실제로 읽을 수 있다는 주장은 다르다. 첫 사용 학습과 다른 조원의 3분
무검색 Test는 [[Wazuh 대시보드 미니 실습]] 대본으로 분리한다. 현재 보존된 다섯 Source
Record는 8월 13일의 S3 접근과 8월 14~16일의 Edge·Workload 검증을 함께 사용하므로,
**한 번의 동일 공격을 관통한 완전한 Timeline으로 해석하지 않는다.**

### Runtime 가능성 확인

2026-08-17에 최근 7일의 현재 Index를 읽기 전용으로 집계해 다음 값을 확인했다.

| 항목 | 현재 보존 Event |
|---|---:|
| WAF `ALLOW` | 8 |
| WAF `BLOCK` | 0 |
| ALB `200` / `302` / `404` / `503` | 76 / 48 / 98 / 1 |
| CloudTrail 주요 Service | EC2·KMS·CloudWatch Logs·STS·S3 등 |

이는 계획한 추세·분포 Panel이 실제 Field로 만들어질 수 있다는 확인이다. 현재 값이
정상 기준선이거나 공격 횟수라는 뜻은 아니다. 충분한 기간의 정상 데이터가 쌓인 뒤에야
평소 범위와 이상 증가를 비교할 수 있다.

### 과장하지 않기 위한 표시 규칙

- `WAF 검사 요청`은 Network Packet 전체가 아니라 WAF가 평가한 HTTP Request다.
- `ALB 4xx·5xx`는 오류 응답이며 그 자체로 공격 판정이 아니다.
- `CloudTrail API 활동`은 AWS 작업량이며 그 자체로 악성 행위가 아니다.
- Event Count `0`은 해당 시간에 Event가 없다는 뜻이지 수집기가 정상이라는 증거가 아니다.
- 대응 상태를 저장하는 외부 데이터가 아직 없으므로 Shuffle 연결 전에는 Markdown에
  `자동 대응 미연결`이라고 고정 표시한다.
- 다섯 Source의 원본 발생 시각 Field는 서로 다르다. 공통 `timestamp` 그래프는
  **공격 발생 순서가 아니라 Wazuh에 Index된 시각의 흐름**이므로 `공격 Timeline`이라고
  부르지 않는다.

다른 공격도 같은 Filter 변경 없이 자동으로 묶는 범용 Timeline은 이후 다음 공통 Field를
정규화해야 한다.

```text
event_time
event.category
event.action
event.outcome
service.name
scenario.id 또는 correlation.id
```

우선 현재 Field로 두 Dashboard와 3분 무검색 사용성 Test를 완료하고, Test에서 드러난
불편만 정규화 대상으로 올린다.

### 구현 순서와 완료 Gate

```text
[완료] Dashboard 2개·Visualization 14개·Saved Search 2개 구현
→ [완료] Saved Object 구조·검색 조건·정렬과 보존 Evidence 읽기 검증
→ [다음] 운호의 보존 Event 기반 안내형 미니 실습
→ 다른 조원의 3분 무검색 사용성 Test
→ 새 대표 시나리오 실행 후 Last 15 minutes로 확인
→ Wazuh UI 공식 Saved Objects Export·보고서용 마스킹 Screenshot
```

Gate 4 통과 기준은 다음과 같다.

- Overview에서 웹 요청 추세·응답 분포·AWS API 활동·중요 경보를 검색식 없이 설명한다.
- Incident View에서 관련 계층·탐지 근거·관측 공백·다음 조치를 검색식 없이 설명한다.
- Source별 수치를 공격 횟수나 수집기 Health로 잘못 해석하지 않는다.
- 민감 운영 식별자를 노출하지 않고 원본 Event로 Drill-down할 수 있다.
- 다른 조원이 3분 안에 위 내용을 설명한다.

### 저장·증거 보존 기준

- 최종 Dashboard 이름: `AWS 보안관제 현황`, `AWS 보안 사건 상세`
- 현재 제작 확인 시간 범위: `Last 7 days`
- 새 시연 직후 확인 시간 범위: `Last 15 minutes`
- Dashboard·Visualization·Saved Search는 `Dashboard management → Saved objects`에서
  `[AWS-SOC]` Prefix 전체를 `.ndjson`으로 Export한다.
- 버전 관리 대상은 `observability/wazuh/saved-objects/`에 둔다.
- 2026-08-17에는 내일 실습 복구를 위해 같은 Local Index용 Raw Backup과 SHA-256을
  `C:\Users\Unoh\Documents\aws-topology-evidence\wazuh\saved-objects\`에 먼저 보존했다.
  이는 Wazuh UI의 공식 Import용 Export가 아니므로 버전 관리본을 대신하지 않는다.
- 보고서용 Screenshot은
  `C:\Users\Unoh\Documents\aws-topology-evidence\report-assets\observability\07_wazuh\`에
  저장하고, IP·Request ID·ARN 전체·Credential·Cookie·Command 응답은 공개본에서 제외한다.

공식 참고:

- [Wazuh Creating custom dashboards](https://documentation.wazuh.com/current/user-manual/wazuh-dashboard/creating-custom-dashboards.html)
- [OpenSearch 2.19 DQL](https://docs.opensearch.org/2.19/dashboards/dql/)
- [OpenSearch 2.19 Discover와 Saved Search](https://docs.opensearch.org/2.19/dashboards/discover/index-discover/)
- [AWS CloudWatch Logs의 WAF·CloudTrail Dashboard 예시](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/CloudWatchLogs-OpenSearch-Dashboards.html)
- [Microsoft Sentinel Overview 구성 예시](https://learn.microsoft.com/en-us/azure/sentinel/get-visibility)

## 6. 최초 탐지 지연 개선 — `10m` Poll에서 `1m` Poll로

### 왜 Dashboard보다 탐지 속도를 먼저 고쳤는가

기존 DVWA 안전 Audit Event는 애플리케이션에서 `2026-08-16T14:37:00Z`에 발생했지만
Wazuh Index에는 `2026-08-16T14:41:55.898Z` 무렵 등록됐다. 당시 AWS Wodle의
`interval`이 `10m`였으므로, Wazuh가 Event를 분석하는 시간보다 **AWS 로그를 다시 읽으러
가는 Poll 대기 시간**이 더 큰 병목이었다.

따라서 목표를 다음처럼 분리했다.

```text
DVWA command.execution + ec2_imds
→ 1분 안에 Wazuh 의심 경보
→ CloudTrail GetObject가 나중에 도착
→ 같은 사건의 데이터 접근 확인 경보
```

여기서 빠른 경보는 침해 확정이 아니다. Workload가 IMDS를 대상으로 Shell Command를
실행했다는 **고신호 의심 행위**이고, 실제 Node Role의 보호 Object 읽기는 기존 CloudTrail
Rule이 별도로 확인한다.

### 영구 원본 변경

`single-node/config/wazuh_cluster/wazuh_manager.conf`의 AWS Wodle 주기를 다음처럼 바꿨다.

```xml
<interval>1m</interval>
```

`capital_one_rules.xml`에는 Rule `100101`, Level 10을 추가했다.

| 조건 | 값 |
|---|---|
| Event Type | `command.execution` |
| Action | `shell_command` |
| Resource | `ec2_imds` |
| DVWA Security Level | `low` |
| Route | `/vulnerabilities/exec/` |

두 Rule의 의미는 다음과 같이 구분한다.

| 단계 | Rule | Level | 의미 |
|---|---:|---:|---|
| 최초 의심 | `100101` | 10 | Workload Command가 EC2 IMDS를 대상으로 실행됨 |
| 침해 확인 | `100100` | 12 | 지정 Node Role로 보호된 검증 S3 Object 읽기에 성공함 |

`100101`은 `result=succeeded`만 요구하지 않는다. Command가 결과를 반환하지 못했더라도
IMDS 대상 실행 **시도 자체**를 놓치지 않기 위해서다. 반대로 일반 대상 Command와 다른
Route는 이 Rule에서 제외한다.

### 정적·대조군 검증

Manager 재생성 전에 `wazuh-analysisd -t`로 전체 Ruleset 로드를 검사했다. 이어서
`wazuh-logtest`에 합성 Event를 넣어 다음 계약을 확인했다.

| 입력 | Rule `100101` |
|---|---|
| IMDS 대상·지정 Command 경로 | 발생 — Level 10 |
| 같은 경로지만 Resource가 `other` | 발생하지 않음 |
| IMDS 대상이지만 Route가 `/health` | 발생하지 않음 |

양성의 Phase 3 결과는 다음과 같았다.

```text
id: 100101
level: 10
description: AWS-SOC: Workload command execution targeted EC2 IMDS.
Alert to be generated.
```

### `1m` 실행 주기 사전 검증

Manager를 재생성한 뒤 컨테이너 내부 `ossec.conf`에도 `<interval>1m</interval>`이 반영된
것을 확인했다. Daily AWS Runtime이 꺼진 상태에서 연속 세 Poll을 관찰한 결과는 다음과
같다.

| Poll | 시작 | 종료 | 소요 |
|---:|---|---|---:|
| 1 | `07:27:05Z` | `07:27:26Z` | 21초 |
| 2 | `07:28:05Z` | `07:28:25Z` | 20초 |
| 3 | `07:29:05Z` | `07:29:25Z` | 20초 |

세 주기 모두 새 `Interval overtaken`, AWS API Error, Wazuh Module Error 없이 끝났다.
이는 현재 보존 데이터 범위에서 1분마다 수집기를 시작할 실행 여유가 있다는 뜻이다.

### 아직 증명하지 않은 것

- 실제 공격 Event 발생부터 Rule `100101` Alert까지 60초 이내인지는 아직 Runtime으로
  증명하지 않았다.
- Daily Runtime이 켜져 로그 Stream과 Event가 늘어난 상태에서도 20초대가 유지되는지는
  아직 확인하지 않았다.
- `1m` Poll은 AWS API 호출량을 기존보다 늘리므로 S3 Request와 CloudWatch Logs 호출량·비용을
  실제 실습 구간에서 측정해야 한다.
- CloudTrail S3 전달은 빠른 최초 Trigger가 아니라 후속 확인 Evidence로 유지한다.
- 기존 `Start-WafLiveViewer.ps1`은 주 관제 화면이 아니라 WAF 원본의 저지연 진단용 보조
  도구로 유지한다.

### 다음 Runtime Gate

```text
minimal + capital-one-lab Daily Up
→ Wazuh Dashboard 자동 새로고침 10초
→ 대표 시나리오 1회 실행
→ Source Event / CloudWatch 도착 / Wazuh Archive / Rule 100101 시각 기록
→ 같은 방법으로 총 3회 반복
→ 60초 이내·중복 없음·Interval overtaken 없음·API 오류 없음 판정
→ 수집 호출량과 비용 확인
```

세 번 모두 통과하면 `1m` Poll을 실습 Profile의 기본값으로 채택한다. 실패하면 Wazuh를
폐기하지 않고, CloudWatch Logs Subscription과 SQS/Lambda 기반 Event-driven Bridge를
다음 대안으로 검토한다.

공식 참고:

- [Wazuh AWS Wodle `interval`](https://documentation.wazuh.com/current/user-manual/reference/ossec-conf/wodle-s3.html)
- [Wazuh Log 수집과 실시간 분석](https://documentation.wazuh.com/current/user-manual/capabilities/log-data-collection/how-it-works.html)
- [CloudWatch Logs API Quota](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/cloudwatch_limits_cwl.html)
- [Amazon S3 Request Pricing](https://aws.amazon.com/s3/pricing/)
