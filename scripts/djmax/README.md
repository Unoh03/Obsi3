# DJMAX 4B 성장 기록 수집기

V-ARCHIVE 공개 API를 사용해 `Unoh03`의 4B **등록 기록**을 읽고, 기존 스냅샷과 비교한다. 메이플의 `scripts/maple/` 수집기와 독립적으로 작동한다. Windows + PowerShell **7.5 이상** 기준이다. 외부 Python 패키지, 계정 비밀번호, V-ARCHIVE `account.txt`가 필요 없다.

## 시작

1. DJMAX 신기록을 **V-ARCHIVE에 먼저 업로드**한다. 게임 내 저장만으로는 API에 나타나지 않는다.
2. `Run-Djmax.cmd`를 더블클릭한다.
3. 완료 후 표시된 `output/exports/ai-context-*.json` 파일 **하나**를 ChatGPT의 DJMAX 프로젝트에 업로드한다.
4. 다음에 신기록을 등록했다면 같은 실행 파일을 다시 실행한다. 직전 정상 수집본과 자동 비교한다.

직접 실행:

    pwsh -NoProfile -File ./Collect-Djmax.ps1

다른 계정/버튼, 또는 출력 위치 변경:

    pwsh -NoProfile -File ./Collect-Djmax.ps1 -Nickname 'Unoh03' -Button 4 -OutputRoot './output'

## 파일 구조

| 파일 | 용도 |
|---|---|
| `output/current.json` | **마지막으로 성공한** 스냅샷 경로를 가리킴. 소비자는 이것부터 읽을 것 |
| `output/snapshots/<수집시각>-<식별자>/latest.json` | API 원본: 기록, 티어, DJ CLASS 응답과 수집 시각 |
| `.../summary.json` | 현재 4B 상태: 등록 채보 수, MAX COMBO, 난이도별 성과, 티어 등 |
| `.../diff.json` | 직전 수집과의 점수 향상/감소, 신규 등록, 신규 MAX COMBO, 티어 변경 |
| `.../ai-context.json` | 현재 상태와 변화를 함께 담은 ChatGPT용 결과 |
| `output/exports/ai-context-*.json` | ChatGPT에 올릴 단일 첨부 파일; 기존 파일 덮어쓰지 않음 |

`output/`은 Git에서 제외한다. 이력은 **로컬에만 보존**되므로 동기화/백업은 별개로 관리해야 한다. 수집기 동시 실행은 지원하지 않는다.

## 해석상 주의

- 첫 실행은 **기준선(baseline)**이다. 기존에 수집된 곡들을 이번에 새로 클리어했다고 집계하지 않는다.
- 이력이 쌓인 후에만 `score_improvements`, `newly_max_combo` 등을 확인할 수 있다.
- `updatedAt`은 **V-ARCHIVE 기록 갱신 시각**이며 실제 게임 플레이 시각을 의미하지 않는다. 특히 컬렉션 스캐너로 일괄 등록한 데이터에서는 주의한다.
- 낮은 점수나 사라진 채보는 API 수정·동기화 문제일 수도 있다. 점수 감소는 '실력 하락'이라고 단정하지 않는다.
- 같은 곡의 다른 채보는 `title:pattern`으로 구분한다. 곡 이름·DLC 문자열만으로 식별하지 않는다.
- `average_registered_score`는 **등록된 채보만의 산술평균**이다. 비플레이 채보, 실패한 시도, 최신 시도의 평균이 아니다.
- 티어·DJ CLASS API가 실패하면 `quality`에 `unavailable`로 표시하고 기록 조회가 정상인 한 계속 진행한다. 점수에서 티어를 임의 계산하지 않는다.
- 본 서비스는 팬 제작 API로 구조가 바뀔 수 있다. 필수 필드 오류/응답 누락이면 기존 `current.json`을 보존한다.
- `current.json`을 기준으로 완성된 스냅샷을 읽는다. 수집 도중 전원 차단 등으로 완성되지 않은 파일은 현재 상태로 취급하지 않는다.

## 오프라인 검증

테스트는 외부 네트워크와 인증 없이 합성 기록만 사용한다.

    pwsh -NoProfile -File ./tests/Test-DjmaxCollector.ps1

스크립트 자체도 합성 입력을 받는다.

    pwsh -NoProfile -File ./Collect-Djmax.ps1 -FixturePath './test-fixture.json' -OutputRoot './test-output'

테스트 fixture JSON의 최상위 필드는 `records_response`, `tier_response`, `djclass_response`이다.

## 출처

- 팬사이트의 API 안내: https://v-archive.net/info/manual/api
- API 문서 저장소: https://github.com/djmax-in/openapi
- 기록 엔드포인트: https://v-archive.net/api/v2/archive/Unoh03/button/4

게임 내 녹화, 키보드 입력, 게임 파일·프로세스 조작 기능은 없다. **공개된 업로드 기록만 조회**한다.
