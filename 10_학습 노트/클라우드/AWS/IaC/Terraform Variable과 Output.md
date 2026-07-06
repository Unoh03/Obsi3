---
title: Terraform Variable과 Output
created: 2026-07-06
status: active
type: concept-note
source:
  - Iac.pdf
  - IaC - Source Digest v2.md
  - IaC - 공식 검증 노트.md
source_pages:
  - p.29-p.37
tags:
  - 과목/AWS
  - 주제/IaC
  - 주제/Terraform
  - 상태/active
  - 개념/Terraform
---

# Terraform Variable과 Output

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

Terraform의 **Input Variable**은 코드에 주입할 값을 외부화하는 기능이고, **Output**은 생성된 리소스 정보를 명령줄이나 다른 모듈에서 참조할 수 있게 노출하는 기능이다.

## Input Variable

PDF p.30 기준:

```hcl
variable "<NAME>" {
  description = "설명"
  default     = "기본값 정의"
  type        = "변수 유형"
}
```

| 요소 | 의미 |
|---|---|
| `NAME` | 입력 변수 이름 |
| `description` | 변수 설명. `plan`, `apply` 실행 시 함께 출력될 수 있음 |
| `default` | 값이 따로 지정되지 않았을 때 사용할 기본값 |
| `type` | 변수에 전달할 값의 유형 |

PDF 설명:

- Resource 정의 시 Config 영역에서 사용할 값을 저장한다.
- 코드 변경 없이 다양한 argument 값을 지정할 수 있어 유연성이 생긴다.
- Terraform Module 구조를 구현하는 데 필수 요소로 설명된다.

## Variable Type

PDF p.30-p.31 기준 주요 type:

| Type | 의미 |
|---|---|
| `any` | 임의 타입 |
| `string` | 문자열 |
| `number` | 숫자 |
| `bool` | 참/거짓 |
| `list` | 순서 있는 목록 |
| `map` | key-value 구조 |
| `set` | 중복 없는 집합 |
| `object` | 이름 있는 attribute 집합 |
| `tuple` | 위치 기반 복합 값 |

예시:

```hcl
variable "ex1" {
  description = "Number Variable"
  type        = number
  default     = 1000
}
```

```hcl
variable "ex2" {
  description = "List Variable"
  type        = list(any)
  default     = ["A", "B", "C"]
}
```

```hcl
variable "ex5" {
  description = "Object Variable"
  type = object({
    name = string
    age  = number
    flag = bool
  })
  default = {
    name = "TEST"
    age  = 20
    flag = true
  }
}
```

## 변수 값 지정 방식

PDF p.32 기준, 모듈 구조가 아닌 환경에서 입력 변수 값을 지정하는 방식은 세 가지다.

| 방식 | 예시 |
|---|---|
| 명령줄 옵션 `-var` | `terraform plan -var "ex1=100"` |
| 환경변수 | `export TF_VAR_ex1=100` |
| 대화식 입력 | `terraform apply` 실행 후 값 입력 |

예시:

```bash
terraform plan -var "ex1=100"
```

```bash
export TF_VAR_ex1=100
terraform plan
```

모듈 구조에서는 root module에서 child module 호출 시 변수 값을 코드로 넘겨 사용하는 방식이 중요하다.

## Variable 참조

PDF p.33 기준:

```hcl
var."<VARIABLE_NAME>"
```

실제 Terraform 코드에서는 보통 다음처럼 쓴다.

```hcl
var.ssh_port
```

예시:

```hcl
variable "ssh_port" {
  description = "The Port the Server Will use for SSH Service"
  type        = number
}

resource "aws_security_group" "SG_1" {
  name = "terraform-instance"

  ingress {
    from_port   = var.ssh_port
    to_port     = var.ssh_port
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
}
```

## Output

PDF p.34 기준:

```hcl
output "<NAME>" {
  value       = <VALUE>
  description = "설명"
  sensitive   = <Bool>
}
```

| 요소 | 의미 |
|---|---|
| `NAME` | 출력 변수 이름 |
| `value` | 출력할 값 |
| `description` | 출력값 설명 |
| `sensitive` | `true`일 경우 화면 노출 제한. 예: 개인키, 패스워드 |

PDF 설명:

- Terraform 코드로 Resource가 정의된 후 Resource 정보를 출력할 때 사용한다.
- AWS Console이 아니라 명령줄에서 Resource 정보를 바로 확인할 수 있다.
- 예시로 EC2 Public IP 출력이 제시된다.

## Output 예시

PDF p.35 전사 기준:

```hcl
output "EC2_Pub_IP" {
  value       = aws_instance.ExampleEC2.public_ip
  description = "EC2 Instance Public IP Address"
}
```

명령 예시:

```bash
terraform output
terraform output public_ip
```

## p.35 이름 불일치 주의

공식 검증 노트 기준, PDF p.35에는 다음 불일치 가능성이 있다.

| 위치 | 이름 |
|---|---|
| 코드 예시 | `EC2_Pub_IP` |
| 출력 예시 | `public_ip` |

Terraform에서 output 이름은 `output "<NAME>"`의 label이 기준이다.

따라서 실습 노트 작성 시 반드시 이름을 통일한다.

예시 1:

```hcl
output "public_ip" {
  value       = aws_instance.ExampleEC2.public_ip
  description = "EC2 Instance Public IP Address"
}
```

```bash
terraform output public_ip
```

예시 2:

```hcl
output "EC2_Pub_IP" {
  value       = aws_instance.ExampleEC2.public_ip
  description = "EC2 Instance Public IP Address"
}
```

```bash
terraform output EC2_Pub_IP
```

## Variable과 Output의 Module 연결

Variable과 Output은 Module 구조에서 특히 중요하다.

```text
Root Module
→ input variable로 Child Module에 값 전달
→ Child Module에서 resource 생성
→ Child Module output으로 결과 노출
→ Root Module이 module.<name>.<output> 형태로 참조
```

## 실습 아키텍처 연결

PDF p.36-p.37은 Variable/Input/Output을 이용한 VPC, ALB, ASG 예제를 제시한다.

핵심 구성:

- VPC `192.168.0.0/16`
- Public Subnet 2개
- Private Subnet 2개
- BastionHost
- NAT Gateway
- Application Load Balancer
- Auto Scaling
- WEB Server

## 관련 노트

- [[Terraform Resource와 Data Source]]
- [[Terraform Module]]
- [[Terraform Backend와 Remote State]]
