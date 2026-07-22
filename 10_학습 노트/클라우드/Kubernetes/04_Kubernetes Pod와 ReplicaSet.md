---
type: concept
status: draft
created: 2026-07-21
topic: kubernetes
parent_moc: "[[10_학습 노트/클라우드/Kubernetes/00_Kubernetes MOC]]"
source: "[[10_학습 노트/클라우드/Kubernetes/Source Digest/Kubernetes - Source Digest 04 Pod and ReplicaSet]]"
verified_on: 2026-07-21
aliases:
  - Kubernetes Pod and ReplicaSet
---

# Kubernetes Pod와 ReplicaSet

> [!summary]
> **Pod**는 Kubernetes가 Container를 실행하는 가장 작은 단위다. **ReplicaSet**은 같은 역할의 Pod가 정해둔 개수만큼 계속 존재하도록 관리한다.

## 먼저 전체 그림부터 본다

```text
Container
→ 실제 Application Process

Pod
→ Container를 Kubernetes에서 실행하는 단위

ReplicaSet
→ 같은 역할의 Pod 개수를 유지하는 관리자

Deployment
→ ReplicaSet을 이용해 Version 교체와 Rollback까지 관리하는 상위 관리자
```

처음에는 `Pod = 실행 단위`, `ReplicaSet = 개수 관리자`라고 이해하면 충분하다.

## Pod는 Container를 담아 실행하는 단위다

Kubernetes는 Container 하나를 그대로 배포하지 않고 **Pod 안에 넣어 배포**한다. Pod는 Kubernetes가 만들고, Node에 배치하고, 상태를 확인하는 가장 작은 단위다.

보통 Pod 하나에 주 Application Container 하나를 넣는다. 하지만 서로 아주 가깝게 협력해야 하는 보조 Container가 있다면 한 Pod에 여러 Container를 함께 넣을 수도 있다.

```text
Pod
├─ Main Container
└─ Sidecar Container (선택)
```

같은 Pod의 Container들은 다음을 공유한다.

- 같은 Network 공간과 Pod IP
- 같은 Port 공간
- 연결해 둔 Volume
- 같은 Node에 함께 배치되는 Pod 단위의 수명 경계

따라서 같은 Pod 안의 Container끼리는 `localhost`로 통신할 수 있다. 대신 같은 Port를 동시에 사용할 수는 없다.

> [!note] 왜 Container마다 Pod를 따로 만들지 않는가
> Main Application과 Log 수집기처럼 함께 배치되고 함께 사라져야 하는 Process는 한 Pod로 묶을 수 있다. 단지 편하다는 이유로 관련 없는 Application들을 한 Pod에 몰아넣지는 않는다.

## Pod는 오래 보존하는 Server가 아니다

Pod는 고장 난 것을 수리해 영구히 사용하는 Server보다 **필요하면 새로 교체하는 일회성 실행 단위**에 가깝다.

Pod가 삭제되거나 Node 장애로 사라지면, Controller는 같은 설정을 이용해 새 Pod를 만들 수 있다. 이때 새 Pod는 이전 Pod와 이름, ID, IP가 달라질 수 있다.

```text
기존 Pod 장애
→ 기존 Pod 자체가 부활하는 것이 아님
→ 같은 역할의 새 Pod가 생성됨
```

그래서 Application 사용자가 특정 Pod IP를 직접 기억해서 접속하는 방식은 적절하지 않다. 여러 Pod가 교체되어도 일정한 주소로 접근하려면 나중에 배우는 **Service**를 사용한다.

> [!important] Pod IP가 항상 외부에서 기술적으로 차단된다는 뜻은 아니다
> Network 구성에 따라 도달 가능 범위는 달라진다. 핵심은 Pod IP가 임시 주소라서 안정적인 Service 진입점으로 사용하지 않는다는 것이다.

## Label은 Pod에 붙이는 분류표다

Kubernetes에는 Object가 많기 때문에 이름만으로 묶어 관리하기 어렵다. **Label**은 Object에 붙이는 `key=value` 형식의 분류표다.

```yaml
labels:
  app: nginx
  env: prod
```

**Selector**는 Label을 기준으로 원하는 Object를 찾는 조건이다.

```text
Label: app=nginx
Selector: app=nginx인 Pod를 선택
```

Service와 ReplicaSet 같은 Object는 Selector를 사용해 자신이 다룰 Pod를 찾는다. 따라서 Label은 단순 메모가 아니라 실제 연결과 제어에 사용된다.

> [!warning] Label을 잘못 겹치면 다른 Pod가 관리 대상이 될 수 있다
> ReplicaSet을 만들기 전에 Selector가 기존 Pod와 겹치지 않는지 확인해야 한다. Owner가 없는 기존 Pod라도 Selector와 일치하면 ReplicaSet이 자기 관리 대상으로 편입할 수 있다.

Label은 분류와 선택을 위한 정보이지, 접근 권한을 막는 보안 경계는 아니다.

## Pod가 실행될 Node는 Scheduler가 고른다

Pod를 만들면 Kubernetes Scheduler가 실행 가능한 Node를 찾는다. 특별한 이유가 없다면 Scheduler의 기본 판단을 따르는 편이 단순하다.

특정 장비, 가용영역, 보안 구역처럼 배치 조건이 필요할 때 다음 기능을 사용한다.

| 기능 | 쉬운 의미 | 조건을 만족하지 못하면 |
|---|---|---|
| `nodeSelector` | 이 Label을 가진 Node에만 배치 | Pod가 `Pending`에 머무를 수 있음 |
| Required Node Affinity | 반드시 지켜야 하는 상세 조건 | 배치하지 않음 |
| Preferred Node Affinity | 가능하면 지키는 선호 조건 | 다른 Node에도 배치 가능 |
| Taint | Node가 특정 Pod를 밀어내는 표시 | 허용받지 못한 Pod의 배치를 막거나 실행을 종료할 수 있음 |
| Toleration | 해당 Taint가 있어도 이 Pod는 허용될 수 있다는 표시 | 배치를 보장하지는 않음 |

`Toleration`은 “이 Node에 반드시 배치해라”가 아니라 “이 Taint 때문에 거절하지는 마라”에 가깝다. 실제 배치에는 Resource와 다른 Scheduling 조건도 함께 적용된다.

Node 점검 때 사용하는 명령의 의미도 구분한다.

- `cordon`: 그 Node에 **새 Pod를 배치하지 않음**
- `drain`: 새 배치를 막고, 가능한 Pod를 다른 Node로 내보냄
- `uncordon`: 다시 새 Pod를 받을 수 있게 함

## ReplicaSet은 원하는 Pod 개수를 유지한다

ReplicaSet은 다음 세 가지를 보고 동작한다.

```text
replicas
→ 몇 개를 유지할 것인가

selector
→ 어떤 Pod를 내 관리 대상으로 볼 것인가

template
→ Pod가 부족할 때 어떤 설정으로 새로 만들 것인가
```

예를 들어 `replicas: 3`인데 해당 Selector와 일치하는 Pod가 두 개뿐이면 ReplicaSet은 Template으로 Pod 하나를 새로 만든다.

```text
원하는 상태: Pod 3개
현재 상태: Pod 2개
ReplicaSet 동작: Pod 1개 생성
결과: 다시 Pod 3개
```

반대로 일치하는 Pod가 너무 많으면 일부를 삭제해 목표 개수로 맞춘다. 이처럼 현재 상태를 원하는 상태에 계속 맞추는 동작이 앞에서 배운 **Reconciliation**의 구체적인 예다.

> [!important] Pod가 스스로 복구하는 것은 아니다
> 사라진 Pod 자체가 살아나는 것이 아니라 ReplicaSet Controller가 부족한 수를 발견하고 새 Pod를 만든다. 그래서 흔히 말하는 Self-Healing은 “동일한 역할의 새 실행 단위를 만들어 상태를 회복한다”는 의미다.

## Selector와 Template Label은 연결되어 있다

ReplicaSet의 Selector와 Pod Template Label은 서로 맞아야 한다.

```yaml
selector:
  matchLabels:
    app: nginx

template:
  metadata:
    labels:
      app: nginx
```

ReplicaSet은 `app=nginx`인 Pod를 세어 목표 개수와 비교한다. 이 때문에 다음 상황도 생길 수 있다.

1. 사람이 먼저 `app=nginx`인 단독 Pod를 만든다.
2. 같은 Selector를 가진 ReplicaSet을 만든다.
3. ReplicaSet이 기존 Pod를 관리 대상에 포함한다.
4. 부족한 수만 새로 만든다.

즉 ReplicaSet은 “자기가 만든 이름의 Pod”만 찾는 것이 아니라 **Selector와 Owner 관계**를 이용한다. Owner 관계는 Kubernetes가 “이 Pod는 이 ReplicaSet이 관리한다”라고 기록하는 부모·자식 표시에 가깝다.

## ReplicaSet은 개수 관리는 잘하지만 Version 교체는 부족하다

ReplicaSet의 Pod Template에서 Image나 Label을 바꿔도 이미 실행 중인 Pod는 자동으로 교체되지 않는다. 바뀐 Template은 이후 새로 만들어지는 Pod에만 적용된다.

```text
ReplicaSet Template의 Image 변경
→ 기존 Pod: 이전 Image로 계속 실행
→ 이후 새 Pod: 새 Image로 생성
```

기존 Pod를 전부 지운 뒤 다시 만들면 새 Version으로 바뀔 수 있지만, 서비스 중단과 Rollback 관리가 어려워진다.

그래서 실제 Application 배포에서는 ReplicaSet을 직접 운영하기보다 **Deployment가 ReplicaSet을 관리하게 하는 방식**이 권장된다. Deployment는 새 ReplicaSet을 만들고 Pod를 순차 교체하며 Revision과 Rollback을 관리한다.

ReplicaSet을 배우는 이유는 Deployment 내부에서 “Pod 개수를 유지하는 층”이 어떻게 동작하는지 이해하기 위해서다.

## 서로 헷갈리기 쉬운 역할

| Object | 주된 역할 |
|---|---|
| Pod | Container를 함께 실행하는 최소 배포 단위 |
| ReplicaSet | 같은 역할의 Pod 개수 유지 |
| Deployment | ReplicaSet을 이용한 Version 배포·교체·Rollback |
| Service | 교체되는 여러 Pod 앞에 안정적인 Network 진입점 제공 |

## 처음부터 알아두면 좋은 실무·보안 팁

### 단독 Pod보다 Controller를 사용한다

학습과 Debug 목적이 아니라면 Pod를 단독으로 만들기보다 Deployment 같은 Controller를 사용해야 장애 시 자동으로 대체할 수 있다.

### Selector는 좁고 명확하게 설계한다

여러 Controller의 Selector가 뜻하지 않게 겹치면 기존 Pod를 잘못 편입하거나 관리가 충돌할 수 있다. `app`, `component`, `environment`처럼 역할이 드러나는 Label을 일관되게 사용한다.

### `latest` 대신 확인 가능한 Image Version을 쓴다

`latest`는 같은 이름이 나중에 다른 Image를 가리킬 수 있다. Version Tag나 변경되지 않는 Image Digest를 사용해야 실행 중인 코드를 확인하고 되돌리기 쉽다.

### 보안용 Node Label은 일반 Label보다 엄격하게 관리한다

민감한 Workload를 특정 Node에만 배치한다면, 침해된 Node가 스스로 보안 Label을 붙이지 못하게 해야 한다. 공식 문서는 Node Authorizer와 `NodeRestriction` admission plugin을 사용하고, 보호되는 Label prefix를 이용하는 방식을 안내한다.

## 강의자료와 현재 기준의 차이

- 강의자료는 ReplicaSet Object가 `Replication Controller`에 의해 관리된다고 표현한다. 현재 기준에서 ReplicaSet과 ReplicationController는 별개의 Resource이며, ReplicaSet은 ReplicationController의 후속 개념이다.
- 강의자료의 ReplicaSet Update·Rollback 실습은 Template 변경이 기존 Pod에 적용되지 않는 한계를 보여준다. 현재 공식 문서는 일반적인 Application 운영에는 ReplicaSet을 직접 다루기보다 Deployment 사용을 권장한다.
- 강의 도식은 외부 Client의 Pod IP 직접 접근을 `Access Denie`로 표시한다. 일반적인 핵심은 “항상 Network 수준에서 접근 불가”가 아니라 Pod IP가 수명에 따라 바뀌므로 Service를 안정적인 진입점으로 사용한다는 것이다.
- Node Affinity의 `IgnoredDuringExecution`은 배치 뒤 Node Label이 바뀌어도 이미 실행 중인 Pod를 자동으로 내보내지 않는다는 뜻이다.

## 지금은 이것만 기억한다

```text
Pod
= Container가 실제로 함께 실행되는 최소 단위

Label과 Selector
= 관리할 Pod를 찾는 분류표와 검색 조건

ReplicaSet
= Selector로 Pod를 세고, 정해둔 개수를 계속 유지하는 Controller

Deployment
= ReplicaSet 위에서 Version 교체와 Rollback을 관리하는 상위 Controller
```

## 정보 출처

- **강의 원자료**: [[Source Digest/Kubernetes - Source Digest 04 Pod and ReplicaSet]] — `Kubernetes.pdf` p.13-p.73
- **Local primary evidence**: 이번 개념 노트에는 별도 Cluster 실행 결과를 반영하지 않음
- **Authoritative external evidence**: 아래 Kubernetes 공식 문서
- **Informal external evidence**: 사용하지 않음
- **Parametric knowledge**: 초보자용 비유와 설명 순서에만 사용

## 공식 문서

- [Kubernetes Pods](https://kubernetes.io/docs/concepts/workloads/pods/)
- [Kubernetes ReplicaSet](https://kubernetes.io/docs/concepts/workloads/controllers/replicaset/)
- [Labels and Selectors](https://kubernetes.io/docs/concepts/overview/working-with-objects/labels/)
- [Assigning Pods to Nodes](https://kubernetes.io/docs/concepts/scheduling-eviction/assign-pod-node/)
- [Taints and Tolerations](https://kubernetes.io/docs/concepts/scheduling-eviction/taint-and-toleration/)
