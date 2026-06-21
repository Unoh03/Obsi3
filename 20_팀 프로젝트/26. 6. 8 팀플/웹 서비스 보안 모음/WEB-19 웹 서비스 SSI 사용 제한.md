---

type: lab  
topic: web-service-security  
source: 주요정보통신기반시설 기술적 취약점 분석·평가 방법 상세가이드  
source_pages:

- 325
    
- 326
    
- 327
    
- 328  
status: draft  
created: 2026-06-18  
tags:
    
- 🏷️과목/웹서비스보안
    
- 🏷️주제/WEB-19
    
- 🏷️주제/SSI
    
- 🏷️주제/Server-Side-Includes
    
- 🏷️주제/Apache
    
- 🏷️상태/draft
    

---
# WEB-19 웹 서비스 SSI 사용 제한

## 1. PDF 기준

PDF p.325-328의 WEB-19는 웹 서비스에서 **SSI(Server Side Includes) 기능 사용이 제한되어 있는지** 점검하는 항목이다.

SSI는 웹 서버가 HTML 문서를 클라이언트에게 전달하기 전에, 문서 안에 포함된 SSI 지시문을 서버 측에서 먼저 해석하는 기능이다.

예를 들어 SSI가 활성화된 `.shtml` 파일 안에 다음과 같은 문법이 들어 있으면:

```html
<!--#echo var="DATE_LOCAL" -->
```

Apache는 이 문자열을 단순 HTML 주석으로 보내지 않고, 서버에서 해석한 결과를 응답에 포함할 수 있다.

SSI가 불필요하게 활성화되어 있으면 공격자가 SSI 지시문을 삽입하거나 악용하여 서버 내부 정보 노출, 파일 내용 유출, 경우에 따라 명령 실행 위험을 만들 수 있다.

PDF의 판단 기준은 다음과 같다.

|판단|기준|
|---|---|
|양호|웹 서비스 SSI 사용 설정이 비활성화되어 있는 경우|
|취약|웹 서비스 SSI 사용 설정이 활성화되어 있는 경우|

Apache 기준으로는 다음 설정을 확인한다.

|설정|의미|
|---|---|
|`include_module`|Apache SSI 기능을 제공하는 `mod_include` 모듈|
|`Options Includes`|해당 디렉터리에서 SSI 처리를 허용|
|`Options +Includes`|상위 설정에 SSI 허용 추가|
|`Options IncludesNOEXEC`|SSI는 허용하되 `exec` 실행은 제한|
|`AddOutputFilter INCLUDES .shtml`|`.shtml` 파일을 SSI 처리 대상으로 지정|
|`AddType text/html .shtml`|`.shtml` 확장자를 HTML로 응답|
|`server-parsed`|SSI 처리와 관련된 레거시 핸들러 설정|

취약 설정 예시는 다음과 같다.

```apache
<Directory /var/www/care>
    Options Includes
</Directory>
```

조치 방향은 다음과 같다.

```apache
<Directory /var/www/care>
    Options -Includes
</Directory>
```

또는 서비스에 SSI가 필요하지 않다면 `mod_include` 모듈과 SSI 관련 필터 설정을 제거한다.

## 2. 최초 진단 결과

`AWS WEB 약점 진단 결과.md`의 WEB-19 항목은 PDF의 WEB-19와 내용이 일치하지 않는다.

진단 결과 파일의 WEB-19는 다음 내용이다.

```text
WEB-19 · WebDAV 모듈 미로드

No WebDAV module or DAV directive found
```

하지만 PDF p.325-328의 WEB-19는 **WebDAV가 아니라 SSI 사용 제한** 항목이다.

따라서 이 노트에서는 다음처럼 처리한다.

|구분|판단|
|---|---|
|PDF 기준 WEB-19|SSI 사용 제한|
|AWS 진단 결과 WEB-19|WebDAV 모듈 미로드|
|일치 여부|불일치|
|자동 진단 결과 사용 가능 여부|PDF WEB-19 판단 근거로 직접 사용 불가|
|이 노트의 기준|PDF 기준에 맞춰 SSI 설정을 별도 확인|

즉, 진단 파일의 WEB-19 결과는 이미 WEB-18 WebDAV 항목과 내용이 겹친다.  
WEB-19는 PDF 기준에 맞춰 `include_module`, `Options Includes`, `AddOutputFilter INCLUDES` 설정을 별도로 확인해야 한다.

PDF 기준으로는 다음 조건을 만족하면 양호로 판단한다.

```text
Apache에 SSI 사용 설정이 없고,
웹 서비스 경로에 Options Includes 또는 AddOutputFilter INCLUDES 설정이 없으면 양호
```

## 3. 현재 서버 상태 해석

WEB-19는 웹 서버가 `.shtml` 같은 파일을 단순 정적 파일로 제공하는지, 아니면 서버 측에서 SSI 지시문을 해석하는지를 확인하는 항목이다.

Apache에서 SSI가 활성화되려면 보통 다음 조건이 필요하다.

```text
1. include_module 로드
2. 특정 디렉터리에서 Options Includes 허용
3. .shtml 파일에 AddOutputFilter INCLUDES 적용
```

이 중 하나만으로 항상 동작하는 것은 아니지만, 다음 설정들이 함께 있으면 SSI 사용 가능성이 높다.

```apache
Options +Includes
AddType text/html .shtml
AddOutputFilter INCLUDES .shtml
```

SSI가 활성화되면 다음과 같은 흐름이 가능하다.

```text
사용자 요청:
GET /web19-ssi/test.shtml

서버 파일:
<!--#echo var="DATE_LOCAL" -->

Apache:
SSI 지시문 해석

응답:
서버가 해석한 날짜 또는 변수 값 반환
```

위험한 상태는 다음과 같다.

|상태|위험|
|---|---|
|SSI가 필요 없는데 `Options Includes`가 켜져 있음|불필요한 서버 측 해석 기능 노출|
|업로드 파일에 `.shtml` 허용|공격자가 SSI 지시문 삽입 가능|
|`exec` 기능까지 허용|서버 명령 실행 위험|
|사용자 입력이 SSI 문맥에 반영됨|SSI Injection 위험|
|`.shtml`, `.shtm`, `.stm` 매핑이 남아 있음|레거시 SSI 처리 경로 노출|

이 항목은 WEB-15와 연결된다.

|연결 항목|연결 이유|
|---|---|
|WEB-15 불필요한 스크립트 매핑 제거|`.shtml` 확장자를 SSI 처리기로 연결하는 것도 스크립트 매핑 성격이 있음|
|WEB-21 동적 페이지 입력값 검증|사용자 입력이 SSI 문맥에 반영되면 SSI Injection 가능|
|WEB-23 HTTP 메서드 제한|업로드·PUT 등으로 SSI 파일을 배치할 수 있으면 위험 증가|

## 4. 실습 전 확인

실습을 시작하기 전에 Apache 모듈, SSI 관련 설정, DocumentRoot를 확인한다.

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
TEST_DIR="$APP_ROOT/web19-ssi"
TEST_FILE="$TEST_DIR/test.shtml"
TEST_CONF=/etc/apache2/conf-available/web-19-ssi-test.conf
INCLUDE_MARKER=/tmp/web19-include-module-was-enabled
```

현재 서버의 DocumentRoot가 다르면 `APP_ROOT` 값을 실제 경로로 바꾼다.

### 4-3. SSI 모듈 확인

```bash
apache2ctl -M | grep include
```

SSI 모듈이 비활성화된 상태라면 출력이 없다.

```text
출력 없음
```

SSI 모듈이 활성화되어 있으면 다음과 같이 출력된다.

```text
include_module (shared)
```

### 4-4. SSI 관련 설정 확인

```bash
grep -Ri "Options.*Includes\|AddOutputFilter.*INCLUDES\|server-parsed\|\.shtml\|\.shtm\|\.stm" \
/etc/apache2/apache2.conf \
/etc/apache2/sites-enabled/ \
/etc/apache2/sites-available/ \
/etc/apache2/conf-enabled/ \
/etc/apache2/conf-available/ 2>/dev/null | grep -v '^\s*#'
```

양호 상태라면 웹 서비스 경로에 불필요한 SSI 설정이 없어야 한다.

```text
출력 없음
```

다만 실제 서비스에서 `.shtml`을 사용하는 경우 출력될 수 있다.  
이 경우 해당 기능이 필요한지, 사용자 업로드 파일이 SSI로 해석될 가능성이 있는지 별도 검토해야 한다.

### 4-5. 실습 전 모듈 상태 기록

실습 후 원래 상태로 되돌리기 위해 `include_module` 상태를 기록한다.

```bash
if apache2ctl -M | grep -q "include_module"; then
  echo "yes" | sudo tee "$INCLUDE_MARKER"
else
  echo "no" | sudo tee "$INCLUDE_MARKER"
fi
```

기록 결과 확인:

```bash
cat "$INCLUDE_MARKER"
```

## 5. 취약 재현

이 항목은 PDF 기준으로 SSI 설정이 비활성화되어 있으면 양호다.  
실습에서는 SSI가 활성화되었을 때 어떤 식으로 서버 측 해석이 발생하는지 확인하기 위해 의도적으로 취약 상태를 만든다.

> 주의: 이 절차는 격리된 실습 서버에서만 수행한다.  
> 실제 서비스 업로드 경로나 운영 페이지에 SSI를 활성화하지 않는다.  
> 실습용 `.shtml` 파일만 사용하고, 증거 확보 후 즉시 제거한다.

취약 재현의 핵심은 다음이다.

```text
실습용 디렉터리에서 Options +Includes와 AddOutputFilter INCLUDES .shtml을 적용하고,
.sHTML 파일 안의 SSI 지시문이 서버에서 해석되는지 확인한다.
```

### 5-1. 실습용 디렉터리 생성

```bash
sudo mkdir -p "$TEST_DIR"
```

### 5-2. 실습용 SSI 파일 생성

```bash
sudo tee "$TEST_FILE" > /dev/null <<'EOF'
WEB-19 SSI test start
SSI_DATE_LOCAL=<!--#echo var="DATE_LOCAL" -->
SSI_DOCUMENT_NAME=<!--#echo var="DOCUMENT_NAME" -->
WEB-19 SSI test end
EOF
```

파일 확인:

```bash
ls -l "$TEST_FILE"
```

```bash
cat "$TEST_FILE"
```

### 5-3. SSI 모듈 활성화

```bash
sudo a2enmod include
```

이미 활성화되어 있으면 다음과 유사한 메시지가 나올 수 있다.

```text
Module include already enabled
```

### 5-4. 실습용 SSI 설정 생성

```bash
sudo tee "$TEST_CONF" > /dev/null <<EOF
<Directory "$TEST_DIR">
    Options +Includes
    AllowOverride None
    Require all granted
    AddType text/html .shtml
    AddOutputFilter INCLUDES .shtml
</Directory>
EOF
```

취약 재현의 핵심 설정은 다음이다.

```apache
Options +Includes
AddOutputFilter INCLUDES .shtml
```

이 설정은 `$TEST_DIR` 안의 `.shtml` 파일을 SSI 처리 대상으로 만든다.

### 5-5. 실습용 설정 활성화

```bash
sudo a2enconf web-19-ssi-test
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

### 5-8. SSI 해석 확인

```bash
curl -i "$SERVER/web19-ssi/test.shtml"
```

취약 재현 상태에서 기대 결과는 다음과 유사하다.

```text
HTTP/1.1 200 OK

WEB-19 SSI test start
SSI_DATE_LOCAL=Thursday, 18-Jun-2026 ...
SSI_DOCUMENT_NAME=test.shtml
WEB-19 SSI test end
```

중요한 점은 응답에 다음 원문이 그대로 남지 않는 것이다.

```html
<!--#echo var="DATE_LOCAL" -->
```

SSI 지시문이 실제 값으로 바뀌어 응답되면 Apache가 SSI를 해석하고 있다는 의미다.  
PDF 기준으로는 SSI 사용 설정이 활성화된 취약 상태다.

### 5-9. SSI 설정 탐지 확인

```bash
grep -Ri "Options.*Includes\|AddOutputFilter.*INCLUDES\|server-parsed\|\.shtml\|\.shtm\|\.stm" \
/etc/apache2/apache2.conf \
/etc/apache2/sites-enabled/ \
/etc/apache2/sites-available/ \
/etc/apache2/conf-enabled/ \
/etc/apache2/conf-available/ 2>/dev/null | grep -v '^\s*#'
```

취약 재현 상태에서는 다음과 같은 결과가 나와야 한다.

```text
/etc/apache2/conf-enabled/web-19-ssi-test.conf:    Options +Includes
/etc/apache2/conf-enabled/web-19-ssi-test.conf:    AddType text/html .shtml
/etc/apache2/conf-enabled/web-19-ssi-test.conf:    AddOutputFilter INCLUDES .shtml
```

## 6. 조치 방법

조치 핵심은 웹 서비스에서 불필요한 SSI 사용 설정을 제거하는 것이다.

Apache에서는 다음을 제거하거나 비활성화한다.

```apache
Options Includes
Options +Includes
AddOutputFilter INCLUDES .shtml
AddHandler server-parsed .shtml
```

실습에서는 실습용 SSI 설정과 테스트 파일을 제거한다.

### 6-1. 실습용 SSI 설정 비활성화

```bash
sudo a2disconf web-19-ssi-test
```

### 6-2. 실습용 설정 파일 제거

```bash
sudo rm -f "$TEST_CONF"
```

### 6-3. 실습용 SSI 파일 제거

```bash
sudo rm -rf "$TEST_DIR"
```

### 6-4. SSI 모듈 상태 원복

실습 전에 `include_module`이 비활성화되어 있었다면 다시 비활성화한다.

```bash
if [ "$(cat "$INCLUDE_MARKER" 2>/dev/null)" = "no" ]; then
  sudo a2dismod include
fi
```

실습 전부터 `include_module`이 활성화되어 있었다면 다른 설정에서 사용할 수 있으므로 비활성화하지 않는다.  
다만 실제 서비스에서 SSI가 필요하지 않다면 별도로 제거 검토한다.

### 6-5. 실습용 마커 제거

```bash
sudo rm -f "$INCLUDE_MARKER"
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

조치 후에는 SSI 설정이 제거되었고, SSI 파일 경로가 더 이상 동작하지 않는지 확인한다.

### 7-1. SSI 관련 설정 제거 확인

```bash
grep -Ri "Options.*Includes\|AddOutputFilter.*INCLUDES\|server-parsed\|\.shtml\|\.shtm\|\.stm" \
/etc/apache2/apache2.conf \
/etc/apache2/sites-enabled/ \
/etc/apache2/sites-available/ \
/etc/apache2/conf-enabled/ \
/etc/apache2/conf-available/ 2>/dev/null | grep -v '^\s*#'
```

기대 결과는 다음이다.

```text
출력 없음
```

실제 서비스에서 `.shtml`을 사용한다면 출력이 있을 수 있다.  
이 경우 해당 사용 목적과 입력값 반영 여부를 별도 검토해야 한다.

### 7-2. SSI 모듈 상태 확인

```bash
apache2ctl -M | grep include
```

실습 전부터 SSI 모듈이 비활성화되어 있었다면 조치 후에도 출력이 없어야 한다.

```text
출력 없음
```

실습 전부터 활성화되어 있었다면 다음 출력이 남을 수 있다.

```text
include_module (shared)
```

이 경우에도 웹 서비스 경로에 `Options Includes`와 `AddOutputFilter INCLUDES`가 없으면 실제 SSI 사용은 제한된 상태로 볼 수 있다.

### 7-3. SSI 테스트 URL 접근 확인

```bash
curl -i "$SERVER/web19-ssi/test.shtml"
```

조치 후 기대 결과는 다음이다.

```text
HTTP/1.1 404 Not Found
```

중요한 것은 다음처럼 SSI 결과가 더 이상 출력되지 않는 것이다.

```text
SSI_DATE_LOCAL=
SSI_DOCUMENT_NAME=test.shtml
```

### 7-4. Apache 서비스 상태 확인

```bash
systemctl status apache2 --no-pager
```

정상 상태라면 다음과 같이 보여야 한다.

```text
Active: active (running)
```

### 7-5. CARE 서비스 정상 응답 확인

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
TEST_DIR="$APP_ROOT/web19-ssi"
TEST_FILE="$TEST_DIR/test.shtml"
TEST_CONF=/etc/apache2/conf-available/web-19-ssi-test.conf
INCLUDE_MARKER=/tmp/web19-include-module-was-enabled
```

```bash
apache2ctl -S
```

```bash
grep -R "DocumentRoot" /etc/apache2/sites-enabled/ /etc/apache2/sites-available/ 2>/dev/null
```

```bash
apache2ctl -M | grep include
```

```bash
grep -Ri "Options.*Includes\|AddOutputFilter.*INCLUDES\|server-parsed\|\.shtml\|\.shtm\|\.stm" \
/etc/apache2/apache2.conf \
/etc/apache2/sites-enabled/ \
/etc/apache2/sites-available/ \
/etc/apache2/conf-enabled/ \
/etc/apache2/conf-available/ 2>/dev/null | grep -v '^\s*#'
```

```bash
if apache2ctl -M | grep -q "include_module"; then
  echo "yes" | sudo tee "$INCLUDE_MARKER"
else
  echo "no" | sudo tee "$INCLUDE_MARKER"
fi
```

### 8-2. 취약 재현

```bash
sudo mkdir -p "$TEST_DIR"
```

```bash
sudo tee "$TEST_FILE" > /dev/null <<'EOF'
WEB-19 SSI test start
SSI_DATE_LOCAL=<!--#echo var="DATE_LOCAL" -->
SSI_DOCUMENT_NAME=<!--#echo var="DOCUMENT_NAME" -->
WEB-19 SSI test end
EOF
```

```bash
sudo a2enmod include
```

```bash
sudo tee "$TEST_CONF" > /dev/null <<EOF
<Directory "$TEST_DIR">
    Options +Includes
    AllowOverride None
    Require all granted
    AddType text/html .shtml
    AddOutputFilter INCLUDES .shtml
</Directory>
EOF
```

```bash
sudo a2enconf web-19-ssi-test
```

```bash
sudo apachectl configtest
```

```bash
sudo systemctl restart apache2
```

```bash
curl -i "$SERVER/web19-ssi/test.shtml"
```

취약 상태 기대 결과:

```text
HTTP/1.1 200 OK

WEB-19 SSI test start
SSI_DATE_LOCAL=서버가 해석한 날짜 값
SSI_DOCUMENT_NAME=test.shtml
WEB-19 SSI test end
```

설정 탐지 확인:

```bash
grep -Ri "Options.*Includes\|AddOutputFilter.*INCLUDES\|server-parsed\|\.shtml\|\.shtm\|\.stm" \
/etc/apache2/apache2.conf \
/etc/apache2/sites-enabled/ \
/etc/apache2/sites-available/ \
/etc/apache2/conf-enabled/ \
/etc/apache2/conf-available/ 2>/dev/null | grep -v '^\s*#'
```

취약 상태 기대 결과:

```text
/etc/apache2/conf-enabled/web-19-ssi-test.conf:    Options +Includes
/etc/apache2/conf-enabled/web-19-ssi-test.conf:    AddType text/html .shtml
/etc/apache2/conf-enabled/web-19-ssi-test.conf:    AddOutputFilter INCLUDES .shtml
```

### 8-3. 조치 및 복구

```bash
sudo a2disconf web-19-ssi-test
```

```bash
sudo rm -f "$TEST_CONF"
```

```bash
sudo rm -rf "$TEST_DIR"
```

```bash
if [ "$(cat "$INCLUDE_MARKER" 2>/dev/null)" = "no" ]; then
  sudo a2dismod include
fi
```

```bash
sudo rm -f "$INCLUDE_MARKER"
```

```bash
sudo apachectl configtest
```

```bash
sudo systemctl restart apache2
```

### 8-4. 조치 후 확인

```bash
grep -Ri "Options.*Includes\|AddOutputFilter.*INCLUDES\|server-parsed\|\.shtml\|\.shtm\|\.stm" \
/etc/apache2/apache2.conf \
/etc/apache2/sites-enabled/ \
/etc/apache2/sites-available/ \
/etc/apache2/conf-enabled/ \
/etc/apache2/conf-available/ 2>/dev/null | grep -v '^\s*#'
```

기대 결과:

```text
출력 없음
```

```bash
apache2ctl -M | grep include
```

실습 전 비활성 상태였다면 기대 결과:

```text
출력 없음
```

```bash
curl -i "$SERVER/web19-ssi/test.shtml"
```

조치 후 기대 결과:

```text
HTTP/1.1 404 Not Found
```

```bash
systemctl status apache2 --no-pager
```

기대 결과:

```text
Active: active (running)
```

```bash
curl -i "$SERVER/"
```

기대 결과:

```text
HTTP/1.1 200 OK
```

또는:

```text
HTTP/1.1 302 Found
```

### 8-5. 실습 환경 제거 확인

```bash
ls -ld "$TEST_DIR" "$TEST_CONF" "$INCLUDE_MARKER" 2>/dev/null
```

기대 결과:

```text
출력 없음
```

## 9. 증거 정리

### 9-1. 최초 상태 증거

진단 결과 파일의 WEB-19는 PDF WEB-19와 불일치한다.

```text
진단 파일 WEB-19: WebDAV 모듈 미로드
PDF WEB-19: SSI 사용 제한
```

따라서 PDF 기준 WEB-19의 최초 상태는 다음 명령으로 별도 확인한다.

```bash
apache2ctl -M | grep include
```

```bash
grep -Ri "Options.*Includes\|AddOutputFilter.*INCLUDES\|server-parsed\|\.shtml\|\.shtm\|\.stm" \
/etc/apache2/apache2.conf \
/etc/apache2/sites-enabled/ \
/etc/apache2/sites-available/ \
/etc/apache2/conf-enabled/ \
/etc/apache2/conf-available/ 2>/dev/null | grep -v '^\s*#'
```

양호 상태 기대 결과:

```text
include_module 출력 없음
SSI 관련 설정 출력 없음
```

### 9-2. 취약 재현 증거

실습용 취약 설정:

```apache
<Directory "/var/www/care/web19-ssi">
    Options +Includes
    AllowOverride None
    Require all granted
    AddType text/html .shtml
    AddOutputFilter INCLUDES .shtml
</Directory>
```

SSI 요청:

```bash
curl -i "$SERVER/web19-ssi/test.shtml"
```

취약 재현 기대 결과:

```text
HTTP/1.1 200 OK

WEB-19 SSI test start
SSI_DATE_LOCAL=서버가 해석한 날짜 값
SSI_DOCUMENT_NAME=test.shtml
WEB-19 SSI test end
```

이 결과는 `.shtml` 파일 안의 SSI 지시문이 서버에서 해석되고 있음을 의미한다.

### 9-3. 조치 후 증거

SSI 설정 제거 확인:

```bash
grep -Ri "Options.*Includes\|AddOutputFilter.*INCLUDES\|server-parsed\|\.shtml\|\.shtm\|\.stm" \
/etc/apache2/apache2.conf \
/etc/apache2/sites-enabled/ \
/etc/apache2/sites-available/ \
/etc/apache2/conf-enabled/ \
/etc/apache2/conf-available/ 2>/dev/null | grep -v '^\s*#'
```

기대 결과:

```text
출력 없음
```

SSI 테스트 URL 재요청:

```bash
curl -i "$SERVER/web19-ssi/test.shtml"
```

조치 후 기대 결과:

```text
HTTP/1.1 404 Not Found
```

## 10. 판단

|항목|판단|
|---|---|
|최초 진단|진단 파일 기준 불일치, PDF 기준 별도 확인 필요|
|불일치 내용|진단 파일 WEB-19는 WebDAV, PDF WEB-19는 SSI 사용 제한|
|PDF 기준 양호 조건|`include_module`, `Options Includes`, `AddOutputFilter INCLUDES` 등 SSI 설정이 없는 경우|
|실습 처리|`.shtml` 파일과 `Options +Includes` 설정으로 SSI 취약 상태 재현 후 제거|
|조치 전 판단|SSI 지시문이 서버에서 해석되면 취약|
|조치 후 판단|SSI 설정이 제거되고 SSI 테스트 URL이 404 또는 미해석 상태가 되면 양호|
|증거 상태|PDF 기준 수동 확인 결과, 취약 재현 및 조치 후 확인 증거 필요|

`AWS WEB 약점 진단 결과.md`의 WEB-19는 WebDAV 모듈 미로드를 말하고 있어 PDF WEB-19와 항목 내용이 일치하지 않는다. 따라서 해당 자동 진단 결과는 PDF 기준 WEB-19의 직접 근거로 사용할 수 없다.

PDF 기준 WEB-19는 SSI 사용 제한 항목이므로, Apache에서 `include_module`, `Options Includes`, `AddOutputFilter INCLUDES`, `.shtml` 처리 설정을 별도로 확인해야 한다.

실습에서는 `/var/www/care/web19-ssi/test.shtml` 파일과 `Options +Includes` 설정을 사용해 SSI가 서버 측에서 해석되는 취약 상태를 재현한다. 이후 실습용 설정과 파일을 제거하고, 필요하지 않은 경우 `include` 모듈도 원래 상태로 되돌린다.

조치 후 SSI 관련 설정이 탐지되지 않고, `/web19-ssi/test.shtml` 요청이 `404 Not Found`로 처리되거나 SSI 지시문이 더 이상 서버에서 해석되지 않으면 WEB-19는 PDF 기준 조치 후 **양호**로 판단한다.