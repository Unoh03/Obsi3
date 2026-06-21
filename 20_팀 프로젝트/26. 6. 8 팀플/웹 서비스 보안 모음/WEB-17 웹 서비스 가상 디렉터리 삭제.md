---

type: lab  
topic: web-service-security  
source: 주요정보통신기반시설 기술적 취약점 분석·평가 방법 상세가이드  
source_pages:

- 320
    
- 321  
status: draft  
created: 2026-06-18  
tags:
    
- 🏷️과목/웹서비스보안
    
- 🏷️주제/WEB-17
    
- 🏷️주제/Virtual-Directory
    
- 🏷️주제/Apache
    
- 🏷️상태/draft
    

---
# WEB-17 웹 서비스 가상 디렉터리 삭제

## 1. PDF 기준

PDF p.320-321의 WEB-17은 웹 서비스에 **불필요한 가상 디렉터리가 존재하는지** 점검하는 항목이다.

가상 디렉터리는 실제 파일 시스템 경로가 웹 루트 내부에 있지 않아도, 웹 브라우저에서는 웹 사이트의 하위 경로처럼 접근할 수 있게 만드는 설정이다.

예를 들어 Apache에서 다음과 같은 설정이 있으면:

```apache
Alias /virtual /var/www/virtual

<Directory /var/www/virtual>
    Options Indexes FollowSymLinks
    AllowOverride None
    Require all granted
</Directory>
```

사용자는 다음 URL로 `/var/www/virtual` 경로에 접근할 수 있다.

```text
http://서버주소/virtual/
```

즉 실제 경로는 DocumentRoot 밖에 있더라도, Apache의 `Alias` 설정 때문에 웹 경로로 노출된다.

PDF의 판단 기준은 다음과 같다.

|판단|기준|
|---|---|
|양호|불필요한 가상 디렉터리가 존재하지 않는 경우|
|취약|불필요한 가상 디렉터리가 존재하는 경우|

PDF의 Apache 조치 방향은 다음과 같다.

```text
1. Alias 지시자 확인
2. 불필요한 가상 디렉터리 삭제
```

Apache 환경에서 WEB-17은 다음 설정을 중심으로 확인한다.

|설정|의미|
|---|---|
|`Alias`|URL 경로를 실제 파일 시스템 경로에 연결|
|`ScriptAlias`|URL 경로를 CGI 실행 경로에 연결|
|`<Directory>`|Alias 대상 실제 경로의 접근 권한 설정|
|`Require all granted`|해당 경로 접근 허용|
|`Options Indexes`|디렉터리 목록 노출 가능|
|`Options FollowSymLinks`|심볼릭 링크 추적 가능|

WEB-17의 핵심은 다음이다.

```text
웹 서비스에 필요하지 않은 Alias, ScriptAlias, 가상 경로가 남아 있으면 제거한다.
```

## 2. 최초 진단 결과

`AWS WEB 약점 진단 결과.md` 기준 최초 진단 결과는 **양호**이다.

|항목|내용|
|---|---|
|진단 결과|양호|
|진단 근거|`Alias` 지시어로 설정된 불필요한 가상 디렉터리 없음|
|진단 결과 메시지|`No Alias directives found`|
|최초 판단|불필요한 가상 디렉터리가 확인되지 않았으므로 양호|

최초 진단 결과는 다음과 같다.

```text
WEB-17 · 웹서비스 가상 디렉터리 삭제

Alias 지시어로 설정된 불필요한 가상 디렉터리 없음

No Alias directives found
```

따라서 현재 최초 상태에서는 Apache에 불필요한 가상 디렉터리 설정이 없는 것으로 판단한다.

## 3. 현재 서버 상태 해석

WEB-17은 DocumentRoot 자체를 확인하는 WEB-11과 다르다.

WEB-11은 “웹 서비스 기본 경로가 어디인가”를 본다.  
WEB-17은 “기본 경로 외에 추가로 웹에 노출된 가상 경로가 있는가”를 본다.

비교하면 다음과 같다.

|항목|핵심 설정|의미|
|---|---|---|
|WEB-11|`DocumentRoot`|웹 서비스 기본 루트 경로|
|WEB-12|`FollowSymLinks`|웹 루트 내부 링크를 따라 외부 경로 접근 가능 여부|
|WEB-17|`Alias`, `ScriptAlias`|URL 경로를 별도 파일 시스템 경로에 직접 매핑|

Apache에서 다음 설정은 가상 디렉터리에 해당한다.

```apache
Alias /download /srv/download
```

이 설정이 있으면 사용자는 `/download/` URL로 `/srv/download` 경로에 접근할 수 있다.

다음 설정은 CGI 실행 경로를 URL에 연결하므로 더 민감하다.

```apache
ScriptAlias /cgi-bin/ /usr/lib/cgi-bin/
```

`ScriptAlias`는 정상 CGI 서비스에 필요할 수 있으므로 무조건 취약은 아니다.  
하지만 사용하지 않는 CGI 경로가 남아 있으면 WEB-05, WEB-15, WEB-17 관점에서 함께 검토해야 한다.

WEB-17에서 위험한 상태는 다음과 같다.

```text
1. 사용하지 않는 Alias가 남아 있음
2. Alias 대상 경로가 DocumentRoot 밖의 민감한 경로임
3. Alias 대상 경로에 Require all granted가 설정되어 있음
4. Alias 대상 경로에 Indexes 또는 FollowSymLinks가 함께 설정되어 있음
5. ScriptAlias로 불필요한 CGI 실행 경로가 노출됨
```

현재 진단 결과는 `No Alias directives found`이므로 최초 상태는 양호하다.  
다만 PDF 내용을 실습하기 위해 불필요한 Alias를 추가하여 취약 상태를 재현한다.

## 4. 실습 전 확인

실습을 시작하기 전에 현재 Apache 가상호스트, Alias 설정, 관련 모듈 상태를 확인한다.

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
VIRTUAL_DIR=/tmp/web17-virtual
TEST_CONF=/etc/apache2/conf-available/web-17-alias-test.conf
```

현재 서버의 DocumentRoot가 다르면 `APP_ROOT` 값을 실제 경로로 바꾼다.

### 4-3. 현재 Alias 설정 확인

```bash
grep -R "^[[:space:]]*Alias\|^[[:space:]]*ScriptAlias" \
/etc/apache2/apache2.conf \
/etc/apache2/sites-enabled/ \
/etc/apache2/sites-available/ \
/etc/apache2/conf-enabled/ \
/etc/apache2/conf-available/ 2>/dev/null | grep -v '^\s*#'
```

최초 양호 상태라면 불필요한 Alias가 없어야 한다.

```text
출력 없음
```

단, Apache 기본 CGI 설정 때문에 다음과 같은 `ScriptAlias`가 출력될 수 있다.

```apache
ScriptAlias /cgi-bin/ /usr/lib/cgi-bin/
```

이 경우 실제 서비스에서 CGI를 사용하는지 확인한다. 사용하지 않는다면 WEB-05, WEB-15, WEB-17 관점에서 제거 후보가 된다.

### 4-4. alias 모듈 확인

```bash
apache2ctl -M | grep alias
```

일반적인 Apache 환경에서는 다음처럼 출력된다.

```text
alias_module (shared)
```

`Alias` 기능은 Apache 기본 구성에서 자주 사용되므로, 모듈 존재 자체가 취약은 아니다.  
불필요한 `Alias` 설정이 존재하는지가 핵심이다.

## 5. 취약 재현

이 항목은 최초 진단 결과가 양호이므로, PDF 내용을 실습하기 위해 의도적으로 불필요한 가상 디렉터리를 추가한다.

> 주의: 이 절차는 격리된 실습 서버에서만 수행한다.  
> 실제 민감 경로를 Alias 대상으로 사용하지 않는다.  
> 실습용 `/tmp/web17-virtual` 경로만 사용한다.  
> 증거 확보 후 즉시 제거한다.

취약 재현의 핵심은 다음이다.

```text
DocumentRoot 밖의 디렉터리를 Alias로 웹 경로에 연결하고,
외부에서 해당 경로에 접근 가능한지 확인한다.
```

### 5-1. 실습용 가상 디렉터리 실제 경로 생성

```bash
mkdir -p "$VIRTUAL_DIR"
```

### 5-2. 실습용 파일 생성

```bash
cat > "$VIRTUAL_DIR/index.html" <<'EOF'
WEB-17 virtual directory exposed
EOF
```

파일을 확인한다.

```bash
ls -l "$VIRTUAL_DIR/index.html"
```

### 5-3. 실습용 Alias 설정 생성

```bash
sudo tee "$TEST_CONF" > /dev/null <<EOF
Alias /web17-virtual/ "$VIRTUAL_DIR/"

<Directory "$VIRTUAL_DIR">
    Options Indexes FollowSymLinks
    AllowOverride None
    Require all granted
</Directory>
EOF
```

이 설정은 `/web17-virtual/` URL을 실제 파일 시스템의 `/tmp/web17-virtual/` 경로에 연결한다.

취약 재현의 핵심 설정은 다음이다.

```apache
Alias /web17-virtual/ "/tmp/web17-virtual/"
```

그리고 다음 설정은 외부 접근을 허용한다.

```apache
Require all granted
```

### 5-4. 실습용 설정 활성화

```bash
sudo a2enconf web-17-alias-test
```

### 5-5. Apache 설정 문법 검사

```bash
sudo apachectl configtest
```

정상이라면 다음 결과가 나와야 한다.

```text
Syntax OK
```

### 5-6. Apache restart

```bash
sudo systemctl restart apache2
```

### 5-7. 가상 디렉터리 접근 확인

```bash
curl -i "$SERVER/web17-virtual/"
```

취약 재현 상태에서 기대 결과는 다음과 같다.

```text
HTTP/1.1 200 OK

WEB-17 virtual directory exposed
```

이 결과는 DocumentRoot 밖의 `/tmp/web17-virtual` 경로가 Apache Alias를 통해 외부 웹 경로로 노출되었음을 의미한다.

PDF 기준으로는 불필요한 가상 디렉터리가 존재하는 취약 상태다.

### 5-8. Alias 설정 탐지 확인

```bash
grep -R "^[[:space:]]*Alias\|^[[:space:]]*ScriptAlias" \
/etc/apache2/apache2.conf \
/etc/apache2/sites-enabled/ \
/etc/apache2/sites-available/ \
/etc/apache2/conf-enabled/ \
/etc/apache2/conf-available/ 2>/dev/null | grep -v '^\s*#'
```

취약 재현 상태에서는 다음과 같은 결과가 나와야 한다.

```text
/etc/apache2/conf-enabled/web-17-alias-test.conf:Alias /web17-virtual/ "/tmp/web17-virtual/"
```

## 6. 조치 방법

조치 핵심은 불필요한 가상 디렉터리 설정을 제거하는 것이다.

실습에서는 `web-17-alias-test.conf`를 비활성화하고, 테스트 파일을 삭제한다.

### 6-1. 실습용 Alias 설정 비활성화

```bash
sudo a2disconf web-17-alias-test
```

### 6-2. 실습용 Alias 설정 파일 제거

```bash
sudo rm -f "$TEST_CONF"
```

### 6-3. 실습용 가상 디렉터리 실제 경로 제거

```bash
rm -rf "$VIRTUAL_DIR"
```

### 6-4. Apache 설정 문법 검사

```bash
sudo apachectl configtest
```

정상이라면 다음 결과가 나와야 한다.

```text
Syntax OK
```

### 6-5. Apache restart

```bash
sudo systemctl restart apache2
```

### 6-6. 운영 Alias 설정 검토

실제 운영 서버에서 Alias가 확인되면 다음 기준으로 판단한다.

|확인 항목|판단|
|---|---|
|서비스에 필요한 Alias인가|필요하면 유지, 불필요하면 제거|
|대상 경로가 DocumentRoot 밖인가|외부 노출 필요성 확인|
|`Require all granted`가 필요한가|접근 범위 최소화|
|`Options Indexes`가 있는가|디렉터리 목록 노출 위험|
|`FollowSymLinks`가 있는가|WEB-12와 함께 검토|
|`ScriptAlias`인가|WEB-05, WEB-15와 함께 검토|

불필요한 Alias는 설정 파일에서 제거한다.

```apache
# 제거 대상 예시
Alias /unused/ "/srv/unused/"
```

필요한 Alias는 목적과 대상 경로를 문서화한다.

```text
필요한 Alias는 왜 필요한지, 어느 경로를 노출하는지, 접근 제한이 어떻게 되어 있는지 기록한다.
```

## 7. 조치 후 확인

조치 후에는 Alias 설정이 제거되었고, 가상 디렉터리 URL로 접근할 수 없는지 확인한다.

### 7-1. Alias 설정 제거 확인

```bash
grep -R "^[[:space:]]*Alias\|^[[:space:]]*ScriptAlias" \
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

단, 실제 서비스에 필요한 `ScriptAlias`나 `Alias`가 있다면 출력될 수 있다.  
이 경우 필요한 설정인지 별도 검토하고, 불필요한 설정만 제거한다.

### 7-2. 실습 설정 파일 제거 확인

```bash
ls -l "$TEST_CONF" 2>/dev/null
```

기대 결과는 다음이다.

```text
출력 없음
```

### 7-3. 실습 가상 디렉터리 제거 확인

```bash
ls -ld "$VIRTUAL_DIR" 2>/dev/null
```

기대 결과는 다음이다.

```text
출력 없음
```

### 7-4. 가상 디렉터리 URL 접근 차단 확인

```bash
curl -i "$SERVER/web17-virtual/"
```

조치 후 기대 결과는 다음 중 하나다.

```text
HTTP/1.1 404 Not Found
```

또는:

```text
HTTP/1.1 403 Forbidden
```

중요한 것은 다음 문자열이 더 이상 출력되지 않는 것이다.

```text
WEB-17 virtual directory exposed
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

실습 중에는 아래 순서대로 진행한다.

### 8-1. 현재 상태 확인

```bash
APP_ROOT=/var/www/care
SERVER=http://172.168.10.10
VIRTUAL_DIR=/tmp/web17-virtual
TEST_CONF=/etc/apache2/conf-available/web-17-alias-test.conf
```

```bash
apache2ctl -S
```

```bash
grep -R "DocumentRoot" /etc/apache2/sites-enabled/ /etc/apache2/sites-available/ 2>/dev/null
```

```bash
grep -R "^[[:space:]]*Alias\|^[[:space:]]*ScriptAlias" \
/etc/apache2/apache2.conf \
/etc/apache2/sites-enabled/ \
/etc/apache2/sites-available/ \
/etc/apache2/conf-enabled/ \
/etc/apache2/conf-available/ 2>/dev/null | grep -v '^\s*#'
```

```bash
apache2ctl -M | grep alias
```

### 8-2. 취약 재현

```bash
mkdir -p "$VIRTUAL_DIR"
```

```bash
cat > "$VIRTUAL_DIR/index.html" <<'EOF'
WEB-17 virtual directory exposed
EOF
```

```bash
ls -l "$VIRTUAL_DIR/index.html"
```

```bash
sudo tee "$TEST_CONF" > /dev/null <<EOF
Alias /web17-virtual/ "$VIRTUAL_DIR/"

<Directory "$VIRTUAL_DIR">
    Options Indexes FollowSymLinks
    AllowOverride None
    Require all granted
</Directory>
EOF
```

```bash
sudo a2enconf web-17-alias-test
```

```bash
sudo apachectl configtest
```

```bash
sudo systemctl restart apache2
```

```bash
curl -i "$SERVER/web17-virtual/"
```

취약 상태 기대 결과:

```text
HTTP/1.1 200 OK

WEB-17 virtual directory exposed
```

설정 탐지 확인:

```bash
grep -R "^[[:space:]]*Alias\|^[[:space:]]*ScriptAlias" \
/etc/apache2/apache2.conf \
/etc/apache2/sites-enabled/ \
/etc/apache2/sites-available/ \
/etc/apache2/conf-enabled/ \
/etc/apache2/conf-available/ 2>/dev/null | grep -v '^\s*#'
```

취약 상태 기대 결과:

```text
/etc/apache2/conf-enabled/web-17-alias-test.conf:Alias /web17-virtual/ "/tmp/web17-virtual/"
```

### 8-3. 조치 및 복구

```bash
sudo a2disconf web-17-alias-test
```

```bash
sudo rm -f "$TEST_CONF"
```

```bash
rm -rf "$VIRTUAL_DIR"
```

```bash
sudo apachectl configtest
```

```bash
sudo systemctl restart apache2
```

### 8-4. 조치 후 확인

```bash
grep -R "^[[:space:]]*Alias\|^[[:space:]]*ScriptAlias" \
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
ls -l "$TEST_CONF" 2>/dev/null
```

기대 결과:

```text
출력 없음
```

```bash
ls -ld "$VIRTUAL_DIR" 2>/dev/null
```

기대 결과:

```text
출력 없음
```

```bash
curl -i "$SERVER/web17-virtual/"
```

조치 후 기대 결과:

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

## 9. 증거 정리

### 9-1. 최초 상태 증거

최초 진단 결과:

```text
WEB-17 · 웹서비스 가상 디렉터리 삭제

Alias 지시어로 설정된 불필요한 가상 디렉터리 없음

No Alias directives found
```

Alias 설정 확인 명령어:

```bash
grep -R "^[[:space:]]*Alias\|^[[:space:]]*ScriptAlias" \
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

실습용 Alias 설정:

```apache
Alias /web17-virtual/ "/tmp/web17-virtual/"

<Directory "/tmp/web17-virtual">
    Options Indexes FollowSymLinks
    AllowOverride None
    Require all granted
</Directory>
```

가상 디렉터리 요청:

```bash
curl -i "$SERVER/web17-virtual/"
```

취약 재현 기대 결과:

```text
HTTP/1.1 200 OK

WEB-17 virtual directory exposed
```

이 결과는 DocumentRoot 밖의 디렉터리가 Apache Alias를 통해 외부 웹 경로로 노출되었음을 의미한다.

### 9-3. 조치 후 증거

Alias 설정 제거 확인:

```bash
grep -R "^[[:space:]]*Alias\|^[[:space:]]*ScriptAlias" \
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

가상 디렉터리 재요청:

```bash
curl -i "$SERVER/web17-virtual/"
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
|최초 진단|양호|
|진단 근거|`Alias` 지시어로 설정된 불필요한 가상 디렉터리 없음|
|실습 처리|`/tmp/web17-virtual`을 `/web17-virtual/` Alias로 노출하여 취약 상태 재현 후 제거|
|조치 전 판단|불필요한 Alias 경로가 외부에서 접근 가능하면 취약|
|조치 후 판단|불필요한 Alias 설정이 제거되고 URL 접근이 404 또는 403으로 처리되면 양호|
|증거 상태|최초 진단 결과 확보, 취약 재현 및 조치 후 접근 증거 필요|

현재 서버는 최초 진단 기준으로 `Alias` 지시어로 설정된 불필요한 가상 디렉터리가 확인되지 않았으므로 WEB-17은 **양호**로 판단한다.

다만 PDF의 취약 조건을 실습하기 위해 `/tmp/web17-virtual` 경로를 `/web17-virtual/` URL에 Alias로 연결하면, DocumentRoot 밖의 디렉터리가 웹 경로로 노출되는 취약 상태를 재현할 수 있다.

조치는 불필요한 Alias 설정을 비활성화하고, 실습용 설정 파일과 대상 디렉터리를 제거하는 방식으로 수행한다.

조치 후 Alias 설정 탐지 결과가 없고, `/web17-virtual/` 요청이 `404 Not Found` 또는 `403 Forbidden`으로 처리되며, `WEB-17 virtual directory exposed` 문자열이 더 이상 출력되지 않으면 WEB-17은 조치 후 **양호**로 판단한다.