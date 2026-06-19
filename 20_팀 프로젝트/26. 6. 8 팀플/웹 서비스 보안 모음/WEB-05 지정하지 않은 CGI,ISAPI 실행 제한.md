---
type: lab  
topic: web-service-security  
source: 주요정보통신기반시설 기술적 취약점 분석·평가 방법 상세가이드 
source_pages:
  - 283  
  - 284  
status: draft  
created: 2026-06-18  
tags:
  - 🏷️과목/웹서비스보안
  - 🏷️주제/WEB-05
  - 🏷️주제/CGI
  - 🏷️주제/Apache
  - 🏷️상태/draft
---
# WEB-05 지정하지 않은 CGI/ISAPI 실행 제한

## 1. PDF 기준

PDF p.283-284의 WEB-05는 웹 서버에서 **CGI/ISAPI 실행 가능 위치가 제한되어 있는지** 점검하는 항목이다.

CGI는 Common Gateway Interface의 약자로, 웹 서버가 외부 실행 프로그램이나 스크립트를 호출하여 동적 결과를 생성할 수 있게 하는 인터페이스다. 예를 들어 특정 디렉터리 안의 `.cgi`, `.pl`, `.sh` 같은 스크립트를 웹 요청으로 실행할 수 있다.

문제는 CGI 실행 가능 범위가 넓게 열려 있을 때 발생한다.

게시판, 자료실, 업로드 디렉터리처럼 사용자가 파일을 올릴 수 있는 위치에서 CGI 실행이 가능하면, 공격자가 실행 가능한 스크립트를 업로드한 뒤 웹 요청으로 실행할 수 있다. 이 경우 시스템 정보 노출, 임의 명령 실행, 침해사고 경로로 이어질 수 있다.

PDF의 판단 기준은 다음과 같다.

|판단|기준|
|---|---|
|양호|CGI 스크립트를 사용하지 않거나, CGI 스크립트가 실행 가능한 디렉터리를 제한한 경우|
|취약|CGI 스크립트를 사용하고, CGI 스크립트가 실행 가능한 디렉터리를 제한하지 않은 경우|

PDF의 Apache 조치 방향은 다음과 같다.

|단계|내용|
|---|---|
|Step 1|Apache 설정 파일에서 CGI 모듈을 비활성화하거나 주석 처리|
|Step 2|Apache 설정 파일 내 모든 디렉터리의 `Options` 지시자에서 `ExecCGI` 옵션 제거|
|Step 3|Apache 재시작 또는 reload|

즉 WEB-05의 핵심은 다음이다.

```text
CGI를 아예 쓰지 않거나,
써야 한다면 지정된 디렉터리에서만 실행되도록 제한한다.
```

## 2. 최초 진단 결과

`AWS WEB 약점 진단 결과.md` 기준 최초 진단 결과는 **양호**이다.

|항목|내용|
|---|---|
|진단 결과|양호|
|진단 근거|CGI 실행이 `ScriptAlias`로 지정된 `/cgi-bin/` 디렉터리로만 제한됨|
|확인된 설정|`ScriptAlias /cgi-bin/ /usr/lib/cgi-bin/`|
|최초 판단|CGI 실행 가능 위치가 제한되어 있으므로 양호|

진단 결과에 확인된 설정은 다음과 같다.

```apache
ScriptAlias /cgi-bin/ /usr/lib/cgi-bin/
```

`ScriptAlias`는 특정 URL 경로를 CGI 실행 디렉터리에 연결하는 설정이다. 위 설정에서는 `/cgi-bin/` 요청만 `/usr/lib/cgi-bin/` 아래 CGI 실행 위치로 매핑된다.

따라서 현재 최초 진단 기준으로는 CGI 실행이 임의 디렉터리에 열려 있지 않고, 지정된 CGI 디렉터리로 제한된 상태다.

## 3. 현재 서버 상태 해석

현재 서버는 Apache 기반이다. WEB-05에서 중요한 설정은 다음 세 가지다.

|확인 대상|의미|
|---|---|
|`ScriptAlias`|CGI 실행 URL과 실제 CGI 디렉터리 매핑|
|`ExecCGI`|해당 디렉터리에서 CGI 실행을 허용하는 `Options` 값|
|`cgi_module`, `cgid_module`|Apache CGI 실행 모듈|

현재 진단 결과에서는 `ScriptAlias /cgi-bin/ /usr/lib/cgi-bin/`이 확인되었다.

이 상태는 다음처럼 해석할 수 있다.

```text
/cgi-bin/ URL로 요청된 CGI만 /usr/lib/cgi-bin/에서 실행 가능
일반 웹 루트나 업로드 디렉터리에서는 CGI 실행이 허용되지 않음
```

따라서 최초 상태는 양호하다.

다만 PDF 내용을 실습하기 위해서는 양호 상태를 잠시 약화하여, CGI 실행 범위가 넓어졌을 때 어떤 문제가 생기는지 확인한 뒤 다시 제한하는 방식으로 진행한다.

## 4. 취약 재현

이 항목은 최초 진단 결과가 양호이므로, PDF 내용을 실습하기 위해 의도적으로 취약 상태를 재현한다.

> 주의: 이 절차는 격리된 실습 서버에서만 수행한다.  
> 운영 서버에서 웹 루트 또는 업로드 디렉터리에 `ExecCGI`를 부여하면 안 된다.  
> 취약 재현 후에는 즉시 원래 설정으로 복구한다.

취약 재현의 핵심은 다음이다.

```text
정해진 /cgi-bin/ 디렉터리가 아닌 일반 웹 경로에서 CGI 실행이 가능하도록 만든다.
```

예시는 다음과 같다.

```apache
<Directory /var/www/care/cgi-test>
    Options +ExecCGI
    AddHandler cgi-script .cgi .pl .sh
    Require all granted
</Directory>
```

이 설정은 `/var/www/care/cgi-test` 아래에서 `.cgi`, `.pl`, `.sh` 파일이 CGI 스크립트로 실행되도록 만든다. 즉 CGI 실행 가능 범위가 지정된 `/usr/lib/cgi-bin/` 바깥으로 확장된다.

### 4-1. 테스트 디렉터리 생성

```bash
sudo mkdir -p /var/www/care/cgi-test
```

### 4-2. 테스트 CGI 파일 생성

실습용 파일은 위험한 명령 실행 기능을 넣지 않고, CGI 실행 여부만 확인할 수 있는 최소 내용으로 만든다.

```bash
sudo tee /var/www/care/cgi-test/test.cgi > /dev/null <<'EOF'
#!/bin/sh
echo "Content-Type: text/plain"
echo
echo "CGI executed"
EOF
```

실행 권한을 부여한다.

```bash
sudo chmod 755 /var/www/care/cgi-test/test.cgi
```

### 4-3. 취약 설정 추가

실습용 설정 파일을 별도로 만든다.

```bash
sudo nano /etc/apache2/conf-available/web-05-cgi-test.conf
```

내용은 다음과 같이 둔다.

```apache
<Directory /var/www/care/cgi-test>
    Options +ExecCGI
    AddHandler cgi-script .cgi
    Require all granted
</Directory>
```

설정을 활성화한다.

```bash
sudo a2enconf web-05-cgi-test
sudo apachectl configtest
sudo systemctl reload apache2
```

### 4-4. CGI 실행 확인

```bash
curl -i http://172.168.10.10/cgi-test/test.cgi
```

취약 재현이 성공하면 다음과 유사한 응답이 나온다.

```text
HTTP/1.1 200 OK
Content-Type: text/plain

CGI executed
```

이 결과는 지정된 `/cgi-bin/` 디렉터리가 아닌 `/cgi-test/` 경로에서도 CGI가 실행된다는 뜻이다.

즉 PDF 기준으로는 CGI 실행 가능 디렉터리가 제한되지 않은 취약 상태에 가깝다.

## 5. 조치 방법

조치 핵심은 CGI 실행 가능 범위를 다시 제한하는 것이다.

방법은 두 가지다.

|조치|설명|
|---|---|
|CGI를 사용하지 않는 경우|CGI 모듈 또는 CGI 설정을 비활성화|
|CGI를 사용하는 경우|지정된 `/cgi-bin/` 같은 디렉터리에서만 실행 허용|

현재 서버는 최초 진단 기준으로 CGI 실행이 `/cgi-bin/`에 제한되어 있으므로, 실습으로 추가한 `/cgi-test/` 설정만 제거하면 된다.

### 5-1. 실습용 CGI 설정 비활성화

```bash
sudo a2disconf web-05-cgi-test
```

### 5-2. 실습용 설정 파일 제거 또는 보관

완전히 제거하려면 다음과 같이 한다.

```bash
sudo rm /etc/apache2/conf-available/web-05-cgi-test.conf
```

보고서 증거 보관을 위해 파일을 남기고 싶다면 주석 처리하거나 `.bak`으로 바꿔둔다.

```bash
sudo mv /etc/apache2/conf-available/web-05-cgi-test.conf /etc/apache2/conf-available/web-05-cgi-test.conf.bak
```

### 5-3. 테스트 CGI 디렉터리 제거

```bash
sudo rm -rf /var/www/care/cgi-test
```

### 5-4. Apache 설정 문법 검사

```bash
sudo apachectl configtest
```

정상이라면 다음 결과가 나와야 한다.

```text
Syntax OK
```

### 5-5. Apache reload

```bash
sudo systemctl reload apache2
```

## 6. 조치 후 확인

조치 후에는 CGI 실행이 다시 제한되었는지 확인한다.

### 6-1. 실습 설정 비활성화 확인

```bash
apache2ctl -S
```

또는 다음 명령으로 실습용 설정이 활성화되어 있지 않은지 확인한다.

```bash
ls -l /etc/apache2/conf-enabled/ | grep web-05-cgi-test
```

기대 결과는 다음이다.

```text
출력 없음
```

### 6-2. ExecCGI 설정 확인

```bash
grep -r 'ExecCGI' /etc/apache2/apache2.conf /etc/apache2/sites-available/ /etc/apache2/sites-enabled/ /etc/apache2/conf-available/ /etc/apache2/conf-enabled/ 2>/dev/null | grep -v '^\s*#'
```

조치 후에는 일반 웹 루트나 업로드 디렉터리에 `Options +ExecCGI`가 남아 있지 않아야 한다.

### 6-3. CGI 실행 차단 확인

```bash
curl -i http://172.168.10.10/cgi-test/test.cgi
```

테스트 디렉터리를 삭제했다면 기대 결과는 다음 중 하나다.

```text
HTTP/1.1 404 Not Found
```

또는:

```text
HTTP/1.1 403 Forbidden
```

중요한 것은 `CGI executed`가 더 이상 출력되지 않는 것이다.

### 6-4. 기존 제한 상태 확인

최초 진단에서 확인된 정상 상태는 다음이다.

```apache
ScriptAlias /cgi-bin/ /usr/lib/cgi-bin/
```

즉 CGI를 사용한다면 `/cgi-bin/`처럼 지정된 디렉터리에서만 실행되도록 제한한다.

## 7. 증거 정리

### 7-1. 최초 양호 상태 증거

최초 진단 결과:

```text
WEB-05 · CGI/ISAPI 실행 제한
CGI 실행이 ScriptAlias로 지정된 /cgi-bin/ 디렉터리로만 제한됨
```

확인된 설정:

```apache
ScriptAlias /cgi-bin/ /usr/lib/cgi-bin/
```

### 7-2. 취약 재현 증거

실습용 취약 설정:

```apache
<Directory /var/www/care/cgi-test>
    Options +ExecCGI
    AddHandler cgi-script .cgi
    Require all granted
</Directory>
```

실행 확인 요청:

```bash
curl -i http://172.168.10.10/cgi-test/test.cgi
```

취약 재현 성공 기대 결과:

```text
CGI executed
```

이 결과는 지정된 `/cgi-bin/` 외부의 일반 웹 경로에서도 CGI가 실행됨을 의미한다.

### 7-3. 조치 후 증거

실습용 설정 비활성화 확인:

```bash
ls -l /etc/apache2/conf-enabled/ | grep web-05-cgi-test
```

기대 결과:

```text
출력 없음
```

조치 후 CGI 실행 확인:

```bash
curl -i http://172.168.10.10/cgi-test/test.cgi
```

기대 결과:

```text
404 Not Found
```

또는:

```text
403 Forbidden
```

## 8. 판단

|항목|판단|
|---|---|
|최초 진단|양호|
|진단 근거|CGI 실행이 `ScriptAlias /cgi-bin/ /usr/lib/cgi-bin/`로 제한됨|
|실습 처리|실습용 `/cgi-test/` 경로에 `ExecCGI`를 부여하여 취약 상태 재현 후 제거|
|조치 전 판단|최초 상태는 양호, 실습 재현 상태는 취약|
|조치 후 판단|실습용 CGI 설정 제거 후 양호|
|증거 상태|최초 진단 결과 확보, 취약 재현 및 조치 후 접근 증거 필요|

현재 서버는 최초 진단 기준으로 CGI 실행이 지정된 `/cgi-bin/` 디렉터리로 제한되어 있으므로 WEB-05는 **양호**로 판단한다.

다만 PDF의 취약 조건을 실습하기 위해 `/var/www/care/cgi-test`에 `ExecCGI`를 부여하고 `.cgi` 실행을 허용하면, 지정된 CGI 디렉터리 외부에서도 CGI가 실행되는 취약 상태를 재현할 수 있다.

조치는 실습용 `ExecCGI` 설정을 제거하고, CGI 실행 가능 위치를 다시 지정된 디렉터리로 제한하는 방식으로 수행한다.

조치 후 일반 웹 경로에서 CGI가 실행되지 않고, 지정된 CGI 디렉터리 외부의 `.cgi` 요청이 `403 Forbidden` 또는 `404 Not Found`로 처리되면 WEB-05는 조치 후 **양호**로 판단한다.