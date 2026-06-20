---

type: lab  
topic: web-service-security  
source: 주요정보통신기반시설 기술적 취약점 분석·평가 방법 상세가이드  
source_pages:
  - 290    
  - 291  
status: draft  
created: 2026-06-18  
tags:
    
- 🏷️과목/웹서비스보안
    
- 🏷️주제/WEB-07
    
- 🏷️주제/Unnecessary-Files
    
- 🏷️주제/Apache
    
- 🏷️상태/draft
---
# WEB-07 웹 서비스 경로 내 불필요한 파일 제거

## 1. PDF 기준

PDF p.290-291의 WEB-07은 웹 서비스 경로 안에 **불필요한 파일이나 디렉터리가 남아 있는지** 점검하는 항목이다.

웹 서버 설치, 웹 애플리케이션 배포, 테스트 과정에서 다음과 같은 파일이 남을 수 있다.

```text
샘플 파일
매뉴얼 파일
임시 파일
테스트 파일
백업 파일
이전 버전 파일
편집기 임시 파일
압축 파일
```

이런 파일이 웹 서비스 경로 안에 남아 있으면 비인가자에게 시스템 구조, 웹 서버 정보, 소스 구조, 백업 데이터가 노출될 수 있다.

예를 들어 다음과 같은 파일이 웹 루트에 있으면 위험하다.

```text
backup.zip
config.php.bak
db_dump.sql
phpinfo.php
test.php
index.php.old
manual/
sample/
```

PDF의 판단 기준은 다음과 같다.

|판단|기준|
|---|---|
|양호|기본으로 생성되는 불필요한 파일 및 디렉터리가 존재하지 않는 경우|
|취약|기본으로 생성되는 불필요한 파일 및 디렉터리가 존재하는 경우|

PDF의 Apache 조치 사례는 확인된 불필요한 매뉴얼 디렉터리나 파일을 제거하는 방식이다.

```bash
rm -rf /<Apache 설치 디렉터리>/htdocs/manual
rm -rf /<Apache 설치 디렉터리>/manual
```

단, 현재 Ubuntu Apache 환경에서는 Apache 2.4 기준으로 `htdocs`가 기본 경로가 아닐 수 있다. 이 실습 서버에서는 CARE 애플리케이션의 DocumentRoot인 `/var/www/care`를 중심으로 확인한다.

## 2. 최초 진단 결과

`AWS WEB 약점 진단 결과.md` 기준 최초 진단 결과는 **양호**이다.

|항목|내용|
|---|---|
|진단 결과|양호|
|진단 근거|백업, 샘플, 테스트 파일 등 불필요한 파일 발견되지 않음|
|진단 결과 메시지|`No unnecessary files found`|
|최초 판단|웹 서비스 경로 내 불필요한 파일이 확인되지 않았으므로 양호|

진단 결과는 다음과 같다.

```text
No unnecessary files found
```

따라서 최초 상태에서는 웹 서비스 경로 안에 대표적인 불필요 파일이나 디렉터리가 발견되지 않은 것으로 판단한다.

## 3. 현재 서버 상태 해석

WEB-07은 Apache 설정 자체보다 **웹 서비스 경로에 남아 있는 파일**을 점검하는 항목이다.

현재 서버의 핵심 확인 대상은 다음과 같다.

|확인 대상|의미|
|---|---|
|DocumentRoot|외부에서 접근 가능한 웹 루트|
|백업 파일|`.bak`, `.old`, `.orig`, `.save`, `~` 등|
|테스트 파일|`test.php`, `phpinfo.php`, `sample.php` 등|
|압축 파일|`.zip`, `.tar`, `.tar.gz`, `.7z` 등|
|DB 덤프 파일|`.sql`, `.dump` 등|
|매뉴얼/샘플 디렉터리|`manual`, `docs`, `sample`, `samples`, `test` 등|

이 항목은 WEB-04 디렉터리 리스팅과 연결된다. 디렉터리 리스팅이 켜져 있으면 불필요 파일의 이름이 쉽게 노출된다. 그러나 WEB-04가 조치되어 디렉터리 목록이 보이지 않더라도, 파일명을 알거나 추측하면 직접 접근이 가능할 수 있다.

예를 들어 다음 파일은 디렉터리 목록이 보이지 않아도 직접 요청할 수 있다.

```text
http://172.168.10.10/backup.zip
http://172.168.10.10/config.php.bak
http://172.168.10.10/phpinfo.php
```

따라서 WEB-07은 “목록이 보이는가”가 아니라 “불필요한 파일이 웹 서비스 경로 안에 존재하는가”를 기준으로 판단한다.

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

이 노트는 CARE 서버의 DocumentRoot가 `/var/www/care`라고 가정한다.

실습용 변수를 지정한다.

```bash
APP_ROOT=/var/www/care
SERVER=http://172.168.10.10
TEST_DIR="$APP_ROOT/web07-unused"
```

현재 서버의 DocumentRoot가 다르면 `APP_ROOT` 값을 실제 경로로 바꾼다.

### 4-3. 현재 불필요 파일 점검

대표적인 백업, 테스트, 임시 파일을 찾는다.

```bash
sudo find "$APP_ROOT" -type f \( \
  -name "*.bak" -o \
  -name "*.old" -o \
  -name "*.orig" -o \
  -name "*.save" -o \
  -name "*~" -o \
  -name "*.swp" -o \
  -name "*.tmp" -o \
  -name "*.zip" -o \
  -name "*.tar" -o \
  -name "*.tar.gz" -o \
  -name "*.sql" -o \
  -name "phpinfo.php" -o \
  -name "test.php" \
\) -print
```

대표적인 샘플, 매뉴얼, 테스트 디렉터리를 찾는다.

```bash
sudo find "$APP_ROOT" -type d \( \
  -name "manual" -o \
  -name "docs" -o \
  -name "sample" -o \
  -name "samples" -o \
  -name "test" -o \
  -name "backup" \
\) -print
```

최초 양호 상태라면 출력이 없거나, 서비스 운영에 필요한 파일만 나와야 한다.

## 5. 취약 재현

이 항목은 최초 진단 결과가 양호이므로, PDF 내용을 실습하기 위해 의도적으로 취약 상태를 재현한다.

> 주의: 이 절차는 격리된 실습 서버에서만 수행한다.  
> 실제 중요 파일이나 운영 백업 파일을 웹 루트에 두지 않는다.  
> 실습용 파일만 만들고, 증거 확보 후 즉시 제거한다.

취약 재현의 핵심은 다음이다.

```text
웹 서비스 경로 안에 백업 파일, 테스트 파일, 매뉴얼 디렉터리 같은 불필요 파일을 만든 뒤 외부에서 접근 가능한지 확인한다.
```

### 5-1. 실습용 불필요 디렉터리 생성

```bash
sudo mkdir -p "$TEST_DIR/manual"
sudo mkdir -p "$TEST_DIR/sample"
```

### 5-2. 실습용 불필요 파일 생성

백업 파일 형태의 테스트 파일을 만든다.

```bash
echo "WEB-07 backup test file" | sudo tee "$TEST_DIR/config.php.bak"
```

이전 버전 파일 형태의 테스트 파일을 만든다.

```bash
echo "WEB-07 old file" | sudo tee "$TEST_DIR/index.php.old"
```

DB 덤프처럼 보이는 테스트 파일을 만든다.

```bash
echo "WEB-07 fake sql dump" | sudo tee "$TEST_DIR/db_dump.sql"
```

테스트 PHP 파일을 만든다.

```bash
sudo tee "$TEST_DIR/test.php" > /dev/null <<'EOF'
<?php
echo "WEB-07 test php file";
EOF
```

매뉴얼 디렉터리 파일을 만든다.

```bash
echo "WEB-07 manual page" | sudo tee "$TEST_DIR/manual/index.html"
```

샘플 디렉터리 파일을 만든다.

```bash
echo "WEB-07 sample page" | sudo tee "$TEST_DIR/sample/index.html"
```

### 5-3. 파일 생성 확인

```bash
sudo find "$TEST_DIR" -maxdepth 3 -type f -print
```

기대 결과는 다음과 유사하다.

```text
/var/www/care/web07-unused/config.php.bak
/var/www/care/web07-unused/index.php.old
/var/www/care/web07-unused/db_dump.sql
/var/www/care/web07-unused/test.php
/var/www/care/web07-unused/manual/index.html
/var/www/care/web07-unused/sample/index.html
```

### 5-4. 불필요 파일 탐지 확인

실습 전 확인에서 사용한 탐지 명령어를 다시 실행한다.

```bash
sudo find "$APP_ROOT" -type f \( \
  -name "*.bak" -o \
  -name "*.old" -o \
  -name "*.orig" -o \
  -name "*.save" -o \
  -name "*~" -o \
  -name "*.swp" -o \
  -name "*.tmp" -o \
  -name "*.zip" -o \
  -name "*.tar" -o \
  -name "*.tar.gz" -o \
  -name "*.sql" -o \
  -name "phpinfo.php" -o \
  -name "test.php" \
\) -print
```

취약 재현 상태라면 다음 파일들이 탐지되어야 한다.

```text
/var/www/care/web07-unused/config.php.bak
/var/www/care/web07-unused/index.php.old
/var/www/care/web07-unused/db_dump.sql
/var/www/care/web07-unused/test.php
```

디렉터리 탐지도 다시 수행한다.

```bash
sudo find "$APP_ROOT" -type d \( \
  -name "manual" -o \
  -name "docs" -o \
  -name "sample" -o \
  -name "samples" -o \
  -name "test" -o \
  -name "backup" \
\) -print
```

취약 재현 상태라면 다음 디렉터리가 탐지되어야 한다.

```text
/var/www/care/web07-unused/manual
/var/www/care/web07-unused/sample
```

### 5-5. 외부 접근 확인

백업 파일처럼 보이는 파일에 접근한다.

```bash
curl -i "$SERVER/web07-unused/config.php.bak"
```

취약 재현 상태에서 기대 결과는 다음과 같다.

```text
HTTP/1.1 200 OK

WEB-07 backup test file
```

DB 덤프처럼 보이는 파일에 접근한다.

```bash
curl -i "$SERVER/web07-unused/db_dump.sql"
```

취약 재현 상태에서 기대 결과는 다음과 같다.

```text
HTTP/1.1 200 OK

WEB-07 fake sql dump
```

매뉴얼 디렉터리 파일에 접근한다.

```bash
curl -i "$SERVER/web07-unused/manual/"
```

취약 재현 상태에서 기대 결과는 다음과 같다.

```text
HTTP/1.1 200 OK

WEB-07 manual page
```

이 결과는 불필요한 파일과 디렉터리가 웹 서비스 경로 안에 존재하고, 외부에서 접근 가능하다는 뜻이다. PDF 기준으로는 취약 상태다.

## 6. 조치 방법

조치 핵심은 웹 서비스 경로 안의 불필요 파일과 디렉터리를 제거하는 것이다.

운영 환경에서는 삭제 전에 해당 파일이 실제 서비스에 필요한지 확인해야 한다.  
실습에서는 우리가 만든 `web07-unused` 디렉터리만 제거한다.

### 6-1. 삭제 전 제거 대상 확인

```bash
sudo find "$TEST_DIR" -maxdepth 3 -print
```

### 6-2. 실습용 불필요 파일 제거

```bash
sudo rm -f "$TEST_DIR/config.php.bak"
sudo rm -f "$TEST_DIR/index.php.old"
sudo rm -f "$TEST_DIR/db_dump.sql"
sudo rm -f "$TEST_DIR/test.php"
```

### 6-3. 실습용 불필요 디렉터리 제거

```bash
sudo rm -rf "$TEST_DIR/manual"
sudo rm -rf "$TEST_DIR/sample"
```

### 6-4. 실습용 상위 디렉터리 제거

```bash
sudo rmdir "$TEST_DIR" 2>/dev/null || true
```

### 6-5. Apache 설정 문법 검사

WEB-07은 파일 제거 항목이므로 Apache 설정을 바꾸지는 않는다.  
그래도 실습 후 웹 서비스 상태를 확인하는 의미로 문법 검사를 수행한다.

```bash
sudo apachectl configtest
```

정상이라면 다음 결과가 나와야 한다.

```text
Syntax OK
```

### 6-6. Apache restart

파일 제거만으로는 일반적으로 Apache restart가 필요하지 않다.  
다만 실습 노트의 공통 흐름에 맞춰 서비스 상태를 정리하고 확인한다.

```bash
sudo systemctl restart apache2
```

## 7. 조치 후 확인

조치 후에는 불필요 파일과 디렉터리가 제거되었는지 확인한다.

### 7-1. 실습 디렉터리 제거 확인

```bash
ls -ld "$TEST_DIR" 2>/dev/null
```

기대 결과는 다음이다.

```text
출력 없음
```

### 7-2. 불필요 파일 재탐지

```bash
sudo find "$APP_ROOT" -type f \( \
  -name "*.bak" -o \
  -name "*.old" -o \
  -name "*.orig" -o \
  -name "*.save" -o \
  -name "*~" -o \
  -name "*.swp" -o \
  -name "*.tmp" -o \
  -name "*.zip" -o \
  -name "*.tar" -o \
  -name "*.tar.gz" -o \
  -name "*.sql" -o \
  -name "phpinfo.php" -o \
  -name "test.php" \
\) -print
```

기대 결과는 다음이다.

```text
출력 없음
```

단, 실제 서비스에서 필요한 파일이 출력되면 바로 삭제하지 않고 별도 확인한다.

### 7-3. 불필요 디렉터리 재탐지

```bash
sudo find "$APP_ROOT" -type d \( \
  -name "manual" -o \
  -name "docs" -o \
  -name "sample" -o \
  -name "samples" -o \
  -name "test" -o \
  -name "backup" \
\) -print
```

기대 결과는 다음이다.

```text
출력 없음
```

### 7-4. HTTP 접근 차단 확인

삭제한 파일에 다시 접근한다.

```bash
curl -i "$SERVER/web07-unused/config.php.bak"
```

기대 결과는 다음이다.

```text
HTTP/1.1 404 Not Found
```

DB 덤프처럼 보이는 파일도 확인한다.

```bash
curl -i "$SERVER/web07-unused/db_dump.sql"
```

기대 결과는 다음이다.

```text
HTTP/1.1 404 Not Found
```

매뉴얼 디렉터리도 확인한다.

```bash
curl -i "$SERVER/web07-unused/manual/"
```

기대 결과는 다음이다.

```text
HTTP/1.1 404 Not Found
```

중요한 것은 다음 내용들이 더 이상 출력되지 않는 것이다.

```text
WEB-07 backup test file
WEB-07 fake sql dump
WEB-07 manual page
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
APP_ROOT=/var/www/care
SERVER=http://172.168.10.10
TEST_DIR="$APP_ROOT/web07-unused"
```

```bash
sudo find "$APP_ROOT" -type f \( \
  -name "*.bak" -o \
  -name "*.old" -o \
  -name "*.orig" -o \
  -name "*.save" -o \
  -name "*~" -o \
  -name "*.swp" -o \
  -name "*.tmp" -o \
  -name "*.zip" -o \
  -name "*.tar" -o \
  -name "*.tar.gz" -o \
  -name "*.sql" -o \
  -name "phpinfo.php" -o \
  -name "test.php" \
\) -print
```

```bash
sudo find "$APP_ROOT" -type d \( \
  -name "manual" -o \
  -name "docs" -o \
  -name "sample" -o \
  -name "samples" -o \
  -name "test" -o \
  -name "backup" \
\) -print
```

### 8-2. 취약 재현

```bash
sudo mkdir -p "$TEST_DIR/manual"
sudo mkdir -p "$TEST_DIR/sample"
```

```bash
echo "WEB-07 backup test file" | sudo tee "$TEST_DIR/config.php.bak"
```

```bash
echo "WEB-07 old file" | sudo tee "$TEST_DIR/index.php.old"
```

```bash
echo "WEB-07 fake sql dump" | sudo tee "$TEST_DIR/db_dump.sql"
```

```bash
sudo tee "$TEST_DIR/test.php" > /dev/null <<'EOF'
<?php
echo "WEB-07 test php file";
EOF
```

```bash
echo "WEB-07 manual page" | sudo tee "$TEST_DIR/manual/index.html"
```

```bash
echo "WEB-07 sample page" | sudo tee "$TEST_DIR/sample/index.html"
```

```bash
sudo find "$TEST_DIR" -maxdepth 3 -type f -print
```

```bash
curl -i "$SERVER/web07-unused/config.php.bak"
```

```bash
curl -i "$SERVER/web07-unused/db_dump.sql"
```

```bash
curl -i "$SERVER/web07-unused/manual/"
```

취약 상태 기대 결과:

```text
HTTP/1.1 200 OK

WEB-07 backup test file
```

또는:

```text
HTTP/1.1 200 OK

WEB-07 fake sql dump
```

또는:

```text
HTTP/1.1 200 OK

WEB-07 manual page
```

### 8-3. 조치 및 복구

```bash
sudo find "$TEST_DIR" -maxdepth 3 -print
```

```bash
sudo rm -f "$TEST_DIR/config.php.bak"
sudo rm -f "$TEST_DIR/index.php.old"
sudo rm -f "$TEST_DIR/db_dump.sql"
sudo rm -f "$TEST_DIR/test.php"
```

```bash
sudo rm -rf "$TEST_DIR/manual"
sudo rm -rf "$TEST_DIR/sample"
```

```bash
sudo rmdir "$TEST_DIR" 2>/dev/null || true
```

```bash
sudo apachectl configtest
```

```bash
sudo systemctl restart apache2
```

### 8-4. 조치 후 확인

```bash
ls -ld "$TEST_DIR" 2>/dev/null
```

기대 결과:

```text
출력 없음
```

```bash
sudo find "$APP_ROOT" -type f \( \
  -name "*.bak" -o \
  -name "*.old" -o \
  -name "*.orig" -o \
  -name "*.save" -o \
  -name "*~" -o \
  -name "*.swp" -o \
  -name "*.tmp" -o \
  -name "*.zip" -o \
  -name "*.tar" -o \
  -name "*.tar.gz" -o \
  -name "*.sql" -o \
  -name "phpinfo.php" -o \
  -name "test.php" \
\) -print
```

```bash
sudo find "$APP_ROOT" -type d \( \
  -name "manual" -o \
  -name "docs" -o \
  -name "sample" -o \
  -name "samples" -o \
  -name "test" -o \
  -name "backup" \
\) -print
```

```bash
curl -i "$SERVER/web07-unused/config.php.bak"
```

```bash
curl -i "$SERVER/web07-unused/db_dump.sql"
```

```bash
curl -i "$SERVER/web07-unused/manual/"
```

조치 후 기대 결과:

```text
HTTP/1.1 404 Not Found
```

## 9. 증거 정리

### 9-1. 최초 상태 증거

최초 진단 결과:

```text
WEB-07 · 불필요한 파일 제거
백업, 샘플, 테스트 파일 등 불필요한 파일 발견되지 않음

No unnecessary files found
```

불필요 파일 탐지 명령어:

```bash
sudo find "$APP_ROOT" -type f \( \
  -name "*.bak" -o \
  -name "*.old" -o \
  -name "*.orig" -o \
  -name "*.save" -o \
  -name "*~" -o \
  -name "*.swp" -o \
  -name "*.tmp" -o \
  -name "*.zip" -o \
  -name "*.tar" -o \
  -name "*.tar.gz" -o \
  -name "*.sql" -o \
  -name "phpinfo.php" -o \
  -name "test.php" \
\) -print
```

기대 결과:

```text
출력 없음
```

### 9-2. 취약 재현 증거

불필요 파일 생성 후 탐지 결과:

```bash
sudo find "$TEST_DIR" -maxdepth 3 -type f -print
```

기대 결과:

```text
/var/www/care/web07-unused/config.php.bak
/var/www/care/web07-unused/index.php.old
/var/www/care/web07-unused/db_dump.sql
/var/www/care/web07-unused/test.php
/var/www/care/web07-unused/manual/index.html
/var/www/care/web07-unused/sample/index.html
```

외부 접근 확인:

```bash
curl -i "$SERVER/web07-unused/config.php.bak"
```

취약 재현 기대 결과:

```text
HTTP/1.1 200 OK

WEB-07 backup test file
```

### 9-3. 조치 후 증거

파일 제거 후 탐지 결과:

```bash
ls -ld "$TEST_DIR" 2>/dev/null
```

기대 결과:

```text
출력 없음
```

삭제 파일 접근 확인:

```bash
curl -i "$SERVER/web07-unused/config.php.bak"
```

조치 후 기대 결과:

```text
HTTP/1.1 404 Not Found
```

## 10. 판단

|항목|판단|
|---|---|
|최초 진단|양호|
|진단 근거|백업, 샘플, 테스트 파일 등 불필요한 파일 발견되지 않음|
|실습 처리|실습용 백업 파일, 테스트 파일, 매뉴얼 디렉터리를 생성하여 취약 상태 재현 후 제거|
|조치 전 판단|최초 상태는 양호, 실습 재현 상태는 취약|
|조치 후 판단|실습용 불필요 파일 제거 후 양호|
|증거 상태|최초 진단 결과 확보, 취약 재현 및 조치 후 접근 증거 필요|

현재 서버는 최초 진단 기준으로 백업, 샘플, 테스트 파일 등 불필요한 파일이 발견되지 않았으므로 WEB-07은 **양호**로 판단한다.

다만 PDF의 취약 조건을 실습하기 위해 웹 서비스 경로 안에 `config.php.bak`, `index.php.old`, `db_dump.sql`, `test.php`, `manual/`, `sample/` 같은 실습용 불필요 파일과 디렉터리를 만들면 취약 상태를 재현할 수 있다.

조치는 웹 서비스 경로 안의 불필요 파일과 디렉터리를 제거하는 방식으로 수행한다.

조치 후 탐지 명령어에서 불필요 파일이 출력되지 않고, 기존 파일 URL 요청이 `404 Not Found`로 처리되면 WEB-07은 조치 후 **양호**로 판단한다.