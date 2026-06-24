---
type: lab  
topic: web-service-security  
source: 주요정보통신기반시설 기술적 취약점 분석·평가 방법 상세가이드  
source_pages:

- 303
    
- 304  
status: draft  
created: 2026-06-18  
tags:
    
- 🏷️과목/웹서비스보안
    
- 🏷️주제/WEB-11
    
- 🏷️주제/DocumentRoot
    
- 🏷️주제/Apache
    
- 🏷️상태/draft
    

---
---

type: lab  
topic: web-service-security  
source: 주요정보통신기반시설 기술적 취약점 분석·평가 방법 상세가이드  
source_pages:

- 303
    
- 304  
    status: draft  
    created: 2026-06-18  
    tags:
    
- 🏷️과목/웹서비스보안
    
- 🏷️주제/WEB-11
    
- 🏷️주제/DocumentRoot
    
- 🏷️주제/Apache
    
- 🏷️상태/draft
    

---

# WEB-11 웹 서비스 경로 설정

## 1. PDF 기준

PDF p.303-304의 WEB-11은 웹 서버에 설정된 **웹 서비스 경로가 기본 경로와 분리되어 있는지** 점검하는 항목이다.

Apache에서는 웹 서비스의 루트 경로를 보통 `DocumentRoot`로 설정한다.  
`DocumentRoot`는 클라이언트가 웹 서버에 요청했을 때 실제 파일을 찾는 기준 디렉터리다.

예를 들어 다음 설정이 있다면:

```apache
DocumentRoot /var/www/care
```

웹 서버는 `/var/www/care` 아래의 파일을 웹 서비스 영역으로 사용한다.

WEB-11의 핵심은 웹 서비스 경로가 기본 설치 경로, 시스템 영역, 기타 업무 영역과 섞여 있지 않은지 확인하는 것이다.

PDF의 판단 기준은 다음과 같다.

|판단|기준|
|---|---|
|양호|웹 서버 경로를 기타 업무와 영역이 분리된 경로로 설정하고, 불필요한 경로가 존재하지 않는 경우|
|취약|웹 서버 경로를 기타 업무와 영역이 분리되지 않은 경로로 설정하거나, 불필요한 경로가 있는 경우|

PDF의 Apache 조치 방향은 다음과 같다.

```apache
DocumentRoot [별도의 경로]
```

Ubuntu Apache의 기본 웹 루트는 보통 다음 경로다.

```text
/var/www/html
```

CARE 실습 서버에서는 애플리케이션 전용 경로인 `/var/www/care`를 웹 서비스 경로로 사용하는 것이 더 적절하다.

따라서 WEB-11의 판단 기준은 다음처럼 정리할 수 있다.

```text
취약: DocumentRoot가 /var/www/html 같은 기본 경로로 설정됨
양호: DocumentRoot가 /var/www/care 같은 서비스 전용 경로로 분리됨
```

## 2. 최초 진단 결과

`AWS WEB 약점 진단 결과.md` 기준 최초 진단 결과는 **취약**이다.

최초 상태에서 `apache2ctl -S` 실행 결과 `Main DocumentRoot`가 Apache 기본 경로인 `/var/www/html`로 표시되었다.

```text
Main DocumentRoot: "/var/www/html"
```

또한 Apache 기본 웹 루트는 다음 경로다.

```text
/var/www/html
```

따라서 최초 상태는 CARE 애플리케이션 전용 경로가 아니라 Apache 기본 경로가 웹 서비스 기본 경로로 남아 있는 상태로 판단한다.

|항목|내용|
|---|---|
|진단 결과|취약|
|진단 근거|`Main DocumentRoot`가 `/var/www/html`로 설정됨|
|관련 설정|Apache `DocumentRoot`|
|최초 판단|기본 웹 루트 사용으로 웹 서비스 경로 분리 미흡|

WEB-11에서는 실제 서비스 VirtualHost의 `DocumentRoot`뿐 아니라 `apache2ctl -S`에 표시되는 `Main DocumentRoot`도 함께 확인해야 한다.

즉 다음처럼 해석한다.

```text
VirtualHost DocumentRoot가 /var/www/care여도,
Main DocumentRoot가 /var/www/html로 남아 있으면
진단 기준상 WEB-11 취약으로 판단될 수 있다.
```

## 3. 현재 서버 상태 해석

WEB-11은 Apache 기능 자체보다 **웹 서비스 파일이 어느 경로에서 제공되는지**를 점검하는 항목이다.

확인 대상은 다음과 같다.

|확인 대상|의미|
|---|---|
|`Main DocumentRoot`|Apache 전역 기본 DocumentRoot|
|`VirtualHost DocumentRoot`|실제 80, 443, 기타 포트 VirtualHost의 DocumentRoot|
|`/var/www/html`|Ubuntu Apache 기본 웹 루트|
|`/var/www/care`|CARE 애플리케이션 전용 웹 루트|
|`sites-enabled`|현재 활성화된 Apache 사이트 설정|
|`conf-enabled`|현재 활성화된 Apache 공통 설정|
|불필요한 기본 페이지|기본 Apache index 파일, 샘플 페이지, 테스트 페이지 등|

취약한 구조는 다음과 같다.

```text
Main DocumentRoot: /var/www/html
DocumentRoot /var/www/html
```

또는:

```text
DocumentRoot /
DocumentRoot /home/ubuntu
DocumentRoot /var
```

이런 설정은 웹 서비스 영역과 시스템 또는 기타 업무 영역이 분리되지 않은 상태로 볼 수 있다.

양호한 구조는 다음과 같다.

```text
Main DocumentRoot: /var/www/care
VirtualHost DocumentRoot: /var/www/care
기본 경로 /var/www/html은 직접 서비스하지 않음
```

특히 `/var/www/html`에 기본 Apache 페이지, 테스트 파일, 백업 파일이 남아 있고 `DocumentRoot`가 이 경로를 바라보면 불필요한 파일이 외부에 노출될 수 있다.

이 항목은 WEB-07 불필요한 파일 제거, WEB-14 파일 접근 통제, WEB-17 가상 디렉터리 삭제와 연결된다.

|연결 항목|연결 이유|
|---|---|
|WEB-07|웹 루트 안에 기본 파일이나 테스트 파일이 남아 있으면 노출 위험 증가|
|WEB-14|웹 서비스 경로 내 파일 권한과 접근 통제 필요|
|WEB-17|불필요한 가상 디렉터리가 추가 경로를 노출할 수 있음|

## 4. 실습 전 확인

실습을 시작하기 전에 현재 Apache 가상호스트와 DocumentRoot를 확인한다.

### 4-1. Apache 가상호스트 및 Main DocumentRoot 확인

```bash
apache2ctl -S
```

취약 상태에서는 다음과 유사한 결과가 확인된다.

```text
Main DocumentRoot: "/var/www/html"
```

### 4-2. 현재 활성 사이트 설정 확인

```bash
ls -l /etc/apache2/sites-enabled/
```

### 4-3. 활성 설정의 DocumentRoot 확인

```bash
grep -RniE '^[[:space:]]*DocumentRoot[[:space:]]+' \
/etc/apache2/apache2.conf \
/etc/apache2/sites-enabled/ \
/etc/apache2/conf-enabled/ 2>/dev/null
```

활성 설정에서 `/var/www/html`이 확인되면 취약 또는 조치 필요 상태다.

```text
DocumentRoot /var/www/html
```

### 4-4. 진단 스크립트 탐지 범위까지 확인

진단 스크립트가 `sites-available` 또는 `conf-available`까지 확인하는 경우가 있으므로, 전체 설정 후보에서도 `/var/www/html` 사용 여부를 확인한다.

```bash
grep -RniE '^[[:space:]]*DocumentRoot[[:space:]]+/var/www/html/?' \
/etc/apache2/apache2.conf \
/etc/apache2/sites-available/ \
/etc/apache2/sites-enabled/ \
/etc/apache2/conf-available/ \
/etc/apache2/conf-enabled/ 2>/dev/null
```

출력이 있으면 해당 파일을 확인한 뒤 조치 대상인지 판단한다.

### 4-5. 실습용 변수 지정

이 노트는 CARE 서버의 전용 웹 루트를 `/var/www/care`, Apache 기본 웹 루트를 `/var/www/html`로 가정한다.

```bash
APP_ROOT=/var/www/care
DEFAULT_ROOT=/var/www/html
SERVER=https://172.168.10.10

MAIN_CONF=/etc/apache2/conf-available/web-11-main-documentroot.conf
MAIN_CONF_ENABLED=/etc/apache2/conf-enabled/web-11-main-documentroot.conf
```

HTTPS가 자체 서명 인증서라면 `curl` 확인 시 `-k` 옵션을 사용한다.

### 4-6. 기본 경로 상태 확인

```bash
ls -ld "$DEFAULT_ROOT"
```

```bash
ls -al "$DEFAULT_ROOT" 2>/dev/null
```

기본 Apache 페이지나 테스트 파일이 남아 있는지 확인한다.

```bash
find "$DEFAULT_ROOT" -maxdepth 2 -type f -print 2>/dev/null
```

## 5. 취약 확인

이 항목의 최초 상태는 취약이다.  
취약 확인의 핵심은 Apache의 기본 웹 루트인 `/var/www/html`이 DocumentRoot로 남아 있는지 확인하는 것이다.

### 5-1. Main DocumentRoot 확인

```bash
apache2ctl -S | grep 'Main DocumentRoot'
```

취약 상태의 기대 결과는 다음과 같다.

```text
Main DocumentRoot: "/var/www/html"
```

이 결과는 Apache 전역 기본 DocumentRoot가 CARE 전용 경로가 아니라 기본 경로로 남아 있음을 의미한다.

### 5-2. `/var/www/html` DocumentRoot 설정 확인

```bash
grep -RniE '^[[:space:]]*DocumentRoot[[:space:]]+/var/www/html/?' \
/etc/apache2/apache2.conf \
/etc/apache2/sites-available/ \
/etc/apache2/sites-enabled/ \
/etc/apache2/conf-available/ \
/etc/apache2/conf-enabled/ 2>/dev/null
```

취약 상태에서는 다음과 같은 결과가 나올 수 있다.

```text
/etc/apache2/sites-available/000-default.conf:DocumentRoot /var/www/html
```

또는 활성 설정에서 다음처럼 나올 수 있다.

```text
/etc/apache2/sites-enabled/care.conf:DocumentRoot /var/www/html
```

### 5-3. 기본 경로 테스트 파일 생성

웹 루트가 실제로 `/var/www/html`을 바라보는지 확인하기 위해 테스트 파일을 만든다.

```bash
echo "WEB-11 default DocumentRoot test" | sudo tee "$DEFAULT_ROOT/web11-default-path-test.html"
```

파일 생성 확인:

```bash
ls -l "$DEFAULT_ROOT/web11-default-path-test.html"
```

### 5-4. 기본 경로 노출 확인

```bash
curl -k -i "$SERVER/web11-default-path-test.html"
```

취약 상태에서 기대 결과는 다음과 같다.

```text
HTTP/1.1 200 OK

WEB-11 default DocumentRoot test
```

이 결과는 Apache가 기본 웹 루트 `/var/www/html`의 파일을 외부로 서비스하고 있음을 의미한다.

단, 현재 서버에 HTTP → HTTPS 리디렉션이 적용되어 있으면 HTTP 요청은 301이 먼저 나올 수 있다.  
이 경우 `https://`로 직접 요청하거나 `curl -k -L`을 사용하여 최종 응답을 확인한다.

```bash
curl -k -L -i http://172.168.10.10/web11-default-path-test.html
```

## 6. 조치 방법

조치 핵심은 Apache의 기본 DocumentRoot를 CARE 애플리케이션 전용 경로인 `/var/www/care`로 변경하고, `/var/www/html`이 직접 서비스되지 않도록 정리하는 것이다.

### 6-1. CARE 전용 경로 확인

```bash
ls -ld "$APP_ROOT"
```

기대 결과:

```text
/var/www/care
```

### 6-2. 전역 Main DocumentRoot 조치 설정 생성

`apache2ctl -S`의 `Main DocumentRoot`가 `/var/www/html`로 남는 경우, 전역 설정에서 `DocumentRoot`를 명시적으로 `/var/www/care`로 지정한다.

```bash
sudo tee "$MAIN_CONF" > /dev/null <<EOF
DocumentRoot $APP_ROOT

<Directory "$APP_ROOT">
    Options -Indexes FollowSymLinks
    AllowOverride None
    Require all granted
</Directory>

<Directory "$DEFAULT_ROOT">
    Options None
    AllowOverride None
    Require all denied
</Directory>
EOF
```

핵심 설정은 다음이다.

```apache
DocumentRoot /var/www/care

<Directory "/var/www/care">
    Options -Indexes FollowSymLinks
    AllowOverride None
    Require all granted
</Directory>

<Directory "/var/www/html">
    Options None
    AllowOverride None
    Require all denied
</Directory>
```

### 6-3. 설정 활성화

```bash
sudo a2enconf web-11-main-documentroot
```

### 6-4. 기본 사이트 비활성화

기본 사이트가 활성화되어 있으면 비활성화한다.

```bash
ls -l /etc/apache2/sites-enabled/ | grep 000-default
```

출력이 있으면 다음을 실행한다.

```bash
sudo a2dissite 000-default.conf
```

### 6-5. `/var/www/html`을 DocumentRoot로 지정한 설정 수정

진단 스크립트가 `sites-available`까지 확인하는 경우, 비활성 파일에 남은 `/var/www/html` 설정도 취약 근거로 잡힐 수 있다.  
따라서 `/var/www/html`을 `DocumentRoot`로 지정한 설정 파일을 확인한다.

```bash
grep -RliE '^[[:space:]]*DocumentRoot[[:space:]]+/var/www/html/?' \
/etc/apache2/sites-available/ \
/etc/apache2/sites-enabled/ \
/etc/apache2/conf-available/ \
/etc/apache2/conf-enabled/ 2>/dev/null
```

출력된 파일은 백업 후 `/var/www/care`로 수정한다.

```bash
for f in $(grep -RliE '^[[:space:]]*DocumentRoot[[:space:]]+/var/www/html/?' \
/etc/apache2/sites-available/ \
/etc/apache2/sites-enabled/ \
/etc/apache2/conf-available/ \
/etc/apache2/conf-enabled/ 2>/dev/null); do
  sudo cp "$f" "$f.bak.WEB-11"
  sudo sed -i -E 's#^([[:space:]]*)DocumentRoot[[:space:]]+/var/www/html/?#\1DocumentRoot /var/www/care#' "$f"
done
```

수정 결과를 확인한다.

```bash
grep -RniE '^[[:space:]]*DocumentRoot[[:space:]]+' \
/etc/apache2/sites-available/ \
/etc/apache2/sites-enabled/ \
/etc/apache2/conf-available/ \
/etc/apache2/conf-enabled/ 2>/dev/null
```

### 6-6. 기본 경로 테스트 파일 제거

```bash
sudo rm -f "$DEFAULT_ROOT/web11-default-path-test.html"
```

제거 확인:

```bash
ls -l "$DEFAULT_ROOT/web11-default-path-test.html" 2>/dev/null
```

기대 결과:

```text
출력 없음
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

## 7. 조치 후 확인

조치 후에는 `Main DocumentRoot`와 활성 VirtualHost의 `DocumentRoot`가 CARE 전용 경로로 변경되었는지 확인한다.

### 7-1. Main DocumentRoot 재확인

```bash
apache2ctl -S | grep 'Main DocumentRoot'
```

조치 후 기대 결과는 다음이다.

```text
Main DocumentRoot: "/var/www/care"
```

### 7-2. 활성 설정의 DocumentRoot 확인

```bash
grep -RniE '^[[:space:]]*DocumentRoot[[:space:]]+' \
/etc/apache2/apache2.conf \
/etc/apache2/sites-enabled/ \
/etc/apache2/conf-enabled/ 2>/dev/null
```

조치 후 기대 결과는 다음과 유사하다.

```text
DocumentRoot /var/www/care
```

활성 설정에서 다음 경로가 DocumentRoot로 남아 있으면 조치가 완료되지 않은 것이다.

```text
DocumentRoot /var/www/html
```

### 7-3. 전체 설정 후보에서 기본 경로 잔존 여부 확인

```bash
grep -RniE '^[[:space:]]*DocumentRoot[[:space:]]+/var/www/html/?' \
/etc/apache2/apache2.conf \
/etc/apache2/sites-available/ \
/etc/apache2/sites-enabled/ \
/etc/apache2/conf-available/ \
/etc/apache2/conf-enabled/ 2>/dev/null
```

조치 후 기대 결과:

```text
출력 없음
```

단, 백업 파일을 `/etc/apache2` 내부에 남겨두면 이 검색에 다시 잡힐 수 있다.  
보고서 증거 확보 후에는 `.bak.WEB-11` 백업 파일을 별도 보관하거나 삭제한다.

### 7-4. 기본 경로 테스트 파일 접근 차단 확인

```bash
curl -k -i "$SERVER/web11-default-path-test.html"
```

조치 후 기대 결과는 다음이다.

```text
HTTP/1.1 404 Not Found
```

또는 `/var/www/html` 접근을 명시적으로 차단한 경우:

```text
HTTP/1.1 403 Forbidden
```

중요한 것은 다음 문자열이 더 이상 출력되지 않는 것이다.

```text
WEB-11 default DocumentRoot test
```

### 7-5. CARE 서비스 정상 응답 확인

```bash
curl -k -i "$SERVER/"
```

정상이라면 CARE 애플리케이션의 메인 페이지, 로그인 페이지, 리다이렉트 등 현재 서비스에 맞는 응답이 나와야 한다.

예상 결과는 서버 상태에 따라 다를 수 있다.

```text
HTTP/1.1 200 OK
```

또는:

```text
HTTP/1.1 302 Found
```

### 7-6. Apache 서비스 상태 확인

```bash
systemctl status apache2 --no-pager
```

정상 상태라면 다음과 같이 보여야 한다.

```text
Active: active (running)
```

### 7-7. 기본 경로의 불필요 파일 확인

```bash
find "$DEFAULT_ROOT" -maxdepth 2 -type f -print 2>/dev/null
```

기본 경로에 테스트 파일, 샘플 파일, 백업 파일이 남아 있으면 삭제하거나 별도 관리한다.

## 8. 실행 순서 요약

실습 중에는 아래 순서대로 진행한다.

### 8-1. 현재 상태 확인

```bash
APP_ROOT=/var/www/care
DEFAULT_ROOT=/var/www/html
SERVER=https://172.168.10.10

MAIN_CONF=/etc/apache2/conf-available/web-11-main-documentroot.conf
MAIN_CONF_ENABLED=/etc/apache2/conf-enabled/web-11-main-documentroot.conf
```

```bash
apache2ctl -S | grep 'Main DocumentRoot'
```

취약 상태 기대 결과:

```text
Main DocumentRoot: "/var/www/html"
```

```bash
grep -RniE '^[[:space:]]*DocumentRoot[[:space:]]+/var/www/html/?' \
/etc/apache2/apache2.conf \
/etc/apache2/sites-available/ \
/etc/apache2/sites-enabled/ \
/etc/apache2/conf-available/ \
/etc/apache2/conf-enabled/ 2>/dev/null
```

```bash
ls -al "$DEFAULT_ROOT" 2>/dev/null
```

### 8-2. 취약 확인

```bash
echo "WEB-11 default DocumentRoot test" | sudo tee "$DEFAULT_ROOT/web11-default-path-test.html"
```

```bash
curl -k -i "$SERVER/web11-default-path-test.html"
```

취약 상태 기대 결과:

```text
HTTP/1.1 200 OK

WEB-11 default DocumentRoot test
```

### 8-3. 조치 적용

```bash
sudo tee "$MAIN_CONF" > /dev/null <<EOF
DocumentRoot $APP_ROOT

<Directory "$APP_ROOT">
    Options -Indexes FollowSymLinks
    AllowOverride None
    Require all granted
</Directory>

<Directory "$DEFAULT_ROOT">
    Options None
    AllowOverride None
    Require all denied
</Directory>
EOF
```

```bash
sudo a2enconf web-11-main-documentroot
```

```bash
ls -l /etc/apache2/sites-enabled/ | grep 000-default
```

`000-default.conf`가 활성화되어 있으면 비활성화한다.

```bash
sudo a2dissite 000-default.conf
```

`/var/www/html`을 DocumentRoot로 지정한 설정 파일이 남아 있으면 백업 후 수정한다.

```bash
for f in $(grep -RliE '^[[:space:]]*DocumentRoot[[:space:]]+/var/www/html/?' \
/etc/apache2/sites-available/ \
/etc/apache2/sites-enabled/ \
/etc/apache2/conf-available/ \
/etc/apache2/conf-enabled/ 2>/dev/null); do
  sudo cp "$f" "$f.bak.WEB-11"
  sudo sed -i -E 's#^([[:space:]]*)DocumentRoot[[:space:]]+/var/www/html/?#\1DocumentRoot /var/www/care#' "$f"
done
```

```bash
sudo rm -f "$DEFAULT_ROOT/web11-default-path-test.html"
```

```bash
sudo apachectl configtest
```

```bash
sudo systemctl restart apache2
```

### 8-4. 조치 후 확인

```bash
apache2ctl -S | grep 'Main DocumentRoot'
```

조치 후 기대 결과:

```text
Main DocumentRoot: "/var/www/care"
```

```bash
grep -RniE '^[[:space:]]*DocumentRoot[[:space:]]+/var/www/html/?' \
/etc/apache2/apache2.conf \
/etc/apache2/sites-available/ \
/etc/apache2/sites-enabled/ \
/etc/apache2/conf-available/ \
/etc/apache2/conf-enabled/ 2>/dev/null
```

기대 결과:

```text
출력 없음
```

```bash
curl -k -i "$SERVER/web11-default-path-test.html"
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
curl -k -i "$SERVER/"
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
systemctl status apache2 --no-pager
```

기대 결과:

```text
Active: active (running)
```

### 8-5. 실습 파일 및 백업 파일 정리

증거 확보 후 테스트 파일을 제거한다.

```bash
sudo rm -f "$DEFAULT_ROOT/web11-default-path-test.html"
```

백업 파일이 진단 검색에 걸릴 수 있으므로, 보고서 증거 확보 후 별도 보관하거나 삭제한다.

```bash
sudo find /etc/apache2 -name '*.bak.WEB-11' -print
```

삭제가 필요하면 다음을 실행한다.

```bash
sudo find /etc/apache2 -name '*.bak.WEB-11' -delete
```

## 9. 증거 정리

### 9-1. 최초 취약 상태 증거

최초 진단 결과:

```text
WEB-11 · 웹 서비스 경로 설정
Main DocumentRoot가 /var/www/html로 설정되어 있어 기본 웹 루트 사용 상태로 확인됨
```

`apache2ctl -S` 확인 결과:

```text
Main DocumentRoot: "/var/www/html"
```

DocumentRoot 확인 명령어:

```bash
apache2ctl -S | grep 'Main DocumentRoot'
```

```bash
grep -RniE '^[[:space:]]*DocumentRoot[[:space:]]+/var/www/html/?' \
/etc/apache2/apache2.conf \
/etc/apache2/sites-available/ \
/etc/apache2/sites-enabled/ \
/etc/apache2/conf-available/ \
/etc/apache2/conf-enabled/ 2>/dev/null
```

취약 상태 판단:

```text
Apache 기본 웹 루트인 /var/www/html이 Main DocumentRoot로 남아 있으므로 WEB-11 취약
```

### 9-2. 취약 확인 증거

기본 경로 테스트 파일:

```text
/var/www/html/web11-default-path-test.html
```

기본 경로 테스트 파일 접근:

```bash
curl -k -i "$SERVER/web11-default-path-test.html"
```

취약 상태 기대 결과:

```text
HTTP/1.1 200 OK

WEB-11 default DocumentRoot test
```

이 결과는 웹 서비스 경로가 CARE 전용 경로가 아니라 Apache 기본 경로를 통해 노출될 수 있음을 의미한다.

### 9-3. 조치 후 증거

조치 후 `Main DocumentRoot` 확인:

```bash
apache2ctl -S | grep 'Main DocumentRoot'
```

조치 후 기대 결과:

```text
Main DocumentRoot: "/var/www/care"
```

활성 및 후보 설정에서 기본 경로 잔존 여부 확인:

```bash
grep -RniE '^[[:space:]]*DocumentRoot[[:space:]]+/var/www/html/?' \
/etc/apache2/apache2.conf \
/etc/apache2/sites-available/ \
/etc/apache2/sites-enabled/ \
/etc/apache2/conf-available/ \
/etc/apache2/conf-enabled/ 2>/dev/null
```

조치 후 기대 결과:

```text
출력 없음
```

기본 경로 테스트 파일 접근:

```bash
curl -k -i "$SERVER/web11-default-path-test.html"
```

조치 후 기대 결과:

```text
HTTP/1.1 404 Not Found
```

또는:

```text
HTTP/1.1 403 Forbidden
```

CARE 서비스 정상 응답 확인:

```bash
curl -k -i "$SERVER/"
```

기대 결과:

```text
HTTP/1.1 200 OK
```

또는:

```text
HTTP/1.1 302 Found
```

## 10. 판단

|항목|판단|
|---|---|
|최초 진단|취약|
|최초 취약 근거|`Main DocumentRoot`가 `/var/www/html`로 설정됨|
|취약 조건|Apache 기본 웹 루트 `/var/www/html` 사용|
|조치 방향|`DocumentRoot`를 CARE 전용 경로 `/var/www/care`로 변경|
|추가 조치|기본 사이트 비활성화, `/var/www/html` 직접 접근 차단, 불필요 파일 제거|
|조치 후 판단|`Main DocumentRoot`와 활성 DocumentRoot가 `/var/www/care`로 확인되면 양호|
|증거 상태|조치 전 `/var/www/html`, 조치 후 `/var/www/care` 비교 필요|

최초 상태에서는 `apache2ctl -S` 결과 `Main DocumentRoot`가 `/var/www/html`로 표시되었으므로 WEB-11은 **취약**으로 판단한다.

```text
Main DocumentRoot: "/var/www/html"
```

이 상태는 Apache 기본 웹 루트가 전역 기본 경로로 남아 있는 상태이며, PDF 기준의 “웹 서버 경로를 기타 업무와 영역이 분리되지 않은 경로로 설정한 경우”에 해당할 수 있다.

조치는 `DocumentRoot`를 CARE 전용 경로인 `/var/www/care`로 변경하고, `/var/www/html` 경로를 직접 서비스하지 않도록 제한하는 방식으로 수행한다.

조치 후 다음 조건이 만족되면 WEB-11은 **양호**로 판단한다.

```text
1. apache2ctl -S에서 Main DocumentRoot가 /var/www/care로 표시됨
2. 활성 Apache 설정에서 DocumentRoot /var/www/html이 더 이상 확인되지 않음
3. /var/www/html/web11-default-path-test.html 요청이 404 또는 403으로 처리됨
4. CARE 서비스가 정상 응답함
```