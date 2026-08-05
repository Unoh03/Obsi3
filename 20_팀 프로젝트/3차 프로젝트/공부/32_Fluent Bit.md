---
type: project-doc
status: draft
study_status: project-mapped
created: 2026-08-04
updated: 2026-08-05
project: 3차 프로젝트
project_moc: "[[20_팀 프로젝트/3차 프로젝트/00_3차프로젝트_목차]]"
---

# Fluent Bit

> [!abstract]- 프로젝트 로그·관측성 MOC
> ![[00_로그 인프라 전체 흐름#전체 흐름]]

> [!info] 이 노트의 위치
> BANK DVWA Pod가 stdout·stderr로 남긴 Container Log를 Node에서 수집·필터링해 CloudWatch Logs로 전달하는 수집 계층이다.

## 한 줄 정의

Fluent Bit은 여러 Source의 Log를 입력받아 Parse·Filter한 뒤 CloudWatch Logs 같은 Destination으로 보내는 경량 Log Processor·Forwarder다.

## 왜 필요한가

DVWA Container는 AWS API를 호출해 CloudWatch Logs에 직접 기록하지 않는다.

```text
DVWA Application
→ stdout·stderr
→ Node의 Container Log File
→ Fluent Bit DaemonSet
→ CloudWatch Logs
```

DaemonSet을 사용하면 Log Agent Pod가 각 Worker Node에 배치돼 해당 Node의 Container Log를 읽을 수 있다.

## 우리 프로젝트의 설정

`templates/install-cluster-addons.sh.tpl`에서 확인된 Helm 설정:

- Chart: `eks/aws-for-fluent-bit`
- Namespace: `amazon-cloudwatch`
- ServiceAccount: `aws-for-fluent-bit`
- Workload 형태: DaemonSet
- `mergeLog: On`
- Parsed Log 저장 Key: `data`
- 원본 Log 유지: `keepLog: On`
- Kubernetes Namespace Filter: BANK Web Namespace만 허용
- CloudWatch Match: `kube.*`
- Log Group: `/aws/eks/aws-topology-primary/dvwa`
- Log Stream Prefix: `dvwa-`
- Log Group 자동 생성: 비활성
- Resource Request: CPU `25m`, Memory `50Mi`
- Memory Limit: `150Mi`

## AWS 권한

Fluent Bit의 Kubernetes ServiceAccount는 EKS Pod Identity Association으로 전용 IAM Role과 연결된다.

허용된 Action:

```text
logs:CreateLogStream
logs:DescribeLogStreams
logs:PutLogEvents
```

허용 Resource는 DVWA 전용 CloudWatch Log Group의 Stream 범위로 제한된다.

```text
Cluster + amazon-cloudwatch/aws-for-fluent-bit
→ EKS Pod Identity Association
→ DVWA Log Forwarder IAM Role
→ 지정 Log Group에만 Write
```

## Filter의 의미

현재 Additional Filter는 Kubernetes Metadata의 `namespace_name`을 검사해 BANK Web Namespace Log만 통과시킨다.

이 설정의 목적:

- 모든 Namespace의 Container Log가 한 Log Group으로 섞이는 것을 방지
- Application Log 수집량과 비용 제한
- 조사 대상 Scope를 BANK Application으로 고정

## 저장소에서 찾을 곳

- Helm Values·설치: `templates/install-cluster-addons.sh.tpl`
- IAM Role·Pod Identity: `observability.tf`
- Log Group: `foundation/observability.tf`
- Application Query: `observability/queries/cloudwatch/`
- Add-on 실행: `cluster-addons-ssm.tf`

## 직접 확인하는 방법

```powershell
kubectl get namespace amazon-cloudwatch
kubectl get daemonset aws-for-fluent-bit -n amazon-cloudwatch
kubectl get pod -n amazon-cloudwatch -o wide
kubectl describe daemonset aws-for-fluent-bit -n amazon-cloudwatch

# Agent 자체 오류 확인
kubectl logs -n amazon-cloudwatch daemonset/aws-for-fluent-bit --tail=200

# Pod Identity Association
aws eks list-pod-identity-associations `
  --cluster-name aws-topology-primary `
  --region ap-northeast-2

# CloudWatch Log Stream 도착
aws logs describe-log-streams `
  --log-group-name /aws/eks/aws-topology-primary/dvwa `
  --log-stream-name-prefix dvwa- `
  --order-by LastEventTime `
  --descending `
  --region ap-northeast-2
```

검증할 때는 DVWA에 식별 가능한 정상 요청 하나를 발생시키고, UTC 시각과 `request_id`를 기준으로 CloudWatch Logs에서 찾는다.

## 현재 확인 수준

- Helm 설치 방식·Namespace Filter·Output 설정: 확인
- IAM 최소 권한·Pod Identity Association Source: 확인
- 기존 Evidence에는 DVWA Application Event와 Logs Insights Query 결과가 있음
- 최신 DaemonSet Ready 수, Agent Error, Stream 도착: 재확인 필요

## 알려주는 것과 한계

### Fluent Bit이 하는 것

- Log File Tail
- Kubernetes Metadata 결합
- Namespace Filter
- CloudWatch Logs 전송

### Fluent Bit이 하지 않는 것

- 공격 여부 판단
- Application Event 의미 생성
- CloudWatch Logs 장기 분석
- Kubernetes RBAC 또는 AWS IAM 정책 결정

Application이 유용한 JSON Audit Event를 출력하지 않으면 Fluent Bit은 의미를 새로 만들어낼 수 없다.

## 장애 시 확인 순서

```text
1. DVWA Container stdout·stderr에 Event가 있는가
2. Fluent Bit Pod가 해당 Node에서 Running인가
3. Namespace Filter와 Tag가 맞는가
4. Pod Identity Association이 존재하는가
5. IAM Role이 지정 Log Group에 PutLogEvents를 허용하는가
6. Log Group·Stream과 Region이 맞는가
7. Fluent Bit 자체 Log에 Retry·AccessDenied·Throttle이 있는가
```

## 근거

- 현재 저장소: `templates/install-cluster-addons.sh.tpl`, `observability.tf`
- 공식 문서: https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/Container-Insights-EKS-logs.html
- Runtime Evidence: 최신 실행 재확인 필요
