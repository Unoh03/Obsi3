---
type: concept
topic: web-security
source: 5-20_웹보안.pdf
source_pages:
  - 4
  - 5
  - 6
  - 7
  - 8
  - 9
  - 10
  - 11
  - 12
  - 13
  - 14
status: active
created: 2026-05-20
reviewed:
aliases:
  - HTTP 메시지 구조
  - HTTP Request Response
  - HTTP 요청 응답 구조
tags:
  - 🏷️과목/웹보안
  - 🏷️주제/HTTP
  - 🏷️상태/active
---

# HTTP 구조와 메시지

source: [[40_자료/강의 자료/5-20_웹보안.pdf|5-20 웹보안]], p.4-14
raw memo: [[10_학습 노트/시스템보안/서론(이라쓰고 빠르게 휘갈겨 쓴거)|서론 raw 메모]]

## 한 줄 요약

HTTP는 Web Client와 Web Server가 **request와 response라는 메시지를 주고받아 resource를 요청하고 전달하는 애플리케이션 계층 프로토콜**이다.

```text
Client -> HTTP Request -> Server
Client <- HTTP Response <- Server
```

웹 보안에서는 HTTP 메시지를 “그냥 통신”으로 보면 안 된다. request line, header, body, URL parameter는 전부 공격자가 조작할 수 있는 입력이고, response의 status code, header, body는 브라우저와 보안 장비가 다음 동작을 판단하는 근거가 된다.

---

## 먼저 잡아야 할 핵심

- HTTP는 웹에서 resource를 가져오거나 전송하기 위한 client-server 프로토콜이다.
- 클라이언트가 보내는 메시지는 request, 서버가 답하는 메시지는 response다.
- HTTP는 애플리케이션 계층 프로토콜이다.
- HTTP/1.x 메시지는 사람이 읽을 수 있는 text 형태에 가깝다.
- HTTP/2와 HTTP/3는 wire format이 binary framing이지만, method, status code, header field 같은 의미 구조는 이어진다.
- HTTP 자체는 상태를 저장하지 않는 stateless 프로토콜이다. 로그인 상태는 Cookie, Session, Token 같은 별도 메커니즘으로 만든다.
- 암호화되지 않은 HTTP는 네트워크에서 request와 response 내용이 노출될 수 있다.

---

## HTTP가 놓이는 위치

강의 자료의 packet layout은 다음처럼 이해하면 된다.

```text
Ethernet
  -> IP
    -> TCP
      -> HTTP
        -> Data
```

정확히는 HTTP를 Ethernet/IP/TCP처럼 같은 의미의 “packet”으로 보면 안 된다. Ethernet frame 안에 IP packet이 들어가고, IP packet 안에 TCP segment가 들어가며, TCP byte stream 위에 HTTP message가 실린다고 보는 쪽이 더 정확하다.

웹 보안에서 이 구분이 중요한 이유는 다음과 같다.

| 계층 | 주로 보는 것 | 보안 연결점 |
| --- | --- | --- |
| Ethernet / LAN | MAC 주소, local network | ARP Spoofing, Sniffing |
| IP | 출발지/목적지 IP | Network Firewall, routing |
| TCP | port, connection, sequence | port filtering, connection handling |
| HTTP | method, URI, header, body | XSS, SQL Injection, 인증 우회, WAF |

---

## HTTP Request 구조

HTTP request는 클라이언트가 서버에게 “이 resource에 대해 이런 동작을 해 달라”고 보내는 메시지다.

기본 구조는 다음과 같다.

```http
METHOD request-target HTTP-version
Header-Name: value
Header-Name: value

message body
```

각 부분은 이렇게 읽는다.

| 부분 | 의미 | 보안 관점 |
| --- | --- | --- |
| Method | 서버에게 기대하는 동작. 예: GET, POST, HEAD | method 제한이 약하면 의도하지 않은 기능이 열릴 수 있다. |
| Request target | 요청 대상. path, query string 등이 들어간다. | URL parameter는 사용자 입력이다. 검증이 필요하다. |
| HTTP version | HTTP/1.0, HTTP/1.1 같은 버전 | Host header, persistent connection 같은 동작 차이에 영향을 준다. |
| Header field | 요청에 대한 부가 정보 | Host, Cookie, Authorization, Content-Type 같은 보안상 중요한 값이 들어간다. |
| Blank line | header와 body의 구분 | CRLF 처리 오류는 request smuggling 같은 문제와 연결될 수 있다. |
| Message body | form, JSON, file upload 같은 본문 | 서버 측 입력 검증의 핵심 대상이다. |

예시:

```http
GET /showtable.asp?page=1&name=nuno HTTP/1.1
Host: www.aegisone.co.kr
User-Agent: Mozilla/5.0
Accept: text/html
Connection: close

```

한 줄씩 분해하면 다음과 같다.

| 줄 | 의미 |
| --- | --- |
| `GET /showtable.asp?page=1&name=nuno HTTP/1.1` | `/showtable.asp` resource를 GET으로 요청한다. `page`와 `name`은 query parameter다. |
| `Host: www.aegisone.co.kr` | 같은 IP에서 여러 도메인을 운영할 때 어떤 host를 요청했는지 알려준다. |
| `User-Agent: Mozilla/5.0` | 클라이언트 프로그램 정보를 담는다. 사용자가 조작할 수 있으므로 신뢰하면 안 된다. |
| `Accept: text/html` | 클라이언트가 받고 싶은 media type을 알려준다. |
| `Connection: close` | 응답 후 TCP 연결을 닫겠다는 연결 처리 지시다. |
| 빈 줄 | header가 끝났음을 나타낸다. 이 예시는 GET 요청이라 body가 없다. |

---

## HTTP Response 구조

HTTP response는 서버가 클라이언트의 request를 처리한 결과다.

기본 구조는 다음과 같다.

```http
HTTP-version status-code reason-phrase
Header-Name: value
Header-Name: value

message body
```

예시:

```http
HTTP/1.1 200 OK
Date: Wed, 20 May 2026 02:30:00 GMT
Content-Type: text/html; charset=UTF-8
Content-Length: 57

<html><body><h1>Hello</h1></body></html>
```

한 줄씩 분해하면 다음과 같다.

| 줄 | 의미 |
| --- | --- |
| `HTTP/1.1 200 OK` | HTTP/1.1 응답이고, 요청 처리가 성공했다는 뜻이다. |
| `Date: ...` | 응답이 생성된 시각이다. |
| `Content-Type: text/html; charset=UTF-8` | body를 HTML과 UTF-8로 해석하라는 뜻이다. |
| `Content-Length: 57` | body 크기를 byte 단위로 알려준다. |
| 빈 줄 | header와 body의 구분이다. |
| `<html>...` | 브라우저가 렌더링할 response body다. |

---

## Status Code 읽는 법

Status code는 response의 첫 줄에 들어가며, 클라이언트가 요청 결과를 빠르게 판단하게 해준다.

| 범위 | 의미 | 예시 |
| --- | --- | --- |
| 1xx | 요청을 받았고 처리 중인 중간 응답 | `100 Continue` |
| 2xx | 성공 | `200 OK`, `201 Created` |
| 3xx | redirection 필요 | `301 Moved Permanently`, `302 Found` |
| 4xx | client 쪽 요청 문제 | `400 Bad Request`, `401 Unauthorized`, `403 Forbidden`, `404 Not Found` |
| 5xx | server 쪽 처리 실패 | `500 Internal Server Error` |

헷갈리기 쉬운 점:

- `401 Unauthorized`는 이름과 달리 “인증이 필요하거나 실패했다”에 가깝다.
- `403 Forbidden`은 서버가 요청자를 이해했지만 허용하지 않는 상황에 가깝다.
- `404 Not Found`는 실제로 없다는 뜻일 수도 있고, 보안을 위해 존재 여부를 숨기는 응답일 수도 있다.
- 모든 에러를 `200 OK`로 감싸고 body 안에만 실패를 쓰면, HTTP의 표준적인 의미를 잃어버린다.

---

## HTTP Version과 현재 기준

강의 자료는 HTTP/1.0과 HTTP/1.1을 중심으로 설명한다. 이것은 웹 보안 입문에서는 적절하다. request line, status line, header, body를 눈으로 읽기 좋고, proxy/WAF/로그 분석에서도 HTTP/1.1 형태를 자주 만나기 때문이다.

다만 최신 기준에서는 다음을 같이 기억해야 한다.

- HTTP/1.0의 원래 문서는 RFC 1945다.
- HTTP/1.1은 과거 RFC 2616으로 많이 설명됐지만, 현재는 여러 RFC로 대체됐다.
- HTTP semantics의 현재 핵심 기준은 RFC 9110이다.
- HTTP/2와 HTTP/3는 전송 방식과 framing이 달라졌지만, method, status code, field의 의미는 HTTP semantics 위에서 이해한다.

정리하면, 수업에서 HTTP/1.1 텍스트 메시지를 먼저 보는 이유는 **웹 요청을 눈으로 분해하는 능력**을 만들기 위해서다.

---

## 보안 관점

HTTP 메시지를 볼 때는 다음 기준으로 나누면 된다.

| 위치 | 질문 | 연결되는 취약점 |
| --- | --- | --- |
| Request line | 어떤 method로 어떤 URI를 요청했는가? | method 우회, path traversal, query tampering |
| Header | 인증, 세션, host, content type이 어떻게 전달되는가? | Host header attack, session hijacking, content-type confusion |
| Body | 사용자가 어떤 값을 보냈는가? | SQL Injection, XSS, file upload, command injection |
| Response status | 서버가 성공/실패/리다이렉트를 어떻게 표현하는가? | 인증 우회 탐지, 정보 노출, 잘못된 error handling |
| Response header | 브라우저가 어떤 보안 정책으로 해석하는가? | X-Content-Type-Options, CSP, Cookie 속성 누락 |
| Response body | 사용자 입력이 HTML/JS 문맥에 출력되는가? | XSS |

> [!important] 핵심
> HTTP request는 서버 입장에서 전부 외부 입력이다. 브라우저가 정상적으로 만든 요청처럼 보여도 proxy tool, script, curl로 얼마든지 조작할 수 있다.

---

## 수업 표현을 정확한 개념으로 바꾸기

| 수업 표현 / 메모 | 의도 추론 | 정확한 정리 |
| --- | --- | --- |
| HTTP는 text 형태라 읽을 수 있다 | Wireshark나 proxy에서 HTTP/1.x 메시지를 눈으로 분석할 수 있음을 강조하려는 표현 | HTTP/1.x는 text 기반 메시지 형식에 가깝다. HTTPS는 TLS로 암호화되어 네트워크에서 그대로 읽을 수 없다. HTTP/2와 HTTP/3는 binary framing을 쓴다. |
| HTTP Packet Layout | Ethernet/IP/TCP 위에 HTTP가 실린다는 계층 감각을 주려는 표현 | HTTP는 애플리케이션 계층 메시지다. TCP stream 위에 HTTP message가 실린다고 보는 것이 정확하다. |
| HTTP 예제를 한 줄씩 분해해야 한다 | 단순 암기보다 request/response를 구조적으로 읽게 하려는 의도 | request line, header, blank line, body를 나눠 읽고, 각 필드가 보안에 어떤 영향을 주는지까지 봐야 한다. |

---

## 오해하기 쉬운 지점

- `HTTP Packet Layout`을 보고 HTTP를 Ethernet/IP/TCP와 같은 종류의 packet으로 보면 안 된다. HTTP는 TCP 연결 위에서 오가는 애플리케이션 계층 message다.
- HTTP/1.x가 text로 읽기 쉽다는 말은 암호화되지 않은 HTTP에 대한 설명이다. HTTPS에서는 TLS가 먼저 복호화되지 않으면 같은 방식으로 읽을 수 없다.
- `200 OK`는 HTTP 요청 처리가 성공했다는 뜻이지, 애플리케이션의 업무 처리가 항상 성공했다는 뜻은 아니다. 어떤 API는 실패를 body에 넣고도 200을 반환한다.
- HTTP가 stateless라는 말은 로그인이 불가능하다는 뜻이 아니다. 로그인 상태는 Cookie, Session, Token 같은 별도 상태 관리 장치로 만든다.
- request가 브라우저에서 온 것처럼 보여도 신뢰하면 안 된다. 공격자는 proxy tool, script, curl로 method, header, body를 직접 만들 수 있다.

---

## 공식 문서로 확인한 기준

- [MDN HTTP Overview](https://developer.mozilla.org/ko/docs/Web/HTTP/Guides/Overview): HTTP가 web data exchange의 기반이고 client-server protocol이며 request/response message로 통신한다는 설명을 기준으로 참고했다.
- [RFC 9110 HTTP Semantics](https://www.rfc-editor.org/rfc/rfc9110): HTTP semantics, request method, status code, field의 현재 기준으로 참고했다.

---

## 관련 노트

- [[10_학습 노트/시스템보안/웹보안/웹 애플리케이션 구조|웹 애플리케이션 구조]]
- [[10_학습 노트/시스템보안/웹보안/HTTP Method와 Header|HTTP Method와 Header]]
- [[10_학습 노트/시스템보안/네트워크보안/HTTP 로그인 평문 노출|HTTP 로그인 평문 노출]]

---

## 확인 질문

- HTTP request에서 공격자가 조작할 수 있는 부분은 어디까지인가?
- `GET /path?name=value HTTP/1.1`에서 method, path, query string, version은 각각 무엇인가?
- response의 `Content-Type`이 잘못되면 브라우저 해석과 보안에 어떤 문제가 생길 수 있는가?
- HTTP/1.x는 text로 읽기 쉬운데, HTTPS에서는 왜 같은 방식으로 볼 수 없는가?
- `200 OK`인데도 실제 로그인이나 결제가 실패할 수 있는 이유는 무엇인가?
