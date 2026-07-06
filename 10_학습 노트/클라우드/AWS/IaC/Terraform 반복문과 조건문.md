---
title: Terraform 반복문과 조건문
created: 2026-07-06
status: active
type: concept-note
source:
  - Iac.pdf
  - IaC - Source Digest v2.md
  - IaC - 공식 검증 노트.md
source_pages:
  - p.38-p.41
tags:
  - 과목/AWS
  - 주제/IaC
  - 주제/Terraform
  - 상태/active
  - 개념/Terraform
---

# Terraform 반복문과 조건문

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

Terraform의 반복문과 조건문은 유사한 리소스를 여러 개 만들거나 환경값에 따라 생성 개수·구성을 달리하기 위해 사용하는 표현식이다.

## PDF 기준 범위

PDF p.38-p.41은 다음을 다룬다.

- `count`
- `for_each`
- 조건문
- `count`와 조건문의 조합
- IAM User, EC2 Instance 생성 개수 예시

## `count`

PDF p.39 기준:

```hcl
resource "aws_iam_user" "count_ex1" {
  count = 3
  name  = "Terra.${count.index}"
}
```

PDF 설명:

- 유사한 형태의 여러 Resource를 반복 정의할 때 사용한다.
- Resource Block 전체를 반복 실행한다.
- Resource 내부 인라인 영역을 반복 실행하는 것은 불가능하다고 설명한다.
- `count.index`를 사용해 반복 인덱스를 참조한다.

핵심:

```text
count.index = 0부터 시작하는 반복 인덱스
```

예상 이름:

```text
Terra.0
Terra.1
Terra.2
```

## `for_each`

PDF p.40 기준 기본 구문:

```hcl
resource "<PROVIDER>_<TYPE>" "<NAME>" {
  for_each = <COLLECTION>
  [ CONFIG ... ]
}
```

PDF 설명:

- 리스트, 집합, 맵을 사용하여 유사한 여러 Resource를 반복 정의할 때 사용한다.
- Resource 내부 인라인 영역을 반복 정의할 때 사용할 수 있다고 설명한다.
- `count`의 제약과 단점을 보완하기 위해 사용한다고 설명한다.

## 공식 검증 반영: `for_each` Collection

공식 검증 기준으로 더 정확한 표현은 다음이다.

```text
for_each는 map 또는 set of strings를 받는다.
list/tuple은 자동으로 set으로 변환되지 않으므로, list 기반 반복이 필요하면 toset() 등 명시적 변환이 필요하다.
```

예시:

```hcl
resource "aws_iam_user" "example" {
  for_each = toset(["alice", "bob", "charlie"])
  name     = each.key
}
```

## `count`와 `for_each` 비교

| 항목 | `count` | `for_each` |
|---|---|---|
| 반복 기준 | 숫자 | map 또는 set |
| 식별 방식 | index | key/value |
| 적합한 경우 | 동일 리소스를 단순 개수만큼 생성 | 이름/속성이 다른 리소스를 안정적으로 생성 |
| 참조 방식 | `[0]`, `[1]` 같은 index | `["key"]` |
| 단점 | 중간 요소 삭제 시 index 변화 위험 | collection 설계 필요 |

## Module 사용 제약 정정

PDF/Digest에는 `count`, `for_each`가 Module 내부에서 사용 불가라는 취지의 표현이 확인 필요 항목으로 남아 있었다.

공식 검증 결과, 현재 Terraform 기준은 다음이다.

```text
count와 for_each는 module block에서도 사용할 수 있다.
단, 같은 block에서 count와 for_each를 동시에 사용할 수는 없다.
```

Concept Note에서는 공식 기준을 우선한다. PDF 원문은 Source Digest에 보존한다.

## 조건문

PDF p.41 기준 조건문 형태:

```hcl
condition ? true_val : false_val
```

예시:

```hcl
variable "env" {
  type        = string
  description = "dev or prod ?"
  default     = "dev"
}

resource "aws_instance" "Conditionals_ex1" {
  ami           = "ami-0ea4d4b8dc1e46212"
  instance_type = "t2.micro"
  count         = var.env == "dev" ? 1 : 2

  tags = {
    Name = "Conditionals_Test"
  }
}
```

실행 결과 의미:

| 명령 | 생성 개수 |
|---|---:|
| `terraform plan -var "env=dev"` | 1개 |
| `terraform plan -var "env=prod"` | 2개 |

## PDF 오탈자

p.41에는 `Conunt` 표기가 있다.  
Concept Note와 Lab Note에서는 `Count` 또는 `count`로 정리한다.

## 주의

- 반복 생성은 비용도 반복 생성한다.
- `count`로 만든 리소스의 index 변화는 실제 인프라 교체를 유발할 수 있다.
- `for_each`는 key 기반이라 장기 운영 리소스에는 더 안정적인 경우가 많다.
- 실습에서는 `plan` 출력에서 생성 개수를 반드시 확인한다.

## 관련 노트

- [[Terraform Workflow]]
- [[Terraform Resource와 Data Source]]
- [[Terraform Variable과 Output]]
- [[Terraform Module]]
