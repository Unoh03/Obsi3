---
type: concept
status: draft
created: 2026-07-22
topic: kubernetes
parent_moc: "[[10_학습 노트/클라우드/Kubernetes/00_Kubernetes MOC]]"
source: "[[10_학습 노트/클라우드/Kubernetes/Source Digest/Kubernetes - Source Digest 03 AWS EKS]]"
verified_on: 2026-07-22
aliases:
  - Amazon EKS
  - Elastic Kubernetes Service
---

# AWS EKS

> [!summary]
> **Amazon EKS**는 AWS가 Kubernetes Control Plane의 설치·고가용성·복구·확장을 관리해 주는 Service다. 사용자는 EKS가 제공하는 Kubernetes API에 접속해 Application을 배포하며, 선택한 Compute 방식과 Workload·권한·Network·보안 설정은 여전히 직접 책임진다.

## EKS를 왜 사용하는가

Kubernetes를 직접 운영하려면 API Server, etcd, Scheduler, Controller Manager 같은 Control Plane Component를 설치하고 여러 Server에 분산해야 한다. 장애가 발생하면 복구하고 Version도 계속 관리해야 한다.

EKS를 사용하면 AWS가 이 Control Plane 운영을 맡는다.

```text
직접 구성한 Kubernetes
사용자 → Control Plane 운영 + Worker Node 운영 + Workload 운영

EKS Standard
AWS    → Control Plane 운영
사용자 → Compute 선택 + Workload와 Cluster 설정 운영
```

EKS도 Kubernetes이므로 Pod, Deployment, Service, RBAC 같은 Kubernetes Object와 `kubectl` 사용법은 그대로 적용된다. EKS는 Kubernetes를 없애는 Service가 아니라 **Kubernetes를 AWS에서 운영하기 쉽게 제공하는 Managed Service**다.

## AWS가 관리하는 것과 사용자가 관리하는 것

### AWS가 관리하는 영역

- Kubernetes API Server와 etcd를 포함한 Control Plane
- Control Plane의 고가용성, 감시, 장애 Instance 교체와 확장
- Cluster마다 분리된 Kubernetes API endpoint
- 지원하는 Kubernetes Version과 Control Plane Upgrade 경로

AWS 공식 Architecture 문서 기준으로 EKS Control Plane은 최소 두 개의 API Server Instance와 세 개의 etcd Instance를 세 Availability Zone에 분산한다.

### 사용자가 계속 책임지는 영역

- 누가 Cluster에 접근할 수 있는지 정하는 IAM·EKS Access·RBAC
- Pod, Deployment, Service와 Application 설정
- Container Image, Secret, Runtime와 Supply Chain 보안
- Network Policy, Security Group, Endpoint 공개 범위
- Log, Monitoring, Backup, Incident Response
- Worker Node 방식과 크기, Add-on Version, 비용 관리

Managed Node Group을 사용하면 Node의 생성·교체·Upgrade 일부를 AWS가 도와준다. EKS Auto Mode나 Fargate를 사용하면 AWS의 관리 범위가 더 넓어지므로, “EKS 사용자는 항상 Data Plane 전체를 직접 관리한다”라고 단정하면 안 된다.

## EKS에 접속할 때 거치는 두 권한 체계

EKS 접근은 **AWS IAM** 하나로 끝나지 않는다. 먼저 AWS Identity를 확인하고, 그 Identity가 Kubernetes에서 무엇을 할 수 있는지도 결정해야 한다.

```text
AWS Credential
→ aws eks get-token
→ EKS Kubernetes API endpoint
→ Authentication: 누구인가?
→ EKS Access Entry 또는 legacy aws-auth mapping
→ Authorization: 무엇을 할 수 있는가?
→ EKS Access Policy 또는 Kubernetes RBAC
→ 허용 / 거부
```

### Authentication: 누구인지 확인

`kubectl`은 kubeconfig의 설정에 따라 `aws eks get-token`으로 짧게 사용하는 인증 Token을 얻는다. EKS는 이 Token의 AWS IAM Identity를 확인한다.

AWS Console이나 EKS API를 볼 IAM 권한이 있다고 해서 Kubernetes API에서 모든 Object를 다룰 수 있는 것은 아니다.

### Authorization: 무엇을 할 수 있는지 결정

인증된 IAM Principal은 다음 방식으로 Kubernetes 권한과 연결할 수 있다.

- 현재 권장 방식: **EKS Access Entry**와 EKS Access Policy 또는 Kubernetes Group·RBAC 연결
- 기존 방식: `aws-auth` ConfigMap에 IAM Role·User를 Kubernetes Group과 연결

AWS는 `aws-auth` ConfigMap 방식을 legacy로 분류하고 Access Entry 사용을 안내한다. 기존 Cluster와 강의 실습에서는 두 방식이 함께 보일 수 있다.

> [!important]
> 사람, Worker Node, Pod가 사용하는 AWS 권한은 서로 분리해서 생각한다.
>
> - 사람·관리 도구: Cluster API에 접속할 IAM Role
> - Worker Node: Node 등록과 ECR Image Pull 등에 필요한 Node IAM Role
> - Pod: AWS Service를 호출할 때 EKS Pod Identity 또는 IRSA로 부여하는 Workload Role

## EKS Network를 보는 기본 틀

### Control Plane 연결

EKS는 Cluster마다 Kubernetes API endpoint를 만든다.

- Public endpoint: Internet에서 endpoint까지 도달 가능
- Private endpoint: VPC 내부에서 EKS 관리 ENI를 통해 접근
- 둘 다 활성화: VPC 내부 경로와 Public 경로를 함께 제공

Public endpoint가 있다고 곧바로 익명 접근이 가능한 것은 아니다. Endpoint에 도달한 뒤에도 IAM Authentication과 Kubernetes Authorization을 통과해야 한다. 그래도 공격 표면을 줄이려면 Public access CIDR을 제한하거나 운영 환경에서 Private access 중심 구성을 검토한다.

### Pod IP와 VPC CNI

Amazon VPC CNI는 EC2 Node의 ENI와 Subnet IP를 사용해 Pod에 VPC에서 통신 가능한 IP를 배정한다.

```text
VPC Subnet
└─ EC2 Worker Node
   ├─ ENI와 IP Pool
   ├─ Pod A → VPC IP
   └─ Pod B → VPC IP
```

이 구조는 Pod를 VPC Routing과 연결하기 쉽지만 다음 한계도 만든다.

- Subnet의 남은 IP가 부족하면 새 Pod 배치가 막힐 수 있다.
- EC2 Instance Type마다 연결 가능한 ENI와 IP 수가 다르다.
- CPU·Memory가 남아도 Pod에 줄 IP가 부족하면 더 배치하지 못할 수 있다.
- 기본적으로 Pod는 Node의 Security Group 영향을 받으며, 별도 기능으로 Pod별 Security Group을 구성할 수도 있다.

Security Group만으로 Kubernetes 내부 통신 정책이 모두 해결되는 것은 아니다. Namespace·Pod 단위 통신 통제에는 Kubernetes NetworkPolicy와 CNI 지원 여부도 함께 본다.

## 현재 실습 환경에서 확인한 모습

2026-07-22 읽기 전용 확인 결과는 다음과 같다.

| 항목 | 확인된 값 | 의미 |
|---|---|---|
| Cluster | `my-eks`, `ACTIVE` | EKS Control Plane 사용 가능 |
| Kubernetes | `1.35` | 현재 실습 Cluster Version |
| API endpoint | Public·Private 모두 활성화 | 두 접근 경로를 함께 사용 |
| 인증 모드 | `API_AND_CONFIG_MAP` | Access Entry API와 `aws-auth` 호환 경로 병행 |
| Worker Node | 2대, 모두 `Ready` | Managed Node Group의 Data Plane 정상 |
| Container Runtime | `containerd` | Worker Node에서 Container 실행 |
| VPC CNI | `aws-node` 2/2 Ready | 두 Node에서 Pod Network Add-on 동작 |

현재 Terraform은 `aws eks get-token --profile terra-user`로 Local Kubernetes Provider를 인증하고, Bastion에는 별도 `admin` Profile로 kubeconfig를 만든다. Profile 이름은 위치마다 다르지만 결국 **어떤 AWS IAM Identity로 Token을 발급받는가**가 핵심이다.

## 처음부터 알아두면 좋은 실무·보안 팁

### 장기 Access Key를 Server 초기화 Script에 넣지 않는다

현재 실습은 흐름을 배우기 위해 Access Key를 Terraform 변수와 Bastion Profile에 사용한다. 실제 운영에서는 장기 IAM User Key보다 IAM Role, Federation, IAM Identity Center처럼 임시 Credential을 우선한다.

User data와 Terraform State에는 입력한 값이 남을 수 있으므로 실제 Secret을 직접 주입하는 설계는 피한다.

### AWS IAM 권한과 Kubernetes RBAC을 모두 최소화한다

IAM에서 넓은 권한을 주고 Kubernetes에서 `cluster-admin`까지 부여하면 한 Identity가 AWS와 Cluster 양쪽을 모두 장악할 수 있다. 사람·자동화·Node·Pod의 Role을 나누고 필요한 작업만 허용한다.

### Public endpoint의 허용 범위를 확인한다

Public endpoint를 사용하는 Lab은 편리하지만 운영 환경에서는 허용 CIDR, Private endpoint, Bastion·VPN 경로를 함께 설계한다. Endpoint 접근 제한과 IAM·RBAC은 서로 대체 관계가 아니라 겹쳐 쓰는 방어 계층이다.

### VPC CNI와 Subnet IP도 Capacity다

Pod가 늘어날 때 CPU와 Memory만 계산하지 않는다. Subnet 가용 IP, Node별 ENI·IP 한도, VPC CNI 설정도 함께 확인한다.

### EKS Cluster 자체에도 시간당 비용이 있다

2026-07-22 AWS 공식 가격 기준으로 Standard Kubernetes Version 지원 Cluster는 시간당 `$0.10`, Extended Support Version은 시간당 `$0.60`이다. 여기에 EC2, EBS, Load Balancer, NAT, Public IPv4 같은 Resource 비용이 별도로 붙을 수 있다.

실습 종료 때 Cluster와 관련 Resource를 함께 제거하고, State만 보고 끝내지 말고 AWS API로 잔존 Resource를 확인한다.

## 강의자료와 현재 기준의 차이

- 강의자료는 사용자가 Data Plane만 관리한다고 단순화한다. EKS Standard의 기본 그림으로는 유용하지만 Managed Node Group, Fargate, EKS Auto Mode에 따라 AWS의 관리 범위가 달라진다.
- 강의자료의 `aws-auth` ConfigMap은 기존 Cluster에서 여전히 볼 수 있지만, 신규 접근 관리의 현재 권장 경로는 EKS Access Entry다.
- 강의자료는 Cluster·Control Plane·Node Security Group을 고정된 세 종류처럼 설명한다. 현재 공식 문서는 EKS가 만드는 Default Cluster Security Group과 사용자가 추가하는 Security Group, Node Group 연결 방식을 기준으로 설명한다.
- 강의자료의 Standard Support Cluster 시간당 `$0.10`은 현재도 맞다. 다만 Extended Support에는 더 높은 Cluster 요금이 적용된다.
- 강의 p.12의 `Role-Base Access Control`은 일반적으로 **Role-Based Access Control**이라고 부른다.

## 지금은 이것만 기억한다

```text
EKS
= AWS가 Control Plane 운영을 맡는 Kubernetes

IAM Authentication
= AWS 관점에서 누구인지 확인

EKS Access / Kubernetes RBAC
= Cluster 안에서 무엇을 할 수 있는지 결정

VPC CNI
= Pod를 VPC IP와 연결

Managed Service
≠ 보안과 운영 책임이 모두 AWS로 넘어감
```

## 정보 출처

- **강의 원자료**: [[Source Digest/Kubernetes - Source Digest 03 AWS EKS]] — `Kubernetes.pdf` p.8-p.12
- **Local primary evidence**: `aws eks describe-cluster`, `kubectl get nodes -o wide`, `kubectl -n kube-system get daemonset aws-node`, `D:\terraform\workspace\00_eks\main.tf`의 2026-07-22 상태
- **Authoritative external evidence**: 아래 AWS 공식 문서
- **Informal external evidence**: 사용하지 않음
- **Parametric knowledge**: 입문 설명의 순서와 비유에만 사용

## 공식 문서

- [What is Amazon EKS?](https://docs.aws.amazon.com/eks/latest/userguide/)
- [Amazon EKS architecture](https://docs.aws.amazon.com/eks/latest/userguide/eks-architecture.html)
- [Cluster API server endpoint](https://docs.aws.amazon.com/eks/latest/userguide/cluster-endpoint.html)
- [Amazon VPC CNI](https://docs.aws.amazon.com/eks/latest/best-practices/vpc-cni.html)
- [EKS access entries](https://docs.aws.amazon.com/eks/latest/userguide/access-entries.html)
- [EKS cluster security group requirements](https://docs.aws.amazon.com/eks/latest/userguide/sec-group-reqs.html)
- [Amazon EKS security best practices](https://docs.aws.amazon.com/eks/latest/best-practices/security.html)
- [Amazon EKS pricing](https://aws.amazon.com/eks/pricing/)
