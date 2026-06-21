---

type: lab  
topic: web-service-security  
source: 주요정보통신기반시설 기술적 취약점 분석·평가 방법 상세가이드  
source_pages:

- 322
    
- 323
    
- 324  
status: draft  
created: 2026-06-18  
tags:
    
- 🏷️과목/웹서비스보안
    
- 🏷️주제/WEB-18
    
- 🏷️주제/WebDAV
    
- 🏷️주제/Apache
    
- 🏷️상태/draft
    

---
# WEB-18 웹 서비스 WebDAV 비활성화

## 1. PDF 기준

PDF p.322-324의 WEB-18은 웹 서비스에서 **WebDAV 기능이 비활성화되어 있는지** 점검하는 항목이다.

WebDAV는 HTTP를 확장하여 원격 웹 서버의 파일을 생성, 수정, 삭제, 이동, 복사할 수 있게 하는 기능이다.

WebDAV가 활성화되면 일반적인 조회용 HTTP 메서드 외에 다음과 같은 메서드가 사용될 수 있다.

```text
PROPFIND
PUT
DELETE
MKCOL
COPY
MOVE
LOCK
UNLOCK
```

이 기능이 불필요하게 활성화되어 있으면 공격자가 웹 서버를 단순 조회 대상이 아니라 원격 파일 저장소처럼 악용할 수 있다.

보안 위협은 다음과 같다.

```text
1. 인증 우회 취약점이 존재할 경우 보호된 WebDAV 자원에 접근할 수 있다.
2. 디렉터리 열람, 파일 다운로드, 파일 업로드가 가능해질 수 있다.
3. PUT, DELETE, MOVE 같은 메서드가 허용되면 웹 루트 파일 변조로 이어질 수 있다.
4. WebDAV 처리 구성요소의 취약점으로 버퍼 오버런 등 추가 공격 위험이 발생할 수 있다.
```

PDF의 판단 기준은 다음과 같다.

|판단|기준|
|---|---|
|양호|WebDAV 서비스를 비활성화하고 있는 경우|
|취약|WebDAV 서비스를 활성화하고 있는 경우|

Apache 기준으로는 다음을 확인한다.

|확인 대상|의미|
|---|---|
|`dav_module`|WebDAV 공통 모듈|
|`dav_fs_module`|파일 시스템 기반 WebDAV 모듈|
|`Dav On`|특정 경로에서 WebDAV 기능 활성화|
|`DAVLockDB`|WebDAV 잠금 데이터베이스 설정|
|`OPTIONS` 응답|WebDAV 관련 메서드와 `DAV` 헤더 노출 여부|
|`PUT`, `PROPFIND` 요청|실제 WebDAV 동작 여부|

취약 설정 예시는 다음과 같다.

```apache
<Directory "/path/to/directory">
    Dav On
</Directory>
```

조치 방향은 다음과 같다.

```apache
<Directory "/path/to/directory">
    Dav Off
</Directory>
```

또는 불필요한 WebDAV 설정과 모듈을 제거한다.

## 2. 최초 진단 결과

`AWS WEB 약점 진단 결과.md` 기준 최초 진단 결과는 **양호**이다.

|항목|내용|
|---|---|
|진단 결과|양호|
|진단 근거|`DAV On` 설정 없음|
|진단 결과 메시지|`DAV disabled or not loaded`|
|관련 설정|Apache `dav`, `dav_fs` 모듈 및 `Dav` 지시자|
|최초 판단|WebDAV가 비활성화되어 있으므로 양호|

최초 진단 결과는 다음과 같다.

```text
WEB-18 · WebDAV 비활성화

DAV On 설정 없음 — WebDAV 비활성화 확인

DAV disabled or not loaded
```

따라서 현재 최초 상태에서는 WebDAV가 활성화되어 있지 않은 것으로 판단한다.

## 3. 현재 서버 상태 해석

WEB-18은 Apache에서 WebDAV 모듈이 로드되어 있는지, 그리고 실제 경로에 `Dav On`이 적용되어 있는지를 확인하는 항목이다.

단순히 `dav_module`이 로드되어 있다고 해서 곧바로 취약이라고 단정하지는 않는다. 실제로 특정 디렉터리나 Location에 `Dav On`이 설정되어 있어야 WebDAV 기능이 동작한다.

판단 기준은 다음과 같이 나눈다.

|상태|판단|
|---|---|
|`dav_module` 미로드, `Dav On` 없음|양호|
|`dav_module` 로드됨, `Dav On` 없음|대체로 양호이나 불필요 모듈이면 제거 권장|
|`Dav On` 존재|취약|
|`OPTIONS` 응답에 `DAV` 헤더 또는 WebDAV 메서드 노출|취약 가능성 높음|
|`PUT` 요청으로 파일 생성 가능|취약|

Apache에서 WebDAV가 활성화된 경로는 웹 서버를 원격 파일 편집 공간처럼 만들 수 있다.

예를 들어 `/web18-dav/` 경로에 WebDAV가 켜져 있고 인증이 없다면 다음과 같은 요청이 가능할 수 있다.

```bash
curl -X PUT --data 'test' http://서버주소/web18-dav/test.txt
```

정상적으로 파일이 생성된다면 매우 위험한 상태다.

이 항목은 WEB-23 HTTP 메서드 제한과 연결된다. WebDAV가 켜져 있으면 `PUT`, `DELETE`, `PROPFIND`, `MKCOL` 같은 메서드가 사용될 수 있으므로, WebDAV 비활성화와 HTTP 메서드 제한은 함께 확인하는 것이 좋다.

## 4. 실습 전 확인

실습을 시작하기 전에 현재 Apache 모듈, WebDAV 설정, HTTP 응답을 확인한다.

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
TEST_DIR="$APP_ROOT/web18-dav"
TEST_CONF=/etc/apache2/conf-available/web-18-dav-test.conf
DAV_LOCK=/tmp/web18-dav-lock
DAV_MARKER=/tmp/web18-dav-module-was-enabled
DAVFS_MARKER=/tmp/web18-davfs-module-was-enabled
```

현재 서버의 DocumentRoot가 다르면 `APP_ROOT` 값을 실제 경로로 바꾼다.

### 4-3. WebDAV 관련 모듈 확인

```bash
apache2ctl -M | grep -E "dav|dav_fs"
```

양호 상태에서는 출력이 없거나, 모듈은 로드되어 있더라도 `Dav On` 설정은 없어야 한다.

출력 없음 예시:

```text
출력 없음
```

모듈 로드 예시:

```text
dav_module (shared)
dav_fs_module (shared)
```

### 4-4. WebDAV 설정 확인

```bash
grep -Ri "^[[:space:]]*Dav[[:space:]]\|^[[:space:]]*DAVLockDB" \
/etc/apache2/apache2.conf \
/etc/apache2/sites-enabled/ \
/etc/apache2/sites-available/ \
/etc/apache2/conf-enabled/ \
/etc/apache2/conf-available/ 2>/dev/null | grep -v '^\s*#'
```

양호 상태라면 `Dav On`이 없어야 한다.

```text
출력 없음
```

### 4-5. OPTIONS 응답 확인

```bash
curl -i -X OPTIONS "$SERVER/"
```

정상 상태에서는 `DAV:` 헤더가 없어야 하며, `Allow` 헤더에 WebDAV 전용 메서드가 불필요하게 포함되지 않아야 한다.

헤더만 정리해서 확인한다.

```bash
curl -s -D - -o /dev/null -X OPTIONS "$SERVER/" | grep -iE '^Allow:|^DAV:'
```

양호 상태 기대 결과 예시는 다음과 같다.

```text
Allow: GET,POST,OPTIONS,HEAD
```

다음과 같이 `DAV` 헤더나 WebDAV 메서드가 보이면 취약 가능성이 있다.

```text
DAV: 1,2
Allow: OPTIONS, GET, HEAD, POST, PUT, DELETE, PROPFIND, MKCOL, COPY, MOVE
```

### 4-6. 실습 전 모듈 상태 기록

실습 후 원래 상태로 되돌리기 위해 현재 모듈 상태를 기록한다.

```bash
if apache2ctl -M | grep -q "dav_module"; then
  echo "yes" | sudo tee "$DAV_MARKER"
else
  echo "no" | sudo tee "$DAV_MARKER"
fi
```

```bash
if apache2ctl -M | grep -q "dav_fs_module"; then
  echo "yes" | sudo tee "$DAVFS_MARKER"
else
  echo "no" | sudo tee "$DAVFS_MARKER"
fi
```

기록 결과를 확인한다.

```bash
cat "$DAV_MARKER"
cat "$DAVFS_MARKER"
```

## 5. 취약 재현

이 항목은 최초 진단 결과가 양호이므로, PDF 내용을 실습하기 위해 의도적으로 WebDAV를 활성화한다.

> 주의: 이 절차는 격리된 실습 서버에서만 수행한다.  
> 실습용 디렉터리에서만 `Dav On`을 적용한다.  
> 인증 없는 WebDAV는 위험하므로 증거 확보 후 즉시 제거한다.  
> 운영 서버에서는 WebDAV를 불필요하게 활성화하지 않는다.

취약 재현의 핵심은 다음이다.

```text
Apache에 dav, dav_fs 모듈을 활성화하고,
실습용 디렉터리에 Dav On을 적용한 뒤,
PUT 요청으로 파일 생성이 가능한지 확인한다.
```

### 5-1. 실습용 WebDAV 디렉터리 생성

```bash
sudo mkdir -p "$TEST_DIR"
```

WebDAV에서 파일 쓰기가 가능하도록 실습 디렉터리 소유권을 `www-data`로 설정한다.

```bash
sudo chown -R www-data:www-data "$TEST_DIR"
```

권한을 확인한다.

```bash
stat -c '%A %U:%G %n' "$TEST_DIR"
```

기대 결과 예시는 다음과 같다.

```text
drwxr-xr-x www-data:www-data /var/www/care/web18-dav
```

### 5-2. WebDAV 모듈 활성화

```bash
sudo a2enmod dav dav_fs
```

이미 활성화되어 있으면 다음과 유사한 메시지가 나올 수 있다.

```text
Module dav already enabled
Module dav_fs already enabled
```

### 5-3. 실습용 WebDAV 설정 생성

```bash
sudo tee "$TEST_CONF" > /dev/null <<EOF
DAVLockDB $DAV_LOCK

<Directory "$TEST_DIR">
    Dav On
    Options Indexes
    AllowOverride None
    Require all granted
</Directory>
EOF
```

취약 재현의 핵심 설정은 다음이다.

```apache
Dav On
```

이 설정은 `$TEST_DIR`에서 WebDAV 기능을 활성화한다.

### 5-4. 실습용 설정 활성화

```bash
sudo a2enconf web-18-dav-test
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

### 5-7. WebDAV OPTIONS 응답 확인

```bash
curl -s -D - -o /dev/null -X OPTIONS "$SERVER/web18-dav/" | grep -iE '^Allow:|^DAV:'
```

취약 재현 상태에서는 다음과 유사한 응답이 나올 수 있다.

```text
DAV: 1,2
Allow: OPTIONS, GET, HEAD, POST, PUT, DELETE, TRACE, PROPFIND, PROPPATCH, COPY, MOVE, LOCK, UNLOCK
```

환경에 따라 표시되는 메서드는 다를 수 있다.  
중요한 것은 `DAV:` 헤더 또는 WebDAV 관련 메서드가 노출되는지다.

### 5-8. PUT 요청으로 파일 생성 확인

```bash
curl -i -X PUT --data 'WEB-18 WebDAV PUT test' "$SERVER/web18-dav/put-test.txt"
```

취약 재현 상태에서 기대 결과는 다음 중 하나다.

```text
HTTP/1.1 201 Created
```

또는:

```text
HTTP/1.1 204 No Content
```

### 5-9. 생성된 파일 확인

```bash
curl -i "$SERVER/web18-dav/put-test.txt"
```

취약 재현 상태에서 기대 결과는 다음과 같다.

```text
HTTP/1.1 200 OK

WEB-18 WebDAV PUT test
```

이 결과는 WebDAV가 활성화되어 외부 요청으로 웹 서비스 경로에 파일 생성이 가능하다는 뜻이다.

PDF 기준으로는 취약 상태다.

### 5-10. PROPFIND 요청 확인

```bash
curl -i -X PROPFIND -H "Depth: 1" "$SERVER/web18-dav/"
```

취약 재현 상태에서는 다음과 유사한 응답이 나올 수 있다.

```text
HTTP/1.1 207 Multi-Status
```

`207 Multi-Status`는 WebDAV 리소스 조회 응답으로 볼 수 있다.

## 6. 조치 방법

조치 핵심은 WebDAV 기능을 비활성화하는 것이다.

실습에서는 `Dav On` 설정을 제거하고, 테스트 파일과 모듈 상태를 원복한다.

### 6-1. 실습용 WebDAV 설정 비활성화

```bash
sudo a2disconf web-18-dav-test
```

### 6-2. 실습용 WebDAV 설정 파일 제거

```bash
sudo rm -f "$TEST_CONF"
```

### 6-3. 실습용 WebDAV 디렉터리 제거

```bash
sudo rm -rf "$TEST_DIR"
```

### 6-4. DAVLockDB 파일 제거

```bash
sudo rm -f "$DAV_LOCK" "$DAV_LOCK".*
```

### 6-5. WebDAV 모듈 원복

실습 전에 `dav_fs` 모듈이 비활성화되어 있었다면 다시 비활성화한다.

```bash
if [ "$(cat "$DAVFS_MARKER" 2>/dev/null)" = "no" ]; then
  sudo a2dismod dav_fs
fi
```

실습 전에 `dav` 모듈이 비활성화되어 있었다면 다시 비활성화한다.

```bash
if [ "$(cat "$DAV_MARKER" 2>/dev/null)" = "no" ]; then
  sudo a2dismod dav
fi
```

`dav_fs`는 `dav`에 의존하므로 `dav_fs`를 먼저 비활성화하고, 그 다음 `dav`를 비활성화한다.

### 6-6. 실습용 마커 제거

```bash
sudo rm -f "$DAV_MARKER" "$DAVFS_MARKER"
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

조치 후에는 WebDAV 설정이 제거되었고, WebDAV 요청이 더 이상 동작하지 않는지 확인한다.

### 7-1. WebDAV 설정 제거 확인

```bash
grep -Ri "^[[:space:]]*Dav[[:space:]]\|^[[:space:]]*DAVLockDB" \
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

### 7-2. WebDAV 모듈 상태 확인

```bash
apache2ctl -M | grep -E "dav|dav_fs"
```

실습 전부터 모듈이 비활성화되어 있었다면 조치 후에도 출력이 없어야 한다.

```text
출력 없음
```

실습 전부터 모듈이 활성화되어 있었다면 모듈 출력이 남을 수 있다.  
이 경우에도 `Dav On` 설정이 없으면 WebDAV 기능은 활성화되지 않은 것으로 볼 수 있다.

### 7-3. OPTIONS 응답 확인

```bash
curl -s -D - -o /dev/null -X OPTIONS "$SERVER/web18-dav/" | grep -iE '^Allow:|^DAV:'
```

조치 후에는 `DAV:` 헤더가 나오지 않아야 한다.

```text
DAV 헤더 없음
```

또는 해당 경로가 제거되었기 때문에 다음처럼 나올 수 있다.

```text
HTTP/1.1 404 Not Found
```

### 7-4. PUT 요청 차단 확인

```bash
curl -i -X PUT --data 'WEB-18 should be blocked' "$SERVER/web18-dav/put-test-after.txt"
```

조치 후 기대 결과는 다음 중 하나다.

```text
HTTP/1.1 404 Not Found
```

또는:

```text
HTTP/1.1 405 Method Not Allowed
```

또는:

```text
HTTP/1.1 403 Forbidden
```

중요한 것은 다음처럼 파일이 생성되지 않는 것이다.

```text
HTTP/1.1 201 Created
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
TEST_DIR="$APP_ROOT/web18-dav"
TEST_CONF=/etc/apache2/conf-available/web-18-dav-test.conf
DAV_LOCK=/tmp/web18-dav-lock
DAV_MARKER=/tmp/web18-dav-module-was-enabled
DAVFS_MARKER=/tmp/web18-davfs-module-was-enabled
```

```bash
apache2ctl -S
```

```bash
grep -R "DocumentRoot" /etc/apache2/sites-enabled/ /etc/apache2/sites-available/ 2>/dev/null
```

```bash
apache2ctl -M | grep -E "dav|dav_fs"
```

```bash
grep -Ri "^[[:space:]]*Dav[[:space:]]\|^[[:space:]]*DAVLockDB" \
/etc/apache2/apache2.conf \
/etc/apache2/sites-enabled/ \
/etc/apache2/sites-available/ \
/etc/apache2/conf-enabled/ \
/etc/apache2/conf-available/ 2>/dev/null | grep -v '^\s*#'
```

```bash
curl -s -D - -o /dev/null -X OPTIONS "$SERVER/" | grep -iE '^Allow:|^DAV:'
```

```bash
if apache2ctl -M | grep -q "dav_module"; then
  echo "yes" | sudo tee "$DAV_MARKER"
else
  echo "no" | sudo tee "$DAV_MARKER"
fi
```

```bash
if apache2ctl -M | grep -q "dav_fs_module"; then
  echo "yes" | sudo tee "$DAVFS_MARKER"
else
  echo "no" | sudo tee "$DAVFS_MARKER"
fi
```

### 8-2. 취약 재현

```bash
sudo mkdir -p "$TEST_DIR"
```

```bash
sudo chown -R www-data:www-data "$TEST_DIR"
```

```bash
sudo a2enmod dav dav_fs
```

```bash
sudo tee "$TEST_CONF" > /dev/null <<EOF
DAVLockDB $DAV_LOCK

<Directory "$TEST_DIR">
    Dav On
    Options Indexes
    AllowOverride None
    Require all granted
</Directory>
EOF
```

```bash
sudo a2enconf web-18-dav-test
```

```bash
sudo apachectl configtest
```

```bash
sudo systemctl restart apache2
```

```bash
curl -s -D - -o /dev/null -X OPTIONS "$SERVER/web18-dav/" | grep -iE '^Allow:|^DAV:'
```

```bash
curl -i -X PUT --data 'WEB-18 WebDAV PUT test' "$SERVER/web18-dav/put-test.txt"
```

```bash
curl -i "$SERVER/web18-dav/put-test.txt"
```

```bash
curl -i -X PROPFIND -H "Depth: 1" "$SERVER/web18-dav/"
```

취약 상태 기대 결과:

```text
DAV: 1,2
HTTP/1.1 201 Created
HTTP/1.1 200 OK

WEB-18 WebDAV PUT test
HTTP/1.1 207 Multi-Status
```

### 8-3. 조치 및 복구

```bash
sudo a2disconf web-18-dav-test
```

```bash
sudo rm -f "$TEST_CONF"
```

```bash
sudo rm -rf "$TEST_DIR"
```

```bash
sudo rm -f "$DAV_LOCK" "$DAV_LOCK".*
```

```bash
if [ "$(cat "$DAVFS_MARKER" 2>/dev/null)" = "no" ]; then
  sudo a2dismod dav_fs
fi
```

```bash
if [ "$(cat "$DAV_MARKER" 2>/dev/null)" = "no" ]; then
  sudo a2dismod dav
fi
```

```bash
sudo rm -f "$DAV_MARKER" "$DAVFS_MARKER"
```

```bash
sudo apachectl configtest
```

```bash
sudo systemctl restart apache2
```

### 8-4. 조치 후 확인

```bash
grep -Ri "^[[:space:]]*Dav[[:space:]]\|^[[:space:]]*DAVLockDB" \
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
apache2ctl -M | grep -E "dav|dav_fs"
```

기대 결과:

```text
출력 없음
```

단, 실습 전부터 WebDAV 모듈이 활성화되어 있었다면 모듈 출력은 남을 수 있다.

```bash
curl -i -X PUT --data 'WEB-18 should be blocked' "$SERVER/web18-dav/put-test-after.txt"
```

조치 후 기대 결과:

```text
HTTP/1.1 404 Not Found
```

또는:

```text
HTTP/1.1 405 Method Not Allowed
```

또는:

```text
HTTP/1.1 403 Forbidden
```

```bash
systemctl status apache2 --no-pager
```

```bash
curl -i "$SERVER/"
```

### 8-5. 실습 환경 제거 확인

```bash
ls -ld "$TEST_DIR" "$TEST_CONF" "$DAV_MARKER" "$DAVFS_MARKER" 2>/dev/null
```

기대 결과:

```text
출력 없음
```

```bash
ls -l "$DAV_LOCK"* 2>/dev/null
```

기대 결과:

```text
출력 없음
```

## 9. 증거 정리

### 9-1. 최초 상태 증거

최초 진단 결과:

```text
WEB-18 · WebDAV 비활성화

DAV On 설정 없음 — WebDAV 비활성화 확인

DAV disabled or not loaded
```

WebDAV 설정 확인 명령어:

```bash
grep -Ri "^[[:space:]]*Dav[[:space:]]\|^[[:space:]]*DAVLockDB" \
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
DAVLockDB /tmp/web18-dav-lock

<Directory "/var/www/care/web18-dav">
    Dav On
    Options Indexes
    AllowOverride None
    Require all granted
</Directory>
```

WebDAV OPTIONS 확인:

```bash
curl -s -D - -o /dev/null -X OPTIONS "$SERVER/web18-dav/" | grep -iE '^Allow:|^DAV:'
```

취약 상태 기대 결과:

```text
DAV: 1,2
Allow: OPTIONS, GET, HEAD, POST, PUT, DELETE, PROPFIND, PROPPATCH, COPY, MOVE, LOCK, UNLOCK
```

PUT 요청 확인:

```bash
curl -i -X PUT --data 'WEB-18 WebDAV PUT test' "$SERVER/web18-dav/put-test.txt"
```

취약 상태 기대 결과:

```text
HTTP/1.1 201 Created
```

생성 파일 확인:

```bash
curl -i "$SERVER/web18-dav/put-test.txt"
```

취약 상태 기대 결과:

```text
HTTP/1.1 200 OK

WEB-18 WebDAV PUT test
```

이 결과는 WebDAV가 활성화되어 외부 요청으로 웹 서비스 경로에 파일 생성이 가능함을 의미한다.

### 9-3. 조치 후 증거

WebDAV 설정 제거 확인:

```bash
grep -Ri "^[[:space:]]*Dav[[:space:]]\|^[[:space:]]*DAVLockDB" \
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

PUT 요청 재확인:

```bash
curl -i -X PUT --data 'WEB-18 should be blocked' "$SERVER/web18-dav/put-test-after.txt"
```

조치 후 기대 결과:

```text
HTTP/1.1 404 Not Found
```

또는:

```text
HTTP/1.1 405 Method Not Allowed
```

또는:

```text
HTTP/1.1 403 Forbidden
```

## 10. 판단

|항목|판단|
|---|---|
|최초 진단|양호|
|진단 근거|`DAV On` 설정 없음, `DAV disabled or not loaded`|
|실습 처리|실습용 디렉터리에 `Dav On`을 적용하여 WebDAV 취약 상태 재현 후 제거|
|조치 전 판단|`Dav On`이 존재하거나 PUT/PROPFIND 요청이 동작하면 취약|
|조치 후 판단|`Dav On` 설정이 없고 WebDAV 요청이 차단되면 양호|
|증거 상태|최초 진단 결과 확보, 취약 재현 및 조치 후 WebDAV 요청 증거 필요|

현재 서버는 최초 진단 기준으로 `DAV On` 설정이 확인되지 않았고 `DAV disabled or not loaded` 상태이므로 WEB-18은 **양호**로 판단한다.

다만 PDF의 취약 조건을 실습하기 위해 실습용 경로 `/var/www/care/web18-dav`에 `Dav On`을 적용하면, WebDAV가 활성화되어 `OPTIONS` 응답에 `DAV` 헤더가 노출되고, `PUT` 요청으로 파일을 생성할 수 있는 취약 상태를 재현할 수 있다.

조치는 실습용 `Dav On` 설정을 제거하고, 필요하지 않은 WebDAV 모듈과 테스트 디렉터리, DAVLockDB 파일을 정리하는 방식으로 수행한다.

조치 후 `Dav On` 설정이 탐지되지 않고, `PUT` 요청이 `404`, `405`, `403` 등으로 차단되면 WEB-18은 조치 후 **양호**로 판단한다.