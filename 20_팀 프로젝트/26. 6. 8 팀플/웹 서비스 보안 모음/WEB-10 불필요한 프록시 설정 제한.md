---
type: lab  
topic: web-service-security  
source: 주요정보통신기반시설 기술적 취약점 분석·평가 방법 상세가이드  
source_pages:
- 299
    
- 300
    
- 301  
status: draft  
created: 2026-06-18  
tags:
    
- 🏷️과목/웹서비스보안
    
- 🏷️주제/WEB-10
    
- 🏷️주제/Proxy
    
- 🏷️주제/Apache
    
- 🏷️상태/draft
    

---

# WEB-10 불필요한 프록시 설정 제한

## 1. PDF 기준

PDF p.299-301의 WEB-10은 웹 서비스에 **불필요한 Proxy 설정이 존재하는지** 점검하는 항목이다.

Proxy 설정은 웹 서버가 클라이언트 요청을 다른 서버로 전달하도록 만드는 기능이다. 정상적으로 설계된 Reverse Proxy 구조에서는 유용하지만, 불필요하거나 의도하지 않은 Proxy 설정이 남아 있으면 공격자가 원래 접근할 수 없어야 할 내부 서버나 백엔드 서비스에 우회 접근할 수 있다.

대표적인 Apache Proxy 설정은 다음과 같다.

```apache
ProxyPreserveHost On
ProxyRequests Off
ProxyPass / http://backend-server.example.com/
ProxyPassReverse / http://backend-server.example.com/
```

각 설정의 의미는 다음과 같다.

|설정|의미|
|---|---|
|`ProxyRequests`|Apache를 Forward Proxy로 사용할지 여부|
|`ProxyPass`|특정 URL 경로를 다른 서버로 전달|
|`ProxyPassReverse`|백엔드 응답의 리다이렉트 헤더를 프록시 경로에 맞게 수정|
|`ProxyPreserveHost`|원래 Host 헤더를 백엔드로 전달|

WEB-10의 판단 기준은 다음과 같다.

|판단|기준|
|---|---|
|양호|불필요한 Proxy 설정을 제한한 경우|
|취약|불필요한 Proxy 설정을 제한하지 않은 경우|

Apache 환경에서는 다음 설정이 남아 있는지 확인한다.

```text
ProxyRequests
ProxyPass
ProxyPassReverse
ProxyPreserveHost
```

특히 `ProxyRequests On`은 Apache가 Forward Proxy처럼 동작할 수 있게 만드는 설정이므로 매우 주의해야 한다.

이 실습에서는 실제 외부 Forward Proxy를 열지 않고, 로컬 테스트 백엔드를 이용해 **불필요한 Reverse Proxy 설정이 생겼을 때 외부에서 백엔드 경로가 노출되는 상황**을 재현한다.

## 2. 최초 진단 결과

`AWS WEB 약점 진단 결과.md` 기준 최초 진단 결과는 **양호**이다.

|항목|내용|
|---|---|
|진단 결과|양호|
|진단 근거|`ProxyPass`, `ProxyPassReverse`, `ProxyRequests` 설정 없음|
|진단 결과 메시지|`No proxy settings found`|
|최초 판단|불필요한 Proxy 설정이 확인되지 않았으므로 양호|

진단 결과는 다음과 같다.

```text
No proxy settings found
```

따라서 최초 상태에서는 Apache에 불필요한 Proxy 설정이 없는 것으로 판단한다.

## 3. 현재 서버 상태 해석

WEB-10은 Apache 설정 파일 안에 Proxy 관련 설정이 남아 있는지 확인하는 항목이다.

확인 대상은 다음과 같다.

|확인 대상|의미|
|---|---|
|`ProxyRequests On`|서버가 Forward Proxy로 동작할 수 있음|
|`ProxyPass`|특정 URL 경로를 다른 서버로 전달|
|`ProxyPassReverse`|Reverse Proxy 응답 헤더를 보정|
|`proxy_module`|Apache Proxy 공통 모듈|
|`proxy_http_module`|HTTP Proxy 기능 모듈|

현재 진단 결과에서는 Proxy 설정이 확인되지 않았으므로 최초 상태는 양호하다.

다만 Proxy 설정이 의도 없이 추가되면 다음 문제가 발생할 수 있다.

|위험|설명|
|---|---|
|내부 서비스 노출|외부에서 접근할 수 없어야 할 백엔드가 프록시 경로로 노출될 수 있음|
|접근 통제 우회|백엔드 접근 제한이 Apache 프록시 경로를 통해 우회될 수 있음|
|관리 복잡성 증가|실제 서비스 경로와 프록시 경로가 섞여 추적이 어려워짐|
|정보 노출|백엔드 응답, 헤더, 에러 메시지가 외부에 노출될 수 있음|
|자원 낭비|불필요한 프록시 요청 처리로 서버 자원이 소모될 수 있음|

이 항목은 WEB-16 웹서버 헤더 정보 노출 제한, WEB-21 입력값 검증, WEB-23 HTTP 메서드 제한과도 연결된다. Proxy를 통해 백엔드 응답이 그대로 노출되면 서버 정보, 헤더, 에러 메시지, 허용 메서드가 의도와 다르게 외부에 보일 수 있다.

## 4. 실습 전 확인

실습을 시작하기 전에 현재 Apache Proxy 설정과 모듈 상태를 확인한다.

### 4-1. Apache 가상호스트 확인

```bash
apache2ctl -S
```

### 4-2. 현재 Proxy 설정 확인

```bash
grep -R "ProxyRequests\|ProxyPass\|ProxyPassReverse\|ProxyPreserveHost" /etc/apache2/apache2.conf /etc/apache2/sites-enabled/ /etc/apache2/sites-available/ /etc/apache2/conf-enabled/ /etc/apache2/conf-available/ 2>/dev/null | grep -v '^\s*#'
```

최초 양호 상태라면 출력이 없어야 한다.

```text
출력 없음
```

### 4-3. Proxy 모듈 상태 확인

```bash
apache2ctl -M | grep -E "proxy|proxy_http"
```

출력이 없으면 Proxy 모듈이 로드되지 않은 상태다.  
출력이 있더라도 Proxy 설정이 없으면 WEB-10 최초 진단 기준으로는 양호로 볼 수 있다.

출력 예시는 다음과 같다.

```text
proxy_module (shared)
proxy_http_module (shared)
```

### 4-4. 실습용 변수 지정

```bash
SERVER=http://172.168.10.10
BACKEND_PORT=18080
BACKEND_DIR=/tmp/web10-backend
BACKEND_PID=/tmp/web10-backend.pid
BACKEND_LOG=/tmp/web10-backend.log
TEST_CONF=/etc/apache2/conf-available/web-10-proxy-test.conf
```

## 5. 취약 재현

이 항목은 최초 진단 결과가 양호이므로, PDF 내용을 실습하기 위해 의도적으로 불필요한 Proxy 설정을 추가한다.

> 주의: 이 실습은 격리된 실습 서버에서만 수행한다.  
> `ProxyRequests On`으로 외부 Forward Proxy를 여는 방식은 사용하지 않는다.  
> 이 노트에서는 로컬 테스트 백엔드에 대한 Reverse Proxy를 만들어 불필요한 Proxy 설정의 위험을 재현한다.  
> 실습 후에는 Proxy 설정과 테스트 백엔드를 제거한다.

취약 재현의 핵심은 다음이다.

```text
원래 외부에 노출할 필요가 없는 로컬 백엔드를 Apache Proxy 경로로 노출한다.
```

### 5-1. 테스트 백엔드 디렉터리 생성

```bash
mkdir -p "$BACKEND_DIR"
```

### 5-2. 테스트 백엔드 파일 생성

```bash
cat > "$BACKEND_DIR/index.html" <<'EOF'
WEB-10 backend test
EOF
```

### 5-3. 로컬 백엔드 서버 실행

```bash
python3 -m http.server "$BACKEND_PORT" --bind 127.0.0.1 --directory "$BACKEND_DIR" > "$BACKEND_LOG" 2>&1 &
echo $! > "$BACKEND_PID"
```

백엔드가 실행 중인지 확인한다.

```bash
cat "$BACKEND_PID"
```

```bash
curl -i "http://127.0.0.1:$BACKEND_PORT/"
```

기대 결과는 다음과 같다.

```text
HTTP/1.0 200 OK

WEB-10 backend test
```

이 백엔드는 127.0.0.1에만 바인딩되어 있으므로 외부에서 직접 접근하는 서비스가 아니다.  
하지만 Apache에 Proxy 설정을 추가하면 외부 사용자가 Apache 경유로 접근할 수 있다.

### 5-4. Apache Proxy 모듈 활성화

```bash
sudo a2enmod proxy proxy_http
```

이미 활성화되어 있으면 다음과 유사한 메시지가 나올 수 있다.

```text
Module proxy already enabled
Module proxy_http already enabled
```

### 5-5. 실습용 Proxy 설정 생성

```bash
sudo tee "$TEST_CONF" > /dev/null <<EOF
ProxyRequests Off
ProxyPreserveHost On

ProxyPass /web10-proxy/ http://127.0.0.1:$BACKEND_PORT/
ProxyPassReverse /web10-proxy/ http://127.0.0.1:$BACKEND_PORT/
EOF
```

이 설정은 `/web10-proxy/`로 들어오는 요청을 로컬 백엔드 `127.0.0.1:18080`으로 전달한다.

`ProxyRequests Off`는 Forward Proxy를 켜지 않기 위한 안전 설정이다.  
하지만 `ProxyPass` 자체가 불필요하게 남아 있다면 PDF 기준 WEB-10의 취약 조건에 해당할 수 있다.

### 5-6. 실습용 설정 활성화

```bash
sudo a2enconf web-10-proxy-test
```

### 5-7. Apache 설정 문법 검사

```bash
sudo apachectl configtest
```

정상이라면 다음 결과가 나와야 한다.

```text
Syntax OK
```

### 5-8. Apache restart

```bash
sudo systemctl restart apache2
```

### 5-9. Proxy 경로 접근 확인

```bash
curl -i "$SERVER/web10-proxy/"
```

취약 재현 상태에서 기대 결과는 다음과 같다.

```text
HTTP/1.1 200 OK

WEB-10 backend test
```

이 결과는 원래 외부에 노출할 필요가 없던 로컬 백엔드가 Apache Proxy 설정을 통해 외부에 노출되었음을 의미한다.

## 6. 조치 방법

조치 핵심은 불필요한 Proxy 설정을 제거하는 것이다.

현재 실습에서는 `web-10-proxy-test.conf` 설정을 제거하고, 테스트 백엔드를 종료한다.

### 6-1. 실습용 Proxy 설정 비활성화

```bash
sudo a2disconf web-10-proxy-test
```

### 6-2. 실습용 Proxy 설정 파일 제거

```bash
sudo rm -f "$TEST_CONF"
```

### 6-3. 테스트 백엔드 종료

```bash
if [ -f "$BACKEND_PID" ]; then
  kill "$(cat "$BACKEND_PID")" 2>/dev/null || true
fi
```

### 6-4. 테스트 백엔드 파일 제거

```bash
rm -rf "$BACKEND_DIR" "$BACKEND_PID" "$BACKEND_LOG"
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

### 6-7. Proxy 모듈 처리

실습에서 Proxy 모듈을 새로 활성화했더라도, 다른 서비스가 사용할 수 있으므로 무조건 비활성화하지 않는다.

현재 서버에서 Proxy 기능을 전혀 사용하지 않는 것이 확실하다면 다음 명령으로 비활성화할 수 있다.

```bash
sudo a2dismod proxy_http proxy
```

모듈을 비활성화했다면 다시 문법 검사와 restart를 수행한다.

```bash
sudo apachectl configtest
```

```bash
sudo systemctl restart apache2
```

단, 다른 설정에서 Proxy 기능을 사용 중이면 `a2dismod`를 실행하지 않는다.

## 7. 조치 후 확인

조치 후에는 Proxy 설정이 제거되었고, Proxy 경로로 백엔드에 접근할 수 없는지 확인한다.

### 7-1. Proxy 설정 제거 확인

```bash
grep -R "ProxyRequests\|ProxyPass\|ProxyPassReverse\|ProxyPreserveHost" /etc/apache2/apache2.conf /etc/apache2/sites-enabled/ /etc/apache2/sites-available/ /etc/apache2/conf-enabled/ /etc/apache2/conf-available/ 2>/dev/null | grep -v '^\s*#'
```

기대 결과는 다음이다.

```text
출력 없음
```

단, 실제 서비스 구조상 필요한 Reverse Proxy가 있다면 해당 설정은 예외로 문서화해야 한다.

### 7-2. 실습 설정 파일 제거 확인

```bash
ls -l "$TEST_CONF" 2>/dev/null
```

기대 결과는 다음이다.

```text
출력 없음
```

### 7-3. 테스트 백엔드 종료 확인

```bash
curl -i "http://127.0.0.1:$BACKEND_PORT/"
```

백엔드를 종료했다면 다음과 유사한 결과가 나온다.

```text
curl: (7) Failed to connect
```

### 7-4. Proxy 경로 접근 차단 확인

```bash
curl -i "$SERVER/web10-proxy/"
```

조치 후 기대 결과는 다음 중 하나다.

```text
HTTP/1.1 404 Not Found
```

또는:

```text
HTTP/1.1 403 Forbidden
```

중요한 것은 다음 문자열이 더 이상 외부에서 출력되지 않는 것이다.

```text
WEB-10 backend test
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

실습 중에는 아래 순서대로 진행한다.

### 8-1. 현재 상태 확인

```bash
SERVER=http://172.168.10.10
BACKEND_PORT=18080
BACKEND_DIR=/tmp/web10-backend
BACKEND_PID=/tmp/web10-backend.pid
BACKEND_LOG=/tmp/web10-backend.log
TEST_CONF=/etc/apache2/conf-available/web-10-proxy-test.conf
```

```bash
apache2ctl -S
```

```bash
grep -R "ProxyRequests\|ProxyPass\|ProxyPassReverse\|ProxyPreserveHost" /etc/apache2/apache2.conf /etc/apache2/sites-enabled/ /etc/apache2/sites-available/ /etc/apache2/conf-enabled/ /etc/apache2/conf-available/ 2>/dev/null | grep -v '^\s*#'
```

```bash
apache2ctl -M | grep -E "proxy|proxy_http"
```

### 8-2. 취약 재현

```bash
mkdir -p "$BACKEND_DIR"
```

```bash
cat > "$BACKEND_DIR/index.html" <<'EOF'
WEB-10 backend test
EOF
```

```bash
python3 -m http.server "$BACKEND_PORT" --bind 127.0.0.1 --directory "$BACKEND_DIR" > "$BACKEND_LOG" 2>&1 &
echo $! > "$BACKEND_PID"
```

```bash
curl -i "http://127.0.0.1:$BACKEND_PORT/"
```

```bash
sudo a2enmod proxy proxy_http
```

```bash
sudo tee "$TEST_CONF" > /dev/null <<EOF
ProxyRequests Off
ProxyPreserveHost On

ProxyPass /web10-proxy/ http://127.0.0.1:$BACKEND_PORT/
ProxyPassReverse /web10-proxy/ http://127.0.0.1:$BACKEND_PORT/
EOF
```

```bash
sudo a2enconf web-10-proxy-test
```

```bash
sudo apachectl configtest
```

```bash
sudo systemctl restart apache2
```

```bash
curl -i "$SERVER/web10-proxy/"
```

취약 상태 기대 결과:

```text
HTTP/1.1 200 OK

WEB-10 backend test
```

### 8-3. 조치 및 복구

```bash
sudo a2disconf web-10-proxy-test
```

```bash
sudo rm -f "$TEST_CONF"
```

```bash
if [ -f "$BACKEND_PID" ]; then
  kill "$(cat "$BACKEND_PID")" 2>/dev/null || true
fi
```

```bash
rm -rf "$BACKEND_DIR" "$BACKEND_PID" "$BACKEND_LOG"
```

```bash
sudo apachectl configtest
```

```bash
sudo systemctl restart apache2
```

Proxy 모듈을 실습용으로만 활성화했고, 다른 서비스에서 사용하지 않는 것이 확실할 때만 다음을 수행한다.

```bash
sudo a2dismod proxy_http proxy
```

```bash
sudo apachectl configtest
```

```bash
sudo systemctl restart apache2
```

### 8-4. 조치 후 확인

```bash
grep -R "ProxyRequests\|ProxyPass\|ProxyPassReverse\|ProxyPreserveHost" /etc/apache2/apache2.conf /etc/apache2/sites-enabled/ /etc/apache2/sites-available/ /etc/apache2/conf-enabled/ /etc/apache2/conf-available/ 2>/dev/null | grep -v '^\s*#'
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
curl -i "$SERVER/web10-proxy/"
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

## 9. 증거 정리

### 9-1. 최초 상태 증거

최초 진단 결과:

```text
WEB-10 · 불필요한 프록시 설정 제한
ProxyPass, ProxyPassReverse, ProxyRequests 설정 없음

No proxy settings found
```

Proxy 설정 확인 명령어:

```bash
grep -R "ProxyRequests\|ProxyPass\|ProxyPassReverse\|ProxyPreserveHost" /etc/apache2/apache2.conf /etc/apache2/sites-enabled/ /etc/apache2/sites-available/ /etc/apache2/conf-enabled/ /etc/apache2/conf-available/ 2>/dev/null | grep -v '^\s*#'
```

양호 상태 기대 결과:

```text
출력 없음
```

### 9-2. 취약 재현 증거

실습용 Proxy 설정:

```apache
ProxyRequests Off
ProxyPreserveHost On

ProxyPass /web10-proxy/ http://127.0.0.1:18080/
ProxyPassReverse /web10-proxy/ http://127.0.0.1:18080/
```

Proxy 경로 접근 확인:

```bash
curl -i "$SERVER/web10-proxy/"
```

취약 재현 기대 결과:

```text
HTTP/1.1 200 OK

WEB-10 backend test
```

이 결과는 원래 외부에 노출할 필요가 없던 로컬 백엔드가 Apache Proxy 경로를 통해 외부에 노출되었음을 의미한다.

### 9-3. 조치 후 증거

Proxy 설정 제거 확인:

```bash
grep -R "ProxyRequests\|ProxyPass\|ProxyPassReverse\|ProxyPreserveHost" /etc/apache2/apache2.conf /etc/apache2/sites-enabled/ /etc/apache2/sites-available/ /etc/apache2/conf-enabled/ /etc/apache2/conf-available/ 2>/dev/null | grep -v '^\s*#'
```

기대 결과:

```text
출력 없음
```

Proxy 경로 재요청:

```bash
curl -i "$SERVER/web10-proxy/"
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
|진단 근거|`ProxyPass`, `ProxyPassReverse`, `ProxyRequests` 설정 없음|
|실습 처리|로컬 테스트 백엔드를 Apache Reverse Proxy 경로로 노출하여 취약 상태 재현 후 제거|
|조치 전 판단|최초 상태는 양호, 실습 Proxy 설정 적용 상태는 취약|
|조치 후 판단|불필요한 Proxy 설정 제거 후 양호|
|증거 상태|최초 진단 결과 확보, 취약 재현 및 조치 후 접근 증거 필요|

현재 서버는 최초 진단 기준으로 `ProxyPass`, `ProxyPassReverse`, `ProxyRequests` 설정이 확인되지 않았으므로 WEB-10은 **양호**로 판단한다.

다만 PDF의 취약 조건을 실습하기 위해 `/web10-proxy/` 경로를 로컬 백엔드 `127.0.0.1:18080`으로 전달하는 불필요한 Reverse Proxy 설정을 추가하면, 원래 외부에 노출할 필요가 없는 백엔드가 Apache를 통해 접근 가능한 취약 상태를 재현할 수 있다.

조치는 불필요한 Proxy 설정을 제거하고, 테스트 백엔드를 종료하는 방식으로 수행한다.

조치 후 Proxy 관련 설정이 출력되지 않고, `/web10-proxy/` 요청에서 `WEB-10 backend test`가 더 이상 출력되지 않으면 WEB-10은 조치 후 **양호**로 판단한다.