---
title: Terraform Resource와 Data Source
created: 2026-07-06
status: active
type: concept-note
source:
  - Iac.pdf
  - IaC - Source Digest v2.md
  - IaC - 공식 검증 노트.md
source_pages:
  - p.12-p.28
tags:
  - 과목/AWS
  - 주제/IaC
  - 주제/Terraform
  - 상태/active
  - 개념/Terraform
  - 실습/Terraform
---

# Terraform Resource와 Data Source

## Source Classification

| 내용 | 출처 분류 | 비고 |
|---|---|---|
| 강의자료 기반 핵심 내용 | PDF | `Iac.pdf`, `IaC - Source Digest v2.md` 기준 |
| Terraform 현재 동작 검증 | 인터넷 고신뢰 정보 | `IaC - 공식 검증 노트.md`와 HashiCorp 공식 문서 기준 |
| 설명 재구성 | 내장 지식 | PDF와 공식 검증 내용을 학습 노트 형태로 재배열 |
| 커뮤니티 의견 | 인터넷 비공식 고품질 의견 | 이 노트에서는 사용하지 않음 |

## 한 줄 정의

Terraform에서 **Resource**는 새로 만들거나 관리할 인프라 객체이고, **Data Source**는 이미 존재하는 외부 정보를 읽어 Terraform 코드에 사용하는 객체다.

## Resource

PDF p.13 기준:

```hcl
resource "<PROVIDER>_<TYPE>" "<NAME>" {
  [ CONFIG ... ]
}
```

| 요소 | 의미 |
|---|---|
| `<PROVIDER>` | 공급자 이름 |
| `<TYPE>` | 공급자의 리소스 유형, 예: EC2, VPC |
| `<NAME>` | Terraform 코드 안에서 해당 리소스를 참조하기 위한 식별 이름 |
| `[CONFIG]` | 해당 리소스를 생성하기 위한 설정값 |

예시:

```hcl
resource "aws_instance" "Example" {
  ami           = "ami-0ea4d4b8dc1e46212"
  instance_type = "t2.micro"
}
```

## EC2 생성 흐름

PDF p.13-p.15 기준 흐름:

```text
main.tf에 aws_instance 정의
→ terraform plan으로 생성 예정 확인
→ terraform apply로 실제 EC2 생성
→ AWS Console EC2 메뉴에서 생성 확인
```

`plan` 예시 결과:

```text
Plan: 1 to add, 0 to change, 0 to destroy.
```

`apply` 예시 결과:

```text
Apply complete! Resources: 1 added, 0 changed, 0 destroyed.
```

## Resource 수정

PDF p.16-p.18 기준:

- 기존 EC2 Resource 코드를 수정한다.
- Instance Tag를 추가한다.
- 다시 `terraform apply`를 수행한다.
- AWS Console에서 Tag 변경 여부를 확인한다.

예시:

```hcl
tags = {
  Name = "Terraform_EC2_Example"
}
```

적용 결과 예시:

```text
Plan: 0 to add, 1 to change, 0 to destroy.
Apply complete! Resources: 0 added, 1 changed, 0 destroyed.
```

## Resource 삭제

PDF p.19에는 삭제 명령이 `terraform destory`로 표기되어 있다.

공식 검증 반영:

```bash
terraform destroy
```

삭제 결과 예시:

```text
Plan: 0 to add, 0 to change, 1 to destroy.
Destroy complete! Resources: 1 destroyed.
```

## Resource 참조

PDF p.20 기준 Resource 참조 구문:

```hcl
<PROVIDER>_<TYPE>.<NAME>.<ATTRIBUTE>
```

예:

```hcl
aws_security_group.Example_sg.id
```

의미:

| 구문 | 의미 |
|---|---|
| `aws_security_group` | AWS Security Group 리소스 유형 |
| `Example_sg` | Terraform 코드 안의 리소스 이름 |
| `id` | 생성된 Security Group의 ID attribute |

## Security Group 참조 예시

PDF p.21 기준:

```hcl
resource "aws_instance" "Example" {
  ami                    = "ami-0ea4d4b8dc1e46212"
  instance_type          = "t2.micro"
  vpc_security_group_ids = [aws_security_group.Example_sg.id]

  tags = {
    Name = "Terraform_EC2_Example"
  }
}
```

핵심:

- EC2는 여러 Security Group을 연결할 수 있으므로 list 형태로 지정한다.
- `aws_security_group.Example_sg.id`는 Security Group Resource의 ID를 참조한다.
- Terraform은 참조 관계를 통해 Security Group을 먼저 만들고 EC2에 연결할 수 있다.

## Data Source

PDF p.24 기준:

```hcl
data "<PROVIDER>_<TYPE>" "<NAME>" {
  [ CONFIG ... ]
}
```

Data Source 참조:

```hcl
data.<PROVIDER>_<TYPE>.<NAME>.<ATTRIBUTE>
```

정의:

```text
Data Source는 외부 공급자(AWS)에서 가져온 읽기 전용 정보다.
새 리소스를 생성하지 않고, 기존 데이터 정보를 가져와 현재 Terraform 코드에 적용한다.
```

예시 대상:

- VPC 정보
- Subnet 정보
- AMI 정보
- IAM 자격증명 정보

## VPC Data Source + Subnet Resource 예시

PDF p.25 기준:

```hcl
data "aws_vpc" "default_vpc" {
  default = true
}

resource "aws_subnet" "default_vpc_subnet" {
  vpc_id     = data.aws_vpc.default_vpc.id
  cidr_block = "172.31.64.0/20"

  tags = {
    Name = "Terraform_Subnet"
  }
}
```

의미:

- `data "aws_vpc" "default_vpc"`는 기본 VPC 정보를 읽는다.
- `data.aws_vpc.default_vpc.id`로 VPC ID를 가져온다.
- 그 VPC 안에 새 Subnet Resource를 생성한다.

## 실습 아키텍처 요약

PDF p.27-p.28은 Resource와 Data Source를 활용한 AWS 아키텍처 구현 실습을 제시한다.

핵심 구성:

- VPC
- Internet Gateway
- Public Subnet
- Private Subnet
- Route Table
- Security Group
- EC2
- NAT Gateway
- BastionHost
- Web-EC2

p.28 예시 CIDR:

| 요소 | 값 |
|---|---|
| VPC | `192.168.0.0/16` |
| Public subnet_1 | `192.168.1.0/24` |
| Public subnet_2 | `192.168.2.0/24` |
| Private subnet_1 | `192.168.10.0/24` |
| Private subnet_2 | `192.168.20.0/24` |
| Region | `ap-northeast-2` |
| AZ | `ap-northeast-2a`, `ap-northeast-2c` |

## 주의

- Resource는 실제 비용이 발생할 수 있다.
- Data Source는 읽기 전용이지만, Data Source 값을 이용해 새 Resource를 만들 수 있다.
- Security Group에서 `0.0.0.0/0` SSH 허용은 실습용으로만 보고, 실제 프로젝트에서는 제한해야 한다.
- PDF 코드는 교육용 예시이므로 실제 프로젝트 반영 전 Provider 문서 확인이 필요하다.

## 관련 노트

- [[Terraform 개요]]
- [[Terraform Workflow]]
- [[Terraform Variable과 Output]]
- [[Terraform Module]]
