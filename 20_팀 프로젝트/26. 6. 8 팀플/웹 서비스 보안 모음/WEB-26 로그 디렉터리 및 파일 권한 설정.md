---

type: lab  
topic: web-service-security  
source: 주요정보통신기반시설 기술적 취약점 분석·평가 방법 상세가이드  
source_pages:

- 350
    
- 351
    
- 352  
status: draft  
created: 2026-06-18  
tags:
    
- 🏷️과목/웹서비스보안
    
- 🏷️주제/WEB-26
    
- 🏷️주제/Log-Permission
    
- 🏷️주제/Apache
    
- 🏷️상태/draft
    

---
# WEB-26 로그 디렉터리 및 파일 권한 설정

## 1. PDF 기준

PDF p.350-352의 WEB-26은 웹 서비스의 **로그 디렉터리와 로그 파일 권한이 적절하게 제한되어 있는지** 점검하는 항목이다.

웹 서버 로그에는 다음과 같은 정보가 포함될 수 있다.

```text
접속 IP
요청 URL
쿼리스트링
User-Agent
Referer
인증 실패 흔적
오류 메시지
내부 경로
애플리케이션 동작 흔적
공격 시도 흔적
```

로그 권한이 과도하게 열려 있으면 일반 사용자가 로그를 읽거나 조작할 수 있다.  
이 경우 정보 유출뿐 아니라 침해 사고 분석을 방해하는 로그 변조 위험도 생긴다.

PDF의 판단 기준은 다음과 같다.

|판단|기준|
|---|---|
|양호|로그 디렉터리 및 로그 파일에 일반 사용자의 접근 권한이 없는 경우|
|취약|로그 디렉터리 및 로그 파일에 일반 사용자의 접근 권한이 있는 경우|

Apache 기준 점검 방향은 다음이다.

```bash
ls -al /var/log/apache2
```

Apache 기준 조치 방향은 다음이다.

```bash
chmod o-rwx /var/log/apache2
chmod o-rwx /var/log/apache2/*
```

JEUS, WebtoB 예시에서는 로그 디렉터리 `750`, 로그 파일 `640`을 권장 예시로 제시한다.

현재 Apache/Ubuntu 환경에서는 다음 기준으로 해석한다.

|대상|권장 예시|
|---|---|
|로그 디렉터리|`750`|
|로그 파일|`640`|
|소유자|`root`|
|그룹|`adm` 또는 운영 정책상 로그 열람이 허용된 관리 그룹|
|일반 사용자 권한|없음|

핵심은 다음이다.

```text
others 권한에 r, w, x가 없어야 한다.
```

## 2. 최초 진단 결과

`AWS WEB 약점 진단 결과.md` 기준 WEB-26의 최초 진단 결과는 **양호**이다.

|항목|내용|
|---|---|
|진단 결과|양호|
|진단 근거|모든 로그 파일 `640`, 로그 디렉터리 `750` 확인|
|확인 대상|`/var/log/apache2`, `access.log`, `error.log`, `other_vhosts_access.log`, rotated log|
|최초 판단|일반 사용자 접근 권한이 없으므로 양호|

최초 진단 결과는 다음과 같다.

```text
WEB-26 · 로그 디렉터리 및 파일 권한 설정

모든 로그 파일 640, 디렉터리 750 으로 적절히 설정됨

access.log: 640
error.log: 640
other_vhosts_access.log: 640
error.log.1: 640
/var/log/apache2: 750
```

따라서 현재 최초 상태에서는 WEB-26을 **양호**로 판단한다.

## 3. 현재 서버 상태 해석

WEB-26은 Apache 설정 파일보다 운영체제의 파일 권한을 확인하는 항목이다.

Apache 로그 기본 경로는 보통 다음이다.

```text
/var/log/apache2
```

대표 로그 파일은 다음과 같다.

```text
access.log
error.log
other_vhosts_access.log
access.log.1
error.log.1
*.gz
```

권한 해석은 다음과 같다.

|권한|의미|판단|
|---|---|---|
|`750` 디렉터리|소유자 전체, 그룹 읽기/진입, others 접근 불가|양호|
|`640` 파일|소유자 읽기/쓰기, 그룹 읽기, others 접근 불가|양호|
|`755` 디렉터리|others가 디렉터리 목록/진입 가능|취약 가능|
|`644` 파일|others가 로그 파일 읽기 가능|취약|
|`666` 파일|others가 로그 파일 쓰기 가능|매우 취약|
|`777` 디렉터리|others가 파일 생성/삭제 가능|매우 취약|

로그 파일에서 특히 위험한 것은 `others` 권한이다.

```text
-rw-r--r-- 644 access.log
      ^^^
      others 읽기 가능
```

`644`는 일반 파일에서는 흔하지만, 웹 로그 파일에는 부적절하다.  
일반 사용자가 로그를 읽을 수 있기 때문이다.

양호한 예시는 다음이다.

```text
drwxr-x--- root adm /var/log/apache2
-rw-r----- root adm /var/log/apache2/access.log
-rw-r----- root adm /var/log/apache2/error.log
```

이 항목은 WEB-16, WEB-22, 침해 사고 분석과 연결된다.

|연결 항목|연결 이유|
|---|---|
|WEB-16|서버 정보 노출이 로그에도 남을 수 있음|
|WEB-22|에러 페이지와 에러 로그는 내부 정보 노출과 연결됨|
|침해 사고 분석|로그 무결성이 깨지면 공격 추적이 어려워짐|

## 4. 실습 전 확인

### 4-1. 실습용 변수 지정

```bash
LOG_DIR=/var/log/apache2
PERM_BEFORE=/tmp/web26-log-permissions.before
PERM_AFTER=/tmp/web26-log-permissions.after
```

### 4-2. Apache 로그 경로 확인

Apache 설정에서 실제 로그 경로를 확인한다.

```bash
grep -R "^[[:space:]]*ErrorLog\|^[[:space:]]*CustomLog" \
/etc/apache2/apache2.conf \
/etc/apache2/sites-enabled/ \
/etc/apache2/sites-available/ \
/etc/apache2/conf-enabled/ \
/etc/apache2/conf-available/ 2>/dev/null | grep -v '^\s*#'
```

기본 경로는 다음과 유사하다.

```text
ErrorLog ${APACHE_LOG_DIR}/error.log
CustomLog ${APACHE_LOG_DIR}/access.log combined
```

`APACHE_LOG_DIR` 값은 보통 `/var/log/apache2`다.

```bash
grep "^export APACHE_LOG_DIR" /etc/apache2/envvars
```

기대 결과:

```text
export APACHE_LOG_DIR=/var/log/apache2$SUFFIX
```

### 4-3. 현재 로그 디렉터리 권한 확인

```bash
stat -c '%A %a %U:%G %n' "$LOG_DIR"
```

양호 상태 기대 결과:

```text
drwxr-x--- 750 root:adm /var/log/apache2
```

### 4-4. 현재 로그 파일 권한 확인

```bash
sudo find "$LOG_DIR" -maxdepth 1 -type f -printf '%m %u:%g %p\n' | sort
```

양호 상태 기대 결과 예시:

```text
640 root:adm /var/log/apache2/access.log
640 root:adm /var/log/apache2/error.log
640 root:adm /var/log/apache2/other_vhosts_access.log
```

### 4-5. 현재 권한 백업 기록

실습 후 원복을 위해 현재 권한을 기록한다.

```bash
{
  echo "## WEB-26 permission snapshot"
  date
  echo
  echo "### log directory"
  stat -c '%A %a %U:%G %n' "$LOG_DIR"
  echo
  echo "### log files"
  sudo find "$LOG_DIR" -maxdepth 1 -type f -printf '%m %u:%g %p\n' | sort
} | tee "$PERM_BEFORE"
```

확인:

```bash
cat "$PERM_BEFORE"
```

### 4-6. 일반 사용자 접근 확인

`nobody` 사용자로 로그 디렉터리 접근을 시도한다.

```bash
sudo -u nobody ls "$LOG_DIR"
```

양호 상태 기대 결과:

```text
Permission denied
```

로그 파일 직접 읽기도 실패해야 한다.

```bash
sudo -u nobody head -n 3 "$LOG_DIR/access.log"
```

양호 상태 기대 결과:

```text
Permission denied
```

## 5. 취약 재현

이 항목은 최초 진단 결과가 양호이다.  
PDF 내용을 실습하기 위해 의도적으로 로그 디렉터리와 로그 파일의 others 권한을 열어 취약 상태를 재현한다.

> 주의: 이 절차는 격리된 실습 서버에서만 수행한다.  
> 로그에는 민감 정보가 포함될 수 있으므로 증거 확보 후 즉시 권한을 복구한다.  
> 운영 서버에서는 로그 파일을 world-readable로 만들지 않는다.

취약 재현의 핵심은 다음이다.

```text
일반 사용자 nobody가 /var/log/apache2 내부 파일을 읽을 수 있게 만든다.
```

### 5-1. 로그 디렉터리를 others 접근 가능하게 변경

```bash
sudo chmod 755 "$LOG_DIR"
```

### 5-2. 로그 파일을 others 읽기 가능하게 변경

```bash
sudo find "$LOG_DIR" -maxdepth 1 -type f -exec chmod o+r {} \;
```

파일 권한이 `644` 또는 이와 유사하게 바뀐다.

```bash
sudo find "$LOG_DIR" -maxdepth 1 -type f -printf '%m %u:%g %p\n' | sort
```

취약 상태 예시:

```text
644 root:adm /var/log/apache2/access.log
644 root:adm /var/log/apache2/error.log
```

### 5-3. 일반 사용자 로그 디렉터리 접근 확인

```bash
sudo -u nobody ls "$LOG_DIR"
```

취약 상태에서는 로그 파일 목록이 보일 수 있다.

```text
access.log
error.log
other_vhosts_access.log
```

### 5-4. 일반 사용자 로그 파일 읽기 확인

```bash
sudo -u nobody head -n 3 "$LOG_DIR/access.log"
```

취약 상태에서는 로그 내용이 출력될 수 있다.

```text
172.168.10.10 - - [date] "GET / HTTP/1.1" 200 ...
```

이 결과는 일반 사용자가 웹 로그를 읽을 수 있음을 의미하므로 PDF 기준 취약이다.

### 5-5. 취약 상태 권한 기록

```bash
stat -c '%A %a %U:%G %n' "$LOG_DIR"
```

```bash
sudo find "$LOG_DIR" -maxdepth 1 -type f -printf '%m %u:%g %p\n' | sort
```

취약 상태 예시:

```text
drwxr-xr-x 755 root:adm /var/log/apache2
644 root:adm /var/log/apache2/access.log
644 root:adm /var/log/apache2/error.log
```

## 6. 조치 방법

조치 핵심은 로그 디렉터리와 로그 파일에서 일반 사용자 권한을 제거하는 것이다.

### 6-1. 로그 디렉터리 권한 복구

```bash
sudo chmod 750 "$LOG_DIR"
```

### 6-2. 로그 파일 권한 복구

```bash
sudo find "$LOG_DIR" -maxdepth 1 -type f -exec chmod 640 {} \;
```

### 6-3. 소유자와 그룹 확인 및 복구

Ubuntu Apache 로그는 보통 `root:adm` 소유다.  
현재 서버에서도 `adm` 그룹을 사용한다면 다음처럼 정리한다.

```bash
getent group adm
```

`adm` 그룹이 있으면 다음 명령을 사용한다.

```bash
sudo chown root:adm "$LOG_DIR"
```

```bash
sudo find "$LOG_DIR" -maxdepth 1 -type f -exec chown root:adm {} \;
```

만약 운영 정책상 별도 로그 관리 그룹을 사용한다면 `adm` 대신 해당 그룹을 사용한다.

### 6-4. logrotate 생성 권한 확인

로그가 rotate된 뒤 다시 `644`로 생성되면 조치가 유지되지 않는다.  
Apache logrotate 설정을 확인한다.

```bash
grep -nE 'create|su|rotate|compress|missingok|notifempty' /etc/logrotate.d/apache2
```

양호한 예시는 다음과 같다.

```text
create 640 root adm
```

`create 644`처럼 되어 있으면 rotate 후 로그 파일이 다시 일반 사용자 읽기 가능 상태가 될 수 있다.

조치 예시:

```bash
sudo cp /etc/logrotate.d/apache2 /etc/logrotate.d/apache2.bak.WEB-26
```

```bash
sudo sed -i -E 's/create[[:space:]]+[0-9]+[[:space:]]+root[[:space:]]+adm/create 640 root adm/' /etc/logrotate.d/apache2
```

변경 확인:

```bash
grep -nE 'create' /etc/logrotate.d/apache2
```

### 6-5. Apache 재시작 여부

단순 로그 파일 권한 변경은 일반적으로 Apache 재시작이 필요 없다.

다만 logrotate 설정을 바꿨거나 로그 파일 생성 정책을 바꾼 경우에는 서비스 상태를 확인한다.

```bash
systemctl status apache2 --no-pager
```

필요 시에만 재시작한다.

```bash
sudo systemctl restart apache2
```

## 7. 조치 후 확인

### 7-1. 로그 디렉터리 권한 확인

```bash
stat -c '%A %a %U:%G %n' "$LOG_DIR"
```

기대 결과:

```text
drwxr-x--- 750 root:adm /var/log/apache2
```

### 7-2. 로그 파일 권한 확인

```bash
sudo find "$LOG_DIR" -maxdepth 1 -type f -printf '%m %u:%g %p\n' | sort
```

기대 결과:

```text
640 root:adm /var/log/apache2/access.log
640 root:adm /var/log/apache2/error.log
640 root:adm /var/log/apache2/other_vhosts_access.log
```

압축 로그나 rotate 로그도 확인한다.

```bash
sudo find "$LOG_DIR" -maxdepth 1 -type f \( -name '*.log*' -o -name '*.gz' \) -printf '%m %u:%g %p\n' | sort
```

### 7-3. 일반 사용자 디렉터리 접근 차단 확인

```bash
sudo -u nobody ls "$LOG_DIR"
```

조치 후 기대 결과:

```text
Permission denied
```

### 7-4. 일반 사용자 로그 파일 읽기 차단 확인

```bash
sudo -u nobody head -n 3 "$LOG_DIR/access.log"
```

조치 후 기대 결과:

```text
Permission denied
```

### 7-5. others 권한 일괄 확인

다음 명령은 others 권한이 남아 있는 로그 파일을 찾는다.

```bash
sudo find "$LOG_DIR" -maxdepth 1 -type f -perm /007 -printf '%m %u:%g %p\n'
```

조치 후 기대 결과:

```text
출력 없음
```

로그 디렉터리 자체도 확인한다.

```bash
find "$LOG_DIR" -maxdepth 0 -perm /007 -printf '%m %u:%g %p\n'
```

조치 후 기대 결과:

```text
출력 없음
```

### 7-6. logrotate 설정 확인

```bash
grep -nE 'create' /etc/logrotate.d/apache2
```

기대 결과:

```text
create 640 root adm
```

### 7-7. 조치 후 권한 기록

```bash
{
  echo "## WEB-26 permission after"
  date
  echo
  echo "### log directory"
  stat -c '%A %a %U:%G %n' "$LOG_DIR"
  echo
  echo "### log files"
  sudo find "$LOG_DIR" -maxdepth 1 -type f -printf '%m %u:%g %p\n' | sort
  echo
  echo "### files with others permission"
  sudo find "$LOG_DIR" -maxdepth 1 -type f -perm /007 -printf '%m %u:%g %p\n'
} | tee "$PERM_AFTER"
```

확인:

```bash
cat "$PERM_AFTER"
```

### 7-8. Apache 서비스 상태 확인

```bash
systemctl status apache2 --no-pager
```

기대 결과:

```text
Active: active (running)
```

### 7-9. CARE 서비스 정상 응답 확인

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

## 8. 실행 순서 요약

### 8-1. 현재 상태 확인

```bash
LOG_DIR=/var/log/apache2
PERM_BEFORE=/tmp/web26-log-permissions.before
PERM_AFTER=/tmp/web26-log-permissions.after
```

```bash
grep -R "^[[:space:]]*ErrorLog\|^[[:space:]]*CustomLog" \
/etc/apache2/apache2.conf \
/etc/apache2/sites-enabled/ \
/etc/apache2/sites-available/ \
/etc/apache2/conf-enabled/ \
/etc/apache2/conf-available/ 2>/dev/null | grep -v '^\s*#'
```

```bash
stat -c '%A %a %U:%G %n' "$LOG_DIR"
```

```bash
sudo find "$LOG_DIR" -maxdepth 1 -type f -printf '%m %u:%g %p\n' | sort
```

```bash
sudo -u nobody ls "$LOG_DIR"
```

```bash
sudo -u nobody head -n 3 "$LOG_DIR/access.log"
```

### 8-2. 취약 재현

```bash
sudo chmod 755 "$LOG_DIR"
```

```bash
sudo find "$LOG_DIR" -maxdepth 1 -type f -exec chmod o+r {} \;
```

```bash
stat -c '%A %a %U:%G %n' "$LOG_DIR"
```

```bash
sudo find "$LOG_DIR" -maxdepth 1 -type f -printf '%m %u:%g %p\n' | sort
```

```bash
sudo -u nobody ls "$LOG_DIR"
```

```bash
sudo -u nobody head -n 3 "$LOG_DIR/access.log"
```

취약 상태 기대 결과:

```text
nobody 사용자가 로그 디렉터리 목록을 볼 수 있음
nobody 사용자가 access.log 일부를 읽을 수 있음
```

### 8-3. 조치 적용

```bash
sudo chmod 750 "$LOG_DIR"
```

```bash
sudo find "$LOG_DIR" -maxdepth 1 -type f -exec chmod 640 {} \;
```

```bash
if getent group adm >/dev/null; then
  sudo chown root:adm "$LOG_DIR"
  sudo find "$LOG_DIR" -maxdepth 1 -type f -exec chown root:adm {} \;
fi
```

```bash
grep -nE 'create' /etc/logrotate.d/apache2
```

필요 시 logrotate 생성 권한도 조정한다.

```bash
sudo cp /etc/logrotate.d/apache2 /etc/logrotate.d/apache2.bak.WEB-26
```

```bash
sudo sed -i -E 's/create[[:space:]]+[0-9]+[[:space:]]+root[[:space:]]+adm/create 640 root adm/' /etc/logrotate.d/apache2
```

### 8-4. 조치 후 확인

```bash
stat -c '%A %a %U:%G %n' "$LOG_DIR"
```

기대 결과:

```text
drwxr-x--- 750 root:adm /var/log/apache2
```

```bash
sudo find "$LOG_DIR" -maxdepth 1 -type f -printf '%m %u:%g %p\n' | sort
```

기대 결과:

```text
640 root:adm /var/log/apache2/access.log
640 root:adm /var/log/apache2/error.log
640 root:adm /var/log/apache2/other_vhosts_access.log
```

```bash
sudo -u nobody ls "$LOG_DIR"
```

기대 결과:

```text
Permission denied
```

```bash
sudo -u nobody head -n 3 "$LOG_DIR/access.log"
```

기대 결과:

```text
Permission denied
```

```bash
sudo find "$LOG_DIR" -maxdepth 1 -type f -perm /007 -printf '%m %u:%g %p\n'
```

기대 결과:

```text
출력 없음
```

```bash
find "$LOG_DIR" -maxdepth 0 -perm /007 -printf '%m %u:%g %p\n'
```

기대 결과:

```text
출력 없음
```

```bash
systemctl status apache2 --no-pager
```

기대 결과:

```text
Active: active (running)
```

### 8-5. 실습 기록 파일 정리

증거 확보 후 임시 기록 파일이 필요 없으면 삭제한다.

```bash
rm -f "$PERM_BEFORE" "$PERM_AFTER"
```

logrotate 백업 파일도 증거 확보 후 필요 없으면 제거한다.

```bash
sudo rm -f /etc/logrotate.d/apache2.bak.WEB-26
```

단, 보고서 증거로 남길 계획이면 삭제하지 않는다.

## 9. 증거 정리

### 9-1. 최초 상태 증거

최초 진단 결과:

```text
WEB-26 · 로그 디렉터리 및 파일 권한 설정

모든 로그 파일 640, 디렉터리 750 으로 적절히 설정됨

access.log: 640
error.log: 640
other_vhosts_access.log: 640
error.log.1: 640
/var/log/apache2: 750
```

권한 확인 명령:

```bash
stat -c '%A %a %U:%G %n' /var/log/apache2
```

```bash
sudo find /var/log/apache2 -maxdepth 1 -type f -printf '%m %u:%g %p\n' | sort
```

일반 사용자 접근 확인:

```bash
sudo -u nobody ls /var/log/apache2
```

기대 결과:

```text
Permission denied
```

### 9-2. 취약 재현 증거

취약 권한 예시:

```text
drwxr-xr-x 755 root:adm /var/log/apache2
644 root:adm /var/log/apache2/access.log
644 root:adm /var/log/apache2/error.log
```

일반 사용자 로그 읽기 확인:

```bash
sudo -u nobody head -n 3 /var/log/apache2/access.log
```

취약 상태 기대 결과:

```text
로그 내용 일부 출력
```

이 결과는 일반 사용자가 로그 파일을 읽을 수 있음을 의미한다.

### 9-3. 조치 후 증거

조치 후 권한:

```text
drwxr-x--- 750 root:adm /var/log/apache2
640 root:adm /var/log/apache2/access.log
640 root:adm /var/log/apache2/error.log
640 root:adm /var/log/apache2/other_vhosts_access.log
```

others 권한 확인:

```bash
sudo find /var/log/apache2 -maxdepth 1 -type f -perm /007 -printf '%m %u:%g %p\n'
```

조치 후 기대 결과:

```text
출력 없음
```

일반 사용자 접근 차단:

```bash
sudo -u nobody ls /var/log/apache2
```

조치 후 기대 결과:

```text
Permission denied
```

```bash
sudo -u nobody head -n 3 /var/log/apache2/access.log
```

조치 후 기대 결과:

```text
Permission denied
```

## 10. 판단

|항목|판단|
|---|---|
|최초 진단|양호|
|진단 근거|로그 파일 `640`, 로그 디렉터리 `750` 확인|
|취약 조건|일반 사용자가 로그 디렉터리 또는 로그 파일에 접근 가능|
|양호 조건|로그 디렉터리 `750`, 로그 파일 `640`, others 권한 없음|
|주요 확인 대상|`/var/log/apache2`, `access.log`, `error.log`, rotated log|
|조치 방향|`chmod 750` 디렉터리, `chmod 640` 로그 파일, `root:adm` 소유권 유지|
|추가 확인|logrotate 설정에서 `create 640 root adm` 유지|

현재 서버는 최초 진단 기준으로 Apache 로그 디렉터리가 `750`, 로그 파일들이 `640`으로 설정되어 있으므로 WEB-26은 **양호**로 판단한다.

다만 실습에서는 `chmod 755 /var/log/apache2`, `chmod o+r /var/log/apache2/*` 형태로 일반 사용자에게 접근 권한을 부여하여 취약 상태를 재현할 수 있다. 이때 `nobody` 사용자가 로그 디렉터리 목록이나 `access.log` 내용을 읽을 수 있으면 취약 상태다.

조치 후 `/var/log/apache2`는 `750`, 로그 파일은 `640`, 소유권은 `root:adm` 기준으로 복구하고, `nobody` 사용자가 로그 디렉터리와 로그 파일에 접근하지 못하면 WEB-26은 조치 후 **양호**로 판단한다.