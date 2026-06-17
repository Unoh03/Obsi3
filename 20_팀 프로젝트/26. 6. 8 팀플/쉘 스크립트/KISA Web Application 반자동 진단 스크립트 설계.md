---
type: project
topic: security-project
status: draft
created: 2026-06-17
---

# KISA Web Application 반자동 진단 스크립트 설계

## 1. 설계 목적

이 문서는 `주요정보통신기반시설 기술적 취약점 분석·평가 방법 상세가이드`의 **X. Web Application(웹)** 항목을 반자동으로 점검하기 위한 스크립트 설계안이다.

목표는 완전한 DAST 제품을 만드는 것이 아니다. 목표는 다음에 가깝다.

```text
KISA Web Application 01~21 항목
-> 대상 웹앱 profile 기반으로 요청 실행
-> 조치 전/후 evidence 저장
-> Markdown / JSON / raw request-response 보고서 생성
```

이 문서는 아직 구현 코드가 아니다. 이후 Python 등으로 구현하기 전, 구조와 경계선을 확정하기 위한 기준 문서다.

## 2. CARE 전용 스크립트가 아닌 이유

CARE만 검사하는 스크립트는 만들기 쉽지만, 다음 문제가 생긴다.

| 방식 | 문제 |
|---|---|
| CARE URL을 코드에 직접 작성 | 다른 웹앱에 재사용 불가 |
| `victim`, `admin`, 특정 게시판 경로를 코드에 직접 작성 | 하드코딩된 실습 시나리오처럼 보임 |
| payload와 기대 결과를 함수 안에 작성 | KISA 항목별 근거와 분리됨 |
| CARE 전용 if문 증가 | 보고서에서 “진단 도구”보다 “CARE 맞춤 자동 클릭기”처럼 보임 |

따라서 이 설계의 기본 원칙은 다음이다.

```text
engine에는 CARE가 없다.
CARE는 첫 번째 target profile일 뿐이다.
KISA 항목은 check 정의에 둔다.
payload는 payload 파일에 둔다.
판정 기준은 evidence rule로 둔다.
```

## 3. 레퍼런스별 참고 요소

| 레퍼런스                                                                                          | 참고할 요소                                                             | 경계                                                   |
| --------------------------------------------------------------------------------------------- | ------------------------------------------------------------------ | ---------------------------------------------------- |
| [KISA-CIIP-2026](https://github.com/rebugui/KISA-CIIP-2026)                                   | 항목 metadata, `run_all` 방식, JSON/TXT 결과, timeout, result manager 구조 | 웹서버/서버 점검용이므로 X. Web Application 진단 로직으로 직접 가져오지 않는다 |
| [OWASP ZAP Automation Framework](https://www.zaproxy.org/docs/automate/automation-framework/) | YAML 기반 plan, environment, auth, job, report 구조                    | ZAP 자체를 대체하려 하지 않는다                                  |
| [OWASP ZAP Baseline Scan](https://www.zaproxy.org/docs/docker/baseline-scan/)                 | passive scan, spider, Markdown/JSON/HTML 보고서 출력 방식                 | CARE/KISA 항목 판정은 별도 해석 필요                            |
| [OWASP WSTG](https://owasp.org/www-project-web-security-testing-guide/)                       | 웹앱 테스트 방법론, 테스트 시나리오 식별 방식, scenario 식별자                           | KISA 21개 항목과 무리하게 1:1 매핑하지 않는다                       |
| [OWASP ASVS](https://owasp.org/www-project-application-security-verification-standard/)       | 조치/검증 기준, 보안 요구사항 표현                                               | 공격 재현 절차로 쓰지 않는다                                     |
| [Nuclei](https://docs.projectdiscovery.io/opensource/nuclei/overview)                         | template, matcher, extractor, severity 구조                          | 무분별한 템플릿 스캔은 하지 않는다                                  |

## 4. 전체 디렉터리 구조

구현 시 권장 구조는 다음과 같다.

```text
kisa-webapp-checker/
  checker.py
  profiles/
    care.yml
    sample.yml
  checks/
    01_code_injection.yml
    02_sql_injection.yml
    ...
    21_unnecessary_method.yml
  payloads/
    sqli.yml
    xss.yml
    ssrf.yml
    file_upload.yml
  reports/
  evidence/
    <run_id>/
      result.json
      report.md
      run.log
      rollback_checklist.md
      02_sql_injection/
        request_001.txt
        response_001.txt
```

## 5. 구성 요소 역할

| 구성 요소 | 역할 | 하드코딩 금지선 |
|---|---|---|
| engine | HTTP 요청 실행, 세션 유지, 변수 치환, evidence 저장, report 생성 | 특정 앱 URL, 계정, 게시판 경로 금지 |
| profile | 대상 앱의 base URL, 로그인 방식, 계정, route, cleanup 정의 | profile에는 대상별 값이 들어가도 됨 |
| check | KISA 번호, 항목명, 실행 mode, route 참조, 판정 rule 정의 | 특정 대상 앱의 절대 URL 금지 |
| payload | SQLi, XSS, SSRF 등 payload 묶음 | payload는 check에서 참조만 함 |
| evidence | raw request/response, screenshot placeholder, 실행 로그 저장 | 결과를 덮어쓰지 않고 run_id별 보존 |
| report | Markdown, JSON, 조치 전/후 비교표 생성 | 자동 판정이 약한 항목은 수동 확인으로 표시 |

## 6. 실행 mode

위험도에 따라 실행 mode를 나눈다. 기본 실행은 안전 모드만 허용한다.

| mode | 기본 실행 | 의미 | 예시 |
|---|---:|---|---|
| `passive` | ON | 이미 접근 가능한 응답, header, cookie 관찰 | cookie 속성, server header |
| `safe-active` | 명시 허용 | 비교적 안전한 추가 요청 | `OPTIONS`, `TRACE`, 404, 디렉터리 접근 |
| `attack-active` | 명시 허용 | 공격성 payload 전송 | SQLi, XSS, SSRF payload |
| `state-changing` | 강한 확인 필요 | 서버 상태 변경 | 글쓰기, 회원정보 수정, 파일 업로드 |
| `destructive-risk` | 기본 금지 | 삭제, 대량 요청, 장애 가능 요청 | 반복 요청, 삭제 method, 대량 brute force |

실행 원칙:

```text
기본값은 passive.
mode가 높아질수록 명시적 flag와 confirm을 요구한다.
허가되지 않은 외부 사이트를 대상으로 실행하지 않는다.
state-changing 이상은 rollback checklist를 생성한다.
```

## 7. KISA Web Application 01~21 자동화 가능성 분류

| 번호 | 항목 | 자동화 수준 | 기본 mode | 설계 판단 |
|---:|---|---|---|---|
| 01 | 코드 인젝션 | 반자동 / 앱 구현 필요 | `attack-active` | LDAP, SSI, XPath, XXE, SSTI 등은 대상 기능이 있어야 의미 있음 |
| 02 | SQL 인젝션 | 자동 / 반자동 | `attack-active` | 로그인, 검색, 조회 route에 payload와 응답 diff rule 적용 |
| 03 | 디렉터리 인덱싱 | 자동 | `safe-active` | 후보 디렉터리 요청 후 listing 패턴 확인 |
| 04 | 에러 페이지 적용 미흡 | 자동 | `safe-active` | 오류 유발 요청 후 path, stack, version 노출 확인 |
| 05 | 정보 누출 | 자동 | `safe-active` | 민감 파일 후보 URL 접근과 본문 패턴 확인 |
| 06 | XSS | 자동 / 반자동 | `attack-active` | reflected/stored 여부 확인, 브라우저 실행 증거는 수동 가능 |
| 07 | CSRF | 반자동 | `state-changing` | token 부재와 상태 변경 요청 재전송 확인 |
| 08 | SSRF | 반자동 / 앱 구현 필요 | `attack-active` | 서버가 URL을 대신 요청하는 sink와 proof target 필요 |
| 09 | 약한 비밀번호 정책 | 반자동 | `state-changing` | 회원가입/변경 route와 약한 비밀번호 fixture 필요 |
| 10 | 불충분한 인증 절차 | 반자동 | `state-changing` | 중요 기능 접근 전 재인증 요구 여부 확인 |
| 11 | 불충분한 권한 검증 | 반자동 | `state-changing` | 사용자 A/B 권한 fixture와 ID/num 변조 필요 |
| 12 | 취약한 비밀번호 복구 절차 | 앱 구현 필요 | `state-changing` | 비밀번호 복구 기능이 없으면 manual 또는 N/A |
| 13 | 프로세스 검증 누락 | 앱 구현 필요 | `state-changing` | 정상 업무 순서와 우회 endpoint 정의 필요 |
| 14 | 악성 파일 업로드 | 반자동 / 위험 | `state-changing` | 업로드 후 실행/접근 여부 확인, 실제 악성 파일은 금지 |
| 15 | 파일 다운로드 | 자동 / 반자동 | `attack-active` | 안전한 proof file 기준으로 traversal 확인 |
| 16 | 불충분한 세션 관리 | 자동 / 반자동 | `passive` | cookie 속성, session id 변화, timeout 확인 |
| 17 | 데이터 평문 전송 | 자동 | `passive` | 민감 form의 HTTP/HTTPS 사용 여부 확인 |
| 18 | 쿠키 변조 | 자동 / 반자동 | `attack-active` | 권한값 쿠키 존재와 변조 영향 확인 |
| 19 | 관리자 페이지 노출 | 자동 / 반자동 | `safe-active` | admin URL 후보, port, IP 제한 확인 |
| 20 | 자동화 공격 | 반자동 / 위험 | `destructive-risk` | 반복 요청은 rate 제한과 상한 필요 |
| 21 | 불필요한 Method 악용 | 자동 | `safe-active` | `OPTIONS`, `TRACE`, `PUT`, `DELETE` 응답 확인 |

중요한 판정:

```text
01~21을 모두 설계 대상으로 포함한다.
하지만 21개를 모두 완전 자동화 가능하다고 보지 않는다.
업무 흐름, 권한, 복구 절차, SSRF sink처럼 앱 문맥이 필요한 항목은 반자동 또는 수동으로 남긴다.
```

## 8. MVP 구현 순서

처음부터 21개 전체를 완전 구현하려고 하면 도구가 무거워진다. 대신 check 파일은 21개 모두 만들되, 실행 가능한 항목부터 동작하게 한다.

| 단계 | 목표 | 항목 |
|---|---|---|
| v1 | 안전하고 자동화 쉬운 항목 | 03, 04, 05, 15, 16, 17, 19, 21 |
| v2 | 로그인 세션과 상태 변경이 필요한 항목 | 02, 06, 07, 09, 10, 11, 14, 20 |
| v3 | 앱 구현 또는 업무 흐름 정의가 필요한 항목 | 01, 08, 12, 13 |

v1의 목적은 “도구 구조가 맞는지” 검증하는 것이다. v1부터 강한 공격성 payload나 대량 요청을 넣지 않는다.

## 9. 출력물 설계

| 출력물 | 내용 |
|---|---|
| `report.md` | Obsidian/보고서용 Markdown 요약 |
| `result.json` | 항목별 status, mode, evidence path, 판정 근거 |
| raw request | 실제 보낸 method, URL, headers, body |
| raw response | status, headers, body 일부 또는 전체 |
| evidence files | proof 파일, 업로드 결과, 다운로드 결과 등 |
| `run.log` | 실행 순서, mode, skipped reason, 오류 |
| `rollback_checklist.md` | 테스트 데이터와 풀어둔 설정 복구 목록 |
| before/after table | 조치 전/후 결과 비교 |

판정값은 다음 정도로 시작한다.

| 값 | 의미 |
|---|---|
| `vulnerable` | 자동 rule로 취약 근거 확인 |
| `not_vulnerable` | 자동 rule로 방어 근거 확인 |
| `manual_required` | 스크린샷/브라우저/업무 판단 필요 |
| `not_applicable` | 대상 기능 없음 |
| `skipped_by_mode` | 현재 mode에서 실행 금지 |
| `inconclusive` | 응답은 받았지만 판정 근거 부족 |

## 10. 안전장치와 rollback 원칙

필수 안전장치:

```text
- target allowlist 없이는 실행 금지
- 기본 mode는 passive
- attack-active 이상은 명시 flag 필요
- state-changing 이상은 confirm 필요
- destructive-risk는 기본 비활성화
- 요청 timeout과 전체 실행 timeout 적용
- 반복 요청에는 rate limit과 최대 횟수 적용
- raw evidence는 run_id별로 분리 저장
- secret으로 보이는 값은 report에서 redaction
```

rollback 원칙:

| 대상 | rollback 방식 |
|---|---|
| 테스트 계정 | 생성한 계정 목록 기록 후 삭제 명령 출력 |
| 테스트 게시글 | 제목 prefix 기준 삭제 후보 출력 |
| 업로드 파일 | 업로드 path 기록 후 삭제 후보 출력 |
| proof 파일 | profile에 정의한 proof path 기준 삭제 후보 출력 |
| 일부러 푼 방어 설정 | 조치 전/후 상태와 재잠금 명령 기록 |
| DB fixture | 생성 SQL과 삭제 SQL을 함께 기록 |

rollback은 자동 삭제보다 checklist 출력이 기본이다. 실습 증거를 남겨야 하는 경우가 많기 때문이다.

## 11. 이후 구현 시 결정할 것

구현 전에 다음 결정을 확정한다.

| 결정 항목 | 기본 선택 |
|---|---|
| 구현 언어 | Python 3 |
| HTTP client | `requests` |
| 설정 파서 | `PyYAML` |
| HTML 파싱 | 필요 시 `BeautifulSoup` |
| report template | Markdown 우선, JSON 병행 |
| 첫 target profile | CARE |
| 기본 실행 mode | `passive` |
| 첫 MVP | 03, 04, 05, 15, 16, 17, 19, 21 |
| ZAP 연동 | 후순위. 먼저 자체 evidence 구조 확정 |
| Nuclei 연동 | 후순위. template 참고만 먼저 적용 |

## 12. 최종 기준

이 설계의 성공 기준은 다음이다.

```text
CARE 없이도 다른 웹앱 profile을 추가할 수 있다.
CARE 전용 값은 profile/config에만 있다.
KISA 항목 번호와 check 정의가 대응된다.
자동화 불가능한 항목은 manual_required 또는 not_applicable로 정직하게 남긴다.
위험한 검사는 기본 비활성화한다.
실습 후 복구할 항목을 rollback checklist로 남긴다.
```

따라서 이 도구의 이름은 “CARE 진단기”가 아니라 **KISA Web Application 반자동 진단 프레임워크**로 보는 것이 맞다.