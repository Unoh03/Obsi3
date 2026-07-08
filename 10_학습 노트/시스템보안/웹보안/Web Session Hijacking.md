---
type: concept
topic: web-security
source: 5-20_웹보안.pdf
source_pages:
  - 80
  - 81
  - 82
status: active
created: 2026-05-22
reviewed: 2026-07-08
aliases:
  - 세션 하이재킹
  - Web Session Token 탈취
  - Session Hijacking
  - Session Token 탈취
  - 세션 토큰 탈취
tags:
  - 🏷️과목/웹보안
  - 🏷️주제/Session
  - 🏷️주제/Session-Hijacking
  - 🏷️상태/active
---

# Web Session Hijacking

source: [[40_자료/강의 자료/5-20_웹보안.pdf|5-20 웹보안]], p.80-82

## 한 줄 요약

Web Session Hijacking은 **다른 사용자의 Session Token을 얻어 서버에 그 사용자처럼 보이게 요청을 보내는 공격**이다.

서버가 `Session Token을 가진 요청 = 로그인된 사용자`로 판단하는 구조에서는 토큰이 곧 신분증처럼 동작한다. 그래서 비밀번호를 몰라도 Session Token을 탈취하면 현재 로그인 중인 사용자의 권한을 획득할 수 있다.

---

## 먼저 잡아야 할 핵심

- Session Token은 사용자가 로그인한 뒤 서버가 사용자를 구분하기 위해 쓰는 식별자다.
- 서버는 보통 매 요청마다 Cookie에 들어온 Session Token을 보고 사용자를 식별한다.
- 세션과 쿠키의 기본 구조는 [[10_학습 노트/시스템보안/웹보안/세션과 쿠키|세션과 쿠키]]를 먼저 본다.
- Session Hijacking은 비밀번호를 맞히는 공격이 아니라 **이미 발급된 세션 식별자를 훔쳐 쓰는 공격**이다.
- PDF는 Session Token 획득 경로로 `Sniffing`과 `XSS`를 든다.
- XSS는 세션 탈취의 수단이 될 수 있으므로 [[10_학습 노트/시스템보안/웹보안/XSS|XSS]]와 연결해서 봐야 한다.

---

## PDF 내용 분해

| page | PDF 핵심 | 정리 |
|---|---|---|
| p.80 | Web Session Hijacking 정의와 영향 | 다른 사용자의 Session Token을 획득해 세션을 가로챈다. 영향은 로그인 중인 사용자의 권한 획득이다. |
| p.81 | 공격 절차 | Victim이 세션을 만들고, Attacker가 토큰을 얻은 뒤, Victim의 토큰으로 사이트를 이용한다. |
| p.82 | Session Token 획득 방법 | HTTP Request sniffing 또는 XSS로 Session Token을 얻을 수 있다. |

---

## 공격 흐름

```text
1. Victim이 정상 로그인한다.
2. Web Server가 Victim에게 Session Token을 발급한다.
3. Attacker가 Sniffing, XSS 등으로 Victim의 Session Token을 얻는다.
4. Attacker가 그 Token을 요청에 넣어 Web Server에 보낸다.
5. 서버가 Token만 보고 Victim으로 판단하면 Attacker가 Victim 권한을 얻는다.
```

핵심은 서버가 “요청을 보낸 사람이 누구인가”를 직접 보는 것이 아니라, 요청에 들어 있는 세션 식별자를 보고 판단한다는 점이다.

---

## Session Token 획득 경로

| 경로 | PDF 설명 | 정확한 해석 |
|---|---|---|
| Sniffing | HTTP Request 패킷에 포함된 Session Token 획득 | 암호화되지 않은 HTTP에서는 Cookie header가 네트워크에 평문으로 보일 수 있다. |
| XSS | Victim 브라우저 HTML DOM에 저장된 Session Token 획득 | 세션 쿠키가 JavaScript에서 읽히면 `document.cookie`로 탈취될 수 있다. `HttpOnly`가 없을 때 위험이 커진다. |

Sniffing은 네트워크 경로에서 보는 공격이고, XSS는 브라우저에서 실행되는 스크립트가 사용자의 인증 상태를 악용하는 공격이다. 둘 다 결과적으로는 Session Token을 얻는 데 연결된다.

---

## 방어 관점

| 방어 | 막는 지점 | 의미 |
|---|---|---|
| HTTPS/TLS 전체 적용 | Sniffing | 세션 쿠키가 네트워크에서 평문으로 노출되는 것을 줄인다. 로그인 화면만 HTTPS로 두고 이후 HTTP로 내려오면 부족하다. |
| Cookie `Secure` | Sniffing | 브라우저가 해당 쿠키를 HTTPS 연결에서만 보내도록 한다. |
| Cookie `HttpOnly` | XSS를 통한 cookie 읽기 | JavaScript가 쿠키를 직접 읽지 못하게 한다. 단, XSS 자체를 없애는 것은 아니다. |
| Cookie `SameSite` | Cross-site 요청 악용 | CSRF 방어에 특히 중요하지만, 세션 쿠키 전송 범위를 줄이는 데도 도움이 된다. |
| Session ID 재발급 | Session Fixation/권한 변경 | 로그인 직후나 권한 상승 시 기존 세션 식별자를 폐기하고 새로 발급한다. |
| 서버 측 세션 저장 | Token 의미 보호 | 클라이언트에는 식별자만 두고 권한/사용자 정보는 서버에서 관리한다. |
| 재인증 요구 | 탈취 후 피해 축소 | 민감한 작업 전에 비밀번호나 MFA를 다시 요구한다. |

PDF의 “Session과 IP를 묶어서 서버 측에서 인증”은 같은 토큰이 다른 IP에서 갑자기 쓰이는 상황을 줄이려는 의도다. 다만 모바일망, NAT, 프록시, 회사/학교 공용망에서는 IP가 바뀌거나 공유될 수 있으므로 운영 환경에서는 보조 신호로 보는 편이 안전하다.

---

## 이 vault에서 쓰는 법

- 세션 구조가 헷갈리면 [[10_학습 노트/시스템보안/웹보안/세션과 쿠키|세션과 쿠키]]를 먼저 본다.
- 이 노트는 `5-20_웹보안.pdf` p.80-82의 stable concept note로 쓴다.
- XSS로 Session Token을 훔쳐 재사용하는 실습 증거는 [[10_학습 노트/시스템보안/웹보안/XSS를 이용한 Session Token 탈취 실습|XSS를 이용한 Session Token 탈취 실습]]에 둔다.
- Sniffing/평문 HTTP 쪽 노출은 [[10_학습 노트/시스템보안/네트워크보안/HTTP 로그인 평문 노출|HTTP 로그인 평문 노출]]에서 본다.
- XSS 자체의 원리와 방어는 [[10_학습 노트/시스템보안/웹보안/XSS|XSS]], [[10_학습 노트/시스템보안/웹보안/실무형 XSS 방어|실무형 XSS 방어]], [[10_학습 노트/시스템보안/웹보안/HTML 인코딩|HTML 인코딩]]으로 내려간다.

---

## 오해하기 쉬운 지점

| 오해 | 정정 |
|---|---|
| 비밀번호가 안전하면 세션 탈취도 막힌다 | 세션 탈취는 로그인 이후의 토큰을 노린다. 비밀번호와 별개다. |
| HTTPS만 쓰면 XSS 세션 탈취도 막힌다 | HTTPS는 네트워크 도청을 줄이지만, 브라우저 안에서 실행되는 XSS를 막지는 못한다. |
| `HttpOnly`면 XSS가 의미 없어진다 | 쿠키 직접 읽기는 막지만, XSS로 사용자 권한 요청을 대신 보내는 문제는 남을 수 있다. |
| Session Token은 그냥 랜덤 문자열이다 | 클라이언트에는 랜덤 식별자처럼 보여야 하지만, 그 의미와 권한은 서버 쪽 세션 저장소가 결정한다. |

---

## 실무 / TMI

- 세션 쿠키 이름은 가능하면 `__Host-` prefix를 쓰고 `Secure`, `HttpOnly`, `SameSite`, `Path=/`를 함께 설정하는 방식이 권장된다.
- `localStorage`나 `sessionStorage`에 인증 토큰을 저장하면 JavaScript로 접근 가능하므로 XSS 한 번에 토큰이 노출될 수 있다.
- 세션 탈취 탐지는 IP, User-Agent, 로그인 위치, 요청 패턴, 민감 작업 시 재인증 같은 여러 신호를 조합한다.
- 장기 세션이나 Remember Me 기능은 편하지만 탈취 시 피해 시간이 길어지므로 만료, 재인증, 기기 관리가 필요하다.

---

## 관련 노트

- [[10_학습 노트/시스템보안/웹보안/세션과 쿠키|세션과 쿠키]]
- [[10_학습 노트/시스템보안/웹보안/XSS를 이용한 Session Token 탈취 실습|XSS를 이용한 Session Token 탈취 실습]]
- [[10_학습 노트/시스템보안/웹보안/XSS|XSS]]
- [[10_학습 노트/시스템보안/웹보안/웹 애플리케이션 구조|웹 애플리케이션 구조]]
- [[10_학습 노트/시스템보안/네트워크보안/HTTP 로그인 평문 노출|HTTP 로그인 평문 노출]]

---

## 참고 자료

- [OWASP Session Management Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html)
- [OWASP WSTG - Testing for Session Hijacking](https://owasp.org/www-project-web-security-testing-guide/latest/4-Web_Application_Security_Testing/06-Session_Management_Testing/09-Testing_for_Session_Hijacking)

---

## 확인 질문

1. Session Hijacking과 Brute Force는 무엇이 다른가?
2. HTTP 환경에서 Cookie가 왜 Sniffing 위험에 노출되는가?
3. XSS가 있으면 왜 `HttpOnly`가 중요해지는가?
4. IP와 Session을 묶는 방어의 장점과 한계는 무엇인가?
