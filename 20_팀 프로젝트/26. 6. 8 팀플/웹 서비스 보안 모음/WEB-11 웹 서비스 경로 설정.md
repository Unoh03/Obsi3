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

즉 Apache 환경에서는 `DocumentRoot`가 기본 경로나 불필요한 경로가 아니라, 서비스 목적에 맞는 별도 경로로 설정되어 있는지 확인한다.

Ubuntu Apache의 기본 웹 루트는 보통 다음 경로다.

```text
/var/www/html
```

CARE 실습 서버에서는 애플리케이션 전용 경로인 `/var/www/care`를 웹 서비스 경로로 사용하는 것이 더 적절하다.

## 2. 최초 진단 결과

`AWS WEB 약점 진단 결과.md` 기준 최초 진단 결과는 **양호**이다.

|항목|내용|
|---|---|
|진단 결과|양호|
|진단 근거|웹 서비스 DocumentRoot가 기본 경로가 아닌 CARE 전용 경로로 분리됨|
|관련 설정|Apache VirtualHost의 `DocumentRoot`|
|최초 판단|웹 서비스 경로가 전용 경로로 분리되어 있으므로 양호|

최초 진단에서 확인해야 할 대표 설정은 다음과 같다.

```apache
DocumentRoot /var/www/care
```

이 설정은 Apache 기본 경로인 `/var/www/html`이 아니라 CARE 애플리케이션 전용 경로를 웹 루트로 사용한다는 의미다.

따라서 최초 상태는 양호로 판단한다.

## 3. 현재 서버 상태 해석

WEB-11은 Apache 기능 자체보다 **웹 서비스 파일이 어느 경로에서 제공되는지**를 점검하는 항목이다.

확인 대상은 다음과 같다.

|확인 대상|의미|
|---|---|
|`DocumentRoot`|실제 웹 서비스 루트 경로|
|`/var/www/html`|Ubuntu Apache 기본 웹 루트|
|`/var/www/care`|CARE 애플리케이션 전용 웹 루트|
|`sites-enabled`|현재 활성화된 Apache 사이트 설정|
|불필요한 기본 페이지|기본 Apache index 파일, 샘플 페이지, 테스트 페이지 등|

안전한 구조는 다음과 같다.

```text
Apache 기본 경로: /var/www/html
CARE 서비스 경로: /var/www/care
실제 DocumentRoot: /var/www/care
```

취약하거나 부적절한 구조는 다음과 같다.

```text
DocumentRoot /var/www/html
```

또는:

```text
DocumentRoot /
DocumentRoot /home/ubuntu
DocumentRoot /var
```

이런 설정은 웹 서비스 영역과 시스템 또는 기타 업무 영역이 분리되지 않은 상태로 볼 수 있다.

특히 `/var/www/html`에 기본 Apache 페이지, 테스트 파일, 백업 파일이 남아 있고 `DocumentRoot`가 이 경로를 바라보면, 불필요한 파일이 외부에 노출될 수 있다.

이 항목은 WEB-07 불필요한 파일 제거, WEB-14 파일 접근 통제, WEB-17 가상 디렉터리 삭제와 연결된다.

|연결 항목|연결 이유|
|---|---|
|WEB-07|웹 루트 안에 기본 파일이나 테스트 파일이 남아 있으면 노출 위험 증가|
|WEB-14|웹 서비스 경로 내 파일 권한과 접근 통제 필요|
|WEB-17|불필요한 가상 디렉터리가 추가 경로를 노출할 수 있음|

## 4. 실습 전 확인

실습을 시작하기 전에 현재 Apache 가상호스트와 DocumentRoot를 확인한다.

### 4-1. Apache 가상호스트 확인

```bash
apache2ctl -S
```

### 4-2. 현재 활성 사이트 설정 확인

```bash
ls -l /etc/apache2/sites-enabled/
```

### 4-3. DocumentRoot 설정 확인

```bash
grep -R "DocumentRoot" /etc/apache2/sites-enabled/ /etc/apache2/sites-available/ 2>/dev/null
```

기대되는 양호 상태는 다음과 유사하다.

```text
DocumentRoot /var/www/care
```

### 4-4. 실습용 변수 지정

이 노트는 CARE 서버의 DocumentRoot가 `/var/www/html/care`라고 가정한다.

```bash
APP_ROOT=/var/www/care
DEFAULT_ROOT=/var/www/html
SERVER=http://172.168.10.10
SITE_CONF=$(grep -Rl "DocumentRoot" /etc/apache2/sites-enabled/ /etc/apache2/sites-available/ 2>/dev/null | head -n 1)
SITE_CONF_REAL=$(readlink -f "$SITE_CONF")
BACKUP="${SITE_CONF_REAL}.bak.WEB-11"
```

현재 선택된 설정 파일을 확인한다.

```bash
echo "$SITE_CONF"
echo "$SITE_CONF_REAL"
```

`SITE_CONF_REAL`이 비어 있으면 Apache 사이트 설정 파일을 직접 확인한 뒤 경로를 지정한다.

예를 들어 CARE 사이트 설정 파일이 `/etc/apache2/sites-available/care.conf`라면 다음처럼 지정한다.

```bash
SITE_CONF_REAL=/etc/apache2/sites-available/care.conf
BACKUP="${SITE_CONF_REAL}.bak.WEB-11"
```

### 4-5. 기본 경로 상태 확인

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

## 5. 취약 재현

이 항목은 최초 진단 결과가 양호이므로, PDF 내용을 실습하기 위해 의도적으로 취약 상태를 재현한다.

> 주의: 이 절차는 격리된 실습 서버에서만 수행한다.  
> 이 실습은 Apache의 실제 `DocumentRoot`를 잠시 기본 경로인 `/var/www/html`로 변경한다.  
> 실습 중 CARE 애플리케이션 접속이 일시적으로 달라질 수 있다.  
> 반드시 설정 파일을 백업하고, 취약 증거 확보 후 즉시 복구한다.

취약 재현의 핵심은 다음이다.

```text
DocumentRoot를 CARE 전용 경로가 아니라 Apache 기본 경로인 /var/www/html로 바꾸어,
웹 서비스 경로가 전용 경로와 분리되지 않은 상태를 만든다.
```

### 5-1. 현재 설정 백업

```bash
sudo cp "$SITE_CONF_REAL" "$BACKUP"
```

백업 확인:

```bash
ls -l "$BACKUP"
```

### 5-2. 기본 경로에 테스트 파일 생성

```bash
sudo mkdir -p "$DEFAULT_ROOT"
```

```bash
echo "WEB-11 default DocumentRoot test" | sudo tee "$DEFAULT_ROOT/web11-default-path-test.html"
```

파일 생성 확인:

```bash
ls -l "$DEFAULT_ROOT/web11-default-path-test.html"
```

### 5-3. DocumentRoot를 기본 경로로 변경

현재 설정 파일의 `DocumentRoot`를 `/var/www/html`로 변경한다.

```bash
sudo sed -i -E "s#^[[:space:]]*DocumentRoot[[:space:]]+.*#    DocumentRoot $DEFAULT_ROOT#" "$SITE_CONF_REAL"
```

변경 결과 확인:

```bash
grep -n "DocumentRoot" "$SITE_CONF_REAL"
```

취약 재현 상태의 기대 결과는 다음이다.

```text
DocumentRoot /var/www/html
```

### 5-4. Apache 설정 문법 검사

```bash
sudo apachectl configtest
```

정상이라면 다음 결과가 나와야 한다.

```text
Syntax OK
```

### 5-5. Apache restart

```bash
sudo systemctl restart apache2
```

### 5-6. 기본 경로 노출 확인

```bash
curl -i "$SERVER/web11-default-path-test.html"
```

취약 재현 상태에서 기대 결과는 다음과 같다.

```text
HTTP/1.1 200 OK

WEB-11 default DocumentRoot test
```

이 결과는 Apache가 CARE 전용 경로가 아니라 기본 웹 루트 `/var/www/html`의 파일을 서비스하고 있음을 의미한다.

PDF 기준으로는 웹 서비스 경로가 별도 업무 경로로 분리되지 않은 상태에 가까우므로 취약 상태로 판단할 수 있다.

## 6. 조치 방법

조치 핵심은 `DocumentRoot`를 CARE 애플리케이션 전용 경로로 복구하고, 기본 웹 루트에 만든 불필요한 테스트 파일을 제거하는 것이다.

### 6-1. 설정 파일 원복

백업 파일로 사이트 설정을 복구한다.

```bash
sudo cp "$BACKUP" "$SITE_CONF_REAL"
```

복구 결과를 확인한다.

```bash
grep -n "DocumentRoot" "$SITE_CONF_REAL"
```

기대 결과는 다음과 같다.

```text
DocumentRoot /var/www/care
```

만약 백업을 사용하지 않고 직접 수정해야 한다면 다음처럼 변경한다.

```bash
sudo sed -i -E "s#^[[:space:]]*DocumentRoot[[:space:]]+.*#    DocumentRoot $APP_ROOT#" "$SITE_CONF_REAL"
```

### 6-2. 기본 경로 테스트 파일 제거

```bash
sudo rm -f "$DEFAULT_ROOT/web11-default-path-test.html"
```

제거 확인:

```bash
ls -l "$DEFAULT_ROOT/web11-default-path-test.html" 2>/dev/null
```

기대 결과는 다음이다.

```text
출력 없음
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

조치 후에는 웹 서비스 경로가 다시 CARE 전용 경로로 돌아왔는지 확인한다.

### 7-1. DocumentRoot 재확인

```bash
grep -R "DocumentRoot" /etc/apache2/sites-enabled/ /etc/apache2/sites-available/ 2>/dev/null
```

기대 결과는 다음과 유사하다.

```text
DocumentRoot /var/www/care
```

`/var/www/html`이 활성 사이트의 DocumentRoot로 남아 있으면 조치가 완료되지 않은 것이다.

### 7-2. 기본 경로 테스트 파일 접근 차단 확인

```bash
curl -i "$SERVER/web11-default-path-test.html"
```

조치 후 기대 결과는 다음이다.

```text
HTTP/1.1 404 Not Found
```

중요한 것은 다음 문자열이 더 이상 출력되지 않는 것이다.

```text
WEB-11 default DocumentRoot test
```

### 7-3. CARE 서비스 정상 응답 확인

```bash
curl -i "$SERVER/"
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

### 7-4. Apache 서비스 상태 확인

```bash
systemctl status apache2 --no-pager
```

정상 상태라면 다음과 같이 보여야 한다.

```text
Active: active (running)
```

### 7-5. 기본 경로의 불필요 파일 확인

```bash
find "$DEFAULT_ROOT" -maxdepth 2 -type f -print 2>/dev/null
```

기본 경로에 테스트 파일, 샘플 파일, 백업 파일이 남아 있으면 삭제하거나 별도 관리해야 한다.

## 8. 실행 순서 요약

실습 중에는 아래 순서대로 진행한다.

### 8-1. 현재 상태 확인

```bash
APP_ROOT=/var/www/care
DEFAULT_ROOT=/var/www/html
SERVER=http://172.168.10.10
SITE_CONF=$(grep -Rl "DocumentRoot" /etc/apache2/sites-enabled/ /etc/apache2/sites-available/ 2>/dev/null | head -n 1)
SITE_CONF_REAL=$(readlink -f "$SITE_CONF")
BACKUP="${SITE_CONF_REAL}.bak.WEB-11"
```

```bash
apache2ctl -S
```

```bash
ls -l /etc/apache2/sites-enabled/
```

```bash
grep -R "DocumentRoot" /etc/apache2/sites-enabled/ /etc/apache2/sites-available/ 2>/dev/null
```

```bash
echo "$SITE_CONF"
echo "$SITE_CONF_REAL"
```

```bash
ls -al "$DEFAULT_ROOT" 2>/dev/null
```

### 8-2. 취약 재현

```bash
sudo cp "$SITE_CONF_REAL" "$BACKUP"
```

```bash
sudo mkdir -p "$DEFAULT_ROOT"
```

```bash
echo "WEB-11 default DocumentRoot test" | sudo tee "$DEFAULT_ROOT/web11-default-path-test.html"
```

```bash
sudo sed -i -E "s#^[[:space:]]*DocumentRoot[[:space:]]+.*#    DocumentRoot $DEFAULT_ROOT#" "$SITE_CONF_REAL"
```

```bash
grep -n "DocumentRoot" "$SITE_CONF_REAL"
```

```bash
sudo apachectl configtest
```

```bash
sudo systemctl restart apache2
```

```bash
curl -i "$SERVER/web11-default-path-test.html"
```

취약 상태 기대 결과:

```text
HTTP/1.1 200 OK

WEB-11 default DocumentRoot test
```

### 8-3. 조치 및 복구

```bash
sudo cp "$BACKUP" "$SITE_CONF_REAL"
```

```bash
grep -n "DocumentRoot" "$SITE_CONF_REAL"
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
grep -R "DocumentRoot" /etc/apache2/sites-enabled/ /etc/apache2/sites-available/ 2>/dev/null
```

기대 결과:

```text
DocumentRoot /var/www/care
```

```bash
curl -i "$SERVER/web11-default-path-test.html"
```

조치 후 기대 결과:

```text
HTTP/1.1 404 Not Found
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

```bash
systemctl status apache2 --no-pager
```

기대 결과:

```text
Active: active (running)
```

### 8-5. 실습 파일 정리

증거 확보 후 백업 파일을 제거한다.

```bash
sudo rm -f "$BACKUP"
```

정리 확인:

```bash
ls -l "$BACKUP" 2>/dev/null
```

기대 결과:

```text
출력 없음
```

## 9. 증거 정리

### 9-1. 최초 상태 증거

최초 진단 결과:

```text
WEB-11 · 웹 서비스 경로 설정
DocumentRoot가 기본 경로가 아닌 CARE 전용 경로로 설정됨
```

DocumentRoot 확인 명령어:

```bash
grep -R "DocumentRoot" /etc/apache2/sites-enabled/ /etc/apache2/sites-available/ 2>/dev/null
```

양호 상태 기대 결과:

```text
DocumentRoot /var/www/care
```

### 9-2. 취약 재현 증거

취약 재현 설정:

```apache
DocumentRoot /var/www/html
```

기본 경로 테스트 파일 접근:

```bash
curl -i "$SERVER/web11-default-path-test.html"
```

취약 재현 기대 결과:

```text
HTTP/1.1 200 OK

WEB-11 default DocumentRoot test
```

이 결과는 웹 서비스 경로가 CARE 전용 경로가 아니라 Apache 기본 경로로 바뀌었음을 의미한다.

### 9-3. 조치 후 증거

DocumentRoot 복구 확인:

```bash
grep -R "DocumentRoot" /etc/apache2/sites-enabled/ /etc/apache2/sites-available/ 2>/dev/null
```

조치 후 기대 결과:

```text
DocumentRoot /var/www/care
```

기본 경로 테스트 파일 접근:

```bash
curl -i "$SERVER/web11-default-path-test.html"
```

조치 후 기대 결과:

```text
HTTP/1.1 404 Not Found
```

CARE 서비스 정상 응답 확인:

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

## 10. 판단

|항목|판단|
|---|---|
|최초 진단|양호|
|진단 근거|DocumentRoot가 기본 경로가 아닌 CARE 전용 경로로 설정됨|
|실습 처리|DocumentRoot를 `/var/www/html`로 변경하여 취약 상태 재현 후 원복|
|조치 전 판단|최초 상태는 양호, 기본 경로 사용 상태는 취약|
|조치 후 판단|DocumentRoot가 CARE 전용 경로로 복구되면 양호|
|증거 상태|최초 진단 결과 확보, 취약 재현 및 조치 후 접근 증거 필요|

현재 서버는 최초 진단 기준으로 DocumentRoot가 Apache 기본 경로가 아닌 CARE 전용 경로로 분리되어 있으므로 WEB-11은 **양호**로 판단한다.

다만 PDF의 취약 조건을 실습하기 위해 DocumentRoot를 `/var/www/html`로 변경하면, 웹 서비스 경로가 기본 경로로 돌아가고 기본 경로의 테스트 파일이 외부에 노출되는 취약 상태를 재현할 수 있다.

조치는 DocumentRoot를 다시 `/var/www/care`로 복구하고, 기본 경로에 만든 테스트 파일을 제거하는 방식으로 수행한다.

조치 후 활성 Apache 설정에서 DocumentRoot가 `/var/www/care`로 확인되고, `/web11-default-path-test.html` 요청이 `404 Not Found`로 처리되며, CARE 서비스가 정상 응답하면 WEB-11은 조치 후 **양호**로 판단한다.