# KISA Web Application Checker v0

KISA X. Web Application 01~21 전체 진단을 목표로 하는 반자동 진단 프레임워크의 v0 구현이다.

v0의 목표는 취약점 진단 정확도가 아니라 다음 파이프라인을 검증하는 것이다.

```text
profile -> check -> request -> evidence -> report
```

## 현재 범위

v0는 전체 21개 항목을 구현하지 않는다. 현재 포함된 sample check는 다음 2개다.

| 번호 | 항목 | mode | 동작 |
|---:|---|---|---|
| 17 | 데이터 평문 전송 | `passive` | base URL scheme, 민감 route 후보, form action 기록 |
| 21 | 불필요한 Method 악용 | `safe-active` | `OPTIONS`, `TRACE`, `PUT`, `DELETE` 응답 기록 |

## 설치

```bash
python -m pip install -r requirements.txt
```

참고: v0는 현재 profile/check 파일을 검증할 수 있도록 제한적인 YAML fallback과 표준 라이브러리 HTTP fallback을 포함한다. 그래도 실제 사용 기준은 `requests`, `PyYAML` 설치 상태로 둔다.

## 실행 전 확인

`profiles/care.yml`에서 target을 먼저 확인한다.

```yaml
base_url: "http://127.0.0.1"
target_allowlist:
  - "127.0.0.1"
  - "localhost"
  - "172.168.10.10"
```

`base_url`의 host는 반드시 `target_allowlist`에 있어야 한다. 이 제한은 허가되지 않은 외부 사이트로 실수 실행하는 것을 막기 위한 안전장치다.

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
```

## 출력

실행 결과는 `evidence/<run_id>/` 아래에 생성된다.

```text
evidence/<run_id>/
  result.json
  report.md
  run.log
  rollback_checklist.md
  17_.../
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
| `*.response.txt` | 실제 받은 HTTP response |

## 상태값

| 상태 | 의미 |
|---|---|
| `passed` | 설정 검증 또는 정보성 단계 통과 |
| `vulnerable` | 자동 rule 기준 취약 근거 확인 |
| `not_vulnerable` | 자동 rule 기준 차단 또는 방어 근거 확인 |
| `manual_required` | 브라우저/스크린샷/업무 판단 필요 |
| `skipped_by_mode` | 현재 mode에서 실행 금지 |
| `inconclusive` | 응답은 받았지만 자동 판정 부족 |
| `error` | 요청 실패 또는 실행 오류 |

## 안전 원칙

- `checker.py`에는 CARE 전용 URL, 계정, payload를 넣지 않는다.
- 대상별 값은 `profiles/*.yml`에 둔다.
- KISA 항목별 동작은 `checks/*.yml`에 둔다.
- 기본 실행은 `passive`다.
- `safe-active`는 `PUT`, `DELETE` 같은 method를 보낼 수 있으므로 실습 대상에서만 실행한다.
- SQLi, XSS, SSRF, 로그인 자동화, 대량 요청은 v0에 포함하지 않는다.

## 이후 단계

| 단계 | 구현 항목 |
|---|---|
| v1 | 03, 04, 05, 15, 16, 17, 19, 21 |
| v2 | 02, 06, 07, 09, 10, 11, 14, 20 |
| v3 | 01, 08, 12, 13 |
