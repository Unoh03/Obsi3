---

type: lab  
topic: web-service-security  
source: 주요정보통신기반시설 기술적 취약점 분석·평가 방법 상세가이드  
source_pages:

- 313
    
- 314
    
- 315  
status: draft  
created: 2026-06-18  
tags:
    
- 🏷️과목/웹서비스보안
    
- 🏷️주제/WEB-15
    
- 🏷️주제/Script-Mapping
    
- 🏷️주제/Apache
    
- 🏷️상태/draft
    

---
 # WEB-15 웹 서비스의 불필요한 스크립트 매핑 제거

## 1. PDF 기준

PDF p.313-315의 WEB-15는 웹 서비스에 **불필요한 스크립트 매핑이 존재하는지** 점검하는 항목이다.

스크립트 매핑은 웹 서버에서 특정 확장자나 URL 경로를 특정 처리기, 실행 엔진, 스크립트 프로그램에 연결하는 설정이다.

예를 들어 다음과 같은 구조다.

```text
요청 확장자 또는 URL 경로
→ 웹 서버의 특정 처리기
→ 스크립트 실행 또는 특수 처리
```

PDF에서는 Tomcat, IIS, JEUS를 중심으로 설명한다.

|환경|예시|
|---|---|
|Tomcat|`servlet-mapping`|
|IIS|처리기 매핑, `.htr`, `.idc`, `.shtml`, `.printer`, `.ida`, `.idq`, `.htw` 등|
|JEUS|`web.xml`의 `servlet-mapping`|

PDF의 판단 기준은 다음과 같다.

|판단|기준|
|---|---|
|양호|불필요한 스크립트 매핑이 존재하지 않는 경우|
|취약|불필요한 스크립트 매핑이 존재하는 경우|

PDF의 보안 위협은 다음과 같다.

```text
불필요한 스크립트 매핑이 남아 있으면
버퍼 오버플로우, 서비스 거부 공격, XSS 등
불필요한 처리기 또는 구버전 기능을 통한 공격 위험이 증가한다.
```

Apache 환경에서는 PDF의 IIS 처리기 매핑을 다음 설정들과 대응해서 해석한다.

|Apache 설정|의미|
|---|---|
|`AddHandler`|특정 확장자를 특정 핸들러에 연결|
|`AddType`|특정 확장자를 특정 MIME 타입에 연결|
|`Action`|특정 핸들러 요청을 별도 CGI 프로그램으로 전달|
|`ScriptAlias`|특정 URL 경로를 CGI 실행 경로에 매핑|
|`SetHandler`|특정 디렉터리나 파일에 처리기 강제 지정|

Apache에서 불필요한 스크립트 매핑이란, 현재 서비스에 필요하지 않은 확장자나 경로가 실행 가능한 처리기로 연결되어 있는 상태를 말한다.

예를 들면 다음과 같은 설정이다.

```apache
AddHandler cgi-script .web15
```

이 설정이 활성화되면 `.web15` 확장자를 가진 파일이 단순 정적 파일이 아니라 CGI 스크립트처럼 실행될 수 있다.

## 2. 최초 진단 결과

`AWS WEB 약점 진단 결과.md` 기준 최초 진단 결과는 **양호**이다.

|항목|내용|
|---|---|
|진단 결과|양호|
|진단 근거|`AddHandler`, `AddType`, `Action`, `ScriptAlias` 등 불필요한 핸들러 매핑 없음|
|진단 결과 메시지|`No script handler mappings found`|
|최초 판단|불필요한 스크립트 매핑이 확인되지 않았으므로 양호|

최초 진단 결과는 다음과 같다.

```text
WEB-15 · 불필요한 스크립트 매핑 제거

AddHandler, AddType, Action, ScriptAlias 등 불필요한 핸들러 없음

No script handler mappings found
```

따라서 현재 최초 상태에서는 Apache에 불필요한 스크립트 매핑이 없는 것으로 판단한다.

## 3. 현재 서버 상태 해석

WEB-15는 “스크립트 실행이 가능한가”만 보는 항목이 아니다. 핵심은 **필요하지 않은 확장자나 경로가 실행 처리기에 연결되어 있는지**다.

Apache에서 확인해야 할 대표 설정은 다음과 같다.

```text
AddHandler
AddType
Action
ScriptAlias
SetHandler
```

안전한 상태는 다음과 같다.

```text
현재 서비스에 필요한 PHP 처리 설정 외에
불필요한 확장자 실행 매핑이 없음
```

취약한 상태는 다음과 같다.

```text
사용하지 않는 확장자나 경로가
CGI, PHP, SSI, 프린터, 레거시 핸들러 등으로 매핑되어 있음
```

예를 들어 다음 설정은 위험할 수 있다.

```apache
AddHandler cgi-script .old
AddHandler cgi-script .bak
AddHandler cgi-script .web15
ScriptAlias /unused-cgi/ /var/www/unused-cgi/
Action unused-handler /cgi-bin/unused-handler
```

특히 다음과 같은 확장자는 불필요하게 실행 처리기로 연결하지 않아야 한다.

```text
.bak
.old
.inc
.txt
.tmp
.web15
사용하지 않는 레거시 확장자
```

이 항목은 WEB-05, WEB-07, WEB-13과 연결된다.

|연결 항목|연결 이유|
|---|---|
|WEB-05|지정하지 않은 CGI 실행 제한과 직접 연결됨|
|WEB-07|백업 파일이나 테스트 파일이 실행 매핑되면 위험 증가|
|WEB-13|DB 연결 파일이나 설정 파일이 스크립트 매핑으로 노출될 수 있음|

현재 진단 결과는 불필요한 핸들러 매핑이 발견되지 않았으므로 양호하다.  
다만 PDF 내용을 실습하기 위해 테스트 확장자 `.web15`를 CGI 처리기로 매핑하여 취약 상태를 재현한다.

## 4. 실습 전 확인

실습을 시작하기 전에 현재 Apache 환경, DocumentRoot, 스크립트 매핑 설정을 확인한다.

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
TEST_DIR="$APP_ROOT/web15-script-map"
TEST_SCRIPT="$TEST_DIR/test.web15"
TEST_CONF="/etc/apache2/conf-available/web-15-script-map-test.conf"
CGID_MARKER=/tmp/web15-cgid-was-enabled
```

현재 서버의 DocumentRoot가 다르면 `APP_ROOT` 값을 실제 경로로 바꾼다.

### 4-3. 현재 스크립트 매핑 확인

```bash
grep -R "AddHandler\|AddType\|Action\|ScriptAlias\|SetHandler" \
/etc/apache2/apache2.conf \
/etc/apache2/sites-enabled/ \
/etc/apache2/sites-available/ \
/etc/apache2/conf-enabled/ \
/etc/apache2/conf-available/ 2>/dev/null | grep -v '^\s*#'
```

최초 양호 상태라면 불필요한 매핑이 없어야 한다.

```text
출력 없음
```

단, 실제 서비스에 필요한 PHP 처리기나 FastCGI 설정이 출력될 수 있다.  
그 경우에는 필요한 설정인지 별도 판단한다.

### 4-4. CGI 관련 모듈 확인

```bash
apache2ctl -M | grep -E "cgi|cgid"
```

출력이 없으면 CGI 실행 모듈이 비활성화된 상태다.

```text
출력 없음
```

실습에서는 `.web15` 확장자를 CGI로 매핑하기 위해 `cgid` 모듈을 사용할 수 있다.  
실습 전 모듈 상태를 기록한다.

```bash
if apache2ctl -M | grep -q "cgid_module"; then
  echo "yes" | sudo tee "$CGID_MARKER"
else
  echo "no" | sudo tee "$CGID_MARKER"
fi
```

기록 결과 확인:

```bash
cat "$CGID_MARKER"
```

## 5. 취약 재현

이 항목은 최초 진단 결과가 양호이므로, PDF 내용을 실습하기 위해 의도적으로 불필요한 스크립트 매핑을 추가한다.

> 주의: 이 절차는 격리된 실습 서버에서만 수행한다.  
> 실제 서비스 확장자나 운영 파일에 실행 매핑을 추가하지 않는다.  
> 실습용 확장자 `.web15`와 실습용 디렉터리만 사용한다.  
> 증거 확보 후 즉시 제거한다.

취약 재현의 핵심은 다음이다.

```text
원래 단순 파일이어야 할 .web15 확장자를 CGI 실행 처리기에 매핑하고,
외부 요청으로 해당 파일이 실행되는지 확인한다.
```

### 5-1. 실습용 디렉터리 생성

```bash
sudo mkdir -p "$TEST_DIR"
```

### 5-2. 실습용 스크립트 생성

```bash
sudo tee "$TEST_SCRIPT" > /dev/null <<'EOF'
#!/bin/sh
echo "Content-Type: text/plain"
echo
echo "WEB-15 script mapping executed"
EOF
```

실행 권한을 부여한다.

```bash
sudo chmod 755 "$TEST_SCRIPT"
```

파일을 확인한다.

```bash
ls -l "$TEST_SCRIPT"
```

### 5-3. CGI 모듈 활성화

```bash
sudo a2enmod cgid
```

이미 활성화되어 있으면 다음과 유사한 메시지가 나올 수 있다.

```text
Module cgid already enabled
```

### 5-4. 실습용 스크립트 매핑 설정 생성

```bash
sudo tee "$TEST_CONF" > /dev/null <<EOF
<Directory $TEST_DIR>
    Options +ExecCGI
    AddHandler cgi-script .web15
    Require all granted
</Directory>
EOF
```

이 설정은 `$TEST_DIR` 안에서 `.web15` 확장자를 CGI 스크립트로 실행하도록 매핑한다.

여기서 핵심 취약 설정은 다음이다.

```apache
AddHandler cgi-script .web15
```

### 5-5. 실습용 설정 활성화

```bash
sudo a2enconf web-15-script-map-test
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

### 5-8. 스크립트 매핑 실행 확인

```bash
curl -i "$SERVER/web15-script-map/test.web15"
```

취약 재현 상태에서 기대 결과는 다음과 같다.

```text
HTTP/1.1 200 OK

WEB-15 script mapping executed
```

이 결과는 `.web15` 확장자가 단순 파일로 제공된 것이 아니라, Apache의 CGI 스크립트 매핑에 의해 실행되었음을 의미한다.

PDF 기준으로는 불필요한 스크립트 매핑이 존재하는 취약 상태다.

### 5-9. 설정 탐지 확인

```bash
grep -R "AddHandler\|AddType\|Action\|ScriptAlias\|SetHandler" \
/etc/apache2/apache2.conf \
/etc/apache2/sites-enabled/ \
/etc/apache2/sites-available/ \
/etc/apache2/conf-enabled/ \
/etc/apache2/conf-available/ 2>/dev/null | grep -v '^\s*#'
```

취약 재현 상태에서는 다음과 같은 설정이 탐지되어야 한다.

```text
/etc/apache2/conf-enabled/web-15-script-map-test.conf:    AddHandler cgi-script .web15
```

## 6. 조치 방법

조치 핵심은 불필요한 스크립트 매핑을 제거하는 것이다.

실습에서는 `web-15-script-map-test.conf` 설정과 테스트 스크립트를 제거한다.

### 6-1. 실습용 설정 비활성화

```bash
sudo a2disconf web-15-script-map-test
```

### 6-2. 실습용 설정 파일 제거

```bash
sudo rm -f "$TEST_CONF"
```

### 6-3. 실습용 스크립트 디렉터리 제거

```bash
sudo rm -rf "$TEST_DIR"
```

### 6-4. 실습용 CGI 모듈 상태 복구

실습 전에 `cgid` 모듈이 비활성화되어 있었다면 다시 비활성화한다.

```bash
if [ "$(cat "$CGID_MARKER" 2>/dev/null)" = "no" ]; then
  sudo a2dismod cgid
fi
```

실습 전부터 `cgid` 모듈이 활성화되어 있었다면 다른 기능에서 사용할 수 있으므로 비활성화하지 않는다.

### 6-5. 실습용 마커 제거

```bash
sudo rm -f "$CGID_MARKER"
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

조치 후에는 불필요한 스크립트 매핑이 제거되었고, `.web15` 스크립트가 더 이상 실행되지 않는지 확인한다.

### 7-1. 스크립트 매핑 제거 확인

```bash
grep -R "AddHandler\|AddType\|Action\|ScriptAlias\|SetHandler" \
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

단, 실제 서비스에 필요한 PHP 처리 설정이 출력될 수 있다.  
필요한 설정은 예외로 문서화하고, 사용하지 않는 확장자 매핑만 제거한다.

### 7-2. 테스트 파일 접근 차단 확인

```bash
curl -i "$SERVER/web15-script-map/test.web15"
```

조치 후 기대 결과는 다음이다.

```text
HTTP/1.1 404 Not Found
```

중요한 것은 다음 문자열이 더 이상 출력되지 않는 것이다.

```text
WEB-15 script mapping executed
```

### 7-3. CGI 모듈 상태 확인

```bash
apache2ctl -M | grep -E "cgi|cgid"
```

실습 전 `cgid`가 비활성화였고 실습 후 비활성화했다면 출력이 없어야 한다.

```text
출력 없음
```

실습 전부터 `cgid`가 활성화되어 있었다면 출력이 남을 수 있다.

```text
cgid_module (shared)
```

이 경우에는 다른 서비스에서 필요한 모듈인지 확인한다.

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
TEST_DIR="$APP_ROOT/web15-script-map"
TEST_SCRIPT="$TEST_DIR/test.web15"
TEST_CONF="/etc/apache2/conf-available/web-15-script-map-test.conf"
CGID_MARKER=/tmp/web15-cgid-was-enabled
```

```bash
apache2ctl -S
```

```bash
grep -R "DocumentRoot" /etc/apache2/sites-enabled/ /etc/apache2/sites-available/ 2>/dev/null
```

```bash
grep -R "AddHandler\|AddType\|Action\|ScriptAlias\|SetHandler" \
/etc/apache2/apache2.conf \
/etc/apache2/sites-enabled/ \
/etc/apache2/sites-available/ \
/etc/apache2/conf-enabled/ \
/etc/apache2/conf-available/ 2>/dev/null | grep -v '^\s*#'
```

```bash
apache2ctl -M | grep -E "cgi|cgid"
```

```bash
if apache2ctl -M | grep -q "cgid_module"; then
  echo "yes" | sudo tee "$CGID_MARKER"
else
  echo "no" | sudo tee "$CGID_MARKER"
fi
```

```bash
cat "$CGID_MARKER"
```

### 8-2. 취약 재현

```bash
sudo mkdir -p "$TEST_DIR"
```

```bash
sudo tee "$TEST_SCRIPT" > /dev/null <<'EOF'
#!/bin/sh
echo "Content-Type: text/plain"
echo
echo "WEB-15 script mapping executed"
EOF
```

```bash
sudo chmod 755 "$TEST_SCRIPT"
```

```bash
sudo a2enmod cgid
```

```bash
sudo tee "$TEST_CONF" > /dev/null <<EOF
<Directory $TEST_DIR>
    Options +ExecCGI
    AddHandler cgi-script .web15
    Require all granted
</Directory>
EOF
```

```bash
sudo a2enconf web-15-script-map-test
```

```bash
sudo apachectl configtest
```

```bash
sudo systemctl restart apache2
```

```bash
curl -i "$SERVER/web15-script-map/test.web15"
```

취약 상태 기대 결과:

```text
HTTP/1.1 200 OK

WEB-15 script mapping executed
```

설정 탐지 확인:

```bash
grep -R "AddHandler\|AddType\|Action\|ScriptAlias\|SetHandler" \
/etc/apache2/apache2.conf \
/etc/apache2/sites-enabled/ \
/etc/apache2/sites-available/ \
/etc/apache2/conf-enabled/ \
/etc/apache2/conf-available/ 2>/dev/null | grep -v '^\s*#'
```

취약 상태 기대 결과:

```text
/etc/apache2/conf-enabled/web-15-script-map-test.conf:    AddHandler cgi-script .web15
```

### 8-3. 조치 및 복구

```bash
sudo a2disconf web-15-script-map-test
```

```bash
sudo rm -f "$TEST_CONF"
```

```bash
sudo rm -rf "$TEST_DIR"
```

```bash
if [ "$(cat "$CGID_MARKER" 2>/dev/null)" = "no" ]; then
  sudo a2dismod cgid
fi
```

```bash
sudo rm -f "$CGID_MARKER"
```

```bash
sudo apachectl configtest
```

```bash
sudo systemctl restart apache2
```

### 8-4. 조치 후 확인

```bash
grep -R "AddHandler\|AddType\|Action\|ScriptAlias\|SetHandler" \
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
curl -i "$SERVER/web15-script-map/test.web15"
```

조치 후 기대 결과:

```text
HTTP/1.1 404 Not Found
```

```bash
apache2ctl -M | grep -E "cgi|cgid"
```

```bash
systemctl status apache2 --no-pager
```

```bash
curl -i "$SERVER/"
```

### 8-5. 실습 환경 제거 확인

```bash
ls -ld "$TEST_DIR" "$TEST_CONF" "$CGID_MARKER" 2>/dev/null
```

기대 결과:

```text
출력 없음
```

## 9. 증거 정리

### 9-1. 최초 상태 증거

최초 진단 결과:

```text
WEB-15 · 불필요한 스크립트 매핑 제거
AddHandler, AddType, Action, ScriptAlias 등 불필요한 핸들러 없음

No script handler mappings found
```

스크립트 매핑 확인 명령어:

```bash
grep -R "AddHandler\|AddType\|Action\|ScriptAlias\|SetHandler" \
/etc/apache2/apache2.conf \
/etc/apache2/sites-enabled/ \
/etc/apache2/sites-available/ \
/etc/apache2/conf-enabled/ \
/etc/apache2/conf-available/ 2>/dev/null | grep -v '^\s*#'
```

양호 상태 기대 결과:

```text
출력 없음
```

### 9-2. 취약 재현 증거

실습용 취약 설정:

```apache
<Directory /var/www/care/web15-script-map>
    Options +ExecCGI
    AddHandler cgi-script .web15
    Require all granted
</Directory>
```

스크립트 실행 요청:

```bash
curl -i "$SERVER/web15-script-map/test.web15"
```

취약 재현 기대 결과:

```text
HTTP/1.1 200 OK

WEB-15 script mapping executed
```

이 결과는 `.web15` 확장자가 불필요하게 CGI 처리기에 매핑되어 실행되었음을 의미한다.

### 9-3. 조치 후 증거

스크립트 매핑 제거 확인:

```bash
grep -R "AddHandler\|AddType\|Action\|ScriptAlias\|SetHandler" \
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

스크립트 URL 재요청:

```bash
curl -i "$SERVER/web15-script-map/test.web15"
```

조치 후 기대 결과:

```text
HTTP/1.1 404 Not Found
```

## 10. 판단

|항목|판단|
|---|---|
|최초 진단|양호|
|진단 근거|`AddHandler`, `AddType`, `Action`, `ScriptAlias` 등 불필요한 핸들러 매핑 없음|
|실습 처리|`.web15` 확장자를 CGI 처리기로 매핑하여 취약 상태 재현 후 제거|
|조치 전 판단|불필요한 확장자가 실행 처리기에 매핑되어 실행되면 취약|
|조치 후 판단|불필요한 스크립트 매핑이 제거되고 테스트 URL이 404로 처리되면 양호|
|증거 상태|최초 진단 결과 확보, 취약 재현 및 조치 후 접근 증거 필요|

현재 서버는 최초 진단 기준으로 `AddHandler`, `AddType`, `Action`, `ScriptAlias` 등 불필요한 핸들러 매핑이 확인되지 않았으므로 WEB-15는 **양호**로 판단한다.

다만 PDF의 취약 조건을 실습하기 위해 `.web15` 확장자를 `cgi-script` 처리기에 연결하면, 원래 단순 파일이어야 할 확장자가 서버에서 실행되는 취약 상태를 재현할 수 있다.

조치는 실습용 `AddHandler cgi-script .web15` 설정과 테스트 파일을 제거하는 방식으로 수행한다. 조치 후 불필요한 스크립트 매핑이 탐지되지 않고, `/web15-script-map/test.web15` 요청이 `404 Not Found`로 처리되면 WEB-15는 조치 후 **양호**로 판단한다.