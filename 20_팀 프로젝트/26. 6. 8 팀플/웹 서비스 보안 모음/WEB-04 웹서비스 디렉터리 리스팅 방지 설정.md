---
type: lab
topic: web-service-security 
source: 주요정보통신기반시설 기술적 취약점 분석·평가 방법 상세가이드
source_pages:
  - 280
  - 281
  - 282
status: draft
created: 2026-06-18
tags:
  - 🏷️과목/웹서비스보안
  - 🏷️주제/WEB-04
  - 🏷️주제/Directory-Listing
  - 🏷️주제/Apache
  - 🏷️상태/draft
---
# WEB-04 웹서비스 디렉터리 리스팅 방지 설정

## 1. PDF 기준

PDF p.280-282의 WEB-04는 웹 서버의 **디렉터리 리스팅 기능 차단 여부**를 점검하는 항목이다.

디렉터리 리스팅은 특정 디렉터리에 기본 페이지가 없을 때 웹 서버가 해당 디렉터리 안의 파일 목록을 자동으로 보여주는 기능이다.

예를 들어 다음과 같은 URL에 접근했을 때:

```text
http://서버주소/uploads/
http://서버주소/data/
http://서버주소/backup/
```

서버가 `index.html`, `index.php` 같은 기본 문서를 찾지 못하고 디렉터리 내부 파일 목록을 보여주면 디렉터리 리스팅이 활성화된 상태다.

이 기능이 활성화되어 있으면 사용자는 파일명을 직접 알지 못해도 디렉터리 내부 구조와 파일 목록을 확인할 수 있다. 이 과정에서 백업 파일, 설정 파일, 테스트 파일, 업로드 파일 등이 노출될 수 있다.

PDF의 판단 기준은 다음과 같다.

|판단|기준|
|---|---|
|양호|디렉터리 리스팅이 설정되지 않은 경우|
|취약|디렉터리 리스팅이 설정된 경우|

Apache에서는 `Options` 지시자에 `Indexes`가 포함되어 있으면 디렉터리 리스팅이 활성화될 수 있다.

```apache
Options Indexes FollowSymLinks
```

반대로 `Indexes`를 제거하거나 `-Indexes`로 명시하면 디렉터리 리스팅을 차단할 수 있다.

```apache
Options -Indexes FollowSymLinks
```

## 2. 최초 진단 결과

`AWS WEB 약점 진단 결과.md` 기준 최초 진단 결과는 **취약**이다.

|항목|내용|
|---|---|
|진단 결과|취약|
|진단 근거|`apache2.conf` 전역 설정에 `Options Indexes FollowSymLinks` 존재|
|영향|index 파일이 없는 디렉터리에서 파일 목록이 노출될 가능성|
|조치 방향|`Indexes` 옵션 제거 또는 `-Indexes` 명시|

진단에 사용된 명령어는 다음과 같다.

```bash
grep -r 'Options.*Indexes' /etc/apache2/apache2.conf /etc/apache2/sites-available/ /etc/apache2/conf-available/ 2>/dev/null | grep -v '^\s*#'
```

진단 결과는 다음과 같다.

```text
/etc/apache2/apache2.conf:    Options Indexes FollowSymLinks
/etc/apache2/apache2.conf:#   Options Indexes FollowSymLinks  ← 주석
```

주석 처리된 줄은 실제 적용 대상이 아니다. 문제는 주석이 아닌 활성 설정에 `Indexes`가 포함되어 있다는 점이다.

따라서 현재 Apache 전역 설정 기준으로 디렉터리 리스팅이 허용될 수 있는 상태로 판단한다.

## 3. 현재 서버 상태 해석

Apache의 `Options` 지시자에서 `Indexes`는 index 파일이 없는 디렉터리에 대해 파일 목록 출력을 허용한다는 의미다.

`Options Indexes FollowSymLinks` 설정은 두 가지 의미를 가진다.

|옵션|의미|관련 항목|
|---|---|---|
|`Indexes`|디렉터리 목록 출력 허용|WEB-04|
|`FollowSymLinks`|심볼릭 링크 추적 허용|WEB-12|

WEB-04에서는 이 중 `Indexes`가 핵심이다. 전역 설정에 `Indexes`가 남아 있으면 새 디렉터리를 만들었을 때 파일 목록이 노출될 수 있다.

이 항목은 CARE PHP 코드의 문제라기보다 Apache 웹 서버 설정 문제다. 다만 다른 취약점과 연결될 수 있다.

|연결 항목|연결 이유|
|---|---|
|웹 앱 05 정보 누출|백업 파일, 설정 파일, 테스트 파일명이 노출될 수 있음|
|웹 앱 14 악성 파일 업로드|업로드된 파일명이 디렉터리 목록으로 확인될 수 있음|
|웹 앱 15 파일 다운로드|다운로드 대상 파일명을 추측하기 쉬워질 수 있음|
|WEB-07 불필요한 파일 제거|디렉터리 리스팅과 불필요 파일이 결합되면 위험 증가|
|WEB-14 파일 접근 통제|파일 목록 차단과 파일 자체 접근 통제는 별도로 관리해야 함|

즉 WEB-04는 단독 취약점이면서 동시에 정보 노출, 파일 업로드, 파일 다운로드 관련 공격의 보조 공격면이 될 수 있다.

## 4. 취약 재현

이 항목은 최초 진단에서 이미 취약으로 확인되었으므로, 별도로 양호 상태를 약화하지 않고 현재 취약 설정을 증거화한다.

재현은 다음 방식으로 수행한다.

1. index 파일이 없는 테스트 디렉터리를 만든다.
    
2. 테스트용 파일을 둔다.
    
3. 브라우저 또는 HTTP 요청으로 해당 디렉터리 경로에 접근한다.
    
4. 파일 목록이 보이면 디렉터리 리스팅 취약 상태로 판단한다.
    

### 4-1. 테스트 디렉터리 생성

```bash
sudo mkdir -p /var/www/care/dir-list-test
```

### 4-2. 테스트 파일 생성

```bash
echo "directory listing test file 1" | sudo tee /var/www/care/dir-list-test/test1.txt
echo "directory listing test file 2" | sudo tee /var/www/care/dir-list-test/test2.txt
```

이 디렉터리에는 `index.html`이나 `index.php`를 만들지 않는다. 디렉터리 리스팅은 기본 index 파일이 없을 때 확인하기 쉽다.

### 4-3. 브라우저 또는 curl로 접근

```bash
curl -i http://172.168.10.10/dir-list-test/
```

취약 상태에서 기대되는 화면은 다음과 같은 `Index of /...` 형태의 디렉터리 목록이다.

```text
Index of /dir-list-test
test1.txt
test2.txt
```

조치가 이미 적용된 상태라면 `403 Forbidden` 또는 사용자 정의 에러 페이지가 출력될 수 있다.

### 4-4. 취약 증거로 남길 내용

증거 캡처는 다음을 남긴다.

```text
1. apache2.conf에 Options Indexes FollowSymLinks가 존재하는 화면
2. /dir-list-test/ 접근 시 Index of 화면이 출력되는 화면
3. test1.txt, test2.txt 파일명이 노출되는 화면
```

## 5. 조치 방법

Apache 설정에서 `Indexes`를 제거하거나 명시적으로 비활성화한다.

취약 설정 예시는 다음과 같다.

```apache
Options Indexes FollowSymLinks
```

WEB-04 조치 후에는 다음처럼 바꾼다.

```apache
Options -Indexes FollowSymLinks
```

WEB-12 조치와 함께 처리한다면 다음처럼 구성할 수 있다.

```apache
Options -Indexes SymLinksIfOwnerMatch
```

다만 WEB-04의 핵심은 `Indexes` 제거다. `FollowSymLinks` 자체는 WEB-12에서 별도로 판단한다.

### 5-1. 설정 파일 백업

Apache 설정을 수정하기 전에 백업한다.

```bash
sudo cp /etc/apache2/apache2.conf /etc/apache2/apache2.conf.bak.WEB-04
```

### 5-2. 설정 파일 수정

```bash
sudo nano /etc/apache2/apache2.conf
```

다음 설정을 찾는다.

```apache
Options Indexes FollowSymLinks
```

다음처럼 수정한다.

```apache
Options -Indexes FollowSymLinks
```

`Indexes`를 단순히 제거해도 된다.

```apache
Options FollowSymLinks
```

다만 실습 기록에서는 차단 의도가 명확하게 보이도록 `-Indexes`를 쓰는 편이 낫다.

### 5-3. 다른 설정 파일 확인

Apache는 `apache2.conf`뿐 아니라 `sites-available`, `sites-enabled`, `conf-available` 아래 설정을 함께 읽을 수 있다. 따라서 다음 명령으로 남아 있는 `Indexes` 설정을 확인한다.

```bash
grep -r 'Options.*Indexes' /etc/apache2/apache2.conf /etc/apache2/sites-available/ /etc/apache2/sites-enabled/ /etc/apache2/conf-available/ 2>/dev/null | grep -v '^\s*#'
```

조치 후에는 `Indexes`가 남아 있지 않거나, `-Indexes`로 명시되어 있어야 한다.

### 5-4. Apache 설정 문법 검사

설정 변경 후에는 Apache 설정 문법 검사를 수행한다.

```bash
sudo apachectl configtest
```

정상이라면 다음 결과가 나와야 한다.

```text
Syntax OK
```

### 5-5. Apache reload

문법 검사에 문제가 없을 때만 Apache 설정을 다시 읽어오게 한다.

```bash
sudo systemctl reload apache2
```

## 6. 조치 후 확인

조치 후에는 다음 두 가지를 확인한다.

|확인|기대 결과|
|---|---|
|Apache 설정 파일|활성 설정에서 `Indexes`가 제거되었거나 `-Indexes`로 명시됨|
|디렉터리 접근 테스트|파일 목록이 보이지 않고 차단 또는 에러 페이지가 출력됨|

조치 후에도 `Index of /...` 형태의 파일 목록이 보이면 조치가 완료되지 않은 것이다.

조치 후 같은 테스트 디렉터리에 다시 접근한다.

```bash
curl -i http://172.168.10.10/dir-list-test/
```

정상 조치 상태라면 파일 목록이 출력되지 않아야 한다. 기대 결과는 다음 중 하나다.

```text
HTTP/1.1 403 Forbidden
```

또는 WEB-22에서 사용자 정의 에러 페이지를 설정했다면 커스텀 403 페이지가 표시될 수 있다.

주의할 점은 **디렉터리 리스팅 차단이 개별 파일 접근 차단과 같지는 않다**는 것이다.

예를 들어 디렉터리 목록은 차단되었더라도, 파일명을 정확히 알면 다음처럼 직접 접근이 가능할 수 있다.

```text
http://172.168.10.10/dir-list-test/test1.txt
```

이 문제는 WEB-04가 아니라 WEB-14 파일 접근 통제 또는 웹 앱 정보 노출 항목에서 별도로 판단한다. WEB-04는 “디렉터리 목록이 보이는가”를 중심으로 판단한다.

## 7. 증거 정리

### 7-1. 조치 전 증거

조치 전 설정 확인:

```bash
grep -r 'Options.*Indexes' /etc/apache2/apache2.conf /etc/apache2/sites-available/ /etc/apache2/conf-available/ 2>/dev/null | grep -v '^\s*#'
```

조치 전 기대 또는 실제 결과:

```text
/etc/apache2/apache2.conf:    Options Indexes FollowSymLinks
```

테스트 디렉터리 접근 결과:

```bash
curl -i http://172.168.10.10/dir-list-test/
```

취약 상태 기대 결과:

```text
Index of /dir-list-test
test1.txt
test2.txt
```

### 7-2. 조치 후 증거

조치 후 설정 확인:

```bash
grep -r 'Options.*Indexes' /etc/apache2/apache2.conf /etc/apache2/sites-available/ /etc/apache2/sites-enabled/ /etc/apache2/conf-available/ 2>/dev/null | grep -v '^\s*#'
```

조치 후 기대 결과:

```text
Options -Indexes FollowSymLinks
```

또는 `Indexes`가 더 이상 출력되지 않음.

조치 후 디렉터리 접근 확인:

```bash
curl -i http://172.168.10.10/dir-list-test/
```

조치 후 기대 결과:

```text
HTTP/1.1 403 Forbidden
```

## 8. 판단

|항목|판단|
|---|---|
|최초 진단|취약|
|진단 근거|`apache2.conf` 전역 설정에 `Options Indexes FollowSymLinks` 존재|
|실습 처리|현재 취약 설정 증거화 후 조치|
|조치 방법|Apache `Options` 지시자에서 `Indexes` 제거 또는 `-Indexes` 명시|
|최종 판단|조치 후 재진단 필요|
|증거 상태|자동 진단 결과 확보, 웹 접근 증거 추가 필요|

현재 서버의 Apache 전역 설정에 `Options Indexes FollowSymLinks`가 존재하므로 WEB-04는 최초 진단 기준 **취약**이다.

조치는 `Indexes`를 제거하거나 `-Indexes`를 명시하는 방식으로 수행한다. 조치 후에는 설정 파일 검사와 실제 디렉터리 접근 테스트를 모두 수행하여 디렉터리 목록이 더 이상 노출되지 않는지 확인한다.

조치 후 디렉터리 목록이 출력되지 않으면 WEB-04는 조치 후 **양호**로 판단한다.
