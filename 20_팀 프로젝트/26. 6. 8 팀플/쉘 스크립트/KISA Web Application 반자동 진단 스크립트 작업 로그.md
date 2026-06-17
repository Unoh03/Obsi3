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
