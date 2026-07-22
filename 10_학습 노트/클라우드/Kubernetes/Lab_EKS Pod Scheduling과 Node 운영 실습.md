---
type: lab
status: active
created: 2026-07-22
lab_date: 2026-07-22
topic: kubernetes
parent_moc: "[[10_학습 노트/클라우드/Kubernetes/00_Kubernetes MOC]]"
source: "[[10_학습 노트/클라우드/Kubernetes/Source Digest/Kubernetes - Source Digest 04 Pod and ReplicaSet]]"
environment: "Amazon EKS ap-northeast-2; Kubernetes v1.35.6-eks-8f14419; Worker Node 2대"
evidence: "Bastion 공유 tmux의 kubectl 명령·출력과 Kubernetes.pdf p.31-p.51"
verified_on: 2026-07-22
---

# EKS Pod Scheduling과 Node 운영 실습

> [!summary]
> Label을 바탕으로 NodeSelector·NodeAffinity의 Hard·Soft 배치를 비교하고, Taint/Toleration·cordon·drain으로 Node의 수용·축출·유지보수 경계를 검증했다.

> [!info] 환경과 선행 실습
> EKS 생성·Bastion 접속·Pod 기본 환경은 [[Lab_EKS 첫 접속과 Pod 기초 실습]]에 기록한다. 이 노트는 PDF p.31-p.51의 Scheduling과 Node 운영만 담당한다.

## 목표

- Pod가 특정 Node를 선택하거나 피하는 규칙을 구분한다.
- Hard·Soft Scheduling 조건과 `Pending`의 원인을 실제 배치로 확인한다.
- `NoSchedule`, `NoExecute`, `cordon`, `drain`, PDB의 역할을 비교한다.

## EX.5 NodeSelector 실습

### 실습 목적과 Manifest

Worker Node 두 대 중 한 대에만 `project=boot` Label을 붙이고, 다음 Selector를 가진 Boot Pod 세 개가 해당 Node에만 배치되는지 확인했다.

```yaml
spec:
  nodeSelector:
    project: boot
```

`pod-boot-1.yml`, `pod-boot-2.yml`, `pod-boot-3.yml`의 Container Image는 강사 계정의 Image에서 다음 사용자 Image로 변경했다.

```yaml
image: unoh03/boot:latest
```

같은 Directory에는 `project=nginx`를 요구하는 `pod-nginx-1.yml`부터 `pod-nginx-3.yml`도 있었다.

### Label 값 불일치로 인한 `Pending`

처음에는 Node 한 대에 Manifest와 다른 값을 붙였다.

```console
$ kubectl label node ip-172-28-11-97.ap-northeast-2.compute.internal project=melong
node/ip-172-28-11-97.ap-northeast-2.compute.internal labeled
```

`kubectl apply -f .`는 현재 Directory의 Boot·Nginx Manifest 여섯 개를 모두 적용했다.

```console
$ kubectl apply -f .
pod/boot-pod-1 created
pod/boot-pod-2 created
pod/boot-pod-3 created
pod/nginx-pod-1 created
pod/nginx-pod-2 created
pod/nginx-pod-3 created
```

Node에는 `project=melong`만 있고 Pod들은 `project=boot` 또는 `project=nginx`를 요구했으므로, 여섯 Pod 모두 배치할 Node를 찾지 못했다.

```console
$ kubectl get pods -o wide
NAME          READY   STATUS    IP       NODE
boot-pod-1    0/1     Pending   <none>   <none>
boot-pod-2    0/1     Pending   <none>   <none>
boot-pod-3    0/1     Pending   <none>   <none>
nginx-pod-1   0/1     Pending   <none>   <none>
nginx-pod-2   0/1     Pending   <none>   <none>
nginx-pod-3   0/1     Pending   <none>   <none>
```

Scheduler Event도 Selector 불일치를 직접 기록했다.

```text
FailedScheduling: 0/2 nodes are available:
2 node(s) didn't match Pod's node affinity/selector.
```

`nodeSelector`는 선호 조건이 아니라 반드시 만족해야 하는 배치 조건이다. 일치하는 Node가 없으면 Pod Object는 생성되지만 Node·Pod IP가 할당되지 않은 `Pending` 상태에 머문다.

### Node Label 보정과 배치 성공

기존 `project` 값을 Manifest가 요구하는 `boot`로 덮어썼다.

```console
$ kubectl label node ip-172-28-11-97.ap-northeast-2.compute.internal project=boot --overwrite
node/ip-172-28-11-97.ap-northeast-2.compute.internal labeled

$ kubectl get nodes -L project
NAME                                               PROJECT
ip-172-28-11-97.ap-northeast-2.compute.internal    boot
ip-172-28-31-206.ap-northeast-2.compute.internal
```

새로 Apply하지 않아도 Scheduler가 기존 `Pending` Pod를 다시 평가했다. Boot Pod 세 개는 모두 `project=boot` Node에 배치됐고, `project=nginx`를 요구하는 Nginx Pod 세 개는 계속 `Pending`이었다.

```console
$ kubectl get pods -o wide
NAME         READY   STATUS    IP              NODE
boot-pod-1   1/1     Running   172.28.11.84    ip-172-28-11-97.ap-northeast-2.compute.internal
boot-pod-2   1/1     Running   172.28.11.153   ip-172-28-11-97.ap-northeast-2.compute.internal
boot-pod-3   1/1     Running   172.28.11.245   ip-172-28-11-97.ap-northeast-2.compute.internal
```

`boot-pod-1`의 Event에는 `FailedScheduling` 이후 다음 성공 과정이 이어졌다.

```text
Scheduled → Pulling unoh03/boot:latest → Pulled → Created → Started
```

즉 Node Label을 수정하면 이미 생성된 `Pending` Pod를 삭제·재생성하지 않아도 조건이 충족되는 시점에 자동 배치된다.

### NodeSelector로 얻는 이점과 한계

이 실습에서 `nodeSelector`가 주는 직접적인 이점은 **특정 조건을 갖춘 Node에만 Workload를 배치할 수 있다는 것**이다.

예를 들어 다음과 같은 Node를 Label로 구분해 사용할 수 있다.

- 특정 애플리케이션 실행에 필요한 설정이나 도구가 준비된 Node
- GPU·고성능 CPU·대용량 Memory처럼 특정 Hardware를 가진 Node
- 개발·검증·운영 등 용도가 구분된 Node
- 특정 가용영역·망·보안 요구사항에 맞는 Node

이번 실습에서는 `project=boot`가 붙은 Node를 “Boot 애플리케이션을 실행하도록 준비된 Node”라고 가정했고, Boot Pod 세 개가 다른 Node로 흩어지지 않도록 배치 위치를 제한했다. 잘못된 Node에서 실행해 생길 수 있는 환경 차이와 운영 실수를 줄이는 것이 핵심 이점이다.

다만 `nodeSelector`는 다음까지 해결하지는 않는다.

- Node가 조건을 만족하는지만 확인하며, Pod를 여러 Node에 고르게 분산하지 않는다.
- 이번처럼 조건을 만족하는 Node가 한 대뿐이면 Pod 세 개가 모두 그 Node에 모인다.
- 해당 Node가 장애 나면 세 Pod가 함께 영향을 받을 수 있다.
- Label 자체는 보안 격리 장치가 아니며, 사용자가 Node Label을 변경할 권한이 있으면 배치 조건도 바꿀 수 있다.

따라서 정확한 Node 종류를 고르는 데는 `nodeSelector`를 사용할 수 있지만, 고가용성이나 분산 배치는 Pod Affinity·Anti-Affinity, Topology Spread Constraints 같은 별도 Scheduling 규칙이 필요하다. 특정 Workload 외의 Pod가 해당 Node에 들어오는 것까지 막으려면 Taint와 Toleration도 별도로 고려한다.

### Nginx Pod 1차 정리 상태

이번 지시는 Boot Pod 세 개의 배치를 확인하는 것이므로, 함께 생성된 Nginx Pod 세 개는 이름을 명시해 삭제했다.

```console
$ kubectl delete pod nginx-pod-1
$ kubectl delete pod nginx-pod-2
$ kubectl delete pod nginx-pod-3
```

이 시점에는 `boot-pod-1`부터 `boot-pod-3`까지만 동일 Node에서 `Running`이었다.

### 기본 Zone Label을 사용한 배치

다음 단계에서는 사용자 지정 `project` Selector를 주석 처리하고, EKS Node에 기본으로 존재하는 Zone Label을 사용하도록 여섯 Manifest를 변경했다.

```yaml
# Boot Pod 3개
spec:
  nodeSelector:
    topology.kubernetes.io/zone: ap-northeast-2a
    # project: boot

# Nginx Pod 3개
spec:
  nodeSelector:
    topology.kubernetes.io/zone: ap-northeast-2c
    # project: nginx
```

현재 Worker Node의 기본 Zone Label은 다음과 같았다.

```console
$ kubectl get nodes -L topology.kubernetes.io/zone
NAME                                               ZONE
ip-172-28-11-97.ap-northeast-2.compute.internal    ap-northeast-2a
ip-172-28-31-206.ap-northeast-2.compute.internal   ap-northeast-2c
```

### 기존 Pod에 Selector 변경 Apply 실패

Nginx Pod는 앞 단계에서 삭제돼 있었지만 Boot Pod는 `project=boot` Selector를 가진 채 실행 중이었다. 이 상태에서 `kubectl apply -f .`를 실행하자 Nginx Pod 세 개는 새 Zone Selector로 생성됐고, Boot Pod 세 개의 Patch만 거부됐다.

```text
Pod "boot-pod-1" is invalid: spec: Forbidden:
pod updates may not change fields ...

NodeSelector:
- project: boot
+ topology.kubernetes.io/zone: ap-northeast-2a
```

Pod의 `nodeSelector`는 생성 후 변경할 수 없는 필드다. 따라서 Manifest 변경만으로 기존 Pod의 배치 조건을 바꿀 수 없고, Pod를 삭제한 뒤 새 Manifest로 다시 생성해야 한다.

또한 `kubectl apply -f .`는 Directory의 모든 Object를 하나의 Transaction으로 처리하지 않는다. 이 실행에서는 Nginx Pod 생성은 성공하고 Boot Pod Patch만 실패해 일부 변경만 반영됐다.

### 전체 Pod 재생성과 Zone별 배치 결과

삭제 누락을 확인한 뒤 여섯 Pod를 모두 삭제하고 현재 Manifest를 다시 적용했다.

```console
$ kubectl delete pod --all
pod "boot-pod-1" deleted from default namespace
pod "boot-pod-2" deleted from default namespace
pod "boot-pod-3" deleted from default namespace
pod "nginx-pod-1" deleted from default namespace
pod "nginx-pod-2" deleted from default namespace
pod "nginx-pod-3" deleted from default namespace

$ kubectl apply -f .
pod/boot-pod-1 created
pod/boot-pod-2 created
pod/boot-pod-3 created
pod/nginx-pod-1 created
pod/nginx-pod-2 created
pod/nginx-pod-3 created
```

재생성 후 여섯 Pod는 각 Manifest가 지정한 Zone의 Node에 정확히 배치됐다.

```console
$ kubectl get pods -o wide
NAME          READY   STATUS    IP              NODE
boot-pod-1    1/1     Running   172.28.11.121   ip-172-28-11-97.ap-northeast-2.compute.internal
boot-pod-2    1/1     Running   172.28.11.234   ip-172-28-11-97.ap-northeast-2.compute.internal
boot-pod-3    1/1     Running   172.28.11.84    ip-172-28-11-97.ap-northeast-2.compute.internal
nginx-pod-1   1/1     Running   172.28.31.54    ip-172-28-31-206.ap-northeast-2.compute.internal
nginx-pod-2   1/1     Running   172.28.31.146   ip-172-28-31-206.ap-northeast-2.compute.internal
nginx-pod-3   1/1     Running   172.28.31.70    ip-172-28-31-206.ap-northeast-2.compute.internal
```

현재 Live Spec도 Boot Pod는 `ap-northeast-2a`, Nginx Pod는 `ap-northeast-2c`를 Selector로 사용한다. Node 1의 사용자 지정 `project=boot` Label은 여전히 남아 있지만, 현재 Manifest에서 주석 처리됐으므로 이번 Zone 배치에는 관여하지 않는다.

Zone Label을 사용하면 특정 가용영역에 Workload를 배치할 수 있다. 반대로 해당 Zone에 사용 가능한 Node가 없으면 Pod가 `Pending`이 되며, 모든 복제본을 한 Zone에 고정하면 가용영역 장애에 함께 영향을 받을 수 있다.

### Shell 경로 오타

Linux Shell에서 Windows식 Backslash로 상위 Directory를 이동하려고 해 실패했다.

```console
$ cd ..\node_selectors
-bash: cd: ..node_selectors: No such file or directory

$ cd ../node_selectors
```

Linux 경로 구분자는 `/`다.

## EX.6 NodeAffinity 실습

### `required` Hard 조건과 존재하지 않는 Label Key

`nodeSelector`보다 다양한 조건식을 사용할 수 있는 NodeAffinity를 실습했다. 먼저 `requiredDuringSchedulingIgnoredDuringExecution`과 `Exists` Operator를 사용했다.

```yaml
spec:
  affinity:
    nodeAffinity:
      requiredDuringSchedulingIgnoredDuringExecution:
        nodeSelectorTerms:
          - matchExpressions:
              - key: melong
                operator: Exists
```

`Exists`는 Label의 값을 비교하지 않고, 지정한 Key 자체가 Node에 존재하는지만 확인한다. 당시 두 Worker Node에는 `project=boot`만 있었고 `melong` Key는 없었다.

```console
$ kubectl get nodes -L project -L melong
NAME                                               PROJECT   MELONG
ip-172-28-11-97.ap-northeast-2.compute.internal    boot
ip-172-28-31-206.ap-northeast-2.compute.internal
```

Boot Pod 두 개는 `melong` Key를 필수로 요구해 `Pending`에 머물렀다. 반면 `project` Key의 존재를 요구한 Nginx Pod 두 개는 `project=boot`가 붙은 Node에 배치됐다. `Exists`는 값이 `boot`인지 `nginx`인지 구분하지 않는다는 점도 함께 확인됐다.

```console
$ kubectl get pods -o wide
NAME          READY   STATUS    NODE
boot-pod-1    0/1     Pending   <none>
boot-pod-2    0/1     Pending   <none>
nginx-pod-1   1/1     Running   ip-172-28-11-97.ap-northeast-2.compute.internal
nginx-pod-2   1/1     Running   ip-172-28-11-97.ap-northeast-2.compute.internal
```

Scheduler Event도 필수 Affinity 조건이 맞지 않았음을 기록했다.

```text
FailedScheduling: 0/2 nodes are available:
2 node(s) didn't match Pod's node affinity/selector.
```

실패 비교를 마친 뒤 Required Manifest의 Key는 다시 `project`로 돌렸다.

### `preferred` Soft 조건과 Zone 선호

다음에는 `preferredDuringSchedulingIgnoredDuringExecution`으로 `ap-northeast-2c` Zone을 선호하도록 했다.

```yaml
spec:
  affinity:
    nodeAffinity:
      preferredDuringSchedulingIgnoredDuringExecution: # 반드시 지켜야 하는 조건이 아니라 가능한 경우 우선하는 Soft 조건
        - weight: 50 # 이 조건을 만족하는 Node에 50점 추가. 50% 확률이라는 뜻이 아님
          preference: # 점수를 받을 Node의 조건
            matchExpressions:
              - key: topology.kubernetes.io/zone # Node의 가용영역 Label 확인
                operator: In # 아래 values 중 하나와 Label 값이 일치하는지 확인
                values:
                  - ap-northeast-2c # 2c Zone의 Node를 가장 우선함
        # - weight: 40 # 주석을 해제하면 2a Zone Node에 40점 추가
        #   preference:
        #     matchExpressions:
        #       - key: topology.kubernetes.io/zone
        #         operator: In
        #         values:
        #           - ap-northeast-2a
        # - weight: 20 # 주석을 해제하면 project=spring Node에 20점 추가
        #   preference:
        #     matchExpressions:
        #       - key: project
        #         operator: In
        #         values:
        #           - spring
```

기존 Pod를 모두 삭제하고 `node_affinity_preferred/`의 Boot·Nginx Manifest를 적용했다.

```console
$ kubectl apply -f .
pod/boot-pod-1 created
pod/nginx-pod-1 created

$ kubectl get pods -o wide
NAME          READY   STATUS    NODE
boot-pod-1    1/1     Running   ip-172-28-31-206.ap-northeast-2.compute.internal
nginx-pod-1   1/1     Running   ip-172-28-31-206.ap-northeast-2.compute.internal
```

두 Pod는 선호 조건을 만족하는 `ap-northeast-2c` Node에 배치됐다. `weight: 50`은 50% 확률이라는 뜻이 아니라, Scheduler가 후보 Node의 우선순위를 계산할 때 더하는 점수다.

여러 `preference`를 활성화하면 Node가 만족한 조건의 `weight`가 합산된다. 예를 들어 2c이면서 `project=spring`인 Node는 50점과 20점을 합쳐 70점을 받고, 2a이면서 `project=spring`인 Node는 60점을 받는다. 어느 조건도 만족하지 못한 Node도 배치 후보에서 제외되지는 않으며, 다른 Scheduling 조건을 통과했다면 낮은 점수로 선택될 수 있다.

| 표현 | 성격 | 일치하는 Node가 없을 때 |
|---|---|---|
| `requiredDuringSchedulingIgnoredDuringExecution` | Hard 조건 | Pod가 `Pending`에 머묾 |
| `preferredDuringSchedulingIgnoredDuringExecution` | Soft 선호 | 다른 Node에도 배치 가능 |

두 표현에 공통으로 들어가는 `IgnoredDuringExecution`은 Pod가 배치된 뒤 Node Label이 달라져도 이미 실행 중인 Pod를 자동으로 축출하지 않는다는 의미다.

같은 이름으로 Pod를 삭제·재생성했기 때문에 `kubectl get events`에는 앞서 삭제된 Boot Pod의 `FailedScheduling` Event가 잠시 남아 있었다. 현재 상태는 `kubectl get pods`와 Pod의 생성 시각을 함께 기준으로 판단해야 한다.

## EX.7 Taints와 Tolerations 실습

### 개념과 명령 구조

NodeAffinity가 Pod 입장에서 원하는 Node를 고르는 규칙이라면, Taint는 Node 입장에서 받아들이지 않을 Pod를 밀어내는 규칙이다. Toleration은 Pod가 특정 Taint를 견딜 수 있다고 선언하는 예외표다.

```text
NodeAffinity  → Pod가 "저 Node로 가고 싶다"고 요청
Taint         → Node가 "조건 없는 Pod는 들어오지 마라"고 제한
Toleration    → Pod가 "나는 그 제한을 견딜 수 있다"고 선언
```

실습에서 사용한 Taint 명령의 구조는 다음과 같다.

```bash
kubectl taint nodes <Node 이름> nodename=node2:NoExecute
```

```text
kubectl                 Kubernetes에 명령
taint nodes             Node에 Taint를 추가
<Node 이름>             실제 적용 대상
nodename=node2          Taint의 Key와 Value
NoExecute               일치하는 Toleration이 없는 기존 Pod까지 축출
```

`NoSchedule`은 Toleration이 없는 새 Pod의 배치만 막고 기존 Pod는 남겨 둔다. `NoExecute`는 새 배치를 막는 것에 더해 이미 실행 중인 Pod도 축출한다.

### 세 Manifest의 Toleration 차이

`taint-tolerations/`의 세 Pod는 Toleration 범위를 비교하도록 구성됐다.

`boot-pod-1`은 Key를 지정하지 않아 모든 Key의 `NoExecute`를 견딘다.

```yaml
tolerations:
  - effect: NoExecute
    operator: Exists
```

`boot-pod-2`와 `nginx-pod-1`은 Key가 `test`인 `NoExecute`만 견딘다. `Exists`이므로 `test`의 Value는 무엇이든 허용하지만, 다른 Key는 허용하지 않는다.

```yaml
tolerations:
  - key: test
    effect: NoExecute
    operator: Exists
```

Toleration은 Pod를 해당 Node로 보내는 배치 지시가 아니다. 조건에 맞는 Taint가 있어도 거부·축출되지 않을 자격만 준다.

### 같은 Node에서 생존·축출 비교

Toleration 차이만 비교하기 위해 기존 Pod와 2c Node의 `NoExecute`를 정리하고, 2a Node를 잠시 `cordon`했다. 그 상태에서 세 Pod를 생성해 모두 2c Node에 배치했다.

```console
$ kubectl cordon ip-172-28-11-97.ap-northeast-2.compute.internal
node/ip-172-28-11-97.ap-northeast-2.compute.internal cordoned

$ kubectl apply -f .
pod/boot-pod-1 created
pod/boot-pod-2 created
pod/nginx-pod-1 created

$ kubectl get pods -o wide
NAME          READY   STATUS    NODE
boot-pod-1    1/1     Running   ip-172-28-31-206.ap-northeast-2.compute.internal
boot-pod-2    1/1     Running   ip-172-28-31-206.ap-northeast-2.compute.internal
nginx-pod-1   1/1     Running   ip-172-28-31-206.ap-northeast-2.compute.internal
```

세 Pod가 같은 Node에 있는 것을 확인한 뒤 2a Node를 다시 `uncordon`하고, 2c Node에 `nodename=node2:NoExecute`를 적용했다.

```console
$ kubectl uncordon ip-172-28-11-97.ap-northeast-2.compute.internal
node/ip-172-28-11-97.ap-northeast-2.compute.internal uncordoned

$ kubectl taint nodes ip-172-28-31-206.ap-northeast-2.compute.internal \
  nodename=node2:NoExecute
node/ip-172-28-31-206.ap-northeast-2.compute.internal tainted
```

결과는 Toleration 범위에 따라 갈렸다.

| Pod | `NoExecute` 허용 범위 | 결과 |
|---|---|---|
| `boot-pod-1` | 모든 Key | 2c Node에서 계속 `Running` |
| `boot-pod-2` | `test` Key만 | `nodename`과 불일치하여 축출·삭제 |
| `nginx-pod-1` | `test` Key만 | `nodename`과 불일치하여 축출·삭제 |

Event에서도 두 Pod의 축출이 확인됐다.

```text
TaintManagerEviction pod/boot-pod-2
Marking for deletion Pod default/boot-pod-2

TaintManagerEviction pod/nginx-pod-1
Marking for deletion Pod default/nginx-pod-1
```

최종적으로 `boot-pod-1`만 2c Node에서 살아남았다. 세 Pod를 같은 Node에 먼저 모았기 때문에, 다른 Node에 있었던 우연이 아니라 Toleration 일치 여부로 결과가 갈렸음을 확인할 수 있다.

### 실제 상황으로 이해하기

Node를 작업장, Taint를 출입 제한 표지, Toleration을 예외 출입증으로 생각할 수 있다.

```text
NoSchedule
→ "지금부터 일반 작업자는 새로 들어오지 마시오"
→ 이미 안에 있는 작업자는 계속 일함

NoExecute
→ "일반 작업자는 즉시 퇴실하시오"
→ 예외 출입증이 있는 작업자만 남음
```

실무에서 가장 흔한 용도는 **특정 Node를 전용 구역으로 예약하는 것**이다.

- GPU Node: 비싼 GPU가 필요한 Pod만 Toleration을 주고, 일반 Pod가 자리를 차지하지 못하게 한다.
- 보안·운영 전용 Node: Log 수집기나 보안 Agent처럼 관리 Workload만 들어가게 한다.
- 장애가 감지된 Node: `not-ready`, `memory-pressure`, `disk-pressure` 같은 상태에 따라 Kubernetes가 Taint를 붙이고 새 배치를 막거나 Pod를 축출한다.

Toleration은 출입 허가일 뿐 해당 Node로 끌어당기지는 않는다. 전용 Workload를 그 Node에 확실히 보내려면 같은 Label을 붙이고 NodeAffinity도 함께 사용하는 것이 일반적이다. Kubernetes 공식 문서도 전용 Node와 특수 Hardware를 대표 용례로 들고 있다: [Taints and Tolerations](https://kubernetes.io/docs/concepts/scheduling-eviction/taint-and-toleration/)

보안 사고 상황에 적용하면 다음과 같이 이해할 수 있다. Worker Node에서 악성 Process, Kernel 이상, Disk 장애처럼 심각한 문제가 의심된다고 가정한다.

1. 운영자는 해당 Node에 `NoExecute` Taint를 붙여 일반 Workload를 축출한다.
2. 일반 애플리케이션 Pod는 해당 Node에서 제거된다.
3. 장애 조사·Log 수집·보안 감시처럼 반드시 남아야 하는 관리 Pod만 정확한 Toleration으로 유지할 수 있다.
4. Deployment나 ReplicaSet이 관리하는 애플리케이션이라면 Controller가 건강한 다른 Node에 대체 Pod를 생성한다.
5. 조사와 증거 보존 후 문제가 확인된 Node는 복구하거나 폐기·재생성한다.

이번 실습을 이 상황에 비유하면 `boot-pod-2`와 `nginx-pod-1`은 일반 애플리케이션이고, 모든 `NoExecute`를 견딘 `boot-pod-1`은 예외 출입증을 가진 관리 작업의 역할을 맡았다고 볼 수 있다. 실제 `boot-pod-1`이 보안 관리 Pod라는 뜻은 아니다.

다만 Taint는 침해를 탐지하거나 Network를 차단하는 보안 기능이 아니다. 실제 침해 대응에서는 Audit Log·Runtime 탐지로 상황을 판단하고, Security Group·NetworkPolicy·Credential 폐기 등으로 격리한 뒤 Taint·cordon·drain·Node 재생성을 함께 사용해야 한다. 또한 Key 없는 광범위한 Toleration은 원치 않는 위험 Node에서도 Pod를 살려둘 수 있으므로, 실무에서는 필요한 Key·Value·Effect만 좁게 허용하는 편이 안전하다.

## EX.8 cordon과 drain 실습

### 실습 목적과 전체 흐름

이번 실습은 다음 차이를 직접 확인하는 데 목적이 있다.

```text
cordon
→ 해당 Node에 새 Pod를 배치하지 못하게 함
→ 이미 실행 중인 Pod는 그대로 유지

drain
→ Node를 cordon 상태로 만듦
→ 해당 Node의 일반 Pod를 안전하게 축출
→ 유지보수·교체 전에 Node를 비우는 작업
```

이번에는 두 Node를 순서대로 모두 `cordon`한 뒤 새 Pod가 `Pending`되는 것을 확인하고, 이어 두 Node를 모두 `drain`해 기존 일반 Pod까지 제거하는 확장 실험을 수행했다.

실제 흐름은 다음과 같다.

```text
1. 2c Node에 boot-pod-1·myapp 실행
2. 2c Node cordon
3. 새 Pod를 Apply → 열려 있는 2a Node에 배치
4. 2a Node도 cordon
5. pod-env·pod-net을 다시 생성 → 배치 가능한 Node가 없어 Pending
6. 2a Node drain 시도 → 독립 Pod·DaemonSet 안전장치에 막힘
7. 필요한 옵션을 붙여 재시도 → CoreDNS PDB에서 다시 막힘
8. 의도적인 전체 중단 실험을 위해 PDB를 우회해 양쪽 Node drain
9. Manifest를 다시 Apply → 모든 일반 Pod가 Pending
10. default Namespace의 실습 Pod 전체 삭제
```

### 1단계: cordon은 기존 Pod를 건드리지 않는다

먼저 2c Node에 `boot-pod-1`과 `myapp`이 실행 중인 상태에서 2c Node를 `cordon`했다.

```console
$ kubectl cordon ip-172-28-31-206.ap-northeast-2.compute.internal
node/ip-172-28-31-206.ap-northeast-2.compute.internal cordoned
```

그 뒤 다른 Pod를 생성하자 기존 두 Pod는 2c Node에서 계속 실행됐고, 새 Pod는 아직 열려 있던 2a Node에 배치됐다. 즉 `cordon`은 기존 Pod를 축출하지 않는다.

```text
2c Node: boot-pod-1·myapp 계속 Running
2a Node: pod-env·pod-net·pod-sidecar·ubuntu-pod 신규 배치
```

이후 2a Node도 `cordon`하고 `pod-env`와 `pod-net`을 삭제·재생성했다.

```console
$ kubectl cordon ip-172-28-11-97.ap-northeast-2.compute.internal
node/ip-172-28-11-97.ap-northeast-2.compute.internal cordoned

$ kubectl apply -f .
pod/pod-env created
pod/pod-net created
```

두 Node가 모두 `SchedulingDisabled`이므로 새로 생성한 두 Pod에는 IP와 Node가 할당되지 않았다.

```text
pod-env   0/1   Pending   IP=<none>   NODE=<none>
pod-net   0/1   Pending   IP=<none>   NODE=<none>
```

반면 먼저 실행 중이던 Pod는 그대로 남았다. 이 결과로 `cordon`은 **신규 Scheduling만 막고 기존 실행을 유지한다**는 것을 확인했다.

### 2단계: 옵션 없는 drain이 중단된 이유

2a Node에 기본 `drain`을 실행했다.

```console
$ kubectl drain ip-172-28-11-97.ap-northeast-2.compute.internal
node/ip-172-28-11-97.ap-northeast-2.compute.internal already cordoned
```

명령은 다음 두 안전장치 때문에 중단됐다.

```text
cannot delete Pods that declare no controller:
  default/pod-sidecar, default/ubuntu-pod

cannot delete DaemonSet-managed Pods:
  kube-system/aws-node-ps6gt
  kube-system/eks-pod-identity-agent-9677l
  kube-system/kube-proxy-llh4x
```

- `pod-sidecar`, `ubuntu-pod`는 ReplicaSet·Deployment 같은 Controller가 없는 독립 Pod다. 삭제되면 자동 복구되지 않으므로 `drain`이 기본적으로 보호한다.
- `aws-node`, `eks-pod-identity-agent`, `kube-proxy`는 각 Node마다 실행되는 DaemonSet Pod다. Node가 존재하는 한 Controller가 다시 만들 수 있어 일반 Pod처럼 Drain할 수 없다.

### drain 옵션의 의미와 사용 이유

이번에 사용한 전체 명령은 다음과 같다.

```bash
kubectl drain <Node 이름> \
  --ignore-daemonsets \
  --delete-emptydir-data \
  --force \
  --disable-eviction
```

| 옵션 | 정확한 의미 | 이번에 필요했던 이유 | 주의점 |
|---|---|---|---|
| `--ignore-daemonsets` | DaemonSet 관리 Pod를 Drain 대상에서 제외하고 작업을 계속한다. | EKS Node마다 `aws-node`, `kube-proxy`, `eks-pod-identity-agent`가 있어 옵션 없이는 중단됐다. | DaemonSet Pod를 삭제한다는 뜻이 아니다. Drain 후에도 해당 Node에 남는다. |
| `--delete-emptydir-data` | `emptyDir`을 사용하는 Pod가 있어도 Local 임시 Data가 사라지는 것을 감수하고 계속한다. | 강의의 표준 Drain 명령에 포함되며, 다양한 Workload가 있는 Node에서도 Local 임시 Data 때문에 중단되지 않게 한다. | `emptyDir` Data는 Node 밖으로 이동하지 않으므로 실제 운영에서는 손실 가능성을 먼저 확인해야 한다. |
| `--force` | Controller가 없는 독립 Pod도 삭제할 수 있게 한다. | 현재 실습 Pod가 모두 직접 생성한 독립 Pod라서 필요했다. | 자동 재생성을 보장하지 않는다. 또한 PDB를 무시하는 옵션도 아니다. |
| `--disable-eviction` | Eviction API 대신 Delete를 사용해 PodDisruptionBudget 검사를 우회한다. | 두 Node를 모두 닫은 의도적 중단 실험에서 마지막 CoreDNS가 PDB로 보호돼 Drain이 끝나지 않았기 때문에 사용했다. | 서비스 가용성을 깨뜨릴 수 있는 위험 옵션이다. 정상 유지보수에서는 기본적으로 사용하지 않는다. |

옵션은 단순히 “강하게 삭제”하는 같은 기능이 아니다.

```text
--force
→ 이 Pod는 Controller가 없어도 삭제해도 된다고 승인

--ignore-daemonsets
→ DaemonSet은 남겨 두고 나머지만 비우겠다고 승인

--delete-emptydir-data
→ Node Local 임시 Data 손실을 승인

--disable-eviction
→ PDB가 보장하는 가용성까지 포기하고 Delete 사용
```

### 3단계: PDB가 첫 Drain을 멈춘 과정

먼저 PDB 우회 없이 다음 명령을 실행했다.

```bash
kubectl drain ip-172-28-11-97.ap-northeast-2.compute.internal \
  --ignore-daemonsets \
  --delete-emptydir-data \
  --force
```

이 명령으로 독립 Pod인 `pod-sidecar`, `ubuntu-pod`와 CoreDNS 한 개는 축출됐다. 그러나 두 Node가 모두 `cordon` 상태라 대체 CoreDNS는 새 Node를 찾지 못하고 `Pending`이 됐다.

CoreDNS의 PDB는 동시에 사용할 수 없는 Replica 수를 제한하고 있었으며 당시 `ALLOWED DISRUPTIONS`는 `0`이었다. 따라서 마지막 실행 중인 CoreDNS까지 축출하면 DNS 가용성이 완전히 사라지므로 Eviction API가 요청을 거부했다.

```text
Cannot evict pod as it would violate the pod's disruption budget.
will retry after 5s
```

실제로 5초 간격으로 세 번 관찰해도 다음 상태가 유지됐다.

```text
기존 CoreDNS 1개: Running
대체 CoreDNS 1개: Pending
CoreDNS PDB ALLOWED DISRUPTIONS: 0
drain: 마지막 CoreDNS Eviction을 반복 재시도
```

이는 오작동이 아니라, 운영자가 동시에 너무 많은 Pod를 중단하지 못하도록 PDB가 가용성을 지킨 결과다.

### 4단계: 의도적 전체 중단을 위한 PDB 우회

이번 실험의 목표는 양쪽 Node를 모두 비우고 신규 Scheduling도 불가능한 상태를 확인하는 것이었다. 반복 중인 명령을 `Ctrl+C`로 중단하고, 실습 환경에서만 `--disable-eviction`을 추가했다.

```console
$ kubectl drain ip-172-28-11-97.ap-northeast-2.compute.internal \
    --ignore-daemonsets \
    --delete-emptydir-data \
    --force \
    --disable-eviction
pod/coredns-7c6bdc968c-l6ds4 deleted
node/ip-172-28-11-97.ap-northeast-2.compute.internal drained
```

이어서 2c Node에도 같은 명령을 적용했다.

```console
$ kubectl drain ip-172-28-31-206.ap-northeast-2.compute.internal \
    --ignore-daemonsets \
    --delete-emptydir-data \
    --force \
    --disable-eviction
pod/boot-pod-1 deleted
pod/myapp deleted
node/ip-172-28-31-206.ap-northeast-2.compute.internal drained
```

### 5단계: 두 Node가 닫힌 상태에서 재배포

Drain 이후 같은 Manifest를 다시 적용했다.

```console
$ kubectl apply -f .
pod/myapp created
pod/pod-env configured
pod/pod-net unchanged
pod/pod-sidecar created
pod/ubuntu-pod created
```

두 Node가 모두 `Ready,SchedulingDisabled`이므로 모든 일반 Pod가 생성은 됐지만 배치되지는 않았다.

```text
myapp         0/1   Pending   IP=<none>   NODE=<none>
pod-env       0/1   Pending   IP=<none>   NODE=<none>
pod-net       0/1   Pending   IP=<none>   NODE=<none>
pod-sidecar   0/2   Pending   IP=<none>   NODE=<none>
ubuntu-pod    0/1   Pending   IP=<none>   NODE=<none>
```

마지막으로 실습 Pod를 정리했다. 첫 명령은 Resource 종류가 없어 실패했고, `pod`를 명시한 두 번째 명령이 성공했다.

```console
$ kubectl delete --all
error: at least one resource must be specified to use a selector

$ kubectl delete pod --all
pod "myapp" deleted
pod "pod-env" deleted
pod "pod-net" deleted
pod "pod-sidecar" deleted
pod "ubuntu-pod" deleted

$ kubectl get pod
No resources found in default namespace.
```

### 결과와 실무 해석

최종 상태는 다음과 같다.

- Worker Node 2대 모두 `Ready,SchedulingDisabled`
- `default` Namespace의 실습 Pod 없음
- CoreDNS 대체 Pod 2개는 배치 가능한 Node가 없어 `Pending`
- DaemonSet인 `aws-node`, `kube-proxy`, `eks-pod-identity-agent`는 각 Node에 계속 실행

실무에서 `drain`은 Server 점검, Kernel Upgrade, Node Group 교체처럼 Node를 안전하게 서비스에서 제외할 때 사용한다. 보통은 **한 Node씩** Drain하고, 다른 Node에 대체 Pod가 정상 배치된 것을 확인한 뒤 다음 Node로 넘어간다. 이번처럼 모든 Worker Node를 동시에 닫고 `--disable-eviction`으로 PDB까지 우회한 것은 `cordon`, `drain`, Controller, PDB의 차이를 확인하기 위한 의도적인 장애 실험이다.

복구할 때는 Node를 다시 Scheduling 대상으로 연다.

```bash
kubectl uncordon ip-172-28-11-97.ap-northeast-2.compute.internal
kubectl uncordon ip-172-28-31-206.ap-northeast-2.compute.internal
```

이후 `kubectl get nodes`와 `kubectl get pods -A -o wide`로 Node가 `Ready`인지, CoreDNS가 다시 `Running`인지 확인해야 한다.


## 오류와 해석 요약

| 증상 | 확인한 원인 또는 현재 판단 | 조치·다음 확인 |
|---|---|---|
| Boot·Nginx Pod 6개 `Pending` | Node의 `project=melong`이 Pod의 `project=boot/nginx` Selector와 불일치 | Node Label을 `project=boot --overwrite`로 보정 |
| Required NodeAffinity Boot Pod `Pending` | `key: melong`, `operator: Exists`지만 어떤 Node에도 `melong` Key가 없음 | 필수 조건과 Node Label을 일치시키거나 Soft 조건 사용 |
| `NoExecute` 적용 후 Pod 두 개가 사라짐 | `test` Toleration이 `nodename` Taint와 일치하지 않아 Taint Manager가 축출 | 의도된 결과이며 Event의 `TaintManagerEviction`으로 확인 |
| 기본 `drain`이 독립 Pod·DaemonSet에서 중단 | Controller 없는 Pod와 DaemonSet을 기본 안전장치가 보호 | 실습 의도 확인 후 `--force`, `--ignore-daemonsets` 사용 |
| Drain이 CoreDNS에서 5초마다 반복 | 두 Node가 cordon되어 대체 CoreDNS가 `Pending`이고 PDB 허용 중단 수가 0 | 정상 운영은 다른 Node를 열어 가용성 회복, 전체 중단 실험만 `--disable-eviction` 사용 |
| `kubectl delete --all` 실패 | 삭제할 Resource 종류가 없음 | `kubectl delete pod --all`처럼 Resource 명시 |
| Zone Selector 변경 Apply가 Boot Pod만 실패 | 기존 Boot Pod의 `nodeSelector`는 생성 후 변경 불가 | 기존 Pod 삭제 후 새 Manifest로 재생성 |
| `cd ..\node_selectors` 실패 | Linux에서 Windows식 경로 구분자 사용 | `cd ../node_selectors` |

## 검증 완료와 미완료

### 완료

- Required·Preferred NodeAffinity의 Hard·Soft 배치 차이
- `NoExecute`와 Toleration 일치 여부에 따른 생존·축출 비교
- `cordon`의 신규 Scheduling 차단과 기존 Pod 유지 확인
- 두 Node Drain, 독립 Pod·DaemonSet 안전장치, CoreDNS PDB 차단·우회 확인
- CoreDNS PDB의 Drain 차단과 의도적 우회
- 두 Node가 닫힌 상태에서 일반 Pod 전체 `Pending` 확인

### 미완료·추가 증거 필요

- 다음 EKS 환경에서 사용자 지정 `project` Node Label 정리 상태 확인
- 정상 운영 방식으로 한 Node씩 Drain하고 대체 Pod가 다른 Node에서 `Running`이 되는 과정

## 다음 재시작 지점

- ReplicaSet 실습은 [[Lab_EKS ReplicaSet 기초 실습]]에서 이어진다.

## 관련 노트

- [[Lab_EKS 첫 접속과 Pod 기초 실습]]
- [[04_Kubernetes Pod와 ReplicaSet]]
- [[Source Digest/Kubernetes - Source Digest 04 Pod and ReplicaSet]]

## 공식 참고

- [Taints and Tolerations](https://kubernetes.io/docs/concepts/scheduling-eviction/taint-and-toleration/)
- [kubectl drain](https://kubernetes.io/docs/reference/kubectl/generated/kubectl_drain/)
- [Safely Drain a Node](https://kubernetes.io/docs/tasks/administer-cluster/safely-drain-node/)
- [Disruptions와 PodDisruptionBudget](https://kubernetes.io/docs/concepts/workloads/pods/disruptions/)
