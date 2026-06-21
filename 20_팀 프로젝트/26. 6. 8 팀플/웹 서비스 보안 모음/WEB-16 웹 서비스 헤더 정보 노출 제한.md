---

type: lab  
topic: web-service-security  
source: 주요정보통신기반시설 기술적 취약점 분석·평가 방법 상세가이드  
source_pages:

- 316
    
- 317  
status: draft  
created: 2026-06-18  
tags:
    
- 🏷️과목/웹서비스보안
    
- 🏷️주제/WEB-16
    
- 🏷️주제/Server-Header
    
- 🏷️주제/Apache
    
- 🏷️상태/draft
    

---
# WEB-16 웹 서비스 헤더 정보 노출 제한

## 1. PDF 기준

PDF p.316-317의 WEB-16은 웹페이지 응답 헤더에서 **웹 서버 버전, 운영체제, 모듈 정보 등 불필요한 서버 정보가 노출되는지** 점검하는 항목이다.

HTTP 응답 헤더에는 서버가 자동으로 추가하는 정보가 포함될 수 있다. 대표적으로 `Server` 헤더가 있다.

예를 들어 다음과 같은 응답은 서버 정보를 과도하게 노출한다.

```text
Server: Apache/2.4.58 (Ubuntu)
```

더 심한 경우 다음처럼 웹 서버 모듈이나 PHP 관련 정보까지 노출될 수 있다.

```text
Server: Apache/2.4.58 (Ubuntu) DAV/2 PHP/8.2
```

이런 정보가 노출되면 공격자는 서버 종류, 버전, 운영체제 정보를 바탕으로 알려진 취약점을 찾을 수 있다.

PDF의 판단 기준은 다음과 같다.

|판단|기준|
|---|---|
|양호|HTTP 응답 헤더에서 웹 서버 정보가 노출되지 않는 경우|
|취약|HTTP 응답 헤더에서 웹 서버 정보가 노출되는 경우|

Apache 기준 조치 방향은 다음 두 설정이다.

```apache
ServerTokens Prod
ServerSignature Off
```

`ServerTokens`는 `Server` 응답 헤더에 어느 정도의 서버 정보를 표시할지 결정한다.

|옵션|노출 정보 예시|의미|
|---|---|---|
|`Prod`|`Apache`|제품명만 표시|
|`Min`|`Apache/2.4.58`|웹 서버 버전 표시|
|`OS`|`Apache/2.4.58 (Ubuntu)`|웹 서버 버전과 OS 표시|
|`Full`|`Apache/2.4.58 (Ubuntu) ...`|모듈 정보까지 표시 가능|

`ServerSignature`는 Apache 기본 에러 페이지 하단에 서버 버전과 호스트 정보를 표시할지 결정한다.

```apache
ServerSignature Off
```

이 설정이 적용되면 Apache 기본 에러 페이지에 서버 버전 정보가 표시되지 않는다.

## 2. 최초 진단 결과

`AWS WEB 약점 진단 결과.md` 기준 최초 진단 결과는 **양호**이다.

|항목|내용|
|---|---|
|진단 결과|양호|
|진단 근거|서버 정보 노출 최소화 설정 확인|
|확인된 설정|`ServerTokens: Minimal`, `ServerSignature: Off`|
|최초 판단|서버 서명은 차단되어 있고, 헤더 정보 노출이 제한된 상태|
|추가 개선|PDF 기준으로는 `ServerTokens Prod`가 더 강한 최소화 설정|

최초 진단 결과는 다음과 같다.

```text
ServerTokens: Minimal
ServerSignature: Off
```

`ServerSignature Off`는 양호하다.

다만 `ServerTokens Minimal`은 서버 버전이 노출될 수 있다. PDF의 Apache 조치 예시는 `ServerTokens Prod`를 제시하므로, 이 노트에서는 실습 조치 기준을 `Prod / Off`로 잡는다.

즉 최초 진단은 양호로 보되, 조치 실습에서는 더 엄격한 값인 `ServerTokens Prod`로 강화한다.

## 3. 현재 서버 상태 해석

WEB-16은 웹 애플리케이션 코드보다 Apache 응답 헤더와 에러 페이지 설정을 확인하는 항목이다.

확인 대상은 다음과 같다.

|확인 대상|의미|
|---|---|
|`Server` 응답 헤더|웹 서버 제품명, 버전, OS 정보 노출 여부|
|`ServerTokens`|`Server` 헤더의 노출 수준|
|`ServerSignature`|Apache 기본 에러 페이지 하단 정보 노출 여부|
|`X-Powered-By`|PHP 또는 프레임워크 정보 노출 여부|
|에러 페이지 본문|서버 버전, OS, 모듈 정보 노출 여부|

Apache에서 `ServerTokens Minimal`이면 다음처럼 버전이 보일 수 있다.

```text
Server: Apache/2.4.58
```

`ServerTokens Prod`이면 다음처럼 제품명만 보인다.

```text
Server: Apache
```

완전히 `Server` 헤더를 제거하는 것은 Apache 기본 기능만으로는 보통 어렵다. WEB-16의 현실적인 Apache 조치 기준은 **버전, OS, 모듈 정보가 노출되지 않도록 최소화하는 것**이다.

이 항목은 WEB-22 에러 페이지 관리와 연결된다. `ServerSignature Off`를 적용해도 에러 페이지를 기본값으로 방치하면 다른 정보가 노출될 수 있으므로, 에러 페이지 통제와 함께 확인하는 것이 좋다.

## 4. 실습 전 확인

실습을 시작하기 전에 현재 Apache 설정과 HTTP 응답 헤더를 확인한다.

### 4-1. Apache 설정 파일 위치 확인

Ubuntu Apache에서는 보통 다음 파일에 보안 관련 설정이 있다.

```text
/etc/apache2/conf-available/security.conf
```

실습용 변수를 지정한다.

```bash
SERVER=http://172.168.10.10
SEC_CONF=/etc/apache2/conf-available/security.conf
TEST_CONF=/etc/apache2/conf-available/web-16-header-test.conf
```

### 4-2. 현재 ServerTokens, ServerSignature 설정 확인

```bash
grep -R "^[[:space:]]*ServerTokens\|^[[:space:]]*ServerSignature" \
/etc/apache2/apache2.conf \
/etc/apache2/sites-enabled/ \
/etc/apache2/sites-available/ \
/etc/apache2/conf-enabled/ \
/etc/apache2/conf-available/ 2>/dev/null | grep -v '^\s*#'
```

최초 진단 기준 기대 결과는 다음과 유사하다.

```text
ServerTokens Minimal
ServerSignature Off
```

### 4-3. 현재 HTTP 응답 헤더 확인

```bash
curl -I "$SERVER/"
```

또는 헤더만 정리해서 확인한다.

```bash
curl -s -D - -o /dev/null "$SERVER/" | grep -iE '^Server:|^X-Powered-By:'
```

양호에 가까운 상태라면 다음처럼 과도한 버전과 OS 정보가 노출되지 않아야 한다.

```text
Server: Apache
```

또는 최초 상태에서는 다음처럼 보일 수 있다.

```text
Server: Apache/2.4.58
```

`Apache/2.4.58`처럼 버전이 보이면 PDF 기준으로는 `Prod`로 강화하는 것이 좋다.

### 4-4. 에러 페이지 서버 서명 확인

존재하지 않는 경로를 요청한다.

```bash
curl -i "$SERVER/web16-not-found-test"
```

확인할 부분은 응답 본문 하단에 다음과 같은 서버 서명이 나오는지 여부다.

```text
Apache/2.4.58 (Ubuntu) Server at ...
```

`ServerSignature Off`가 적용되어 있으면 이런 서버 서명이 노출되지 않아야 한다.

## 5. 취약 재현

이 항목은 최초 진단 결과가 양호이다.  
PDF 내용을 실습하기 위해 의도적으로 서버 정보가 과도하게 노출되는 상태를 만든다.

> 주의: 이 절차는 격리된 실습 서버에서만 수행한다.  
> 실습 후 즉시 `ServerTokens Prod`, `ServerSignature Off`로 복구한다.  
> 외부 공개 서버에서는 `ServerTokens Full`, `ServerSignature On`을 적용하지 않는다.

취약 재현의 핵심은 다음이다.

```text
ServerTokens Full
ServerSignature On
```

이 설정은 응답 헤더와 Apache 기본 에러 페이지에 서버 정보를 더 많이 노출할 수 있다.

### 5-1. 실습용 취약 설정 파일 생성

```bash
sudo tee "$TEST_CONF" > /dev/null <<'EOF'
ServerTokens Full
ServerSignature On
EOF
```

### 5-2. 실습용 설정 활성화

```bash
sudo a2enconf web-16-header-test
```

### 5-3. Apache 설정 문법 검사

```bash
sudo apachectl configtest
```

정상이라면 다음 결과가 나와야 한다.

```text
Syntax OK
```

### 5-4. Apache restart

```bash
sudo systemctl restart apache2
```

### 5-5. 취약 상태 헤더 확인

```bash
curl -s -D - -o /dev/null "$SERVER/" | grep -iE '^Server:|^X-Powered-By:'
```

취약 재현 상태에서는 다음과 유사한 결과가 나올 수 있다.

```text
Server: Apache/2.4.58 (Ubuntu)
```

또는 환경에 따라 모듈 정보가 더 붙을 수 있다.

```text
Server: Apache/2.4.58 (Ubuntu) DAV/2
```

### 5-6. 취약 상태 에러 페이지 확인

```bash
curl -i "$SERVER/web16-not-found-test"
```

취약 재현 상태에서는 에러 페이지 하단에 다음과 유사한 서버 서명이 노출될 수 있다.

```text
Apache/2.4.58 (Ubuntu) Server at 172.168.10.10 Port 80
```

이 결과는 웹 서버 버전, OS, 포트 정보가 에러 응답에서 노출되는 상태이므로 PDF 기준 취약 상태다.

## 6. 조치 방법

조치 핵심은 응답 헤더와 에러 페이지에서 서버 정보를 최소화하는 것이다.

Apache에서는 다음 설정을 적용한다.

```apache
ServerTokens Prod
ServerSignature Off
```

### 6-1. 실습용 취약 설정 비활성화

```bash
sudo a2disconf web-16-header-test
```

### 6-2. 실습용 취약 설정 파일 제거

```bash
sudo rm -f "$TEST_CONF"
```

### 6-3. 기존 보안 설정 파일 백업

```bash
sudo cp "$SEC_CONF" "$SEC_CONF.bak.WEB-16"
```

### 6-4. ServerTokens를 Prod로 설정

기존 `ServerTokens` 값을 `Prod`로 바꾼다.

```bash
if grep -q "^[[:space:]]*ServerTokens" "$SEC_CONF"; then
  sudo sed -i -E 's/^[[:space:]]*ServerTokens[[:space:]]+.*/ServerTokens Prod/' "$SEC_CONF"
else
  echo "ServerTokens Prod" | sudo tee -a "$SEC_CONF"
fi
```

### 6-5. ServerSignature를 Off로 설정

```bash
if grep -q "^[[:space:]]*ServerSignature" "$SEC_CONF"; then
  sudo sed -i -E 's/^[[:space:]]*ServerSignature[[:space:]]+.*/ServerSignature Off/' "$SEC_CONF"
else
  echo "ServerSignature Off" | sudo tee -a "$SEC_CONF"
fi
```

### 6-6. 설정 적용 확인

```bash
grep -E "^[[:space:]]*ServerTokens|^[[:space:]]*ServerSignature" "$SEC_CONF"
```

기대 결과는 다음이다.

```text
ServerTokens Prod
ServerSignature Off
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

조치 후에는 응답 헤더에서 버전, OS, 모듈 정보가 제거되었는지 확인한다.

### 7-1. Apache 설정 확인

```bash
grep -R "^[[:space:]]*ServerTokens\|^[[:space:]]*ServerSignature" \
/etc/apache2/apache2.conf \
/etc/apache2/sites-enabled/ \
/etc/apache2/sites-available/ \
/etc/apache2/conf-enabled/ \
/etc/apache2/conf-available/ 2>/dev/null | grep -v '^\s*#'
```

기대 결과는 다음과 같다.

```text
ServerTokens Prod
ServerSignature Off
```

### 7-2. HTTP 응답 헤더 확인

```bash
curl -s -D - -o /dev/null "$SERVER/" | grep -iE '^Server:|^X-Powered-By:'
```

조치 후 기대 결과는 다음과 같다.

```text
Server: Apache
```

다음과 같이 버전이나 OS가 노출되면 조치가 부족하다.

```text
Server: Apache/2.4.58 (Ubuntu)
```

### 7-3. 에러 페이지 서버 서명 확인

```bash
curl -i "$SERVER/web16-not-found-test"
```

조치 후에는 에러 페이지 하단에 다음과 같은 정보가 나오지 않아야 한다.

```text
Apache/2.4.58 (Ubuntu) Server at 172.168.10.10 Port 80
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
SERVER=http://172.168.10.10
SEC_CONF=/etc/apache2/conf-available/security.conf
TEST_CONF=/etc/apache2/conf-available/web-16-header-test.conf
```

```bash
grep -R "^[[:space:]]*ServerTokens\|^[[:space:]]*ServerSignature" \
/etc/apache2/apache2.conf \
/etc/apache2/sites-enabled/ \
/etc/apache2/sites-available/ \
/etc/apache2/conf-enabled/ \
/etc/apache2/conf-available/ 2>/dev/null | grep -v '^\s*#'
```

```bash
curl -s -D - -o /dev/null "$SERVER/" | grep -iE '^Server:|^X-Powered-By:'
```

```bash
curl -i "$SERVER/web16-not-found-test"
```

### 8-2. 취약 재현

```bash
sudo tee "$TEST_CONF" > /dev/null <<'EOF'
ServerTokens Full
ServerSignature On
EOF
```

```bash
sudo a2enconf web-16-header-test
```

```bash
sudo apachectl configtest
```

```bash
sudo systemctl restart apache2
```

```bash
curl -s -D - -o /dev/null "$SERVER/" | grep -iE '^Server:|^X-Powered-By:'
```

```bash
curl -i "$SERVER/web16-not-found-test"
```

취약 상태 기대 결과:

```text
Server: Apache/2.4.58 (Ubuntu)
```

또는:

```text
Apache/2.4.58 (Ubuntu) Server at 172.168.10.10 Port 80
```

### 8-3. 조치 및 적용

```bash
sudo a2disconf web-16-header-test
```

```bash
sudo rm -f "$TEST_CONF"
```

```bash
sudo cp "$SEC_CONF" "$SEC_CONF.bak.WEB-16"
```

```bash
if grep -q "^[[:space:]]*ServerTokens" "$SEC_CONF"; then
  sudo sed -i -E 's/^[[:space:]]*ServerTokens[[:space:]]+.*/ServerTokens Prod/' "$SEC_CONF"
else
  echo "ServerTokens Prod" | sudo tee -a "$SEC_CONF"
fi
```

```bash
if grep -q "^[[:space:]]*ServerSignature" "$SEC_CONF"; then
  sudo sed -i -E 's/^[[:space:]]*ServerSignature[[:space:]]+.*/ServerSignature Off/' "$SEC_CONF"
else
  echo "ServerSignature Off" | sudo tee -a "$SEC_CONF"
fi
```

```bash
grep -E "^[[:space:]]*ServerTokens|^[[:space:]]*ServerSignature" "$SEC_CONF"
```

```bash
sudo apachectl configtest
```

```bash
sudo systemctl restart apache2
```

### 8-4. 조치 후 확인

```bash
grep -R "^[[:space:]]*ServerTokens\|^[[:space:]]*ServerSignature" \
/etc/apache2/apache2.conf \
/etc/apache2/sites-enabled/ \
/etc/apache2/sites-available/ \
/etc/apache2/conf-enabled/ \
/etc/apache2/conf-available/ 2>/dev/null | grep -v '^\s*#'
```

기대 결과:

```text
ServerTokens Prod
ServerSignature Off
```

```bash
curl -s -D - -o /dev/null "$SERVER/" | grep -iE '^Server:|^X-Powered-By:'
```

조치 후 기대 결과:

```text
Server: Apache
```

```bash
curl -i "$SERVER/web16-not-found-test"
```

조치 후 에러 페이지에서는 다음 정보가 나오지 않아야 한다.

```text
Apache/2.4.58 (Ubuntu) Server at 172.168.10.10 Port 80
```

```bash
systemctl status apache2 --no-pager
```

기대 결과:

```text
Active: active (running)
```

### 8-5. 실습 파일 정리

실습용 설정 파일이 남아 있지 않은지 확인한다.

```bash
ls -l "$TEST_CONF" 2>/dev/null
```

기대 결과:

```text
출력 없음
```

백업 파일은 증거 확보 후 필요 없으면 제거한다.

```bash
sudo rm -f "$SEC_CONF.bak.WEB-16"
```

정리 확인:

```bash
ls -l "$SEC_CONF.bak.WEB-16" 2>/dev/null
```

기대 결과:

```text
출력 없음
```

## 9. 증거 정리

### 9-1. 최초 상태 증거

최초 진단 결과:

```text
WEB-16 · 웹서버 헤더 정보 노출 제한

ServerTokens: Minimal
ServerSignature: Off
```

설정 확인 명령어:

```bash
grep -R "^[[:space:]]*ServerTokens\|^[[:space:]]*ServerSignature" \
/etc/apache2/apache2.conf \
/etc/apache2/sites-enabled/ \
/etc/apache2/sites-available/ \
/etc/apache2/conf-enabled/ \
/etc/apache2/conf-available/ 2>/dev/null | grep -v '^\s*#'
```

응답 헤더 확인 명령어:

```bash
curl -s -D - -o /dev/null "$SERVER/" | grep -iE '^Server:|^X-Powered-By:'
```

### 9-2. 취약 재현 증거

취약 설정:

```apache
ServerTokens Full
ServerSignature On
```

취약 상태 헤더 확인:

```bash
curl -s -D - -o /dev/null "$SERVER/" | grep -iE '^Server:|^X-Powered-By:'
```

취약 상태 기대 결과:

```text
Server: Apache/2.4.58 (Ubuntu)
```

취약 상태 에러 페이지 확인:

```bash
curl -i "$SERVER/web16-not-found-test"
```

취약 상태 기대 결과:

```text
Apache/2.4.58 (Ubuntu) Server at 172.168.10.10 Port 80
```

### 9-3. 조치 후 증거

조치 설정:

```apache
ServerTokens Prod
ServerSignature Off
```

조치 후 헤더 확인:

```bash
curl -s -D - -o /dev/null "$SERVER/" | grep -iE '^Server:|^X-Powered-By:'
```

조치 후 기대 결과:

```text
Server: Apache
```

조치 후 에러 페이지 확인:

```bash
curl -i "$SERVER/web16-not-found-test"
```

조치 후에는 다음 정보가 나오지 않아야 한다.

```text
Apache/2.4.58 (Ubuntu) Server at 172.168.10.10 Port 80
```

## 10. 판단

|항목|판단|
|---|---|
|최초 진단|양호|
|진단 근거|`ServerTokens Minimal`, `ServerSignature Off` 확인|
|실습 처리|`ServerTokens Full`, `ServerSignature On`으로 취약 상태 재현 후 `Prod / Off`로 강화|
|조치 전 판단|서버 버전, OS, 모듈 정보가 응답 헤더나 에러 페이지에 노출되면 취약|
|조치 후 판단|`Server: Apache` 수준으로 최소화되고 에러 페이지 서명이 제거되면 양호|
|증거 상태|최초 진단 결과 확보, 취약 재현 및 조치 후 헤더 증거 필요|

현재 서버는 최초 진단 기준으로 `ServerTokens Minimal`, `ServerSignature Off`가 확인되었으므로 WEB-16은 **양호**로 판단한다.

다만 `Minimal`은 서버 버전이 노출될 수 있으므로 PDF의 Apache 조치 예시인 `ServerTokens Prod` 기준으로 강화하는 것이 더 적절하다.

실습에서는 `ServerTokens Full`, `ServerSignature On`을 적용하여 서버 버전과 OS 정보가 노출되는 취약 상태를 재현한다. 이후 실습 설정을 제거하고 `/etc/apache2/conf-available/security.conf`에 `ServerTokens Prod`, `ServerSignature Off`를 적용한다.

조치 후 HTTP 응답 헤더에서 버전과 OS 정보가 사라지고, 에러 페이지 하단에 Apache 버전 서명이 표시되지 않으면 WEB-16은 조치 후 **양호**로 판단한다.