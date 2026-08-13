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
