---
title: Terraform RDS 초기화 방식 비교와 S3 schema.sql 검증 실습
version: v7.1-draft
created: 2026-07-09
status: draft
type: lab-note-draft
source:
  - Terraform RDS 인프라 구성 실습 v7.0.md
  - Terraform AWS CLI 초기 설정 실습 v6.3.md
  - 02_rds/main.tf
  - user_data/00-common.sh
  - user_data/20-web-install.sh.tftpl
  - conversation-log
official_refs:
  - https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_VPC.WorkingWithRDSInstanceinaVPC.html
  - https://docs.aws.amazon.com/cli/latest/reference/rds/wait/db-instance-available.html
  - https://developer.hashicorp.com/terraform/language/meta-arguments/depends_on
  - https://developer.hashicorp.com/terraform/language/functions/templatefile
tags:
  - 과목/AWS
  - 주제/IaC
  - 주제/Terraform
  - 주제/RDS
  - 주제/S3
  - 주제/user_data
  - 상태/draft
  - 실습/Terraform
---

# Terraform RDS 초기화 방식 비교와 S3 schema.sql 검증 실습 v7.1 초안

## 목적

이 초안은 v7.1 실습을 시작하기 전에 **RDS 초기화 SQL을 어디서, 언제, 어떤 방식으로 실행할지**를 정리하기 위한 설계 노트다.

v7.1의 핵심은 단순히 `/db-test.php`가 성공하는 것이 아니다.

핵심 논점은 다음이다.

```text
RDS는 EC2처럼 DB 서버 내부에 user_data를 넣을 수 없다.
따라서 DB/table/schema 초기화 SQL을 실행할 위치와 타이밍을 새로 선택해야 한다.

방법 2:
WEB의 /db-test.php 요청 시점에 table을 만든다.

방법 3:
WEB EC2 user_data 실행 중 RDS에 접속해 table을 만든다.

방법 3-1:
방법 3을 확장해, SQL을 user_data에 직접 박지 않고 S3의 schema.sql로 분리한다.
```

> [!important] v7.1의 초점
> v7.1은 **방법 2와 방법 3의 구조 차이**, **Terraform 의존성과 RDS readiness의 차이**, **방법 3에서 5초 확인 루프가 필요한 이유**, **S3 schema.sql 방식의 의미**를 설명한 뒤 실제 검증으로 이어간다.

---

## 출처 구분

```text
① 내장 지식:
- Terraform 의존성 그래프 해석
- user_data/cloud-init 실행 타이밍 해석
- DB 초기화 방식 비교
- 실습 노트 구조화

② 인터넷 고신뢰 정보:
- AWS RDS 공식 문서
- AWS CLI RDS waiter 공식 문서
- HashiCorp Terraform depends_on 공식 문서
- HashiCorp Terraform templatefile 공식 문서

③ 인터넷 비공식 고품질 의견:
- 사용 안 함

④ 업로드/실습 자료:
- Terraform RDS 인프라 구성 실습 v7.0.md
- Terraform AWS CLI 초기 설정 실습 v6.3.md
- 현재 02_rds Terraform 코드와 user_data 파일
- 실습 중 대화와 오류 로그
```

---

## 빠른 이동

> [!abstract] 주요 이동
> - [[#Part 1. v7.0 RDS 인프라 구성까지의 정리|Part 1. v7.0 RDS 인프라 구성까지의 정리]]
> - [[#1. v6.3에서 가능했던 DB EC2 user_data 초기화|1. v6.3에서 가능했던 DB EC2 user_data 초기화]]
> - [[#2. v7.0에서 바뀐 RDS 구조|2. v7.0에서 바뀐 RDS 구조]]
> - [[#3. v7.0 완료 지점과 v7.1로 넘긴 지점|3. v7.0 완료 지점과 v7.1로 넘긴 지점]]
> - [[#Part 2. v7.1 RDS 초기화 방식 비교와 S3 schema.sql 설계|Part 2. v7.1 RDS 초기화 방식 비교와 S3 schema.sql 설계]]
> - [[#4. 문제: RDS에서는 DB 서버 user_data를 쓸 수 없다|4. 문제: RDS에서는 DB 서버 user_data를 쓸 수 없다]]
> - [[#5. 방법 2: /db-test.php 요청 시점 초기화|5. 방법 2]]
> - [[#6. 방법 3: WEB user_data에서 RDS 초기화|6. 방법 3]]
> - [[#7. Terraform 의존성의 타이밍|7. Terraform 의존성의 타이밍]]
> - [[#8. 방법 3에서 5초 확인 루프가 필요한 이유|8. 방법 3에서 5초 확인 루프가 필요한 이유]]
> - [[#9. 방법 2는 왜 5초 확인 루프가 필수가 아닌가|9. 방법 2는 왜 5초 확인 루프가 필수가 아닌가]]
> - [[#10. 방법 3-1: S3 schema.sql + WEB user_data|10. 방법 3-1]]
> - [[#11. v7.1 구현 설계안|11. v7.1 구현 설계안]]
> - [[#12. 검증 증거 수집 계획|12. 검증 증거 수집 계획]]
> - [[#13. v7.1 완료 판정 기준|13. v7.1 완료 판정 기준]]

---

# Part 1. v7.0 RDS 인프라 구성까지의 정리

이 파트는 v7.1의 새 실습을 시작하기 전, v7.0에서 이미 끝낸 내용을 하나의 큰 단위로 묶어 정리한다.

## 1. v6.3에서 가능했던 DB EC2 user_data 초기화

v6.3에서는 DB가 RDS가 아니라 Private Subnet의 EC2였다.

```text
Public WEB EC2
→ Private DB EC2
→ DB EC2 내부에 MariaDB 직접 설치
```

이 구조에서는 DB 서버 운영체제에 접근할 수 있었다.  
따라서 DB EC2의 `user_data` 또는 shell script에서 다음 작업을 수행할 수 있었다.

```text
- MariaDB 설치
- MariaDB service enable/start
- bind-address 설정
- appdb 생성
- webuser 생성
- connection_test 테이블 생성
- 초기 데이터 INSERT
```

핵심은 이것이다.

```text
DB가 EC2이면,
우리가 DB 서버 OS에 user_data를 넣을 수 있다.
```

따라서 v6에서는 table 생성 코드를 DB 서버의 shell script에 넣는 방식이 자연스러웠다.

---

## 2. v7.0에서 바뀐 RDS 구조

v7.0부터는 DB 서버가 EC2가 아니라 RDS MariaDB가 되었다.

```text
Public WEB EC2
→ Private RDS MariaDB
```

RDS는 관리형 DB 서비스이므로, 일반 EC2처럼 DB 서버 운영체제에 `user_data`를 넣을 수 없다.

바뀐 점:

| 항목 | v6.3 | v7.0 |
|---|---|---|
| DB 구현 | Private EC2 + MariaDB | RDS MariaDB |
| DB 서버 OS 접근 | 가능 | 불가능 |
| DB 서버 user_data | 가능 | 불가능 |
| DB 접속 주소 | Private IP | RDS endpoint DNS |
| DB subnet | private subnet 1개 | DB subnet group용 private subnet 2개 |
| DB 초기화 위치 | DB EC2 shell script | 새로 결정 필요 |

## 2-1. v7.0에서 확정한 인프라 구조

```text
VPC 10.20.0.0/16
├─ Public Subnet A       10.20.1.0/24   ap-northeast-2a
│  └─ WEB EC2
│
├─ Private DB Subnet A   10.20.10.0/24  ap-northeast-2a
│  └─ RDS subnet group member
│
└─ Private DB Subnet C   10.20.11.0/24  ap-northeast-2c
   └─ RDS subnet group member
```

v7.0에서 확인한 핵심 제약:

```text
RDS DB Instance가 1개여도,
일반 Region의 DB subnet group은 최소 2개 AZ의 subnet을 포함해야 한다.
```

## 2-2. v7.0에서 남긴 핵심 시행착오

```text
- aws_db_instance에 subnet ID를 직접 넣으려 한 오류
- templatefile 경로 오류
- RDS master password 8자 미만 오류
- DBSubnetGroupDoesNotCoverEnoughAZs 오류
```

특히 `DBSubnetGroupDoesNotCoverEnoughAZs`는 v7.0의 핵심 학습 포인트였다.

```text
subnet 1개 DB subnet group
→ apply 단계에서 AWS RDS API가 거부
→ 서로 다른 AZ의 private subnet 2개로 수정
→ RDS 생성 성공
```

---

## 3. v7.0 완료 지점과 v7.1로 넘긴 지점

## 3-1. v7.0 완료 지점

```text
[x] 02_rds 별도 Terraform root module 구성
[x] VPC 10.20.0.0/16 구성
[x] Public WEB Subnet 구성
[x] Private DB Subnet 2개 구성
[x] DB subnet group 2AZ 요구사항 검증
[x] RDS MariaDB instance 생성 성공
[x] RDS endpoint를 WEB user_data에 주입하는 구조 구성
[x] Terraform implicit dependency로 RDS → WEB 생성 순서가 잡힘을 확인
```

## 3-2. v7.1로 넘긴 지점

```text
[ ] RDS 내부 table 생성 방식 결정
[ ] WEB → RDS SQL 접속 검증
[ ] /db-test.php에서 INSERT/SELECT 증적 확보
[ ] DB 초기화 방식의 타이밍 차이 정리
[ ] S3 schema.sql 방식 적용 여부 결정
```

v7.1은 여기서 출발한다.

---

# Part 2. v7.1 RDS 초기화 방식 비교와 S3 schema.sql 설계

이 파트는 이번에 새로 추가하는 내용이다.  
핵심은 **RDS 초기화 SQL을 어디에서 실행할 것인가**와 **그 실행 타이밍에 따라 readiness check가 왜 달라지는가**다.

## 4. 문제: RDS에서는 DB 서버 user_data를 쓸 수 없다

v6에서는 DB EC2에 직접 shell script를 넣었다.

```text
DB EC2 user_data
→ MariaDB 설치
→ appdb 생성
→ table 생성
```

하지만 RDS에서는 이 구조가 불가능하다.

```text
RDS는 관리형 DB다.
DB 서버 OS에 SSH로 들어가거나 user_data를 넣는 구조가 아니다.
```

따라서 v7.1에서는 DB 초기화 SQL을 실행할 위치를 다시 선택해야 한다.

가능한 선택지:

```text
방법 2:
WEB의 /db-test.php 요청 시점에 table 생성

방법 3:
WEB EC2 user_data에서 RDS에 접속해 table 생성

방법 3-1:
방법 3을 확장해, SQL을 S3의 schema.sql로 분리하고 WEB user_data가 가져와 실행
```

---

## 5. 방법 2: `/db-test.php` 요청 시점 초기화

## 5-1. 구조

방법 2는 현재 v7.0의 `20-web-install.sh.tftpl`에 이미 들어가 있는 방식이다.

```text
사용자 또는 검증자가 /db-test.php 요청
→ PHP가 RDS endpoint에 접속
→ CREATE TABLE IF NOT EXISTS
→ INSERT
→ SELECT
→ 결과 출력
```

흐름:

```text
terraform apply 완료
→ WEB EC2 생성 완료
→ Apache/PHP-FPM 구동
→ 사용자가 /db-test.php 요청
→ 그 시점에 RDS 접속 및 SQL 실행
```

## 5-2. 장점

```text
- 가장 단순하다.
- 추가 리소스가 거의 없다.
- 실패해도 브라우저 새로고침 또는 curl 재실행으로 재시도할 수 있다.
- RDS가 준비될 시간을 사람이 자연스럽게 벌어준다.
```

## 5-3. 단점

```text
- 검증 페이지가 DB schema 생성까지 담당한다.
- 애플리케이션 요청이 DB 초기화를 수행하는 구조다.
- 운영식 정석과는 거리가 있다.
```

## 5-4. 판정

```text
방법 2는 실습 검증에는 쉽고 빠르지만,
v7.1에서 새로 배우려는 “초기화 타이밍”과 “readiness check”를 설명하기에는 약하다.
```

---

## 6. 방법 3: WEB `user_data`에서 RDS 초기화

## 6-1. 구조

방법 3은 WEB EC2가 부팅될 때 RDS 초기화 SQL을 실행한다.

```text
WEB EC2 생성
→ cloud-init/user_data 실행
→ Apache/PHP 등 패키지 설치
→ RDS endpoint 접속 가능 여부 확인
→ CREATE TABLE / 초기 INSERT 실행
→ db-test.php 배포
```

## 6-2. 방법 2와의 핵심 차이

| 항목 | 방법 2 | 방법 3 |
|---|---|---|
| SQL 실행 시점 | `/db-test.php` 요청 시점 | WEB EC2 부팅 초기 |
| 실행 주체 | PHP 페이지 | WEB EC2 user_data shell script |
| 실패 시 재시도 | 브라우저 새로고침/curl 재실행 | user_data는 이미 실패하고 끝날 수 있음 |
| readiness check 필요성 | 낮음 | 높음 |
| 구조적 분리 | 약함 | 더 좋음 |
| 검증 페이지 역할 | 생성 + 검증 | 검증 중심 |

## 6-3. 방법 3의 장점

```text
- DB 초기화와 검증 페이지 역할을 분리할 수 있다.
- RDS table 생성이 사용자의 HTTP 요청에 의존하지 않는다.
- 인프라 생성 후 자동 초기화 흐름을 설명하기 좋다.
```

## 6-4. 방법 3의 단점

```text
- user_data 실행 타이밍이 빠르다.
- RDS가 실제 SQL 접속을 받을 준비가 되기 전에 SQL을 던지면 실패할 수 있다.
- 그래서 readiness check가 필요하다.
```

---

## 7. Terraform 의존성의 타이밍

현재 Terraform 구조에서는 WEB user_data가 RDS endpoint를 참조한다.

```hcl
web_user_data = templatefile("${path.module}/user_data/20-web-install.sh.tftpl", {
  db_host     = aws_db_instance.terra_rds.address
  db_name     = "appdb"
  db_user     = "webuser"
  db_password = "itbank1234"
})
```

이 참조 때문에 Terraform은 다음 의존성을 추론한다.

```text
aws_instance.terra_WEB
→ local.web_user_data
→ aws_db_instance.terra_rds.address
→ aws_db_instance.terra_rds
```

따라서 Terraform은 RDS resource가 먼저 필요하다고 판단한다.

## 7-1. Terraform 의존성이 보장하는 것

```text
[x] RDS resource를 먼저 생성
[x] RDS endpoint 값을 계산
[x] 그 값을 WEB user_data 템플릿에 렌더링
[x] 그 뒤 WEB EC2 생성
```

## 7-2. Terraform 의존성이 보장하지 않는 것

```text
[ ] WEB EC2 user_data가 SQL을 실행하는 바로 그 순간 RDS가 SQL 접속을 받을 준비가 끝났는지
[ ] MariaDB engine이 로그인과 쿼리를 안정적으로 받을 준비가 되었는지
[ ] DNS/SG/route/engine 상태가 user_data 실행 타이밍과 완전히 맞물리는지
```

정리:

```text
Terraform 의존성은 리소스 생성 순서를 보장한다.
하지만 user_data 내부 SQL 실행 시점의 DB readiness를 보장하는 것은 아니다.
```

---

## 8. 방법 3에서 5초 확인 루프가 필요한 이유

## 8-1. 핵심 문장

```text
RDS endpoint 값을 안다
≠
RDS MariaDB가 SQL 접속을 받을 준비가 되었다
```

방법 3은 WEB EC2의 user_data가 자동으로 SQL을 실행한다.  
user_data는 EC2 부팅 초기에 한 번 실행되므로, 그 순간 RDS 접속이 실패하면 초기화 SQL도 실패하고 지나갈 수 있다.

따라서 WEB user_data 내부에서 RDS 접속 가능성을 반복 확인해야 한다.

## 8-2. ICMP ping이 아니라 SQL 접속 확인을 해야 한다

강사님이 말한 “핑”은 일반 표현으로 이해하는 것이 안전하다.

RDS 준비 확인에는 다음보다:

```bash
ping <RDS_ENDPOINT>
```

아래 방식이 더 적절하다.

```bash
mysql -h "$DB_HOST" -u "$DB_USER" -p"$DB_PASSWORD" "$DB_NAME" -e "SELECT 1;"
```

이 명령이 성공하면 다음을 동시에 확인한다.

```text
- DNS 해석
- WEB → RDS 3306 네트워크 접근
- RDS MariaDB engine 응답
- 사용자 인증
- 대상 DB 접근
- SQL 실행 가능
```

## 8-3. 5초 확인 루프 예시

```bash
DB_READY=0

for i in {1..60}; do
  if mysql -h "$DB_HOST" -u "$DB_USER" -p"$DB_PASSWORD" "$DB_NAME" -e "SELECT 1;" >/dev/null 2>&1; then
    echo "RDS is ready"
    DB_READY=1
    break
  fi

  echo "Waiting for RDS... attempt $i"
  sleep 5
done

if [[ "$DB_READY" -ne 1 ]]; then
  echo "RDS was not ready in time"
  exit 1
fi
```

이 설정은 최대 5분 동안 RDS SQL 접속 가능 상태를 기다린다.

```text
60회 × 5초 = 300초
```

## 8-4. 노트용 문장

```text
방법 3에서는 Terraform 의존성으로 RDS 생성 순서는 보장되지만,
WEB EC2의 user_data가 실행되는 순간의 SQL 접속 가능성까지 보장되지는 않는다.
따라서 user_data 내부에서 5초 간격으로 RDS 접속을 재시도하고,
`SELECT 1`이 성공한 뒤 table 생성 SQL을 실행하는 방식이 안전하다.
```

---

## 9. 방법 2는 왜 5초 확인 루프가 필수가 아닌가

방법 2는 SQL 실행 시점이 다르다.

```text
방법 2:
terraform apply 완료
→ 사용자가 브라우저/curl로 /db-test.php 요청
→ 그때 PHP가 RDS 접속 시도
```

즉 SQL 실행이 EC2 부팅 직후 자동 실행되는 것이 아니다.  
사람이 요청한 시점에 실행된다.

보통 그 사이에 시간이 지난다.

```text
- RDS 생성 완료 후
- WEB EC2 부팅 완료 후
- Apache/PHP-FPM 구동 후
- 사용자가 직접 요청한 시점
```

그리고 실패해도 재시도가 쉽다.

```text
방법 2 실패:
브라우저 새로고침 또는 curl 재실행

방법 3 실패:
cloud-init/user_data가 이미 실패하고 끝났을 수 있음
```

따라서 방법 2에서는 5초 확인 루프가 필수는 아니다.

다만 더 견고하게 만들려면 PHP 안에서 retry를 넣을 수는 있다.  
그러나 이번 실습의 핵심은 방법 3과 방법 3-1의 자동 초기화 구조이므로, 방법 2는 비교 대상으로만 둔다.

---

## 10. 방법 3-1: S3 schema.sql + WEB user_data

## 10-1. 구조

방법 3-1은 방법 3을 확장한다.

```text
S3 Bucket
└─ schema.sql

WEB EC2 user_data
→ S3에서 schema.sql 다운로드
→ RDS 접속 가능 여부를 5초 간격으로 확인
→ SELECT 1 성공
→ schema.sql 실행
→ db-test.php는 INSERT/SELECT 검증만 수행
```

## 10-2. 방법 3과의 차이

| 항목 | 방법 3 | 방법 3-1 |
|---|---|---|
| SQL 위치 | user_data 내부 heredoc | S3의 `schema.sql` |
| user_data 역할 | SQL 보관 + 실행 | SQL 다운로드 + 실행 |
| SQL 관리 | 스크립트에 섞임 | 별도 파일로 분리 |
| 실습 의미 | 자동 초기화 | 자동 초기화 + S3 연동 |
| 확장성 | 보통 | 더 좋음 |

## 10-3. 이 방식을 선택하는 이유

```text
- /db-test.php가 table 생성까지 담당하지 않아도 된다.
- SQL을 user_data에 길게 박지 않아도 된다.
- schema.sql을 별도 파일로 관리할 수 있다.
- v6에서 다룬 S3 Gateway Endpoint 사고방식과 연결된다.
- 강사님이 언급한 S3 맥락도 반영할 수 있다.
- Migration EC2/Lambda/CodeBuild까지 가는 것보다는 가볍다.
```

## 10-4. 이번 v7.1의 최종 선택

```text
v7.1에서는 방법 2와 방법 3을 비교한 뒤,
최종 구현 방식으로 방법 3-1을 선택한다.
```

---

## 11. v7.1 구현 설계안

> [!warning] 상태
> 아래 코드는 v7.1 구현 설계안이다.  
> 실제 적용 후 `terraform validate`, `terraform plan`, `terraform apply`, `cloud-init-output.log` 결과로 검증해야 한다.

## 11-1. `schema.sql` 파일 추가

예상 경로:

```text
02_rds/schema/schema.sql
```

초안:

```sql
CREATE TABLE IF NOT EXISTS connection_test (
  id INT AUTO_INCREMENT PRIMARY KEY,
  message VARCHAR(255) NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO connection_test (message)
VALUES ('S3 schema.sql -> RDS bootstrap OK');
```

## 11-2. Terraform에서 S3 object로 업로드

구성 후보:

```hcl
data "aws_caller_identity" "current" {}

resource "aws_s3_bucket" "schema_bucket" {
  bucket = "terra-rds-schema-${data.aws_caller_identity.current.account_id}"
}

resource "aws_s3_object" "schema_sql" {
  bucket = aws_s3_bucket.schema_bucket.id
  key    = "rds/schema.sql"
  source = "${path.module}/schema/schema.sql"
  etag   = filemd5("${path.module}/schema/schema.sql")
}
```

## 11-3. WEB EC2가 S3 object를 읽을 IAM role

구성 후보:

```hcl
resource "aws_iam_role" "web_role" {
  name = "terra-web-rds-schema-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })
}

resource "aws_iam_role_policy" "web_schema_read" {
  name = "terra-web-read-schema-sql"
  role = aws_iam_role.web_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject"
        ]
        Resource = aws_s3_object.schema_sql.arn
      }
    ]
  })
}

resource "aws_iam_instance_profile" "web_profile" {
  name = "terra-web-rds-schema-profile"
  role = aws_iam_role.web_role.name
}
```

WEB EC2에 instance profile 연결:

```hcl
resource "aws_instance" "terra_WEB" {
  # 기존 설정 유지

  iam_instance_profile = aws_iam_instance_profile.web_profile.name
}
```

## 11-4. `templatefile()` 변수 추가

```hcl
web_user_data = templatefile("${path.module}/user_data/20-web-install.sh.tftpl", {
  db_host       = aws_db_instance.terra_rds.address
  db_name       = "appdb"
  db_user       = "webuser"
  db_password   = "itbank1234"
  schema_s3_uri = "s3://${aws_s3_bucket.schema_bucket.id}/${aws_s3_object.schema_sql.key}"
})
```

이렇게 하면 WEB user_data는 RDS endpoint뿐 아니라 S3의 schema.sql 위치도 알 수 있다.

Terraform 의존성은 더 늘어난다.

```text
aws_instance.terra_WEB
→ local.web_user_data
→ aws_db_instance.terra_rds.address
→ aws_db_instance.terra_rds

aws_instance.terra_WEB
→ local.web_user_data
→ aws_s3_object.schema_sql.key
→ aws_s3_object.schema_sql
→ aws_s3_bucket.schema_bucket
```

## 11-5. `20-web-install.sh.tftpl` 수정 방향

핵심 변경:

```text
기존:
db-test.php 안에서 CREATE TABLE IF NOT EXISTS 실행

변경:
user_data에서 S3 schema.sql 다운로드
→ RDS readiness check
→ schema.sql 실행
→ db-test.php는 INSERT/SELECT 검증만 수행
```

설계안:

```bash
dnf install -y httpd php php-mysqlnd php-fpm mariadb105 awscli

DB_HOST='${db_host}'
DB_NAME='${db_name}'
DB_USER='${db_user}'
DB_PASSWORD='${db_password}'
SCHEMA_S3_URI='${schema_s3_uri}'
SCHEMA_LOCAL_PATH='/tmp/schema.sql'

aws s3 cp "$SCHEMA_S3_URI" "$SCHEMA_LOCAL_PATH"

DB_READY=0

for i in {1..60}; do
  if mysql -h "$DB_HOST" -u "$DB_USER" -p"$DB_PASSWORD" "$DB_NAME" -e "SELECT 1;" >/dev/null 2>&1; then
    echo "RDS is ready"
    DB_READY=1
    break
  fi

  echo "Waiting for RDS... attempt $i"
  sleep 5
done

if [[ "$DB_READY" -ne 1 ]]; then
  echo "RDS was not ready in time"
  exit 1
fi

mysql -h "$DB_HOST" -u "$DB_USER" -p"$DB_PASSWORD" "$DB_NAME" < "$SCHEMA_LOCAL_PATH"

echo "DB init completed from $SCHEMA_S3_URI"
```

> [!warning] 확인 필요
> Amazon Linux 2023에서 AWS CLI 패키지명이 환경에 따라 다를 수 있다.  
> `dnf install -y awscli`가 실패하면 실제 패키지명 또는 기본 탑재 여부를 확인해야 한다.

## 11-6. 검증용 `db-test.php`의 역할 변경

기존 역할:

```text
CREATE TABLE IF NOT EXISTS
INSERT
SELECT
```

v7.1 목표 역할:

```text
INSERT
SELECT
```

즉, table 생성은 user_data + schema.sql이 담당하고, `/db-test.php`는 검증만 담당한다.

검증용 PHP 방향:

```php
$pdo->exec("INSERT INTO connection_test (message) VALUES ('WEB -> RDS VERIFY OK')");

$stmt = $pdo->query(
    "SELECT id, message, created_at
     FROM connection_test
     ORDER BY id DESC
     LIMIT 5"
);
```

기대 결과:

```text
WEB -> RDS CONNECT OK
DB_HOST=terra-rds-lab.xxxxxxxxxxxx.ap-northeast-2.rds.amazonaws.com

2 | WEB -> RDS VERIFY OK | ...
1 | S3 schema.sql -> RDS bootstrap OK | ...
```

---

## 12. 검증 증거 수집 계획

## 12-1. Terraform 실행

```powershell
cd D:\terraform\workspace\02_rds

terraform fmt
terraform validate
terraform plan
terraform apply
```

수집할 것:

```text
- terraform validate 성공
- terraform plan 요약
- terraform apply 성공
```

## 12-2. WEB cloud-init 로그

WEB EC2 접속 후:

```bash
sudo tail -200 /var/log/cloud-init-output.log
```

찾을 문자열:

```text
Waiting for RDS...
RDS is ready
DB init completed
```

## 12-3. S3 schema.sql 다운로드 확인

cloud-init 로그에서 확인:

```text
aws s3 cp s3://.../rds/schema.sql /tmp/schema.sql
```

WEB 내부에서 추가 확인:

```bash
ls -l /tmp/schema.sql
cat /tmp/schema.sql
```

## 12-4. WEB index 확인

외부 PC에서:

```powershell
curl.exe -v http://<WEB_PUBLIC_IP>/
```

기대:

```text
HTTP/1.1 200 OK
Terraform RDS Web Server
```

## 12-5. WEB → RDS 검증

외부 PC에서:

```powershell
curl.exe -v http://<WEB_PUBLIC_IP>/db-test.php
```

기대:

```text
WEB -> RDS CONNECT OK
DB_HOST=terra-rds-lab.xxxxxxxxxxxx.ap-northeast-2.rds.amazonaws.com

2 | WEB -> RDS VERIFY OK | ...
1 | S3 schema.sql -> RDS bootstrap OK | ...
```

이 결과가 나오면 다음이 증명된다.

```text
[x] schema.sql이 RDS에 적용됨
[x] connection_test table이 존재함
[x] bootstrap row가 존재함
[x] WEB 요청으로 INSERT가 추가됨
[x] WEB PHP가 RDS endpoint로 SELECT 결과를 가져옴
```

## 12-6. AWS Console 캡처 후보

```text
- RDS instance available 화면
- RDS endpoint 화면
- DB subnet group 2AZ subnet 화면
- S3 bucket과 schema.sql object 화면
- WEB EC2 IAM role/profile 연결 화면
- WEB EC2 public IP 화면
```

---

## 13. v7.1 완료 판정 기준

```text
[ ] 방법 2와 방법 3의 구조 차이 설명 완료
[ ] Terraform 의존성과 RDS readiness의 차이 설명 완료
[ ] 방법 3에서 5초 확인 루프가 필요한 이유 설명 완료
[ ] 방법 2에서 5초 확인 루프가 필수가 아닌 이유 설명 완료
[ ] 방법 3-1 S3 schema.sql 방식 설계 완료
[ ] schema/schema.sql 작성
[ ] Terraform S3 bucket/object 구성
[ ] WEB EC2 IAM role/profile 구성
[ ] WEB user_data에서 schema.sql 다운로드
[ ] WEB user_data에서 RDS readiness check 수행
[ ] WEB user_data에서 schema.sql 실행
[ ] `/db-test.php`를 검증 전용으로 변경
[ ] cloud-init 로그에서 `Waiting for RDS...` 확인
[ ] cloud-init 로그에서 `RDS is ready` 확인
[ ] cloud-init 로그에서 `DB init completed` 확인
[ ] `/db-test.php`에서 bootstrap row와 verify row 확인
[ ] 브라우저 또는 curl 증적 확보
[ ] 실습 후 `terraform destroy` 완료
```

---

## 14. 보고서용 문장 초안

```text
v6 실습에서는 Private DB EC2의 user_data에서 MariaDB 설치와 table 생성을 수행할 수 있었다.
그러나 v7 실습에서는 DB 계층을 Amazon RDS MariaDB로 전환했기 때문에 DB 서버 운영체제에 user_data를 삽입할 수 없다.
이에 따라 RDS 초기화 SQL을 어디에서 실행할지 별도로 설계해야 했다.

먼저 `/db-test.php` 요청 시점에 table을 생성하는 방법을 검토했으나,
이 방식은 검증 페이지가 DB schema 생성까지 담당한다는 점에서 구조적으로 아쉬움이 있었다.
따라서 WEB EC2의 user_data에서 RDS에 접속해 초기 SQL을 실행하는 방식을 검토하였다.

다만 Terraform의 implicit dependency는 RDS와 WEB EC2의 생성 순서를 보장할 뿐,
WEB user_data가 실행되는 순간 RDS MariaDB가 SQL 접속을 받을 준비가 완료되었는지를 보장하지는 않는다.
따라서 user_data 내부에서 5초 간격으로 `SELECT 1` 접속 확인을 수행하고,
RDS가 준비된 뒤 초기화 SQL을 실행하도록 구성하였다.

최종적으로 SQL을 user_data에 직접 작성하지 않고 S3의 `schema.sql`로 분리하였다.
WEB EC2는 IAM instance profile을 통해 해당 S3 object를 다운로드하고,
RDS readiness check 이후 `schema.sql`을 실행한다.
이후 `/db-test.php`는 table 생성이 아니라 WEB → RDS INSERT/SELECT 검증 전용으로 사용한다.
```

---

## 15. 확장 후보

이번 v7.1에서는 구현하지 않고, 부록 또는 후속 노트 후보로만 둔다.

```text
- 일회용 Migration EC2
- VPC Lambda DB Initializer
- CodeBuild VPC Migration Job
- ECS/Fargate one-shot migration task
- RDS snapshot 기반 seeded DB 복원
```

판정:

```text
위 방식들은 구조적으로 더 분리되어 있지만, v7.1 실습 단계에서는 과하다.
이번에는 WEB user_data + S3 schema.sql 방식으로 충분하다.
```

---

## 관련 노트

- [[00_IaC MOC]]
- [[Terraform AWS CLI 초기 설정 실습 v6.3]]
- [[Terraform RDS 인프라 구성 실습 v7.0]]
- [[Terraform Workflow]]
- [[Terraform Resource와 Data Source]]
- [[AWS Security Group의 Stateful 동작]]
- [[Amazon RDS]]
