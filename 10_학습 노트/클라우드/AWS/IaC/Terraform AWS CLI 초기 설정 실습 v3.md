---
title: Terraform AWS CLI 초기 설정 실습
created: 2026-07-06
status: active
type: lab-note
source:
  - raw 노트.md
  - Terraform 개요.md
  - Terraform Workflow.md
  - IaC 도구 분류.md
official_refs:
  - https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html
  - https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-files.html
  - https://developer.hashicorp.com/terraform/install
tags:
  - 과목/AWS
  - 주제/IaC
  - 주제/Terraform
  - 주제/AWS-CLI
  - 상태/active
  - 실습/Terraform
---

# Terraform AWS CLI 초기 설정 실습

## 목적

이 노트는 Windows 환경에서 **Terraform으로 AWS 리소스를 만들기 전 최소 준비 작업**을 정리한다.

목표는 다음이다.

```text
AWS IAM 사용자/Access Key 준비
→ AWS CLI 설치
→ AWS CLI profile 설정
→ AWS 인증 검증
→ Terraform 설치
→ Terraform 작업 폴더 구성
→ AWS Provider 코드 준비
→ terraform init까지 확인
```

## 이 노트의 범위

포함:

- IAM 사용자와 Access Key 준비 흐름
- Access Key CSV 보관/삭제 기준
- AWS CLI 설치/업데이트
- `aws configure --profile Terra-user`
- `aws configure list` / `sts get-caller-identity` 검증
- 공용/남의 컴퓨터에서 `.aws` 정리
- `D:\terraform`, `D:\terraform\workspace` 구성
- Terraform 설치와 Path 등록
- VS Code Terraform Extension
- Terraform Registry AWS Provider 코드 가져오기
- 첫 `main.tf` 작성
- `terraform init` 확인

제외:

- EC2/VPC 실제 생성
- Terraform Resource/Data Source 실습
- Backend/Remote State 구성
- Module 구조
- AWS IAM 최소권한 정책 설계

위 제외 항목은 별도 노트로 분리한다.

---

## 0. 먼저 알아야 할 용어

| 용어 | 의미 |
|---|---|
| IAM User | AWS에서 사람/프로그램에게 권한을 주기 위한 사용자 |
| Access Key | CLI/API에서 AWS에 인증할 때 쓰는 키 쌍 |
| Access Key ID | 공개 식별자에 가까운 값. 단독으로는 부족하지만 노출하지 않는 것이 원칙 |
| Secret Access Key | 비밀번호에 해당하는 민감정보. 노출되면 즉시 폐기해야 함 |
| Profile | 여러 AWS 계정/사용자 인증정보를 이름으로 구분하는 AWS CLI 설정 단위 |
| Region | AWS 리소스를 만들 물리적/논리적 지역. 서울은 `ap-northeast-2` |
| Provider | Terraform이 특정 플랫폼 API를 호출하기 위해 사용하는 플러그인 |
| `main.tf` | Terraform 설정을 작성하는 기본 파일 이름으로 자주 사용 |

---

## 1. IAM 사용자와 Access Key 준비

수업 흐름:

```text
AWS Console
→ IAM 검색
→ IAM 사용자
→ 실습용 사용자 생성
→ 필요한 권한 부여
→ Access Key 생성
→ CSV 다운로드
```

### 권한 관련 주의

수업에서 다음처럼 매우 강한 권한 정책을 사용할 수 있다.

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

의미:

```text
모든 AWS 리소스에 대해 모든 작업을 허용한다.
```

이 권한은 실습 편의용으로는 쓸 수 있지만, 실제 프로젝트나 장기 운영 계정에서는 위험하다.  
실제 환경에서는 최소 권한 원칙에 맞춰 필요한 권한만 부여해야 한다.

---

## 2. Access Key CSV 보관 기준

raw 노트 질문:

```text
액세스 키 만들기. .csv는 격리 된 곳에 두기
{질문: C드라이브가 나을까 D드라이브가 나을까?}
```

정리:

```text
C드라이브냐 D드라이브냐가 핵심이 아니다.
핵심은 “얼마나 짧게 보관하고, 얼마나 빨리 삭제하느냐”다.
```

권장 흐름:

```text
1. Access Key CSV 다운로드
2. 곧바로 aws configure에 입력
3. 입력 완료 후 CSV 삭제
4. 휴지통 비우기
5. 장기 보관이 필요하면 암호화 저장소나 password manager에 보관
```

하지 말 것:

```text
- Obsidian Vault에 저장
- GitHub에 커밋
- 메신저에 붙여넣기
- 스크린샷으로 저장
- 평문 txt 파일로 장기 보관
```

### 공용/남의 컴퓨터에서 더 중요한 것

공용 PC나 남의 노트북에서 실습했다면 CSV 삭제만으로 끝나지 않는다.  
AWS CLI 설정 파일에도 credential이 남을 수 있다.

확인 위치:

```cmd
dir "%USERPROFILE%\.aws"
```

대표 파일:

```text
%USERPROFILE%\.aws\credentials
%USERPROFILE%\.aws\config
```

---

## 3. AWS CLI 설치 또는 업데이트

raw 노트 명령:

```cmd
msiexec.exe /i https://awscli.amazonaws.com/AWSCLIV2.msi
```

절차:

```cmd
aws --version
```

이미 설치되어 있으면 버전이 출력된다.

설치/업데이트:

```cmd
msiexec.exe /i https://awscli.amazonaws.com/AWSCLIV2.msi
```

설치 후 새 터미널을 열고 다시 확인한다.

```cmd
aws --version
```

정상 예시:

```text
aws-cli/2.x.x Python/3.x Windows/...
```

문제 상황:

| 증상 | 원인 후보 | 조치 |
|---|---|---|
| `'aws' is not recognized` | PATH 반영 안 됨 | 터미널 재시작, Windows 재로그인, 설치 재확인 |
| 설치 마법사 실행 안 됨 | 권한/정책 문제 | 관리자 권한 CMD/PowerShell에서 실행 |
| v1이 잡힘 | 기존 AWS CLI v1과 충돌 | `where aws`로 실행 경로 확인 |

확인:

```cmd
where aws
aws --version
```

---

## 4. AWS CLI Profile 설정

raw 노트 명령:

```cmd
aws configure --profile Terra-user
```

실행:

```cmd
aws configure --profile Terra-user
```

입력값:

```text
AWS Access Key ID [None]: <Access Key ID 입력>
AWS Secret Access Key [None]: <Secret Access Key 입력>
Default region name [None]: ap-northeast-2
Default output format [None]: json
```

권장 Profile 이름:

```text
Terra-user
```

주의:

- Profile 이름은 대소문자와 하이픈까지 그대로 맞춘다.
- Terraform Provider에서 `profile = "Terra-user"`라고 쓰면 AWS CLI profile 이름도 정확히 같아야 한다.
- PDF 예시의 `terraform_user`와 수업 raw 노트의 `Terra-user`를 섞지 않는다.

---

## 5. AWS CLI 설정 파일 위치

AWS CLI는 보통 사용자 홈 아래 `.aws` 폴더에 설정을 저장한다.

Windows 기준:

```text
%USERPROFILE%\.aws\credentials
%USERPROFILE%\.aws\config
```

예상 구조:

```text
C:\Users\<사용자명>\.aws\credentials
C:\Users\<사용자명>\.aws\config
```

`credentials` 예시:

```ini
[Terra-user]
aws_access_key_id = AKIA...
aws_secret_access_key = ...
```

`config` 예시:

```ini
[profile Terra-user]
region = ap-northeast-2
output = json
```

주의:

```text
credentials 파일은 민감정보 파일이다.
Obsidian, GitHub, 캡처, 공유 폴더에 넣지 않는다.
```

---

## 6. 인증 설정 검증

### 6-1. Profile 목록/설정 확인

```cmd
aws configure list
```

명시적으로 profile 확인:

```cmd
aws configure list --profile Terra-user
```

### 6-2. 현재 AWS 계정/사용자 확인

가장 확실한 검증 명령:

```cmd
aws sts get-caller-identity --profile Terra-user
```

정상 예시:

```json
{
    "UserId": "AIDA...",
    "Account": "123456789012",
    "Arn": "arn:aws:iam::123456789012:user/Terra-user"
}
```

이 명령이 성공하면 최소한 다음은 확인된 것이다.

```text
AWS CLI 설치됨
Profile 이름 정상
Access Key / Secret Key 정상
AWS API 인증 성공
```

---

## 7. “profile 지정 안 했는데 왜 key가 not set이 아니지?”

raw 노트 질문:

```text
{질문: 프로필 지정 안했으면 키도 not set 나와야하는거 아닌가?}
```

정답:

```text
아니다.
profile을 지정하지 않으면 AWS CLI는 default profile 또는 다른 credential source를 찾는다.
```

가능한 경우:

| 상황 | 결과 |
|---|---|
| `default` profile에 키가 있음 | `--profile`을 안 줘도 key가 잡힘 |
| 환경변수에 AWS 키가 있음 | profile과 무관하게 key가 잡힐 수 있음 |
| EC2 Role, SSO 등 다른 인증 경로가 있음 | 다른 credential source가 사용될 수 있음 |
| 아무 credential도 없음 | 그때 `not set` 또는 인증 실패 |

확인 명령:

```cmd
aws configure list
aws configure list --profile Terra-user
aws sts get-caller-identity
aws sts get-caller-identity --profile Terra-user
```

실습에서는 헷갈림 방지를 위해 항상 `--profile Terra-user`를 붙여 확인한다.

---

## 8. 공용/남의 컴퓨터에서 정리

raw 노트:

```text
만약 남의 컴에서 cli 과정 했으면 사용자 폴더의 .aws 폴더 날리기.
```

방향은 맞다. 다만 남의 컴퓨터에 다른 AWS 설정이 있을 수 있으므로, 무조건 전체 삭제보다 먼저 확인한다.

확인:

```cmd
dir "%USERPROFILE%\.aws"
notepad "%USERPROFILE%\.aws\credentials"
notepad "%USERPROFILE%\.aws\config"
```

내 실습 profile만 제거할 수 있으면 해당 section만 삭제한다.

예:

```ini
[Terra-user]
aws_access_key_id = ...
aws_secret_access_key = ...
```

위 블록 삭제.

정말 내 실습 전용 임시 환경이고 `.aws` 전체를 지워도 되는 경우:

```cmd
rmdir /s /q "%USERPROFILE%\.aws"
```

더 안전한 사고 대응:

```text
1. AWS Console 접속
2. IAM 사용자로 이동
3. 해당 Access Key 비활성화 또는 삭제
4. 새 Access Key 발급
5. 새 키로 다시 aws configure
```

---

## 9. Terraform 폴더 구성

raw 노트:

```text
D:\terraform 랑 D:\terraform\workspace 만들기
```

권장 구조:

```text
D:\terraform
├─ terraform.exe
└─ workspace
   └─ 01_basic
      └─ main.tf
```

폴더 생성:

```cmd
mkdir D:\terraform
mkdir D:\terraform\workspace
mkdir D:\terraform\workspace\01_basic
```

---

## 10. Terraform 설치

절차:

```text
1. https://developer.hashicorp.com/terraform/install 접속
2. Windows AMD64용 Terraform 다운로드
3. zip 압축 해제
4. terraform.exe를 D:\terraform에 배치
5. Path에 D:\terraform 추가
6. 새 터미널에서 terraform version 확인
```

직접 실행 확인:

```cmd
D:\terraform\terraform.exe version
```

PATH 등록 후 확인:

```cmd
terraform version
where terraform
```

정상이라면:

```text
Terraform v1.x.x
on windows_amd64
```

### PATH 등록

raw 노트 흐름:

```text
윈 + R
→ sysdm.cpl
→ 고급
→ 환경 변수
→ 시스템 변수 Path 더블클릭
→ D:\terraform 추가
```

등록 후에는 **새 CMD/PowerShell/VS Code 터미널**을 열어야 반영된다.

문제 예시:

```cmd
D:\terraform\workspace\01_basic>terraform init
'terraform' is not recognized as an internal or external command,
operable program or batch file.
```

해석:

```text
현재 터미널의 PATH에 D:\terraform이 반영되지 않았거나,
terraform.exe가 D:\terraform에 없거나,
터미널을 재시작하지 않았다.
```

응급 실행:

```cmd
D:\terraform\terraform.exe init
```

근본 확인:

```cmd
dir D:\terraform
where terraform
echo %PATH%
```

---

## 11. VS Code 준비

raw 노트:

```text
VSC에서 실행. 테라폼 플러그인 깔기를 강추.
```

권장:

```text
VS Code Extension에서 Terraform 검색
→ HashiCorp Terraform 계열 Extension 설치
```

목적:

- `.tf` 파일 문법 강조
- 자동 완성
- Terraform fmt 연동
- 오류 표시
- HCL 코드 읽기 편의성

Obsidian 코드블록은 Terraform 코드에 `hcl`을 우선 사용한다.

````markdown
```hcl
resource "aws_instance" "example" {
  ami           = "ami-xxxxxxxx"
  instance_type = "t2.micro"
}
```
````

---

## 12. Terraform Registry에서 AWS Provider 코드 가져오기

raw 노트:

```text
https://registry.terraform.io/providers/hashicorp/aws/latest
→ 오른쪽 밑의 How to use this provider 의 코드 복붙
```

기본 예시:

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
  region  = "ap-northeast-2"
  profile = "Terra-user"
}
```

주의:

```text
PDF 예시와 수업 당시 Registry 예시의 provider version이 다를 수 있다.
PDF 재현이면 PDF 버전 사용.
현재 실습이면 Registry 현재 예시 사용.
프로젝트면 공식 문서 확인 후 version pinning.
```

`~> 6.0` 의미는 [[Terraform 개요]] 참고.

---

## 13. 첫 실습 디렉터리에서 초기화

작업 폴더 이동:

```cmd
cd /d D:\terraform\workspace\01_basic
```

`main.tf` 생성:

```cmd
notepad main.tf
```

내용:

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
  region  = "ap-northeast-2"
  profile = "Terra-user"
}
```

초기화:

```cmd
terraform init
```

PATH가 아직 안 잡혀 있으면:

```cmd
D:\terraform\terraform.exe init
```

정상 결과의 핵심:

```text
Terraform has been successfully initialized!
```

생성될 수 있는 항목:

```text
.terraform/
.terraform.lock.hcl
```

의미:

- `.terraform/`: provider/plugin/module 등 초기화 결과
- `.terraform.lock.hcl`: 선택된 provider 버전과 checksum 기록

---

---

## 14. VPC/Subnet/EC2 최소 골격 실습 코드

이 절은 `terraform init` 이후, 실제로 **Terraform 리소스 참조 관계로 VPC → Subnet → EC2가 생성되는지 확인하는 최소 실습 코드**다.

목표는 “인터넷 접속 가능한 완성형 웹 서버”가 아니다.

```text
목표:
Terraform 코드로 VPC, Subnet, EC2를 만들고
리소스 간 참조 관계가 어떻게 연결되는지 확인한다.

비목표:
Public Subnet 완성
Internet Gateway 구성
Route Table 구성
Security Group 세부 제어
SSH 접속 검증
Multi-AZ 고가용성 구성
```

즉, 이 코드는 **EC2가 올라가는 최소 골격**이다.

### `main.tf` 전체 코드

> [!note]- `main.tf` 전체 코드
> ```hcl
> terraform {
>   required_providers {
>     aws = {
>       source  = "hashicorp/aws"
>       version = "~> 6.0"
>     }
>   }
> }
> 
> provider "aws" {
>   region  = "ap-northeast-2"
>   profile = "Terra-user"
> }
> 
> resource "aws_vpc" "terra_vpc" {
>   cidr_block = "10.0.0.0/16"
> 
>   tags = {
>     Name = "terra_vpc"
>   }
> }
> 
> resource "aws_subnet" "terra_subnet" {
>   vpc_id     = aws_vpc.terra_vpc.id
>   cidr_block = "10.0.1.0/24"
> 
>   tags = {
>     Name = "terra_subnet"
>   }
> }
> 
> resource "aws_instance" "terra_web" {
>   ami           = "ami-0b1cb107a74bad43e"
>   instance_type = "t3.micro"
>   subnet_id     = aws_subnet.terra_subnet.id
>   key_name      = "asd-open"
> 
>   tags = {
>     Name = "terra_web"
>   }
> }
> ```

원래 수업 중 작성한 코드에서는 provider block에 `region`을 명시하지 않았지만, 이 노트에서는 가독성과 재현성을 위해 `region = "ap-northeast-2"`를 추가한 형태로 정리한다.

AWS CLI의 `Terra-user` profile에 이미 기본 region이 들어 있다면 region 생략도 동작할 수 있다. 다만 Terraform 코드만 보고도 “서울 리전에 배포하는 실습”임을 알 수 있도록 provider block에 region을 명시하는 편이 낫다.

---

## 15. 코드 블록별 해설

### 15-1. Terraform Provider 요구사항

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

이 블록은 Terraform 자체 설정 중 **어떤 Provider를 사용할지**를 선언한다.

| 항목 | 의미 |
|---|---|
| `terraform` block | Terraform 실행에 필요한 설정을 담는 블록 |
| `required_providers` | 이 코드에서 필요한 Provider 목록 |
| `aws` | 로컬 이름. 아래 resource에서 `aws_vpc`, `aws_instance`처럼 쓰이는 Provider |
| `source = "hashicorp/aws"` | Terraform Registry에서 가져올 AWS Provider 위치 |
| `version = "~> 6.0"` | AWS Provider 6.x 계열 사용 |

`~> 6.0`은 “6.0 이상 아무 버전”이 아니라, 보통 다음처럼 이해한다.

```text
>= 6.0.0, < 7.0.0
```

즉, AWS Provider 6.x 계열 안에서 허용 가능한 버전을 사용하겠다는 뜻이다.

실습 포인트:

```text
terraform init을 실행하면 이 required_providers 정보를 보고 AWS Provider를 다운로드한다.
```

---

### 15-2. AWS Provider 설정

```hcl
provider "aws" {
  region  = "ap-northeast-2"
  profile = "Terra-user"
}
```

이 블록은 AWS Provider가 **어느 AWS 계정/Region에 API 요청을 보낼지** 정한다.

| 항목 | 의미 |
|---|---|
| `provider "aws"` | AWS Provider 설정 시작 |
| `region = "ap-northeast-2"` | 서울 리전에 리소스 생성 |
| `profile = "Terra-user"` | AWS CLI에 저장된 `Terra-user` profile 사용 |

여기서 `profile = "Terra-user"`는 이전 단계의 명령과 연결된다.

```cmd
aws configure --profile Terra-user
```

검증 명령:

```cmd
aws sts get-caller-identity --profile Terra-user
```

이 명령이 성공해야 Terraform도 같은 profile을 이용해 AWS API를 호출할 수 있다.

#### region을 코드에 적는 이유

AWS CLI config에 기본 region을 이미 설정했다면 다음 코드도 동작할 수 있다.

```hcl
provider "aws" {
  profile = "Terra-user"
}
```

하지만 실습 노트와 재현성 기준에서는 region을 명시하는 편이 좋다.

```text
코드만 봐도 배포 위치가 보임
다른 PC에서 실행해도 의도가 유지됨
나중에 Multi-AZ 구성으로 확장할 때 기준 Region이 명확함
```

주의할 점:

```text
Region = 서울 전체 리전, ap-northeast-2
AZ     = 서울 리전 안의 가용 영역, 예: ap-northeast-2a, ap-northeast-2c
```

고가용성을 높인다는 것은 보통 “서울 리전 안에서 여러 AZ를 사용한다”는 뜻이다.

---

### 15-3. VPC 생성

```hcl
resource "aws_vpc" "terra_vpc" {
  cidr_block = "10.0.0.0/16"

  tags = {
    Name = "terra_vpc"
  }
}
```

이 블록은 AWS에 새 VPC를 만든다.

| 항목 | 의미 |
|---|---|
| `resource` | Terraform이 생성/관리할 인프라 리소스 선언 |
| `aws_vpc` | AWS Provider의 VPC 리소스 타입 |
| `terra_vpc` | Terraform 코드 안에서 이 VPC를 부를 이름 |
| `cidr_block = "10.0.0.0/16"` | VPC 전체 사설 IP 대역 |
| `tags.Name` | AWS Console에서 보이는 이름 태그 |

Terraform 리소스 주소는 다음처럼 된다.

```text
aws_vpc.terra_vpc
```

나중에 다른 리소스가 이 VPC의 ID를 참조할 때는 다음처럼 쓴다.

```hcl
aws_vpc.terra_vpc.id
```

#### CIDR 의미

```text
10.0.0.0/16
```

은 대략 다음 범위의 사설 IP 대역이다.

```text
10.0.0.0 ~ 10.0.255.255
```

이 VPC 안에 여러 subnet을 쪼개 넣을 수 있다.

예:

```text
10.0.1.0/24
10.0.2.0/24
10.0.10.0/24
10.0.20.0/24
```

---

### 15-4. Subnet 생성

```hcl
resource "aws_subnet" "terra_subnet" {
  vpc_id     = aws_vpc.terra_vpc.id
  cidr_block = "10.0.1.0/24"

  tags = {
    Name = "terra_subnet"
  }
}
```

이 블록은 위에서 만든 VPC 안에 Subnet을 만든다.

| 항목 | 의미 |
|---|---|
| `aws_subnet` | AWS Provider의 Subnet 리소스 타입 |
| `terra_subnet` | Terraform 코드 안에서 이 Subnet을 부를 이름 |
| `vpc_id` | 이 Subnet이 들어갈 VPC ID |
| `aws_vpc.terra_vpc.id` | 위에서 만든 VPC의 ID 참조 |
| `cidr_block = "10.0.1.0/24"` | Subnet IP 대역 |
| `tags.Name` | AWS Console에서 보이는 이름 태그 |

핵심은 이 줄이다.

```hcl
vpc_id = aws_vpc.terra_vpc.id
```

이 줄 때문에 Terraform은 다음 관계를 알 수 있다.

```text
Subnet은 VPC가 있어야 만들 수 있다.
따라서 VPC를 먼저 만들고 Subnet을 만든다.
```

#### 이 Subnet은 Public Subnet인가?

아직 아니다.

현재 코드에는 다음이 없다.

```text
Internet Gateway
Route Table
0.0.0.0/0 → Internet Gateway route
Route Table Association
map_public_ip_on_launch = true
```

따라서 이 subnet은 “VPC 안에 존재하는 subnet”일 뿐, 인터넷 통신까지 완성된 public subnet은 아니다.

이 실습의 목적이 EC2 최소 생성 골격이라면 문제 없다.  
하지만 SSH 접속이나 웹 접속까지 하려면 public subnet 구성을 추가해야 한다.

---

### 15-5. EC2 Instance 생성

```hcl
resource "aws_instance" "terra_web" {
  ami           = "ami-0b1cb107a74bad43e"
  instance_type = "t3.micro"
  subnet_id     = aws_subnet.terra_subnet.id
  key_name      = "asd-open"

  tags = {
    Name = "terra_web"
  }
}
```

이 블록은 EC2 Instance를 만든다.

| 항목 | 의미 |
|---|---|
| `aws_instance` | AWS Provider의 EC2 Instance 리소스 타입 |
| `terra_web` | Terraform 코드 안에서 이 EC2를 부를 이름 |
| `ami` | EC2에 사용할 Amazon Machine Image ID |
| `instance_type` | EC2 성능/요금 타입 |
| `subnet_id` | EC2를 배치할 Subnet ID |
| `key_name` | EC2 SSH 접속에 사용할 Key Pair 이름 |
| `tags.Name` | AWS Console에서 보이는 이름 태그 |

핵심 참조는 이 줄이다.

```hcl
subnet_id = aws_subnet.terra_subnet.id
```

이 줄 때문에 Terraform은 다음 관계를 알 수 있다.

```text
EC2는 Subnet이 있어야 만들 수 있다.
Subnet은 VPC가 있어야 만들 수 있다.
따라서 VPC → Subnet → EC2 순서가 된다.
```

#### AMI ID 주의

```hcl
ami = "ami-0b1cb107a74bad43e"
```

AMI ID는 Region마다 다르다.  
즉, 서울 리전에서 존재하는 AMI라도 버지니아 리전에서는 같은 ID가 존재하지 않을 수 있다.

현재 provider region을 `ap-northeast-2`로 명시했으므로, 이 AMI ID도 서울 리전 기준으로 검증해야 한다.

확인 명령:

```cmd
aws ec2 describe-images --image-ids ami-0b1cb107a74bad43e --region ap-northeast-2 --profile Terra-user
```

#### Key Pair 주의

```hcl
key_name = "asd-open"
```

이 값은 AWS EC2 Key Pair 이름이다.  
로컬 `.pem` 파일 이름이 아니라, AWS에 등록된 Key Pair의 이름과 일치해야 한다.

확인 명령:

```cmd
aws ec2 describe-key-pairs --key-names asd-open --region ap-northeast-2 --profile Terra-user
```

#### Security Group 주의

현재 코드에는 `vpc_security_group_ids`가 없다.

즉, 별도 Security Group을 명시하지 않았다.  
이 경우 기본 Security Group이 붙을 수 있지만, 실습/보고서 관점에서는 의도가 불명확하다.

현재 목표가 “EC2 생성 최소 골격”이면 일단 괜찮다.  
하지만 SSH 접속이나 웹 접속을 목표로 하는 순간 별도 Security Group을 만드는 것이 좋다.

---

## 16. Terraform이 이해하는 의존성 흐름

이 코드의 핵심은 리소스 생성 순서를 사람이 직접 명령하지 않는다는 점이다.

Terraform은 참조 관계를 보고 의존성을 추론한다.

```text
aws_vpc.terra_vpc
↓
aws_subnet.terra_subnet
↓
aws_instance.terra_web
```

구체적으로는 다음 참조 때문이다.

```hcl
vpc_id = aws_vpc.terra_vpc.id
```

```hcl
subnet_id = aws_subnet.terra_subnet.id
```

그래서 Terraform 입장에서는 다음처럼 해석한다.

```text
1. aws_vpc.terra_vpc를 먼저 만들어야 한다.
2. 그래야 aws_subnet.terra_subnet의 vpc_id를 채울 수 있다.
3. aws_subnet.terra_subnet을 만들어야 한다.
4. 그래야 aws_instance.terra_web의 subnet_id를 채울 수 있다.
5. 마지막으로 EC2를 만든다.
```

이것이 Terraform의 “선언적” 성격과 연결된다.

사용자는 “VPC 만들고, 그 다음 Subnet 만들고, 그 다음 EC2 만들어라”라고 절차를 직접 명령하지 않는다.  
대신 “이런 최종 상태가 되게 해라”라고 작성한다.

---

## 17. 이 코드로 가능한 것과 불가능한 것

### 가능한 것

```text
VPC 생성
Subnet 생성
EC2 생성 시도
Terraform resource 참조 실습
Terraform plan/apply 흐름 확인
AWS Console에서 리소스 생성 확인
```

### 아직 어려운 것

```text
외부 인터넷에서 EC2로 SSH 접속
웹 브라우저로 EC2 접속
EC2에서 인터넷으로 패키지 설치
Multi-AZ 고가용성
ALB 연결
Auto Scaling Group 구성
보안적으로 명확한 Security Group 관리
```

이유는 다음 리소스가 아직 없기 때문이다.

```text
Internet Gateway
Public Route Table
Route Table Association
Security Group ingress rule
Public IP 자동 할당 설정
```

따라서 이 코드는 다음 단계로 확장될 수 있다.

```text
1단계: VPC/Subnet/EC2 최소 생성
2단계: Internet Gateway + Route Table로 Public Subnet 구성
3단계: Security Group으로 SSH 또는 HTTP 허용
4단계: EC2 접속 검증
5단계: Multi-AZ Subnet 구성
6단계: ALB/ASG 구성
```

---

## 18. 실행 순서

작업 디렉터리:

```cmd
cd /d D:\terraform\workspace\01_basic
```

코드 포맷:

```cmd
terraform fmt
```

초기화:

```cmd
terraform init
```

문법/기본 검증:

```cmd
terraform validate
```

실행 계획 확인:

```cmd
terraform plan
```

실제 생성:

```cmd
terraform apply
```

실습 후 삭제:

```cmd
terraform destroy
```

주의:

```text
terraform apply 후에는 AWS에 실제 리소스가 생성된다.
비용 발생 가능성이 있으므로 실습 후 destroy까지 확인한다.
```

---

## 19. `plan`에서 확인할 것

`terraform plan`을 실행했을 때 최소한 다음 리소스 생성이 보여야 한다.

```text
aws_vpc.terra_vpc
aws_subnet.terra_subnet
aws_instance.terra_web
```

예상 요약은 대략 다음과 비슷해야 한다.

```text
Plan: 3 to add, 0 to change, 0 to destroy.
```

다만 Provider가 내부적으로 읽는 정보나 설정 상태에 따라 출력 내용은 달라질 수 있다.

### plan에서 실패할 수 있는 지점

| 실패 지점 | 원인 후보 |
|---|---|
| Provider 인증 실패 | `Terra-user` profile 오류, Access Key 오류 |
| Region 오류 | provider region 누락, AWS config region 누락 |
| AMI 오류 | AMI ID가 해당 region에 없음 |
| Key Pair 오류 | `asd-open` Key Pair가 해당 region에 없음 |
| 권한 오류 | IAM User 권한 부족 |
| VPC/Subnet CIDR 오류 | CIDR 범위 충돌 또는 형식 오류 |

---

## 20. 실습 후 AWS Console에서 볼 것

`apply` 후 AWS Console에서 확인할 대상:

```text
VPC
Subnet
EC2 Instance
```

확인 기준:

| 콘솔 메뉴 | 확인할 값 |
|---|---|
| VPC | `terra_vpc`, CIDR `10.0.0.0/16` |
| Subnet | `terra_subnet`, CIDR `10.0.1.0/24`, 연결 VPC |
| EC2 | `terra_web`, instance type `t3.micro`, subnet 연결 |
| Key Pair | `asd-open` 연결 여부 |
| Security Group | 어떤 SG가 붙었는지 확인 |

중요:

```text
EC2가 생성되었다고 해서 접속 가능하다는 뜻은 아니다.
이 코드는 접속성보다 리소스 생성과 참조 관계 확인이 목적이다.
```

---

## 21. 이 코드의 다음 개선 후보

현재 코드가 성공하면 다음 개선을 순서대로 붙이는 것이 좋다.

### 21-1. Availability Zone 명시

현재 Subnet은 AZ를 명시하지 않았다.

```hcl
resource "aws_subnet" "terra_subnet" {
  vpc_id            = aws_vpc.terra_vpc.id
  cidr_block        = "10.0.1.0/24"
  availability_zone = "ap-northeast-2a"
}
```

AZ를 명시하면 “서울 리전의 특정 AZ에 subnet을 만든다”는 의도가 더 분명해진다.

### 21-2. Public Subnet 구성

추가 리소스 후보:

```text
aws_internet_gateway
aws_route_table
aws_route_table_association
```

Subnet 옵션:

```hcl
map_public_ip_on_launch = true
```

EC2 옵션:

```hcl
associate_public_ip_address = true
```

### 21-3. Security Group 명시

추가 리소스 후보:

```hcl
resource "aws_security_group" "terra_web_sg" {
  # ingress / egress rule
}
```

EC2 연결:

```hcl
vpc_security_group_ids = [aws_security_group.terra_web_sg.id]
```

### 21-4. AMI Data Source 사용

AMI ID를 직접 박아두면 Region이나 시점에 따라 깨질 수 있다.  
나중에는 `data "aws_ami"` 또는 SSM Parameter Store 기반으로 AMI를 가져오면 더 유연하다.

### 21-5. Output 추가

생성된 리소스 ID를 CLI에서 바로 확인하려면 output을 붙일 수 있다.

```hcl
output "vpc_id" {
  value = aws_vpc.terra_vpc.id
}

output "subnet_id" {
  value = aws_subnet.terra_subnet.id
}

output "instance_id" {
  value = aws_instance.terra_web.id
}
```

---

## 22. 이 실습의 판정

이 코드는 다음을 배우기에 적절하다.

```text
Terraform resource 선언
Terraform resource address
Resource 간 attribute 참조
VPC/Subnet/EC2의 기본 포함 관계
plan/apply/destroy 흐름
provider profile 사용
```

하지만 다음을 배우기에는 아직 부족하다.

```text
Public subnet
EC2 SSH 접속
Security Group 설계
Route Table
Internet Gateway
고가용성
```

따라서 이 코드는 “완성형 AWS 아키텍처”가 아니라 **Terraform으로 AWS 리소스를 처음 생성해 보는 최소 골격 실습**으로 분류한다.


---

## 23. 2차 실습: Public/Private Subnet 분리와 EC2 배치

이번 실습 요구사항은 다음이다.

```text
VPC 1개
Public Subnet 1개
Private Subnet 1개
Public Subnet에 EC2 Instance 1개
Private Subnet에 EC2 Instance 1개
```

이 단계의 핵심은 **Subnet을 2개로 분리하고, 각 EC2가 의도한 Subnet에 들어가도록 `subnet_id` 참조를 연결하는 것**이다.

### 23-1. 작성한 `main.tf` 초안

> [!note]- `main.tf` 초안 - Public/Private Subnet + EC2 2대
> ```hcl
> terraform {
>   required_providers {
>     aws = {
>       source  = "hashicorp/aws"
>       version = "~> 6.0"
>     }
>   }
> }
> 
> provider "aws" {
>   profile = "Terra-user"
> }
> 
> resource "aws_vpc" "terra_vpc" {
>   cidr_block = "10.0.0.0/16"
> 
>   tags = {
>     Name = "terra_vpc"
>   }
> }
> 
> resource "aws_subnet" "terra_open_subnet" {
>   vpc_id     = aws_vpc.terra_vpc.id
>   cidr_block = "10.0.1.0/24"
> 
>   tags = {
>     Name = "terra_open_subnet"
>   }
> }
> 
> resource "aws_subnet" "terra_close_subnet" {
>   vpc_id     = aws_vpc.terra_vpc.id
>   cidr_block = "10.0.2.0/24"
> 
>   tags = {
>     Name = "terra_close_subnet"
>   }
> }
> 
> # resource "aws_security_group" "open_sg" {
> #   name        = "open_sg"
> #   vpc_id      = aws_vpc.terra_vpc.id
> 
> #   tags = {
> #     Name = "open_sg"
> #   }
> # }
> 
> # resource "aws_security_group" "close_sg" {
> #   name        = "close_sg"
> #   vpc_id      = aws_vpc.terra_vpc.id
> 
> #   tags = {
> #     Name = "close_sg"
> #   }
> # }
> 
> resource "aws_instance" "terra_web" {
>   ami           = "ami-0b1cb107a74bad43e"
>   instance_type = "t3.micro"
>   subnet_id     = aws_subnet.terra_close_subnet.id
>   key_name      = "asd-close"
>   # security_groups = [aws_security_group.close_sg.name]
> 
>   tags = {
>     Name = "terra_web"
>   }
> }
> 
> resource "aws_instance" "terra_bastion" {
>   ami           = "ami-0b1cb107a74bad43e"
>   instance_type = "t3.micro"
>   subnet_id     = aws_subnet.terra_open_subnet.id
>   key_name      = "asd-open"
>   # security_groups = [aws_security_group.open_sg.name]
> 
>   tags = {
>     Name = "terra_bastion"
>   }
> }
> ```

---

### 23-2. 필수 조건 판정

| 요구사항 | 현재 코드 | 판정 |
|---|---|---|
| VPC 1개 | `aws_vpc.terra_vpc` | 만족 |
| Public Subnet 1개 | `aws_subnet.terra_open_subnet` | 이름/배치 구조상 만족 |
| Private Subnet 1개 | `aws_subnet.terra_close_subnet` | 이름/배치 구조상 만족 |
| Public Subnet에 EC2 1개 | `terra_bastion` → `terra_open_subnet` | 만족 |
| Private Subnet에 EC2 1개 | `terra_web` → `terra_close_subnet` | 만족 |

정확한 판정은 다음과 같다.

```text
리소스 개수와 배치 조건:
만족

AWS 네트워크 의미상 Public/Private Subnet:
아직 미완성
```

현재 코드는 **Subnet 2개와 EC2 2개를 만들고, EC2를 서로 다른 Subnet에 배치하는 조건**은 충족한다.

하지만 `terra_open_subnet`이 이름 그대로 실제 public subnet이 되려면 추가 구성이 필요하다.

---

### 23-3. 현재 코드의 리소스 관계

현재 관계는 다음과 같다.

```text
aws_vpc.terra_vpc
├─ aws_subnet.terra_open_subnet
│  └─ aws_instance.terra_bastion
└─ aws_subnet.terra_close_subnet
   └─ aws_instance.terra_web
```

핵심 참조는 두 줄이다.

```hcl
subnet_id = aws_subnet.terra_close_subnet.id
```

```hcl
subnet_id = aws_subnet.terra_open_subnet.id
```

이 때문에 Terraform은 다음을 알 수 있다.

```text
terra_web은 terra_close_subnet이 있어야 생성 가능
terra_bastion은 terra_open_subnet이 있어야 생성 가능
두 subnet은 terra_vpc가 있어야 생성 가능
```

따라서 이 실습은 Terraform의 resource 참조 학습에 적절하다.

---

### 23-4. 왜 아직 진짜 Public Subnet이 아닌가

현재 `terra_open_subnet`은 이름만 open/public 역할이다.

```hcl
resource "aws_subnet" "terra_open_subnet" {
  vpc_id     = aws_vpc.terra_vpc.id
  cidr_block = "10.0.1.0/24"
}
```

이 설정만으로는 인터넷과 연결되지 않는다.

실제 public subnet에 가까워지려면 보통 다음이 필요하다.

```text
Internet Gateway
Public Route Table
0.0.0.0/0 → Internet Gateway route
Route Table Association
Public IP 자동 할당 설정
```

즉, 지금 코드는 다음 단계로 가기 전의 중간 상태다.

```text
현재:
Subnet을 2개로 나누고 EC2를 각각 배치함

아직:
Public subnet / Private subnet의 라우팅 의미는 완성하지 않음
```

---

### 23-5. AZ를 지정하지 않았는데 2c로 간 이유

실습 결과, AZ를 명시하지 않았는데 private subnet과 web server가 `ap-northeast-2c`에 생성되었다.

이것은 Terraform이 고가용성을 판단해 “센스 있게” 배치한 것이 아니다.

정확한 해석은 다음이다.

```text
1. aws_subnet.terra_close_subnet에서 availability_zone을 지정하지 않음
2. Subnet 생성 요청 시 AWS가 AZ 하나를 선택함
3. 그 결과 terra_close_subnet이 ap-northeast-2c에 생성됨
4. terra_web은 terra_close_subnet.id를 참조함
5. 따라서 terra_web도 ap-northeast-2c에 배치됨
```

즉, EC2가 직접 AZ를 고른 것이 아니다.

```text
Subnet이 2c에 생겼고,
EC2는 그 Subnet 안에 들어갔을 뿐이다.
```

이 관찰은 중요하다.

Terraform은 의존성 관계를 잘 계산하지만, 사람이 의도한 고가용성 배치까지 자동 설계해주지는 않는다.  
AZ를 명확히 나누고 싶으면 코드에 `availability_zone`을 직접 적는 편이 좋다.

예:

```hcl
resource "aws_subnet" "terra_open_subnet" {
  vpc_id            = aws_vpc.terra_vpc.id
  cidr_block        = "10.0.1.0/24"
  availability_zone = "ap-northeast-2a"

  tags = {
    Name = "terra_open_subnet"
  }
}

resource "aws_subnet" "terra_close_subnet" {
  vpc_id            = aws_vpc.terra_vpc.id
  cidr_block        = "10.0.2.0/24"
  availability_zone = "ap-northeast-2c"

  tags = {
    Name = "terra_close_subnet"
  }
}
```

---

### 23-6. Public IP 자동 할당이 꺼져 있던 이유

실습 결과, `terra_open_subnet`에서 Public IP 자동 할당이 켜져 있지 않았다.

이것도 정상적인 결과다.

현재 코드에는 다음 설정이 없다.

```hcl
map_public_ip_on_launch = true
```

따라서 subnet 설정에서 새 인스턴스에 public IPv4를 자동 할당하도록 지정하지 않았다.

Public Subnet 역할을 더 명확히 하려면 open subnet에 다음 옵션을 넣는다.

```hcl
resource "aws_subnet" "terra_open_subnet" {
  vpc_id                  = aws_vpc.terra_vpc.id
  cidr_block              = "10.0.1.0/24"
  availability_zone       = "ap-northeast-2a"
  map_public_ip_on_launch = true

  tags = {
    Name = "terra_open_subnet"
  }
}
```

다만 이것만으로 충분하지 않다.

```text
map_public_ip_on_launch = true
```

는 “이 Subnet에서 새 EC2를 만들 때 Public IP를 자동 부여할 수 있게 하는 설정”이다.

하지만 인터넷 통신이 되려면 여전히 다음이 필요하다.

```text
Internet Gateway
0.0.0.0/0 → Internet Gateway route
해당 Route Table과 Public Subnet 연결
Security Group ingress/egress
```

---

### 23-7. Security Group 주석에 대한 메모

초안에는 Security Group 리소스가 주석 처리되어 있다.

```hcl
# resource "aws_security_group" "open_sg" {
#   name        = "open_sg"
#   vpc_id      = aws_vpc.terra_vpc.id
# }
```

현재 실습 조건이 “EC2를 각 Subnet에 배치”라면 Security Group은 필수 조건이 아닐 수 있다.

하지만 접속 검증까지 목표가 확장되면 Security Group은 사실상 필요하다.

또한 VPC 안의 EC2에 Security Group을 명시할 때는 다음 속성을 우선 사용한다.

```hcl
vpc_security_group_ids = [aws_security_group.open_sg.id]
```

초안의 주석처럼 `security_groups`에 Security Group 이름을 넣는 방식은 VPC 환경에서는 혼동을 만들기 쉽다.

```hcl
# security_groups = [aws_security_group.open_sg.name]
```

이 줄은 나중에 접속 구성 단계에서 다음처럼 바꾸는 편이 낫다.

```hcl
vpc_security_group_ids = [aws_security_group.open_sg.id]
```

---

### 23-8. 이 실습에서 얻은 결론

이번 실습에서 확인한 것은 다음이다.

```text
VPC 안에 Subnet을 2개 만들 수 있다.
각 Subnet에 서로 다른 CIDR을 줄 수 있다.
EC2는 subnet_id로 특정 Subnet에 배치할 수 있다.
Subnet이 생성된 AZ가 EC2의 AZ를 결정한다.
AZ 미지정 시 AWS가 AZ를 선택할 수 있다.
Public IP 자동 할당은 명시하지 않으면 켜지지 않는다.
Subnet 이름만으로 Public/Private이 결정되지는 않는다.
```

따라서 이번 코드는 다음 단계로 분류한다.

```text
1차 실습:
VPC/Subnet/EC2 최소 골격

2차 실습:
Public/Private 역할을 의도한 Subnet 2개와 EC2 2대 배치

아직 남은 단계:
Public Subnet 라우팅 완성
Private Subnet 라우팅/격리 검증
Security Group 명시
Bastion을 통한 Private EC2 접속 검증
```


## 24. 초기화 후 검증 체크리스트

```cmd
terraform version
aws --version
aws configure list --profile Terra-user
aws sts get-caller-identity --profile Terra-user
terraform init
```

체크:

```text
[ ] aws --version 출력됨
[ ] terraform version 출력됨
[ ] Terra-user profile 설정됨
[ ] sts get-caller-identity 성공
[ ] main.tf에 AWS Provider 작성됨
[ ] terraform init 성공
[ ] .terraform.lock.hcl 생성됨
```

---

## 25. 자주 나는 오류

### 15-1. `terraform` is not recognized

원인:

```text
PATH 미등록
터미널 재시작 안 함
terraform.exe 위치 다름
```

조치:

```cmd
dir D:\terraform
D:\terraform\terraform.exe version
where terraform
```

### 15-2. AWS 인증 실패

증상 예:

```text
Unable to locate credentials
The security token included in the request is invalid
InvalidClientTokenId
```

조치:

```cmd
aws configure list --profile Terra-user
aws sts get-caller-identity --profile Terra-user
```

확인할 것:

```text
Profile 이름 오타
Access Key ID 오타
Secret Access Key 오타
키 삭제/비활성화 여부
환경변수에 다른 키가 잡혀 있는지
```

### 15-3. AccessDenied

의미:

```text
인증은 됐지만 권한이 부족하다.
```

조치:

```text
IAM 사용자 권한 확인
실습에서 요구하는 정책이 붙어 있는지 확인
계정/사용자가 맞는지 sts get-caller-identity로 확인
```

### 15-4. Region 관련 오류

확인:

```cmd
aws configure list --profile Terra-user
```

Terraform Provider에 region 명시:

```hcl
provider "aws" {
  region  = "ap-northeast-2"
  profile = "Terra-user"
}
```

---

## Definition of Done

이 실습 노트는 아래가 되면 완료로 본다.

```text
[ ] AWS CLI 설치/업데이트 완료
[ ] Terraform 설치 및 PATH 확인 완료
[ ] AWS CLI Terra-user profile 생성
[ ] sts get-caller-identity로 현재 사용자 확인
[ ] D:\terraform\workspace\01_basic 생성
[ ] main.tf에 AWS Provider 작성
[ ] terraform init 성공
[ ] VPC/Subnet/EC2 최소 골격 main.tf 작성
[ ] Public/Private 역할 Subnet 2개와 EC2 2대 배치 실습 작성
[ ] AZ 미지정 시 AWS가 AZ를 선택할 수 있음을 확인
[ ] Public IP 자동 할당은 별도 설정이 필요함을 확인
[ ] terraform fmt 실행
[ ] terraform validate 성공
[ ] terraform plan에서 VPC/Subnet/EC2 생성 예정 확인
[ ] 실습으로 apply했다면 terraform destroy까지 완료
[ ] Access Key CSV 삭제 또는 안전한 저장소로 이동
[ ] 공용/남의 컴퓨터라면 .aws credential 정리
```

---

## 관련 노트

- [[00_IaC MOC]]
- [[IaC 도구 분류]]
- [[Terraform 개요]]
- [[Terraform Workflow]]
- [[Terraform Resource와 Data Source]]
- [[Terraform Backend와 Remote State]]
