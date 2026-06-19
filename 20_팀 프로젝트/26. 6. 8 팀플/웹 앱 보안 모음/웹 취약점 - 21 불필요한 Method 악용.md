---
type: lab  
topic: web-security  
source: 주요정보통신기반시설 기술적 취약점 분석·평가 방법 상세가이드  
source_pages:
  - 779
  - 780
  - 781
  - 782
  - 783
  - 784  
status: draft  
created: 2026-06-17  
tags:
    
- 🏷️과목/웹보안
    
- 🏷️주제/HTTP-Method
    
- 🏷️상태/draft
    

---

# 웹 취약점 - 21 불필요한 Method 악용

source: [[40_자료/주요정보통신기반시설 기술적 취약점 분석·평가 방법 상세가이드.pdf|주요정보통신기반시설 기술적 취약점 분석·평가 방법 상세가이드]], p.779-784.

## 1. 개요

**불필요한 Method 악용**은 웹 서버가 서비스에 필요하지 않은 HTTP Method를 허용하여, 임의 파일 생성, 파일 삭제, 요청 정보 반사, 터널링 같은 비정상 동작이 가능한지 확인하는 항목이다.

일반 웹 서비스에서 주로 필요한 Method는 다음 정도다.

|Method|일반적 의미|CARE 필요 여부|
|---|---|---|
|`GET`|페이지 조회|필요|
|`POST`|로그인, 회원가입, 게시글 작성 등 form 전송|필요|
|`HEAD`|응답 header 확인|일반적으로 허용 가능|
|`OPTIONS`|서버가 허용하는 method 확인, CORS preflight 등에 사용|단순 웹에서는 필수는 아니지만 허용되어도 즉시 취약은 아님|

반대로 다음 Method는 일반적인 CARE 기능에는 필요하지 않다.

|Method|의미|위험|
|---|---|---|
|`PUT`|서버에 자원 생성 또는 업로드|임의 파일 생성 가능성|
|`DELETE`|서버 자원 삭제|임의 파일 삭제 가능성|
|`TRACE`|요청 내용을 서버가 그대로 반사|요청 header, cookie 반사로 정보 노출 가능성|
|`CONNECT`|터널 연결|프록시 오용 가능성|

따라서 이 항목의 핵심은 다음이다.

```text
CARE에서 필요한 GET/POST/HEAD 정도만 허용되는가?
PUT, DELETE, TRACE, CONNECT 같은 불필요한 Method가 차단되는가?
```

## 2. CARE 적용 가능성

CARE의 PHP 기능은 로그인, 회원가입, 게시글 조회, 게시글 작성, 파일 업로드, 파일 다운로드 등으로 구성되어 있다.

이 기능들은 일반적으로 `GET`과 `POST`만으로 처리된다.

|CARE 기능|일반 Method|
|---|---|
|메인 페이지 조회|`GET`|
|로그인 화면 조회|`GET`|
|로그인 처리|`POST`|
|회원가입 처리|`POST`|
|게시판 목록 조회|`GET`|
|게시글 작성 처리|`POST`|
|파일 다운로드|`GET`|

즉 CARE 애플리케이션 자체가 `PUT`, `DELETE`, `TRACE`, `CONNECT`를 사용할 필요는 없다.

따라서 21번은 CARE PHP 코드 취약점이라기보다, **Apache 웹 서버가 불필요한 HTTP Method를 허용하는지 확인하는 서버 설정 점검 항목**에 가깝다.

## 3. 문제가 되는 부분

문제가 되는 구조는 다음과 같다.

```text
클라이언트
-> PUT /method-test.txt
-> 서버가 파일 생성 허용
-> 공격자가 웹루트에 임의 파일을 만들 수 있음
```

또는 다음과 같다.

```text
클라이언트
-> TRACE /
-> 서버가 요청 내용을 그대로 응답
-> 요청 header 또는 cookie가 응답에 반사될 수 있음
```

이번 서버 상태에서는 `PUT`과 `TRACE`가 차단되는 것을 확인했다. 따라서 현재까지 확인한 범위에서는 불필요 Method 악용 가능성은 낮다.

## 4. 점검 방법

이번 점검은 서버에서 `curl`을 사용해 수행했다.

대상 서버는 다음과 같다.

```text
http://172.168.10.10/
```

### 4.1 OPTIONS 확인

`OPTIONS`는 서버가 허용하는 Method 정보를 확인하기 위해 사용한다.

```bash
curl -i -X OPTIONS http://172.168.10.10/
```

실제 응답은 다음과 같았다.

```http
HTTP/1.1 200 OK
Date: Wed, 17 Jun 2026 02:17:06 GMT
Server: Apache
Set-Cookie: PHPSESSID=005e6d6a88ebc525e020f703faa7cdd4; path=/
Expires: Thu, 19 Nov 1981 08:52:00 GMT
Cache-Control: no-store, no-cache, must-revalidate
Pragma: no-cache
Vary: Accept-Encoding
Content-Length: 2589
Content-Type: text/html; charset=UTF-8
```

응답 본문은 CARE 메인 페이지 HTML이었다.

이 결과는 서버가 `OPTIONS` 요청을 차단하지 않고, 메인 페이지와 유사하게 처리한다는 뜻이다. 다만 `OPTIONS`가 허용된 것만으로 즉시 임의 파일 생성이나 삭제가 가능한 것은 아니다.

### 4.2 TRACE 확인

`TRACE`는 보통 비활성화되어 있어야 한다.

```bash
curl -i -X TRACE http://172.168.10.10/
```

실제 응답은 다음과 같았다.

```http
HTTP/1.1 405 Method Not Allowed
Date: Wed, 17 Jun 2026 02:17:15 GMT
Server: Apache
Allow:
Content-Length: 388
Content-Type: text/html; charset=iso-8859-1
```

응답 상태가 `405 Method Not Allowed`이므로, 현재 서버는 `TRACE` 요청을 허용하지 않는다.

응답 본문에 다음 문구가 포함되었다.

```text
The requested method GET is not allowed for this URL.
Additionally, a 405 Method Not Allowed
error was encountered while trying to use an ErrorDocument to handle the request.
```

문구상 `GET`이라고 표시되는 부분은 에러 페이지 처리 과정의 메시지로 보인다. 핵심 판단은 HTTP 상태 코드가 `405 Method Not Allowed`라는 점이다.

### 4.3 PUT 확인

`PUT`이 허용되면 서버에 임의 파일을 만들 수 있으므로 위험하다.

```bash
curl -i -X PUT --data "method-test" http://172.168.10.10/method-test.txt
```

실제 응답은 다음과 같았다.

```http
HTTP/1.1 405 Method Not Allowed
Date: Wed, 17 Jun 2026 02:17:23 GMT
Server: Apache
Allow: GET,POST,OPTIONS,HEAD
Content-Length: 388
Content-Type: text/html; charset=iso-8859-1
```

`PUT` 요청이 `405 Method Not Allowed`로 차단되었다. 또한 `Allow` header에는 다음 Method만 표시되었다.

```text
GET, POST, OPTIONS, HEAD
```

따라서 현재 서버는 `PUT`을 통한 임의 파일 생성을 허용하지 않는다.

### 4.4 DELETE 확인 필요

아직 `DELETE` 요청은 확인하지 않았다.

추가 점검 명령은 다음과 같다.

```bash
curl -i -X DELETE http://172.168.10.10/method-test.txt
```

응답.

```http
HTTP/1.1 405 Method Not Allowed
Date: Fri, 19 Jun 2026 06:35:11 GMT
Server: Apache
Allow: POST,OPTIONS,HEAD,GET
Content-Length: 388
Content-Type: text/html; charset=iso-8859-1
```

`DELETE`도 차단되었으므로 21번은 B로 확정되었다.

## 5. 현재 서버 상태 요약

|Method|점검 명령|실제 결과|판단|
|---|---|---|---|
|`OPTIONS`|`curl -i -X OPTIONS http://172.168.10.10/`|`200 OK`, CARE 메인 HTML 반환|허용됨. 단독 취약은 아님|
|`TRACE`|`curl -i -X TRACE http://172.168.10.10/`|`405 Method Not Allowed`|차단됨|
|`PUT`|`curl -i -X PUT --data "method-test" http://172.168.10.10/method-test.txt`|`405 Method Not Allowed`, `Allow: GET,POST,OPTIONS,HEAD`|차단됨|
|`DELETE`|미수행|미확인|추가 확인 필요|

현재까지 확인한 결과, `TRACE`와 `PUT`은 차단되어 있다. `OPTIONS`는 허용되지만, 응답상 위험한 Method 허용 근거는 확인되지 않았다.

따라서 현재 상태는 **불필요 Method 악용 가능성이 낮은 상태**로 본다.

## 6. 조치 방안

현재 서버는 `PUT`과 `TRACE`를 차단하고 있으므로 즉시 조치가 필요한 상태로 보이지는 않는다.

다만 운영 기준에서는 명시적으로 필요한 Method만 허용하는 설정을 둘 수 있다.

### 6.1 TRACE 비활성화

Apache 전역 설정에 다음을 적용한다.

```apache
TraceEnable Off
```

Ubuntu Apache에서는 보통 다음 파일 중 하나에서 관리한다.

```text
/etc/apache2/conf-available/security.conf
/etc/apache2/apache2.conf
```

설정 후 문법 검사와 reload를 수행한다.

```bash
sudo apache2ctl configtest
sudo systemctl reload apache2
```

### 6.2 필요한 Method만 허용

CARE가 일반 웹 애플리케이션으로만 동작한다면 `GET`, `POST`, `HEAD`만 허용해도 충분하다.

Apache 설정 예시는 다음과 같다.

```apache
<Directory /var/www/html/care>
    <LimitExcept GET POST HEAD>
        Require all denied
    </LimitExcept>
</Directory>
```

다만 `OPTIONS`는 CORS preflight나 일부 점검 도구에서 사용할 수 있다. CARE는 별도 API/CORS 구조가 아니므로 차단해도 큰 문제는 없을 가능성이 높지만, 운영 환경에서는 실제 서비스 요구사항을 확인해야 한다.

현재 서버의 `PUT` 응답에서 `Allow: GET,POST,OPTIONS,HEAD`가 확인되었으므로, 이미 위험 Method는 차단되는 것으로 보인다. 따라서 이번 실습에서는 별도 조치보다 **현재 차단 상태를 증거로 남기는 것**을 우선한다.

## 7. 조치 후 점검 기준

명시적 Method 제한을 적용했다면 다음을 다시 확인한다.

```bash
curl -i -X OPTIONS http://172.168.10.10/
curl -i -X TRACE http://172.168.10.10/
curl -i -X PUT --data "method-test" http://172.168.10.10/method-test.txt
curl -i -X DELETE http://172.168.10.10/method-test.txt
```

기대 결과는 다음과 같다.

|Method|기대 결과|
|---|---|
|`GET`|정상 동작|
|`POST`|정상 기능에서만 동작|
|`HEAD`|허용 가능|
|`OPTIONS`|정책에 따라 허용 또는 차단|
|`TRACE`|차단|
|`PUT`|차단|
|`DELETE`|차단|
|`CONNECT`|차단|

## 8. 증거

현재 수집한 증거는 다음과 같다.

### OPTIONS

-  `OPTIONS /` 요청 수행
![[Pasted image 20260617112152.png]]
```bash
curl -i -X OPTIONS http://172.168.10.10/
```

### TRACE

-  `TRACE /` 요청 수행
![[Pasted image 20260617112221.png]]
```bash
curl -i -X TRACE http://172.168.10.10/
```

### PUT

-  `PUT /method-test.txt` 요청 수행
![[Pasted image 20260617112248.png]]
```bash
curl -i -X PUT --data "method-test" http://172.168.10.10/method-test.txt
```

### DELETE

-  `DELETE /method-test.txt` 요청 확인 필요
    

```bash
curl -i -X DELETE http://172.168.10.10/method-test.txt
```

## 9. 판단

|항목|판단|
|---|---|
|1차 분류|B 가능성 높음|
|판정 상태|실행 검증 일부 완료|
|조치 상태|별도 조치 불필요 가능성 높음|
|증거 상태|OPTIONS, TRACE, PUT 증거 확보 / DELETE 미확인|

현재 서버는 `TRACE`와 `PUT`을 `405 Method Not Allowed`로 차단한다. 특히 `PUT` 응답의 `Allow` header에서 허용 Method가 `GET,POST,OPTIONS,HEAD`로 표시되므로, 임의 파일 생성에 악용될 수 있는 `PUT`은 허용되지 않는 것으로 확인했다.

`OPTIONS`는 `200 OK`로 응답하지만, 이는 서버가 허용 Method 정보를 확인하는 요청을 처리하거나 PHP 애플리케이션이 메인 페이지를 반환한 것으로 보인다. `OPTIONS` 허용 자체만으로 임의 파일 생성, 삭제, 요청 반사 같은 직접적인 악용이 확인되지는 않는다.

따라서 현재까지의 증거 기준으로 21번은 취약으로 보기 어렵고, **B 판정 가능성이 높다.** 다만 `DELETE`는 아직 확인하지 않았으므로, `DELETE`까지 차단되는 것을 확인한 뒤 최종적으로 B로 확정한다.
