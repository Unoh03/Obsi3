---
type: project-doc
status: draft
study_status: project-mapped
created: 2026-08-04
updated: 2026-08-05
project: 3차 프로젝트
project_moc: "[[20_팀 프로젝트/3차 프로젝트/00_3차프로젝트_목차]]"
---

# VPC Flow Logs

> [!abstract]- 프로젝트 로그·관측성 MOC
> ![[00_로그 인프라 전체 흐름#전체 흐름]]

> [!info] 이 노트의 위치
> Primary VPC의 ENI에서 거부된 Network Flow Metadata를 기록해 Security Log S3로 전달하는 네트워크 관측 계층이다.

## 한 줄 정의

VPC Flow Logs는 VPC, Subnet 또는 ENI를 통과하는 IP Traffic의 흐름 정보를 기록하는 기능이다.

## 무엇을 기록하는가

현재 프로젝트가 사용하는 기본 14개 Field 형식:

```text
version account-id interface-id srcaddr dstaddr srcport dstport
protocol packets bytes start end action log-status
```

중요 Field:

- `interface_id`: 관측된 ENI
- `srcaddr`, `dstaddr`: Source·Destination IP
- `srcport`, `dstport`: Port
- `protocol`: IP Protocol Number
- `packets`, `bytes`: 집계된 Traffic 양
- `action`: `ACCEPT` 또는 `REJECT`
- `log_status`: 정상 기록 여부

Packet Payload, URL, HTTP Header, SQL 문자열은 기록하지 않는다.

## 우리 프로젝트에서의 역할

`observability.tf`에서 확인된 설정:

- Resource: `aws_flow_log.primary_reject`
- 대상: Primary VPC
- Traffic Type: `REJECT`
- Destination Type: S3
- Destination Prefix: `vpc-flow`
- Max Aggregation Interval: 60초
- 활성화 조건: `enable_vpc_reject_flow_logs`

```text
Primary VPC ENI의 거부 Traffic
→ VPC Flow Logs
→ Security Log S3/vpc-flow/
→ Athena Table vpc_reject
→ vpc-reject Query
→ Grafana 예정
```

## 보안 분석에서의 사용

- 허용되지 않은 Port 접근 시도 확인
- Security Group·NACL·Route 문제의 후보 찾기
- 특정 Source IP가 여러 Destination을 반복 탐색했는지 집계
- Network 계층에서 요청이 거부됐는지 확인

`REJECT`가 보였다는 사실만으로 Security Group과 NACL 중 어디서 거부됐는지 항상 단정할 수는 없다. Resource 구성과 함께 해석한다.

## 저장소에서 찾을 곳

- Flow Log: `observability.tf`
- Security Log Bucket Policy: `foundation/observability.tf`
- Athena Schema: `observability/queries/athena/00_create_security_log_tables.sql`
- Query: `observability/queries/athena/02_vpc_reject_by_source.sql`
- Runner: `observability/Invoke-AthenaQueryPack.ps1`

## 직접 확인하는 방법

```powershell
aws ec2 describe-flow-logs `
  --filter Name=resource-id,Values=<PRIMARY_VPC_ID> `
  --region ap-northeast-2

aws s3api list-objects-v2 `
  --bucket <SECURITY_LOG_BUCKET> `
  --prefix vpc-flow/ `
  --max-items 10

.\observability\Invoke-AthenaQueryPack.ps1 `
  -QueryName vpc-reject `
  -StartUtc <UTC_START> `
  -EndUtc <UTC_END> `
  -SourceIp <OPTIONAL_SOURCE_IP>
```

## 현재 확인 수준

- `REJECT` 전용 Flow Log와 S3 Destination Source: 확인
- Athena 14 Field Schema·Query: 확인
- 기존 Evidence에는 `vpc-reject` Athena Query 성공 기록이 있음
- 최신 Flow Log Status, S3 Object 도착, 실제 거부 Event: 재확인 필요

## 알려주는 것과 한계

### 확인할 수 있는 것

- Network 연결 시도의 IP·Port·Protocol
- `ACCEPT`·`REJECT` 결과
- ENI 기준 Traffic 양과 시간 범위

### 이것만으로 확인할 수 없는 것

- HTTP Method·URI·Payload
- 사용자의 Application 계정
- 공격 성공 여부
- 정확한 Packet 순서와 모든 Packet 내용

## 주의점

- Flow Log는 Packet Capture가 아니라 일정 시간창의 Flow Metadata다.
- `start`·`end`는 Unix Time이므로 다른 로그의 UTC Timestamp와 변환해 맞춘다.
- `log_status`가 `NODATA` 또는 `SKIPDATA`인 경우 정상 Flow Record와 구분한다.
- 현재는 `REJECT`만 보존하므로 정상 Traffic Baseline 전체를 제공하지 않는다.

## 근거

- 현재 저장소: `observability.tf`, Athena DDL·Query
- 공식 문서: https://docs.aws.amazon.com/vpc/latest/userguide/flow-logs.html
- Runtime Evidence: 최신 실행 재확인 필요
