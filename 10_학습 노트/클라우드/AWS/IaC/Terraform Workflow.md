---
title: Terraform Workflow
created: 2026-07-06
status: active
type: concept-note
source:
  - Iac.pdf
  - IaC - Source Digest v2.md
  - IaC - 공식 검증 노트.md
source_pages:
  - p.9-p.11
  - p.14-p.19
tags:
  - 과목/AWS
  - 주제/IaC
  - 주제/Terraform
  - 상태/active
  - 개념/Terraform
  - 실습/Terraform
---

# Terraform Workflow

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

Terraform Workflow는 작성한 `.tf` 코드와 현재 인프라 상태를 비교하고, 변경 계획을 확인한 뒤, 실제 인프라에 반영하거나 삭제하는 흐름이다.

## PDF 기준 Workflow

PDF p.9는 Terraform Workflow를 다음 순서로 설명한다.

```text
코드 작성/수정
→ 현재 인프라 상태 확인(Terraform State)
→ 코드의 목표 상태와 현재 상태 비교(plan)
→ 실제 인프라 변경(apply)
→ Terraform 코드로 배포된 리소스 삭제(destroy)
```

PDF 원문에는 삭제 명령이 `destory`로 표기되어 있으나, 공식 검증 결과 실제 명령은 `destroy`다.

## 주요 명령어

| 명령어 | 역할 | 공식 검증 반영 |
|---|---|---|
| `terraform fmt` | HCL 코드 포맷 정리 | PDF p.10에 TIP으로 등장 |
| `terraform init` | 작업 디렉터리 초기화, provider/module/backend 준비 | HashiCorp 공식 문서 기준 첫 실행 명령 |
| `terraform plan` | 실제 변경 전 실행 계획 확인 | `+`, `-`, `~`로 변경 요약 |
| `terraform apply` | plan을 바탕으로 실제 리소스 생성/변경 | 사용자 승인 후 반영 |
| `terraform destroy` | Terraform이 관리하는 리소스 삭제 | PDF의 `destory`는 오타로 처리 |

## `terraform init`

PDF p.11의 핵심:

- Provider Resource, Data Source를 다운로드한다.
- Terraform 초기 구성 작업을 수행한다.
- Terraform 및 Provider 설정이 변경되면 다시 수행해야 한다.
- `.terraform.lock.hcl` 파일이 생성된다.

공식 검증 반영:

- `terraform init`은 Terraform configuration 파일이 있는 작업 디렉터리를 초기화한다.
- 새 configuration을 작성하거나 기존 configuration을 clone한 뒤 처음 실행해야 하는 명령이다.
- 여러 번 실행해도 안전한 명령으로 설명된다.
- Provider 설치 후 선택된 provider 정보를 dependency lock file에 기록한다.

## `.terraform.lock.hcl`

PDF는 `.terraform.lock.hcl`을 잠금 파일로 설명한다.

공식 검증 결과, 더 정확한 표현은 다음이다.

```text
.terraform.lock.hcl은 Terraform provider dependency의 선택 버전과 checksum을 기록하여,
다음 init 시 동일 provider 버전을 재선택하도록 돕는 dependency lock file이다.
```

주의:

- 이것은 주로 Provider dependency lock file이다.
- 원격 state 동시 접근 방지용 lock과 혼동하면 안 된다.
- 팀 프로젝트에서는 버전 관리에 포함하는 것이 권장된다.

## `terraform plan`

PDF p.14 기준:

| 기호 | 의미 |
|---|---|
| `+` | 생성 |
| `-` | 삭제 |
| `~` | 변경 |

예시 요약:

```text
Plan: 1 to add, 0 to change, 0 to destroy.
```

의미:

- 리소스 1개 생성 예정
- 변경 리소스 없음
- 삭제 리소스 없음

## `terraform apply`

PDF p.15, p.17, p.22, p.26 기준:

- `apply`는 실제 리소스 정의/생성/변경을 수행한다.
- 실행 중 계획이 출력된다.
- 사용자는 `yes`를 입력하여 승인한다.
- 실행 후 `Apply complete!`와 함께 생성/변경/삭제 수가 표시된다.

예시:

```text
Apply complete! Resources: 1 added, 0 changed, 0 destroyed.
```

## `terraform destroy`

PDF p.19 원문:

```text
terraform destory
```

공식 검증 결과:

```bash
terraform destroy
```

실습 노트에는 반드시 `terraform destroy`로 쓴다.

## 의존성 처리

PDF p.9는 Terraform이 리소스 간 의존 관계를 별도로 명시하지 않아도 스스로 의존 관계를 파악하고 병렬 배포한다고 설명한다.

예:

```text
Security Group 생성
→ EC2 생성
→ EC2에 Security Group 연결
```

Terraform은 리소스 참조 관계를 보고 생성 순서를 정한다.

## 실습 노트로 분리할 후보

이 노트 자체는 Concept Note다. 실제 실행 절차는 별도 Lab Note로 분리한다.

- `Terraform 초기화 실습.md`
- `Terraform EC2 생성 수정 삭제 실습.md`
- `Terraform Resource 참조 실습.md`
- `Terraform Data Source 실습.md`

## 확인 필요

- 실제 AWS 계정에서 실행하면 비용이 발생할 수 있다.
- `destroy` 전후 리소스 삭제 여부를 AWS Console에서 검증해야 한다.
- `apply` 성공 여부는 `plan`만으로 보장되지 않는다.

## 관련 노트

- [[Terraform 개요]]
- [[Terraform Resource와 Data Source]]
- [[Terraform Backend와 Remote State]]
