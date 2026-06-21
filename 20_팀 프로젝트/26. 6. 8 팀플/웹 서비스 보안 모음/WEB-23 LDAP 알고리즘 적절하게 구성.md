---

type: lab  
topic: web-service-security  
source: 주요정보통신기반시설 기술적 취약점 분석·평가 방법 상세가이드  
source_pages:

- 342  
status: draft  
created: 2026-06-18  
tags:
    
- 🏷️과목/웹서비스보안
    
- 🏷️주제/WEB-23
    
- 🏷️주제/LDAP
    
- 🏷️주제/Password-Digest
    
- 🏷️주제/Tomcat
    
- 🏷️상태/draft
    

---
# WEB-23 LDAP 알고리즘 적절하게 구성

## 1. PDF 기준

PDF p.342의 WEB-23은 **LDAP 연결 인증 시 안전한 비밀번호 다이제스트 알고리즘을 사용하는지** 점검하는 항목이다.

LDAP는 네트워크상에서 사용자, 조직, 장비, 권한 같은 디렉터리 정보를 조회하거나 관리하기 위한 프로토콜이다. 웹 서버 또는 WAS가 LDAP와 연동되어 사용자 인증을 수행하는 경우, 인증 정보가 취약한 방식으로 처리되면 스니핑이나 무차별 대입 공격에 의해 인증 정보가 노출될 수 있다.

PDF의 점검 목적은 다음과 같다.

```text
LDAP 연결 시 안전한 비밀번호 다이제스트 알고리즘을 사용하여
비밀번호 평문 전송 또는 취약한 다이제스트 사용으로 발생할 수 있는
인증 정보 노출 위험을 줄인다.
```

PDF의 판단 기준은 다음과 같다.

|판단|기준|
|---|---|
|양호|LDAP 연결 인증 시 안전한 비밀번호 다이제스트 알고리즘을 사용하는 경우|
|취약|LDAP 연결 인증 시 안전한 비밀번호 다이제스트 알고리즘을 사용하지 않는 경우|

PDF의 조치 기준은 다음이다.

```text
LDAP 연결 인증 시 SHA-256 이상의 알고리즘을 사용하도록 설정
```

PDF의 점검 사례는 Tomcat을 기준으로 한다.

```bash
grep 'digest=' /[Tomcat 설치 디렉터리]/conf/server.xml
```

취약 또는 미흡한 설정 예시는 다음과 같다.

```xml
digest="SSHA"
```

조치 예시는 다음과 같다.

```xml
digest="SHA-256"
```

즉 WEB-23의 핵심은 다음이다.

```text
Tomcat 등 WAS에서 LDAP 인증을 사용할 때
LDAP 인증 비밀번호 다이제스트 알고리즘이 SHA-256 이상인지 확인한다.
```

## 2. 최초 진단 결과

`AWS WEB 약점 진단 결과.md`의 WEB-23 항목은 PDF의 WEB-23과 내용이 일치하지 않는다.

진단 파일의 WEB-23은 다음 내용으로 되어 있다.

```text
WEB-23 | HTTP 메서드 제한 | LimitExcept 설정 확인
```

하지만 PDF p.342의 WEB-23은 **HTTP 메서드 제한이 아니라 LDAP 알고리즘 적절하게 구성** 항목이다.

따라서 이 노트에서는 다음처럼 처리한다.

|구분|내용|
|---|---|
|PDF 기준 WEB-23|LDAP 알고리즘 적절하게 구성|
|진단 파일 WEB-23|HTTP 메서드 제한|
|일치 여부|불일치|
|자동 진단 결과 활용|PDF WEB-23의 직접 근거로 사용 불가|
|이 노트의 판단 방식|Tomcat/LDAP 사용 여부와 `digest=` 설정 수동 확인|

현재 실습 환경은 Apache + PHP 기반 CARE 서버다. PDF의 WEB-23 점검 사례는 Tomcat의 `server.xml`과 LDAP 인증 설정을 대상으로 한다.

따라서 현재 환경에서는 먼저 다음을 확인해야 한다.

```text
1. Tomcat이 설치되어 있는가
2. CARE 서비스가 Tomcat에서 동작하는가
3. LDAP 인증을 사용하는가
4. LDAP 관련 digest 설정이 존재하는가
```

이 조건이 모두 해당되지 않으면 WEB-23은 현재 Apache/PHP/CARE 환경에 직접 적용되는 항목이 아니다.

## 3. 현재 서버 상태 해석

WEB-23은 Apache의 일반 HTTP 설정 항목이 아니다.  
PDF 기준으로는 Tomcat과 LDAP 인증 설정을 대상으로 한다.

현재 CARE 서버가 Apache + PHP + MySQL 기반으로 동작하고, Tomcat LDAP 인증을 사용하지 않는다면 다음처럼 해석한다.

|확인 대상|현재 CARE 환경에서의 의미|
|---|---|
|Tomcat|CARE 서비스의 주 실행 환경이 아니면 직접 적용 대상 아님|
|LDAP|CARE 로그인 방식이 LDAP가 아니라 MySQL `member` 테이블 기반이면 직접 적용 대상 아님|
|`server.xml`|Tomcat LDAP Realm 설정이 없으면 점검 대상 없음|
|`digest=`|LDAP Realm 또는 인증 설정에 존재하지 않으면 조치 대상 없음|
|Apache 설정|WEB-23의 직접 점검 대상이 아님|

CARE 애플리케이션이 일반 PHP 로그인과 MySQL 계정 테이블을 사용한다면, WEB-23의 LDAP 다이제스트 알고리즘 설정은 현재 서비스 구조에 직접 대응하지 않는다.

다만 다음과 같은 경우에는 WEB-23을 적용 대상으로 다시 봐야 한다.

```text
1. Tomcat이 별도 WAS로 설치되어 있음
2. Tomcat Manager 또는 별도 Java 애플리케이션이 LDAP 인증을 사용함
3. /etc/tomcat*/server.xml 또는 conf/server.xml에 LDAP Realm이 있음
4. digest= 설정이 존재함
5. LDAP bind 또는 LDAP password comparison 기능을 사용함
```

이 경우 `digest` 값이 `SHA-256` 이상인지 확인한다.

## 4. 실습 전 확인

실습 전에는 현재 서버에 Tomcat과 LDAP 설정이 있는지 확인한다.

### 4-1. Apache/PHP 서비스 확인

```bash
apache2ctl -S
```

```bash
php -v
```

```bash
grep -R "DocumentRoot" /etc/apache2/sites-enabled/ /etc/apache2/sites-available/ 2>/dev/null
```

이 노트는 CARE 서버가 `/var/www/care`를 DocumentRoot로 사용하는 Apache/PHP 환경이라고 가정한다.

### 4-2. Tomcat 설치 여부 확인

```bash
systemctl list-units --type=service | grep -i tomcat
```

패키지 기준으로도 확인한다.

```bash
dpkg -l | grep -i tomcat
```

프로세스 기준으로도 확인한다.

```bash
ps -ef | grep -i '[t]omcat'
```

Tomcat이 없으면 다음처럼 출력이 없을 수 있다.

```text
출력 없음
```

### 4-3. Tomcat 설정 파일 후보 확인

Tomcat이 설치되어 있을 가능성이 있으면 설정 파일 후보를 찾는다.

```bash
sudo find /etc /opt /usr/local -path '*tomcat*' -name 'server.xml' 2>/dev/null
```

일반적인 후보는 다음과 같다.

```text
/etc/tomcat9/server.xml
/etc/tomcat10/server.xml
/opt/tomcat/conf/server.xml
```

### 4-4. LDAP 설정 확인

Tomcat 설정 파일에서 LDAP 관련 설정을 찾는다.

```bash
sudo grep -RniE 'ldap|JNDIRealm|UserDatabaseRealm|digest=' /etc/tomcat* /opt/tomcat/conf 2>/dev/null
```

출력이 없다면 Tomcat LDAP 설정이 확인되지 않은 것이다.

```text
출력 없음
```

### 4-5. CARE PHP 코드에서 LDAP 사용 여부 확인

CARE 소스 경로에서 LDAP 관련 함수를 검색한다.

```bash
grep -RniE 'ldap_connect|ldap_bind|ldap_search|ldap_set_option|LDAP|ldap_' /var/www/care 2>/dev/null
```

CARE 애플리케이션이 LDAP를 사용하지 않으면 출력이 없어야 한다.

```text
출력 없음
```

### 4-6. PHP LDAP 모듈 확인

```bash
php -m | grep -i ldap
```

출력이 없으면 PHP LDAP 확장이 로드되지 않은 상태다.

```text
출력 없음
```

단, PHP LDAP 모듈이 설치되어 있지 않다는 것만으로 WEB-23 양호를 의미하지는 않는다.  
WEB-23은 Tomcat LDAP 인증 설정의 다이제스트 알고리즘 점검 항목이므로, 핵심은 실제 LDAP 인증 사용 여부다.

## 5. 취약 재현

현재 Apache/PHP/CARE 환경에 Tomcat LDAP 인증이 없다면 실제 운영 환경을 취약하게 만들 필요는 없다.  
대신 PDF의 취약 조건을 이해하기 위해 **실습용 설정 파일을 `/tmp`에 만들어 정적 검토 방식으로 재현**한다.

> 주의: 이 절차는 실제 Tomcat 설정을 수정하지 않는다.  
> `/tmp/web23-server.xml` 파일만 만들어 취약 설정과 조치 설정을 비교한다.  
> 운영 Tomcat이 있는 경우에도 실제 `server.xml`을 직접 수정하기 전에 반드시 백업한다.

취약 재현의 핵심은 다음이다.

```text
digest 값이 SHA-256 미만 또는 권고 기준보다 약한 값으로 설정된 상태를 만든다.
```

### 5-1. 실습용 취약 server.xml 생성

```bash
cat > /tmp/web23-server.xml <<'EOF'
<Server>
  <Service name="Catalina">
    <Engine name="Catalina" defaultHost="localhost">
      <Realm className="org.apache.catalina.realm.JNDIRealm"
             connectionURL="ldap://ldap.example.local:389"
             userBase="ou=users,dc=example,dc=local"
             userSearch="(uid={0})"
             digest="SSHA" />
    </Engine>
  </Service>
</Server>
EOF
```

### 5-2. 취약 digest 설정 확인

```bash
grep 'digest=' /tmp/web23-server.xml
```

취약 재현 상태의 기대 결과는 다음이다.

```text
digest="SSHA" />
```

`SSHA`는 PDF의 조치 예시에서 `SHA-256`으로 변경하라고 제시된 값이다.  
따라서 이 실습 파일은 PDF 기준 취약 설정 예시로 볼 수 있다.

### 5-3. 약한 알고리즘 탐지 예시

```bash
grep -E 'digest="(MD5|SHA|SSHA|SHA-1|SHA1)"' /tmp/web23-server.xml
```

취약 재현 상태의 기대 결과는 다음과 유사하다.

```text
             digest="SSHA" />
```

이 결과가 나오면 안전한 SHA-256 이상 알고리즘을 사용하지 않는 설정으로 판단한다.

## 6. 조치 방법

조치 핵심은 LDAP 인증 다이제스트 알고리즘을 `SHA-256` 이상으로 설정하는 것이다.

실제 Tomcat 환경에서 조치할 경우에는 먼저 설정 파일을 백업한다.

### 6-1. 실습용 설정 조치

실습 파일의 `digest` 값을 `SHA-256`으로 변경한다.

```bash
sed -i 's/digest="SSHA"/digest="SHA-256"/' /tmp/web23-server.xml
```

### 6-2. 조치 결과 확인

```bash
grep 'digest=' /tmp/web23-server.xml
```

조치 후 기대 결과는 다음이다.

```text
digest="SHA-256" />
```

### 6-3. 실제 Tomcat 환경 조치 예시

실제 Tomcat 설정 파일이 `/etc/tomcat9/server.xml`에 있다면 먼저 백업한다.

```bash
sudo cp /etc/tomcat9/server.xml /etc/tomcat9/server.xml.bak.WEB-23
```

`digest` 값을 확인한다.

```bash
sudo grep 'digest=' /etc/tomcat9/server.xml
```

취약한 값이 확인되면 `SHA-256` 이상으로 변경한다.

```bash
sudo sed -i -E 's/digest="[^"]+"/digest="SHA-256"/' /etc/tomcat9/server.xml
```

변경 결과를 확인한다.

```bash
sudo grep 'digest=' /etc/tomcat9/server.xml
```

Tomcat 설정 문법과 애플리케이션 동작에 문제가 없는지 확인한 뒤 재시작한다.

```bash
sudo systemctl restart tomcat9
```

Tomcat 버전이 다르면 서비스명은 다를 수 있다.

```bash
systemctl list-units --type=service | grep -i tomcat
```

예를 들어 Tomcat 10이면 다음처럼 재시작한다.

```bash
sudo systemctl restart tomcat10
```

## 7. 조치 후 확인

### 7-1. 실습 파일 조치 확인

```bash
grep 'digest=' /tmp/web23-server.xml
```

기대 결과:

```text
digest="SHA-256" />
```

### 7-2. 취약 알고리즘 미탐지 확인

```bash
grep -E 'digest="(MD5|SHA|SSHA|SHA-1|SHA1)"' /tmp/web23-server.xml
```

기대 결과:

```text
출력 없음
```

단, `SHA-256` 안에 `SHA` 문자열이 포함될 수 있으므로 단순 `grep SHA`가 아니라 정확한 패턴으로 검사해야 한다.

### 7-3. SHA-256 이상 사용 확인

```bash
grep -E 'digest="SHA-(256|384|512)"' /tmp/web23-server.xml
```

기대 결과:

```text
             digest="SHA-256" />
```

### 7-4. 실제 Tomcat 설정 확인

Tomcat이 있는 경우 실제 설정에서 확인한다.

```bash
sudo grep -RniE 'ldap|JNDIRealm|digest=' /etc/tomcat* /opt/tomcat/conf 2>/dev/null
```

양호 상태 예시는 다음이다.

```text
digest="SHA-256"
```

또는 더 강한 알고리즘이다.

```text
digest="SHA-384"
digest="SHA-512"
```

### 7-5. Tomcat 서비스 상태 확인

Tomcat을 실제로 재시작했다면 상태를 확인한다.

```bash
systemctl status tomcat9 --no-pager
```

또는 설치된 서비스명을 먼저 확인한다.

```bash
systemctl list-units --type=service | grep -i tomcat
```

정상 상태라면 다음과 유사하게 보여야 한다.

```text
Active: active (running)
```

### 7-6. CARE 서비스 영향 확인

현재 CARE 서비스가 Apache/PHP 기반이면 Tomcat 설정 변경과 직접 연결되지 않는다.  
그래도 실습 서버 상태를 확인하기 위해 Apache와 CARE 응답을 확인한다.

```bash
systemctl status apache2 --no-pager
```

```bash
curl -i http://172.168.10.10/
```

정상이라면 현재 CARE 애플리케이션 상태에 맞는 응답이 나와야 한다.

```text
HTTP/1.1 200 OK
```

또는:

```text
HTTP/1.1 302 Found
```

## 8. 실행 순서 요약

### 8-1. 현재 적용성 확인

```bash
systemctl list-units --type=service | grep -i tomcat
```

```bash
dpkg -l | grep -i tomcat
```

```bash
ps -ef | grep -i '[t]omcat'
```

```bash
sudo find /etc /opt /usr/local -path '*tomcat*' -name 'server.xml' 2>/dev/null
```

```bash
sudo grep -RniE 'ldap|JNDIRealm|UserDatabaseRealm|digest=' /etc/tomcat* /opt/tomcat/conf 2>/dev/null
```

```bash
grep -RniE 'ldap_connect|ldap_bind|ldap_search|ldap_set_option|LDAP|ldap_' /var/www/care 2>/dev/null
```

### 8-2. 실습용 취약 설정 생성

```bash
cat > /tmp/web23-server.xml <<'EOF'
<Server>
  <Service name="Catalina">
    <Engine name="Catalina" defaultHost="localhost">
      <Realm className="org.apache.catalina.realm.JNDIRealm"
             connectionURL="ldap://ldap.example.local:389"
             userBase="ou=users,dc=example,dc=local"
             userSearch="(uid={0})"
             digest="SSHA" />
    </Engine>
  </Service>
</Server>
EOF
```

```bash
grep 'digest=' /tmp/web23-server.xml
```

취약 상태 기대 결과:

```text
digest="SSHA" />
```

### 8-3. 조치 적용

```bash
sed -i 's/digest="SSHA"/digest="SHA-256"/' /tmp/web23-server.xml
```

```bash
grep 'digest=' /tmp/web23-server.xml
```

조치 후 기대 결과:

```text
digest="SHA-256" />
```

### 8-4. 조치 후 검증

```bash
grep -E 'digest="(MD5|SHA|SSHA|SHA-1|SHA1)"' /tmp/web23-server.xml
```

기대 결과:

```text
출력 없음
```

```bash
grep -E 'digest="SHA-(256|384|512)"' /tmp/web23-server.xml
```

기대 결과:

```text
digest="SHA-256" />
```

### 8-5. 실습 파일 정리

```bash
rm -f /tmp/web23-server.xml
```

정리 확인:

```bash
ls -l /tmp/web23-server.xml 2>/dev/null
```

기대 결과:

```text
출력 없음
```

## 9. 증거 정리

### 9-1. 진단 파일 불일치 증거

```text
진단 파일 WEB-23: HTTP 메서드 제한
PDF WEB-23: LDAP 알고리즘 적절하게 구성
```

따라서 진단 파일의 WEB-23 결과는 PDF WEB-23 판단 근거로 직접 사용하지 않는다.

### 9-2. 현재 환경 적용성 확인 증거

Tomcat 서비스 확인:

```bash
systemctl list-units --type=service | grep -i tomcat
```

Tomcat 설정 파일 확인:

```bash
sudo find /etc /opt /usr/local -path '*tomcat*' -name 'server.xml' 2>/dev/null
```

LDAP 설정 확인:

```bash
sudo grep -RniE 'ldap|JNDIRealm|UserDatabaseRealm|digest=' /etc/tomcat* /opt/tomcat/conf 2>/dev/null
```

CARE PHP LDAP 사용 여부 확인:

```bash
grep -RniE 'ldap_connect|ldap_bind|ldap_search|ldap_set_option|LDAP|ldap_' /var/www/care 2>/dev/null
```

Tomcat과 LDAP 관련 출력이 없다면 현재 Apache/PHP/CARE 환경에서는 PDF WEB-23의 직접 점검 대상이 없는 것으로 기록한다.

### 9-3. 취약 재현 증거

실습용 취약 설정:

```xml
<Realm className="org.apache.catalina.realm.JNDIRealm"
       connectionURL="ldap://ldap.example.local:389"
       userBase="ou=users,dc=example,dc=local"
       userSearch="(uid={0})"
       digest="SSHA" />
```

확인 명령:

```bash
grep 'digest=' /tmp/web23-server.xml
```

취약 상태 기대 결과:

```text
digest="SSHA" />
```

### 9-4. 조치 후 증거

조치 후 설정:

```xml
<Realm className="org.apache.catalina.realm.JNDIRealm"
       connectionURL="ldap://ldap.example.local:389"
       userBase="ou=users,dc=example,dc=local"
       userSearch="(uid={0})"
       digest="SHA-256" />
```

확인 명령:

```bash
grep -E 'digest="SHA-(256|384|512)"' /tmp/web23-server.xml
```

조치 후 기대 결과:

```text
digest="SHA-256" />
```

## 10. 판단

|항목|판단|
|---|---|
|자동 진단|수동 항목으로 기록되어 있으나 내용 불일치|
|진단 파일 내용|WEB-23이 HTTP 메서드 제한으로 표시됨|
|PDF 기준 항목|LDAP 알고리즘 적절하게 구성|
|직접 점검 대상|Tomcat LDAP 인증 설정의 `digest=` 값|
|취약 조건|LDAP 인증에 취약하거나 권고 미만의 다이제스트 알고리즘 사용|
|양호 조건|LDAP 인증 시 `SHA-256` 이상 알고리즘 사용|
|현재 Apache/PHP/CARE 적용성|Tomcat/LDAP 미사용이면 직접 적용 대상 없음|
|실습 처리|`/tmp/web23-server.xml` 실습 파일로 취약 설정과 조치 설정 비교|

현재 WEB-23은 진단 파일과 PDF 항목명이 일치하지 않는다. 진단 파일의 WEB-23은 HTTP 메서드 제한으로 되어 있지만, PDF p.342의 WEB-23은 LDAP 알고리즘 적절하게 구성 항목이다.

PDF 기준으로는 Tomcat LDAP 인증 설정의 `digest=` 값을 확인해야 한다. 현재 CARE 서버가 Apache/PHP/MySQL 기반이고 Tomcat LDAP 인증을 사용하지 않는다면, WEB-23은 현재 환경에 직접 대응하는 점검 대상이 없는 항목으로 볼 수 있다.

다만 실습 이해를 위해 `/tmp/web23-server.xml`에 `digest="SSHA"` 설정을 만들어 취약 상태를 재현하고, 이를 `digest="SHA-256"`으로 변경하여 조치 기준을 확인한다.

실제 Tomcat LDAP 설정이 존재하는 환경에서는 `digest="SHA-256"`, `SHA-384`, `SHA-512` 등 SHA-256 이상의 알고리즘이 사용되면 WEB-23은 **양호**로 판단한다. 반대로 `MD5`, `SHA`, `SHA-1`, `SSHA` 등 권고 기준 미만 또는 취약한 알고리즘이 사용되면 **취약**으로 판단한다.