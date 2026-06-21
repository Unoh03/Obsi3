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

## 8. 저장형 XSS, 반사형 XSS와 06번 진단의 범위

> [!summary]
> 이 노트의 CARE 게시판 실습은 **저장형 XSS**다. KISA checker의 06번은 상태 변경 없이 HTTP 응답을 비교하기 위해 **반사형 XSS 후보**를 먼저 확인한다. DB가 꺼져 있을 때 사용하는 `reflected.php`는 checker의 출력 인코딩 판정을 위한 DB 없는 proof route이며, 게시판 저장형 XSS의 최종 안전 판정은 아니다.

### 8.1 두 유형의 차이

| 구분 | 저장형 XSS | 반사형 XSS |
|---|---|---|
| 입력 위치 | 게시글 작성, 회원정보 등 저장 기능 | 검색어, 오류 메시지, URL query 등 요청 값 |
| 저장 여부 | DB나 파일에 저장됨 | 저장하지 않고 현재 응답에 바로 반영됨 |
| 실행 시점 | 다른 사용자가 저장된 글을 조회할 때 | 공격자가 만든 URL을 열었을 때 |
| 이번 CARE 근거 | `writeModel.php` -> DB -> `view.php` | `/vuln/xss/reflected.php?data=...` proof route |
| DB 필요성 | 실제 재현에는 필요 | proof route 기준 필요 없음 |
| checker 06의 역할 | 이후 state-changing fixture로 별도 점검 | 현재 `attack-active`에서 HTTP 응답 자동 비교 |

현재 CARE에서 실제 증거가 있는 것은 저장형 XSS다. 따라서 `reflected.php` 결과가 `not_vulnerable`이어도, 그것은 게시판의 저장형 XSS가 안전하다는 뜻이 아니다.

### 8.2 06번 checker의 진단 원리

checker는 브라우저를 열어 JavaScript 실행 여부를 직접 보지 않는다. 정상 요청과 payload 요청의 **HTTP 응답 본문**을 비교한다.

```text
1. baseline: data=kisa-baseline 요청이 200인지 확인
2. payload: data에 XSS marker를 넣어 GET 요청
3. raw <script> 또는 onerror marker가 응답에 남으면 vulnerable
4. &lt;script&gt; 또는 &lt;img처럼 escape되면 not_vulnerable
5. 어느 근거도 없으면 manual_required
6. DB-backed baseline이 실패하면 DB 없는 proof route로 fallback
```

현재 profile의 primary route는 `center/list.php` 검색 기능이다. DB가 없으면 이 route가 500을 내므로, 06번은 `xss_reflected_proof`로 fallback하고 다음 메타데이터를 남긴다.

```text
conditions: [db_unavailable, fallback_used]
scope: db_independent_proof_only
```

이 상태의 `not_vulnerable`은 **DB 없는 proof route에서 출력 인코딩 근거를 확인했다**는 뜻이다. 게시판 검색이나 저장형 XSS의 runtime 결과를 대신하지 않는다.

핵심 실행 분기는 다음과 같다.

```python
# checker.py의 payload_probe() 핵심 흐름
if response.status_code not in baseline_expected_statuses:
    # 예: DB가 없는 board_search가 500
    fallback_result = self.payload_probe(check, fallback_step, check_dir)
    statuses.append(fallback_result.status)

body_matches = find_regex_matches(response.text, vulnerable_body_patterns)
if response.status_code in vulnerable_statuses or body_matches:
    statuses.append("vulnerable")
elif find_regex_matches(response.text, not_vulnerable_body_patterns):
    statuses.append("not_vulnerable")
else:
    statuses.append("manual_required")
```

> [!note]- 06번 XSS 진단 정의 전문 (`checks/06_xss.yml`)
> ```yaml
> id: "06"
> name: "XSS"
> kisa_section: "X. Web Application"
> db_dependency: "DB-backed recommended"
> required_mode: "attack-active"
> description: "A reflected candidate is probed with XSS payloads. The DB-backed board search can fall back to a profile-defined DB-independent proof route; stored XSS remains a separate state-changing check."
> steps:
>   - id: reflected_search_xss_probe
>     action: payload_probe
>     summary: "Search-like input parameter is checked for reflected XSS indicators. No state-changing request is sent."
>     routes:
>       - board_search
>     parameter: data
>     baseline_value: "kisa-baseline"
>     baseline_expected_statuses:
>       - 200
>     baseline_unexpected_status: "error"
>     fallback_routes:
>       - xss_reflected_proof
>     fallback_conditions:
>       - db_unavailable
>       - fallback_used
>     fallback_scope: "db_independent_proof_only"
>     payloads_file: "payloads/xss.yml"
>     payload_group: "reflected_basic"
>     vulnerable_statuses: []
>     vulnerable_body_patterns:
>       - '<script[^>]*>\\s*alert\(["'']KISA_XSS["'']\)\\s*</script>'
>       - '<img\\b[^>]*\\bonerror\\s*=\\s*alert\(["'']KISA_XSS["'']\)'
>     not_vulnerable_body_patterns:
>       - '&lt;script&gt;alert'
>       - '&lt;img'
>     no_match_status: "manual_required"
> ```

### 8.3 DB 없는 반사형 XSS proof route

`/vuln/xss/reflected.php`는 DB, 로그인, 게시글 작성 없이 query의 `data` 값을 현재 응답에 반영한다.

| mode | 동작 | 용도 |
|---|---|---|
| `safe` | `htmlspecialchars()`로 escape 후 출력 | checker의 방어 근거 확인 기본값 |
| `vulnerable` | `data`를 그대로 출력 | 조치 전 반사형 XSS 비교 실습 |

checker profile은 항상 `mode=safe`를 보낸다.

```yaml
xss_reflected_proof:
  method: GET
  path: "/vuln/xss/reflected.php"
  params:
    mode: "safe"
    data: "kisa-baseline"
```

> [!example]- 반사형 XSS proof page 전문 (`vuln/xss/reflected.php`)
> ```php
> <?php
> declare(strict_types=1);
>
> header('Content-Type: text/html; charset=UTF-8');
>
> $mode = $_GET['mode'] ?? 'safe';
> $data = $_GET['data'] ?? 'kisa-baseline';
>
> if (!is_string($mode) || !in_array($mode, ['safe', 'vulnerable'], true)) {
>     http_response_code(400);
>     exit('mode must be safe or vulnerable.');
> }
>
> if (!is_string($data)) {
>     http_response_code(400);
>     exit('data must be a string.');
> }
>
> function h(string $value): string
> {
>     return htmlspecialchars($value, ENT_QUOTES | ENT_SUBSTITUTE | ENT_HTML5, 'UTF-8', false);
> }
>
> $reflection = $mode === 'vulnerable' ? $data : h($data);
> ?>
> <!doctype html>
> <html lang="ko">
> <head>
>     <meta charset="UTF-8">
>     <title>Reflected XSS Proof Lab</title>
> </head>
> <body>
>     <h1>Reflected XSS Proof Lab</h1>
>     <p>DB를 사용하지 않는 반사형 XSS와 06번 checker의 출력 인코딩 판정용 실습 페이지다.</p>
>     <p>mode: <strong><?= h($mode) ?></strong></p>
>
>     <h2>Reflection</h2>
>     <div id="reflection"><?= $reflection ?></div>
>
>     <p>기본값은 <code>safe</code>이며, 사용자 입력을 HTML entity로 출력한다.</p>
>     <p><code>?mode=vulnerable&amp;data=...</code>은 조치 전 반사형 XSS 비교 실습용이다.</p>
> </body>
> </html>
> ```

### 8.4 자동 진단의 한계

> [!important]
> HTTP 응답에 marker가 남았다는 사실만으로 모든 XSS 실행 가능성을 증명할 수는 없다. HTML attribute, JavaScript string, URL, DOM sink처럼 출력 위치가 달라지면 browser/DOM 확인이 필요하다.

- checker 06은 반사형 후보의 raw reflection 또는 기본 escape 근거를 빠르게 분류한다.
- 실제 CARE 게시판의 저장형 XSS는 DB, controlled test post, `view.php` 확인, cleanup이 필요한 별도 state-changing 진단으로 남긴다.
- 따라서 이 proof route는 checker의 DB 없는 fallback을 검증하는 장치이며, 기존 6절의 저장형 XSS 증거를 대체하지 않는다.
