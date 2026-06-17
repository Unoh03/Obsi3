---
type: concept
topic: web-security
source: 5-20_웹보안.pdf
source_pages:
  - 40
status: draft
created: 2026-05-27
reviewed:
aliases:
  - HTML Encoding
  - HTML Entity Encoding
  - HTML Character Reference
  - 출력 인코딩
tags:
  - 🏷️과목/웹보안
  - 🏷️주제/Encoding
  - 🏷️주제/XSS
  - 🏷️상태/draft
---

# HTML 인코딩

source: [[40_자료/강의 자료/5-20_웹보안.pdf|5-20 웹보안]], p.40

## 한 줄 요약

HTML 인코딩은 `<`, `>`, `"`, `'`, `&`처럼 HTML에서 특별한 의미를 갖는 문자를 **브라우저가 태그나 코드가 아니라 화면에 보여줄 글자로 해석하게 바꾸는 방법**이다.

XSS 관점에서는 “나쁜 문자열을 지운다”보다 “브라우저가 이 값을 코드로 실행하지 못하게 한다”가 핵심이다.

---

## 왜 XSS 방어와 연결되는가

브라우저는 응답 HTML 안의 `<script>`, `<img>`, `<iframe>` 같은 문자열을 단순한 글자가 아니라 HTML 태그로 해석한다. 그래서 사용자가 입력한 값이 게시글, 댓글, 검색 결과, 에러 메시지에 그대로 출력되면 XSS가 생길 수 있다.

HTML 인코딩을 적용하면 같은 입력도 이렇게 바뀐다.

```html
<script>alert(1)</script>
```

```html
&lt;script&gt;alert(1)&lt;/script&gt;
```

브라우저는 두 번째 값을 script 태그로 실행하지 않고, 화면에 `<script>alert(1)</script>`라는 글자로 보여준다.

---

## PDF p.40 HTML Encoding 표

PDF p.40은 HTML 문서 안에서 특별한 기능을 수행하는 문자를 안전하게 표현하기 위해 HTML Encoding을 사용한다고 설명한다. 같은 문자는 이름이 붙은 상수, 10진수 문자 참조, 16진수 문자 참조로 표현할 수 있다.

| 문자 | 이름 기반 상수 | 10진수 문자 참조 | 16진수 문자 참조 |
|---|---|---|---|
| 공백 | `&nbsp;` | `&#32;` | `&#x20;` |
| `<` | `&lt;` | `&#60;` | `&#x3c;` |
| `>` | `&gt;` | `&#62;` | `&#x3e;` |
| `"` | `&quot;` | `&#34;` | `&#x22;` |
| `'` | `&apos;` | `&#39;` | `&#x27;` |
| `&` | `&amp;` | `&#38;` | `&#x26;` |

정리하면 세 방식은 모두 “문자를 다른 표기법으로 적는 방법”이다.

| 방식 | 예시 | 의미 |
|---|---|---|
| Named character reference | `&lt;` | 이름으로 문자를 표현 |
| Decimal numeric character reference | `&#60;` | 10진수 코드값으로 문자를 표현 |
| Hexadecimal numeric character reference | `&#x3c;` | 16진수 코드값으로 문자를 표현 |

---

## XSS 방어에서 특히 중요한 문자

일반 텍스트를 HTML 본문에 출력할 때는 최소한 아래 문자들을 안전하게 처리해야 한다.

| 문자 | 인코딩 예 | 중요한 이유 |
|---|---|---|
| `&` | `&amp;` | 다른 entity를 만들거나 기존 entity 해석에 영향을 줄 수 있다. |
| `<` | `&lt;` | HTML 태그 시작으로 해석될 수 있다. |
| `>` | `&gt;` | HTML 태그 끝으로 해석될 수 있다. |
| `"` | `&quot;` | 큰따옴표 attribute 밖으로 탈출하는 데 쓰일 수 있다. |
| `'` | `&#x27;` 또는 `&#39;` | 작은따옴표 attribute나 JavaScript 문자열 밖으로 탈출하는 데 쓰일 수 있다. |

수업 실습에서 `<`와 `>`만 바꿔도 `<script>`, `<img>`, `<iframe>` 같은 태그형 payload는 글자로 바뀐다. 다만 attribute, URL, JavaScript 문자열, CSS 안에 들어가는 값은 필요한 인코딩 방식이 달라질 수 있다.

---

## `str_replace` 실습 관점

강사님이 `str_replace`를 쓰라고 한 것은 “문자열이 브라우저에서 어떻게 해석되는가”를 직접 확인하기 위한 수업용 방식으로 보는 편이 맞다.

| 방식 | 예 | 평가 |
|---|---|---|
| 특정 문자열 제거 | `<script>`만 삭제 또는 치환 | 아주 좁다. `<img onerror=...>`, `<iframe>`, 대소문자 변형, 중첩 문자열, 인코딩 변형을 놓칠 수 있다. |
| `<`, `>` 인코딩 | `<`를 `&#60;`, `>`를 `&#62;`로 치환 | 태그 시작과 끝을 글자로 바꾸므로 수업의 Stored XSS payload를 막는 데 더 본질적이다. |
| 위험 태그만 선별 치환 | `<script>`, `<iframe>` 등만 골라 치환 | 직접 구현하면 빠뜨리기 쉽다. 실무에서는 문자열 치환보다 HTML parser 기반 sanitizer가 맡아야 하는 영역이다. |

즉 “보안 위험 태그만 골라 `str_replace`”는 최선이 아니다. 그 방식은 sanitizer를 손으로 흉내 내는 것에 가깝고, HTML 문법의 예외와 우회를 감당하기 어렵다.

---

## 저장 전 치환과 출력 전 인코딩

수업 실습에서는 `writeModel.php`에서 DB 저장 전에 값을 바꿔도 된다. 실습 목표가 “악성 게시글을 새로 저장했을 때 브라우저에서 실행되지 않게 되는가”를 보는 것이기 때문이다.

```text
사용자 입력
-> writeModel.php에서 str_replace
-> DB에는 치환된 문자열 저장
-> view.php에서 글을 열람해도 script가 실행되지 않음
```

실무에서 일반 텍스트 게시판은 보통 관점이 다르다.

```text
사용자 입력은 데이터로 저장
-> 화면에 출력하는 순간 문맥에 맞게 인코딩
-> 브라우저가 코드가 아니라 텍스트로 해석
```

이 차이가 중요한 이유:

- 저장 전 치환은 원본 데이터가 사라진다.
- 같은 데이터라도 HTML 본문, HTML 속성, JavaScript 문자열, URL에서 필요한 처리가 다르다.
- 출력 지점이 여러 곳이면 각 출력 문맥에서 안전하게 처리해야 한다.

---

## 문맥별 출력 인코딩

OWASP는 브라우저가 HTML, attribute, JavaScript, CSS, URL을 서로 다르게 해석하므로 출력 위치에 맞는 인코딩을 적용해야 한다고 정리한다.

| 출력 위치 | 예 | 필요한 처리 방향 |
|---|---|---|
| HTML 본문 | `<div>사용자 입력</div>` | HTML entity encoding |
| HTML attribute | `<input value="사용자 입력">` | attribute 값을 따옴표로 감싸고 HTML attribute encoding |
| URL parameter | `<a href="/search?q=사용자 입력">` | URL encoding 후, HTML attribute 문맥이면 attribute encoding도 고려 |
| JavaScript 문자열 | `<script>var x = '사용자 입력';</script>` | 가능하면 넣지 않는다. 꼭 필요하면 quoted data value 안에서 JavaScript encoding |
| CSS 값 | `<span style="width: 사용자 입력">` | 가능하면 넣지 않는다. 꼭 필요하면 CSS property value로 제한하고 CSS encoding/검증 |
| 위험 문맥 | `<script>직접 삽입</script>`, HTML 주석, 이벤트 핸들러 | 인코딩만 믿지 말고 untrusted data를 넣지 않는 쪽이 맞다. |

---

## PHP에서는 보통 무엇을 쓰는가

PHP에서 HTML 본문이나 attribute에 일반 텍스트를 출력할 때는 직접 `str_replace`를 여러 번 이어 붙이기보다 `htmlspecialchars()` 같은 표준 함수를 쓰는 편이 안전하다.

핵심 의미:

```text
특수 문자를 HTML entity로 바꿔서
브라우저가 태그/속성/코드가 아니라 글자로 해석하게 만든다.
```

단, 이 함수도 “어디에 출력하는가”를 대신 판단해주지는 않는다. URL, JavaScript, CSS, HTML sanitizer가 필요한 상황은 별도로 봐야 한다.

---

## HTML Sanitizer가 필요한 경우

일반 텍스트 게시판이면 HTML 전체를 글자로 보여주는 출력 인코딩이 기본 방향이다.

하지만 사용자가 일부 HTML을 쓸 수 있게 하고 싶다면 단순 인코딩만으로는 목적이 맞지 않는다.

```html
<b>중요</b>
```

이 값을 모두 인코딩하면 굵은 글씨가 아니라 `<b>중요</b>`라는 글자로 보인다. 이럴 때는 allowlist 기반 HTML sanitizer가 필요하다.

| 목적 | 적절한 방식 |
|---|---|
| HTML을 전혀 허용하지 않는 일반 텍스트 | 출력 인코딩 |
| `<b>`, `<i>`, `<p>`, `<br>` 같은 일부 HTML만 허용 | HTML sanitizer |
| `<script>`, 이벤트 속성, `javascript:` URL 차단 | 직접 `str_replace`보다 parser 기반 sanitizer |

---

## 현재 XSS 방어 실습에 연결

현재 수업용 CARE 게시판 실습에서는 다음 기준으로 보면 된다.

| 판단 지점 | 정리 |
|---|---|
| 방어 위치 | `writeModel.php`에서 `$subject`, `$content`를 DB에 넣기 전 |
| 우선 적용 대상 | 저번 Stored XSS payload가 들어간 `content` |
| 수업용 최소 방어 | `<script>` 같은 특정 문자열 치환 |
| 수업용으로 더 본질적인 방어 | `<`, `>`를 HTML entity로 치환해 태그 해석을 막기 |
| 실무형 기본 방향 | `view.php`처럼 출력하는 지점에서 문맥별 출력 인코딩 |
| HTML 일부 허용이 필요한 경우 | 검증된 HTML sanitizer 사용 |

검증은 새 게시글로 해야 한다. 기존 악성 게시글은 방어 코드 적용 전에 DB에 저장된 값이므로, 저장 전 치환 방식이 적용됐는지 확인할 수 없다.

---

## 오해하기 쉬운 지점

| 오해 | 정정 |
|---|---|
| `<script>`만 막으면 XSS가 막힌다 | XSS 실행 지점은 script 태그만이 아니다. 이미지, iframe, 이벤트 속성, URL, DOM sink 등 여러 경로가 있다. |
| `<`, `>`만 바꾸면 모든 XSS가 끝난다 | HTML 본문 태그형 payload에는 강하지만, attribute/JS/URL/CSS 문맥은 별도 처리가 필요하다. |
| 위험 태그 목록을 잘 만들면 sanitizer가 필요 없다 | HTML parser가 해석하는 문법과 우회가 복잡하므로 직접 문자열 목록으로 처리하기 어렵다. |
| DB 컬럼 이름도 보안 변수명으로 바꿔야 한다 | 보통 DB 컬럼은 기존 `content`를 유지하고, 저장할 값 변수만 안전 처리된 값으로 바꾼다. |
| 인코딩은 공격 문자열을 삭제한다 | 삭제가 아니라 브라우저의 해석 방식을 글자로 바꾸는 것이다. |

---

## 관련 노트

- [[10_학습 노트/시스템보안/웹보안/XSS|XSS]]
- [[10_학습 노트/시스템보안/웹보안/XSS를 이용한 Session Token 탈취 실습|XSS를 이용한 Session Token 탈취 실습]]
- [[10_학습 노트/시스템보안/웹보안/HTTP 구조와 메시지|HTTP 구조와 메시지]]

---

## 참고 자료

- [OWASP Cross Site Scripting Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html)
- [MDN Character reference](https://developer.mozilla.org/en-US/docs/Glossary/Character_reference)
- [PHP htmlspecialchars manual](https://www.php.net/manual/en/function.htmlspecialchars.php)

---

## 확인 질문

1. HTML 인코딩은 문자열을 삭제하는가, 브라우저의 해석 방식을 바꾸는가?
2. `<script>`만 막는 방식이 왜 부족한가?
3. `<`와 `>`를 인코딩하면 저번 Stored XSS payload가 왜 실행되지 않는가?
4. HTML 본문과 HTML attribute에서 필요한 방어가 왜 달라질 수 있는가?
5. HTML sanitizer는 출력 인코딩과 무엇이 다른가?
