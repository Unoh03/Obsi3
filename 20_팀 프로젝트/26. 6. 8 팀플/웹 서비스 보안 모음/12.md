---

type: lab  
topic: web-service-security  
source: 주요정보통신기반시설 기술적 취약점 분석·평가 방법 상세가이드  
source_pages:

- 305
    
- 306
    
- 307  
status: draft  
created: 2026-06-18  
tags:
    
- 🏷️과목/웹서비스보안
    
- 🏷️주제/WEB-12
    
- 🏷️주제/Symbolic-Link
    
- 🏷️주제/Apache
    
- 🏷️상태/draft
    

---

# WEB-12 웹 서비스 링크 사용 금지

## 1. PDF 기준

PDF p.305-307의 WEB-12는 웹 서비스 경로에서 **심볼릭 링크, alias, 바로가기 등의 링크 사용이 제한되어 있는지** 점검하는 항목이다.

심볼릭 링크는 실제 파일이나 디렉터리의 위치를 직접 포함하지 않고, 다른 위치를 가리키는 링크 파일이다. 사용자가 심볼릭 링크 파일을 요청하면 시스템은 링크가 가리키는 실제 대상 파일을 따라가서 내용을 반환할 수 있다.

예를 들어 웹 루트 안에 다음과 같은 심볼릭 링크가 있다고 가정한다.

```text
/var/www/care/link-test/secret-link.txt -> /tmp/web12-secret/secret.txt
```

Apache가 심볼릭 링크 추적을 허용하고 있으면 사용자는 웹 루트 내부의 `secret-link.txt`를 요청하는 것만으로 웹 루트 외부의 `/tmp/web12-secret/secret.txt`에 접근할 수 있다.

```text
http://서버주소/link-test/secret-link.txt
```

이런 설정이 무분별하게 허용되면 웹 서비스 경로 검증을 우회하여 원래 노출하면 안 되는 파일이나 디렉터리에 접근할 수 있다.

PDF의 판단 기준은 다음과 같다.

|판단|기준|
|---|---|
|양호|심볼릭 링크, aliases, 바로가기 등의 링크 사용을 허용하지 않는 경우|
|취약|심볼릭 링크, aliases, 바로가기 등의 링크 사용을 허용하는 경우|

PDF의 Apache 조치 방향은 `Options` 지시자에서 `FollowSymLinks` 옵션을 제거하는 것이다.

취약 설정 예시는 다음과 같다.

```apache
Options Indexes FollowSymLinks
```

조치 방향은 다음과 같다.

```apache
Options -FollowSymLinks
```

단, Apache에서는 `Options` 지시자에 `+` 또는 `-`를 섞어 쓸 때 문법 오류가 날 수 있으므로, 실제 설정에서는 문법 검사를 반드시 수행해야 한다.

## 2. 최초 진단 결과

`AWS WEB 약점 진단 결과.md` 기준 최초 진단 결과는 **취약**이다.

|항목|내용|
|---|---|
|진단 결과|취약|
|진단 근거|Apache 설정에 `Options Indexes FollowSymLinks` 존재|
|관련 설정|`/etc/apache2/apache2.conf` 또는 Apache 사이트 설정의 `Options` 지시자|
|영향|웹 루트 내부 심볼릭 링크를 통해 웹 루트 외부 파일에 접근 가능|
|조치 방향|`FollowSymLinks` 제거 또는 `-FollowSymLinks` 적용|

최초 진단에서 확인된 취약 설정은 다음과 같은 형태다.

```apache
Options Indexes FollowSymLinks
```

`FollowSymLinks`는 Apache가 웹 경로 안의 심볼릭 링크를 따라가도록 허용하는 옵션이다.

따라서 현재 최초 진단 기준으로는 웹 서비스 링크 사용이 허용될 수 있으므로 WEB-12는 취약으로 판단한다.

## 3. 현재 서버 상태 해석

WEB-12는 웹 서비스 경로 안에서 **링크가 가리키는 실제 대상 경로까지 접근할 수 있는지**를 확인하는 항목이다.

Apache에서 확인해야 할 핵심 설정은 다음과 같다.

|확인 대상|의미|
|---|---|
|`Options FollowSymLinks`|심볼릭 링크 추적 허용|
|`Options +FollowSymLinks`|상위 설정에 심볼릭 링크 추적 허용 추가|
|`Options -FollowSymLinks`|상위 설정에서 심볼릭 링크 추적 제거|
|`Options SymLinksIfOwnerMatch`|링크와 대상 파일의 소유자가 같을 때만 심볼릭 링크 추적 허용|
|`Alias`|URL 경로를 다른 실제 파일 시스템 경로에 매핑|
|`ScriptAlias`|URL 경로를 CGI 실행 경로에 매핑|

WEB-12에서 가장 직접적인 Apache 설정은 `FollowSymLinks`다.

`FollowSymLinks`가 허용되면 다음과 같은 흐름이 가능하다.

```text
사용자 요청:
GET /web12-link/secret-link.txt

웹 루트 내부:
secret-link.txt -> /tmp/web12-secret/secret.txt

Apache:
심볼릭 링크를 따라감

결과:
웹 루트 외부 파일 내용 반환
```

이 항목은 WEB-04, WEB-11, WEB-14와 연결된다.

|연결 항목|연결 이유|
|---|---|
|WEB-04 디렉터리 리스팅|디렉터리 목록이 보이면 심볼릭 링크 파일명도 노출될 수 있음|
|WEB-11 웹 서비스 경로 설정|DocumentRoot를 분리해도 심볼릭 링크가 외부 경로를 다시 연결할 수 있음|
|WEB-14 파일 접근 통제|링크 대상 파일의 권한과 접근 정책을 함께 확인해야 함|
|WEB-17 가상 디렉터리 삭제|Alias나 가상 디렉터리도 웹 경로 외부 접근을 열 수 있음|

즉 WEB-12의 핵심은 “웹 루트 안에 링크 파일이 있더라도, 그 링크가 웹 루트 외부 경로를 노출하지 못하게 하는 것”이다.

## 4. 실습 전 확인

실습을 시작하기 전에 현재 Apache 설정과 DocumentRoot를 확인한다.

### 4-1. Apache 가상호스트 확인

```bash
apache2ctl -S
```

### 4-2. DocumentRoot 확인

```bash
grep -R "DocumentRoot" /etc/apache2/sites-enabled/ /etc/apache2/sites-available/ 2>/dev/null
```

이 노트는 CARE 서버의 DocumentRoot가 `/var/www/care`라고 가정한다.

실습용 변수를 지정한다.

```bash
APP_ROOT=/var/www/care
SERVER=http://172.168.10.10
TEST_DIR="$APP_ROOT/web12-link"
SECRET_DIR=/tmp/web12-secret
TEST_CONF="/etc/apache2/conf-available/web-12-link-test.conf"
```

현재 서버의 DocumentRoot가 다르면 `APP_ROOT` 값을 실제 경로로 바꾼다.

### 4-3. 현재 FollowSymLinks 설정 확인

```bash
grep -R "FollowSymLinks\|SymLinksIfOwnerMatch\|Alias" /etc/apache2/apache2.conf /etc/apache2/sites-enabled/ /etc/apache2/sites-available/ /etc/apache2/conf-enabled/ /etc/apache2/conf-available/ 2>/dev/null | grep -v '^\s*#'
```

취약 상태에서는 다음과 같은 설정이 확인될 수 있다.

```apache
Options Indexes FollowSymLinks
```

또는:

```apache
Options +FollowSymLinks
```

### 4-4. Apache 설정 문법 검사

실습 전에 현재 설정이 정상인지 확인한다.

```bash
sudo apachectl configtest
```

정상이라면 다음 결과가 나와야 한다.

```text
Syntax OK
```

## 5. 취약 재현

이 항목은 최초 진단에서 이미 취약으로 확인된 항목이다.

다만 실제 웹 요청으로 취약 상태를 확인하기 위해, 실습용 디렉터리와 심볼릭 링크를 만든 뒤 Apache가 링크를 따라가는지 확인한다.

> 주의: 이 절차는 격리된 실습 서버에서만 수행한다.  
> 실제 민감 파일을 링크 대상으로 사용하지 않는다.  
> 실습용 파일만 만들고, 증거 확보 후 즉시 제거한다.

취약 재현의 핵심은 다음이다.

```text
웹 루트 안에 웹 루트 외부 파일을 가리키는 심볼릭 링크를 만들고,
Apache가 그 링크를 따라가 파일 내용을 반환하는지 확인한다.
```

### 5-1. 실습용 디렉터리 생성

```bash
sudo mkdir -p "$TEST_DIR"
sudo mkdir -p "$SECRET_DIR"
```

### 5-2. 웹 루트 외부 테스트 파일 생성

```bash
echo "WEB-12 symbolic link secret" | sudo tee "$SECRET_DIR/secret.txt"
```

파일을 확인한다.

```bash
ls -l "$SECRET_DIR/secret.txt"
```

### 5-3. 웹 루트 내부에 심볼릭 링크 생성

```bash
sudo ln -sf "$SECRET_DIR/secret.txt" "$TEST_DIR/secret-link.txt"
```

생성된 링크를 확인한다.

```bash
ls -l "$TEST_DIR/secret-link.txt"
```

기대 결과는 다음과 유사하다.

```text
/var/www/care/web12-link/secret-link.txt -> /tmp/web12-secret/secret.txt
```

### 5-4. 실습용 취약 설정 생성

현재 전역 설정에 이미 `FollowSymLinks`가 있더라도, 실습 경로에서 재현을 명확히 하기 위해 테스트 설정 파일을 따로 만든다.

```bash
sudo tee "$TEST_CONF" > /dev/null <<EOF
<Directory $TEST_DIR>
    Options +FollowSymLinks
    Require all granted
</Directory>
EOF
```

이 설정은 `$TEST_DIR` 안에서 심볼릭 링크 추적을 허용한다.

### 5-5. 실습용 설정 활성화

```bash
sudo a2enconf web-12-link-test
```

### 5-6. Apache 설정 문법 검사

```bash
sudo apachectl configtest
```

정상이라면 다음 결과가 나와야 한다.

```text
Syntax OK
```

### 5-7. Apache restart

```bash
sudo systemctl restart apache2
```

### 5-8. 심볼릭 링크 접근 확인

```bash
curl -i "$SERVER/web12-link/secret-link.txt"
```

취약 재현 상태에서 기대 결과는 다음과 같다.

```text
HTTP/1.1 200 OK

WEB-12 symbolic link secret
```

이 결과는 웹 루트 내부의 심볼릭 링크를 통해 웹 루트 외부 파일이 노출되었음을 의미한다.

따라서 PDF 기준으로는 취약 상태다.

## 6. 조치 방법

조치 핵심은 웹 서비스 경로에서 심볼릭 링크 추적을 허용하지 않는 것이다.

실습에서는 `$TEST_DIR`에 대해 `FollowSymLinks`를 비활성화한다.

### 6-1. 실습용 설정을 보안 설정으로 변경

```bash
sudo tee "$TEST_CONF" > /dev/null <<EOF
<Directory $TEST_DIR>
    Options -FollowSymLinks
    Require all granted
</Directory>
EOF
```

이 설정은 `$TEST_DIR`에서 상위 설정으로부터 상속된 `FollowSymLinks`를 제거한다.

운영 설정에서는 전역 또는 웹 서비스 경로에 남아 있는 다음 설정을 제거해야 한다.

```apache
Options FollowSymLinks
```

또는:

```apache
Options +FollowSymLinks
```

필요하면 다음처럼 명시적으로 제한한다.

```apache
Options -FollowSymLinks
```

### 6-2. Apache 설정 문법 검사

```bash
sudo apachectl configtest
```

정상이라면 다음 결과가 나와야 한다.

```text
Syntax OK
```

### 6-3. Apache restart

```bash
sudo systemctl restart apache2
```

### 6-4. 운영 설정 전체 확인

```bash
grep -R "FollowSymLinks\|SymLinksIfOwnerMatch\|Alias" /etc/apache2/apache2.conf /etc/apache2/sites-enabled/ /etc/apache2/sites-available/ /etc/apache2/conf-enabled/ /etc/apache2/conf-available/ 2>/dev/null | grep -v '^\s*#'
```

조치 후에는 불필요한 `FollowSymLinks` 설정이 남아 있지 않아야 한다.

`SymLinksIfOwnerMatch`는 `FollowSymLinks`보다 제한적이지만, PDF 기준 WEB-12가 “링크 사용 금지”를 요구하므로 기본 판단에서는 링크 허용 설정으로 별도 검토한다.

### 6-5. Alias 설정 확인

심볼릭 링크 외에도 Apache의 `Alias` 설정은 URL 경로를 다른 실제 경로로 연결한다. 불필요한 Alias가 있으면 WEB-12 또는 WEB-17과 연결해서 제거한다.

```bash
grep -R "^[[:space:]]*Alias\|^[[:space:]]*ScriptAlias" /etc/apache2/apache2.conf /etc/apache2/sites-enabled/ /etc/apache2/sites-available/ /etc/apache2/conf-enabled/ /etc/apache2/conf-available/ 2>/dev/null | grep -v '^\s*#'
```

필요한 Alias인지 확인하고, 불필요하면 제거한다.

## 7. 조치 후 확인

조치 후에는 Apache가 심볼릭 링크를 더 이상 따라가지 않는지 확인한다.

### 7-1. 심볼릭 링크 접근 차단 확인

```bash
curl -i "$SERVER/web12-link/secret-link.txt"
```

정상 조치 상태라면 다음과 유사한 응답이 나와야 한다.

```text
HTTP/1.1 403 Forbidden
```

서버 설정에 따라 다음 결과가 나올 수 있다.

```text
HTTP/1.1 404 Not Found
```

중요한 것은 다음 내용이 더 이상 출력되지 않는 것이다.

```text
WEB-12 symbolic link secret
```

### 7-2. Apache 설정 확인

```bash
grep -R "FollowSymLinks\|SymLinksIfOwnerMatch\|Alias" /etc/apache2/apache2.conf /etc/apache2/sites-enabled/ /etc/apache2/sites-available/ /etc/apache2/conf-enabled/ /etc/apache2/conf-available/ 2>/dev/null | grep -v '^\s*#'
```

실습용 설정만 남아 있다면 다음처럼 보여야 한다.

```apache
Options -FollowSymLinks
```

운영 환경에서는 불필요한 `FollowSymLinks`, `Alias`, `ScriptAlias`가 남아 있지 않은지 확인한다.

### 7-3. Apache 서비스 상태 확인

```bash
systemctl status apache2 --no-pager
```

정상 상태라면 다음과 같이 보여야 한다.

```text
Active: active (running)
```

### 7-4. CARE 서비스 정상 응답 확인

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

실습 중에는 아래 순서대로 진행한다.

### 8-1. 현재 상태 확인

```bash
APP_ROOT=/var/www/care
SERVER=http://172.168.10.10
TEST_DIR="$APP_ROOT/web12-link"
SECRET_DIR=/tmp/web12-secret
TEST_CONF="/etc/apache2/conf-available/web-12-link-test.conf"
```

```bash
apache2ctl -S
```

```bash
grep -R "DocumentRoot" /etc/apache2/sites-enabled/ /etc/apache2/sites-available/ 2>/dev/null
```

```bash
grep -R "FollowSymLinks\|SymLinksIfOwnerMatch\|Alias" /etc/apache2/apache2.conf /etc/apache2/sites-enabled/ /etc/apache2/sites-available/ /etc/apache2/conf-enabled/ /etc/apache2/conf-available/ 2>/dev/null | grep -v '^\s*#'
```

```bash
sudo apachectl configtest
```

### 8-2. 취약 재현

```bash
sudo mkdir -p "$TEST_DIR"
sudo mkdir -p "$SECRET_DIR"
```

```bash
echo "WEB-12 symbolic link secret" | sudo tee "$SECRET_DIR/secret.txt"
```

```bash
sudo ln -sf "$SECRET_DIR/secret.txt" "$TEST_DIR/secret-link.txt"
```

```bash
ls -l "$TEST_DIR/secret-link.txt"
```

```bash
sudo tee "$TEST_CONF" > /dev/null <<EOF
<Directory $TEST_DIR>
    Options +FollowSymLinks
    Require all granted
</Directory>
EOF
```

```bash
sudo a2enconf web-12-link-test
```

```bash
sudo apachectl configtest
```

```bash
sudo systemctl restart apache2
```

```bash
curl -i "$SERVER/web12-link/secret-link.txt"
```

취약 상태 기대 결과:

```text
HTTP/1.1 200 OK

WEB-12 symbolic link secret
```

### 8-3. 조치 및 적용

```bash
sudo tee "$TEST_CONF" > /dev/null <<EOF
<Directory $TEST_DIR>
    Options -FollowSymLinks
    Require all granted
</Directory>
EOF
```

```bash
sudo apachectl configtest
```

```bash
sudo systemctl restart apache2
```

### 8-4. 조치 후 확인

```bash
curl -i "$SERVER/web12-link/secret-link.txt"
```

조치 후 기대 결과:

```text
HTTP/1.1 403 Forbidden
```

또는:

```text
HTTP/1.1 404 Not Found
```

```bash
grep -R "FollowSymLinks\|SymLinksIfOwnerMatch\|Alias" /etc/apache2/apache2.conf /etc/apache2/sites-enabled/ /etc/apache2/sites-available/ /etc/apache2/conf-enabled/ /etc/apache2/conf-available/ 2>/dev/null | grep -v '^\s*#'
```

```bash
systemctl status apache2 --no-pager
```

```bash
curl -i "$SERVER/"
```

### 8-5. 실습 환경 제거

증거 확보 후에는 실습용 설정과 파일을 제거한다.

```bash
sudo a2disconf web-12-link-test
```

```bash
sudo rm -f "$TEST_CONF"
```

```bash
sudo rm -rf "$TEST_DIR"
```

```bash
sudo rm -rf "$SECRET_DIR"
```

```bash
sudo apachectl configtest
```

```bash
sudo systemctl restart apache2
```

정리 확인:

```bash
ls -ld "$TEST_DIR" "$SECRET_DIR" "$TEST_CONF" 2>/dev/null
```

기대 결과:

```text
출력 없음
```

## 9. 증거 정리

### 9-1. 최초 상태 증거

최초 진단 결과:

```text
WEB-12 · 웹 서비스 링크 사용 금지
Apache 설정에 Options Indexes FollowSymLinks 존재
```

심볼릭 링크 관련 설정 확인:

```bash
grep -R "FollowSymLinks\|SymLinksIfOwnerMatch\|Alias" /etc/apache2/apache2.conf /etc/apache2/sites-enabled/ /etc/apache2/sites-available/ /etc/apache2/conf-enabled/ /etc/apache2/conf-available/ 2>/dev/null | grep -v '^\s*#'
```

취약 상태 설정 예시:

```apache
Options Indexes FollowSymLinks
```

### 9-2. 취약 재현 증거

심볼릭 링크 확인:

```bash
ls -l "$TEST_DIR/secret-link.txt"
```

기대 결과:

```text
/var/www/care/web12-link/secret-link.txt -> /tmp/web12-secret/secret.txt
```

심볼릭 링크 접근 요청:

```bash
curl -i "$SERVER/web12-link/secret-link.txt"
```

취약 재현 기대 결과:

```text
HTTP/1.1 200 OK

WEB-12 symbolic link secret
```

이 결과는 웹 루트 내부의 심볼릭 링크를 통해 웹 루트 외부 파일에 접근 가능함을 의미한다.

### 9-3. 조치 후 증거

보안 설정 확인:

```bash
grep -R "FollowSymLinks\|SymLinksIfOwnerMatch\|Alias" /etc/apache2/apache2.conf /etc/apache2/sites-enabled/ /etc/apache2/sites-available/ /etc/apache2/conf-enabled/ /etc/apache2/conf-available/ 2>/dev/null | grep -v '^\s*#'
```

기대 설정 예시:

```apache
Options -FollowSymLinks
```

심볼릭 링크 재요청:

```bash
curl -i "$SERVER/web12-link/secret-link.txt"
```

조치 후 기대 결과:

```text
HTTP/1.1 403 Forbidden
```

또는:

```text
HTTP/1.1 404 Not Found
```

## 10. 판단

|항목|판단|
|---|---|
|최초 진단|취약|
|진단 근거|Apache 설정에 `Options Indexes FollowSymLinks` 존재|
|실습 처리|웹 루트 내부 심볼릭 링크로 외부 테스트 파일 접근을 재현한 뒤 `-FollowSymLinks` 적용|
|조치 전 판단|심볼릭 링크 요청이 200 OK로 처리되면 취약|
|조치 후 판단|심볼릭 링크 요청이 403 또는 404로 차단되면 양호|
|증거 상태|최초 진단 결과 확보, 취약 재현 및 조치 후 접근 증거 필요|

현재 서버는 최초 진단 기준으로 Apache 설정에 `Options Indexes FollowSymLinks`가 존재하므로 WEB-12는 **취약**으로 판단한다.

`FollowSymLinks`가 허용되면 웹 루트 내부의 심볼릭 링크를 통해 웹 루트 외부 파일에 접근할 수 있다. 이는 DocumentRoot를 분리해도 심볼릭 링크가 외부 경로를 다시 연결할 수 있다는 점에서 위험하다.

실습에서는 `/var/www/care/web12-link/secret-link.txt`가 `/tmp/web12-secret/secret.txt`를 가리키도록 만든 뒤, `FollowSymLinks` 허용 상태에서 파일 내용이 웹으로 노출되는지 확인한다.

조치는 `FollowSymLinks`를 제거하거나 `Options -FollowSymLinks`를 적용하는 방식으로 수행한다. 조치 후 같은 심볼릭 링크 요청이 `403 Forbidden` 또는 `404 Not Found`로 처리되고, 링크 대상 파일 내용이 더 이상 출력되지 않으면 WEB-12는 조치 후 **양호**로 판단한다.