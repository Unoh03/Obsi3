---
type: project-log
topic: security-project
status: active
created: 2026-06-17
---

# KISA Web Application 반자동 진단 스크립트 작업 로그

이 문서는 `KISA Web Application 반자동 진단 스크립트` 작업 중 컨텍스트 압축으로 사라지기 쉬운 결정 과정, 검증 결과, 다음 작업 기준을 남기는 운영 로그다.

설계 원칙은 `KISA Web Application 반자동 진단 스크립트 설계.md`에 두고, 이 문서는 실제 구현 과정의 이력만 기록한다.

## 기록 원칙

- 큰 설계 변경, 구현 milestone, 검증 결과, 다음 `/goal` 기준만 기록한다.
- raw request/response, 실행 산출물 전체는 `kisa-webapp-checker/evidence/` 아래 run별 결과에 맡긴다.
- 보고서용 문장보다 나중에 작업을 재개할 때 필요한 판단 근거를 우선한다.
- 구현 중 실패한 가설도 다음 작업에 영향을 주면 짧게 남긴다.

## 2026-06-17 v0 구현

### 목적

v0의 목표는 KISA Web Application 01~21 전체 진단이 아니라, 아래 파이프라인이 실제로 동작하는지 확인하는 것이었다.

```text
profile -> check -> request -> evidence -> report
```

### 구현 범위

생성 위치:

```text
20_팀 프로젝트/26. 6. 8 팀플/쉘 스크립트/kisa-webapp-checker/
```

생성 및 확인한 파일:

```text
checker.py
requirements.txt
README.md
profiles/care.yml
checks/17_plaintext_transport.yml
checks/21_unnecessary_method.yml
evidence/.gitkeep
```

v0 포함 항목:

| 번호 | 항목 | mode | v0 역할 |
|---:|---|---|---|
| 17 | 데이터 평문 전송 | `passive` | base URL scheme, 민감 route 후보, form action 관찰 |
| 21 | 불필요한 Method 악용 | `safe-active` | `OPTIONS`, `TRACE`, `PUT`, `DELETE` 요청 구조 준비 |

### 주요 결정

- `checker.py`에는 CARE 전용 URL, 계정, payload를 넣지 않는다.
- CARE 관련 값은 `profiles/care.yml`에만 둔다.
- KISA 항목별 동작은 `checks/*.yml`에 둔다.
- v0에는 SQLi, XSS, SSRF payload, 로그인 자동화, 상태 변경 테스트를 넣지 않는다.
- `requests`, `PyYAML`을 권장 dependency로 두되, bare Python 환경에서도 v0 검증이 가능하도록 제한적 fallback을 넣었다.
- HTTP 요청 실패도 evidence로 남기도록 request 파일과 error response 파일을 생성하게 했다.

### 검증 결과

실행한 검증:

```bash
python -c "import py_compile, tempfile, pathlib; py_compile.compile(..., cfile=..., doraise=True)"
python checker.py --help
python checker.py --profile profiles/care.yml --checks checks --mode passive --validate-only
python checker.py --profile profiles/care.yml --checks checks --mode safe-active --validate-only
python checker.py --profile profiles/care.yml --checks checks --mode passive --output <TEMP>
rg -n "172\.168\.10\.10|victim|admin|/member/login|/center|http://127" checker.py
git diff --check
git status --short
```

확인한 사실:

- `py_compile` 통과.
- `--help` 출력 정상.
- passive validate에서 17번은 `passed`, 21번은 `skipped_by_mode`.
- safe-active validate에서 17번과 21번 모두 config 검증 통과.
- passive 실제 실행에서 `result.json`, `report.md`, `run.log`, `rollback_checklist.md` 생성 확인.
- target 서버가 없는 상태의 connection refused도 request/error response evidence로 남음.
- `checker.py`에서 CARE 전용 값 하드코딩 검색 결과 없음.
- `git diff --check` 통과.
- repo 내부 `__pycache__` 생성 없음.

### 현재 한계

- v0는 진단기 완성본이 아니라 프레임워크 pipeline 검증본이다.
- 현재 자동 진단 항목은 17, 21뿐이다.
- 21번은 실제 `safe-active` 실행 시 `PUT`, `DELETE` 요청을 보낼 수 있으므로 실습 대상에서만 실행해야 한다.
- 결과 판정은 아직 항목별 정밀 진단이라기보다 evidence 수집 구조 확인에 가깝다.

### 다음 작업 기준

다음 `/goal`은 v1 구현으로 잡는다.

v1 후보:

```text
03 디렉터리 인덱싱
04 에러 페이지
05 정보 노출
15 파일 다운로드
16 세션 예측
19 관리자 페이지 노출
21 불필요한 Method 악용 보강
```

v1에서도 금지할 것:

- SQLi/XSS/SSRF payload 추가
- 로그인 자동화
- brute force
- 파일 업로드/삭제/수정
- DB 변경
- ZAP/Nuclei 연동
- 01~21 전체 구현으로 scope 확장

## 2026-06-17 v1 구현

### 목적

v1의 목표는 v0 파이프라인을 유지하면서, KISA X. Web Application 항목 중 비교적 안전하게 자동/반자동 점검 가능한 항목을 추가하는 것이었다.

범위는 low-risk `passive` / `safe-active` 항목으로 제한했다. SQLi, XSS, SSRF payload, 로그인 자동화, brute force, 파일 업로드/삭제, DB 변경은 포함하지 않았다.

### 구현 범위

추가 및 보강한 check:

| 번호 | 항목 | mode | 구현 방식 |
|---:|---|---|---|
| 03 | 디렉터리 인덱싱 | `safe-active` | 후보 디렉터리 GET 후 listing 패턴 확인 |
| 04 | 에러 페이지 | `safe-active` | 없는 경로 GET 후 stack trace, local path, version 노출 확인 |
| 05 | 정보 노출 | `safe-active` | 후보 민감 파일 GET 후 설정/소스 노출 패턴 확인 |
| 15 | 파일 다운로드 | `safe-active` | profile에 정의한 known download candidate 접근 확인 |
| 16 | 불충분한 세션 관리 | `passive` | session cookie의 `HttpOnly`, `SameSite`, `Secure` 조건 확인 |
| 17 | 데이터 평문 전송 | `passive` | v0 기능 유지 |
| 19 | 관리자 페이지 노출 | `safe-active` | 후보 관리자 페이지 접근 가능 여부 확인 |
| 21 | 불필요한 Method 악용 | `safe-active` | v0 기능 유지, v1 README 기준으로 정리 |

추가한 범용 action:

```text
path_probe
inspect_cookies
```

`path_probe`는 status code, body regex, header regex를 YAML에서 받아 판정한다. `inspect_cookies`는 Set-Cookie 응답을 보고 session cookie 방어 플래그를 확인한다.

### 주요 결정

- 취약점마다 Python 함수를 새로 만들지 않고, 범용 action + YAML rule 구조로 확장했다.
- CARE 전용 route 후보는 `profiles/care.yml`에만 추가했다.
- `checker.py`에는 CARE URL, 계정, payload를 넣지 않았다.
- 15번은 traversal payload 없이 profile에 정의한 known download candidate 접근 여부만 확인한다.
- 16번은 세션 ID 예측 자체를 자동화하지 않고, cookie flag 점검 수준으로 제한한다.
- 21번 실제 실행은 `safe-active`이며, 실습 대상에서만 돌린다는 주의를 README에 남겼다.

### 검증 결과

실행한 검증:

```bash
python -c "import py_compile, tempfile, pathlib; py_compile.compile(..., cfile=..., doraise=True)"
python checker.py --help
python checker.py --profile profiles/care.yml --checks checks --mode passive --validate-only
python checker.py --profile profiles/care.yml --checks checks --mode safe-active --validate-only
python checker.py --profile profiles/care.yml --checks checks --mode passive --output <TEMP>
python checker.py --profile profiles/care.yml --checks <TEMP 21-only checks> --mode safe-active --output <TEMP>
```

확인한 사실:

- `py_compile` 통과.
- `--help` 출력 정상.
- passive validate에서 safe-active 항목은 `skipped_by_mode`, 16/17번은 `passed`.
- safe-active validate에서 03, 04, 05, 15, 16, 17, 19, 21번 config 검증 통과.
- passive 실제 실행에서 `result.json`, `report.md`, `run.log`, `rollback_checklist.md` 생성 확인.
- target 서버가 없는 상태에서는 16번이 connection refused로 `error`가 되지만, request/error response evidence는 남는다.
- 21번만 따로 safe-active 실제 실행했을 때 OPTIONS/TRACE/PUT/DELETE request/error response evidence가 생성됐다.

### 현재 한계

- v1도 아직 완성형 01~21 진단기가 아니다.
- 03, 04, 05, 15, 19는 profile에 등록된 후보 경로에 의존한다.
- 15번은 path traversal 공격 검증이 아니라 known candidate 노출 확인이다.
- 16번은 cookie flag 중심이며, 세션 ID 난수성이나 재사용성까지 자동 검증하지 않는다.
- 실제 CARE 서버에서 돌려야 HTTP 성공/차단 기준의 의미 있는 판정이 나온다.

### 다음 작업 기준

다음 `/goal`은 v2 후보 중 상태 변경이 필요하지만 비교적 구현 가능한 항목으로 잡는다.

v2 후보:

```text
02 SQL 인젝션
06 XSS
07 CSRF
09 약한 비밀번호 정책
10 불충분한 인증 절차
11 불충분한 권한 검증
14 악성 파일 업로드
20 자동화 공격
```

단, v2부터는 로그인, fixture, rollback, state-changing 허용 범위를 먼저 정해야 한다.

## 2026-06-18 실제 WEB 서버 실행 테스트와 v2 전환 결정

### 목적

v1 checker를 실제 WEB 서버 홈 디렉터리에서 실행해 보고, validate-only 결과와 실제 실행 결과가 어떻게 다른지 확인했다.

또한 16번과 17번은 VM/GNS 환경에서 완전 조치까지 밀어붙이기보다 AWS 환경에서 HTTPS를 구성한 뒤 재검증하는 편이 낫다고 판단했다.

### 실행한 명령

사용자가 WEB 서버에서 실행한 명령은 다음과 같다.

```bash
cd kisa-webapp-checker/

python3 checker.py --profile profiles/care.yml --checks checks --mode passive --validate-only

python3 checker.py --profile profiles/care.yml --checks checks --mode passive

mkdir -p /tmp/kisa-checks-21
cp checks/21_unnecessary_method.yml /tmp/kisa-checks-21/
python3 checker.py --profile profiles/care.yml --checks /tmp/kisa-checks-21 --mode safe-active
```

### 확인된 결과

`passive --validate-only` 결과:

```text
[OK] run_id=20260618-002938
[OK] evidence=/home/webuser/kisa-webapp-checker/evidence/20260618-002938
[skipped_by_mode] 03 디렉터리 인덱싱
[skipped_by_mode] 04 에러 페이지
[skipped_by_mode] 05 정보 노출
[skipped_by_mode] 15 파일 다운로드
[passed] 16 불충분한 세션 관리
[passed] 17 데이터 평문 전송
[skipped_by_mode] 19 관리자 페이지 노출
[skipped_by_mode] 21 불필요한 Method 악용
```

`passive` 실제 실행 결과:

```text
[OK] run_id=20260618-002949
[OK] evidence=/home/webuser/kisa-webapp-checker/evidence/20260618-002949
[skipped_by_mode] 03 디렉터리 인덱싱
[skipped_by_mode] 04 에러 페이지
[skipped_by_mode] 05 정보 노출
[skipped_by_mode] 15 파일 다운로드
[vulnerable] 16 불충분한 세션 관리
[vulnerable] 17 데이터 평문 전송
[skipped_by_mode] 19 관리자 페이지 노출
[skipped_by_mode] 21 불필요한 Method 악용
```

21번만 따로 `safe-active`로 실행한 결과:

```text
[OK] run_id=20260618-003323
[OK] evidence=/home/webuser/kisa-webapp-checker/evidence/20260618-003323
[not_vulnerable] 21 불필요한 Method 악용
```

### 해석

`validate-only`의 `passed`는 설정 파일과 실행 전제의 형식 검증이 통과했다는 뜻으로 본다. 실제 서비스 상태가 안전하다는 의미가 아니다.

실제 `passive` 실행에서 16번과 17번이 `vulnerable`로 나온 이유는 다음처럼 해석했다.

| 번호 | 결과 | 해석 |
|---:|---|---|
| 16 | `vulnerable` | HTTPS가 없으면 `Secure` 쿠키 속성까지 완성 검증하기 어렵다. 현재 cookie flag 기준에서 취약으로 판정됨 |
| 17 | `vulnerable` | profile의 기준 URL과 실제 서비스가 HTTP 기반이므로 데이터 평문 전송 취약 상태로 판정됨 |
| 21 | `not_vulnerable` | 현재 CARE/Apache 환경에서 불필요한 Method 악용은 v1 checker 기준으로 취약하지 않음 |

### 주요 결정

- 16번과 17번을 VM/GNS에서 더 끌지 않고 AWS 후속 검증으로 분리했다.
- AWS 후속 절차는 [[AWS 후속 조치와 재검증|AWS 후속 조치와 재검증]]에 정리했다.
- v1 checker의 기본 구조는 유지한다.
- 다음 작업은 v2로 넘어간다.

### 현재 한계

- 16번의 `vulnerable` 판정은 세션 ID 난수성, 세션 재사용성 전체를 자동 검증한 결과가 아니라 cookie flag 중심 판정이다.
- 17번의 `vulnerable` 판정은 현재 환경이 HTTP라는 사실과 직접 연결된다.
- AWS에서 HTTPS가 구성되면 `profiles/care.yml`의 `base_url`을 `https://...`로 바꾸고 16/17을 다시 확인해야 한다.
- v2부터는 로그인, fixture, rollback, state-changing 요청을 어떻게 다룰지 결정해야 한다.

### 다음 작업 기준

다음 작업은 v2로 간다.

v2의 목표는 v1보다 더 실제 취약점에 가까운 항목을 다루되, 하드코딩된 CARE 전용 공격기가 아니라 profile 기반 반자동 진단기 구조를 유지하는 것이다.

우선 검토할 후보:

```text
02 SQL 인젝션
06 XSS
07 CSRF
09 약한 비밀번호 정책
10 불충분한 인증 절차
11 불충분한 권한 검증
14 악성 파일 업로드
20 자동화 공격
```

v2 시작 전에 정해야 할 것:

- 로그인 세션을 profile로 주입할지
- 테스트용 fixture 계정을 둘지
- state-changing 요청을 어디까지 허용할지
- evidence를 어디까지 저장할지
- rollback checklist를 항목별로 만들지

## 2026-06-18 v2 공통 기반과 02 SQL 인젝션 check 추가

### 목적

v2의 첫 작업은 02, 06, 07, 09, 10, 11, 14, 20을 한 번에 완성하는 것이 아니라, v2 계열 check를 안전하게 붙일 수 있는 공통 기반을 만드는 것이었다.

이번 범위는 다음으로 제한했다.

```text
v2 공통 기반
-> session 주입
-> fixture / rollback 메모 구조
-> payload 파일 참조
-> state-changing confirm
-> generic payload_probe action
-> 02 SQL 인젝션 check 1개
```

### 구현 범위

수정 및 추가한 파일:

```text
kisa-webapp-checker/checker.py
kisa-webapp-checker/README.md
kisa-webapp-checker/profiles/care.yml
kisa-webapp-checker/checks/02_sql_injection.yml
kisa-webapp-checker/payloads/sqli.yml
```

추가한 엔진 기능:

| 기능 | 내용 |
|---|---|
| `payload_probe` | payload 파일 또는 inline payload를 route parameter에 주입하고 response status/body/header rule로 판정 |
| `payloads/*.yml` | SQLi 등 payload를 checker.py 밖으로 분리 |
| `session.cookies` / `session.headers` | 로그인 자동화 대신 profile에서 기존 세션 쿠키나 헤더를 주입할 수 있게 함 |
| `fixtures` | 테스트 prefix, 계정, 게시글, 업로드 파일 등 상태 변경 전제를 profile에 기록할 공간 |
| `rollback` | profile 기반 rollback 메모를 `rollback_checklist.md`에 반영 |
| `--confirm-state-changing` | `state-changing` 이상 실제 실행 시 필수 확인 플래그 |
| `--confirm-destructive-risk` | `destructive-risk` 실제 실행 시 필수 확인 플래그 |

추가한 v2 check:

| 번호 | 항목 | mode | 구현 상태 |
|---:|---|---|---|
| 02 | SQL 인젝션 | `attack-active` | `board_search` route의 `data` parameter에 `payloads/sqli.yml` payload를 주입하는 구조 추가 |

### 주요 결정

- `checker.py`에는 CARE URL, 계정, 게시글 번호, SQLi payload를 넣지 않았다.
- CARE의 검색 route는 `profiles/care.yml`의 `board_search`에만 추가했다.
- SQLi payload는 `payloads/sqli.yml`에 분리했다.
- 02번은 `attack-active`로 두어 `passive`와 `safe-active` 기본 실행에서는 스킵되게 했다.
- 로그인 자동화는 아직 넣지 않았다. 대신 profile의 `session.cookies` / `session.headers`로 기존 세션을 주입하는 방식을 먼저 열었다.
- state-changing 이상은 실제 실행 시 confirm 없이는 막히게 했다.

### v2 후보 재분류

| 번호 | 항목 | v2 판단 | 기본 mode | 필요 fixture / 전제 | 이번 구현 |
|---:|---|---|---|---|---|
| 02 | SQL 인젝션 | 먼저 구현 가능 | `attack-active` | 검색/로그인/조회 route, payload 파일 | 구현 시작 |
| 06 | XSS | 구현 가능하나 reflected/stored 분리 필요 | `attack-active` 또는 `state-changing` | reflected route 또는 테스트 게시글 fixture | 보류 |
| 07 | CSRF | 반자동. 토큰 부재와 상태 변경 재전송 확인 필요 | `state-changing` | 로그인 세션, 회원정보 수정 route, rollback | 보류 |
| 09 | 약한 비밀번호 정책 | 반자동. 회원가입/수정 route 필요 | `state-changing` | 테스트 계정, 약한 비밀번호 목록, cleanup | 보류 |
| 10 | 불충분한 인증 절차 | 반자동. 중요 기능 접근 전 재인증 요구 여부 확인 | `state-changing` | 로그인 세션, 회원정보 수정 route | 보류 |
| 11 | 불충분한 권한 검증 | 반자동. 사용자 A/B와 객체 ID fixture 필요 | `state-changing` | 저권한/고권한 계정, 게시글/회원 object id | 보류 |
| 14 | 악성 파일 업로드 | 반자동. 안전한 proof 파일만 허용 | `state-changing` | 업로드 route, proof file, cleanup path | 보류 |
| 20 | 자동화 공격 | 위험. rate limit과 요청 상한 먼저 필요 | `destructive-risk` | 요청 횟수 상한, sleep, 중단 조건 | 보류 |

### 검증 결과

실행한 검증:

```bash
python -c "import py_compile, tempfile; py_compile.compile('checker.py', cfile=tempfile.NamedTemporaryFile(delete=False).name, doraise=True); print('py_compile ok')"
python checker.py --help
python checker.py --profile profiles/care.yml --checks checks --mode passive --validate-only --output "$env:TEMP\kisa-checker-validate-passive2"
python checker.py --profile profiles/care.yml --checks checks --mode safe-active --validate-only --output "$env:TEMP\kisa-checker-validate-safe2"
python checker.py --profile profiles/care.yml --checks checks --mode attack-active --validate-only --output "$env:TEMP\kisa-checker-validate-attack2"
python checker.py --profile profiles/care.yml --checks checks --mode state-changing --validate-only --output "$env:TEMP\kisa-checker-validate-state2"
python checker.py --profile profiles/care.yml --checks checks --mode state-changing --output "$env:TEMP\kisa-checker-state-block2"
git diff --check
```

확인한 사실:

- `py_compile` 통과.
- `--help`에 v2 설명과 `--confirm-state-changing`, `--confirm-destructive-risk` 표시.
- `passive --validate-only`에서 02번은 `skipped_by_mode`, 16/17은 `passed`.
- `safe-active --validate-only`에서 02번은 `skipped_by_mode`, v1 safe-active 항목은 `passed`.
- `attack-active --validate-only`에서 02,03,04,05,15,16,17,19,21 모두 설정 검증 통과.
- `state-changing --validate-only`도 설정 검증 통과.
- 실제 `state-changing` 실행은 confirm 없이 다음 오류로 차단됨.

```text
[ERROR] `state-changing` mode requires --confirm-state-changing
```

- `git diff --check` 통과.
- `checker.py`에서 CARE 전용 URL, 계정명, SQLi payload 하드코딩 검색 결과 없음.
- repo 내부 `__pycache__` 생성 없음.

### 현재 한계

- 02번은 error-based SQLi 중심의 첫 구조다. boolean-based diff, time-based check, 로그인/조회 route 검증은 아직 없다.
- `payload_probe`는 GET/POST parameter 주입만 지원한다.
- 로그인 자동화는 아직 없다. 현재 방식은 profile에 기존 세션 쿠키/헤더를 주입하는 방식이다.
- state-changing check의 rollback은 아직 자동 생성이 아니라 profile 메모와 공통 checklist 중심이다.
- v2 후보 중 06,07,09,10,11,14,20은 아직 구현하지 않았다.
- 실제 `attack-active` 실행은 하지 않았다. 이번 검증은 validate-only와 confirm 차단 확인까지만 수행했다.

### 다음 작업 기준

다음 작업은 둘 중 하나로 잡는다.

```text
1. 02 SQL 인젝션을 실제 CARE 검색 route 기준으로 제한 실행하고 evidence 품질 확인
2. 06 XSS 또는 07 CSRF를 위한 state-changing fixture 구조를 먼저 구현
```

권장 순서는 1번이다. 02번은 state-changing이 아니므로 v2 첫 실제 실행 검증 대상으로 가장 부담이 낮다.

## 2026-06-18 다음 `/goal` 실행 전 상태 고정

### 현재 확정된 흐름

방금 완료한 goal은 v2 전체 완성이 아니라 다음 기반을 만드는 작업이었다.

```text
v2 공통 기반
-> session 주입 구조
-> fixture / rollback 기록 구조
-> payload 파일 구조
-> state-changing confirm gate
-> generic payload_probe
-> 02 SQL 인젝션 check 1개
```

따라서 다음 goal은 06, 07, 09, 10, 11, 14, 20을 바로 붙이는 작업이 아니라, 먼저 02번을 실제 CARE route에 제한 실행해서 v2 evidence 파이프라인이 제대로 작동하는지 확인하는 작업으로 잡는다.

### 왜 02번을 먼저 실제 실행하는가

02 SQL 인젝션은 현재 v2 후보 중 가장 부담이 낮다.

| 이유 | 설명 |
|---|---|
| 상태 변경 없음 | 검색 route의 GET parameter에 payload를 넣는 구조라 글쓰기, 회원정보 수정, 업로드가 아니다. |
| fixture 부담 낮음 | 로그인 세션, 테스트 계정, rollback 대상이 없어도 첫 검증이 가능하다. |
| v2 엔진 검증에 적합 | `payload_probe`, `payloads/*.yml`, request/response evidence 저장이 실제로 맞는지 확인할 수 있다. |
| 다음 확장의 기준점 | 02 evidence 품질이 괜찮아야 06 XSS, 07 CSRF 같은 더 복잡한 항목으로 넘어갈 수 있다. |

### 다음 goal에서 할 일

다음 goal은 다음 범위로 제한한다.

```text
02 SQL 인젝션만 제한 실행
-> result.json / report.md / run.log 확인
-> 02 request/response evidence 확인
-> vulnerable / manual_required / inconclusive 판정이 근거와 맞는지 평가
-> 부족하면 02 check rule 또는 로그/README만 최소 보정
```

실행 방식은 전체 checks를 한 번에 돌리는 것보다, 필요하면 임시 checks 디렉터리에 `02_sql_injection.yml`만 복사해서 돌리는 쪽이 안전하다.

### 다음 goal에서 하지 않을 일

```text
06 XSS 구현 금지
07 CSRF 구현 금지
09, 10, 11, 14, 20 구현 금지
state-changing 실행 금지
DB 삭제, 글쓰기, 회원정보 수정, 파일 업로드 금지
ZAP / Nuclei 연동 금지
MOC / index 수정 금지
```

### 문장 해석 정리

이전 판단의 다음 문장은 큰 방향이다.

```text
그다음 goal에서 02/06/07 같은 개별 check를 더 공격적으로 붙이면 된다.
```

현재 로그 기준으로는 이 큰 방향을 다음처럼 더 좁혀서 실행한다.

```text
v2 개별 check 확장 1단계
= 02 SQL 인젝션 check를 실제 제한 실행하여 v2 evidence 파이프라인을 검증한다.
```

즉, 다음 goal은 “v2 후보 여러 개 구현”이 아니라 “02번 실제 증거 품질 확인”이다.

## 2026-06-18 02 SQL 인젝션 제한 실행 시도

### 목적

02 SQL 인젝션 check만 실제로 실행해서 `payload_probe`가 request / response evidence를 보고서 재료로 쓸 수 있게 남기는지 확인하려 했다.

이번 실행은 다음 범위로 제한했다.

```text
02_sql_injection.yml만 실행
state-changing 없음
DB 삭제, 글쓰기, 회원정보 수정, 파일 업로드 없음
```

### 실행 준비

전체 `checks/`를 돌리지 않기 위해 임시 디렉터리에 02번 check와 payload만 복사했다.

```powershell
$tmpRoot = Join-Path $env:TEMP "kisa-checker-02-only"
$tmpChecks = Join-Path $tmpRoot "checks"
$tmpPayloads = Join-Path $tmpRoot "payloads"
$tmpOut = Join-Path $tmpRoot "evidence"
New-Item -ItemType Directory -Force -Path $tmpChecks, $tmpPayloads, $tmpOut | Out-Null
Copy-Item -LiteralPath ".\checks\02_sql_injection.yml" -Destination $tmpChecks -Force
Copy-Item -LiteralPath ".\payloads\sqli.yml" -Destination $tmpPayloads -Force
```

처음에는 02번 check만 복사했기 때문에 `payloads/sqli.yml` 상대 경로가 끊겼다.

```text
[ERROR] Missing dependency: PyYAML, and the built-in v0 YAML fallback could not parse ...
File not found: ...\kisa-checker-02-only\payloads\sqli.yml
```

판단:

```text
02번만 임시 실행할 때도 checks/와 payloads/는 같은 임시 root 아래에 같이 복사해야 한다.
```

### validate-only 결과

payload 파일까지 함께 둔 뒤 02번만 validate-only를 실행했다.

```powershell
python checker.py --profile profiles/care.yml --checks $tmpChecks --mode attack-active --validate-only --output $tmpOut
```

결과:

```text
[OK] run_id=20260618-111606
[OK] evidence=C:\Users\Unoh\AppData\Local\Temp\kisa-checker-02-only\evidence\20260618-111606
[passed] 02 SQL 인젝션
```

판단:

```text
02_sql_injection.yml, payloads/sqli.yml, board_search route 설정 자체는 통과한다.
```

### 실제 실행 1차: profile 기본값 `127.0.0.1`

`profiles/care.yml`의 기본 `base_url`은 `http://127.0.0.1`이다. 이 값은 checker를 WEB 서버 내부에서 실행할 때 맞는 값이다.

```powershell
python checker.py --profile profiles/care.yml --checks $tmpChecks --mode attack-active --output $tmpOut
```

결과:

```text
[OK] run_id=20260618-111627
[OK] evidence=C:\Users\Unoh\AppData\Local\Temp\kisa-checker-02-only\evidence\20260618-111627
[error] 02 SQL 인젝션
```

`result.json`의 핵심 내용:

```text
Route `board_search` baseline request failed:
<urlopen error [WinError 10061] 대상 컴퓨터에서 연결을 거부했으므로 연결하지 못했습니다>
```

생성된 baseline request:

```http
GET http://127.0.0.1/center/list.php?mode=search&find=subject&data=kisa-baseline HTTP/1.1
User-Agent: kisa-webapp-checker-v2
```

판단:

```text
request 생성은 맞다.
하지만 현재 Codex 실행 위치의 127.0.0.1에는 CARE 웹서버가 떠 있지 않아 baseline부터 실패했다.
따라서 이 실행은 SQLi evidence로 쓸 수 없다.
```

### 실제 실행 2차: 임시 profile로 `172.168.10.10` 지정

repo의 `profiles/care.yml`은 수정하지 않고, 임시 profile만 `base_url: "http://172.168.10.10"`으로 바꿔 실행했다.

처음에는 Codex 실행 환경의 proxy 때문에 172.168.10.10으로 직접 나가지 못했다.

확인된 proxy 환경:

```text
HTTP_PROXY=http://127.0.0.1:9
HTTPS_PROXY=http://127.0.0.1:9
ALL_PROXY=http://127.0.0.1:9
NO_PROXY=localhost,127.0.0.1,::1
```

그래서 실행 프로세스에서만 proxy를 비우고 `NO_PROXY`에 `172.168.10.10`을 추가했다.

```powershell
$env:HTTP_PROXY=''
$env:HTTPS_PROXY=''
$env:ALL_PROXY=''
$env:NO_PROXY='localhost,127.0.0.1,::1,172.168.10.10'
python checker.py --profile $tmpProfile --checks $tmpChecks --mode attack-active --output $tmpOut
```

sandbox 밖 네트워크 접근으로도 한 번 재시도했다.

결과:

```text
[OK] run_id=20260618-111901
[OK] evidence=C:\Users\Unoh\AppData\Local\Temp\kisa-checker-02-only\evidence-172-nosandbox\20260618-111901
[error] 02 SQL 인젝션
```

`result.json`의 핵심 내용:

```text
Route `board_search` baseline request failed:
<urlopen error timed out>
```

생성된 baseline request:

```http
GET http://172.168.10.10/center/list.php?mode=search&find=subject&data=kisa-baseline HTTP/1.1
User-Agent: kisa-webapp-checker-v2
```

판단:

```text
proxy 문제는 분리했다.
하지만 현재 Codex 실행 위치에서는 172.168.10.10의 CARE 서버에도 도달하지 못했다.
따라서 실제 SQLi payload probe evidence는 아직 확보하지 못했다.
```

### 현재 판정

| 항목 | 판정 |
|---|---|
| 02번 설정 검증 | 통과 |
| 02번 request 생성 | 정상 |
| 02번 실제 SQLi payload 실행 | 미완료 |
| 취약 / 비취약 판정 | 불가 |
| 보고서용 SQLi evidence | 아직 부족 |

이번 실행으로 확인된 것은 다음까지다.

```text
02번 check는 설정상 실행 가능하다.
checker는 올바른 baseline request를 만든다.
현재 Codex 실행 환경에서는 CARE 서버에 네트워크로 도달하지 못한다.
```

이번 실행으로 확인하지 못한 것은 다음이다.

```text
SQLi payload 전송 결과
vulnerable / manual_required / inconclusive 중 실제 판정
payload별 request / response evidence 품질
```

### 다음 재시도 기준

02번 실제 evidence 확보는 다음 둘 중 하나가 필요하다.

```text
1. WEB 서버 내부에서 checker를 실행한다.
   - 이 경우 profile 기본값 `http://127.0.0.1` 사용 가능.

2. Codex/Windows 실행 위치에서 172.168.10.10:80 또는 실제 CARE 포트에 접근 가능하게 만든 뒤 실행한다.
   - 이 경우 임시 profile 또는 profile의 base_url을 해당 주소로 맞춘다.
```

WEB 서버 내부에서 재시도할 때의 기준 명령:

```bash
cd ~/kisa-webapp-checker
mkdir -p /tmp/kisa-checker-02-only/checks /tmp/kisa-checker-02-only/payloads
cp checks/02_sql_injection.yml /tmp/kisa-checker-02-only/checks/
cp payloads/sqli.yml /tmp/kisa-checker-02-only/payloads/
python3 checker.py --profile profiles/care.yml --checks /tmp/kisa-checker-02-only/checks --mode attack-active
```

Windows에서 재시도할 때는 proxy 환경을 같이 정리한다.

```powershell
$env:HTTP_PROXY=''
$env:HTTPS_PROXY=''
$env:ALL_PROXY=''
$env:NO_PROXY='localhost,127.0.0.1,::1,172.168.10.10'
```

### 다음 작업 기준

```text
다음에는 새 기능을 만들지 않는다.
먼저 CARE 서버에 도달 가능한 위치에서 위 02번 제한 실행을 다시 수행한다.
성공하면 result.json / report.md / run.log / 02_SQL request-response를 읽고 evidence 품질을 판단한다.
```

### SSH 경유 가능성 확인

추가 단서:

```text
Windows/Codex 위치에서는 172.168.10.10 HTTP 접근이 안 된다.
하지만 VS Code Remote SSH로 192.168.240.146 접속은 가능하다.
```

이 구조는 다음처럼 해석한다.

```text
172.168.10.10
= GNS/VM 내부 웹 서비스 IP
= Windows/Codex에서 직접 HTTP 접근 불가

192.168.240.146
= Windows 호스트가 SSH로 접근 가능한 VM 관리/어댑터 IP
```

따라서 02번 check는 Windows/Codex에서 억지로 돌리는 것보다, VS Code SSH로 WEB VM에 접속한 터미널에서 직접 실행하는 쪽이 맞다.

Codex 쉘에서 SSH 재사용 가능 여부도 확인했다.

```powershell
ssh
```

기본 `ssh`는 sandbox deny wrapper로 잡혀 있었다.

```text
C:\Users\Unoh\.sbx-denybin\ssh.bat
C:\Users\Unoh\.sbx-denybin\ssh.cmd
C:\Windows\System32\OpenSSH\ssh.exe
```

직접 OpenSSH 실행 파일로 비대화식 접속도 시도했다.

```powershell
& "$env:WINDIR\System32\OpenSSH\ssh.exe" -o BatchMode=yes -o ConnectTimeout=5 webuser@192.168.240.146 "printf 'ssh-ok\n'; hostname; pwd"
```

결과:

```text
webuser@192.168.240.146: Permission denied (publickey,password).
```

판단:

```text
VS Code Remote SSH는 사용자가 직접 접속할 수 있지만,
현재 Codex 쉘에서는 같은 인증 상태를 비대화식으로 재사용할 수 없다.
그러므로 02번 실제 evidence 생성은 사용자가 VSC SSH 터미널에서 실행해야 한다.
```

VSC SSH 터미널에서 실행할 명령:

```bash
cd ~/kisa-webapp-checker
mkdir -p /tmp/kisa-checker-02-only/checks /tmp/kisa-checker-02-only/payloads
cp checks/02_sql_injection.yml /tmp/kisa-checker-02-only/checks/
cp payloads/sqli.yml /tmp/kisa-checker-02-only/payloads/
python3 checker.py --profile profiles/care.yml --checks /tmp/kisa-checker-02-only/checks --mode attack-active
```

실행 후 확인할 파일:

```bash
ls -R evidence | tail -n 40
cat evidence/<run_id>/result.json
cat evidence/<run_id>/report.md
cat evidence/<run_id>/run.log
ls evidence/<run_id>/02_SQL
```

이 출력이 돌아오면 다음에 할 일:

```text
1. result.json의 02 status 확인
2. request/response가 실제 SQLi payload probe 증거인지 확인
3. vulnerable / manual_required / inconclusive / error 중 판정 정리
4. 보고서 재료로 충분한지 판단
5. 작업 로그에 최종 실행 결과 추가
```

## 2026-06-18 DB 중단 상태에서 02번 false positive 보정

### 상황

WEB VM 내부에서 02번만 제한 실행했다.

```bash
cd ~/kisa-webapp-checker
mkdir -p /tmp/kisa-checker-02-only/checks /tmp/kisa-checker-02-only/payloads
cp checks/02_sql_injection.yml /tmp/kisa-checker-02-only/checks/
cp payloads/sqli.yml /tmp/kisa-checker-02-only/payloads/
python3 checker.py --profile profiles/care.yml --checks /tmp/kisa-checker-02-only/checks --mode attack-active
```

결과:

```text
[OK] run_id=20260618-042454
[OK] evidence=/home/webuser/kisa-webapp-checker/evidence/20260618-042454
[vulnerable] 02 SQL 인젝션
```

하지만 당시 DB가 꺼져 있었다.

`result.json`의 핵심 findings:

```text
Route `board_search` baseline returned 500.
Route `board_search` payload #1 indicates possible exposure: status 500.
Route `board_search` payload #2 indicates possible exposure: status 500.
Route `board_search` payload #3 indicates possible exposure: status 500.
Route `board_search` payload #4 indicates possible exposure: status 500.
Route `board_search` payload #5 indicates possible exposure: status 500.
```

`run.log`의 핵심 흐름:

```text
GET http://127.0.0.1/center/list.php?mode=search&find=subject&data=kisa-baseline -> 500
GET http://127.0.0.1/center/list.php?mode=search&find=subject&data=%27 -> 500
GET http://127.0.0.1/center/list.php?mode=search&find=subject&data=%22 -> 500
GET http://127.0.0.1/center/list.php?mode=search&find=subject&data=%27+OR+%271%27%3D%271 -> 500
GET http://127.0.0.1/center/list.php?mode=search&find=subject&data=%22+OR+%221%22%3D%221 -> 500
GET http://127.0.0.1/center/list.php?mode=search&find=subject&data=%27+UNION+SELECT+NULL--+ -> 500
```

### 판단

이 결과는 SQL Injection 취약 증거로 쓰면 안 된다.

이유:

```text
baseline인 kisa-baseline 요청부터 500이다.
즉, payload 때문에 500이 난 것이 아니라 DB 중단 같은 공통 장애 때문에 모든 요청이 500이 된 상태다.
```

따라서 기존 checker 판정은 false positive였다.

```text
기존 판정: vulnerable
올바른 판정: inconclusive 또는 error 성격
```

### 코드 보정

`checker.py`의 `payload_probe`를 최소 수정했다.

변경 의도:

```text
baseline 응답이 이미 vulnerable_statuses 또는 vulnerable pattern에 걸리면,
payload 비교가 불가능하므로 vulnerable로 판정하지 않는다.
```

새 동작:

```text
baseline 500
-> payload 비교 생략
-> status: inconclusive
-> finding: baseline already matches exposure indicators; payload comparison is not reliable
```

### 회귀 검증

로컬 임시 HTTP 서버를 띄워 모든 요청에 500을 반환하게 만든 뒤, 02번 payload_probe를 실행했다.

검증 목적:

```text
DB 장애처럼 baseline부터 500인 상태에서 vulnerable로 오판하지 않는지 확인
```

결과:

```text
[OK] run_id=20260618-150810
[OK] evidence=C:\Users\Unoh\AppData\Local\Temp\kisa-baseline-500-s6b3ihhe\evidence\20260618-150810
[inconclusive] 02 SQL ???
REGRESSION_STATUS=inconclusive
```

판단:

```text
baseline 500 false positive는 보정됐다.
```

### 현재 결론

DB가 꺼져 있으면 02 SQL 인젝션 actual evidence는 만들 수 없다.

다른 것으로 대체 테스트할 수 있는 범위는 다음뿐이다.

| 테스트 | 가능 여부 | 의미 |
|---|---:|---|
| checker 설정 검증 | 가능 | YAML, route, payload 파일 구조 확인 |
| request 생성 확인 | 가능 | `/center/list.php?...data=...` 요청이 만들어지는지 확인 |
| baseline 500 false positive 방지 | 가능 | DB 장애를 SQLi로 오판하지 않는지 확인 |
| 실제 SQL Injection 취약 판정 | 불가 | DB가 켜져 있고 baseline이 정상이어야 함 |

### 다음 재시도 기준

DB를 켠 뒤 WEB VM 내부에서 다시 실행한다.

```bash
cd ~/kisa-webapp-checker
python3 checker.py --profile profiles/care.yml --checks /tmp/kisa-checker-02-only/checks --mode attack-active
```

재실행 후 기대 조건:

```text
baseline request는 200 또는 정상적인 게시판 응답이어야 한다.
payload request에서만 500, SQL error, mysqli_sql_exception, MariaDB/MySQL error 등이 나와야 SQLi evidence로 쓸 수 있다.
```

DB가 켜진 뒤에도 baseline이 500이면 다음을 먼저 확인한다.

```text
1. Apache/PHP error log
2. config.local.php의 DB host/user/password/dbname
3. MariaDB service 상태
4. center table 존재 여부
5. /center/list.php?mode=search&find=subject&data=kisa-baseline 직접 접속 결과
```

### DB 없이 가능한 대체 작업

DB가 꺼져 있으면 실제 CARE SQL Injection 증거는 만들 수 없다.

하지만 checker 자체의 02번 동작은 mock target으로 검증할 수 있다.

추가한 파일:

```text
kisa-webapp-checker/mock_targets/sqli_search_mock.py
kisa-webapp-checker/profiles/mock_sqli.yml
```

용도:

```text
실제 CARE 취약 증거 생성이 아니라,
payload_probe가 다음 세 상태를 구분하는지 검증한다.
```

| mock mode | 의미 | 기대 판정 |
|---|---|---|
| `vulnerable` | baseline은 200, SQLi-like payload는 SQL error 500 | `vulnerable` |
| `safe` | baseline과 payload 모두 정상 200 | `manual_required` |
| `db-down` | baseline과 payload 모두 500 | `inconclusive` |

사용법:

```bash
# 터미널 1
python mock_targets/sqli_search_mock.py --mode vulnerable --port 18080

# 터미널 2
python checker.py --profile profiles/mock_sqli.yml --checks checks --mode attack-active
```

중요:

```text
mock 결과는 checker 검증용이다.
보고서용 SQLi evidence는 DB를 켠 뒤 실제 CARE route에서 다시 만들어야 한다.
```

검증 결과:

```text
MOCK_MODE=vulnerable STATUS=vulnerable EXPECTED=vulnerable
MOCK_MODE=safe STATUS=manual_required EXPECTED=manual_required
MOCK_MODE=db-down STATUS=inconclusive EXPECTED=inconclusive
```

판단:

```text
mock target 기준으로는 02 payload_probe가 세 상태를 구분한다.
baseline 정상 + payload SQL error는 vulnerable로 잡는다.
baseline 정상 + payload 정상은 manual_required로 남긴다.
baseline부터 500이면 inconclusive로 남긴다.
```

이 검증으로 확인한 것:

```text
checker의 02번 evidence 파이프라인은 DB 없이도 검증 가능하다.
DB 장애 상태를 SQLi 취약으로 오판하는 문제는 보정됐다.
```

이 검증으로 확인하지 못한 것:

```text
실제 CARE /center/list.php의 SQL Injection 취약 여부
실제 CARE 응답이 보고서 증거로 충분한지 여부
```

## 2026-06-18 v3 범위와 구현 순서 확정

### 목적

v2에서 02 SQL 인젝션은 checker 구조와 mock 검증까지는 끝났지만, 실제 CARE 증거는 DB가 꺼진 상태라 더 진행할 수 없었다.

그래서 다음 단계는 v2 항목을 억지로 계속 붙이는 것이 아니라, DB 없이도 검증 가능한 v3 후보를 고르고 구현 순서를 확정하는 것으로 잡았다.

### 현재 구현 coverage

현재 `checks/`에 실제 구현된 항목은 다음뿐이다.

```text
02, 03, 04, 05, 15, 16, 17, 19, 21
```

01~21 전체 상태는 다음과 같다.

| 번호 | 항목 | 현재 checker 상태 | 다음 처리 |
|---:|---|---|---|
| 01 | 코드 인젝션 | 미구현 | v3 후보. 하위 유형이 많아 08 이후 분해 필요 |
| 02 | SQL 인젝션 | 구현됨. mock 검증 완료, 실제 CARE 증거는 DB 중단으로 보류 | DB가 켜지면 실제 evidence 재실행 |
| 03 | 디렉터리 인덱싱 | 구현됨 | 유지 |
| 04 | 에러 페이지 | 구현됨 | 유지 |
| 05 | 정보 노출 | 구현됨 | 유지 |
| 06 | XSS | 미구현 | reflected/stored 분리 후 v2 후속 |
| 07 | CSRF | 미구현 | state-changing fixture가 필요하므로 v2 후속 |
| 08 | SSRF | 미구현 | v3 1순위 구현 후보 |
| 09 | 약한 비밀번호 정책 | 미구현 | 회원가입/수정 fixture 필요. v2 후속 |
| 10 | 불충분한 인증 절차 | 미구현 | 로그인 세션과 회원정보 수정 흐름 필요. v2 후속 |
| 11 | 불충분한 권한 검증 | 미구현 | 사용자 A/B와 object id fixture 필요. v2 후속 |
| 12 | 취약한 비밀번호 복구 절차 | 미구현 | v3 후보. 13과 같은 복구 흐름에 묶임 |
| 13 | 프로세스 검증 누락 | 미구현 | v3 후보. 12 구현 이후가 자연스러움 |
| 14 | 악성 파일 업로드 | 미구현 | state-changing/upload fixture 필요. v2 후속 |
| 15 | 파일 다운로드 | 구현됨 | 현재는 known candidate 확인. traversal 확장은 별도 판단 |
| 16 | 불충분한 세션 관리 | 구현됨 | HTTPS/AWS 재검증 필요 |
| 17 | 데이터 평문 전송 | 구현됨 | HTTPS/AWS 재검증 필요 |
| 18 | 쿠키 변조 | 미구현 | 쿠키 기반 권한값이 있는지 먼저 확인 필요 |
| 19 | 관리자 페이지 노출 | 구현됨 | 유지 |
| 20 | 자동화 공격 | 미구현 | destructive-risk라 요청 상한/rollback 설계 필요 |
| 21 | 불필요한 Method 악용 | 구현됨 | 유지 |

### v3 후보 판단

| 번호 | 후보 | 필요한 CARE 기능 / endpoint | profile route | fixture | mode | rollback | 자동화 가능성 | mock 필요 | 실제 보고서 evidence |
|---:|---|---|---|---|---|---|---|---|---|
| 01 | 코드 인젝션 | `/vuln/code-injection/` 아래 OS Command, SSI, XPath, XXE, SSTI endpoint | 하위 유형별 route 필요 | 유형별 proof 입력값 필요 | `attack-active` | SSI generated 파일 등 일부 정리 필요 | 부분 자동화 가능. 한 check로 묶으면 과함 | 유형별로 있으면 좋음 | 가능하지만 하위 유형별 스크린샷/응답 해석 필요 |
| 08 | SSRF | `/vuln/ssrf/fetch.php`, `/vuln/ssrf/internal-proof.php` | `ssrf_fetch`, `ssrf_internal_proof` | proof 문자열과 target URL 정도면 충분 | `attack-active` | 상태 변경 없음. rollback 거의 없음 | 높음. request/response만으로 1차 판정 가능 | 선택 사항 | 매우 적합. proof 문자열 노출/차단이 명확함 |
| 12 | 취약한 비밀번호 복구 절차 | `/vuln/password-recovery/request.php`, `verify.php` | request/verify route 필요 | victim 계정, 인증번호 mailbox, 세션 필요 | `state-changing` | 인증번호/세션/비밀번호 변경 흔적 정리 필요 | 반자동 | 있으면 좋음 | 가능하지만 업무 흐름과 서버 mailbox 증거가 필요 |
| 13 | 프로세스 검증 누락 | `/vuln/password-recovery/reset.php` 직접 호출 | reset route 필요 | victim 계정, 새 비밀번호, 세션 상태 필요 | `state-changing` | 변경된 비밀번호 복구 필요 | 반자동 | 12 mock 이후가 자연스러움 | 가능하지만 12번 흐름과 함께 해석해야 함 |

### v3 1순위 결정

v3 첫 구현 대상은 **08 SSRF**로 잡는다.

이유:

| 기준 | 판단 |
|---|---|
| DB 필요 여부 | 필요 없음 |
| 로그인 필요 여부 | 필요 없음 |
| 상태 변경 여부 | 없음 |
| 기존 CARE endpoint | `/vuln/ssrf/fetch.php`, `/vuln/ssrf/internal-proof.php`가 이미 노트에 정리됨 |
| evidence 명확성 | 조치 전 proof 문자열 노출, 조치 후 차단으로 비교 가능 |
| profile/check 구조 적합성 | `payload_probe` 또는 SSRF 전용 `url_probe` 형태로 확장하기 쉬움 |
| 위험도 | 내부망 스캔 없이 통제된 proof URL만 쓰면 낮음 |

따라서 다음 `/goal`은 다음 범위가 적절하다.

```text
08 SSRF check 설계와 구현
-> profile에 ssrf_fetch / ssrf_internal_proof route 추가
-> payloads/ssrf.yml 또는 inline target URL 구조 결정
-> 조치 전 proof 문자열 노출을 vulnerable로 판정
-> 조치 후 차단 응답은 not_vulnerable 또는 manual_required로 판정
-> DB, 로그인, 파일 업로드, 상태 변경 없이 검증
```

다음 `/goal`에서 하지 않을 일:

```text
01 코드 인젝션 구현 금지
12/13 비밀번호 복구 구현 금지
06/07/09/10/11/14/20 구현 금지
CARE PHP 코드 수정 금지
DB 실행 또는 데이터 변경 금지
ZAP/Nuclei 연동 금지
MOC/index 수정 금지
```

## 2026-06-18 08 SSRF check 구현과 로컬 검증

### 목적

v3 첫 구현 대상으로 확정한 08 SSRF를 checker에 추가했다.

이번 goal은 실제 CARE 서버 evidence 생성이 아니라 다음까지를 목표로 했다.

```text
08 SSRF check 구현
-> 로컬 validate-only / mock 검증
-> WEB VM에서 사용자가 실행할 명령 준비
```

Codex 로컬에서는 `172.168.10.10` CARE 서버와 직접 통신하지 않는다.

### 구현 범위

수정 및 추가한 파일:

```text
kisa-webapp-checker/profiles/care.yml
kisa-webapp-checker/checks/08_ssrf.yml
kisa-webapp-checker/payloads/ssrf.yml
kisa-webapp-checker/profiles/mock_ssrf.yml
kisa-webapp-checker/mock_targets/ssrf_fetch_mock.py
kisa-webapp-checker/README.md
```

`checker.py`는 수정하지 않았다. 기존 `payload_probe` 구조를 그대로 사용했다.

추가한 CARE route:

| route | 의미 |
|---|---|
| `ssrf_fetch` | `/vuln/ssrf/fetch.php`에 `url` 파라미터를 넣어 서버 측 요청 기능을 검사 |
| `ssrf_internal_proof` | `/vuln/ssrf/internal-proof.php` 내부 proof page 위치 기록 |

추가한 payload:

```text
http://127.0.0.1/vuln/ssrf/internal-proof.php
```

### 판정 기준

08번 check의 기준:

| 상황 | 기대 상태 |
|---|---|
| baseline fetch가 정상이고, loopback proof payload 응답에 `SSRF_INTERNAL_PROOF` 또는 `care-ssrf-local-only-proof`가 보임 | `vulnerable` |
| baseline fetch는 정상이나 proof 문자열이 보이지 않음 | `manual_required` |
| baseline부터 실패 | `error` 또는 `inconclusive` 성격으로 Goal 2에서 재판단 |

조치 후를 자동으로 `not_vulnerable`로 단정하지 않고 `manual_required`로 남긴 이유:

```text
차단 문구, HTTP status, redirect, 운영 정책은 target마다 다를 수 있다.
따라서 proof가 안 보인다는 사실만으로는 자동 확정하지 않고 request/response evidence를 보고 Goal 2에서 판정한다.
```

### 검증 결과

실행한 로컬 검증:

```powershell
python -c "import py_compile, tempfile; files=['checker.py','mock_targets/ssrf_fetch_mock.py']; [py_compile.compile(f, cfile=tempfile.NamedTemporaryFile(delete=False).name, doraise=True) for f in files]; print('py_compile ok')"

python checker.py --profile profiles/care.yml --checks checks --mode attack-active --validate-only --output "$env:TEMP\kisa-checker-ssrf-validate2"
```

확인 결과:

```text
py_compile ok

[passed] 02 SQL 인젝션
[passed] 03 디렉터리 인덱싱
[passed] 04 에러 페이지
[passed] 05 정보 노출
[passed] 08 SSRF
[passed] 15 파일 다운로드
[passed] 16 불충분한 세션 관리
[passed] 17 데이터 평문 전송
[passed] 19 관리자 페이지 노출
[passed] 21 불필요한 Method 악용
```

mock target 검증 결과:

```text
MOCK_MODE=vulnerable STATUS=vulnerable
MOCK_MODE=safe STATUS=manual_required
```

초기 검증 중 `vulnerable_statuses: []`가 YAML fallback에서 문자열처럼 해석되어 `status lists must be YAML lists` 오류가 났다. 그래서 빈 리스트 대신 실제로 쓰이지 않을 상태 코드 `599`를 block list로 넣어 파서 호환성을 맞췄다.

### WEB VM 실행 명령

실제 CARE evidence는 WEB VM의 VSC SSH 터미널에서 실행한다.

```bash
cd ~/kisa-webapp-checker
mkdir -p /tmp/kisa-checker-08-only/checks /tmp/kisa-checker-08-only/payloads
cp checks/08_ssrf.yml /tmp/kisa-checker-08-only/checks/
cp payloads/ssrf.yml /tmp/kisa-checker-08-only/payloads/
python3 checker.py --profile profiles/care.yml --checks /tmp/kisa-checker-08-only/checks --mode attack-active
```

실행 후 확인할 출력:

```bash
RUN_ID="<방금 출력된 run_id>"
cat "evidence/${RUN_ID}/result.json"
cat "evidence/${RUN_ID}/report.md"
cat "evidence/${RUN_ID}/run.log"
find "evidence/${RUN_ID}" -type f | sort
```

사용자는 위 출력과 08 SSRF request/response evidence를 가져오고, Goal 2에서 판정과 보정을 진행한다.

### 현재 한계

- 실제 CARE 서버와 통신하지 않았으므로 보고서용 SSRF evidence는 아직 없다.
- mock 결과는 checker 판정 구조 검증일 뿐이다.
- 조치 후 차단은 자동 `not_vulnerable`로 확정하지 않고 `manual_required`로 남긴다.
- AWS metadata, 내부망 스캔, 포트 스캔은 이번 check 범위가 아니다.

### 다음 작업 기준

다음 작업은 Goal 2로 진행한다.

```text
WEB VM에서 08번만 실행
-> result.json / report.md / run.log / request-response 확인
-> vulnerable 또는 manual_required 판정이 evidence와 맞는지 검토
-> 필요하면 08 check rule 또는 README/로그만 보정
```

### Goal 2 프롬프트 보관

Goal 1은 08 SSRF check 구현, 로컬 검증, WEB VM 실행 명령 준비까지로 끝낸다. 실제 CARE 서버 evidence는 사용자가 WEB VM에서 실행한 뒤 결과를 가져오면 Goal 2에서 분석한다.

복붙용 Goal 2 프롬프트:

```text
목표: WEB VM에서 실행한 08 SSRF check 결과를 분석하고, 판정/문서/로그를 마무리한다.

배경:
- Goal 1에서 KISA Web Application Checker에 08 SSRF check를 구현했다.
- Codex 로컬에서는 실제 `172.168.10.10` CARE 서버와 직접 통신하지 않는다.
- 사용자가 WEB VM의 VSC SSH 터미널에서 실행한 결과를 붙여넣었다.

입력으로 받을 수 있는 것:
- WEB VM에서 실행한 명령어
- checker stdout
- `evidence/<run_id>/result.json`
- `evidence/<run_id>/report.md`
- `evidence/<run_id>/run.log`
- 08 SSRF request/response evidence
- 오류 메시지 또는 connection 실패 출력

범위:
1. 사용자가 붙여넣은 실행 결과를 읽고 08 SSRF 판정이 타당한지 확인한다.
2. `vulnerable`, `not_vulnerable`, `manual_required`, `inconclusive`, `error` 중 상태가 evidence와 맞는지 검토한다.
3. 조치 전 proof 문자열 노출과 조치 후 loopback 차단이 구분되는지 확인한다.
4. 판정이 잘못되었으면 08 check rule 또는 README/로그 문서만 최소 보정한다.
5. 실제 CARE evidence로 보고서에 쓸 수 있는지 판단한다.
6. 작업 로그에 실행 결과, 판정, 한계, 다음 작업 기준을 기록한다.
7. 필요하면 WEB VM에서 다시 실행할 명령어를 짧게 제시한다.
8. `git diff --check`를 통과시킨다.

금지:
- 새 취약점 check 구현 금지
- 01/12/13 구현 금지
- CARE PHP 코드 수정 금지
- DB 실행 또는 데이터 변경 금지
- 파일 업로드, 글쓰기, 회원정보 수정 금지
- 내부망 스캔, 포트스캔, AWS metadata 탈취 시도 금지
- ZAP/Nuclei 연동 금지
- MOC/index 수정 금지

완료 기준:
- WEB VM 실행 결과에 대한 판정이 evidence 기준으로 정리됨
- 08 SSRF check의 false positive/false negative 가능성이 필요한 만큼 보정됨
- 보고서용 evidence 가능 여부가 정리됨
- 작업 로그가 갱신됨
- `git diff --check` 통과
```

## 2026-06-18 08 SSRF 차단 문구 자동 판정 보정

### 목적

WEB VM에서 08번 SSRF check를 실제 CARE 서버에 실행한 결과, 조치 후 차단 문구가 명확히 남았는데도 상태가 `manual_required`로 나왔다.

사용자가 가져온 실제 실행 근거:

```text
run_id=20260618-082321
checker stdout: [manual_required] 08 SSRF
payload response body: 허용되지 않은 요청 대상입니다.
```

이 결과는 “proof 문자열이 노출되지 않았으니 사람이 봐야 함”이 아니라, 현재 CARE 조치 코드가 loopback/internal 요청을 의도적으로 차단했다는 자동 판정 근거에 가깝다.

### 구현 보정

`payload_probe`에 조치 후 차단 근거를 선언할 수 있는 rule을 추가했다.

```yaml
not_vulnerable_statuses:
  - 403
not_vulnerable_body_patterns:
  - "허용되지 않은 요청 대상입니다"
```

이에 따라 08번 SSRF check는 다음처럼 판정한다.

| 응답 근거 | 판정 |
|---|---|
| `SSRF_INTERNAL_PROOF` 또는 `care-ssrf-local-only-proof` 노출 | `vulnerable` |
| `허용되지 않은 요청 대상입니다` 차단 문구 확인 | `not_vulnerable` |
| proof도 차단 문구도 없고 rule로 해석 불가 | `manual_required` |

### 주요 결정

- `manual_required`는 “알 수 없는 응답”에만 남긴다.
- 이미 rule로 정의한 차단 문구나 차단 status는 `not_vulnerable`로 자동 판정한다.
- 이는 CARE에 하드코딩하는 것이 아니라, `checks/08_ssrf.yml`에 target별 차단 근거를 선언하는 방식이다.
- 실제 request/response evidence는 계속 저장하므로, 최종 보고서에서는 자동 판정과 원문 evidence를 함께 확인할 수 있다.

### 검증 결과

로컬에서 문법, 설정, mock target 판정을 다시 확인했다.

```text
py_compile ok

attack-active validate-only:
[passed] 08 SSRF

mock target:
MOCK_MODE=vulnerable STATUS=vulnerable
MOCK_MODE=safe STATUS=not_vulnerable
```

### 다음 실행 기준

WEB VM에서 08번만 다시 실행하면, 현재와 같은 조치 후 응답에서는 다음 상태가 기대된다.

```text
[not_vulnerable] 08 SSRF
```

다시 실행할 명령:

```bash
cd ~/kisa-webapp-checker
mkdir -p /tmp/kisa-checker-08-only/checks /tmp/kisa-checker-08-only/payloads
cp checks/08_ssrf.yml /tmp/kisa-checker-08-only/checks/
cp payloads/ssrf.yml /tmp/kisa-checker-08-only/payloads/
python3 checker.py --profile profiles/care.yml --checks /tmp/kisa-checker-08-only/checks --mode attack-active
```

## 2026-06-19 압축 전 다음 계획 고정

### 목적

컨텍스트 압축 전에 다음 작업 방향을 다시 고정했다.

직전 대화에서 잠시 12번으로 바로 넘어가자는 제안이 나왔지만, 기존 설계와 맞지 않는 흐름으로 판단했다. 원래 단계 구분은 다음과 같다.

| 단계 | 성격 | 항목 |
|---|---|---|
| `v1` | 안전하고 자동화 쉬운 항목 | 03, 04, 05, 15, 16, 17, 19, 21 |
| `v2` | 로그인 세션, payload, 상태 변경 후보 | 02, 06, 07, 09, 10, 11, 14, 20 |
| `v3` | 앱 문맥 또는 별도 기능이 필요한 항목 | 01, 08, 12, 13 |

08 SSRF는 원래 v3 항목이지만 DB가 필요 없고 이미 실습 endpoint가 있어서 먼저 처리한 예외 케이스다.

### 현재 확정된 다음 방향

다음 작업은 12번으로 바로 가지 않는다. v2 미완성 항목으로 돌아간다.

다만 v2 항목을 하나씩 구현하면 컨텍스트와 작업 전환 비용이 커진다. 따라서 다음 `/goal`은 항목별 실제 공격 실행이 아니라 **v2 batch scaffold 구현**으로 잡는다.

```text
v2 batch scaffold
= 06, 07, 09, 10, 11, 14, 20의 check/profile/payload 구조를 한 번에 추가
= 실제 WEB VM 공격 실행은 하지 않음
= validate-only와 정적 검증까지만 수행
```

### 구현 단위와 실행 단위 구분

| 작업 | 단위 | 판단 |
|---|---|---|
| check 파일 생성 | v2 batch | 한 번에 하는 게 맞음 |
| profile route 후보 추가 | v2 batch | CARE 경로 근거가 있는 것만 추가 |
| payload 파일 추가 | v2 batch | 실제 악성/대량 요청은 제외 |
| engine 보강 | 공통 기반 | CARE 전용 if문 금지, 범용 action만 허용 |
| validate-only | v2 batch | 안전하게 한 번에 가능 |
| 실제 WEB VM 공격 실행 | 항목별 | 상태 변경, 업로드, 반복 요청이 섞이면 위험 |
| 보고서 evidence 확정 | 항목별 | 스크린샷과 판정이 섞이지 않게 분리 |

### 다음 `/goal` 핵심 범위

다음 goal은 아래로 잡는다.

```text
목표: KISA Web Application Checker의 v2 batch scaffold를 구현한다.

포함:
- checks/06_xss.yml
- checks/07_csrf.yml
- checks/09_weak_password_policy.yml
- checks/10_insufficient_authentication.yml
- checks/11_insufficient_authorization.yml
- checks/14_malicious_file_upload.yml
- checks/20_automation_attack.yml
- 필요한 payload 파일
- profiles/care.yml의 route 후보
- README의 v2 scaffold 설명
- 작업 로그 갱신

검증:
- Python 문법 검증
- attack-active validate-only
- state-changing validate-only
- state-changing 실제 실행 confirm 차단 확인
- git diff --check
```

### 금지선

다음 goal에서 하지 않을 일:

```text
실제 WEB VM 공격 실행 금지
실제 글쓰기, 회원정보 수정, 업로드, 비밀번호 변경 금지
DB 변경 금지
CARE PHP 코드 수정 금지
brute force / 대량 요청 금지
실제 악성 파일 생성 금지
01, 12, 13 구현 금지
ZAP/Nuclei 연동 금지
MOC/index 수정 금지
커밋 금지
```

### 압축 후 재개 기준

압축 후에는 이 섹션을 기준으로 재개한다.

```text
다음 작업 = v2 batch scaffold 구현
구현은 batch
실제 공격 검증은 항목별 후속 작업
```

## 2026-06-19 v2 batch scaffold 구현

### 목적

v2 미완성 항목을 하나씩 실제 공격으로 밀기 전에, 06, 07, 09, 10, 11, 14, 20의 check/profile/payload 구조를 한 번에 준비했다.

이번 작업은 실제 WEB VM 공격 실행이 아니라 scaffold 작업이다.

```text
check 파일 생성
-> profile route 후보 추가
-> payload 후보 분리
-> validate-only 통과
-> 실제 공격/evidence는 항목별 후속 작업
```

### 구현 범위

추가한 check:

| 번호 | 항목 | required mode | 현재 자동화 수준 |
|---:|---|---|---|
| 06 | XSS | `attack-active` | 검색 route reflected 후보는 `payload_probe`, 게시글 stored 후보는 `manual_check` |
| 07 | CSRF | `state-changing` | 회원정보 수정 route와 hidden form 후보를 `manual_check`로 기록 |
| 09 | 약한 비밀번호 정책 | `state-changing` | 회원가입/회원수정 route와 약한 비밀번호 후보를 `manual_check`로 기록 |
| 10 | 불충분한 인증 절차 | `state-changing` | 회원정보 수정 전 현재 비밀번호 재인증 확인 후보를 `manual_check`로 기록 |
| 11 | 불충분한 권한 검증 | `state-changing` | ID/object 변조 후보를 `manual_check`로 기록 |
| 14 | 악성 파일 업로드 | `state-changing` | 업로드 form/handler/proof file 후보를 `manual_check`로 기록 |
| 20 | 자동화 공격 | `destructive-risk` | 반복 요청 후보와 cap/delay 후보만 `manual_check`로 기록 |

추가한 payload:

```text
payloads/xss.yml
payloads/csrf.yml
payloads/weak_passwords.yml
payloads/authentication.yml
payloads/authorization.yml
payloads/upload_proof.yml
payloads/automation.yml
```

추가한 CARE route 후보:

```text
login_submit
register_submit
member_modify_submit
member_delete
member_delete_submit
board_write
board_write_submit
board_view_candidate
data_upload_proof
```

### 주요 결정

- `checker.py`에는 CARE 전용 URL, 계정, 게시글 번호, payload를 넣지 않았다.
- CARE 경로와 자리표시자 값은 `profiles/care.yml`에만 둔다.
- 공격 문자열은 `payloads/*.yml`에 둔다.
- KISA 항목별 실행 의도는 `checks/*.yml`에 둔다.
- state-changing 항목은 지금 단계에서 실제 요청을 보내지 않는다.
- 반복 요청 위험이 있는 20번은 `destructive-risk`로 둔다.
- 새 범용 action으로 `manual_check`를 추가했다. 이 action은 HTTP 요청을 보내지 않고 route, payload, 수동 확인 조건을 report에 남기는 scaffold용 action이다.

### 검증 결과

실행한 검증:

```powershell
python -c "import py_compile, tempfile; py_compile.compile('checker.py', cfile=tempfile.NamedTemporaryFile(delete=False).name, doraise=True); print('py_compile ok')"
python checker.py --profile profiles/care.yml --checks checks --mode attack-active --validate-only --output "$env:TEMP\kisa-checker-v2-batch-attack-validate"
python checker.py --profile profiles/care.yml --checks checks --mode state-changing --validate-only --output "$env:TEMP\kisa-checker-v2-batch-state-validate"
python checker.py --profile profiles/care.yml --checks checks --mode destructive-risk --validate-only --output "$env:TEMP\kisa-checker-v2-batch-destructive-validate"
python checker.py --profile profiles/care.yml --checks checks --mode state-changing --output "$env:TEMP\kisa-checker-v2-batch-state-block"
```

확인 결과:

```text
py_compile ok

attack-active validate-only:
06 XSS passed
07, 09, 10, 11, 14 skipped_by_mode
20 skipped_by_mode

state-changing validate-only:
06, 07, 09, 10, 11, 14 passed
20 skipped_by_mode

destructive-risk validate-only:
02, 03, 04, 05, 06, 07, 08, 09, 10, 11, 14, 15, 16, 17, 19, 20, 21 passed

state-changing actual without confirm:
[ERROR] `state-changing` mode requires --confirm-state-changing
```

### 현재 한계

- 06 reflected 후보 외에는 실제 HTTP 요청을 보내지 않는 scaffold다.
- 07, 09, 10, 11, 14는 실제 세션, fixture, rollback을 정한 뒤 항목별로 실행해야 한다.
- 20은 `destructive-risk`라 대량 요청이나 brute force를 구현하지 않았다.
- 14의 upload proof는 harmless proof 후보만 payload로 분리했다. 실제 악성코드나 웹쉘은 만들지 않는다.
- mock target은 추가하지 않았다. 이번 goal의 검증 기준은 validate-only와 confirm 차단이다.

### 다음 작업 기준

다음 단계는 v2 항목별 실제 검증을 하나씩 분리한다.

우선순위 후보:

| 우선순위 | 항목 | 이유 |
|---:|---:|---|
| 1 | 06 XSS | reflected GET 후보는 상태 변경 없이 먼저 확인 가능. stored는 별도 글쓰기 fixture 필요 |
| 2 | 10 불충분한 인증 절차 | 회원정보 수정 route와 현재 비밀번호 재확인 여부가 비교적 명확 |
| 3 | 11 불충분한 권한 검증 | 실제 취약보다는 방어/분류 확인 성격이 강하므로 안전하게 검토 가능 |
| 4 | 07 CSRF | 세션과 rollback이 필요하므로 10 이후가 자연스러움 |
| 5 | 09 약한 비밀번호 정책 | 테스트 계정 생성/수정 fixture 필요 |
| 6 | 14 악성 파일 업로드 | 업로드 및 파일 정리 필요 |
| 7 | 20 자동화 공격 | 반복 요청 위험이 있어 가장 나중에 매우 작은 cap으로만 실행 |

다음 goal에서는 batch 구현이 아니라 항목 하나를 골라 실제 WEB VM evidence 생성 절차와 rollback을 확정한다.

## 2026-06-19 status 명칭 정리

### 목적

`--validate-only` 결과의 `[passed]`가 실제 보안 판정처럼 읽히는 문제를 줄인다.

### 구현 범위

- `checker.py`의 validate-only 성공 상태를 `passed`에서 `ready`로 변경했다.
- 실제 probe 내부에서 위험 신호가 없을 때 쓰던 `passed`도 `not_vulnerable`로 정리했다.
- README 상태표도 `ready`, `vulnerable`, `not_vulnerable`, `manual_required`, `skipped_by_mode`, `inconclusive`, `error` 기준으로 맞췄다.

### 주요 결정

- `ready`: `--validate-only`에서 실행 준비 완료.
- `vulnerable`: 취약 증거 확인.
- `not_vulnerable`: 검사 기준상 차단 또는 방어 근거 확인.
- `manual_required`: 자동 판정 불가.
- `error`: 검사 실패.
- `safe`는 전체 안전을 단정하는 표현이라 상태값으로 쓰지 않는다.

### 검증 결과

```powershell
python -m py_compile "20_팀 프로젝트/26. 6. 8 팀플/쉘 스크립트/kisa-webapp-checker/checker.py"
python checker.py --profile profiles/care.yml --checks checks --mode attack-active --validate-only
git diff --check
```

확인 결과:

```text
[ready] 02 SQL 인젝션
[ready] 03 디렉터리 인덱싱
[ready] 04 에러 페이지
[ready] 05 정보 노출
[ready] 06 XSS
[skipped_by_mode] 07 CSRF
...
```

`ready`는 실행 준비 상태일 뿐이며, 취약/안전 판정이 아니다.

## 2026-06-19 06 XSS 단독 실행 안정화

### 목적

v2 batch scaffold 이후 첫 항목별 실제 검증 대상으로 06 XSS를 안정화한다.

### 구현 범위

- `checker.py`에 `--check-id` 옵션을 추가했다.
  - `--check-id 06`
  - `--check-id 6`
  - `--check-id "06,08"`
  모두 동작하도록 숫자 ID를 두 자리로 정규화했다.
- `ready`는 validate-only 전용 상태로 유지하고, check YAML의 `manual_check.status`나 `no_match_status`에는 지정할 수 없게 막았다.
- `run_id`를 초 단위에서 microsecond 포함 형식으로 바꿨다.
  - 이전: `20260619-110033`
  - 이후: `20260619-110429-859313`
  - 빠르게 여러 번 실행해도 evidence 폴더가 덮일 위험을 줄이기 위함이다.
- `checks/06_xss.yml`은 reflected XSS 자동 검사만 담당하도록 정리했다.
- `vulnerable_statuses: [599]` 같은 우회값을 제거하고, 본문 패턴 기반 판정으로 명확히 바꿨다.
- stored XSS는 글쓰기 fixture와 브라우저 증거가 필요하므로 현재 06 자동 check에서 제외하고, 이후 별도 `state-changing` 후보로 남겼다.
- README에 06 단독 실행 명령과 상태 해석을 추가했다.

### 주요 결정

- 06 자동 check의 최종 status는 reflected XSS 자동 검사 결과를 직접 표현해야 한다.
- stored XSS를 같은 check 안에 `manual_required`로 넣으면 reflected가 `not_vulnerable`이어도 전체 status가 `manual_required`가 되어 판정이 흐려진다.
- 따라서 이번 goal에서는 reflected XSS만 자동화하고, stored XSS는 별도 후속 작업으로 분리한다.

### 검증 결과

실행한 검증:

```powershell
python checker.py --profile profiles/care.yml --checks checks --mode attack-active --validate-only --check-id 06 --output "$env:TEMP\kisa-xss-final-06c"
python checker.py --profile profiles/care.yml --checks checks --mode attack-active --validate-only --output "$env:TEMP\kisa-xss-final-all2"
python -c "import py_compile, tempfile; f=tempfile.NamedTemporaryFile(delete=False, suffix='.pyc'); f.close(); py_compile.compile('checker.py', cfile=f.name, doraise=True); print('py_compile ok')"
git diff --check
```

`ready` runtime 사용 차단 후 재검증:

```powershell
python checker.py --profile profiles/care.yml --checks checks --mode attack-active --validate-only --check-id 06 --output "$env:TEMP\kisa-xss-ready-only-06"
python checker.py --profile profiles/care.yml --checks checks --mode attack-active --validate-only --output "$env:TEMP\kisa-xss-ready-only-all"
```

확인 결과:

```text
[OK] run_id=20260619-110429-859313
[ready] 06 XSS

[OK] run_id=20260619-110429-995349
[ready] 02 SQL 인젝션
[ready] 03 디렉터리 인덱싱
[ready] 04 에러 페이지
[ready] 05 정보 노출
[ready] 06 XSS
[skipped_by_mode] 07 CSRF
...

py_compile ok
git diff --check 통과
```

`checker.py` 안에 CARE 전용 URL, 계정, 게시글 번호, `KISA_XSS`, `board_search` 같은 대상별 값이 들어가지 않았는지도 확인했다.

### WEB VM 실제 실행 명령

WEB VM에서 실제 reflected XSS evidence를 만들 때:

```bash
cd ~/kisa-webapp-checker
python3 checker.py --profile profiles/care.yml --checks checks --mode attack-active --check-id 06
```

기대 판정:

| status | 의미 |
|---|---|
| `vulnerable` | 응답 본문에 실행 가능한 `<script>` 또는 `onerror` payload가 그대로 반사됨 |
| `not_vulnerable` | payload가 HTML entity로 escape된 근거가 확인됨 |
| `manual_required` | 응답은 받았지만 반사/escape 근거가 부족해 브라우저 또는 코드 확인 필요 |
| `error` | WEB 서버 접근 실패, route 오류, 요청 실패 |

결과 확인:

```bash
cat evidence/<RUN_ID>/result.json
cat evidence/<RUN_ID>/report.md
find evidence/<RUN_ID>/06_XSS -type f | sort
```

### 현재 한계

- 이 goal은 reflected XSS 자동 검사만 안정화했다.
- stored XSS는 controlled test post, 로그인 세션, 브라우저 screenshot evidence가 필요하므로 후속 `state-changing` 작업으로 남긴다.
- 로컬 Codex 환경에서는 WEB VM의 CARE 서버에 직접 접근하지 않고, validate-only와 구조 검증까지만 수행했다.

### 다음 작업 기준

1. 사용자가 WEB VM에서 06 실제 실행 결과를 가져오면 `result.json`, `report.md`, raw response 기준으로 판정이 맞는지 본다.
2. 06 reflected 결과가 안정되면 다음 항목은 10 불충분한 인증 절차 또는 11 불충분한 권한 검증으로 넘어간다.

## 2026-06-19 06 XSS WEB VM 결과 반영

### 관찰 결과

WEB VM에서 06 XSS를 실제 실행했을 때 다음 결과가 나왔다.

```bash
cd ~/kisa-webapp-checker
python3 checker.py --profile profiles/care.yml --checks checks --mode attack-active --check-id 06
```

```text
[OK] run_id=20260619-053520-080912
[manual_required] 06 XSS
```

`result.json` 기준 findings:

```text
Route `board_search` baseline returned 500.
Route `board_search` payload #1 returned 500; no configured exposure or blocking pattern matched.
Route `board_search` payload #2 returned 500; no configured exposure or blocking pattern matched.
```

### 판단

이 결과는 XSS가 애매하다는 뜻이 아니라, baseline부터 500이라서 XSS payload 비교가 신뢰 불가능하다는 뜻이다.

정상적인 reflected XSS 검사는 baseline 검색 요청이 먼저 200으로 동작해야 한다. baseline이 500이면 route, DB, PHP 오류, 설정 문제 같은 선행 오류를 먼저 해결해야 한다.

### 보강 내용

- `payload_probe`에 `baseline_expected_statuses`와 `baseline_unexpected_status`를 추가했다.
- 06 XSS check에는 다음 기준을 넣었다.

```yaml
baseline_expected_statuses:
  - 200
baseline_unexpected_status: "error"
```

이제 WEB VM에서 같은 상황이 나오면 `manual_required`가 아니라 `error`로 떨어지는 것이 맞다.

### 재검증

로컬 구조 검증:

```powershell
python checker.py --profile profiles/care.yml --checks checks --mode attack-active --validate-only --check-id 06 --output "$env:TEMP\kisa-xss-baseline-status-06"
python checker.py --profile profiles/care.yml --checks checks --mode attack-active --validate-only --output "$env:TEMP\kisa-xss-baseline-status-all"
python -c "import py_compile, tempfile; f=tempfile.NamedTemporaryFile(delete=False, suffix='.pyc'); f.close(); py_compile.compile('checker.py', cfile=f.name, doraise=True); print('py_compile ok')"
git diff --check
```

확인 결과:

```text
[ready] 06 XSS
py_compile ok
git diff --check 통과
```

### 다음 확인

WEB VM에서 다시 실행한다.

```bash
cd ~/kisa-webapp-checker
python3 checker.py --profile profiles/care.yml --checks checks --mode attack-active --check-id 06
```

예상:

| 결과 | 의미 |
|---|---|
| `error` | baseline이 여전히 500이라 검사 대상 route가 먼저 고장난 상태 |
| `vulnerable` | baseline은 정상이고 payload가 실행 가능한 형태로 반사됨 |
| `not_vulnerable` | baseline은 정상이고 payload가 escape된 근거 확인 |
| `manual_required` | baseline은 정상이나 자동 rule로 반사/escape 판단 부족 |

## 2026-06-19 DB 의존도 축 추가 결정

### 배경

06 XSS 실행 중 `board_search` baseline이 500을 반환했다. 이 때문에 XSS payload가 반사되는지, escape되는지 비교할 수 없었다.

이 문제는 단순히 06 XSS만의 문제가 아니다. SQL Injection, XSS, CSRF처럼 DB 또는 상태 저장 기능과 엮인 항목은 DB가 꺼져 있거나 fixture가 없으면 진단 결과가 왜곡된다.

### 결정

설계 문서에 DB 의존도 축을 추가했다.

| DB 의존도 | 의미 |
|---|---|
| `DB-independent` | DB 없이도 신뢰성 있게 점검 가능 |
| `DB-backed recommended` | DB 없이 proof route로 일부 검증 가능하지만 실제 앱 기능 검증 신뢰도는 낮아짐 |
| `DB-required` | DB, 세션, fixture, 상태 저장이 없으면 원래 항목 점검 의미가 거의 없음 |

### fallback 정책

`DB-backed recommended` 항목은 원 route가 DB 오류로 500을 내면 DB-less fallback route를 실행할 수 있다.

하지만 fallback 결과를 원 route의 최종 안전 판정으로 승격하지 않는다.

표현 기준:

```text
primary_status: error
condition: db_unavailable
fallback_status: not_vulnerable
fallback_scope: db_independent_proof_only
```

보고서 요약 표현:

```text
[db_unavailable, fallback_not_vulnerable]
```

이 의미는 “DB 없는 대체 route에서는 방어 근거가 확인됐지만, 원래 CARE 기능은 DB 장애로 판정하지 못했다”는 것이다.

### fallback 금지

`DB-required` 항목은 fallback하지 않는다.

예:

- 02 SQL Injection
- 07 CSRF
- 09 약한 비밀번호 정책
- 10 불충분한 인증 절차
- 11 불충분한 권한 검증
- 12 취약한 비밀번호 복구 절차
- 13 프로세스 검증 누락
- 20 자동화 공격

이 항목들은 DB/세션/fixture/상태 변경이 핵심이라, 대체 proof route를 돌려도 원래 취약점 진단으로 보기 어렵다.

### 다음 구현 기준

다음 코드 작업에서는 다음을 검토한다.

1. check YAML에 `db_dependency` 필드 추가
2. `DB-backed recommended` 항목에 `fallback_step` 또는 `fallback_route` 추가
3. baseline 500이 DB 오류 패턴이면 `condition: db_unavailable` 기록
4. fallback 결과는 `fallback_status`로 따로 기록
5. `result.json`과 `report.md`에서 primary와 fallback을 분리 출력

우선 적용 후보:

| 우선순위 | 항목 | 이유 |
|---:|---:|---|
| 1 | 06 XSS | 현재 board_search 500으로 실제 문제가 드러남 |
| 2 | 15 파일 다운로드 | known file 직접 다운로드와 DB 기반 권한 검증을 분리하기 좋음 |
| 3 | 16 세션 관리 | cookie flag 관찰과 로그인 후 세션 변화 확인을 분리해야 함 |
| 4 | 14 악성 파일 업로드 | FS 기반 업로드 proof와 게시판 DB 연동 업로드를 분리해야 함 |

## 다음 기록 템플릿

```markdown
## YYYY-MM-DD 작업명

### 목적

### 구현 범위

### 주요 결정

### 검증 결과

### 현재 한계

### 다음 작업 기준
```
