---
type: project-doc
status: active
created: 2026-08-17
project: 3차 프로젝트
project_moc: "[[20_팀 프로젝트/3차 프로젝트/00_3차프로젝트_목차]]"
---

# Wazuh 대시보드 미니 실습

> [!important] 이 실습의 목적
> 새 공격을 실행하거나 수집 파이프라인을 다시 검증하는 실습이 아니다. 이미 보존된
> 대표 사건을 이용해 `현황 → 이상 발견 → 사건 상세 → 탐지 근거 → 다음 조치` 순서로
> Dashboard를 읽는 방법을 익힌다.

관련 개념과 구현 근거는 [[Wazuh SIEM 로그 분석과 대응]]에서 확인한다.

## 실습 경계

- **읽기 전용:** AWS Apply, 공격 실행, Wazuh Rule·Dashboard 수정 없음
- **AWS 불필요:** Daily Runtime이 내려간 상태에서도 Local Wazuh Index만으로 진행
- **첫 실행:** 운호가 안내를 받으며 천천히 조사
- **합격 시험:** 이후 다른 조원이 별도 검색식 없이 3분 안에 같은 질문에 답하는 시험
- **과장 금지:** 현재 다섯 Source의 보존 Record는 여러 날짜의 실습에서 수집됐다. 한 번의
  동일 공격을 끝까지 관통한 완전한 Timeline이라고 주장하지 않는다.

## 오늘 고정한 준비 상태

2026-08-17 읽기 전용 Preflight 결과는 다음과 같다.

| 항목 | 확인 결과 |
|---|---:|
| Wazuh Service | Manager·Indexer·Dashboard 3/3 Running |
| Dashboard | 2개 |
| Visualization | 14개 |
| Saved Search | 2개 |
| Edge 요청 Evidence | 6건 |
| WAF 검사 Evidence | 8건 |
| ALB 전달 Evidence | 12건 |
| Workload 실행 Evidence | 2건 |
| AWS 데이터 접근 Evidence | 1건 |
| Rule `100100` Alert | 1건 |

Saved Search 두 개는 안전한 6개 Field·최신순 정렬·불필요한 Exists Filter 0개로 확인했고,
ALB 응답 상태는 응답 코드 오름차순으로 확인했다.

원본 복구용 백업은 다음 위치에 있다. 이는 같은 Local Wazuh Index의 장애 복구용 Raw
Backup이며, Wazuh UI의 공식 Import용 Export와는 구분한다.

```text
C:\Users\Unoh\Documents\aws-topology-evidence\wazuh\saved-objects\aws-soc-20260817.raw.ndjson
SHA-256: d36aaf73e133374cfa5da0fe523bf7f3457553e6893b3d9ab20dee7647a081df
```

### AWS 종료 상태

준비를 마친 뒤 2026-08-17에 표준 `daily-down.ps1`을 실행했다.

| 항목 | 결과 |
|---|---|
| Terraform Destroy | 124개 삭제 완료 |
| Daily Terraform State | 0개·Empty |
| Tracked Daily AWS Residue | 없음 |
| Tagged Daily AWS Runtime | 없음 |
| Active Daily Session | 없음 |
| Foundation | ECR·GitHub Actions Role·Security Log Bucket 보존 |
| 소요 시간 | 23.5분 |

```text
Pre-destroy manifest
C:\Users\Unoh\Documents\aws-topology-evidence\daily-20260816T174015Z-9913c9d3-pre-destroy\manifest.json

Post-destroy manifest
C:\Users\Unoh\Documents\aws-topology-evidence\daily-20260816T174015Z-9913c9d3-post-destroy\manifest.json
```

Daily Down 뒤에도 Local Wazuh Preflight와 Backup SHA-256을 다시 확인했다. 따라서 내일
미니 실습을 위해 `daily-up.ps1`을 실행하지 않는다. 필요한 것은 Docker Desktop과 Local
Wazuh뿐이다.

## 내일 시작 절차

Docker Desktop을 먼저 실행한 뒤 PowerShell 7에서 다음 명령을 실행한다.

```powershell
Set-Location 'D:\terraform\aws_terraform_build_code'

.\observability\wazuh\Test-WazuhMiniDrill.ps1 -StartStack
```

마지막에 다음 문장이 보여야 한다.

```text
WAZUH_MINI_DRILL_READY=yes
```

그다음 `https://localhost`의 Wazuh Dashboard에 로그인한다. ID·Password는 이 문서나
Screenshot에 기록하지 않는다.

> [!warning] 시간 범위
> 두 Dashboard는 실제 새 시연에 맞춰 `Last 15 minutes`를 저장한다. 보존 Event로 하는
> 이번 미니 실습에서는 **Dashboard를 열 때마다 `Last 7 days`로 바꾸고 Refresh**한다.
> 이 단계를 빠뜨리면 모든 Panel이 `0`으로 보일 수 있다.

## 진행자 대본

진행자는 처음부터 답을 설명하지 않고 아래 문장만 읽는다.

> 중요 보안 경보가 발생했습니다. 검색식을 직접 입력하지 말고, Wazuh의 두 Dashboard를
> 이용해 무슨 일이 있었는지, 어떤 근거가 있는지, 무엇이 아직 증명되지 않았는지
> 조사해 주세요.

첫 실습에서는 제한시간을 두지 않는다. 운호가 화면을 직접 찾도록 질문을 한 개씩 주고,
막혔을 때만 다음 클릭 위치를 알려준다. 정답은 각 단계가 끝난 뒤에만 연다.

## 1단계 — 관제 현황에서 이상 발견

1. `Dashboard`에서 `AWS 보안관제 현황`을 연다.
2. 시간 범위를 `Last 7 days`로 바꾸고 `Refresh`한다.
3. 위에서 아래로 화면을 훑고 다음 질문에 답한다.

```text
Q1. Wazuh가 중요하다고 판정한 경보가 있는가?
Q2. 웹 요청과 WAF 차단은 같은 의미인가?
Q3. ALB 오류 응답이 있으면 곧바로 공격이라고 할 수 있는가?
Q4. 최근 중요 경보에서 위험도와 사건 설명을 찾을 수 있는가?
```

> [!answer]- 1단계 정답과 해석
> - `중요 경보`는 1건이며, `최근 중요 경보`에도 Rule Level 12 행이 1건 보인다.
> - WAF 검사 요청은 8건, WAF `BLOCK`은 0건이다. 검사는 요청을 평가했다는 뜻이고 차단과
>   같지 않다.
> - ALB `4xx·5xx`는 오류 응답이지 공격 판정이 아니다. 현재 Index에는 인터넷 배경
>   Scan으로 보이는 요청도 섞여 있으므로 숫자만으로 사건을 확정하지 않는다.
> - 새 사건 조사를 시작하게 하는 가장 강한 신호는 Rule이 만든 `중요 경보`와 최근 경보
>   행이다.

다음 조건 중 하나가 보이면 `AWS 보안 사건 상세`로 이동한다고 설명한다.

```text
중요 경보 또는 최근 중요 경보 발생
WAF BLOCK 급증
ALB 4xx·5xx 급증
평소와 다른 AWS API 활동
```

## 2단계 — 사건 상세에서 근거 확인

1. `Dashboard`에서 `AWS 보안 사건 상세`를 연다.
2. 다시 시간 범위를 `Last 7 days`로 바꾸고 `Refresh`한다.
3. 다음 질문에 답한다.

```text
Q1. Workload에서 어떤 종류의 의심 행위가 있었는가?
Q2. 보호 데이터 접근은 Alert로 판정됐는가?
Q3. 어느 계층에서 관련 Evidence가 남았는가?
Q4. 다섯 막대의 숫자는 공격 순서인가, Evidence 수인가?
Q5. 관련 Event 수집 흐름은 실제 공격 발생 순서인가?
```

> [!answer]- 2단계 정답과 해석
> - Workload에는 `command.execution`이면서 대상 Resource가 `ec2_imds`인 Event 2건이 있다.
> - 보호 데이터 접근과 Rule `100100` Alert는 각각 1건이다.
> - 보존 Evidence는 Edge 6, WAF 8, ALB 12, Workload 2, AWS 데이터 접근 1건이다.
> - `사건 단계별 Evidence`의 막대는 Source별 **보존 Event 수**이지 공격 순서가 아니다.
> - `관련 Event 수집 흐름`의 `timestamp`는 Wazuh Index 등록 시각이다. Source 원본 시각을
>   정규화한 공격 Timeline이 아니다.

## 3단계 — 탐지 근거 읽기

`탐지 근거` Saved Search의 행을 읽고 다음 질문에 답한다. 검색식은 입력하지 않는다.

```text
Q1. Wazuh Rule ID와 위험도는 무엇인가?
Q2. 어떤 AWS Service와 API가 관련됐는가?
Q3. 어떤 Object Key를 읽었는가?
Q4. 왜 일반적인 모든 S3 접근이 아니라 이 Event만 높은 경보가 됐는가?
```

> [!answer]- 3단계 정답과 해석
> - Rule `100100`, Level 12다.
> - `s3.amazonaws.com`의 `GetObject`다.
> - `validation/capital-one-demo.csv`를 읽었다.
> - 지정된 Karpenter Node Role, Primary Bucket, 고정 검증 Object, 성공한 `GetObject` 조건을
>   모두 만족했기 때문에 프로젝트 Custom Rule이 높은 신뢰도의 Alert로 판정했다.
> - Description은 `CAPITAL-ONE: Karpenter node role successfully read the protected
>   validation object.`다.

필요할 때만 행의 Document Details로 내려간다. 공개 Screenshot에는 Account ID 전체, ARN,
Client IP, Request ID, Credential, Cookie, Command 원문·응답을 넣지 않는다.

## 4단계 — 한 문장으로 사건 설명

실습자는 화면을 닫기 전에 아래 틀을 자기 말로 채운다.

```text
[어디에서 어떤 의심 행위]가 관측됐고,
[어떤 AWS API가 어떤 대상에 성공]했으며,
[어떤 Rule과 위험도]로 Alert가 생성됐다.
[어느 Source들의 Evidence]를 함께 확인했지만,
[아직 증명하지 못한 공백]은 남아 있다.
현재 대응은 [상태]이며 다음에는 [조치]가 필요하다.
```

> [!answer]- 모범 답안
> DVWA Workload에서 IMDS를 대상으로 한 Command 실행이 관측됐고, Node Role을 이용한
> S3 `GetObject`가 고정 검증 Object에 성공했다. CloudTrail Event는 Wazuh Rule `100100`,
> Level 12 Alert가 됐다. CloudFront·WAF·ALB·DVWA·CloudTrail의 관련 Evidence를 Wazuh
> 한곳에서 확인할 수 있지만, 현재 보존 Record는 여러 실습 실행에 걸쳐 있어 한 번의
> 요청을 끝까지 관통한 완전한 인과 Timeline은 아니다. Pod→IMDS 직접 Network Log도
> 없으며, Shuffle 자동 대응은 아직 연결되지 않았으므로 다음 단계는 Rule Alert를
> Shuffle Dry Run으로 전달하는 것이다.

## 진행자가 지켜야 할 판정 경계

- WAF·ALB·CloudTrail 숫자가 크다고 공격 횟수라고 말하지 않는다.
- `0건`을 수집기 정상의 증거로 사용하지 않는다.
- 5개 Source에 Record가 있다는 사실과 한 요청이 5개를 모두 만들었다는 주장을 구분한다.
- Rule `100100`만 현재 대표 공격의 명시적 Custom Alert다.
- `자동 대응 미연결` Markdown은 현재 상태 안내이며 실제 자동 대응 결과가 아니다.
- Dashboard가 사건을 한국어 문장으로 자동 진단한 것은 아니다. 검색식 없이 필요한 근거를
  찾도록 화면을 구성한 것이다.

## 막혔을 때 복구 순서

### 모든 숫자가 0이다

1. 시간 범위가 `Last 15 minutes`인지 확인한다.
2. `Last 7 days`로 바꾸고 `Refresh`한다.
3. 그래도 0이면 PowerShell에서 Preflight를 다시 실행한다.

```powershell
Set-Location 'D:\terraform\aws_terraform_build_code'
.\observability\wazuh\Test-WazuhMiniDrill.ps1
```

### Wazuh 화면이 열리지 않는다

```powershell
Set-Location 'D:\terraform\aws_terraform_build_code'
.\observability\wazuh\Test-WazuhMiniDrill.ps1 -StartStack
```

서비스가 시작된 직후에는 Dashboard 준비에 시간이 걸릴 수 있다. `WAZUH_MINI_DRILL_READY=yes`
확인 뒤 브라우저를 새로 고친다.

### Saved Object 또는 Evidence 검사에 실패한다

Dashboard를 즉석에서 다시 만들거나 Wazuh Volume을 초기화하지 않는다. Preflight가 출력한
첫 실패 항목을 보존하고, 오늘 만든 Raw Backup과 현재 `.kibana_1`을 대조한 뒤 복구한다.
`docker compose down -v`는 Index와 Dashboard를 삭제하므로 실행하지 않는다.

## 첫 실습 뒤 기록할 것

```text
처음 막힌 화면:
헷갈린 Panel 이름:
잘못 해석한 숫자:
원본 Drill-down이 필요했는가:
한 문장 사건 설명에 걸린 시간:
설명서에서 고칠 문장:
```

이 기록을 반영한 뒤 다른 조원에게 아무 설명 없이 3분 사용성 Test를 실시한다. 첫 운호
실습은 학습 단계이므로 Gate 4의 최종 3분 합격 시험으로 계산하지 않는다.

## 실습 종료

로컬 Wazuh를 더 사용하지 않을 때만 다음 명령으로 Container를 정지한다. Named Volume과
Host 설정은 삭제하지 않는다.

```powershell
Set-Location 'D:\Wazuh\wazuh-docker\single-node'
docker compose stop
```
