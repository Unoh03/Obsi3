---
title: Terraform RDS 실습 노트 재료
created: 2026-07-09
status: draft
type: note-material
source_context:
  - conversation-log
  - terraform-02_rds-lab
  - AWS RDS official docs
  - AWS VPC Security Group official docs
  - HashiCorp Terraform official docs
tags:
  - 과목/AWS
  - 주제/IaC
  - 주제/Terraform
  - 주제/RDS
  - 주제/SecurityGroup
  - 상태/draft
---

# Terraform RDS 실습 노트 재료

> 이 파일은 정식 실습 노트가 아니라, `02_rds` 실습 중 나온 시행착오·경험·새로 배운 개념을 나중에 정식 노트로 편입하기 위한 재료 모음이다.

---

## 0. 이번 실습의 기준 상황

### 이전 실습

```text
Public WEB EC2
→ Private DB EC2
→ DB EC2 내부에 MariaDB 직접 설치
```

### 이번 실습

```text
Public WEB EC2
→ Private RDS MariaDB
→ DB 서버 운영체제/패키지 설치는 AWS RDS가 관리
```

핵심 변화:

```text
EC2에 DB를 설치하는 실습
→ VPC 안에 관리형 DB인 RDS를 배치하고 WEB에서 endpoint로 접속하는 실습
```

---

## 1. RDS는 DB 인스턴스 1개여도 DB subnet group은 2AZ가 필요했다

### 시도

처음에는 `DB subnet group`에 private subnet 하나만 넣었다.

```hcl
resource "aws_db_subnet_group" "terra_rds_subnet_group" {
  name = "terra-rds-subnet-group"

  subnet_ids = [
    aws_subnet.terra_close_subnet.id
  ]
}
```

### 결과

`terraform apply`에서 AWS RDS API가 거부했다.

```text
Error: creating RDS DB Subnet Group (terra-rds-subnet-group): operation error RDS: CreateDBSubnetGroup, https response error StatusCode: 400, RequestID: e9d17a68-7ef4-41f1-bc8d-585b157556e4, DBSubnetGroupDoesNotCoverEnoughAZs: The DB subnet group doesn't meet Availability Zone (AZ) coverage requirement. Current AZ coverage: ap-northeast-2a. Add subnets to cover at least 2 AZs.

with aws_db_subnet_group.terra_rds_subnet_group,
on main.tf line 64, in resource "aws_db_subnet_group" "terra_rds_subnet_group":
64: resource "aws_db_subnet_group" "terra_rds_subnet_group" {
```

### 판정

```text
RDS DB Instance가 1개라는 것과,
DB subnet group이 2개 이상의 AZ를 커버해야 한다는 것은 별개다.
```

정리:

| 항목 | 결론 |
|---|---|
| RDS DB Instance 수 | 1개 가능 |
| Multi-AZ 여부 | `multi_az = false` 가능 |
| DB Subnet Group | 일반 Region에서는 최소 2개 AZ subnet 필요 |
| subnet 1개 시도 | `DBSubnetGroupDoesNotCoverEnoughAZs`로 실패 |

### 노트용 문장

```text
Terraform validate/plan 단계에서는 subnet 1개 DB subnet group 문제가 드러나지 않을 수 있다.
하지만 apply 단계에서 AWS RDS API가 `DBSubnetGroupDoesNotCoverEnoughAZs` 오류로 생성을 거부했다.
오류 메시지는 현재 AZ coverage가 `ap-northeast-2a` 하나뿐이며, 최소 2개 AZ를 커버하도록 subnet을 추가하라고 안내했다.
따라서 Single-AZ RDS DB instance를 1개만 생성하더라도, 일반 Region의 DB subnet group은 최소 2개 AZ의 subnet을 가져야 함을 실증했다.
```

---

## 2. 실습 그림이 `Public 1개 + Private 1개`여도 RDS 구현에서는 private subnet을 하나 더 둔다

### 문제의식

실습 예시 그림이 단순히 다음 구조만 보여줄 수 있다.

```text
Public Subnet
Private Subnet
```

하지만 RDS는 DB subnet group 요구사항 때문에 실제 구현에서 private subnet을 하나 더 만든다.

### 최종 구현 구조

```text
VPC 10.20.0.0/16
├─ Public Subnet A       10.20.1.0/24   ap-northeast-2a
│  └─ WEB EC2
├─ Private DB Subnet A   10.20.10.0/24  ap-northeast-2a
│  └─ RDS subnet group member
└─ Private DB Subnet C   10.20.11.0/24  ap-northeast-2c
   └─ RDS subnet group member
```

### 노트용 문장

```text
실습 그림은 Public Web 영역과 Private DB 영역의 논리 구조를 단순화한 것이다.
RDS는 DB subnet group 요구사항 때문에 서로 다른 AZ의 private subnet 2개를 구성했지만,
생성되는 RDS DB instance는 1개이며 `multi_az = false`로 Single-AZ DB instance를 생성했다.
```

---

## 3. `aws_db_instance`에 subnet ID를 직접 넣는 게 아니라 DB subnet group을 참조한다

### 잘못된 접근

```hcl
db_subnet_names = [aws_subnet.terra_close_subnet.id]
```

문제:

```text
`aws_db_instance`에는 `db_subnet_names`라는 인자가 없다.
```

### 올바른 구조

```text
subnet id
→ aws_db_subnet_group.subnet_ids
→ aws_db_instance.db_subnet_group_name
```

예시:

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

### 노트용 문장

```text
RDS instance는 subnet ID를 직접 받지 않는다.
RDS는 DB subnet group을 통해 subnet 후보 목록을 전달받고,
`aws_db_instance`에서는 `db_subnet_group_name`으로 해당 DB subnet group의 이름을 참조한다.
```

---

## 4. RDS endpoint는 IP가 아니라 DNS 이름으로 사용한다

### 기존 EC2 DB 방식

```php
$host = '192.168.10.13';
```

### RDS 방식

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

최종 PHP 파일 안에는 다음과 같은 실제 endpoint 문자열이 들어가는 것이 목표다.

```php
$host = 'terra-rds-lab.xxxxxxxxxxxx.ap-northeast-2.rds.amazonaws.com';
```

### 잘못된 예

```php
$host = 'aws_db_instance.terra_rds.address';
```

이건 Terraform 값 참조가 아니라 PHP 문자열이다.  
PHP는 Terraform resource address를 해석하지 못한다.

### 노트용 문장

```text
Terraform resource address는 Terraform 코드 안에서만 의미가 있다.
PHP 파일 안에 `'aws_db_instance.terra_rds.address'`라고 적으면 Terraform 값이 아니라 단순 문자열이 된다.
RDS endpoint를 PHP에 넣으려면 `templatefile()`로 Terraform 값인 `aws_db_instance.terra_rds.address`를 렌더링해야 한다.
```

---

## 5. `.tftpl`은 Terraform templatefile용 템플릿 파일이라는 의도를 드러낸다

### 정리

```text
.tpl:
일반적인 template 확장자 관습

.tftpl:
Terraform templatefile용 템플릿이라는 의도를 드러내는 확장자
```

확장자 자체가 Terraform 동작을 바꾸는 것은 아니다. 핵심은 `templatefile()`로 읽느냐다.

```hcl
templatefile("${path.module}/user_data/20-web-install.sh.tftpl", {
  db_host = aws_db_instance.terra_rds.address
})
```

### 파일 경로 실수

`terraform validate`에서 다음 오류가 발생했다.

```text
Error: Invalid function argument

Invalid value for "path" parameter: no file exists at "./user_data/20-web-install.sh.tftpl"; this function works only with files that are distributed as part of the configuration source code
```

원인:

```text
D:\terraform\workspace\02_rds\user_data\20-web-install.sh.tftpl
파일이 실제로 없었음
```

### 노트용 문장

```text
`templatefile()`은 Terraform 실행 시점에 실제 파일이 configuration source code 안에 존재해야 한다.
파일명이 다르거나, Windows에서 `.txt` 확장자가 붙어 있거나, 다른 폴더에 있으면 validate 단계에서 바로 실패한다.
```

---

## 6. Terraform의 implicit dependency: `depends_on`이 필요 없는 경우

### 현재 구조

```hcl
web_user_data = templatefile("${path.module}/user_data/20-web-install.sh.tftpl", {
  db_host     = aws_db_instance.terra_rds.address
  db_name     = "appdb"
  db_user     = "webuser"
  db_password = "itbank1234"
})
```

```hcl
resource "aws_instance" "terra_WEB" {
  user_data = join("\n", [
    local.common_user_data,
    local.web_user_data
  ])
}
```

### Terraform이 보는 의존성

```text
aws_instance.terra_WEB
→ local.web_user_data
→ aws_db_instance.terra_rds.address
→ aws_db_instance.terra_rds
```

### 판정

```text
`terra_WEB`의 user_data가 RDS address를 참조하므로,
Terraform은 RDS가 먼저 생성되어야 WEB user_data를 만들 수 있다고 판단한다.
따라서 이 경우 별도의 `depends_on = [aws_db_instance.terra_rds]`는 불필요하다.
```

### `depends_on`이 필요한 경우

```text
Terraform 코드의 expression reference로는 드러나지 않지만,
실제 운영 순서상 먼저 존재해야 하는 hidden dependency가 있을 때 사용한다.
```

예:

```hcl
resource "aws_instance" "app" {
  user_data = file("${path.module}/user_data/install.sh")
}
```

`install.sh` 내부에서 특정 S3 bucket이나 외부 리소스를 사용하지만 Terraform 코드상 직접 참조가 없다면 Terraform은 의존성을 자동 추론하지 못한다.

---

## 7. Security Group은 stateful이다

### 새로 배운 점

```text
허용된 inbound traffic에 대한 response traffic은 outbound rule과 무관하게 나갈 수 있다.
허용된 outbound traffic에 대한 response traffic은 inbound rule과 무관하게 들어올 수 있다.
```

### RDS 관점

WEB에서 RDS로 접속한다.

```text
WEB EC2
→ RDS:3306
```

RDS SG에 필요한 핵심 규칙:

```hcl
ingress {
  description     = "Allow MariaDB from WEB SG"
  from_port       = 3306
  to_port         = 3306
  protocol        = "tcp"
  security_groups = [aws_security_group.open_sg.id]
}
```

RDS가 이 inbound 3306 요청을 허용하면, 그 응답은 Security Group의 stateful 동작으로 반환된다.

### 주의점

```text
RDS SG outbound가 없어도 허용된 inbound 요청의 response는 나갈 수 있다.
하지만 WEB SG outbound가 막혀 있으면 WEB이 RDS로 최초 연결 요청을 보낼 수 없다.
```

### 현재 실습 구조

```text
WEB SG:
- inbound 80 from Internet
- inbound 22 from my IP
- outbound all

RDS SG:
- inbound 3306 from WEB SG
- egress 없음
```

판정:

```text
WEB → RDS 최초 연결은 WEB SG outbound all 때문에 가능하다.
RDS → WEB 응답은 RDS SG의 stateful 동작 때문에 가능하다.
```

### 개념 노트 후보

이 내용은 실습 노트뿐 아니라 Security Group 개념 노트로 분리할 가치가 있다.

후보 제목:

```text
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

## 8. Terraform `aws_security_group`에서 egress를 안 쓰는 것의 의미

AWS 자체는 새 Security Group 생성 시 기본적으로 all outbound rule을 만든다.

하지만 Terraform `aws_security_group` 리소스는 VPC 안의 새 Security Group을 만들 때 AWS의 기본 allow-all egress rule을 제거하고, 필요하면 명시적으로 다시 만들도록 한다.

실습에서 명시적으로 all outbound를 열고 싶다면:

```hcl
egress {
  description = "Allow all outbound for lab"
  from_port   = 0
  to_port     = 0
  protocol    = "-1"
  cidr_blocks = ["0.0.0.0/0"]
}
```

RDS SG에서는 실습상 egress 없이도 WEB 요청에 대한 응답은 가능하다.  
다만 초보 실습에서 변수 제거를 원하면 all egress를 명시해도 된다.

---

## 9. RDS master password 길이 조건

초기 실습용 비밀번호로 다음 값을 사용하려 했다.

```hcl
password = "itbank"
```

하지만 RDS master password 조건상 너무 짧을 수 있으므로, 실험 목적과 무관한 오류를 피하기 위해 다음처럼 변경했다.

```hcl
password = "itbank1234"
```

`templatefile()` 변수도 같이 맞췄다.

```hcl
db_password = "itbank1234"
```

### 노트용 문장

```text
이번 실험의 목적은 DB subnet group의 AZ coverage 오류를 확인하는 것이었다.
따라서 비밀번호 길이 오류 같은 unrelated failure를 피하기 위해 RDS master password를 8자 이상으로 조정했다.
```

---

## 10. `validate`, `plan`, `apply`에서 잡히는 오류가 다르다

이번 실습에서 오류는 여러 층에서 발생했다.

| 단계 | 잡힌 오류 | 의미 |
|---|---|---|
| `terraform validate` | `templatefile()` 경로의 파일 없음 | Terraform configuration/source code 수준 오류 |
| `terraform validate` 또는 provider schema | `db_subnet_names` 같은 존재하지 않는 argument | Terraform Provider schema 수준 오류 |
| `terraform apply` | `DBSubnetGroupDoesNotCoverEnoughAZs` | AWS RDS API/service constraint 수준 오류 |

### 노트용 문장

```text
Terraform의 검증 단계는 계층별로 다르다.
`validate`는 Terraform 코드와 provider schema 수준의 오류를 잡지만,
AWS 서비스가 실제로 요구하는 제약은 `apply`에서 API 호출 시점에 드러날 수 있다.
이번 실습에서는 subnet 1개 DB subnet group이 HCL 문법상 리스트 형태로는 표현 가능했지만,
AWS RDS API가 `DBSubnetGroupDoesNotCoverEnoughAZs` 오류로 최종 거부했다.
```

---

## 11. `close_sg`는 RDS 실습에서는 죽은 코드가 되었다

기존 EC2 DB 실습에서는 DB EC2에 `close_sg`를 붙였다.

RDS 전환 후에는 RDS가 별도의 `rds_sg`를 사용한다.

```hcl
vpc_security_group_ids = [aws_security_group.rds_sg.id]
```

WEB은 `open_sg`를 사용한다.

```hcl
vpc_security_group_ids = [aws_security_group.open_sg.id]
```

따라서 `close_sg`가 어떤 리소스에도 연결되지 않는다면 죽은 코드다.

### 노트용 문장

```text
EC2 DB에서 RDS로 전환하면서 DB EC2용 `close_sg`는 더 이상 사용되지 않는다.
RDS에는 `rds_sg`를 별도로 연결하고, inbound 3306 source를 WEB SG로 제한하는 것이 더 명확하다.
```

---

## 12. 두 번째 private subnet도 route table association을 명시하는 것이 좋다

성공한 코드에서는 두 번째 private subnet을 추가했다.

```hcl
resource "aws_subnet" "terra_close_subnet2" {
  vpc_id                  = aws_vpc.terra_vpc.id
  cidr_block              = "10.20.11.0/24"
  availability_zone       = "ap-northeast-2c"
  map_public_ip_on_launch = false
}
```

기존 private route table association은 첫 번째 private subnet에만 적용되어 있었다.

```hcl
resource "aws_route_table_association" "terra_close_assoc" {
  subnet_id      = aws_subnet.terra_close_subnet.id
  route_table_id = aws_route_table.terra_close_rt.id
}
```

보강 추천:

```hcl
resource "aws_route_table_association" "terra_close_assoc2" {
  subnet_id      = aws_subnet.terra_close_subnet2.id
  route_table_id = aws_route_table.terra_close_rt.id
}
```

### 노트용 문장

```text
RDS의 두 번째 private subnet은 인터넷 route가 필요하지 않지만,
학습 코드의 의도를 명확히 하기 위해 두 private subnet 모두 같은 private route table에 명시적으로 association하는 것이 좋다.
```

---

## 13. 현재 성공 코드의 핵심 구조

```hcl
resource "aws_subnet" "terra_close_subnet" {
  cidr_block        = "10.20.10.0/24"
  availability_zone = "ap-northeast-2a"
}

resource "aws_subnet" "terra_close_subnet2" {
  cidr_block        = "10.20.11.0/24"
  availability_zone = "ap-northeast-2c"
}

resource "aws_db_subnet_group" "terra_rds_subnet_group" {
  name = "terra-rds-subnet-group"

  subnet_ids = [
    aws_subnet.terra_close_subnet.id,
    aws_subnet.terra_close_subnet2.id
  ]
}

resource "aws_db_instance" "terra_rds" {
  identifier = "terra-rds-lab"

  allocated_storage = 20
  storage_type      = "gp3"

  engine         = "mariadb"
  instance_class = "db.t3.micro"

  db_name  = "appdb"
  username = "webuser"
  password = "itbank1234"

  db_subnet_group_name   = aws_db_subnet_group.terra_rds_subnet_group.name
  vpc_security_group_ids = [aws_security_group.rds_sg.id]

  publicly_accessible = false
  multi_az            = false

  skip_final_snapshot     = true
  deletion_protection     = false
  backup_retention_period = 0
}
```

---

## 14. 이번 실습 노트에 넣을 체크리스트

```text
[x] `02_rds` 별도 Terraform root module 구성
[x] VPC CIDR을 `10.20.0.0/16`으로 변경
[x] Public WEB Subnet `10.20.1.0/24` 구성
[x] Private DB Subnet A `10.20.10.0/24` 구성
[x] Private DB Subnet C `10.20.11.0/24` 구성
[x] subnet 1개 DB subnet group 시도
[x] `DBSubnetGroupDoesNotCoverEnoughAZs` 오류 확인
[x] 서로 다른 AZ subnet 2개로 DB subnet group 수정
[x] RDS MariaDB instance apply 성공
[x] `20-web-install.sh`를 `20-web-install.sh.tftpl`로 전환
[x] PHP DB host를 RDS endpoint 변수로 주입
[x] Terraform implicit dependency로 RDS → WEB 생성 순서가 잡힘을 확인
[ ] WEB `/db-test.php`에서 `WEB -> RDS CONNECT OK` 확인
[ ] RDS table에 `WEB -> RDS OK` 행 누적 확인
[ ] 두 번째 private subnet route table association 추가 여부 결정
[ ] 실습 후 `terraform destroy` 완료
```

---

## 15. 나중에 정식 노트로 편입할 위치 후보

| 재료 | 편입 후보 |
|---|---|
| subnet 1개 DB subnet group 실패 | RDS 실습 노트 |
| 실습 그림과 실제 RDS 구현 차이 | RDS 실습 노트 / AWS 아키텍처 노트 |
| SG stateful 동작 | Security Group 개념 노트 |
| Terraform implicit dependency | Terraform Resource와 Data Source / Terraform Workflow |
| `templatefile()`과 `.tftpl` | Terraform Function 또는 user_data 리팩토링 노트 |
| `validate`/`plan`/`apply` 오류 계층 차이 | Terraform Workflow / Terraform Troubleshooting |
| RDS endpoint DNS 사용 | RDS 실습 노트 / AWS DB 서비스 노트 |
| 비밀번호와 Terraform state 주의 | Terraform State / RDS 실습 노트 |

---

## 16. 공식 근거 메모

### AWS RDS

- RDS DB instance를 VPC에 배포하려면 VPC에 최소 2개 subnet이 필요하고, 서로 다른 AZ에 있어야 한다.
- DB subnet group은 일반적으로 private subnet들의 collection이며, 최소 2개 AZ의 subnet을 가져야 한다.
- Local Zone DB subnet group은 subnet 1개 예외가 있다.
- RDS는 DB subnet group에서 subnet과 IP를 선택해 DB instance에 연결한다.
- RDS 접속에는 underlying IP보다 DNS endpoint 사용이 권장된다.

### AWS Security Group

- Security Group은 stateful이다.
- 허용된 outbound request의 response는 inbound rule과 관계없이 허용된다.
- 허용된 inbound traffic의 response는 outbound rule과 관계없이 허용된다.

### Terraform / HashiCorp

- `templatefile(path, vars)`는 파일을 읽고 변수 map으로 템플릿을 렌더링한다.
- `*.tftpl`은 Terraform template 파일임을 드러내기 위한 권장 naming pattern이다.
- Terraform은 expression reference를 기반으로 implicit dependency graph를 만든다.
- `depends_on`은 Terraform이 자동 추론할 수 없는 hidden dependency에 사용한다.
- `aws_security_group`은 AWS가 기본 생성하는 allow-all egress rule을 제거하며, 필요하면 사용자가 명시적으로 작성해야 한다.
- `aws_db_instance`의 `username`/`password` 등 argument는 Terraform raw state에 plain text로 저장될 수 있다.

---

## 17. 보고서/노트용 한 문단 요약

```text
이번 RDS 전환 실습에서는 기존 Private DB EC2를 제거하고, AWS 관리형 데이터베이스인 RDS MariaDB를 VPC 내부 private subnet group에 배치하였다. 처음에는 예시 그림처럼 private subnet 1개만 사용해 DB subnet group을 구성하려 했으나, `terraform apply` 단계에서 AWS RDS API가 `DBSubnetGroupDoesNotCoverEnoughAZs` 오류로 생성을 거부하였다. 이를 통해 Single-AZ RDS DB instance 1개를 만들더라도, 일반 Region의 DB subnet group은 서로 다른 Availability Zone의 subnet을 최소 2개 포함해야 함을 확인하였다. 이후 `ap-northeast-2a`, `ap-northeast-2c`에 private subnet을 각각 추가하고 DB subnet group에 포함시켜 RDS 생성을 성공시켰다. Web EC2는 Terraform `templatefile()`을 통해 RDS endpoint를 PHP 설정에 주입받도록 구성했으며, Terraform은 `aws_db_instance.terra_rds.address` 참조를 통해 RDS와 WEB EC2 사이의 생성 순서를 자동으로 추론하였다.
```
