---
title: Terraform Module
created: 2026-07-06
status: active
type: concept-note
source:
  - Iac.pdf
  - IaC - Source Digest v2.md
  - IaC - 공식 검증 노트.md
source_pages:
  - p.42-p.44
  - p.46-p.52
tags:
  - 과목/AWS
  - 주제/IaC
  - 주제/Terraform
  - 상태/active
  - 개념/Terraform
  - 개념/Module
---

# Terraform Module

## Source Classification

| 내용 | 출처 분류 | 비고 |
|---|---|---|
| 강의자료 기반 핵심 내용 | PDF | `Iac.pdf`, `IaC - Source Digest v2.md` 기준 |
| Terraform 현재 동작 검증 | 인터넷 고신뢰 정보 | `IaC - 공식 검증 노트.md`와 HashiCorp 공식 문서 기준 |
| 설명 재구성 | 내장 지식 | PDF와 공식 검증 내용을 학습 노트 형태로 재배열 |
| 커뮤니티 의견 | 인터넷 비공식 고품질 의견 | 이 노트에서는 사용하지 않음 |
## 공식 검증 참고

- Terraform `init`: https://developer.hashicorp.com/terraform/cli/commands/init
- Dependency lock file: https://developer.hashicorp.com/terraform/language/files/dependency-lock
- `count`: https://developer.hashicorp.com/terraform/language/meta-arguments/count
- `for_each`: https://developer.hashicorp.com/terraform/language/meta-arguments/for_each
- Module block: https://developer.hashicorp.com/terraform/language/block/module
- `terraform_remote_state`: https://developer.hashicorp.com/terraform/language/state/remote-state-data
- S3 backend: https://developer.hashicorp.com/terraform/language/backend/s3
- Output values: https://developer.hashicorp.com/terraform/language/values/outputs

## 한 줄 정의

Terraform Module은 Terraform 코드를 재사용 가능한 단위로 분리하여 여러 환경이나 프로젝트에서 같은 인프라 구성을 반복 사용할 수 있게 하는 구조다.

## PDF 기준 핵심

PDF p.43은 Module을 다음처럼 설명한다.

```text
Terraform 코드를 모듈화하여 여러 위치에서 해당 모듈을 사용할 수 있도록 구현하는 것.
재사용 가능한 코드형 인프라를 구성하는 핵심 요소.
```

예시 상황:

- stage 환경
- prod 환경
- 두 환경이 비슷한 구조를 공유하지만 입력값은 다름
- 공통 인프라 구조는 module로 만들고 환경별 root module에서 호출

## Root Module과 Child Module

PDF p.43 도식 기준:

```text
global
└─ s3
   └─ main.tf                 # Terraform Status Management

modules
├─ vpc
│  ├─ main.tf
│  ├─ outputs.tf
│  └─ variables.tf
└─ web-cluster
   ├─ main.tf
   ├─ outputs.tf
   └─ variables.tf

prod
└─ Application-1
   ├─ main.tf
   └─ variables.tf            # Prod Root Module

stage
└─ Application-1
   ├─ main.tf
   └─ variables.tf            # Stage Root Module
```

| 구분 | 의미 |
|---|---|
| Root Module | 사용자가 `terraform init/plan/apply`를 실행하는 기준 디렉터리 |
| Child Module | Root Module에서 `module` block으로 호출되는 재사용 코드 |
| Local Module | 로컬 경로로 참조하는 module |
| Registry Module | Terraform Registry에서 가져오는 외부 module |

## Module 기본 구문

PDF p.44 기준:

```hcl
module "<NAME>" {
  source = "<SOURCE>"
  [ CONFIG ... ]
}
```

| 요소 | 의미 |
|---|---|
| `<NAME>` | 모듈 식별 이름 |
| `source` | 모듈 파일 경로 또는 Registry 주소 |
| `[CONFIG]` | 해당 모듈에 넘길 입력 변수 값 |

## Local Module 예시

PDF p.44, p.46 기준:

```hcl
module "local-vpc" {
  source = "../../modules/vpc"

  name = var.vpc_name
  cidr = var.vpc_cidr
}
```

p.46 예시:

```hcl
module "vpc" {
  source = "../../modules/vpc"

  vpc_cidr       = "10.10.0.0/16"
  public-1_cidr  = "10.10.1.0/24"
  public-2_cidr  = "10.10.2.0/24"
  private-1_cidr = "10.10.10.0/24"
  private-2_cidr = "10.10.20.0/24"
  ssh_port       = 22
}
```

Output 재정의:

```hcl
output "EC2_Pub_IP" {
  value       = module.vpc.EC2_Pub_IP
  description = "Stage BastionHost Public IP Address"
}
```

## Registry Module 예시

PDF p.44 기준:

```hcl
module "reg-vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "4.0.2"

  name = var.vpc_name
  cidr = var.vpc_cidr
}
```

PDF p.49 기준 VPC 외부 Module:

```hcl
module "stage_vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "5.1.1"

  name = "stage_vpc"
  cidr = local.stage_cidr

  azs             = local.azs
  public_subnets  = local.public_subnets
  private_subnets = local.private_subnets

  enable_dns_hostnames = "true"
  enable_dns_support   = "true"

  enable_nat_gateway     = true
  single_nat_gateway     = true
  one_nat_gateway_per_az = false

  tags = {
    "TerraformManaged" = "true"
  }
}
```

## Registry 사용 절차

PDF p.44 기준:

1. `https://registry.terraform.io/` 접속
2. Search All Resource에서 `AWS` 검색
3. AWS Provider 선택
4. `terraform-aws-modules / vpc` 클릭
5. Provision Instructions 코드 복사
6. Terraform 코드에 붙여넣기
7. `terraform init`으로 module 다운로드 후 사용

## Module 변경 시 `terraform init`

PDF p.43은 Root Module에서 참조 중인 Module에 변경 사항이 생기면 반드시 `terraform init`을 다시 수행해야 한다고 설명한다.

공식 검증 기준:

- `terraform init`은 child module을 검색하고 `source`에 지정된 위치에서 module을 가져온다.
- module source가 추가되거나 변경되면 다시 초기화가 필요할 수 있다.
- `-upgrade`를 사용하면 기존 module/provider를 version constraint 내 최신으로 갱신할 수 있다.

## Module 간 참조

PDF p.47은 VPC Module과 Web-Cluster Module 간 직접 참조 오류를 보여준다.

오류 요지:

```text
A managed resource "aws_vpc" "my_vpc" has not been declared in module.web-cluster.
```

의미:

- `web-cluster` module 내부에서 `aws_vpc.my_vpc.id`를 참조하려 했지만, 그 리소스는 해당 module 안에 없다.
- module은 경계가 있으므로 다른 module 내부 리소스를 직접 참조할 수 없다.

## 공식 검증 반영: Module 값 전달

정확한 정리:

```text
같은 root module 안에서 child module 간 값을 전달할 때는
root module이 한 module의 output을 받아 다른 module의 input으로 넘기는 방식이 일반적이다.
```

예시 구조:

```hcl
module "vpc" {
  source = "../../modules/vpc"
}

module "web_cluster" {
  source = "../../modules/web-cluster"
  vpc_id = module.vpc.vpc_id
}
```

`terraform_remote_state`는 다른 Terraform configuration/state의 root output을 읽을 때 쓰는 방식이다. 같은 root module 안의 값 연결까지 무조건 remote state로 처리해야 한다고 일반화하면 안 된다.

## 외부 Module 버전 주의

PDF는 다음 버전을 사용한다.

| Module | PDF 버전 |
|---|---|
| `terraform-aws-modules/vpc/aws` | `5.1.1` |
| `terraform-aws-modules/security-group/aws` | `5.1.0` |

정리:

- PDF 실습 재현 목적이면 PDF 버전 사용
- 새 프로젝트 설계 목적이면 Terraform Registry의 현재 문서와 changelog 확인
- major version이 바뀌면 input/output 이름, 기본값, provider requirement가 바뀔 수 있음
- `latest` 무지성 사용보다 명시적 version pinning이 안전함

## 관련 노트

- [[Terraform Variable과 Output]]
- [[Terraform Backend와 Remote State]]
- [[Terraform 반복문과 조건문]]
