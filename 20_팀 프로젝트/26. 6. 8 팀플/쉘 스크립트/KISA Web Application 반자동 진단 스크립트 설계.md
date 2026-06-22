---
type: project
topic: security-project
status: draft
created: 2026-06-17
---

# KISA Web Application 반자동 진단 스크립트 설계

## 체크리스트

이 표는 **진단 결과의 안전성 표가 아니라 checker 진도표**다. 첫 열은 check YAML·source rule·설계가 준비됐는지를, 뒤 두 열은 실제 WEB VM evidence 확보 여부를 분리한다. `vulnerable`도 evidence 확보가 끝났으면 `[x]`로 표시한다. `inconclusive`, 설정 검증만 완료, 로컬 정규식 검증만 완료한 evidence는 `[ ]`로 남긴다.

| 번호 | 항목 | 구현·설계 | DB 없음: 정적 / proof / DB-less evidence | DB·세션·fixture runtime evidence | 현재 상태 |
|---:|---|---|---|---|---|
| 01 | 코드 인젝션 | - [ ] 하위 유형별 check 설계 | - [ ] 대상 기능별 proof | — | LDAP·SSI·XXE·SSTI 등 하위 유형 분해 필요 |
| 02 | SQL 인젝션 | - [x] attack-active check scaffold | — | - [ ] DB query 결과·오류·인증 우회 evidence | DB-required |
| 03 | 디렉터리 인덱싱 | - [x] safe-active check | - [x] `not_vulnerable` | — | R1 WEB VM evidence 확보 |
| 04 | 에러 페이지 | - [x] safe-active check | - [x] `not_vulnerable` | — | R1 WEB VM evidence 확보 |
| 05 | 정보 누출 | - [x] safe-active check | - [ ] 실행 결과 `inconclusive` | — | 후보 응답의 추가 근거 필요 |
| 06 | XSS | - [x] reflected check·fallback 구현 | - [x] reflected proof route `not_vulnerable` | - [ ] board/stored XSS, DB fixture·브라우저 evidence | R2 DB-less 범위만 완료 |
| 07 | CSRF | - [x] manual·source evidence check | - [x] WEB VM에서 CSRF defense pattern 0개 확인 | - [ ] 로그인 세션·cross-site form·rollback | pattern 부재만으로 취약 확정하지 않음 |
| 08 | SSRF | - [x] attack-active check | - [x] controlled loopback 차단 `not_vulnerable` | — | R2 WEB VM evidence 확보 |
| 09 | 약한 비밀번호 정책 | - [x] manual·source evidence check | - [x] WEB VM에서 policy helper pattern 0개 확인 | - [ ] 가입/수정 거부와 test account cleanup | helper 부재만으로 취약 확정하지 않음 |
| 10 | 불충분한 인증 절차 | - [x] manual·source-assisted rule | - [x] WEB VM에서 재인증 pattern 3개 확인 | - [ ] 현재 비밀번호 재인증 runtime evidence | source evidence 확보. 실제 변경 차단은 R4 필요 |
| 11 | 불충분한 권한 검증 | - [x] manual·session subject source rule | - [x] WEB VM deployed source에서 session subject pattern 확인 | - [ ] 사용자 A/B·객체 IDOR evidence | R3 회원 수정 범위의 source evidence 확보. 전체 권한 검증은 R4 필요 |
| 12 | 취약한 비밀번호 복구 절차 | - [x] manual·source variant check | - [ ] WEB VM source variant evidence | - [ ] 코드 전달·만료·reset 결과 evidence | local source fixture에서 vuln/safe variant 3개 확인 |
| 13 | 프로세스 검증 누락 | - [x] manual·source variant check | - [ ] WEB VM source variant evidence | - [ ] 단계 생략 reset·rollback evidence | local source fixture에서 vuln/safe variant 3개 확인 |
| 14 | 악성 파일 업로드 | - [x] state-changing manual scaffold | - [ ] 파일 처리 source/proof evidence | - [ ] 게시글 DB 연동 업로드·cleanup evidence | check 존재 |
| 15 | 파일 다운로드 | - [x] safe-active check | - [x] known download candidate `vulnerable` | - [ ] 소유권/권한 기반 다운로드 evidence | R1 직접 다운로드 경로 완료 |
| 16 | 불충분한 세션 관리 | - [x] passive check | - [ ] 비로그인 관찰 결과 `inconclusive` | - [ ] 로그인 후 세션 변화·timeout evidence | cookie 관찰만 수행 |
| 17 | 데이터 평문 전송 | - [x] passive check | - [x] HTTP transport `vulnerable` | — | R1 WEB VM evidence 확보 |
| 18 | 쿠키 변조 | - [ ] check 설계·구현 | - [ ] cookie role/value source·관찰 evidence | - [ ] 로그인·권한 영향 runtime evidence | check 미구현 |
| 19 | 관리자 페이지 노출 | - [x] safe-active check | - [x] `not_vulnerable` | — | R1 WEB VM evidence 확보 |
| 20 | 자동화 공격 | - [x] destructive-risk manual scaffold | — | - [ ] 반복 요청·rate limit·cleanup evidence | check 존재 |
| 21 | 불필요한 Method 악용 | - [x] safe-active check | - [x] `not_vulnerable` | — | R1 WEB VM evidence 확보 |

체크 순서 규칙:

```text
1. `구현·설계`의 [x]는 check YAML, source rule, 또는 명시된 설계가 준비됐다는 뜻이다.
2. source evidence는 WEB VM의 source_root에서 실제 실행되어 evidence file이 생긴 뒤 체크한다.
3. DB·세션·fixture runtime은 테스트 데이터와 rollback/cleanup 근거까지 남긴 뒤 체크한다.
4. 한 칸의 [x]는 다른 칸의 안전 판정이나 완료를 대신하지 않는다.
```

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

## 6-1. DB 의존도와 대체 진단 정책

KISA Web Application 항목은 실행 위험도뿐 아니라 **DB 의존도**도 함께 봐야 한다. 실행 mode가 낮아도 DB가 꺼져 있으면 baseline route가 500이 되어 진단 결과가 왜곡될 수 있다.

DB 의존도는 다음 세 단계로 분류한다.

| DB 의존도 | 의미 | 처리 원칙 |
|---|---|---|
| `DB-independent` | DB 없이도 원래 항목을 신뢰성 있게 점검 가능 | DB preflight 없이 실행 가능 |
| `DB-backed recommended` | DB 없이 proof route로 일부 검증 가능하지만, 실제 앱 기능 검증 신뢰도는 낮아짐 | 원 route baseline 실패 시 DB-less fallback을 실행할 수 있음 |
| `DB-required` | DB, 세션, fixture, 상태 저장이 없으면 원래 항목 점검 의미가 거의 없음 | fallback으로 원래 항목의 방어 판정을 내지 않고, DB 준비 후 재실행하거나 `manual_required` / `inconclusive`로 남김 |

### DB-less fallback 원칙

`DB-backed recommended` 항목은 원래 CARE route가 DB 오류로 500을 내는 경우, profile에 정의된 DB 없는 proof route를 대체 진단으로 실행할 수 있다.

다만 fallback 결과는 원래 기능의 최종 안전 판정으로 승격하지 않는다.

잘못된 표현:

```text
board_search가 DB 오류로 500
-> reflected proof route가 escape됨
-> 06 XSS는 not_vulnerable
```

올바른 표현:

```text
status: not_vulnerable
conditions: [db_backed_primary_unavailable, fallback_used]
scope: db_independent_proof_only
```

즉 보고서에는 다음처럼 표현한다.

```text
status: not_vulnerable
conditions: db_backed_primary_unavailable, fallback_used
scope: db_independent_proof_only
```

이 의미는 **DB 없는 대체 route에서는 방어 근거가 확인됐지만, DB-backed 원래 CARE 기능은 판정하지 못했다**는 것이다. timeout이나 예상 밖 HTTP 응답만으로 DB 장애를 단정하지 않는다. 실제 DB preflight로 장애를 확인했을 때만 `db_unavailable`을 사용한다. fallback 전용 합성 status를 새로 만들지 않는다.

### fallback 금지선

`DB-required` 항목에는 자동 fallback을 걸지 않는다. 예를 들어 CSRF, 약한 비밀번호 정책, 불충분한 인증 절차는 실제 DB 상태 변경과 rollback이 있어야 의미가 있다. 이 경우 DB가 없으면 `manual_required` 또는 `inconclusive`로 남기고, DB를 켠 뒤 다시 실행한다.

## 7. KISA Web Application 01~21 자동화 가능성 분류

| 번호 | 항목 | 자동화 수준 | 기본 mode | 설계 판단 |
|---:|---|---|---|---|
| 01 | 코드 인젝션 | 반자동 / 앱 구현 필요 | `attack-active` | LDAP, SSI, XPath, XXE, SSTI 등은 대상 기능이 있어야 의미 있음 |
| 02 | SQL 인젝션 | 자동 / 반자동 | `attack-active` | 로그인, 검색, 조회 route에 payload와 응답 diff rule 적용 |
| 03 | 디렉터리 인덱싱 | 자동 | `safe-active` | 후보 디렉터리 요청 후 listing 패턴 확인 |
| 04 | 에러 페이지 적용 미흡 | 자동 | `safe-active` | 오류 유발 요청 후 path, stack, version 노출 확인 |
| 05 | 정보 누출 | 자동 | `safe-active` | 민감 파일 후보 URL 접근과 본문 패턴 확인 |
| 06 | XSS | 자동 / 반자동 | `attack-active` | reflected/stored 여부 확인, 브라우저 실행 증거는 수동 가능 |
| 07 | CSRF | 반자동 | `safe-active` source / `state-changing` runtime | token·서버 검증 source evidence와 실제 상태 변경 요청 재전송을 분리 |
| 08 | SSRF | 반자동 / 앱 구현 필요 | `attack-active` | 서버가 URL을 대신 요청하는 sink와 proof target 필요 |
| 09 | 약한 비밀번호 정책 | 반자동 | `safe-active` source / `state-changing` runtime | policy helper source evidence와 회원가입/변경 fixture를 분리 |
| 10 | 불충분한 인증 절차 | 반자동 | `safe-active` source / `state-changing` runtime | 재인증 source evidence와 중요 기능 변경 차단 runtime을 분리 |
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

## 7-1. 항목별 DB 의존도

| 번호 | 항목 | DB 의존도 | DB 영향 판단 |
|---:|---|---|---|
| 01 | 코드 인젝션 | `DB-independent` 또는 `DB-backed recommended` | OS Command, SSI, XXE, SSTI는 DB 없이 가능. XPath/LDAP처럼 저장소가 필요한 하위 유형은 별도 분류 |
| 02 | SQL 인젝션 | `DB-required` | DB 쿼리 오류, 결과 차이, 인증 우회 여부가 핵심이라 DB 없으면 신뢰도 크게 하락 |
| 03 | 디렉터리 인덱싱 | `DB-independent` | 디렉터리 응답만 확인 |
| 04 | 에러 페이지 | `DB-independent` | 없는 경로나 일반 오류 응답 확인. 단 DB 오류 노출을 별도 증거로 볼 때는 DB 영향 있음 |
| 05 | 정보 노출 | `DB-independent` | 민감 파일 직접 노출 확인 중심 |
| 06 | XSS | `DB-backed recommended` | reflected proof route는 DB 없이 가능. CARE 게시판 검색/조회 XSS는 DB 정상 동작 필요. stored XSS는 DB-required에 가까움 |
| 07 | CSRF | `DB-backed recommended` / runtime은 `DB-required` | form token 존재와 처리 코드 흔적은 DB 없이 확인 가능. 실제 상태 변경과 rollback은 DB 필요 |
| 08 | SSRF | `DB-independent` | URL fetch sink와 internal proof page 중심 |
| 09 | 약한 비밀번호 정책 | `DB-backed recommended` / runtime은 `DB-required` | 비밀번호 정책 코드 흔적은 DB 없이 확인 가능. 회원가입/수정 결과 검증은 DB 필요 |
| 10 | 불충분한 인증 절차 | `DB-backed recommended` / runtime은 `DB-required` | 현재 비밀번호 재확인 코드 흔적은 DB 없이 확인 가능. 실제 변경 차단 여부는 DB 필요 |
| 11 | 불충분한 권한 검증 | `DB-backed recommended` / runtime은 `DB-required` | 세션 사용자 기준 처리인지 소스에서 일부 확인 가능. 사용자 A/B, 객체 ID 변조 영향은 DB 필요 |
| 12 | 취약한 비밀번호 복구 절차 | `DB-backed recommended` / runtime은 `DB-required` | 인증번호 저장/노출/검증 코드 흐름은 DB 없이 일부 확인 가능. 계정 존재와 reset 결과는 DB 필요 |
| 13 | 프로세스 검증 누락 | `DB-backed recommended` / runtime은 `DB-required` | 단계 토큰, 세션 플래그, 이전 단계 검증 코드 흔적은 DB 없이 일부 확인 가능. 실제 우회 성공 여부는 DB 필요 |
| 14 | 악성 파일 업로드 | `DB-backed recommended` 또는 `DB-required` | 단순 파일 업로드 sink는 FS 중심. CARE 게시판 업로드 흐름은 DB 글/첨부 기록과 엮임 |
| 15 | 파일 다운로드 | `DB-backed recommended` | known file 직접 다운로드는 DB 없이 가능. 권한/소유권 기반 다운로드는 DB 필요 |
| 16 | 불충분한 세션 관리 | `DB-backed recommended` | 쿠키 flag는 DB 없이 가능. 로그인 후 세션 변화와 timeout은 DB 필요 |
| 17 | 데이터 평문 전송 | `DB-independent` | HTTP/HTTPS, form action, transport 관찰 중심 |
| 18 | 쿠키 변조 | `DB-backed recommended` 또는 `DB-required` | 쿠키 속성 관찰은 DB 없이 가능. 변조 영향 확인은 로그인/권한/상태 필요 |
| 19 | 관리자 페이지 노출 | `DB-independent` | 후보 URL 접근 가능 여부 중심 |
| 20 | 자동화 공격 | `DB-required` | 로그인 반복, 게시글 반복 등록, rate limit 확인은 상태 저장 필요. rate limit 코드/설정 흔적은 보조 정보일 뿐 fallback 판정으로 승격하지 않음 |
| 21 | 불필요한 Method 악용 | `DB-independent` | HTTP method 응답 중심 |

## 7-2. DB-required 재검토 결론

DB가 없을 때 실행 가능한 대체 진단은 두 종류로 나눈다.

| 대체 진단 종류 | 의미 | 최종 status 처리 |
|---|---|---|
| `runtime_fallback_route` | DB를 쓰지 않는 proof route를 실제 HTTP로 요청 | 기존 status 사용 가능. 단 `conditions: [db_backed_primary_unavailable, fallback_used]`, `scope`를 함께 기록 |
| `source_assisted_fallback` | profile에 `source_root`가 있을 때 PHP 소스에서 방어 코드 흔적 확인 | 자동 판정은 보수적으로 처리. 강한 근거 없으면 `manual_required` 또는 `inconclusive` |

재검토 결과:

|  번호 | 기존 판단         | 재검토 판단 | 이유                                                                                       |
| --: | ------------- | ------ | ---------------------------------------------------------------------------------------- |
|  02 | `DB-required` | 유지     | SQLi는 DB 쿼리 결과, 오류, 인증 우회가 핵심이다. DB 없는 proof route나 소스 grep만으로 원래 route의 방어 판정을 내리면 과장이다 |
|  07 | `DB-required` | 부분 승격  | CSRF token hidden field와 서버 검증 코드 흔적은 DB 없이 확인 가능하다. 실제 회원정보 변경 차단은 DB 필요                |
|  09 | `DB-required` | 부분 승격  | 비밀번호 정책 함수, 길이/복잡도/blocklist 검증 코드는 DB 없이 확인 가능하다. 실제 가입/수정 거부는 DB 필요                    |
|  10 | `DB-required` | 부분 승격  | `currentPw` 같은 재인증 입력과 서버 검증 코드는 DB 없이 확인 가능하다. 실제 수정 차단은 DB 필요                          |
|  11 | `DB-required` | 부분 승격  | 요청 파라미터의 사용자 id를 신뢰하는지, 세션 id를 기준으로 처리하는지 소스에서 일부 확인 가능하다. 권한 우회 성공은 DB 필요               |
|  12 | `DB-required` | 부분 승격  | 인증번호 노출, 서버 저장, reset 단계 검증 흐름은 소스에서 일부 확인 가능하다. 실제 reset 결과는 DB 필요                      |
|  13 | `DB-required` | 부분 승격  | 이전 단계 완료 플래그, token, session state 검증 흔적은 소스에서 일부 확인 가능하다. 실제 단계 우회 성공은 DB 필요            |
|  20 | `DB-required` | 유지     | 자동화 공격은 반복 요청에 대한 상태 저장, 실패 횟수, rate limit이 핵심이다. 코드/설정 흔적은 보조 정보일 뿐 대체 진단으로 충분하지 않다     |

## 7-3. DB 의존도 기반 실행 전략

앞으로 check는 다음 순서로 실행한다.

```text
1. DB 의존도 확인
2. baseline route 정상성 확인
3. baseline이 500이면 DB 오류인지 일반 route 오류인지 분류
4. DB-backed recommended이면 fallback route 실행 가능
5. DB-required이면 fallback하지 않고 DB 준비 후 재실행
6. result/report에는 최종 `status`와 별도로 `conditions`, `scope`, primary/fallback route 기록을 남김
```

예시:

```text
06 XSS
- primary route: board_search
- DB가 켜져 있으면 board_search로 실제 CARE 검색 XSS 진단
- DB가 꺼져 board_search baseline이 500이면 reflected_xss_proof 같은 DB-less route로 fallback 가능
- 단, fallback 결과는 CARE 게시판 검색의 최종 판정이 아니라 checker/payload/escape 동작의 대체 증거로만 기록
```

### V.db 구현 필드

V.db 기반은 다음 필드를 사용한다.

| 위치 | 필드 | 의미 |
|---|---|---|
| profile | `source_root` | source-assisted fallback이 읽을 앱 소스 루트 |
| check | `db_dependency` | `DB-independent`, `DB-backed recommended`, `DB-required` 같은 의존도 메모 |
| payload step | `fallback_routes` | primary baseline이 신뢰 불가능할 때 실행할 DB-less route |
| payload step | `fallback_conditions` | fallback 실행 시 result/report에 붙일 조건. 예: `db_backed_primary_unavailable`, `fallback_used` |
| payload step | `fallback_scope` | fallback 결과의 해석 범위. 예: `db_independent_proof_only` |
| source step | `source_assisted_fallback` | HTTP 요청 없이 PHP 소스에서 방어 코드 흔적을 확인하는 action |
| result/report | `conditions`, `scope` | status의 의미를 제한하는 부가 정보 |

대표 적용:

| 항목 | fallback 계열 | 현재 적용 |
|---:|---|---|
| 06 XSS | `runtime_fallback_route` | `board_search` baseline이 200이 아니면 `xss_reflected_proof` route를 fallback으로 실행 |
| 10 불충분한 인증 절차 | `source_assisted_fallback` | `source_root` 아래 `member/modify.php`, `member/modifyModel.php`에서 `currentPw` 검증 흔적 확인 |

## 8. MVP 구현 순서

처음부터 21개 전체를 완전 구현하려고 하면 도구가 무거워진다. 대신 check 파일은 21개 모두 만들되, 실행 가능한 항목부터 동작하게 한다.

| 단계 | 목표 | 항목 |
|---|---|---|
| v1 | 안전하고 자동화 쉬운 항목 | 03, 04, 05, 15, 16, 17, 19, 21 |
| v2 | 로그인 세션과 상태 변경이 필요한 항목 | 02, 06, 07, 09, 10, 11, 14, 20 |
| v3 | 앱 구현 또는 업무 흐름 정의가 필요한 항목 | 01, 08, 12, 13 |

v1의 목적은 “도구 구조가 맞는지” 검증하는 것이다. v1부터 강한 공격성 payload나 대량 요청을 넣지 않는다.

## 8-0. 2026-06-19 설계 리베이스

기존 v1/v2/v3 계획은 실패한 계획이 아니라 **위험도와 구현 난이도 기준의 1차 로드맵**이었다. 다만 실제 구현 중 DB가 꺼진 환경에서 500 응답이 반복되면서, 단순한 v단계만으로는 판정 의미를 정확히 표현하기 어려워졌다.

따라서 현재 로드맵은 다음 두 축으로 다시 본다.

| 축 | 역할 | 상태 |
|---|---|---|
| v단계 | 어떤 항목을 어떤 순서로 구현할지 정하는 구현 순서 | 유지하되 재정렬 |
| V.db | DB 없음, fallback, source-assisted 판정 의미를 표현하는 공통 기반 | 새로 추가된 필수 기반 |

### 기존 계획 대비 현재 상태

| 구분 | 기존 계획 | 현재 상태 | 판정 |
|---|---|---|---|
| v1 | 03, 04, 05, 15, 16, 17, 19, 21 같은 안전한 자동 점검 | 기본 check와 mode 구조가 들어가 있음 | 유지 |
| v2 | 02, 06, 07, 09, 10, 11, 14, 20의 payload/state-changing 계열 | batch scaffold는 있으나 DB 의존성 때문에 실제 판정이 흔들림 | 수정 |
| v3 | 01, 08, 12, 13 같은 앱 문맥/별도 기능 필요 항목 | 08 SSRF가 먼저 들어갔고, 12/13은 source-assisted 또는 DB 준비가 필요 | 수정 |
| V.db | 기존 계획에 없었음 | `conditions`, `scope`, `runtime_fallback_route`, `source_assisted_fallback` 기반 추가 | 새 기준선 |

### 유지 / 폐기 / 수정

| 분류 | 항목 | 결정 |
|---|---|---|
| 유지 | 기존 status vocabulary | `vulnerable`, `not_vulnerable`, `manual_required`, `not_applicable`, `skipped_by_mode`, `inconclusive`, `error` 유지 |
| 유지 | `ready` | validate-only 전용 상태로 유지 |
| 유지 | profile/check/payload 분리 | CARE 전용 값을 `checker.py`에 넣지 않는 원칙 유지 |
| 유지 | v1 안전 항목 | 경량 자동 점검 기준선으로 유지 |
| 폐기 | v2를 한 번에 실제 공격 자동화하는 흐름 | DB, 세션, fixture, rollback 없이는 결과가 과장될 수 있어 폐기 |
| 폐기 | fallback 전용 합성 status | `fallback_not_vulnerable` 같은 상태는 만들지 않음 |
| 수정 | v2/v3 경계 | 번호 기준이 아니라 DB 의존도와 실행 위험도 기준으로 재배치 |
| 수정 | DB 없는 판정 | status를 새로 만들지 않고 `conditions`, `scope`로 의미 제한 |
| 수정 | source-assisted 판정 | 실제 runtime 성공/실패가 아니라 소스 근거 보조 진단으로 제한 |

### 새 단계별 로드맵

| 단계 | 목표 | 항목/작업 | 완료 기준 |
|---|---|---|---|
| R0 | 현재 기준선 고정 | V.db 기반, status 명칭, v1/v2/v3 재정렬 | 설계/로그에 기준선 기록 |
| R1 | DB-independent 중심 자동 점검 안정화 | 03, 04, 05, 17, 19, 21 + 15/16 제한 관찰 | 실제 WEB VM에서 evidence와 report가 의미 있게 생성됨 |
| R2 | attack-active 중 DB 없이 가능한 항목 안정화 | 06 reflected XSS fallback, 08 SSRF | `conditions/scope`가 의도대로 출력됨 |
| R3 | source-assisted fallback 확장 | 07, 09, 10, 11, 12, 13 | 소스 근거는 기록하되 runtime 판정으로 과장하지 않음 |
| R4 | DB/세션/fixture 기반 runtime 검증 | 02, 07, 09, 10, 11, 12, 13, 14, 20 | fixture, confirm flag, rollback 또는 cleanup 절차가 있음 |
| R5 | 통합 실행과 보고서 품질 | 전체 check 실행, result/report 정리 | 항목별 status, conditions, scope, evidence가 읽히는 형태로 정리됨 |

R1의 핵심은 `DB-independent`인 03, 04, 05, 17, 19, 21이다. 15 파일 다운로드와 16 세션 관리는 `DB-backed recommended`로, R1에서는 제한적인 관찰 결과만 남기고 권한·로그인 세션 검증은 R4에서 수행한다.

R1 실제 WEB VM 실행 결과를 기록한 뒤에는, DB-required runtime으로 가지 말고 **R2: 06 reflected XSS fallback과 08 SSRF의 attack-active runtime evidence 안정화**로 진행한다. 21 Method는 이미 `safe-active` R1 항목이므로 R2에 포함하지 않는다.

### R2 06 XSS fallback 실제 실행 결과

2026-06-21 WEB VM에서 `board_search` baseline은 DB 연결 대기로 5초 timeout이 났다. 기존 engine은 HTTP status가 예상과 다를 때만 fallback을 실행했으므로, `RequestFailed` 예외에서는 `xss_reflected_proof`까지 도달하지 못하고 `error`로 끝났다.

06번에 fallback route가 명시된 경우에만 primary baseline의 request 실패도 fallback 실행 조건으로 처리하도록 보정했다. proof route는 `mode: safe`로 고정했고, WEB VM에서 다음 결과를 확인했다.

```text
curl http://127.0.0.1/vuln/xss/reflected.php?mode=safe&data=kisa-baseline
-> HTTP 200, kisa-baseline 출력

python3 checker.py --profile profiles/care.yml --checks checks --mode attack-active --check-id 06
-> [not_vulnerable] 06 XSS
```

이 `not_vulnerable`은 proof route의 HTML escaping 근거에 한정한다. DB-backed `board_search`의 stored/reflected XSS 안전 판정은 아니며, DB와 fixture가 준비된 R4에서 별도로 검증한다.

### R2 08 SSRF 실제 실행 결과

WEB VM에서 controlled loopback proof URL을 payload로 실행했다.

```text
python3 checker.py --profile profiles/care.yml --checks checks --mode attack-active --check-id 08
-> [not_vulnerable] 08 SSRF
```

payload response는 HTTP 200이지만 `허용되지 않은 요청 대상입니다.`라는 `fetch.php`의 차단 문구를 포함했다. 따라서 HTTP status만으로 판단하지 않고 body의 configured blocking evidence로 `not_vulnerable`을 판정했다.

baseline의 외부 URL은 application 내부 `curl` timeout을 본문에 기록했지만, 이는 외부 대상 연결성 문제일 뿐 loopback 차단 규칙의 우회 성공 증거는 아니다. R2의 06과 08은 모두 제한된 proof route 또는 controlled payload 범위에서 실제 WEB VM evidence를 생성했다.

## 8-1. R2 완료와 R3 시작점

R2는 완료했다. 다음은 DB 없는 상태에서 원래 runtime 판정을 흉내 내는 작업이 아니라, 이미 있는 `source_assisted_fallback`을 보수적으로 확장하는 R3다.

R3는 새로운 engine 대공사가 아니라, 이미 존재하는 profile/check/payload/evidence 구조에 **앱 문맥이 필요한 항목의 소스 근거**를 하나씩 붙이는 단계로 본다. 10번의 재인증 검사 정의를 대표 구조로 삼는다.

| 우선순위 | 번호 | 항목 | 판단 |
|---:|---:|---|---|
| 1 | 07 | CSRF | token hidden field와 서버 검증 코드 흔적은 source-assisted로 볼 수 있음. 실제 상태 변경은 R4 |
| 2 | 09 | 약한 비밀번호 정책 | 길이·복잡도·blocklist 검증 함수의 존재를 보조 근거로 기록 가능 |
| 3 | 11 | 불충분한 권한 검증 | 요청 id 대신 세션 기준 처리가 있는지 확인 가능. 사용자 A/B 우회는 R4 |
| 4 | 12, 13 | 비밀번호 복구 / 프로세스 검증 | 구현된 `/vuln/password-recovery/` 흐름의 token·session·단계 검증을 소스 근거로 확인 |

다음 goal은 **R3 대상의 source-assisted 적용 가능 범위와 공통 rule을 설계**하는 것이다. 이 goal에서는 runtime 요청, DB fixture, 회원정보 수정, reset, 파일 업로드를 실행하지 않는다.

R3의 1차 완료 기준:

```text
07, 09, 11, 12, 13의 source files와 판단 가능한 방어/취약 pattern을 확정한다.
각 check는 source 근거만으로 runtime 안전 판정을 과장하지 않는다.
source_root가 없거나 파일이 없으면 manual_required 또는 inconclusive로 남긴다.
DB, 로그인, 상태 변경, 대량 요청은 사용하지 않는다.
```

### R3 source-assisted 적용 판단

`source_assisted_fallback`은 파일에 특정 문자열이 있다는 사실만 확인한다. 현재 구현은 여러 파일을 하나의 문자열로 합쳐 pattern을 찾고, `vulnerable_patterns`는 하나라도 일치하면 `vulnerable`을 우선한다. 따라서 **방어 코드가 없다는 사실만으로 취약하다고 판정하거나, 취약/조치 분기가 공존하는 실습 코드를 하나의 status로 판정하면 안 된다.**

| 번호 | 적용 판단 | 읽을 파일 | source 근거 후보 | 자동 판정 범위 | R4 runtime으로 남길 범위 |
|---:|---|---|---|---|---|
| 07 CSRF | evidence-only, 현재는 `manual_required` | `member/modify.php`, `member/modifyModel.php` | hidden `csrf_token`, session token 저장, `$_POST['csrf_token']`, `hash_equals()` | 방어 pattern이 모두 있을 때만 “token 검증 코드 존재”를 기록. 현재 파일에 pattern이 없다는 사실만으로 취약 확정 금지 | 로그인된 피해자 세션, cross-site form, 실제 회원정보 변경과 rollback |
| 09 약한 비밀번호 정책 | evidence-only, 현재는 `manual_required` | `member/registerModel.php`, `vuln/password-recovery/reset.php` | 공통 password-policy helper 호출, 최소 길이, 복잡도, blocklist, id 포함/반복 문자 검증 | 특정 handler가 정책 helper를 서버에서 호출하는지 확인. 회원가입과 reset의 정책이 다르면 하나의 안전 판정 금지 | 약한 비밀번호 가입·변경 거부와 test account cleanup |
| 11 불충분한 권한 검증 | 제한적으로 적용 가능 | `member/modifyModel.php`, `member/deleteModel.php` | `$id = $_SESSION['id']`, `UPDATE`/`DELETE ... WHERE id='$id'` | **회원 수정·탈퇴에서 client-supplied id 대신 session subject를 쓰는지**만 `not_vulnerable` 근거로 기록 가능 | 사용자 A/B, 게시글/파일 소유권, 역할 기반 권한, IDOR 실제 우회 |
| 12 취약한 비밀번호 복구 절차 | source variant evidence-only | `vuln/password-recovery/request.php`, `verify.php` | 취약 branch의 고정 코드/화면 노출, 조치 branch의 `random_int`, `password_hash`, 만료·시도 횟수·`password_verify` | named pattern set별 일치 여부만 기록하고 전체 status는 `manual_required`로 고정 | 등록된 계정, 코드 전달, 만료, 시도 횟수, reset 결과 |
| 13 프로세스 검증 누락 | source variant evidence-only | `vuln/password-recovery/verify.php`, `reset.php` | 조치 branch의 `verified`, `user_id`, `verified_at`, 만료 확인과 취약 branch의 직접 reset 경로 | named pattern set별 일치 여부만 기록하고 전체 status는 `manual_required`로 고정 | request/verify 생략 후 reset 성공/차단과 DB rollback |

### 공통 YAML rule 형태

현재 engine으로 구현 가능한 제한적 규칙은 다음 형태다. 이는 runtime 안전 판정이 아니라 source evidence의 범위를 명시한다.

```yaml
- id: bounded_server_side_check
  action: source_assisted_fallback
  files:
    - "member/modifyModel.php"
  conditions:
    - source_assisted_evidence_only
  scope: "member_modify_session_subject_only"
  not_vulnerable_patterns:
    - "...server-side session subject pattern..."
    - "...sensitive query bound to that subject..."
  not_vulnerable_match: "all"
  no_match_status: "manual_required"
  missing_source_status: "manual_required"
```

이 규칙을 `not_vulnerable` 근거로 사용할 수 있는 조건은 모두 충족해야 한다.

1. 한 endpoint와 한 보안 속성으로 범위가 좁다.
2. 서버 측 방어 코드가 긍정적으로 확인된다. 단순한 pattern 부재는 근거가 아니다.
3. 실제 값, DB 상태, 로그인 사용자 조합, mode 분기에 따라 의미가 바뀌지 않는다.
4. `scope`에 source가 증명한 속성만 쓴다.

### profile 필요값

현재 R3 source-assisted check에 필요한 profile 값은 배포된 앱 소스 루트 하나다.

```yaml
source_root: "/var/www/html/care"
```

이 값은 HTTP base URL, 계정, DB 연결값과 다르며, checker가 source evidence를 읽을 WEB VM의 코드 경로다. 07·09·10·11·12·13은 이 값만으로 source evidence를 만들 수 있다. 12·13은 YAML `variants`의 named pattern set으로 vuln/safe code 흔적을 따로 기록한다.

07·09는 현재 파일에 긍정 방어 근거가 없어 `manual_required`로 남긴다. 12·13 variant 기능은 PHP AST나 조건문 block을 해석하지 않는다. 지정한 pattern 묶음이 모두 같은 source set에 있는지만 확인하며, `variant_status: manual_required`를 강제한다.

향후 12·13에 branch별 자동 runtime verdict가 꼭 필요해지면 다음 중 적어도 하나가 추가로 필요하다.

```text
- vulnerable pattern도 all-match를 요구하는 vulnerable_match: all
- file별로 pattern을 묶는 per_file_patterns
- profile이 검사 대상의 vuln/safe branch를 명시하는 source_variant 또는 branch selector
```

이는 R3 source evidence 범위를 넘으므로 현재 goal에서는 구현하지 않는다.

### R3 구현 순서

1. 11번의 회원 수정 endpoint session subject binding source check를 추가했고, WEB VM run `20260622-014631-686408`에서 `member/modifyModel.php`의 두 pattern을 확인했다. 전체 status는 manual step 때문에 `manual_required`이며, A/B IDOR은 R4에 남긴다.
2. 같은 방식으로 회원 탈퇴 endpoint를 별도 source step으로 추가할지 검토한다. 두 endpoint를 한 pattern 묶음으로 합쳐 판정하지 않는다.
3. 07·09 source evidence check를 추가했고, WEB VM에서 defense/helper pattern 부재를 기록했다. pattern 부재를 `vulnerable`로 바꾸지 않는다.
4. 12·13 named source variant rule을 추가했고, local source fixture에서 각 vuln/safe pattern set이 일치하는지 확인했다. WEB VM evidence와 R4 runtime은 남긴다.

11번 check의 `required_mode`는 `safe-active`다. 현재 포함된 manual step과 source step은 HTTP 요청을 보내지 않으므로 `--confirm-state-changing`이 필요하지 않다. 다만 manual step의 `manual_required`가 source step의 `not_vulnerable`보다 높은 우선순위로 병합되므로, 최종 check status는 의도적으로 `manual_required`다. source evidence는 findings와 evidence 파일에서만 확인한다.

## 9. 출력물 설계

| 출력물 | 내용 |
|---|---|
| `report.md` | Obsidian/보고서용 Markdown 요약 |
| `result.json` | 항목별 status, mode, evidence path, 판정 근거, conditions, scope |
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
| `error` | 요청 실패 또는 실행 오류 |

`conditions`와 `scope`는 status가 아니다. 예를 들어 DB-backed primary route가 timeout 또는 예상 밖 응답으로 신뢰 불가하고 fallback route가 방어 근거를 확인하면 `status: not_vulnerable`은 유지하되, `conditions: [db_backed_primary_unavailable, fallback_used]`, `scope: db_independent_proof_only`를 함께 기록한다. 실제 DB preflight로 장애를 확인한 경우에만 `db_unavailable`을 사용한다.

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
