---
title: Terraform 개요
created: 2026-07-06
status: active
type: concept-note
source:
  - Iac.pdf
  - IaC - Source Digest v2.md
  - IaC - 공식 검증 노트.md
  - raw 노트.md
source_pages:
  - p.6-p.8
tags:
  - 과목/AWS
  - 주제/IaC
  - 주제/Terraform
  - 상태/active
  - 개념/Terraform
---

# Terraform 개요

## Source Classification

| 내용 | 출처 분류 | 비고 |
|---|---|---|
| 강의자료 기반 핵심 내용 | PDF | `Iac.pdf`, `IaC - Source Digest v2.md` 기준 |
| Terraform 현재 동작 검증 | 인터넷 고신뢰 정보 | `IaC - 공식 검증 노트.md`와 HashiCorp 공식 문서 기준 |
| 설명 재구성 | 내장 지식 | PDF와 공식 검증 내용을 학습 노트 형태로 재배열 |
| 수업 중 의문/문제의식 | 사용자 raw 메모 | `raw 노트.md` 기준 보강 |
| 커뮤니티 의견 | 인터넷 비공식 고품질 의견 | 이 노트에서는 사용하지 않음 |

## 한 줄 정의

**Terraform**은 HashiCorp가 개발한 오픈소스 IaC 도구로, 클라우드 API 호출을 코드로 정의하여 인프라 리소스를 생성·수정·삭제한다.

## PDF 기반 핵심

PDF p.7은 Terraform을 다음처럼 설명한다.

- HashiCorp사가 Go 언어로 개발한 오픈소스 도구
- 여러 클라우드 공급자를 지원
- 각 클라우드 플랫폼의 API를 호출하여 리소스를 생성
- API 호출을 코드로 정의
- 마스터 서버나 에이전트 설치가 필요 없음
- 구성 관리가 간편하고 추가 서버 구성이 필요 없음
- 선언적 언어를 지향

## 선언적 언어

PDF는 Terraform을 **선언적 언어**로 설명한다.

```text
선언적 언어
= 어떻게 처리할지보다, 구현하려는 최종 상태를 지정하는 코드
```

PDF 예시의 핵심:

| 상황 | 결과 |
|---|---|
| 기존 서버 10대가 있음 |
| 서버 수를 10 → 15로 변경 |
| 절차적 방식 | 기존 10대에 새로 15대를 더 만들어 총 25대가 될 수 있음 |
| 선언적 방식 | 최종 목표가 15대이므로 5대만 추가되어 총 15대 유지 |

## 선언적 언어와 재실행성

수업 raw 노트의 질문처럼 “선언적 언어는 재실행성이 좋다”고 이해해도 어느 정도 맞다. 다만 더 정확한 표현은 다음이다.

```text
Terraform은 코드에 적힌 목표 상태와 현재 상태를 비교해서,
필요한 변경만 계획하려고 한다.
```

즉, 같은 코드를 다시 실행한다고 해서 무조건 같은 리소스를 계속 새로 만드는 것이 아니다. Terraform은 state와 provider를 통해 파악한 현재 상태를 기준으로 “이미 목표 상태와 같으면 바꿀 것이 없음”에 가깝게 동작한다.

주의할 점:

- “재실행해도 항상 안전하다”는 뜻은 아니다.
- 코드, state, 실제 클라우드 리소스 상태가 어긋나면 예상과 다른 plan이 나올 수 있다.
- `plan`으로 변경 예정 사항을 확인하고 `apply`해야 한다.

## Terraform의 장점

PDF p.8 기준:

- 별도 콘솔 로그인 없이 인프라 리소스를 관리·운영할 수 있다.
- 일관성 있는 배포를 수행할 수 있다.
- 자동화된 관리를 지원하여 빠른 배포가 가능하다.
- 인프라 배포 전 유효성 검증으로 문제를 예방할 수 있다.

## Terraform의 단점

PDF p.8 기준:

- 이미 배포된 대규모 인프라를 한 번에 Terraform 코드로 마이그레이션하기 어렵다.
- 모듈형 Terraform 코드를 작성하지 않으면 배포마다 전체 인프라를 지우고 새로 배포하는 방식이 되어 배포 속도가 저하될 수 있다.
- Terraform의 유효성 검사는 100% 신뢰할 수 없다.
  - 예: `plan` 성공 후 `apply` 실패 가능
- HCL 문법 학습이 필요하다.
- 인프라 배포 전략이 제한적일 수 있다.

## Provider

Terraform은 Provider를 통해 특정 플랫폼의 API와 연결된다.

PDF p.10 기준 AWS Provider 설정 예시는 다음 구조를 가진다.

```hcl
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region  = "ap-northeast-2"
  profile = "terraform_user"
}
```

| 항목 | 의미 |
|---|---|
| `required_providers` | 사용할 Provider와 버전 조건 정의 |
| `source` | Provider Plugin 다운로드 경로 |
| `version` | Provider Plugin 버전 조건 |
| `provider "aws"` | AWS Provider 설정 |
| `region` | 리소스를 생성할 AWS Region |
| `profile` | AWS CLI 인증정보 Profile |

## Provider version constraint

수업 raw 노트에는 Terraform Registry의 AWS Provider 예시를 복사하면서 다음 코드가 나온다.

```hcl
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }
}
```

여기서 `~> 6.0`은 “6.0 이상이면 아무 최신 버전이나 사용”이라는 뜻이 아니다. 실무적으로는 다음처럼 이해하면 된다.

```text
~> 6.0
= 6.x 계열 안에서 허용 가능한 최신 버전을 사용
= 보통 >= 6.0.0, < 7.0.0 범위로 이해
```

비교:

| 표현 | 의미 감각 |
|---|---|
| `~> 5.0` | 5.x 계열 허용 |
| `~> 6.0` | 6.x 계열 허용 |
| `>= 6.0` | 6.0 이상이면 major version 상승도 허용될 수 있어 더 넓음 |

PDF 예시는 `~> 5.0`이고, 수업 중 Registry 최신 예시는 `~> 6.0`이다. 따라서 노트 작성 시 둘을 섞지 말고 다음처럼 구분한다.

```text
PDF 재현: PDF의 provider version 사용
현재 실습: Registry에서 확인한 현재 provider version 사용
프로젝트: 공식 문서와 호환성 확인 후 version pinning
```

## AWS Provider 실습 권한 예시

raw 노트에는 다음 IAM Policy JSON이 있다.

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": "*",
            "Resource": "*"
        }
    ]
}
```

해석:

| 필드 | 의미 |
|---|---|
| `Version` | IAM Policy 문법 버전. 날짜 형식이지만 정책 작성일이 아니라 정책 언어 버전 |
| `Statement` | 권한 규칙 목록 |
| `Effect: Allow` | 허용 규칙 |
| `Action: "*"` | 모든 AWS API 작업 허용 |
| `Resource: "*"` | 모든 리소스 대상 허용 |

결론:

```text
모든 AWS 리소스에 대해 모든 작업을 허용하는 매우 강한 권한이다.
```

실습에서는 편의상 이런 넓은 권한을 줄 수 있지만, 실제 프로젝트나 장기 운영 계정에서는 최소 권한 원칙에 맞춰 제한해야 한다.

## HCL 기본

PDF p.10 기준:

```hcl
식별자 = 값
```

- `.tf`: Terraform 소스 파일 확장자
- `main.tf`: Terraform 설정 및 Provider 지정 파일로 사용
- `{ }`: Attribute Block 정의
- `terraform fmt`: HCL 문법 정리 명령어

## Obsidian 코드블록 표기

Terraform 코드는 HCL 기반이므로 Obsidian 코드블록에서는 우선 `hcl`을 쓰는 것이 안전하다.

````markdown
```hcl
resource "aws_instance" "example" {
  ami           = "ami-xxxxxxxx"
  instance_type = "t2.micro"
}
```
````

환경에 따라 `terraform` 코드블록이 동작할 수도 있지만, 색상이 제대로 안 먹으면 `hcl`로 통일한다.

## 주의

PDF에 포함된 Terraform 다운로드 URL은 특정 시점의 Terraform 1.4.6 Windows AMD64 ZIP이다. 새 환경에서는 HashiCorp 공식 설치 문서 기준으로 최신 설치 방법을 확인해야 한다.

## 관련 노트

- [[IaC 개념]]
- [[IaC 도구 분류]]
- [[Terraform Workflow]]
- [[Terraform Resource와 Data Source]]