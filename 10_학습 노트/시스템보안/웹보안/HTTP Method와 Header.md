---
type: concept
topic: web-security
source: 5-20_웹보안.pdf
source_pages:
  - 9
  - 10
  - 15
  - 16
  - 17
  - 18
  - 19
  - 20
  - 21
  - 22
  - 23
status: active
created: 2026-05-20
reviewed:
aliases:
  - HTTP Method
  - HTTP Header
  - HTTP 메서드와 헤더
tags:
  - 🏷️과목/웹보안
  - 🏷️주제/HTTP
  - 🏷️상태/active
---

# HTTP Method와 Header

source: [[40_자료/강의 자료/5-20_웹보안.pdf|5-20 웹보안]], p.9-10, p.15-23
raw memo: [[10_학습 노트/시스템보안/서론(이라쓰고 빠르게 휘갈겨 쓴거)|서론 raw 메모]]

## 한 줄 요약

HTTP Method는 **target resource에 어떤 동작을 요청하는지**를 나타내고, HTTP Header는 **요청과 응답을 어떻게 해석하고 처리할지에 대한 부가 정보**를 전달한다.

```text
GET /login.asp?id=nuno&pw=1234 HTTP/1.1
Host: example.com
User-Agent: ...
Accept: text/html
```

웹 보안에서는 method와 header를 단순 문법으로 외우는 것보다, “서버가 이 값을 믿어도 되는가?”와 “중간 장비, 브라우저, 캐시, 인증 로직이 이 값을 어떻게 해석하는가?”를 보는 것이 중요하다.

---

## 먼저 잡아야 할 핵심

- Method는 request line의 첫 번째 토큰이다. 예: `GET`, `POST`, `HEAD`.
- URI와 query string은 target resource와 parameter를 표현한다.
- Header는 `Field-Name: value` 형태로 request나 response에 부가 정보를 붙인다.
- Header 이름은 HTTP/1.x에서 대소문자를 구분하지 않는다.
- Header 값은 사용자가 조작할 수 있으므로 서버 측에서 신뢰하면 안 된다.
- `Entity Header`라는 표현은 오래된 분류다. 현대 HTTP 문서에서는 representation metadata, content field 같은 표현으로 정리되는 경우가 많다.

---

## Method는 요청의 의도를 나타낸다

| Method | 핵심 의미 | 보안 관점 |
| --- | --- | --- |
| GET | resource 조회 | query string이 URL, 로그, 브라우저 기록, Referer로 노출될 수 있다. 민감정보를 넣으면 안 된다. |
| POST | request body를 포함해 서버가 처리할 작업을 요청 | 로그인, 검색, 생성, 결제 등 다양하게 쓰인다. “POST = Create”로만 외우면 부정확하다. |
| HEAD | GET과 같은 응답 header를 요청하되 body는 받지 않음 | 상태 확인, metadata 확인에 유용하다. ICMP ping과 같은 계층의 기능은 아니다. |
| PUT | target URI의 resource를 생성하거나 대체 | 허용되면 파일 업로드/덮어쓰기 위험과 연결될 수 있다. 보통 엄격히 제한한다. |
| DELETE | target URI의 resource 삭제 요청 | 인증/권한 검사가 약하면 치명적이다. |
| OPTIONS | target resource가 지원하는 통신 option/method 확인 | CORS preflight에 쓰인다. 허용 method 노출과 misconfiguration 확인 지점이 된다. |
| TRACE | 요청 메시지 loop-back test | 보안상 비활성화하는 경우가 많다. 과거 XST(Cross-Site Tracing)와 연결되어 설명된다. |
| CONNECT | proxy를 통해 target server로 tunnel 생성 | HTTPS proxy tunnel에 쓰인다. VPN을 대체한다기보다 HTTP proxy에서 특정 목적지로 tunnel을 여는 기능이다. |

---

## CRUD와 HTTP Method

수업 메모의 “POST는 Create, GET은 Read, PUT은 Update?, DELETE는 Delete?”는 REST API를 설명할 때 자주 쓰는 단순화다.

정확히는 다음처럼 보는 편이 안전하다.

| CRUD | 자주 대응되는 HTTP Method | 주의점 |
| --- | --- | --- |
| Create | POST 또는 PUT | 서버가 URI를 정하면 POST, 클라이언트가 target URI를 정해 생성/대체하면 PUT이 자연스럽다. |
| Read | GET | GET은 조회 의도가 핵심이다. 서버 상태를 바꾸는 기능을 GET에 넣으면 위험하다. |
| Update | PUT, PATCH, POST | PUT은 전체 대체에 가깝고, PATCH는 부분 수정에 가깝다. POST로 처리하는 API도 많다. |
| Delete | DELETE | 삭제 요청은 반드시 인증/권한/CSRF 방어를 봐야 한다. |

CRUD 대응은 설계 관례이지 HTTP 프로토콜의 절대 법칙은 아니다. 특히 로그인, 검색, 결제, 파일 처리 같은 기능은 단순 CRUD 표에 안 들어맞는 경우가 많다.

---

## GET과 URL Parameter

GET 요청은 URL 뒤에 query string을 붙여 parameter를 전달할 수 있다.

```text
/login.asp?id=nuno&pw=1234
```

분해하면 다음과 같다.

| 부분 | 의미 |
| --- | --- |
| `/login.asp` | 요청 path |
| `?` | path와 query string의 구분자 |
| `id=nuno` | `id` parameter의 값이 `nuno` |
| `&` | parameter 사이의 구분자 |
| `pw=1234` | `pw` parameter의 값이 `1234` |

보안 관점:

- query string은 브라우저 주소창에 보인다.
- proxy, web server, application log에 남기 쉽다.
- 다른 사이트로 이동할 때 `Referer` header를 통해 일부 노출될 수 있다.
- 비밀번호, token, 주민번호 같은 민감정보를 GET query에 넣으면 안 된다.
- URL encoding은 보안 장치가 아니라 전송 표현 방식이다. `%27`, `%3Cscript%3E`처럼 encoding된 값도 서버에서 해석하면 공격 payload가 될 수 있다.

---

## HEAD는 ping인가?

수업 메모의 “HEAD는 ping 같은 느낌”은 비유로는 이해할 수 있지만 정확한 표현은 아니다.

| 비교 | HEAD | ping |
| --- | --- | --- |
| 계층 | HTTP 애플리케이션 계층 | ICMP 네트워크 계층 |
| 목적 | GET과 같은 응답 header를 body 없이 확인 | host 도달성과 왕복 시간 확인 |
| 대상 | 특정 HTTP resource | IP host |
| 보안 의미 | 웹 서버, routing, auth, cache, header 확인 가능 | HTTP 애플리케이션 동작은 확인하지 못함 |

정리하면 HEAD는 “HTTP resource에 대해 body를 빼고 상태와 header만 확인하는 방법”이다. 서버가 HEAD를 제대로 구현하지 않았거나 GET과 다르게 처리하는 경우도 있으므로, 보안 테스트에서는 실제 GET/POST 동작까지 따로 확인해야 한다.

---

## CONNECT와 VPN은 다르다

수업 메모의 “CONNECT 쓸 바에 VPN”은 거칠게 적힌 표현이라 그대로 외우면 안 된다.

CONNECT는 HTTP proxy에게 “이 host:port까지 TCP tunnel을 열어 달라”고 요청하는 method다. 대표적으로 HTTP proxy를 통해 HTTPS 사이트에 접속할 때 쓰인다.

VPN은 보통 장치나 네트워크 단위의 traffic을 암호화된 tunnel로 보내는 기술이다. 범위가 다르다.

| 구분 | CONNECT | VPN |
| --- | --- | --- |
| 위치 | HTTP proxy 기능 | 네트워크/터널링 솔루션 |
| 범위 | 보통 특정 target host:port | 장치 또는 네트워크 traffic 전반 |
| 대표 목적 | proxy를 통한 HTTPS tunnel | 원격 네트워크 접속, traffic 보호 |
| 보안 관점 | proxy 정책 우회, tunnel 허용 범위 확인 | split tunneling, route, DNS leak, 인증 확인 |

---

## Header는 메시지의 맥락을 붙인다

Header는 request와 response에 붙는 metadata다.

```http
Header-Name: value
```

강의 자료는 header를 General, Request, Response, Entity로 나눈다. 입문용 분류로는 유용하지만, 현대 HTTP 문서에서는 “field”와 “representation metadata”처럼 더 정리된 용어를 쓴다. 시험이나 강의 맥락에서는 PDF의 분류를 알고, 실무 문서를 볼 때는 최신 용어도 같이 읽어야 한다.

---

## Header 표는 어떻게 공부해야 하나?

강의 자료의 header 표는 전부 암기하라는 표라기보다, HTTP 메시지에 어떤 종류의 맥락 정보가 붙는지 보여주는 지도에 가깝다.

우선순위는 다음처럼 잡는 것이 좋다.

| 우선순위 | 먼저 볼 Header | 이유 |
| --- | --- | --- |
| 1 | `Host`, `Cookie`, `Authorization` | routing, session, 인증과 바로 연결된다. |
| 2 | `Content-Type`, `Content-Length`, `Transfer-Encoding` | 서버 parser, body 해석, request smuggling과 연결된다. |
| 3 | `Referer`, `Origin`, `Location` | CSRF, CORS, redirect, 유입 경로 분석과 연결된다. |
| 4 | `Cache-Control`, `ETag`, `Vary` | 캐시 동작과 개인정보 노출, cache poisoning 관점에서 중요하다. |
| 5 | `Server`, `Via`, `X-Forwarded-*` | 서버 fingerprinting, proxy/CDN/reverse proxy 구조 분석에 쓰인다. |

나머지는 이름을 봤을 때 “request 맥락인지, response 맥락인지, body 설명인지”를 분류하고 필요할 때 공식 문서로 확인하는 정도면 된다.

---

## General Header로 자주 보는 것

| Header | 의미 | 보안/운영 관점 |
| --- | --- | --- |
| `Cache-Control` | 캐시 정책 제어 | 민감 페이지는 `no-store` 같은 정책이 필요할 수 있다. |
| `Connection` | 연결 처리 지시 | HTTP/1.x 연결 관리와 관련된다. proxy 환경에서는 주의가 필요하다. |
| `Date` | 메시지 생성 시각 | 캐시, 로그 분석, 시간 비교에 쓰인다. |
| `Pragma` | 오래된 캐시 제어 호환용 | HTTP/1.0 호환 때문에 보일 수 있다. |
| `Transfer-Encoding` | body 전송 인코딩 방식 | `chunked` 처리 차이는 request smuggling과 연결될 수 있다. |
| `Via` | proxy/gateway를 거쳤음을 표시 | 중간 장비 존재를 보여준다. proxy 구조 분석에 단서가 된다. |

### Via는 무엇인가?

`Via`는 요청이나 응답이 proxy, gateway 같은 중간 장비를 통과했을 때 추가될 수 있는 header다.

예시:

```http
Via: 1.1 proxy.example.net
```

보안 관점에서는 다음을 볼 수 있다.

- 요청이 직접 origin server로 간 것인지, 중간 proxy를 거쳤는지
- 중간 장비가 HTTP version을 바꾸거나 header를 추가/삭제하는지
- reverse proxy, CDN, gateway 구조가 노출되는지

---

## Request Header로 자주 보는 것

| Header | 의미 | 보안 관점 |
| --- | --- | --- |
| `Host` | 요청한 host 이름 | virtual host 선택에 중요하다. Host header injection 확인 지점이다. |
| `Accept` | 받고 싶은 media type | content negotiation에 쓰인다. |
| `Accept-Charset` | 받고 싶은 문자셋 | encoding 해석 차이와 연결될 수 있다. |
| `Accept-Encoding` | gzip, br 같은 압축 방식 | 압축, cache, 일부 side-channel 이슈와 연결될 수 있다. |
| `Accept-Language` | 선호 언어 | locale 처리와 cache vary에 영향을 줄 수 있다. |
| `Authorization` | 인증 정보 | Basic/Bearer 등 민감한 값이 들어간다. 로그에 남기면 안 된다. |
| `Cookie` | 브라우저가 보낸 cookie | session 식별자, CSRF, session hijacking과 연결된다. |
| `If-Modified-Since` / `If-None-Match` | 조건부 요청 | cache 검증과 resource 변경 여부 판단에 쓰인다. |
| `Referer` | 이전 페이지 URL | 유입 경로 분석에 쓰이지만 민감정보 노출 위험이 있다. |
| `User-Agent` | 클라이언트 정보 | 사용자가 조작할 수 있으므로 보안 판단 근거로 쓰면 약하다. |

### Referer 예시

수업 메모의 “네이버에서 11번가로 들어가면 할인” 예시는 `Referer`를 유입 경로 판단에 쓰는 상황을 설명하려는 것으로 보인다.

정확히는 다음과 같다.

- 사용자가 A 사이트의 링크를 눌러 B 사이트로 이동하면, 브라우저가 B 사이트 요청에 `Referer: A의 URL`을 붙일 수 있다.
- B 사이트는 이 값을 보고 사용자가 어디에서 왔는지 추정할 수 있다.
- 하지만 `Referer`는 privacy 정책, Referrer-Policy, HTTPS->HTTP 이동, 브라우저/확장 설정에 따라 빠지거나 줄어들 수 있다.
- 공격자가 직접 HTTP 요청을 만들면 조작할 수도 있으므로 강한 보안 판단에 쓰면 안 된다.

---

## Response Header로 자주 보는 것

| Header | 의미 | 보안 관점 |
| --- | --- | --- |
| `Accept-Ranges` | range 요청 지원 여부 | 대용량 파일, partial content 처리와 연결된다. |
| `Age` | cache에 머문 시간 | CDN/cache 동작 분석에 쓰인다. |
| `ETag` | resource version 식별자 | cache 검증에 쓰인다. 추적 이슈가 될 수도 있다. |
| `Location` | redirect 대상 | open redirect, 인증 흐름 분석에 중요하다. |
| `Server` | 서버 소프트웨어 정보 | 정보 노출을 줄이기 위해 숨기거나 일반화하는 경우가 많다. |
| `Vary` | cache key에 영향을 주는 request header | cache poisoning, content negotiation과 연결된다. |
| `WWW-Authenticate` | 인증 방식 challenge | Basic, Bearer 같은 인증 흐름과 연결된다. |

### Server header는 왜 잘 안 보일 수 있나?

수업 메모의 “요즘엔 Server도 막힌 경우가 많음”은 타당하다. `Server: Apache/2.4.49`처럼 상세한 버전이 노출되면 공격자가 알려진 취약점과 매칭하기 쉽다.

다만 완전히 숨기는 것만으로 보안이 완성되지는 않는다. header를 지워도 TLS fingerprint, error page, static file 경로, cookie 이름, response pattern 등으로 기술 스택을 추정할 수 있다. 그래서 Server header 제거는 hardening의 일부일 뿐이다.

---

## Entity Header와 Representation Metadata

강의 자료의 Entity Header는 body의 성격을 설명하는 header로 이해하면 된다.

| Header | 의미 | 보안 관점 |
| --- | --- | --- |
| `Content-Type` | body의 media type | 브라우저가 HTML/JSON/image/script를 어떻게 해석할지에 영향을 준다. |
| `Content-Length` | body 크기 | proxy와 server의 해석 차이는 request smuggling과 연결될 수 있다. |
| `Content-Encoding` | body 압축/인코딩 방식 | 중간 장비와 애플리케이션의 decoding 순서가 중요하다. |
| `Content-Language` | body 언어 | locale 처리와 관련된다. |
| `Content-Range` | range 응답 범위 | 파일 다운로드와 partial response에 쓰인다. |
| `Expires` | cache 만료 시각 | 민감정보 cache 방지에 중요하다. |

현대 문서에서는 `Entity Header`라는 용어보다 representation metadata 또는 content 관련 field로 읽는 것이 더 정확하다.

---

## 보안 관점으로 보는 Method와 Header

| 확인 지점 | 봐야 하는 이유 |
| --- | --- |
| 허용 method | PUT, DELETE, TRACE가 열려 있으면 불필요한 공격면이 생길 수 있다. |
| GET query | 민감정보가 URL에 들어가면 로그, history, Referer로 퍼질 수 있다. |
| Host | reverse proxy, virtual host, password reset link 생성 로직과 연결된다. |
| Authorization | 인증정보가 로그나 error page에 노출되면 안 된다. |
| Cookie | session, SameSite, Secure, HttpOnly와 연결된다. |
| Content-Type | 서버 parser 선택, 브라우저 MIME sniffing, API 처리 방식에 영향을 준다. |
| Content-Length / Transfer-Encoding | proxy와 backend의 메시지 길이 해석 차이는 request smuggling으로 이어질 수 있다. |
| Referer | 분석에는 유용하지만 조작 가능하고 privacy 정책에 따라 사라질 수 있다. |
| Server | 상세 버전 노출은 fingerprinting에 도움을 준다. |

---

## 수업 표현을 정확한 개념으로 바꾸기

| 수업 표현 / 메모 | 의도 추론 | 정확한 정리 |
| --- | --- | --- |
| HEAD는 ping 같은 느낌 | body 없이 가볍게 상태를 확인하는 용도를 설명하려는 표현 | HEAD는 GET과 같은 header를 body 없이 받는 HTTP method다. ICMP ping과는 계층과 목적이 다르다. |
| POST Create, GET Read, PUT Update, DELETE Delete | REST API의 CRUD 대응을 빠르게 설명하려는 표현 | CRUD 대응은 설계 관례다. POST는 Create만 뜻하지 않고, PUT은 전체 대체에 가깝다. PATCH도 현대 API에서 자주 쓰인다. |
| CONNECT 쓸 바에 VPN | tunnel이라는 공통 인상을 거칠게 표현한 것으로 보인다 | CONNECT는 proxy를 통한 특정 target tunnel이고, VPN은 보통 장치/네트워크 단위 tunnel이다. |
| Server header는 요즘 막힌 경우가 많다 | 정보 노출 hardening을 설명하려는 표현 | 상세 서버 정보는 줄이는 것이 좋지만, header 제거만으로 fingerprinting을 막지는 못한다. |
| URL Encoding되어 전달된다 | URL에 직접 쓰기 어려운 문자를 전송 가능한 형태로 바꾼다는 뜻 | encoding은 보안 필터가 아니다. decoding 후의 값까지 검증해야 한다. |

---

## 오해하기 쉬운 지점

- `POST`는 자동으로 안전한 method가 아니다. URL에 안 보일 뿐 body, proxy log, application log, browser devtools 등에서 노출될 수 있다.
- `GET = 조회`, `POST = 생성`은 REST 스타일 설명에 가까운 관례다. 실제 서비스에서는 POST로 검색하거나 PUT으로 생성하는 경우도 있다.
- Header 값은 브라우저가 만들어 보내는 것처럼 보여도 조작 가능하다. `User-Agent`, `Referer`, `X-Forwarded-For` 같은 값으로 보안 판단을 확정하면 위험하다.
- `HEAD`는 ping과 다르다. 서버의 HTTP resource 처리 경로를 확인할 수 있지만, 네트워크 host 도달성만 보는 ICMP ping과는 계층이 다르다.
- `CONNECT`는 VPN이 아니다. proxy를 통한 특정 tunnel 요청이고, VPN은 보통 장치나 네트워크 traffic 전체를 다루는 별도 기술이다.
- header 표는 전부 외우는 것이 목표가 아니다. 보안과 직접 연결되는 header를 먼저 읽고, 나머지는 필요할 때 찾아보는 방식이 맞다.

---

## 공식 문서로 확인한 기준

- [MDN HTTP request methods](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Methods): HEAD, PUT, TRACE, CONNECT 등 method의 기본 의미를 참고했다.
- [MDN HTTP headers](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers): HTTP header가 request/response에 부가 정보를 전달한다는 설명과 주요 header 분류를 참고했다.
- [RFC 9110 HTTP Semantics](https://www.rfc-editor.org/rfc/rfc9110): method semantics, status code, field 의미의 현재 기준으로 참고했다.

---

## 관련 노트

- [[10_학습 노트/시스템보안/웹보안/HTTP 구조와 메시지|HTTP 구조와 메시지]]
- [[10_학습 노트/시스템보안/웹보안/웹 애플리케이션 구조|웹 애플리케이션 구조]]
- [[10_학습 노트/시스템보안/네트워크보안/HTTP 로그인 평문 노출|HTTP 로그인 평문 노출]]

---

## 확인 질문

- `HEAD`와 `ping`은 왜 비슷해 보이지만 같은 기능이 아닌가?
- GET query string에 비밀번호를 넣으면 어떤 경로로 새어 나갈 수 있는가?
- `POST = Create`라고만 외우면 어떤 오해가 생기는가?
- `CONNECT`와 VPN은 tunnel이라는 점 외에 무엇이 다른가?
- `Server` header를 숨겨도 기술 스택 추정이 완전히 막히지 않는 이유는 무엇인가?
- header 표를 전부 암기하지 않는다면, 어떤 header부터 우선적으로 봐야 하는가?
