---
type: lab
topic: web-security
source: 주요정보통신기반시설 기술적 취약점 분석·평가 방법 상세가이드
source_pages:
  - 711
  - 712
  - 713
  - 714
status: draft
created: 2026-06-12
tags:
  - 🏷️과목/웹보안
  - 🏷️주제/XSS
  - 🏷️상태/draft
---

# 웹 취약점 - 06 XSS

source: [[40_자료/주요정보통신기반시설 기술적 취약점 분석·평가 방법 상세가이드.pdf|주요정보통신기반시설 기술적 취약점 분석·평가 방법 상세가이드]], p.711-714.

## 1. 개요

**XSS(Cross-Site Scripting)**는 사용자가 입력한 스크립트가 다른 사용자의 브라우저에서 실행되는 취약점이다.

PDF p.711의 판단 기준은 다음처럼 정리할 수 있다.

| 판단 | 기준 |
|---|---|
| 양호 | 사용자 입력값에 대해 검증 및 필터링이 이루어져 악성 스크립트가 실행되지 않음 |
| 취약 | 사용자 입력값이 HTML에 그대로 출력되어 스크립트가 입력 및 실행됨 |

이번 CARE 실습에서는 Kali를 사용하지 않고, PDF p.712의 방식처럼 **게시판에 스크립트 구문을 저장한 뒤 글 열람 시 실행되는지** 브라우저로 직접 확인했다.

## 2. 문제가 되는 부분

CARE 게시판은 글 작성 시 제목과 내용을 그대로 DB에 저장한다.

| 파일 | 문제 지점 |
|---|---|
| `center/writeModel.php` | `$_POST['subject']`, `$_POST['content']`를 별도 검증 없이 받아 DB에 저장 |
| `center/view.php` | DB에서 꺼낸 `$subject`, `$content`를 HTML에 그대로 출력 |

문제의 핵심은 **입력값이 저장되고, 나중에 HTML 문서 안에 escape 없이 출력된다**는 점이다.

취약한 저장 흐름은 다음과 같다.

```php
$subject = $_POST['subject'];
$content = $_POST['content'];

$query = "INSERT INTO center(id, subject, content, date, hit, filename) ";
$query = $query . "VALUES('$id','$subject', '$content', '$date', 0, '$upfile')";
```

취약한 출력 흐름은 다음과 같다.

```php
<div class="title1"> <?=$subject?> </div>

<div id="view_content">
    <?=$content?>
</div>
```

이 구조에서는 게시글 내용에 `<script>` 또는 이벤트 핸들러가 들어가면, 글을 보는 사용자의 브라우저가 이를 HTML/JavaScript로 해석할 수 있다.

## 3. 악용 흐름

이번 실습에서는 저장형 XSS를 확인했다.

```text
공격자 또는 일반 사용자
-> 게시글 작성
-> content에 스크립트 삽입
-> DB에 저장
-> 다른 사용자가 게시글 열람
-> 브라우저에서 스크립트 실행
```

사용한 payload는 다음과 같다.

```html
<script>alert("XSS")</script>
```

작은따옴표를 쓰면 현재 `writeModel.php`의 SQL 문자열이 같이 깨질 수 있으므로, 이번 실습에서는 큰따옴표를 사용했다.

## 4. 점검 방법

PDF p.712는 게시판, 검색 등 사용자 입력값이 HTML에 렌더링되는 기능에 스크립트 구문을 넣고 실행 여부를 확인하라고 한다.

CARE에서는 다음 순서로 확인한다.

1. 로그인한다.
2. 게시글 작성 화면으로 이동한다.
3. 제목은 일반 문자열로 입력한다.
4. 내용에 XSS payload를 입력한다.
5. 작성한 글을 조회한다.
6. alert가 실행되는지 확인한다.

확인 URL은 다음과 같다.

```text
http://172.168.10.10/center/write.php
http://172.168.10.10/center/view.php?num=게시글번호
```

## 5. 조치 방안

### 5.1 출력 시 HTML Entity 처리

XSS 방어의 핵심은 사용자가 입력한 값을 HTML에 출력할 때 브라우저가 태그나 스크립트로 해석하지 못하게 만드는 것이다.

CARE의 `center/view.php`에 출력용 escape 함수를 추가한다.

```php
function h($value) {
    return htmlspecialchars($value ?? '', ENT_QUOTES | ENT_HTML5, 'UTF-8', false);
}
```

그 다음 게시글 제목과 내용을 출력하는 부분에 적용한다.

```php
<div class="title1"> <?=h($subject)?> </div>

<div id="view_content">
    <?=h($content)?>
</div>
```

이렇게 하면 `<script>alert("XSS")</script>`가 JavaScript로 실행되지 않고, 문자 그대로 화면에 표시된다.

### 5.2 입력값 검증과 화이트리스트

PDF p.713은 특수문자 필터링과 화이트리스트 방식을 함께 언급한다.

다만 게시판 내용은 일반 텍스트가 목적이므로, 이 프로젝트에서는 HTML 태그를 허용하지 않는 방향이 단순하다. 굳이 일부 HTML을 허용해야 한다면 `<b>`, `<i>`처럼 허용할 태그를 정하고 나머지는 제거하는 화이트리스트 방식이 필요하다.

### 5.3 쿠키 보호 옵션

PDF p.713은 세션 탈취 피해를 줄이기 위해 쿠키에 `HttpOnly`, `Secure`, `SameSite` 옵션을 설정하라고 설명한다.

이 조치는 XSS 자체를 제거하지는 않는다. 하지만 XSS가 발생했을 때 JavaScript로 세션 쿠키를 훔치는 피해를 줄일 수 있다.

```php
session_set_cookie_params([
    'httponly' => true,
    'secure' => true,
    'samesite' => 'Lax',
]);
session_start();
```

현재 실습 환경이 HTTP라면 `Secure`는 HTTPS 구성 후 적용하는 것이 맞다.

## 6. 증거

아래 스크린샷을 증거로 넣는다.

- [x] 취약 코드: 게시글 작성 시 사용자 입력값을 그대로 저장

![[Pasted image 20260612173912.png]]

- [x] 취약 코드: 게시글 조회 시 제목과 내용을 escape 없이 출력

![[Pasted image 20260614110307.png]]

- [x] 공격 입력: 게시글 내용에 XSS payload 입력

![[Pasted image 20260612174036.png]]

사용한 payload는 다음과 같다.

```html
<script>alert("XSS")</script>
```

- [x] 취약 상태: 게시글 조회 시 브라우저에서 스크립트 실행

![[Pasted image 20260612174105.png]]

`center/view.php?num=3`에 접근하자 `alert("XSS")`가 실행되었다. 이로써 게시판 내용에 저장된 스크립트가 열람자의 브라우저에서 실행되는 저장형 XSS를 확인했다.

- [x] 조치 코드: `htmlspecialchars()` 기반 출력 인코딩 적용

![[Pasted image 20260612174808.png]]

적용한 핵심 코드는 다음과 같다.

```php
function h($value) {
    return htmlspecialchars($value ?? '', ENT_QUOTES | ENT_HTML5, 'UTF-8', false);
}

<div class="title1"> <?=h($subject)?> </div>

<div id="view_content">
    <?=h($content)?>
</div>
```

- [x] 조치 후: 같은 payload가 실행되지 않고 문자열로 출력됨

![[Pasted image 20260612174855.png]]

조치 후에는 `<script>alert("XSS")</script>`가 JavaScript로 실행되지 않고 게시글 내용에 문자 그대로 표시되었다.

## 7. 판단

조치 전 CARE 게시판은 게시글 내용을 DB에 저장한 뒤 조회 화면에서 그대로 출력했다. 이 때문에 `<script>alert("XSS")</script>` payload가 게시글 열람 시 브라우저에서 실행되었다.

따라서 PDF p.711-714의 `크로스사이트 스크립트` 기준으로 보면 조치 전 상태는 취약이다.

조치 후에는 `htmlspecialchars()`를 이용해 제목과 내용을 HTML Entity로 변환하여 출력했고, 같은 payload가 스크립트로 실행되지 않고 문자열로 표시되는 것을 확인했다.

본 항목의 핵심은 입력값을 단순히 DB에 저장하지 않는 것이 아니라, **사용자 입력값이 HTML 문서로 나갈 때 브라우저가 코드로 해석하지 못하도록 출력 인코딩을 적용하는 것**이다.
