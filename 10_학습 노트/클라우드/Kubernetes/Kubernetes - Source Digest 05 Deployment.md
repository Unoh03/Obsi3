---
type: source-digest
status: stable
created: 2026-07-21
parent_moc: "[[10_학습 노트/클라우드/Kubernetes/00_Kubernetes MOC]]"
source: "[[40_자료/강의 자료/Kubernetes.pdf]]"
source_pages: "74-109"
digest_role: chapter
digest_index: "[[10_학습 노트/클라우드/Kubernetes/Kubernetes - Source Digest v1]]"
chapter: "Kubernetes Deployment"
source_hash: F97666865E22749C47640689B5C41DEE38476A40312A53915F60B4F6A4330D24
source_version: "PowerPoint PDF; 266 pages; metadata created 2024-07-18"
coverage_status: complete
extraction_method: "pdfplumber 0.11.9 text extraction + pypdfium2 render visual review"
reviewed_on: 2026-07-21
---

# Kubernetes - Source Digest 05 Deployment

> [!summary]
> `Kubernetes.pdf` p.74-p.109의 Deployment 원자료를 페이지 순서대로 구조화한 Chapter Digest다. 원자료 내용을 현재 지식으로 교정하지 않았으며, 명령·YAML·출력·도식의 의미를 렌더링과 대조했다.

## Coverage

| 범위 | 내용 | 처리 상태 |
|---:|---|---|
| p.74-p.75 | Deployment 표지와 Controller 개요 | Text·Visual 대조 |
| p.76-p.87 | Basic, Rollout, Revision | YAML·명령·출력 대조 |
| p.88-p.102 | Recreate와 Rolling-Update | Text·YAML·명령·단계 도식 대조 |
| p.103-p.109 | Namespace | Text·YAML·명령·도식 대조 |

## PDF p.74 - Kubernetes Deployment 표지

- 원문: [[40_자료/강의 자료/Kubernetes.pdf#page=74|Kubernetes.pdf p.74]]
- `Kubernetes Deployment` Chapter의 구분 표지이며 정보성 본문은 없다.

## PDF p.75 - Deployment Controller 개요

- 원문: [[40_자료/강의 자료/Kubernetes.pdf#page=75|Kubernetes.pdf p.75]]

### 원자료 내용

- Deployment는 Pod 배포 자동화를 수행하는 Controller다.
- Pod의 Rollout(Update)·Rollback에 쓰이는 ReplicaSet을 관리하며 ReplicaSet의 상위 Object로 설명한다.
- Revision을 이용한 Rollback과 무중단 배포를 위한 Rolling-Update를 지원한다고 설명한다.

### 도식 의미

- 하나의 Deployment가 `Old Pod Area (V1)`와 `New Pod Area (V2)`의 ReplicaSet을 관리한다.
- 각 ReplicaSet은 `replicas: 2`이며 Worker Node 1·2에 Pod가 배치된다.
- V1에서 V2로 향하는 화살표는 `Rollout`, V2에서 V1로 돌아오는 화살표는 `Rollback`이다.

## PDF p.76 - Basic Deployment Manifest

- 원문: [[40_자료/강의 자료/Kubernetes.pdf#page=76|Kubernetes.pdf p.76]]
- 작업 파일: `deployment-basic.yml`

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-deployment
spec:
  replicas: 3
  selector:
    matchLabels:
      app: my-app
  template:
    metadata:
      labels:
        app: my-app
    spec:
      containers:
        - name: my-nginx
          image: nginx:1.22
          ports:
            - containerPort: 80
```

- ReplicaSet Manifest와 유사한 구조라고 설명한다.
- `replicas`가 복제 Pod 수를 정의한다.
- `selector.matchLabels`가 선택할 Pod Template의 Label을 지정하며, `app: my-app`이 Template Label과 반드시 일치해야 한다.
- 렌더링에서는 selector에서 Template Label로 연결되는 선과 Template Container가 별도 Box로 표시된다.

## PDF p.77 - Basic Deployment 생성과 Object 관계 확인

- 원문: [[40_자료/강의 자료/Kubernetes.pdf#page=77|Kubernetes.pdf p.77]]

```console
$ kubectl apply -f ./deployment-basic.yml
$ kubectl get deploy -o wide
NAME           READY   UP-TO-DATE   AVAILABLE   AGE    CONTAINERS   IMAGES       SELECTOR
my-deployment  3/3     3            3           107s   my-nginx     nginx:1.22   app=my-app

$ kubectl describe deploy my-deployment
Events:
Normal  ScalingReplicaSet  deployment-controller  Scaled up replica set my-deployment-79b4f9588f to 3

$ kubectl get rs --show-labels
NAME                      DESIRED   CURRENT   READY   AGE     LABELS
my-deployment-5c8448bb6b  3         3         3       8m29s   app=my-app,pod-template-hash=5c8448bb6b

$ kubectl get pod --show-labels
NAME                               READY   STATUS    RESTARTS   AGE     LABELS
my-deployment-5c8448bb6b-9kz4k    1/1     Running   0          9m10s   app=my-app,pod-template-hash=5c8448bb6b
my-deployment-5c8448bb6b-qhwqb    1/1     Running   0          9m10s   app=my-app,pod-template-hash=5c8448bb6b
my-deployment-5c8448bb6b-xl85r    1/1     Running   0          9m10s   app=my-app,pod-template-hash=5c8448bb6b
```

- Deployment가 ReplicaSet 하나를 3개 Pod로 Scale Up하고 ReplicaSet·Pod에 동일한 `pod-template-hash`가 붙는 결과를 보여준다.

## PDF p.78 - Scale을 이용한 replicas 변경

- 원문: [[40_자료/강의 자료/Kubernetes.pdf#page=78|Kubernetes.pdf p.78]]

```console
$ kubectl scale deploy my-deployment --replicas=5
$ kubectl get rs --show-labels
my-deployment-5c8448bb6b   DESIRED=5   CURRENT=5   READY=5

$ kubectl get pod --show-labels
my-deployment-5c8448bb6b-9kz4k   Running
my-deployment-5c8448bb6b-f72c4   Running
my-deployment-5c8448bb6b-kzndj   Running
my-deployment-5c8448bb6b-qhwqb   Running
my-deployment-5c8448bb6b-xl85r   Running

$ kubectl describe deploy my-deployment
Scaled up replica set my-deployment-5c8448bb6b to 3
Scaled up replica set my-deployment-5c8448bb6b to 5
```

- 같은 ReplicaSet이 3개에서 5개 Pod로 확장되는 것을 확인한다.

## PDF p.79 - Pod Template Label 변경

- 원문: [[40_자료/강의 자료/Kubernetes.pdf#page=79|Kubernetes.pdf p.79]]

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-deployment
spec:
  replicas: 3
  selector:
    matchLabels:
      app: my-app
  template:
    metadata:
      labels:
        app: my-app
        env: prod
    spec:
      containers:
        - name: my-nginx
          image: nginx:1.22
          ports:
            - containerPort: 80
```

- Update Test를 위해 Pod Template에 `env: prod` Label을 추가한다.

## PDF p.80 - 새 ReplicaSet과 Pod 생성

- 원문: [[40_자료/강의 자료/Kubernetes.pdf#page=80|Kubernetes.pdf p.80]]

```console
$ kubectl apply -f deployment/deployment-basic.yml
deployment.apps/my-deployment configured

$ kubectl get rs --show-labels
my-deployment-5c8448bb6b   0   0   0   app=my-app,pod-template-hash=5c8448bb6b
my-deployment-74d6d7448d   3   3   3   app=my-app,env=prod,pod-template-hash=74d6d7448d

$ kubectl get pod --show-labels
my-deployment-74d6d7448d-kcbvb   Running   app=my-app,env=prod,pod-template-hash=74d6d7448d
my-deployment-74d6d7448d-tt4dr   Running   app=my-app,env=prod,pod-template-hash=74d6d7448d
my-deployment-74d6d7448d-vxxd7   Running   app=my-app,env=prod,pod-template-hash=74d6d7448d
```

- 이전 ReplicaSet의 목표·현재 Pod 수가 0이 되고 새 `pod-template-hash`를 가진 ReplicaSet과 Pod 3개가 생긴다.

## PDF p.81 - Rollout Event 순서

- 원문: [[40_자료/강의 자료/Kubernetes.pdf#page=81|Kubernetes.pdf p.81]]

```text
OLD ReplicaSet: my-deployment-5c8448bb6b
NEW ReplicaSet: my-deployment-74d6d7448d

OLD[5→3] → NEW[0→1] → OLD[3→2] → NEW[1→2]
→ OLD[2→1] → NEW[2→3] → OLD[1→0]
```

- `kubectl describe deploy` Event는 이전 ReplicaSet을 5→3→2→1→0으로 내리면서 새 ReplicaSet을 0→1→2→3으로 올린 순서를 기록한다.

## PDF p.82 - Container Image 변경

- 원문: [[40_자료/강의 자료/Kubernetes.pdf#page=82|Kubernetes.pdf p.82]]

```yaml
template:
  metadata:
    labels:
      app: my-app
      env: prod
  spec:
    containers:
      - name: my-nginx
        image: nginx:latest
        ports:
          - containerPort: 80
```

- p.79 Manifest에서 Image만 `nginx:1.22`에서 `nginx:latest`로 변경한다.

## PDF p.83 - Image 변경 후 새 Revision

- 원문: [[40_자료/강의 자료/Kubernetes.pdf#page=83|Kubernetes.pdf p.83]]

```console
$ kubectl apply -f ./deployment-basic.yml
deployment.apps/my-deployment configured

$ kubectl get rs --show-labels
my-deployment-5c8448bb6b   0   0   0   app=my-app,pod-template-hash=5c8448bb6b
my-deployment-6f5579bcb    3   3   3   app=my-app,env=prod,pod-template-hash=6f5579bcb
my-deployment-74d6d7448d   0   0   0   app=my-app,env=prod,pod-template-hash=74d6d7448d

$ kubectl get pod --show-labels
my-deployment-6f5579bcb-77lm8   Running   app=my-app,env=prod,pod-template-hash=6f5579bcb
my-deployment-6f5579bcb-8m2vx   Running   app=my-app,env=prod,pod-template-hash=6f5579bcb
my-deployment-6f5579bcb-vzmrd   Running   app=my-app,env=prod,pod-template-hash=6f5579bcb
```

- 세 ReplicaSet이 남지만 새 `6f5579bcb`만 3개 Pod를 운용한다.

## PDF p.84 - 두 번째 Rollout Event 순서

- 원문: [[40_자료/강의 자료/Kubernetes.pdf#page=84|Kubernetes.pdf p.84]]

```text
OLD ReplicaSet: my-deployment-74d6d7448d
NEW ReplicaSet: my-deployment-6f5579bcb

NEW[0→1] → OLD[3→2] → NEW[1→2]
→ OLD[2→1] → NEW[2→3] → OLD[1→0]
```

- Event는 새 ReplicaSet Scale Up과 이전 ReplicaSet Scale Down을 교대로 수행한 순서를 보여준다.

## PDF p.85 - Revision History와 직전 Revision Rollback

- 원문: [[40_자료/강의 자료/Kubernetes.pdf#page=85|Kubernetes.pdf p.85]]

```console
$ kubectl rollout history deploy my-deployment
REVISION   CHANGE-CAUSE
1          <none>
2          <none>
3          <none>

$ kubectl rollout history deploy/my-deployment --revision=1
$ kubectl rollout undo deploy my-deployment
deployment.apps/my-deployment rolled back

$ kubectl get rs --show-labels
my-deployment-5c8448bb6b   0   0   0
my-deployment-6f5579bcb    0   0   0
my-deployment-74d6d7448d   3   3   3
```

- 총 3개 Revision이 있으며 `rollout undo`가 직전 Revision의 기존 ReplicaSet을 다시 사용한다.

## PDF p.86 - Change Cause와 특정 Revision Rollback

- 원문: [[40_자료/강의 자료/Kubernetes.pdf#page=86|Kubernetes.pdf p.86]]

```console
$ kubectl annotate deploy my-deployment kubernetes.io/change-cause="image-rollback"
$ kubectl rollout history deploy my-deployment
REVISION   CHANGE-CAUSE
1          <none>
3          <none>
4          image-rollback

$ kubectl rollout undo deploy my-deployment --to-revision=1
deployment.apps/my-deployment rolled back

$ kubectl get rs --show-labels
my-deployment-5c8448bb6b   3   3   3
my-deployment-6f5579bcb    0   0   0
my-deployment-74d6d7448d   0   0   0
```

- 현재 Revision에 `kubernetes.io/change-cause` Annotation을 붙여 Rollback 사유를 기록한다.
- 특정 Revision은 `--to-revision=<Revision Num>`으로 지정하며 생략 시 직전 Revision이라고 설명한다.

## PDF p.87 - Revision Annotation과 정리

- 원문: [[40_자료/강의 자료/Kubernetes.pdf#page=87|Kubernetes.pdf p.87]]

```console
$ kubectl annotate deploy my-deployment kubernetes.io/change-cause="First-rollback"
$ kubectl rollout history deploy my-deployment
REVISION   CHANGE-CAUSE
3          <none>
4          image-rollback
5          First-rollback

$ kubectl delete deploy my-deployment
deployment.apps "my-deployment" deleted
$ kubectl get deploy my-deployment
Error from server (NotFound): deployments.apps "my-deployment" not found
$ kubectl get rs
No resources found in default namespace.
$ kubectl get pod
No resources found in default namespace.
```

## PDF p.88 - Recreate와 Rolling-Update

- 원문: [[40_자료/강의 자료/Kubernetes.pdf#page=88|Kubernetes.pdf p.88]]

### 원자료 내용

- Deployment의 Rollout 방식을 `Recreate`와 `Rolling-Update` 두 가지로 구분한다.
- Recreate는 이전 Pod를 즉시 모두 종료하므로 새 배포 완료 전 Service Down Time이 발생하며 개발·Test 환경에 적합하다고 설명한다.
- Rolling-Update는 새 Pod를 올리면서 이전 Pod를 순차 종료해 Service 중단을 최소화하며 운영 환경에 적합하다고 설명한다.

### 도식 의미

- Recreate는 `기존 Pod 전체 → Service Down Time → 새 Pod 전체` 순서다.
- Rolling-Update는 중간 단계에서 파란 기존 Pod와 빨간 새 Pod가 동시에 존재하고 마지막에 모두 새 Pod가 된다.

## PDF p.89 - maxUnavailable과 maxSurge

- 원문: [[40_자료/강의 자료/Kubernetes.pdf#page=89|Kubernetes.pdf p.89]]

- 두 속성은 숫자 또는 전체 replicas의 `%`로 지정하며 배포 속도와 일시적 Resource 사용량을 제어한다.
- `replicas=10`, `maxUnavailable=30%`이면 이전 Pod를 최대 3개 내리고 최소 7개를 유지한다: `10 - 3 = 7`.
- `replicas=10`, `maxSurge=30%`이면 새 Pod를 최대 3개 즉시 올리고 전체를 최대 13개까지 유지한다: `10 + 3 = 13`.

## PDF p.90 - RollingUpdate Manifest

- 원문: [[40_자료/강의 자료/Kubernetes.pdf#page=90|Kubernetes.pdf p.90]]

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-deployment
spec:
  replicas: 5
  selector:
    matchLabels:
      app: my-app
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxUnavailable: 2
      maxSurge: 1
  template:
    metadata:
      labels:
        app: my-app
    spec:
      containers:
        - name: my-nginx
          image: nginx:1.22
          ports:
            - containerPort: 80
```

- `type: Recreate`도 가능하며 Recreate에는 추가 RollingUpdate 속성을 정의하지 않는다고 설명한다.

## PDF p.91 - 초기 RollingUpdate 상태

- 원문: [[40_자료/강의 자료/Kubernetes.pdf#page=91|Kubernetes.pdf p.91]]

```console
$ kubectl apply -f deployment/deploy-rollingupdate.yml
deployment.apps/my-deployment created
$ kubectl get deploy my-deployment
my-deployment   READY=5/5   UP-TO-DATE=5   AVAILABLE=5

$ kubectl describe deploy my-deployment
Replicas:               5 desired | 5 updated | 5 total | 5 available | 0 unavailable
StrategyType:           RollingUpdate
MinReadySeconds:        0
RollingUpdateStrategy:  2 max unavailable, 1 max surge
```

- 계산 결과 최소 유지 Pod는 `5 - 2 = 3`, 최대 Pod는 `5 + 1 = 6`이다.

## PDF p.92 - Label과 Image 변경

- 원문: [[40_자료/강의 자료/Kubernetes.pdf#page=92|Kubernetes.pdf p.92]]

```yaml
template:
  metadata:
    labels:
      app: my-app
      env: prod
  spec:
    containers:
      - name: my-nginx
        image: nginx:lates
```

> [!warning]
> 렌더링의 Manifest에는 `nginx:lates`로 표시되지만 설명 문장은 `nginx:latest`로 변경했다고 적는다. 원자료 내부 철자 불일치를 그대로 기록한다.

## PDF p.93 - maxUnavailable 2 / maxSurge 1 Event

- 원문: [[40_자료/강의 자료/Kubernetes.pdf#page=93|Kubernetes.pdf p.93]]

```bash
kubectl apply -f deployment/deploy-rollingupdate.yml
kubectl describe deploy my-deployment
```

```text
OLD ReplicaSet: my-deployment-5c8448bb6b
NEW ReplicaSet: my-deployment-6f5579bcb

NEW[0→1] → OLD[5→3] → NEW[1→3] → OLD[3→2]
→ NEW[3→4] → OLD[2→1] → NEW[4→5] → OLD[1→0]
```

- Event에는 기존 ReplicaSet을 먼저 `5`로 Scale Up한 초기 상태도 기록되어 있다.
- Event는 새 ReplicaSet을 1개 올리고 이전 ReplicaSet을 2개 내린 뒤, 최소 Pod 수와 최대 Pod 수를 지키며 교대하는 순서를 보여준다.

## PDF p.94 - Rolling-Update 단계 도식 1

- 원문: [[40_자료/강의 자료/Kubernetes.pdf#page=94|Kubernetes.pdf p.94]]
- 파란 점선 Pod는 V1, 빨간 점선 Pod는 V2, 빨간 `X`는 종료된 이전 Pod다.
- 세 Frame은 `기존 5 + 신규 1`에서 시작하여 이전 Pod를 최대 2개씩 제거하고 신규 Pod를 늘리는 중간 단계를 보여준다.
- 텍스트 추출에는 Pod 개수·색상·`X`·시간 순서가 보존되지 않아 렌더링을 기준으로 해석했다.

## PDF p.95 - Rolling-Update 단계 도식 2

- 원문: [[40_자료/강의 자료/Kubernetes.pdf#page=95|Kubernetes.pdf p.95]]
- p.94의 연속 도식으로 이전 V1 Pod가 모두 `X` 처리되고 V2 Pod 5개만 남는 완료 상태까지 표현한다.

## PDF p.96 - replicas 3 / maxSurge 3 변경

- 원문: [[40_자료/강의 자료/Kubernetes.pdf#page=96|Kubernetes.pdf p.96]]

```yaml
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 3
  template:
    metadata:
      labels:
        app: my-app
        env: prod
    spec:
      containers:
        - name: my-nginx
          image: nginx:lates
```

- 기존 예제에서 `replicas: 5 → 3`, `maxSurge: 1 → 3`으로 바꾸고 `maxUnavailable`을 삭제한다.
- `nginx:lates` 철자는 원자료 표시 그대로다.

## PDF p.97 - 기본 maxUnavailable 확인

- 원문: [[40_자료/강의 자료/Kubernetes.pdf#page=97|Kubernetes.pdf p.97]]

```console
$ kubectl delete deploy my-deployment
deployment.apps/my-deployment deleted
$ kubectl apply -f deployment/deploy-rollingupdate.yml
deployment.apps/my-deployment created

$ kubectl describe deploy my-deployment
Replicas:               3 desired | 3 updated | 3 total | 3 available | 0 unavailable
StrategyType:           RollingUpdate
RollingUpdateStrategy:  25% max unavailable, 3 max surge
```

- Event 기록을 초기화하기 위해 기존 Deployment를 삭제하고 다시 배포한다.
- `maxUnavailable`을 생략하면 출력에 기본값 25%가 표시된다.
- 최대 유지 Pod 계산은 `replicas 3 + maxSurge 3 = 6`이다.

## PDF p.98 - project Label 추가

- 원문: [[40_자료/강의 자료/Kubernetes.pdf#page=98|Kubernetes.pdf p.98]]

```yaml
template:
  metadata:
    labels:
      app: my-app
      env: prod
      project: kube
```

- p.96 Manifest의 Pod Template에 `project: kube`를 추가한다.
- 그 밖의 `replicas: 3`, `maxSurge: 3`, `maxUnavailable` 삭제, `image: nginx:lates` 설정은 p.96과 동일하다.

## PDF p.99 - maxSurge를 replicas와 같게 둔 Event

- 원문: [[40_자료/강의 자료/Kubernetes.pdf#page=99|Kubernetes.pdf p.99]]

```text
OLD ReplicaSet: my-deployment-b4469cb67
NEW ReplicaSet: my-deployment-7b4bd8d6b7

NEW[0→3] → OLD[3→2] → OLD[2→0]
```

- 새 ReplicaSet을 한 번에 3개로 올린 뒤 기존 ReplicaSet을 0으로 내린다.
- `maxSurge`를 replicas만큼 지정하면 빠른 Update가 가능하지만 일시적으로 많은 Compute Resource를 소비한다고 설명한다.

> [!warning] 원자료 내부 불일치
> Event 출력의 ReplicaSet은 `my-deployment-6c6b7bc57d`와 `my-deployment-6b6b584974`인데, 페이지 하단 요약은 OLD/NEW를 `my-deployment-b4469cb67`와 `my-deployment-7b4bd8d6b7`로 적는다. 어느 Hash가 실제 대상이었는지는 이 PDF만으로 확정하지 않는다.

## PDF p.100 - maxSurge 3 단계 도식 1

- 원문: [[40_자료/강의 자료/Kubernetes.pdf#page=100|Kubernetes.pdf p.100]]
- 파란 V1 Pod 3개와 빨간 V2 Pod 3개가 동시에 존재하는 상태에서 이전 Pod가 제거되는 과정을 세 Frame으로 표현한다.
- p.99의 `NEW[0→3] → OLD[3→2] → OLD[2→0]` 순서를 시각화한다.

## PDF p.101 - maxSurge 3 단계 도식 2

- 원문: [[40_자료/강의 자료/Kubernetes.pdf#page=101|Kubernetes.pdf p.101]]
- p.100의 연속 도식이며 이전 V1 Pod가 모두 제거되고 신규 V2 Pod 3개만 남는 완료 상태를 보여준다.

## PDF p.102 - Deployment와 하위 Object 삭제

- 원문: [[40_자료/강의 자료/Kubernetes.pdf#page=102|Kubernetes.pdf p.102]]

```console
$ kubectl delete deploy my-deployment
deployment.apps "my-deployment" deleted
$ kubectl get deploy my-deployment
Error from server (NotFound): deployments.apps "my-deployment" not found
$ kubectl get rs
No resources found in default namespace.
$ kubectl get pod
No resources found in default namespace.
```

- Deployment를 삭제하면 관리하던 ReplicaSet과 Pod도 함께 삭제된다고 설명한다.
- 다음 Test 전에 기존 Object가 남았는지 반드시 확인하도록 지시한다.

## PDF p.103 - Namespace 개념

- 원문: [[40_자료/강의 자료/Kubernetes.pdf#page=103|Kubernetes.pdf p.103]]

### 원자료 내용

- Namespace는 Kubernetes Cluster 안에 논리적 작업 영역을 만든다.
- Test/Prod 또는 Project A/B를 분리하는 용도로 설명한다.
- 명령 적용 범위, Object, Compute Resource 할당, Network 영역을 구분한다고 설명한다.

### 도식 의미

- 같은 Cluster 안에 Test와 Prod Namespace가 별도 경계로 표시된다.
- 각각 Service·Pod·Deployment로 구성된 `App1`이 있으며 DNS 이름은 `app1.test.svc.cluster.local`, `app1.prod.svc.cluster.local`로 구분된다.

## PDF p.104 - Namespace 생성

- 원문: [[40_자료/강의 자료/Kubernetes.pdf#page=104|Kubernetes.pdf p.104]]

```console
$ kubectl create namespace prod
namespace/prod created
$ kubectl create namespace dev-stage
namespace/dev-stage created
$ kubectl get namespace
NAME              STATUS   AGE
default           Active   3d22h
dev-stage         Active   6s
kube-node-lease   Active   3d22h
kube-public       Active   3d22h
kube-system       Active   3d22h
prod              Active   8m48s
```

## PDF p.105 - Prod Namespace Deployment

- 원문: [[40_자료/강의 자료/Kubernetes.pdf#page=105|Kubernetes.pdf p.105]]
- 작업 파일: `deploy-prod.yml`

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: prod-deploy
  namespace: prod
spec:
  replicas: 3
  selector:
    matchLabels:
      app: prod-nginx
  template:
    metadata:
      labels:
        app: prod-nginx
        env: production
    spec:
      containers:
        - name: my-nginx
          image: nginx:1.22
          ports:
            - containerPort: 80
```

## PDF p.106 - Dev-stage Namespace Deployment

- 원문: [[40_자료/강의 자료/Kubernetes.pdf#page=106|Kubernetes.pdf p.106]]
- 작업 파일: `deploy-dev-stage.yml`

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: dev-deploy
  namespace: dev-stage
spec:
  replicas: 2
  selector:
    matchLabels:
      app: dev-apache
  template:
    metadata:
      labels:
        app: dev-apache
        env: development
    spec:
      containers:
        - name: dev-web
          image: httpd:latest
          ports:
            - containerPort: 8080
```

> [!note]
> 원자료 주석은 `namespace: dev-stage` 옆에 `Namespace Prod 지정`이라고 적지만 아래 설명은 dev-stage를 지정한다고 한다. 전자는 복사 과정의 표현 불일치로 보이며 원자료 사실로 남긴다.

## PDF p.107 - Namespace별 Deployment 조회

- 원문: [[40_자료/강의 자료/Kubernetes.pdf#page=107|Kubernetes.pdf p.107]]

```console
$ kubectl apply -f deployment/deploy-prod.yml
deployment.apps/prod-deploy created
$ kubectl apply -f deployment/deploy-dev-stage.yml
deployment.apps/dev-deploy created

$ kubectl get deploy -o wide
No resources found in default namespace.

$ kubectl get deploy -o wide -n prod
prod-deploy   3/3   my-nginx   nginx:1.22   app=prod-nginx

$ kubectl get deploy -o wide -n dev-stage
dev-deploy    2/2   dev-web    httpd:latest app=dev-apache
```

- 기본 조회 범위는 `default`; 다른 Namespace는 `--namespace` 또는 `-n`을 사용한다고 설명한다.

## PDF p.108 - Namespace별 ReplicaSet과 Pod

- 원문: [[40_자료/강의 자료/Kubernetes.pdf#page=108|Kubernetes.pdf p.108]]

```text
prod:
  ReplicaSet prod-deploy-bc4b64b5d: desired/current/ready 3
  Pod IP: 192.168.20.185, 192.168.10.58, 192.168.10.156
  Node: node-2, node-2, node-1

dev-stage:
  ReplicaSet dev-deploy-5d7dfcf975: desired/current/ready 2
  Pod IP: 192.168.20.169, 192.168.10.112
  Node: node-1, node-2
```

- ReplicaSet과 Pod도 각 Namespace 영역에 분리되어 생성된 결과를 보여준다.

## PDF p.109 - Namespace 실습 정리

- 원문: [[40_자료/강의 자료/Kubernetes.pdf#page=109|Kubernetes.pdf p.109]]

```console
$ kubectl delete deploy prod-deploy -n prod
deployment.apps "prod-deploy" deleted
$ kubectl delete deploy dev-deploy -n dev-stage
deployment.apps "dev-deploy" deleted
$ kubectl delete namespace prod
namespace "prod" deleted
$ kubectl delete namespace dev-stage
namespace "dev-stage" deleted
$ kubectl get namespace
default           Active
kube-node-lease   Active
kube-public       Active
kube-system       Active
```

- 다음 Test를 위해 생성한 Deployment와 Namespace를 삭제한다.

## 판독·검증 대기

- 이 문서는 원자료를 보존한 것으로, Deployment 동작의 최신 공식 검증을 수행하지 않았다.
- p.92·p.96의 `nginx:lates`, p.106의 `Namespace Prod 지정` 주석은 원자료 내부 불일치다.
- p.94-p.95와 p.100-p.101의 단계별 Pod 도식은 렌더링을 대조했으나 원자료에 각 Frame의 숫자 Caption이 없으므로 Event 순서를 함께 보존했다.
