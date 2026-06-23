---

type: project-note  
topic: security-project  
status: draft  
created: 2026-06-22  
project: KISA Web Application 진단 스크립트  
tags:

- 보안교육
    
- 팀프로젝트
    
- 웹보안
    
- KISA
    
- AI-assisted
    
- evidence
    
- diagnostic-framework
    

---
# KISA Web Application 진단 스크립트 방향 전환 노트

## 1. 한 줄 결론

기존 목표였던 **“KISA Web Application 완전 자동 진단 스크립트”**는 실무적으로도 이론적으로도 과하게 넓다.

현재 프로젝트는 다음 방향으로 전환하는 것이 더 현실적이다.

```text
KISA Web Application 항목별 evidence를 구조화해 수집하고,
AI가 오탐 분석·판정 보조·후속 검증 설계·보고서화를 돕는
AI-assisted 진단 프레임워크
```

즉, 스크립트가 모든 취약점을 최종 판정하는 구조가 아니라:

```text
checker.py
= deterministic evidence collector

AI
= adaptive analyst / false-positive reviewer / next-step planner / report drafter

사람
= state-changing 승인 / 실제 환경 조작 / 최종 판정 책임자
```

이 구조로 재정의한다.

---

## 2. 왜 이런 전환이 나왔는가

### 2.1 최초 목표

처음 목표는 대략 다음이었다.

```text
KISA Web Application 01~21 항목을 기준으로
CARE 웹앱을 자동 또는 반자동으로 진단하고,
request/response evidence와 보고서를 생성하는 Python checker를 만든다.
```

구조는 다음과 같이 잡았다.

```text
profile -> check -> request -> evidence -> report
```

그리고 핵심 원칙은 다음이었다.

```text
checker.py에는 CARE 전용 값을 넣지 않는다.
CARE는 첫 target profile일 뿐이다.
KISA 항목은 check YAML에 둔다.
payload는 payload 파일에 둔다.
판정 기준은 evidence rule로 둔다.
```

이 설계는 여전히 유효하다.

다만 시간이 지나면서 “완전 자동 판정”이라는 목표가 점점 부정확해졌다.

---

## 3. 시행착오 요약

## 3.1 v0: pipeline 검증

처음에는 전체 21개 항목을 구현하지 않고, 최소 pipeline만 검증했다.

```text
profile -> check -> request -> evidence -> report
```

v0에서 확인한 것은 “취약점 진단이 완성됐다”가 아니라 다음이었다.

```text
- profile을 읽는다.
- check YAML을 읽는다.
- HTTP 요청을 만든다.
- request/response evidence를 남긴다.
- result.json과 report.md를 만든다.
- 허용되지 않은 mode는 실행하지 않는다.
```

이 단계의 의미:

```text
진단기 완성본이 아니라 evidence collector의 뼈대 확인.
```

---

## 3.2 v1: 안전한 자동 점검 항목 추가

다음은 비교적 안전한 항목을 추가했다.

```text
03 디렉터리 인덱싱
04 에러 페이지
05 정보 노출
15 파일 다운로드
16 세션 관리
17 평문 전송
19 관리자 페이지 노출
21 불필요한 Method
```

이때 얻은 교훈은 다음이다.

```text
자동화가 쉬운 항목도 HTTP status만으로 판정하면 오탐이 생긴다.
```

특히 15 파일 다운로드에서 문제가 드러났다.

---

## 3.3 v2: attack-active와 상태 변경 후보

v2에서는 더 공격성 있는 항목을 준비했다.

```text
02 SQL Injection
06 XSS
07 CSRF
09 약한 비밀번호 정책
10 불충분한 인증 절차
11 불충분한 권한 검증
14 악성 파일 업로드
20 자동화 공격
```

그러나 곧 문제가 드러났다.

```text
DB가 꺼져 있거나 baseline route가 500이면,
payload 결과가 취약 증거인지 일반 장애인지 구분할 수 없다.
```

02 SQL Injection에서 baseline부터 500이 나왔을 때 처음에는 vulnerable로 오판했다.

이때 얻은 교훈:

```text
baseline이 이미 실패한 상태에서는 payload 결과를 취약 증거로 보면 안 된다.
```

그래서 baseline 500 false positive를 막는 보정이 들어갔다.

---

## 3.4 V.db: DB 의존도 축 추가

단순히 v1/v2/v3처럼 구현 순서만으로는 부족했다.

웹앱 항목은 실행 위험도뿐 아니라 DB 의존도를 함께 봐야 했다.

분류는 다음과 같이 잡았다.

```text
DB-independent
= DB 없이도 신뢰성 있게 점검 가능

DB-backed recommended
= DB 없이 proof route나 source evidence로 일부 확인 가능하지만,
  실제 기능의 최종 판정으로 승격하면 안 됨

DB-required
= DB, 세션, fixture, 상태 저장이 없으면 원래 항목 진단 의미가 크게 떨어짐
```

핵심 원칙:

```text
fallback 결과를 원래 기능의 최종 안전 판정으로 승격하지 않는다.
status는 유지하되 conditions와 scope로 의미를 제한한다.
```

예:

```text
status: not_vulnerable
conditions: [db_backed_primary_unavailable, fallback_used]
scope: db_independent_proof_only
```

이 의미:

```text
DB 없는 proof route에서는 방어 근거가 확인됐지만,
DB-backed 원래 CARE 기능은 아직 판정하지 못했다.
```

---

## 3.5 R1/R2/R3 재정렬

기존 v1/v2/v3은 실패한 계획이 아니라, 단순한 1차 로드맵이었다.

하지만 V.db 이후에는 로드맵을 다시 잡았다.

```text
R0: 기준선 고정
R1: DB-independent 중심 자동 점검 안정화
R2: DB 없이 가능한 attack-active 항목 안정화
R3: source-assisted fallback 확장
R4: DB/세션/fixture 기반 runtime 검증
R5: 통합 실행과 보고서 품질 정리
```

이 재정렬의 의미:

```text
번호순 구현이 아니라,
DB 의존도와 실행 위험도 기준으로 진행한다.
```

---

## 3.6 R1 결과

R1에서는 safe-active 중심 항목을 실제 WEB VM에서 실행했다.

대략 결과:

```text
03 디렉터리 인덱싱: not_vulnerable
04 에러 페이지: not_vulnerable
05 정보 노출: inconclusive
15 파일 다운로드: vulnerable
16 세션 관리: inconclusive
17 평문 전송: vulnerable
19 관리자 페이지 노출: not_vulnerable
21 불필요한 Method: not_vulnerable
```

해석:

```text
03, 04, 19, 21은 비교적 선명했다.
17은 HTTP 환경이라 vulnerable이 맞다.
05와 16은 증거 부족으로 inconclusive가 자연스럽다.
15는 이후 false positive 가능성이 제기됐다.
```

---

## 3.7 R2 결과

R2에서는 DB 없이 가능한 attack-active 항목을 안정화했다.

### 06 XSS

`board_search`가 DB/timeout으로 신뢰 불가할 때, DB-less reflected proof route를 fallback으로 실행했다.

결과:

```text
06 XSS: not_vulnerable
scope: db_independent_proof_only
```

의미:

```text
proof route에서는 escaping 근거가 확인됐다.
하지만 board_search/stored XSS 전체 안전 판정은 아니다.
```

### 08 SSRF

controlled loopback proof URL을 보냈고, 응답 body에서 차단 문구를 확인했다.

결과:

```text
08 SSRF: not_vulnerable
근거: "허용되지 않은 요청 대상입니다."
```

의미:

```text
controlled loopback SSRF proof는 차단됐다.
내부망 스캔이나 모든 SSRF 우회 방식을 검증한 것은 아니다.
```

---

## 3.8 R3 결과

R3에서는 source-assisted fallback을 확장했다.

대상:

```text
07 CSRF
09 약한 비밀번호 정책
10 불충분한 인증 절차
11 불충분한 권한 검증
12 취약한 비밀번호 복구 절차
13 프로세스 검증 누락
```

교훈:

```text
source evidence는 runtime verdict가 아니다.
source pattern이 있다는 것은 보조 근거일 뿐이다.
pattern 부재만으로 취약을 확정하면 안 된다.
```

예:

```text
07 CSRF:
CSRF token pattern 0개 확인.
하지만 실제 cross-site 상태 변경을 검증하기 전까지 vulnerable 확정 금지.

10 불충분한 인증 절차:
currentPw input, POST currentPw, DB 재확인 pattern 확인.
하지만 실제 수정 차단 여부는 R4 runtime 필요.

12/13:
vulnerable branch와 safe branch source pattern이 모두 존재.
따라서 source만으로 vulnerable/not_vulnerable 단일 판정 금지.
```

---

## 3.9 R4 진입

R4 목표는 다음이었다.

```text
DB·세션·fixture 기반 runtime 진단을 generic checker workflow로 구축한다.
```

Pass 1에서는 다음을 구현했다.

```text
workflow_probe
run_id 기반 fixture 변수
setup/probe/verify/cleanup sequence
session 유지
assertion
extract
context 변수
when 조건
outcome별 set_context
evidence redaction
fixture_ledger.json
cleanup 실패 처리
stdlib fallback cookie jar
mock regression
```

R4의 핵심은:

```text
manual_required를 억지로 없애는 것이 아니라,
실제 runtime 근거를 생성할 수 있는 fixture/cleanup 계약을 만드는 것.
```

---

## 4. 결정적 전환점: manual_required가 너무 많다

전체 attack-active 실행 결과에서 다음처럼 manual_required가 많이 나왔다.

```text
06 XSS: manual_required
07 CSRF: manual_required
09 약한 비밀번호 정책: manual_required
10 불충분한 인증 절차: manual_required
11 불충분한 권한 검증: manual_required
12 취약한 비밀번호 복구 절차: manual_required
13 프로세스 검증 누락: manual_required
```

처음에는 이것이 실패처럼 보였다.

질문:

```text
이럴 거면 진단 스크립트가 맞나?
manual을 안 하려면 결국 하드코딩해야 하는 것 아닌가?
웹 앱 진단 스크립트 자체가 불가능한 것 아닌가?
```

이 질문이 방향 전환의 출발점이었다.

---

## 5. manual_required에 대한 재해석

manual_required는 모두 같은 의미가 아니었다.

### 5.1 미완성에 가까운 manual_required

아래 항목은 fixture가 들어가면 자동화 가능하다.

```text
09 약한 비밀번호 정책
10 불충분한 인증 절차
12 취약한 비밀번호 복구 절차
13 프로세스 검증 누락
```

이들은 본질적으로 수동이라기보다:

```text
로그인 세션
임시 계정
변경 전/후 비교
cleanup
fixture ledger
```

이 없어서 manual로 남은 것이다.

### 5.2 조건부 manual_required

아래 항목은 앱 문맥에 따라 자동화 가능성이 달라진다.

```text
07 CSRF
11 불충분한 권한 검증
14 악성 파일 업로드
18 쿠키 변조
20 자동화 공격
```

예:

```text
11 권한 검증은 A/B 계정과 private object가 있어야 의미 있다.
14 파일 업로드는 게시글/파일 cleanup 계약이 있어야 한다.
20 자동화 공격은 destructive-risk라 제한적으로만 수행해야 한다.
```

### 5.3 정상적인 manual_required

일부 항목은 최종적으로 manual이나 AI review queue로 남아도 된다.

```text
업무 흐름 판단
브라우저 실행 증거
권한 모델 해석
위험한 반복 요청
운영 정책 확인
```

이 영역은 고정 스크립트보다 사람이 판단해야 한다.

---

## 6. 15 파일 다운로드 false positive가 준 교훈

15번 파일 다운로드는 매우 중요한 전환점이었다.

### 6.1 현상

checker는 15번을 vulnerable로 판정했다.

하지만 CARE의 `download.php`를 보면 방어 코드가 들어가 있었다.

확인된 방어 요소:

```text
- 로그인 세션 확인
- 파일명에 /, \, %, 널바이트, .. 차단
- 허용 문자 whitelist
- realpath로 최종 경로 정규화
- 다운로드 디렉터리 내부인지 확인
- DB에 등록된 filename인지 prepared statement로 확인
- 통과한 경우에만 Content-Disposition attachment와 readfile 실행
- 취약 원본 코드는 주석 처리
```

### 6.2 오판 원인

checker의 rule은 대략 다음이었다.

```yaml
vulnerable_statuses:
  - 200
status_only_vulnerable: true
```

즉 HTTP 200이면 곧바로 vulnerable로 봤다.

하지만 `download.php`는 비로그인 상태에서 다음처럼 JS redirect를 200으로 반환할 수 있다.

```php
echo "<script>location.href='/member/login.php';</script>";
exit;
```

따라서:

```text
HTTP 200 == 파일 다운로드 성공
```

이 가정이 틀렸다.

### 6.3 교훈

```text
HTTP status만으로 웹앱 취약점을 판정하면 오탐이 쉽게 생긴다.
```

정확한 판정에는 다음이 필요하다.

```text
status
header
body
redirect 방식
login state
source code
DB state
expected behavior
```

이 지점에서 고정 스크립트의 한계가 명확해졌다.

---

## 7. “완전 범용 웹 앱 진단 스크립트”는 가능한가

결론:

```text
범용 웹앱 스캐너는 가능하다.
완전 자동으로 모든 취약점을 오탐 없이 판정하는 범용 스크립트는 사실상 불가능하다.
```

이유:

웹앱 취약점에는 test oracle 문제가 있다.

즉, 단순히 요청을 보내는 것보다 어려운 질문이 있다.

```text
이 응답이 진짜 취약 증거인가?
정상 redirect인가?
로그인 실패인가?
업무적으로 허용된 동작인가?
A 사용자가 B 사용자의 객체에 접근한 것인가?
상태 변경이 실제로 일어났는가?
성공 문구와 실패 문구는 무엇인가?
cleanup은 가능한가?
```

이 답은 앱마다 다르다.

따라서 완전 범용 자동 판정기는 현실성이 낮다.

---

## 8. 실무에서는 어떻게 하는가

실무 웹앱 진단은 도구 한 방으로 끝나지 않는다.

보통 다음처럼 진행한다.

```text
1. 범위와 권한 정의
2. 테스트 계정 확보
3. 자동 스캐너 실행
4. 로그인 세션 설정
5. 수동 탐색과 고위험 기능 식별
6. 취약점별 재현
7. request/response/source/log evidence 수집
8. 오탐 제거
9. 조치 후 재검증
10. 보고서 작성
```

즉 실무에서도:

```text
자동 스캔 + 수동 검증 + evidence 해석 + 보고서화
```

가 기본이다.

따라서 현재 프로젝트도 완전 자동 스캐너가 아니라:

```text
AI-assisted evidence-based diagnostic framework
```

로 잡는 편이 더 실무적이다.

---

## 9. AI 연계 발상의 논리

### 9.1 출발점

사용자의 발상은 다음에서 나왔다.

```text
이럴 바에 그냥 통째로 AI에게 던지면 되는 것 아닌가?
AI는 능동적으로 source, response, result, log를 같이 보고 판단할 수 있지 않나?
```

이 발상은 즉흥적이지만 논리적으로 강하다.

고정 스크립트가 힘든 부분은 다음이다.

```text
문맥 해석
오탐 제거
source와 runtime evidence 비교
다음 검증 설계
보고서 문장화
```

이것들은 AI가 상대적으로 잘하는 영역이다.

반대로 스크립트가 잘하는 영역은 다음이다.

```text
재현 가능한 요청 실행
run_id별 evidence 저장
mode gate
fixture ledger
cleanup 기록
raw request/response 보존
```

따라서 역할 분리 구조가 나온다.

```text
스크립트는 증거 수집기.
AI는 증거 해석기.
사람은 승인자이자 최종 책임자.
```

---

## 10. 새 방향: AI-assisted evidence framework

새 목표:

```text
KISA Web Application 항목별 evidence를 구조화해 수집하고,
AI가 오탐 분석·판정 보조·후속 검증 설계·보고서화를 돕는 프레임워크.
```

이 방향은 기존 결과물을 버리지 않는다.

|기존 구성|새 방향에서 역할|
|---|---|
|`checker.py`|deterministic evidence collector|
|`profiles/care.yml`|target profile|
|`checks/*.yml`|KISA 항목별 probe/template|
|`payloads/*.yml`|controlled input set|
|`evidence/<run_id>`|AI가 읽을 evidence bundle|
|`result.json`|raw status input|
|`report.md`|보고서 초안 source|
|`fixture_ledger.json`|state-changing 안전 근거|
|`manual_required`|AI review queue|
|`inconclusive`|evidence 부족 또는 rule 보정 후보|

---

## 11. 새 구조

```text
profiles/care.yml
       ↓
checks/*.yml
       ↓
checker.py
       ↓
evidence/<run_id>/
  - result.json
  - report.md
  - run.log
  - raw request/response
  - fixture_ledger.json
       ↓
ai_review_bundle.md
       ↓
AI analyst pass
       ↓
ai_review.json / ai_review.md
       ↓
human-approved final report
```

---

## 12. AI review layer의 역할

AI는 최종 책임자가 아니다.

AI가 맡을 일:

```text
- raw_status 검토
- false positive 가능성 분석
- source와 response 비교
- check rule 보정안 제시
- 후속 실행 명령 제안
- 보고서 문장 초안 작성
- manual_required 항목의 다음 검증 절차 설계
```

AI가 하면 안 되는 일:

```text
- 승인 없이 state-changing 실행
- 승인 없이 계정 생성/삭제
- 승인 없이 비밀번호 변경
- 승인 없이 파일 업로드
- 승인 없이 게시글 작성
- 승인 없이 destructive-risk 실행
- evidence 없이 최종 안전 판정
```

---

## 13. AI review output 설계

AI 판단도 artifact로 남겨야 한다.

예상 출력:

```json
{
  "check_id": "15",
  "raw_status": "vulnerable",
  "review_status": "not_vulnerable",
  "confidence": "medium-high",
  "reason": "HTTP 200 alone is insufficient. The response appears to be login redirect or guarded normal download path. Source validates filename, canonical path, and DB registration before readfile.",
  "evidence_refs": [
    "evidence/<run_id>/15_...response.txt",
    "care/center/download.php",
    "checks/15_file_download.yml"
  ],
  "false_positive_risk": "high",
  "followup_command": "Inspect response headers for Content-Disposition and body for login redirect.",
  "report_sentence": "초기 자동 판정은 HTTP 200에 기반한 취약 의심이었으나, 소스와 응답 검토 결과 파일명 검증 및 DB 등록 파일 대조가 적용되어 오탐 가능성이 높다고 판단했다."
}
```

필드:

```text
check_id
raw_status
review_status
confidence
reason
evidence_refs
false_positive_risk
required_followup
suggested_rule_patch
report_sentence
```

---

## 14. status 체계 재정의

현재 status는 유지한다.

```text
vulnerable
not_vulnerable
manual_required
not_applicable
skipped_by_mode
inconclusive
error
ready
```

단, AI layer에서는 다음을 추가한다.

```text
raw_status
review_status
confidence
review_reason
evidence_refs
next_action
```

중요:

```text
raw_status는 checker의 1차 판정이다.
review_status는 AI/사람 검토 후 판정이다.
final_status는 사람이 승인한 보고서 판정이다.
```

---

## 15. manual_required의 새 의미

기존에는 manual_required가 실패처럼 보였다.

전환 후 의미:

```text
manual_required
= AI/사람이 evidence와 source를 함께 봐야 하는 review queue
= 또는 fixture workflow가 아직 없는 항목
```

단, 계속 manual로 남기면 안 되는 항목도 있다.

줄여야 하는 manual:

```text
09 약한 비밀번호 정책
10 불충분한 인증 절차
12 취약한 비밀번호 복구 절차
13 프로세스 검증 누락
```

남아도 되는 manual 또는 조건부 항목:

```text
07 CSRF
11 불충분한 권한 검증
14 악성 파일 업로드
18 쿠키 변조
20 자동화 공격
01 코드 인젝션 일부
```

---

## 16. R4는 버리지 않는다

방향을 AI-assisted로 바꿔도 R4는 유효하다.

오히려 R4는 다음 역할을 갖는다.

```text
AI가 "이 항목은 fixture runtime이 필요하다"고 판단하면,
checker가 승인 기반으로 fixture workflow를 실행한다.
```

R4의 목표를 다음처럼 좁힌다.

```text
R4 전체 자동화
```

가 아니라:

```text
R4-fixture baseline
= 임시 계정 생성 -> 로그인 -> 삭제 -> ledger -> redaction 확인
```

이후 순서:

```text
fixture lifecycle
-> 09
-> 10
-> 13
-> 12
```

절대 한 번에 하지 않는다.

---

## 17. 다음 실행 전략

### 17.1 즉시 할 일

먼저 15번 false positive를 정리한다.

```text
왜?
15번은 checker가 HTTP 200을 곧바로 vulnerable로 보는 문제를 드러냈다.
이는 AI review layer 필요성을 설명하는 핵심 사례다.
```

해야 할 일:

```text
1. evidence/<run_id>/15 response 확인
2. Content-Disposition attachment 여부 확인
3. login redirect 200 여부 확인
4. download.php source와 비교
5. checks/15_file_download.yml rule 보정
```

보정 방향:

```text
HTTP 200만으로 vulnerable 금지.
Content-Disposition attachment 또는 실제 proof body 확인 필요.
login redirect, download denied, invalid file name은 not_vulnerable 또는 inconclusive 처리.
```

### 17.2 다음 할 일

AI review bundle 기능 설계.

예상 파일:

```text
evidence/<run_id>/ai_review_bundle.md
```

포함 내용:

```text
- run summary
- raw status table
- suspicious checks
- each check's findings
- relevant request/response snippets
- source file refs
- check YAML snippet
- AI에게 물을 질문
```

### 17.3 이후 할 일

R4 fixture-first.

```text
register
-> login
-> delete
-> fixture_ledger 확인
-> redaction 확인
```

그 다음 09부터 단독 실행.

---

## 18. 프로젝트 보고서에서의 포장

기존 제목:

```text
KISA Web Application 자동 진단 스크립트
```

수정 제목 후보:

```text
KISA Web Application AI-assisted 진단 프레임워크
```

또는:

```text
KISA Web Application Evidence-based 진단 자동화 및 AI 검토 프레임워크
```

보고서 설명 문장:

```text
본 도구는 웹 취약점을 완전 자동으로 확정하는 스캐너가 아니라,
KISA Web Application 항목별 요청/응답/source evidence를 구조화해 수집하고,
AI를 활용해 오탐 가능성 분석, 판정 보조, 후속 검증 절차 설계, 보고서 초안 생성을 지원하는
AI-assisted evidence framework로 설계하였다.
```

중요한 방어 문장:

```text
AI는 최종 판정자가 아니라 evidence reviewer로 사용한다.
상태 변경이 있는 요청은 confirm gate와 사용자 승인 후 실행한다.
최종 취약/양호 판정은 request/response/source/ledger 근거를 사람이 검토해 확정한다.
```

---

## 19. 이 방향의 현실성 평가

### 19.1 실무적 가능성

높다.

실무 웹앱 진단도 자동 스캐너만으로 끝나지 않는다.

실무 흐름은 대체로 다음이다.

```text
scope 설정
인증 세션 설정
자동 스캔
수동 탐색
고위험 기능 식별
오탐 제거
재현
증적 수집
보고서화
조치 후 재검증
```

따라서 AI-assisted evidence framework는 실무 흐름과 충돌하지 않는다.

---

### 19.2 이론적 가능성

높다.

웹앱 진단의 어려움은 요청 생성보다 판정 oracle에 있다.

즉:

```text
이 응답이 취약 증거인지 아닌지
```

를 판단하는 데 앱 문맥이 필요하다.

AI는 이 문맥 판단에 강하고, 스크립트는 반복 가능 evidence 수집에 강하다.

따라서 두 역할을 분리하는 것은 이론적으로도 적절하다.

---

### 19.3 프로젝트 평가 가능성

오히려 좋아질 수 있다.

강점:

```text
- 완전 자동화의 한계를 인식했다.
- 오탐 사례를 직접 발견했다.
- evidence 기반 검토 구조로 방향을 바꿨다.
- 위험한 요청은 confirm gate로 제어한다.
- AI를 최종 판정자가 아니라 검토 보조자로 제한했다.
- 실무 진단 workflow와 유사하다.
```

위험:

```text
- AI가 다 해준다는 식으로 포장하면 신뢰도 하락
- evidence 없는 AI 판단을 보고서에 쓰면 안 됨
- state-changing을 AI가 자동 실행하면 위험
```

---

## 20. 최종 판단

방향 전환은 타당하다.

이 프로젝트의 핵심은 이제 다음이다.

```text
완전 자동 취약점 스캐너를 만들려다 실패한 것이 아니다.
웹앱 진단에서 완전 자동 판정이 왜 어려운지 직접 확인했고,
그 한계를 evidence collector + AI analyst + human approval 구조로 재설계했다.
```

이것이 이번 시행착오의 실제 학습 성과다.

---

## 21. 다음 Codex 전달용 요약

```text
목표를 KISA WebApp 완전 자동 진단기에서 AI-assisted evidence framework로 전환한다.

checker.py의 역할은 최종 판정기가 아니라 deterministic evidence collector다.
AI는 오탐 제거, source/response 비교, 후속 검증 설계, 보고서 초안 생성을 맡는다.
사람은 state-changing 승인과 최종 판정을 맡는다.

우선 15 파일 다운로드 false positive를 정리한다.
HTTP 200만으로 vulnerable 처리한 rule을 보정한다.
그 다음 evidence/<run_id>/ai_review_bundle.md 생성 기능을 설계한다.
R4는 버리지 않고 fixture-first로 재정렬한다.
09·10·12·13은 fixture runtime으로 줄여야 할 manual_required다.
07·11·14·18·20은 조건부/manual_required가 남아도 된다.

금지:
- AI 판단을 최종 판정으로 단정하지 않는다.
- 승인 없이 state-changing 실행하지 않는다.
- checker.py에 CARE 전용 분기를 넣지 않는다.
- evidence 없는 보고서 문장을 만들지 않는다.
```

---

## 22. 남은 질문

```text
1. AI review bundle을 checker.py가 자동 생성할 것인가, 별도 script로 만들 것인가?
2. ai_review.json을 사람이 직접 붙여 넣는 구조로 할 것인가, Codex/ChatGPT 출력물을 수동 저장할 것인가?
3. report.md에 raw_status와 review_status를 둘 다 표시할 것인가?
4. 15번은 not_vulnerable로 재분류할 것인가, inconclusive로 둘 것인가?
5. R4 fixture lifecycle은 09 check에 통합할 것인가, 별도 00_fixture_lifecycle check로 만들 것인가?
```