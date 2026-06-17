---
type: lab
topic: web-security
source: lab-observation
status: draft
created: 2026-05-20
tags:
  - 🏷️과목/웹보안
  - 🏷️주제/WEB서버
  - 🏷️주제/LAMP
  - 🏷️상태/draft
---

# 웹보안 LAMP 실습 환경 구축

## 실습 개요

한 줄 요약: **Paros와 Hydra 실습에 필요한 Apache/PHP/MySQL 기반 `care` 웹 애플리케이션 환경을 구축하고 DB 동작을 확인한 기록이다.**

이 노트는 원래 `Hydra 로그인 Brute Force 실습` 안에 함께 있던 공통 환경 구축 구간을 분리한 것이다. p.75-76 입력 검증 위치 실습과 p.77-79 Hydra 실습이 모두 이 환경을 전제로 한다.

| 항목 | 내용 |
|---|---|
| 목적 | 웹보안 실습용 LAMP 환경과 `care` 애플리케이션 준비 |
| WEB 서버 | Apache + PHP |
| Database | MySQL |
| 실습 앱 | `care` 웹 애플리케이션 |
| 관찰 도구 | Paros |
| 후속 실습 | [[10_학습 노트/시스템보안/웹보안/Client-side Validation 우회와 Server-side Validation 실습|Client-side Validation 우회와 Server-side Validation 실습]], [[10_학습 노트/시스템보안/웹보안/Hydra 로그인 Brute Force 실습|Hydra 로그인 Brute Force 실습]] |

---
## 실습 환경 구축

### Windows VM 도구 준비 단계

`web_tool.zip`에는 다음 파일이 포함되어 있다.

| 파일                                     | 현재 해석                                                   |
| -------------------------------------- | ------------------------------------------------------- |
| `web_tool/jre-6u11-windows-i586-p.exe` | Paros 실행에 필요한 Java Runtime 설치 파일로 보임                    |
| `web_tool/paros-3.2.13-win.exe`        | Web Proxy Tool인 Paros 설치 파일. 웹 요청을 프록시로 관찰/조작하는 데 사용 예정 |
| `web_tool/nc(1234).zip`                | netcat 계열 도구로 추정. 아직 직접 사용 단계는 아님                       |
두 `.exe`는 관리자 권한으로 실행했다. 설치 경로는 기본값을 유지했다.
그 다음 Paros를 실행하면 `javaw`를 찾으라는 창이 뜨는데, 찾아보기를 클릭한 후 `C:\Program Files (x86)\Java\jre6\bin`에서 `javaw`를 지정하면 된다.

엣지 → 설정 → 프록시 검색 → ![[Pasted image 20260521114306.png|697]]
![[Pasted image 20260521114349.png]]

프록시 설정을 바꾼 뒤에는 반드시 저장해야 Paros로 요청이 지나간다.

---
### WEB 서버 구축 단계

| 항목           | 값 / 의미                                    |
| ------------ | ----------------------------------------- |
| 구성 방식        | LAMP 계열 환경 구성                             |
| Web Server   | Apache                                    |
| Apache 포트    | `8080`                                    |
| DocumentRoot | `/var/www/care`                           |
| 개발/소유 계정     | 실행 전 `web`으로 수정 필요                        |
| PHP          | Apache용 PHP 모듈과 관련 패키지 설치                 |
| PHP 테스트 파일   | `/var/www/care/index.php`에 `phpinfo()` 생성 |
| Database     | MySQL                                     |
| DB 이름        | `care`                                    |
| DB 사용자       | `care`                                    |
| DB 비밀번호      | 스크립트에 평문으로 들어 있으므로 노트에는 기록하지 않음           |
#### WEB 서버 설치 스크립트와 Linux 설정

WEB 서버 VM은 Linux로 설치하고, 강사님이 제공한 [스크립트](https://mybox.naver.com/share/list?shareKey=fFWPu3ZYRTMvxDAuERWO41CiEvNmAKz3fcUWpqJeumMD&resourceKey=a3lzODUwMnwzNDcyNTk2MTQ5NTYwNjA0NDkyfER8MTg1OTMzNTI)를 실행한다.
스크립트는 위 표의 Apache/PHP/MySQL 기반 실습 환경을 한 번에 구성한다.

#### 예상 구축 흐름

1. 패키지 목록을 갱신한다.
2. Apache를 설치하고 활성화한다.
3. Apache가 `8080` 포트에서 동작하도록 설정한다.
4. DocumentRoot를 `/var/www/care`로 바꾼다.
5. 웹 루트 디렉터리를 만들고 권한을 설정한다.
6. PHP와 관련 확장 패키지를 설치한다.
7. `phpinfo()` 테스트 페이지를 만든다.
8. MySQL을 설치하고 활성화한다.
9. 실습용 DB와 DB 사용자를 만든다.
10. Apache를 재시작한다.

#### Apache DocumentRoot와 `care` 파일 배포

스크립트 실행이 완료되면 Apache는 `/var/www/care`를 웹 루트로 사용한다. 이 디렉터리는 그냥 임의 폴더가 아니라, 브라우저가 `http://<WEB_SERVER_IP>:8080/`로 접근했을 때 Apache가 파일을 찾아 읽는 **DocumentRoot**다.

강사님 클라우드에서 `care` 폴더를 내려받아 VS Code로 WEB 서버에 옮긴 뒤, 다음 명령으로 웹 루트에 배포한다.

```bash
sudo cp -r care/* /var/www/care
ls -la /var/www/care/
```

- `sudo cp -r care/* /var/www/care`
  다운로드한 웹 애플리케이션 파일을 Apache가 서비스하는 위치로 복사
- `ls -la /var/www/care/`
  실제로 파일이 들어갔는지 확인

#### 네트워크 설정 의도

스크립트 실행 후 실습망 접속과 Host PC에서의 관리 접속을 같이 고려해 네트워크를 잡았다.

이번에 배운 핵심은 **하나의 Linux 인터페이스에 IP 주소를 2개 부여해서 두 대역을 동시에 쓰는 방식**이다. 이 방식이 성립하면 실습 내부망용 NIC와 VS Code SSH 접속용 NIC를 따로 나누지 않아도 된다.

이미지 기준으로 VMware `VMnet3`는 Host-only 네트워크이며, Subnet은 `172.16.2.0/24`다. DHCP는 꺼져 있으므로 VM 쪽 IP는 직접 정적으로 넣어야 한다.

![[Pasted image 20260521095848.png]]

```yaml
sudo tee /etc/netplan/50-cloud-init.yaml > /dev/null << EOF
network:
  version: 2
  ethernets:
    ens33:
      dhcp4: false
      addresses:
        - 172.16.0.150/24
        - 172.16.2.150/24
      routes:
        - to: default
          via: 172.16.0.254
      nameservers:
        addresses: [1.1.1.1, 168.126.63.1]
    ens37:
      dhcp4: true
      dhcp6: false
EOF


sudo chmod 600 /etc/netplan/50-cloud-init.yaml

sudo netplan apply

```

#### 확인 결과

![[Pasted image 20260521095813.png]]

`ip a` 결과에서 `ens33`에 다음 두 주소가 같이 붙은 것을 확인했다.

- `172.16.0.150/24`: 실습 내부망에서 WEB 서버로 사용할 주소
- `172.16.2.150/24`: Host-only 대역에서 Host PC 또는 VS Code SSH 접속에 사용할 주소

정리하면, 이 구성은 **NIC를 2개 꽂은 것처럼 보이게 만드는 설정**이 아니라, **한 NIC에 여러 IP를 부여하는 설정**이다. 따라서 실제 통신이 되려면 VMware의 가상 네트워크 연결과 각 대역의 L2/L3 경로가 맞아야 한다.

---

## DB와 실습 애플리케이션 준비

`web_install.sh` 실행 후 MySQL에 `care` 데이터베이스가 생성되어 있는 것을 확인했다.

```sql
SHOW DATABASES;
USE care;
```

확인 결과 `information_schema`와 `care` 데이터베이스가 보였고, 이후 `care` 데이터베이스 안에 실습용 테이블을 만들었다.

### `member` 테이블

`member` 테이블은 로그인 실습에서 사용할 사용자 정보를 저장한다.

```sql
CREATE TABLE member(
  num int unsigned not null auto_increment,
  id varchar(50) not null,
  pw varchar(50) not null,
  name varchar(50) not null,
  mobile varchar(20),
  address varchar(50),
  email varchar(50),
  date varchar(30),
  primary key(num, id)
);
```

초기 데이터로 실습용 `admin` 계정을 넣고, `SELECT * FROM member;`로 조회되는 것을 확인했다. MySQL history에는 SQL 문이 그대로 남으므로, 노트에는 실습용 비밀번호 값을 직접 적지 않는다.

로컬 DB 구축 명령 파일인 `C:\Users\Unoh\Downloads\care\member\테이블 생성.txt`에는 다음 흐름이 함께 기록되어 있다.

- `id='aaa'` 조회 결과가 `Empty set`으로 나온 확인
- `ALTER TABLE member convert to charset utf8;`
- `ALTER DATABASE care DEFAULT CHARACTER SET utf8;`
- 한글 값이 포함된 `user1` 샘플 계정 추가와 조회

따라서 이 부분은 미확인이 아니라 DB 구축 기록의 일부로 본다. 단, 노트에는 실습용 비밀번호 값을 직접 적지 않는다.

Hydra 실습에는 별도 실습 계정 `unoh03`을 사용했다. 비밀번호는 숫자 3자리로 설정해 `-x 3:3:1` 생성 범위에 들어가게 했고, 값 자체는 기록하지 않는다.

### `center` 테이블

`care` 폴더 안의 `center(table).txt`를 참고해 게시판용으로 보이는 `center` 테이블도 만들었다.

```sql
CREATE TABLE center(
  num int unsigned not null auto_increment,
  id varchar(50) not null,
  subject varchar(255) not null,
  content text,
  date varchar(30),
  hit int unsigned,
  filename varchar(255),
  primary key(num)
);
```

### `dbconn.php`로 DB 연결 확인

WEB 서버에 `dbconn.php`를 만들어 브라우저에서 MySQL 연결과 `member` 테이블 조회가 되는지 확인했다.

접속 URL:

```text
http://172.16.0.150:8080/dbconn.php
```

`dbconn.php`의 흐름:

1. `mysqli_connect()`로 `localhost`의 `care` 데이터베이스에 접속한다.
2. `$id = 'admin'`으로 조회 대상 계정을 정한다.
3. `SELECT * FROM member WHERE id='$id'` 쿼리를 실행한다.
4. `mysqli_num_rows()`로 조회된 행 개수를 출력한다.
5. `mysqli_fetch_assoc()`로 결과 행을 가져와 `id`, `pw`, `name` 값을 출력한다.
6. `mysqli_close()`로 DB 연결을 닫는다.

이 파일은 PHP에서 MySQL 연결, 쿼리 실행, 결과 출력이 정상 동작하는지 확인하는 테스트 페이지다. 다만 실습용 페이지라도 DB 비밀번호와 사용자 비밀번호를 코드/화면에 그대로 노출하므로, 운영 환경에서는 이런 방식으로 작성하면 안 된다.

실습 계정을 지울 때는 삭제 전 대상을 먼저 확인하고 `DELETE`를 사용한다.

```sql
SELECT num, id, name FROM member;
DELETE FROM member WHERE id='user1';
```

### MySQL history가 바로 안 보이는 이유

MySQL 프롬프트에서 입력한 SQL은 Bash의 `history` 명령으로 보이지 않는다. MySQL 클라이언트는 별도 히스토리 파일을 쓰며, 보통 정상 종료 후 `~/.mysql_history`에 저장된다.

이번 확인에서는 `web` 사용자의 `~/.mysql_history`에 MySQL 명령 기록이 남아 있었다. 파일 안에서는 공백이 `\040`처럼 escape된 형태로 보이고, 오타나 실패한 시도도 함께 남을 수 있다.

`sudo mysql ...`로 실행한 경우 환경에 따라 히스토리 파일이 `/root/.mysql_history`에 생길 수도 있으므로, 둘 다 확인할 수 있다.

확인 명령:

```bash
tail -n 30 ~/.mysql_history
sudo tail -n 30 /root/.mysql_history
```


---

## 진행 로그

### 2026-05-20

- 강사님 제공 `web_install.sh` 확인.
- 스크립트가 Apache, PHP, MySQL을 한 번에 설치하는 WEB 서버 구축 스크립트임을 확인.
- 서버 환경에 맞게 `DEV_USER`를 `web`으로 수정해야 한다는 메모를 남김.
- 2026-05-20 확인 당시 로컬 스크립트 사본은 아직 `DEV_USER="user1"`로 보였음.
- `web_tool.zip` 확인. 안에는 `jre-6u11-windows-i586-p.exe`, `paros-3.2.13-win.exe`, `nc(1234).zip`이 있음.
- Windows VM에 `web_tool.zip`을 넣고, 두 `.exe`를 관리자 권한으로 실행하는 단계까지 진행.
- 강사님 설명: Paros를 통해 프록시를 설정하고, 이후 "패스워드 크랙" 등의 실습을 진행할 예정.
- MySQL `care` 데이터베이스 안에 `member`, `center` 테이블 생성.
- `member` 테이블에 실습용 계정 데이터를 추가하고 조회 확인.
- `dbconn.php`로 PHP에서 MySQL `care.member` 조회가 되는지 확인.
- Paros에서 `POST /member/loginModel.php` 로그인 요청과 서버 응답을 관찰.
- Paros `Trap request`로 로그인 요청을 서버 전송 전에 멈춰 세우는 동작 확인.

## 보안 관찰 포인트

- 스크립트에 DB 비밀번호가 평문으로 포함되어 있다. 실습 노트에는 값 자체를 남기지 않는다.
- Apache 설정에 `Options Indexes`가 포함되어 있다면, 파일 목록 노출과 Directory Listing 취약점 실습과 연결될 수 있다.
- `/var/www/care` 권한이 넓게 열려 있으므로, 실습 편의와 운영 보안의 차이를 나중에 구분해야 한다.
- `phpinfo()` 페이지는 환경 정보가 많이 노출되므로, 운영 환경에서는 제거해야 한다.

## 관련 노트

- [[10_학습 노트/시스템보안/웹보안/Client-side Validation 우회와 Server-side Validation 실습|Client-side Validation 우회와 Server-side Validation 실습]]
- [[10_학습 노트/시스템보안/웹보안/Hydra 로그인 Brute Force 실습|Hydra 로그인 Brute Force 실습]]
- [[10_학습 노트/시스템보안/웹보안/웹 애플리케이션 구조|웹 애플리케이션 구조]]
- [[10_학습 노트/시스템보안/웹보안/HTTP 구조와 메시지|HTTP 구조와 메시지]]
- [[10_학습 노트/시스템보안/웹보안/5-20 웹보안 PDF 구조 지도|5-20 웹보안 PDF 구조 지도]]
