---
type: lab
topic: aws
source:
  - AWS기초.pdf
  - lab-observation
source_pages:
  - "13-25"
status: active
created: 2026-06-01
reviewed: 2026-06-02
aliases:
  - EC2 RDS 연동 실습
  - EC2와 RDS 연결 실습
tags:
  - 🏷️과목/AWS
  - 🏷️주제/EC2
  - 🏷️주제/RDS
  - 🏷️주제/SecurityGroup
  - 🏷️주제/TLS
  - 🏷️상태/active
---

# EC2와 RDS 기본 구성 실습

## 실습 결과

> [!summary] EC2 웹 서버와 RDS 연동 성공
> Ubuntu EC2 instance에 Tomcat과 `boot.war`를 배포하고, RDS for MariaDB의 `care` database와 연결했다. EC2 Security Group의 `8080` inbound rule과 RDS Security Group의 `3306` inbound rule을 조정하고 JDBC TLS 옵션을 추가한 뒤, 2026-06-02에 외부 브라우저에서 `http://3.39.190.74:8080/boot/boardForm` 접속을 확인했다.

> [!note] public IPv4는 바뀔 수 있다
> 위 주소는 성공 당시의 관찰값이다. EC2의 일반 public IPv4는 instance를 `stop` 후 `start`하거나 다시 만들면 바뀔 수 있다. 다시 실습할 때는 EC2 Console에서 현재 주소를 확인한다.

## EC2 서비스 진입

![[Pasted image 20260601154458.png]]

AWS Console에서 `EC2`를 검색했다. EC2는 AWS Cloud에서 가상 서버인 instance를 생성하고 관리하는 서비스다.

## 인스턴스 시작

![[Pasted image 20260601154715.png]]

EC2 instance 생성 화면으로 진입했다. 화면에 표시된 Region은 `아시아 태평양(서울)`이다.

> [!important] Region을 바꾸면 다른 Region의 리소스는 목록에서 보이지 않는다
> 실습 도중 instance가 사라진 것처럼 보이면 먼저 Console 상단의 Region을 확인한다.

## 이름, AMI, Instance Type

![[Pasted image 20260601154941.png]]

- **이름**은 AWS Console에서 instance를 구분하기 위해 붙이는 `Name` 태그다.
- **AMI**(Amazon Machine Image)는 instance를 시작할 때 사용하는 이미지다. 운영체제 환경과 root volume 구성을 선택하는 출발점이다.
- 화면에서는 Ubuntu AMI와 `t3.micro` instance type을 선택했다.
- **인스턴스 유형**은 CPU, 메모리 같은 서버 사양을 결정한다.

> [!note] AMI ID와 Terraform
> AMI ID는 Terraform으로 EC2 instance를 만들 때도 사용할 수 있다. AMI ID는 Region과 이미지 버전에 종속되므로 다른 Region에 그대로 복사해서 사용하지 않는다.

## 키 페어와 네트워크 설정

![[Pasted image 20260601155036.png]]

- **키 페어**는 ID와 password 대신 SSH 인증키로 로그인하기 위해 사용한다. EC2 instance에는 공개키가 등록되고, 사용자 컴퓨터에는 개인키가 남는다.
- **VPC**는 AWS 안에서 사용할 논리적으로 격리된 가상 네트워크다.
- **Subnet**은 VPC의 IP 주소 범위를 더 작게 나눈 구간이다. instance는 특정 subnet에 배치된다.
- **가용 영역**(Availability Zone, AZ)은 Region 내부의 분리된 인프라 위치다. subnet은 하나의 AZ에 속한다.
- **퍼블릭 IP 자동 할당**을 활성화하면 인터넷에서 instance에 접근할 때 사용할 public IPv4를 받을 수 있다.
- **Security Group**은 instance 단위에서 inbound와 outbound traffic을 제어하는 가상 방화벽이다. 처음에는 Cisco ACL처럼 허용할 traffic을 적는 규칙 목록으로 이해하면 편하다. 다만 Security Group은 stateful이고 allow rule만 사용하므로 완전히 같지는 않다.

> [!note] 수업 메모: 체크박스 세 개와 Tomcat `8080`
> 화면에는 SSH, HTTPS, HTTP 허용 체크박스가 있다. 수업 중에는 나중에 Security Group을 다시 수정하는 번거로움을 줄이기 위해 세 항목을 모두 체크하라는 안내가 있었다. 다만 Tomcat 기본 포트 `8080`은 HTTP `80`이나 HTTPS `443`과 다른 포트다. 이번 실습처럼 `http://<public IPv4>:8080/boot/`로 접속하려면 `8080` rule을 별도로 추가해야 한다.

| 체크박스 | 생성되는 inbound rule | 용도 |
| --- | --- | --- |
| SSH traffic 허용 | TCP `22` | 원격 터미널 접속 |
| HTTPS traffic 허용 | TCP `443` | TLS를 적용한 일반 웹 서비스 |
| HTTP traffic 허용 | TCP `80` | 일반 HTTP 웹 서비스 |

> [!warning] SSH를 `0.0.0.0/0`에 장기간 열지 않는다
> `0.0.0.0/0`은 모든 IPv4 주소를 의미한다. 짧은 실습에서는 사용할 수 있지만, SSH `22`는 가능하면 `내 IP` 또는 필요한 IP 범위로 제한한다.

## 키 페어 생성

![[Pasted image 20260601155213.png]]

- 키 페어 이름으로 `web`을 입력했다.
- 키 페어 유형은 `RSA`, 프라이빗 키 파일 형식은 `.pem`을 선택했다.
- `.pem`은 OpenSSH에서 사용할 수 있는 개인키 파일이다. `.ppk`는 PuTTY에서 사용하는 형식이다.

> [!warning] 개인키 파일은 노출하지 않는다
> 개인키는 생성 직후 안전한 위치에 보관한다. Obsidian vault, Git 저장소, 메신저, 스크린샷에 넣지 않는다. 개인키를 잃어버리면 같은 파일을 다시 내려받을 수 없다.

![[Pasted image 20260601162314.png]]

- 네트워크 설정 오른쪽 위의 `편집`을 누르면 VPC, subnet, public IP, Security Group과 inbound rule을 직접 설정할 수 있다.

| 항목 | 의미 | 이번 실습 기준 |
| --- | --- | --- |
| VPC | instance가 속할 가상 네트워크 | 기본 VPC |
| Subnet | instance가 배치될 VPC 내부 구간 | 기본 subnet |
| 가용 영역 | instance를 배치할 AZ | 기본 설정 |
| 퍼블릭 IP 자동 할당 | 인터넷에서 접근할 public IPv4 부여 여부 | 활성화 |
| 보안 그룹 생성 | 새 Security Group 생성 | `launch-wizard-1` |
| Type | 허용할 traffic의 대표 유형 | SSH 또는 Custom TCP |
| Protocol | transport protocol | TCP |
| Port range | instance에서 열 포트 | SSH는 `22`, Tomcat은 `8080` |
| Source type | 접근을 허용할 출발지 범위 선택 | SSH는 `내 IP` 권장 |
| Source | 실제 CIDR 또는 Security Group | 예: 단일 IP는 `<public IPv4>/32` |
| Description | rule의 목적을 남기는 메모 | 예: `관리자 SSH`, `Tomcat 실습` |

이번 EC2는 SSH 접속을 위해 TCP `22`를 열고, Tomcat 외부 접속을 위해 Custom TCP `8080`도 추가한다. 외부 공개 범위는 수업 조건에 맞춰 정하되, 실습 종료 후 불필요한 rule을 정리한다.

고급 설정은 생략.
![[Pasted image 20260601163042.png]]

instance가 생성되면 상세 정보에서 public IPv4, private IPv4, VPC ID, subnet ID, Security Group, key pair를 확인할 수 있다.

![[Pasted image 20260601163624.png]]

`작업 -> 네트워킹 -> 소스/대상 확인 변경`에서는 source/destination check를 바꿀 수 있다.

> [!important] 일반 웹 서버에서는 source/destination check를 유지한다
> 기본값은 활성화다. EC2가 자신을 목적지로 하는 traffic을 받거나 자신이 시작한 traffic을 보내는 일반 웹 서버라면 그대로 둔다. NAT instance, router, firewall appliance처럼 다른 대상의 packet을 전달해야 하는 instance에서만 비활성화를 검토한다.

프록시의 forwarding과 비슷한 방향으로 이해할 수 있지만, 일반적인 reverse proxy는 각 연결의 종착점 역할도 하므로 무조건 source/destination check를 끄는 것은 아니다.


## RDS for MariaDB 생성

![[Pasted image 20260602093117.png]]

AWS Console에서 `rds`를 검색하고 `Aurora and RDS`로 진입한다.

![[Pasted image 20260602093258.png]]

왼쪽 메뉴에서 `데이터베이스`를 선택한다.

![[Pasted image 20260602093310.png]]

`데이터베이스 생성`을 선택한다.

![[Pasted image 20260602093613.png]]

- Engine type은 `MariaDB`를 선택했다.
- 생성 방식은 `전체 구성`을 선택했다.
- Template은 실습 비용을 줄이기 위해 `프리 티어`를 선택했다.

> [!warning] DB engine과 template은 비용을 확인하고 선택한다
> Console에는 Aurora, MySQL, PostgreSQL, MariaDB, Oracle, Microsoft SQL Server, IBM Db2 등이 표시된다. 지원 기능과 과금 구조가 다르므로 수업 화면을 무조건 따라가지 말고 생성 전 예상 비용을 확인한다.

![[Pasted image 20260602094059.png]]![[Pasted image 20260602094311.png]]

- DB engine version은 화면에서 `MariaDB 11.8.6`을 선택했다.
- DB instance identifier와 master username은 화면에서 `admin`을 사용했다.
- DB instance class는 burstable class의 `db.t4g.micro`를 선택했다.
- Storage는 General Purpose SSD `gp2`, `20 GiB`를 선택했다.
- Multi-AZ deployment는 사용하지 않았다.

> [!warning] Multi-AZ는 무료가 아니다
> Multi-AZ는 장애 대응을 위한 추가 DB instance를 구성하므로 비용이 늘어난다. 이번 실습에서는 비용을 줄이기 위해 비활성화했다. 애초에 무료 이용자는 사용 할 수 없다.

![[Pasted image 20260602094732.png]]

- EC2 compute resource 연결은 직접 구성하기 위해 `연결 안 함`을 선택했다.
- Network type은 `IPv4`를 선택했다.
- EC2와 RDS가 통신할 수 있도록 같은 VPC를 선택했다.
- DB subnet group은 기본값을 사용했다.
- Public access는 `아니요`를 선택했다. 이 구성은 VPC 내부의 EC2에서 RDS로 접근한다.
- 새 VPC Security Group 이름은 `rds-sg`로 입력했다.
- RDS Proxy는 사용하지 않았다.
- 인증 기관은 화면의 기본값을 사용했다.

> [!note] Security Group 이름은 조직 규칙에 맞춘다
> 수업에서는 Security Group 이름을 회사별 규칙에 따라 관리한다는 설명이 있었다. 실무에서는 역할, 환경, 시스템을 식별할 수 있는 이름을 사용한다.

> [!note] 자동 연결과 수동 연결
> RDS Console에서 EC2 compute resource를 연결하면 AWS가 EC2와 RDS의 VPC Security Group을 자동으로 구성할 수 있다. 이번 실습은 rule의 의미를 확인하기 위해 직접 구성했다.

![[Pasted image 20260602094852.png]]

- Tag는 `Name=rds`로 입력했다.
- Monitoring은 기본값을 사용했다.
- Initial database name은 `care`로 입력했다.

![[Pasted image 20260602095240.png]]

- Storage encryption은 기본 AWS KMS key로 활성화했다.
- Automatic backup은 활성화하고 retention period는 `1`일로 설정했다.
- Auto minor version upgrade는 활성화했다.
- Deletion protection은 활성화하지 않았다.

> [!important] RDS의 관리 경계
> RDS는 managed database service다. 사용자는 EC2처럼 DB 서버 운영체제에 SSH로 접속해 직접 패키지를 관리하지 않는다. 대신 RDS가 지원하는 engine version과 maintenance 기능을 사용한다.

> [!note] Auto minor version upgrade
> minor upgrade는 일반적으로 이전 버전과 호환되는 bug fix와 security enhancement를 포함한다. 활성화하면 RDS가 maintenance window에 대상 minor version으로 업그레이드한다. 업그레이드 중에는 downtime이 발생할 수 있다.

> [!important] 저장 데이터 암호화와 연결 암호화는 별개다
> 화면의 Storage encryption은 disk와 snapshot 같은 저장 데이터의 암호화다. 뒤에서 설정할 JDBC TLS는 EC2와 RDS 사이를 이동하는 데이터의 암호화다. 한쪽을 설정했다고 다른 쪽이 자동으로 해결되는 것은 아니다.

## EC2 웹 서버와 RDS 연결

### 1. Security Group rule 확인

EC2와 RDS의 역할에 맞춰 inbound rule을 구성한다.

| 대상 | Type | Protocol | Port | Source | 목적 |
| --- | --- | --- | --- | --- | --- |
| EC2 Security Group | SSH | TCP | `22` | `내 IP` 권장 | SSH 접속 |
| EC2 Security Group | Custom TCP | TCP | `8080` | 실습에서 필요한 IP 범위 | Tomcat 외부 접속 |
| RDS Security Group | MYSQL/Aurora | TCP | `3306` | EC2 Security Group ID | EC2에서 RDS 접속 |

> [!important] RDS의 `3306` source에는 EC2 public IPv4보다 EC2 Security Group을 사용한다
> Security Group을 source로 지정하면 AWS는 연결된 instance의 private IP를 기준으로 traffic을 허용한다. EC2 public IPv4가 바뀌어도 같은 Security Group을 사용하는 EC2는 계속 RDS에 접근할 수 있다.

### 2. EC2에 Tomcat과 `boot.war` 배포

강사님이 제공한 `boot.war`를 EC2의 Ubuntu 사용자 home directory에 먼저 전송한다.

```text
/home/ubuntu/boot.war
```

AWS 폴더에 작성한 `ec2_tomcat_setup.sh`를 EC2에 전송한 뒤 실행한다.

```bash
chmod +x ec2_tomcat_setup.sh
sudo ./ec2_tomcat_setup.sh
```

스크립트는 Java 17과 Tomcat을 설치하고 `/opt/tomcat/current/webapps/boot.war`로 WAR를 복사한다. 실행 전에 `boot.war`를 넣지 않았다면 파일을 넣으라는 안내를 표시하고, Enter를 누를 때마다 다시 확인한다.

Tomcat 상태와 로컬 접속을 확인한다.

```bash
sudo systemctl status tomcat --no-pager -l
sudo ss -lntp | grep ':8080'
curl -i http://127.0.0.1:8080/boot/
```

### 3. EC2에 MariaDB client 설치

DB server는 RDS에 있으므로 EC2에는 접속 점검용 client만 설치한다.

```bash
sudo apt update
sudo apt install -y mariadb-client
```

### 4. RDS CA bundle 다운로드

AWS가 제공하는 RDS CA bundle을 내려받는다.

```bash
curl -o "$HOME/global-bundle.pem" \
  https://truststore.pki.rds.amazonaws.com/global/global-bundle.pem
```

### 5. RDS master account로 접속

RDS 상세 화면에서 endpoint를 확인한다. 아래 `<RDS endpoint>`에는 현재 RDS endpoint를 넣는다.

```bash
mysql \
  -h <RDS endpoint> \
  -P 3306 \
  -u admin \
  -p \
  --ssl-verify-server-cert \
  --ssl-ca="$HOME/global-bundle.pem"
```

- `-h`: 접속할 RDS endpoint
- `-P 3306`: MariaDB server port
- `-u admin`: RDS 생성 시 만든 master username
- `-p`: password를 명령줄에 노출하지 않고 입력
- `--ssl-ca`: 신뢰할 RDS CA bundle 지정
- `--ssl-verify-server-cert`: 접속한 DB server의 인증서 검증

### 6. Database와 table 준비

RDS 생성 화면에서 Initial database name을 `care`로 입력했다. `care` database를 선택한 뒤 애플리케이션에서 사용할 `member`, `board` table을 생성한다.

```sql
USE care;

CREATE TABLE member (
    id varchar(20),
    pw varchar(200),
    username varchar(99),
    postcode varchar(5),
    address varchar(1000),
    detailaddress varchar(100),
    mobile varchar(15),
    PRIMARY KEY (id)
) DEFAULT CHARSET = UTF8;

CREATE TABLE board (
    no int,
    title varchar(200),
    content varchar(9999),
    id varchar(20),
    writedate varchar(100),
    hits int(11),
    filename varchar(1000),
    PRIMARY KEY (no)
) DEFAULT CHARSET = UTF8;

SHOW TABLES;
```

`SHOW TABLES;` 결과에 `member`, `board`가 표시되는지 확인한다.

### 7. 애플리케이션용 DB 계정 생성

master account를 애플리케이션에 직접 넣지 않고, `care` database 전용 계정을 만든다.

```sql
CREATE USER 'web'@'%' IDENTIFIED BY '<새 비밀번호>';
GRANT ALL PRIVILEGES ON care.* TO 'web'@'%';
```

이미 `web` 계정을 만들었다면 password를 교체한다.

```sql
ALTER USER 'web'@'%' IDENTIFIED BY '<새 비밀번호>';
```

> [!warning] password는 노트, Git, 스크린샷에 남기지 않는다
> 예시에는 `<REDACTED>` 또는 `<새 비밀번호>`만 적는다.

> [!note] `GRANT ALL PRIVILEGES`는 수업용 범위다
> 재현이 우선인 실습에서는 `care.*` 범위에 한정해 사용했다. 실제 서비스에서는 애플리케이션이 필요한 작업만 확인해 권한을 더 줄인다.

### 8. `web` 계정으로 RDS 접속 확인

```bash
mysql \
  --connect-timeout=5 \
  -h <RDS endpoint> \
  -P 3306 \
  -u web \
  -p \
  --ssl-verify-server-cert \
  --ssl-ca="$HOME/global-bundle.pem" \
  care \
  -e 'SELECT 1;'
```

`1`이 출력되면 EC2에서 RDS까지의 network path, `web` 인증, `care` database 접근 권한을 확인한 것이다.

### 9. Tomcat에서 사용할 RDS CA bundle 설치

MariaDB CLI 접속과 `boot.war`의 JDBC 접속은 별도 client다. CLI가 성공했더라도 애플리케이션 JDBC URL도 TLS를 사용하도록 구성해야 한다.

```bash
sudo install -m 0640 -o root -g tomcat \
  "$HOME/global-bundle.pem" \
  /opt/tomcat/rds-global-bundle.pem
```

### 10. `application.properties` 수정

Tomcat이 펼친 애플리케이션 설정 파일을 수정한다.

```bash
sudoedit /opt/tomcat/current/webapps/boot/WEB-INF/classes/application.properties
```

```properties
spring.datasource.url=jdbc:mariadb://<RDS endpoint>:3306/care?sslMode=verify-full&serverSslCert=/opt/tomcat/rds-global-bundle.pem
spring.datasource.username=web
spring.datasource.password=<REDACTED>
```

- `/care`: 접속할 database 이름
- `?`: JDBC URL query option 시작
- `sslMode=verify-full`: TLS 암호화, CA 검증, hostname 검증
- `&`: 다음 option 연결
- `serverSslCert=/opt/tomcat/rds-global-bundle.pem`: 검증에 사용할 RDS CA bundle 경로

> [!warning] 펼쳐진 디렉터리의 설정은 다시 배포하면 덮어쓸 수 있다
> `boot.war`를 다시 배포하면 `/opt/tomcat/current/webapps/boot/`가 다시 생성될 수 있다. 재배포 후에는 properties 수정 여부를 다시 확인한다.

### 11. Tomcat 재시작과 최종 확인

```bash
sudo systemctl restart tomcat
sleep 10
curl -i http://127.0.0.1:8080/boot/boardForm
```

외부 브라우저에서도 현재 EC2 public IPv4로 접속한다.

```text
http://<EC2 public IPv4>:8080/boot/boardForm
```

> [!summary] 관찰된 성공
> 2026-06-02에 `http://3.39.190.74:8080/boot/boardForm` 접속을 확인했다.

## 이번 실습 트러블슈팅

이번 실습에서는 EC2에 Tomcat과 `boot.war`를 배포하고, 별도로 생성한 RDS for MariaDB와 연결했다. 문제를 해결할 때는 한 번에 설정을 바꾸지 않고, 아래 계층을 순서대로 분리해서 확인했다.

```text
브라우저
  -> EC2 Security Group
  -> EC2의 Tomcat:8080
  -> boot.war 애플리케이션
  -> JDBC 연결
  -> RDS Security Group
  -> RDS for MariaDB
```

> [!important] HTTP 오류와 connection timeout은 같은 문제가 아니다
> `connection timeout`은 요청이 서버 애플리케이션까지 도달하지 못했다는 뜻이다. 반면 `HTTP 500`은 요청이 Tomcat과 애플리케이션까지 도달했지만, 애플리케이션 내부 처리 중 오류가 발생했다는 뜻이다.

### EC2에서 MariaDB 서버를 설치하지 않는다

이번 구성에서 DB 서버는 EC2가 아니라 RDS다. EC2에는 Tomcat과 `boot.war`가 있고, RDS에는 MariaDB 서버와 실제 데이터가 있다.

| 위치 | 역할 |
| --- | --- |
| EC2 | Tomcat, `boot.war`, 점검용 MariaDB CLI client |
| RDS | MariaDB server, `care` database |

따라서 EC2에는 접속 점검용 client만 설치하면 된다.

```bash
sudo apt update
sudo apt install -y mariadb-client
```

EC2에 MariaDB server를 직접 설치하지 않았으므로 아래 명령도 실행하지 않는다.

```bash
sudo sed -i 's/bind-address.*/bind-address = 0.0.0.0/' \
  /etc/mysql/mariadb.conf.d/50-server.cnf
```

`bind-address`는 직접 운영하는 MariaDB server가 어느 주소에서 접속을 받을지 정하는 설정이다. RDS의 접속 허용 범위는 EC2 내부 설정 파일이 아니라 RDS Security Group에서 제어한다.

### 외부 브라우저에서 EC2의 8080 포트에 접속하지 못함

#### 관찰

EC2 내부에서는 Tomcat과 `boot.war`에 접속할 수 있었다.

```text
http://127.0.0.1:8080/
http://127.0.0.1:8080/boot/
```

하지만 외부 브라우저에서는 아래 주소가 `connection timeout`으로 실패했다.

```text
http://<EC2 public IPv4>:8080/boot/
```

당시 EC2 Security Group의 inbound rule에는 `22`, `80`, `443`만 있었고 `8080`은 없었다.

#### 해석

Tomcat과 애플리케이션은 EC2 내부에서 정상 동작했다. 외부 요청만 EC2에 들어오지 못했으므로 애플리케이션 문제가 아니라 EC2 Security Group 문제였다.

#### 해결

EC2 Security Group에 실습용 inbound rule을 추가했다.

| Type | Protocol | Port | Source |
| --- | --- | --- | --- |
| Custom TCP | TCP | `8080` | 접속할 IP 또는 수업에서 요구한 범위 |

> [!warning] `0.0.0.0/0`은 실습 후 정리한다
> `0.0.0.0/0`은 모든 IPv4 주소에서 접근할 수 있다는 뜻이다. 수업에서 임시로 사용했다면 실습 종료 후 제거하거나 필요한 IP 범위로 줄인다.

### EC2에서 RDS 접속을 시도했지만 응답을 기다림

#### 관찰

EC2에서 아래 명령으로 RDS 접속을 시도했다.

```bash
mysql \
  -h <RDS endpoint> \
  -u admin \
  -p
```

비밀번호 입력 후 즉시 접속되지 않았다. 당시 RDS Security Group은 사용자의 PC public IP 한 개만 `/32`로 허용하고 있었다.

#### 해석

`/32`는 단일 IP만 허용한다는 뜻이다. 사용자의 PC에서 RDS에 직접 접근할 때와 EC2에서 RDS에 접근할 때는 출발지가 다르다. PC public IP만 허용한 규칙은 EC2의 접속을 허용하지 않는다.

#### 해결

RDS Security Group의 `3306` inbound rule에 EC2가 사용하는 Security Group을 source로 추가했다.

| Type | Protocol | Port | Source |
| --- | --- | --- | --- |
| MYSQL/Aurora | TCP | `3306` | EC2 Security Group ID |

> [!important] IP보다 Security Group 참조가 재구축에 유리하다
> EC2의 일반 public IPv4는 `stop` 후 `start`하거나 instance를 다시 만들면 바뀔 수 있다. RDS rule의 source를 EC2 Security Group으로 지정하면 instance의 IP가 바뀌어도 같은 Security Group을 사용하는 EC2만 접근할 수 있다.

### DB 계정의 host를 EC2 public IP로 한정하면 재구축에 취약함

처음에는 EC2 public IPv4를 host로 지정하는 방식을 검토했다.

```sql
CREATE USER 'web'@'<EC2 public IPv4>' IDENTIFIED BY '<REDACTED>';
```

하지만 같은 VPC 안의 EC2에서 RDS로 접속하면 DB server가 EC2 public IPv4를 접속 host로 식별한다고 전제할 수 없다. 게다가 EC2 public IPv4는 고정된 식별자도 아니다. 이번 실습처럼 Security Group으로 접근 범위를 제한한다면, 실습용 계정은 다음처럼 만들 수 있다.

```sql
CREATE USER 'web'@'%' IDENTIFIED BY '<새 비밀번호>';
GRANT ALL PRIVILEGES ON care.* TO 'web'@'%';
```

`'web'@'%'`는 MariaDB 인증 계층에서는 모든 host에서 로그인을 시도할 수 있다는 뜻이다. 따라서 이것만 단독으로 쓰는 것이 아니라, RDS Security Group의 `3306` source를 EC2 Security Group으로 제한하는 네트워크 통제와 함께 사용한다.

> [!warning] 노출된 DB 비밀번호는 교체한다
> 트러블슈팅 과정에서 `application.properties`를 출력하면서 실습용 DB 비밀번호가 로그에 노출됐다. 최종 노트와 스크린샷에는 실제 값을 남기지 않고 `<REDACTED>`로 처리한다. RDS 계정의 비밀번호도 새 값으로 변경한다.

### CLI 접속은 성공했지만 웹 요청은 HTTP 500으로 실패함

#### 관찰

EC2에서 `web` 계정으로 `care` database에 접속해 쿼리를 실행할 수 있었다.

```bash
mysql \
  --connect-timeout=5 \
  -h <RDS endpoint> \
  -u web \
  -p \
  care \
  -e 'SELECT 1;'
```

결과로 `1`이 반환됐다. 즉, 아래 항목은 정상임을 확인했다.

| 확인 항목 | 결과 |
| --- | --- |
| EC2에서 RDS endpoint DNS 해석 | 정상 |
| EC2에서 RDS `3306` 접근 | 정상 |
| `web` 계정 인증 | 정상 |
| `care` database 접근 권한 | 정상 |

### AWS Console에 표시된 CLI TLS 접속 옵션

RDS Console의 `연결 및 보안` 탭에는 CA bundle을 내려받고 인증서를 검증하며 접속하는 예시도 표시됐다.

```bash
curl -o global-bundle.pem \
  https://truststore.pki.rds.amazonaws.com/global/global-bundle.pem

mysql \
  -h <RDS endpoint> \
  -P 3306 \
  -u admin \
  -p \
  --ssl-verify-server-cert \
  --ssl-ca=/home/ubuntu/global-bundle.pem
```

| 옵션 | 역할 |
| --- | --- |
| `--ssl-ca=/home/ubuntu/global-bundle.pem` | RDS 서버 인증서를 검증할 때 신뢰할 Amazon RDS CA bundle을 지정한다. 이 옵션은 TLS 연결도 활성화한다. |
| `--ssl-verify-server-cert` | 접속한 DB 서버가 제시한 인증서를 검증한다. |

AWS Console의 예시는 `--ssl-ca=./global-bundle.pem`처럼 현재 디렉터리를 기준으로 한 상대 경로를 보여줬다. EC2에서 재사용할 명령에는 현재 위치에 따라 깨지지 않도록 절대 경로를 적었다.

> [!note] CLI 옵션과 JDBC 옵션은 적용 위치가 다르다
> `--ssl-verify-server-cert --ssl-ca=...`는 터미널에서 `mysql` 또는 `mariadb` client로 수동 접속을 검증할 때 사용한다. `boot.war`는 CLI가 아니라 MariaDB Connector/J로 접속하므로 `application.properties`에는 아래의 JDBC URL 옵션을 별도로 넣어야 한다.

하지만 브라우저에서 게시판 기능을 요청하면 애플리케이션은 `HTTP 500`을 반환했다. Tomcat 로그의 핵심 오류는 다음과 같았다.

```text
org.springframework.jdbc.CannotGetJdbcConnectionException:
Failed to obtain JDBC Connection

Caused by: java.sql.SQLNonTransientConnectionException:
Connections using insecure transport are prohibited while
--require_secure_transport=ON.
```

#### 원인

RDS for MariaDB는 `require_secure_transport=ON` 상태였다. 따라서 client는 TLS로 암호화된 연결을 사용해야 한다.

MariaDB CLI client는 RDS와 TLS 연결을 성립시켜 `SELECT 1`에 성공했다. 반면 `boot.war`의 JDBC URL에는 TLS 옵션이 없었다.

```properties
spring.datasource.url=jdbc:mariadb://<RDS endpoint>:3306/care
```

애플리케이션에 포함된 MariaDB Connector/J는 평문 연결을 시도했고, RDS가 이를 거절했다. 그 결과 MyBatis가 DB connection을 얻지 못하면서 게시판 쿼리가 실패하고 `HTTP 500`이 발생했다.

#### 적용할 해결 방법

RDS의 TLS 요구를 끄지 않고, 애플리케이션이 RDS CA certificate를 검증하며 TLS로 연결하도록 수정한다.

```bash
curl --fail --silent --show-error --location \
  https://truststore.pki.rds.amazonaws.com/global/global-bundle.pem \
  --output /tmp/global-bundle.pem

sudo install -m 0640 -o root -g tomcat \
  /tmp/global-bundle.pem \
  /opt/tomcat/rds-global-bundle.pem
```

`application.properties`의 JDBC URL에는 TLS 검증 옵션을 추가한다.

```properties
spring.datasource.url=jdbc:mariadb://<RDS endpoint>:3306/care?sslMode=verify-full&serverSslCert=/opt/tomcat/rds-global-bundle.pem
spring.datasource.username=web
spring.datasource.password=<REDACTED>
```

| 옵션                    | 역할                                 |
| --------------------- | ---------------------------------- |
| `sslMode=verify-full` | TLS 암호화, CA 검증, hostname 검증을 수행한다. |
| `serverSslCert`       | 검증에 사용할 Amazon RDS CA bundle의 경로다. |

#### Connector/J의 `sslMode` 네 단계

MariaDB Connector/J 3.x의 `sslMode`는 아래 네 단계다. TLS를 사용하는 단계만 세면 `trust`, `verify-ca`, `verify-full`의 세 가지다.

| `sslMode` | TLS 암호화 | CA 검증 | hostname 검증 | 의미 |
| --- | --- | --- | --- | --- |
| `disable` | X | X | X | 기본값이다. 현재 RDS처럼 `require_secure_transport=ON`이면 연결이 거절된다. |
| `trust` | O | X | X | 서버 인증서를 검증하지 않고 TLS만 사용한다. 빠른 연결 확인에는 쓸 수 있지만 연결 대상의 신원은 확인하지 않는다. |
| `verify-ca` | O | O | X | 신뢰한 CA가 발급한 인증서인지 검증한다. 접속한 hostname과 인증서의 이름이 일치하는지는 확인하지 않는다. |
| `verify-full` | O | O | O | CA와 hostname을 모두 검증한다. 재현 절차에서는 이 방식을 사용한다. |

> [!important] URL 문자열 수와 보안 단계 수는 다르다
> 수업 중 확인한 JDBC URL suffix는 세 가지지만, Connector/J의 보안 단계는 네 가지다. `serverSslCert`는 별도 보안 단계가 아니라 검증에 사용할 CA certificate를 지정하는 옵션이다.

#### `[강사님 방식]` 간단한 TLS 연결

강사님은 아래처럼 `sslMode=trust`만 추가해 연결했다.

```properties
spring.datasource.url=jdbc:mariadb://<RDS endpoint>:3306/care?sslMode=trust
```

이 방식은 TLS 암호화를 사용하므로 RDS의 `require_secure_transport=ON` 조건을 만족한다. 다만 CA와 hostname을 검증하지 않으므로, 수업 중 빠르게 연결을 확인할 때와 검증을 포함한 구성은 구분해야 한다.

#### `[용준님 방식]` 빠른 TLS 연결

같은 수업 환경에서 다음과 같이 TLS 옵션을 추가한 사례도 있었다.

```properties
spring.datasource.url=jdbc:mariadb://<RDS endpoint>:3306/care?useSSL=true&trustServerCertificate=true
```

| 옵션 | 역할 |
| --- | --- |
| `useSSL=true` | DB 연결에 TLS 암호화를 사용한다. |
| `trustServerCertificate=true` | 서버 인증서를 별도로 검증하지 않고 신뢰한다. |

이 방식도 RDS의 `require_secure_transport=ON` 조건을 만족시켜 연결 오류를 빠르게 해결할 수 있다. 보안 수준은 `[강사님 방식]`의 `sslMode=trust`와 같다. 하지만 레거시 옵션을 조합한 표기라서 새 설정에는 `sslMode`를 우선한다.

| 수업에서 확인한 JDBC URL suffix | 대응하는 보안 단계 | TLS 암호화 | CA 검증 | hostname 검증 | 용도 |
| --- | --- | --- | --- | --- | --- |
| `[강사님 방식]` `sslMode=trust` | `trust` | O | X | X | 수업 중 빠른 연결 확인 |
| `[용준님 방식]` `useSSL=true&trustServerCertificate=true` | `trust`와 같은 수준 | O | X | X | 레거시 표기와의 비교 |
| `sslMode=verify-full&serverSslCert=...` | `verify-full` | O | O | O | 검증을 포함한 재현 절차 |

> [!note] Connector/J 옵션 표기
> MariaDB Connector/J 3.x 문서는 `sslMode`를 사용한다. `useSsl`과 `trustServerCertificate`는 이전 버전과의 호환을 위한 deprecated 옵션이다. 수업 중 확인한 문자열은 `useSSL=true`였고, 공식 문서에는 `useSSL`도 `useSsl`의 alias로 표시된다.

설정 변경 후 Tomcat을 다시 시작하고 로컬 응답부터 확인한다.

```bash
sudo systemctl restart tomcat
sleep 10
curl -i http://127.0.0.1:8080/boot/
```

#### 해결 확인

JDBC TLS 옵션을 추가한 뒤 Tomcat을 재시작했다. 2026-06-02에 외부 브라우저에서 아래 URL의 게시판 작성 화면까지 접속되는 것을 확인했다.

```text
http://3.39.190.74:8080/boot/boardForm
```

> [!note] 현재 runtime에 적용된 suffix를 따로 확인하려면
> 아래 명령으로 Tomcat이 읽는 `application.properties`의 JDBC URL을 확인한다. 비밀번호는 출력하지 않는다.
>
> ```bash
> sudo grep '^spring.datasource.url=' \
>   /opt/tomcat/current/webapps/boot/WEB-INF/classes/application.properties
> ```

## 참고 자료

- [MariaDB Connector/J - Using TLS/SSL](https://mariadb.com/docs/connectors/mariadb-connector-j/using-tls-ssl-with-mariadb-java-connector)
- [MariaDB Connector/J - Connection options](https://mariadb.com/kb/en/about-mariadb-connector-j/)
- [Amazon RDS - Using SSL/TLS to encrypt a connection to a DB instance](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/UsingWithRDS.SSL.html)
- [Amazon RDS - Connecting an EC2 instance and a DB instance automatically](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/ec2-rds-connect.html)
- [Amazon EC2 - Control traffic to your AWS resources using security groups](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-security-groups.html)
