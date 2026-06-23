---
type: lab  
topic: web-service-security  
source: 주요정보통신기반시설 기술적 취약점 분석·평가 방법 상세가이드  
source_pages:
- 292
- 293    
- 294  
status: draft  
created: 2026-06-18  
tags:
    
- 🏷️과목/웹서비스보안
    
- 🏷️주제/WEB-08
    
- 🏷️주제/Upload-Download-Limit
    
- 🏷️주제/Apache
    
- 🏷️상태/draft
    

---
# WEB-08 웹 서비스 파일 업로드 및 다운로드 용량 제한

## 1. PDF 기준

PDF p.292-294의 WEB-08은 웹 서비스에서 **파일 업로드 및 다운로드 용량 제한이 설정되어 있는지** 점검하는 항목이다.

웹 서비스에서 파일 업로드나 다운로드 기능을 제공할 경우, 용량 제한이 없으면 다음 문제가 발생할 수 있다.

```text
1. 공격자가 대용량 파일을 반복 업로드하여 서버 디스크나 웹 서버 자원을 고갈시킬 수 있다.
2. 업로드 기능이 웹 쉘 업로드와 결합되면 시스템 침해로 이어질 수 있다.
3. 대용량 요청이 반복되면 서비스 지연 또는 장애가 발생할 수 있다.
4. 정책상 허용되지 않은 파일이 업로드되거나 다운로드될 수 있다.
```

PDF의 판단 기준은 다음과 같다.

|판단|기준|
|---|---|
|양호|파일 업로드 및 다운로드 용량을 제한한 경우|
|취약|파일 업로드 및 다운로드 용량을 제한하지 않은 경우|

PDF의 Apache 조치 예시는 `LimitRequestBody` 지시자를 사용하여 요청 본문 크기를 제한하는 방식이다.

```apache
<Directory />
    LimitRequestBody 5000000
</Directory>
```

`LimitRequestBody`는 Apache가 클라이언트 요청 본문 크기를 제한하는 지시자다. 파일 업로드는 HTTP 요청 본문에 파일 데이터가 포함되므로, 이 값을 설정하면 일정 크기를 초과하는 업로드 요청을 웹 서버 단계에서 차단할 수 있다.

PDF 예시에서는 `5000000` 바이트, 즉 약 5MB 수준의 제한을 제시한다.

```text
5000000 bytes ≒ 약 5 MB
```

다만 다운로드 용량 제한은 Apache의 `LimitRequestBody`만으로 직접 통제되는 항목은 아니다. `LimitRequestBody`는 주로 업로드처럼 클라이언트가 서버로 보내는 요청 본문 크기를 제한한다. 다운로드 크기 제한은 애플리케이션 로직, 파일 제공 정책, 별도 웹 서버 모듈, 접근 통제 정책과 함께 관리해야 한다.

따라서 Apache 환경에서 WEB-08은 다음처럼 해석한다.

|구분|Apache 기준 해석|
|---|---|
|업로드 용량 제한|`LimitRequestBody`, PHP `upload_max_filesize`, `post_max_size` 확인|
|다운로드 용량 제한|CARE 애플리케이션의 파일 제공 정책, 파일 저장 위치, 다운로드 기능 구현 여부 확인|
|서버 자원 보호|대용량 요청이 웹 서버나 PHP에 과도하게 전달되지 않도록 제한|

## 2. 최초 진단 결과

`AWS WEB 약점 진단 결과.md`와 PDF의 WEB-08 항목명이 서로 일치하지 않는다.

진단 결과 파일의 WEB-08은 다음처럼 기록되어 있다.

```text
WEB-08 · .htaccess 오버라이드 제한
AllowOverride All 없음 — .htaccess 를 통한 보안 설정 변경 불가
```

하지만 PDF p.292-294의 WEB-08은 다음 항목이다.

```text
WEB-08 · 웹 서비스 파일 업로드 및 다운로드 용량 제한
```

따라서 이 노트에서는 진단 결과 파일의 WEB-08 판정을 그대로 사용하지 않는다.

|항목|내용|
|---|---|
|PDF 기준 WEB-08|파일 업로드 및 다운로드 용량 제한|
|AWS 진단 결과의 WEB-08|`.htaccess` 오버라이드 제한|
|상태|항목명 불일치|
|최초 판단|PDF 기준 WEB-08은 수동 확인 필요|
|확인 대상|`LimitRequestBody`, PHP 업로드 제한, CARE 업로드·다운로드 기능|

이 항목은 직접 설정을 확인해야 한다.

## 3. 현재 서버 상태 해석

WEB-08은 Apache 설정과 PHP 설정을 함께 봐야 한다.

Apache에서 업로드 크기를 제한하는 대표 설정은 `LimitRequestBody`다.

PHP 기반 애플리케이션에서는 다음 설정도 함께 영향을 준다.

|설정|의미|
|---|---|
|`LimitRequestBody`|Apache가 허용하는 HTTP 요청 본문 최대 크기|
|`upload_max_filesize`|PHP가 허용하는 업로드 파일 1개의 최대 크기|
|`post_max_size`|PHP가 허용하는 전체 POST 요청 최대 크기|
|`max_file_uploads`|한 요청에서 허용되는 최대 업로드 파일 개수|

Apache의 `LimitRequestBody`가 작으면 Apache 단계에서 먼저 요청을 차단한다.  
PHP의 `post_max_size`나 `upload_max_filesize`가 작으면 Apache를 통과한 요청이 PHP 단계에서 제한된다.

일반적으로 다음 관계가 자연스럽다.

```text
LimitRequestBody >= post_max_size >= upload_max_filesize
```

다만 보안 관점에서는 웹 서버 단계에서 너무 큰 요청을 먼저 거부하는 것이 유리하다.

CARE 서버에서 파일 업로드 기능이 실제로 존재하는 경우, 이 항목은 업로드 기능과 직접 연결된다. 파일 업로드 기능이 없다면, 서버 차원의 대용량 POST 요청 제한 여부를 중심으로 확인한다.

## 4. 실습 전 확인

실습을 시작하기 전에 현재 Apache, PHP, DocumentRoot 상태를 확인한다.

### 4-1. Apache 가상호스트 확인

```bash
apache2ctl -S
```

### 4-2. DocumentRoot 확인

```bash
grep -R "DocumentRoot" /etc/apache2/sites-enabled/ /etc/apache2/sites-available/ 2>/dev/null
```

이 노트는 CARE 서버의 DocumentRoot가 `/var/www/html/care`라고 가정한다.

실습용 변수를 지정한다.

```bash
APP_ROOT=/var/www/html/care
SERVER=http://172.168.10.10
TEST_PHP="$APP_ROOT/web08-upload-test.php"
TEST_CONF="/etc/apache2/conf-available/web-08-limit-test.conf"
SMALL_FILE=/tmp/web08-small.bin
BIG_FILE=/tmp/web08-big.bin
```

현재 서버의 DocumentRoot가 다르면 `APP_ROOT` 값을 실제 경로로 바꾼다.

### 4-3. Apache의 LimitRequestBody 설정 확인

```bash
grep -R "LimitRequestBody" /etc/apache2/apache2.conf /etc/apache2/sites-enabled/ /etc/apache2/sites-available/ /etc/apache2/conf-enabled/ /etc/apache2/conf-available/ 2>/dev/null | grep -v '^\s*#'
```

출력이 없으면 Apache 설정에서 요청 본문 크기 제한이 명시적으로 설정되지 않은 상태다.

```text
출력 없음
```

이 경우 PDF 기준으로는 업로드 용량 제한 확인이 필요하다.

### 4-4. PHP 업로드 제한 확인

```bash
php -i | grep -E "upload_max_filesize|post_max_size|max_file_uploads"
```

예상 출력 예시는 다음과 같다.

```text
max_file_uploads => 20 => 20
post_max_size => 8M => 8M
upload_max_filesize => 2M => 2M
```

Apache에서 제한이 없더라도 PHP에서 제한이 있으면 업로드가 일부 제한될 수 있다.  
하지만 PDF의 Apache 조치 예시는 Apache 설정의 `LimitRequestBody`를 기준으로 하므로, 이 노트에서는 Apache 단계의 제한 설정을 중심으로 실습한다.

## 5. 취약 재현

이 항목은 PDF 기준 최초 진단 결과가 확정되어 있지 않으므로, 먼저 취약 상태를 재현한다.

> 주의: 이 절차는 격리된 실습 서버에서만 수행한다.  
> 실습 파일은 `/tmp`와 CARE 테스트 PHP 파일만 사용한다.  
> 실제 대용량 파일을 과도하게 생성하거나 반복 요청하지 않는다.  
> 실습 후에는 테스트 설정과 파일을 제거한다.

취약 재현의 핵심은 다음이다.

```text
Apache에서 LimitRequestBody 제한이 없거나 매우 크게 설정되어,
5MB를 초과하는 POST 요청이 웹 서버 단계에서 차단되지 않는 상태를 확인한다.
```

### 5-1. 테스트 PHP 파일 생성

요청이 PHP까지 도달했는지 확인하기 위해 테스트 PHP 파일을 만든다.  
이 파일은 업로드 파일을 저장하지 않고, 요청 크기만 출력한다.

```bash
sudo tee "$TEST_PHP" > /dev/null <<'EOF'
<?php
header('Content-Type: text/plain');
echo "WEB-08 upload size test\n";
echo "REQUEST_METHOD=" . $_SERVER['REQUEST_METHOD'] . "\n";
echo "CONTENT_LENGTH=" . ($_SERVER['CONTENT_LENGTH'] ?? 'none') . "\n";
EOF
```

권한을 정리한다.

```bash
sudo chown www-data:www-data "$TEST_PHP"
sudo chmod 640 "$TEST_PHP"
ls -l "$TEST_PHP"
```

### 5-2. 테스트 파일 생성

1MB 파일을 만든다.

```bash
dd if=/dev/zero of="$SMALL_FILE" bs=1M count=1 status=none
```

6MB 파일을 만든다.

```bash
dd if=/dev/zero of="$BIG_FILE" bs=1M count=6 status=none
```

파일 크기를 확인한다.

```bash
ls -lh "$SMALL_FILE" "$BIG_FILE"
```

기대 결과는 다음과 유사하다.

```text
-rw-r--r-- 1 root root 1.0M /tmp/web08-small.bin
-rw-r--r-- 1 root root 6.0M /tmp/web08-big.bin
```

### 5-3. 작은 요청 확인

```bash
curl -i -X POST --data-binary @"$SMALL_FILE" "$SERVER/web08-upload-test.php"
```

기대 결과는 다음과 유사하다.

```text
HTTP/1.1 200 OK

WEB-08 upload size test
REQUEST_METHOD=POST
CONTENT_LENGTH=1048576
```

### 5-4. 큰 요청 확인

```bash
curl -i -X POST --data-binary @"$BIG_FILE" "$SERVER/web08-upload-test.php"
```

취약 상태라면 Apache 단계에서 차단되지 않고 PHP까지 요청이 도달한다.

기대 결과는 다음과 유사하다.

```text
HTTP/1.1 200 OK

WEB-08 upload size test
REQUEST_METHOD=POST
CONTENT_LENGTH=6291456
```

이 결과는 5MB를 초과하는 요청이 웹 서버 단계에서 차단되지 않았다는 뜻이다.

단, PHP의 `post_max_size`가 더 작게 설정되어 있으면 PHP 동작에 따라 다른 결과가 나올 수 있다. 이 경우 Apache의 `LimitRequestBody` 설정 확인 결과와 함께 판단한다.

## 6. 조치 방법

조치 핵심은 Apache에서 요청 본문 크기를 허용 가능한 최소 범위로 제한하는 것이다.

PDF 예시 기준으로 5MB 제한을 적용한다.

```text
5MB 기준값: 5000000 bytes
```

### 6-1. 실습용 Apache 제한 설정 생성

CARE DocumentRoot에 대해 `LimitRequestBody 5000000`을 적용한다.

```bash
sudo tee "$TEST_CONF" > /dev/null <<EOF
<Directory $APP_ROOT>
    LimitRequestBody 5000000
</Directory>
EOF
```

이 설정은 `/var/www/html/care` 아래 요청 본문 크기를 약 5MB로 제한한다.

### 6-2. 실습용 설정 활성화

```bash
sudo a2enconf web-08-limit-test
```

### 6-3. Apache 설정 문법 검사

```bash
sudo apachectl configtest
```

정상이라면 다음 결과가 나와야 한다.

```text
Syntax OK
```

### 6-4. Apache restart

```bash
sudo systemctl restart apache2
```

## 7. 조치 후 확인

조치 후에는 5MB 이하 요청은 허용되고, 5MB 초과 요청은 차단되는지 확인한다.

### 7-1. Apache 설정 확인

```bash
grep -R "LimitRequestBody" /etc/apache2/apache2.conf /etc/apache2/sites-enabled/ /etc/apache2/sites-available/ /etc/apache2/conf-enabled/ /etc/apache2/conf-available/ 2>/dev/null | grep -v '^\s*#'
```

기대 결과는 다음과 같다.

```text
LimitRequestBody 5000000
```

### 7-2. 작은 요청 확인

```bash
curl -i -X POST --data-binary @"$SMALL_FILE" "$SERVER/web08-upload-test.php"
```

1MB 요청은 제한값보다 작으므로 정상적으로 처리되어야 한다.

기대 결과는 다음과 유사하다.

```text
HTTP/1.1 200 OK

WEB-08 upload size test
REQUEST_METHOD=POST
CONTENT_LENGTH=1048576
```

### 7-3. 큰 요청 차단 확인

```bash
curl -i -X POST --data-binary @"$BIG_FILE" "$SERVER/web08-upload-test.php"
```

5MB를 초과하는 요청은 차단되어야 한다.

기대 결과는 다음과 유사하다.

```text
HTTP/1.1 413 Request Entity Too Large
```

또는 Apache 버전에 따라 다음 표현이 나올 수 있다.

```text
HTTP/1.1 413 Payload Too Large
```

중요한 것은 6MB 요청이 더 이상 정상 처리되지 않는 것이다.

### 7-4. PHP 제한과 함께 확인

```bash
php -i | grep -E "upload_max_filesize|post_max_size|max_file_uploads"
```

PHP 설정도 운영 정책과 맞는지 확인한다.

예를 들어 Apache에서 5MB를 제한한다면 PHP도 다음처럼 과도하게 크지 않은 값으로 관리하는 것이 좋다.

```text
upload_max_filesize = 2M
post_max_size = 5M 또는 8M
```

## 8. 실행 순서 요약

실습 중에는 아래 순서대로 진행한다.

### 8-1. 현재 상태 확인

```bash
apache2ctl -S
```

```bash
grep -R "DocumentRoot" /etc/apache2/sites-enabled/ /etc/apache2/sites-available/ 2>/dev/null
```

```bash
APP_ROOT=/var/www/html/care
SERVER=http://172.168.10.10
TEST_PHP="$APP_ROOT/web08-upload-test.php"
TEST_CONF="/etc/apache2/conf-available/web-08-limit-test.conf"
SMALL_FILE=/tmp/web08-small.bin
BIG_FILE=/tmp/web08-big.bin
```

```bash
grep -R "LimitRequestBody" /etc/apache2/apache2.conf /etc/apache2/sites-enabled/ /etc/apache2/sites-available/ /etc/apache2/conf-enabled/ /etc/apache2/conf-available/ 2>/dev/null | grep -v '^\s*#'
```

```bash
php -i | grep -E "upload_max_filesize|post_max_size|max_file_uploads"
```

### 8-2. 취약 재현

```bash
sudo tee "$TEST_PHP" > /dev/null <<'EOF'
<?php
header('Content-Type: text/plain');
echo "WEB-08 upload size test\n";
echo "REQUEST_METHOD=" . $_SERVER['REQUEST_METHOD'] . "\n";
echo "CONTENT_LENGTH=" . ($_SERVER['CONTENT_LENGTH'] ?? 'none') . "\n";
EOF
```

```bash
sudo chown www-data:www-data "$TEST_PHP"
sudo chmod 640 "$TEST_PHP"
ls -l "$TEST_PHP"
```

```bash
dd if=/dev/zero of="$SMALL_FILE" bs=1M count=1 status=none
dd if=/dev/zero of="$BIG_FILE" bs=1M count=6 status=none
ls -lh "$SMALL_FILE" "$BIG_FILE"
```

```bash
curl -i -X POST --data-binary @"$SMALL_FILE" "$SERVER/web08-upload-test.php"
```

```bash
curl -i -X POST --data-binary @"$BIG_FILE" "$SERVER/web08-upload-test.php"
```

취약 상태 기대 결과:

```text
HTTP/1.1 200 OK

WEB-08 upload size test
CONTENT_LENGTH=6291456
```

### 8-3. 조치 및 적용

```bash
sudo tee "$TEST_CONF" > /dev/null <<EOF
<Directory $APP_ROOT>
    LimitRequestBody 5000000
</Directory>
EOF
```

```bash
sudo a2enconf web-08-limit-test
```

```bash
sudo apachectl configtest
```

```bash
sudo systemctl restart apache2
```

### 8-4. 조치 후 확인

```bash
grep -R "LimitRequestBody" /etc/apache2/apache2.conf /etc/apache2/sites-enabled/ /etc/apache2/sites-available/ /etc/apache2/conf-enabled/ /etc/apache2/conf-available/ 2>/dev/null | grep -v '^\s*#'
```

```bash
curl -i -X POST --data-binary @"$SMALL_FILE" "$SERVER/web08-upload-test.php"
```

작은 요청 기대 결과:

```text
HTTP/1.1 200 OK
```

```bash
curl -i -X POST --data-binary @"$BIG_FILE" "$SERVER/web08-upload-test.php"
```

큰 요청 기대 결과:

```text
HTTP/1.1 413 Request Entity Too Large
```

또는:

```text
HTTP/1.1 413 Payload Too Large
```

### 8-5. 실습 환경 제거

실습 증거를 확보한 뒤에는 테스트 설정과 파일을 제거한다.

```bash
sudo a2disconf web-08-limit-test
```

```bash
sudo rm -f "$TEST_CONF"
```

```bash
sudo rm -f "$TEST_PHP"
```

```bash
rm -f "$SMALL_FILE" "$BIG_FILE"
```

```bash
sudo apachectl configtest
```

```bash
sudo systemctl restart apache2
```

제거 확인:

```bash
ls -l "$TEST_PHP" "$SMALL_FILE" "$BIG_FILE" 2>/dev/null
```

기대 결과:

```text
출력 없음
```

실습 설정 제거 확인:

```bash
ls -l /etc/apache2/conf-enabled/ | grep web-08-limit-test
```

기대 결과:

```text
출력 없음
```

## 9. 증거 정리

### 9-1. 최초 상태 증거

PDF 기준 WEB-08과 AWS 진단 결과 파일의 WEB-08 항목명이 일치하지 않는다.

```text
PDF WEB-08: 웹 서비스 파일 업로드 및 다운로드 용량 제한
AWS 진단 결과 WEB-08: .htaccess 오버라이드 제한
```

따라서 최초 진단은 PDF 기준으로 별도 확인한다.

Apache 제한 설정 확인:

```bash
grep -R "LimitRequestBody" /etc/apache2/apache2.conf /etc/apache2/sites-enabled/ /etc/apache2/sites-available/ /etc/apache2/conf-enabled/ /etc/apache2/conf-available/ 2>/dev/null | grep -v '^\s*#'
```

PHP 업로드 제한 확인:

```bash
php -i | grep -E "upload_max_filesize|post_max_size|max_file_uploads"
```

### 9-2. 취약 재현 증거

6MB POST 요청:

```bash
curl -i -X POST --data-binary @"$BIG_FILE" "$SERVER/web08-upload-test.php"
```

취약 재현 기대 결과:

```text
HTTP/1.1 200 OK

WEB-08 upload size test
CONTENT_LENGTH=6291456
```

이 결과는 5MB를 초과하는 요청이 Apache 단계에서 차단되지 않고 PHP까지 도달했음을 의미한다.

### 9-3. 조치 후 증거

Apache 제한 설정:

```bash
grep -R "LimitRequestBody" /etc/apache2/apache2.conf /etc/apache2/sites-enabled/ /etc/apache2/sites-available/ /etc/apache2/conf-enabled/ /etc/apache2/conf-available/ 2>/dev/null | grep -v '^\s*#'
```

기대 결과:

```text
LimitRequestBody 5000000
```

6MB POST 요청 재확인:

```bash
curl -i -X POST --data-binary @"$BIG_FILE" "$SERVER/web08-upload-test.php"
```

조치 후 기대 결과:

```text
HTTP/1.1 413 Request Entity Too Large
```

또는:

```text
HTTP/1.1 413 Payload Too Large
```

## 10. 판단

|항목|판단|
|---|---|
|최초 진단|확인 필요|
|진단 근거|AWS 진단 결과의 WEB-08 항목명이 PDF WEB-08과 불일치|
|실습 처리|6MB POST 요청을 이용해 용량 제한 미적용 상태를 재현한 뒤 `LimitRequestBody 5000000` 적용|
|조치 전 판단|5MB 초과 요청이 200 OK로 처리되면 취약|
|조치 후 판단|5MB 초과 요청이 413으로 차단되면 양호|
|증거 상태|PDF 기준 수동 확인 필요, 취약 재현 및 조치 후 접근 증거 필요|

PDF 기준 WEB-08은 파일 업로드 및 다운로드 용량 제한 항목이다. 그러나 현재 `AWS WEB 약점 진단 결과.md`의 WEB-08은 `.htaccess` 오버라이드 제한으로 기록되어 있어 PDF 항목과 일치하지 않는다.

따라서 이 항목은 자동 진단 결과를 그대로 사용하지 않고, Apache와 PHP 설정을 직접 확인해야 한다.

Apache 환경에서는 `LimitRequestBody 5000000`을 설정하여 약 5MB를 초과하는 요청 본문을 차단할 수 있다. 조치 전 6MB POST 요청이 정상 처리되면 취약 상태로 볼 수 있고, 조치 후 같은 요청이 `413 Request Entity Too Large` 또는 `413 Payload Too Large`로 차단되면 WEB-08은 조치 후 **양호**로 판단한다.