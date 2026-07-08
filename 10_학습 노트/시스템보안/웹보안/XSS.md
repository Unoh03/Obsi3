---
type: concept
topic: web-security
source:
  - 5-20_웹보안.pdf
  - OWASP Cross Site Scripting Prevention Cheat Sheet
  - OWASP DOM based XSS Prevention Cheat Sheet
source_pages:
  - 83
  - 84
  - 85
  - 86
  - 87
  - 88
  - 89
  - 90
  - 91
  - 92
  - 93
  - 94
  - 95
  - 96
  - 97
status: active
created: 2026-05-22
reviewed: 2026-07-08
aliases:
  - Cross Site Scripting
  - 크로스 사이트 스크립팅
  - Reflected XSS
  - Stored XSS
  - DOM-based XSS
  - Cookie Stealing
  - XSS 필터링 우회
tags:
  - 🏷️과목/웹보안
  - 🏷️주제/XSS
  - 🏷️주제/Client-Side
  - 🏷️상태/active
---

# XSS

source:

- [[40_자료/강의 자료/5-20_웹보안.pdf|5-20 웹보안]], p.83-97
- [OWASP Cross Site Scripting Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html)
- [OWASP DOM based XSS Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/DOM_based_XSS_Prevention_Cheat_Sheet.html)

## 한 줄 요약

XSS(Cross Site Scripting)는 **사용자 입력이 HTML/JavaScript 문맥에 안전하지 않게 출력되어, 피해자 브라우저에서 공격자가 넣은 스크립트가 실행되는 취약점**이다.

서버를 직접 장악하지 않아도 서버가 만든 정상 페이지 안에서 스크립트가 실행되기 때문에, 피해자 브라우저는 그 스크립트를 해당 웹 사이트의 코드처럼 취급한다. 그래서 Cookie 접근, DOM 조작, 키 입력 탈취, 세션 탈취 같은 문제가 이어질 수 있다.

---

## 먼저 잡아야 할 핵심

- XSS는 서버를 우회 경유지로 삼아 **클라이언트 브라우저를 공격하는 취약점**이다.
- 근본 원인은 사용자 입력을 Web Document에 출력할 때 적절한 검증/인코딩을 하지 않는 것이다.
- 입력 검증만으로는 부족하고, 출력 위치에 맞는 **context-aware output encoding**이 필요하다.
- PDF는 `Reflective XSS`와 `Stored XSS`를 다루고, 공식 문서 기준으로는 `DOM-based XSS`도 별도로 이해해야 한다.
- XSS는 [[10_학습 노트/시스템보안/웹보안/Web Session Hijacking|Web Session Hijacking]]의 Session Token 탈취 경로가 될 수 있다.

---

## PDF 내용 분해

| page | PDF 핵심 | 정리 |
|---|---|---|
| p.83 | Preface | 동적 웹과 사용자 입력이 늘면서 XSS가 중요해졌다. 서버 장악 없이 개인정보 유출이 가능하다. |
| p.84 | Main Cause / Impact | 검증 없이 Web Document에 출력할 때 발생한다. Cookie, DOM, Clipboard, Key logging 영향이 있다. |
| p.85 | Type of XSS | Reflective XSS와 Stored XSS를 구분한다. |
| p.86 | Reflective XSS flow | 악성 스크립트가 포함된 요청을 서버가 반사해 응답하고, 피해자 브라우저에서 실행된다. |
| p.87 | Stored XSS flow | 악성 스크립트가 서버에 저장되고, 이후 피해자가 해당 게시물/페이지를 볼 때 실행된다. |
| p.88-91 | 취약한 페이지 유형 | HTML 게시판, 검색, 개인화 페이지, Referer 표시 페이지, 회원가입 폼 등 사용자 입력을 다시 출력하는 곳이 위험하다. |
| p.92 | XSS에 쓰일 수 있는 스크립트 형태 | `<script>`, 이미지/스타일/iframe/embed 등 여러 HTML/JS 실행 지점이 있다. |
| p.93 | Filtering 우회 | URL encoding, HTML entity, 개행/제어문자 등 다양한 표현으로 단순 필터를 우회할 수 있다. |
| p.94-95 | Cookie Stealing 실습 | `document.cookie`를 외부 요청에 붙여 보내고 서버가 저장하는 구조를 보여준다. 노트에서는 방어 관점으로만 다룬다. |
| p.96 | Server 대응책 | 입력 검증, white list, 출력 인코딩, 필요한 HTML만 허용, `HttpOnly`, TRACE 금지 등을 제시한다. |
| p.97 | Client 대응책 | 수상한 링크 회피, 브라우저/플러그인 보안 설정, 패치, 비밀번호 재사용 금지 등을 제시한다. |

---

## XSS가 생기는 위치

XSS는 다음 흐름에서 생긴다.

```text
1. 사용자 입력이 서버로 들어간다.
2. 서버가 그 입력을 저장하거나 응답에 다시 넣는다.
3. 응답 HTML/JavaScript 문맥에서 입력값이 코드처럼 해석된다.
4. 피해자 브라우저가 그 코드를 현재 사이트의 권한으로 실행한다.
```

중요한 지점은 3번이다. 같은 문자열이라도 HTML 본문, HTML attribute, URL, CSS, JavaScript 문자열 안에서 필요한 방어가 다르다.

---

## XSS 유형

| 유형 | 저장 여부 | 실행 흐름 | 예 |
|---|---|---|---|
| Reflective XSS | 서버에 저장되지 않음 | 악성 입력이 요청에 들어가고, 서버 응답에 바로 반사되어 실행됨 | 검색어, 에러 메시지, URL parameter |
| Stored XSS | 서버에 저장됨 | 악성 입력이 게시글/프로필 등에 저장되고, 다른 사용자가 볼 때 실행됨 | 게시판, 방명록, 댓글, 프로필 |
| DOM-based XSS | 서버 응답 HTML보다 브라우저 DOM 조작이 핵심 | 클라이언트 JavaScript가 URL fragment, query, storage 등의 값을 위험한 DOM sink에 넣어 실행됨 | `innerHTML`, `document.write` 등 위험한 sink |

PDF는 Reflective와 Stored를 중심으로 설명한다. DOM-based XSS는 p.84의 DOM Access, p.94의 `document.cookie`와 이어지므로 같이 기억하는 편이 좋다.

---

## Reflective XSS

```text
Attacker
  -> 악성 입력이 포함된 URL을 Victim에게 전달
Victim
  -> URL 클릭 또는 요청 전송
Web Server
  -> 입력값을 응답 HTML에 반사
Victim Browser
  -> 응답 안의 스크립트 실행
```

Reflective XSS는 서버에 저장되지 않기 때문에 “한 번 눌렀을 때 실행되는 링크형 공격”처럼 보이기 쉽다. 하지만 본질은 링크가 아니라 **요청 값이 응답에 안전하지 않게 반사되는 것**이다.

---

## Stored XSS

```text
Attacker
  -> 게시글/댓글/프로필 등에 악성 입력 저장
Web Server
  -> 악성 입력을 DB나 파일에 저장
Victim
  -> 해당 페이지 열람
Web Server
  -> 저장된 값을 응답에 포함
Victim Browser
  -> 저장된 스크립트 실행
```

Stored XSS는 피해자가 공격 링크를 직접 받지 않아도 된다. 많은 사용자가 보는 게시판, 공지, 댓글, 프로필에 들어가면 피해 범위가 커진다.

---

## 취약한 페이지 유형

| 페이지 유형 | 왜 위험한가 |
|---|---|
| HTML 지원 게시판 | 사용자가 HTML처럼 보이는 내용을 올리고 다른 사용자가 열람한다. |
| Search Page | 검색어를 결과 페이지에 다시 출력한다. |
| Personalize Page | 사용자 이름, 별명, 상태 메시지 등을 화면에 반영한다. |
| Join Form Page | 가입 실패 시 사용자가 입력한 값을 다시 보여준다. |
| Referer 이용 Page | 이전 페이지 값을 그대로 출력하면 조작된 `Referer`가 화면에 나타날 수 있다. |
| 그 외 입력 출력 페이지 | 입력을 받아 화면에 다시 표시하는 모든 지점은 후보가 된다. |

이 목록은 “이 페이지만 위험하다”가 아니라 “사용자 입력을 다시 출력하는 곳을 찾아라”는 탐색 기준이다.

---

## 필터링 우회가 가능한 이유

PDF는 URL encoding, HTML entity, 개행/제어문자 같은 표현을 이용해 단순 필터를 우회할 수 있다고 설명한다.

정확한 의미는 다음과 같다.

```text
브라우저와 서버는 같은 문자를 여러 표현으로 해석할 수 있다.
단순히 문자열 "<script>"만 지우는 필터는 다른 표현, 다른 태그, 다른 문맥에서 쉽게 깨질 수 있다.
```

따라서 XSS 방어는 blacklist로 특정 문자열만 막는 방식보다 다음 순서가 더 중요하다.

1. 입력값의 형식과 허용 범위를 검증한다.
2. HTML을 허용하지 않아도 되는 곳은 텍스트로만 출력한다.
3. 출력 위치에 맞게 인코딩한다.
4. 꼭 HTML을 허용해야 한다면 검증된 HTML sanitizer와 allowlist를 사용한다.

---

## Cookie Stealing 실습의 의미

PDF p.94-95는 XSS로 `document.cookie`를 읽어 공격자 서버로 보내고, 서버가 그 값을 파일에 저장하는 구조를 보여준다.

이 노트에서는 악용 가능한 코드 전문을 재현하지 않고 구조만 남긴다.

실제 실습 기록은 [[10_학습 노트/시스템보안/웹보안/XSS를 이용한 Session Token 탈취 실습|XSS를 이용한 Session Token 탈취 실습]]에 따로 정리한다.

```text
1. 피해자 브라우저에서 스크립트가 실행된다.
2. 스크립트가 document.cookie 값을 읽는다.
3. 외부 서버로 cookie 값을 포함한 요청을 보낸다.
4. 외부 서버가 전달받은 값을 저장한다.
```

이 실습이 보여주는 핵심은 “XSS가 있으면 Cookie가 노출될 수 있다”는 점이다. 그래서 세션 쿠키에는 `HttpOnly`를 설정하고, 애초에 XSS가 생기지 않도록 출력 인코딩과 HTML sanitizer를 적용해야 한다.

---

## XSS 방어의 우선순위

PDF p.96은 Server 대응책, p.97은 Client 대응책으로 나누지만, 실제로는 **예방책**, **보조 통제**, **피해 완화책**, **사용자/브라우저 위생**이 섞여 있다. 실습에서 확인한 기준으로 다시 나누면 아래 순서가 더 이해하기 쉽다.

### 1. 실행 자체를 막는 핵심 방어

XSS의 본질은 사용자가 넣은 문자열이 브라우저에서 HTML/JavaScript 코드로 해석되는 것이다. 따라서 핵심 방어는 브라우저가 그 값을 코드가 아니라 데이터로 보게 만드는 것이다.

| 방어 | 의미 | 실습에서 연결된 점 |
|---|---|---|
| 출력 문맥별 인코딩 | HTML 본문, HTML 속성, JavaScript 문자열, CSS, URL 문맥에 맞게 다르게 인코딩한다. | `view.php`에서 출력 직전에 `htmlspecialchars()`를 적용하는 방향 |
| 안전한 sink 사용 | DOM을 바꿀 때 `innerHTML` 같은 위험한 sink 대신 text 처리 API를 사용한다. | 같은 값이라도 어디에 넣느냐에 따라 실행 여부가 달라진다는 점 |
| HTML sanitizer | HTML 일부를 허용해야 할 때 허용된 태그/속성만 남긴다. | `<b>`, `<br>`은 허용하고 `<script>`, 이벤트 속성은 제거해야 하는 경우 |

> [!important] 실습에서 얻은 기준
> `writeModel.php`에서 저장 전에 바꾸는 방식은 수업용 원리 확인에는 좋다. 하지만 일반 텍스트 게시판의 실무 기본값은 **DB에는 원본에 가깝게 저장하고, `view.php`에서 출력 직전에 문맥별 인코딩**하는 쪽이다. 저장 시점과 출력 시점에서 둘 다 인코딩하면 `&lt;`가 `&amp;lt;`로 보이는 이중 인코딩이 생길 수 있다.

OWASP 기준으로도 “출력 위치에 맞는 encoding”이 핵심이다. HTML 본문, HTML attribute, JavaScript, CSS, URL은 각각 안전하게 처리하는 방식이 다르다.

출력 인코딩을 적용할 때는 응답의 charset/code page도 명확히 지정해야 한다. 같은 바이트라도 브라우저가 다른 문자 체계로 해석하면 필터링이나 인코딩 의도와 다르게 처리될 수 있으므로, PDF의 `ISO 8859-1`, `UTF-8` 언급은 “브라우저가 어떤 문자 체계로 해석할지도 서버가 분명히 알려야 한다”는 뜻으로 보면 된다.

### 2. 공격 표면을 줄이는 보조 방어

입력 검증은 필요하지만, 입력 검증만으로 XSS 방어를 끝내면 안 된다. 공격자는 `<script>` 말고도 이미지, iframe, 이벤트 속성, 인코딩 변형, DOM sink 등 다양한 실행 경로를 찾을 수 있다.

| 방어 | 의미 | 한계 |
|---|---|---|
| 입력값 검증 | 길이, 형식, 허용 문자, URL scheme 등을 제한한다. | 출력 문맥이 안전하지 않으면 여전히 XSS가 가능하다. |
| allowlist | 허용할 값, 태그, 속성, URL scheme을 명확히 정한다. | HTML을 허용하는 경우 sanitizer와 함께 설계해야 한다. |
| HTML 기능 최소화 | 게시판 등에서 HTML 입력 기능을 아예 줄인다. | 리치 텍스트가 필요한 서비스에서는 별도 sanitizer가 필요하다. |
| 프레임워크 escaping 유지 | 템플릿 엔진의 자동 escape 기능을 끄지 않는다. | `dangerouslySetInnerHTML`, `innerHTML` 같은 escape 우회 지점은 여전히 위험하다. |

실습에서 `<script>`만 `str_replace()`로 깨는 방식은 이번 payload에는 통했지만, 방어 기준으로는 너무 좁다. 반대로 `<`, `>` 인코딩과 `htmlspecialchars()`는 “태그로 해석되는 것” 자체를 막는 방향이라 원리에 더 가깝다.

### 3. 피해를 줄이는 방어

아래 항목들은 중요하지만 XSS 실행 자체를 막는 1차 방어는 아니다. XSS가 발생했을 때 세션 탈취나 피해 확산을 줄이는 역할에 가깝다.

| 방어 | 줄이는 위험 | 주의할 점 |
|---|---|---|
| `HttpOnly` | JavaScript가 세션 Cookie를 직접 읽는 위험 | `document.cookie` 기반 탈취는 줄지만 DOM 조작, 사용자 권한 요청은 여전히 가능하다. |
| `Secure`, HTTPS | 네트워크에서 Cookie가 평문으로 오가는 위험 | XSS 실행 자체를 막지는 않는다. |
| `SameSite` | Cross-site 요청에서 Cookie가 자동 전송되는 범위 | 주로 CSRF와 연결된다. XSS 자체의 직접 방어는 아니다. |
| Cookie에 민감정보 저장 금지 | Cookie 탈취 시 개인정보나 권한 정보가 바로 노출되는 위험 | Cookie에는 개인정보를 직접 넣지 말고, 서버 측 세션 저장소를 가리키는 식별자만 두는 편이 안전하다. |
| Session과 IP 묶기 | 탈취한 Session Token을 다른 위치에서 재사용하는 위험 | 다른 IP에서 같은 세션이 쓰이면 의심할 수 있다. 단, NAT, 모바일망, 프록시 환경에서는 오탐과 사용성 문제가 생길 수 있다. |
| CSP | 인라인 스크립트, 외부 스크립트 로딩 등 일부 실행 경로 | 좋은 보조 방어지만 인코딩/검증을 대체하지 않는다. |
| TRACE Method 금지 | XST 같은 오래된 공격면 | 최신 XSS 방어의 중심은 아니지만 불필요한 method는 줄이는 편이 좋다. |

이번 Cookie Stealing 실습은 이 구분을 잘 보여준다. `HttpOnly`가 없으면 XSS로 `document.cookie`를 읽을 수 있다. 하지만 `HttpOnly`를 켜도 XSS 취약점 자체가 사라지는 것은 아니므로, 근본 방어는 여전히 출력 인코딩과 안전한 HTML 처리다.

### 4. 사용자/브라우저 측 보조 대응

PDF p.97의 Client 대응책은 “사용자가 조심하면 XSS가 해결된다”는 뜻이 아니다. 공격 유도 가능성이나 피해 확산을 줄이는 보조 조언에 가깝다.

| PDF 표현 | 현재식 해석 |
|---|---|
| 링크를 클릭하지 말고 직접 URL 입력 | 수상한 링크로 들어가는 Reflective XSS 유도를 줄이려는 의도다. |
| Flash 디폴트 실행 금지 | 플러그인 기반 공격 표면을 줄이려는 오래된 환경의 조언이다. 현대 브라우저에서는 Flash 자체가 사실상 퇴장했다. |
| 브라우저 개인 정보 등급 상향 | 불필요한 쿠키 전송과 추적을 줄이려는 의도다. |
| Internet Explorer 최신 패치 | 브라우저 취약점과 스크립트 실행 취약점을 줄이려는 의도다. 현대 환경에서는 지원되는 최신 브라우저 사용으로 바꿔 이해하면 된다. |
| 동일 패스워드 사용 금지 / 주기적 변경 | XSS만의 직접 방어는 아니지만 계정 탈취 피해 확산을 줄이려는 계정 보안 조언이다. |

최종 정리는 이렇다.

```text
XSS의 1차 책임: 서버와 프론트엔드가 사용자 입력을 안전하게 출력해야 함
사용자/브라우저 대응: 공격 가능성과 피해 범위를 줄이는 보조 수단
```

실무형 방어 판단 기준은 [[10_학습 노트/시스템보안/웹보안/실무형 XSS 방어|실무형 XSS 방어]]에 따로 정리한다.

---

## 이 vault에서 쓰는 법

- 이 노트는 `5-20_웹보안.pdf` p.83-97의 stable concept note로 쓴다.
- Cookie Stealing과 세션 재사용 실습 증거는 [[10_학습 노트/시스템보안/웹보안/XSS를 이용한 Session Token 탈취 실습|XSS를 이용한 Session Token 탈취 실습]]에 둔다.
- 실무 방어 기준은 [[10_학습 노트/시스템보안/웹보안/실무형 XSS 방어|실무형 XSS 방어]]에서 본다.
- 출력 인코딩과 문자 해석 문제는 [[10_학습 노트/시스템보안/웹보안/HTML 인코딩|HTML 인코딩]]에서 본다.
- 세션 탈취와 연결되는 지점은 [[10_학습 노트/시스템보안/웹보안/Web Session Hijacking|Web Session Hijacking]]에서 본다.
- PDF 순서로 이어서 볼 다음 범위는 [[10_학습 노트/시스템보안/웹보안/CSRF|CSRF]] p.98-106이다.

---

## 강사님/PDF 표현 의도 추론

| 표현 | 의도 | 정확한 정리 |
|---|---|---|
| “서버를 장악하지 않고도 개인정보 유출” | XSS의 위험을 직관적으로 강조하려는 표현 | 서버 권한을 얻지 않아도 브라우저가 사이트 권한으로 스크립트를 실행하므로 사용자 정보와 세션이 위험해진다. |
| “서버를 경유하여 클라이언트를 공격” | XSS의 공격 대상이 서버가 아니라 브라우저임을 설명하려는 표현 | 취약점은 서버의 출력 처리에 있지만, 실행과 피해는 클라이언트 브라우저에서 발생한다. |
| “스크립트 무효화 / 필터링” | 입력에서 위험한 스크립트 실행을 막으려는 표현 | 단순 문자열 제거가 아니라 문맥별 출력 인코딩, allowlist sanitizer, 안전한 DOM API 사용이 필요하다. |
| “중요한 정보는 쿠키에 저장하지 않기” | 탈취 시 피해를 줄이려는 표현 | 클라이언트 쿠키에는 민감정보를 직접 담지 말고, 서버 측 세션 저장소의 식별자만 두는 편이 안전하다. |

---

## 오해하기 쉬운 지점

| 오해 | 정정 |
|---|---|
| XSS는 서버 공격이다 | XSS는 서버의 출력 취약점을 통해 브라우저에서 실행되는 클라이언트 공격이다. |
| `<script>`만 막으면 된다 | 태그, 속성, URL, CSS, DOM sink 등 실행 문맥이 다양하므로 단순 필터는 부족하다. |
| 입력 검증만 하면 된다 | 입력 검증은 필요하지만, 최종 방어는 출력 문맥에 맞는 encoding과 안전한 sink 사용이다. |
| `HttpOnly`면 XSS가 해결된다 | 쿠키 직접 탈취를 줄일 뿐, DOM 조작이나 사용자 권한 요청은 여전히 가능하다. |
| WAF가 있으면 코드 수정이 필요 없다 | WAF는 보조 방어다. 애플리케이션의 출력 처리 문제를 대신 고쳐주지는 못한다. |

---

## 관련 노트

- [[10_학습 노트/시스템보안/웹보안/XSS를 이용한 Session Token 탈취 실습|XSS를 이용한 Session Token 탈취 실습]]
- [[10_학습 노트/시스템보안/웹보안/실무형 XSS 방어|실무형 XSS 방어]]
- [[10_학습 노트/시스템보안/웹보안/Web Session Hijacking|Web Session Hijacking]]
- [[10_학습 노트/시스템보안/웹보안/HTML 인코딩|HTML 인코딩]]
- [[10_학습 노트/시스템보안/웹보안/HTTP 구조와 메시지|HTTP 구조와 메시지]]
- [[10_학습 노트/시스템보안/웹보안/웹 애플리케이션 구조|웹 애플리케이션 구조]]

---

## 참고 자료

- [OWASP Cross Site Scripting Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html)
- [OWASP DOM based XSS Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/DOM_based_XSS_Prevention_Cheat_Sheet.html)
- [OWASP Session Management Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html)

---

## 확인 질문

1. XSS는 서버 공격인가, 클라이언트 공격인가?
2. Reflective XSS와 Stored XSS는 무엇이 다른가?
3. Search Page와 Join Form Page가 왜 XSS 후보가 되는가?
4. 단순히 `<script>` 문자열을 막는 필터가 왜 부족한가?
5. `HttpOnly`는 XSS를 막는가, 아니면 피해를 줄이는가?
6. XSS와 Session Hijacking은 어떻게 연결되는가?
