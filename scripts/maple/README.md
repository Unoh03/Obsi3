# 메이플 캐릭터 정보 수집기

NEXON Open API로 캐릭터 정보를 수집하고, AI와 대화할 때 사용할 JSON을 만든다. PowerShell **7.5 이상**만 필요하다(현재 7.6.5에서 검증). 날짜 문자열의 시간대를 원문대로 보존하기 위한 조건이다. Python·별도 패키지·브라우저 연동은 사용하지 않는다.

## 사용

1. `Run-MapleCharacterData.cmd`를 더블클릭한다.
2. PowerShell 입력창에 NEXON API key를 입력한다. 키는 파일에 저장하지 않는다.
3. 현재 스펙·저장 프리셋·직전 변경을 분석하려면 **`output/ai-context.json`을 AI에 첨부**한다. 원본 API 응답을 감사하거나 생략한 외형/식별 정보를 확인할 때는 raw를 사용한다.

기본 캐릭터는 우노03이다. 직접 실행하거나 다른 캐릭터를 수집하려면:

```powershell
Set-Location 'D:\Obsidian\Vault\Obsi2\scripts\maple'
./Get-MapleCharacterData.ps1 -CharacterName '캐릭터명' -NoPause
./Build-MapleSnapshot.ps1 -SourcePath './output/캐릭터명-maple-api.json'
```

수집 없이 기존 파일만 재가공할 수도 있다. API key와 네트워크 연결이 필요 없다.

```powershell
./Build-MapleSnapshot.ps1
# 과거 원본은 별도 출력 폴더를 사용한다.
./Build-MapleSnapshot.ps1 -SourcePath './output/raw/과거파일.json' -OutputDirectory './output/past-review'
```

## 출력 파일

| 파일 | 역할 |
|---|---|
| `ai-context.json` | AI용 기본 파일. 현재 상태 + 저장 프리셋 + 수집 품질 + 직전 수집과의 변경 내역. 공백을 줄인 JSON |
| `summary.json` | 같은 현재 상태와 저장 프리셋을 사람이 읽기 좋게 들여쓴 JSON. 변경 내역 제외 |
| `diff.json` | 변경 내역만 필요할 때 사용 |
| `캐릭터명-maple-api.json`, `latest.json` | 원본 응답을 보존한 수집본 |
| `raw/캐릭터명-*.json` | 덮어쓰지 않는 과거 원본. 기존 이력도 계속 사용 |
| `current.json` | 마지막으로 완료된 결과 묶음의 경로와 파일별 SHA-256 |
| `snapshots/<hash>/` | 함께 생성·검증된 summary/diff/latest/ai-context. 공개 후 덮어쓰지 않는 결과 묶음 |

여러 캐릭터의 raw 이력은 구분하지만, `ai-context.json` 등 고정 이름 파일은 마지막으로 처리한 캐릭터를 가리킨다. 동시에 실행하지 않는다. 모든 생성 파일은 Git 제외 대상이다.

`summary.json`과 `diff.json`의 내용은 `ai-context.json`에 들어 있으므로 AI에 중복 첨부할 필요가 없다. 두 파일은 로컬 확인용으로 계속 생성한다. `latest.json`은 캐릭터별 수집 원본의 복사본이며, raw 이력과 함께 원본 검증용으로 보존한다.

출력은 먼저 별도 결과 묶음에 모두 저장·검증하고, 마지막에 `current.json` 하나를 교체해 완료 처리한다. 기존 경로의 네 파일은 편의 복사본이다. 파일 잠금은 교체 전 확인하고, 교체 도중 예외가 발생하면 바뀐 복사본을 이전 값으로 복구한다. 프로세스 강제 종료·전원 차단 중에는 편의 복사본끼리 시점이 다를 수 있으므로, **파일 여러 개를 함께 읽는 프로그램은 `current.json`을 한 번 읽고 그 묶음만 사용**한다. 묶음 검증은 모듈의 `Get-MaplePublishedSet`으로 할 수 있다. 수집 원본은 후처리에 실패해도 보존하며, 원본 수집 시각과 마지막 완료 시각이 다를 수 있다.

**기본 정보(`basic`) 또는 최종 스탯(`stat`)이 실패·누락되면** 실패 응답까지 raw에 보관한 뒤 후처리를 오류로 종료한다. `current.json`과 ai-context/summary/diff/latest는 마지막 정상 결과를 유지한다. 최초 수집부터 실패했다면 완료 결과를 만들지 않는다. 나머지 API만 실패한 경우는 품질 정보에 표시하고 부분 결과를 제공한다. 다음 정상 수집의 변경 비교에서도 필수 정보가 실패한 raw는 건너뛰고, 직전 필수 정보가 정상인 수집본을 기준으로 삼는다.

## AI에 전달하는 내용

- `metadata`: 캐릭터명, 수집 시작·종료 시각, NEXON 출처, raw 상대 경로와 SHA-256.
- `quality`: 각 API의 성공/실패/누락/불완전(`partial`), 오류, 구조 검증 사유(`validation_issues`), API 응답의 데이터 기준 시각. `date: null`은 기준 시각을 확인하지 못했다는 뜻이다.
- `actual`: 모든 최종 스탯, 현재 장비의 상세 옵션·잠재·추옵·스타포스, 하이퍼 스탯·어빌리티, 심볼, 세트, 펫, 링크, V 매트릭스, HEXA 코어·스탯, 무릉, 기타 스탯, 반지, 유니온·아티팩트·챔피언.
- `presets`: 저장된 하이퍼 스탯·어빌리티·장비·칭호·링크/자체 링크·V 매트릭스·HEXA 스탯·유니온·펫 장비 프리셋. API 섹션과 원래 필드명을 유지하며, 현재 적용 설정으로 간주하지 않는다.
- `changes_since_previous`: 직전의 더 오래된 **동일 캐릭터** 수집본과 비교한 현재 상태·저장 프리셋의 변경값 및 비교하지 못한 섹션. 프리셋 변경 경로는 `$.presets.`로 시작한다.

예를 들어 하이퍼 2번은 `presets.hyper_stat.hyper_stat_preset_2`, 어빌리티 2번은 `presets.ability.ability_preset_2`, 칭호 3번은 `presets.item_equipment.title_preset3`에 있다. 유니온 상태 프리셋은 `presets.union_raider.union_state_stat_preset`에 있다. 번호와 API가 반환한 순서를 유지하며, 보스용/사냥용 용도는 임의로 붙이지 않는다.

이미지 URL과 외형 표시 필드는 현재 상태와 프리셋 모두에서 덜어낸다. 하이퍼 스탯의 현재 배분은 API의 사용 프리셋 번호로 선택하며, 번호가 확인되지 않거나 선택한 값이 null/비정상 구조이면 `active_preset_resolved: false`, 섹션 상태 `partial`로 표시하고 후보들은 `presets`에 남긴다. 빈 배열은 null과 구분해 그대로 보존한다. 프리셋별 남은 포인트·수치 문자열·0·null·빈 배열도 보존한다. 스탯 이름은 NEXON의 한글 이름을 사용한다. 아이템 설명은 효과 정보가 포함될 수 있어 유지한다. **이 파일은 raw 전체를 대체하지 않는다.** OCID·외형 정보 등 생략한 정보, 현재 수집 대상 밖 정보, API 오류로 받지 못한 정보까지 포함한다는 뜻은 아니다.

API 최종 스탯에 장비·링크·유니온 효과를 다시 더하면 중복 계산이 된다. 수집 시각은 실제 게임 상태의 기준 시각과 같다고 보장하지 않는다. 제공된 API 범위 밖 정보나 실패 응답을 0/미장착으로 추정하지 않으며, 별도의 환산 계산은 하지 않는다.

현재 수집에서는 과거 조회용 `ring_exchange`를 호출하지 않고 `ring_reserve`를 사용한다. [NEXON의 2026-03-19 업데이트 안내](https://openapi.nexon.com/ko/support/notice/3402834/)에 따른 구분이다. 기존 raw에 남아 있는 `ring_exchange` 데이터/오류는 그대로 읽고 보존하므로, 과거 수집본을 재가공했다고 과거 오류가 사라지지는 않는다.

## 변경 비교와 이력

- 정상 수집된 섹션끼리만 비교한다. 이전 성공 → 이번 실패/불완전을 현재 장비나 저장 프리셋의 삭제로 표시하지 않는다.
- 장비 슬롯·심볼명·스킬명 등 양쪽 배열에 유일한 식별자가 있으면 같은 항목끼리 비교한다. 그 외 배열은 위치로 비교한다. 현재 상태 배열의 원래 순서는 바꾸지 않는다.
- `before_exists` / `after_exists`로 필드 누락과 `null`을 구분하고 문자열·숫자·boolean도 구분한다.
- 같은 원본을 다시 처리하면 SHA-256으로 기존 raw를 재사용한다. 직전 비교 대상도 유지하므로 재가공만으로 변경 내역이 0건이 되지 않는다.
- 과거 원본은 수집 시각 순서로 선택한다. 손상된 과거 파일은 건너뛰고 `history_warnings`에 표시한다. 같은 시각에 서로 다른 원본이 있으면 비교를 중단한다.
- 현재 스키마는 `schema_version: 3`이다. 버전 2에서 빠졌던 저장 프리셋이 별도 영역으로 추가되었다. 예전 raw도 같은 규칙으로 재가공한 뒤 비교하므로 스키마 변경 자체를 캐릭터 변화로 세지 않는다.

## 구성과 검증

| 파일 | 역할 |
|---|---|
| `Get-MapleCharacterData.ps1` | SecureString 키 입력, API 요청 간격·429 재시도·요청 제한 시간, 원본 저장 |
| `MapleSnapshot.psm1` | API 목록, JSON 입출력, AI용 상태 정리, 변경 비교 |
| `Build-MapleSnapshot.ps1` | raw 이력 선택·보관과 출력 생성 |
| `tests/Test-MapleSnapshot.ps1` | 네트워크 없이 가공·변경 비교·원본 보존 검증 |

```powershell
pwsh -NoProfile -File ./tests/Test-MapleSnapshot.ps1
```

환산 실험용 코드·테스트·의존성·가상환경·문서는 제거했다. 기존 `.runtime/`, `fixtures/maplescouter/`의 로컬 자료는 이 도구에서 사용하지 않으며, 기존 사용자 상태/증거 보존을 위해 Git 제외 상태로 남겨 두었다.

Data based on NEXON Open API. [공식 안내](https://openapi.nexon.com/ko/game/maplestory/)
