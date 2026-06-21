---

type: lab  
topic: web-service-security  
source: 주요정보통신기반시설 기술적 취약점 분석·평가 방법 상세가이드  
source_pages:

- 347
    
- 348
    
- 349  
status: draft  
created: 2026-06-18  
tags:
    
- 🏷️과목/웹서비스보안
    
- 🏷️주제/WEB-25
    
- 🏷️주제/Security-Patch
    
- 🏷️주제/Patch-Management
    
- 🏷️주제/Apache
    
- 🏷️상태/draft
    

---
# WEB-25 주기적 보안 패치 및 벤더 권고사항 적용

## 1. PDF 기준

PDF p.347-349의 WEB-25는 웹 서비스 구성요소에 **최신 보안 패치가 적용되어 있는지**, 그리고 **주기적인 패치 관리 정책이 수립되어 있는지** 점검하는 항목이다.

점검 목적은 다음과 같다.

```text
주기적인 최신 보안 패치를 통해
웹 서버의 보안성과 시스템 안정성을 확보한다.
```

패치가 적용되지 않은 웹 서버는 이미 공개된 취약점에 노출될 수 있다.  
공격자는 Apache, Tomcat, Nginx, IIS, JEUS, WebtoB 등 웹 서버 제품의 버전 정보를 확인한 뒤, 해당 버전에 알려진 취약점과 공격 코드를 찾을 수 있다.

PDF의 판단 기준은 다음과 같다.

|판단|기준|
|---|---|
|양호|최신 보안 패치가 적용되어 있고, 패치 적용 정책을 수립하여 주기적으로 패치를 관리하는 경우|
|취약|최신 보안 패치가 적용되어 있지 않거나, 패치 적용 정책과 주기적 패치 관리가 없는 경우|

PDF의 점검 대상은 다음 제품군이다.

|대상|
|---|
|Apache|
|Tomcat|
|Nginx|
|IIS|
|JEUS|
|WebtoB|

현재 CARE 서버는 Apache/PHP 기반이므로, 이 노트에서는 Apache, PHP, OpenSSL, OS 패키지 관점으로 해석한다.

주요 확인 대상은 다음과 같다.

|확인 대상|의미|
|---|---|
|Apache 버전|웹 서버 본체 보안 패치 상태|
|Apache 패키지 상태|배포판 저장소 기준 최신 패치 적용 여부|
|OpenSSL 버전|TLS 라이브러리 보안 패치 상태|
|PHP 버전|CARE 애플리케이션 실행 환경 보안 패치 상태|
|OS 보안 업데이트|Ubuntu/Debian 계열 보안 패치 상태|
|패치 정책|정기 점검, 테스트, 백업, 적용, 재점검 절차 존재 여부|

중요한 점은 “무조건 upstream 최신 버전”만 양호 기준으로 보지 않는다는 것이다.  
PDF 참고문에도 운영상 최신 버전 적용이 어려운 경우, **최신이 아니더라도 알려진 취약점이 존재하지 않는 버전**을 허용할 수 있다고 되어 있다.

따라서 판단은 다음처럼 해야 한다.

```text
1. 현재 설치 버전 확인
2. OS 패키지 저장소 기준 보안 업데이트 여부 확인
3. 벤더 권고사항 또는 보안 공지 확인
4. 운영 영향도 테스트 여부 확인
5. 패치 적용 정책 존재 여부 확인
```

## 2. 최초 진단 결과

`AWS WEB 약점 진단 결과.md`의 WEB-25 항목은 PDF의 WEB-25와 내용이 일치하지 않는다.

진단 파일의 WEB-25는 다음 항목으로 되어 있다.

```text
WEB-25 | X-XSS-Protection 헤더 | Header always set X-XSS-Protection "1; mode=block" 설정 여부
```

하지만 PDF p.347-349의 WEB-25는 **X-XSS-Protection 헤더가 아니라 주기적 보안 패치 및 벤더 권고사항 적용** 항목이다.

따라서 이 노트에서는 다음처럼 처리한다.

|구분|내용|
|---|---|
|PDF 기준 WEB-25|주기적 보안 패치 및 벤더 권고사항 적용|
|진단 파일 WEB-25|X-XSS-Protection 헤더|
|일치 여부|불일치|
|자동 진단 결과 활용|PDF WEB-25의 직접 근거로 사용 불가|
|이 노트의 판단 방식|Apache/OS/PHP 패치 상태와 패치 정책을 수동 확인|

PDF 기준 WEB-25는 자동 진단만으로 확정하기 어렵다.  
실제 판단에는 다음 정보가 필요하다.

```text
1. 설치된 Apache 버전
2. 설치된 Apache 패키지의 후보 버전
3. 보안 업데이트 대기 여부
4. PHP, OpenSSL 등 관련 패키지 업데이트 여부
5. 패치 적용 정책 또는 정기 점검 기록
```

## 3. 현재 서버 상태 해석

WEB-25는 서버 설정 한 줄로 끝나는 항목이 아니다.  
패치 상태와 운영 절차를 함께 확인하는 관리 항목이다.

Apache 환경에서 단순히 `apache2 -v`만 보는 것은 부족하다.

예를 들어 다음처럼 Apache 버전만 확인할 수 있다.

```bash
apache2 -v
```

하지만 이 결과만으로 최신 보안 패치 적용 여부를 확정할 수 없다.  
Ubuntu/Debian 계열에서는 배포판이 upstream 버전을 그대로 올리지 않고, 기존 버전에 보안 패치를 backport하는 경우가 있다.

따라서 확인은 다음 기준으로 나누어야 한다.

|확인 항목|의미|
|---|---|
|`apache2 -v`|현재 실행 중인 Apache 버전|
|`dpkg -l apache2`|설치된 패키지 버전|
|`apt-cache policy apache2`|설치 버전과 후보 버전 비교|
|`apt list --upgradable`|업데이트 대기 패키지 확인|
|`unattended-upgrades`|자동 보안 업데이트 설정 여부|
|`/var/log/apt/history.log`|최근 패치 적용 기록|
|벤더 보안 공지|알려진 취약점 영향 여부 확인|

판단은 다음처럼 한다.

|상태|판단|
|---|---|
|보안 업데이트 대기 없음, 패치 정책 있음|양호|
|Apache/PHP/OpenSSL 보안 업데이트 대기 중|취약 또는 조치 필요|
|패치 적용 기록 없음|확인 필요|
|패치 정책 없음|취약 또는 관리 미흡|
|최신 버전은 아니지만 배포판 보안 패치가 적용됨|양호 가능|
|EOL 버전 사용|취약 가능성 높음|

현재 CARE 서버에서는 Apache만이 아니라 PHP와 OpenSSL도 함께 확인해야 한다.

|구성요소|이유|
|---|---|
|Apache|웹 요청 처리|
|PHP|CARE 애플리케이션 실행|
|OpenSSL|HTTPS/TLS 통신|
|OS 패키지|웹 서버와 라이브러리의 보안 패치 기반|

WEB-25는 WEB-16, WEB-20, WEB-26과 연결된다.

|연결 항목|연결 이유|
|---|---|
|WEB-16|서버 버전 노출 시 미패치 취약점 탐색 위험 증가|
|WEB-20|SSL/TLS 라이브러리 취약점은 HTTPS 보안에 직접 영향|
|WEB-26|로그는 패치 적용 전후 장애와 공격 시도 추적에 필요|

## 4. 실습 전 확인

### 4-1. 실습용 변수 지정

```bash
PATCH_NOTE=/tmp/web25-patch-check.txt
```

### 4-2. Apache 버전 확인

```bash
apache2 -v
```

또는:

```bash
apachectl -v
```

결과 예시는 다음과 같다.

```text
Server version: Apache/2.4.x (Ubuntu)
```

### 4-3. Apache 패키지 버전 확인

```bash
dpkg -l apache2 apache2-bin apache2-data apache2-utils 2>/dev/null
```

확인할 것은 설치 버전이다.

```text
ii  apache2       ...
ii  apache2-bin   ...
ii  apache2-data  ...
ii  apache2-utils ...
```

### 4-4. Apache 후보 버전 확인

```bash
apt-cache policy apache2 apache2-bin apache2-data apache2-utils
```

확인할 항목은 다음이다.

|항목|의미|
|---|---|
|Installed|현재 설치된 버전|
|Candidate|현재 저장소 기준 설치 가능한 후보 버전|

`Installed`와 `Candidate`가 다르면 업데이트 대기 가능성이 있다.

### 4-5. 전체 업데이트 대기 패키지 확인

```bash
sudo apt update
```

```bash
apt list --upgradable 2>/dev/null
```

웹 서비스 관련 패키지만 필터링한다.

```bash
apt list --upgradable 2>/dev/null | grep -Ei 'apache2|openssl|libssl|php|curl|nghttp2|expat|apr|krb5|zlib'
```

출력이 있으면 웹 서비스 관련 보안 업데이트 대기 가능성이 있다.

출력 예시:

```text
apache2/jammy-updates ...
openssl/jammy-updates ...
php8.1/jammy-updates ...
```

### 4-6. 보안 업데이트 대기 확인

Ubuntu 계열에서는 다음 명령으로 보안 업데이트 후보를 확인할 수 있다.

```bash
/usr/lib/update-notifier/apt-check 2>&1
```

출력 예시는 다음과 같다.

```text
3;1
```

의미는 다음과 같이 해석한다.

```text
전체 업데이트 3개
보안 업데이트 1개
```

이 명령이 없는 환경이면 다음 로그와 `apt list --upgradable`을 함께 본다.

```bash
apt list --upgradable 2>/dev/null
```

### 4-7. 최근 패치 적용 기록 확인

```bash
sudo grep -E 'Start-Date|Commandline|Install:|Upgrade:|End-Date' /var/log/apt/history.log | tail -n 80
```

압축된 과거 로그까지 확인하려면 다음을 사용한다.

```bash
zgrep -hE 'Start-Date|Commandline|Install:|Upgrade:|End-Date' /var/log/apt/history.log.*.gz 2>/dev/null | tail -n 80
```

### 4-8. 자동 보안 업데이트 설정 확인

```bash
dpkg -l unattended-upgrades 2>/dev/null
```

```bash
grep -R "Unattended-Upgrade::Allowed-Origins\|Unattended-Upgrade::Package-Blacklist" \
/etc/apt/apt.conf.d/ 2>/dev/null
```

자동 보안 업데이트가 켜져 있는지 확인한다.

```bash
grep -R "APT::Periodic::Unattended-Upgrade\|APT::Periodic::Update-Package-Lists" \
/etc/apt/apt.conf.d/ 2>/dev/null
```

양호 예시는 다음과 같다.

```text
APT::Periodic::Update-Package-Lists "1";
APT::Periodic::Unattended-Upgrade "1";
```

### 4-9. 현재 확인 결과 기록

```bash
{
  echo "## WEB-25 patch check"
  date
  echo
  echo "### apache version"
  apache2 -v 2>/dev/null || true
  echo
  echo "### apache packages"
  dpkg -l apache2 apache2-bin apache2-data apache2-utils 2>/dev/null || true
  echo
  echo "### candidate versions"
  apt-cache policy apache2 apache2-bin apache2-data apache2-utils 2>/dev/null || true
  echo
  echo "### upgradable web-related packages"
  apt list --upgradable 2>/dev/null | grep -Ei 'apache2|openssl|libssl|php|curl|nghttp2|expat|apr|krb5|zlib' || true
  echo
  echo "### recent apt history"
  sudo grep -E 'Start-Date|Commandline|Install:|Upgrade:|End-Date' /var/log/apt/history.log | tail -n 80 || true
} | tee "$PATCH_NOTE"
```

기록 파일 확인:

```bash
cat "$PATCH_NOTE"
```

## 5. 취약 재현

WEB-25는 실제 서버를 의도적으로 구버전으로 낮추는 방식으로 재현하지 않는다.  
패키지 downgrade는 서비스 장애와 취약점 노출을 만들 수 있으므로 실습 서버에서도 권장하지 않는다.

대신 다음 두 방식으로 취약 상태를 확인한다.

|방식|설명|
|---|---|
|실제 업데이트 대기 확인|`apt list --upgradable`에 웹 서비스 관련 패키지가 남아 있는지 확인|
|실습용 취약 정책 파일|`/tmp`에 패치 정책 부재 또는 미적용 상태를 문서화해 판단 흐름만 재현|

### 5-1. 업데이트 대기 상태 확인

```bash
apt list --upgradable 2>/dev/null | grep -Ei 'apache2|openssl|libssl|php|curl|nghttp2|expat|apr|krb5|zlib'
```

취약 또는 조치 필요 상태 예시는 다음이다.

```text
apache2/...
openssl/...
php8.1/...
```

웹 서비스 관련 패키지가 업데이트 대기 중이면 패치 미적용 상태로 볼 수 있다.

### 5-2. 패치 정책 부재 상태 기록

패치 정책이 없다면 다음처럼 기록한다.

```bash
cat > /tmp/web25-policy-check.txt <<'EOF'
WEB-25 patch policy check

Patch schedule: not documented
Patch test procedure: not documented
Rollback procedure: not documented
Recent patch evidence: not confirmed
Vendor advisory review: not confirmed
EOF
```

확인:

```bash
cat /tmp/web25-policy-check.txt
```

취약 또는 관리 미흡 상태는 다음과 같다.

```text
Patch schedule: not documented
Patch test procedure: not documented
Rollback procedure: not documented
Recent patch evidence: not confirmed
Vendor advisory review: not confirmed
```

이 상태는 PDF 기준 “패치 적용 정책을 수립 및 주기적인 패치 관리를 하지 않는 경우”에 해당한다.

### 5-3. 취약 판단 예시

다음 둘 중 하나라도 해당하면 취약 또는 조치 필요로 본다.

```text
1. Apache/PHP/OpenSSL 등 웹 서비스 관련 패키지 업데이트가 대기 중이다.
2. 정기 패치 정책, 테스트 절차, 롤백 절차, 최근 적용 기록이 없다.
```

## 6. 조치 방법

조치 핵심은 보안 패치를 적용하고, 주기적인 패치 관리 정책을 남기는 것이다.

패치는 서비스 영향이 있으므로 무작정 실행하지 않는다.

```text
1. 현재 버전과 업데이트 후보 확인
2. 백업 또는 스냅샷 확보
3. 테스트 환경에서 업데이트 검증
4. 점검 시간에 운영 서버 적용
5. Apache/PHP 서비스 재시작 여부 확인
6. 적용 후 버전과 서비스 정상 동작 확인
7. 패치 기록 보관
```

### 6-1. 패치 전 백업 또는 스냅샷

AWS 환경이면 패치 전 다음 중 하나를 수행한다.

```text
EC2 AMI 생성
EBS 스냅샷 생성
배포 가능한 설정 파일 백업
```

서버 내부 설정 백업 예시는 다음이다.

```bash
sudo tar -czf /tmp/web25-apache-backup.tar.gz /etc/apache2
```

확인:

```bash
ls -lh /tmp/web25-apache-backup.tar.gz
```

### 6-2. 패키지 목록 갱신

```bash
sudo apt update
```

### 6-3. 웹 서비스 관련 패키지 업데이트 후보 확인

```bash
apt list --upgradable 2>/dev/null | grep -Ei 'apache2|openssl|libssl|php|curl|nghttp2|expat|apr|krb5|zlib'
```

### 6-4. Apache 관련 패키지만 우선 업데이트

```bash
sudo apt install --only-upgrade apache2 apache2-bin apache2-data apache2-utils
```

### 6-5. TLS 관련 패키지 업데이트

OpenSSL 또는 libssl 업데이트가 있는 경우 적용한다.

```bash
sudo apt install --only-upgrade openssl libssl3
```

배포판에 따라 `libssl3` 대신 `libssl1.1` 또는 다른 패키지명이 사용될 수 있다.  
먼저 현재 설치 패키지를 확인한다.

```bash
dpkg -l | grep -Ei '^ii\s+(openssl|libssl)'
```

### 6-6. PHP 관련 패키지 업데이트

PHP 패키지 업데이트가 있는 경우 적용한다.

```bash
dpkg -l | grep -Ei '^ii\s+php|^ii\s+libapache2-mod-php'
```

설치된 PHP 패키지를 기준으로 업데이트한다.

```bash
sudo apt install --only-upgrade php libapache2-mod-php
```

버전별 패키지라면 실제 설치된 버전에 맞춘다.

```bash
sudo apt install --only-upgrade php8.1 php8.1-cli php8.1-common libapache2-mod-php8.1
```

### 6-7. 전체 보안 업데이트 적용

운영 정책상 가능한 경우에는 보안 업데이트 전체를 적용한다.

```bash
sudo apt upgrade
```

무인 자동화보다는 테스트와 변경 기록을 남기는 방식이 적절하다.

### 6-8. Apache 설정 문법 검사

```bash
sudo apachectl configtest
```

기대 결과:

```text
Syntax OK
```

### 6-9. Apache restart

패키지 업데이트 후 Apache가 자동 재시작되지 않았거나 모듈이 갱신되었다면 재시작한다.

```bash
sudo systemctl restart apache2
```

### 6-10. 패치 정책 파일 작성

실습용으로 패치 정책 초안을 만든다.

```bash
cat > /tmp/web25-patch-policy.txt <<'EOF'
WEB-25 patch management policy

1. Patch check cycle
- Check web service security updates at least monthly.
- Check urgent vendor security advisories when announced.

2. Scope
- Apache
- PHP
- OpenSSL/libssl
- OS security packages
- Web application dependencies

3. Pre-check
- Confirm current version.
- Confirm available candidate version.
- Review changelog and security advisory.
- Create backup, snapshot, or rollback point.

4. Test
- Apply in test environment first when possible.
- Check Apache config with apachectl configtest.
- Confirm CARE login, upload, download, and main workflow.

5. Apply
- Apply during agreed maintenance window.
- Record command, package version, operator, and time.

6. Post-check
- Confirm apache2 status.
- Confirm HTTP/HTTPS response.
- Confirm logs for errors.
- Confirm no pending critical security update.

7. Rollback
- Restore package version, config backup, AMI, or EBS snapshot if service impact occurs.
EOF
```

확인:

```bash
cat /tmp/web25-patch-policy.txt
```

## 7. 조치 후 확인

### 7-1. Apache 버전 재확인

```bash
apache2 -v
```

### 7-2. Apache 패키지 상태 확인

```bash
dpkg -l apache2 apache2-bin apache2-data apache2-utils 2>/dev/null
```

### 7-3. 후보 버전과 설치 버전 비교

```bash
apt-cache policy apache2 apache2-bin apache2-data apache2-utils
```

`Installed`와 `Candidate`가 같으면 저장소 기준 최신 상태다.

```text
Installed: x.x.x
Candidate: x.x.x
```

### 7-4. 웹 서비스 관련 업데이트 대기 확인

```bash
apt list --upgradable 2>/dev/null | grep -Ei 'apache2|openssl|libssl|php|curl|nghttp2|expat|apr|krb5|zlib'
```

조치 후 기대 결과:

```text
출력 없음
```

### 7-5. 보안 업데이트 대기 확인

```bash
/usr/lib/update-notifier/apt-check 2>&1
```

기대 결과 예시:

```text
0;0
```

의미는 다음과 같다.

```text
전체 업데이트 0개
보안 업데이트 0개
```

환경에 따라 일반 업데이트가 남을 수 있다.  
WEB-25 판단에서는 웹 서비스 관련 보안 업데이트가 남아 있는지 우선 확인한다.

### 7-6. 최근 패치 기록 확인

```bash
sudo grep -E 'Start-Date|Commandline|Install:|Upgrade:|End-Date' /var/log/apt/history.log | tail -n 80
```

업데이트 명령과 패키지가 기록되어 있어야 한다.

```text
Commandline: apt install --only-upgrade apache2 ...
Upgrade: apache2 ...
```

### 7-7. Apache 서비스 상태 확인

```bash
systemctl status apache2 --no-pager
```

기대 결과:

```text
Active: active (running)
```

### 7-8. CARE 서비스 정상 응답 확인

```bash
curl -i http://172.168.10.10/
```

기대 결과:

```text
HTTP/1.1 200 OK
```

또는:

```text
HTTP/1.1 302 Found
```

HTTPS가 구성되어 있다면 같이 확인한다.

```bash
curl -k -I https://172.168.10.10/
```

기대 결과:

```text
HTTP/1.1 200 OK
```

또는:

```text
HTTP/1.1 302 Found
```

### 7-9. 패치 정책 존재 확인

```bash
cat /tmp/web25-patch-policy.txt
```

운영 노트로 남길 경우에는 `/tmp`가 아니라 프로젝트 문서 또는 운영 문서 경로에 보관한다.

예시:

```text
20_팀 프로젝트/26. 6. 8 팀플/웹 서비스 보안 모음/WEB-25 패치 관리 정책.md
```

## 8. 실행 순서 요약

### 8-1. 현재 상태 확인

```bash
PATCH_NOTE=/tmp/web25-patch-check.txt
```

```bash
apache2 -v
```

```bash
dpkg -l apache2 apache2-bin apache2-data apache2-utils 2>/dev/null
```

```bash
apt-cache policy apache2 apache2-bin apache2-data apache2-utils
```

```bash
sudo apt update
```

```bash
apt list --upgradable 2>/dev/null | grep -Ei 'apache2|openssl|libssl|php|curl|nghttp2|expat|apr|krb5|zlib'
```

```bash
/usr/lib/update-notifier/apt-check 2>&1
```

```bash
sudo grep -E 'Start-Date|Commandline|Install:|Upgrade:|End-Date' /var/log/apt/history.log | tail -n 80
```

### 8-2. 취약 상태 확인

웹 서비스 관련 업데이트가 남아 있으면 조치 필요로 기록한다.

```bash
apt list --upgradable 2>/dev/null | grep -Ei 'apache2|openssl|libssl|php|curl|nghttp2|expat|apr|krb5|zlib'
```

취약 또는 조치 필요 예시:

```text
apache2/...
openssl/...
php8.1/...
```

패치 정책 부재 상태도 확인한다.

```bash
cat > /tmp/web25-policy-check.txt <<'EOF'
WEB-25 patch policy check

Patch schedule: not documented
Patch test procedure: not documented
Rollback procedure: not documented
Recent patch evidence: not confirmed
Vendor advisory review: not confirmed
EOF
```

```bash
cat /tmp/web25-policy-check.txt
```

### 8-3. 조치 적용

```bash
sudo tar -czf /tmp/web25-apache-backup.tar.gz /etc/apache2
```

```bash
sudo apt update
```

```bash
sudo apt install --only-upgrade apache2 apache2-bin apache2-data apache2-utils
```

OpenSSL 업데이트가 있는 경우:

```bash
dpkg -l | grep -Ei '^ii\s+(openssl|libssl)'
```

```bash
sudo apt install --only-upgrade openssl libssl3
```

PHP 업데이트가 있는 경우:

```bash
dpkg -l | grep -Ei '^ii\s+php|^ii\s+libapache2-mod-php'
```

```bash
sudo apt install --only-upgrade php libapache2-mod-php
```

또는 실제 버전 패키지 기준:

```bash
sudo apt install --only-upgrade php8.1 php8.1-cli php8.1-common libapache2-mod-php8.1
```

```bash
sudo apachectl configtest
```

```bash
sudo systemctl restart apache2
```

### 8-4. 패치 정책 작성

```bash
cat > /tmp/web25-patch-policy.txt <<'EOF'
WEB-25 patch management policy

1. Patch check cycle
- Check web service security updates at least monthly.
- Check urgent vendor security advisories when announced.

2. Scope
- Apache
- PHP
- OpenSSL/libssl
- OS security packages
- Web application dependencies

3. Pre-check
- Confirm current version.
- Confirm available candidate version.
- Review changelog and security advisory.
- Create backup, snapshot, or rollback point.

4. Test
- Apply in test environment first when possible.
- Check Apache config with apachectl configtest.
- Confirm CARE login, upload, download, and main workflow.

5. Apply
- Apply during agreed maintenance window.
- Record command, package version, operator, and time.

6. Post-check
- Confirm apache2 status.
- Confirm HTTP/HTTPS response.
- Confirm logs for errors.
- Confirm no pending critical security update.

7. Rollback
- Restore package version, config backup, AMI, or EBS snapshot if service impact occurs.
EOF
```

### 8-5. 조치 후 확인

```bash
apache2 -v
```

```bash
apt-cache policy apache2 apache2-bin apache2-data apache2-utils
```

```bash
apt list --upgradable 2>/dev/null | grep -Ei 'apache2|openssl|libssl|php|curl|nghttp2|expat|apr|krb5|zlib'
```

기대 결과:

```text
출력 없음
```

```bash
/usr/lib/update-notifier/apt-check 2>&1
```

기대 결과 예시:

```text
0;0
```

```bash
sudo grep -E 'Start-Date|Commandline|Install:|Upgrade:|End-Date' /var/log/apt/history.log | tail -n 80
```

```bash
systemctl status apache2 --no-pager
```

기대 결과:

```text
Active: active (running)
```

```bash
curl -i http://172.168.10.10/
```

```bash
curl -k -I https://172.168.10.10/
```

## 9. 증거 정리

### 9-1. 진단 파일 불일치 증거

```text
진단 파일 WEB-25: X-XSS-Protection 헤더
PDF WEB-25: 주기적 보안 패치 및 벤더 권고사항 적용
```

따라서 진단 파일의 WEB-25 결과는 PDF WEB-25 판단 근거로 직접 사용하지 않는다.

### 9-2. 현재 버전 증거

Apache 버전:

```bash
apache2 -v
```

패키지 상태:

```bash
dpkg -l apache2 apache2-bin apache2-data apache2-utils 2>/dev/null
```

후보 버전 비교:

```bash
apt-cache policy apache2 apache2-bin apache2-data apache2-utils
```

### 9-3. 취약 또는 조치 필요 증거

웹 서비스 관련 업데이트 대기 확인:

```bash
apt list --upgradable 2>/dev/null | grep -Ei 'apache2|openssl|libssl|php|curl|nghttp2|expat|apr|krb5|zlib'
```

출력이 있으면 조치 필요로 기록한다.

패치 정책 부재 증거:

```text
Patch schedule: not documented
Patch test procedure: not documented
Rollback procedure: not documented
Recent patch evidence: not confirmed
Vendor advisory review: not confirmed
```

### 9-4. 조치 후 증거

업데이트 후 후보 버전 비교:

```bash
apt-cache policy apache2 apache2-bin apache2-data apache2-utils
```

조치 후 업데이트 대기 확인:

```bash
apt list --upgradable 2>/dev/null | grep -Ei 'apache2|openssl|libssl|php|curl|nghttp2|expat|apr|krb5|zlib'
```

기대 결과:

```text
출력 없음
```

최근 패치 기록:

```bash
sudo grep -E 'Start-Date|Commandline|Install:|Upgrade:|End-Date' /var/log/apt/history.log | tail -n 80
```

서비스 정상 확인:

```bash
systemctl status apache2 --no-pager
```

```bash
curl -i http://172.168.10.10/
```

## 10. 판단

|항목|판단|
|---|---|
|자동 진단|진단 파일 내용이 PDF WEB-25와 불일치|
|진단 파일 내용|WEB-25가 X-XSS-Protection 헤더로 표시됨|
|PDF 기준 항목|주기적 보안 패치 및 벤더 권고사항 적용|
|취약 조건|최신 보안 패치 미적용 또는 패치 정책 부재|
|양호 조건|웹 서비스 관련 보안 패치 적용, 주기적 패치 정책 수립, 적용 기록 존재|
|주요 확인 대상|Apache, PHP, OpenSSL/libssl, OS 보안 업데이트|
|조치 방향|패치 전 백업, 테스트, 패치 적용, Apache 재시작, 조치 후 서비스 확인|

현재 WEB-25는 진단 파일과 PDF 항목명이 일치하지 않는다. 진단 파일의 WEB-25는 X-XSS-Protection 헤더를 말하지만, PDF p.347-349의 WEB-25는 주기적 보안 패치 및 벤더 권고사항 적용 항목이다.

PDF 기준으로는 Apache, PHP, OpenSSL/libssl, OS 보안 패키지의 업데이트 대기 여부와 패치 정책 존재 여부를 직접 확인해야 한다.

웹 서비스 관련 보안 업데이트가 남아 있거나, 정기 패치 점검·테스트·롤백·적용 기록 정책이 없다면 WEB-25는 **취약 또는 조치 필요**로 판단한다.

조치 후 웹 서비스 관련 업데이트 대기 항목이 없고, 패치 적용 기록과 패치 관리 정책이 확인되며, Apache와 CARE 서비스가 정상 동작하면 WEB-25는 **양호**로 판단한다.