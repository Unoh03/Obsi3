# KISA Web Application Checker v1

KISA X. Web Application 01~21 전체 진단을 목표로 하는 반자동 진단 프레임워크다.

v1은 완성형 취약점 스캐너가 아니라, 비교적 안전한 passive / safe-active 항목을 중심으로 다음 흐름을 검증한다.

```text
profile -> check -> request -> evidence -> report
```

## 현재 범위

| 번호 | 항목 | mode | 동작 |
|---:|---|---|---|
| 03 | 디렉터리 인덱싱 | `safe-active` | 후보 디렉터리 요청 후 listing 패턴 확인 |
| 04 | 에러 페이지 | `safe-active` | 없는 경로 요청 후 stack trace, local path, version 노출 확인 |
| 05 | 정보 노출 | `safe-active` | 후보 민감 파일 요청 후 설정/소스 노출 패턴 확인 |
| 15 | 파일 다운로드 | `safe-active` | profile에 정의한 known download candidate 접근 확인 |
| 16 | 불충분한 세션 관리 | `passive` | session cookie의 `HttpOnly`, `SameSite`, `Secure` 조건 확인 |
| 17 | 데이터 평문 전송 | `passive` | base URL scheme, 민감 route 후보, form action 기록 |
| 19 | 관리자 페이지 노출 | `safe-active` | 후보 관리자 페이지 접근 가능 여부 확인 |
| 21 | 불필요한 Method 악용 | `safe-active` | `OPTIONS`, `TRACE`, `PUT`, `DELETE` 응답 기록 |

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

## 실행

passive mode:

```bash
python checker.py --profile profiles/care.yml --checks checks --mode passive
```

safe-active mode:

```bash
python checker.py --profile profiles/care.yml --checks checks --mode safe-active
```

설정만 검증하고 HTTP 요청을 보내지 않으려면:

```bash
python checker.py --profile profiles/care.yml --checks checks --mode passive --validate-only
python checker.py --profile profiles/care.yml --checks checks --mode safe-active --validate-only
```

## mode 주의

| mode | 의미 |
|---|---|
| `passive` | GET 요청과 응답 관찰 중심. 상태 변경 없음 |
| `safe-active` | 없는 경로 요청, 후보 URL 확인, `OPTIONS`/`TRACE`/`PUT`/`DELETE` 같은 method 확인 포함 |

`safe-active`는 실습 대상에서만 실행한다. 특히 21번은 `PUT`, `DELETE` 요청을 보낼 수 있다.

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
- 기본 실행은 `passive`다.
- SQLi, XSS, SSRF, 로그인 자동화, brute force, 파일 업로드/삭제, DB 변경은 v1 범위가 아니다.

## 이후 단계

| 단계 | 구현 후보 |
|---|---|
| v2 | 02, 06, 07, 09, 10, 11, 14, 20 |
| v3 | 01, 08, 12, 13 |
