---

type: lab  
topic: web-service-security  
source: 주요정보통신기반시설 기술적 취약점 분석·평가 방법 상세가이드  
source_pages:

- 311
    
- 312  
status: draft  
created: 2026-06-18  
tags:
    
- 🏷️과목/웹서비스보안
    
- 🏷️주제/WEB-14
    
- 🏷️주제/File-Permission
    
- 🏷️주제/Apache
    
- 🏷️상태/draft
    

---

# WEB-14 웹 서비스 경로 내 파일의 접근 통제

## 1. PDF 기준

PDF p.311-312의 WEB-14는 웹 서비스 경로 안의 주요 파일과 디렉터리에 대해 **불필요한 접근 권한이 부여되어 있는지** 점검하는 항목이다.

웹 서비스 경로에는 웹 애플리케이션 소스 코드, 설정 파일, 업로드 디렉터리, 로그성 파일, 임시 파일 등이 존재할 수 있다. 이 파일들에 대해 일반 사용자에게 불필요한 읽기·쓰기·실행 권한이 부여되어 있으면 파일 변조, 삭제, 정보 노출 위험이 발생한다.

PDF의 점검 목적은 관리자를 제외한 일반 사용자의 불필요한 파일 접근 권한을 제거하여, 인가되지 않은 사용자가 허용되지 않은 파일에 접근하지 못하도록 하는 것이다.

PDF의 판단 기준은 다음과 같다.

|판단|기준|
|---|---|
|양호|주요 설정 파일 및 디렉터리에 불필요한 접근 권한이 부여되지 않은 경우|
|취약|주요 설정 파일 및 디렉터리에 불필요한 접근 권한이 부여된 경우|

PDF의 Apache 조치 예시는 다음과 같은 방향이다.

```bash
chown -R <Apache 계정>:<Apache 그룹> apache2.conf
chmod -R 750 apache2.conf
```

다만 Ubuntu Apache 환경에서 `/etc/apache2` 전체를 무조건 `www-data:www-data`로 바꾸는 것은 적절하지 않을 수 있다. 일반적으로 Apache 설정 파일은 `root`가 소유하고, 웹 서버 프로세스는 필요한 파일을 읽기만 하는 구조가 더 안전하다.

따라서 현재 CARE Apache 환경에서는 다음 원칙으로 해석한다.

|구분|권장 방향|
|---|---|
|Apache 설정 파일|`root` 소유 유지, 일반 사용자 쓰기 금지|
|웹 애플리케이션 소스|배포 계정 또는 `root` 소유, Apache가 필요한 범위만 읽기|
|일반 정적 파일|Apache가 읽을 수 있으나 일반 사용자가 수정할 수 없어야 함|
|업로드 디렉터리|필요한 위치에만 `www-data` 쓰기 허용|
|민감 파일|가능하면 DocumentRoot 밖에 두거나 웹 접근 차단|

즉 WEB-14의 핵심은 다음이다.

```text
웹 서비스 경로 안의 파일과 디렉터리에 대해
불필요한 일반 사용자 접근 권한, 특히 쓰기 권한을 제거한다.
```

## 2. 최초 진단 결과

`AWS WEB 약점 진단 결과.md` 기준 최초 진단 결과는 **양호**로 정리한다.

|항목|내용|
|---|---|
|진단 결과|양호|
|진단 근거|웹 서비스 경로 내 주요 파일과 디렉터리에 과도한 일반 사용자 쓰기 권한이 확인되지 않음|
|관련 설정|파일 소유자, 그룹, 권한 모드|
|최초 판단|불필요한 접근 권한이 확인되지 않았으므로 양호|

이 항목은 Apache 설정 한 줄만으로 판단하기 어렵다. 실제 파일 시스템 권한을 확인해야 한다.

대표적으로 확인할 권한은 다음과 같다.

```text
world-writable 파일 또는 디렉터리
group-writable 파일 또는 디렉터리
민감 파일의 일반 사용자 읽기 권한
웹 루트 내부 설정 파일의 웹 접근 가능 여부
```

최초 상태가 양호하더라도, PDF 내용을 실습하기 위해 의도적으로 실습용 파일에 과도한 권한을 부여한 뒤 탐지하고 복구한다.

## 3. 현재 서버 상태 해석

WEB-14는 웹 클라이언트의 URL 접근만 보는 항목이 아니라, 서버 파일 시스템의 권한 통제를 함께 본다.

특히 다음 권한이 중요하다.

|권한|의미|위험|
|---|---|---|
|`777`|모든 사용자 읽기·쓰기·실행 가능|누구나 파일 생성·수정·삭제 가능|
|`666`|모든 사용자 읽기·쓰기 가능|누구나 파일 내용 수정 가능|
|`755`|모든 사용자 읽기·실행 가능|공개 파일에는 가능하나 민감 디렉터리에는 부적절할 수 있음|
|`644`|모든 사용자 읽기 가능|소스·설정 파일이 민감하면 부적절할 수 있음|
|`750`|소유자 전체 권한, 그룹 읽기·실행, 기타 사용자 접근 불가|웹 서비스 디렉터리 제한에 적합|
|`640`|소유자 읽기·쓰기, 그룹 읽기, 기타 사용자 접근 불가|웹 서비스 파일 제한에 적합|

웹 서비스 경로에서 특히 위험한 것은 다음이다.

```text
other 쓰기 권한
world-writable 권한
민감 파일의 world-readable 권한
업로드 디렉터리 외부의 www-data 쓰기 권한
```

예를 들어 다음 권한은 위험하다.

```text
-rw-rw-rw- 1 root root config.php
drwxrwxrwx 2 root root upload/
```

일반 사용자도 파일을 수정할 수 있기 때문이다.

반대로 다음처럼 제한하면 일반 사용자의 불필요한 접근을 막을 수 있다.

```text
drwxr-x--- root www-data web14-perm-test/
-rw-r----- root www-data config.inc
```

이 항목은 WEB-07 불필요 파일 제거, WEB-11 웹 서비스 경로 설정, WEB-12 심볼릭 링크 제한과 연결된다.

|연결 항목|연결 이유|
|---|---|
|WEB-07|불필요 파일이 남아 있고 권한이 넓으면 노출 위험 증가|
|WEB-11|DocumentRoot가 넓게 잡히면 권한 관리 범위도 넓어짐|
|WEB-12|심볼릭 링크가 외부 파일을 가리키면 권한 우회 위험 증가|
|WEB-17|가상 디렉터리가 추가 경로를 노출할 수 있음|

## 4. 실습 전 확인

실습을 시작하기 전에 현재 Apache 환경과 웹 루트를 확인한다.

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
TEST_DIR="$APP_ROOT/web14-perm-test"
TEST_FILE="$TEST_DIR/config.inc"
```

현재 서버의 DocumentRoot가 다르면 `APP_ROOT` 값을 실제 경로로 바꾼다.

### 4-3. 현재 웹 루트 권한 확인

```bash
stat -c '%A %U:%G %n' "$APP_ROOT"
```

웹 루트 하위 주요 파일과 디렉터리 권한을 확인한다.

```bash
sudo find "$APP_ROOT" -maxdepth 2 -printf '%M %u:%g %p\n' | head -50
```

### 4-4. world-writable 파일 및 디렉터리 확인

```bash
sudo find "$APP_ROOT" -xdev \( -type f -o -type d \) -perm -0002 -printf '%M %u:%g %p\n'
```

양호 상태라면 출력이 없어야 한다.

```text
출력 없음
```

### 4-5. group-writable 파일 및 디렉터리 확인

```bash
sudo find "$APP_ROOT" -xdev \( -type f -o -type d \) -perm -0020 -printf '%M %u:%g %p\n'
```

이 결과는 무조건 취약은 아니다. 업로드 디렉터리처럼 의도적으로 웹 서버 그룹 쓰기 권한이 필요한 위치가 있을 수 있다.

다만 소스 파일, 설정 파일, 일반 정적 파일에 group-writable 권한이 있으면 별도 검토가 필요하다.

## 5. 취약 재현

이 항목은 최초 진단 결과가 양호이므로, PDF 내용을 실습하기 위해 의도적으로 취약 상태를 재현한다.

> 주의: 이 절차는 격리된 실습 서버에서만 수행한다.  
> 실제 운영 파일의 권한을 777 또는 666으로 바꾸지 않는다.  
> 반드시 실습용 디렉터리와 파일만 대상으로 한다.

취약 재현의 핵심은 다음이다.

```text
웹 서비스 경로 안에 일반 사용자가 수정 가능한 파일과 디렉터리를 만들고,
일반 사용자 권한으로 파일 수정이 가능한지 확인한다.
```

### 5-1. 실습용 디렉터리 생성

```bash
sudo mkdir -p "$TEST_DIR"
```

### 5-2. 실습용 파일 생성

```bash
echo "WEB-14 permission test original" | sudo tee "$TEST_FILE"
```

### 5-3. 취약 권한 부여

디렉터리를 모든 사용자가 접근·쓰기 가능한 상태로 만든다.

```bash
sudo chmod 777 "$TEST_DIR"
```

파일도 모든 사용자가 읽고 쓸 수 있게 만든다.

```bash
sudo chmod 666 "$TEST_FILE"
```

권한을 확인한다.

```bash
stat -c '%A %U:%G %n' "$TEST_DIR" "$TEST_FILE"
```

취약 상태 기대 결과는 다음과 유사하다.

```text
drwxrwxrwx root:root /var/www/care/web14-perm-test
-rw-rw-rw- root:root /var/www/care/web14-perm-test/config.inc
```

### 5-4. world-writable 탐지 확인

```bash
sudo find "$APP_ROOT" -xdev \( -type f -o -type d \) -perm -0002 -printf '%M %u:%g %p\n'
```

취약 재현 상태에서는 다음과 같은 결과가 나와야 한다.

```text
drwxrwxrwx root:root /var/www/care/web14-perm-test
-rw-rw-rw- root:root /var/www/care/web14-perm-test/config.inc
```

### 5-5. 일반 사용자 권한으로 수정 가능 여부 확인

`nobody` 계정으로 실습 파일에 내용을 추가해본다.

```bash
sudo -u nobody sh -c "echo 'modified by nobody' >> '$TEST_FILE'"
```

파일 내용을 확인한다.

```bash
cat "$TEST_FILE"
```

취약 상태 기대 결과는 다음과 같다.

```text
WEB-14 permission test original
modified by nobody
```

이 결과는 관리자가 아닌 일반 사용자 권한으로 웹 서비스 경로 내 파일을 수정할 수 있음을 의미한다.

### 5-6. 웹 접근 확인

파일이 웹 루트 안에 있으므로 HTTP로도 접근 가능하다.

```bash
curl -i "$SERVER/web14-perm-test/config.inc"
```

기대 결과는 다음과 유사하다.

```text
HTTP/1.1 200 OK

WEB-14 permission test original
modified by nobody
```

이 HTTP 결과 자체보다 더 중요한 것은, 서버 내부 일반 사용자가 해당 파일을 수정할 수 있었다는 점이다.  
WEB-14의 핵심은 파일 시스템 권한 통제다.

## 6. 조치 방법

조치 핵심은 웹 서비스 경로 내 파일과 디렉터리에서 불필요한 일반 사용자 권한을 제거하는 것이다.

실습에서는 테스트 디렉터리의 소유자와 권한을 다음과 같이 정리한다.

|대상|조치|
|---|---|
|디렉터리|`root:www-data`, `750`|
|파일|`root:www-data`, `640`|
|기타 사용자|접근 권한 제거|

### 6-1. 소유자와 그룹 변경

```bash
sudo chown -R root:www-data "$TEST_DIR"
```

### 6-2. 디렉터리 권한 제한

```bash
sudo find "$TEST_DIR" -type d -exec chmod 750 {} \;
```

### 6-3. 파일 권한 제한

```bash
sudo find "$TEST_DIR" -type f -exec chmod 640 {} \;
```

### 6-4. 권한 확인

```bash
stat -c '%A %U:%G %n' "$TEST_DIR" "$TEST_FILE"
```

조치 후 기대 결과는 다음과 유사하다.

```text
drwxr-x--- root:www-data /var/www/care/web14-perm-test
-rw-r----- root:www-data /var/www/care/web14-perm-test/config.inc
```

### 6-5. Apache 설정 문법 검사

WEB-14는 파일 권한 항목이므로 Apache 설정을 바꾸지는 않는다.  
그래도 실습 후 웹 서비스 상태 확인을 위해 문법 검사를 수행한다.

```bash
sudo apachectl configtest
```

정상이라면 다음 결과가 나와야 한다.

```text
Syntax OK
```

### 6-6. Apache restart

파일 권한 변경만으로는 일반적으로 Apache restart가 필요하지 않다.  
다만 실습 공통 흐름에 맞춰 서비스 상태를 재확인한다.

```bash
sudo systemctl restart apache2
```

## 7. 조치 후 확인

조치 후에는 일반 사용자가 더 이상 파일을 수정할 수 없는지 확인한다.

### 7-1. world-writable 재탐지

```bash
sudo find "$APP_ROOT" -xdev \( -type f -o -type d \) -perm -0002 -printf '%M %u:%g %p\n'
```

기대 결과는 다음이다.

```text
출력 없음
```

### 7-2. 테스트 파일 권한 확인

```bash
stat -c '%A %U:%G %n' "$TEST_DIR" "$TEST_FILE"
```

기대 결과는 다음과 유사하다.

```text
drwxr-x--- root:www-data /var/www/care/web14-perm-test
-rw-r----- root:www-data /var/www/care/web14-perm-test/config.inc
```

### 7-3. 일반 사용자 수정 차단 확인

```bash
sudo -u nobody sh -c "echo 'modified again by nobody' >> '$TEST_FILE'"
```

정상 조치 상태라면 다음과 유사한 결과가 나와야 한다.

```text
sh: 1: cannot create /var/www/care/web14-perm-test/config.inc: Permission denied
```

파일 내용을 다시 확인한다.

```bash
cat "$TEST_FILE"
```

기대 결과는 기존 내용만 유지되는 것이다.

```text
WEB-14 permission test original
modified by nobody
```

`modified again by nobody`가 추가되면 조치가 실패한 것이다.

### 7-4. Apache 사용자 읽기 가능 여부 확인

웹 서버 프로세스 계정인 `www-data`가 파일을 읽을 수 있는지 확인한다.

```bash
sudo -u www-data cat "$TEST_FILE"
```

기대 결과는 다음이다.

```text
WEB-14 permission test original
modified by nobody
```

이 결과는 웹 서버가 필요한 파일을 읽을 수는 있지만, 일반 사용자는 수정할 수 없다는 뜻이다.

### 7-5. HTTP 접근 확인

```bash
curl -i "$SERVER/web14-perm-test/config.inc"
```

서비스 정책상 이 파일을 공개해도 되는 파일이라면 `200 OK`가 나올 수 있다.

```text
HTTP/1.1 200 OK
```

다만 `config.inc` 같은 설정성 파일은 실제 운영 환경에서는 DocumentRoot 밖에 두거나, Apache 접근 차단을 적용하는 편이 안전하다.  
HTTP 공개 여부는 WEB-14의 OS 권한 통제와 별개로 WEB-07, WEB-11, WEB-17과 함께 검토한다.

## 8. 실행 순서 요약

실습 중에는 아래 순서대로 진행한다.

### 8-1. 현재 상태 확인

```bash
APP_ROOT=/var/www/care
SERVER=http://172.168.10.10
TEST_DIR="$APP_ROOT/web14-perm-test"
TEST_FILE="$TEST_DIR/config.inc"
```

```bash
apache2ctl -S
```

```bash
grep -R "DocumentRoot" /etc/apache2/sites-enabled/ /etc/apache2/sites-available/ 2>/dev/null
```

```bash
stat -c '%A %U:%G %n' "$APP_ROOT"
```

```bash
sudo find "$APP_ROOT" -maxdepth 2 -printf '%M %u:%g %p\n' | head -50
```

```bash
sudo find "$APP_ROOT" -xdev \( -type f -o -type d \) -perm -0002 -printf '%M %u:%g %p\n'
```

### 8-2. 취약 재현

```bash
sudo mkdir -p "$TEST_DIR"
```

```bash
echo "WEB-14 permission test original" | sudo tee "$TEST_FILE"
```

```bash
sudo chmod 777 "$TEST_DIR"
```

```bash
sudo chmod 666 "$TEST_FILE"
```

```bash
stat -c '%A %U:%G %n' "$TEST_DIR" "$TEST_FILE"
```

```bash
sudo find "$APP_ROOT" -xdev \( -type f -o -type d \) -perm -0002 -printf '%M %u:%g %p\n'
```

```bash
sudo -u nobody sh -c "echo 'modified by nobody' >> '$TEST_FILE'"
```

```bash
cat "$TEST_FILE"
```

```bash
curl -i "$SERVER/web14-perm-test/config.inc"
```

취약 상태 기대 결과:

```text
drwxrwxrwx root:root /var/www/care/web14-perm-test
-rw-rw-rw- root:root /var/www/care/web14-perm-test/config.inc
WEB-14 permission test original
modified by nobody
```

### 8-3. 조치 및 적용

```bash
sudo chown -R root:www-data "$TEST_DIR"
```

```bash
sudo find "$TEST_DIR" -type d -exec chmod 750 {} \;
```

```bash
sudo find "$TEST_DIR" -type f -exec chmod 640 {} \;
```

```bash
stat -c '%A %U:%G %n' "$TEST_DIR" "$TEST_FILE"
```

```bash
sudo apachectl configtest
```

```bash
sudo systemctl restart apache2
```

### 8-4. 조치 후 확인

```bash
sudo find "$APP_ROOT" -xdev \( -type f -o -type d \) -perm -0002 -printf '%M %u:%g %p\n'
```

기대 결과:

```text
출력 없음
```

```bash
stat -c '%A %U:%G %n' "$TEST_DIR" "$TEST_FILE"
```

기대 결과:

```text
drwxr-x--- root:www-data /var/www/care/web14-perm-test
-rw-r----- root:www-data /var/www/care/web14-perm-test/config.inc
```

```bash
sudo -u nobody sh -c "echo 'modified again by nobody' >> '$TEST_FILE'"
```

기대 결과:

```text
Permission denied
```

```bash
cat "$TEST_FILE"
```

기대 결과:

```text
WEB-14 permission test original
modified by nobody
```

```bash
sudo -u www-data cat "$TEST_FILE"
```

기대 결과:

```text
WEB-14 permission test original
modified by nobody
```

### 8-5. 실습 환경 제거

증거 확보 후에는 실습용 디렉터리를 제거한다.

```bash
sudo rm -rf "$TEST_DIR"
```

```bash
sudo apachectl configtest
```

```bash
sudo systemctl restart apache2
```

정리 확인:

```bash
ls -ld "$TEST_DIR" 2>/dev/null
```

기대 결과:

```text
출력 없음
```

## 9. 증거 정리

### 9-1. 최초 상태 증거

최초 진단 결과:

```text
WEB-14 · 웹 서비스 경로 내 파일의 접근 통제
주요 파일 및 디렉터리에 불필요한 접근 권한이 부여되지 않음
```

world-writable 탐지 명령어:

```bash
sudo find "$APP_ROOT" -xdev \( -type f -o -type d \) -perm -0002 -printf '%M %u:%g %p\n'
```

양호 상태 기대 결과:

```text
출력 없음
```

### 9-2. 취약 재현 증거

취약 권한 확인:

```bash
stat -c '%A %U:%G %n' "$TEST_DIR" "$TEST_FILE"
```

취약 상태 기대 결과:

```text
drwxrwxrwx root:root /var/www/care/web14-perm-test
-rw-rw-rw- root:root /var/www/care/web14-perm-test/config.inc
```

일반 사용자 수정 확인:

```bash
sudo -u nobody sh -c "echo 'modified by nobody' >> '$TEST_FILE'"
cat "$TEST_FILE"
```

기대 결과:

```text
WEB-14 permission test original
modified by nobody
```

### 9-3. 조치 후 증거

조치 후 권한 확인:

```bash
stat -c '%A %U:%G %n' "$TEST_DIR" "$TEST_FILE"
```

기대 결과:

```text
drwxr-x--- root:www-data /var/www/care/web14-perm-test
-rw-r----- root:www-data /var/www/care/web14-perm-test/config.inc
```

일반 사용자 수정 차단 확인:

```bash
sudo -u nobody sh -c "echo 'modified again by nobody' >> '$TEST_FILE'"
```

기대 결과:

```text
Permission denied
```

world-writable 재탐지:

```bash
sudo find "$APP_ROOT" -xdev \( -type f -o -type d \) -perm -0002 -printf '%M %u:%g %p\n'
```

기대 결과:

```text
출력 없음
```

## 10. 판단

|항목|판단|
|---|---|
|최초 진단|양호|
|진단 근거|주요 파일 및 디렉터리에 불필요한 일반 사용자 쓰기 권한이 확인되지 않음|
|실습 처리|실습용 파일과 디렉터리에 777/666 권한을 부여하여 취약 상태 재현 후 750/640으로 제한|
|조치 전 판단|일반 사용자 권한으로 웹 서비스 경로 내 파일 수정이 가능하면 취약|
|조치 후 판단|일반 사용자 수정이 차단되고 필요한 웹 서버 읽기만 허용되면 양호|
|증거 상태|최초 진단 결과 확보, 취약 재현 및 조치 후 권한 증거 필요|

현재 서버는 최초 진단 기준으로 주요 웹 서비스 파일과 디렉터리에 불필요한 접근 권한이 확인되지 않았으므로 WEB-14는 **양호**로 판단한다.

다만 PDF의 취약 조건을 실습하기 위해 `/var/www/care/web14-perm-test` 디렉터리를 만들고 `777`, `666` 권한을 부여하면, 일반 사용자 권한으로 파일을 수정할 수 있는 취약 상태를 재현할 수 있다.

조치는 해당 디렉터리와 파일의 소유권을 `root:www-data`로 정리하고, 디렉터리는 `750`, 파일은 `640`으로 제한하는 방식으로 수행한다.

조치 후 `nobody` 같은 일반 사용자로 파일 수정이 차단되고, world-writable 탐지 결과가 없으면 WEB-14는 조치 후 **양호**로 판단한다.