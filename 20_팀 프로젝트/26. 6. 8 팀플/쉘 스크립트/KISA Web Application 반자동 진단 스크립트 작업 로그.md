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
