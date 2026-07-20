---
type: source-digest
status: draft
created: 2026-07-20
parent_moc: "[[10_학습 노트/클라우드/Kubernetes/00_Kubernetes MOC]]"
source: "[[40_자료/강의 자료/Kubernetes.pdf]]"
source_pages: "1-266"
extraction_method: "pdfplumber text extraction + pypdfium2 visual review"
reviewed_on: 2026-07-20
tags:
  - 과목/클라우드
  - 주제/Kubernetes
  - 주제/EKS
---

# Kubernetes - Source Digest v1

> [!summary]
> 원자료의 범위·페이지·도식·불확실성을 보존하는 중간 산출물이다. 완성된 concept note나 공식 문서 검증본이 아니다. 전체 266쪽의 Section Map을 먼저 만들고, 현재 수업 범위인 p.1-p.12만 상세 Digest로 작성했다.

## Source 범위

| 항목 | 내용 |
|---|---|
| 원자료 | [[40_자료/강의 자료/Kubernetes.pdf|Kubernetes.pdf]] |
| 전체 범위 | p.1-p.266 |
| 현재 상세 검수 | p.1-p.12 |
| 현재 색인만 완료 | p.13-p.266 |
| 추출 방식 | `pdfplumber` Text 추출 + 주요 페이지 Rendering 육안 검토 |
| 외부 검증 | 아직 수행하지 않음 |
| 제외 범위 | `boot.zip` Source Code 전문, 실제 EKS 구축·실행 결과 |

## Source Digest의 역할

이 문서는 PDF 내용을 짧은 요약으로 대체하지 않는다.

```text
PDF 원문
→ Page·Section 위치 보존
→ Text와 Visual 의미 색인
→ OCR·시점·표현 불확실성 표시
→ 후속 concept / lab 노트 후보 분리
```

- PDF에 적힌 내용은 `원문 사실`로 기록한다.
- 현재 Kubernetes·AWS 동작에 대한 판단은 공식 문서 검증 전까지 섞지 않는다.
- 오래된 명칭·Version·가격은 임의로 최신화하지 않고 `검토 필요`로 남긴다.
- 도식은 PDF Page Link를 최종 기준으로 삼아 이미지 복제를 피한다.

## Coverage

| 구간 | 주제 | 처리 상태 | 비고 |
|---:|---|---|---|
| p.1-p.3 | Container Orchestration·가상화 | 상세 검수 | 현재 수업 범위 |
| p.4-p.7 | Kubernetes Architecture | 상세 검수 | 현재 수업 범위 |
| p.8-p.12 | AWS EKS Architecture·CNI·Security·인증 | 상세 검수 | 현재 수업 범위 |
| p.13-p.73 | Pod·ReplicaSet | 색인 완료 / 상세 대기 | Manifest, Label, Scheduling 포함 |
| p.74-p.109 | Deployment | 색인 완료 / 상세 대기 | Rollout·Rollback·Namespace 포함 |
| p.110-p.134 | Service | 색인 완료 / 상세 대기 | ClusterIP·NodePort·ExternalName·LoadBalancer |
| p.135-p.160 | ConfigMap·Secret | 색인 완료 / 상세 대기 | 환경변수·Volume·TLS 포함 |
| p.161-p.171 | Pod Health Check | 색인 완료 / 상세 대기 | Liveness·Readiness Probe |
| p.172-p.186 | Resource Management | 색인 완료 / 상세 대기 | Request·Limit·Quota·LimitRange |
| p.187-p.197 | ServiceAccount·RBAC | 색인 완료 / 상세 대기 | EKS IAM·IRSA 포함 |
| p.198-p.212 | Ingress | 색인 완료 / 상세 대기 | Helm·AWS Load Balancer Controller |
| p.213-p.234 | Volume | 색인 완료 / 상세 대기 | Local·EFS·EBS |
| p.235-p.245 | StatefulSet | 색인 완료 / 상세 대기 | MySQL·Persistent Volume |
| p.246-p.250 | DaemonSet | 색인 완료 / 상세 대기 | Fluentd 예제 |
| p.251-p.261 | Auto Scaling | 색인 완료 / 상세 대기 | HPA·Cluster Autoscaler |
| p.262-p.266 | Related Tools | 색인 완료 / 상세 대기 | K9s·Lens·Helm·ECR·Karpenter |

## 전체 흐름

```text
Container Virtualization
→ Container Orchestration 필요성
→ Kubernetes Control Plane·Worker Node
→ Pod 배포 흐름
→ AWS EKS Managed Control Plane
→ VPC CNI·Security Group
→ IAM Authentication·Kubernetes RBAC Authorization
→ Kubernetes Object와 운영 기능
→ ECR·Helm·Karpenter 등의 연계 도구
```

---

# Page Digest - 현재 상세 범위

## p.1 - Container Orchestration 표지

- 원문 위치: [[40_자료/강의 자료/Kubernetes.pdf#page=1|Kubernetes.pdf p.1]]
- Section 시작 표지다.
- 별도 설명이나 도식은 없다.

## p.2 - Container Orchestration의 의미와 필요성

- 원문 위치: [[40_자료/강의 자료/Kubernetes.pdf#page=2|Kubernetes.pdf p.2]]

### 원문 사실

- 여러 Server와 Container의 관리 작업을 코드로 자동화하는 개념으로 설명한다.
- Cluster 구성, Container 배포, Service 탐색·접근, 부하 처리와 장애 복구 자동화를 주요 기능으로 제시한다.
- Docker Swarm과 Kubernetes를 예로 들고 Kubernetes를 사실상 표준으로 표현한다.
- 수동 방식은 Server마다 Image Pull과 다수의 `docker run`을 반복해야 한다고 설명한다.

### Visual / Code Notes

- Developer가 Image를 Build·Push한 뒤 Test·Prod Server에서 각각 Pull하고 `docker run × 20`을 수행하는 반복 작업 도식이 있다.
- 핵심 대비는 `Container 사용`과 `Container 운영 자동화`가 서로 다른 문제라는 점이다.

## p.3 - Container Virtualization Summary

- 원문 위치: [[40_자료/강의 자료/Kubernetes.pdf#page=3|Kubernetes.pdf p.3]]

### 원문 사실

- Traditional 환경의 Library Version 충돌과 독립성 문제에서 가상화가 발전했다고 설명한다.
- Hypervisor 방식은 VM마다 Guest OS를 사용하고, Container 방식은 Host OS Kernel을 공유한다고 비교한다.
- Docker를 사실상의 Container 표준으로 소개한다.

### Visual / Code Notes

- `Traditional → Virtual Machine → Container`의 Layer 차이를 비교하는 그림이 있다.
- Container가 VM보다 항상 우월하다는 결론이 아니라, Guest OS 중복을 줄인 구조를 보여주는 도식이다.

## p.4 - Kubernetes Architecture 표지

- 원문 위치: [[40_자료/강의 자료/Kubernetes.pdf#page=4|Kubernetes.pdf p.4]]
- Kubernetes Architecture Section의 구분 페이지다.

## p.5 - Kubernetes의 역할

- 원문 위치: [[40_자료/강의 자료/Kubernetes.pdf#page=5|Kubernetes.pdf p.5]]

### 원문 사실

- Kubernetes를 Google이 2014년에 공개한 Container Orchestration 도구로 소개한다.
- MSA Container 배포, 장애 복구, Cloud 연동과 확장성을 주요 특성으로 제시한다.
- CNCF가 관리하는 Open Source Project라고 설명한다.

### Visual / Code Notes

- Manifest File이 Master Node에 전달되고 여러 Worker Node의 Container 실행으로 이어지는 Cluster 그림이 있다.
- 도식에는 `Master Node`, `Docker Engine` 표현이 사용된다. 원문 보존을 위해 그대로 기록하며 현재 용어 여부는 별도 검증한다.

## p.6 - Control Plane과 Worker Node 구성

- 원문 위치: [[40_자료/강의 자료/Kubernetes.pdf#page=6|Kubernetes.pdf p.6]]

### 도식 의미

- 사용자는 UI 또는 `kubectl` CLI를 통해 API Server와 통신한다.
- Control Plane 영역에는 API Server, Scheduler, Controller Manager, `etcd`가 표시된다.
- Worker Node에는 Pod·Container, Kubelet, kube-proxy가 표시된다.
- Service Discovery·Load Balancing, Storage Orchestration, Secret·Configuration Management, Rollout·Rollback, Self-healing 등 Kubernetes 기능을 함께 표현한다.

### 불확실성

- Page Text 추출이 거의 되지 않는 도식 중심 페이지이므로 PDF Image가 최종 기준이다.
- Worker Runtime을 Docker로 그린 부분은 자료 작성 시점의 표현일 가능성이 있어 최신 EKS Runtime과 별도 대조가 필요하다.

## p.7 - Pod 생성 Sequence

- 원문 위치: [[40_자료/강의 자료/Kubernetes.pdf#page=7|Kubernetes.pdf p.7]]

### 도식 흐름

```text
Manifest·Client
→ API Server에 Pod 생성 요청
→ API Server가 etcd에 기록
→ Scheduler가 미배치 Pod 확인
→ 배치할 Node를 결정하고 Binding 기록
→ Kubelet이 할당된 Pod 확인
→ Container Runtime에 실행 요청
→ Pod Status를 API Server에 보고
→ API Server가 etcd에 상태 기록
```

### 불확실성

- 원문 도식에는 `Doker Run` 오타와 Docker Runtime이 표시된다.
- 위 흐름은 도식의 의미를 검색 가능한 Text로 옮긴 것이며 최신 Kubernetes 내부 구현 검증은 아니다.

## p.8 - Elastic Kubernetes Service 표지

- 원문 위치: [[40_자료/강의 자료/Kubernetes.pdf#page=8|Kubernetes.pdf p.8]]
- AWS EKS Section 시작 페이지다.

## p.9 - AWS EKS 개요와 Architecture

- 원문 위치: [[40_자료/강의 자료/Kubernetes.pdf#page=9|Kubernetes.pdf p.9]]

### 원문 사실

- EKS를 Kubernetes Control Plane을 AWS가 관리하는 Managed Service로 설명한다.
- 사용자는 주로 Data Plane을 관리하고 EKS Endpoint를 통해 Cluster API에 접근한다고 설명한다.
- Worker Node VPC와 AWS 관리 EKS Control Plane 영역을 분리해 보여준다.
- PDF에는 서울 Region Cluster 비용을 시간당 `$0.10`으로 표기한다.

### Visual / Code Notes

- Worker Node Auto Scaling Group, ENI, EKS Endpoint, Control Plane의 연결이 표시된다.
- 가격은 시점 의존 정보이므로 현재 청구 기준으로 사용하기 전에 AWS 공식 가격 검증이 필요하다.

## p.10 - EKS VPC CNI

- 원문 위치: [[40_자료/강의 자료/Kubernetes.pdf#page=10|Kubernetes.pdf p.10]]

### 원문 사실

- CNI를 Pod Network 연결을 담당하는 Plugin으로 설명한다.
- EKS VPC CNI에서는 Pod가 VPC Subnet 대역의 IP를 받는다고 설명한다.
- VPC의 Security Group, Route Table, Network ACL과 통합할 수 있다는 장점을 제시한다.
- Worker Node Instance Type에 따라 ENI·Secondary IP와 최대 Pod 수에 한계가 있다고 설명한다.

### Visual / Code Notes

- 두 Subnet의 Worker Node ENI와 Pod IP가 같은 VPC Address Space에 속하는 구조를 보여준다.

## p.11 - EKS Security Group

- 원문 위치: [[40_자료/강의 자료/Kubernetes.pdf#page=11|Kubernetes.pdf p.11]]

### 원문 사실

- Cluster Security Group, Control Plane Security Group, Node Security Group의 역할을 구분한다.
- Control Plane Endpoint의 Public Access와 Private Access 경로를 함께 표시한다.

### Visual / Code Notes

- 사용자 → EKS Endpoint → Control Plane과 Worker ENI 사이의 통신 경계를 색상별 선으로 표현한다.
- 강의 슬라이드 제목에 `(Terraform)`이 있으나 이 페이지에는 Terraform Code보다 Security Group Architecture가 중심이다.

## p.12 - EKS Authentication과 Authorization

- 원문 위치: [[40_자료/강의 자료/Kubernetes.pdf#page=12|Kubernetes.pdf p.12]]

### 원문 사실

- AWS IAM과 `aws-auth`를 Authentication 영역으로 설명한다.
- Kubernetes RBAC을 Authorization 영역으로 구분한다.
- `kubeconfig` Token, STS `GetCallerIdentity`, Identity Mapping, Role Check 후 Allow·Deny가 결정되는 흐름을 그린다.

### 핵심 구분

```text
Authentication
→ 요청자가 누구인지 확인

Authorization
→ 확인된 주체가 해당 Kubernetes Action을 수행할 수 있는지 판단
```

### 검토 필요

- `aws-auth` 중심 설명은 자료 작성 시점의 방식일 수 있으므로 실제 EKS 구축 단계에서는 현재 AWS 공식 인증·Access Entry 문서를 확인해야 한다.

---

## 연계 실습 자료: boot.zip

`boot.zip`은 PDF 원문이 아니므로 Digest Source 범위에서 분리한다.

| 항목 | 현재 확인 |
|---|---|
| 자료 성격 | Spring Boot Maven Project Source |
| Java | 17 |
| Spring Boot | 3.4.5 |
| Container Build | Jib Maven Plugin 3.4.5 |
| 현재 Image Target | Docker Hub |
| 예상 용도 | Container Image Build·Push 후 Kubernetes/EKS 배포 |
| 미확인 | 실제 Build, Image Push, EKS Manifest, Runtime 결과 |

> [!warning]
> `pom.xml`에 Docker Registry 자격증명이 평문으로 포함되어 있다. 실제 자격증명이라면 교체가 필요하며, 값은 이 노트에 복사하지 않는다. `application.properties`는 추가 민감정보 가능성 때문에 열지 않았다.

## 검토 필요

- PDF의 Kubernetes·EKS Version과 현재 지원 Version 차이
- `Master Node`, Docker Runtime, `aws-auth` 등 시점 의존 표현
- p.9의 EKS 가격
- EKS Endpoint Public·Private Access의 현재 권장 구성
- EKS VPC CNI의 현재 ENI·Pod 수 제한
- ECR·IRSA·AWS Load Balancer Controller의 현재 공식 설치 방식
- PDF Text 추출에서 명령어의 Dash·Quote가 변형될 가능성

## 후속 노트 후보

- concept: Container Orchestration과 Kubernetes Architecture
- concept: EKS Control Plane·Data Plane·VPC CNI
- concept: EKS Authentication과 Kubernetes RBAC
- lab: Spring Boot Image Build와 ECR Push
- lab: Terraform 또는 `eksctl` 기반 EKS Cluster 구성
- lab: Deployment·Service·Ingress로 Spring Boot 배포

## 다음 누적 순서

1. 강의가 p.13 이후로 진행될 때 해당 Section을 상세 Digest로 확장한다.
2. 실제 명령·Manifest·오류·검증은 별도 Lab Note에 기록한다.
3. 현재 동작 검증이 필요한 항목은 Kubernetes·AWS 공식 문서와 대조한다.
4. 안정된 개념만 별도 Concept Note로 분리하고 Source Digest는 원자료 색인 역할을 유지한다.
