---
type: lab
topic: web-security
source: 주요정보통신기반시설 기술적 취약점 분석·평가 방법 상세가이드
source_pages:
  - 715
  - 716
  - 717
  - 718
status: draft
created: 2026-06-12
tags:
  - 🏷️과목/웹보안
  - 🏷️주제/CSRF
  - 🏷️상태/draft
---

# 웹 취약점 - 07 CSRF

source: [[40_자료/주요정보통신기반시설 기술적 취약점 분석·평가 방법 상세가이드.pdf|주요정보통신기반시설 기술적 취약점 분석·평가 방법 상세가이드]], p.715-718.

## 1. 개요

**CSRF(Cross-Site Request Forgery)**는 피해자가 로그인한 브라우저를 이용해, 피해자가 의도하지 않은 상태 변경 요청을 서버에 보내게 만드는 취약점이다.

PDF p.715의 판단 기준은 다음처럼 정리할 수 있다.

| 판단 | 기준 |
|---|---|
| 양호 | 중요한 요청에 CSRF 방어 token이 적용되어 있고, 서버에서 token 검증이 정상적으로 수행됨 |
| 취약 | 중요한 요청에 CSRF token이 없거나, token 검증을 수행하지 않아 인증된 사용자의 요청 위조가 가능함 |

이번 CARE 실습에서는 회원정보 수정 기능을 대상으로 확인했다. 피해자가 로그인된 상태에서 게시글에 저장된 위장 버튼을 누르면, 브라우저가 피해자의 session cookie를 붙여 `/member/modifyModel.php`로 요청을 보내고 회원정보가 변경된다.

## 2. 문제가 되는 부분

CARE의 회원정보 수정 기능은 정상 화면에서도 `POST /member/modifyModel.php`로 정보를 전송한다.

```php
<form action="modifyModel.php" method="post" name="f" id="form_reg">
    <input type="password" name="pw" id="pw">
    <input type="password" name="pwCheck" id="pwCheck">
    <input type="text" name="name" id="name" value="<?=$_SESSION['name'] ?>">
    <input type="text" name="mobile" value="<?=$_SESSION['mobile'] ?>">
    <input type="text" name="address" value="<?=$_SESSION['address'] ?>">
    <input type="text" name="email" value="<?=$_SESSION['email'] ?>">
</form>
```

문제는 처리 파일인 `member/modifyModel.php`가 session 로그인 여부만 확인하고, 요청이 정상 화면에서 온 것인지 확인하지 않는다는 점이다.

```php
session_start();
if($_SESSION['id'] == ""){
    echo "<script>location.href='login.php';</script>";
    exit;
}
$id = $_SESSION['id'];

$pw = $_POST['pw'];
$pwCheck = $_POST['pwCheck'];
$name = $_POST['name'];
$mobile = $_POST['mobile'];
$address = $_POST['address'];
$email= $_POST['email'];

$query = "UPDATE member SET pw='$pw', name='$name', mobile='$mobile',
email='$email', address='$address' WHERE id='$id'";
mysqli_query($link, $query);
```

정리하면 다음과 같다.

| 확인 지점 | 현재 상태 | CSRF 관점 |
|---|---|---|
| 인증 확인 | `$_SESSION['id']`만 확인 | 로그인된 피해자 브라우저라면 통과 가능 |
| CSRF token | 없음 | 정상 form에서 온 요청인지 구분 불가 |
| Origin / Referer 검증 | 없음 | 외부 페이지나 조작된 게시글에서 온 요청을 구분하기 어려움 |
| 현재 비밀번호 재확인 | 없음 | 회원정보 변경 같은 중요 작업에 추가 확인 없음 |

### 2.1 06 XSS 방어코드와 충돌한 지점

처음에는 06 XSS 조치에서 넣었던 `htmlspecialchars()` 기반 출력 인코딩이 `center/view.php`에 남아 있었다.

이 상태에서는 게시글 본문에 저장한 `<form>`이 실제 form으로 렌더링되지 않고 문자 그대로 출력된다. 따라서 게시판을 전달 지점으로 쓰는 CSRF 실습이 진행되지 않았다.

그래서 이번 CSRF 재현에서는 의도적으로 `center/view.php`의 출력 인코딩을 다시 빼고, 게시글 본문이 HTML로 해석되는 취약 상태로 되돌렸다.

```php
<div class="title1"> <?=$subject?> </div>

<div id="view_content">
    <?=$content?>
</div>
```

이 시행착오는 중요하다. XSS 방어코드는 CSRF의 근본 원인인 `modifyModel.php`의 token 부재를 고치지는 않지만, **게시판을 이용한 CSRF 전달 경로는 막을 수 있다.** 이번 실습은 취약점 재현을 위해 그 방어를 잠시 제거한 상태다.

## 3. 악용 흐름

이번 실습에서는 게시글 본문에 회원정보 수정 요청을 보내는 form을 저장했다.

```html
이벤트 중. 버튼 누르면 포인트 줌.
<form method="POST" action="/member/modifyModel.php">
  <input type="hidden" name="pw" value="123" />
  <input type="hidden" name="pwCheck" value="123" />
  <input type="hidden" name="name" value="babo" />
  <input type="hidden" name="mobile" value="babo" />
  <input type="hidden" name="address" value="boba" />
  <input type="hidden" name="email" value="babo" />
  <input type="submit" value="1000포인트 획득" />
</form>
```

흐름은 다음과 같다.

```text
피해자 계정으로 로그인
-> CSRF form이 저장된 게시글 열람
-> "1000포인트 획득" 버튼 클릭
-> 브라우저가 session cookie를 붙여 /member/modifyModel.php로 POST 전송
-> 서버가 CSRF token 없이 session만 확인
-> 피해자 계정의 회원정보가 form의 hidden 값으로 변경됨
```

버튼 문구는 포인트 획득처럼 보이지만, 실제 요청은 회원정보 수정이다. 공격자는 피해자의 비밀번호나 session cookie 값을 직접 알지 못해도, 피해자의 브라우저가 이미 가진 인증 상태를 이용할 수 있다.

## 4. 점검 방법

PDF p.715는 비밀번호 변경, 개인정보 수정, 게시글 삭제 같은 중요한 요청에서 CSRF token 검증이 있는지 확인하라고 본다.

CARE에서는 다음 순서로 확인한다.

1. 회원정보 수정 화면의 form field와 action URL을 확인한다.
2. 처리 파일에서 CSRF token, Origin, Referer, 재인증 검증 여부를 확인한다.
3. 같은 field를 가진 조작 form을 만든다.
4. 로그인된 브라우저에서 조작 form을 제출한다.
5. 회원정보가 피해자 계정 권한으로 변경되는지 확인한다.

확인 URL은 다음과 같다.

```text
http://172.168.10.10/member/modify.php
http://172.168.10.10/member/modifyModel.php
http://172.168.10.10/center/view.php?num=게시글번호
```

## 5. 조치 방안

### 5.1 CSRF token 생성 및 form 포함

회원정보 수정 화면에서 session에 CSRF token을 만들고, form에 hidden field로 넣는다.

`member/modify.php`의 form 출력 전에 추가한다.

```php
if (empty($_SESSION['csrf_token'])) {
    $_SESSION['csrf_token'] = bin2hex(random_bytes(32));
}
```

form 내부에 token 값을 넣는다.

```php
<input type="hidden" name="csrf_token"
       value="<?=htmlspecialchars($_SESSION['csrf_token'], ENT_QUOTES | ENT_HTML5, 'UTF-8', false)?>">
```

이렇게 하면 정상 회원정보 수정 화면을 거친 요청은 token을 함께 보내지만, 공격자가 임의로 만든 form은 올바른 token 값을 알기 어렵다.

### 5.2 서버 측 token 검증

`member/modifyModel.php`에서 DB update를 실행하기 전에 token을 검증한다.

```php
$csrfToken = $_POST['csrf_token'] ?? '';
$sessionToken = $_SESSION['csrf_token'] ?? '';

if (!$sessionToken || !hash_equals($sessionToken, $csrfToken)) {
    http_response_code(403);
    exit('CSRF 검증 실패');
}

unset($_SESSION['csrf_token']);
```

중요한 점은 token을 form에 넣는 것만으로 끝내지 않고, **서버에서 session token과 요청 token을 비교해야 한다**는 것이다.

### 5.3 보조 방어

PDF p.716의 조치 방법은 token 검증 외에도 Referer/Origin 검증, SameSite cookie 옵션을 함께 제시한다.

| 조치 | 역할 | 주의점 |
|---|---|---|
| CSRF token | 정상 화면에서 발급된 요청인지 확인 | 핵심 방어 |
| Origin / Referer 검증 | 외부 site에서 온 요청 차단 | 일부 환경에서 header가 빠질 수 있어 보조 방어로 사용 |
| SameSite cookie | cross-site 요청에서 cookie 자동 전송 범위 제한 | token을 완전히 대체하지는 않음 |
| 현재 비밀번호 재입력 | 비밀번호 변경, 개인정보 수정 같은 중요 작업 재확인 | 사용자 불편은 늘지만 중요 기능에는 적절 |
| XSS 방어 유지 | 게시글을 통한 form/script 삽입 차단 | CSRF token 탈취나 같은 origin 요청 실행 위험도 줄임 |

이번 실습에서 특히 확인한 점은 XSS 방어와 CSRF 방어의 관계다. `center/view.php`에서 출력 인코딩을 적용하면 게시글을 통한 CSRF form 전달은 막히지만, 회원정보 수정 endpoint 자체에는 여전히 CSRF token 검증이 필요하다.


### 조치 후 재점검 기준

조치 후에는 기존 CSRF form을 다시 실행한다.

```
<form method="POST" action="/member/modifyModel.php">
  <input type="hidden" name="pw" value="123" />
  <input type="hidden" name="pwCheck" value="123" />
  <input type="hidden" name="name" value="babo" />
  <input type="hidden" name="mobile" value="babo" />
  <input type="hidden" name="address" value="boba" />
  <input type="hidden" name="email" value="babo" />
  <input type="submit" value="1000포인트 획득" />
</form>
```

조치 전에는 피해자 세션으로 회원정보 변경 요청이 처리될 수 있다.

조치 후에는 다음 중 하나로 차단되어야 한다.

- CSRF token이 없어서 요청 거부
- Origin/Referer가 허용 출처가 아니라서 요청 거부
- SameSite 설정으로 외부 유도 요청에 세션 쿠키가 붙지 않음
- 현재 비밀번호 재인증 실패로 요청 거부

따라서 조치 후 같은 CSRF form을 실행했을 때 회원정보가 변경되지 않으면 CSRF 방어가 동작한 것으로 판단한다.

### 5.4 AWS 재사용 시 점검 포인트

이번 VM 실습에서 사용한 CSRF 조치 방식은 AWS 환경에서도 그대로 재사용할 수 있다. 다만 AWS에서는 접속 도메인, HTTPS 적용 여부, 로드 밸런서 사용 여부에 따라 일부 설정값을 환경에 맞게 바꿔야 한다.

|항목|VM 실습 기준|AWS 적용 시 확인할 점|
|---|---|---|
|CSRF token|`member/modify.php`에서 token 생성 후 hidden field로 전달|EC2로 옮겨도 동일하게 적용 가능|
|token 검증|`member/modifyModel.php`에서 session token과 POST token 비교|Auto Scaling이나 다중 서버 구성 시 session 저장 위치 확인 필요|
|Origin / Referer 검증|`http://172.168.10.10` 같은 내부 IP 기준|AWS에서는 실제 도메인, ALB DNS, HTTPS 주소 기준으로 변경 필요|
|SameSite Cookie|`Lax` 또는 `Strict` 설정|HTTPS 사용 시 `Secure`, `HttpOnly`, `SameSite`를 함께 확인|
|중요 기능 재인증|회원정보 변경 시 현재 비밀번호 재확인|AWS에서도 동일하게 적용 가능|
|XSS 방어|게시글의 form/script 삽입 차단|CSRF 전달 경로를 줄이는 보조 방어로 유지|

AWS에서 특히 바뀌는 부분은 Origin/Referer 기준값이다. VM에서는 내부 IP를 기준으로 볼 수 있지만, AWS에서는 다음 중 실제 사용 주소를 기준으로 잡아야 한다.

```text
http://EC2_PUBLIC_IP
http://도메인
https://도메인
http://ALB_DNS_NAME
https://ALB_DNS_NAME
```

예를 들어 AWS에서 HTTPS 도메인을 사용한다면 허용 Origin은 다음처럼 잡는다.

```php
$allowedOrigin = 'https://example.com';
```

Origin/Referer 검증은 환경에 따라 누락되거나 프록시, 로드 밸런서, HTTPS 전환 구성의 영향을 받을 수 있으므로 단독 방어로 보지 않는다. 핵심 방어는 CSRF token 검증이고, Origin/Referer와 SameSite Cookie는 보조 방어로 함께 적용한다.

AWS 재점검 기준은 VM과 같다.

```text
1. 로그인된 사용자로 회원정보 수정 정상 요청을 확인한다.
2. CSRF token이 없는 조작 form을 제출한다.
3. 서버가 요청을 거부하는지 확인한다.
4. 회원정보가 hidden 값으로 변경되지 않는지 확인한다.
5. HTTPS 적용 시 session cookie에 Secure, HttpOnly, SameSite 속성이 붙었는지 확인한다.
```

따라서 AWS 이전 시에는 VM에서 사용한 CSRF form을 그대로 다시 실행하되, 조치 후에는 token 없는 요청이 실패해야 한다.

### 5.5 구현 시 주의점

CSRF token 조치는 다음 위치에 넣는다.

| 파일 | 넣을 내용 | 위치 |
|---|---|---|
| `member/modify.php` | CSRF token 생성 | `session_start()` 이후, form 출력 전 |
| `member/modify.php` | hidden `csrf_token` input | `<form>` 내부 |
| `member/modifyModel.php` | token 검증 | POST 값 읽은 뒤, DB `UPDATE` 실행 전 |
| 공통 session 설정 파일 또는 각 진입점 | `SameSite`, `HttpOnly`, `Secure` cookie 설정 | `session_start()`보다 먼저 |

주의할 점은 다음과 같다.

- `session_set_cookie_params()`는 반드시 `session_start()`보다 먼저 실행해야 한다.
- 기존 CARE 코드는 mysqli 기반이므로, 조치 예시도 mysqli 흐름을 깨지 않게 넣는다.
- CSRF token 검증은 form에 hidden 값을 넣는 것만으로 끝나지 않고, `modifyModel.php`에서 `$_SESSION['csrf_token']`과 `$_POST['csrf_token']`을 비교해야 한다.
- AWS에서는 Origin/Referer 기준값을 VM 내부 IP가 아니라 실제 접속 주소로 바꾼다.
  - EC2 Public IP
  - 도메인
  - ALB DNS
  - HTTPS 도메인
- XSS 출력 인코딩을 다시 적용하면 게시글에 삽입한 CSRF form이 실행되지 않을 수 있다. 이것은 전달 경로 차단이지, `modifyModel.php`의 CSRF token 검증을 대체하는 것은 아니다.
## 6. 증거

아래 스크린샷을 증거로 넣는다.

- [x] 공격 입력: 게시글 본문에 회원정보 수정 CSRF form 저장

![[Pasted image 20260612175225.png]]

게시글 본문에는 포인트 획득 이벤트처럼 보이는 문구와 함께 `/member/modifyModel.php`로 전송되는 hidden form을 넣었다.

- [x] 시행착오: 06 XSS 방어코드가 남아 있어 form이 문자 그대로 출력됨

![[Pasted image 20260612175210.png]]

이 상태에서는 `<form>`이 실제 버튼으로 렌더링되지 않았다. 06 XSS 조치로 넣었던 출력 인코딩이 남아 있었기 때문이다. CSRF 재현을 위해 `center/view.php`를 다시 취약 상태로 되돌렸다.

- [x] 취약 상태 복구 후: 같은 게시글에서 위장 버튼이 렌더링됨

![[Pasted image 20260612175834.png]]

출력 인코딩을 제거하자 게시글 안의 `<form>`이 HTML로 해석되어 `1000포인트 획득` 버튼이 표시되었다.

- [x] 실행 결과: form의 hidden 값이 회원정보에 반영됨

![[Pasted image 20260612175754.png]]

![[Pasted image 20260612175810.png]]

`name`, `mobile`, `address`, `email` 값이 form에서 지정한 `babo`, `boba` 계열 값으로 바뀌었다. 즉, 로그인된 피해자 권한으로 회원정보 수정 요청이 처리되었다.

## 7. 판단

CARE의 회원정보 수정 기능은 session 로그인 여부만 확인하고 CSRF token, Origin/Referer, 현재 비밀번호 재확인 같은 추가 검증을 하지 않는다. 따라서 로그인된 사용자가 조작 form을 제출하면, 사용자의 의도와 무관하게 회원정보가 변경될 수 있다.

이번 실습에서는 게시글에 저장한 버튼 클릭형 form을 통해 `/member/modifyModel.php`로 POST 요청을 보냈고, form의 hidden 값이 피해자 계정 정보에 반영되는 것을 확인했다.

따라서 PDF p.715-718의 `크로스사이트 요청 위조(CSRF)` 기준으로 보면 현재 상태는 취약이다.

다만 이번 증거에서 한 가지를 구분해야 한다. 06 XSS 방어코드가 남아 있던 상태에서는 게시글 안의 form이 문자 그대로 출력되어 CSRF가 실행되지 않았다. 하지만 이 차단 효과는 **CSRF의 정석 방어가 아니라 XSS 출력 인코딩의 부수 효과**다.

| 구분 | 이번 실습에서 확인한 내용 | CSRF 관점의 의미 |
|---|---|---|
| XSS 출력 인코딩 | 게시글의 `<form>`이 HTML로 실행되지 않고 문자로 출력됨 | 게시판을 이용한 CSRF 전달 경로를 줄임 |
| CSRF token 검증 | `modifyModel.php`에서 token 비교를 하지 않음 | 정석 CSRF 방어가 아직 없음 |
| Origin / Referer 검증 | 요청 출처를 확인하지 않음 | 보조 방어도 없음 |
| SameSite cookie | 이번 증거에서는 확인하지 않음 | 별도 확인 필요 |

따라서 이번 실습에서 실제로 확인된 방어 효과는 **게시글을 통한 공격 전달을 막는 XSS 방어 효과**에 가깝다. 이것만으로는 `/member/modifyModel.php`가 CSRF에 안전하다고 볼 수 없다. 공격자가 다른 외부 페이지에서 같은 POST form을 만들거나, 다른 삽입 지점을 확보하면 token 없는 상태 변경 요청은 여전히 처리될 수 있다.

최종 조치 판정은 다음처럼 분리한다.

| 항목 | 판정 |
|---|---|
| CARE의 CSRF 취약 여부 | 취약 |
| 게시글을 이용한 전달 경로 | XSS 방어가 있으면 차단 가능 |
| CSRF 정석 조치 적용 여부 | 미적용 |
| 근본 조치 | `modify.php`에서 CSRF token 발급, `modifyModel.php`에서 session token과 요청 token 비교 |

정리하면, **XSS 방어는 CSRF의 보조 방어가 될 수 있지만 CSRF의 정석 방어를 대체하지 않는다.** 이 항목의 근본 조치는 `modifyModel.php`에서 CSRF token을 서버 측으로 검증하는 것이다.
