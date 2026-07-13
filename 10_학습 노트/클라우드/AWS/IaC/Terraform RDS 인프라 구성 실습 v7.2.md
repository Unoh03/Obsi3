---
title: Terraform RDS 인프라 구성 실습
version: v7.2
created: 2026-07-09
updated: 2026-07-10
status: active
type: lab-note
source:
  - Terraform AWS CLI 초기 설정 실습 v6.3.md
  - Terraform RDS 실습 노트 재료 v0.1.md
  - 02_rds/main.tf
  - user_data/00-common.sh
  - user_data/20-web-install.sh.tftpl
  - conversation-log
  - 07_networks/main.tf
  - 07_networks/user_data/10-nat.sh
  - 07_servers/main.tf
official_refs:
  - https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_VPC.WorkingWithRDSInstanceinaVPC.html
  - https://docs.aws.amazon.com/vpc/latest/userguide/vpc-security-groups.html
  - https://developer.hashicorp.com/terraform/language/functions/templatefile
  - https://developer.hashicorp.com/terraform/language/meta-arguments/depends_on
  - https://developer.hashicorp.com/terraform/language/files
  - https://developer.hashicorp.com/terraform/language/state/remote-state-data
tags:
  - 과목/AWS
  - 주제/IaC
  - 주제/Terraform
  - 주제/RDS
  - 주제/SecurityGroup
  - 주제/Terraform-State
  - 주제/Root-Module
  - 상태/active
  - 실습/Terraform
---

# Terraform RDS 인프라 구성 실습 v7.2

## 목적

이 노트는 기존 `v6.3`의 **Public Web + Private DB EC2** 구조를 RDS 기반 구조로 전환하고, 이후 같은 인프라를 **Network와 Server라는 두 개의 독립적인 Terraform Root Module**로 분리하는 과정을 누적 정리한다.

버전별 초점은 다음과 같다.

```text
v7.0:
Public WEB EC2
→ Private RDS MariaDB
→ RDS 인프라 생성과 DB subnet group 요구사항 확인

v7.1:
WEB → RDS 실제 연결
→ 테이블 생성
→ INSERT/SELECT
→ PHP/PDO와 TLS 검증

v7.2:
하나의 Terraform 구성
→ 07_networks와 07_servers로 분리
→ output과 terraform_remote_state로 데이터 전달
→ State와 생명주기 분리의 장점·비용 정리
```

> [!important] v7.1 범위 보존
> `/db-test.php`를 통한 실제 INSERT/SELECT, PHP/PDO 연결, TLS 적용과 기능 검증은 v7.1 범위로 남겨둔다.  
> v7.2는 이 기능 검증을 대체하지 않고, 인프라 코드를 여러 Root Module로 분리하는 Terraform 구조 학습에 집중한다.

> [!important] v7.2의 핵심
> 같은 폴더에 `.tf` 파일을 여러 개 두는 것은 **파일 정리**다.  
> 폴더를 나누는 것은 **Root Module, State, 실행 단위, 생명주기를 나누는 것**이다.

> [!note] 증적 범위
> v7.2는 Terraform의 구성 경계와 State 연동 원리를 설명하는 실습 노트다.  
> 별도의 브라우저 스크린샷이나 고의적인 오류 증적은 필수로 요구하지 않는다. 코드 구조, 명령, 예상 동작을 중심으로 정리한다.

---

## 출처 구분

```text
① 내장 지식:
- Terraform dependency graph 해석
- VPC/Subnet/Route Table/Security Group/RDS 구조 해석
- Root Module과 State 경계 해석
- 구성 분리의 장점과 운영 비용 비교

② 인터넷 고신뢰 정보:
- AWS RDS 공식 문서
- AWS VPC Security Group 공식 문서
- HashiCorp Terraform 파일/모듈 구조 공식 문서
- HashiCorp `terraform_remote_state` 공식 문서

③ 인터넷 비공식 고품질 의견:
- 사용 안 함

④ 업로드/실습 자료:
- Terraform AWS CLI 초기 설정 실습 v6.3.md
- Terraform RDS 실습 노트 재료 v0.1.md
- 현재 02_rds/main.tf
- user_data/00-common.sh
- user_data/20-web-install.sh.tftpl
- 07_networks/main.tf
- 07_networks/user_data/10-nat.sh
- 07_servers/main.tf 골격
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
> - [[#14. validate / plan / apply 오류 계층 정리|14. 오류 계층]]
> - [[#15. 보고서용 한 문단 요약|15. v7.0 요약]]
> - [[#16. v7.2 목표와 범위|16. v7.2 목표와 범위]]
> - [[#17. 같은 폴더의 여러 `.tf` 파일은 하나의 구성이다|17. 같은 폴더의 여러 .tf 파일]]
> - [[#18. 폴더를 나누면 무엇이 달라지는가|18. 폴더 분리의 의미]]
> - [[#19. v7.2 책임 경계와 폴더 구조|19. 책임 경계와 폴더 구조]]
> - [[#20. `output`과 `terraform_remote_state`로 데이터 전달|20. State 데이터 전달]]
> - [[#21. Output은 구성 사이의 계약이다|21. 구성 사이의 계약]]
> - [[#22. State가 나뉘면 전체 의존성 그래프도 나뉜다|22. 의존성과 생명주기]]
> - [[#23. 폴더와 State를 분리하는 이점|23. 분리의 이점]]
> - [[#24. 분리의 비용과 한계|24. 분리의 비용]]
> - [[#25. Root Module, Child Module, Backend의 차이|25. 개념 구분]]
> - [[#26. 현재 `07_networks`와 `07_servers` 검토|26. 현재 구성 검토]]
> - [[#27. v7.2 구현 순서|27. 구현 순서]]
> - [[#28. v7.2 완료 판정|28. 완료 판정]]
> - [[#29. v7.2 보고서용 한 문단 요약|29. v7.2 요약]]
> - [[#부록 A. 현재 `main.tf`|부록 A. v7.0 main.tf]]
> - [[#부록 B. 현재 `00-common.sh`|부록 B. 공통 user_data]]
> - [[#부록 C. 현재 `20-web-install.sh.tftpl`|부록 C. Web user_data]]
> - [[#부록 D. 공식 근거 메모|부록 D. 공식 근거]]
> - [[#부록 E. 현재 `07_networks/main.tf`|부록 E. 07_networks main.tf]]
> - [[#부록 F. 현재 `07_networks/user_data/10-nat.sh`|부록 F. NAT user_data]]
> - [[#부록 G. 현재 `07_servers/main.tf` 골격|부록 G. 07_servers 골격]]

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


# 16. v7.2 목표와 범위

## 16-1. 이번 버전의 질문

v7.2는 다음 질문에 답하는 실습이다.

```text
Terraform은 같은 폴더의 여러 .tf 파일을 어떻게 처리하는가?

여러 파일을 사용할 수 있는데도
왜 07_networks와 07_servers처럼 폴더까지 나누는가?

나뉜 두 Terraform 구성은
VPC ID와 Subnet ID를 어떻게 전달하는가?

State를 나누면 무엇이 좋아지고,
어떤 책임이 새로 생기는가?
```

## 16-2. 포함 범위

```text
- 같은 디렉터리의 여러 .tf 파일과 하나의 Root Module 관계
- 디렉터리 분리에 따른 Root Module 분리
- Terraform State 분리
- Network와 Server의 책임 경계
- Network root output 공개
- Server root에서 terraform_remote_state 조회
- 구성 사이의 데이터 계약
- 독립적인 init / plan / apply / destroy
- 생성 및 삭제 순서
- 변경 범위와 장애 범위 축소
- State 접근 권한과 local state 방식의 한계
```

## 16-3. 제외 범위

다음은 v7.2에서 다루지 않는다.

```text
- v7.1의 WEB → RDS 실제 INSERT/SELECT 검증
- PHP/PDO TLS 조치
- S3 Remote Backend 구축
- State locking 구성
- 재사용 가능한 Child Module 제작
- CI/CD 파이프라인에서 Root Module 실행 순서 자동화
- 운영용 IAM 최소 권한 설계
```

---

# 17. 같은 폴더의 여러 `.tf` 파일은 하나의 구성이다

## 17-1. 파일을 나누는 예

Terraform 코드는 하나의 `main.tf`에 모두 넣지 않아도 된다.

```text
02_rds/
├─ providers.tf
├─ network.tf
├─ security_groups.tf
├─ ec2.tf
├─ rds.tf
├─ variables.tf
└─ outputs.tf
```

파일이 여러 개여도 같은 디렉터리의 최상위 `.tf` 파일은 하나의 Terraform Module로 평가된다.

```text
파일 수:
여러 개

Root Module:
1개

State:
1개

Dependency Graph:
1개

plan / apply / destroy:
각각 1회
```

## 17-2. 파일 분리는 사람을 위한 구조다

같은 폴더에서는 `network.tf`에 선언한 리소스를 `ec2.tf`에서 직접 참조할 수 있다.

```hcl
# network.tf
resource "aws_subnet" "web" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = "192.168.10.0/24"
  availability_zone = "ap-northeast-2a"
}
```

```hcl
# ec2.tf
resource "aws_instance" "web" {
  subnet_id = aws_subnet.web.id
}
```

Terraform은 파일을 따로 실행하지 않는다.

```text
network.tf 실행
→ ec2.tf 실행
```

같은 순서 개념은 없다.

Terraform은 같은 디렉터리의 모든 구성 블록을 함께 읽고 참조 관계를 기반으로 Dependency Graph를 만든다.

## 17-3. 파일명은 실행 순서를 결정하지 않는다

다음과 같이 이름을 붙여도 실행 순서를 강제하지 않는다.

```text
01-network.tf
02-security-group.tf
03-ec2.tf
```

이 이름은 사람이 읽기 편하게 정렬하는 효과만 있다.

실제 생성 순서는 다음 참조로 결정된다.

```hcl
subnet_id = aws_subnet.web.id
```

```text
EC2가 Subnet ID를 참조
→ Subnet이 먼저 필요함
→ Terraform이 의존성을 계산
```

## 17-4. 파일만 나누는 것이 적절한 경우

다음 조건이라면 하나의 Root Module 안에서 `.tf` 파일만 분리하는 편이 단순하다.

```text
- 모든 리소스를 항상 같이 배포함
- 같은 사람이 관리함
- 권한과 변경 주기가 비슷함
- State를 따로 나눌 이유가 없음
- 구성 규모가 작음
- 전체 의존성을 Terraform이 한 번에 계산하는 편이 유리함
```

---

# 18. 폴더를 나누면 무엇이 달라지는가

## 18-1. v7.2 구조

```text
WORKSPACE/
├─ 07_networks/
│  ├─ main.tf
│  └─ user_data/
│     └─ 10-nat.sh
│
└─ 07_servers/
   ├─ main.tf
   ├─ security_groups.tf
   ├─ instances.tf
   ├─ rds.tf
   ├─ variables.tf
   ├─ outputs.tf
   └─ user_data/
      └─ 20-web-install.sh
```

`07_networks`와 `07_servers`는 단순한 파일 묶음이 아니다.

각 디렉터리에서 별도로 Terraform CLI를 실행하므로 각각 독립된 Root Module이 된다.

```text
07_networks:
Root Module 1
State 1
Dependency Graph 1
init / plan / apply / destroy 1세트

07_servers:
Root Module 2
State 2
Dependency Graph 2
init / plan / apply / destroy 1세트
```

## 18-2. 다른 폴더의 리소스를 직접 참조할 수 없는 이유

`07_servers`에서 다음 코드는 사용할 수 없다.

```hcl
subnet_id = aws_subnet.close_subnet_1.id
```

`aws_subnet.close_subnet_1`은 `07_networks` Root Module에 선언된 리소스 주소다.

`07_servers`의 구성만 읽는 Terraform에게는 해당 리소스가 선언되어 있지 않다.

```text
07_networks의 리소스 주소:
aws_subnet.close_subnet_1

07_servers가 아는 리소스 주소:
07_servers 폴더에 선언된 리소스와 Data Source만
```

즉 폴더를 나누면 코드 파일의 가시 범위도 나뉜다.

## 18-3. 중요한 결론

```text
같은 폴더의 여러 .tf:
가독성 분리

서로 다른 폴더:
Terraform 구성 경계 분리
State 분리
실행 단위 분리
생명주기 분리
```

---

# 19. v7.2 책임 경계와 폴더 구조

## 19-1. `07_networks`의 책임

```text
- VPC
- Public Subnet
- Private Web Subnet
- Private DB Subnet 2개
- Internet Gateway
- Public Route Table
- Web Private Route Table
- DB Private Route Table
- NAT Instance
- NAT Security Group
- S3 Gateway Endpoint
- 다른 Root Module에 공개할 output
```

NAT Instance는 EC2 리소스지만 `07_networks`에 둔다.

이유는 AWS 서비스 종류가 EC2라서가 아니라, 이 인스턴스의 역할과 생명주기가 네트워크에 속하기 때문이다.

```text
리소스 종류:
EC2 Instance

논리적 역할:
Private Subnet의 outbound network path

소유 Root Module:
07_networks
```

## 19-2. `07_servers`의 책임

```text
- Bastion Host
- Private Web EC2
- RDS MariaDB
- RDS DB Subnet Group
- Bastion Security Group
- Web Security Group
- RDS Security Group
- Web 설치 user_data
- 서버와 DB 관련 output
```

## 19-3. 역할 분리 기준

리소스를 어느 폴더에 둘지는 다음 질문으로 판단한다.

```text
이 리소스는 누구와 같이 생성·변경·삭제되어야 하는가?

이 리소스는 Network의 공개 인터페이스인가,
Server 내부 구현인가?

이 리소스를 변경할 때
어느 범위의 plan을 확인하는 것이 자연스러운가?
```

예:

| 리소스 | 배치 | 이유 |
|---|---|---|
| VPC | `07_networks` | 모든 서버가 사용하는 기반 |
| NAT Instance | `07_networks` | Private outbound 경로를 구성 |
| Bastion Host | `07_servers` | 관리 대상 서버와 함께 운영 |
| Web SG | `07_servers` | Web workload의 통신 정책 |
| DB Subnet Group | `07_servers` | RDS가 소비하는 DB 배치 설정 |
| DB Subnet 자체 | `07_networks` | VPC 주소 공간과 AZ 배치를 정의 |

## 19-4. 현재 아키텍처

```text
VPC 192.168.0.0/16
├─ ap-northeast-2a
│  ├─ open_subnet_1     192.168.1.0/24
│  │  └─ NAT Instance   192.168.1.13
│  ├─ close_subnet_1    192.168.10.0/24
│  │  └─ Private Web EC2 예정
│  └─ db_subnet_1       192.168.30.0/24
│     └─ RDS DB subnet group member
│
└─ ap-northeast-2c
   ├─ open_subnet_2     192.168.2.0/24
   │  └─ Bastion Host 예정
   └─ close_subnet_2    192.168.20.0/24
      └─ RDS DB subnet group member
```

라우팅 관계:

```text
open_subnet_1, open_subnet_2
→ public_rt
→ 0.0.0.0/0 → Internet Gateway

close_subnet_1
→ web_private_rt
→ 0.0.0.0/0 → NAT Instance ENI
→ S3 Gateway Endpoint

db_subnet_1, close_subnet_2
→ db_private_rt
→ VPC local route만 사용
```

---

# 20. `output`과 `terraform_remote_state`로 데이터 전달

## 20-1. 왜 output이 필요한가

`07_servers`가 서버를 만들려면 다음 값을 알아야 한다.

```text
- VPC ID
- Bastion용 Public Subnet ID
- Web용 Private Subnet ID
- RDS용 DB Subnet ID 2개
```

이 값은 `07_networks`가 생성한다.

따라서 Network Root Module이 필요한 값만 root output으로 공개한다.

```hcl
output "vpc_id" {
  value = aws_vpc.vpc.id
}

output "open_subnet_2_id" {
  value = aws_subnet.open_subnet_2.id
}

output "close_subnet_1_id" {
  value = aws_subnet.close_subnet_1.id
}

output "db_subnet_1_id" {
  value = aws_subnet.db_subnet_1.id
}

output "close_subnet_2_id" {
  value = aws_subnet.close_subnet_2.id
}
```

## 20-2. Network State 읽기

`07_servers`에서는 Terraform 내장 `terraform_remote_state` Data Source를 사용한다.

```hcl
data "terraform_remote_state" "network" {
  backend = "local"

  config = {
    path = "${path.module}/../07_networks/terraform.tfstate"
  }
}
```

이름에 `remote_state`가 들어가지만 `backend = "local"`을 사용할 수 있다.

이번 실습에서는 다른 폴더의 로컬 State 파일을 읽는다.

```text
07_networks/terraform.tfstate
→ 07_servers의 terraform_remote_state
```

## 20-3. Output 사용

```hcl
locals {
  vpc_id            = data.terraform_remote_state.network.outputs.vpc_id
  bastion_subnet_id = data.terraform_remote_state.network.outputs.open_subnet_2_id
  web_subnet_id     = data.terraform_remote_state.network.outputs.close_subnet_1_id
  db_subnet_1_id    = data.terraform_remote_state.network.outputs.db_subnet_1_id
  db_subnet_2_id    = data.terraform_remote_state.network.outputs.close_subnet_2_id
}
```

이후 리소스에서는 local 값을 사용한다.

```hcl
resource "aws_security_group" "web_sg" {
  vpc_id = local.vpc_id
}
```

```hcl
resource "aws_instance" "web" {
  subnet_id = local.web_subnet_id
}
```

```hcl
resource "aws_db_subnet_group" "rds" {
  subnet_ids = [
    local.db_subnet_1_id,
    local.db_subnet_2_id
  ]
}
```

## 20-4. 전체 데이터 흐름

```text
aws_vpc.vpc.id
aws_subnet.*.id
        │
        ▼
07_networks의 root output
        │
        ▼
07_networks/terraform.tfstate
        │
        ▼
data.terraform_remote_state.network
        │
        ▼
07_servers의 locals
        │
        ├─ Security Group
        ├─ Bastion EC2
        ├─ Web EC2
        └─ RDS DB Subnet Group
```

## 20-5. Root output만 읽을 수 있다

`terraform_remote_state`의 `outputs`에서 사용할 수 있는 것은 Network Root Module이 명시적으로 공개한 root output이다.

다음 리소스가 State에 존재한다고 해서:

```hcl
resource "aws_route_table" "db_private_rt" {
  # ...
}
```

자동으로 아래처럼 읽을 수 있는 것은 아니다.

```hcl
data.terraform_remote_state.network.outputs.db_private_rt_id
```

먼저 Network에 output이 있어야 한다.

```hcl
output "db_private_rt_id" {
  value = aws_route_table.db_private_rt.id
}
```

이번 서버 구성은 Route Table ID를 소비할 필요가 없으므로 공개하지 않는다.

이것은 Network 내부 구현을 불필요하게 노출하지 않는다는 의미도 있다.

---

# 21. Output은 구성 사이의 계약이다

## 21-1. 내부 리소스 주소와 공개 인터페이스

`07_networks` 내부 구현:

```text
aws_subnet.close_subnet_1
aws_subnet.db_subnet_1
aws_subnet.close_subnet_2
```

`07_servers`가 사용하는 공개 인터페이스:

```text
outputs.close_subnet_1_id
outputs.db_subnet_1_id
outputs.close_subnet_2_id
```

Server Root Module은 Network의 전체 구현을 알 필요가 없다.

```text
Network가 어떻게 NAT를 설정했는가:
Server가 알 필요 없음

Network Route Table의 resource 이름:
Server가 알 필요 없음

서버를 배치할 Subnet ID:
Server가 알아야 함
```

## 21-2. Output 이름 변경은 계약 변경이다

Network에서:

```hcl
output "close_subnet_1_id" {
  value = aws_subnet.close_subnet_1.id
}
```

를 다음처럼 바꾼다면:

```hcl
output "web_subnet_id" {
  value = aws_subnet.close_subnet_1.id
}
```

Server의 참조도 같이 바꿔야 한다.

```hcl
web_subnet_id = data.terraform_remote_state.network.outputs.web_subnet_id
```

값이 같아도 output 이름이 바뀌면 소비자 입장에서는 인터페이스가 바뀐 것이다.

## 21-3. 좋은 output의 조건

```text
- 소비자가 실제로 필요한 값만 공개
- 리소스 내부 이름보다 역할을 드러내는 이름 사용
- 의미가 바뀌지 않는 안정적인 이름 사용
- 민감정보를 output으로 내보내지 않음
- 설명 description을 추가
```

예:

```hcl
output "web_private_subnet_id" {
  description = "Private Web EC2를 배치할 ap-northeast-2a subnet ID"
  value       = aws_subnet.close_subnet_1.id
}
```

## 21-4. 현재 이름의 개선 후보

현재 output:

```text
close_subnet_1_id
close_subnet_2_id
```

은 생성 당시 리소스 이름은 반영하지만 역할이 완전히 드러나지는 않는다.

현재 의미:

```text
close_subnet_1_id:
Web용 Private Subnet

close_subnet_2_id:
RDS용 두 번째 DB Subnet
```

후속 정리 후보:

```text
web_private_subnet_id
db_private_subnet_1_id
db_private_subnet_2_id
```

다만 이미 Server 구성에서 사용하기 시작했다면 이름 변경은 양쪽을 동시에 수정해야 한다.

---

# 22. State가 나뉘면 전체 의존성 그래프도 나뉜다

## 22-1. 하나의 Root Module일 때

모든 리소스가 같은 Root Module과 State에 있으면 Terraform이 전체 참조 관계를 계산한다.

```text
VPC
→ Subnet
→ DB Subnet Group
→ RDS

VPC
→ Subnet
→ Web EC2

Web SG
→ RDS SG
```

`terraform apply` 한 번으로 전체 생성 순서를 조정한다.

## 22-2. 두 Root Module일 때

v7.2에서는 그래프가 나뉜다.

```text
07_networks graph:
VPC
→ Subnet
→ Route Table
→ NAT
→ output

07_servers graph:
remote state output
→ SG
→ Bastion
→ Web
→ DB Subnet Group
→ RDS
```

Terraform은 `07_servers`를 실행할 때 Network State를 읽을 수 있지만, 두 Root Module을 하나의 전역 그래프로 합치지는 않는다.

## 22-3. 생성 순서

```text
1. 07_networks terraform init
2. 07_networks terraform apply
3. Network State와 output 생성
4. 07_servers terraform init
5. 07_servers terraform apply
```

Network를 먼저 apply해야 실제 State와 output 값이 생긴다.

## 22-4. 삭제 순서

```text
1. 07_servers terraform destroy
2. 07_networks terraform destroy
```

Server 리소스가 Subnet과 VPC를 사용하고 있으므로 소비자부터 제거한다.

```text
생성:
기반 → 소비자

삭제:
소비자 → 기반
```

## 22-5. Terraform이 역방향 의존성을 모르는 이유

`07_servers`는 Network State를 읽는다.

하지만 `07_networks`는 Server State를 읽지 않는다.

따라서 Network에서 `terraform destroy`를 실행해도 Network Terraform은 다른 State의 EC2와 RDS가 자신의 Subnet을 사용한다는 전체 관계를 알지 못한다.

AWS API가 실제 종속 리소스 때문에 삭제를 거부할 수는 있지만, 이것은 Terraform의 전역 Dependency Graph가 보호한 결과가 아니다.

## 22-6. 독립 실행의 의미

```text
07_networks에서 terraform plan:
네트워크 State와 네트워크 코드만 비교

07_servers에서 terraform plan:
서버 State와 서버 코드,
그리고 읽어온 Network output을 기준으로 비교
```

Network와 Server가 자동으로 같이 plan되지는 않는다.

---

# 23. 폴더와 State를 분리하는 이점

## 23-1. 변경 범위가 작아진다

하나의 큰 State에서는 Network, EC2, RDS 변경이 하나의 plan에 섞인다.

분리하면:

```text
Network 변경:
07_networks plan

Web/RDS 변경:
07_servers plan
```

관심 범위가 작아져 plan 검토가 쉬워진다.

## 23-2. 변경 주기를 다르게 관리할 수 있다

일반적으로 Network 기반은 서버 애플리케이션보다 변경 빈도가 낮다.

```text
VPC/Subnet/Route Table:
낮은 변경 빈도

Web EC2/user_data/RDS 설정:
상대적으로 높은 변경 빈도
```

분리하면 서버만 자주 apply하고 Network는 안정적으로 유지할 수 있다.

## 23-3. 장애 범위를 줄일 수 있다

Server 코드를 수정하다가 오류가 나도 Network State 자체를 직접 수정하지 않는다.

반대로 Network 변경을 검토할 때 Server 리소스의 세부 변경이 plan에 섞이지 않는다.

이것은 논리적인 변경 범위와 State lock 범위를 줄인다.

## 23-4. 권한과 소유권을 분리할 수 있다

운영 환경에서는 다음과 같은 역할 분리가 가능하다.

```text
Network 팀:
VPC, Subnet, Route Table 관리

Application/Server 팀:
EC2, RDS, workload SG 관리
```

State Backend와 실행 권한도 별도로 관리할 수 있다.

이번 로컬 실습에서는 같은 사용자가 모두 관리하지만, 구조적 의미를 확인할 수 있다.

## 23-5. 실수의 영향 범위를 제한한다

Server Root에서 잘못된 `terraform destroy`를 실행해도 정상적인 State 구성이라면 Network Root의 VPC와 Subnet은 Server State에 없으므로 destroy 대상에 포함되지 않는다.

```text
07_servers destroy 대상:
Bastion, Web, RDS, Server SG 등

07_networks destroy 대상:
VPC, Subnet, Route Table, NAT 등
```

단, 잘못된 State 이동이나 수동 AWS 작업까지 방지하는 절대적인 안전장치는 아니다.

## 23-6. State 규모와 처리 범위를 줄일 수 있다

대규모 환경에서는 State가 커질수록 refresh, plan, lock 경쟁, 변경 검토가 복잡해질 수 있다.

여러 Root Module로 적절히 분리하면 각 Terraform 작업의 관리 범위를 줄일 수 있다.

이번 실습 규모에서는 성능 차이가 핵심이 아니라 구조 학습이 핵심이다.

---

# 24. 분리의 비용과 한계

## 24-1. 실행 순서를 직접 관리해야 한다

하나의 Root Module에서는 Terraform이 전체 생성 순서를 계산한다.

State를 분리하면 Root Module 사이의 순서는 사용자가 관리한다.

```text
Network apply 전 Server apply:
실패 가능

Server destroy 전 Network destroy:
삭제 실패 또는 의존 리소스 문제
```

## 24-2. 구성 사이의 계약을 관리해야 한다

Network output 이름이나 의미가 바뀌면 Server도 수정해야 한다.

```text
Network 변경
→ output 변경
→ Network apply
→ Server 참조 수정
→ Server plan/apply
```

Root Module이 많아질수록 이 계약 관리 비용도 증가한다.

## 24-3. State 접근 권한 문제가 생긴다

`terraform_remote_state`는 코드에서 root output만 노출한다.

하지만 해당 Data Source를 읽으려면 State snapshot 자체에 접근할 권한이 필요하다.

State에는 다음 정보가 포함될 수 있다.

```text
- 내부 IP와 리소스 ID
- 리소스 전체 속성
- DB endpoint
- 변수와 Provider가 State에 기록한 민감값
- RDS password 같은 비밀값
```

따라서 운영 환경에서는 State Backend 접근 권한을 신중히 관리해야 한다.

## 24-4. 로컬 경로 의존성이 생긴다

이번 실습:

```hcl
path = "${path.module}/../07_networks/terraform.tfstate"
```

이 방식은 단순하지만 다음 조건에 의존한다.

```text
- 두 폴더의 상대적 위치가 유지됨
- 같은 PC에 State 파일이 존재함
- 다른 사용자가 동일한 State를 공유하지 않음
- CI/CD 실행 환경에서도 같은 경로를 구성해야 함
```

실습에는 적합하지만 협업과 자동화에는 한계가 있다.

## 24-5. 여러 명령을 반복해야 한다

각 Root Module에서 별도로 실행한다.

```text
terraform init
terraform fmt
terraform validate
terraform plan
terraform apply
```

State가 둘이면 작업과 검토도 둘이다.

## 24-6. 작은 실습에서는 과도할 수 있다

현재 리소스 수만 보면 하나의 Root Module과 여러 `.tf` 파일로도 충분히 관리할 수 있다.

이번에 폴더를 나누는 직접적인 이유는 다음이다.

```text
운영 규모가 커서 반드시 분리해야 하기 때문:
아님

Terraform State 경계와 구성 간 데이터 전달을 학습하기 위해:
맞음
```

## 24-7. 폴더 분리는 무조건 좋은 것이 아니다

판단 기준:

| 질문 | `예`라면 분리 고려 |
|---|---|
| 배포 주기가 다른가? | Network와 Server를 분리 |
| 관리 팀이나 권한이 다른가? | State 분리 |
| 장애 범위를 나눌 필요가 있는가? | State 분리 |
| 항상 같이 생성·삭제되는가? | 하나의 Root 유지 가능 |
| 단순히 파일이 길어서 불편한가? | 먼저 `.tf` 파일만 분리 |
| 재사용이 목적인가? | Child Module 검토 |

---

# 25. Root Module, Child Module, Backend의 차이

## 25-1. 현재 구조는 Root Module 2개다

```text
07_networks:
독립적으로 Terraform CLI를 실행하는 Root Module

07_servers:
독립적으로 Terraform CLI를 실행하는 Root Module
```

현재 구조를 Module 분리라고 말할 수는 있지만, 재사용 가능한 Child Module을 만든 것은 아니다.

## 25-2. Child Module 구조와의 차이

Child Module 예:

```hcl
module "network" {
  source = "../modules/network"

  vpc_cidr = "192.168.0.0/16"
}
```

이 경우:

```text
상위 Root Module:
1개

Child Module:
network

State:
보통 Root Module의 State 1개

apply:
상위 Root Module에서 1회
```

반면 현재 구조:

```text
07_networks Root Module + State
07_servers Root Module + State
```

즉 Child Module은 코드 재사용과 추상화가 주목적이고, 현재 v7.2 분리는 독립적인 생명주기와 State 경계가 주목적이다.

## 25-3. Backend와의 차이

Backend는 Terraform State를 어디에 저장하고 어떻게 관리할지 결정한다.

```text
현재:
local backend
각 폴더의 terraform.tfstate

향후 운영 후보:
S3 backend
State 암호화
공유
접근 권한
locking
```

Root Module을 분리하는 것과 Remote Backend를 사용하는 것은 다른 문제다.

```text
Root Module 분리:
무엇을 하나의 Terraform 구성으로 관리할지

Backend:
그 구성의 State를 어디에 저장할지
```

## 25-4. `terraform_remote_state` 이름 해석

`terraform_remote_state`는 다른 Terraform 구성의 State를 읽는 Data Source다.

State 저장소가 반드시 인터넷의 원격 저장소일 필요는 없다.

```hcl
backend = "local"
```

도 지원한다.

이번 실습은:

```text
독립 Root Module:
2개

Backend:
둘 다 local

State 전달:
terraform_remote_state로 07_networks local state 읽기
```

---

# 26. 현재 `07_networks`와 `07_servers` 검토

## 26-1. 현재 Network Root Module

현재 `07_networks/main.tf`는 다음을 포함한다.

```text
[x] VPC
[x] Public Subnet 2개
[x] Private Web Subnet 1개
[x] RDS용 Private DB Subnet 2개
[x] Internet Gateway
[x] Public Route Table
[x] Web Private Route Table
[x] DB Private Route Table
[x] S3 Gateway Endpoint
[x] NAT Security Group
[x] NAT Instance
[x] Web Private Route의 기본 경로 → NAT
[x] Server Root에 전달할 output
```

현재 공개 output:

```text
vpc_id
open_subnet_1_id
open_subnet_2_id
close_subnet_1_id
db_subnet_1_id
close_subnet_2_id
nat_instance_id
nat_public_ip
```

## 26-2. Server가 실제로 소비할 output

```text
vpc_id
open_subnet_2_id
close_subnet_1_id
db_subnet_1_id
close_subnet_2_id
```

현재 Server 구성에서는 다음 값이 필수는 아니다.

```text
open_subnet_1_id
nat_instance_id
nat_public_ip
```

Network 운영 확인이나 후속 검증에는 유용할 수 있으므로 output으로 유지할 수 있다.

## 26-3. 현재 Server Root Module 골격

현재 `07_servers/main.tf` 골격에는 다음이 있다.

```text
- AWS Provider
- HTTP Provider
- 현재 공인 IP 조회
- my_ip_cidr local
- Network와 Server 역할 주석
```

아직 추가해야 할 핵심:

```text
- terraform_remote_state
- Network output을 정리할 locals
- Bastion SG
- Web SG
- RDS SG
- Bastion Host
- Private Web EC2
- RDS DB Subnet Group
- RDS MariaDB
```

## 26-4. Server에 추가할 State 연결

```hcl
data "terraform_remote_state" "network" {
  backend = "local"

  config = {
    path = "${path.module}/../07_networks/terraform.tfstate"
  }
}

locals {
  vpc_id            = data.terraform_remote_state.network.outputs.vpc_id
  bastion_subnet_id = data.terraform_remote_state.network.outputs.open_subnet_2_id
  web_subnet_id     = data.terraform_remote_state.network.outputs.close_subnet_1_id
  db_subnet_1_id    = data.terraform_remote_state.network.outputs.db_subnet_1_id
  db_subnet_2_id    = data.terraform_remote_state.network.outputs.close_subnet_2_id
}
```

## 26-5. `http` Provider와 State 연동은 별개다

`terraform_remote_state`는 Terraform 내장 Data Source이므로 별도의 Provider 선언이 필요하지 않다.

현재 `http` Provider는 다음 목적이다.

```text
현재 Terraform 실행 PC의 공인 IP 조회
→ Bastion SSH ingress를 /32로 제한
```

```hcl
data "http" "my_public_ip" {
  url = "https://checkip.amazonaws.com/"
}
```

Network State를 읽기 위해 `http` Provider를 사용하는 것은 아니다.

---

# 27. v7.2 구현 순서

## 27-1. 1단계: Network 코드 준비

```powershell
cd D:\terraform\workspace\07_networks
terraform fmt
terraform init
terraform validate
terraform plan
```

확인 대상:

```text
- DB subnet이 서로 다른 2개 AZ에 존재
- Web Private Route만 NAT Instance를 사용
- DB Private Route에는 0.0.0.0/0이 없음
- 필요한 output이 선언됨
```

## 27-2. 2단계: Network apply

```powershell
terraform apply
```

Network State가 생성되면 다음으로 확인할 수 있다.

```powershell
terraform output
```

예상 output 이름:

```text
vpc_id
open_subnet_2_id
close_subnet_1_id
db_subnet_1_id
close_subnet_2_id
```

## 27-3. 3단계: Server에서 Network State 읽기

```powershell
cd D:\terraform\workspace\07_servers
terraform init
terraform validate
terraform plan
```

`terraform_remote_state`는 `07_networks/terraform.tfstate`의 root output을 읽는다.

## 27-4. 4단계: Server 리소스 구성

권장 작성 순서:

```text
1. terraform_remote_state
2. locals
3. Security Group
4. Bastion Host
5. Private Web EC2
6. RDS DB Subnet Group
7. RDS MariaDB
8. outputs
```

Terraform 생성 순서를 파일 배치로 강제하는 것은 아니다.

이 순서는 사람이 코드를 이해하고 검토하기 쉽게 하기 위한 작성 순서다.

## 27-5. 5단계: 전체 apply

```text
07_networks apply
→ 07_servers apply
```

## 27-6. 6단계: 비용 발생 리소스 확인

Network apply:

```text
- NAT EC2
- NAT EBS
- Public IPv4
```

Server apply:

```text
- Bastion EC2
- Web EC2
- 각 EC2 EBS
- Bastion Public IPv4
- RDS MariaDB
```

따라서 apply 후 장시간 방치하지 않는다.

## 27-7. 7단계: 전체 destroy

```powershell
cd D:\terraform\workspace\07_servers
terraform destroy

cd D:\terraform\workspace\07_networks
terraform destroy
```

반드시 소비자인 Server를 먼저 제거한다.

---

# 28. v7.2 완료 판정

## 28-1. 개념 및 설계 완료

```text
[x] 같은 폴더의 여러 .tf 파일은 하나의 Module로 처리됨을 정리
[x] 파일 분리와 Root Module 분리의 차이 정리
[x] 07_networks와 07_servers의 책임 경계 결정
[x] NAT Instance를 Network Root에 두는 이유 정리
[x] Network Root output 설계
[x] terraform_remote_state 데이터 흐름 정리
[x] Output을 구성 사이의 계약으로 해석
[x] Root Module 분리 시 State와 Dependency Graph가 나뉨을 정리
[x] 생성 순서 Network → Server 정리
[x] 삭제 순서 Server → Network 정리
[x] State 분리의 장점과 비용 비교
[x] Root Module / Child Module / Backend 차이 정리
[x] v7.1의 WEB → RDS 기능 및 TLS 검증 범위 보존
```

## 28-2. 코드 기준 현재 상태

```text
[x] 07_networks 코드 작성
[x] RDS용 DB subnet 2개 반영
[x] Network output 작성
[x] NAT user_data 분리
[x] 07_servers 초기 골격 작성
[ ] 07_servers에 terraform_remote_state 추가
[ ] 07_servers Security Group 작성
[ ] Bastion Host 작성
[ ] Private Web EC2 작성
[ ] RDS DB Subnet Group 작성
[ ] RDS MariaDB 작성
```

## 28-3. 실행 단계

```text
[ ] 07_networks terraform init
[ ] 07_networks terraform validate
[ ] 07_networks terraform plan
[ ] 07_networks terraform apply
[ ] terraform output으로 Network output 확인
[ ] 07_servers terraform init
[ ] 07_servers terraform validate
[ ] 07_servers terraform plan
[ ] 07_servers terraform apply
[ ] 실습 후 07_servers destroy
[ ] 실습 후 07_networks destroy
```

## 28-4. 증적 요구사항

```text
필수:
- 코드 구조
- 실행 명령
- output과 remote state의 관계 이해
- 생성·삭제 순서 이해

필수 아님:
- 고의적인 오류 로그 확보
- 브라우저 스크린샷
- output 화면 캡처
```

## 28-5. v7.2 판정

```text
v7.2는 Terraform 코드를 Network와 Server라는
두 개의 독립적인 Root Module로 분리하고,
Network의 root output을 Server가 terraform_remote_state로 읽는 구조를 학습하는 버전이다.

이번 실습의 핵심은 리소스를 새로 배우는 것이 아니라,
이미 배운 VPC, NAT, EC2, RDS를 어떤 State 경계로 나누고
그 경계 사이의 데이터를 어떻게 전달하는지 이해하는 데 있다.
```

---

# 29. v7.2 보고서용 한 문단 요약

```text
이번 v7.2 실습에서는 기존에 하나의 Terraform 구성에서 관리하던 VPC, Subnet, NAT, EC2, RDS 리소스를 `07_networks`와 `07_servers`라는 두 개의 독립적인 Root Module로 분리하였다. 같은 디렉터리에 여러 `.tf` 파일을 배치하는 것은 코드 가독성을 위한 파일 분리에 불과하며, Terraform은 이를 하나의 Module과 State로 처리한다. 반면 디렉터리를 분리하여 각각 Terraform을 실행하면 Root Module, State, Dependency Graph, plan/apply/destroy 생명주기가 독립된다. `07_networks`는 VPC와 Subnet ID를 root output으로 공개하고, `07_servers`는 `terraform_remote_state`를 통해 해당 output을 읽어 Bastion, Private Web EC2, RDS를 배치한다. 이 구조는 변경 범위와 관리 책임을 분리할 수 있지만, 두 State 사이의 전체 의존성은 Terraform이 자동 관리하지 않으므로 Network → Server 순서로 생성하고 Server → Network 순서로 삭제해야 한다.
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
- 같은 디렉터리의 최상위 `.tf` 파일들은 하나의 Module로 평가된다.
- 하위 디렉터리는 자동으로 포함되지 않으며 별도 Module로 취급된다.
- Terraform CLI의 Root Module은 일반적으로 Terraform을 실행한 작업 디렉터리다.
- `terraform_remote_state`는 다른 Terraform 구성의 최신 State snapshot에서 root output을 읽는다.
- `terraform_remote_state`는 output만 코드에 노출하지만, 읽기 권한은 State 전체에 대한 접근을 동반할 수 있다.
```

공식 문서:

```text
https://developer.hashicorp.com/terraform/language/functions/templatefile
https://developer.hashicorp.com/terraform/language/meta-arguments/depends_on
https://developer.hashicorp.com/terraform/language/files
https://developer.hashicorp.com/terraform/language/state/remote-state-data
```

---

# 부록 E. 현재 `07_networks/main.tf`

> [!note]- `07_networks/main.tf` - Network Root Module
> ```hcl
> terraform {
>   required_providers {
>     aws = {
>       source  = "hashicorp/aws"
>       version = "~> 6.0"
>     }
>   }
> }
> 
> provider "aws" {
>   region  = "ap-northeast-2"
>   profile = "Terra-user"
> }
> 
> # =============================================================================
> # VPC
> # =============================================================================
> 
> resource "aws_vpc" "vpc" {
>   cidr_block           = "192.168.0.0/16"
>   enable_dns_support   = true
>   enable_dns_hostnames = true
> 
>   tags = {
>     Name = "vpc"
>   }
> }
> 
> # =============================================================================
> # Subnets
> # =============================================================================
> 
> # Public subnet 1: NAT Instance
> resource "aws_subnet" "open_subnet_1" {
>   vpc_id                  = aws_vpc.vpc.id
>   cidr_block              = "192.168.1.0/24"
>   availability_zone       = "ap-northeast-2a"
>   map_public_ip_on_launch = true
> 
>   tags = {
>     Name = "open_subnet_1"
>   }
> }
> 
> # Private subnet 1: Web Server
> resource "aws_subnet" "close_subnet_1" {
>   vpc_id                  = aws_vpc.vpc.id
>   cidr_block              = "192.168.10.0/24"
>   availability_zone       = "ap-northeast-2a"
>   map_public_ip_on_launch = false
> 
>   tags = {
>     Name = "close_subnet_1"
>   }
> }
> 
> # Public subnet 2: Bastion Host 예정
> resource "aws_subnet" "open_subnet_2" {
>   vpc_id                  = aws_vpc.vpc.id
>   cidr_block              = "192.168.2.0/24"
>   availability_zone       = "ap-northeast-2c"
>   map_public_ip_on_launch = true
> 
>   tags = {
>     Name = "open_subnet_2"
>   }
> }
> 
> # Private DB subnet 1: RDS DB subnet group용
> resource "aws_subnet" "db_subnet_1" {
>   vpc_id                  = aws_vpc.vpc.id
>   cidr_block              = "192.168.30.0/24"
>   availability_zone       = "ap-northeast-2a"
>   map_public_ip_on_launch = false
> 
>   tags = {
>     Name = "db_subnet_1"
>   }
> }
> 
> # Private DB subnet 2: RDS DB subnet group용
> resource "aws_subnet" "close_subnet_2" {
>   vpc_id                  = aws_vpc.vpc.id
>   cidr_block              = "192.168.20.0/24"
>   availability_zone       = "ap-northeast-2c"
>   map_public_ip_on_launch = false
> 
>   tags = {
>     Name = "close_subnet_2"
>   }
> }
> 
> # =============================================================================
> # Internet Gateway
> # =============================================================================
> 
> resource "aws_internet_gateway" "gw" {
>   vpc_id = aws_vpc.vpc.id
> 
>   tags = {
>     Name = "internet_gateway"
>   }
> }
> 
> # =============================================================================
> # Public Route Table
> # =============================================================================
> 
> resource "aws_route_table" "public_rt" {
>   vpc_id = aws_vpc.vpc.id
> 
>   route {
>     cidr_block = "0.0.0.0/0"
>     gateway_id = aws_internet_gateway.gw.id
>   }
> 
>   tags = {
>     Name = "public_rt"
>   }
> }
> 
> resource "aws_route_table_association" "public_rt_assoc_1" {
>   subnet_id      = aws_subnet.open_subnet_1.id
>   route_table_id = aws_route_table.public_rt.id
> }
> 
> resource "aws_route_table_association" "public_rt_assoc_2" {
>   subnet_id      = aws_subnet.open_subnet_2.id
>   route_table_id = aws_route_table.public_rt.id
> }
> 
> # =============================================================================
> # Private Route Tables
> # =============================================================================
> 
> # Web subnet: NAT Instance를 통한 일반 outbound 허용
> resource "aws_route_table" "web_private_rt" {
>   vpc_id = aws_vpc.vpc.id
> 
>   tags = {
>     Name = "web_private_rt"
>   }
> }
> 
> resource "aws_route_table_association" "web_private_rt_assoc" {
>   subnet_id      = aws_subnet.close_subnet_1.id
>   route_table_id = aws_route_table.web_private_rt.id
> }
> 
> # DB subnets: 일반 인터넷 기본 경로 없이 격리
> resource "aws_route_table" "db_private_rt" {
>   vpc_id = aws_vpc.vpc.id
> 
>   tags = {
>     Name = "db_private_rt"
>   }
> }
> 
> resource "aws_route_table_association" "db_private_rt_assoc_1" {
>   subnet_id      = aws_subnet.db_subnet_1.id
>   route_table_id = aws_route_table.db_private_rt.id
> }
> 
> resource "aws_route_table_association" "db_private_rt_assoc_2" {
>   subnet_id      = aws_subnet.close_subnet_2.id
>   route_table_id = aws_route_table.db_private_rt.id
> }
> 
> # =============================================================================
> # S3 Gateway Endpoint
> # =============================================================================
> 
> # Web private subnet만 S3 경로를 사용한다.
> resource "aws_vpc_endpoint" "s3" {
>   vpc_id            = aws_vpc.vpc.id
>   service_name      = "com.amazonaws.ap-northeast-2.s3"
>   vpc_endpoint_type = "Gateway"
> 
>   route_table_ids = [
>     aws_route_table.web_private_rt.id
>   ]
> 
>   tags = {
>     Name = "s3_endpoint"
>   }
> }
> 
> # =============================================================================
> # NAT Instance
> # =============================================================================
> 
> resource "aws_security_group" "nat_sg" {
>   name        = "nat_sg"
>   description = "Allow forwarding traffic from the private web subnet"
>   vpc_id      = aws_vpc.vpc.id
> 
>   ingress {
>     description = "Allow traffic from the private web subnet"
>     from_port   = 0
>     to_port     = 0
>     protocol    = "-1"
>     cidr_blocks = [aws_subnet.close_subnet_1.cidr_block]
>   }
> 
>   egress {
>     description = "Allow outbound traffic"
>     from_port   = 0
>     to_port     = 0
>     protocol    = "-1"
>     cidr_blocks = ["0.0.0.0/0"]
>   }
> 
>   tags = {
>     Name = "nat_sg"
>   }
> }
> 
> resource "aws_instance" "nat" {
>   ami                         = "ami-0b1cb107a74bad43e"
>   instance_type               = "t3.micro"
>   subnet_id                   = aws_subnet.open_subnet_1.id
>   key_name                    = "asd-open"
>   vpc_security_group_ids      = [aws_security_group.nat_sg.id]
>   associate_public_ip_address = true
>   source_dest_check           = false
>   private_ip                  = "192.168.1.13"
> 
>   user_data = file("${path.module}/user_data/10-nat.sh")
> 
>   # NAT 부팅 직후 패키지 설치가 필요하므로 Public Route 연결을 먼저 완료한다.
>   depends_on = [
>     aws_route_table_association.public_rt_assoc_1
>   ]
> 
>   tags = {
>     Name = "nat_instance"
>   }
> }
> 
> resource "aws_route" "web_private_default_route" {
>   route_table_id         = aws_route_table.web_private_rt.id
>   destination_cidr_block = "0.0.0.0/0"
>   network_interface_id   = aws_instance.nat.primary_network_interface_id
> }
> 
> # =============================================================================
> # Outputs for 07_servers
> # =============================================================================
> 
> output "vpc_id" {
>   value = aws_vpc.vpc.id
> }
> 
> output "open_subnet_1_id" {
>   value = aws_subnet.open_subnet_1.id
> }
> 
> output "open_subnet_2_id" {
>   value = aws_subnet.open_subnet_2.id
> }
> 
> output "close_subnet_1_id" {
>   value = aws_subnet.close_subnet_1.id
> }
> 
> output "db_subnet_1_id" {
>   value = aws_subnet.db_subnet_1.id
> }
> 
> output "close_subnet_2_id" {
>   value = aws_subnet.close_subnet_2.id
> }
> 
> output "nat_instance_id" {
>   value = aws_instance.nat.id
> }
> 
> output "nat_public_ip" {
>   value = aws_instance.nat.public_ip
> }
> ```

---

# 부록 F. 현재 `07_networks/user_data/10-nat.sh`

> [!note]- `10-nat.sh` - NAT Instance 내부 설정
> ```bash
> #!/bin/bash
> set -euxo pipefail
> 
> IFACE="$(ip route | awk '/default/ {print $5; exit}')"
> 
> # IPv4 forwarding 활성화 및 재부팅 후 유지
> sysctl -w net.ipv4.ip_forward=1
> cat > /etc/sysctl.d/99-nat.conf <<'EOF'
> net.ipv4.ip_forward = 1
> EOF
> 
> # NAT용 iptables 설치
> yum install -y iptables-services
> 
> # 중복 실행 시 같은 규칙을 반복 추가하지 않음
> iptables -t nat -C POSTROUTING -o "$IFACE" -j MASQUERADE 2>/dev/null \
>   || iptables -t nat -A POSTROUTING -o "$IFACE" -j MASQUERADE
> 
> # 규칙 저장 및 서비스 활성화
> service iptables save
> iptables-save > /etc/sysconfig/iptables
> systemctl enable --now iptables
> ```

---

# 부록 G. 현재 `07_servers/main.tf` 골격

> [!note]- `07_servers/main.tf` - State 연동 전 초기 골격
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
> locals {
>   my_ip_cidr = "${chomp(data.http.my_public_ip.response_body)}/32"
> }
> 
> provider "aws" {
>   region  = "ap-northeast-2"
>   profile = "Terra-user"
> }
> 
> # 07_networks
> # - VPC, Sunbet, RouteTable, NAT 등 네트워크 서비스
> 
> # 07_servers
> # - WEB, DB, SG 등 서버 서비스 
> 
> # 진행순서
> # - 07_networks 서비스 구성
> # - 07_servers 서비스 구성
> ```

현재 골격에는 아직 `terraform_remote_state`가 없다.

v7.2에서 다음 블록을 추가한다.

```hcl
data "terraform_remote_state" "network" {
  backend = "local"

  config = {
    path = "${path.module}/../07_networks/terraform.tfstate"
  }
}
```

---

## 관련 노트

- [[00_IaC MOC]]
- [[Terraform AWS CLI 초기 설정 실습 v6.3]]
- [[Terraform Resource와 Data Source]]
- [[Terraform Workflow]]
- [[AWS Security Group의 Stateful 동작]]
- [[Amazon RDS]]
- [[Terraform Backend와 Remote State]]
- [[Terraform Module]]
- [[Terraform State]]
