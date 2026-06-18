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
- AWS 후속 절차는 [[20_팀 프로젝트/26. 6. 8 팀플/웹 보안 모음/AWS 후속 조치와 재검증|AWS 후속 조치와 재검증]]에 정리했다.
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
