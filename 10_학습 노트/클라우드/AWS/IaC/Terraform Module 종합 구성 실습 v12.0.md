---
title: Terraform Module 종합 구성 실습
version: v12.0
created: 2026-07-14
updated: 2026-07-14
status: active
type: lab-note
source:
  - Terraform Module 구성 실습 v11.0.md
  - 12_module_quiz/dev/main.tf
  - 12_module_quiz/prod/main.tf
  - 12_module_quiz/modules/networks/main.tf
  - 12_module_quiz/modules/networks/variables.tf
  - 12_module_quiz/modules/networks/output.tf
  - 12_module_quiz/modules/networks/nat_install.tpl
  - 12_module_quiz/modules/servers/main.tf
  - 12_module_quiz/modules/servers/variables.tf
  - 12_module_quiz/modules/servers/output.tf
  - 12_module_quiz/modules/servers/web_install.tpl
  - 12_module_quiz/modules/servers/boot.war
  - Iac.pdf p.42-52
tags:
  - 과목/AWS
  - 주제/IaC
  - 주제/Terraform
  - 주제/Terraform-Module
  - 주제/Root-Module
  - 주제/Child-Module
  - 주제/Composition-Root
  - 주제/Module-Input
  - 주제/Module-Output
  - 주제/Dependency-Graph
  - 주제/AWS-Network
  - 주제/AWS-Server
  - 상태/active
  - 실습/Terraform
---

# Terraform Module 종합 구성 실습 v12.0

> **v12.0 부제:** Networks·Servers 책임 분리와 Dev/Prod 조립

## 목적

이 노트는 v11.0에서 익힌 Local Module의 기본 구조를 짧게 정리한 뒤, 강사의 `12_module_quiz` 소스를 기준으로 기존 종합 AWS 인프라를 `networks`와 `servers` Child Module로 재구성하는 흐름을 분석한다.

이번 단계의 핵심은 다음과 같다.

```text
개별 VPC·Subnet Module 연습
→ 인프라 책임 단위로 Module 확대
→ Networks Module이 네트워크 기반 제공
→ Servers Module이 Compute·DB·Artifact 구성
→ Dev/Prod Root Module이 동일한 Child Module 조립
```

> [!important] 출처 사용 원칙
> 실제 강사 코드와 폴더 구조를 주 근거로 사용한다.  
> `Iac.pdf` p.42~52는 Module 재사용, 환경 분리, Input/Output이라는 개념을 보충하는 참고자료로만 사용한다.  
> 현재 코드에 없는 S3 Backend, `terraform_remote_state`, Registry 외부 Module은 이번 본문의 구현 사실로 기록하지 않는다.

> [!note] 검증 범위
> `12_module_quiz.zip`의 Terraform HCL과 Template을 정적으로 분석했다.  
> `boot.war`는 파일 존재, 크기, Hash만 확인했으며 내부 애플리케이션 코드는 분석하지 않았다.  
> `terraform fmt`, `init`, `validate`, `plan`, `apply` 결과는 확인하지 않았다.

---

## 이전 진도 요약: v11.0

v11에서는 Module의 가장 작은 연결 구조를 확인했다.

```text
Stage/Prod Root Module
├─ VPC Child Module
└─ Subnet Child Module
```

VPC Child Module은 `vpc-id`, `vpc-cidr`를 Output으로 공개하고, Root Module은 이를 Subnet Child Module의 Input으로 전달했다.

```text
VPC Module Output
→ Root Module의 module 참조
→ Subnet Module Input
```

v12에서는 같은 원리를 더 큰 책임 단위에 적용한다.

```text
v11:
VPC와 Subnet을 개별 Module로 분리

v12:
네트워크 전체를 Networks Module로 묶고
서버·DB·배포 구성을 Servers Module로 묶음
```

따라서 v12의 핵심은 Module 문법을 새로 배우는 것이 아니라, **어디까지를 하나의 Module 책임으로 묶을지 판단하고 Root Module에서 조립하는 것**이다.

---

## 빠른 이동

> - [[#Part 1. Module 종합 구성의 목적|Part 1. 종합 구성의 목적]]
> - [[#Part 2. Networks Child Module|Part 2. Networks Module]]
> - [[#Part 3. Servers Child Module|Part 3. Servers Module]]
> - [[#Part 4. Root Module 조립|Part 4. Dev/Prod 조립]]
> - [[#19. Networks Output → Servers Input|Module 계약 연결]]
> - [[#23. 전체 Module Dependency Graph|전체 의존성]]
> - [[#26. 현재 코드의 확인 필요 항목|확인 필요 항목]]
> - [[#28. v12.0 완료 판정|완료 판정]]
> - [[#Appendices|부록]]

---

# Part 1. Module 종합 구성의 목적

## 1. v11 기초에서 v12 종합 구성으로

v11은 Module의 기본 Interface를 학습하는 단계였다.

```text
variable:
외부 입력

resource:
Module 내부 구현

output:
외부 공개 값

module Block:
Child Module 호출
```

v12는 이 기본 문법을 실제 종합 인프라에 적용한다.

```text
Network 관련 Resource 14개
→ modules/networks

Server·DB·Artifact 관련 Resource 12개
→ modules/servers

환경별 값과 Module 연결
→ dev, prod Root Module
```

학습 초점:

```text
Module을 만드는 방법
→ 어떤 책임을 Module로 묶을 것인가
→ Module 사이에 어떤 값만 공개할 것인가
→ 환경별 Root가 공통 구현을 어떻게 조립할 것인가
```

---

## 2. 전체 폴더 구조

```text
12_module_quiz/
├─ dev/
│  └─ main.tf
├─ prod/
│  └─ main.tf
└─ modules/
   ├─ networks/
   │  ├─ main.tf
   │  ├─ variables.tf
   │  ├─ output.tf
   │  └─ nat_install.tpl
   └─ servers/
      ├─ main.tf
      ├─ variables.tf
      ├─ output.tf
      ├─ web_install.tpl
      └─ boot.war
```

역할:

| 경로 | 역할 |
|---|---|
| `dev/` | Dev 환경 Root Module |
| `prod/` | Prod 환경 Root Module |
| `modules/networks/` | 공통 Network Child Module |
| `modules/servers/` | 공통 Server·DB·배포 Child Module |

`dev`와 `prod`에는 AWS Resource가 직접 정의되지 않는다. 실제 Resource 구현은 Child Module 안에 있다.

---

## 3. Root Module과 Composition Root

이번 `dev/main.tf`, `prod/main.tf`는 단순 실행 폴더를 넘어 **조립 계층**의 역할을 한다.

Root Module이 결정하는 것:

```text
- AWS Provider와 Profile
- 환경 이름
- 환경별 VPC CIDR
- 어떤 Child Module을 호출할지
- Networks Output을 Servers Input에 어떻게 연결할지
```

Child Module이 담당하는 것:

```text
- Resource 구현
- 내부 Resource 참조
- 환경 이름을 이용한 Resource Naming
- 외부에 공개할 Output 정의
```

이를 Composition Root 관점으로 표현하면:

```text
dev 또는 prod
│
├─ networks 구현 선택 및 입력 전달
├─ servers 구현 선택 및 입력 전달
└─ 두 Module 사이의 계약 연결
```

> [!note] 용어
> `Composition Root`는 Terraform의 별도 문법이 아니라, 애플리케이션이나 인프라 구성요소를 최상위에서 조립하는 설계 관점이다.  
> 현재 Root Module의 역할을 설명하기 위한 해석이다.

---

## 4. Networks와 Servers의 책임 경계

### Networks Module

소유 Resource:

```text
VPC
Public Subnet 2개
Private Subnet 2개
Internet Gateway
Public Route Table
Public Route Table Association 2개
NAT Instance
NAT Security Group
Private Route Table
Private Route Table Association 2개
```

책임:

```text
주소 공간
AZ별 Subnet
Public/Private Routing
Internet Gateway
Private Outbound용 NAT Instance
```

### Servers Module

소유 Resource:

```text
Bastion EC2
Web EC2
Bastion Security Group
Web Security Group
RDS Security Group
RDS DB Instance
DB Subnet Group
S3 Bucket
S3 Object
IAM Role
IAM Inline Policy
IAM Instance Profile
```

책임:

```text
관리 접속
애플리케이션 실행
데이터베이스
Artifact 저장과 전달
EC2의 S3 접근 권한
초기 설치 Script
```

Module 경계는 단순히 AWS 서비스 이름을 나누는 것이 아니라, **함께 생성되고 서로 밀접하게 참조되는 책임 묶음**으로 구성됐다.

---

## 5. Dev와 Prod 환경 재사용

Dev와 Prod는 동일한 Child Module 소스를 호출한다.

```hcl
source = "../modules/networks"
source = "../modules/servers"
```

환경별 차이는 두 값뿐이다.

| 항목 | Dev | Prod |
|---|---|---|
| `env` | `dev` | `prod` |
| VPC CIDR | `192.168.0.0/16` | `10.0.0.0/16` |

그 외 Resource 구조는 같다.

```text
Dev:
dev-vpc
dev-public-subnet-2a
dev-web-instance
dev-1 RDS
dev-boot-bucket-2026

Prod:
prod-vpc
prod-public-subnet-2a
prod-web-instance
prod-1 RDS
prod-boot-bucket-2026
```

즉 환경별 코드를 복사해 별도로 유지하는 것이 아니라:

```text
공통 구현:
modules/networks
modules/servers

환경 차이:
dev/main.tf
prod/main.tf
```

로 분리한다.

---

# Part 2. Networks Child Module

## 6. Networks Module의 입력 Interface

`modules/networks/variables.tf`:

```hcl
variable "vpc-cidr" {
  type = string
}

variable "env" {
  type = string
}
```

입력 계약:

| 입력 | 역할 |
|---|---|
| `vpc-cidr` | 환경별 VPC 주소 공간 |
| `env` | Resource 이름 Prefix |

Networks Module은 Dev 또는 Prod를 직접 판단하지 않는다. Root Module이 전달한 값만 사용한다.

```text
Dev Root:
vpc-cidr = 192.168.0.0/16
env      = dev

Prod Root:
vpc-cidr = 10.0.0.0/16
env      = prod
```

---

## 7. VPC와 Public/Private Subnet

VPC:

```hcl
resource "aws_vpc" "module-vpc" {
  cidr_block           = var.vpc-cidr
  tags                 = { Name = "${var.env}-vpc" }
  enable_dns_hostnames = true
  enable_dns_support   = true
}
```

Subnet 구성:

| Subnet | `cidrsubnet()` 번호 | AZ | Public IP 자동 할당 |
|---|---:|---|---|
| Public 2a | 10 | `ap-northeast-2a` | 활성 |
| Public 2c | 30 | `ap-northeast-2c` | 활성 |
| Private 2a | 11 | `ap-northeast-2a` | 비활성 |
| Private 2c | 31 | `ap-northeast-2c` | 비활성 |

Dev 기준:

```text
VPC:
192.168.0.0/16

Public 2a:
192.168.10.0/24

Private 2a:
192.168.11.0/24

Public 2c:
192.168.30.0/24

Private 2c:
192.168.31.0/24
```

Prod 기준:

```text
VPC:
10.0.0.0/16

Public 2a:
10.0.10.0/24

Private 2a:
10.0.11.0/24

Public 2c:
10.0.30.0/24

Private 2c:
10.0.31.0/24
```

---

## 8. Internet Gateway와 Public Route

Internet Gateway:

```hcl
resource "aws_internet_gateway" "module-igw" {
  vpc_id = aws_vpc.module-vpc.id
}
```

Public Route Table:

```hcl
route {
  gateway_id = aws_internet_gateway.module-igw.id
  cidr_block = "0.0.0.0/0"
}
```

두 Public Subnet은 동일한 Public Route Table에 연결된다.

```text
Public Subnet 2a ─┐
                  ├─ Public Route Table → Internet Gateway
Public Subnet 2c ─┘
```

Networks Module 내부 참조만으로 다음 의존성이 만들어진다.

```text
VPC
→ Internet Gateway
→ Public Route Table
→ Route Table Association
```

---

## 9. NAT Instance와 Private Route

NAT Instance는 Public Subnet 2a에 생성된다.

```hcl
resource "aws_instance" "module-nat-instance" {
  subnet_id        = aws_subnet.module-public-subnet-2a.id
  source_dest_check = false
  user_data         = templatefile("${path.module}/nat_install.tpl", {})
}
```

`nat_install.tpl`:

```bash
echo "net.ipv4.ip_forward = 1" | sudo tee -a /etc/sysctl.d/99-custom-nat.conf
sudo sysctl -p /etc/sysctl.d/99-custom-nat.conf
IFACE=$(ip route show default | awk '/default/ {print $5}')
sudo iptables -t nat -A POSTROUTING -o $IFACE -j MASQUERADE
```

Private Route Table:

```hcl
route {
  cidr_block           = "0.0.0.0/0"
  network_interface_id = aws_instance.module-nat-instance.primary_network_interface_id
}
```

경로:

```text
Private Subnet 2a ─┐
                   ├─ Private Route Table
Private Subnet 2c ─┘
                          │
                          ▼
                NAT Instance ENI
                          │
                          ▼
                 Public Subnet 2a
                          │
                          ▼
                 Internet Gateway
```

현재 구조에서는 두 AZ의 Private Subnet이 하나의 2a NAT Instance를 공유한다.

---

## 10. Networks Module Output

`modules/networks/output.tf`은 Servers Module에 필요한 Network ID만 공개한다.

```hcl
output "vpc-id" {
  value = aws_vpc.module-vpc.id
}

output "public-subnet-2a-id" {
  value = aws_subnet.module-public-subnet-2a.id
}

output "public-subnet-2c-id" {
  value = aws_subnet.module-public-subnet-2c.id
}

output "private-subnet-2a-id" {
  value = aws_subnet.module-private-subnet-2a.id
}

output "private-subnet-2c-id" {
  value = aws_subnet.module-private-subnet-2c.id
}
```

Output 계약표:

| Output | 소비 위치 |
|---|---|
| `vpc-id` | Servers Module의 Security Group |
| `public-subnet-2a-id` | Servers Input으로 전달되지만 현재 내부에서 미사용 |
| `public-subnet-2c-id` | Bastion EC2 |
| `private-subnet-2a-id` | Web EC2, RDS DB Subnet Group |
| `private-subnet-2c-id` | RDS DB Subnet Group |

Output은 Networks Module 내부 Resource를 외부에 전부 노출하는 것이 아니라, 다음 Module이 실제로 필요로 하는 식별자를 Interface로 공개한다.

---

## 11. Networks Module의 Dependency Graph

```text
aws_vpc.module-vpc
├─ Public Subnet 2a
├─ Public Subnet 2c
├─ Private Subnet 2a
├─ Private Subnet 2c
├─ Internet Gateway
└─ NAT Security Group

Public Subnet 2a
└─ NAT Instance

NAT Security Group
└─ NAT Instance

Internet Gateway
└─ Public Route Table
   ├─ Public Association 2a
   └─ Public Association 2c

NAT Instance Primary ENI
└─ Private Route Table
   ├─ Private Association 2a
   └─ Private Association 2c
```

Networks Module은 외부 Module에 의존하지 않는다. Root에서 받은 `env`, `vpc-cidr`만으로 내부 Graph를 완성한다.

---

# Part 3. Servers Child Module

## 12. Servers Module의 입력 Interface

`modules/servers/variables.tf`:

```text
env
vpc-id
public-subnet-2a-id
public-subnet-2c-id
private-subnet-2a-id
private-subnet-2c-id
```

입력 계약:

| 입력 | 현재 사용 |
|---|---|
| `env` | Resource 이름 |
| `vpc-id` | 모든 Security Group |
| `public-subnet-2a-id` | 현재 내부에서 미사용 |
| `public-subnet-2c-id` | Bastion EC2 |
| `private-subnet-2a-id` | Web EC2, RDS Subnet Group |
| `private-subnet-2c-id` | RDS Subnet Group |

Servers Module은 VPC나 Subnet Resource를 직접 생성하지 않는다.  
필요한 Network 식별자를 Input으로 받는다.

---

## 13. Bastion과 Web EC2

### Bastion

```hcl
resource "aws_instance" "module-bastion-instance" {
  subnet_id              = var.public-subnet-2c-id
  vpc_security_group_ids = [aws_security_group.module-bastion-sg.id]
}
```

배치:

```text
Public Subnet 2c
```

역할:

```text
Private 영역 관리 접속의 진입점
```

### Web EC2

```hcl
resource "aws_instance" "module-web-instance" {
  subnet_id              = var.private-subnet-2a-id
  vpc_security_group_ids = [aws_security_group.module-web-sg.id]
  iam_instance_profile   = aws_iam_instance_profile.module-instance-profile.name
}
```

배치:

```text
Private Subnet 2a
```

Web EC2는 다음 Resource에 의존한다.

```text
Web Security Group
IAM Instance Profile
RDS Endpoint
S3 Bucket
web_install.tpl
boot.war Object
```

`user_data`의 Template 입력:

```hcl
TOMCAT_VERSION = "10.1.57"
RDS_ENDPOINT   = aws_db_instance.module-rds-instance.address
DB_PASSWORD    = "mariaPass"
DB_USER        = "admin"
S3_BUCKET      = aws_s3_bucket.module-s3-bucket.id
```

---

## 14. Security Group 연결

### Bastion Security Group

```text
Inbound:
TCP 22
Source 0.0.0.0/0

Outbound:
All
```

### Web Security Group

```text
Inbound:
TCP 8080 from 0.0.0.0/0
TCP 22 from 0.0.0.0/0

Outbound:
All
```

### RDS Security Group

```hcl
ingress {
  from_port       = 3306
  to_port         = 3306
  protocol        = "TCP"
  security_groups = [aws_security_group.module-web-sg.id]
}
```

RDS는 CIDR가 아니라 Web Security Group을 Source로 사용한다.

```text
Web SG가 연결된 ENI
→ TCP 3306
→ RDS
```

이 연결은 Servers Module 내부 Graph로 처리된다.

---

## 15. RDS와 DB Subnet Group

DB Subnet Group:

```hcl
subnet_ids = [
  var.private-subnet-2a-id,
  var.private-subnet-2c-id
]
```

의미:

```text
RDS가 사용할 Subnet 후보를 두 AZ에 제공
```

RDS:

```hcl
resource "aws_db_instance" "module-rds-instance" {
  engine                 = "mariadb"
  engine_version         = "11.8"
  instance_class         = "db.t3.micro"
  db_name                = "care"
  username               = "admin"
  password               = "mariaPass"
  db_subnet_group_name   = aws_db_subnet_group.module-rds-subnet-group.id
  vpc_security_group_ids = [aws_security_group.module-rds-sg.id]
}
```

Resource 이름은 환경별로 분리된다.

```text
Dev:
identifier = dev-1

Prod:
identifier = prod-1
```

현재 `skip_final_snapshot = true`이므로 Destroy 시 최종 Snapshot을 남기지 않는다. 실습 종료를 단순화하기 위한 설정으로 볼 수 있지만 데이터 보존을 요구하는 환경에는 적합하지 않다.

---

## 16. S3 Artifact와 IAM Instance Profile

S3 Bucket:

```hcl
bucket = "${var.env}-boot-bucket-2026"
```

S3 Object:

```hcl
key    = "boot.war"
source = "${path.module}/boot.war"
etag   = filemd5("${path.module}/boot.war")
```

Artifact 흐름:

```text
modules/servers/boot.war
→ Terraform이 S3 Object로 업로드
→ Web EC2의 IAM Role
→ user_data에서 aws s3 cp
→ Tomcat webapps에 배포
```

IAM 흐름:

```text
IAM Role
→ Inline Policy
→ Instance Profile
→ Web EC2
```

현재 Policy:

```hcl
Action   = ["s3:GetObject"]
Resource = "*"
```

학습용으로 단순하지만, Module이 생성한 Bucket Object ARN으로 Scope를 제한할 수 있다.

---

## 17. `templatefile()`과 Web 초기화

`web_install.tpl`의 주요 단계:

```text
1. Swap 2GB 생성
2. Java 17 설치
3. Tomcat 10.1.57 설치
4. systemd Service 등록
5. MariaDB Client 설치
6. RDS 응답 대기
7. care Database와 Table 생성
8. AWS CLI 설치
9. S3에서 boot.war 다운로드
10. Application 압축 해제 대기
11. application.properties 수정
12. Tomcat 재시작
```

Terraform 참조로 형성되는 의존성:

```text
RDS Address
S3 Bucket ID
IAM Instance Profile
→ Web EC2 user_data 생성
→ Web EC2 생성
```

`templatefile()`에 전달된 값:

```text
TOMCAT_VERSION
RDS_ENDPOINT
DB_PASSWORD
DB_USER
S3_BUCKET
```

Template 초반과 DB 초기화는 전달값을 사용한다.

---

## 18. Servers Module의 내부 Dependency Graph

```text
var.vpc-id
├─ Bastion SG
├─ Web SG
└─ RDS SG

var.public-subnet-2c-id
└─ Bastion EC2
   └─ Bastion SG

var.private-subnet-2a-id
├─ Web EC2
└─ RDS DB Subnet Group

var.private-subnet-2c-id
└─ RDS DB Subnet Group

Web SG
└─ RDS SG

RDS DB Subnet Group
RDS SG
└─ RDS Instance
   └─ RDS Endpoint
      └─ Web EC2 user_data

S3 Bucket
└─ S3 Object boot.war

IAM Role
├─ IAM Inline Policy
└─ IAM Instance Profile
   └─ Web EC2
```

Servers Module은 하나의 큰 Module이지만 내부 Resource 참조를 통해 생성 순서를 계산할 수 있다.

---

# Part 4. Root Module 조립

## 19. Networks Output → Servers Input

Dev와 Prod Root Module은 동일한 연결을 사용한다.

```hcl
module "servers" {
  source               = "../modules/servers"
  env                  = var.env
  vpc-id               = module.networks.vpc-id
  public-subnet-2a-id  = module.networks.public-subnet-2a-id
  public-subnet-2c-id  = module.networks.public-subnet-2c-id
  private-subnet-2a-id = module.networks.private-subnet-2a-id
  private-subnet-2c-id = module.networks.private-subnet-2c-id
}
```

이 코드는 Module 계약의 연결 지점이다.

```text
Networks Output 이름
= Root에서 참조하는 이름
= Servers Input에 전달하는 값
```

데이터 흐름:

```text
Networks 내부 Resource
→ Networks Output
→ Root Module
→ Servers Input
→ Servers 내부 Resource
```

Child Module이 서로의 내부 Resource를 직접 참조하지 않는다. Root Module이 명시적으로 연결한다.

---

## 20. Dev Root Module

Dev 입력:

```hcl
variable "env" {
  default = "dev"
}

module "networks" {
  env      = var.env
  vpc-cidr = "192.168.0.0/16"
}
```

Dev Root의 역할:

```text
AWS Provider 선택
환경 이름 dev 지정
VPC CIDR 192.168.0.0/16 지정
Networks Module 호출
Networks Output을 Servers Module에 전달
```

예상 Resource Naming:

```text
dev-vpc
dev-public-subnet-2a
dev-private-subnet-2a
dev-nat-instance
dev-bastion-instance
dev-web-instance
dev-1
```

---

## 21. Prod Root Module

Prod 입력:

```hcl
variable "env" {
  default = "prod"
}

module "networks" {
  env      = var.env
  vpc-cidr = "10.0.0.0/16"
}
```

Prod Root는 Dev와 동일한 Module Graph를 사용하며 입력값만 다르다.

예상 Resource Naming:

```text
prod-vpc
prod-public-subnet-2a
prod-private-subnet-2a
prod-nat-instance
prod-bastion-instance
prod-web-instance
prod-1
```

Dev와 Prod의 코드 차이:

```text
env 기본값
VPC CIDR
```

Module Source와 Module 연결 구조는 동일하다.

---

## 22. Dev와 Prod의 State 경계

`dev`와 `prod`는 서로 다른 Root Module 디렉터리다.

기본 Local Backend라면:

```text
dev/terraform.tfstate
└─ module.networks
└─ module.servers

prod/terraform.tfstate
└─ module.networks
└─ module.servers
```

정리:

```text
Networks와 Servers:
Child Module은 분리됐지만 같은 환경 State에 함께 기록

Dev와 Prod:
Root Module이 다르므로 State도 별도
```

현재 코드에는 S3 Backend가 없다.

```text
현재:
환경별 Local State가 예상됨

PDF 후속 진도:
S3 Backend와 환경별 Key

이번 코드의 직접 관찰:
Remote Backend 미구현
```

---

## 23. 전체 Module Dependency Graph

```text
Dev 또는 Prod Root Module
│
├─ module.networks
│  ├─ VPC
│  ├─ Public/Private Subnet
│  ├─ IGW
│  ├─ NAT Instance
│  └─ Public/Private Route
│
│  Outputs
│  ├─ vpc-id
│  ├─ public-subnet-2a-id
│  ├─ public-subnet-2c-id
│  ├─ private-subnet-2a-id
│  └─ private-subnet-2c-id
│
└─ module.servers
   ├─ Bastion
   ├─ Web EC2
   ├─ Security Groups
   ├─ RDS
   ├─ S3 Artifact
   └─ IAM Role/Profile
```

Root의 Module Input 참조 때문에 다음 순서가 형성된다.

```text
Networks Module의 Output 계산 가능
→ Servers Module Input 확정
→ Servers Module Resource 생성
```

따라서 Module Block의 물리적 작성 순서가 아니라 `module.networks.*` 참조가 의존성을 만든다.

---

# Part 5. 코드 검토와 학습 판정

## 24. 직접 관찰된 구현

### Root Module

```text
[x] Dev와 Prod 분리
[x] 공통 Networks Module 호출
[x] 공통 Servers Module 호출
[x] 환경별 `env`와 VPC CIDR 분리
[x] Networks Output → Servers Input 연결
```

### Networks Module

```text
[x] VPC
[x] Public Subnet 2개
[x] Private Subnet 2개
[x] Internet Gateway
[x] Public Route Table과 Association
[x] NAT Instance
[x] NAT Security Group
[x] Private Route Table과 Association
[x] VPC/Subnet ID Output
```

### Servers Module

```text
[x] Bastion EC2
[x] Web EC2
[x] Bastion/Web/RDS Security Group
[x] RDS DB Instance와 DB Subnet Group
[x] S3 Bucket과 boot.war Object
[x] IAM Role·Policy·Instance Profile
[x] Web 설치 Template
[ ] Servers Output
```

---

## 25. 강사의 교육 의도

> [!note] 교육 흐름 해석
> 아래는 폴더 구조, Resource 소유권, Input/Output 연결을 바탕으로 한 해석이다.  
> 강사가 명시한 문장을 그대로 옮긴 것은 아니다.

핵심 의도:

```text
1. 기존 종합 인프라를 Module 구조로 리팩터링
2. 네트워크와 서버 책임을 분리
3. Root Module을 환경별 조립 계층으로 단순화
4. Module 내부 구현을 Dev/Prod가 공유
5. Output과 Input으로 Module 계약 형성
6. 참조를 통해 Module Dependency Graph 구성
```

v11과의 차이:

```text
v11:
Module 문법과 작은 연결 구조를 이해

v12:
실제 서비스 인프라 전체에 Module 경계를 적용
```

PDF p.42 이후의 Stage/Prod 재사용 개념과는 연결되지만, 이번 코드에는 Backend, Remote State, Registry Module이 아직 나타나지 않는다.

---

## 26. 현재 코드의 확인 필요 항목

### 26-1. Web 설정의 RDS Endpoint 하드코딩

Template은 RDS Endpoint를 입력받는다.

```bash
RDS_ENDPOINT="${RDS_ENDPOINT}"
```

DB 준비 대기와 초기화에도 사용한다.

그러나 최종 `application.properties`에는 특정 Endpoint가 하드코딩돼 있다.

```bash
spring.datasource.url=jdbc:mariadb://database-1.cji0a2aaa6bd.ap-northeast-2.rds.amazonaws.com:3306/care
```

현재 Dev/Prod Module이 새로 생성한 RDS를 사용하려는 의도라면 이 값은 불일치할 수 있다.

의도상 연결:

```text
aws_db_instance.module-rds-instance.address
→ RDS_ENDPOINT Template 변수
→ application.properties URL
```

### 26-2. DB Credential 하드코딩

현재 값:

```text
username = admin
password = mariaPass
```

노출 위치:

```text
Terraform Configuration
Terraform State
EC2 user_data
Web 설정 파일
```

교육용 실습 값으로 볼 수 있으나 운영형 설계에서는 Secret Manager, SSM Parameter Store 또는 별도 Sensitive Input 검토가 필요하다.

### 26-3. `servers/output.tf`가 비어 있음

Servers Module은 현재 외부 Output이 없다.

현재 Root나 다른 Module이 Servers 결과를 사용하지 않으므로 실행상 필수는 아니다.

후속 후보:

```text
Bastion Public IP
Web Private IP
RDS Endpoint
S3 Bucket Name
```

### 26-4. 전달되지만 사용되지 않는 Public Subnet 2a ID

Root는 다음 값을 Servers Module에 전달한다.

```hcl
public-subnet-2a-id = module.networks.public-subnet-2a-id
```

그러나 현재 Servers Module 내부에서는 `var.public-subnet-2a-id`를 사용하지 않는다.

```text
Public 2a:
Networks Module의 NAT Instance가 사용

Public 2c:
Servers Module의 Bastion이 사용
```

불필요한 Input인지, 향후 Resource 추가를 위한 준비인지 현재 코드만으로 확정하지 않는다.

### 26-5. 단일 NAT Instance

```text
Private 2a
Private 2c
→ 하나의 2a NAT Instance
```

학습용 단순 구조로는 가능하지만 다음 특성이 있다.

```text
2c Private Subnet의 Cross-AZ 경로
단일 장애 지점
AZ 간 Data Transfer 가능성
```

### 26-6. Security Group 허용 범위

```text
Bastion SSH:
0.0.0.0/0

Web SSH:
0.0.0.0/0

Web 8080:
0.0.0.0/0
```

Module 학습 자체와는 별개지만 운영 환경에서는 Source를 최소화해야 한다.

후속 구조 후보:

```text
Bastion SSH:
관리자 공인 IP/32

Web SSH:
Bastion Security Group

Web 8080:
ALB Security Group 또는 필요한 대역
```

### 26-7. S3 Bucket 이름의 전역 유일성

```hcl
bucket = "${var.env}-boot-bucket-2026"
```

S3 Bucket 이름은 계정 내부가 아니라 전역 Namespace에서 고유해야 한다. 실제 `plan/apply`에서 이름 충돌 여부를 확인해야 한다.

### 26-8. S3 IAM Policy Scope

현재:

```hcl
Action   = ["s3:GetObject"]
Resource = "*"
```

Web EC2가 다운로드할 대상은 Module이 생성한 Bucket의 `boot.war`이므로 Object ARN으로 Scope를 줄일 수 있다.

### 26-9. Template Script의 실행 안정성

현재 `until` Loop는 제한 시간이 없다.

```text
RDS가 계속 준비되지 않음
→ user_data가 계속 대기

Application이 압축 해제되지 않음
→ Loop가 계속 대기
```

실습에서는 Resource 준비를 기다리는 기능이지만 Timeout과 오류 처리를 추가하면 실패 원인을 더 명확히 알 수 있다.

### 26-10. Region·AMI·Key Pair·RDS Version

현재 코드는 AWS Profile에 Region 설정을 의존한다.

또한 다음 값은 대상 계정과 Region에서 실제 사용 가능한지 `plan`으로 확인해야 한다.

```text
AMI ID
Key Pair 이름
MariaDB Engine Version
Default Parameter Group
```

이 항목들은 정적 코드만으로 성공을 확정하지 않는다.

---

## 27. 실행 전 비용과 검증 항목

한 환경을 Apply할 경우 주요 비용 발생 후보:

```text
NAT EC2 1대
Bastion EC2 1대
Web EC2 1대
RDS 1대
EBS Volume
Public IPv4
S3 Storage·Request
Data Transfer
```

Dev와 Prod를 동시에 Apply하면 같은 구조가 각각 생성된다.

실행 순서:

```powershell
cd dev
terraform init
terraform fmt -recursive
terraform validate
terraform plan
```

Plan에서 확인할 내용:

```text
- Resource 총 생성 수
- Dev/Prod Resource Name
- VPC와 Subnet CIDR
- Bastion과 NAT의 Public Subnet 배치
- Web의 Private Subnet 배치
- RDS DB Subnet Group의 두 AZ
- S3 Bucket 이름 충돌
- AMI·Key Pair·RDS Version 유효성
- User Data Template 렌더링
```

실습 종료 후:

```powershell
terraform destroy
```

주의:

```text
Dev와 Prod는 Root Module과 State가 별도이므로
각 환경 디렉터리에서 별도로 Destroy해야 한다.
```

---

## 28. v12.0 완료 판정

### 28-1. Module 설계 이해

```text
[x] Root Module을 환경별 Composition Root로 이해
[x] Networks와 Servers 책임 경계 이해
[x] Input/Output을 Module 계약으로 이해
[x] Module 내부 Resource 소유권 구분
[x] Networks → Servers 의존성 이해
[x] Module 분리와 State 분리의 차이 이해
```

### 28-2. 코드 구조 분석

```text
[x] Dev/Prod Root Module 확인
[x] Networks Module Resource 14개 확인
[x] Networks Output 5개 확인
[x] Servers Module Resource 12개 확인
[x] Servers Input 6개 확인
[x] NAT와 Private Route 연결 확인
[x] RDS·S3·IAM·Web Template 연결 확인
[x] boot.war Artifact 존재 확인
```

### 28-3. 실행 검증

```text
[ ] terraform fmt
[ ] Dev terraform init
[ ] Dev terraform validate
[ ] Dev terraform plan
[ ] Dev terraform apply
[ ] Dev 기능 검증
[ ] Dev terraform destroy
[ ] Prod terraform init
[ ] Prod terraform validate
[ ] Prod terraform plan
[ ] Prod terraform apply
[ ] Prod 기능 검증
[ ] Prod terraform destroy
```

### 28-4. 최종 판정

```text
v12.0은 기존 종합 AWS 인프라를
Networks와 Servers Child Module로 재구성한
Module 종합 퀴즈의 설계 및 정적 분석 단계로 완료했다.

Dev와 Prod Root Module은 같은 Child Module 구현을 재사용하며,
Networks Module의 VPC/Subnet Output을
Servers Module의 Input으로 전달한다.

다만 Terraform CLI와 AWS에서 실행한 결과는 확인하지 않았으므로
실제 인프라 배포 완료로 판정하지 않는다.
```

---

## 29. 한 문단 요약

```text
v12.0에서는 v11에서 배운 Local Module의 Input·Output 연결을 기존 종합 AWS 인프라 전체로 확장하였다. `modules/networks`는 VPC, AZ별 Public/Private Subnet, Internet Gateway, Public/Private Route Table, NAT Instance를 소유하고 VPC와 Subnet ID를 Output으로 공개한다. `modules/servers`는 해당 Output을 Input으로 받아 Bastion, Web EC2, Security Group, RDS, S3 Artifact, IAM Role과 Instance Profile을 구성한다. Dev와 Prod Root Module은 Resource를 직접 구현하지 않고 환경 이름과 VPC CIDR을 전달하며 두 Child Module을 조립하는 Composition Root 역할을 한다. 이 구조를 통해 공통 인프라 구현을 환경별로 재사용하고, Module 내부 구현과 외부 계약, Resource 소유권, 환경별 State 경계를 분리하는 방법을 확인하였다. 현재 코드에서는 Web 설정의 RDS Endpoint 하드코딩, DB Credential 노출, 단일 NAT, Security Group 범위, 빈 Servers Output 등의 확인 항목이 남아 있으며 실제 `validate`, `plan`, `apply` 결과는 아직 검증하지 않았다.
```

---

# Appendices

## 부록 A. 전체 폴더 구조

```text
12_module_quiz/
├─ dev/
│  └─ main.tf
├─ prod/
│  └─ main.tf
└─ modules/
   ├─ networks/
   │  ├─ main.tf
   │  ├─ variables.tf
   │  ├─ output.tf
   │  └─ nat_install.tpl
   └─ servers/
      ├─ main.tf
      ├─ variables.tf
      ├─ output.tf
      ├─ web_install.tpl
      └─ boot.war
```

`boot.war` 확인 정보:

```text
Size:
44,398,352 bytes

SHA-256:
53d09cecee76279be6b31b4a4a14ff5c512fc1301b6c5ec492583abe752510db
```

---

## 부록 B. Module Input/Output 계약표

### Root → Networks

| Input | Dev | Prod |
|---|---|---|
| `env` | `dev` | `prod` |
| `vpc-cidr` | `192.168.0.0/16` | `10.0.0.0/16` |

### Networks → Root → Servers

| Networks Output | Servers Input | 사용 Resource |
|---|---|---|
| `vpc-id` | `vpc-id` | Bastion/Web/RDS SG |
| `public-subnet-2a-id` | `public-subnet-2a-id` | 현재 미사용 |
| `public-subnet-2c-id` | `public-subnet-2c-id` | Bastion EC2 |
| `private-subnet-2a-id` | `private-subnet-2a-id` | Web EC2, DB Subnet Group |
| `private-subnet-2c-id` | `private-subnet-2c-id` | DB Subnet Group |

---

## 부록 C. Resource 소유권 지도

| Module | Resource Type | Terraform Label |
|---|---|---|
| Networks | VPC | `module-vpc` |
| Networks | Public Subnet | `module-public-subnet-2a`, `module-public-subnet-2c` |
| Networks | Private Subnet | `module-private-subnet-2a`, `module-private-subnet-2c` |
| Networks | Internet Gateway | `module-igw` |
| Networks | Public Route Table | `module-public-rt` |
| Networks | Public Association | `module-public-rt-2a`, `module-public-rt-2c` |
| Networks | Private Route Table | `module-private-rt` |
| Networks | Private Association | `module-private-rt-2a`, `module-private-rt-2c` |
| Networks | NAT EC2 | `module-nat-instance` |
| Networks | NAT Security Group | `module-nat-sg` |
| Servers | Bastion EC2 | `module-bastion-instance` |
| Servers | Web EC2 | `module-web-instance` |
| Servers | Security Group | `module-bastion-sg`, `module-web-sg`, `module-rds-sg` |
| Servers | RDS | `module-rds-instance` |
| Servers | DB Subnet Group | `module-rds-subnet-group` |
| Servers | S3 Bucket/Object | `module-s3-bucket`, `module-boot-object` |
| Servers | IAM Role/Policy/Profile | `module-s3-role`, `module-s3-role-policy`, `module-instance-profile` |

---

## 부록 D. 최신 강사 코드 원문


### `dev/main.tf`

```hcl
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }
}

provider "aws" {
  profile = "terra-user"
}

variable "env" {
  default = "dev"
  type    = string
}

module "networks" {
  source   = "../modules/networks"
  env      = var.env
  vpc-cidr = "192.168.0.0/16"
}
module "servers" {
  source               = "../modules/servers"
  env                  = var.env
  vpc-id               = module.networks.vpc-id
  public-subnet-2a-id  = module.networks.public-subnet-2a-id
  public-subnet-2c-id  = module.networks.public-subnet-2c-id
  private-subnet-2a-id = module.networks.private-subnet-2a-id
  private-subnet-2c-id = module.networks.private-subnet-2c-id
}
```

### `prod/main.tf`

```hcl
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }
}

provider "aws" {
  profile = "terra-user"
}

variable "env" {
  default = "prod"
  type    = string
}

module "networks" {
  source   = "../modules/networks"
  env      = var.env
  vpc-cidr = "10.0.0.0/16"
}
module "servers" {
  source               = "../modules/servers"
  env                  = var.env
  vpc-id               = module.networks.vpc-id
  public-subnet-2a-id  = module.networks.public-subnet-2a-id
  public-subnet-2c-id  = module.networks.public-subnet-2c-id
  private-subnet-2a-id = module.networks.private-subnet-2a-id
  private-subnet-2c-id = module.networks.private-subnet-2c-id
}
```

### `modules/networks/variables.tf`

```hcl
variable "vpc-cidr" {
  type = string
}
variable "env" {
  type = string
}
```

### `modules/networks/output.tf`

```hcl
output "vpc-id" {
  value = aws_vpc.module-vpc.id
}

output "public-subnet-2a-id" {
  value = aws_subnet.module-public-subnet-2a.id
}
output "public-subnet-2c-id" {
  value = aws_subnet.module-public-subnet-2c.id
}

output "private-subnet-2a-id" {
  value = aws_subnet.module-private-subnet-2a.id
}
output "private-subnet-2c-id" {
  value = aws_subnet.module-private-subnet-2c.id
}
```

### `modules/networks/main.tf`

```hcl
resource "aws_vpc" "module-vpc" {
  cidr_block           = var.vpc-cidr
  tags                 = { Name = "${var.env}-vpc" }
  enable_dns_hostnames = true
  enable_dns_support   = true
}

resource "aws_subnet" "module-public-subnet-2a" {
  vpc_id                  = aws_vpc.module-vpc.id
  cidr_block              = cidrsubnet(var.vpc-cidr, 8, 10)
  tags                    = { Name = "${var.env}-public-subnet-2a" }
  availability_zone       = "ap-northeast-2a"
  map_public_ip_on_launch = true
}

resource "aws_subnet" "module-public-subnet-2c" {
  vpc_id                  = aws_vpc.module-vpc.id
  cidr_block              = cidrsubnet(var.vpc-cidr, 8, 30)
  tags                    = { Name = "${var.env}-public-subnet-2c" }
  availability_zone       = "ap-northeast-2c"
  map_public_ip_on_launch = true
}

resource "aws_subnet" "module-private-subnet-2a" {
  vpc_id            = aws_vpc.module-vpc.id
  cidr_block        = cidrsubnet(var.vpc-cidr, 8, 11)
  tags              = { Name = "${var.env}-private-subnet-2a" }
  availability_zone = "ap-northeast-2a"

}
resource "aws_subnet" "module-private-subnet-2c" {
  vpc_id            = aws_vpc.module-vpc.id
  cidr_block        = cidrsubnet(var.vpc-cidr, 8, 31)
  tags              = { Name = "${var.env}-private-subnet-2c" }
  availability_zone = "ap-northeast-2c"
}

resource "aws_internet_gateway" "module-igw" {
  vpc_id = aws_vpc.module-vpc.id
  tags   = { Name = "${var.env}-igw" }
}

resource "aws_route_table" "module-public-rt" {
  vpc_id = aws_vpc.module-vpc.id
  route {
    gateway_id = aws_internet_gateway.module-igw.id
    cidr_block = "0.0.0.0/0"
  }
  tags = { Name = "${var.env}-public-rt" }
}

resource "aws_route_table_association" "module-public-rt-2a" {
  route_table_id = aws_route_table.module-public-rt.id
  subnet_id      = aws_subnet.module-public-subnet-2a.id
}
resource "aws_route_table_association" "module-public-rt-2c" {
  route_table_id = aws_route_table.module-public-rt.id
  subnet_id      = aws_subnet.module-public-subnet-2c.id
}

resource "aws_route_table" "module-private-rt" {
  vpc_id = aws_vpc.module-vpc.id
  route {
    cidr_block           = "0.0.0.0/0"
    network_interface_id = aws_instance.module-nat-instance.primary_network_interface_id
  }
  tags = { Name = "${var.env}-private-rt" }
}
resource "aws_route_table_association" "module-private-rt-2a" {
  route_table_id = aws_route_table.module-private-rt.id
  subnet_id      = aws_subnet.module-private-subnet-2a.id
}
resource "aws_route_table_association" "module-private-rt-2c" {
  route_table_id = aws_route_table.module-private-rt.id
  subnet_id      = aws_subnet.module-private-subnet-2c.id
}


resource "aws_instance" "module-nat-instance" {
  ami                    = "ami-0bc151a94289adb52"
  instance_type          = "t3.micro"
  key_name               = "my-public-ec2-key"
  subnet_id              = aws_subnet.module-public-subnet-2a.id
  vpc_security_group_ids = [aws_security_group.module-nat-sg.id]
  tags = {
    Name = "${var.env}-nat-instance"
  }
  source_dest_check = false
  user_data         = templatefile("${path.module}/nat_install.tpl", {})
}

resource "aws_security_group" "module-nat-sg" {
  vpc_id      = aws_vpc.module-vpc.id
  name        = "${var.env}-nat-sg"
  description = "NAT instance security group"
  ingress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = [aws_vpc.module-vpc.cidr_block]
  }
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}
```

### `modules/networks/nat_install.tpl`

```bash
#!/bin/bash

echo "net.ipv4.ip_forward = 1" | sudo tee -a /etc/sysctl.d/99-custom-nat.conf
sudo sysctl -p /etc/sysctl.d/99-custom-nat.conf
IFACE=$(ip route show default | awk '/default/ {print $5}')
sudo iptables -t nat -A POSTROUTING -o $IFACE -j MASQUERADE
```

### `modules/servers/variables.tf`

```hcl

variable "env" {
  type = string
}
variable "vpc-id" {
  type = string
}
variable "public-subnet-2a-id" {
  type = string
}
variable "public-subnet-2c-id" {
  type = string
}
variable "private-subnet-2a-id" {
  type = string
}
variable "private-subnet-2c-id" {
  type = string
}
```

### `modules/servers/output.tf`

```hcl

```

### `modules/servers/main.tf`

```hcl
resource "aws_instance" "module-bastion-instance" {
  ami                    = "ami-0bc151a94289adb52"
  instance_type          = "t3.micro"
  key_name               = "my-public-ec2-key"
  subnet_id              = var.public-subnet-2c-id
  vpc_security_group_ids = [aws_security_group.module-bastion-sg.id]

  tags = {
    Name = "${var.env}-bastion-instance"
  }
}

resource "aws_instance" "module-web-instance" {
  ami                    = "ami-0bc151a94289adb52"
  instance_type          = "t3.micro"
  key_name               = "my-public-ec2-key"
  subnet_id              = var.private-subnet-2a-id
  vpc_security_group_ids = [aws_security_group.module-web-sg.id]
  iam_instance_profile   = aws_iam_instance_profile.module-instance-profile.name
  tags = {
    Name = "${var.env}-web-instance"
  }
  user_data = templatefile("${path.module}/web_install.tpl", {
    TOMCAT_VERSION = "10.1.57",
    RDS_ENDPOINT   = aws_db_instance.module-rds-instance.address,
    DB_PASSWORD    = "mariaPass",
    DB_USER        = "admin",
    S3_BUCKET      = aws_s3_bucket.module-s3-bucket.id
  })
}

resource "aws_security_group" "module-bastion-sg" {
  vpc_id      = var.vpc-id
  name        = "${var.env}-bastion-sg"
  description = "bastion host group"

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "TCP"
    cidr_blocks = ["0.0.0.0/0"]
  }
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

}


resource "aws_security_group" "module-web-sg" {
  vpc_id      = var.vpc-id
  name        = "${var.env}-web-sg"
  description = "web security group"
  ingress {
    from_port   = 8080
    to_port     = 8080
    protocol    = "TCP"
    cidr_blocks = ["0.0.0.0/0"]
  }
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "TCP"
    cidr_blocks = ["0.0.0.0/0"]
  }
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

}

resource "aws_security_group" "module-rds-sg" {
  vpc_id = var.vpc-id
  name   = "${var.env}-rds-sg"
  tags   = { Name = "${var.env}-rds-sg" }

  description = "rds security group"
  ingress {
    from_port       = 3306
    to_port         = 3306
    protocol        = "TCP"
    security_groups = [aws_security_group.module-web-sg.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_db_instance" "module-rds-instance" {
  allocated_storage      = 10
  db_name                = "care"
  engine                 = "mariadb"
  engine_version         = "11.8"
  instance_class         = "db.t3.micro"
  username               = "admin"
  password               = "mariaPass"
  parameter_group_name   = "default.mariadb11.8"
  skip_final_snapshot    = true
  apply_immediately      = true # 데이터베이스 수정 사항을 즉시 적용
  identifier             = "${var.env}-1"
  db_subnet_group_name   = aws_db_subnet_group.module-rds-subnet-group.id
  vpc_security_group_ids = [aws_security_group.module-rds-sg.id]
}

resource "aws_db_subnet_group" "module-rds-subnet-group" {
  name        = "${var.env}-rds-subnet-group"
  description = "${var.env}-rds-subnet-group"
  subnet_ids = [
   var.private-subnet-2a-id, var.private-subnet-2c-id
  ]
  tags = {
    Name = "${var.env}-rds-subnet-group"
  }
}

resource "aws_s3_bucket" "module-s3-bucket" {
  bucket = "${var.env}-boot-bucket-2026"

  tags = {
    Name = "${var.env}-boot-bucket-2026"
  }
}
resource "aws_s3_object" "module-boot-object" {
  bucket = aws_s3_bucket.module-s3-bucket.id
  key    = "boot.war"
  source = "${path.module}/boot.war"
  etag   = filemd5("${path.module}/boot.war")
}

resource "aws_iam_role" "module-s3-role" {
  name = "${var.env}-s3-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
      },
    ]
  })
}
resource "aws_iam_role_policy" "module-s3-role-policy" {
  name = "${var.env}-s3-file-donwload"
  role = aws_iam_role.module-s3-role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "s3:GetObject",
        ]
        Effect   = "Allow"
        Resource = "*"
      },
    ]
  })
}
resource "aws_iam_instance_profile" "module-instance-profile" {
  name = "${var.env}-instance-profile"
  role = aws_iam_role.module-s3-role.name
}
```

### `modules/servers/web_install.tpl`

```bash
#!/bin/bash

TOMCAT_VERSION="${TOMCAT_VERSION}"
RDS_ENDPOINT="${RDS_ENDPOINT}"
DB_PASSWORD="${DB_PASSWORD}"
DB_USER="${DB_USER}"
S3_BUCKET="${S3_BUCKET}"

fallocate -l 2G /swapfile
chmod 600 /swapfile
mkswap /swapfile
swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab

apt update -y
apt install -y openjdk-17-jdk
wget http://mirror.apache-kr.org/apache/tomcat/tomcat-10/v${TOMCAT_VERSION}/bin/apache-tomcat-${TOMCAT_VERSION}.tar.gz
useradd -r -m -U -d /opt/tomcat -s /bin/false tomcat
tar -xf apache-tomcat-${TOMCAT_VERSION}.tar.gz -C /opt/tomcat
mv /opt/tomcat/apache-tomcat-${TOMCAT_VERSION} /opt/tomcat/tomcat-10
chown -RH tomcat: /opt/tomcat/tomcat-10
cat << EOF > /etc/systemd/system/tomcat.service
[Unit]
Description=Apache Tomcat 10
After=network.target

[Service]
Type=forking
User=tomcat
Group=tomcat

Environment="JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64"
Environment="CATALINA_HOME=/opt/tomcat/tomcat-10"
Environment="CATALINA_BASE=/opt/tomcat/tomcat-10"
Environment="CATALINA_PID=/opt/tomcat/tomcat-10/temp/tomcat.pid"
Environment="CATALINA_OPTS=-Xms512M -Xmx1024M -server -XX:+UseParallelGC"
ExecStart=/opt/tomcat/tomcat-10/bin/startup.sh
ExecStop=/opt/tomcat/tomcat-10/bin/shutdown.sh
Restart=always

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable tomcat
systemctl start tomcat

apt install -y  mariadb-client 
# RDS 생성 시 까지 대기 상태 
# mysqladmin ping이 성공할 '때까지(until)' 루프를 돕니다.
until mysqladmin ping -h "${RDS_ENDPOINT}" -u "${DB_USER}" -p"${DB_PASSWORD}" --silent; do
    echo "RDS is not ready yet. Sleeping for 5 seconds..."
    sleep 5
done

echo "RDS Connected!!"

mariadb -h "${RDS_ENDPOINT}" -u "${DB_USER}" -p"${DB_PASSWORD}" << EOF
CREATE DATABASE IF NOT EXISTS care;
USE care;

CREATE TABLE IF NOT EXISTS member(
id varchar(20),
pw varchar(200),
username varchar(99),
postcode varchar(5),
address varchar(1000),
detailaddress varchar(100),
mobile varchar(15),
PRIMARY KEY(id)
)DEFAULT CHARSET=UTF8;

CREATE TABLE IF NOT EXISTS board(
no int,
title varchar(200),
content varchar(9999),
id varchar(20),
writedate varchar(100),
hit int,
filename varchar(1000),
PRIMARY KEY(no)
)DEFAULT CHARSET=UTF8;

EOF

## S3에서 boot.war를 다운로드 받기.
apt install -y awscli
aws s3 cp "s3://${S3_BUCKET}/boot.war" /opt/tomcat/tomcat-10/webapps/boot.war

## 다운로드 및 압축 해제 대기
until [ -f "/opt/tomcat/tomcat-10/webapps/boot/WEB-INF/classes/application.properties" ]; do
    echo "appcalition.properties is not ready yet. Sleeping for 5 seconds..."
    sleep 5
done

## application.properties 수정하기.
sed -i 's/^spring.datasource.username=.*/spring.datasource.username=admin/' /opt/tomcat/tomcat-10/webapps/boot/WEB-INF/classes/application.properties
sed -i 's/^spring.datasource.password=.*/spring.datasource.password=mariaPass/' /opt/tomcat/tomcat-10/webapps/boot/WEB-INF/classes/application.properties
sed -i 's|^spring.datasource.url=.*|spring.datasource.url=jdbc:mariadb://database-1.cji0a2aaa6bd.ap-northeast-2.rds.amazonaws.com:3306/care?sslMode=trust|' /opt/tomcat/tomcat-10/webapps/boot/WEB-INF/classes/application.properties
systemctl restart tomcat
```

---

## 관련 노트

- [[Terraform Module 구성 실습 v11.0]]
- [[Terraform RDS 인프라 구성 실습 v10.1]]
- [[Terraform Module]]
- [[Terraform Variable과 Output]]
- [[Terraform Backend와 Remote State]]
- [[Terraform Workflow]]
