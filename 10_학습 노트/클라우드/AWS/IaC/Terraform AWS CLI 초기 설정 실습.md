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

## 14. 초기화 후 검증 체크리스트

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

## 15. 자주 나는 오류

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
[ ] Access Key CSV 삭제 또는 안전한 저장소로 이동
[ ] 공용/남의 컴퓨터라면 .aws credential 정리
```

---

## 관련 노트

- [[IaC MOC]]
- [[IaC 도구 분류]]
- [[Terraform 개요]]
- [[Terraform Workflow]]
- [[Terraform Resource와 Data Source]]
- [[Terraform Backend와 Remote State]]
