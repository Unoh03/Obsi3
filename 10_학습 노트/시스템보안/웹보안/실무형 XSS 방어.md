---
type: concept
topic: web-security
source:
  - OWASP Cross Site Scripting Prevention Cheat Sheet
  - OWASP DOM based XSS Prevention Cheat Sheet
  - MDN Set-Cookie
  - MDN Content Security Policy
source_pages:
status: active
created: 2026-05-27
reviewed: 2026-07-08
aliases:
  - XSS 실무 방어
  - XSS 방어 실무
  - Output Encoding
  - HTML Sanitizer
tags:
  - 🏷️과목/웹보안
  - 🏷️주제/XSS
  - 🏷️주제/Secure-Coding
  - 🏷️상태/draft
---

# 실무형 XSS 방어

source:
- [OWASP Cross Site Scripting Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html)
- [OWASP DOM based XSS Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/DOM_based_XSS_Prevention_Cheat_Sheet.html)
- [MDN Set-Cookie](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Set-Cookie)
- [MDN Content Security Policy](https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/CSP)

## 한 줄 결론

실무에서 XSS 방어의 중심은 **위험해 보이는 입력을 지우는 것**이 아니라, **사용자 입력이 출력되는 위치에서 코드가 아니라 데이터로 해석되게 만드는 것**이다.

게시판 글처럼 그냥 텍스트로 보여주면 되는 값은 출력 시점에 인코딩한다. 사용자가 일부 HTML을 써야 하는 기능이라면 검증된 HTML sanitizer로 허용할 태그와 속성만 남긴다. Cookie 속성, CSP, WAF는 피해를 줄이는 보조 방어이지, 출력 처리 문제를 대신 고쳐주지는 않는다.

---

## 먼저 쉬운 그림으로 이해하기

브라우저는 HTML을 보면 “글자”와 “명령”을 구분해서 처리한다.

```text
안녕하세요
```

이건 그냥 화면에 보여줄 글자다.

```html
<script>...</script>
```

이건 브라우저 입장에서는 실행할 수 있는 명령이다.

XSS는 사용자가 쓴 값이 원래는 글자여야 하는데, 서버나 프론트엔드가 그 값을 HTML/JavaScript 안에 그대로 넣어서 브라우저가 명령으로 착각할 때 생긴다.

그래서 실무 방어의 핵심은 이것이다.

```text
사용자 입력을 믿지 않는다.
하지만 입력값을 무작정 지우는 게 아니라,
출력되는 위치에 맞게 안전한 글자로 바꿔서 보여준다.
```

예를 들어 사용자가 `<`를 입력했을 때, HTML 본문에서는 이것을 태그 시작으로 해석하지 못하도록 `&lt;`처럼 글자 데이터로 바꿔 출력한다. 그러면 화면에는 `<`가 보이지만 브라우저는 그것을 태그나 스크립트로 실행하지 않는다.

---

## 실무 판단표

| 상황 | 실무 방어 | 이유 |
|---|---|---|
| 게시글, 댓글, 닉네임처럼 일반 텍스트만 보여주면 됨 | 출력 인코딩 | 입력값을 코드가 아니라 화면용 글자로 만들면 된다. |
| 굵게, 줄바꿈, 링크 같은 일부 HTML을 허용해야 함 | HTML sanitizer allowlist | 모든 HTML을 막으면 기능이 깨지고, 모든 HTML을 허용하면 위험하다. 허용할 태그/속성만 남긴다. |
| JavaScript로 DOM에 사용자 값을 넣음 | 안전한 DOM sink 사용 | `innerHTML` 같은 곳은 HTML로 해석될 수 있으므로 `textContent` 같은 안전한 대입을 우선한다. |
| 세션 쿠키가 있음 | `HttpOnly`, `Secure`, `SameSite` | XSS 자체를 막지는 못하지만 Cookie 탈취와 세션 악용 피해를 줄인다. |
| 서비스 전체에 보조 방어를 깔고 싶음 | CSP | 인라인 스크립트, 외부 스크립트 로딩, `eval()` 같은 실행 경로를 제한해 피해를 줄인다. |
| 입력 형식이 정해져 있음 | 서버 측 입력 검증 | 길이, 타입, 허용 문자, URL scheme을 제한한다. 단독 XSS 방어로 보지는 않는다. |

---

## 출력 인코딩

출력 인코딩은 사용자가 넣은 값을 브라우저가 **코드가 아니라 데이터**로 읽게 만드는 처리다.

중요한 점은 “어디에 출력하느냐”에 따라 필요한 처리가 달라진다는 것이다.

| 출력 위치 | 방어 관점 |
|---|---|
| HTML 본문 | `<`, `>`, `&`, 따옴표 등을 HTML entity로 바꿔 태그로 해석되지 않게 한다. |
| HTML 속성 값 | 속성 탈출을 막기 위해 더 강하게 인코딩하고, 안전한 속성에만 사용자 값을 넣는다. |
| URL parameter | parameter 값만 URL encoding하고, 전체 URL을 통째로 인코딩하지 않는다. |
| `href`, `src` 같은 URL 속성 | URL encoding만 보지 말고 `http`, `https` 같은 허용 scheme인지도 검증한다. |
| JavaScript 문자열 | JavaScript 문자열 문맥에 맞게 인코딩하고, 가능하면 사용자 값을 직접 script 안에 넣지 않는다. |
| CSS 값 | 구조 검증과 CSS encoding이 필요하다. 가능하면 사용자 입력을 CSS 실행 문맥에 넣지 않는다. |

여기서 초보자가 가장 자주 놓치는 점은 **HTML 인코딩 하나로 모든 위치가 안전해지는 것이 아니라는 점**이다. HTML 본문에서 안전한 처리가 JavaScript 문자열이나 URL 속성에서도 그대로 안전하다고 보면 안 된다.

---

## HTML sanitizer

출력 인코딩은 사용자가 쓴 HTML을 “전부 글자”로 보여준다. 게시판이 일반 텍스트 게시판이면 이게 맞다.

하지만 사용자가 글에 `<b>`, `<p>`, `<br>`, `<a>` 같은 일부 HTML을 써야 하는 기능이라면 출력 인코딩만으로는 기능 요구사항을 만족하기 어렵다. 이때는 HTML sanitizer를 쓴다.

sanitizer의 핵심은 blacklist가 아니라 allowlist다.

```text
나쁜 걸 찾아서 지운다: 위험
허용한 것만 남긴다: 실무적으로 더 안전
```

실무에서는 직접 정규식으로 HTML을 파싱하려고 하지 않는다. HTML은 브라우저 해석 규칙이 복잡하고 예외가 많기 때문에, 검증된 sanitizer 라이브러리를 사용한다.

정리하면:

- HTML이 필요 없으면 sanitizer보다 출력 인코딩이 먼저다.
- HTML이 필요하면 허용할 태그와 속성을 명확히 정한다.
- event handler 속성, `javascript:` URL, 위험한 style, 위험한 iframe/embed는 기본적으로 제거 대상으로 본다.
- sanitizer를 적용한 뒤에도 출력 위치와 프레임워크 escaping 동작을 같이 봐야 한다.

---

## 안전한 DOM sink와 위험한 DOM sink

DOM-based XSS에서는 서버에 저장된 HTML보다, 브라우저에서 JavaScript가 DOM을 어떻게 조작하는지가 더 중요해진다.

쉬운 기준은 이것이다.

```text
사용자 값을 HTML로 해석시키는 곳은 위험하다.
사용자 값을 글자로만 넣는 곳은 상대적으로 안전하다.
```

| 구분 | 예 | 판단 |
|---|---|---|
| 상대적으로 안전한 sink | `textContent`, `innerText` | 값을 글자로 넣는다. HTML로 실행하지 않는다. |
| 주의가 필요한 sink | `setAttribute` | 안전한 속성에 제한해서 써야 한다. 이벤트 속성이나 URL 속성은 위험할 수 있다. |
| 위험한 sink | `innerHTML`, `outerHTML`, `document.write` | 문자열을 HTML로 해석하므로 사용자 입력을 넣으면 XSS가 되기 쉽다. |
| 피해야 할 실행 경로 | `eval()`, 문자열 기반 timer, 인라인 이벤트 핸들러 | 문자열을 코드처럼 실행할 수 있다. |

DOM 방어는 “필터를 더 세게 걸기”보다 **애초에 안전한 API를 쓰는 것**이 더 낫다.

---

## Cookie 속성은 방어가 아니라 피해 감소 장치

XSS 실습에서 `document.cookie`로 세션 토큰을 읽는 흐름을 봤다면, 실무에서는 먼저 `HttpOnly`를 떠올려야 한다.

| 속성 | 의미 | XSS 관점 |
|---|---|---|
| `HttpOnly` | JavaScript에서 해당 Cookie를 읽지 못하게 한다. | `document.cookie` 기반 세션 탈취를 줄인다. XSS 자체를 막지는 못한다. |
| `Secure` | HTTPS 요청에서만 Cookie를 보내게 한다. | 네트워크 평문 탈취 위험을 줄인다. JavaScript 접근 차단은 아니다. |
| `SameSite` | Cross-site 요청에서 Cookie 전송 범위를 줄인다. | CSRF 피해를 줄이는 데 중요하다. XSS 방어의 1차 수단은 아니다. |

중요한 정정:

```text
HttpOnly를 켜면 document.cookie 탈취는 어려워진다.
하지만 XSS가 사라지는 것은 아니다.
```

XSS가 있으면 여전히 화면 조작, 사용자 대신 요청 보내기, 피싱 UI 삽입, DOM 변조가 가능할 수 있다.

---

## CSP는 안전벨트다

CSP(Content Security Policy)는 브라우저에게 “어떤 스크립트를 실행해도 되는지” 알려주는 보안 정책이다.

실무에서 CSP는 중요하지만, CSP만 믿으면 안 된다.

| CSP가 잘하는 것 | 한계 |
|---|---|
| 인라인 스크립트 실행 제한 | 이미 취약한 출력 처리를 자동으로 고쳐주지는 않는다. |
| 허용된 script source 제한 | 허용된 스크립트가 취약하게 DOM을 조작하면 여전히 위험하다. |
| `eval()` 같은 실행 방식 제한 | 기존 코드 리팩터링 비용이 생길 수 있다. |
| nonce/hash 기반 정책으로 스크립트 신뢰 관리 | 설정이 느슨하면 효과가 크게 줄어든다. |

좋은 순서는 보통 이렇다.

```text
1. 출력 인코딩 / sanitizer / 안전한 DOM API로 원인을 고친다.
2. Cookie 속성으로 세션 피해를 줄인다.
3. CSP로 실행 경로를 한 번 더 제한한다.
4. 로그와 모니터링으로 우회나 정책 위반을 관찰한다.
```

---

## 프레임워크 escaping을 믿되, 끄는 순간 책임은 개발자에게 온다

현대 웹 프레임워크는 기본적으로 템플릿 출력값을 escape해주는 경우가 많다. 그래서 단순히 `{{ userInput }}`처럼 출력하면 HTML이 실행되지 않고 글자로 보이는 경우가 많다.

하지만 개발자가 “이 값은 HTML로 넣을래”라고 지시하는 기능을 쓰면 기본 보호가 꺼진다.

예:

| 계열 | 위험 신호 |
|---|---|
| React | `dangerouslySetInnerHTML` |
| Vue | `v-html` |
| Angular | `bypassSecurityTrust...` 류 API |
| 서버 템플릿 | raw/unescaped 출력 문법 |

이런 기능이 보이면 코드 리뷰에서 바로 질문해야 한다.

```text
이 HTML은 어디서 왔는가?
sanitizer를 거쳤는가?
허용 태그/속성 목록이 있는가?
정말 HTML 출력이 필요한가?
그냥 텍스트 출력이면 안 되는가?
```

---

## XSS 유형별 실무 관점

| 유형 | 주로 봐야 할 지점 | 실무 방어 |
|---|---|---|
| Stored XSS | DB나 파일에 저장된 사용자 입력이 다시 출력되는 지점 | 저장값을 믿지 말고 출력 시 인코딩한다. HTML 허용 기능이면 sanitizer를 둔다. |
| Reflected XSS | query parameter, form 값, error message가 응답에 바로 반사되는 지점 | 응답에 넣는 모든 사용자 입력을 문맥별로 인코딩한다. |
| DOM-based XSS | URL fragment/query/localStorage 값을 JavaScript가 DOM에 넣는 지점 | `innerHTML`, `document.write`, `eval()`류를 피하고 안전한 sink를 쓴다. |
| Cookie stealing | XSS로 `document.cookie`를 읽어 외부로 보내는 흐름 | `HttpOnly`로 Cookie 읽기를 막고, XSS 원인은 별도로 제거한다. |
| Session Hijacking | 탈취된 세션 토큰을 재사용하는 흐름 | `HttpOnly`, `Secure`, 세션 재발급, 만료, 이상 행위 탐지를 함께 본다. |

---

## 코드 리뷰 체크리스트

사용자 입력이 화면에 나오는 코드를 보면 다음 순서로 본다.

1. 이 값은 어디서 왔는가?
2. 이 값은 어디에 출력되는가?
3. 출력 위치가 HTML 본문인가, 속성인가, URL인가, JavaScript인가, CSS인가?
4. 프레임워크가 자동 escaping을 해주는 위치인가?
5. raw HTML 출력 기능을 쓰고 있지는 않은가?
6. HTML 허용이 필요하다면 sanitizer allowlist가 있는가?
7. DOM 조작에서 `innerHTML`, `document.write`, `eval()` 같은 위험한 sink를 쓰고 있지는 않은가?
8. 세션 Cookie에 `HttpOnly`, `Secure`, `SameSite`가 붙어 있는가?
9. CSP가 보조 방어로 설정되어 있는가?
10. XSS 방어를 WAF나 blacklist 필터에만 맡기고 있지는 않은가?

---

## 오해하기 쉬운 지점

| 오해 | 정정 |
|---|---|
| 입력할 때 막으면 끝난다 | 저장된 값도 다른 위치에 출력될 수 있으므로 출력 시점 방어가 중요하다. |
| `<script>`만 지우면 된다 | XSS 실행 문맥은 태그, 속성, URL, CSS, DOM sink 등 다양하다. |
| HTML 인코딩 하나면 어디서든 안전하다 | 출력 문맥마다 필요한 인코딩이 다르다. |
| sanitizer는 모든 문제를 해결한다 | HTML 허용이 필요한 경우의 도구다. 일반 텍스트 출력에는 출력 인코딩이 더 단순하고 안전하다. |
| `HttpOnly`면 XSS가 막힌다 | Cookie 읽기 피해를 줄일 뿐, 브라우저 안에서 실행되는 악성 동작 자체를 막지는 못한다. |
| CSP가 있으면 코드 수정이 덜 중요하다 | CSP는 보조 방어다. 취약한 출력 처리는 코드에서 고쳐야 한다. |

---

## 관련 노트

- [[10_학습 노트/시스템보안/웹보안/XSS|XSS]]
- [[10_학습 노트/시스템보안/웹보안/XSS를 이용한 Session Token 탈취 실습|XSS를 이용한 Session Token 탈취 실습]]
- [[10_학습 노트/시스템보안/웹보안/Web Session Hijacking|Web Session Hijacking]]
- [[10_학습 노트/시스템보안/웹보안/HTML 인코딩|HTML 인코딩]]

---

## 확인 질문

1. 일반 텍스트 게시판에서 출력 인코딩이 sanitizer보다 먼저 떠올라야 하는 이유는 무엇인가?
2. HTML 본문에서 안전한 인코딩이 JavaScript 문자열 안에서도 그대로 안전하다고 볼 수 없는 이유는 무엇인가?
3. `innerHTML`과 `textContent`는 사용자 입력 처리 관점에서 무엇이 다른가?
4. `HttpOnly`는 XSS를 막는가, 아니면 XSS 피해 일부를 줄이는가?
5. CSP를 “1차 방어”가 아니라 “보조 방어”라고 보는 이유는 무엇인가?
