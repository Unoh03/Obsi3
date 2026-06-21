---

type: lab  
topic: web-service-security  
source: 주요정보통신기반시설 기술적 취약점 분석·평가 방법 상세가이드  
source_pages:

- 329
    
- 330
    
- 331
    
- 332
    
- 333  
status: draft  
created: 2026-06-18  
tags:
    
- 🏷️과목/웹서비스보안
    
- 🏷️주제/WEB-20
    
- 🏷️주제/SSL-TLS
    
- 🏷️주제/HTTPS
    
- 🏷️주제/Apache
    
- 🏷️상태/draft
    

---
# WEB-20 SSL/TLS 활성화

## 1. PDF 기준

PDF p.329-333의 WEB-20은 웹 서비스에서 **SSL/TLS가 활성화되어 있는지** 점검하는 항목이다.

SSL/TLS는 서버와 클라이언트 사이의 통신을 암호화하여, 중간에서 트래픽을 도청하더라도 로그인 정보, 세션 정보, 개인정보, 요청·응답 데이터가 평문으로 노출되지 않도록 한다.

HTTP만 사용하는 경우 다음과 같은 위험이 있다.

```text
사용자 브라우저 ↔ 웹 서버
통신 데이터가 평문으로 전송됨
공격자가 네트워크 중간에서 스니핑하면 요청/응답 내용 확인 가능
```

HTTPS를 사용하는 경우 다음과 같이 통신이 암호화된다.

```text
사용자 브라우저 ↔ TLS 암호화 통신 ↔ 웹 서버
중간에서 패킷을 보더라도 실제 데이터 내용 확인이 어려움
```

PDF의 판단 기준은 다음과 같다.

|판단|기준|
|---|---|
|양호|SSL/TLS 설정이 활성화되어 있는 경우|
|취약|SSL/TLS 설정이 비활성화되어 있는 경우|

Apache 기준 조치 흐름은 다음이다.

```text
1. ssl_module 활성화 확인
2. 443 포트 VirtualHost 설정
3. SSLEngine On 설정
4. 인증서 파일과 개인키 파일 설정
5. SSL 사이트 활성화
6. Apache 재시작
```

Apache SSL 가상호스트의 핵심 설정 예시는 다음과 같다.

```apache
<VirtualHost *:443>
    ServerName example.com
    DocumentRoot /var/www/html

    SSLEngine on
    SSLCertificateFile /path/to/cert.crt
    SSLCertificateKeyFile /path/to/private.key
</VirtualHost>
```

## 2. 최초 진단 결과

`AWS WEB 약점 진단 결과.md` 기준 WEB-20의 자동 진단 결과는 **취약**으로 표시되어 있다.

다만 진단 파일 내부에 다음 모순이 있다.

```text
command_result: SSL module loaded, HTTPS configured
Result: VULNERABLE
```

즉 명령 결과는 `SSL module loaded, HTTPS configured`라고 표시되지만, 최종 결과는 `VULNERABLE`로 판정되어 있다.

따라서 이 항목은 다음처럼 처리한다.

|구분|판단|
|---|---|
|자동 진단 표기|취약|
|자동 진단 내부 근거|SSL 모듈 로드 및 HTTPS 설정 확인|
|문제|결과와 근거가 충돌함|
|최종 처리|수동 확인 후 판단|
|실습 기준|HTTPS가 실제로 응답하면 양호, HTTPS가 동작하지 않으면 취약|

WEB-20은 자동 진단 결과만 보고 바로 취약으로 확정하면 안 된다.  
다음 세 가지를 직접 확인해야 한다.

```text
1. Apache ssl_module 로드 여부
2. 443 포트 Listen 여부
3. HTTPS 요청이 실제로 성공하는지 여부
```

## 3. 현재 서버 상태 해석

WEB-20은 단순히 SSL 모듈이 로드되어 있는지만 보는 항목이 아니다.

다음 조건이 함께 만족되어야 실제로 SSL/TLS가 활성화되었다고 판단할 수 있다.

|확인 항목|양호 조건|
|---|---|
|Apache SSL 모듈|`ssl_module (shared)` 확인|
|443 포트|`0.0.0.0:443` 또는 `*:443` Listen|
|SSL 가상호스트|`<VirtualHost *:443>` 존재|
|SSL 엔진|`SSLEngine on`|
|인증서|`SSLCertificateFile` 설정|
|개인키|`SSLCertificateKeyFile` 설정|
|HTTPS 응답|`curl -k -I https://서버주소/` 성공|
|AWS 보안 그룹|TCP 443 인바운드 허용|

판단을 나누면 다음과 같다.

|상태|판단|
|---|---|
|`ssl_module` 없음|취약|
|`ssl_module` 있음, 443 Listen 없음|취약|
|443 Listen 있음, HTTPS 요청 실패|취약 또는 네트워크 설정 문제|
|HTTPS 요청 성공|양호|
|서버 내부 HTTPS 성공, 외부 HTTPS 실패|Apache는 양호 가능, AWS 보안 그룹/NACL 확인 필요|

WEB-20은 WEB-21 HTTP 리디렉션과 구분해야 한다.

|항목|핵심|
|---|---|
|WEB-20|HTTPS 자체가 활성화되어 있는가|
|WEB-21|HTTP 접속을 HTTPS로 리디렉션하는가|

즉 WEB-20은 HTTPS가 동작하는지 확인하는 항목이고, WEB-21은 HTTP로 들어온 사용자를 HTTPS로 강제 이동시키는지 확인하는 항목이다.

## 4. 실습 전 확인

실습 전 현재 Apache SSL 상태를 확인한다.

### 4-1. 실습용 변수 지정

```bash
SERVER_IP=172.168.10.10
HTTP_URL="http://$SERVER_IP"
HTTPS_URL="https://$SERVER_IP"
APP_ROOT=/var/www/care

SSL_SITE=/etc/apache2/sites-available/web-20-ssl-test.conf
CERT_DIR=/etc/apache2/ssl/web20
CERT_FILE="$CERT_DIR/web20.crt"
KEY_FILE="$CERT_DIR/web20.key"

SSL_MARKER=/tmp/web20-ssl-module-was-enabled
```

현재 서버 IP가 다르면 `SERVER_IP`를 실제 서버 IP로 바꾼다.

### 4-2. Apache 가상호스트 확인

```bash
apache2ctl -S
```

443 가상호스트가 있다면 다음과 유사한 출력이 보일 수 있다.

```text
*:443                  172.168.10.10 (/etc/apache2/sites-enabled/xxx.conf:1)
```

### 4-3. SSL 모듈 확인

```bash
apache2ctl -M | grep ssl
```

SSL 모듈이 활성화되어 있으면 다음처럼 출력된다.

```text
ssl_module (shared)
```

출력이 없으면 SSL 모듈이 로드되지 않은 상태다.

### 4-4. 443 포트 Listen 확인

```bash
sudo ss -tlnp | grep ':443'
```

HTTPS가 활성화되어 있으면 다음과 유사한 결과가 나와야 한다.

```text
LISTEN 0 511 0.0.0.0:443 0.0.0.0:* users:(("apache2",pid=...,fd=...))
```

출력이 없으면 Apache가 443 포트에서 대기하지 않는 상태다.

### 4-5. SSL 설정 확인

```bash
grep -R "SSLEngine\|SSLCertificateFile\|SSLCertificateKeyFile\|<VirtualHost .*443" \
/etc/apache2/sites-enabled/ \
/etc/apache2/sites-available/ \
/etc/apache2/conf-enabled/ \
/etc/apache2/conf-available/ 2>/dev/null | grep -v '^\s*#'
```

양호 상태에서는 다음과 같은 설정이 확인되어야 한다.

```apache
<VirtualHost *:443>
SSLEngine on
SSLCertificateFile /path/to/cert.crt
SSLCertificateKeyFile /path/to/key.key
```

### 4-6. HTTPS 응답 확인

자체 서명 인증서나 사설 인증서를 사용할 수 있으므로, 실습에서는 `-k` 옵션으로 인증서 검증을 생략한다.

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

HTTPS가 동작하지 않으면 다음과 같은 실패가 나올 수 있다.

```text
curl: (7) Failed to connect to 172.168.10.10 port 443
```

또는:

```text
curl: (35) OpenSSL SSL_connect: SSL_ERROR_SYSCALL
```

## 5. 취약 재현

WEB-20은 최초 자동 진단에서 취약으로 표시되었지만, 내부 결과에 `HTTPS configured`가 있어 오탐 가능성이 있다.

따라서 취약 재현은 다음 두 경우로 나누어 처리한다.

|현재 상태|처리|
|---|---|
|HTTPS가 실제로 동작하지 않음|현재 상태 자체가 취약 재현 증거|
|HTTPS가 이미 동작함|운영 HTTPS를 끄지 말고, 진단 오탐으로 기록한 뒤 조치 후 확인으로 이동|

운영 중인 HTTPS를 일부러 끄는 것은 서비스 영향이 크므로, 실습 서버에서만 수행한다.

### 5-1. HTTPS 미동작 상태 확인

```bash
curl -k -I "$HTTPS_URL/"
```

취약 상태 기대 결과는 다음과 같다.

```text
curl: (7) Failed to connect to 172.168.10.10 port 443
```

또는 HTTP 상태코드가 나오지 않는다.

상태코드만 확인하려면 다음 명령을 사용한다.

```bash
curl -k -s -o /dev/null -w "%{http_code}\n" "$HTTPS_URL/"
```

HTTPS 미동작 상태에서는 다음처럼 `000`이 나올 수 있다.

```text
000
```

### 5-2. 443 포트 미사용 확인

```bash
sudo ss -tlnp | grep ':443'
```

취약 상태 기대 결과는 다음이다.

```text
출력 없음
```

### 5-3. SSL 모듈 미로드 확인

```bash
apache2ctl -M | grep ssl
```

취약 상태에서는 다음처럼 출력이 없을 수 있다.

```text
출력 없음
```

### 5-4. SSL 가상호스트 부재 확인

```bash
apache2ctl -S | grep ':443'
```

취약 상태에서는 다음처럼 출력이 없을 수 있다.

```text
출력 없음
```

이 상태라면 PDF 기준 WEB-20은 취약으로 판단할 수 있다.

## 6. 조치 방법

조치 핵심은 Apache에서 HTTPS 가상호스트를 구성하고 SSL/TLS를 활성화하는 것이다.

실습에서는 자체 서명 인증서를 사용한다.  
운영 환경에서는 자체 서명 인증서가 아니라 공인 CA 또는 내부 CA 인증서를 사용해야 한다.

### 6-1. 실습 전 SSL 모듈 상태 기록

```bash
if apache2ctl -M | grep -q "ssl_module"; then
  echo "yes" | sudo tee "$SSL_MARKER"
else
  echo "no" | sudo tee "$SSL_MARKER"
fi
```

확인:

```bash
cat "$SSL_MARKER"
```

### 6-2. SSL 모듈 활성화

```bash
sudo a2enmod ssl
```

이미 활성화되어 있으면 다음과 유사한 메시지가 나올 수 있다.

```text
Module ssl already enabled
```

### 6-3. 인증서 디렉터리 생성

```bash
sudo mkdir -p "$CERT_DIR"
```

### 6-4. 실습용 자체 서명 인증서 생성

```bash
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout "$KEY_FILE" \
  -out "$CERT_FILE" \
  -subj "/CN=$SERVER_IP"
```

생성 확인:

```bash
sudo ls -l "$CERT_FILE" "$KEY_FILE"
```

개인키 권한을 제한한다.

```bash
sudo chmod 600 "$KEY_FILE"
```

### 6-5. SSL 가상호스트 설정 생성

이미 운영 SSL 사이트가 존재한다면 이 테스트 사이트를 새로 만들지 말고, 기존 SSL 사이트 설정을 점검한다.

443 가상호스트가 없는 경우에만 다음 실습용 설정을 만든다.

```bash
sudo tee "$SSL_SITE" > /dev/null <<EOF
<VirtualHost *:443>
    ServerName $SERVER_IP
    DocumentRoot $APP_ROOT

    SSLEngine on
    SSLCertificateFile $CERT_FILE
    SSLCertificateKeyFile $KEY_FILE

    <Directory "$APP_ROOT">
        AllowOverride All
        Require all granted
    </Directory>

    ErrorLog \${APACHE_LOG_DIR}/web20-ssl-error.log
    CustomLog \${APACHE_LOG_DIR}/web20-ssl-access.log combined
</VirtualHost>
EOF
```

핵심 설정은 다음이다.

```apache
SSLEngine on
SSLCertificateFile /etc/apache2/ssl/web20/web20.crt
SSLCertificateKeyFile /etc/apache2/ssl/web20/web20.key
```

### 6-6. SSL 사이트 활성화

```bash
sudo a2ensite web-20-ssl-test
```

### 6-7. Apache 설정 문법 검사

```bash
sudo apachectl configtest
```

정상이라면 다음 결과가 나와야 한다.

```text
Syntax OK
```

### 6-8. Apache restart

```bash
sudo systemctl restart apache2
```

### 6-9. AWS 보안 그룹 확인

서버 내부에서 HTTPS가 동작하는데 외부에서 접속이 안 되면 Apache 문제가 아니라 AWS 보안 그룹 또는 NACL 문제일 수 있다.

AWS 보안 그룹 인바운드 규칙에 다음이 필요하다.

|유형|프로토콜|포트|소스|
|---|---|---|---|
|HTTPS|TCP|443|실습 환경에 맞는 IP 또는 0.0.0.0/0|

운영 환경에서는 `0.0.0.0/0`을 무조건 쓰기보다 실제 공개 범위에 맞게 제한한다.

## 7. 조치 후 확인

조치 후에는 SSL 모듈, 443 포트, HTTPS 응답을 모두 확인한다.

### 7-1. SSL 모듈 확인

```bash
apache2ctl -M | grep ssl
```

기대 결과:

```text
ssl_module (shared)
```

### 7-2. 443 포트 Listen 확인

```bash
sudo ss -tlnp | grep ':443'
```

기대 결과:

```text
LISTEN ... :443 ... apache2
```

### 7-3. SSL 가상호스트 확인

```bash
apache2ctl -S | grep ':443'
```

기대 결과:

```text
*:443
```

### 7-4. SSL 설정 확인

```bash
grep -R "SSLEngine\|SSLCertificateFile\|SSLCertificateKeyFile\|<VirtualHost .*443" \
/etc/apache2/sites-enabled/ \
/etc/apache2/sites-available/ \
/etc/apache2/conf-enabled/ \
/etc/apache2/conf-available/ 2>/dev/null | grep -v '^\s*#'
```

기대 결과:

```apache
SSLEngine on
SSLCertificateFile ...
SSLCertificateKeyFile ...
```

### 7-5. HTTPS 응답 확인

```bash
curl -k -I "$HTTPS_URL/"
```

기대 결과:

```text
HTTP/1.1 200 OK
```

또는:

```text
HTTP/1.1 302 Found
```

상태코드만 확인하려면 다음 명령을 사용한다.

```bash
curl -k -s -o /dev/null -w "%{http_code}\n" "$HTTPS_URL/"
```

기대 결과:

```text
200
```

또는:

```text
302
```

### 7-6. 인증서 정보 확인

```bash
openssl s_client -connect "$SERVER_IP:443" -servername "$SERVER_IP" </dev/null 2>/dev/null | openssl x509 -noout -subject -issuer -dates
```

실습용 자체 서명 인증서라면 subject와 issuer가 같을 수 있다.

```text
subject=CN = 172.168.10.10
issuer=CN = 172.168.10.10
```

운영 환경에서는 공인 또는 내부 CA가 발급한 인증서를 사용하는 것이 적절하다.

### 7-7. TLS 1.2 이상 확인

```bash
openssl s_client -connect "$SERVER_IP:443" -tls1_2 </dev/null 2>/dev/null | grep -E "Protocol|Cipher"
```

가능하면 TLS 1.3도 확인한다.

```bash
openssl s_client -connect "$SERVER_IP:443" -tls1_3 </dev/null 2>/dev/null | grep -E "Protocol|Cipher"
```

TLS 1.2 또는 TLS 1.3 연결이 정상 수립되면 암호화 통신이 가능하다.

### 7-8. Apache 서비스 상태 확인

```bash
systemctl status apache2 --no-pager
```

기대 결과:

```text
Active: active (running)
```

## 8. 실행 순서 요약

실습 중에는 아래 순서대로 진행한다.

### 8-1. 현재 상태 확인

```bash
SERVER_IP=172.168.10.10
HTTP_URL="http://$SERVER_IP"
HTTPS_URL="https://$SERVER_IP"
APP_ROOT=/var/www/care

SSL_SITE=/etc/apache2/sites-available/web-20-ssl-test.conf
CERT_DIR=/etc/apache2/ssl/web20
CERT_FILE="$CERT_DIR/web20.crt"
KEY_FILE="$CERT_DIR/web20.key"

SSL_MARKER=/tmp/web20-ssl-module-was-enabled
```

```bash
apache2ctl -S
```

```bash
apache2ctl -M | grep ssl
```

```bash
sudo ss -tlnp | grep ':443'
```

```bash
grep -R "SSLEngine\|SSLCertificateFile\|SSLCertificateKeyFile\|<VirtualHost .*443" \
/etc/apache2/sites-enabled/ \
/etc/apache2/sites-available/ \
/etc/apache2/conf-enabled/ \
/etc/apache2/conf-available/ 2>/dev/null | grep -v '^\s*#'
```

```bash
curl -k -I "$HTTPS_URL/"
```

### 8-2. 취약 상태 확인

HTTPS가 미동작하는 경우 다음 결과를 취약 증거로 기록한다.

```bash
curl -k -s -o /dev/null -w "%{http_code}\n" "$HTTPS_URL/"
```

취약 상태 기대 결과:

```text
000
```

```bash
sudo ss -tlnp | grep ':443'
```

취약 상태 기대 결과:

```text
출력 없음
```

### 8-3. 조치 적용

```bash
if apache2ctl -M | grep -q "ssl_module"; then
  echo "yes" | sudo tee "$SSL_MARKER"
else
  echo "no" | sudo tee "$SSL_MARKER"
fi
```

```bash
sudo a2enmod ssl
```

```bash
sudo mkdir -p "$CERT_DIR"
```

```bash
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout "$KEY_FILE" \
  -out "$CERT_FILE" \
  -subj "/CN=$SERVER_IP"
```

```bash
sudo chmod 600 "$KEY_FILE"
```

443 가상호스트가 없을 때만 실습용 SSL 사이트를 생성한다.

```bash
sudo tee "$SSL_SITE" > /dev/null <<EOF
<VirtualHost *:443>
    ServerName $SERVER_IP
    DocumentRoot $APP_ROOT

    SSLEngine on
    SSLCertificateFile $CERT_FILE
    SSLCertificateKeyFile $KEY_FILE

    <Directory "$APP_ROOT">
        AllowOverride All
        Require all granted
    </Directory>

    ErrorLog \${APACHE_LOG_DIR}/web20-ssl-error.log
    CustomLog \${APACHE_LOG_DIR}/web20-ssl-access.log combined
</VirtualHost>
EOF
```

```bash
sudo a2ensite web-20-ssl-test
```

```bash
sudo apachectl configtest
```

```bash
sudo systemctl restart apache2
```

### 8-4. 조치 후 확인

```bash
apache2ctl -M | grep ssl
```

기대 결과:

```text
ssl_module (shared)
```

```bash
sudo ss -tlnp | grep ':443'
```

기대 결과:

```text
LISTEN ... :443 ... apache2
```

```bash
apache2ctl -S | grep ':443'
```

기대 결과:

```text
*:443
```

```bash
curl -k -I "$HTTPS_URL/"
```

기대 결과:

```text
HTTP/1.1 200 OK
```

또는:

```text
HTTP/1.1 302 Found
```

```bash
openssl s_client -connect "$SERVER_IP:443" -servername "$SERVER_IP" </dev/null 2>/dev/null | openssl x509 -noout -subject -issuer -dates
```

```bash
systemctl status apache2 --no-pager
```

기대 결과:

```text
Active: active (running)
```

### 8-5. 실습용 SSL 설정 정리

운영용 HTTPS 설정으로 사용할 목적이 아니라, WEB-20 실습용으로만 만든 경우에는 증거 확보 후 제거한다.

```bash
sudo a2dissite web-20-ssl-test
```

```bash
sudo rm -f "$SSL_SITE"
```

```bash
sudo rm -rf "$CERT_DIR"
```

실습 전에 `ssl_module`이 비활성화되어 있었고, 다른 사이트에서 SSL을 사용하지 않는 경우에만 비활성화한다.

```bash
if [ "$(cat "$SSL_MARKER" 2>/dev/null)" = "no" ]; then
  sudo a2dismod ssl
fi
```

```bash
sudo rm -f "$SSL_MARKER"
```

```bash
sudo apachectl configtest
```

```bash
sudo systemctl restart apache2
```

단, WEB-20을 실제 조치 완료 상태로 유지해야 한다면 위 정리 절차를 수행하지 않는다.  
이 경우 실습용 자체 서명 인증서를 운영용 인증서로 교체하는 것이 필요하다.

## 9. 증거 정리

### 9-1. 최초 진단 증거

진단 파일의 WEB-20 결과는 다음처럼 모순되어 있다.

```text
command_result: SSL module loaded, HTTPS configured
Result: VULNERABLE
```

따라서 자동 진단 결과는 그대로 신뢰하지 않고, 다음 수동 확인 결과를 증거로 사용한다.

```bash
apache2ctl -M | grep ssl
```

```bash
sudo ss -tlnp | grep ':443'
```

```bash
curl -k -I "$HTTPS_URL/"
```

### 9-2. 취약 상태 증거

HTTPS가 동작하지 않는 경우 다음 결과를 취약 증거로 기록한다.

```bash
curl -k -s -o /dev/null -w "%{http_code}\n" "$HTTPS_URL/"
```

취약 상태 기대 결과:

```text
000
```

443 포트 미사용 증거:

```bash
sudo ss -tlnp | grep ':443'
```

취약 상태 기대 결과:

```text
출력 없음
```

SSL 가상호스트 부재 증거:

```bash
apache2ctl -S | grep ':443'
```

취약 상태 기대 결과:

```text
출력 없음
```

### 9-3. 조치 후 증거

SSL 모듈 활성화:

```bash
apache2ctl -M | grep ssl
```

기대 결과:

```text
ssl_module (shared)
```

443 포트 Listen:

```bash
sudo ss -tlnp | grep ':443'
```

기대 결과:

```text
LISTEN ... :443 ... apache2
```

HTTPS 응답:

```bash
curl -k -I "$HTTPS_URL/"
```

기대 결과:

```text
HTTP/1.1 200 OK
```

또는:

```text
HTTP/1.1 302 Found
```

인증서 확인:

```bash
openssl s_client -connect "$SERVER_IP:443" -servername "$SERVER_IP" </dev/null 2>/dev/null | openssl x509 -noout -subject -issuer -dates
```

## 10. 판단

|항목|판단|
|---|---|
|자동 진단|취약으로 표시됨|
|자동 진단 근거|`SSL module loaded, HTTPS configured`로 표시되어 결과와 모순|
|최종 판단 방식|수동 확인 필요|
|취약 조건|SSL 모듈 없음, 443 포트 미사용, HTTPS 요청 실패|
|양호 조건|SSL 모듈 활성화, 443 포트 Listen, HTTPS 요청 성공|
|조치 방향|SSL 모듈 활성화, 443 VirtualHost 구성, 인증서/개인키 설정|
|증거 상태|자동 진단 모순 기록, 수동 HTTPS 확인 증거 필요|

현재 WEB-20은 자동 진단 결과만 기준으로 하면 **취약**으로 표시되어 있다.

하지만 진단 파일 내부에 `SSL module loaded, HTTPS configured`라는 결과가 함께 기록되어 있어 자동 진단 오탐 가능성이 있다. 따라서 이 항목은 반드시 수동 확인으로 최종 판단해야 한다.

수동 확인에서 `apache2ctl -M | grep ssl` 결과로 `ssl_module (shared)`가 확인되고, `ss -tlnp | grep ':443'`에서 Apache가 443 포트를 Listen하며, `curl -k -I https://172.168.10.10/` 요청이 `200 OK` 또는 `302 Found`로 응답하면 WEB-20은 **양호**로 판단한다.

반대로 HTTPS 요청이 실패하고 443 포트가 열려 있지 않다면 WEB-20은 **취약**이다. 이 경우 SSL 모듈을 활성화하고, 443 가상호스트와 인증서 설정을 추가한 뒤 Apache를 재시작하여 조치한다.