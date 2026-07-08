---
type: concept
topic: web-security
source:
  - 5-20_웹보안.pdf
  - MDN HTTP authentication
  - RFC 7617
source_pages:
  - 44
  - 45
  - 46
  - 47
  - 48
status: active
created: 2026-07-07
aliases:
  - 웹 인증 구조
  - Basic Authentication
  - Anonymous Authentication
  - Form Based Authentication
tags:
  - 🏷️과목/웹보안
  - 🏷️주제/WebAuth
  - 🏷️주제/HTTP
  - 🏷️상태/active
---

# 기초 웹 인증 방식 - Basic, Anonymous, Form

source:
- [[40_자료/강의 자료/5-20_웹보안.pdf|5-20 웹보안]], p.44-48
- [MDN HTTP authentication](https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/Authentication)
- [RFC 7617 - The Basic HTTP Authentication Scheme](https://www.rfc-editor.org/rfc/rfc7617)

## 한 줄 요약

웹 인증 방식은 **사용자가 누구인지 서버가 확인하고, 이후 요청을 어떤 사용자 권한으로 처리할지 결정하는 방식**이다.

이 PDF 범위에서는 `Basic Authentication`, `Anonymous Authentication`, `Form Based Authentication`을 비교한다. 보안 관점에서 핵심은 **인증 정보가 HTTP로 평문 전송되면 노출될 수 있으므로 HTTPS/TLS가 필요하다**는 점이다.

---

## 먼저 잡아야 할 핵심

- `Basic Authentication`은 HTTP 인증 프레임워크를 이용해 `Authorization` header로 ID/PW를 보낸다.
- Basic에서 ID/PW는 Base64로 인코딩될 뿐 암호화되는 것이 아니다.
- `Anonymous Authentication`은 별도 로그인 없이 익명 계정 권한으로 서버 자원을 제공하는 방식이다.
- `Form Based Authentication`은 HTML form으로 ID/PW를 서버에 보내고, 서버가 자체 로직으로 인증을 처리하는 방식이다.
- Form 인증은 대부분의 웹 애플리케이션에서 흔하지만, HTTP로 보내면 ID/PW가 평문 노출될 수 있다.
- 인증이 성공한 뒤 로그인 상태 유지는 보통 [[10_학습 노트/시스템보안/웹보안/세션과 쿠키|세션과 쿠키]] 구조로 이어진다.

---

## 세 방식의 차이

| 방식 | 인증 정보 전달 위치 | 주로 쓰는 곳 | 핵심 위험 |
|---|---|---|---|
| Basic Authentication | HTTP `Authorization` header | 서버/디렉터리 단위 접근 제한, 오래된 관리 페이지 | Base64는 암호화가 아니므로 HTTPS 없으면 ID/PW 노출 |
| Anonymous Authentication | 서버가 정한 익명 계정 권한 | 공개 자료, 로그인 없이 보는 리소스 | 익명 계정 권한이 과하면 불필요한 자원 노출 |
| Form Based Authentication | HTML form 요청 body 또는 query | 일반 웹 로그인 화면 | HTTPS 없으면 ID/PW 노출. 인증 후 session 관리 필요 |

---

## Basic Authentication

Basic Authentication은 서버가 보호 자원에 대해 인증을 요구하면, 브라우저나 클라이언트가 ID/PW를 `Authorization` header에 담아 보내는 방식이다.

흐름은 대략 다음과 같다.

```text
1. 클라이언트가 보호된 자원 요청
2. 서버가 401 Unauthorized + WWW-Authenticate: Basic ... 응답
3. 클라이언트가 ID/PW를 입력받음
4. 클라이언트가 Authorization: Basic <base64(id:password)> 전송
5. 서버가 credential을 확인하고 접근 허용/거부
```

PDF는 IIS의 Basic 인증 설정과 브라우저 인증창을 예로 든다.

중요한 점은 Base64다.

```text
id:password
-> Base64 encoding
-> Authorization header
```

Base64는 암호화가 아니라 표현 방식 변환이다. 다시 디코딩할 수 있으므로, HTTP 평문 통신에서 가로채면 ID/PW가 노출될 수 있다.

따라서 Basic Authentication은 반드시 HTTPS/TLS 위에서만 제한적으로 봐야 한다.

---

## Anonymous Authentication

Anonymous Authentication은 사용자가 직접 로그인하지 않아도 서버가 정한 익명 계정 권한으로 자원을 제공하는 방식이다.

예를 들어 공개 이미지, 공개 문서, 정적 파일처럼 “누구나 봐도 되는 자원”은 익명 접근으로 제공할 수 있다.

보안 관점에서는 다음을 구분해야 한다.

| 구분 | 의미 |
|---|---|
| 의도된 공개 자원 | 익명 접근 허용 가능 |
| 내부 관리 페이지 | 익명 접근 허용하면 안 됨 |
| 업로드 파일, 백업 파일, 설정 파일 | 실수로 익명 공개되면 정보 노출 |
| 익명 계정 권한 | 최소 권한이어야 함 |

즉 Anonymous Authentication은 “보안이 없는 방식”이라기보다, **서버가 어느 자원을 로그인 없이 공개할지 정하는 접근 제어 설정**에 가깝다.

---

## Form Based Authentication

Form Based Authentication은 HTML form에 사용자가 ID/PW를 입력하고, 서버가 그 값을 받아 자체 로그인 로직으로 확인하는 방식이다.

PDF 예시는 다음 구조다.

```html
<form method="POST">
  <input type="text" name="user_id">
  <input type="password" name="user_pw">
  <input type="submit" value="로그인">
</form>
```

이 방식은 일반 웹 애플리케이션 로그인 화면에서 가장 흔하다.

하지만 form이 HTTP로 전송되면 ID/PW가 평문으로 네트워크에 흘러간다. 그래서 로그인 페이지와 로그인 요청은 HTTPS/TLS로 보호해야 한다.

인증 성공 후에는 보통 서버가 session을 만들고, 브라우저에는 session cookie를 발급한다. 이 다음 단계는 [[10_학습 노트/시스템보안/웹보안/세션과 쿠키|세션과 쿠키]]에서 다룬다.

---

## Basic과 Form의 차이

| 비교 | Basic Authentication | Form Based Authentication |
|---|---|---|
| 표준 위치 | HTTP 인증 프레임워크 | 애플리케이션 로그인 로직 |
| 입력 UI | 브라우저 기본 인증창인 경우가 많음 | 웹 페이지가 만든 로그인 form |
| 전달 위치 | `Authorization` header | 보통 POST body |
| credential 보호 | HTTPS 없으면 위험 | HTTPS 없으면 위험 |
| 인증 후 상태 관리 | 요청마다 credential을 다시 보낼 수 있음 | 보통 session cookie로 로그인 상태 유지 |
| 커스터마이징 | 제한적 | 로그인 정책, MFA, lockout, CSRF 방어 등 구현 가능 |

Basic은 단순하고 설정이 쉽지만 사용자 경험과 세밀한 보안 정책 적용이 제한적이다. Form 방식은 구현 책임이 애플리케이션으로 넘어오지만, 일반 웹 서비스에서 필요한 정책을 더 세밀하게 만들 수 있다.

---

## 평문 노출과 HTTPS

이 범위에서 제일 중요한 보안 연결은 [[10_학습 노트/시스템보안/네트워크보안/HTTP 로그인 평문 노출|HTTP 로그인 평문 노출]]이다.

| 상황 | 노출될 수 있는 것 |
|---|---|
| Basic over HTTP | `Authorization` header의 Base64 credential |
| Form login over HTTP | form으로 전송한 ID/PW |
| 로그인 이후 HTTP | session cookie, session identifier |

그래서 “로그인 화면만 HTTPS”로는 부족할 수 있다. 로그인 이후 session cookie도 보호해야 하므로, 인증과 세션이 필요한 전체 구간을 HTTPS로 유지해야 한다.

---

## 수업 표현을 정확한 개념으로 바꾸기

| 수업/PDF 표현 | 이 노트에서의 정리 |
|---|---|
| Basic은 Base64로 인코딩한다 | Base64는 암호화가 아니다. 디코딩 가능하므로 HTTPS가 필요하다. |
| 사용자 계정은 시스템 계정이 이용됨 | 전통적인 서버 설정 예시로 이해한다. 실제 서비스에서는 별도 계정 저장소와 정책을 둘 수 있다. |
| Anonymous는 익명 계정을 이용한다 | 로그인 없이 접근 가능한 자원을 서버 권한으로 제공한다. 익명 계정 권한을 최소화해야 한다. |
| Form은 대부분 웹 앱에서 사용한다 | 맞다. 다만 form 전송 보호, session 발급, 실패 횟수 제한, CSRF 방어 등 구현 책임이 따른다. |
| SSL을 이용한 암호화가 필요함 | 현재 표현으로는 HTTPS/TLS 적용이 필요하다고 이해한다. |

---

## 관련 노트

- [[10_학습 노트/시스템보안/웹보안/HTTP 구조와 메시지|HTTP 구조와 메시지]]
- [[10_학습 노트/시스템보안/네트워크보안/HTTP 로그인 평문 노출|HTTP 로그인 평문 노출]]
- [[10_학습 노트/시스템보안/웹보안/세션과 쿠키|세션과 쿠키]]
- [[10_학습 노트/시스템보안/웹보안/Hydra 로그인 Brute Force 실습|Hydra 로그인 Brute Force 실습]]
- [[10_학습 노트/시스템보안/웹보안/HTML 인코딩|HTML 인코딩]]

---

## 오해하기 쉬운 지점

- Base64는 암호화가 아니다.
- Basic이 “예전 방식”이라고 해서 개념을 버려도 되는 것은 아니다. HTTP 인증과 credential 전송 위험을 이해하는 좋은 기준점이다.
- Form login은 자동으로 안전한 방식이 아니다. HTTPS, session 관리, 실패 횟수 제한, CSRF 방어가 필요하다.
- Anonymous 접근은 “아무 권한 없음”이 아니라 서버가 정한 익명 권한으로 접근하는 것이다.
- 인증과 세션은 다르다. 인증은 사용자가 누구인지 확인하는 단계이고, 세션은 그 결과를 여러 요청 동안 유지하는 구조다.

---

## 확인 질문

- Basic Authentication에서 Base64가 왜 암호화가 아닌가?
- Basic과 Form 방식은 credential을 어디에 담아 보내는가?
- Form login이 HTTP로 전송되면 어떤 정보가 노출되는가?
- Anonymous Authentication은 언제 의도된 설정이고, 언제 위험한 설정인가?
- 인증 성공 이후 왜 [[10_학습 노트/시스템보안/웹보안/세션과 쿠키|세션과 쿠키]]가 필요한가?

---

## 공식 보강 근거

| Source | Freshness | Reliability | Finding used |
|---|---|---|---|
| MDN HTTP authentication | Current checked, Date explicit 2025-08-01 | MDN Web Docs | HTTP 인증은 `WWW-Authenticate` challenge와 `Authorization` header 흐름을 사용하며, Basic은 credential을 encoded but not encrypted 상태로 보내므로 HTTPS/TLS 없이는 안전하지 않다고 설명한다. |
| RFC 7617 | Current checked, Historical/spec | IETF RFC | Basic HTTP Authentication Scheme의 기준 문서로, Basic credential이 user-id/password pair를 Base64로 인코딩해 전달하는 방식임을 확인했다. |
