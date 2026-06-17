---
type: lab
topic: aws
source:
  - AWS기초.pdf
  - lab-observation
source_pages:
  - "82-85"
status: active
created: 2026-06-04
reviewed: 2026-06-05
aliases:
  - Web VPC와 DB 연계 실습
  - Web EC2와 EC2 MariaDB 연계 실습
  - Web VPC와 RDS 연계 실습
tags:
  - 🏷️과목/AWS
  - 🏷️주제/VPC
  - 🏷️주제/EC2
  - 🏷️주제/MariaDB
  - 🏷️주제/Tomcat
  - 🏷️주제/SecurityGroup
  - 🏷️상태/active
---

# Web VPC와 DB 연계 실습

## 실습 결과

> [!summary] Web EC2에서 DB EC2의 MariaDB로 연결하는 구조를 구성했다
> 원래 PDF 흐름은 Web VPC와 RDS 연계지만, 이번 실습에서는 비용과 단순화를 위해 RDS 대신 EC2에 MariaDB를 설치해 DB 서버로 사용했다. Web EC2는 Tomcat과 `boot.war`를 실행하고, DB EC2는 `care` database와 `member`, `board` table을 제공한다.

이번 실습에서 중요한 결론은 **브라우저가 DB에 직접 접근하는 것이 아니라, 브라우저 요청을 받은 Web EC2가 DB EC2의 private IP로 MariaDB에 접근한다**는 점이다.

```text
Browser
-> Web EC2 public IPv4:8080
-> Tomcat / boot.war
-> DB EC2 private IPv4:3306
-> MariaDB care database
```

> [!note] 관찰값은 인스턴스를 다시 만들면 바뀐다
> 아래 public IP, private IP, hostname은 해당 실습 시점의 관찰값이다. 볼륨 삭제나 instance 재생성 후에는 Console에서 현재 값을 다시 확인해서 properties, SSH config, Security Group source를 맞춘다.

## 현재 구성

| 역할 | 관찰값 / 설정 | 의미 |
| --- | --- | --- |
| Web EC2 | `ip-10-0-1-105`, public IPv4 `3.36.96.47` | 외부 브라우저가 `8080`으로 접근하는 서버 |
| DB EC2 | private IPv4 `10.0.2.186`, public IPv4 `54.180.226.59` 관찰 | MariaDB가 실행되는 DB 서버 |
| Web app | Tomcat `10.1.55`, `boot.war` | `/boot/` 경로로 배포되는 Spring app |
| Database | `care` | app이 사용하는 MariaDB database |
| DB user | `web` | app이 DB에 접속할 때 쓰는 계정 |
| DB port | TCP `3306` | Web EC2에서 DB EC2로 접근해야 하는 포트 |

> [!important] app properties에는 DB의 private IP를 넣는다
> 같은 VPC 내부의 Web EC2가 DB에 접근할 때는 DB EC2의 public IPv4가 아니라 private IPv4를 사용한다. 이번 관찰값 기준으로는 `10.0.2.186:3306`이다.

## 역할 구분

| 역할 | 핵심 기능 | 이번 실습에서 헷갈린 지점 |
| --- | --- | --- |
| Bastion EC2 | 외부에서 private server로 들어가기 위한 관리 접속 경유지 | DB에 SSH, ping을 하려면 DB SG가 Bastion SG를 허용해야 한다 |
| NAT EC2 | Private Subnet server가 인터넷으로 나가기 위한 outbound 경유지 | DB가 `8.8.8.8`로 나가는 문제와 Web이 DB에 붙는 문제는 다르다 |
| Web EC2 | 외부 브라우저 요청을 받고 Tomcat app을 실행 | `8080` inbound가 열려야 브라우저 timeout이 풀린다 |
| DB EC2 | MariaDB와 `care` database 제공 | Web에서 오는 `3306`은 필요하지만 DB의 `8080` inbound는 필요 없다 |

## 사용한 스크립트

- [[10_학습 노트/클라우드/AWS/ec2_tomcat_setup.sh|ec2_tomcat_setup.sh]]
  - Web EC2에 Java 17, Tomcat 10.1.55를 설치하고 `boot.war`를 배포한다.
  - application properties와 Security Group은 수정하지 않는다.
- [[10_학습 노트/클라우드/AWS/ec2_mariadb_setup.sh|ec2_mariadb_setup.sh]]
  - DB EC2에 MariaDB를 설치하고 `care` database, `member`, `board` table, `web` user를 준비한다.
  - MariaDB `bind-address`를 `0.0.0.0`으로 열어 원격 접속이 가능하게 한다.
  - EC2 Security Group은 수정하지 않는다.

## Security Group 구성

### Web Security Group

실습 중 Web EC2는 외부 브라우저 접속과 원격 접속 확인을 위해 여러 inbound rule을 열었다.

| Type | Port | Source | 목적 |
| --- | --- | --- | --- |
| SSH | `22` | `0.0.0.0/0` | 실습 중 VS Code / SSH 접속 |
| HTTP | `80` | `0.0.0.0/0` | 일반 HTTP 확인용 |
| HTTPS | `443` | `0.0.0.0/0` | HTTPS 확인용 |
| Custom TCP | `8080` | `0.0.0.0/0` | Tomcat `boot.war` 브라우저 접속 |
| ICMP | all | `0.0.0.0/0` | ping 확인 |

> [!warning] 실습 후에는 SSH와 8080을 넓게 열어둔 상태를 정리한다
> `0.0.0.0/0`은 모든 IPv4 주소에서 접근 가능하다는 뜻이다. 실습 중에는 빠르게 확인하기 위해 열 수 있지만, 정리 단계에서는 SSH는 내 IP로 제한하고, 8080은 더 이상 필요 없으면 닫는다.

### DB Security Group

DB EC2에는 최종적으로 Web EC2에서 MariaDB로 들어오는 traffic만 필요하다.

| Type | Port | Source | 판단 |
| --- | --- | --- | --- |
| MYSQL/Aurora | `3306` | Web Security Group | 필요 |
| SSH | `22` | Bastion Security Group | DB 서버에 직접 관리 접속할 때만 필요 |
| ICMP | all | Bastion Security Group | ping 검증용. 최종 서비스에는 필수 아님 |
| Custom TCP | `8080` | 임시 설정 | DB 서버에는 불필요 |

DB 서버의 inbound 정답은 보통 다음 한 줄이다.

```text
MYSQL/Aurora TCP 3306 Source = Web EC2의 Security Group
```

이렇게 하면 Web SG가 붙은 인스턴스만 DB EC2의 MariaDB 포트로 접근할 수 있다. DB에 `8080` inbound rule은 필요 없다.

> [!tip] 임시 디버깅용 SG를 따로 붙일 수 있다
> EC2에는 Security Group을 여러 개 붙일 수 있고, 허용 규칙은 합쳐진다. 실습 중에는 `db-final-sg`는 유지하고, `db-temp-debug-sg`에 `SSH`, `ICMP`, 임시 `All traffic from Bastion SG` 같은 규칙을 넣었다가 검증 후 제거하면 덜 헷갈린다.

## NAT EC2 준비

상세 절차는 [[NAT Instance 실습]]에 둔다. 이 실습에서 NAT EC2는 DB EC2 같은 private server가 외부 package repository나 인터넷 주소로 나갈 때 쓰는 outbound 경유지다.

NAT EC2에서 필요한 핵심 조건:

| 위치 | 설정 |
| --- | --- |
| EC2 Console | NAT EC2의 Source/Destination Check 중지 |
| Private Route Table | `0.0.0.0/0 -> NAT EC2` |
| NAT EC2 OS | `net.ipv4.ip_forward = 1` |
| NAT EC2 OS | `iptables` MASQUERADE |

> [!important] NAT와 Web -> DB 연결은 다른 문제다
> DB EC2에서 `8.8.8.8` ping이 안 되는 것은 NAT / route table / Source-Destination Check 문제다. Web EC2에서 DB EC2의 `3306`에 붙는 것은 DB SG, MariaDB listen, DB 계정 문제다.

## DB EC2 준비

Bastion에 먼저 DB 서버와 연결하기 위한 key file과 DB 서버에서 실행시킬 script를 준비한다. 그 다음 Bastion에서 DB 서버의 private IP로 script를 전송한다.

```bash
chmod 400 asd-close.pem
scp -i asd-close.pem ec2_mariadb_setup.sh ubuntu@<DB_PRIVATE_IP>:~/
```

> [!note] `scp` 목적지에는 `:`가 필요하다
> `ubuntu@10.0.2.186:~/`처럼 colon 뒤에 원격 경로를 적어야 remote copy가 된다. 로컬 PC에서 private IP로 직접 전송하는 것이 아니라 Bastion 안에서 DB private IP로 전송한다.

DB 서버에는 MariaDB를 설치하고 `care` database를 준비했다.

```bash
sudo bash ./ec2_mariadb_setup.sh
```

스크립트는 실행 중 MariaDB root password와 app user password를 입력받는다. 실제 password는 노트에 남기지 않는다.

DB script가 수행하는 핵심 작업은 다음과 같다.

```sql
CREATE DATABASE IF NOT EXISTS care;

CREATE TABLE IF NOT EXISTS member (...);
CREATE TABLE IF NOT EXISTS board (...);

CREATE USER IF NOT EXISTS 'web'@'%' IDENTIFIED BY '<DB_APP_PASSWORD>';
GRANT ALL PRIVILEGES ON care.* TO 'web'@'%';
```

> [!note] `web`@`%`는 DB 계정 범위를 넓게 잡는 방식이다
> app user host를 `%`로 두면 여러 host에서 같은 계정으로 접속할 수 있다. 대신 실제 접근 범위는 DB Security Group에서 Web SG 또는 Web private IP로 제한해야 한다.

## Web EC2 준비

Web EC2에는 Tomcat과 `boot.war`를 배포했다.

```bash
sudo bash ./ec2_tomcat_setup.sh
```

Tomcat이 실행 중인지 확인한다.

```bash
sudo systemctl status tomcat
sudo ss -lntp | grep 8080
```

브라우저 접속은 다음 형태다.

```text
http://<WEB_PUBLIC_IPV4>:8080/boot/
```

이번 관찰값 기준:

```text
http://3.36.96.47:8080/boot/
```

## application.properties 수정

Web app이 DB EC2를 보도록 `application.properties`를 수정한다.

```properties
spring.datasource.driver-class-name=org.mariadb.jdbc.Driver
spring.datasource.username=web
spring.datasource.password=<DB_APP_PASSWORD>
spring.datasource.url=jdbc:mariadb://10.0.2.186:3306/care
```

RDS가 아니라 EC2 MariaDB를 쓰는 현재 구조에서는 RDS 인증서나 `global-bundle.pem`은 필요하지 않다. TLS를 따로 구성하지 않았다면 먼저 위처럼 단순한 URL로 연결을 확인하는 편이 낫다.

> [!important] properties 수정 후 Tomcat을 반드시 재시작한다
> 배포된 app의 설정 파일을 수정해도 Tomcat을 재시작하지 않으면 실행 중인 app은 이전 설정을 계속 사용할 수 있다.

```bash
sudo systemctl restart tomcat
```

## 연결 검증

### 1. Bastion에서 DB 관리 접속 확인

Bastion에서 DB 서버의 private IP로 관리 접속이 되는지 먼저 확인한다.

```bash
ping -c 3 <DB_PRIVATE_IP>
ssh -i asd-close.pem ubuntu@<DB_PRIVATE_IP>
```

판정:

| 결과 | 의미 |
| --- | --- |
| ping 실패, SSH 성공 | ICMP만 막힌 것이다. 서비스 연결 문제는 아닐 수 있다 |
| SSH 실패 | DB SG의 `SSH 22 from Bastion SG`, key, username, subnet/VPC를 확인한다 |
| 둘 다 실패 | 같은 VPC인지, DB private IP가 맞는지, DB SG/NACL을 확인한다 |

### 2. Web 포트 확인

로컬 PC에서 Web EC2 public IPv4의 `8080`이 열렸는지 확인한다.

```powershell
Test-NetConnection 3.36.96.47 -Port 8080
```

브라우저에서 connection timeout이 뜨면 주로 Web SG의 `8080` inbound, public subnet route table, public IPv4를 확인한다.

### 3. Web에서 DB 포트 확인

Web EC2에서 DB EC2의 private IP와 port를 확인한다.

```bash
nc -vz 10.0.2.186 3306
```

`nc`가 없으면 진단용으로만 설치한다.

```bash
sudo apt-get update
sudo apt-get install -y netcat-openbsd
```

### 4. Web에서 DB login 확인

DB client는 app 실행에 필수는 아니지만, 장애 진단에 유용하다.

```bash
mysql -h 10.0.2.186 -u web -p -D care -e "show tables;"
```

이 명령이 성공하면 다음이 함께 확인된다.

| 확인 항목 | 의미 |
| --- | --- |
| Web -> DB network | Security Group, route, MariaDB listen 상태가 큰 틀에서 맞음 |
| DB user | `web` 계정으로 login 가능 |
| DB name | `care` database 존재 |
| table | `member`, `board` 등 app이 기대하는 table 존재 여부 확인 가능 |

## 이번 실습 트러블슈팅

### 외부 접속 timeout

브라우저에서 다음 주소가 connection timeout이었다.

```text
http://3.36.96.47:8080/
```

이 경우 Tomcat app 문제가 아니라 보통 외부에서 Web EC2의 `8080`까지 도달하지 못한 것이다. Web Security Group에 TCP `8080` inbound rule을 추가해야 한다. HTTP `80` rule과 Tomcat `8080` rule은 서로 다르다.

### HTTP 500

`8080`을 열고 나면 timeout 대신 HTTP 500이 발생했다. 이는 네트워크 외부 접근은 통과했고, app 내부에서 예외가 발생했다는 뜻이다.

Tomcat log에서 확인된 핵심 에러는 다음이었다.

```text
Failed to obtain JDBC Connection
Socket fail to connect to host:address=(host=localhost)(port=3306)
Connection refused
```

이 에러는 app이 DB EC2가 아니라 Web EC2 자기 자신의 `localhost:3306`으로 접속하려 했다는 뜻이다.

원인 판단:

```text
application.properties 수정 후 Tomcat restart를 하지 않음
-> 실행 중인 app은 이전 localhost 설정을 계속 사용
-> localhost:3306에 MariaDB가 없어서 connection refused
-> MyBatis query 시점에 HTTP 500 발생
```

조치:

```bash
sudo systemctl restart tomcat
sudo journalctl -u tomcat -n 80 --no-pager
```

새 로그에서 `localhost:3306`이 사라지고 `10.0.2.186:3306` 기준의 에러로 바뀌면, properties 반영은 된 것이다. 그 이후 에러는 Security Group, DB 계정, password, database/table 문제로 분리해서 본다.

### Web에 DB client를 설치해야 하는가

Web EC2에 `mysql` 또는 `mariadb-client`가 없어도 app은 실행될 수 있다. Spring app은 shell의 `mysql` 명령어가 아니라 WAR 내부의 JDBC driver로 DB에 연결한다.

다만 DB client는 다음을 확인하기 위한 진단 도구로 유용하다.

```bash
mysql -h 10.0.2.186 -u web -p -D care -e "show tables;"
```

즉:

```text
DB client 설치 = 500 해결책 아님
DB client 설치 = DB 연결 진단 도구
```

### DB에서 8.8.8.8 ping 실패

DB EC2에서 `8.8.8.8` ping이 실패한다고 해서 Web app의 DB 연결이 반드시 실패하는 것은 아니다.

- Web app 연결: Web EC2 -> DB EC2 private IP `10.0.2.186:3306`
- DB outbound 인터넷: DB EC2 -> NAT / IGW -> Internet

두 흐름은 다르다. Web에서 DB의 `3306`에 붙는 문제는 DB Security Group, MariaDB bind-address, VPC 내부 route가 핵심이고, DB가 인터넷으로 나가는 문제는 NAT, IGW, route table, public IP가 핵심이다.

### 다른 subnet끼리 통신이 안 되는 것처럼 보임

같은 VPC 안의 subnet끼리는 route table에 기본 `local` route가 있어서 원래 통신된다. 통신이 안 되면 "subnet이 달라서"라기보다 다음을 먼저 확인한다.

| 확인 | 판단 |
| --- | --- |
| Bastion VPC ID와 DB VPC ID가 같은가 | 다르면 private IP 통신 경로 자체가 다름 |
| DB private IP로 접속 중인가 | public IP나 예전 IP를 쓰면 판정이 꼬임 |
| DB SG가 Bastion SG를 허용하는가 | 완성 후 DB SG가 Web `3306`만 허용하면 Bastion SSH/ping은 막힘 |
| NACL이 기본값인가 | custom NACL이면 양방향 rule이 필요 |

이번에 막힌 이유는 DB SG가 완성 후 상태를 기준으로 만들어져 Bastion의 SSH/ICMP 검증 traffic을 허용하지 않았기 때문이다.

## 비용 정리 체크리스트

> [!warning] 계정 콘솔을 직접 확인한 것이 아니므로, 아래 항목이 모두 정리되어야 "추가 과금 위험이 낮다"고 볼 수 있다
> AWS는 실행 중인 compute뿐 아니라 남은 storage, public IPv4, NAT Gateway, snapshot 같은 주변 리소스에서도 비용이 발생할 수 있다.

실습 종료 전 확인할 항목:

| Console 위치 | 확인할 것 | 비용 판단 |
| --- | --- | --- |
| EC2 > Instances | Web, DB, NAT, Bastion 등 실습 instance | 끝났으면 `Terminate`. `Stop`은 instance hour는 멈추지만 EBS 비용은 남음 |
| EC2 > Volumes | 남은 EBS volume | `available` 상태로 남은 volume도 storage 비용 발생 가능. 필요 없으면 삭제 |
| EC2 > Snapshots | 직접 만든 snapshot | snapshot storage 비용 발생 가능. 필요 없으면 삭제 |
| EC2 > Elastic IPs | 할당된 Elastic IP | 연결 여부와 관계없이 public IPv4 비용 발생 가능. 필요 없으면 release |
| VPC > NAT Gateways | NAT Gateway | 시간당 비용과 처리량 비용 발생. 실습 후 반드시 삭제 |
| RDS > Databases | RDS instance | stopped여도 storage/backup/public IPv4 비용 가능. 필요 없으면 snapshot 여부 결정 후 delete |
| RDS > Snapshots | manual snapshot | snapshot storage 비용 가능. 필요 없으면 삭제 |
| EC2 > Load Balancers | ALB / ELB | 아직 만들지 않았으면 해당 없음. 만들었다면 시간당 비용 가능 |

과금과 거의 무관하게 남겨도 되는 구성 요소:

| 리소스 | 판단 |
| --- | --- |
| VPC | 자체는 보통 직접 과금 대상 아님 |
| Subnet | 자체는 보통 직접 과금 대상 아님 |
| Route Table | 자체는 보통 직접 과금 대상 아님 |
| Security Group | 자체는 보통 직접 과금 대상 아님 |
| Internet Gateway | 자체는 보통 직접 과금 대상 아님 |
| Key Pair | 자체는 보통 직접 과금 대상 아님 |

이번 실습에서 특히 조심할 것:

1. DB EC2에 public IPv4가 붙어 있었으므로, 계속 실행 중이면 EC2 instance 비용과 public IPv4 비용이 같이 날 수 있다.
2. EC2를 terminate해도 EBS volume이 남아 있으면 storage 비용이 계속 날 수 있다.
3. NAT Gateway를 만들었다면 NAT Instance와 달리 별도 관리형 리소스 비용이 크므로 반드시 삭제한다.
4. RDS를 만들었다가 EC2 DB로 갈아탄 경우, RDS instance와 snapshot이 남아 있는지 확인한다.

## 참고 자료

- AWS Docs, Delete an Amazon EBS volume: EBS volume은 attached 상태에서는 삭제할 수 없고, `available` 상태에서 삭제해야 한다.
- AWS Docs, Stop Amazon RDS DB instance temporarily: RDS는 stopped 상태에서도 provisioned storage, backup storage, public IPv4 비용이 남을 수 있다.
- AWS Docs, Pricing for NAT gateways: NAT Gateway는 사용 가능한 시간과 처리한 데이터 양에 대해 비용이 발생한다.
- AWS VPC Pricing: public IPv4 address는 사용 중이거나 idle 상태여도 시간당 비용이 발생할 수 있다.
