# KISA Web Application Checker v3

KISA X. Web Application 01~21 전체 진단을 목표로 하는 반자동 진단 프레임워크다.

v3는 완성형 취약점 스캐너가 아니라, v1의 passive / safe-active 파이프라인과 v2의 payload 기반 검사 구조 위에 SSRF처럼 앱 문맥이 필요한 check를 하나씩 붙이는 단계다.

```text
profile -> check -> request -> evidence -> report
```

## 현재 범위

| 번호 | 항목 | mode | 동작 |
|---:|---|---|---|
| 02 | SQL 인젝션 | `attack-active` | payload 파일의 SQLi 문자열을 profile-defined route에 주입하고 오류/노출 패턴 확인 |
| 06 | XSS | `attack-active` | reflected 후보는 payload probe, stored 후보는 manual scaffold로 route/payload만 준비 |
| 07 | CSRF | `state-changing` | 회원정보 수정 route의 CSRF token 유무와 서버 측 검증을 manual scaffold로 준비 |
| 08 | SSRF | `attack-active` | profile-defined URL fetch route에 통제된 loopback-only proof URL을 주입하고 proof 문자열 노출 또는 차단 근거 확인 |
| 09 | 약한 비밀번호 정책 | `state-changing` | 회원가입/회원수정 route와 약한 비밀번호 후보를 manual scaffold로 준비 |
| 10 | 불충분한 인증 절차 | `state-changing` | 회원정보 수정 전 현재 비밀번호 재인증 여부를 manual scaffold로 준비 |
| 11 | 불충분한 권한 검증 | `state-changing` | 회원/게시글/다운로드 후보 route와 ID/object 변조 후보를 manual scaffold로 준비 |
| 14 | 악성 파일 업로드 | `state-changing` | 업로드 form/handler/proof file 후보를 manual scaffold로 준비 |
| 03 | 디렉터리 인덱싱 | `safe-active` | 후보 디렉터리 요청 후 listing 패턴 확인 |
| 04 | 에러 페이지 | `safe-active` | 없는 경로 요청 후 stack trace, local path, version 노출 확인 |
| 05 | 정보 노출 | `safe-active` | 후보 민감 파일 요청 후 설정/소스 노출 패턴 확인 |
| 15 | 파일 다운로드 | `safe-active` | profile에 정의한 known download candidate 접근 확인 |
| 16 | 불충분한 세션 관리 | `passive` | session cookie의 `HttpOnly`, `SameSite`, `Secure` 조건 확인 |
| 17 | 데이터 평문 전송 | `passive` | base URL scheme, 민감 route 후보, form action 기록 |
| 19 | 관리자 페이지 노출 | `safe-active` | 후보 관리자 페이지 접근 가능 여부 확인 |
| 20 | 자동화 공격 | `destructive-risk` | 로그인/게시글 반복 요청 후보와 매우 작은 cap 후보만 manual scaffold로 준비 |
| 21 | 불필요한 Method 악용 | `safe-active` | `OPTIONS`, `TRACE`, `PUT`, `DELETE` 응답 기록 |

02번, 06번, 08번은 기본 실행에서는 동작하지 않는다. `--mode attack-active`를 명시해야 실행된다.

07, 09, 10, 11, 14번은 `state-changing` scaffold다. 현재는 실제 회원정보 수정, 글쓰기, 업로드 요청을 보내지 않고 route, payload, fixture 전제만 report에 남긴다. 실제 실행은 항목별 후속 작업에서만 한다.

20번은 반복 요청 위험이 있으므로 `destructive-risk` scaffold다. 현재는 brute force나 대량 요청을 보내지 않는다.

## 설치

권장:

```bash
python -m pip install -r requirements.txt
```

v1은 제한적인 YAML fallback과 표준 라이브러리 HTTP fallback을 포함한다. 그래서 `requests`, `PyYAML`이 없어도 기본 검증은 가능하지만, 실제 사용 기준은 dependency 설치 상태다.

## target 설정

`profiles/care.yml`에서 target을 먼저 확인한다.

```yaml
base_url: "http://127.0.0.1"
target_allowlist:
  - "127.0.0.1"
  - "localhost"
  - "172.168.10.10"
```

`base_url`의 host는 반드시 `target_allowlist`에 있어야 한다. 이 제한은 실수로 외부 사이트를 검사하지 않기 위한 안전장치다.

CARE 전용 경로 후보는 `profiles/care.yml`에만 둔다. `checker.py`에는 CARE URL, 계정, payload를 넣지 않는다.

로그인된 세션이 필요한 항목은 profile에 쿠키나 헤더를 직접 넣어 주입한다.

```yaml
session:
  cookies:
    PHPSESSID: "실습용_세션값"
  headers: {}
```

실제 세션 쿠키는 보고서나 Git에 남기지 않는다.

## DB 없이 02번 checker 동작만 검증

DB가 꺼져 있으면 실제 CARE SQL Injection 증거는 만들 수 없다. 대신 mock target으로 checker의 `payload_probe` 동작만 검증할 수 있다.

이 결과는 보고서용 CARE 취약 증거가 아니다.

터미널 1:

```bash
python mock_targets/sqli_search_mock.py --mode vulnerable --port 18080
```

터미널 2:

```bash
python checker.py --profile profiles/mock_sqli.yml --checks checks --mode attack-active
```

mock mode:

| mode | 의미 | 기대 판정 |
|---|---|---|
| `vulnerable` | baseline은 200, SQLi-like payload는 SQL error 500 | `vulnerable` |
| `safe` | baseline과 payload 모두 정상 200 | `manual_required` |
| `db-down` | baseline과 payload 모두 500 | `inconclusive` |

## WEB VM 없이 08번 checker 동작만 검증

Codex 로컬에서는 실제 `172.168.10.10` CARE 서버와 직접 통신하지 않는다. 대신 mock target으로 08번 판정 구조만 검증할 수 있다.

이 결과는 보고서용 CARE 취약 증거가 아니다.

터미널 1:

```bash
python mock_targets/ssrf_fetch_mock.py --mode vulnerable --port 18081
```

터미널 2:

```bash
mkdir -p /tmp/kisa-checker-08-only/checks /tmp/kisa-checker-08-only/payloads
cp checks/08_ssrf.yml /tmp/kisa-checker-08-only/checks/
cp payloads/ssrf.yml /tmp/kisa-checker-08-only/payloads/
python checker.py --profile profiles/mock_ssrf.yml --checks /tmp/kisa-checker-08-only/checks --mode attack-active
```

mock mode:

| mode | 의미 | 기대 판정 |
|---|---|---|
| `vulnerable` | fetch endpoint가 loopback-only proof 응답을 그대로 반환 | `vulnerable` |
| `safe` | fetch endpoint가 loopback/internal 요청을 차단 | `not_vulnerable` |

`safe` mock은 CARE의 조치 후 응답인 `허용되지 않은 요청 대상입니다`와 같은 차단 문구를 반환하므로 자동 `not_vulnerable`이 기대된다. 알 수 없는 차단 문구, 빈 응답, redirect 정책처럼 rule에 없는 경우만 `manual_required`로 남긴다.

## WEB VM에서 08번 실제 CARE evidence 생성

08번 실제 evidence는 WEB VM의 VSC SSH 터미널에서 실행한다. Codex 로컬에서 `172.168.10.10`으로 직접 접근하려고 하지 않는다.

```bash
cd ~/kisa-webapp-checker
mkdir -p /tmp/kisa-checker-08-only/checks /tmp/kisa-checker-08-only/payloads
cp checks/08_ssrf.yml /tmp/kisa-checker-08-only/checks/
cp payloads/ssrf.yml /tmp/kisa-checker-08-only/payloads/
python3 checker.py --profile profiles/care.yml --checks /tmp/kisa-checker-08-only/checks --mode attack-active
```

실행 후 확인할 파일:

```bash
RUN_ID="<방금 출력된 run_id>"
cat "evidence/${RUN_ID}/result.json"
cat "evidence/${RUN_ID}/report.md"
cat "evidence/${RUN_ID}/run.log"
find "evidence/${RUN_ID}" -type f | sort
```

Goal 2에서는 위 출력과 08 SSRF request/response evidence를 기준으로 `vulnerable`, `not_vulnerable`, `manual_required`, `inconclusive`, `error` 판정이 맞는지 다시 본다. 현재 CARE 조치 후 응답처럼 `허용되지 않은 요청 대상입니다`가 확인되면 `not_vulnerable`이 기대된다.

## 실행

passive mode:

```bash
python checker.py --profile profiles/care.yml --checks checks --mode passive
```

safe-active mode:

```bash
python checker.py --profile profiles/care.yml --checks checks --mode safe-active
```

attack-active mode:

```bash
python checker.py --profile profiles/care.yml --checks checks --mode attack-active
```

state-changing mode:

```bash
python checker.py --profile profiles/care.yml --checks checks --mode state-changing --confirm-state-changing
```

설정만 검증하고 HTTP 요청을 보내지 않으려면:

```bash
python checker.py --profile profiles/care.yml --checks checks --mode passive --validate-only
python checker.py --profile profiles/care.yml --checks checks --mode safe-active --validate-only
python checker.py --profile profiles/care.yml --checks checks --mode attack-active --validate-only
python checker.py --profile profiles/care.yml --checks checks --mode state-changing --validate-only
python checker.py --profile profiles/care.yml --checks checks --mode destructive-risk --validate-only
```

v2 batch scaffold를 확인할 때는 먼저 validate-only만 실행한다.

```bash
python checker.py --profile profiles/care.yml --checks checks --mode attack-active --validate-only
python checker.py --profile profiles/care.yml --checks checks --mode state-changing --validate-only
python checker.py --profile profiles/care.yml --checks checks --mode destructive-risk --validate-only
```

`state-changing` 실제 실행은 confirm 없이는 차단되어야 정상이다.

```bash
python checker.py --profile profiles/care.yml --checks checks --mode state-changing
```

기대 결과:

```text
[ERROR] `state-changing` mode requires --confirm-state-changing
```

## mode 주의

| mode | 의미 |
|---|---|
| `passive` | GET 요청과 응답 관찰 중심. 상태 변경 없음 |
| `safe-active` | 없는 경로 요청, 후보 URL 확인, `OPTIONS`/`TRACE`/`PUT`/`DELETE` 같은 method 확인 포함 |
| `attack-active` | SQLi/XSS 등 payload 전송 가능. 실습 대상에서만 실행 |
| `state-changing` | 글쓰기, 회원정보 수정, 업로드처럼 상태 변경 가능. `--confirm-state-changing` 필요 |
| `destructive-risk` | 삭제, 대량 요청, 장애 가능 요청. 기본 금지, `--confirm-destructive-risk` 필요 |

`safe-active` 이상은 실습 대상에서만 실행한다. 특히 21번은 `PUT`, `DELETE` 요청을 보낼 수 있다.

## 출력

실행 결과는 `evidence/<run_id>/` 아래에 생성된다.

```text
evidence/<run_id>/
  result.json
  report.md
  run.log
  rollback_checklist.md
  03_.../
    *.request.txt
    *.response.txt
```

| 파일 | 의미 |
|---|---|
| `result.json` | 항목별 status, evidence path, finding |
| `report.md` | Obsidian/보고서용 Markdown 요약 |
| `run.log` | 실행 순서와 오류 |
| `rollback_checklist.md` | 테스트 후 확인/복구할 항목 |
| `*.request.txt` | 실제 보낸 HTTP request |
| `*.response.txt` | 실제 받은 HTTP response 또는 요청 실패 기록 |

## 상태값

| 상태 | 의미 |
|---|---|
| `passed` | 설정 검증 또는 정보 수집 단계 통과 |
| `vulnerable` | 자동 rule 기준 취약 근거 확인 |
| `not_vulnerable` | 자동 rule 기준 차단 또는 방어 근거 확인 |
| `manual_required` | 브라우저, 스크린샷, 업무 흐름 판단 필요 |
| `skipped_by_mode` | 현재 mode에서 실행 금지 |
| `inconclusive` | 응답은 받았지만 자동 판정 근거 부족 |
| `error` | 요청 실패 또는 실행 오류 |

## 안전 원칙

- `checker.py`에는 CARE 전용 URL, 계정, payload를 넣지 않는다.
- target 값은 `profiles/*.yml`에 둔다.
- KISA 항목별 동작은 `checks/*.yml`에 둔다.
- payload는 `payloads/*.yml`에 둔다.
- 기본 실행은 `passive`다.
- state-changing 이상은 confirm 없이는 실행하지 않는다.
- brute force, 파일 삭제, DB 변경, 서비스 장애 유발 요청은 v2 범위가 아니다.

## 이후 단계

| 단계 | 구현 후보 |
|---|---|
| v2 scaffold 완료 | 06, 07, 09, 10, 11, 14, 20 |
| v2 실제 검증 후보 | 06, 07, 09, 10, 11, 14, 20을 항목별로 분리 실행 |
| v3 다음 후보 | 01, 12, 13 |

`v2 batch scaffold`는 완료된 상태다. 다음 단계는 실제 WEB VM 공격 실행이 아니라, 항목별로 실행 전제와 rollback을 확인한 뒤 하나씩 evidence를 만든다.
