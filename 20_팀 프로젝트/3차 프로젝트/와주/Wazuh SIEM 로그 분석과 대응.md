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

> [!tip] 앞으로 남길 핵심 화면
> 준비 성공 화면 자체보다 `공격 성공`, `Alarm 전환`, `같은 eventID의 Raw Event`, `Rule 100100·Level 12 Alert`가 핵심 증거다. 이 네 장면이 “공격이 기록되고 SIEM이 해석해 경보로 만들었다”는 주장을 연결한다.

### 4.5 현재 위치와 다음 작업

- [x] Dashboard에 `wazuh-archives-*` Index Pattern 생성
- [x] `timestamp` 시간 필드와 Discover 조회 확인
- [x] `minimal + capital-one-lab` Runtime Apply 및 사전 조건 확인
- [x] 고정된 가짜 S3 Object 준비 및 검증
- [ ] `Invoke-CapitalOneBaseline.ps1` Preview 확인
- [ ] 새 통제 공격 Event 1회 실행
- [ ] 같은 CloudTrail `eventID`의 Raw 문서와 Rule `100100`·Level 12 Alert 동시 확인
- [ ] 정상적인 S3 조회가 같은 Rule에 걸리지 않는지 오탐 확인
- [ ] Archive Index의 하루 증가량 기록
- [ ] 7일 Retention 적용 및 검증

기존 `minimal + hardened` Session에서는 Capital One Runner의 사전 검사가 실행을
거부했으므로 공격 Event가 생성되지 않았다. 해당 Runtime의 Daily Down을 완료한 뒤,
현재는 `minimal + capital-one-lab` Runtime을 새로 Apply하고 가짜 실습 데이터까지
준비했다. 다음 단계는 Baseline Preview로 최종 조건을 확인하는 것이다.

Retention부터 먼저 만들지 않는다. 실제 통제 Event와 하루 증가량을 확인한 뒤 적용해,
잘못된 조건으로 실습 Evidence를 먼저 삭제하는 일을 막는다.
![[Pasted image 20260813174238.png]]