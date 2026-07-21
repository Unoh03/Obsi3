---
type: concept
status: draft
created: 2026-07-21
topic: kubernetes
parent_moc: "[[10_학습 노트/클라우드/Kubernetes/00_Kubernetes MOC]]"
source: "[[10_학습 노트/클라우드/Kubernetes/Source Digest/Kubernetes - Source Digest 02 Kubernetes Architecture]]"
verified_on: 2026-07-21
aliases:
  - Kubernetes Architecture
---

# Kubernetes 아키텍처

> [!summary]
> Kubernetes Cluster는 전체 상태를 관리하는 **Control Plane**과 실제 Application을 실행하는 **Worker Node**로 나뉜다. 사용자는 API Server에 원하는 상태를 전달하고, 각 Component가 역할을 나눠 Pod를 적절한 Node에서 실행한다.

## 큰 그림부터 보기

Kubernetes는 하나의 거대한 프로그램이 모든 일을 처리하는 구조가 아니다. 역할이 다른 여러 Component가 Kubernetes API에 기록된 상태를 보며 함께 움직인다.

```text
사용자와 kubectl
      ↓
Control Plane
├─ 요청을 받음
├─ Cluster 상태를 저장함
├─ 어디에서 실행할지 정함
└─ 원하는 상태가 유지되는지 확인함
      ↓
Worker Node
└─ 실제 Pod와 Container를 실행함
```

처음에는 **Control Plane은 관리 영역**, **Worker Node는 실행 영역**이라고 구분하면 충분하다.

## Pod란 무엇인가

Kubernetes가 직접 배치하고 관리하는 가장 작은 단위는 Container가 아니라 **Pod**다.

- Pod에는 Container가 하나 이상 들어갈 수 있다.
- 같은 Pod의 Container는 같은 Node에서 함께 실행된다.
- 같은 Network 주소와 필요한 저장공간을 함께 사용할 수 있다.
- 일반적인 Application은 Pod 하나에 주 Container 하나를 두는 경우가 많다.

Container 여러 개를 실행한다고 복제본 하나의 Pod에 모두 넣는 것은 아니다. 같은 Application을 세 개 실행하려면 보통 Container 세 개를 한 Pod에 넣는 것이 아니라, 같은 형태의 Pod를 세 개 만든다.

```text
Pod A → Application Container 1개
Pod B → Application Container 1개
Pod C → Application Container 1개
```

## Control Plane의 주요 Component

### API Server: 모든 요청이 들어오는 정문

사용자가 `kubectl`로 보낸 요청과 다른 Component의 상태 변경은 Kubernetes API를 통해 처리된다. API Server는 요청을 받고 형식과 권한을 확인하며, Cluster 상태를 조회하거나 변경하는 통로가 된다.

> [!important]
> `kubectl`이 Cluster를 직접 조작하는 것이 아니다. `kubectl`은 API Server에 요청을 보내는 Client다.

### etcd: Cluster 상태를 보관하는 저장소

etcd에는 Pod, Deployment, 설정처럼 Kubernetes가 관리하는 상태가 저장된다. 원하는 상태와 현재 상태를 판단할 때 필요한 핵심 기록이다.

etcd가 손상되면 Cluster 상태를 잃을 수 있으므로 Production에서는 Backup과 복구 계획이 중요하다. 사용자가 일반 Database처럼 직접 값을 수정하는 저장소는 아니다.

### Scheduler: Pod가 실행될 Node를 선택

새 Pod에 아직 실행할 Node가 정해지지 않았다면 Scheduler가 적절한 Node를 찾는다.

- 필요한 CPU와 Memory를 제공할 수 있는가?
- 특정 Node에서 실행해야 하는 조건이 있는가?
- 배치 정책을 만족하는가?

조건을 만족하는 Node가 없다면 Pod는 바로 실행되지 못하고 기다린다.

### Controller Manager: 원하는 상태를 계속 유지

Controller는 현재 상태와 원하는 상태를 비교한다. Pod가 부족하면 만들고, 너무 많으면 줄이는 식으로 차이를 맞춘다.

앞에서 배운 **Reconciliation**, 즉 “현재 상태를 원하는 상태에 계속 맞추는 동작”을 실제로 수행하는 핵심 영역이다.

## Worker Node의 주요 Component

### Kubelet: 자기 Node의 Pod 담당자

Kubelet은 각 Worker Node에서 실행된다. API Server를 통해 자기 Node에 배정된 Pod를 확인하고, Container가 명세대로 실행되도록 관리한다. 실행 상태도 다시 API Server에 보고한다.

### Container Runtime: 실제 Container 실행

Container Runtime은 Image를 받아 실제 Container를 만들고 실행한다. 현재 Kubernetes는 `containerd`, `CRI-O`처럼 CRI 규격을 지원하는 Runtime을 사용할 수 있다.

### Kube-proxy: Service 통신을 위한 Network 규칙

Kube-proxy는 각 Node에서 Network 규칙을 관리해 Kubernetes Service로 들어온 통신이 적절한 Pod로 전달되도록 돕는다. Cluster의 Network 구현에 따라 이 역할을 다른 Network Component가 담당할 수도 있다.

## Pod 하나가 만들어지는 흐름

사용자가 Pod YAML을 적용했을 때의 흐름을 단순화하면 다음과 같다.

```text
1. kubectl이 YAML 내용을 API Server에 보냄
2. API Server가 요청을 확인하고 상태를 etcd에 기록
3. Scheduler가 Node가 없는 새 Pod를 발견
4. Scheduler가 실행할 Node를 선택해 결과를 API Server에 기록
5. 선택된 Node의 Kubelet이 자기에게 배정된 Pod를 발견
6. Kubelet이 Container Runtime에 Container 실행을 요청
7. Kubelet이 Pod 상태를 API Server에 보고
```

각 Component가 서로의 내부로 직접 들어가 작업하는 것이 아니라, 대부분 API Server에 기록된 상태와 변경을 확인하며 협력한다.

## 처음부터 알아두면 좋은 실무 팁

### `kubectl apply` 성공은 Application 정상 동작을 뜻하지 않는다

명령이 성공했다는 것은 우선 API Server가 요청을 받아들였다는 뜻이다. 그 뒤에도 Scheduling, Image 다운로드, Container 시작, Health Check가 남아 있다.

```text
요청 접수 성공
≠ Pod 실행 성공
≠ Application 요청 처리 가능
```

따라서 실제 상태와 Event를 추가로 확인해야 한다.

### Pod가 기다리면 단계부터 구분한다

- `Pending`: 아직 Node를 선택하지 못했거나 필요한 준비가 끝나지 않은 상태
- `ContainerCreating`: Image·Network·Storage 등 Container 실행 준비 중
- `Running`: Container가 실행 중인 상태
- `Ready`: 사용자의 요청을 받을 준비가 됐다고 판단된 상태

`Running`이어도 `Ready`가 아닐 수 있다는 점이 중요하다.

### etcd는 일반 사용자가 직접 고치는 곳이 아니다

Cluster 문제를 고친다고 etcd 값을 임의로 수정하면 Kubernetes API가 기대하는 상태와 어긋날 수 있다. 평상시 상태 변경은 `kubectl`이나 Kubernetes API를 통해 수행한다.

## 강의자료와 현재 기준의 차이

- 강의자료의 `Kubernetes Master`는 현재 일반적으로 **Control Plane**이라고 부른다.
- 강의 도식은 Worker Node의 실행 도구를 `Docker`로 표시하지만, 현재 Kubernetes는 Docker Engine에 종속되지 않고 여러 Container Runtime을 사용할 수 있다.
- 강의 p.7은 API가 Scheduler와 Kubelet에 순서대로 직접 메시지를 보내는 것처럼 표현한다. 실제 Component는 Kubernetes API의 Object 변경을 Watch하여 새 작업을 발견하는 구조에 가깝다.
- 강의 p.7의 `Doker Run`은 원자료 오타다. 현재 기준에서는 Kubelet이 CRI를 통해 Container Runtime에 실행을 요청한다고 이해한다.

## 지금은 이것만 기억한다

```text
Control Plane
= Cluster의 원하는 상태를 저장하고 관리하는 영역

Worker Node
= 실제 Pod와 Container가 실행되는 Server

API Server
= 모든 요청과 상태 변경이 통과하는 정문

Scheduler
= Pod가 실행될 Node를 선택

Kubelet
= 자기 Node에 배정된 Pod를 실제로 실행·확인
```

## 정보 출처

- **강의 원자료**: [[Source Digest/Kubernetes - Source Digest 02 Kubernetes Architecture]] — `Kubernetes.pdf` p.4-p.7
- **Local primary evidence**: 아직 실제 Cluster 실행 결과 없음
- **Authoritative external evidence**: 아래 Kubernetes 공식 문서
- **Informal external evidence**: 사용하지 않음
- **Parametric knowledge**: 입문 설명을 위한 비유와 표현 단순화에만 사용

## 공식 문서

- [Kubernetes Components](https://kubernetes.io/docs/concepts/overview/components/)
- [Kubernetes Pods](https://kubernetes.io/docs/concepts/workloads/pods/)
- [Kubernetes API Concepts](https://kubernetes.io/docs/reference/using-api/api-concepts/)
- [Kubernetes Scheduler](https://kubernetes.io/docs/concepts/scheduling-eviction/kube-scheduler/)
