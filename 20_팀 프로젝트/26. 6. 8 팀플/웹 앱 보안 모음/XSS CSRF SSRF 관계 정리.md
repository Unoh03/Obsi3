---
type: project-note
topic: web-security
status: draft
created: 2026-06-14
tags:
  - 🏷️과목/웹보안
  - 🏷️주제/XSS
  - 🏷️주제/CSRF
  - 🏷️주제/SSRF
  - 🏷️상태/draft
---

# XSS CSRF SSRF 관계 정리

관련 노트:

- [[웹 취약점 - 06 XSS|웹 취약점 - 06 XSS]]
- [[웹 취약점 - 07 CSRF|웹 취약점 - 07 CSRF]]
- [[웹 취약점 - 08 SSRF|웹 취약점 - 08 SSRF]]

## 한 줄 결론

**XSS, CSRF, SSRF는 모두 웹 요청과 신뢰 경계를 악용한다는 점에서는 친척이다.**

하지만 SQL Injection과 LDAP Injection처럼 같은 형제는 아니다.

```text
XSS  = 브라우저가 사용자 입력을 코드로 해석하는 문제
CSRF = 피해자 브라우저가 인증된 상태로 원치 않는 요청을 보내는 문제
SSRF = 서버가 공격자가 지정한 주소로 요청을 보내는 문제
```

## 세 취약점의 핵심 차이

| 항목 | XSS | CSRF | SSRF |
|---|---|---|---|
| 정체 | Client-side code injection | Request forgery | Server-side request forgery |
| 악용되는 신뢰/검증 실패 지점 | 브라우저가 입력을 코드로 해석함 | 서버가 피해자 browser의 session 요청을 사용자 의도로 믿음 | 서버가 사용자 입력 URL을 안전한 요청 대상으로 믿음 |
| 요청을 보내는 주체 | 피해자 브라우저 안에서 실행된 script | 피해자 브라우저 | 웹 서버 |
| 공격자가 노리는 것 | 브라우저에서 script 실행 | 피해자 권한으로 상태 변경 | 서버 위치에서 내부/외부 자원 요청 |
| 핵심 조건 | 입력값이 HTML/JS로 해석됨 | 로그인 세션 + 상태 변경 endpoint + 추가 검증 없음 | 사용자 입력 URL/주소를 서버가 검증 없이 요청 |
| CARE 예시 | 게시글 본문 `<script>` 실행 | 게시글 form으로 `/member/modifyModel.php` POST | 실습용 `/vuln/ssrf/fetch.php?url=...` |
| 정석 방어 | 출력 인코딩, 입력 검증, 허용 태그 제한 | CSRF token 서버 검증, Origin/Referer, SameSite, 재인증 | URL allowlist, 내부 IP 차단, scheme 제한, redirect 제한, egress 통제 |

## 외부 기준 팩트체크 반영

OWASP와 CWE 기준으로 보면 이 노트의 큰 방향은 맞다. 다만 표현은 조금 더 정확하게 잡는 편이 좋다.

| 항목 | 보정 |
|---|---|
| XSS | CWE-79 기준으로 injection 계열에 넣을 수 있다. 단, 해석기가 SQL/LDAP가 아니라 브라우저라는 점을 구분해야 한다. |
| CSRF | 단순히 "요청 위조"라고만 보면 부족하다. 서버가 피해자 browser의 인증된 요청을 사용자 의도로 오인하는 문제다. |
| SSRF | 서버가 사용자 입력 URL을 대신 요청한다는 점이 핵심이다. CWE-918은 이를 서버가 의도치 않은 proxy/intermediary처럼 동작하는 문제로 본다. |
| CSRF와 SSRF 관계 | 둘 다 request forgery처럼 보이지만, 더 정확히는 신뢰받는 주체를 대리자로 악용하는 confused deputy 계열 친척이다. |
| XSS와 CSRF 관계 | XSS는 CSRF 방어를 우회하거나 CSRF payload의 전달 경로가 될 수 있다. 그래서 XSS 방어는 CSRF의 보조 방어가 될 수 있지만, CSRF token 검증을 대체하지는 않는다. |

참고한 외부 기준:

- [OWASP XSS Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html)
- [OWASP CSRF Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html)
- [OWASP SSRF Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Server_Side_Request_Forgery_Prevention_Cheat_Sheet.html)
- [CWE-79: Cross-site Scripting](https://cwe.mitre.org/data/definitions/79.html)
- [CWE-352: Cross-Site Request Forgery](https://cwe.mitre.org/data/definitions/352.html)
- [CWE-918: Server-Side Request Forgery](https://cwe.mitre.org/data/definitions/918.html)
- [OWASP XXE Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/XML_External_Entity_Prevention_Cheat_Sheet.html)
- [OWASP Clickjacking Defense Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Clickjacking_Defense_Cheat_Sheet.html)
- [OWASP XS-Leaks Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/XS_Leaks_Cheat_Sheet.html)
- [PortSwigger: CORS](https://portswigger.net/web-security/cors)
- [PortSwigger: HTTP Host header attacks](https://portswigger.net/web-security/host-header)

## 관계를 어떻게 봐야 하나

### XSS와 CSRF

XSS와 CSRF는 가장 헷갈리기 쉽다.

이번 프로젝트에서도 CSRF form을 게시글에 넣었기 때문에 겉보기에는 XSS처럼 보였다. 하지만 최종 피해는 브라우저에서 alert가 실행되는 것이 아니라, **피해자 권한으로 회원정보 수정 요청이 처리되는 것**이었다.

```text
게시글에 form/script가 저장되고 실행됨
-> XSS/HTML 삽입 전달 경로

그 form이 피해자 세션으로 회원정보 수정 요청을 보냄
-> CSRF 피해
```

따라서 XSS 방어는 CSRF의 보조 방어가 될 수 있다. `center/view.php`에서 `htmlspecialchars()`로 게시글 내용을 출력하면 게시글 안의 `<form>`이 문자로 표시되어, 게시글을 통한 CSRF 전달 경로가 막힌다.

하지만 이것은 CSRF의 근본 방어가 아니다.

```text
XSS 방어
= 게시글에 심은 CSRF form/script 전달 경로를 막을 수 있음

CSRF 방어
= /member/modifyModel.php 같은 상태 변경 endpoint에서 요청 의도를 검증해야 함
```

그래서 CSRF의 정석 방어는 [[웹 취약점 - 07 CSRF|웹 취약점 - 07 CSRF]]의 `## 5. 조치 방안`이다.

### CSRF와 SSRF

CSRF와 SSRF는 이름처럼 둘 다 `Request Forgery`처럼 보이는 친척이다. 더 정확히는 신뢰받는 주체를 대리자로 악용하는 `confused deputy` 성격을 가진다.

공통점은 공격자가 직접 정상 권한을 가진 것이 아니라, **신뢰받는 주체에게 요청을 대신 보내게 만든다**는 점이다.

| 구분 | CSRF | SSRF |
|---|---|---|
| 대신 요청하는 주체 | 피해자 브라우저 | 웹 서버 |
| 신뢰의 근거 | 피해자 session cookie | 서버의 네트워크 위치와 권한 |
| 대표 피해 | 회원정보 변경, 글 작성, 삭제, 송금 | 내부망 접근, localhost 접근, metadata 접근 |
| 방어 위치 | 상태 변경 endpoint | 서버 측 URL 요청 기능과 네트워크 egress |

즉, CSRF와 SSRF는 같은 `forgery / confused deputy` 친척이지만 공격 무대가 다르다.

```text
CSRF: 브라우저야, 네 쿠키로 이 요청 좀 보내.
SSRF: 서버야, 네 위치에서 이 주소 좀 요청해.
```

### XSS와 SSRF

XSS와 SSRF는 셋 중 가장 멀다.

XSS는 브라우저의 HTML/JavaScript 해석 문제이고, SSRF는 서버가 사용자 입력 URL을 대신 요청하는 문제다. 둘 다 입력값 검증이 중요하지만, 실행 위치와 피해 지점이 다르다.

| 구분 | XSS | SSRF |
|---|---|---|
| 실행 위치 | 피해자 브라우저 | 웹 서버 |
| 위험한 입력 | HTML/JS로 해석될 문자열 | 서버가 요청할 URL, host, IP |
| 대표 방어 | 출력 인코딩 | 요청 대상 제한 |

## SQL Injection / LDAP Injection과 비교

SQL Injection, LDAP Injection, Command Injection은 같은 계열로 훨씬 가깝다.

```text
사용자 입력
-> 서버 측 해석기(SQL, LDAP, Shell)에 명령 일부로 섞임
-> 의도하지 않은 query/command 실행
```

XSS도 넓게 보면 injection 계열이지만, 해석기가 DB나 LDAP가 아니라 **브라우저**다.

CSRF와 SSRF는 injection보다 request forgery / confused deputy 쪽에 가깝다. 공격자가 명령어를 해석기에 섞는다기보다, 신뢰받는 주체가 요청을 보내게 만든다.

| 계열 | 포함하기 좋은 항목 |
|---|---|
| Injection | SQL Injection, LDAP Injection, Command Injection, XSS |
| Request Forgery / Confused Deputy | CSRF, SSRF |
| Session / Trust Abuse | CSRF, Session Hijacking, Cookie 변조 일부 |
| Server-side Network Abuse | SSRF |

## 이번 프로젝트에서 얻은 기준

### 1. XSS 방어는 CSRF 전달 경로를 막을 수 있다

06 XSS에서 `center/view.php`에 출력 인코딩을 적용하자 게시글 안의 `<script>`가 실행되지 않았다.

같은 이유로 07 CSRF에서 게시글 안의 `<form>`도 실제 form으로 렌더링되지 않고 문자로 출력되었다.

따라서 다음 문장은 맞다.

```text
XSS의 정석 방어법은 CSRF의 보조 방어법이 될 수 있다.
```

### 2. 하지만 CSRF 정석 방어는 token 검증이다

게시글 form 전달을 막아도 `/member/modifyModel.php`가 session cookie만 믿고 회원정보를 수정하면 근본 문제는 남는다.

CSRF는 상태 변경 endpoint에서 다음을 확인해야 한다.

| 방어 | 의미 |
|---|---|
| CSRF token | 정상 form에서 발급된 token이 요청에 포함됐는지 확인 |
| 서버 측 token 검증 | session token과 요청 token을 비교 |
| Origin / Referer 검증 | 허용된 출처에서 온 요청인지 확인 |
| SameSite cookie | cross-site 요청에서 cookie 자동 전송 범위 제한 |
| 재인증 | 회원정보 변경 같은 중요 작업에서 현재 비밀번호 등 추가 확인 |

### 3. SSRF는 서버가 요청하는 순간부터 위험하다

CARE 기본 기능에서는 자연 발생한 SSRF 지점이 확인되지 않았다. 그래서 08 SSRF에서는 실습용 `fetch.php`를 만들어 서버가 입력 URL을 요청하는 구조를 구성했다.

SSRF의 핵심 질문은 다음이다.

```text
사용자가 입력한 URL을 서버가 대신 요청하는가?
그 요청이 localhost, 내부망, metadata 같은 곳으로 갈 수 있는가?
```

AWS에서는 특히 위험하다. EC2는 외부 사용자가 직접 접근할 수 없는 VPC 내부 자원이나 metadata service에 접근할 수 있는 위치에 있기 때문이다.

## 보고서에 쓸 수 있는 짧은 문장

```text
XSS는 사용자 입력이 브라우저에서 코드로 실행되는 문제이고,
CSRF는 피해자의 인증된 브라우저가 상태 변경 요청을 보내게 되는 문제이며,
SSRF는 서버가 공격자가 지정한 주소로 요청을 보내는 문제이다.
```

```text
XSS 방어는 게시글에 삽입된 CSRF form/script 전달을 차단할 수 있으므로 CSRF의 보조 방어가 될 수 있다.
그러나 CSRF의 근본 방어는 상태 변경 endpoint에서 CSRF token을 검증하는 것이다.
```

```text
CSRF와 SSRF는 둘 다 request forgery처럼 보이지만,
더 정확히는 신뢰받는 주체를 대리자로 악용하는 confused deputy 계열 친척이다.
CSRF는 피해자 브라우저를 이용하고 SSRF는 서버를 이용한다.
```

## 헷갈리면 이 질문으로 분류한다

| 질문 | 예라고 답하면 |
|---|---|
| 사용자 입력이 브라우저에서 HTML/JS로 실행되는가? | XSS |
| 로그인된 사용자의 브라우저가 의도하지 않은 상태 변경 요청을 보내는가? | CSRF |
| 서버가 사용자 입력 URL/주소로 직접 요청을 보내는가? | SSRF |
| 사용자 입력이 SQL/LDAP/Shell query 문법으로 섞이는가? | Injection |

## 부록: 비슷한 주변 취약점

이 표는 엄밀한 CWE 계보표가 아니라, XSS / CSRF / SSRF를 공부할 때 같이 헷갈리기 쉬운 주변 취약점 묶음이다.

| 주변 취약점 | 가까운 축 | 왜 비슷한가 |
|---|---|---|
| HTML Injection | XSS | 사용자 입력이 HTML로 해석된다. script 실행까지 가면 XSS로 이어진다. |
| DOM XSS | XSS | 서버 응답보다 브라우저 JavaScript가 DOM에 입력을 넣는 방식에서 발생한다. |
| Client-side Template Injection | XSS | 브라우저 또는 client template engine이 사용자 입력을 template 문법으로 해석한다. |
| CORS Misconfiguration | XSS / CSRF 주변 | cross-origin 읽기 권한과 credential 처리가 잘못되면 다른 origin에서 민감 응답을 읽을 수 있다. 단, CORS 자체는 CSRF 방어책이 아니다. |
| XS-Leaks | CSRF / browser side-channel | cross-site 요청의 응답 차이를 직접 읽지 않고도 로그인 여부나 리소스 존재를 추론한다. |
| Clickjacking | CSRF 주변 | 사용자의 브라우저와 클릭 행동을 이용해 원치 않는 상태 변경을 유도한다. |
| XXE | SSRF 주변 | XML external entity를 통해 서버가 파일이나 내부 URL을 읽거나 요청하게 만들 수 있다. |
| Open Redirect / URL validation bypass | SSRF 보조/우회 | URL allowlist가 약하면 redirect나 parsing 차이로 내부 목적지 요청까지 이어질 수 있다. |
| Host Header Injection | SSRF / cache poisoning 주변 | 서버가 `Host` header를 신뢰하면 password reset poisoning, cache poisoning, routing-based SSRF로 이어질 수 있다. |
| DNS Rebinding | CSRF / SSRF 중간 | 브라우저를 이용해 내부망 주소로 요청하게 만드는 공격으로, 브라우저와 내부 네트워크 신뢰 경계를 동시에 건드린다. |

## BAS 비유법

RF 계열 취약점은 공격자가 직접 접근하지 못하는 대상에 대해, 신뢰받는 중간 주체를 통과시켜 요청을 보내게 만든다는 점에서 Bastion 흐름과 닮았다.

```text
정상 Bastion:
외부 관리자 -> Bastion Host -> 내부 서버

RF 계열:
외부 공격자 -> 신뢰받는 대상 -> 보호된 기능/내부 자원
```

| 구분 | 흐름 | 신뢰되는 지점 |
|---|---|---|
| Bastion | 외부 사용자 -> Bastion -> 내부 서버 | 내부망이 Bastion을 허용된 접속 경로로 신뢰 |
| CSRF | 공격자 페이지 -> 피해자 browser -> 웹 서버 | 웹 서버가 피해자 session cookie를 정상 사용자 의도로 신뢰 |
| SSRF | 공격자 입력 -> 취약한 웹 서버 -> 내부망 / localhost / metadata | 내부 자원이 웹 서버의 네트워크 위치와 권한을 신뢰 |

다만 Bastion은 원래 의도된 안전한 접근 경로이고, RF의 중간 주체는 공격자가 오용한 대리자다.

```text
Bastion = 의도된 중계 지점
RF 대상 = 원래 그런 중계를 하라고 만든 게 아닌데 공격자가 억지로 중계하게 만든 지점
```
