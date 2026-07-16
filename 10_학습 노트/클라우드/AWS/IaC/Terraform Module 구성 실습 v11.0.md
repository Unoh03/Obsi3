---
title: Terraform Module 구성 실습
version: v11.0
created: 2026-07-14
updated: 2026-07-14
status: legacy
type: lab
topic: Terraform Module
parent_moc: "[[00_IaC MOC]]"
source:
  - Terraform RDS 인프라 구성 실습 v10.1.md
  - 11_modules(2)/vpc/main.tf
  - 11_modules(2)/vpc/variables.tf
  - 11_modules(2)/vpc/output.tf
  - 11_modules(2)/subnet/main.tf
  - 11_modules(2)/subnet/variables.tf
  - 11_modules(2)/stage/main.tf
  - 11_modules(2)/prod/main.tf
  - Iac.pdf p.42-44
official_refs:
  - https://developer.hashicorp.com/terraform/language/modules
  - https://developer.hashicorp.com/terraform/language/block/module
tags:
  - 과목/AWS
  - 주제/IaC
  - 주제/Terraform
  - 주제/Terraform-Module
  - 주제/Root-Module
  - 주제/Child-Module
  - 주제/Local-Module
  - 주제/Module-Input
  - 주제/Module-Output
  - 실습/Terraform
---

# Terraform Module 구성 실습 v11.0

> **v11.0 부제:** Local Module 분리와 Stage/Prod 재사용

## 목적

이 노트는 v10.0~v10.1에서 학습한 반복문·조건문을 짧게 정리한 뒤, 강사의 최신 `11_modules` 소스를 기준으로 Terraform Local Module의 기본 구조를 분석한다.

현재 핵심 범위는 다음과 같다.

```text
VPC Resource를 Child Module로 분리
→ Input Variable로 환경별 값 전달
→ VPC ID와 CIDR을 Output으로 공개
→ Subnet Child Module의 Input으로 연결
→ Stage와 Prod Root Module에서 같은 구현 재사용
```

> [!important] 출처 사용 원칙
> 실제 강사 코드와 폴더 구조를 주 근거로 사용한다.  
> `Iac.pdf` p.42 이후 내용은 용어와 학습 방향을 보충하는 참고자료로만 사용한다.  
> Backend, Remote State, Registry Module은 실제 코드에 등장하기 전까지 본문 핵심 범위에 포함하지 않는다.

> [!note] 검증 범위
> `11_modules(2).zip`의 HCL을 정적으로 분석했다.  
> `terraform fmt`, `init`, `validate`, `plan`, `apply` 결과는 확인하지 않았다.

---

## 이전 진도 요약: v10.0~v10.1

v10은 하나의 Root Module 내부에서 반복되는 Resource 정의를 줄이는 단계였다.

```text
Map과 객체형 Map
→ for_each
→ each.key / each.value
→ for 표현식의 if 필터
→ 조건식
→ 반복 Resource 사이 Key 기반 연결
```

핵심 학습:

- `for_each`로 Subnet, EC2, Route Table Association을 반복 생성했다.
- `cidr`, `az`, `public` 속성을 가진 객체형 Map으로 인프라 데이터를 구조화했다.
- Public/Private Resource 집합을 조건에 따라 선택했다.
- 같은 Key를 사용해 반복 Resource 사이의 대응 관계를 만들었다.

v11에서는 반복되는 개별 Resource가 아니라 **반복되는 인프라 구성 단위**를 재사용한다.

```text
v10:
한 Root Module 내부의 반복 제거

v11:
구성 단위를 Child Module로 분리하고
여러 Root Module에서 재사용
```

---

## 빠른 이동

> - [[#Part 1. Terraform Module 개념|Part 1. Terraform Module 개념]]
> - [[#Part 2. 강사 최신 Local Module 코드|Part 2. 강사 최신 코드]]
> - [[#13. VPC Output을 Subnet Input으로 전달|Module 간 값 전달]]
> - [[#15. Module 분리와 State 분리의 관계|Module과 State]]
> - [[#19. v11.0 완료 판정|완료 판정]]
> - [[#Appendices|부록]]

---

# Part 1. Terraform Module 개념

## 1. 반복문 다음에 Module을 배우는 이유

반복문과 Module은 모두 중복을 줄이지만 범위가 다르다.

| 기능 | 줄이는 중복 | 예시 |
|---|---|---|
| `for_each`, `count` | 동일한 Resource Block의 반복 | Subnet 6개 |
| Module | 관련 Resource 구성 전체의 반복 | Stage VPC 구성, Prod VPC 구성 |

```text
반복문:
같은 종류의 객체를 데이터에 따라 여러 개 생성

Module:
여러 Resource와 설정을 하나의 재사용 가능한 구성요소로 묶음
```

따라서 학습 흐름은 자연스럽다.

```text
Resource 직접 작성
→ 파일 분할
→ 반복문·조건문
→ Module
```

---

## 2. Terraform Module의 기본 정의

Terraform Module은 다음처럼 이해할 수 있다.

> 관련된 인프라 Resource 구성을 하나의 재사용 가능한 단위로 묶은 것

Module은 보통 다음 요소를 가진다.

```text
내부 구현:
resource, data, locals

입력 Interface:
variable

출력 Interface:
output

호출:
module Block
```

현재 실습의 VPC Module:

```text
vpc/
├─ main.tf
├─ variables.tf
└─ output.tf
```

역할:

| 파일 | 현재 역할 |
|---|---|
| `main.tf` | VPC 구현 |
| `variables.tf` | CIDR과 환경 이름 입력 |
| `output.tf` | VPC ID와 CIDR 공개 |

파일명은 관례일 뿐이다. 같은 디렉터리의 `.tf` 파일들은 하나의 Module 구성으로 함께 평가된다.

---

## 3. 보편적인 Module 개념으로 이해해도 되는가

결론:

> 보편적인 Module 개념으로 받아들여도 된다.  
> 다만 “파일 단위 코드 Module”보다 “입력과 출력을 가진 재사용 가능한 인프라 구성요소”라고 이해하는 편이 정확하다.

일반적인 Module과 같은 점:

- 관련 기능을 하나의 단위로 묶는다.
- 내부 구현과 외부 Interface를 구분한다.
- 입력값에 따라 다른 구성을 만들 수 있다.
- 여러 위치에서 재사용할 수 있다.
- 다른 Module과 조합할 수 있다.

현재 코드에 대응시키면:

```text
VPC Module:
VPC 생성 방식을 캡슐화

Stage Root Module:
Stage 입력값으로 VPC Module 호출

Prod Root Module:
Prod 입력값으로 같은 VPC Module 호출
```

따라서 모듈화, 캡슐화, 재사용, 조합이라는 보편적 개념은 그대로 적용된다.

---

## 4. 함수·클래스와의 비유

완전히 같지는 않지만 Interface를 이해하는 데 유용하다.

| 프로그래밍 개념 | Terraform |
|---|---|
| 함수·클래스 정의 | Module 디렉터리 |
| 함수 호출·객체 생성 | `module` Block |
| 인자 | Input Variable |
| 반환값 | Output |
| 내부 코드 | Resource, Data Source, Local |
| 같은 정의의 재사용 | 동일 Module을 여러 Root에서 호출 |

예:

```hcl
module "module-vpc" {
  source = "../vpc"
  cidr   = "10.0.0.0/16"
  env    = "stage"
}
```

해석:

```text
../vpc:
재사용할 구현

cidr, env:
호출자가 전달하는 입력

module.module-vpc.vpc-id:
호출 결과로 공개된 출력
```

단, Terraform Module은 함수를 순서대로 실행하는 Runtime 단위가 아니다. 원하는 인프라 상태를 선언하고, Terraform이 전체 Dependency Graph를 계산한다.

---

## 5. Terraform Module의 특수한 점

### 5-1. `.tf` 파일 하나가 Module인 것은 아니다

```text
main.tf
networks.tf
instances.tf
```

같은 디렉터리에 있다면 일반적으로 하나의 Module이다.

```text
디렉터리 경계
→ Module 경계
```

별도 디렉터리를 `module` Block의 `source`로 호출할 때 Child Module 경계가 생긴다.

### 5-2. 단순한 `import`가 아니다

```hcl
module "module-vpc" {
  source = "../vpc"
}
```

이 코드는 텍스트를 복사해 붙이는 것이 아니다.

Terraform Resource 주소에는 Module Instance 경계가 남는다.

```text
module.module-vpc.aws_vpc.module-vpc
```

### 5-3. 선언형 구성이다

일반 함수식 사고:

```text
먼저 VPC 함수를 실행
→ 반환된 값으로 Subnet 함수 실행
```

Terraform식 사고:

```text
Subnet은 VPC ID가 필요함
→ 참조 관계로 의존성 형성
→ Terraform이 생성 순서를 계산
```

### 5-4. Module 분리와 State 분리는 다르다

```text
Module 분리
≠ State 분리
```

같은 Root Module이 VPC와 Subnet Child Module을 함께 호출하면, 일반적으로 두 Child Module의 Resource는 같은 Root Module의 State에 함께 기록된다.

---

## 6. Root Module과 Child Module

### Root Module

Terraform CLI를 실행하는 디렉터리의 구성이다.

현재 실습:

```text
stage/
prod/
```

각 디렉터리는 별도로 `terraform init`, `plan`, `apply`할 수 있는 Root Module이다.

### Child Module

Root Module이 `module` Block으로 호출하는 구성이다.

현재 실습:

```text
vpc/
subnet/
```

호출 관계:

```text
stage Root Module
├─ ../vpc Child Module
└─ ../subnet Child Module

prod Root Module
├─ ../vpc Child Module
└─ ../subnet Child Module
```

같은 Child Module 구현을 서로 다른 Root Module이 재사용한다.

---

# Part 2. 강사 최신 Local Module 코드

## 7. 현재 스냅샷 구조

`11_modules(2).zip`:

```text
11_modules/
├─ vpc/
│  ├─ main.tf
│  ├─ variables.tf
│  └─ output.tf
├─ subnet/
│  ├─ main.tf
│  └─ variables.tf
├─ stage/
│  └─ main.tf
└─ prod/
   └─ main.tf
```

각 디렉터리의 역할:

| 디렉터리 | 역할 |
|---|---|
| `vpc/` | 공통 VPC Child Module |
| `subnet/` | 공통 Subnet Child Module |
| `stage/` | Stage Root Module |
| `prod/` | Prod Root Module |

---

## 8. 이전 스냅샷에서 추가된 변화

`11_modules(1)`에서 `11_modules(2)`로 바뀌며 다음이 실제로 추가됐다.

```text
vpc/output.tf 추가
subnet/variables.tf 추가
subnet/main.tf 구현
stage에서 subnet Module 호출
prod에서 subnet Module 호출
prod의 env 값을 Root Variable로 전환
```

가장 중요한 변화:

```text
VPC Child Module의 Output
→ Root Module의 module 참조
→ Subnet Child Module의 Input
```

이제 Module의 정의, 입력, 출력, 조합이 실제 코드로 모두 나타났다.

---

## 9. VPC Child Module 구현

`vpc/main.tf`:

```hcl
resource "aws_vpc" "module-vpc" {
  cidr_block = var.cidr

  tags = {
    Name = "${var.env}-vpc"
  }

  enable_dns_hostnames = true
  enable_dns_support   = true
}
```

현재 VPC Module이 책임지는 것:

```text
VPC 생성
DNS hostname 활성화
DNS support 활성화
환경 이름 기반 Name Tag 생성
```

Module 내부에는 Stage 또는 Prod CIDR이 하드코딩되지 않는다.

---

## 10. VPC Module Input Variable

`vpc/variables.tf`:

```hcl
variable "cidr" {
  type = string
}

variable "env" {
  type = string
}
```

Interface:

| 입력 | 의미 |
|---|---|
| `cidr` | 생성할 VPC CIDR |
| `env` | `stage-vpc`, `prod-vpc`를 만들 환경 이름 |

Module 내부 구현:

```hcl
cidr_block = var.cidr
Name       = "${var.env}-vpc"
```

Root Module은 구현을 수정하지 않고 값만 바꾼다.

---

## 11. VPC Module Output

`vpc/output.tf`:

```hcl
output "vpc-id" {
  value = aws_vpc.module-vpc.id
}

output "vpc-cidr" {
  value = aws_vpc.module-vpc.cidr_block
}
```

Module 내부 Resource는 외부에서 다음처럼 직접 참조하지 않는다.

```hcl
aws_vpc.module-vpc.id
```

Child Module이 공개한 Output을 호출자가 참조한다.

```hcl
module.module-vpc.vpc-id
module.module-vpc.vpc-cidr
```

Output은 Module 외부에 공개하는 Interface다.

---

## 12. Subnet Child Module

`subnet/variables.tf`:

```hcl
variable "vpc-cidr" {
  type = string
}

variable "vpc-id" {
  type = string
}

variable "env" {
  type = string
}
```

`subnet/main.tf`:

```hcl
resource "aws_subnet" "module-subnet" {
  vpc_id           = var.vpc-id
  cidr_block       = cidrsubnet(var.vpc-cidr, 8, 10)
  availability_zone = "ap-northeast-2a"

  tags = {
    Name = "${var.env}-subnet"
  }
}
```

Subnet Module의 입력:

| 입력 | 사용 위치 |
|---|---|
| `vpc-id` | Subnet이 속할 VPC |
| `vpc-cidr` | `cidrsubnet()`의 기준 Network |
| `env` | Name Tag |

현재 결과:

```text
Stage:
10.0.10.0/24
stage-subnet

Prod:
192.168.10.0/24
prod-subnet
```

---

## 13. VPC Output을 Subnet Input으로 전달

Stage와 Prod 모두 다음 연결을 사용한다.

```hcl
module "module-subnet" {
  source = "../subnet"

  env      = "stage"
  vpc-cidr = module.module-vpc.vpc-cidr
  vpc-id   = module.module-vpc.vpc-id
}
```

데이터 흐름:

```text
Root Module이 VPC Child Module 호출
        │
        ├─ cidr
        └─ env
        ▼
VPC Child Module
        │
        ├─ vpc-id Output
        └─ vpc-cidr Output
        ▼
Root Module의 module.module-vpc 참조
        │
        ▼
Subnet Child Module Input
        │
        ▼
aws_subnet.module-subnet
```

핵심:

> Child Module A가 Child Module B를 직접 탐색하는 것이 아니다.  
> Root Module이 A의 Output을 B의 Input으로 연결한다.

현재 참조가 있으므로 Terraform은 Subnet Module이 VPC Module의 결과에 의존한다는 것을 알 수 있다.

---

## 14. Stage와 Prod에서 같은 Module 재사용

### Stage

```hcl
module "module-vpc" {
  source = "../vpc"
  cidr   = "10.0.0.0/16"
  env    = "stage"
}
```

### Prod

```hcl
variable "env" {
  default = "prod"
  type    = string
}

module "module-vpc" {
  source = "../vpc"
  cidr   = "192.168.0.0/16"
  env    = var.env
}
```

같은 구현:

```text
../vpc
../subnet
```

다른 입력:

| 환경 | VPC CIDR | 환경 이름 |
|---|---|---|
| Stage | `10.0.0.0/16` | `stage` |
| Prod | `192.168.0.0/16` | `prod` |

생성 의도:

```text
Stage Root
├─ stage-vpc
└─ stage-subnet

Prod Root
├─ prod-vpc
└─ prod-subnet
```

이것이 Module 재사용의 핵심이다.

---

## 15. Module 분리와 State 분리의 관계

Stage 내부:

```text
stage Root Module
├─ VPC Child Module
└─ Subnet Child Module
```

VPC와 Subnet은 Child Module이 서로 다르지만 같은 Stage Root Module에 속한다. 따라서 기본 Local Backend 기준으로 Stage State 하나에 함께 기록된다.

```text
stage/terraform.tfstate
├─ module.module-vpc...
└─ module.module-subnet...
```

Prod도 별도 Root Module이므로 기본적으로 별도의 State를 가진다.

```text
prod/terraform.tfstate
├─ module.module-vpc...
└─ module.module-subnet...
```

정리:

```text
VPC와 Subnet:
Module은 분리
State는 같은 환경 Root 안에서 공유

Stage와 Prod:
Root Module이 분리
State도 환경별로 분리
```

현재 연결:

```hcl
module.module-vpc.vpc-id
```

이는 같은 Root Module 내부의 Module Output 참조다. `terraform_remote_state`가 아니다.

---

## 16. Dependency Graph

Stage 또는 Prod Root Module의 참조 관계:

```text
module.module-vpc
└─ aws_vpc.module-vpc
       │
       ├─ output.vpc-id
       └─ output.vpc-cidr
               │
               ▼
module.module-subnet
└─ aws_subnet.module-subnet
```

Subnet Module 호출이 VPC Module Output을 참조하므로 다음 의존성이 형성된다.

```text
VPC 생성
→ VPC ID와 CIDR 계산
→ Subnet 생성
```

HCL 파일의 물리적 작성 순서가 아니라 참조 관계가 순서를 결정한다.

---

## 17. 현재 코드에서 직접 관찰된 사항

### 구현된 항목

```text
[x] VPC Child Module
[x] VPC Input Variable
[x] VPC Output
[x] Subnet Child Module
[x] Subnet Input Variable
[x] VPC Output → Subnet Input 연결
[x] Stage Root Module
[x] Prod Root Module
[x] 같은 Child Module의 환경별 재사용
```

### 아직 고정된 값

```hcl
cidr_block        = cidrsubnet(var.vpc-cidr, 8, 10)
availability_zone = "ap-northeast-2a"
```

현재 Subnet은 환경마다 하나이며 다음 값은 고정이다.

```text
Subnet 번호:
10

Availability Zone:
ap-northeast-2a
```

### Stage와 Prod의 `env` 표현 차이

Stage:

```hcl
env = "stage"
```

Prod:

```hcl
variable "env" {
  default = "prod"
}

env = var.env
```

두 방식 모두 값 전달은 가능하다. 강사가 Root Variable 외부화를 설명하는 중인지, 아직 표현을 통일하지 않은 것인지는 현재 코드만으로 확정하지 않는다.

### Provider Region

```hcl
provider "aws" {
  profile = "terra-user"
}
```

Region은 코드에 명시되지 않았다. AWS Profile 또는 환경 설정에서 Region이 제공돼야 한다.

---

## 18. 강사 의도 해석과 다음 단계 후보

> [!note] 교육 흐름 해석
> 아래 내용은 현재 코드 변화와 PDF의 전체 진도를 바탕으로 한 추정이다.  
> 강사가 명시한 문장을 그대로 옮긴 것이 아니다.

현재까지 확인된 교육 순서:

```text
1. VPC Resource를 Child Module로 분리
2. CIDR과 환경 이름을 Input Variable로 전환
3. Stage와 Prod에서 같은 VPC Module 재사용
4. VPC ID와 CIDR을 Output으로 공개
5. Subnet Module 작성
6. VPC Output을 Subnet Input으로 연결
```

가능성이 높은 후속 단계:

```text
- Subnet 설정의 추가 변수화
- 여러 Subnet 또는 반복문과 Module 결합
- Subnet Output 공개
- Web 또는 Security Group Module 추가
- 환경별 Backend 구성
- 서로 다른 State 사이의 Remote State
- Registry 외부 Module 사용
```

현재 코드에 등장하지 않은 Backend, Remote State, Registry Module은 예정 사항으로만 취급한다.

---

## 19. v11.0 완료 판정

### 19-1. 개념

```text
[x] 보편적인 Module 개념과 Terraform Module의 공통점 이해
[x] 디렉터리가 Terraform Module 경계라는 점 이해
[x] Root Module과 Child Module 구분
[x] Input Variable과 Output Interface 구분
[x] Module 분리와 State 분리가 다름을 이해
[x] Module이 선언형 Dependency Graph에 포함됨을 이해
```

### 19-2. 코드 구조

```text
[x] VPC Child Module 구현 확인
[x] Subnet Child Module 구현 확인
[x] Stage/Prod Root Module 확인
[x] VPC Output → Subnet Input 연결 확인
[x] 환경별 Module 재사용 확인
```

### 19-3. 실행 검증

```text
[ ] terraform fmt
[ ] stage terraform init
[ ] stage terraform validate
[ ] stage terraform plan
[ ] prod terraform init
[ ] prod terraform validate
[ ] prod terraform plan
[ ] 실제 apply
[ ] 실제 destroy
```

### 19-4. 최종 판정

```text
v11.0은 Local Module의 기본 구조와
같은 Root Module 내부의 Child Module 연결을 정리한 첫 누적본이다.

현재 코드는 VPC와 Subnet을 별도 Child Module로 분리하고,
Stage와 Prod Root Module이 같은 구현을 다른 입력값으로 재사용한다.

실제 Terraform 실행 결과는 아직 검증하지 않았으므로
인프라 배포 완료로 판정하지 않는다.
```

---

## 20. 한 문단 요약

```text
v11.0에서는 Terraform Module을 입력과 출력을 가진 재사용 가능한 인프라 구성요소로 이해하고, VPC와 Subnet 구현을 각각 Local Child Module로 분리하였다. Stage와 Prod는 독립된 Root Module로서 같은 `../vpc`, `../subnet` 소스를 호출하지만 서로 다른 VPC CIDR과 환경 이름을 전달한다. VPC Module은 생성한 VPC의 ID와 CIDR을 Output으로 공개하고, Root Module은 이를 `module.module-vpc.<output>` 형태로 참조하여 Subnet Module의 Input으로 전달한다. 이 구조를 통해 Module은 일반적인 모듈화·캡슐화·재사용 개념을 따르면서도, Terraform에서는 디렉터리가 Module 경계를 이루고 Module 분리 자체가 State 분리를 의미하지 않으며, Resource 생성 순서는 호출문의 작성 순서가 아니라 Output/Input 참조로 형성된 Dependency Graph에 의해 결정된다는 점을 확인하였다.
```

---

# Appendices

## 부록 A. 최신 폴더 구조

```text
11_modules/
├─ vpc/
│  ├─ main.tf
│  ├─ variables.tf
│  └─ output.tf
├─ subnet/
│  ├─ main.tf
│  └─ variables.tf
├─ stage/
│  └─ main.tf
└─ prod/
   └─ main.tf
```

---

## 부록 B. `11_modules(1)` → `11_modules(2)` 변경 지도

| 변경 대상 | 변경 내용 | 학습 의미 |
|---|---|---|
| `vpc/output.tf` | 새로 추가 | Child Module 결과 공개 |
| `subnet/variables.tf` | 새로 추가 | Subnet Module 입력 Interface |
| `subnet/main.tf` | Resource 구현 | 두 번째 Child Module 구성 |
| `stage/main.tf` | Subnet Module 호출 추가 | 같은 Root에서 Module 조합 |
| `prod/main.tf` | Subnet Module 호출 추가 | 환경별 동일 구조 재사용 |
| `prod/main.tf` | `env` Root Variable 추가 | Root 입력값 외부화 시작 |

---

## 부록 C. 최신 강사 코드 원문


### `vpc/main.tf`

```hcl
resource "aws_vpc" "module-vpc" {
  cidr_block = var.cidr
  tags = {Name = "${var.env}-vpc"}
  enable_dns_hostnames = true
  enable_dns_support = true

}
```

### `vpc/variables.tf`

```hcl
variable "cidr" {
  type = string
}
variable "env" {
  type = string
}
```

### `vpc/output.tf`

```hcl
output "vpc-id" {
  value = aws_vpc.module-vpc.id
}
output "vpc-cidr" {
  value = aws_vpc.module-vpc.cidr_block
}
```

### `subnet/main.tf`

```hcl
resource "aws_subnet" "module-subnet" {
  vpc_id = var.vpc-id
  cidr_block = cidrsubnet(var.vpc-cidr, 8, 10)
  tags = {Name = "${var.env}-subnet"}
  availability_zone = "ap-northeast-2a"
}
```

### `subnet/variables.tf`

```hcl
variable "vpc-cidr" {
  type = string
}
variable "vpc-id" {
  type = string
}
variable "env" {
  type = string
}
```

### `stage/main.tf`

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

module "module-vpc" {
  source = "../vpc"
  cidr   = "10.0.0.0/16"
  env    = "stage"
}

module "module-subnet" {
  source = "../subnet"
  env = "stage"
  vpc-cidr = module.module-vpc.vpc-cidr
  vpc-id = module.module-vpc.vpc-id
}
# terraform init
# terraform apply
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
  type = string
}
module "module-vpc" {
  source = "../vpc"
  cidr   = "192.168.0.0/16"
  env    = var.env
}

module "module-subnet" {
  source = "../subnet"
  env = var.env
  vpc-cidr = module.module-vpc.vpc-cidr
  vpc-id = module.module-vpc.vpc-id
}

# PS C:\terraform\workspace\11_modules\stage> cd ..\prod\
# PS C:\terraform\workspace\11_modules\prod> terraform init
# PS C:\terraform\workspace\11_modules\prod> terraform apply
```

---

## 관련 노트

- [[Terraform RDS 인프라 구성 실습 v10.1]]
- [[Terraform Module]]
- [[Terraform Variable과 Output]]
- [[Terraform Backend와 Remote State]]
- [[Terraform Workflow]]
