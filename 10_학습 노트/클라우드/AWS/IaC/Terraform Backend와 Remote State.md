---
title: Terraform Backend와 Remote State
created: 2026-07-06
status: active
type: concept-note
source:
  - Iac.pdf
  - IaC - Source Digest v2.md
  - IaC - 공식 검증 노트.md
source_pages:
  - p.43
  - p.45
  - p.47-p.52
tags:
  - 과목/AWS
  - 주제/IaC
  - 주제/Terraform
  - 상태/active
  - 개념/Terraform
  - 개념/State
---

# Terraform Backend와 Remote State

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

Terraform Backend는 state 저장 위치와 잠금 방식을 정의하는 설정이고, Remote State는 외부 저장소에 있는 Terraform state의 output 값을 다른 구성에서 참조하는 방식이다.

## Terraform State

PDF p.9는 Terraform Workflow에서 현재 구성되어 있는 인프라 상태를 `Terraform State`로 확인한다고 설명한다.

State의 역할:

- Terraform 코드가 관리하는 리소스와 실제 인프라의 대응 관계 저장
- 현재 상태와 목표 상태 비교
- `plan`, `apply`, `destroy`의 판단 근거
- module output과 resource attribute 참조 기반 제공

## Backend

Backend는 state를 어디에 저장하고 어떻게 접근할지 정의한다.

PDF p.45 예시:

```hcl
terraform {
  backend "s3" {
    key = "prod/terraform.tfstate"
  }

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}
```

`backend.hcl` 예시:

```hcl
bucket         = "myterraform-bucket-state-choi-t"
region         = "ap-northeast-2"
profile        = "terraform_user"
dynamodb_table = "myTerraform-bucket-lock-choi-t"
encrypt        = true
```

초기화 명령:

```bash
terraform init -backend-config="C:\Terraform_module\global\s3\backend.hcl"
```

## S3 Backend

PDF 기준:

- S3 bucket에 state 파일 저장
- `key = "prod/terraform.tfstate"`로 저장 경로 지정
- `backend.hcl`로 bucket, region, profile, DynamoDB table, encrypt 설정
- backend 구성 정보 변경 시 `-backend-config` 사용

## 공식 검증 반영: S3 Locking

현재 HashiCorp 공식 문서 기준:

- S3 backend는 state를 S3 object로 저장한다.
- state locking은 opt-in이다.
- S3 lockfile 방식은 `use_lockfile = true`로 설정한다.
- DynamoDB 기반 locking은 deprecated로 표시된다.
- S3 bucket versioning 활성화가 강력히 권장된다.

현재화된 예시:

```hcl
terraform {
  backend "s3" {
    bucket       = "example-bucket"
    key          = "prod/terraform.tfstate"
    region       = "ap-northeast-2"
    encrypt      = true
    use_lockfile = true
  }
}
```

주의:

- PDF의 DynamoDB table 방식은 강의자료 원문으로 보존한다.
- 새 설계에서는 `use_lockfile = true` 우선 검토가 필요하다.
- 기존 환경 마이그레이션에서는 두 방식을 함께 둘 수 있는지 공식 문서를 확인해야 한다.

## `terraform_remote_state`

PDF p.47 기준 설명:

```text
서로 다른 모듈(VPC <-> Web-Cluster)로 구성된 Resource 간 참조를 위해 terraform_remote_state를 사용해야 한다.
terraform_remote_state는 Terraform 상태파일에 저장된 정보를 Data Source로 사용하는 것이다.
```

공식 검증 기준으로 정확히 말하면:

```text
terraform_remote_state data source는 다른 Terraform configuration의 root module output values를
state backend에서 읽어오는 기능이다.
```

중요한 제약:

- root output만 읽을 수 있다.
- nested module output은 root module에서 다시 output으로 노출해야 한다.
- state snapshot 접근 권한이 필요하다.
- state 안에 민감정보가 포함될 수 있으므로 접근 제어가 중요하다.

## 같은 Root Module 내부 vs 다른 State 참조

| 상황 | 권장 방식 |
|---|---|
| 같은 root module 안에서 `vpc` module output을 `web-cluster` module input으로 전달 | `module.vpc.<output>`을 root module에서 연결 |
| 다른 Terraform configuration/state에 있는 output을 참조 | `terraform_remote_state` 사용 |
| 팀 단위로 state 공유 | Remote backend + locking + IAM 접근 제어 |
| 민감한 output 공유 | remote state 대신 별도 secret/config store 검토 |

## PDF p.47 오류의 의미

오류:

```text
A managed resource "aws_vpc" "my_vpc" has not been declared in module.web-cluster.
```

의미:

- `web-cluster` module 안에는 `aws_vpc.my_vpc`가 없다.
- 다른 module 내부 resource를 직접 참조할 수 없다.
- 필요한 값은 input variable로 전달해야 한다.
- 다른 state에 있는 값이면 `terraform_remote_state`로 root output을 읽어야 한다.

## 실습 3 요구조건

PDF p.48 기준:

- Stage 환경 Resource 삭제 후 작업
- Prod 환경 배포
- Local Module 활용: VPC, WEB-Cluster
- Backend Key: `prod/terraform.tfstate`
- VPC CIDR: `192.168.0.0/16`
- Public/Private을 24 bit network로 구성
- Instance Type: `m4.large`
- ASG Min: 2
- ASG Max: 4
- Terraform Remote State로 Module 간 참조 구현
- 테스트 후 Resource 삭제

## 실습 4 요구조건

PDF p.52 기준:

- Stage 환경 Resource 삭제 후 작업
- Prod 환경 배포
- 외부 Module: VPC, Security-Group
- Local Module: Web-Cluster
- Backend Key: `prod/terraform.tfstate`
- VPC CIDR: `192.168.0.0/16`
- Public/Private을 24 bit network로 구성
- Instance Type: `m4.large`
- ASG Min: 2
- ASG Max: 4
- Terraform Remote State로 Module 간 참조 구현
- 테스트 후 Resource 삭제

## 보안 관점 주의

- Remote state는 인프라 구조와 output 값을 담는다.
- state 접근 권한은 사실상 인프라 정보 접근 권한이다.
- S3 bucket policy, IAM 권한, encryption, versioning, locking을 함께 설계해야 한다.
- `sensitive = true` output도 state 내부에는 값이 남을 수 있으므로 state 보호가 필요하다.

## 관련 노트

- [[Terraform Workflow]]
- [[Terraform Variable과 Output]]
- [[Terraform Module]]
