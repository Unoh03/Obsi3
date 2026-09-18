# Maple Bridge Phase 1

기존 NEXON 수집기를 유지하면서 실제 환산 웹의 요청·응답과 외부 replay를 검증하는 로컬 도구다. 계산식이나 자동 `userStat` 변환기는 구현하지 않는다.

## 설치 및 검증

PowerShell 7에서 실행한다. API key는 기존 수집기 입력창에만 입력한다.

```powershell
Set-Location 'D:\Obsidian\Vault\Obsi2\scripts\maple'
python -m venv .venv
& .venv/Scripts/python.exe -m pip install -r requirements-phase1.txt
& .venv/Scripts/python.exe tools/maple_phase1.py doctor
& .venv/Scripts/python.exe -m unittest discover -s tests -v
```

Windows Codex sandbox에서 Python 임시 폴더·Playwright 파이프 생성이 `PermissionError`로 막힐 수 있다. 이는 테스트 판정과 구분한다. 같은 명령을 승인된 일반 실행 환경에서 재실행하며 파일 ACL이나 TLS 검증을 완화하지 않는다.

## 수집 준비

```powershell
& tools/Start-ScouterCaptureBrowser.ps1
& tools/Collect-Phase1Snapshot.ps1
& .venv/Scripts/python.exe tools/maple_phase1.py probe
& .venv/Scripts/python.exe tools/maple_phase1.py context-template --out .runtime/context.json
```

- 전용 Brave에서 우노03을 검색하고 평소 설정과 일치하는지 확인한다. 기본 프로필은 복사하지 않는다.
- 수집 helper는 기존 collector → snapshot 처리 → SHA-256으로 고정한 NEXON 사본 생성 순서다. 완료된 bundle 경로는 `.runtime/latest-frozen-snapshot.txt`에 기록한다.
- `.runtime/context.json`에서 확인한 설정·UI 표시값을 작성하고, 실제 확인한 뒤에만 `settings_confirmed`를 `true`로 바꾼다. 모르는 설정은 `unknown`으로 유지한다.
- 기존 파일은 재사용 시 명시적으로 읽는다. 모든 생성 명령은 기존 경로를 덮어쓰지 않으므로 실험 ID와 출력 경로는 매번 새롭게 지정한다.
- 브라우저 프로필·가상환경·실제 fixtures는 Git ignore 대상이다. 필터가 모든 비밀을 자동 판별한다고 보장하지 않으며, 별도 검토 전 Git에 추가하지 않는다.

## baseline 캡처

`probe`로 나온 정확한 페이지 URL을 사용한다. `--snapshot`은 helper가 만든 **bundle 디렉터리**다.

```powershell
$Snapshot = (Get-Content .runtime/latest-frozen-snapshot.txt -Raw).Trim()
& .venv/Scripts/python.exe tools/maple_phase1.py capture --page-url '<probe에서 확인한 URL>' --host maplescouter.com --snapshot $Snapshot --context .runtime/context.json --kind baseline-normal --out fixtures/maplescouter/baseline-normal-a
```

1. CLI에서 Enter를 눌러 `ARMED` 확인.
2. 사용자가 같은 조건으로 실제 환산 조회/계산을 실행.
3. 결과 표시가 끝난 뒤 CLI에서 Enter를 눌러 STOP.
4. 아무 설정도 바꾸지 않고 `baseline-normal-b`로 반복.

`--seconds 120 --stop-file .runtime/stop-a`로 시간 제한/파일 신호 방식도 사용할 수 있다. stop 파일은 새 경로를 지정한다. 과거 stop 파일이 있으면 캡처가 즉시 끝날 수 있다.

HTTP cache는 normal에서 건드리지 않는다. 요청/body가 없을 때만 `--kind baseline-forced-network --forced-network`로 별도 두 건을 수집한다. body 보존 오류가 확인된 경우 `--buffer-mb 32` 같은 별도 조건으로 재캡처한다. service worker는 자동 우회하지 않는다.

각 캡처의 `requests.json`에서 URL·method·시각·응답·UI 변화가 계산과 연결되는 요청을 **실제로 선택**한다. 첫 POST를 자동으로 계산 endpoint로 지정하지 않는다. `request-0001-hop-0` 등의 디렉터리는 요청별 fixture이며, context는 상위 캡처 디렉터리에 있다. 관측 범위는 선택한 페이지 CDP이고 worker/OOPIF 전체 커버리지는 미확인이다.

## 설정 선택 백업

사이트 Export가 있으면 우선 사용한다. 없으면 key 이름부터 확인한다.

```powershell
& .venv/Scripts/python.exe tools/maple_phase1.py storage list --page-url '<현재 URL>'
& .venv/Scripts/python.exe tools/maple_phase1.py storage export --page-url '<현재 URL>' --key '<확인된 설정 key>' --out fixtures/maplescouter/settings-backup.json
```

값은 명시한 key만 읽는다. 민감 key·민감 필드를 포함한 JSON은 저장하지 않는다. 아직 실제 key/schema를 관측하지 않았으므로 `preset`이나 `character-store`를 하드코딩하지 않는다. 백업은 원문 문자열과 origin을 보존한다. 복원은 동일 origin에서 해당 key만 `localStorage.setItem`한 뒤 새로고침하는 방식이며, 자동 복원 명령은 제공하지 않는다. 사용자가 복원하거나, 확인된 백업을 대상으로 필요한 복원만 수행한 후 UI·계산 결과를 재검증한다.

## 비교와 replay

```powershell
& .venv/Scripts/python.exe tools/maple_phase1.py diff '<A 요청/request.json>' '<B 요청/request.json>' --out '<새 diff.json>'
& .venv/Scripts/python.exe tools/maple_phase1.py replay '<선택한 요청 디렉터리>' --mode observed --out '<새 replay-observed 디렉터리>'
& .venv/Scripts/python.exe tools/maple_phase1.py replay '<같은 요청 디렉터리>' --mode json --out '<새 replay-json 디렉터리>'
```

- `observed`: 보존된 POST data의 hash를 확인하고 `content=`로 전송한다.
- `json`: 같은 body를 파싱한 `request.json`인지 확인한 뒤 `json=`으로 전송한다. UTF-8 JSON을 대상으로 한다.
- HTTPX는 `trust_env=False`, redirect off, 30초 timeout, 새 client, 재시도 없음이다. CLI는 HTTPS endpoint만 허용한다.
- 기본 replay 헤더는 관측된 Content-Type/Accept/Origin/Referer다. 비민감 커스텀 헤더는 capture의 `--allow-header X-Client-Version`으로 검토 후 보존하고 replay의 `--header X-Client-Version`으로 명시해서 사용한다. 민감 헤더는 override로 허용할 수 없다.
- 캡처 헤더와 replay 헤더 차이·제외 사유를 확인한다. 응답이 JSON이 아니거나 민감값을 포함하면 body 저장을 중단하고 오류 종류만 기록한다.
- `parsed_response_equal`은 파싱된 JSON 비교, `body_bytes_equal`은 보존한 body와의 바이트 비교다. 둘 다 UI mapping이나 전체 backend 적합성의 자동 PASS를 뜻하지 않는다.
- diff exit code: 0 동일, 1 차이 있음, 2 오류. replay는 HTTP 200만으로 A 판정을 자동 승격하지 않는다.

## 변경 실험과 판정

일반 stat 하나와 Scouter-only 설정 하나를 각각 baseline에서 변경한다. context의 `backup_path`와 `changed_setting`을 작성하고 `--kind perturb-stat` 또는 `perturb-special`을 사용한다. 매 실험 후 설정·계산 입력·결과가 baseline으로 돌아왔는지 확인한다. 설명되지 않는 차이가 있으면 다음 실험을 멈춘다.

normal/forced-network에서 계산 요청이 없으면 iframe·worker·service worker, 다른 통신 방식, JS/WASM·결과 재사용을 조사한다. endpoint를 추측하지 않는다. 수동 DevTools는 교차 확인용 fallback이다.

## 로컬 CDP 스모크 테스트

```powershell
& .venv/Scripts/python.exe tests/smoke_cdp.py
```

전용 Brave에 별도의 임시 context를 만들고 loopback HTTP 서버만 호출한다. 실제 CDP 캡처→observed/JSON replay 경로를 확인한 후 해당 context와 서버만 닫는다. **MapleScouter의 endpoint·schema·결과 검증은 아니다.**

상세 진행 상태는 [contract](docs/maplescouter-contract.md), 기존 구조는 [현재 구조](docs/current-architecture.md)에 기록한다.
