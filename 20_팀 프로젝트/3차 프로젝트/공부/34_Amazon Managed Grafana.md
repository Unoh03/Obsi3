---
type: project-doc
status: draft
study_status: project-mapped
created: 2026-08-05
project: 3차 프로젝트
project_moc: "[[20_팀 프로젝트/3차 프로젝트/00_3차프로젝트_목차]]"
---

# Amazon Managed Grafana

> [!abstract]- 프로젝트 로그·관측성 MOC
> ![[00_로그 인프라 전체 흐름#전체 흐름]]

> [!info] 이 노트의 위치
> Athena가 S3 Log를 SQL로 조회한 결과를 Dashboard Panel로 표현하는 시각화 계층이다. 현재는 설계만 있고 Workspace·Data Source·Dashboard는 아직 생성되지 않았다.

## 한 줄 정의

Amazon Managed Grafana는 AWS가 Grafana Server의 운영·Upgrade를 관리하고, 사용자가 Data Source와 Dashboard를 구성하는 관리형 시각화 서비스다.

## 이 프로젝트에서의 정확한 흐름

```text
CloudFront·ALB·VPC REJECT Log
→ Security Log S3
→ Athena External Table·SQL
→ Grafana Athena Data Source
→ Dashboard Panel
```

Grafana가 S3 Object를 직접 File처럼 읽는 구조가 아니다. Athena가 SQL Query를 실행하고 Grafana가 결과를 시각화한다.

## 1차 시각화 범위

| Source | 최소 Panel | Data Source |
|---|---|---|
| CloudFront | 시간대별 Request·Status | Athena `cloudfront_access` |
| Primary ALB | 4xx·5xx와 Target Status | Athena `alb_primary_access` |
| Primary VPC REJECT | Source IP·Destination Port별 REJECT | Athena `vpc_reject` |

Request Trace Panel은 선택 범위다. WAF·EKS·DVWA·GuardDuty는 현재 CloudWatch Logs에 유지하며 1차 Grafana 범위에는 넣지 않는다.

## 필요한 구성요소

### AWS 측

- Amazon Managed Grafana Workspace
- Workspace 전용 IAM Role
- Athena·Glue 접근 권한
- 원본 Security Log S3 Prefix Read 권한
- Athena 전용 WorkGroup
- Query Result Bucket

### Grafana 측

- Athena Data Source
- Region·Catalog·Database·WorkGroup 설정
- Dashboard와 Panel
- Variable·Time Range

### 사용자 인증

Managed Grafana Workspace 사용자는 다음 중 하나로 인증한다.

- IAM Identity Center
- SAML Identity Provider

현재 조원용 IAM User 3명을 Workspace 사용자로 직접 연결하는 방식은 사용하지 않는다. 인증 방식 활성화는 Account·Organizations에 영향을 줄 수 있으므로 사람 승인 Gate다.

## 권한 경계

`AmazonGrafanaAthenaAccess`만으로 원본 Security Log S3 전체 Read가 자동 해결되는 것은 아니다.

```text
Workspace Role
├─ Athena Query 실행
├─ Glue Catalog 조회
├─ Query Result Bucket Read·Write
└─ Security Log Bucket의 지정 Prefix Read — 별도 Custom Policy
```

원본 Read 범위는 1차 Source로 제한한다.

- `AWSLogs/<account>/CloudFront/*`
- `alb/primary/*`
- `vpc-flow/*`

## 현재 설계 결정

- Analytics는 Foundation·Daily와 별도 수명주기
- AWS Resource와 Grafana Content를 별도 Terraform Root로 관리하는 안을 채택
- Workspace Permission: Customer-managed Role
- First Pass에서 기존 Athena DDL·Query Pack 유지
- 모든 Log를 Grafana에 넣지 않고 S3 Source 3종만 시각화

> [!warning] 기술 제약과 프로젝트 선택
> Athena를 Data Source로 사용하는 것은 요구사항에 직접 연결된 기술 경로다. 반면 Terraform Root 분리, Panel 수, Scan Limit, Result Retention은 현재 프로젝트의 운영 선택이며 절대적인 정답은 아니다.

## 구현 전 사람 Gate

1. Workspace 비용 승인
2. IAM Identity Center 또는 SAML 선택
3. Account에 필요한 인증 기반 활성화 승인
4. 실제 Admin·Viewer 사용자 결정
5. Dashboard를 프로젝트 종료 후 유지할지 결정

## 저장소에서 찾을 곳

- 결정 검증: `OBSERVABILITY-IAM-DECISIONS.md`
- 실행 레시피: `OBSERVABILITY-IAM-IMPLEMENTATION-PLAN.md`
- 기존 Athena Query: `observability/queries/athena/`
- 현재 Terraform에는 Grafana Workspace Resource가 아직 없음

## 구현 후 직접 확인할 항목

```powershell
aws grafana list-workspaces --region ap-northeast-2
aws grafana describe-workspace `
  --workspace-id <WORKSPACE_ID> `
  --region ap-northeast-2
```

Grafana UI에서는 다음을 확인한다.

1. Workspace가 `ACTIVE`
2. Admin 또는 Editor로 로그인 가능
3. Athena Data Source `Save & Test` 성공
4. Catalog·Database·WorkGroup 선택값 정확
5. 세 Panel이 실제 Row를 반환
6. 지정한 실험 UTC 시간창이 Dashboard에서 보임
7. Dashboard Screenshot과 Query ID를 Evidence로 보존

## 현재 확인 수준

- S3→Athena 분석 기반: Source와 기존 Runtime Evidence 있음
- Grafana 설계 결정·실행 레시피: 존재
- Workspace: 미구성
- User Authentication: 미결정·미구성
- Athena Data Source: 미구성
- Dashboard: 미구성

따라서 현재 요구사항 `S3 로그 분석을 AWS Grafana로 시각화`는 **분석 기반까지만 존재하고 시각화 결과는 미완료**다.

## 알려주는 것과 한계

### 확인할 수 있는 것

- 시간대별 요청·오류·REJECT 추세
- Source별 집계와 상위 값
- 동일 Query를 반복해서 보는 운영 화면

### 이것만으로 확인할 수 없는 것

- 원본 Log의 모든 Field와 상세 Context
- Dashboard에 보이지 않는 Source의 상태
- Chart 증가가 실제 공격인지 여부
- Query가 누락한 Event

## 운영·보안 주의점

- Dashboard Panel은 탐지 규칙이 아니라 시각화다.
- 넓은 시간 범위와 `SELECT *`는 Athena Scan 비용을 증가시킨다.
- Workspace Role에 Security Log Bucket 전체 권한을 주지 않는다.
- Dashboard에 IP·Finding ID를 표시할 때 발표용 화면과 원본 조사 화면을 구분한다.
- Service Account Token을 사용하면 짧게 생성하고 작업 후 삭제하며 State·Git에 저장하지 않는다.

## 근거

- 현재 저장소: `OBSERVABILITY-IAM-DECISIONS.md`, 실행 레시피, Athena Query Pack
- 공식 문서: https://docs.aws.amazon.com/grafana/latest/userguide/Athena-using-the-data-source.html
- 공식 문서: https://docs.aws.amazon.com/grafana/latest/userguide/authentication-in-AMG-SSO.html
- Runtime Evidence: Grafana 미구성
