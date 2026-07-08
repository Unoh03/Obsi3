---
type: concept
topic: web-security
source:
  - 5-20_웹보안.pdf
  - MDN Client-side form validation
source_pages:
  - 73
  - 74
  - 75
  - 76
status: active
created: 2026-07-08
reviewed: 2026-07-08
aliases:
  - 웹 진단 기초
  - Web Spidering
  - Spidering
  - Client-side Validation 우회
  - Server-side Validation
tags:
  - 🏷️과목/웹보안
  - 🏷️주제/Spidering
  - 🏷️주제/ClientSideValidation
  - 🏷️주제/ServerSideValidation
  - 🏷️상태/active
---

# 웹 진단 기초 - Spidering과 Client-side Validation 우회

source:

- [[40_자료/강의 자료/5-20_웹보안.pdf|5-20 웹보안]], p.73-76
- [MDN Client-side form validation](https://developer.mozilla.org/en-US/docs/Learn_web_development/Extensions/Forms/Form_validation)

## 한 줄 요약

웹 진단의 첫 단계는 애플리케이션의 경로와 기능을 파악하는 것이다. Spidering은 이 탐색을 자동화하지만, 동적 메뉴·입력값·세션·토큰 때문에 빠뜨리거나 반복할 수 있다. Client-side Validation은 사용자 경험에는 유용하지만 공격자가 요청과 응답을 조작할 수 있으므로 보안 판단의 최종 기준이 될 수 없다.

---

## PDF p.73-76 구조

| 범위 | 주제 | 핵심 판단 |
|---|---|---|
| p.73 | Web Spidering | 웹 애플리케이션의 구조와 기능을 파악하는 정보수집 단계 |
| p.74 | Spidering 주의점 | 자동화 도구는 동적 메뉴, 입력값 요구, 무한 반복, 세션 종료, token 요구에 취약할 수 있음 |
| p.75 | Type of Validation | Client-side Validation과 Server-side Validation의 장단점 구분 |
| p.76 | Bypassing Client Side Validation | 소스 수정 또는 proxy tool로 request/response를 조작해 우회 가능 |

이 범위는 공격 절차를 외우는 단원이 아니라, “진단자가 어떤 기능을 찾아야 하고, 어떤 검증을 신뢰하지 말아야 하는가”를 정리하는 단원이다.

---

## Web Spidering

Spidering은 사이트의 링크, form, script, response를 따라가며 URL과 기능 후보를 수집하는 과정이다. 수작업 browsing보다 빠르게 구조를 훑을 수 있지만, 자동화 도구가 보는 화면이 실제 사용자·인증 상태·JavaScript 실행 결과와 항상 같지는 않다.

PDF p.73은 예시 도구로 Paros, Burp Spider, WebScarab을 든다. 이 vault에서는 이후 실습에서 Paros Spider가 관리자 로그인 endpoint를 찾는 흐름으로 다시 등장한다.

Spidering 결과는 “발견한 경로 목록”이지 “전체 구조를 완전히 안다”는 증거가 아니다.

---

## 자동화 Spidering의 한계

PDF p.74는 자동화 도구 사용 시 주의점을 정리한다.

| 한계 | 왜 문제가 되는가 |
|---|---|
| 동적으로 생성되는 메뉴 | JavaScript 실행, 사용자 상태, 화면 이벤트에 따라 링크가 생기면 일반 spider가 놓칠 수 있다. |
| 정확한 입력값 요구 | 검색어, ID, token, form field가 필요하면 빈 요청만으로는 다음 페이지에 도달하지 못할 수 있다. |
| 같은 URL에 POST 데이터로 다른 페이지 표시 | URL만 보면 같은 페이지처럼 보여도 request body에 따라 다른 기능일 수 있다. |
| 일회성 정보가 URL에 포함됨 | nonce, token, timestamp가 계속 바뀌면 무한히 다른 URL처럼 보일 수 있다. |
| logout 처리 | spider가 logout 링크를 밟으면 인증 세션이 끊겨 이후 기능을 못 볼 수 있다. |
| page별 인증 token 요구 | token 갱신 흐름을 따라가지 못하면 정상 경로를 놓치거나 반복 실패한다. |

따라서 spidering 뒤에는 사람이 확인해야 한다.

```text
자동 수집 결과
-> 누락 가능 경로 확인
-> 인증 상태 유지 여부 확인
-> form/request body 차이 확인
-> 실제 취약점 테스트는 별도 수행
```

---

## Client-side Validation과 Server-side Validation

Client-side Validation은 브라우저에서 HTML 속성이나 JavaScript로 입력값을 먼저 검사하는 방식이다. 사용자가 잘못 입력한 값을 즉시 고칠 수 있게 해주고, 불필요한 서버 요청을 줄인다.

Server-side Validation은 서버가 요청을 받은 뒤 최종적으로 검사하는 방식이다. 보안 판단은 이쪽에 있어야 한다.

| 구분 | 위치 | 장점 | 보안상 한계 또는 의미 |
|---|---|---|---|
| Client-side Validation | 브라우저 HTML/JavaScript | 빠른 피드백, 서버 부하 감소 | 사용자나 proxy가 우회할 수 있으므로 신뢰 경계가 아님 |
| Server-side Validation | 서버 처리 코드 | 검증 신뢰도가 높음 | 구현 누락 시 client 검증만 남아 우회됨 |

MDN도 client-side form validation을 좋은 사용자 경험을 위한 초기 검사로 설명하면서, client에서 서버로 넘어오는 데이터는 신뢰하면 안 되고 서버에서도 검증해야 한다고 정리한다.

---

## Client-side Validation 우회 방식

PDF p.76은 두 가지 우회 축을 든다.

| 방식 | 의미 | 연결 실습 |
|---|---|---|
| 소스코드 수정 | 브라우저가 받은 HTML/JavaScript를 저장하거나 수정해 검증 코드를 제거 | 개발자 도구 또는 로컬 수정으로 재현 가능 |
| Web Proxy Tool 이용 | request 또는 response를 proxy에서 직접 조작 | [[Client-side Validation 우회와 Server-side Validation 실습]] |

기존 실습 노트는 Paros로 이 차이를 확인했다.

- `Trap request`: 브라우저 검증을 통과한 뒤 서버로 가는 요청 값을 바꾼다.
- `Trap response`: 서버가 내려준 JavaScript 검증 코드를 브라우저 도착 전에 지운다.
- `Server-side Validation`: 서버 PHP가 같은 조건을 다시 검사하면 위 두 방식으로도 차단된다.

---

## 이 vault에서 쓰는 법

이 노트는 실습 증거 노트가 아니라 진단 기준 노트다.

복습 경로:

```text
웹 애플리케이션 기능 탐색 필요
-> 이 노트에서 spidering 한계와 validation 신뢰 경계 확인
-> [[Client-side Validation 우회와 Server-side Validation 실습]]에서 Paros 우회 흐름 확인
-> Brute Force, SQL Injection, CSRF, XSS 실습에서 request/response 조작이 왜 가능한지 연결
```

이 범위는 특히 아래 노트들과 연결된다.

- [[Hydra 로그인 Brute Force 실습]]: Paros로 로그인 request/response 구조를 먼저 확인한다.
- [[SQL Injection 인증 우회 실습]]: 브라우저 제한이 아니라 서버 SQL 해석이 핵심이다.
- [[SQL Injection Error와 UNION 기반 정보 추출과 Schema 파악]]: client 제한을 우회해 긴 payload를 넣는 흐름과 연결된다.
- [[장운호_웹보안실습]]: Paros Spider로 관리자 로그인 endpoint를 발견한 사례가 있다.

---

## 오해하기 쉬운 지점

| 오해 | 정정 |
|---|---|
| Spidering을 돌리면 전체 구조를 다 찾은 것이다 | 자동화 도구는 동적 메뉴, 입력값, token, 인증 상태 때문에 누락할 수 있다. |
| Client-side Validation이 있으면 서버는 안전하다 | client 검증은 사용자가 우회할 수 있으므로 서버에서 다시 검사해야 한다. |
| Proxy 조작은 서버 코드를 바꾸는 것이다 | proxy는 HTTP request/response를 바꿀 수 있지만 서버 내부 코드 실행 자체를 제거하지는 못한다. |
| Server-side Validation은 client validation을 대체하므로 UX 검증은 필요 없다 | 둘은 목적이 다르다. client 검증은 UX, server 검증은 신뢰 경계다. |
| 자동화 도구는 항상 안전하게 돈다 | logout 링크, 무한 URL, 상태 변경 form을 따라가면 세션과 상태가 바뀔 수 있다. |

---

## 근거 요약

| 근거 | 이 노트에서 사용한 판단 |
|---|---|
| PDF p.73-74 | Web Spidering은 구조·기능 파악 단계이고, 자동화 도구에는 동적 메뉴, 입력값, 반복, 세션, token 한계가 있다. |
| PDF p.75-76 | Client-side Validation은 우회 가능하고, Server-side Validation은 최종 신뢰 경계로 봐야 한다. |
| MDN Client-side form validation | client-side validation은 UX에 유용하지만, client에서 서버로 넘어오는 데이터는 신뢰하지 말고 서버에서도 검증해야 한다. |
| 기존 실습 노트 | Paros Trap request/response와 server-side validation 차이를 실습 증거로 보존한다. |

---

## 확인 질문

1. Spidering 결과가 전체 구조의 증거가 아닌 이유는 무엇인가?
2. 같은 URL이라도 POST body가 다르면 왜 다른 기능으로 봐야 하는가?
3. Client-side Validation은 어떤 목적에는 좋고, 어떤 목적에는 부족한가?
4. Paros `Trap request`와 `Trap response`는 각각 무엇을 바꾸는가?
5. Server-side Validation이 있으면 client-side 우회가 왜 차단되는가?
