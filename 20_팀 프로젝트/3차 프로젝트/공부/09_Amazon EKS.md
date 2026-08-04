---
type: project-doc
status: draft
study_status: not-started
created: 2026-08-04
project: 3차 프로젝트
project_moc: "[[20_팀 프로젝트/3차 프로젝트/00_3차프로젝트_목차]]"
---
# Amazon EKS

## 한 줄 정의

Amazon EKS는 **AWS가 Kubernetes Control Plane을 관리하고, 사용자가 AWS의 컴퓨팅·네트워크·스토리지 위에 컨테이너 워크로드를 배포하도록 제공하는 관리형 Kubernetes 서비스**다.

> [!summary]
> 강의자료는 `AWS가 Control Plane을 관리하고 사용자가 Data Plane을 관리한다`고 설명한다. 이는 현재 프로젝트처럼 EKS Standard와 EC2 Node를 사용하는 구성에는 대체로 맞는다. 다만 현재는 AWS가 Node까지 관리 범위를 확장하는 **EKS Auto Mode**도 존재한다. 우리 프로젝트는 Auto Mode가 아니라 Managed Node Group과 Karpenter를 사용한다. 

## 보편적·일반적인 역할

Kubernetes를 직접 구축하려면 API Server, etcd, Scheduler, Controller Manager와 같은 Control Plane 구성요소를 설치하고 고가용성·백업·업그레이드·장애 복구를 관리해야 한다.

Amazon EKS는 이 Control Plane을 AWS 관리 영역에서 운영한다. 현재 EKS Control Plane은 리전 내 3개 가용 영역에 걸쳐 최소 2개의 API Server와 3개의 etcd Instance를 배치하며, 장애가 발생한 Control Plane Instance를 AWS가 교체한다. 사용자는 EKS가 제공하는 Kubernetes API Endpoint를 통해 `kubectl`, Helm, Argo CD 등의 도구로 클러스터를 관리한다. 

EKS 자체가 모든 애플리케이션 실행 자원을 제공하는 것은 아니다. Pod가 실제로 실행될 컴퓨팅 환경은 다음과 같은 별도 선택지가 담당한다.

- EKS Managed Node Group
- Karpenter가 생성한 EC2 Node
- Self-managed Node
- AWS Fargate
- EKS Auto Mode Node

우리 프로젝트에서는 **Managed Node Group을 기본 System Node로 사용하고, Application Node는 Karpenter가 동적으로 공급**한다.

## 핵심 구성요소

### Control Plane

AWS가 관리하는 Kubernetes의 중앙 관리 영역이다.

- **API Server**: `kubectl`, Controller, Node가 Kubernetes API를 호출하는 진입점
- **etcd**: Kubernetes Object의 원하는 상태와 현재 상태를 저장하는 분산 Key-Value Store
- **Scheduler**: 새 Pod를 어느 Node에 배치할지 결정
- **Controller Manager**: Deployment, ReplicaSet, Node 등의 실제 상태를 원하는 상태에 맞춤

### Data Plane 또는 Compute

Pod가 실제로 실행되는 영역이다.

- **Node**: 컨테이너를 실행하는 EC2 Instance 등의 컴퓨팅 자원
- **kubelet**: Node에서 Pod와 Container 상태를 관리
- **Container Runtime**: 실제 Container 실행
- **kube-proxy**: Kubernetes Service 통신에 필요한 네트워크 규칙 관리

EKS Managed Node Group은 EC2 Instance와 Auto Scaling Group의 생성·업데이트·종료 및 Node Drain 과정을 자동화한다. Managed Node Group 사용 자체의 별도 추가 요금은 없으며 EC2, EBS 등의 실제 AWS 자원 비용을 지불한다. 

### Cluster API Endpoint

사용자와 Node가 Kubernetes API Server에 접근하는 주소다.

Endpoint 접근 방식은 다음과 같다.

- Public Endpoint
- Private Endpoint
- Public + Private Endpoint

우리 프로젝트는 다음과 같이 구성한다.

```hcl
endpoint_private_access = true
endpoint_public_access  = false
```

따라서 인터넷에서 직접 `kubectl`로 접근할 수 없으며, VPC 내부 또는 연결된 네트워크를 통해 접근해야 한다. 현재 프로젝트에서는 SSM Bastion이 접근 경로 역할을 한다. 

### EKS Add-on

Kubernetes가 AWS 자원과 연동하거나 기본 기능을 수행하도록 돕는 운영 구성요소다.

우리 프로젝트에서 사용하는 주요 Add-on은 다음과 같다.

- **Amazon VPC CNI**: Pod에 VPC의 Private IP 할당
- **CoreDNS**: Cluster 내부 DNS와 Service Discovery
- **kube-proxy**: Service 네트워크 규칙
- **EKS Pod Identity Agent**: ServiceAccount와 IAM Role 연결 지원
- **AWS EFS CSI Driver**: Pod가 EFS Volume을 Mount하도록 지원

VPC CNI는 EC2 Node에 ENI를 연결하고 Pod에 VPC 대역의 Private IP를 할당한다. 

### 인증과 권한

EKS 접근에는 서로 다른 두 권한 체계가 관여한다.

```text
AWS IAM Identity
→ EKS 인증
→ Kubernetes 권한 확인
→ API 요청 허용 또는 거부
```

강의자료 p.12는 `IAM + aws-auth ConfigMap → Kubernetes RBAC` 구조로 설명한다. 현재 EKS에서는 **Access Entry**가 IAM Principal에게 Kubernetes API 권한을 부여하는 권장 방식이며, 우리 프로젝트도 Access Entry를 사용한다.  

## 입력과 출력

- 입력:
  - Kubernetes Version
  - VPC와 Private Subnet
  - Cluster Endpoint 공개 범위
  - Cluster·Node Security Group
  - IAM Role과 EKS Access Entry
  - Managed Node Group의 Instance Type과 수량
  - EKS Add-on 설정
  - Helm Chart와 Kubernetes Manifest
  - Deployment, Service, ConfigMap, Secret 등의 Kubernetes Object

- 출력:
  - Kubernetes API Endpoint
  - AWS 관리형 Control Plane
  - 클러스터에 등록된 Node
  - Node에 배치된 Pod와 Container
  - Service·DNS·Volume 등 Kubernetes Resource
  - API·Audit·Authenticator Control Plane Log
  - Controller를 통해 생성되는 ALB, Route 53 Record 등의 AWS Resource
  - 클러스터와 Node의 상태 정보

EKS에 Manifest를 입력했다고 해서 항상 Pod가 정상 실행되는 것은 아니다. Scheduler가 적절한 Node를 찾지 못하거나, Image Pull·IAM·Network·Volume·Probe 조건에 문제가 있으면 `Pending`, `ImagePullBackOff`, `CrashLoopBackOff` 등의 상태가 발생한다.

## 우리 프로젝트에서의 역할

우리 프로젝트의 EKS는 **BANK DVWA 애플리케이션과 Kubernetes 운영 구성요소를 실행하는 중심 플랫폼**이다.

### Primary Cluster

```text
이름: aws-topology-primary
리전: ap-northeast-2
Subnet: Primary VPC Private Subnet
API Endpoint: Private Only
```

Primary Cluster에는 다음 구성이 존재한다.

- `workload=system` Label을 가진 EKS Managed Node Group
- Application Node를 생성하는 Karpenter
- VPC CNI, CoreDNS, kube-proxy
- EKS Pod Identity Agent
- 조건부 EFS CSI Driver
- AWS Load Balancer Controller
- ExternalDNS
- Fluent Bit
- Argo CD
- DVWA 애플리케이션

### DR Cluster

Runtime Profile에 따라 Tokyo Region의 DR EKS Cluster를 조건부로 생성한다.

```text
이름: aws-topology-dr
리전: ap-northeast-1
생성 조건: enable_dr_runtime
```

### 접근 제어

Primary와 DR 모두 Bastion IAM Role에 EKS Access Entry를 연결한다.

```text
Bastion IAM Role
→ EKS Access Entry
→ AmazonEKSClusterAdminPolicy
→ kubectl 관리 가능
```

Bastion Security Group에서 EKS Private API Endpoint의 TCP 443 접근을 허용한다.

### 컴퓨팅 분리

```text
Managed Node Group
└─ workload=system
   ├─ Karpenter
   ├─ AWS Load Balancer Controller
   ├─ ExternalDNS
   └─ 기타 운영 Controller

Karpenter Node
└─ workload=application
   └─ DVWA와 Application Workload
```

현재 `eks.tf`는 Primary·DR Cluster, System Managed Node Group, Add-on, Karpenter IAM·Helm 구성을 정의한다. `cluster-controllers.tf`는 AWS Load Balancer Controller와 ExternalDNS의 Pod Identity 및 Helm 배포를 정의한다.  

### 로그

우리 프로젝트는 다음 EKS Control Plane Log를 활성화한다.

- `api`
- `audit`
- `authenticator`

다음 두 Log는 현재 활성 목록에 없다.

- `controllerManager`
- `scheduler`

Control Plane Log는 CloudWatch Logs로 전달되며, Kubernetes API 호출·사용자 행위·IAM 인증 문제를 조사하는 데 사용한다. EKS Control Plane Log는 수분 정도 지연될 수 있으며 전달은 Best Effort이므로, 특정 Event가 없다는 사실만으로 행위가 없었다고 단정해서는 안 된다. 

## 다른 서비스와의 연결

### 클러스터 생성과 접근

```text
Terraform
→ VPC·Private Subnet
→ Amazon EKS
→ Private API Endpoint
→ SSM Bastion
→ kubectl·Helm
```

### 애플리케이션 배포

```text
GitHub Actions
→ Amazon ECR
→ Argo CD
→ EKS Deployment
→ Pod
```

### 외부 요청

```text
CloudFront
→ AWS WAF
→ ALB
→ TargetGroupBinding
→ EKS Service
→ DVWA Pod
```

### Node 확장

```text
Pending Pod
→ Karpenter
→ EC2 Node 생성
→ Node가 EKS에 Join
→ Scheduler가 Pod 배치
```

### AWS API 권한

```text
Kubernetes ServiceAccount
→ EKS Pod Identity
→ IAM Role
→ AWS API
```

예:

```text
AWS Load Balancer Controller
→ Pod Identity
→ ELB API
→ ALB·Target Group 관리
```

### 스토리지

```text
Pod
→ EFS CSI Driver
→ Amazon EFS
```

### 로그

```text
DVWA Container stdout·stderr
→ Fluent Bit DaemonSet
→ CloudWatch Logs
```

```text
Kubernetes API 요청
→ EKS Control Plane
→ API·Audit·Authenticator Log
→ CloudWatch Logs
```

## 비용과 수명주기

### EKS Cluster 비용

현재 EKS Cluster 요금은 Kubernetes Version의 Support Tier에 따라 달라진다.

| Support Tier | Cluster 시간당 요금 |
|---|---:|
| Standard Support | USD 0.10 |
| Extended Support | USD 0.60 |

Kubernetes Version은 EKS 출시 후 처음 14개월 동안 Standard Support를 받고, 이후 12개월 동안 Extended Support로 전환된다. Cluster에 Pod가 없어도 EKS Cluster가 존재하는 동안 Cluster 시간 요금은 발생한다. 

### 별도 발생 비용

EKS Cluster 비용과 별도로 다음 비용이 발생할 수 있다.

- Managed Node Group과 Karpenter Node의 EC2 비용
- Node EBS Volume
- NAT Gateway 또는 NAT Instance
- ALB
- Public IPv4
- CloudWatch Logs 저장·조회
- EFS
- Data Transfer

### 우리 프로젝트의 수명주기

우리 프로젝트에서 EKS는 Persistent Foundation이 아니라 Daily Runtime Terraform Root에 정의돼 있다. 따라서 현재 구조상 `daily-up`에서 생성되고 `daily-down`에서 제거되는 일일 Runtime 대상이다.

반면 ECR, Security Log Bucket, CloudTrail 등은 별도 Foundation에 유지된다. 이는 Runtime 제거 후에도 Image와 보안 증거를 보존하기 위한 분리다. 이 부분은 현재 저장소 구조에 근거한 판단이며, 실제 `daily-down` 실행 시 어떤 EKS 연계 자원이 남는지는 Runtime 검증이 필요하다.

## 우리 저장소에서 찾을 곳

- Terraform:
  - `eks.tf`
    - Primary·DR EKS Cluster
    - Managed Node Group
    - EKS Add-on
    - Karpenter IAM·Helm 구성
  - `cluster-controllers.tf`
    - AWS Load Balancer Controller
    - ExternalDNS
    - 각 Controller의 Pod Identity
  - `cluster-addons-ssm.tf`
    - SSM을 통한 Cluster Add-on 설치
  - `securitygroups.tf`
    - Bastion·Node·ALB 등의 통신 규칙
  - `observability.tf`
    - EKS와 Application Log 수집 구성
  - `target-group-binding.tf`
    - ALB Target Group과 EKS Service 연결

- Helm·Kubernetes:
  - `charts/karpenter-node-config/`
  - `templates/install-cluster-addons.sh.tpl`
  - `Uns-DVWA/deploy/dvwa/`
  - `Uns-DVWA/deploy/argocd/`

- Script:
  - `daily-up.ps1`
  - `daily-down.ps1`
  - `daily-common.ps1`
  - `templates/install-cluster-addons.sh.tpl`
  - DVWA의 Argo CD Bootstrap Script

- Query:
  - `observability/queries/cloudwatch/03_kubectl_exec_and_secret_access.cwli`
  - EKS Control Plane Log Group:
    - `/aws/eks/aws-topology-primary/cluster`

- Application:
  - `Unoh03/Uns-DVWA`
  - DVWA Deployment·Service·Helm Chart
  - DVWA Audit Log Code

## 직접 확인하는 방법

### AWS Console

```text
AWS Console
→ Amazon EKS
→ Clusters
→ aws-topology-primary
```

주요 확인 위치:

- **Overview**: Cluster 상태, Kubernetes Version, API Endpoint
- **Compute**: Managed Node Group과 Node
- **Add-ons**: VPC CNI, CoreDNS, kube-proxy, Pod Identity Agent
- **Networking**: VPC, Subnet, Security Group, Endpoint 접근 방식
- **Access**: Access Entry와 연결된 Policy
- **Observability**: 활성화된 Control Plane Log

### CLI

```bash
aws eks describe-cluster \
  --name aws-topology-primary \
  --region ap-northeast-2
```

```bash
aws eks list-nodegroups \
  --cluster-name aws-topology-primary \
  --region ap-northeast-2
```

```bash
aws eks list-addons \
  --cluster-name aws-topology-primary \
  --region ap-northeast-2
```

```bash
aws eks list-access-entries \
  --cluster-name aws-topology-primary \
  --region ap-northeast-2
```

API Endpoint가 Private Only이므로 `aws eks describe-cluster` 같은 AWS API 조회는 로컬에서도 가능하지만, 실제 `kubectl` 통신은 VPC 내부 또는 연결된 환경에서 수행해야 한다.

### Kubernetes

SSM Bastion에서 실행:

```bash
kubectl cluster-info
```

```bash
kubectl get nodes -o wide
```

```bash
kubectl get pods -A -o wide
```

```bash
kubectl get deployment,statefulset,daemonset -A
```

```bash
kubectl get events -A \
  --sort-by=.metadata.creationTimestamp
```

```bash
kubectl auth can-i --list
```

```bash
kubectl get ec2nodeclass,nodepool
```

### 기타

CloudWatch Logs에서 EKS Control Plane Log 확인:

```text
/aws/eks/aws-topology-primary/cluster
```

확인할 항목:

- Kubernetes API 호출
- `kubectl exec`
- Secret 접근
- 인증 실패
- IAM Principal과 Kubernetes User Mapping
- API 요청의 허용·거부 결과

## 직접 확인한 결과

### 저장소에서 확인

- Primary와 DR EKS Cluster가 Terraform으로 정의돼 있다.
- 두 Cluster 모두 Private Endpoint만 사용한다.
- Bastion Role이 Access Entry를 통해 Cluster Admin 권한을 받는다.
- System Managed Node Group은 `workload=system` Label을 사용한다.
- Karpenter가 Application Node 공급을 담당하도록 구성돼 있다.
- `api`, `audit`, `authenticator` Control Plane Log가 활성화돼 있다.
- VPC CNI, CoreDNS, kube-proxy, Pod Identity Agent가 Add-on으로 구성돼 있다. 

### Runtime Evidence에서 확인

2026-08-04 Add-on 설치 출력에서는 다음 사실이 확인됐다.

- `aws-topology-primary` Context가 `/root/.kube/config`에 추가됨
- Kubernetes Control Plane Endpoint 응답 확인
- Karpenter Helm Release 배포
- AWS for Fluent Bit 배포
- AWS Load Balancer Controller 배포
- ExternalDNS 배포
- Argo CD 배포
- 초기 `EC2NodeClass` 적용 시 제한된 `kubernetes.io/cluster/` Tag 때문에 검증 실패

해당 Tag는 이후 Template에서 제거됐지만, 수정된 `EC2NodeClass`와 NodePool이 실제 Runtime에서 정상 생성됐는지는 다시 확인해야 한다. 

### 아직 직접 확인하지 않은 것

- 현재 AWS 계정에 Cluster가 실제로 존재하는지
- 현재 Kubernetes Version
- 전체 Node와 Pod의 `Ready` 상태
- Karpenter Node 생성 성공 여부
- DR Cluster의 실제 생성 여부
- Control Plane Log가 현재 정상 수집되는지
- `daily-down` 후 EKS 연계 자원이 모두 제거되는지

## 이 구성요소가 알려주는 것과 한계

- 확인할 수 있는 것:
  - Cluster가 정상 상태인지
  - 어떤 Node가 Cluster에 등록됐는지
  - Pod가 어느 Node에 배치됐는지
  - Deployment가 원하는 Replica 수를 유지하는지
  - Pod가 `Pending`, `Running`, `CrashLoopBackOff` 중 어떤 상태인지
  - Kubernetes API에서 누가 어떤 Object에 접근했는지
  - IAM 인증이 성공 또는 실패했는지
  - Add-on과 Controller가 정상 실행되는지
  - Resource 부족이나 Scheduling 조건 때문에 Pod 배치가 실패했는지

- 이것만으로는 확인할 수 없는 것:
  - WAF Rule이 어떤 HTTP 요청과 일치했는지
  - ALB가 어떤 Client 요청을 어떤 Target으로 전달했는지
  - 사용자의 로그인이나 SQL Injection이 실제로 성공했는지
  - AWS IAM·Security Group·S3 Policy가 누가 변경했는지
  - Network Packet의 실제 Payload
  - VPC에서 특정 연결이 `ACCEPT` 또는 `REJECT`된 전체 내역
  - 애플리케이션 내부의 업무 의미와 처리 결과

따라서 EKS 상태와 Audit Log만으로 보안 사건 전체를 판정할 수 없다.

```text
EKS Audit Log
+ Application Audit Log
+ WAF Log
+ ALB Access Log
+ CloudTrail
+ VPC Flow Log
= 사건의 전체 흐름에 가까워짐
```

## 아직 모르는 것

- [ ] 현재 설정된 `kubernetes_version`의 실제 값과 Support Tier
- [ ] EKS Control Plane과 Worker Node가 통신할 때 생성되는 ENI의 구체적 역할
- [ ] `api`, `audit`, `authenticator` Log의 실제 Event 구조 차이
- [ ] `controllerManager`, `scheduler` Log를 비활성화한 정확한 이유
- [ ] Access Entry Policy와 Kubernetes RBAC가 충돌할 때 최종 권한 계산 방식
- [ ] Karpenter Node와 Managed Node Group을 함께 사용할 때 Scheduling 우선순위
- [ ] Pod Identity Agent가 Credential을 Pod에 전달하는 상세 과정
- [ ] VPC CNI의 ENI·Secondary IP와 최대 Pod 수 계산 방식
- [ ] DR Runtime Profile별 Cluster 생성·삭제 조건
- [ ] EKS Version Upgrade 절차와 Add-on Version 호환성
- [ ] Cluster 삭제 시 ALB, ENI, EBS 등의 종속 자원이 남는 조건

## 근거

- 강의자료:
  - `Kubernetes.pdf`
  - p.4~7: Kubernetes Architecture
  - p.8~12: EKS Architecture, VPC CNI, Security Group, 인증·인가
  - p.187~197: ServiceAccount, RBAC, EKS 인증·인가, IRSA
  - p.198~212: Ingress와 AWS Load Balancer Controller
  - p.251~261: HPA와 Cluster Autoscaler
  - p.266: Karpenter 

- 공식 문서:
  - Amazon EKS Architecture 
  - EKS API Server Endpoint 
  - EKS Control Plane Logging 
  - EKS Managed Node Groups 
  - EKS Access Entries 
  - Amazon VPC CNI 
  - Amazon EKS Pricing 

- 현재 저장소:
  - `bank-security-lab-infra/eks.tf` 
  - `bank-security-lab-infra/cluster-controllers.tf` 
  - `bank-security-lab-infra/templates/install-cluster-addons.sh.tpl` 
  - `bank-security-lab-infra/observability.tf` 

- Runtime Evidence:
  - `ssm-addons-output.txt`
  - 2026-08-04 Add-on 설치 및 `EC2NodeClass` 오류 출력