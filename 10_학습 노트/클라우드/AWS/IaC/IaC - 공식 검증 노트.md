---
title: IaC - 공식 검증 노트
created: 2026-07-06
status: active
type: verification-note
source_digest: IaC - Source Digest v2.md
source_pdf: Iac.pdf
source_classification:
  - PDF
  - 인터넷 고신뢰 정보
tags:
  - 과목/AWS
  - 주제/IaC
  - 주제/Terraform
  - 상태/active
---

# IaC - 공식 검증 노트

## 0. 목적

이 노트는 `IaC - Source Digest v2.md`의 **확인 필요 항목**을 Terraform/AWS 공식 자료 기준으로 검증한 결과다.

목표는 다음 단계인 Concept Note 작성 전에 다음을 정리하는 것이다.

1. PDF 원문을 보존해야 하는 부분
2. 공식 문서 기준으로 정정해야 하는 부분
3. 현재 Terraform/AWS 기준으로 표현을 보강해야 하는 부분
4. 실습 노트 작성 시 그대로 쓰면 위험한 부분

---

## 1. 기준 자료

| 구분 | 자료 |
|---|---|
| 기준 PDF | `Iac.pdf` |
| 기준 Digest | `IaC - Source Digest v2.md` |
| 검증 기준 | HashiCorp Terraform 공식 문서, Terraform Registry |
| 검증일 | 2026-07-06 |
| 검증 범위 | `Source Digest v2`의 확인 필요 항목 중심 |
| 미검증 범위 | 실제 AWS 계정에서 Terraform 실행, 강의자료 원본 코드 파일 존재 여부, 실제 Provider 호환 테스트 |

---

## 2. 출처 분류

| 분류 | 이번 노트에서의 사용 |
|---|---|
| **PDF** | `Iac.pdf`, `IaC - Source Digest v2.md`에 기록된 강의자료 원문·전사본 |
| **인터넷 고신뢰 정보** | HashiCorp Terraform 공식 문서, Terraform Registry |
| **내장 지식** | 공식 문서와 PDF를 연결하는 설명, 실습 노트 반영 방식 판단 |
| **인터넷 비공식 고품질 의견** | 이번 검증에서는 사용하지 않음 |

---

## 3. 공식 출처 목록

| ID | 출처 | 신뢰도 | freshness | 검증에 사용한 내용 |
|---|---|---|---|---|
| H-TF-DESTROY | HashiCorp Developer - Destroy a resource | 공식 | Current checked, Date absent | `terraform destroy` 명령 확인 |
| H-TF-LOCK | HashiCorp Developer - Dependency Lock File | 공식 | Current checked, Date absent | `.terraform.lock.hcl` 역할 확인 |
| H-TF-COUNT | HashiCorp Developer - count meta-argument | 공식 | Current checked, Date absent | `count` 지원 블록, `count.index`, `count`/`for_each` 동시 사용 불가 |
| H-TF-FOREACH | HashiCorp Developer - for_each meta-argument | 공식 | Current checked, Date absent | `for_each`의 map/set 요구, list/tuple 자동 변환 없음, module block 지원 |
| H-TF-MODULE | HashiCorp Developer - module block reference | 공식 | Current checked, Date absent | module block에서 `count`/`for_each` 사용 가능 확인 |
| H-TF-REMOTE | HashiCorp Developer - terraform_remote_state data source | 공식 | Current checked, Date absent | 다른 Terraform configuration의 root output 참조 |
| H-TF-S3 | HashiCorp Developer - S3 backend | 공식 | Current checked, Date absent | S3 backend, state locking, DynamoDB locking deprecated |
| H-TF-OUTPUT | HashiCorp Developer - Use outputs | 공식 | Current checked, Date absent | root/child module output 동작 |
| REG-VPC | Terraform Registry - terraform-aws-modules/vpc/aws | 공식 Registry | Current checked, Date explicit in search result | 최신 모듈 버전 drift 확인 |
| REG-SG | Terraform Registry - terraform-aws-modules/security-group/aws | 공식 Registry | Current checked, Date explicit in search result | 최신 모듈 버전 drift 확인 |

> URL은 Obsidian에서 직접 열람할 수 있도록 아래에 별도 보존한다.
>
> - H-TF-DESTROY: https://developer.hashicorp.com/terraform/language/resources/destroy
> - H-TF-LOCK: https://developer.hashicorp.com/terraform/language/files/dependency-lock
> - H-TF-COUNT: https://developer.hashicorp.com/terraform/language/meta-arguments/count
> - H-TF-FOREACH: https://developer.hashicorp.com/terraform/language/meta-arguments/for_each
> - H-TF-MODULE: https://developer.hashicorp.com/terraform/language/block/module
> - H-TF-REMOTE: https://developer.hashicorp.com/terraform/language/state/remote-state-data
> - H-TF-S3: https://developer.hashicorp.com/terraform/language/backend/s3
> - H-TF-OUTPUT: https://developer.hashicorp.com/terraform/language/values/outputs
> - REG-VPC: https://registry.terraform.io/modules/terraform-aws-modules/vpc/aws/latest
> - REG-SG: https://registry.terraform.io/modules/terraform-aws-modules/security-group/aws/latest

---

## 4. 검증 결과 요약

| 항목 | PDF/Digest 표기 | 공식 기준 | 판정 | Concept Note 반영 방식 |
|---|---|---|---|---|
| Terraform 삭제 명령 | `terraform destory` | `terraform destroy` | PDF 오타로 판정 | 원문은 보존, 실습 노트에는 `terraform destroy` 사용 |
| `.terraform.lock.hcl` | Provider 선택 기록/잠금 파일 | Provider dependency version selection을 기록. root module 작업 디렉터리에 위치. `terraform init` 때 생성/갱신 | 대체로 맞음, 설명 보강 필요 | “Provider 버전 선택을 재현하기 위한 dependency lock file”로 설명 |
| `count` | 반복 생성, `count.index` 사용 | resource/module/data 등에서 사용 가능. `count.index` 제공 | 맞음 | 그대로 사용 가능 |
| `for_each` | map/set, list 미지원 취지 | map 또는 set of strings. list/tuple은 자동으로 set 변환되지 않음. `toset()` 필요 | 맞음 | “list 자체 불가”보다 “명시적 set 변환 필요”로 표현 |
| `count`, `for_each`와 module | Digest에 “Module 내부에서는 사용 불가” 확인 필요 | module block에서 `count`, `for_each` 사용 가능 | 정정 필요 | “현재 Terraform에서는 module block에도 사용 가능”으로 수정 |
| `terraform_remote_state` | 서로 다른 Module 간 참조에 사용 | 다른 Terraform configuration의 root output을 state backend에서 읽음 | 조건부 정정 | 같은 root module 내부는 직접 output 전달, 다른 state/configuration 간은 remote state |
| S3 backend + DynamoDB Lock | S3 backend + DynamoDB table + encrypt | S3 backend는 state 저장 가능. 현재 DynamoDB 기반 locking은 deprecated. S3 lockfile 방식 권장 | 현재화 필요 | 강의자료는 보존하되, 최신 실무 노트에는 `use_lockfile = true` 우선 |
| 외부 VPC module 버전 | `terraform-aws-modules/vpc/aws` v5.1.1 | Registry latest는 별도 최신 버전으로 drift 발생 | 확인 필요 유지 | 실습 재현은 PDF 버전, 새 프로젝트는 최신 버전 문서 확인 |
| 외부 SG module 버전 | `terraform-aws-modules/security-group/aws` v5.1.0 | Registry latest는 6.0.0으로 확인됨 | 현재화 필요 | 버전 고정 이유와 최신 문서 확인 필요 표시 |
| Output 이름 불일치 | 코드 `EC2_Pub_IP`, 출력 예시 `public_ip` | Terraform output 이름은 output block label이 기준 | PDF/전사 불일치 가능성 | 원본 이미지 대조 후 하나로 정리. 실습 노트에는 동일 이름 사용 |

---

## 5. 항목별 검증

### 5.1 `terraform destory` vs `terraform destroy`

#### PDF/Digest 상태

- `IaC - Source Digest v2.md` p.19 전사에 `terraform destory`가 등장한다.
- p.9에도 `destory` 표기가 확인 필요 항목으로 기록되어 있다.

#### 공식 기준

공식 문서 기준 Terraform 전체 인프라 삭제 명령은 다음이다.

```bash
terraform destroy
```

#### 판정

`terraform destory`는 **PDF 오타**로 판정한다.

#### 반영 방식

```markdown
- PDF 원문: `terraform destory`
- 공식 기준: `terraform destroy`
- 판정: PDF 오타
```

실습 노트에는 반드시 다음처럼 쓴다.

```bash
terraform destroy
```

---

### 5.2 `.terraform.lock.hcl` 역할

#### PDF/Digest 상태

- `terraform init` 후 `.terraform.lock.hcl`이 생성된다고 설명한다.
- 잠금 파일로 설명되어 있다.

#### 공식 기준

`.terraform.lock.hcl`은 Terraform configuration 전체에 속하는 dependency lock file이다. root module의 `.tf` 파일이 있는 현재 작업 디렉터리에 생성된다. `terraform init` 실행 시 자동 생성 또는 갱신된다.

중요한 점은 다음과 같다.

- 현재 Terraform 기준으로 lock file은 **Provider dependency** 선택을 추적한다.
- Terraform은 lock file에 기록된 provider version selection을 이후 실행에서도 기본적으로 재사용한다.
- remote module version selection은 lock file에 저장하지 않는다.
- 버전 관리에 포함하는 것이 권장된다.

#### 판정

PDF 설명은 큰 방향에서 맞지만, Concept Note에는 다음처럼 더 정확히 적어야 한다.

```text
.terraform.lock.hcl은 Terraform provider dependency의 선택 버전과 checksum을 기록하여,
다음 init 시 동일 provider 버전을 재선택하도록 돕는 dependency lock file이다.
```

#### 반영 방식

- `terraform init` 노트에 포함
- Terraform Workflow 노트에 포함
- Git 관리 정책과 연결 가능

---

### 5.3 `count`

#### PDF/Digest 상태

- `count = 3`
- `name = "Terra.${count.index}"`
- 반복적으로 IAM User를 생성하는 예시가 있다.
- 조건문과 함께 `count = var.env == "dev" ? 1 : 2` 예시가 있다.

#### 공식 기준

공식 문서 기준 `count`는 다음 블록에서 사용할 수 있다.

- `resource`
- `module`
- `data`
- `ephemeral`
- query `list`

`count.index`는 0부터 시작하는 index number를 제공한다. `count`와 `for_each`는 같은 `resource` 또는 `module` block 안에서 동시에 사용할 수 없다.

#### 판정

PDF의 `count` 설명은 대체로 맞다.  
단, module 관련 제약 표현은 별도로 정정해야 한다.

#### 반영 방식

Concept Note에는 다음을 포함한다.

```text
count는 동일하거나 거의 동일한 리소스/모듈 인스턴스를 여러 개 만들 때 쓰는 meta-argument다.
각 인스턴스는 count.index로 0부터 시작하는 인덱스를 가진다.
```

---

### 5.4 `for_each`

#### PDF/Digest 상태

- `for_each = <COLLECTION>`
- Collection은 set 또는 map으로 설명된다.
- Resource 내부에서 `for_each`를 사용하는 경우 list는 지원되지 않는다고 설명한다.

#### 공식 기준

공식 문서 기준 `for_each`는 `map` 또는 `set of strings`를 받는다.  
list 또는 tuple은 자동으로 set으로 변환되지 않으므로 `toset()` 같은 명시적 변환이 필요하다.

#### 판정

PDF의 “list 미지원” 취지는 맞지만, 더 정확한 표현은 다음이다.

```text
for_each는 map 또는 set of strings를 받는다.
list/tuple은 자동 변환되지 않으므로, list를 기반으로 반복하려면 toset() 등으로 명시 변환해야 한다.
```

#### 반영 방식

`Terraform 반복문과 조건문.md`에 반영한다.

---

### 5.5 `count`, `for_each`와 Module 사용 제약

#### PDF/Digest 상태

- `Source Digest v2`에서는 p.40에 “`count`, `for_each`는 Module 내부에서는 사용 불가라고 설명한다”는 확인 필요 항목이 있다.

#### 공식 기준

공식 문서 기준:

- `count`는 `module blocks`에서 사용할 수 있다.
- `for_each`도 `module blocks`에서 사용할 수 있다.
- `module` block reference에서도 `count` 또는 `for_each`를 사용해 module resource의 여러 instance를 만들 수 있다고 설명한다.

#### 판정

현재 Terraform 기준으로 **정정 필요**다.

다만 PDF 문장이 “Module 내부”라는 표현을 어떤 의미로 썼는지에 따라 해석 여지가 있다.

| 해석 | 판정 |
|---|---|
| module block 자체에서 `count`/`for_each`를 못 쓴다는 의미 | 틀림 |
| 특정 강의 실습 구조에서 child module 내부 반복 사용을 제한했다는 의미 | 강의 제약일 수 있음 |
| 예전 Terraform 버전 기준 설명 | 현재 기준으로는 오래된 설명 가능성 |

#### 반영 방식

Concept Note에는 다음처럼 쓴다.

```text
현재 Terraform 기준으로 count와 for_each는 module block에서도 사용할 수 있다.
단, count와 for_each를 같은 block에 동시에 사용할 수는 없다.
```

PDF 원문은 Source Digest에 보존하되, 개념 노트에서는 공식 기준을 우선한다.

---

### 5.6 `terraform_remote_state`

#### PDF/Digest 상태

- p.47에서 서로 다른 Module인 VPC와 Web-Cluster 간 Resource 참조를 위해 `terraform_remote_state`를 사용해야 한다고 설명한다.
- `terraform_remote_state`는 Terraform 상태파일에 저장된 정보를 Data Source로 사용하는 것이라고 설명한다.

#### 공식 기준

`terraform_remote_state` data source는 지정된 state backend의 최신 state snapshot에서 **다른 Terraform configuration의 root module output values**를 가져온다.

중요한 제약:

- provider 설정 없이 built-in provider로 사용 가능
- root output만 노출된다.
- nested module output은 root module에서 다시 output으로 노출해야 접근 가능하다.
- remote state output을 읽으려면 결과적으로 state snapshot에 접근 가능한 권한이 필요하다. 민감정보 포함 가능성에 주의해야 한다.

#### 판정

PDF 설명은 부분적으로 맞지만, 표현을 보강해야 한다.

정확한 기준:

```text
terraform_remote_state는 “다른 Terraform configuration/state”의 root output을 참조할 때 사용한다.
같은 root module 안에서 child module끼리 값을 전달하는 경우에는 remote state보다 module output을 parent root module에서 연결하는 방식이 일반적이다.
```

#### 반영 방식

`Terraform Module.md`와 `Terraform Backend와 Remote State.md`에 둘 다 반영한다.

---

### 5.7 S3 Backend + DynamoDB Lock

#### PDF/Digest 상태

p.45 전사 기준:

```hcl
terraform {
  backend "s3" {
    key = "prod/terraform.tfstate"
  }
}
```

`backend.hcl`:

```hcl
bucket         = "myterraform-bucket-state-choi-t"
region         = "ap-northeast-2"
profile        = "terraform_user"
dynamodb_table = "myTerraform-bucket-lock-choi-t"
encrypt        = true
```

#### 공식 기준

Terraform S3 backend는 state를 S3 object로 저장한다.  
S3 backend의 state locking은 opt-in이다.

현재 공식 문서 기준:

- S3 lockfile 방식: `use_lockfile = true`
- DynamoDB 기반 locking: deprecated, future minor version에서 제거 예정
- 마이그레이션을 위해 S3/DynamoDB locking 설정을 동시에 둘 수 있음
- S3 bucket versioning 활성화가 강력히 권장됨
- `use_lockfile` 사용 시 `<key>.tflock` object에 대한 권한도 필요함

#### 판정

PDF는 예전 또는 교육용 구성으로 볼 수 있다.  
현재 실무/Concept Note 기준에서는 다음처럼 현재화해야 한다.

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

단, 실제 프로젝트에서 bucket, key, region, profile, KMS, IAM 권한은 별도 설계가 필요하다.

#### 반영 방식

- PDF 원문: DynamoDB table 사용 보존
- 공식 현재 기준: `use_lockfile = true` 우선
- DynamoDB locking: deprecated 표시
- 실습 재현 목적이면 PDF 방식 유지 가능
- 새 프로젝트 설계 목적이면 S3 lockfile 방식으로 정리

---

### 5.8 외부 Module 버전

#### PDF/Digest 상태

p.49:

```hcl
module "stage_vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "5.1.1"
}
```

p.50:

```hcl
module "SSH_security-group" {
  source  = "terraform-aws-modules/security-group/aws"
  version = "5.1.0"
}
```

#### 공식 기준

Terraform Registry 기준 latest version은 PDF 작성 당시와 달라질 수 있다.

이번 확인 기준:

- `terraform-aws-modules/vpc/aws` latest는 `6.x` 계열로 drift 확인
- `terraform-aws-modules/security-group/aws` latest는 `6.0.0`으로 확인
- `security-group/aws` v5.1.0 페이지는 존재하며, Terraform 0.13 이상에서는 v4.5.0 이상을 사용하라는 호환성 설명이 확인됨

#### 판정

PDF의 version pinning은 강의 시점의 실습 재현에는 유효할 수 있다.  
그러나 새 프로젝트 Concept Note에서는 “그대로 최신”이라고 쓰면 안 된다.

#### 반영 방식

```text
PDF 실습 재현: PDF에 적힌 version을 사용한다.
새 프로젝트 설계: Registry latest와 module changelog를 확인하고 version pinning한다.
```

주의:

- major version이 바뀌면 input/output 이름, 기본값, provider requirement가 달라질 수 있다.
- `latest`를 무작정 쓰지 말고, 명시적 version pinning을 유지한다.

---

### 5.9 p.35 Output 이름 불일치

#### PDF/Digest 상태

p.35 전사:

```hcl
output "EC2_Pub_IP" {
  value       = aws_instance.ExampleEC2.public_ip
  description = "EC2 Instance Public IP Address"
}
```

출력 예시:

```text
Outputs:
public_ip = 54.123.45.6

terraform output
public_ip = 54.123.45.6

terraform output public_ip
54.123.45.6
```

#### 공식 기준

Terraform output name은 `output "<NAME>"` block의 label에 의해 결정된다.  
root module output은 `terraform apply` 후 CLI에 표시될 수 있고, `terraform output` 명령으로 조회할 수 있다.

#### 판정

`EC2_Pub_IP`와 `public_ip`가 동시에 등장하는 것은 PDF/전사/예제 간 불일치 가능성이 높다.

#### 반영 방식

실습 노트 작성 시에는 반드시 하나로 통일한다.

예:

```hcl
output "public_ip" {
  value       = aws_instance.ExampleEC2.public_ip
  description = "EC2 Instance Public IP Address"
}
```

그리고 명령:

```bash
terraform output public_ip
```

또는 PDF 원문 이름을 유지하려면:

```hcl
output "EC2_Pub_IP" {
  value       = aws_instance.ExampleEC2.public_ip
  description = "EC2 Instance Public IP Address"
}
```

명령도 같이 맞춘다.

```bash
terraform output EC2_Pub_IP
```

---

## 6. Concept Note 반영 지침

### 6.1 `Terraform Workflow.md`

반영할 내용:

- `terraform init`
- `.terraform.lock.hcl`
- `terraform plan`
- `terraform apply`
- `terraform destroy`

주의:

- PDF 오타 `destory`는 원문 보존 영역에서만 언급
- 실습 명령은 `destroy` 사용

---

### 6.2 `Terraform 반복문과 조건문.md`

반영할 내용:

- `count`
- `count.index`
- `for_each`
- `each.key`, `each.value`
- `condition ? true_val : false_val`

정정 반영:

```text
현재 Terraform 기준으로 count와 for_each는 module block에서도 사용할 수 있다.
for_each는 map 또는 set of strings를 받으며, list/tuple은 자동으로 set 변환되지 않는다.
```

---

### 6.3 `Terraform Module.md`

반영할 내용:

- Root Module
- Child Module
- Local Module
- Registry Module
- Module source
- Module input/output

정정 반영:

```text
같은 root module 안에서 child module 간 값을 전달할 때는 root module에서 module output을 연결한다.
다른 Terraform configuration/state 간 값을 공유할 때 terraform_remote_state를 사용한다.
```

---

### 6.4 `Terraform Backend와 Remote State.md`

반영할 내용:

- local state
- remote state
- backend
- S3 backend
- state locking
- `terraform_remote_state`

현재화 반영:

```text
S3 backend의 DynamoDB 기반 locking은 현재 공식 문서에서 deprecated로 표시된다.
새 설계에서는 S3 lockfile 방식인 use_lockfile = true를 우선 검토한다.
```

---

### 6.5 `AWS 프로젝트에 Terraform 적용하기.md`

반영할 내용:

- 실습 재현 목적과 실제 프로젝트 설계 목적을 분리한다.
- PDF version pinning을 그대로 사용할지, 최신 module version으로 재작성할지 결정해야 한다.
- 팀 작업에서는 remote state, lock, IAM 권한, S3 bucket versioning을 별도 설계해야 한다.

---

## 7. 최종 판정

| 항목 | 최종 판정 |
|---|---|
| Source Digest v2 | Concept Note 작성 기준본으로 사용 가능 |
| 공식 검증 | 1차 완료 |
| PDF 오타 | `terraform destory`, `Conunt`, `Resorce` 등은 원문 보존 + 정정 표시 |
| 최신성 반영 필요 | S3 Backend Locking, 외부 Module 버전 |
| Concept Note 진입 가능 여부 | 가능. 단, 공식 검증 결과를 반영해야 함 |
| Lab Note 진입 가능 여부 | 아직 보류. Concept Note 이후 실습 목적이 명확할 때 작성 |

---

## 8. 다음 작업

다음 단계는 Concept Note 작성이다.

권장 순서:

1. `IaC 개념.md`
2. `IaC 도구 분류.md`
3. `Terraform 개요.md`
4. `Terraform Workflow.md`
5. `Terraform Resource와 Data Source.md`
6. `Terraform Variable과 Output.md`
7. `Terraform 반복문과 조건문.md`
8. `Terraform Module.md`
9. `Terraform Backend와 Remote State.md`

Lab Note는 Concept Note를 만든 뒤, 실제 실행 목적이 있는 부분만 분리한다.
