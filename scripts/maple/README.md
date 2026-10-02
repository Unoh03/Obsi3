# 메이플 캐릭터 정보 수집기

NEXON Open API로 캐릭터 정보를 수집하고, AI와 대화할 때 사용할 JSON을 만든다. PowerShell **7.5 이상**만 필요하다(현재 7.6.5에서 검증). 날짜 문자열의 시간대를 원문대로 보존하기 위한 조건이다. Python·별도 패키지·브라우저 연동은 사용하지 않는다.

## 사용

1. `Run-MapleCharacterData.cmd`를 더블클릭한다. 선택 메뉴 없이 **우노03 → 우노03레테** 순서로 수집한다.
2. PowerShell 입력창에 NEXON API key를 한 번 입력한다. 같은 프로세스에서 두 수집에 사용하며 파일·환경변수·명령줄 문자열에 저장하지 않는다.
3. 마지막 결과표에서 캐릭터별 성공 여부와 **이번 실행의 첨부 경로**를 확인한다. GPT 프로젝트에는 `output/exports/ai-context-캐릭터-날짜-시간-KST-해시.json`을 **캐릭터당 하나씩** 첨부한다. [[scripts/maple/00_메이플_AI_목차|메이플 AI 데이터 목차]]는 공통 안내다. 폴더나 합본 JSON을 올릴 필요가 없다.

직접 일괄 실행하려면 `./Run-MapleCharacters.ps1`을 사용한다. 하나만 수집하는 기존 기능도 유지한다. 예를 들어:

```powershell
Set-Location 'D:\Obsidian\Vault\Obsi2\scripts\maple'
./Get-MapleCharacterData.ps1 -CharacterName '우노03레테' -OutputPath './output/characters/우노03레테/우노03레테-maple-api.json' -NoPause
./Build-MapleSnapshot.ps1 -SourcePath './output/characters/우노03레테/우노03레테-maple-api.json' -ExportDirectory './output/exports'
```

수집 없이 기존 파일만 재가공할 수도 있다. API key와 네트워크 연결이 필요 없다.

```powershell
./Build-MapleSnapshot.ps1 -SourcePath './output/characters/우노03/우노03-maple-api.json' -ExportDirectory './output/exports'
# 과거 원본은 별도 출력 폴더를 사용한다.
./Build-MapleSnapshot.ps1 -SourcePath './output/raw/과거파일.json' -OutputDirectory './output/past-review'
```

## 출력 파일

일괄 실행의 내부 결과는 **`output/characters/우노03/`와 `output/characters/우노03레테/`** 아래에 독립적으로 저장한다. 아래 표의 결과 파일은 각 캐릭터 폴더 기준이며, `exports`와 `last-batch.json`만 공통 `output` 바로 아래에 있다.

| 파일 | 역할 |
|---|---|
| `ai-context.json` | AI용 기본 파일. 현재 상태 + 저장 프리셋 + 수집 품질 + 직전 수집과의 변경 내역. 공백을 줄인 JSON |
| `exports/ai-context-*.json` | 검증된 완료 묶음의 AI 파일과 바이트가 같은 전달용 사본. 수집 시작 시각(KST)과 내용 해시를 이름에 포함하며 덮어쓰지 않음 |
| `summary.json` | 같은 현재 상태와 저장 프리셋을 사람이 읽기 좋게 들여쓴 JSON. 변경 내역 제외 |
| `diff.json` | 변경 내역만 필요할 때 사용 |
| `캐릭터명-maple-api.json`, `latest.json` | 원본 응답을 보존한 수집본 |
| `raw/캐릭터명-*.json` | 덮어쓰지 않는 과거 원본. 기존 이력도 계속 사용 |
| `current.json` | 마지막으로 완료된 결과 묶음의 경로와 파일별 SHA-256 |
| `snapshots/<hash>/` | 함께 생성·검증된 summary/diff/latest/ai-context. 공개 후 덮어쓰지 않는 결과 묶음 |
| `output/last-batch.json` | 마지막 완료된 일괄 실행의 캐릭터별 상태·수집 시각·이번 첨부 경로. 시작/종료 시각 확인 필요 |

이력과 diff는 캐릭터별로만 비교한다. 일괄 실행 잠금은 같은 출력 루트의 중복 실행을 막는다. 단일 수집 명령을 일괄 실행과 동시에 같은 경로에 실행하지 않는다. 모든 생성 파일은 Git 제외 대상이다. raw·snapshots·과거 전달본은 로컬에 보존되지만 Git 커밋·푸시로 백업되지는 않는다.

기존 명령의 기본 경로는 호환성을 위해 유지한다. 인자 없이 단일 수집/후처리를 실행하면 예전 공용 `output`을 사용하므로, 위 예시처럼 캐릭터별 경로를 명시한다. 일괄 실행은 공용 `latest.json`·`ai-context.json` 등을 갱신하지 않는다.

로컬 재수집만으로 ChatGPT에 이미 첨부한 사본이 바뀌지는 않는다. 같은 캐릭터의 옛 첨부를 새 전달본으로 교체하고 AI가 `metadata.collected_at`을 먼저 확인하도록 한다. 파일명은 가공 시각이 아닌 **원본 수집 시각**이다. 같은 원본도 가공 규칙·비교 이력이 다르면 전달본 내용 해시가 달라질 수 있다. 전달본 SHA-256과 `metadata.raw_sha256`(원본 해시)은 서로 다른 파일의 식별자다.

전달본 생성 실패 시 완료 묶음은 유지하지만 이번 첨부 경로를 안내하지 않는다. 단독 후처리도 오류를 반환한다. `-ExportDirectory`로 전달 위치를 지정하고, `-SkipExport`로 전달본 생성을 생략할 수 있다.

## 기존 자료와 실행 결과

일괄 실행은 기존 공용 raw의 **metadata 캐릭터명**을 정확히 대조한 뒤 캐릭터별 raw에 복사하고 해시를 검증한다. 원본은 삭제·이동하지 않으며 반복 실행해도 동일 자료를 중복 생성하지 않는다. 읽을 수 없는 파일은 보존하고 경고한다. 같은 수집 시각에 다른 내용이 있으면 해당 캐릭터를 실패 처리한다.

새 캐릭터 저장소에 완료 결과가 없고 기존 공용 완료 묶음이 해당 캐릭터의 것이라면, 묶음 해시를 검증해 이전 정상 결과를 복구한다. 이때 전달본은 만들지 않으며 **이번 API 수집 성공으로 표시하지 않는다**.

한 캐릭터의 실패 후에도 다른 캐릭터를 계속 처리한다. 결과는 `성공`, `부분 성공`, `실패`, `전달본 생성 실패`로 구분한다. 부분 성공도 품질 정보가 포함된 새 전달본을 제공하지만, 전체 종료 코드는 1이다. 모든 캐릭터가 완전히 성공한 경우만 0이다. 시작 단계 오류도 1로 종료한다. 실패한 캐릭터의 이전 첨부 파일을 이번 결과로 재안내하지 않는다. `last-batch.json`은 종료된 실행 기록이므로 진행 중인 실행이나 잠금 실패의 실시간 상태로 해석하지 않는다.

`summary.json`과 `diff.json`의 내용은 `ai-context.json`에 들어 있으므로 AI에 중복 첨부할 필요가 없다. 두 파일은 로컬 확인용으로 계속 생성한다. `latest.json`은 캐릭터별 수집 원본의 복사본이며, raw 이력과 함께 원본 검증용으로 보존한다.

출력은 먼저 별도 결과 묶음에 모두 저장·검증하고, 마지막에 `current.json` 하나를 교체해 완료 처리한다. 기존 경로의 네 파일은 편의 복사본이다. 파일 잠금은 교체 전 확인하고, 교체 도중 예외가 발생하면 바뀐 복사본을 이전 값으로 복구한다. 프로세스 강제 종료·전원 차단 중에는 편의 복사본끼리 시점이 다를 수 있으므로, **파일 여러 개를 함께 읽는 프로그램은 `current.json`을 한 번 읽고 그 묶음만 사용**한다. 묶음 검증은 모듈의 `Get-MaplePublishedSet`으로 할 수 있다. 수집 원본은 후처리에 실패해도 보존하며, 원본 수집 시각과 마지막 완료 시각이 다를 수 있다.

**기본 정보(`basic`) 또는 최종 스탯(`stat`)이 실패·누락되면** 실패 응답까지 raw에 보관한 뒤 후처리를 오류로 종료한다. `current.json`과 ai-context/summary/diff/latest는 마지막 정상 결과를 유지한다. 최초 수집부터 실패했다면 완료 결과를 만들지 않는다. 나머지 API만 실패한 경우는 품질 정보에 표시하고 부분 결과를 제공한다. 다음 정상 수집의 변경 비교에서도 필수 정보가 실패한 raw는 건너뛰고, 직전 필수 정보가 정상인 수집본을 기준으로 삼는다.

## AI에 전달하는 내용

- `metadata`: OCID를 포함한 원본 수집 메타데이터, raw 상대 경로와 SHA-256.
- `quality`: 각 API의 성공/실패/누락/불완전(`partial`), 오류, 구조 검증 사유(`validation_issues`), API 응답의 데이터 기준 시각. `date: null`은 기준 시각을 확인하지 못했다는 뜻이다.
- `quality.assessment`: 수행한 검증의 범위, 전체 스키마 검증 미수행, 섹션 간 동시 갱신·최종 스탯과 프리셋 연결 미확인, 기준 시각 없는 섹션 목록. 유니온 새 프리셋 필드는 `missing` / `null` / `empty_array` / `array_present` / `unexpected_type`을 구분한다. 배열 존재는 내용 검증이나 현재 적용의 증거가 아니다.
- `actual`: 모든 최종 스탯, 현재 장비의 상세 옵션·잠재·추옵·스타포스, 하이퍼 스탯·어빌리티, 심볼, 세트, 펫, 링크, V 매트릭스, HEXA 코어·스탯, 무릉, 기타 스탯, 반지, 유니온·아티팩트·챔피언.
- `presets`: 저장된 하이퍼 스탯·어빌리티·장비·칭호·링크/자체 링크·V 매트릭스·HEXA 스탯·유니온·펫 장비 프리셋. API 섹션과 원래 필드명을 유지하며, 현재 적용 설정으로 간주하지 않는다.
- `user_context`: 해당 캐릭터에 등록한 사용자 설명이 있을 때만 포함. `preset_roles`의 용도·원본 JSON 경로·데이터 존재 여부와, 등록된 월드의 `owned_link_skills` 보유 후보 목록을 제공한다. NEXON 응답과 분리되며 최종 스탯이나 활성 상태를 덮어쓰지 않는다.
- `changes_since_previous`: 직전의 더 오래된 **동일 캐릭터** 수집본과 비교한 현재 상태·저장 프리셋의 변경값 및 비교하지 못한 섹션. 프리셋 변경 경로는 `$.presets.`로 시작한다.

예를 들어 하이퍼 2번은 `presets.hyper_stat.hyper_stat_preset_2`, 어빌리티 2번은 `presets.ability.ability_preset_2`, 칭호 3번은 `presets.item_equipment.title_preset3`에 있다. 유니온 상태 프리셋은 `presets.union_raider.union_state_stat_preset`에 있다. 번호와 API가 반환한 순서를 유지하며, 보스용/사냥용 용도는 임의로 붙이지 않는다.

확인된 아이콘·이미지 필드의 HTTP(S) URL만 현재 상태와 프리셋에서 덜어낸다. 외형 이름·훈장 설명·펫 외형·OCID는 보존한다. 이미지 필드라도 null·객체·URL이 아닌 값은 남기며, 알 수 없는 필드는 이름만으로 버리지 않는다. 직업·성별은 `basic`과 값·타입이 같을 때만 중복 제거한다. `date`는 `quality.data_dates`로 옮기되 원본에 없는 필드는 null로 만들지 않는다.

하이퍼 스탯의 현재 배분은 API의 사용 프리셋 번호로 선택하며, 번호가 확인되지 않거나 선택한 값이 null/비정상 구조이면 `active_preset_resolved: false`, 섹션 상태 `partial`로 표시하고 후보들은 `presets`에 남긴다. 빈 배열은 null과 구분해 그대로 보존한다. 프리셋별 남은 포인트·수치 문자열·0·null·빈 배열도 보존한다. 스탯 이름은 NEXON의 한글 이름을 사용한다. `final_stat` 항목에 이름·값 이외의 속성이 있으면 원문 배열도 `actual.stat.final_stat`에 남긴다. 이때 `values`와 중복 합산하지 않는다. 값 필드가 누락되면 임의의 null로 바꾸지 않고 후처리를 실패시킨다. 아이템 설명은 효과 정보가 포함될 수 있어 유지한다. **이 파일은 raw 전체를 대체하지 않는다.** 생략한 이미지 URL, 현재 수집 대상 밖 정보, API 오류로 받지 못한 정보까지 포함한다는 뜻은 아니다.

API 최종 스탯에 장비·링크·유니온 효과를 다시 더하면 중복 계산이 된다. 수집 시각은 실제 게임 상태의 기준 시각과 같다고 보장하지 않는다. 제공된 API 범위 밖 정보나 실패 응답을 0/미장착으로 추정하지 않으며, 별도의 환산 계산은 하지 않는다.

`section_status: ok`는 섹션 존재와 오류 응답 여부를 기준으로 하며, 하이퍼 활성 배분 등 일부 추가 검증을 포함한다. 모든 필드가 정상이라는 뜻은 아니다. `validation_issues`가 비어 있어도 미검증 영역이 있으므로 `assessment`를 함께 읽는다.

## 단발 수집과 프리셋 용도

한 번 수집하여 현재 최종 스탯, 저장된 대안 프리셋, 이전 수집과의 차이를 제공한다. 두 프리셋을 연속 수집하거나 게임 내 전환을 감시하는 기능은 도입하지 않는다. 미착용 프리셋의 최종 전투력은 계산하지 않는다.

`preset-roles.json`에 캐릭터별 사용자 설명을 저장한다. 우노03은 사용자가 설명한 장비·하이퍼·어빌·링크의 1번을 보스용, 2번을 사냥용으로 연결했다. 유니온·V 매트릭스 등 별도 번호의 용도가 확인되지 않은 항목은 임의로 연결하지 않는다.

우노03레테의 용도 설명은 확인되지 않아 등록하지 않았다. 우노03 설명을 복사하지 않고 API가 제공한 프리셋만 보존한다.

설정의 `characters` 아래 캐릭터명, `recorded_on`(설명 기록일), `preset_roles`의 섹션별 번호/용도를 수정하면 다음 후처리부터 반영된다. 다른 캐릭터에 우노03 설명을 적용하지 않는다. 현재 지원하는 네 섹션은 1~3번을 지정할 수 있다. 설명 날짜는 API 수집 시각과 별개이며 재가공할 때 자동 갱신하지 않는다. 용도를 바꿨다면 설정도 함께 수정해야 한다.

참조 대상이 없으면 `data_presence: missing`, null이면 `null`, 값이 있으면 `present`로 표시한다. `present`는 내용의 유효성이나 현재 적용을 보증하지 않는다. 사용자 설명은 캐릭터 변화 diff에 섞지 않는다. 잘못된 설정 파일은 후처리를 오류로 종료하고 기존 완료 결과를 유지한다. 별도 설정은 `Build-MapleSnapshot.ps1 -PresetRolesPath 경로`로 지정하며, `-PresetRolesPath ''`로 설명을 제외할 수 있다. 과거 원본 재가공도 현재 지정한 설명을 사용하므로 기록일과 수집일을 함께 확인한다.

현재 수집에서는 과거 조회용 `ring_exchange`를 호출하지 않고 `ring_reserve`를 사용한다. [NEXON의 2026-03-19 업데이트 안내](https://openapi.nexon.com/ko/support/notice/3402834/)에 따른 구분이다. 기존 raw에 남아 있는 `ring_exchange` 데이터/오류는 그대로 읽고 보존하므로, 과거 수집본을 재가공했다고 과거 오류가 사라지지는 않는다.

## 보유 링크 후보 목록

`owned-link-skills.json`은 사용자 확인 목록을 담는 별도 설정 데이터다. 링크 이름이나 개수는 코드에 고정하지 않는다. 스카니아의 우노03·우노03레테를 같은 그룹으로 등록했으며, 2026-10-03 사용자 재확인 19종을 초기 데이터로 사용한다. 스크린샷 파일은 제공되지 않았으므로 별도 이미지 검증을 주장하지 않는다. 다른 월드나 미등록 캐릭터에는 자동 적용하지 않는다.

- `user_context.owned_link_skills`: 이름, `level`, 출처(`user_verified` / `api_observed`), 관측 레벨과 캐릭터·필드·수집 시각, `level_review_required`.
- `user_context.owned_link_skills_info`: 그룹·월드·사용자 확인일·확인 캐릭터·근거·API 관측 상한 시각·경고·추천 규칙. API 수집보다 뒤의 사용자 확인을 적용한 경우 `verification_newer_than_snapshot: true`다.
- 추천은 이 목록의 이름을 후보로 삼는다. 목록 밖은 보유 미확인/육성 후보로 분리한다. 실제 장착·자체 링크·효과·프리셋은 **해당 캐릭터의** `actual.link_skill`과 `presets.link_skill`을 읽는다. 본인 링크를 전수 슬롯에 중복 추천하지 않는다. [공식 링크 스킬 안내](https://maplestory.nexon.com/Guide/N23GameInformation/Articles/406)

현재 원본과 보존된 raw에서 현재 링크·자체 링크·각 1~3번 프리셋을 조사한다. 표준 `output/characters/<캐릭터>/` 구조에서는 같은 그룹에 명시된 캐릭터의 raw도 함께 읽는다. 별도 출력 폴더에서는 그 폴더의 raw만 사용한다. 다른 월드·미등록 캐릭터·현재 수집 시각보다 미래인 원본은 제외한다. 관측 자료는 캐릭터/필드/레벨별 마지막 시각으로 압축한다.

전체 목록 확인일 이후에 API에서 새 이름이 발견되면 자동 추가한다. 이후 미관측·API 실패만으로 삭제하지 않으며 raw 이력으로 재구성하므로 별도 변경 가능한 캐시를 만들지 않는다. raw를 보존해야 과거 API 추가 항목도 유지된다. 전체 목록을 다시 검증할 때 설정의 `skills`와 `verified_on`을 갱신하면, 새 확인일보다 오래된 미등록 항목을 다시 보유 목록으로 끌어오지 않는다.

사용자 확인 레벨은 API로 덮어쓰지 않는다. 확인일 이후 다른 레벨이 관측되면 `level_review_required`로 표시한다. API에서만 추가된 항목은 관측 레벨이 하나일 때만 `level`을 채우며 여러 레벨이면 null로 남긴다. 최대값 선택이나 합산을 하지 않는다. 차이는 성장·프리셋·자체 링크 등 맥락 확인 대상이며 오류나 현재 적용 레벨로 단정하지 않는다. 오래된 관측도 날짜와 함께 남지만 현재 수준을 보증하지 않는다.

API 수집·`actual`·`presets`·직전 diff는 이 사용자 컨텍스트와 독립적이다. `Build-MapleSnapshot.ps1 -OwnedLinksPath 경로`로 별도 설정을 지정하고 `-OwnedLinksPath ''`로 보유 목록만 제외할 수 있다. 기존 `-PresetRolesPath ''`는 프리셋 용도 설명만 제외한다. 설정 오류 시 이전 완료 묶음을 유지한다.

## 변경 비교와 이력

- 첨부에는 **직전 비교 가능한 수집과의 변화만** 담는다. 누적 이력이나 최근 N회 이력은 추가하지 않는다. 더 오래된 원본·완료 묶음·전달본은 로컬에 남지만, 최신 첨부만 받은 AI가 자동으로 읽을 수 있는 것은 아니다.
- 정상 수집된 섹션끼리만 비교한다. 이전 성공 → 이번 실패/불완전을 현재 장비나 저장 프리셋의 삭제로 표시하지 않는다.
- 장비 슬롯·심볼명·스킬명 등 양쪽 배열에 유일한 식별자가 있으면 같은 항목끼리 비교한다. 그 외 배열은 위치로 비교한다. 현재 상태 배열의 원래 순서는 바꾸지 않는다.
- `before_exists` / `after_exists`로 필드 누락과 `null`을 구분하고 문자열·숫자·boolean도 구분한다.
- 같은 원본을 다시 처리하면 SHA-256으로 기존 raw를 재사용한다. 직전 비교 대상도 유지하므로 재가공만으로 변경 내역이 0건이 되지 않는다.
- 과거 원본은 수집 시각 순서로 선택한다. 손상된 과거 파일은 건너뛰고 `history_warnings`에 표시한다. 같은 시각에 서로 다른 원본이 있으면 비교를 중단한다.
- 현재 스키마는 `schema_version: 3`이다. 버전 2에서 빠졌던 저장 프리셋이 별도 영역으로 추가되었다. 예전 raw도 같은 규칙으로 재가공한 뒤 비교하므로 스키마 변경 자체를 캐릭터 변화로 세지 않는다.

## 구성과 검증

| 파일 | 역할 |
|---|---|
| `Run-MapleCharacters.ps1`, `MapleBatch.psm1` | 두 캐릭터 순차 실행, 공통 키 입력, 실행 잠금, 기존 이력 복사, 결과 집계 |
| `Get-MapleCharacterData.ps1` | SecureString 키 입력, API 요청 간격·429 재시도·요청 제한 시간, 원본 저장 |
| `MapleSnapshot.psm1` | API 목록, JSON 입출력, AI용 상태 정리, 변경 비교 |
| `Build-MapleSnapshot.ps1` | raw 이력 선택·보관과 출력 생성 |
| `preset-roles.json` | 캐릭터별 사용자 설명. API 원본과 별개로 보존하는 프리셋 용도 |
| `owned-link-skills.json`, `MapleOwnedLinks.psm1` | 월드·캐릭터 그룹별 사용자 확인 링크와 raw 관측을 합친 보유 후보 목록 |
| `tests/Test-MapleSnapshot.ps1` | 네트워크 없이 가공·변경 비교·원본 보존 검증 |

```powershell
pwsh -NoProfile -File ./tests/Test-MapleSnapshot.ps1
pwsh -NoProfile -File ./tests/Test-MapleBatch.ps1
pwsh -NoProfile -File ./tests/Test-MapleOwnedLinks.ps1
```

환산 실험용 코드·테스트·의존성·가상환경·문서는 제거했다. 기존 `.runtime/`, `fixtures/maplescouter/`의 로컬 자료는 이 도구에서 사용하지 않으며, 기존 사용자 상태/증거 보존을 위해 Git 제외 상태로 남겨 두었다.

Data based on NEXON Open API. [공식 안내](https://openapi.nexon.com/ko/game/maplestory/)
