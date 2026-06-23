---
type: lab  
topic: web-service-security  
source: 주요정보통신기반시설 기술적 취약점 분석·평가 방법 상세가이드  
source_pages:
  - 286
  - 287
  - 288
  - 289  
status: draft  
created: 2026-06-18  
tags:  
  - 🏷️과목/웹서비스보안 
  - 🏷️주제/WEB-06 
  - 🏷️주제/Directory-Traversal 
  - 🏷️주제/Apache 
  - 🏷️상태/draft 
---
# WEB-06 웹 서비스 상위 디렉터리 접근 제한 설정

## 1. PDF 기준

PDF p.286-289의 WEB-06은 웹 서버에서 **상위 디렉터리 접근이 제한되어 있는지** 점검하는 항목이다.

상위 디렉터리 접근은 URL이나 경로에 `..` 같은 문자열을 사용하여 현재 디렉터리의 상위 경로로 이동하려는 접근을 의미한다.

예를 들어 다음과 같은 요청이 이에 해당한다.

```text
http://서버주소/some/path/../target/file.txt
http://서버주소/download?file=../../../../etc/passwd
```

웹 서버나 웹 애플리케이션이 이런 경로 이동을 적절히 제한하지 않으면, 공격자는 허용된 디렉터리를 벗어나 다른 파일이나 디렉터리에 접근하려고 시도할 수 있다.

PDF의 판단 기준은 다음과 같다.

|판단|기준|
|---|---|
|양호|상위 디렉터리 접근 기능을 제거한 경우|
|취약|상위 디렉터리 접근 기능을 제거하지 않은 경우|

PDF의 Apache 조치 사례는 `AllowOverride AuthConfig`와 `.htaccess`를 이용하여 특정 디렉터리에 사용자 인증을 적용하는 방식이다.

Apache 기준으로는 다음을 확인한다.

|확인 대상|의미|
|---|---|
|`AllowOverride`|`.htaccess`에서 인증 설정을 사용할 수 있는지|
|`.htaccess`|특정 디렉터리 접근 시 인증을 요구하는지|
|`AuthType`, `AuthName`, `AuthUserFile`, `Require`|Basic 인증 구성 요소|
|`../` 요청 결과|상위 경로 접근 시 비인가 접근이 차단되는지|

현재 실습 서버는 Apache 기반이므로, 이 노트에서는 Apache의 디렉터리 접근 제한과 `.htaccess` 인증을 중심으로 정리한다.

## 2. 최초 진단 결과

`AWS WEB 약점 진단 결과.md` 기준 WEB-06은 **수동 진단 항목**이다.

|항목|내용|
|---|---|
|진단 결과|수동|
|진단 근거|자동 진단만으로 상위 디렉터리 접근 차단 여부를 확정하기 어려움|
|확인 방법|`AllowOverride None` 여부 확인, `../` 요청 시 403 또는 401 응답 확인|
|최초 판단|직접 설정 확인과 HTTP 요청 테스트 필요|

진단 파일에서 제시된 확인 방향은 다음과 같다.

```text
AllowOverride None 확인, ../ 요청 시 403 응답 테스트
```

즉 이 항목은 설정 파일만 보고 바로 양호 또는 취약으로 단정하기 어렵다.  
실제 접근 제한이 적용되는지 HTTP 요청으로 확인해야 한다.

## 3. 현재 서버 상태 해석

Apache에서 상위 디렉터리 접근 제한은 두 층위로 나눠서 봐야 한다.

|구분|설명|
|---|---|
|웹 서버 경로 처리|Apache가 URL의 `../` 요청을 어떻게 정규화하고 차단하는지|
|디렉터리 접근 통제|특정 디렉터리에 인증 또는 접근 제한이 적용되어 있는지|
|애플리케이션 경로 처리|PHP 코드가 파일 경로 파라미터에서 `../`를 허용하는지|

WEB-06은 웹 서비스 보안 항목이므로 우선 Apache 설정을 본다.

다만 주의할 점이 있다. Apache는 일반적으로 웹 루트 바깥의 시스템 파일을 단순 URL `../`만으로 바로 노출하지 않는다. 그러나 웹 루트 안에 보호해야 할 디렉터리가 있고 인증이나 접근 제한이 없다면, 사용자는 상위 경로 이동 형태의 URL을 통해 보호해야 할 파일에 접근할 수 있다.

따라서 이 노트에서는 다음을 실습한다.

```text
1. 보호가 필요한 테스트 디렉터리를 만든다.
2. 인증이 없는 상태에서 상위 경로 이동 형태의 URL로 접근 가능한지 확인한다.
3. .htaccess Basic 인증을 적용한다.
4. 같은 요청이 인증 없이 차단되는지 확인한다.
```

PDF의 Apache 조치 사례가 `.htaccess` 인증을 사용하는 이유도 이 흐름과 연결된다.

## 4. 실습 전 확인

실습을 시작하기 전에 현재 Apache 환경과 DocumentRoot를 확인한다.

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
PUBLIC_DIR="$APP_ROOT/web06-public"
PROTECTED_DIR="$APP_ROOT/web06-protected"
TEST_CONF="/etc/apache2/conf-available/web-06-upperdir-test.conf"
HTPASSWD_FILE="/etc/apache2/.htpasswd-web06"
```

현재 서버의 DocumentRoot가 다르면 `APP_ROOT` 값을 실제 경로로 바꾼다.

### 4-3. 현재 AllowOverride 설정 확인

```bash
grep -R "AllowOverride" /etc/apache2/apache2.conf /etc/apache2/sites-enabled/ /etc/apache2/sites-available/ /etc/apache2/conf-enabled/ /etc/apache2/conf-available/ 2>/dev/null | grep -v '^\s*#'
```

`AllowOverride None`은 해당 디렉터리에서 `.htaccess` 설정을 무시한다는 뜻이다.

PDF의 Apache 조치 사례처럼 `.htaccess` 인증을 적용하려면 해당 디렉터리에 대해 다음과 같은 설정이 필요하다.

```apache
AllowOverride AuthConfig
```

### 4-4. htpasswd 명령어 확인

```bash
command -v htpasswd
```

출력이 없으면 `apache2-utils` 패키지가 필요하다.

```bash
sudo apt update
sudo apt install -y apache2-utils
```

## 5. 취약 재현

WEB-06은 최초 진단에서 수동 항목이므로, 직접 접근 테스트를 통해 상태를 확인한다.

이 실습에서는 보호가 필요한 디렉터리를 만든 뒤, 인증이 없는 상태에서 상위 경로 이동 형태의 URL로 접근 가능한지 확인한다.

> 주의: 이 절차는 격리된 실습 서버에서만 수행한다.  
> 실습용 디렉터리와 파일만 만들고, 실제 중요 파일이나 운영 경로를 사용하지 않는다.  
> 실습 후에는 생성한 설정과 파일을 제거한다.

### 5-1. 실습용 공개 디렉터리와 보호 대상 디렉터리 생성

```bash
sudo mkdir -p "$PUBLIC_DIR"
sudo mkdir -p "$PROTECTED_DIR"
```

### 5-2. 공개 디렉터리 파일 생성

```bash
echo "WEB-06 public directory" | sudo tee "$PUBLIC_DIR/index.html"
```

### 5-3. 보호 대상 테스트 파일 생성

```bash
echo "WEB-06 protected secret" | sudo tee "$PROTECTED_DIR/secret.txt"
```

### 5-4. 취약 상태 확인

일반 접근을 먼저 확인한다.

```bash
curl -i "$SERVER/web06-protected/secret.txt"
```

취약 상태라면 다음과 유사한 응답이 나온다.

```text
HTTP/1.1 200 OK

WEB-06 protected secret
```

상위 경로 이동 형태의 URL도 확인한다.

```bash
curl --path-as-is -i "$SERVER/web06-public/../web06-protected/secret.txt"
```

취약 상태라면 다음과 유사한 응답이 나온다.

```text
HTTP/1.1 200 OK

WEB-06 protected secret
```

이 결과는 보호가 필요한 디렉터리에 인증 또는 접근 제한이 적용되어 있지 않아, 상위 경로 이동 형태의 URL로도 파일 접근이 가능하다는 뜻이다.

## 6. 조치 방법

조치 핵심은 보호 대상 디렉터리에 인증을 적용하여 비인가 접근을 차단하는 것이다.

PDF의 Apache 조치 사례에 따라 다음 흐름으로 조치한다.

```text
1. 보호 대상 디렉터리에 AllowOverride AuthConfig 허용
2. .htaccess 생성
3. htpasswd로 인증 사용자 생성
4. Apache 설정 문법 검사
5. Apache restart
```

### 6-1. Apache 실습용 설정 파일 생성

```bash
sudo tee "$TEST_CONF" > /dev/null <<EOF
<Directory $PROTECTED_DIR>
    AllowOverride AuthConfig
    Require all granted
</Directory>
EOF
```

이 설정은 `$PROTECTED_DIR` 디렉터리에서 `.htaccess`의 인증 관련 설정을 허용한다.

`AllowOverride All`이 아니라 `AuthConfig`만 허용하는 이유는 인증 설정에 필요한 범위만 열기 위해서다.

### 6-2. 보호 대상 디렉터리에 .htaccess 생성

```bash
sudo tee "$PROTECTED_DIR/.htaccess" > /dev/null <<EOF
AuthName "WEB-06 Protected Directory"
AuthType Basic
AuthUserFile $HTPASSWD_FILE
Require valid-user
EOF
```

### 6-3. 인증 사용자 생성

```bash
sudo htpasswd -Bbc "$HTPASSWD_FILE" web06user 'Web06!Pass123'
```

생성된 인증 파일 권한을 확인한다.

```bash
sudo chmod 640 "$HTPASSWD_FILE"
sudo chown root:www-data "$HTPASSWD_FILE"
ls -l "$HTPASSWD_FILE"
```

### 6-4. Apache 설정 활성화

```bash
sudo a2enconf web-06-upperdir-test
```

### 6-5. Apache 설정 문법 검사

```bash
sudo apachectl configtest
```

정상이라면 다음 결과가 나와야 한다.

```text
Syntax OK
```

### 6-6. Apache restart

```bash
sudo systemctl restart apache2
```

## 7. 조치 후 확인

조치 후에는 인증 없이 보호 대상 파일에 접근했을 때 차단되는지 확인한다.

### 7-1. 일반 직접 접근 확인

```bash
curl -i "$SERVER/web06-protected/secret.txt"
```

정상 조치 상태라면 다음과 유사한 응답이 나와야 한다.

```text
HTTP/1.1 401 Unauthorized
```

또는 서버 설정에 따라 다음이 나올 수 있다.

```text
HTTP/1.1 403 Forbidden
```

중요한 것은 다음 내용이 인증 없이 출력되지 않는 것이다.

```text
WEB-06 protected secret
```

### 7-2. 상위 경로 이동 형태의 요청 확인

```bash
curl --path-as-is -i "$SERVER/web06-public/../web06-protected/secret.txt"
```

정상 조치 상태라면 다음과 유사한 응답이 나와야 한다.

```text
HTTP/1.1 401 Unauthorized
```

또는:

```text
HTTP/1.1 403 Forbidden
```

### 7-3. 인증 성공 확인

인증을 넣으면 접근 가능해야 한다.
보안 기능으로 인해 해당 명령어를 그대로 넣으면 커밋,푸쉬가 안되어 왜곡하여 기록한다.
```bash
컬 --path-as-is -u web06user:'Web06!Pass123' -i "$SERVER/web06-public/../web06-protected/secret.txt"
```

기대 결과는 다음과 같다.

```text
HTTP/1.1 200 OK

WEB-06 protected secret
```

이 결과는 접근 제한이 정상 적용되었고, 인증된 사용자만 접근할 수 있음을 의미한다.

### 7-4. AllowOverride 설정 확인

```bash
grep -R "web06-protected\|AllowOverride AuthConfig" /etc/apache2/apache2.conf /etc/apache2/sites-enabled/ /etc/apache2/sites-available/ /etc/apache2/conf-enabled/ /etc/apache2/conf-available/ 2>/dev/null
```

기대 결과는 다음과 같다.

```text
<Directory /var/www/html/care/web06-protected>
    AllowOverride AuthConfig
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
grep -R "AllowOverride" /etc/apache2/apache2.conf /etc/apache2/sites-enabled/ /etc/apache2/sites-available/ /etc/apache2/conf-enabled/ /etc/apache2/conf-available/ 2>/dev/null | grep -v '^\s*#'
```

```bash
command -v htpasswd
```

### 8-2. 취약 재현

```bash
APP_ROOT=/var/www/html/care
SERVER=http://172.168.10.10
PUBLIC_DIR="$APP_ROOT/web06-public"
PROTECTED_DIR="$APP_ROOT/web06-protected"
TEST_CONF="/etc/apache2/conf-available/web-06-upperdir-test.conf"
HTPASSWD_FILE="/etc/apache2/.htpasswd-web06"
```

```bash
sudo mkdir -p "$PUBLIC_DIR"
sudo mkdir -p "$PROTECTED_DIR"
```

```bash
echo "WEB-06 public directory" | sudo tee "$PUBLIC_DIR/index.html"
```

```bash
echo "WEB-06 protected secret" | sudo tee "$PROTECTED_DIR/secret.txt"
```

```bash
curl -i "$SERVER/web06-protected/secret.txt"
```

```bash
curl --path-as-is -i "$SERVER/web06-public/../web06-protected/secret.txt"
```

취약 상태 기대 결과:

```text
HTTP/1.1 200 OK

WEB-06 protected secret
```

### 8-3. 조치 및 적용

```bash
sudo tee "$TEST_CONF" > /dev/null <<EOF
<Directory $PROTECTED_DIR>
    AllowOverride AuthConfig
    Require all granted
</Directory>
EOF
```

```bash
sudo tee "$PROTECTED_DIR/.htaccess" > /dev/null <<EOF
AuthName "WEB-06 Protected Directory"
AuthType Basic
AuthUserFile $HTPASSWD_FILE
Require valid-user
EOF
```

```bash
sudo htpasswd -Bbc "$HTPASSWD_FILE" web06user 'Web06!Pass123'
```

```bash
sudo chmod 640 "$HTPASSWD_FILE"
sudo chown root:www-data "$HTPASSWD_FILE"
ls -l "$HTPASSWD_FILE"
```

```bash
sudo a2enconf web-06-upperdir-test
```

```bash
sudo apachectl configtest
```

```bash
sudo systemctl restart apache2
```

### 8-4. 조치 후 확인

```bash
curl -i "$SERVER/web06-protected/secret.txt"
```

```bash
curl --path-as-is -i "$SERVER/web06-public/../web06-protected/secret.txt"
```

조치 후 기대 결과:

```text
HTTP/1.1 401 Unauthorized
```

또는:

```text
HTTP/1.1 403 Forbidden
```

인증 성공 확인:

```bash
컬 --path-as-is -u web06user:'Web06!Pass123' -i "$SERVER/web06-public/../web06-protected/secret.txt"
```

인증 성공 기대 결과:

```text
HTTP/1.1 200 OK

WEB-06 protected secret
```

### 8-5. 실습 환경 제거

실습 증거를 확보한 뒤에는 테스트 설정과 파일을 제거한다.

```bash
sudo a2disconf web-06-upperdir-test
```

```bash
sudo rm -f "$TEST_CONF"
```

```bash
sudo rm -f "$HTPASSWD_FILE"
```

```bash
sudo rm -rf "$PUBLIC_DIR" "$PROTECTED_DIR"
```

```bash
sudo apachectl configtest
```

```bash
sudo systemctl restart apache2
```

제거 확인:

```bash
ls -ld "$PUBLIC_DIR" "$PROTECTED_DIR" 2>/dev/null
```

기대 결과:

```text
출력 없음
```

## 9. 증거 정리

### 9-1. 최초 상태 증거

WEB-06은 자동 진단에서 수동 항목으로 분류되었다.

```text
WEB-06 | 상위 디렉터리 접근 제한 | AllowOverride None 확인, ../ 요청 시 403 응답 테스트
```

현재 AllowOverride 설정 확인:

```bash
grep -R "AllowOverride" /etc/apache2/apache2.conf /etc/apache2/sites-enabled/ /etc/apache2/sites-available/ /etc/apache2/conf-enabled/ /etc/apache2/conf-available/ 2>/dev/null | grep -v '^\s*#'
```

### 9-2. 취약 재현 증거

인증 적용 전 요청:

```bash
curl --path-as-is -i "$SERVER/web06-public/../web06-protected/secret.txt"
```

취약 재현 기대 결과:

```text
HTTP/1.1 200 OK

WEB-06 protected secret
```

이 결과는 보호가 필요한 테스트 디렉터리에 접근 제한이 없어, 상위 경로 이동 형태의 요청으로 파일 내용을 확인할 수 있음을 의미한다.

### 9-3. 조치 후 증거

인증 적용 후 요청:

```bash
curl --path-as-is -i "$SERVER/web06-public/../web06-protected/secret.txt"
```

조치 후 기대 결과:

```text
HTTP/1.1 401 Unauthorized
```

또는:

```text
HTTP/1.1 403 Forbidden
```

인증 성공 요청:

```bash
컬 --path-as-is -u web06user:'Web06!Pass123' -i "$SERVER/web06-public/../web06-protected/secret.txt"
```

인증 성공 기대 결과:

```text
HTTP/1.1 200 OK

WEB-06 protected secret
```

## 10. 판단

|항목|판단|
|---|---|
|최초 진단|수동|
|진단 근거|`AllowOverride` 설정 확인과 `../` 요청 결과를 직접 확인해야 함|
|실습 처리|보호 대상 테스트 디렉터리를 만들고, 인증 적용 전후 접근 결과 비교|
|조치 전 판단|인증 없이 보호 대상 파일이 보이면 취약|
|조치 후 판단|인증 없이 401 또는 403이 반환되면 양호|
|증거 상태|자동 진단 결과 확보, 수동 접근 테스트 증거 필요|

WEB-06은 자동 진단만으로 최종 판단하기 어려운 수동 항목이다.

Apache 환경에서는 `AllowOverride AuthConfig`와 `.htaccess` Basic 인증을 이용하여 보호 대상 디렉터리 접근을 제한할 수 있다. 인증 적용 전에는 상위 경로 이동 형태의 URL로 보호 대상 파일에 접근 가능한지 확인하고, 인증 적용 후에는 같은 요청이 `401 Unauthorized` 또는 `403 Forbidden`으로 차단되는지 확인한다.

조치 후 인증 없이 보호 대상 파일 내용이 출력되지 않고, 인증된 사용자만 접근 가능하면 WEB-06은 **양호**로 판단한다.