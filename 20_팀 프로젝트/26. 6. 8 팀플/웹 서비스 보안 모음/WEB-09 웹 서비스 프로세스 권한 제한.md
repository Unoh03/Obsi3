---
type: lab  
topic: web-service-security  
source: 주요정보통신기반시설 기술적 취약점 분석·평가 방법 상세가이드  
source_pages:
- 295
- 296
- 297
- 298
- 299  
status: draft  
created: 2026-06-18  
tags:
    
- 🏷️과목/웹서비스보안
    
- 🏷️주제/WEB-09
    
- 🏷️주제/Process-Privilege
    
- 🏷️주제/Apache
    
- 🏷️상태/draft
    

---
# WEB-09 웹 서비스 프로세스 권한 제한

## 1. PDF 기준

PDF p.295-299의 WEB-09는 웹 서비스 프로세스가 **관리자 권한으로 구동되고 있는지** 점검하는 항목이다.

웹 서버 프로세스가 관리자 권한으로 동작하면, 웹 애플리케이션 취약점을 통해 공격자가 웹 서버 프로세스 권한을 획득했을 때 피해 범위가 커진다.

예를 들어 Apache 자식 프로세스가 `root` 권한으로 동작하는 경우, 웹 취약점이 서버 권한 탈취로 이어졌을 때 시스템 파일 변경, 로그 훼손, 설정 파일 변조, 추가 악성 파일 배치 같은 피해가 발생할 수 있다.

PDF의 판단 기준은 다음과 같다.

|판단|기준|
|---|---|
|양호|웹 프로세스가 관리자 권한이 아닌 별도 계정으로 구동되는 경우|
|취약|웹 프로세스가 관리자 권한으로 구동되는 경우|

Apache 기준 조치 방향은 다음과 같다.

|단계|내용|
|---|---|
|Step 1|`envvars` 파일에서 Apache 실행 계정을 관리자 계정이 아닌 별도 계정으로 설정|
|Step 2|Apache 관련 파일과 디렉터리 소유권을 실행 계정에 맞게 조정|
|Step 3|웹 서비스 실행 계정의 로그인 쉘 제한|
|Step 4|Apache 재구동|

Ubuntu Apache 환경에서는 일반적으로 다음 계정을 사용한다.

```apache
export APACHE_RUN_USER=www-data
export APACHE_RUN_GROUP=www-data
```

중요한 점은 Apache에서 `root` 프로세스가 하나 보인다고 무조건 취약은 아니라는 것이다.

Apache는 80번 포트 같은 privileged port 바인딩과 자식 프로세스 관리를 위해 마스터 프로세스가 `root`로 보일 수 있다. 실제 웹 요청을 처리하는 자식 프로세스가 `www-data` 같은 낮은 권한 계정으로 실행되는지가 핵심이다.

## 2. 최초 진단 결과

`AWS WEB 약점 진단 결과.md` 기준 최초 진단 결과는 **양호**이다.

|항목|내용|
|---|---|
|진단 결과|양호|
|진단 근거|Apache 자식 프로세스가 `www-data` 계정으로 구동 중|
|확인된 상태|`root` 마스터 프로세스 / `www-data` 자식 프로세스|
|최초 판단|실제 요청 처리 프로세스가 관리자 권한이 아니므로 양호|

진단 결과 요약은 다음과 같다.

```text
root(마스터) / www-data(자식 프로세스 8건)
```

이 결과는 Apache 마스터 프로세스는 `root`로 보이지만, 실제 요청을 처리하는 자식 프로세스는 `www-data`로 동작하고 있다는 뜻이다.

따라서 최초 진단 기준 WEB-09는 양호로 판단한다.

## 3. 현재 서버 상태 해석

WEB-09에서 봐야 하는 것은 “Apache 프로세스 전체에 root가 보이는가”가 아니라, **웹 요청을 처리하는 worker 또는 child process가 어떤 계정으로 실행되는가**이다.

Apache 프로세스 구조는 일반적으로 다음과 같다.

|프로세스|일반적인 권한|의미|
|---|---|---|
|마스터 프로세스|root|포트 바인딩, 자식 프로세스 관리|
|자식 프로세스|www-data|실제 HTTP 요청 처리|

즉 다음 상태는 일반적으로 정상이다.

```text
root      1000  ... /usr/sbin/apache2 -k start
www-data  1001  ... /usr/sbin/apache2 -k start
www-data  1002  ... /usr/sbin/apache2 -k start
```

반대로 다음 상태는 취약하다.

```text
root      1000  ... /usr/sbin/apache2 -k start
root      1001  ... /usr/sbin/apache2 -k start
root      1002  ... /usr/sbin/apache2 -k start
```

현재 진단 결과는 `www-data` 자식 프로세스가 확인되었으므로 양호하다.

다만 PDF 내용을 실습하기 위해서는 취약한 설정이 어떤 형태인지 확인해야 한다. 이 항목은 실제 Apache를 `root` 자식 프로세스로 재구동하는 방식이 위험하고, Apache가 설정을 거부하거나 서비스가 비정상화될 수 있으므로 **실제 서비스 취약화 대신 설정 파일 수준의 모의 취약 재현**으로 진행한다.

## 4. 실습 전 확인

실습을 시작하기 전에 현재 Apache 프로세스 권한과 실행 계정 설정을 확인한다.

### 4-1. Apache 상태 확인

```bash
systemctl status apache2 --no-pager
```

### 4-2. Apache 프로세스 권한 확인

```bash
ps -eo user,group,pid,ppid,cmd | grep '[a]pache2'
```

기대되는 양호 상태는 다음과 유사하다.

```text
root     root       1000     1 /usr/sbin/apache2 -k start
www-data www-data   1001  1000 /usr/sbin/apache2 -k start
www-data www-data   1002  1000 /usr/sbin/apache2 -k start
```

마스터 프로세스가 `root`인 것은 일반적인 구조다.  
중요한 것은 자식 프로세스가 `www-data`인지 확인하는 것이다.

### 4-3. Apache 실행 계정 설정 확인

```bash
grep -E '^export APACHE_RUN_USER=|^export APACHE_RUN_GROUP=' /etc/apache2/envvars
```

기대 결과는 다음과 같다.

```text
export APACHE_RUN_USER=www-data
export APACHE_RUN_GROUP=www-data
```

### 4-4. www-data 계정 확인

```bash
id www-data
```

```bash
getent passwd www-data
```

기대 결과 예시는 다음과 같다.

```text
uid=33(www-data) gid=33(www-data) groups=33(www-data)
```

```text
www-data:x:33:33:www-data:/var/www:/usr/sbin/nologin
```

로그인 쉘이 `/usr/sbin/nologin` 또는 `/sbin/nologin`이면 웹 서비스 계정의 직접 로그인도 제한된 상태다.

### 4-5. 실습용 변수 지정

```bash
ENVVARS=/etc/apache2/envvars
BACKUP=/etc/apache2/envvars.bak.WEB-09
VULN_COPY=/tmp/web09-envvars.vulnerable
SAFE_COPY=/tmp/web09-envvars.safe
```

## 5. 취약 재현

이 항목은 최초 진단 결과가 양호이다.

원칙대로라면 양호 상태를 의도적으로 취약하게 만들어야 하지만, WEB-09에서 실제 Apache 자식 프로세스를 `root`로 실행하도록 바꾸는 것은 위험하다. 서비스가 중단될 수 있고, Apache가 root 자식 프로세스 실행을 거부할 수 있으며, 실습 서버라도 피해 범위가 커진다.

따라서 이 노트에서는 실제 Apache 서비스를 root 권한으로 재구동하지 않고, **설정 파일 복사본을 이용해 취약 설정이 어떤 형태인지 모의 재현**한다.

> 주의: `/etc/apache2/envvars`를 실제로 `root:root` 실행 계정으로 바꾸고 Apache를 재시작하지 않는다.  
> 이 실습은 취약 설정 형태를 확인하는 모의 재현이다.  
> 실제 조치는 현재 안전 설정을 확인하고 유지하는 방식으로 수행한다.

### 5-1. 현재 envvars 백업

```bash
sudo cp "$ENVVARS" "$BACKUP"
```

백업 확인:

```bash
ls -l "$BACKUP"
```

### 5-2. 실습용 복사본 생성

```bash
cp "$ENVVARS" "$VULN_COPY"
cp "$ENVVARS" "$SAFE_COPY"
```

### 5-3. 취약 설정 형태 만들기

실습용 복사본에서 실행 계정을 `root`로 바꾼다.

```bash
sed -i 's/^export APACHE_RUN_USER=.*/export APACHE_RUN_USER=root/' "$VULN_COPY"
sed -i 's/^export APACHE_RUN_GROUP=.*/export APACHE_RUN_GROUP=root/' "$VULN_COPY"
```

### 5-4. 취약 설정 확인

```bash
grep -E '^export APACHE_RUN_USER=|^export APACHE_RUN_GROUP=' "$VULN_COPY"
```

취약 설정 형태는 다음과 같다.

```text
export APACHE_RUN_USER=root
export APACHE_RUN_GROUP=root
```

이 설정은 웹 서비스 프로세스를 관리자 권한으로 실행하려는 구성이므로 PDF 기준 취약 설정에 해당한다.

### 5-5. 현재 실제 Apache는 안전 상태인지 재확인

모의 취약 설정을 만들었더라도 실제 Apache 설정은 건드리지 않았는지 확인한다.

```bash
grep -E '^export APACHE_RUN_USER=|^export APACHE_RUN_GROUP=' "$ENVVARS"
```

기대 결과는 다음이다.

```text
export APACHE_RUN_USER=www-data
export APACHE_RUN_GROUP=www-data
```

실제 프로세스도 다시 확인한다.

```bash
ps -eo user,group,pid,ppid,cmd | grep '[a]pache2'
```

기대 결과는 자식 프로세스가 `www-data`인 상태다.

```text
www-data www-data ... /usr/sbin/apache2 -k start
```

## 6. 조치 방법

조치 핵심은 Apache 자식 프로세스가 관리자 계정이 아닌 별도 계정으로 실행되도록 유지하는 것이다.

현재 서버는 최초 상태가 양호이므로, 실제 조치는 다음을 확인하고 유지하는 방식으로 수행한다.

```text
1. envvars에서 APACHE_RUN_USER와 APACHE_RUN_GROUP을 www-data로 설정
2. Apache 관련 주요 경로의 소유권과 권한 확인
3. www-data 계정 로그인 제한 확인
4. Apache 설정 문법 검사
5. Apache restart
```

### 6-1. envvars 안전 설정 확인 또는 복구

현재 설정을 확인한다.

```bash
grep -E '^export APACHE_RUN_USER=|^export APACHE_RUN_GROUP=' "$ENVVARS"
```

만약 값이 `root`이거나 다른 관리자 계정으로 되어 있다면 다음처럼 수정한다.

```bash
sudo sed -i 's/^export APACHE_RUN_USER=.*/export APACHE_RUN_USER=www-data/' "$ENVVARS"
sudo sed -i 's/^export APACHE_RUN_GROUP=.*/export APACHE_RUN_GROUP=www-data/' "$ENVVARS"
```

수정 후 다시 확인한다.

```bash
grep -E '^export APACHE_RUN_USER=|^export APACHE_RUN_GROUP=' "$ENVVARS"
```

기대 결과는 다음이다.

```text
export APACHE_RUN_USER=www-data
export APACHE_RUN_GROUP=www-data
```

### 6-2. www-data 로그인 제한 확인

```bash
getent passwd www-data
```

로그인 쉘이 `/usr/sbin/nologin` 또는 `/sbin/nologin`이면 양호하다.

```text
www-data:x:33:33:www-data:/var/www:/usr/sbin/nologin
```

만약 로그인 가능한 쉘이 설정되어 있다면 다음처럼 제한한다.

```bash
sudo usermod -s /usr/sbin/nologin www-data
```

일부 배포판에서는 다음 경로를 사용할 수 있다.

```bash
sudo usermod -s /sbin/nologin www-data
```

### 6-3. 주요 경로 소유권 확인

Apache 설정 디렉터리, 웹 루트, 로그 디렉터리 소유권을 확인한다.

```bash
ls -ld /etc/apache2 /var/www /var/www/care /var/log/apache2
```

권한 상태는 운영 정책에 맞게 해석해야 한다.

주의할 점은 `/etc/apache2` 전체를 무조건 `www-data:www-data`로 바꾸는 것은 권장하지 않는다는 것이다.  
PDF 예시는 서비스 파일 소유권 변경을 제시하지만, Ubuntu 운영 환경에서는 설정 파일은 보통 `root`가 소유하고 웹 서버 프로세스가 읽기만 하는 구조가 더 안전하다.

따라서 실습 서버에서는 다음 원칙을 적용한다.

|경로|권장 방향|
|---|---|
|`/etc/apache2`|root 소유 유지, 일반 사용자 쓰기 금지|
|`/var/www/care`|배포 정책에 따라 관리, 웹 서버가 필요한 범위만 읽기/쓰기|
|`/var/log/apache2`|Apache 로그 기록 가능 상태 유지|
|업로드 디렉터리|필요한 경우에만 `www-data` 쓰기 허용|

이 항목의 핵심은 디렉터리 전체 소유권을 무조건 바꾸는 것이 아니라, 웹 서비스 프로세스가 관리자 권한으로 실행되지 않도록 하는 것이다.

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

## 7. 조치 후 확인

조치 후에는 Apache 자식 프로세스가 `www-data`로 동작하는지 확인한다.

### 7-1. Apache 서비스 상태 확인

```bash
systemctl status apache2 --no-pager
```

정상 상태라면 `active (running)`이 보여야 한다.

```text
Active: active (running)
```

### 7-2. Apache 프로세스 권한 확인

```bash
ps -eo user,group,pid,ppid,cmd | grep '[a]pache2'
```

양호 상태의 예시는 다음과 같다.

```text
root     root       1000     1 /usr/sbin/apache2 -k start
www-data www-data   1001  1000 /usr/sbin/apache2 -k start
www-data www-data   1002  1000 /usr/sbin/apache2 -k start
```

판단 기준은 다음이다.

|확인 결과|판단|
|---|---|
|마스터만 root, 자식은 www-data|양호|
|요청 처리 자식 프로세스도 root|취약|
|Apache가 비정상 종료|조치 실패|

### 7-3. envvars 설정 확인

```bash
grep -E '^export APACHE_RUN_USER=|^export APACHE_RUN_GROUP=' /etc/apache2/envvars
```

기대 결과는 다음이다.

```text
export APACHE_RUN_USER=www-data
export APACHE_RUN_GROUP=www-data
```

### 7-4. 로그인 쉘 확인

```bash
getent passwd www-data
```

기대 결과는 다음과 유사하다.

```text
www-data:x:33:33:www-data:/var/www:/usr/sbin/nologin
```

### 7-5. 웹 서비스 정상 응답 확인

```bash
curl -i http://172.168.10.10/
```

정상이라면 `200 OK`, `302 Found`, 애플리케이션 로그인 페이지 등 현재 서비스에 맞는 응답이 나와야 한다.

```text
HTTP/1.1 200 OK
```

## 8. 실행 순서 요약

실습 중에는 아래 순서대로 진행한다.

### 8-1. 현재 상태 확인

```bash
ENVVARS=/etc/apache2/envvars
BACKUP=/etc/apache2/envvars.bak.WEB-09
VULN_COPY=/tmp/web09-envvars.vulnerable
SAFE_COPY=/tmp/web09-envvars.safe
```

```bash
systemctl status apache2 --no-pager
```

```bash
ps -eo user,group,pid,ppid,cmd | grep '[a]pache2'
```

```bash
grep -E '^export APACHE_RUN_USER=|^export APACHE_RUN_GROUP=' "$ENVVARS"
```

```bash
id www-data
```

```bash
getent passwd www-data
```

### 8-2. 취약 설정 모의 재현

```bash
sudo cp "$ENVVARS" "$BACKUP"
```

```bash
cp "$ENVVARS" "$VULN_COPY"
cp "$ENVVARS" "$SAFE_COPY"
```

```bash
sed -i 's/^export APACHE_RUN_USER=.*/export APACHE_RUN_USER=root/' "$VULN_COPY"
sed -i 's/^export APACHE_RUN_GROUP=.*/export APACHE_RUN_GROUP=root/' "$VULN_COPY"
```

```bash
grep -E '^export APACHE_RUN_USER=|^export APACHE_RUN_GROUP=' "$VULN_COPY"
```

취약 설정 형태 기대 결과:

```text
export APACHE_RUN_USER=root
export APACHE_RUN_GROUP=root
```

실제 Apache 설정이 안전한지 재확인한다.

```bash
grep -E '^export APACHE_RUN_USER=|^export APACHE_RUN_GROUP=' "$ENVVARS"
```

기대 결과:

```text
export APACHE_RUN_USER=www-data
export APACHE_RUN_GROUP=www-data
```

### 8-3. 조치 및 복구

현재 설정이 이미 양호하다면 변경하지 않는다.

만약 실제 `envvars`가 root 또는 관리자 계정으로 되어 있다면 다음을 실행한다.

```bash
sudo sed -i 's/^export APACHE_RUN_USER=.*/export APACHE_RUN_USER=www-data/' "$ENVVARS"
sudo sed -i 's/^export APACHE_RUN_GROUP=.*/export APACHE_RUN_GROUP=www-data/' "$ENVVARS"
```

로그인 쉘을 제한한다.

```bash
sudo usermod -s /usr/sbin/nologin www-data
```

만약 `/usr/sbin/nologin`이 없고 `/sbin/nologin`만 있다면 다음을 사용한다.

```bash
sudo usermod -s /sbin/nologin www-data
```

설정 문법을 확인한다.

```bash
sudo apachectl configtest
```

Apache를 재시작한다.

```bash
sudo systemctl restart apache2
```

### 8-4. 조치 후 확인

```bash
systemctl status apache2 --no-pager
```

```bash
ps -eo user,group,pid,ppid,cmd | grep '[a]pache2'
```

```bash
grep -E '^export APACHE_RUN_USER=|^export APACHE_RUN_GROUP=' "$ENVVARS"
```

```bash
getent passwd www-data
```

```bash
curl -i http://172.168.10.10/
```

기대 결과:

```text
Apache 마스터 프로세스는 root
Apache 자식 프로세스는 www-data
APACHE_RUN_USER=www-data
APACHE_RUN_GROUP=www-data
www-data 로그인 쉘은 nologin
웹 서비스 정상 응답
```

### 8-5. 실습 파일 정리

```bash
rm -f "$VULN_COPY" "$SAFE_COPY"
```

백업 파일은 증거 확보 후 필요 없으면 제거한다.

```bash
sudo rm -f "$BACKUP"
```

정리 확인:

```bash
ls -l "$VULN_COPY" "$SAFE_COPY" "$BACKUP" 2>/dev/null
```

기대 결과:

```text
출력 없음
```

## 9. 증거 정리

### 9-1. 최초 상태 증거

최초 진단 결과:

```text
WEB-09 · 웹서비스 프로세스 권한 제한
Apache 자식 프로세스가 www-data 계정으로 구동 중
root(마스터) / www-data(자식 프로세스 8건)
```

프로세스 확인 명령어:

```bash
ps -eo user,group,pid,ppid,cmd | grep '[a]pache2'
```

양호 상태 기대 결과:

```text
root     root       ... /usr/sbin/apache2 -k start
www-data www-data   ... /usr/sbin/apache2 -k start
```

### 9-2. 취약 설정 모의 재현 증거

모의 취약 설정 확인:

```bash
grep -E '^export APACHE_RUN_USER=|^export APACHE_RUN_GROUP=' "$VULN_COPY"
```

취약 설정 형태:

```text
export APACHE_RUN_USER=root
export APACHE_RUN_GROUP=root
```

이 설정은 웹 서비스 프로세스를 관리자 권한으로 실행하려는 구성이므로 PDF 기준 취약 설정이다.

### 9-3. 조치 후 증거

실제 envvars 확인:

```bash
grep -E '^export APACHE_RUN_USER=|^export APACHE_RUN_GROUP=' /etc/apache2/envvars
```

기대 결과:

```text
export APACHE_RUN_USER=www-data
export APACHE_RUN_GROUP=www-data
```

프로세스 권한 확인:

```bash
ps -eo user,group,pid,ppid,cmd | grep '[a]pache2'
```

기대 결과:

```text
root 마스터 프로세스 1개
www-data 자식 프로세스 다수
```

웹 서비스 계정 로그인 쉘 확인:

```bash
getent passwd www-data
```

기대 결과:

```text
www-data:x:33:33:www-data:/var/www:/usr/sbin/nologin
```

## 10. 판단

|항목|판단|
|---|---|
|최초 진단|양호|
|진단 근거|Apache 자식 프로세스가 `www-data` 계정으로 구동 중|
|실습 처리|실제 root 실행은 하지 않고, `envvars` 복사본으로 취약 설정 형태를 모의 재현|
|조치 전 판단|최초 상태는 양호, root 실행 설정은 취약|
|조치 후 판단|Apache 자식 프로세스가 `www-data`로 유지되면 양호|
|증거 상태|최초 진단 결과 확보, 프로세스 권한 및 envvars 확인 증거 필요|

현재 서버는 최초 진단 기준으로 Apache 자식 프로세스가 `www-data` 계정으로 구동 중이므로 WEB-09는 **양호**로 판단한다.

Apache 마스터 프로세스가 `root`로 보이는 것은 일반적인 구조일 수 있다. WEB-09의 핵심은 실제 웹 요청을 처리하는 자식 프로세스가 관리자 권한으로 동작하지 않는지 확인하는 것이다.

실습에서는 실제 Apache를 root 자식 프로세스로 재구동하지 않고, `envvars` 복사본을 이용해 `APACHE_RUN_USER=root`, `APACHE_RUN_GROUP=root` 형태의 취약 설정을 모의 재현한다. 실제 조치에서는 `/etc/apache2/envvars`가 `www-data`로 설정되어 있고, Apache 자식 프로세스가 `www-data`로 실행되며, `www-data` 계정의 로그인 쉘이 `nologin`으로 제한되어 있으면 조치 후 **양호**로 판단한다.