---
type: source-digest
status: stable
created: 2026-07-21
parent_moc: "[[10_학습 노트/클라우드/Kubernetes/00_Kubernetes MOC]]"
source: "[[40_자료/강의 자료/Kubernetes.pdf]]"
source_pages: "8-12"
digest_role: chapter
digest_index: "[[10_학습 노트/클라우드/Kubernetes/Kubernetes - Source Digest v1]]"
chapter: "03 AWS EKS"
source_hash: F97666865E22749C47640689B5C41DEE38476A40312A53915F60B4F6A4330D24
source_version: "PowerPoint PDF; 266 pages; metadata created 2024-07-18"
coverage_status: complete
extraction_method: "pdfplumber 0.11.9 text extraction + pypdfium2 render visual review"
reviewed_on: 2026-07-21
---

# Kubernetes - Source Digest 03 AWS EKS

> [!purpose]
> [[40_자료/강의 자료/Kubernetes.pdf|Kubernetes.pdf]] p.8-p.12의 EKS 설명과 Network·Security·인증 도식을 보존한 Chapter Digest다. 가격·Version·권장 구성의 현재성은 검증하지 않는다.

## Coverage

| Page | Text | Visual | 원본 대조 | 정보 유형 |
|---:|---|---|---|---|
| p.8 | 완료 | 완료 | 완료 | Chapter 표지 |
| p.9 | 완료 | 완료 | 완료 | EKS 개요·Architecture 도식 |
| p.10 | 완료 | 완료 | 완료 | VPC CNI·IP 도식 |
| p.11 | 완료 | 완료 | 완료 | Security Group·Access 경로 도식 |
| p.12 | 완료 | 완료 | 완료 | Authentication·Authorization Sequence |

## p.8 - Elastic Kubernetes Service 표지

- 원자료: [[40_자료/강의 자료/Kubernetes.pdf#page=8|Kubernetes.pdf p.8]]
- `Elastic Kubernetes Service` Chapter의 표지다.
- 별도의 본문·Code·정보성 도식은 없다.

## p.9 - AWS EKS 개요와 Architecture

- 원자료: [[40_자료/강의 자료/Kubernetes.pdf#page=9|Kubernetes.pdf p.9]]

### 원자료 내용

- EKS는 Kubernetes Control Plane을 직접 구성·관리하지 않고 Kubernetes 환경을 실행할 수 있는 완전 관리형 Service라고 설명한다.
- 사용자는 Data Plane 영역만 관리하고 Control Plane은 AWS가 직접 관리한다고 설명한다.
- Kubernetes 접근 Endpoint를 제공받아 해당 주소로 관리 작업을 수행한다고 설명한다.
- 서울 Region 기준 EKS Cluster 비용을 `Cluster × 시간당 $0.10`으로 제시하고 Instance 요금은 별도라고 설명한다.

### 도식·이미지 의미

```text
VPC (Worker Node)
└─ Auto Scaling group
   └─ EC2 Worker Node 4개
      ├─ API Access → Network Load Balancer
      └─ TLS ↔ Elastic Network Interface

VPC (Amazone EKS)
├─ Network LoadBalancer
├─ EKS Control Plane
└─ EKS Endpoints ← EKS User

Elastic Network Interface ↔ EKS Control Plane: Kubectl EXEC
```

- Worker Node VPC와 AWS가 관리하는 EKS VPC를 분리한다.
- User는 EKS Endpoint로 접근하고, Network Load Balancer와 Control Plane이 점선으로 연결된다.
- 원자료에는 `Amazone EKS`, `LoadBalancer`, `Kubectl EXEC` 표기가 사용된다.

## p.10 - AWS EKS VPC CNI

- 원자료: [[40_자료/강의 자료/Kubernetes.pdf#page=10|Kubernetes.pdf p.10]]

### 원자료 내용

- CNI를 Kubernetes 안에서 Pod Network 연결을 담당하는 Open Source Plugin으로 설명하고 EKS 구성 시 함께 자동 구성된다고 적는다.
- EKS에서는 VPC와 CNI가 통합되며 VPC Subnet IP 대역과 Pod가 받는 IP 대역이 같다고 설명한다.
- Security Group, Routing Table, Network ACL 정책을 생성·연결하기 편리하다고 설명한다.
- Worker Node Instance Type에 따라 Pod에 줄 수 있는 IP 주소 개수가 정해지는 것을 한계로 제시한다.

### 도식·이미지 의미

```text
VPC 192.168.0.0/16
├─ Subnet 192.168.10.0/24
│  └─ Worker Node
│     ├─ ENI 192.168.10.9
│     ├─ ENI Secondary IPs 192.168.10.10, 192.168.10.11, ...
│     └─ Pod 192.168.10.10 / Pod 192.168.10.11
└─ Subnet 192.168.20.0/24
   └─ Worker Node
      ├─ ENI 192.168.20.9
      ├─ ENI Secondary IPs 192.168.20.10, 192.168.20.11, ...
      └─ Pod 192.168.20.10 / Pod 192.168.20.11
```

- 각 Pod IP가 Worker Node ENI의 Secondary IP 목록과 대응하는 구조다.
- 두 Subnet의 CNI Icon은 VPC 수준 연결선으로 이어져 있다.

## p.11 - EKS Security Group

- 원자료: [[40_자료/강의 자료/Kubernetes.pdf#page=11|Kubernetes.pdf p.11]]

### 원자료 내용

- `Cluster Security Group`: Control Plane과 Worker Node 사이 모든 통신을 허용하기 위해 생성되는 Security Group으로 설명한다.
- `Control Plane Security Group`: Control Plane Cluster API와 Worker Node 사이 통신을 허용하기 위해 생성되는 Security Group으로 설명한다.
- `Node Security Group`: Worker Node EC2 Instance에 할당되며 CoreDNS와 Cluster API 허용 정책을 설정한다고 설명한다.
- Slide 소제목은 `AWS EKS Security Group (Terraform)`이지만 Terraform Code는 없다.

### 도식·이미지 의미

- VPC(Worker Node) 안에 두 Worker와 각 ENI가 있다.
- Node Security Group `my-eks-node`는 Worker 영역을 감싼다.
- Control Plane SG `my-eks-cluster`는 ENI 영역을 감싼다.
- Cluster Security Group `eks-cluster-sg-"ID"`는 위 영역들을 더 크게 감싼다.
- VPC(EKS)에는 Network Load Balancer, EKS Control Plane, EKS Endpoints가 있다.
- 범례에서 초록색은 `Public Access`, 빨간색은 `Private Access`다.
- EKS User의 Public Access는 Network Load Balancer 방향으로, Private Access는 Worker 측에서 EKS Control Plane 방향으로 표현된다.

## p.12 - EKS Authentication과 Authorization

- 원자료: [[40_자료/강의 자료/Kubernetes.pdf#page=12|Kubernetes.pdf p.12]]

### 원자료 내용

- IAM과 `aws-auth`를 Authentication, Kubernetes RBAC을 Authorization으로 구분한다.
- Diagram Actor는 User, `kubelet`로 표기된 Client Icon, `~/.kube/kubeconfig`, API, `ConfigMap: aws-auth`, AWS IAM, AWS STS, RB, Role이다.

### 도식·이미지 의미

원자료 번호와 방향을 보존하면 다음과 같다.

```text
1. User → Client Icon: K8s Action
2. Client Icon ↔ ~/.kube/kubeconfig: Get Token
3. Client Icon → API: Action + Token
4. API → Authentication 영역: Token Review
5. AWS IAM → AWS STS: STS:GetCallerIdentity
6. AWS STS → AWS IAM: IAM Identity Return
7. aws-auth / AWS IAM: IAM Identity Mapping Check
8. API → RBAC 영역: Role Checking
9. API → Client Icon: Allow / Deny
```

- Authentication 점선 영역은 `ConfigMap: aws-auth`, AWS IAM, AWS STS를 포함한다.
- Authorization 점선 영역은 `rb`와 `role` Icon을 연결하며 `Role-Base Access Control`이라고 표기한다.

### 판독 불확실성

- 원자료 그림의 Client Icon Label은 `kubelet`이다. 이것이 정확한 Component 선택인지 PDF 밖에서 교정하지 않았다.
- 원자료는 `Role-Base Access Control`이라고 표기한다. 일반적으로 쓰이는 용어로 몰래 변경하지 않았다.
- Diagram만으로 5-7단계 내부 호출의 세부 주체를 더 확정하지 않았다.

## 원자료 밖 보충

이 Chapter에는 외부 현재성 검증을 추가하지 않았다. `$0.10`, `aws-auth`, Security Group 구조와 Runtime 표현은 모두 2024-07-18 PDF의 내용으로만 취급한다.

## 완료 검증

- [x] p.8-p.12 모든 Page를 Coverage에 포함했다.
- [x] p.9-p.11의 Network·Security 연결과 수치·Label을 원본과 대조했다.
- [x] p.12의 1-9단계와 Actor를 원본과 대조했다.
- [x] 원자료의 오타·시점 의존 표현을 임의 교정하지 않았다.
- [x] 각 Page에서 PDF 원본으로 역추적할 수 있다.
