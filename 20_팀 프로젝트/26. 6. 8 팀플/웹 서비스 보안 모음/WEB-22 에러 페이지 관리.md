---

type: lab  
topic: web-service-security  
source: 주요정보통신기반시설 기술적 취약점 분석·평가 방법 상세가이드  
source_pages:

- 338
    
- 339
    
- 340
    
- 341  
status: draft  
created: 2026-06-18  
tags:
    
- 🏷️과목/웹서비스보안
    
- 🏷️주제/WEB-22
    
- 🏷️주제/ErrorDocument
    
- 🏷️주제/Error-Page
    
- 🏷️주제/Apache
    
- 🏷️상태/draft
    

---
# WEB-22 에러 페이지 관리

## 1. PDF 기준

PDF p.338-341의 WEB-22는 웹 서비스에서 **에러 페이지가 별도로 지정되어 있는지**, 그리고 에러 페이지에서 **웹 서버 버전, 운영체제, 내부 경로, 상세 에러 코드 등 불필요한 정보가 노출되지 않는지** 점검하는 항목이다.

웹 서버에서 404, 403, 500 같은 오류가 발생하면 기본 에러 페이지가 출력될 수 있다. 기본 에러 페이지는 서버 종류, 서버 버전, 포트, 요청 경로, 내부 구성 힌트 등을 노출할 수 있다.

예를 들어 기본 에러 페이지 하단에 다음과 같은 정보가 표시되면 공격자에게 서버 환경 정보를 제공하게 된다.

```text
Apache/2.4.58 (Ubuntu) Server at 172.168.10.10 Port 80
```

PDF의 판단 기준은 다음과 같다.

|판단|기준|
|---|---|
|양호|웹 서비스 에러 페이지가 별도로 지정된 경우|
|취약|웹 서비스 에러 페이지가 별도로 지정되지 않거나, 에러 발생 시 중요 정보가 노출되는 경우|

PDF의 Apache 조치 방향은 필수 에러 코드에 대해 일원화된 에러 페이지를 설정하는 것이다.

```apache
ErrorDocument 400 /error.html
ErrorDocument 401 /error.html
ErrorDocument 403 /error.html
ErrorDocument 404 /error.html
ErrorDocument 500 /error.html
ErrorDocument 503 /error.html
```

이 항목의 핵심은 다음이다.

```text
1. 에러 코드별 기본 Apache 에러 페이지를 그대로 쓰지 않는다.
2. 별도의 사용자 정의 에러 페이지를 지정한다.
3. 에러 페이지 본문에 서버 버전, OS, 내부 경로, 스택 트레이스, 상세 설정 정보를 노출하지 않는다.
4. 필수 에러 코드에 대해 일관된 에러 페이지를 사용한다.
```

## 2. 최초 진단 결과

`AWS WEB 약점 진단 결과.md` 기준 WEB-22의 최초 진단 결과는 **취약**이다.

|항목|내용|
|---|---|
|진단 결과|취약|
|진단 근거|`ErrorDocument` 설정 없음|
|진단 결과 메시지|`No ErrorDocument directives found`|
|관련 설정|Apache `ErrorDocument` 지시자|
|최초 판단|별도 에러 페이지가 지정되지 않았으므로 취약|

진단 명령어는 다음과 같다.

```bash
grep -rE '^\s*ErrorDocument\s+(400|401|403|404|500|503)' /etc/apache2/apache2.conf /etc/apache2/sites-available/ 2>/dev/null | grep -v '^\s*#'
```

진단 결과는 다음과 같다.

```text
No ErrorDocument directives found
```

따라서 최초 상태에서는 필수 에러 코드에 대한 사용자 정의 에러 페이지가 설정되어 있지 않으므로 WEB-22는 취약으로 판단한다.

## 3. 현재 서버 상태 해석

WEB-22는 단순히 `ServerSignature Off` 여부만 보는 항목이 아니다.

WEB-16에서 서버 헤더 정보 노출을 줄였더라도, WEB-22에서는 에러 페이지 자체가 별도로 관리되는지 확인해야 한다.

|확인 대상|의미|
|---|---|
|`ErrorDocument 400`|잘못된 요청에 대한 사용자 정의 페이지|
|`ErrorDocument 401`|인증 필요 응답에 대한 사용자 정의 페이지|
|`ErrorDocument 403`|접근 거부 응답에 대한 사용자 정의 페이지|
|`ErrorDocument 404`|존재하지 않는 페이지에 대한 사용자 정의 페이지|
|`ErrorDocument 500`|내부 서버 오류 응답에 대한 사용자 정의 페이지|
|`ErrorDocument 503`|서비스 사용 불가 응답에 대한 사용자 정의 페이지|
|에러 페이지 본문|서버 정보, 내부 경로, 스택 트레이스 노출 여부|
|`ServerSignature`|기본 에러 페이지 하단 서버 서명 노출 여부|

취약한 상태는 다음과 같다.

```text
ErrorDocument 설정 없음
기본 Apache 에러 페이지 출력
에러 페이지에 Apache 버전, OS, 포트 정보 노출
애플리케이션 오류 시 PHP 경고, 경로, SQL 오류, 스택 트레이스 노출
```

양호한 상태는 다음과 같다.

```text
필수 에러 코드에 대해 별도 에러 페이지 지정
에러 페이지 문구는 사용자 안내 중심
서버 버전, OS, 내부 경로, 상세 오류 내용 미노출
```

이 항목은 WEB-16과 연결된다.

|연결 항목|연결 이유|
|---|---|
|WEB-16 웹 서비스 헤더 정보 노출 제한|`ServerSignature Off`, `ServerTokens Prod`로 기본 에러 페이지의 서버 정보 노출을 줄임|
|WEB-22 에러 페이지 관리|기본 에러 페이지 대신 사용자 정의 에러 페이지를 사용함|

즉 WEB-16은 “서버가 자동으로 붙이는 정보”를 줄이는 항목이고, WEB-22는 “에러 응답 화면 자체”를 통제하는 항목이다.

## 4. 실습 전 확인

실습 전 현재 Apache 설정과 에러 페이지 응답을 확인한다.

### 4-1. 실습용 변수 지정

```bash
SERVER=http://172.168.10.10
APP_ROOT=/var/www/care
ERROR_DIR="$APP_ROOT/errors"
ERROR_PAGE="$ERROR_DIR/error.html"
TEST_CONF=/etc/apache2/conf-available/web-22-error-page.conf
```

현재 서버 IP나 DocumentRoot가 다르면 `SERVER`, `APP_ROOT` 값을 실제 환경에 맞게 바꾼다.

### 4-2. Apache 가상호스트 확인

```bash
apache2ctl -S
```

### 4-3. DocumentRoot 확인

```bash
grep -R "DocumentRoot" /etc/apache2/sites-enabled/ /etc/apache2/sites-available/ 2>/dev/null
```

### 4-4. 현재 ErrorDocument 설정 확인

```bash
grep -rE '^\s*ErrorDocument\s+(400|401|403|404|500|503)' \
/etc/apache2/apache2.conf \
/etc/apache2/sites-enabled/ \
/etc/apache2/sites-available/ \
/etc/apache2/conf-enabled/ \
/etc/apache2/conf-available/ 2>/dev/null | grep -v '^\s*#'
```

취약 상태에서는 다음처럼 출력이 없을 수 있다.

```text
출력 없음
```

또는 진단 결과처럼 다음으로 정리할 수 있다.

```text
No ErrorDocument directives found
```

### 4-5. 기본 404 에러 페이지 확인

존재하지 않는 경로를 요청한다.

```bash
curl -i "$SERVER/web22-not-found-test"
```

취약 상태에서는 Apache 기본 404 페이지가 출력될 수 있다.

```text
HTTP/1.1 404 Not Found
```

본문에 다음과 같은 기본 문구가 보이면 사용자 정의 에러 페이지가 적용되지 않은 상태다.

```html
<title>404 Not Found</title>
<h1>Not Found</h1>
```

### 4-6. 기본 403 에러 페이지 확인용 디렉터리 생성

403 응답 확인을 위해 실습용 접근 차단 디렉터리를 만든다.

```bash
sudo mkdir -p "$APP_ROOT/web22-forbidden-test"
```

```bash
echo "WEB-22 forbidden test" | sudo tee "$APP_ROOT/web22-forbidden-test/index.html"
```

Apache가 파일을 읽지 못하게 권한을 제한한다.

```bash
sudo chmod 000 "$APP_ROOT/web22-forbidden-test"
```

403 응답을 확인한다.

```bash
curl -i "$SERVER/web22-forbidden-test/"
```

취약 상태에서는 기본 403 에러 페이지가 출력될 수 있다.

```text
HTTP/1.1 403 Forbidden
```

확인 후 권한을 되돌려 정리 가능하게 만든다.

```bash
sudo chmod 755 "$APP_ROOT/web22-forbidden-test"
```

## 5. 취약 재현

이 항목은 최초 진단에서 이미 취약으로 확인되었다.

취약 재현의 핵심은 다음이다.

```text
ErrorDocument 설정이 없는 상태에서 404 또는 403 에러를 발생시켜
기본 Apache 에러 페이지가 출력되는지 확인한다.
```

### 5-1. ErrorDocument 부재 확인

```bash
grep -rE '^\s*ErrorDocument\s+(400|401|403|404|500|503)' \
/etc/apache2/apache2.conf \
/etc/apache2/sites-enabled/ \
/etc/apache2/sites-available/ \
/etc/apache2/conf-enabled/ \
/etc/apache2/conf-available/ 2>/dev/null | grep -v '^\s*#'
```

취약 상태 기대 결과:

```text
출력 없음
```

### 5-2. 404 기본 에러 페이지 확인

```bash
curl -i "$SERVER/web22-not-found-test"
```

취약 상태 기대 결과:

```text
HTTP/1.1 404 Not Found
```

본문 예시:

```html
<title>404 Not Found</title>
<h1>Not Found</h1>
```

### 5-3. 403 기본 에러 페이지 확인

```bash
sudo mkdir -p "$APP_ROOT/web22-forbidden-test"
echo "WEB-22 forbidden test" | sudo tee "$APP_ROOT/web22-forbidden-test/index.html"
sudo chmod 000 "$APP_ROOT/web22-forbidden-test"
```

```bash
curl -i "$SERVER/web22-forbidden-test/"
```

취약 상태 기대 결과:

```text
HTTP/1.1 403 Forbidden
```

기본 에러 페이지가 출력되면 별도 에러 페이지가 지정되지 않은 상태이므로 PDF 기준 취약이다.

확인 후 권한을 복구한다.

```bash
sudo chmod 755 "$APP_ROOT/web22-forbidden-test"
```

## 6. 조치 방법

조치 핵심은 필수 에러 코드에 대해 일원화된 사용자 정의 에러 페이지를 설정하는 것이다.

### 6-1. 에러 페이지 디렉터리 생성

```bash
sudo mkdir -p "$ERROR_DIR"
```

### 6-2. 사용자 정의 에러 페이지 생성

```bash
sudo tee "$ERROR_PAGE" > /dev/null <<'EOF'
<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <title>요청을 처리할 수 없습니다</title>
</head>
<body>
  <h1>요청을 처리할 수 없습니다</h1>
  <p>요청하신 페이지를 찾을 수 없거나, 현재 접근할 수 없습니다.</p>
  <p>입력한 주소를 다시 확인하거나, 잠시 후 다시 시도해 주세요.</p>
</body>
</html>
EOF
```

에러 페이지에는 다음 내용을 넣지 않는다.

```text
Apache 버전
Ubuntu 버전
서버 내부 경로
PHP 경고 메시지
SQL 오류 메시지
스택 트레이스
상세 예외 메시지
```

### 6-3. 권한 설정

```bash
sudo chown -R root:www-data "$ERROR_DIR"
```

```bash
sudo find "$ERROR_DIR" -type d -exec chmod 750 {} \;
```

```bash
sudo find "$ERROR_DIR" -type f -exec chmod 640 {} \;
```

Apache가 읽을 수 있는지 확인한다.

```bash
sudo -u www-data cat "$ERROR_PAGE"
```

### 6-4. ErrorDocument 설정 파일 생성

```bash
sudo tee "$TEST_CONF" > /dev/null <<'EOF'
ErrorDocument 400 /errors/error.html
ErrorDocument 401 /errors/error.html
ErrorDocument 403 /errors/error.html
ErrorDocument 404 /errors/error.html
ErrorDocument 500 /errors/error.html
ErrorDocument 503 /errors/error.html
EOF
```

핵심 설정은 다음이다.

```apache
ErrorDocument 400 /errors/error.html
ErrorDocument 401 /errors/error.html
ErrorDocument 403 /errors/error.html
ErrorDocument 404 /errors/error.html
ErrorDocument 500 /errors/error.html
ErrorDocument 503 /errors/error.html
```

### 6-5. 설정 활성화

```bash
sudo a2enconf web-22-error-page
```

### 6-6. Apache 설정 문법 검사

```bash
sudo apachectl configtest
```

정상이라면 다음 결과가 나와야 한다.

```text
Syntax OK
```

### 6-7. Apache restart

```bash
sudo systemctl restart apache2
```

## 7. 조치 후 확인

조치 후에는 404, 403 등 주요 에러 응답에서 사용자 정의 에러 페이지가 출력되는지 확인한다.

### 7-1. ErrorDocument 설정 확인

```bash
grep -rE '^\s*ErrorDocument\s+(400|401|403|404|500|503)' \
/etc/apache2/apache2.conf \
/etc/apache2/sites-enabled/ \
/etc/apache2/sites-available/ \
/etc/apache2/conf-enabled/ \
/etc/apache2/conf-available/ 2>/dev/null | grep -v '^\s*#'
```

기대 결과:

```text
ErrorDocument 400 /errors/error.html
ErrorDocument 401 /errors/error.html
ErrorDocument 403 /errors/error.html
ErrorDocument 404 /errors/error.html
ErrorDocument 500 /errors/error.html
ErrorDocument 503 /errors/error.html
```

### 7-2. 404 사용자 정의 에러 페이지 확인

```bash
curl -i "$SERVER/web22-not-found-test"
```

조치 후 기대 결과:

```text
HTTP/1.1 404 Not Found
```

본문에 다음 문구가 포함되어야 한다.

```text
요청을 처리할 수 없습니다
```

기본 Apache 에러 페이지 문구가 사라졌는지 확인한다.

```bash
curl -s "$SERVER/web22-not-found-test" | grep -Ei 'Apache/[0-9]|Ubuntu|Server at|Not Found'
```

기대 결과:

```text
출력 없음
```

단, 사용자 정의 페이지에 직접 `Not Found` 같은 문구를 넣었다면 출력될 수 있으므로, 에러 페이지 문구 설계에 맞춰 판단한다.

### 7-3. 403 사용자 정의 에러 페이지 확인

403 테스트 디렉터리를 다시 접근 차단 상태로 만든다.

```bash
sudo chmod 000 "$APP_ROOT/web22-forbidden-test"
```

```bash
curl -i "$SERVER/web22-forbidden-test/"
```

조치 후 기대 결과:

```text
HTTP/1.1 403 Forbidden
```

본문에 다음 문구가 포함되어야 한다.

```text
요청을 처리할 수 없습니다
```

확인 후 권한을 복구한다.

```bash
sudo chmod 755 "$APP_ROOT/web22-forbidden-test"
```

### 7-4. 에러 페이지 내 정보 노출 점검

```bash
curl -s "$SERVER/web22-not-found-test" | grep -Ei 'Apache/[0-9]|Ubuntu|/var/www|/etc/apache2|PHP Warning|SQL|Stack trace|Exception'
```

조치 후 기대 결과:

```text
출력 없음
```

### 7-5. Apache 서비스 상태 확인

```bash
systemctl status apache2 --no-pager
```

정상 상태라면 다음과 같이 보여야 한다.

```text
Active: active (running)
```

### 7-6. CARE 서비스 정상 응답 확인

```bash
curl -i "$SERVER/"
```

정상이라면 CARE 애플리케이션의 메인 페이지, 로그인 페이지, 리다이렉트 등 현재 서비스에 맞는 응답이 나와야 한다.

```text
HTTP/1.1 200 OK
```

또는:

```text
HTTP/1.1 302 Found
```

## 8. 실행 순서 요약

### 8-1. 현재 상태 확인

```bash
SERVER=http://172.168.10.10
APP_ROOT=/var/www/care
ERROR_DIR="$APP_ROOT/errors"
ERROR_PAGE="$ERROR_DIR/error.html"
TEST_CONF=/etc/apache2/conf-available/web-22-error-page.conf
```

```bash
apache2ctl -S
```

```bash
grep -R "DocumentRoot" /etc/apache2/sites-enabled/ /etc/apache2/sites-available/ 2>/dev/null
```

```bash
grep -rE '^\s*ErrorDocument\s+(400|401|403|404|500|503)' \
/etc/apache2/apache2.conf \
/etc/apache2/sites-enabled/ \
/etc/apache2/sites-available/ \
/etc/apache2/conf-enabled/ \
/etc/apache2/conf-available/ 2>/dev/null | grep -v '^\s*#'
```

```bash
curl -i "$SERVER/web22-not-found-test"
```

### 8-2. 취약 상태 확인

```bash
curl -i "$SERVER/web22-not-found-test"
```

취약 상태 예시:

```text
HTTP/1.1 404 Not Found

<title>404 Not Found</title>
<h1>Not Found</h1>
```

```bash
sudo mkdir -p "$APP_ROOT/web22-forbidden-test"
echo "WEB-22 forbidden test" | sudo tee "$APP_ROOT/web22-forbidden-test/index.html"
sudo chmod 000 "$APP_ROOT/web22-forbidden-test"
curl -i "$SERVER/web22-forbidden-test/"
sudo chmod 755 "$APP_ROOT/web22-forbidden-test"
```

취약 상태 예시:

```text
HTTP/1.1 403 Forbidden
```

### 8-3. 조치 적용

```bash
sudo mkdir -p "$ERROR_DIR"
```

```bash
sudo tee "$ERROR_PAGE" > /dev/null <<'EOF'
<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <title>요청을 처리할 수 없습니다</title>
</head>
<body>
  <h1>요청을 처리할 수 없습니다</h1>
  <p>요청하신 페이지를 찾을 수 없거나, 현재 접근할 수 없습니다.</p>
  <p>입력한 주소를 다시 확인하거나, 잠시 후 다시 시도해 주세요.</p>
</body>
</html>
EOF
```

```bash
sudo chown -R root:www-data "$ERROR_DIR"
sudo find "$ERROR_DIR" -type d -exec chmod 750 {} \;
sudo find "$ERROR_DIR" -type f -exec chmod 640 {} \;
```

```bash
sudo tee "$TEST_CONF" > /dev/null <<'EOF'
ErrorDocument 400 /errors/error.html
ErrorDocument 401 /errors/error.html
ErrorDocument 403 /errors/error.html
ErrorDocument 404 /errors/error.html
ErrorDocument 500 /errors/error.html
ErrorDocument 503 /errors/error.html
EOF
```

```bash
sudo a2enconf web-22-error-page
```

```bash
sudo apachectl configtest
```

```bash
sudo systemctl restart apache2
```

### 8-4. 조치 후 확인

```bash
grep -rE '^\s*ErrorDocument\s+(400|401|403|404|500|503)' \
/etc/apache2/apache2.conf \
/etc/apache2/sites-enabled/ \
/etc/apache2/sites-available/ \
/etc/apache2/conf-enabled/ \
/etc/apache2/conf-available/ 2>/dev/null | grep -v '^\s*#'
```

기대 결과:

```text
ErrorDocument 400 /errors/error.html
ErrorDocument 401 /errors/error.html
ErrorDocument 403 /errors/error.html
ErrorDocument 404 /errors/error.html
ErrorDocument 500 /errors/error.html
ErrorDocument 503 /errors/error.html
```

```bash
curl -i "$SERVER/web22-not-found-test"
```

기대 결과:

```text
HTTP/1.1 404 Not Found

요청을 처리할 수 없습니다
```

```bash
sudo chmod 000 "$APP_ROOT/web22-forbidden-test"
curl -i "$SERVER/web22-forbidden-test/"
sudo chmod 755 "$APP_ROOT/web22-forbidden-test"
```

기대 결과:

```text
HTTP/1.1 403 Forbidden

요청을 처리할 수 없습니다
```

```bash
curl -s "$SERVER/web22-not-found-test" | grep -Ei 'Apache/[0-9]|Ubuntu|/var/www|/etc/apache2|PHP Warning|SQL|Stack trace|Exception'
```

기대 결과:

```text
출력 없음
```

```bash
systemctl status apache2 --no-pager
```

기대 결과:

```text
Active: active (running)
```

### 8-5. 실습용 파일 정리

WEB-22 조치를 실제로 유지할 목적이면 `ErrorDocument` 설정과 `/errors/error.html`은 제거하지 않는다.

실습용으로만 적용했다면 증거 확보 후 제거한다.

```bash
sudo a2disconf web-22-error-page
```

```bash
sudo rm -f "$TEST_CONF"
```

```bash
sudo rm -rf "$ERROR_DIR"
```

```bash
sudo rm -rf "$APP_ROOT/web22-forbidden-test"
```

```bash
sudo apachectl configtest
```

```bash
sudo systemctl restart apache2
```

단, WEB-22는 실제 취약 항목이므로 운영 조치 목적이라면 정리하지 않고 유지하는 편이 맞다.

## 9. 증거 정리

### 9-1. 최초 상태 증거

최초 진단 결과:

```text
WEB-22 · 웹서비스 에러페이지 사용

ErrorDocument 설정 없음 — 기본 Apache 에러 페이지 노출 시 서버 정보 유출 위험

No ErrorDocument directives found
```

진단 명령어:

```bash
grep -rE '^\s*ErrorDocument\s+(400|401|403|404|500|503)' /etc/apache2/apache2.conf /etc/apache2/sites-available/ 2>/dev/null | grep -v '^\s*#'
```

진단 결과:

```text
No ErrorDocument directives found
```

### 9-2. 취약 상태 증거

404 기본 에러 페이지 확인:

```bash
curl -i "$SERVER/web22-not-found-test"
```

취약 상태 예시:

```text
HTTP/1.1 404 Not Found

<title>404 Not Found</title>
<h1>Not Found</h1>
```

403 기본 에러 페이지 확인:

```bash
sudo chmod 000 "$APP_ROOT/web22-forbidden-test"
curl -i "$SERVER/web22-forbidden-test/"
sudo chmod 755 "$APP_ROOT/web22-forbidden-test"
```

취약 상태 예시:

```text
HTTP/1.1 403 Forbidden
```

### 9-3. 조치 후 증거

ErrorDocument 설정 확인:

```bash
grep -rE '^\s*ErrorDocument\s+(400|401|403|404|500|503)' \
/etc/apache2/apache2.conf \
/etc/apache2/sites-enabled/ \
/etc/apache2/sites-available/ \
/etc/apache2/conf-enabled/ \
/etc/apache2/conf-available/ 2>/dev/null | grep -v '^\s*#'
```

조치 후 기대 결과:

```text
ErrorDocument 400 /errors/error.html
ErrorDocument 401 /errors/error.html
ErrorDocument 403 /errors/error.html
ErrorDocument 404 /errors/error.html
ErrorDocument 500 /errors/error.html
ErrorDocument 503 /errors/error.html
```

404 사용자 정의 에러 페이지 확인:

```bash
curl -i "$SERVER/web22-not-found-test"
```

조치 후 기대 결과:

```text
HTTP/1.1 404 Not Found

요청을 처리할 수 없습니다
```

정보 노출 문자열 점검:

```bash
curl -s "$SERVER/web22-not-found-test" | grep -Ei 'Apache/[0-9]|Ubuntu|/var/www|/etc/apache2|PHP Warning|SQL|Stack trace|Exception'
```

조치 후 기대 결과:

```text
출력 없음
```

## 10. 판단

|항목|판단|
|---|---|
|최초 진단|취약|
|진단 근거|`ErrorDocument` 설정 없음|
|취약 조건|기본 Apache 에러 페이지가 출력되거나 에러 페이지에서 서버 정보, 내부 경로, 상세 오류가 노출됨|
|양호 조건|필수 에러 코드에 대해 사용자 정의 에러 페이지가 지정되고 불필요 정보가 노출되지 않음|
|조치 방향|`ErrorDocument 400/401/403/404/500/503 /errors/error.html` 설정 추가|
|증거 상태|최초 진단 결과 확보, 조치 후 404/403 에러 페이지 확인 필요|

현재 서버는 최초 진단 기준으로 `ErrorDocument` 설정이 없으므로 WEB-22는 **취약**으로 판단한다.

조치는 `/var/www/care/errors/error.html`처럼 별도 사용자 정의 에러 페이지를 생성하고, Apache 설정에 400, 401, 403, 404, 500, 503 에러 코드별 `ErrorDocument`를 지정하는 방식으로 수행한다.

조치 후 404와 403 요청에서 사용자 정의 에러 페이지가 출력되고, 페이지 본문에 Apache 버전, Ubuntu 정보, 내부 경로, PHP 경고, SQL 오류, 스택 트레이스 등이 노출되지 않으면 WEB-22는 조치 후 **양호**로 판단한다.