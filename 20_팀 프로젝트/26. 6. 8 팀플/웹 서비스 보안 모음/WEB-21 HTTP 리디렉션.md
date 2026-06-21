---

type: lab  
topic: web-service-security  
source: 주요정보통신기반시설 기술적 취약점 분석·평가 방법 상세가이드  
source_pages:

- 334
    
- 335
    
- 336
    
- 337  
status: draft  
created: 2026-06-18  
tags:
    
- 🏷️과목/웹서비스보안
    
- 🏷️주제/WEB-21
    
- 🏷️주제/HTTP-Redirect
    
- 🏷️주제/HTTPS
    
- 🏷️주제/Apache
    
- 🏷️상태/draft
    

---
# WEB-21 HTTP 리디렉션

## 1. PDF 기준

PDF p.334-337의 WEB-21은 웹 서비스 접근 시 **HTTP 접속이 HTTPS로 리디렉션되는지** 점검하는 항목이다.

WEB-20이 “HTTPS 자체가 활성화되어 있는가”를 보는 항목이라면, WEB-21은 “사용자가 `http://`로 접속했을 때 자동으로 `https://`로 이동하는가”를 보는 항목이다.

HTTP는 평문 통신이다. 로그인 요청, 세션 쿠키, 개인정보가 HTTP로 전송되면 네트워크 중간에서 스니핑될 수 있다.

```text
HTTP 접속
→ 평문 전송
→ 계정 정보, 세션 정보, 요청 데이터 노출 위험
```

HTTPS 리디렉션이 활성화되어 있으면 사용자가 실수로 HTTP 주소에 접속해도 서버가 HTTPS 주소로 이동시킨다.

```text
http://172.168.10.10/
→ 301 또는 302 Redirect
→ https://172.168.10.10/
```

PDF의 판단 기준은 다음과 같다.

|판단|기준|
|---|---|
|양호|HTTP 접근 시 HTTPS Redirection이 활성화된 경우|
|취약|HTTP 접근 시 HTTPS Redirection이 비활성화된 경우|

Apache 기준 조치 예시는 다음 두 방식이다.

### Redirect 지시자 방식

```apache
<VirtualHost *:80>
    ServerName example.com
    Redirect permanent / https://example.com/
</VirtualHost>
```

### mod_rewrite 방식

```apache
<VirtualHost *:80>
    RewriteEngine On
    RewriteCond %{HTTPS} off
    RewriteRule ^ https://%{HTTP_HOST}%{REQUEST_URI} [L,R=301]
</VirtualHost>
```

CARE 실습 서버에서는 실제 도메인이 없을 수 있으므로, IP 기반으로 다음 흐름을 확인한다.

```text
http://172.168.10.10/
→ https://172.168.10.10/
```

## 2. 최초 진단 결과

`AWS WEB 약점 진단 결과.md` 기준 WEB-21은 **수동 진단 항목**으로 분류되어 있다.

다만 진단 파일의 WEB-21 설명은 PDF WEB-21과 일치하지 않는다.

진단 파일의 WEB-21 설명은 다음과 같다.

```text
WEB-21 | 동적 페이지 입력값 검증 | 소스코드 레벨 수동 검토 필요
```

하지만 PDF p.334-337의 WEB-21은 **동적 페이지 입력값 검증이 아니라 HTTP 리디렉션** 항목이다.

따라서 이 노트에서는 다음처럼 처리한다.

|구분|내용|
|---|---|
|PDF 기준 WEB-21|HTTP 리디렉션|
|진단 파일 WEB-21|동적 페이지 입력값 검증|
|일치 여부|불일치|
|자동 진단 결과 활용|PDF WEB-21의 직접 근거로 사용 불가|
|이 노트의 판단 방식|HTTP 요청이 HTTPS로 리디렉션되는지 수동 확인|

즉 WEB-21은 자동 진단 결과를 그대로 쓰지 않고, 다음 명령으로 직접 판단해야 한다.

```bash
curl -I http://172.168.10.10/
```

양호 상태의 핵심 증거는 다음이다.

```text
HTTP/1.1 301 Moved Permanently
Location: https://172.168.10.10/
```

또는:

```text
HTTP/1.1 302 Found
Location: https://172.168.10.10/
```

## 3. 현재 서버 상태 해석

WEB-21은 WEB-20의 후속 항목으로 봐야 한다.

|항목|핵심|
|---|---|
|WEB-20|HTTPS가 실제로 동작하는가|
|WEB-21|HTTP 접속을 HTTPS로 강제 이동시키는가|

HTTPS가 아직 동작하지 않으면 HTTP 리디렉션을 적용해도 사용자가 최종 HTTPS 페이지에 접속할 수 없다.

따라서 WEB-21 실습 전에는 WEB-20 상태를 먼저 확인해야 한다.

```text
1. HTTPS가 동작한다.
2. HTTP 요청이 HTTPS로 리디렉션된다.
3. 리디렉션 후 HTTPS 페이지가 정상 응답한다.
```

판단 기준은 다음과 같다.

|상태|판단|
|---|---|
|HTTP 요청이 200 OK로 그대로 응답|취약|
|HTTP 요청이 HTTPS가 아닌 다른 HTTP 경로로 이동|취약 또는 확인 필요|
|HTTP 요청이 HTTPS URL로 301/302 이동|양호|
|HTTPS 리디렉션은 되지만 HTTPS 접속 실패|WEB-21은 일부 충족, WEB-20 또는 네트워크 설정 확인 필요|
|서버 내부는 정상, 외부에서 HTTPS 실패|AWS 보안 그룹/NACL 확인 필요|

HTTP 리디렉션은 보통 다음 중 하나로 구현한다.

|방식|설명|
|---|---|
|`Redirect permanent`|단순하고 명확한 전체 경로 리디렉션|
|`RewriteRule`|조건 기반 리디렉션. 경로와 쿼리 보존에 유리|
|애플리케이션 코드|PHP나 프레임워크에서 리디렉션|
|로드밸런서/프록시|ALB, Nginx, CloudFront 등 앞단에서 처리|

CARE Apache 단일 서버 실습에서는 Apache `mod_rewrite` 방식이 가장 직접적이다.

## 4. 실습 전 확인

### 4-1. 실습용 변수 지정

```bash
SERVER_IP=172.168.10.10
HTTP_URL="http://$SERVER_IP"
HTTPS_URL="https://$SERVER_IP"
APP_ROOT=/var/www/care

TEST_CONF=/etc/apache2/conf-available/web-21-https-redirect-test.conf
REWRITE_MARKER=/tmp/web21-rewrite-module-was-enabled
```

현재 서버 IP가 다르면 `SERVER_IP` 값을 실제 서버 IP로 바꾼다.

### 4-2. Apache 가상호스트 확인

```bash
apache2ctl -S
```

확인할 대상은 다음이다.

```text
*:80
*:443
```

### 4-3. HTTPS 동작 확인

```bash
curl -k -I "$HTTPS_URL/"
```

HTTPS가 정상 동작하면 다음과 유사한 응답이 나온다.

```text
HTTP/1.1 200 OK
```

또는:

```text
HTTP/1.1 302 Found
```

HTTPS가 동작하지 않으면 WEB-21보다 WEB-20 조치가 먼저다.

### 4-4. 현재 HTTP 응답 확인

```bash
curl -I "$HTTP_URL/"
```

헤더만 정리해서 보려면 다음 명령을 사용한다.

```bash
curl -s -D - -o /dev/null "$HTTP_URL/" | grep -iE '^HTTP/|^Location:'
```

취약 상태에서는 HTTP가 그대로 응답할 수 있다.

```text
HTTP/1.1 200 OK
```

또는 애플리케이션 자체 리다이렉트가 있더라도 HTTPS가 아닐 수 있다.

```text
HTTP/1.1 302 Found
Location: /login.php
```

양호 상태에서는 `Location`이 `https://`로 시작해야 한다.

```text
HTTP/1.1 301 Moved Permanently
Location: https://172.168.10.10/
```

### 4-5. rewrite 모듈 확인

```bash
apache2ctl -M | grep rewrite
```

활성화되어 있으면 다음처럼 출력된다.

```text
rewrite_module (shared)
```

출력이 없으면 현재 `mod_rewrite`가 비활성화된 상태다.

### 4-6. 기존 리디렉션 설정 확인

```bash
grep -R "Redirect permanent\|RewriteEngine\|RewriteCond.*HTTPS\|RewriteRule.*https" \
/etc/apache2/apache2.conf \
/etc/apache2/sites-enabled/ \
/etc/apache2/sites-available/ \
/etc/apache2/conf-enabled/ \
/etc/apache2/conf-available/ 2>/dev/null | grep -v '^\s*#'
```

기존에 HTTPS 리디렉션 설정이 이미 있으면 중복으로 추가하지 않는다.

## 5. 취약 재현

WEB-21은 수동 확인 항목이다.

HTTP 요청이 HTTPS로 리디렉션되지 않는다면 그 자체가 취약 재현 증거가 된다.

### 5-1. HTTP 요청 확인

```bash
curl -s -D - -o /dev/null "$HTTP_URL/" | grep -iE '^HTTP/|^Location:'
```

취약 상태 예시는 다음이다.

```text
HTTP/1.1 200 OK
```

또는:

```text
HTTP/1.1 302 Found
Location: /login.php
```

위 상태는 HTTP 요청이 HTTPS로 강제 이동하지 않은 것이다.

### 5-2. HTTPS 리디렉션 미적용 확인

다음 명령으로 `Location` 헤더에 `https://`가 있는지 확인한다.

```bash
curl -s -D - -o /dev/null "$HTTP_URL/" | grep -i '^Location:'
```

취약 상태에서는 출력이 없거나, HTTPS가 아닌 경로가 나온다.

```text
출력 없음
```

또는:

```text
Location: /login.php
```

### 5-3. 상태코드만 확인

```bash
curl -s -o /dev/null -w "%{http_code} %{redirect_url}\n" "$HTTP_URL/"
```

취약 상태 예시:

```text
200
```

또는:

```text
302 http://172.168.10.10/login.php
```

양호 상태라면 다음처럼 `redirect_url`이 HTTPS여야 한다.

```text
301 https://172.168.10.10/
```

## 6. 조치 방법

조치 핵심은 HTTP 요청을 HTTPS로 리디렉션하도록 Apache 설정을 추가하는 것이다.

실습에서는 실제 VirtualHost 파일을 직접 수정하지 않고, CARE 웹 루트 디렉터리에 적용되는 별도 conf 파일을 만든다.

이 방식은 기존 사이트 설정을 크게 건드리지 않고 실습할 수 있다.

### 6-1. rewrite 모듈 상태 기록

```bash
if apache2ctl -M | grep -q "rewrite_module"; then
  echo "yes" | sudo tee "$REWRITE_MARKER"
else
  echo "no" | sudo tee "$REWRITE_MARKER"
fi
```

확인:

```bash
cat "$REWRITE_MARKER"
```

### 6-2. rewrite 모듈 활성화

```bash
sudo a2enmod rewrite
```

이미 활성화되어 있으면 다음과 유사한 메시지가 나올 수 있다.

```text
Module rewrite already enabled
```

### 6-3. HTTPS 리디렉션 설정 생성

```bash
sudo tee "$TEST_CONF" > /dev/null <<EOF
<Directory "$APP_ROOT">
    RewriteEngine On
    RewriteCond %{HTTPS} off
    RewriteRule ^ https://%{HTTP_HOST}%{REQUEST_URI} [R=301,L]
</Directory>
EOF
```

핵심 설정은 다음이다.

```apache
RewriteEngine On
RewriteCond %{HTTPS} off
RewriteRule ^ https://%{HTTP_HOST}%{REQUEST_URI} [R=301,L]
```

이 설정은 HTTP 요청일 때만 같은 호스트와 같은 URI를 HTTPS로 리디렉션한다.

예시는 다음과 같다.

```text
http://172.168.10.10/login.php
→ https://172.168.10.10/login.php
```

### 6-4. 설정 활성화

```bash
sudo a2enconf web-21-https-redirect-test
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

### 7-1. HTTP 요청의 HTTPS 리디렉션 확인

```bash
curl -s -D - -o /dev/null "$HTTP_URL/" | grep -iE '^HTTP/|^Location:'
```

조치 후 기대 결과는 다음이다.

```text
HTTP/1.1 301 Moved Permanently
Location: https://172.168.10.10/
```

또는 환경에 따라 다음처럼 나올 수 있다.

```text
HTTP/1.1 302 Found
Location: https://172.168.10.10/
```

### 7-2. 경로 보존 확인

```bash
curl -s -D - -o /dev/null "$HTTP_URL/web21-redirect-test?x=1" | grep -iE '^HTTP/|^Location:'
```

기대 결과는 다음과 유사하다.

```text
HTTP/1.1 301 Moved Permanently
Location: https://172.168.10.10/web21-redirect-test?x=1
```

경로와 쿼리스트링이 보존되는지 확인한다.

### 7-3. 최종 HTTPS 응답 확인

`-L` 옵션으로 리디렉션을 따라간다.

```bash
curl -k -L -I "$HTTP_URL/"
```

기대 흐름은 다음이다.

```text
HTTP/1.1 301 Moved Permanently
Location: https://172.168.10.10/

HTTP/1.1 200 OK
```

또는:

```text
HTTP/1.1 301 Moved Permanently
Location: https://172.168.10.10/

HTTP/1.1 302 Found
```

최종 HTTPS 응답은 CARE 애플리케이션 상태에 따라 달라질 수 있다.

### 7-4. 설정 적용 확인

```bash
grep -R "RewriteEngine\|RewriteCond.*HTTPS\|RewriteRule.*https" \
/etc/apache2/apache2.conf \
/etc/apache2/sites-enabled/ \
/etc/apache2/sites-available/ \
/etc/apache2/conf-enabled/ \
/etc/apache2/conf-available/ 2>/dev/null | grep -v '^\s*#'
```

기대 결과는 다음과 유사하다.

```text
/etc/apache2/conf-enabled/web-21-https-redirect-test.conf:    RewriteEngine On
/etc/apache2/conf-enabled/web-21-https-redirect-test.conf:    RewriteCond %{HTTPS} off
/etc/apache2/conf-enabled/web-21-https-redirect-test.conf:    RewriteRule ^ https://%{HTTP_HOST}%{REQUEST_URI} [R=301,L]
```

### 7-5. Apache 서비스 상태 확인

```bash
systemctl status apache2 --no-pager
```

정상 상태라면 다음과 같이 보여야 한다.

```text
Active: active (running)
```

## 8. 실행 순서 요약

### 8-1. 현재 상태 확인

```bash
SERVER_IP=172.168.10.10
HTTP_URL="http://$SERVER_IP"
HTTPS_URL="https://$SERVER_IP"
APP_ROOT=/var/www/care

TEST_CONF=/etc/apache2/conf-available/web-21-https-redirect-test.conf
REWRITE_MARKER=/tmp/web21-rewrite-module-was-enabled
```

```bash
apache2ctl -S
```

```bash
curl -k -I "$HTTPS_URL/"
```

```bash
curl -s -D - -o /dev/null "$HTTP_URL/" | grep -iE '^HTTP/|^Location:'
```

```bash
apache2ctl -M | grep rewrite
```

```bash
grep -R "Redirect permanent\|RewriteEngine\|RewriteCond.*HTTPS\|RewriteRule.*https" \
/etc/apache2/apache2.conf \
/etc/apache2/sites-enabled/ \
/etc/apache2/sites-available/ \
/etc/apache2/conf-enabled/ \
/etc/apache2/conf-available/ 2>/dev/null | grep -v '^\s*#'
```

### 8-2. 취약 상태 확인

```bash
curl -s -o /dev/null -w "%{http_code} %{redirect_url}\n" "$HTTP_URL/"
```

취약 상태 예시:

```text
200
```

또는:

```text
302 http://172.168.10.10/login.php
```

양호 상태 예시:

```text
301 https://172.168.10.10/
```

### 8-3. 조치 적용

```bash
if apache2ctl -M | grep -q "rewrite_module"; then
  echo "yes" | sudo tee "$REWRITE_MARKER"
else
  echo "no" | sudo tee "$REWRITE_MARKER"
fi
```

```bash
sudo a2enmod rewrite
```

```bash
sudo tee "$TEST_CONF" > /dev/null <<EOF
<Directory "$APP_ROOT">
    RewriteEngine On
    RewriteCond %{HTTPS} off
    RewriteRule ^ https://%{HTTP_HOST}%{REQUEST_URI} [R=301,L]
</Directory>
EOF
```

```bash
sudo a2enconf web-21-https-redirect-test
```

```bash
sudo apachectl configtest
```

```bash
sudo systemctl restart apache2
```

### 8-4. 조치 후 확인

```bash
curl -s -D - -o /dev/null "$HTTP_URL/" | grep -iE '^HTTP/|^Location:'
```

기대 결과:

```text
HTTP/1.1 301 Moved Permanently
Location: https://172.168.10.10/
```

```bash
curl -s -D - -o /dev/null "$HTTP_URL/web21-redirect-test?x=1" | grep -iE '^HTTP/|^Location:'
```

기대 결과:

```text
Location: https://172.168.10.10/web21-redirect-test?x=1
```

```bash
curl -k -L -I "$HTTP_URL/"
```

기대 흐름:

```text
HTTP/1.1 301 Moved Permanently
Location: https://172.168.10.10/

HTTP/1.1 200 OK
```

또는:

```text
HTTP/1.1 301 Moved Permanently
Location: https://172.168.10.10/

HTTP/1.1 302 Found
```

```bash
systemctl status apache2 --no-pager
```

기대 결과:

```text
Active: active (running)
```

### 8-5. 실습용 설정 정리

WEB-21 조치를 실제로 유지할 목적이면 이 정리 절차를 수행하지 않는다.

실습용으로만 적용했다면 증거 확보 후 제거한다.

```bash
sudo a2disconf web-21-https-redirect-test
```

```bash
sudo rm -f "$TEST_CONF"
```

실습 전에 `rewrite` 모듈이 비활성화되어 있었고, 다른 서비스에서 사용하지 않는 경우에만 비활성화한다.

```bash
if [ "$(cat "$REWRITE_MARKER" 2>/dev/null)" = "no" ]; then
  sudo a2dismod rewrite
fi
```

```bash
sudo rm -f "$REWRITE_MARKER"
```

```bash
sudo apachectl configtest
```

```bash
sudo systemctl restart apache2
```

단, HTTPS 리디렉션은 보안 조치이므로 운영 목적이라면 제거하지 않고 유지하는 편이 맞다.

## 9. 증거 정리

### 9-1. 최초 상태 증거

진단 파일의 WEB-21은 PDF 항목과 불일치한다.

```text
진단 파일 WEB-21: 동적 페이지 입력값 검증
PDF WEB-21: HTTP 리디렉션
```

따라서 PDF 기준 WEB-21은 다음 명령으로 별도 확인한다.

```bash
curl -s -D - -o /dev/null "$HTTP_URL/" | grep -iE '^HTTP/|^Location:'
```

취약 상태 예시:

```text
HTTP/1.1 200 OK
```

또는:

```text
HTTP/1.1 302 Found
Location: /login.php
```

양호 상태 예시:

```text
HTTP/1.1 301 Moved Permanently
Location: https://172.168.10.10/
```

### 9-2. 취약 상태 증거

HTTP 요청이 HTTPS로 이동하지 않는 경우 다음 결과를 취약 증거로 사용한다.

```bash
curl -s -o /dev/null -w "%{http_code} %{redirect_url}\n" "$HTTP_URL/"
```

취약 상태 기대 결과:

```text
200
```

또는:

```text
302 http://172.168.10.10/login.php
```

이 결과는 HTTP 접속이 HTTPS로 강제 전환되지 않는다는 의미다.

### 9-3. 조치 후 증거

조치 설정:

```apache
<Directory "/var/www/care">
    RewriteEngine On
    RewriteCond %{HTTPS} off
    RewriteRule ^ https://%{HTTP_HOST}%{REQUEST_URI} [R=301,L]
</Directory>
```

HTTP 요청 확인:

```bash
curl -s -D - -o /dev/null "$HTTP_URL/" | grep -iE '^HTTP/|^Location:'
```

조치 후 기대 결과:

```text
HTTP/1.1 301 Moved Permanently
Location: https://172.168.10.10/
```

리디렉션 최종 응답 확인:

```bash
curl -k -L -I "$HTTP_URL/"
```

기대 흐름:

```text
HTTP/1.1 301 Moved Permanently
Location: https://172.168.10.10/

HTTP/1.1 200 OK
```

또는:

```text
HTTP/1.1 301 Moved Permanently
Location: https://172.168.10.10/

HTTP/1.1 302 Found
```

## 10. 판단

|항목|판단|
|---|---|
|자동 진단|수동|
|진단 파일 내용|WEB-21이 동적 페이지 입력값 검증으로 표시되어 PDF WEB-21과 불일치|
|PDF 기준 항목|HTTP 접근 시 HTTPS Redirection 활성화 여부|
|취약 조건|HTTP 요청이 HTTPS로 리디렉션되지 않음|
|양호 조건|HTTP 요청이 `301` 또는 `302`로 HTTPS URL에 리디렉션됨|
|선행 조건|WEB-20 HTTPS 활성화 필요|
|조치 방향|Apache `Redirect` 또는 `mod_rewrite`로 HTTP → HTTPS 리디렉션 적용|

현재 WEB-21은 자동 진단 결과만으로 판단할 수 없다. 진단 파일의 WEB-21 설명이 PDF WEB-21과 일치하지 않기 때문이다.

PDF 기준 WEB-21은 HTTP 리디렉션 항목이므로, `curl -I http://172.168.10.10/` 요청에서 `Location: https://172.168.10.10/` 형태의 응답이 나오는지 직접 확인해야 한다.

HTTP 요청이 `200 OK`로 그대로 응답하거나, HTTPS가 아닌 HTTP 경로로만 이동하면 WEB-21은 **취약**이다.

조치 후 HTTP 요청이 `301` 또는 `302`로 HTTPS URL에 이동하고, `curl -k -L -I http://172.168.10.10/` 명령에서 최종 HTTPS 응답이 정상 확인되면 WEB-21은 **양호**로 판단한다.