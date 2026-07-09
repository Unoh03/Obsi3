---
title: Terraform RDS 인프라 구성 실습
version: v7.0
created: 2026-07-09
status: active
type: lab-note
source:
  - Terraform AWS CLI 초기 설정 실습 v6.3.md
  - Terraform RDS 실습 노트 재료 v0.1.md
  - 02_rds/main.tf
  - user_data/00-common.sh
  - user_data/20-web-install.sh.tftpl
  - conversation-log
official_refs:
  - https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_VPC.WorkingWithRDSInstanceinaVPC.html
  - https://docs.aws.amazon.com/vpc/latest/userguide/vpc-security-groups.html
  - https://developer.hashicorp.com/terraform/language/functions/templatefile
  - https://developer.hashicorp.com/terraform/language/meta-arguments/depends_on
tags:
  - 과목/AWS
  - 주제/IaC
  - 주제/Terraform
  - 주제/RDS
  - 주제/SecurityGroup
  - 상태/active
  - 실습/Terraform
---

# Terraform RDS 인프라 구성 실습 v7.0

## 목적

이 노트는 기존 `v6.3`의 **Public Web + Private DB EC2** 구조를 **Public Web + Private RDS MariaDB** 구조로 전환한 실습 기록이다.

핵심 목표는 다음이다.

```text
기존:
Public WEB EC2
→ Private DB EC2
→ DB EC2 내부에 MariaDB 직접 설치

이번:
Public WEB EC2
→ Private RDS MariaDB
→ DB 엔진과 DB 서버 운영체제는 AWS RDS가 관리
```

이번 버전의 초점은 **RDS 인프라 생성, DB subnet group 요구사항 검증, Terraform 시행착오 정리**다.

> [!important] v7.0의 범위
> v7.0은 RDS 인프라 구성과 apply 성공까지를 다룬다.  
> `/db-test.php`를 통한 실제 INSERT/SELECT 검증과 브라우저 스크린샷 확보는 v7.1에서 추가한다.

---

## 출처 구분

```text
① 내장 지식:
- Terraform dependency graph 해석
- VPC/Subnet/Route Table/Security Group/RDS 구조 해석

② 인터넷 고신뢰 정보:
- AWS RDS 공식 문서
- AWS VPC Security Group 공식 문서
- HashiCorp Terraform 공식 문서

③ 인터넷 비공식 고품질 의견:
- 사용 안 함

④ 업로드/실습 자료:
- Terraform AWS CLI 초기 설정 실습 v6.3.md
- Terraform RDS 실습 노트 재료 v0.1.md
- 현재 02_rds/main.tf
- user_data/00-common.sh
- user_data/20-web-install.sh.tftpl
- 실습 중 발생한 Terraform 오류 로그
```

---

## 빠른 이동

> [!abstract] 주요 이동
> - [[#1. v6.3에서 v7.0으로 바뀐 점|1. v6.3에서 v7.0으로 바뀐 점]]
> - [[#2. 최종 아키텍처|2. 최종 아키텍처]]
> - [[#3. RDS DB subnet group의 2AZ 요구사항|3. RDS DB subnet group의 2AZ 요구사항]]
> - [[#4. 시행착오 1 `aws_db_instance`에 subnet ID를 직접 넣으려 한 오류|4. 시행착오 1]]
> - [[#5. 시행착오 2 `templatefile()` 파일 경로 오류|5. 시행착오 2]]
> - [[#6. 시행착오 3 RDS master password 길이 오류|6. 시행착오 3]]
> - [[#7. 시행착오 4 subnet 1개 DB subnet group 실패|7. 시행착오 4]]
> - [[#8. RDS endpoint와 `templatefile()`|8. RDS endpoint와 templatefile]]
> - [[#9. Terraform implicit dependency와 `depends_on`|9. implicit dependency]]
> - [[#10. Security Group stateful 동작|10. Security Group stateful]]
> - [[#11. 현재 코드 검토|11. 현재 코드 검토]]
> - [[#12. v7.0 완료 판정|12. v7.0 완료 판정]]
> - [[#13. v7.1 예정 범위|13. v7.1 예정 범위]]
> - [[#부록 A. 현재 `main.tf`|부록 A. 현재 main.tf]]
> - [[#부록 B. 현재 `00-common.sh`|부록 B. 현재 00-common.sh]]
> - [[#부록 C. 현재 `20-web-install.sh.tftpl`|부록 C. 현재 20-web-install.sh.tftpl]]

---

# 1. v6.3에서 v7.0으로 바뀐 점

## 1-1. v6.3 구조

v6.3에서는 Public Subnet에 WEB EC2, Private Subnet에 DB EC2를 배치했다.

```text
외부 사용자
→ Public WEB EC2
→ Private DB EC2
→ MariaDB 직접 설치
```

DB 서버는 EC2였으므로 다음 작업을 `user_data/10-db-install.sh`에서 수행했다.

```text
- MariaDB 패키지 설치
- MariaDB service enable/start
- bind-address 설정
- appdb 생성
- webuser 생성
- connection_test 테이블 생성
- WEB → DB INSERT/SELECT 검증
```

## 1-2. v7.0 구조

v7.0에서는 Private DB EC2를 제거하고 RDS MariaDB로 대체한다.

```text
외부 사용자
→ Public WEB EC2
→ Private RDS MariaDB
```

RDS에서는 DB 서버 운영체제에 직접 접근하지 않는다.  
따라서 기존처럼 DB EC2에 SSH로 들어가 `dnf install mariadb105-server`를 실행하는 구조가 아니다.

변경 사항:

| 항목 | v6.3 | v7.0 |
|---|---|---|
| DB 구현 | Private EC2 + MariaDB 직접 설치 | Amazon RDS MariaDB |
| DB 서버 `user_data` | 있음 | 없음 |
| DB subnet | private subnet 1개 | RDS DB subnet group용 private subnet 2개 |
| DB 접속 주소 | 고정 private IP `192.168.10.13` | RDS DNS endpoint |
| DB 보안 그룹 | `close_sg` | `rds_sg` |
| DB 테이블 생성 | DB EC2 user_data에서 생성 | v7.1에서 검증 예정. 현재 PHP 코드에는 `CREATE TABLE IF NOT EXISTS` 포함 |

---

# 2. 최종 아키텍처

## 2-1. 리소스 구조

```text
VPC 10.20.0.0/16
├─ Public Subnet A       10.20.1.0/24   ap-northeast-2a
│  └─ WEB EC2
│     ├─ Private IP: 10.20.1.13
│     ├─ Public IP: 자동 할당
│     ├─ Apache httpd
│     ├─ PHP-FPM
│     └─ db-test.php
│
├─ Private DB Subnet A   10.20.10.0/24  ap-northeast-2a
│  └─ RDS subnet group member
│
└─ Private DB Subnet C   10.20.11.0/24  ap-northeast-2c
   └─ RDS subnet group member
```

## 2-2. 통신 흐름

```text
외부 사용자
→ WEB EC2:80
→ Apache/PHP
→ RDS endpoint:3306
→ RDS MariaDB
```

## 2-3. 핵심 Terraform 리소스

| 역할 | Terraform resource |
|---|---|
| VPC | `aws_vpc.terra_vpc` |
| Internet Gateway | `aws_internet_gateway.gw` |
| Public Subnet | `aws_subnet.terra_open_subnet` |
| Private DB Subnet A | `aws_subnet.terra_close_subnet` |
| Private DB Subnet C | `aws_subnet.terra_close_subnet2` |
| DB Subnet Group | `aws_db_subnet_group.terra_rds_subnet_group` |
| RDS MariaDB | `aws_db_instance.terra_rds` |
| WEB EC2 | `aws_instance.terra_WEB` |
| WEB SG | `aws_security_group.open_sg` |
| RDS SG | `aws_security_group.rds_sg` |

---

# 3. RDS DB subnet group의 2AZ 요구사항

## 3-1. 새로 확정한 점

이번 실습에서 가장 중요한 학습 포인트는 이것이다.

```text
RDS DB Instance가 1개라는 것과,
DB subnet group이 최소 2개 AZ를 커버해야 한다는 것은 별개다.
```

즉 다음은 동시에 성립한다.

```text
RDS DB instance 수:
1개

RDS 배포 형태:
Single-AZ

Terraform 설정:
multi_az = false

DB subnet group:
서로 다른 AZ의 subnet 2개 필요
```

## 3-2. 왜 private subnet을 하나 더 만들었는가

처음에는 실습 그림처럼 `Public Subnet 1개 + Private Subnet 1개`만 두려 했다.

하지만 RDS DB subnet group은 일반 Region에서 최소 2개 AZ의 subnet을 요구한다.  
따라서 실제 Terraform 구현에서는 private DB subnet을 하나 더 추가했다.

```hcl
resource "aws_subnet" "terra_close_subnet2" {
  vpc_id                  = aws_vpc.terra_vpc.id
  cidr_block              = "10.20.11.0/24"
  availability_zone       = "ap-northeast-2c"
  map_public_ip_on_launch = false
}
```

그리고 DB subnet group에 두 subnet을 모두 넣었다.

```hcl
resource "aws_db_subnet_group" "terra_rds_subnet_group" {
  name = "terra-rds-subnet-group"

  subnet_ids = [
    aws_subnet.terra_close_subnet.id,
    aws_subnet.terra_close_subnet2.id
  ]
}
```

## 3-3. 보고서용 문장

```text
실습 그림은 Public Web 영역과 Private DB 영역의 논리 구조를 단순화한 것이다.
Amazon RDS는 Single-AZ DB instance를 생성하더라도 DB subnet group 구성을 위해 서로 다른 Availability Zone의 subnet을 최소 2개 요구한다.
따라서 본 실습에서는 RDS DB instance는 1개로 구성하되, Private DB Subnet은 ap-northeast-2a와 ap-northeast-2c에 각각 1개씩 생성하였다.
```

---

# 4. 시행착오 1: `aws_db_instance`에 subnet ID를 직접 넣으려 한 오류

## 4-1. 잘못된 접근

처음에는 RDS instance에 subnet ID를 직접 넣으려 했다.

```hcl
db_subnet_names = [aws_subnet.terra_close_subnet.id]
```

## 4-2. 문제

`aws_db_instance`에는 `db_subnet_names`라는 argument가 없다.

또한 RDS instance는 subnet ID를 직접 받는 구조가 아니다.  
Subnet ID 목록은 DB subnet group에 들어가야 한다.

## 4-3. 올바른 구조

```text
subnet id
→ aws_db_subnet_group.subnet_ids
→ aws_db_instance.db_subnet_group_name
```

올바른 예:

```hcl
resource "aws_db_subnet_group" "terra_rds_subnet_group" {
  name = "terra-rds-subnet-group"

  subnet_ids = [
    aws_subnet.terra_close_subnet.id,
    aws_subnet.terra_close_subnet2.id
  ]
}
```

```hcl
resource "aws_db_instance" "terra_rds" {
  db_subnet_group_name = aws_db_subnet_group.terra_rds_subnet_group.name
}
```

## 4-4. 노트용 정리

```text
RDS instance는 subnet ID를 직접 받지 않는다.
RDS는 DB subnet group을 통해 subnet 후보 목록을 전달받고,
`aws_db_instance`에서는 `db_subnet_group_name`으로 해당 DB subnet group의 이름을 참조한다.
```

---

# 5. 시행착오 2: `templatefile()` 파일 경로 오류

## 5-1. 오류 로그

> [!failure]- terraform validate 오류 - templatefile 경로의 파일 없음
> ```text
> Error: Invalid function argument
> 
> on main.tf line 130, in locals:
> 130:   web_user_data = templatefile("${path.module}/user_data/20-web-install.sh.tftpl", {
> 131:     db_host     = aws_db_instance.terra_rds.address
> 132:     db_name     = "appdb"
> 133:     db_user     = "webuser"
> 134:     db_password = "itbank"
> 135:   })
> ├────────────────
> │ while calling templatefile(path, vars)
> │ path.module is "."
> 
> Invalid value for "path" parameter: no file exists at "./user_data/20-web-install.sh.tftpl"; this function works only with files that are distributed as part of the
> configuration source code, so if this file will be created by a resource in this configuration you must instead obtain this result from an attribute of that resource.
> ```

## 5-2. 원인

Terraform은 다음 파일을 찾고 있었다.

```text
D:\terraform\workspace\02_rds\user_data\20-web-install.sh.tftpl
```

하지만 해당 경로에 실제 파일이 없었다.

가능한 원인:

```text
- 파일명이 아직 20-web-install.sh였음
- Windows 확장자 숨김 때문에 20-web-install.sh.tftpl.txt가 되었음
- 01_basic/user_data에 만들고 02_rds/user_data에는 복사하지 않았음
```

## 5-3. 조치

`02_rds/user_data` 아래에 실제 파일명을 맞췄다.

```text
20-web-install.sh.tftpl
```

## 5-4. 배운 점

```text
`templatefile()`은 Terraform 실행 시점에 실제 파일이 configuration source code 안에 존재해야 한다.
파일명이 다르거나, Windows에서 `.txt` 확장자가 붙어 있거나, 다른 폴더에 있으면 validate 단계에서 바로 실패한다.
```

---

# 6. 시행착오 3: RDS master password 길이 오류

## 6-1. 오류 로그

> [!failure]- terraform apply 오류 - RDS MasterUserPassword 8자 미만
> ```text
> Error: creating RDS DB Instance (terra-rds-lab): operation error RDS: CreateDBInstance, https response error StatusCode: 400, RequestID: b3f201e7-ec42-4a25-a50a-8a1b1b71dd73, api error InvalidParameterValue: The parameter MasterUserPassword is not a valid password because it is shorter than 8 characters.
> 
> with aws_db_instance.terra_rds,
> on main.tf line 149, in resource "aws_db_instance" "terra_rds":
> 149: resource "aws_db_instance" "terra_rds" {
> ```

## 6-2. 원인

처음에는 v6.x EC2 DB 실습과 맞추기 위해 다음 비밀번호를 사용했다.

```hcl
password = "itbank"
```

하지만 RDS master password는 8자 이상이어야 하므로 `CreateDBInstance` 단계에서 거부되었다.

## 6-3. 조치

실습용 비밀번호를 8자 이상으로 바꿨다.

```hcl
password = "itbank1234"
```

`templatefile()`에 넘기는 변수도 같이 바꿨다.

```hcl
db_password = "itbank1234"
```

## 6-4. 노트용 정리

```text
이번 실험의 목적은 DB subnet group과 RDS 인프라 구성 검증이었다.
따라서 비밀번호 길이 오류 같은 unrelated failure를 제거하기 위해 RDS master password를 8자 이상으로 조정했다.
```

> [!warning] Terraform state 주의
> `aws_db_instance`의 `password` 값은 Terraform state에 평문으로 저장될 수 있다.  
> 실습용 값이라도 `terraform.tfstate`를 공개 저장소에 올리지 않는다.

---

# 7. 시행착오 4: subnet 1개 DB subnet group 실패

## 7-1. 의도

일부러 DB subnet group에 private subnet 하나만 넣어 실제로 실패하는지 확인했다.

```hcl
resource "aws_db_subnet_group" "terra_rds_subnet_group" {
  name = "terra-rds-subnet-group"

  subnet_ids = [
    aws_subnet.terra_close_subnet.id
  ]
}
```

## 7-2. 오류 로그

> [!failure]- terraform apply 오류 - DBSubnetGroupDoesNotCoverEnoughAZs
> ```text
> Error: creating RDS DB Subnet Group (terra-rds-subnet-group): operation error RDS: CreateDBSubnetGroup, https response error StatusCode: 400, RequestID: e9d17a68-7ef4-41f1-bc8d-585b157556e4, DBSubnetGroupDoesNotCoverEnoughAZs: The DB subnet group doesn't meet Availability Zone (AZ) coverage requirement. Current AZ coverage: ap-northeast-2a. Add subnets to cover at least 2 AZs.
> 
> with aws_db_subnet_group.terra_rds_subnet_group,
> on main.tf line 64, in resource "aws_db_subnet_group" "terra_rds_subnet_group":
> 64: resource "aws_db_subnet_group" "terra_rds_subnet_group" {
> ```

## 7-3. 판정

이 오류는 Terraform HCL 문법 오류가 아니다.  
`terraform apply` 중 AWS RDS API의 `CreateDBSubnetGroup` 단계에서 거부된 것이다.

```text
현재 AZ coverage:
ap-northeast-2a

요구사항:
최소 2개 AZ를 cover하도록 subnet 추가
```

## 7-4. 조치

`ap-northeast-2c`에 두 번째 private subnet을 추가했다.

```hcl
resource "aws_subnet" "terra_close_subnet2" {
  vpc_id                  = aws_vpc.terra_vpc.id
  cidr_block              = "10.20.11.0/24"
  availability_zone       = "ap-northeast-2c"
  map_public_ip_on_launch = false
}
```

DB subnet group에 두 subnet을 모두 포함했다.

```hcl
subnet_ids = [
  aws_subnet.terra_close_subnet.id,
  aws_subnet.terra_close_subnet2.id
]
```

수정 후 `terraform apply`는 성공했다.

## 7-5. 노트용 정리

```text
Terraform validate/plan 단계에서는 subnet 1개 DB subnet group 문제가 드러나지 않을 수 있다.
하지만 apply 단계에서 AWS RDS API가 `DBSubnetGroupDoesNotCoverEnoughAZs` 오류로 생성을 거부했다.
오류 메시지는 현재 AZ coverage가 `ap-northeast-2a` 하나뿐이며, 최소 2개 AZ를 커버하도록 subnet을 추가하라고 안내했다.
따라서 Single-AZ RDS DB instance를 1개만 생성하더라도, 일반 Region의 DB subnet group은 최소 2개 AZ의 subnet을 가져야 함을 실증했다.
```

---

# 8. RDS endpoint와 `templatefile()`

## 8-1. 기존 EC2 DB 방식

v6.x에서는 DB EC2의 private IP를 고정해서 PHP에 직접 넣었다.

```php
$host = '192.168.10.13';
```

## 8-2. RDS 방식

RDS는 고정 private IP를 직접 쓰는 것이 아니라 DNS endpoint를 사용한다.

```php
$host = '${db_host}';
```

Terraform에서 실제 RDS endpoint를 주입한다.

```hcl
web_user_data = templatefile("${path.module}/user_data/20-web-install.sh.tftpl", {
  db_host     = aws_db_instance.terra_rds.address
  db_name     = "appdb"
  db_user     = "webuser"
  db_password = "itbank1234"
})
```

## 8-3. 잘못된 예

```php
$host = 'aws_db_instance.terra_rds.address';
```

이건 Terraform 값 참조가 아니다.  
PHP 입장에서는 그냥 문자열이다.

## 8-4. 올바른 흐름

```text
aws_db_instance.terra_rds.address
→ templatefile() vars의 db_host
→ 20-web-install.sh.tftpl 안의 ${db_host}
→ EC2 user_data로 렌더링
→ /var/www/html/db-test.php의 $host 값
```

## 8-5. v7.0에서의 상태

현재 `20-web-install.sh.tftpl`에는 다음 로직이 포함되어 있다.

```text
- Apache httpd 설치
- PHP/PHP-FPM/php-mysqlnd 설치
- index.html 생성
- db-test.php 생성
- RDS endpoint로 PDO 접속
- connection_test 테이블이 없으면 생성
- WEB -> RDS OK INSERT
- 최근 5개 행 SELECT
```

다만 v7.0에서는 아직 `/db-test.php` 검증 스크린샷을 확보하지 않았으므로, 이 부분은 **구성 코드 존재**로만 기록한다.  
실제 통신 검증은 v7.1에서 수행한다.

---

# 9. Terraform implicit dependency와 `depends_on`

## 9-1. 현재 코드

```hcl
locals {
  web_user_data = templatefile("${path.module}/user_data/20-web-install.sh.tftpl", {
    db_host     = aws_db_instance.terra_rds.address
    db_name     = "appdb"
    db_user     = "webuser"
    db_password = "itbank1234"
  })
}
```

WEB EC2는 이 값을 `user_data`로 사용한다.

```hcl
resource "aws_instance" "terra_WEB" {
  user_data = join("\\n", [
    local.common_user_data,
    local.web_user_data
  ])
}
```

## 9-2. Terraform이 보는 의존성

```text
aws_instance.terra_WEB
→ local.web_user_data
→ aws_db_instance.terra_rds.address
→ aws_db_instance.terra_rds
```

즉 `terra_WEB`의 `user_data` 값은 RDS의 `address` 값을 필요로 한다.  
따라서 Terraform은 RDS가 먼저 생성되어야 WEB EC2의 user_data를 완성할 수 있다고 판단한다.

## 9-3. 결론

현재 코드에서는 다음이 불필요하다.

```hcl
depends_on = [aws_db_instance.terra_rds]
```

이미 expression reference로 의존성이 드러나기 때문이다.

## 9-4. `depends_on`이 필요한 경우

`depends_on`은 Terraform 코드의 참조식으로 드러나지 않는 hidden dependency가 있을 때 사용한다.

예:

```hcl
resource "aws_instance" "app" {
  user_data = file("${path.module}/user_data/install.sh")
}
```

이때 `install.sh` 내부에서 특정 S3 bucket이나 외부 리소스를 사용하더라도 Terraform은 script 내부 의미를 분석하지 않는다.  
이런 경우에는 명시적 `depends_on`이 필요할 수 있다.

---

# 10. Security Group stateful 동작

## 10-1. 새로 배운 점

AWS Security Group은 stateful이다.

```text
허용된 inbound traffic에 대한 response traffic은 outbound rule과 무관하게 나갈 수 있다.
허용된 outbound traffic에 대한 response traffic은 inbound rule과 무관하게 들어올 수 있다.
```

## 10-2. 현재 RDS SG

```hcl
resource "aws_security_group" "rds_sg" {
  name   = "rds_sg"
  vpc_id = aws_vpc.terra_vpc.id

  ingress {
    description     = "Allow MariaDB from WEB SG"
    from_port       = 3306
    to_port         = 3306
    protocol        = "tcp"
    security_groups = [aws_security_group.open_sg.id]
  }
}
```

현재 `rds_sg`에는 별도 egress rule이 없다.

## 10-3. 왜 동작할 수 있는가

WEB EC2에서 RDS로 최초 연결을 보낸다.

```text
WEB EC2
→ RDS:3306
```

필요 조건:

```text
WEB SG outbound:
RDS:3306으로 나갈 수 있어야 함

RDS SG inbound:
WEB SG에서 오는 3306을 허용해야 함
```

현재 `open_sg`는 outbound all을 허용한다.

```hcl
egress {
  from_port   = 0
  to_port     = 0
  protocol    = "-1"
  cidr_blocks = ["0.0.0.0/0"]
}
```

RDS SG는 WEB SG에서 오는 3306 inbound를 허용한다.

따라서 RDS가 받은 요청의 응답은 Security Group의 stateful 동작으로 반환될 수 있다.

## 10-4. 주의

```text
RDS SG outbound가 없어도 허용된 inbound 요청의 response는 나갈 수 있다.
하지만 WEB SG outbound가 막혀 있으면 WEB이 RDS로 최초 연결 요청을 보낼 수 없다.
```

## 10-5. 분리 후보

이 내용은 별도 개념 노트로 분리할 가치가 있다.

```text
후보 제목:
AWS Security Group의 Stateful 동작
```

포함할 내용:

```text
- SG는 stateless NACL과 다르게 stateful
- 허용된 요청의 응답은 반대 방향 rule 없이 허용
- WEB → RDS 3306 예시
- inbound와 outbound를 각각 어떤 관점에서 봐야 하는지
```

---

# 11. 현재 코드 검토

## 11-1. 좋은 점

```text
[x] `02_rds`를 별도 Terraform root module로 분리
[x] VPC CIDR을 `10.20.0.0/16`으로 변경해 v6.x와 구분
[x] VPC DNS 옵션 활성화
[x] Public Subnet과 Private DB Subnet 분리
[x] RDS 요구사항에 맞게 2AZ private subnet 구성
[x] DB subnet group 사용
[x] RDS instance는 `multi_az = false`로 Single-AZ 구성
[x] RDS는 `publicly_accessible = false`
[x] WEB EC2는 public subnet에 배치
[x] WEB Security Group은 HTTP 80을 인터넷에 허용
[x] SSH와 ICMP는 Terraform 실행 환경의 현재 공인 IP/32로 제한
[x] WEB user_data에서 RDS endpoint를 templatefile로 주입
```

## 11-2. 보강 후보

### 두 번째 private subnet의 route table association

현재 `terra_close_subnet2`는 DB subnet group에는 들어가지만, `terra_close_rt`에 명시적으로 association되어 있지는 않다.

현재 코드:

```hcl
resource "aws_route_table_association" "terra_close_assoc" {
  subnet_id      = aws_subnet.terra_close_subnet.id
  route_table_id = aws_route_table.terra_close_rt.id
}
```

보강 후보:

```hcl
resource "aws_route_table_association" "terra_close_assoc2" {
  subnet_id      = aws_subnet.terra_close_subnet2.id
  route_table_id = aws_route_table.terra_close_rt.id
}
```

이 보강은 당장 RDS 생성 성공 여부에는 치명적이지 않을 수 있다.  
하지만 학습 코드의 의도를 명확히 하려면 두 private subnet 모두 같은 private route table에 명시적으로 연결하는 편이 좋다.

### `rds_sg` egress 명시 여부

현재 `rds_sg`에는 egress가 없다.

개념 검증 관점:

```text
SG stateful 동작을 보여주기 좋음
```

초보 실습 변수 제거 관점:

```text
egress all을 명시해도 됨
```

명시한다면 다음과 같다.

```hcl
egress {
  description = "Allow all outbound for lab"
  from_port   = 0
  to_port     = 0
  protocol    = "-1"
  cidr_blocks = ["0.0.0.0/0"]
}
```

이번 v7.0에서는 현재 코드를 보존하고, v7.1 검증에서 문제가 생기면 조정한다.

### Hardcoded password

현재 실습 코드는 다음 값을 직접 사용한다.

```hcl
password = "itbank1234"
```

실습 편의상 사용했지만, 운영/공개 저장소 기준으로는 좋지 않다.

개선 후보:

```text
- variable + sensitive = true
- tfvars는 .gitignore 처리
- AWS Secrets Manager 또는 SSM Parameter Store 사용
- Terraform state 보안 관리
```

---

# 12. v7.0 완료 판정

## 12-1. 완료한 것

```text
[x] `02_rds` 별도 Terraform root module 구성
[x] VPC CIDR을 `10.20.0.0/16`으로 변경
[x] Public WEB Subnet `10.20.1.0/24` 구성
[x] Private DB Subnet A `10.20.10.0/24` 구성
[x] Private DB Subnet C `10.20.11.0/24` 구성
[x] subnet 1개 DB subnet group 시도
[x] `DBSubnetGroupDoesNotCoverEnoughAZs` 오류 확인
[x] RDS master password 8자 미만 오류 확인
[x] password를 `itbank1234`로 수정
[x] 서로 다른 AZ subnet 2개로 DB subnet group 수정
[x] `aws_db_instance`에서 `db_subnet_group_name` 사용
[x] RDS MariaDB instance apply 성공
[x] `20-web-install.sh`를 `20-web-install.sh.tftpl`로 전환
[x] PHP DB host를 RDS endpoint 변수로 주입
[x] Terraform implicit dependency로 RDS → WEB 생성 순서가 잡힘을 확인
```

## 12-2. 아직 완료하지 않은 것

```text
[ ] WEB `/db-test.php`에서 `WEB -> RDS CONNECT OK` 확인
[ ] RDS table에 `WEB -> RDS OK` 행 누적 확인
[ ] 브라우저 또는 curl 기반 증적 확보
[ ] RDS 콘솔 available 화면 캡처
[ ] DB subnet group 콘솔 화면 캡처
[ ] 두 번째 private subnet route table association 추가 여부 결정
[ ] 실습 후 `terraform destroy` 완료
```

## 12-3. v7.0 판정

```text
v7.0은 RDS 인프라 구성 실습으로 완료.
RDS 기반 WEB-DB 기능 검증은 v7.1 범위로 넘긴다.
```

---

# 13. v7.1 예정 범위

v7.1의 목표는 **RDS에 실제 테이블을 만들고, WEB에서 RDS에 INSERT/SELECT하는 증적을 확보하는 것**이다.

현재 `20-web-install.sh.tftpl`에는 이미 다음 코드가 있다.

```sql
CREATE TABLE IF NOT EXISTS connection_test (
    id INT AUTO_INCREMENT PRIMARY KEY,
    message VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

그리고 PHP는 다음 작업을 수행하도록 되어 있다.

```text
1. RDS endpoint로 접속
2. `connection_test` 테이블이 없으면 생성
3. `WEB -> RDS OK` INSERT
4. 최근 5개 행 SELECT
5. `WEB -> RDS CONNECT OK` 출력
```

v7.1에서 확인할 명령:

```powershell
curl.exe -v http://<WEB_PUBLIC_IP>/
curl.exe -v http://<WEB_PUBLIC_IP>/db-test.php
```

기대 출력:

```text
WEB -> RDS CONNECT OK
DB_HOST=terra-rds-lab.xxxxxxxxxxxx.ap-northeast-2.rds.amazonaws.com

1 | WEB -> RDS OK | 2026-...
```

v7.1에서 확보할 증거:

```text
[x] WEB index 화면
[x] `/db-test.php` 출력
[x] `WEB -> RDS CONNECT OK`
[x] DB_HOST가 RDS endpoint로 출력됨
[x] `WEB -> RDS OK` 행 누적
[x] 가능하면 RDS 콘솔에서 endpoint/available 상태 캡처
```

---

# 14. validate / plan / apply 오류 계층 정리

이번 실습에서는 오류가 여러 계층에서 발생했다.

| 단계 | 오류 | 의미 |
|---|---|---|
| `terraform validate` | `templatefile()` 경로의 파일 없음 | Terraform configuration/source code 수준 오류 |
| provider schema 검증 | 존재하지 않는 argument 사용 | Terraform Provider schema 수준 오류 |
| `terraform apply` | RDS password 8자 미만 | AWS RDS `CreateDBInstance` API/service constraint |
| `terraform apply` | `DBSubnetGroupDoesNotCoverEnoughAZs` | AWS RDS `CreateDBSubnetGroup` API/service constraint |

정리:

```text
Terraform의 검증 단계는 계층별로 다르다.
`validate`는 Terraform 코드와 provider schema 수준의 오류를 잡지만,
AWS 서비스가 실제로 요구하는 제약은 `apply`에서 API 호출 시점에 드러날 수 있다.
```

---

# 15. 보고서용 한 문단 요약

```text
이번 RDS 전환 실습에서는 기존 Private DB EC2를 제거하고, AWS 관리형 데이터베이스인 RDS MariaDB를 VPC 내부 private subnet group에 배치하였다. 처음에는 예시 그림처럼 private subnet 1개만 사용해 DB subnet group을 구성하려 했으나, `terraform apply` 단계에서 AWS RDS API가 `DBSubnetGroupDoesNotCoverEnoughAZs` 오류로 생성을 거부하였다. 이를 통해 Single-AZ RDS DB instance 1개를 만들더라도, 일반 Region의 DB subnet group은 서로 다른 Availability Zone의 subnet을 최소 2개 포함해야 함을 확인하였다. 이후 `ap-northeast-2a`, `ap-northeast-2c`에 private subnet을 각각 추가하고 DB subnet group에 포함시켜 RDS 생성을 성공시켰다. Web EC2는 Terraform `templatefile()`을 통해 RDS endpoint를 PHP 설정에 주입받도록 구성했으며, Terraform은 `aws_db_instance.terra_rds.address` 참조를 통해 RDS와 WEB EC2 사이의 생성 순서를 자동으로 추론하였다.
```

---

# 부록 A. 현재 `main.tf`

> [!note]- 02_rds/main.tf - RDS 인프라 구성 v7.0
> ```hcl
> terraform {
>   required_providers {
>     aws = {
>       source  = "hashicorp/aws"
>       version = "~> 6.0"
>     }
>     http = {
>       source = "hashicorp/http"
>     }
>   }
> }
> 
> data "http" "my_public_ip" {
>   url = "https://checkip.amazonaws.com/"
> }
> 
> locals {
>   my_ip_cidr = "${chomp(data.http.my_public_ip.response_body)}/32"
> }
> 
> provider "aws" {
>   region  = "ap-northeast-2"
>   profile = "Terra-user"
> }
> 
> resource "aws_vpc" "terra_vpc" {
>   cidr_block           = "10.20.0.0/16"
>   enable_dns_support   = true
>   enable_dns_hostnames = true
>   tags = {
>     Name = "terra_vpc"
>   }
> }
> 
> resource "aws_internet_gateway" "gw" {
>   vpc_id = aws_vpc.terra_vpc.id
> 
>   tags = {
>     Name = "main"
>   }
> }
> 
> resource "aws_subnet" "terra_open_subnet" {
>   vpc_id                  = aws_vpc.terra_vpc.id
>   cidr_block              = "10.20.1.0/24"
>   availability_zone       = "ap-northeast-2a"
>   map_public_ip_on_launch = true
> 
>   tags = {
>     Name = "terra_open_subnet"
>   }
> }
> 
> resource "aws_subnet" "terra_close_subnet" {
>   vpc_id                  = aws_vpc.terra_vpc.id
>   cidr_block              = "10.20.10.0/24"
>   availability_zone       = "ap-northeast-2a"
>   map_public_ip_on_launch = false
>   tags = {
>     Name = "terra_close_subnet"
>   }
> }
> 
> resource "aws_subnet" "terra_close_subnet2" {
>   vpc_id                  = aws_vpc.terra_vpc.id
>   cidr_block              = "10.20.11.0/24"
>   availability_zone       = "ap-northeast-2c"
>   map_public_ip_on_launch = false
>   tags = {
>     Name = "terra_close_subnet2"
>   }
> }
> 
> resource "aws_db_subnet_group" "terra_rds_subnet_group" {
>   name = "terra-rds-subnet-group"
> 
>   subnet_ids = [
>     aws_subnet.terra_close_subnet.id,
>     aws_subnet.terra_close_subnet2.id
>   ]
> }
> 
> resource "aws_security_group" "open_sg" {
>   name   = "open_sg"
>   vpc_id = aws_vpc.terra_vpc.id
> 
>   ingress {
>     description = "Allow HTTP from Internet"
>     from_port   = 80
>     to_port     = 80
>     protocol    = "tcp"
>     cidr_blocks = ["0.0.0.0/0"]
>   }
> 
>   ingress {
>     description = "Allow SSH from my IP"
>     from_port   = 22
>     to_port     = 22
>     protocol    = "tcp"
>     cidr_blocks = [local.my_ip_cidr]
>   }
> 
>   ingress {
>     description = "Allow all ICMP from current public IP"
>     from_port   = -1
>     to_port     = -1
>     protocol    = "icmp"
>     cidr_blocks = [local.my_ip_cidr]
>   }
> 
>   egress {
>     from_port   = 0
>     to_port     = 0
>     protocol    = "-1"
>     cidr_blocks = ["0.0.0.0/0"]
>   }
> }
> 
> 
> resource "aws_security_group" "rds_sg" {
>   name   = "rds_sg"
>   vpc_id = aws_vpc.terra_vpc.id
> 
>   ingress {
>     description     = "Allow MariaDB from WEB SG"
>     from_port       = 3306
>     to_port         = 3306
>     protocol        = "tcp"
>     security_groups = [aws_security_group.open_sg.id]
>   }
> 
>   tags = {
>     Name = "rds_sg"
>   }
> }
> 
> 
> locals {
>   common_user_data = file("${path.module}/user_data/00-common.sh")
> 
>   web_user_data = templatefile("${path.module}/user_data/20-web-install.sh.tftpl", {
>     db_host     = aws_db_instance.terra_rds.address
>     db_name     = "appdb"
>     db_user     = "webuser"
>     db_password = "itbank1234"
>   })
> }
> 
> resource "aws_db_instance" "terra_rds" {
>   identifier = "terra-rds-lab"
> 
>   allocated_storage = 20
>   storage_type      = "gp3"
> 
>   engine         = "mariadb"
>   instance_class = "db.t3.micro"
> 
>   db_name  = "appdb"
>   username = "webuser"
>   password = "itbank1234"
> 
>   db_subnet_group_name   = aws_db_subnet_group.terra_rds_subnet_group.name
>   vpc_security_group_ids = [aws_security_group.rds_sg.id]
> 
>   publicly_accessible = false
>   multi_az            = false
> 
>   skip_final_snapshot     = true
>   deletion_protection     = false
>   backup_retention_period = 0
> 
>   tags = {
>     Name = "terra_rds"
>   }
> }
> 
> 
> 
> 
> resource "aws_route_table" "terra_close_rt" {
>   vpc_id = aws_vpc.terra_vpc.id
>   tags = {
>     Name = "terra_close_rt"
>   }
> }
> resource "aws_route_table_association" "terra_close_assoc" {
>   subnet_id      = aws_subnet.terra_close_subnet.id
>   route_table_id = aws_route_table.terra_close_rt.id
> }
> 
> 
> 
> 
> 
> resource "aws_instance" "terra_WEB" {
>   ami                         = "ami-0b1cb107a74bad43e"
>   instance_type               = "t3.micro"
>   subnet_id                   = aws_subnet.terra_open_subnet.id
>   key_name                    = "asd-open"
>   vpc_security_group_ids      = [aws_security_group.open_sg.id]
>   associate_public_ip_address = true
>   private_ip                  = "10.20.1.13"
> 
>   user_data = join("\n", [
>     local.common_user_data,
>     local.web_user_data
>   ])
> 
>   tags = {
>     Name = "terra_WEB"
>   }
> }
> 
> resource "aws_route_table" "terra_open_rt" {
>   vpc_id = aws_vpc.terra_vpc.id
> 
>   route {
>     cidr_block = "0.0.0.0/0"
>     gateway_id = aws_internet_gateway.gw.id
>   }
> 
>   tags = {
>     Name = "terra_open_rt"
>   }
> }
> resource "aws_route_table_association" "terra_open_assoc" {
>   subnet_id      = aws_subnet.terra_open_subnet.id
>   route_table_id = aws_route_table.terra_open_rt.id
> }
> ```

---

# 부록 B. 현재 `00-common.sh`

> [!note]- user_data/00-common.sh
> ```bash
> #!/bin/bash
> set -euo pipefail
> 
> SWAP_FILE="/swapfile"
> SWAP_SIZE="2G"
> 
> if ! swapon --show=NAME | grep -qx "$SWAP_FILE"; then
>     if [[ ! -f "$SWAP_FILE" ]]; then
>     fallocate -l "$SWAP_SIZE" "$SWAP_FILE" || dd if=/dev/zero of="$SWAP_FILE" bs=1M count=2048
>     fi
> 
>     chmod 600 "$SWAP_FILE"
>     mkswap "$SWAP_FILE"
>     swapon "$SWAP_FILE"
> fi
> 
> grep -qxF "$SWAP_FILE none swap sw 0 0" /etc/fstab || echo "$SWAP_FILE none swap sw 0 0" >> /etc/fstab
> 
> echo 'vm.swappiness = 10' > /etc/sysctl.d/99-low-memory-lab.conf
> sysctl --system >/dev/null
> ```

---

# 부록 C. 현재 `20-web-install.sh.tftpl`

> [!note]- user_data/20-web-install.sh.tftpl
> ```bash
> dnf install -y httpd php php-mysqlnd php-fpm
> 
> systemctl enable --now php-fpm
> systemctl enable --now httpd
> 
> cat > /var/www/html/index.html <<'HTML'
> <h1>Terraform RDS Web Server</h1>
> <p>Public Web Server is running.</p>
> <p>DB test: <a href="/db-test.php">/db-test.php</a></p>
> HTML
> 
> cat > /var/www/html/db-test.php <<'PHP'
> <?php
> header('Content-Type: text/plain; charset=utf-8');
> 
> $host = '${db_host}';
> $db   = '${db_name}';
> $user = '${db_user}';
> $pass = '${db_password}';
> 
> try {
>     $pdo = new PDO(
>         "mysql:host=$host;dbname=$db;charset=utf8mb4",
>         $user,
>         $pass,
>         [
>             PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
>             PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
>         ]
>     );
> 
>     $pdo->exec("
>         CREATE TABLE IF NOT EXISTS connection_test (
>             id INT AUTO_INCREMENT PRIMARY KEY,
>             message VARCHAR(255) NOT NULL,
>             created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
>         )
>     ");
> 
>     $pdo->exec("INSERT INTO connection_test (message) VALUES ('WEB -> RDS OK')");
> 
>     $stmt = $pdo->query(
>         "SELECT id, message, created_at
>          FROM connection_test
>          ORDER BY id DESC
>          LIMIT 5"
>     );
> 
>     echo "WEB -> RDS CONNECT OK\n";
>     echo "DB_HOST={$host}\n\n";
> 
>     foreach ($stmt as $row) {
>         echo "{$row['id']} | {$row['message']} | {$row['created_at']}\n";
>     }
> } catch (Throwable $e) {
>     http_response_code(500);
>     echo "WEB -> RDS CONNECT FAIL\n";
>     echo $e->getMessage() . "\n";
> }
> PHP
> 
> systemctl restart httpd
> ```

---

# 부록 D. 공식 근거 메모

## AWS RDS

```text
- RDS DB instance를 VPC에 배포하려면 VPC에 최소 2개 subnet이 필요하고, 서로 다른 AZ에 있어야 한다.
- DB subnet group은 일반적으로 private subnet들의 collection이며, 최소 2개 AZ의 subnet을 가져야 한다.
- Local Zone DB subnet group은 subnet 1개 예외가 있다.
- RDS는 DB subnet group에서 subnet과 IP를 선택해 DB instance에 연결한다.
- RDS 접속에는 underlying IP보다 DNS endpoint 사용이 권장된다.
```

공식 문서:

```text
https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_VPC.WorkingWithRDSInstanceinaVPC.html
```

## AWS Security Group

```text
- Security Group은 stateful이다.
- 허용된 outbound request의 response는 inbound rule과 관계없이 허용된다.
- 허용된 inbound traffic의 response는 outbound rule과 관계없이 허용된다.
```

공식 문서:

```text
https://docs.aws.amazon.com/vpc/latest/userguide/vpc-security-groups.html
```

## Terraform / HashiCorp

```text
- `templatefile(path, vars)`는 파일을 읽고 변수 map으로 템플릿을 렌더링한다.
- `*.tftpl`은 Terraform template 파일임을 드러내기 위한 권장 naming pattern이다.
- Terraform은 expression reference를 기반으로 implicit dependency graph를 만든다.
- `depends_on`은 Terraform이 자동 추론할 수 없는 hidden dependency에 사용한다.
```

공식 문서:

```text
https://developer.hashicorp.com/terraform/language/functions/templatefile
https://developer.hashicorp.com/terraform/language/meta-arguments/depends_on
```

---

## 관련 노트

- [[00_IaC MOC]]
- [[Terraform AWS CLI 초기 설정 실습 v6.3]]
- [[Terraform Resource와 Data Source]]
- [[Terraform Workflow]]
- [[AWS Security Group의 Stateful 동작]]
- [[Amazon RDS]]
