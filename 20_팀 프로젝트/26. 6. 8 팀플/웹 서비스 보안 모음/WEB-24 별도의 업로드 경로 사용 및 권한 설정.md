---

type: lab  
topic: web-service-security  
source: 주요정보통신기반시설 기술적 취약점 분석·평가 방법 상세가이드  
source_pages:

- 343
    
- 344
    
- 345
    
- 346  
status: draft  
created: 2026-06-18  
tags:
    
- 🏷️과목/웹서비스보안
    
- 🏷️주제/WEB-24
    
- 🏷️주제/Upload-Path
    
- 🏷️주제/File-Permission
    
- 🏷️주제/Apache
    
- 🏷️상태/draft
    

---
# WEB-24 별도의 업로드 경로 사용 및 권한 설정

## 1. PDF 기준

PDF p.343-346의 WEB-24는 웹 서비스에서 사용하는 **파일 업로드 경로가 웹 서버 루트 디렉터리와 분리되어 있는지**, 그리고 해당 업로드 경로의 권한이 적절하게 제한되어 있는지 점검하는 항목이다.

점검 목적은 다음과 같다.

```text
웹 서버 루트 디렉터리 내부에 업로드 파일이 저장되면,
공격자가 악성 PHP, JSP, HTML, 스크립트 파일 등을 업로드한 뒤
웹 요청으로 직접 실행하거나 열람할 수 있다.
```

PDF의 판단 기준은 다음과 같다.

|판단|기준|
|---|---|
|양호|별도의 업로드 경로를 사용하고 일반 사용자의 접근 권한이 부여되지 않은 경우|
|취약|별도의 업로드 경로를 사용하지 않거나, 일반 사용자의 접근 권한이 부여된 경우|

Apache 기준으로 보면 위험한 상태는 다음과 같다.

```text
/var/www/care/uploads
/var/www/html/uploads
```

이처럼 DocumentRoot 내부에 업로드 디렉터리가 있고, 웹에서 직접 접근 가능하면 업로드 파일이 그대로 외부에 노출될 수 있다.

권장 구조는 다음과 같다.

```text
웹 루트:
  /var/www/care

업로드 저장 경로:
  /srv/care-uploads
  /var/lib/care/uploads
  /opt/care/uploads
```

즉 업로드 파일은 웹 루트 밖에 저장하고, 웹 서버가 직접 URL로 제공하지 않도록 제한한다.

Apache 설정 예시는 다음과 같다.

```apache
<Directory "/srv/care-uploads">
    Require all denied
</Directory>
```

권한 예시는 다음과 같다.

```bash
chmod 750 /srv/care-uploads
chown www-data:www-data /srv/care-uploads
```

## 2. 최초 진단 결과

`AWS WEB 약점 진단 결과.md`의 WEB-24 항목은 PDF의 WEB-24와 내용이 일치하지 않는다.

진단 파일의 WEB-24는 다음 항목으로 되어 있다.

```text
WEB-24 | X-Frame-Options 헤더 | Header always set X-Frame-Options DENY 설정 여부
```

하지만 PDF p.343-346의 WEB-24는 **X-Frame-Options가 아니라 별도의 업로드 경로 사용 및 권한 설정** 항목이다.

따라서 이 노트에서는 다음처럼 처리한다.

|구분|내용|
|---|---|
|PDF 기준 WEB-24|별도의 업로드 경로 사용 및 권한 설정|
|진단 파일 WEB-24|X-Frame-Options 헤더|
|일치 여부|불일치|
|자동 진단 결과 활용|PDF WEB-24의 직접 근거로 사용 불가|
|이 노트의 판단 방식|업로드 경로와 권한을 수동 확인|

PDF 기준 WEB-24는 다음 항목을 직접 확인해야 한다.

```text
1. CARE 애플리케이션의 업로드 기능 존재 여부
2. 업로드 파일 저장 경로
3. 저장 경로가 DocumentRoot 내부인지 여부
4. 업로드 경로의 소유자와 권한
5. 웹 요청으로 업로드 파일에 직접 접근 가능한지 여부
6. 업로드 경로에서 PHP 등 스크립트 실행이 가능한지 여부
```

## 3. 현재 서버 상태 해석

WEB-24는 단순히 “업로드 디렉터리가 있는가”만 보는 항목이 아니다. 핵심은 **업로드 파일이 웹 루트 내부에서 직접 실행되거나 열람될 수 있는 구조인지**다.

취약한 구조는 다음과 같다.

```text
/var/www/care/uploads/shell.php
/var/www/care/upload/profile.php
/var/www/care/files/test.html
```

이런 경로에 파일이 업로드되고, 다음 URL로 접근할 수 있다면 위험하다.

```text
http://172.168.10.10/uploads/shell.php
http://172.168.10.10/upload/profile.php
http://172.168.10.10/files/test.html
```

특히 `.php` 파일이 업로드되고 실행되면 웹쉘 실행으로 이어질 수 있다.

양호한 구조는 다음과 같다.

```text
업로드 저장:
  /srv/care-uploads

웹 루트:
  /var/www/care

웹 요청:
  http://172.168.10.10/uploads/file.txt → 404 또는 403
```

이 경우 애플리케이션이 파일을 직접 읽어 다운로드 응답을 만들 수는 있지만, 웹 서버가 업로드 디렉터리를 정적 경로로 직접 노출하지 않는다.

Apache/PHP 환경에서는 다음 설정도 함께 확인해야 한다.

|확인 항목|의미|
|---|---|
|`upload_tmp_dir`|PHP 임시 업로드 경로|
|애플리케이션 업로드 저장 경로|실제 업로드 파일 저장 위치|
|`Alias /uploads`|외부 업로드 경로를 다시 웹 경로로 노출하는지|
|`<Directory>` 권한|업로드 디렉터리에 `Require all granted`가 있는지|
|`Options`|`Indexes`, `FollowSymLinks`, `ExecCGI` 여부|
|PHP 실행 여부|업로드 파일이 `.php`로 실행 가능한지|

WEB-24는 다음 항목들과 연결된다.

|연결 항목|연결 이유|
|---|---|
|WEB-07 불필요한 파일 제거|업로드된 테스트 파일, 백업 파일, 임시 파일 관리|
|WEB-14 파일 접근 통제|업로드 경로의 파일 권한과 소유자 관리|
|WEB-17 가상 디렉터리 삭제|외부 업로드 경로를 Alias로 노출하면 다시 취약해질 수 있음|
|WEB-23 HTTP 메서드 제한 진단 항목|PUT 같은 메서드로 파일 업로드가 가능하면 위험 증가|
|웹 애플리케이션 파일 업로드 취약점|확장자 검증, MIME 검증, 저장 경로 분리와 직접 연결|

## 4. 실습 전 확인

실습 전에는 DocumentRoot, 업로드 후보 경로, PHP 업로드 설정을 확인한다.

### 4-1. 실습용 변수 지정

```bash
SERVER=http://172.168.10.10
APP_ROOT=/var/www/care

BAD_UPLOAD_DIR="$APP_ROOT/web24-uploads"
SAFE_UPLOAD_DIR=/srv/care-uploads-web24
TEST_CONF=/etc/apache2/conf-available/web-24-upload-path.conf
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

### 4-4. 웹 루트 내부 업로드 후보 경로 확인

```bash
find "$APP_ROOT" -maxdepth 3 -type d \
  \( -iname '*upload*' -o -iname '*file*' -o -iname '*attach*' -o -iname '*download*' \) \
  -print 2>/dev/null
```

출력 예시는 다음과 같다.

```text
/var/www/care/uploads
/var/www/care/files
/var/www/care/attach
```

이런 경로가 실제 업로드 저장 경로라면 웹에서 직접 접근 가능한지 확인해야 한다.

### 4-5. 업로드 관련 PHP 코드 확인

```bash
grep -RniE 'move_uploaded_file|_FILES|upload|uploads|attach|file_put_contents' "$APP_ROOT" 2>/dev/null
```

업로드 처리 코드에서 저장 경로를 확인한다.

예를 들어 다음과 같은 코드가 있으면 위험할 수 있다.

```php
move_uploaded_file($_FILES['file']['tmp_name'], "/var/www/care/uploads/" . $_FILES['file']['name']);
```

웹 루트 내부에 저장하기 때문이다.

### 4-6. PHP 업로드 설정 확인

```bash
php -i | grep -E 'file_uploads|upload_tmp_dir|upload_max_filesize|post_max_size'
```

확인할 항목은 다음이다.

|항목|의미|
|---|---|
|`file_uploads`|PHP 파일 업로드 기능 사용 여부|
|`upload_tmp_dir`|임시 업로드 파일 저장 경로|
|`upload_max_filesize`|업로드 최대 크기|
|`post_max_size`|POST 요청 최대 크기|

### 4-7. Alias로 업로드 경로가 노출되는지 확인

```bash
grep -RniE 'Alias .*upload|Alias .*uploads|<Directory .*upload|<Directory .*uploads' \
/etc/apache2/apache2.conf \
/etc/apache2/sites-enabled/ \
/etc/apache2/sites-available/ \
/etc/apache2/conf-enabled/ \
/etc/apache2/conf-available/ 2>/dev/null | grep -v '^\s*#'
```

업로드 경로가 Alias로 노출되어 있으면 WEB-17과 함께 검토한다.

## 5. 취약 재현

이 항목은 PDF 기준 수동 확인 항목이다.  
실습에서는 웹 루트 내부에 업로드 디렉터리를 만들고, 해당 파일이 웹에서 직접 접근되는 취약 상태를 재현한다.

> 주의: 이 절차는 격리된 실습 서버에서만 수행한다.  
> 실제 악성 웹쉘을 만들지 않는다.  
> 실행 가능한 PHP 파일 대신 일반 텍스트 파일과 실행 방지 확인용 PHP 파일만 사용한다.  
> 증거 확보 후 즉시 제거한다.

취약 재현의 핵심은 다음이다.

```text
DocumentRoot 내부에 업로드 디렉터리가 있고,
외부 URL로 업로드 파일에 직접 접근 가능한 상태를 만든다.
```

### 5-1. 취약 업로드 디렉터리 생성

```bash
sudo mkdir -p "$BAD_UPLOAD_DIR"
```

```bash
sudo chown -R www-data:www-data "$BAD_UPLOAD_DIR"
```

```bash
sudo chmod 755 "$BAD_UPLOAD_DIR"
```

### 5-2. 테스트 파일 생성

```bash
echo "WEB-24 upload path exposed" | sudo tee "$BAD_UPLOAD_DIR/exposed.txt"
```

### 5-3. 웹 접근 확인

```bash
curl -i "$SERVER/web24-uploads/exposed.txt"
```

취약 상태 기대 결과는 다음이다.

```text
HTTP/1.1 200 OK

WEB-24 upload path exposed
```

이 결과는 웹 루트 내부 업로드 경로의 파일이 외부에서 직접 접근 가능하다는 뜻이다.

### 5-4. 실행 가능한 파일 위험 확인

실제 악성 코드를 만들지 않고, PHP 실행 가능성을 확인하기 위한 안전한 테스트 파일을 만든다.

```bash
sudo tee "$BAD_UPLOAD_DIR/test.php" > /dev/null <<'EOF'
<?php echo "WEB-24 PHP execution test"; ?>
EOF
```

요청한다.

```bash
curl -i "$SERVER/web24-uploads/test.php"
```

위험한 상태에서는 다음처럼 PHP가 실행된다.

```text
HTTP/1.1 200 OK

WEB-24 PHP execution test
```

이 결과가 나오면 업로드 경로에서 PHP 실행이 가능한 상태다.  
웹쉘 업로드 공격으로 이어질 수 있으므로 취약성이 매우 크다.

### 5-5. 디렉터리 권한 확인

```bash
stat -c '%A %U:%G %n' "$BAD_UPLOAD_DIR"
```

취약 재현 상태 예시는 다음이다.

```text
drwxr-xr-x www-data:www-data /var/www/care/web24-uploads
```

웹 루트 내부에 있고 외부에서 접근 가능하므로, 권한만 755라고 해서 안전한 것은 아니다.

## 6. 조치 방법

조치 핵심은 업로드 경로를 웹 루트 밖으로 분리하고, 웹 요청으로 직접 접근할 수 없도록 제한하는 것이다.

### 6-1. 웹 루트 외부 업로드 디렉터리 생성

```bash
sudo mkdir -p "$SAFE_UPLOAD_DIR"
```

### 6-2. 소유자와 권한 설정

Apache/PHP가 업로드 파일을 저장해야 하므로, 실습에서는 `www-data:www-data` 소유로 설정한다.

```bash
sudo chown -R www-data:www-data "$SAFE_UPLOAD_DIR"
```

```bash
sudo chmod 750 "$SAFE_UPLOAD_DIR"
```

확인한다.

```bash
stat -c '%A %U:%G %n' "$SAFE_UPLOAD_DIR"
```

기대 결과:

```text
drwxr-x--- www-data:www-data /srv/care-uploads-web24
```

### 6-3. 웹 루트 내부 취약 업로드 디렉터리 제거

```bash
sudo rm -rf "$BAD_UPLOAD_DIR"
```

### 6-4. 외부 업로드 경로 접근 차단 설정 생성

웹 루트 밖의 경로는 기본적으로 URL로 접근되지 않는다.  
그래도 Apache 설정에서 해당 경로가 노출되지 않도록 명시적으로 차단한다.

```bash
sudo tee "$TEST_CONF" > /dev/null <<EOF
<Directory "$SAFE_UPLOAD_DIR">
    Options None
    AllowOverride None
    Require all denied
</Directory>
EOF
```

핵심 설정은 다음이다.

```apache
<Directory "/srv/care-uploads-web24">
    Options None
    AllowOverride None
    Require all denied
</Directory>
```

### 6-5. 설정 활성화

```bash
sudo a2enconf web-24-upload-path
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

### 6-8. 애플리케이션 업로드 저장 경로 변경

실제 CARE 업로드 기능이 있다면 PHP 코드나 설정 파일에서 업로드 저장 경로를 웹 루트 외부로 변경해야 한다.

취약한 예시는 다음이다.

```php
$upload_dir = "/var/www/care/uploads";
```

조치 예시는 다음이다.

```php
$upload_dir = "/srv/care-uploads-web24";
```

파일 다운로드가 필요하면 업로드 디렉터리를 직접 웹에 노출하지 말고, 다운로드 처리 스크립트를 통해 권한 확인 후 파일 내용을 전송한다.

예시는 다음 흐름이다.

```text
사용자 요청:
  /download.php?id=123

애플리케이션:
  1. 로그인 여부 확인
  2. 파일 소유자 또는 접근 권한 확인
  3. /srv/care-uploads-web24 내부 파일을 readfile()로 전송
```

## 7. 조치 후 확인

### 7-1. 웹 루트 내부 취약 업로드 경로 제거 확인

```bash
ls -ld "$BAD_UPLOAD_DIR" 2>/dev/null
```

기대 결과:

```text
출력 없음
```

### 7-2. 웹 루트 외부 업로드 경로 권한 확인

```bash
stat -c '%A %U:%G %n' "$SAFE_UPLOAD_DIR"
```

기대 결과:

```text
drwxr-x--- www-data:www-data /srv/care-uploads-web24
```

### 7-3. 일반 사용자 접근 제한 확인

```bash
sudo -u nobody ls "$SAFE_UPLOAD_DIR"
```

조치 후 기대 결과는 다음이다.

```text
Permission denied
```

### 7-4. Apache 설정 확인

```bash
grep -RniE 'web24|care-uploads|Require all denied|Alias .*upload|Alias .*uploads' \
/etc/apache2/apache2.conf \
/etc/apache2/sites-enabled/ \
/etc/apache2/sites-available/ \
/etc/apache2/conf-enabled/ \
/etc/apache2/conf-available/ 2>/dev/null | grep -v '^\s*#'
```

기대 결과는 다음과 유사하다.

```text
/etc/apache2/conf-enabled/web-24-upload-path.conf:<Directory "/srv/care-uploads-web24">
/etc/apache2/conf-enabled/web-24-upload-path.conf:    Require all denied
```

`Alias /uploads`처럼 외부 업로드 경로를 웹 경로로 노출하는 설정이 있으면 별도 검토한다.

### 7-5. 웹 URL 직접 접근 차단 확인

```bash
curl -i "$SERVER/web24-uploads/exposed.txt"
```

조치 후 기대 결과는 다음이다.

```text
HTTP/1.1 404 Not Found
```

또는:

```text
HTTP/1.1 403 Forbidden
```

중요한 것은 다음 문자열이 더 이상 외부 응답에 나오지 않는 것이다.

```text
WEB-24 upload path exposed
```

### 7-6. PHP 실행 차단 확인

```bash
curl -i "$SERVER/web24-uploads/test.php"
```

조치 후 기대 결과는 다음이다.

```text
HTTP/1.1 404 Not Found
```

또는:

```text
HTTP/1.1 403 Forbidden
```

다음처럼 PHP 코드가 실행되면 안 된다.

```text
WEB-24 PHP execution test
```

### 7-7. Apache 서비스 상태 확인

```bash
systemctl status apache2 --no-pager
```

기대 결과:

```text
Active: active (running)
```

### 7-8. CARE 서비스 정상 응답 확인

```bash
curl -i "$SERVER/"
```

정상이라면 현재 CARE 애플리케이션 상태에 맞는 응답이 나와야 한다.

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

BAD_UPLOAD_DIR="$APP_ROOT/web24-uploads"
SAFE_UPLOAD_DIR=/srv/care-uploads-web24
TEST_CONF=/etc/apache2/conf-available/web-24-upload-path.conf
```

```bash
apache2ctl -S
```

```bash
grep -R "DocumentRoot" /etc/apache2/sites-enabled/ /etc/apache2/sites-available/ 2>/dev/null
```

```bash
find "$APP_ROOT" -maxdepth 3 -type d \
  \( -iname '*upload*' -o -iname '*file*' -o -iname '*attach*' -o -iname '*download*' \) \
  -print 2>/dev/null
```

```bash
grep -RniE 'move_uploaded_file|_FILES|upload|uploads|attach|file_put_contents' "$APP_ROOT" 2>/dev/null
```

```bash
php -i | grep -E 'file_uploads|upload_tmp_dir|upload_max_filesize|post_max_size'
```

### 8-2. 취약 재현

```bash
sudo mkdir -p "$BAD_UPLOAD_DIR"
sudo chown -R www-data:www-data "$BAD_UPLOAD_DIR"
sudo chmod 755 "$BAD_UPLOAD_DIR"
```

```bash
echo "WEB-24 upload path exposed" | sudo tee "$BAD_UPLOAD_DIR/exposed.txt"
```

```bash
curl -i "$SERVER/web24-uploads/exposed.txt"
```

취약 상태 기대 결과:

```text
HTTP/1.1 200 OK

WEB-24 upload path exposed
```

```bash
sudo tee "$BAD_UPLOAD_DIR/test.php" > /dev/null <<'EOF'
<?php echo "WEB-24 PHP execution test"; ?>
EOF
```

```bash
curl -i "$SERVER/web24-uploads/test.php"
```

위험한 상태 기대 결과:

```text
HTTP/1.1 200 OK

WEB-24 PHP execution test
```

### 8-3. 조치 적용

```bash
sudo mkdir -p "$SAFE_UPLOAD_DIR"
sudo chown -R www-data:www-data "$SAFE_UPLOAD_DIR"
sudo chmod 750 "$SAFE_UPLOAD_DIR"
```

```bash
stat -c '%A %U:%G %n' "$SAFE_UPLOAD_DIR"
```

기대 결과:

```text
drwxr-x--- www-data:www-data /srv/care-uploads-web24
```

```bash
sudo rm -rf "$BAD_UPLOAD_DIR"
```

```bash
sudo tee "$TEST_CONF" > /dev/null <<EOF
<Directory "$SAFE_UPLOAD_DIR">
    Options None
    AllowOverride None
    Require all denied
</Directory>
EOF
```

```bash
sudo a2enconf web-24-upload-path
```

```bash
sudo apachectl configtest
```

```bash
sudo systemctl restart apache2
```

### 8-4. 조치 후 확인

```bash
ls -ld "$BAD_UPLOAD_DIR" 2>/dev/null
```

기대 결과:

```text
출력 없음
```

```bash
stat -c '%A %U:%G %n' "$SAFE_UPLOAD_DIR"
```

기대 결과:

```text
drwxr-x--- www-data:www-data /srv/care-uploads-web24
```

```bash
sudo -u nobody ls "$SAFE_UPLOAD_DIR"
```

기대 결과:

```text
Permission denied
```

```bash
curl -i "$SERVER/web24-uploads/exposed.txt"
```

기대 결과:

```text
HTTP/1.1 404 Not Found
```

또는:

```text
HTTP/1.1 403 Forbidden
```

```bash
curl -i "$SERVER/web24-uploads/test.php"
```

기대 결과:

```text
HTTP/1.1 404 Not Found
```

또는:

```text
HTTP/1.1 403 Forbidden
```

```bash
systemctl status apache2 --no-pager
```

기대 결과:

```text
Active: active (running)
```

### 8-5. 실습용 파일 정리

WEB-24 조치를 실제로 유지할 목적이면 `/srv/care-uploads-web24`와 `web-24-upload-path.conf`는 제거하지 않는다.

실습용으로만 적용했다면 증거 확보 후 제거한다.

```bash
sudo a2disconf web-24-upload-path
```

```bash
sudo rm -f "$TEST_CONF"
```

```bash
sudo rm -rf "$SAFE_UPLOAD_DIR"
```

```bash
sudo apachectl configtest
```

```bash
sudo systemctl restart apache2
```

단, 실제 업로드 기능이 있는 서비스라면 업로드 경로 분리는 운영 조치로 유지해야 한다.

## 9. 증거 정리

### 9-1. 진단 파일 불일치 증거

```text
진단 파일 WEB-24: X-Frame-Options 헤더
PDF WEB-24: 별도의 업로드 경로 사용 및 권한 설정
```

따라서 진단 파일의 WEB-24 결과는 PDF WEB-24 판단 근거로 직접 사용하지 않는다.

### 9-2. 현재 환경 확인 증거

DocumentRoot 확인:

```bash
grep -R "DocumentRoot" /etc/apache2/sites-enabled/ /etc/apache2/sites-available/ 2>/dev/null
```

업로드 후보 경로 확인:

```bash
find "$APP_ROOT" -maxdepth 3 -type d \
  \( -iname '*upload*' -o -iname '*file*' -o -iname '*attach*' -o -iname '*download*' \) \
  -print 2>/dev/null
```

업로드 코드 확인:

```bash
grep -RniE 'move_uploaded_file|_FILES|upload|uploads|attach|file_put_contents' "$APP_ROOT" 2>/dev/null
```

### 9-3. 취약 재현 증거

웹 루트 내부 업로드 경로:

```text
/var/www/care/web24-uploads
```

외부 접근 확인:

```bash
curl -i "$SERVER/web24-uploads/exposed.txt"
```

취약 상태 기대 결과:

```text
HTTP/1.1 200 OK

WEB-24 upload path exposed
```

PHP 실행 가능성 확인:

```bash
curl -i "$SERVER/web24-uploads/test.php"
```

위험한 상태 기대 결과:

```text
HTTP/1.1 200 OK

WEB-24 PHP execution test
```

### 9-4. 조치 후 증거

웹 루트 외부 업로드 경로:

```text
/srv/care-uploads-web24
```

권한 확인:

```bash
stat -c '%A %U:%G %n' "$SAFE_UPLOAD_DIR"
```

조치 후 기대 결과:

```text
drwxr-x--- www-data:www-data /srv/care-uploads-web24
```

일반 사용자 접근 제한 확인:

```bash
sudo -u nobody ls "$SAFE_UPLOAD_DIR"
```

조치 후 기대 결과:

```text
Permission denied
```

웹 직접 접근 차단 확인:

```bash
curl -i "$SERVER/web24-uploads/exposed.txt"
```

조치 후 기대 결과:

```text
HTTP/1.1 404 Not Found
```

또는:

```text
HTTP/1.1 403 Forbidden
```

## 10. 판단

|항목|판단|
|---|---|
|자동 진단|수동 항목으로 보되, 진단 파일 내용은 PDF WEB-24와 불일치|
|진단 파일 내용|WEB-24가 X-Frame-Options 헤더로 표시됨|
|PDF 기준 항목|별도의 업로드 경로 사용 및 권한 설정|
|취약 조건|웹 루트 내부 업로드 경로 사용, 직접 접근 가능, 일반 사용자 접근 권한 부여|
|양호 조건|웹 루트 밖 별도 업로드 경로 사용, 권한 750 수준, 직접 URL 접근 차단|
|주요 확인 대상|업로드 코드, 업로드 저장 경로, 디렉터리 권한, 웹 접근 가능 여부|
|조치 방향|업로드 경로를 `/srv/care-uploads-web24` 같은 웹 루트 외부 경로로 분리하고 접근 제한|

현재 WEB-24는 진단 파일과 PDF 항목명이 일치하지 않는다. 진단 파일의 WEB-24는 X-Frame-Options 헤더를 말하지만, PDF p.343-346의 WEB-24는 별도의 업로드 경로 사용 및 권한 설정 항목이다.

PDF 기준으로는 CARE 애플리케이션의 업로드 기능과 저장 경로를 직접 확인해야 한다. 업로드 파일이 `/var/www/care/uploads`처럼 웹 루트 내부에 저장되고 외부 URL로 직접 접근 가능하면 WEB-24는 **취약**이다.

조치 후 업로드 경로가 웹 루트 밖의 `/srv/care-uploads-web24` 같은 별도 경로로 분리되고, 권한이 `750`, 소유자가 `www-data:www-data`로 제한되며, 외부 URL로 직접 접근할 수 없으면 WEB-24는 **양호**로 판단한다.