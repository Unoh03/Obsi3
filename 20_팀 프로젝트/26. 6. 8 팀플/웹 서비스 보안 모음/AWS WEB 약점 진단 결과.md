# KISA CIIP 2026 — Apache 웹서버 취약점 진단 결과

> [!info] 진단 정보
> 
> - **호스트**: ip-10-0-11-117
> - **진단 일시**: 2026-06-18 01:48:27
> - **플랫폼**: Apache (웹서버)
> - **도구**: KISA-CIIP-2026 v1.0.0

---

## 📊 진단 통계

|구분|건수|
|---|---|
|✅ 양호|13|
|❌ 취약|4|
|🔍 수동|5|
|➖ N/A|4|
|**총계**|**26**|
|**양호율**|**50.0%**|

---

## ❌ 취약 항목 (4건)

### WEB-04 · 웹서비스 디렉터리 리스팅 방지 설정

> [!danger] VULNERABLE `apache2.conf` 전역 설정에 `Options Indexes FollowSymLinks` 가 존재함

**진단 명령어**

```bash
grep -r 'Options.*Indexes' /etc/apache2/apache2.conf /etc/apache2/sites-available/ /etc/apache2/conf-available/ 2>/dev/null | grep -v '^\s*#'
```

**결과**

```
/etc/apache2/apache2.conf:    Options Indexes FollowSymLinks
/etc/apache2/apache2.conf:#   Options Indexes FollowSymLinks  ← 주석
```

**조치**

```bash
sudo nano /etc/apache2/apache2.conf
# Options Indexes FollowSymLinks  →  Options -Indexes FollowSymLinks
sudo apachectl configtest && sudo systemctl reload apache2
```

---

### WEB-12 · 웹서비스 링크 사용 금지 (FollowSymLinks)

> [!danger] VULNERABLE `FollowSymLinks` 활성화 — 심볼릭 링크를 통한 시스템 파일 접근 가능

**진단 명령어**

```bash
grep -E '^\s*Options' /etc/apache2/apache2.conf /etc/apache2/sites-enabled/*.conf 2>/dev/null | grep -v '^\s*#'
```

**결과**

```
Options FollowSymLinks          ← apache2.conf 전역
Options Indexes FollowSymLinks  ← apache2.conf 전역
```

**조치**

```bash
sudo nano /etc/apache2/apache2.conf
# Options FollowSymLinks         →  Options SymLinksIfOwnerMatch
# Options Indexes FollowSymLinks →  Options -Indexes SymLinksIfOwnerMatch
sudo apachectl configtest && sudo systemctl reload apache2
```

> [!note] SymLinksIfOwnerMatch vs -FollowSymLinks
> 
> - `-FollowSymLinks`: 모든 심볼릭 링크 차단 (가장 안전)
> - `SymLinksIfOwnerMatch`: 링크와 실제 파일 소유자 동일할 때만 허용 (절충안)

---

### WEB-20 · SSL/TLS 활성화

> [!danger] VULNERABLE — ⚠️ 진단 스크립트 오탐 의심

**진단 결과 모순**

```
command_result: SSL module loaded, HTTPS configured  ← 양호
Result: VULNERABLE  ← 모순
```

**수동 확인**

```bash
apache2ctl -M | grep ssl
ss -tlnp | grep 443
ls /etc/apache2/sites-enabled/
```

> [!warning] 오탐 가능성 command_result 에 "HTTPS configured" 라고 명시됨에도 VULNERABLE 판정. 진단 스크립트 로직 버그로 추정. 수동 확인 후 실제 상태 판단 필요.

---

### WEB-22 · 웹서비스 에러페이지 사용

> [!danger] VULNERABLE `ErrorDocument` 설정 없음 — 기본 Apache 에러 페이지 노출 시 서버 정보 유출 위험

**진단 명령어**

```bash
grep -rE '^\s*ErrorDocument\s+(400|401|403|404|500|503)' /etc/apache2/apache2.conf /etc/apache2/sites-available/ 2>/dev/null | grep -v '^\s*#'
```

**결과**

```
No ErrorDocument directives found
```

**조치**

```bash
sudo nano /etc/apache2/sites-available/<vhost>.conf
```

```apache
ErrorDocument 400 /errors/error.html
ErrorDocument 403 /errors/error.html
ErrorDocument 404 /errors/error.html
ErrorDocument 500 /errors/error.html
```

```bash
# 에러 페이지 파일 생성 후
sudo apachectl configtest && sudo systemctl reload apache2
```

---

## ✅ 양호 항목 (13건)

### WEB-05 · CGI/ISAPI 실행 제한

CGI 실행이 ScriptAlias로 지정된 `/cgi-bin/` 디렉터리로만 제한됨

```
ScriptAlias /cgi-bin/ /usr/lib/cgi-bin/
```

---

### WEB-07 · 불필요한 파일 제거

백업, 샘플, 테스트 파일 등 불필요한 파일 발견되지 않음

```
No unnecessary files found
```

---

### WEB-08 · .htaccess 오버라이드 제한

`AllowOverride All` 없음 — `.htaccess` 를 통한 보안 설정 변경 불가

---

### WEB-09 · 웹서비스 프로세스 권한 제한

Apache 자식 프로세스가 `www-data` 계정으로 구동 중 (root 아님)

```
root(마스터) / www-data(자식 프로세스 8건)
```

---

### WEB-10 · 불필요한 프록시 설정 제한

`ProxyPass`, `ProxyPassReverse`, `ProxyRequests` 설정 없음

```
No proxy settings found
```

---

### WEB-11 · 웹서비스 경로 설정

DocumentRoot가 기본 경로가 아닌 별도 경로로 분리됨

```
DocumentRoot: /var/www/care
```

---

### WEB-14 · 웹서비스 경로 내 파일 접근 통제

`Require all denied` / `Require all granted` 적절히 구성됨

```
Require all denied   ← 기본 차단
Require all granted  ← 명시적 허용 경로만 오픈
```

---

### WEB-15 · 불필요한 스크립트 매핑 제거

`AddHandler`, `AddType`, `Action`, `ScriptAlias` 등 불필요한 핸들러 없음

```
No script handler mappings found
```

---

### WEB-16 · 웹서버 헤더 정보 노출 제한

서버 정보 노출 최소화 설정 확인

```
ServerTokens: Minimal
ServerSignature: Off
```

> [!note] 권장사항 `Minimal` 은 양호 판정이나, 가능하면 `Prod` 로 변경 시 Apache 명칭만 노출 (버전 완전 제거)

---

### WEB-17 · 웹서비스 가상 디렉터리 삭제

`Alias` 지시어로 설정된 불필요한 가상 디렉터리 없음

```
No Alias directives found
```

---

### WEB-18 · WebDAV 비활성화

`DAV On` 설정 없음 — WebDAV 비활성화 확인

```
DAV disabled or not loaded
```

---

### WEB-19 · WebDAV 모듈 미로드

`mod_dav` 모듈이 로드되지 않았거나 `DAV` 지시어 미설정

```
No WebDAV module or DAV directive found
```

---

### WEB-26 · 로그 디렉터리 및 파일 권한 설정

모든 로그 파일 640, 디렉터리 750 으로 적절히 설정됨

|파일|권한|
|---|---|
|access.log|640 ✅|
|error.log|640 ✅|
|other_vhosts_access.log|640 ✅|
|error.log.1|640 ✅|
|/var/log/apache2 (디렉터리)|750 ✅|

---

## 🔍 수동 진단 항목 (5건)

|항목|내용|확인 방법|
|---|---|---|
|WEB-06|상위 디렉터리 접근 제한|`AllowOverride None` 확인, `../` 요청 시 403 응답 테스트|
|WEB-21|동적 페이지 입력값 검증|소스코드 레벨 수동 검토 필요|
|WEB-23|HTTP 메서드 제한|`LimitExcept` 설정 확인|
|WEB-24|X-Frame-Options 헤더|`Header always set X-Frame-Options DENY` 설정 여부|
|WEB-25|X-XSS-Protection 헤더|`Header always set X-XSS-Protection "1; mode=block"` 설정 여부|

---

## ➖ N/A 항목 (4건)

|항목|사유|
|---|---|
|WEB-01|Tomcat/IIS/JEUS 대상 항목 — Apache 해당 없음|
|WEB-02|Tomcat/IIS/JEUS 대상 항목 — Apache 해당 없음|
|WEB-03|Tomcat/IIS/JEUS 대상 항목 — Apache 해당 없음|
|WEB-13|WEB-04와 중복 — Apache 해당 없음|

---

## 🛠️ 조치 우선순위

```
즉시 조치 (설정 변경만 필요)
├── WEB-04  apache2.conf Options -Indexes 적용
├── WEB-12  FollowSymLinks → SymLinksIfOwnerMatch
└── WEB-22  ErrorDocument 커스텀 에러 페이지 추가

수동 확인 후 판단
└── WEB-20  SSL 상태 수동 확인 (오탐 가능성)
```

---

_출처: KISA-CIIP-2026 v1.0.0 / https://github.com/rebugui/KISA-CIIP-2026_ _진단일: 2026-06-18_