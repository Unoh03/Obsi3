---
type: lab
status: active
created: 2026-07-23
lab_date: 2026-07-23
topic: kubernetes
parent_moc: "[[10_학습 노트/클라우드/Kubernetes/00_Kubernetes MOC]]"
source: "[[10_학습 노트/클라우드/Kubernetes/Source Digest/Kubernetes - Source Digest 05 Deployment]]"
environment: "Amazon EKS ap-northeast-2; Kubernetes v1.35.6-eks-8f14419; Worker Node 2대"
evidence: "Bastion deployment-basic.yml·tmux·kubectl Deployment/ReplicaSet/Pod/Event 출력"
verified_on: 2026-07-23
---

# EKS Deployment 기초와 Rolling Update 실습

> [!summary]
> `deploy-basic` Deployment를 생성하고 `httpd:alpine3.23 → httpd:alpine3.24 → unoh03/boot:latest`로 Pod Template Image를 변경했다. 각 변경에서 새 ReplicaSet과 Revision이 생겼고, `kubectl rollout undo`로 직전 `httpd:alpine3.24` Template을 현재 Revision 4로 되돌리는 과정까지 확인했다.

> [!info] 선행 실습
> Pod와 ReplicaSet의 직접 생성·Scale·Self-Healing·Template 변경 원리는 [[Lab_EKS ReplicaSet 기초 실습]]에 기록한다. 이 노트는 Deployment가 ReplicaSet과 Pod Revision을 관리하는 단계부터 담당한다.

## 목표

- Deployment → ReplicaSet → Pod의 소유·관리 계층을 확인한다.
- Pod Template 변경이 새 ReplicaSet과 Revision을 만드는 과정을 관찰한다.
- 구·신 Version Pod가 함께 존재하는 Rolling Update 중간 상태를 확인한다.
- `kubectl describe deployment`의 Strategy·Condition·Event를 해석한다.

## 1. Deployment Directory 진입과 예행

강의자료 Directory에는 Deployment 관련 Manifest가 함께 있었다.

```text
deployment-basic.yml
deployment-prod.yml
deployment-rolling-update.yml
deployment-stage.yml
dp-basic.yml
```

처음에는 존재하지 않는 `dp` 경로를 지정해 실패했다.

```console
$ kubectl apply -f dp
error: the path "dp" does not exist
```

정확한 파일명인 `dp-basic.yml`을 지정하자 `dp-basic` Deployment와 Pod 5개가 정상 생성됐다. 이후 해당 예행 Resource를 정리하고, 현재 강의 흐름은 `deployment-basic.yml`의 `deploy-basic`으로 다시 시작했다.

파일명과 Object 이름이 비슷하므로 다음 세 이름을 구분해야 한다.

```text
dp-basic.yml          → 예행 파일
deployment-basic.yml  → 현재 작업 파일
deploy-basic          → 현재 Deployment Object 이름
```

## 2. 첫 Version 생성

현재 실습을 시작할 때 Namespace에는 Deployment와 Pod가 없었다.

```console
$ kubectl get deploy -o wide
No resources found in default namespace.

$ kubectl get pod -o wide
No resources found in default namespace.
```

`deployment-basic.yml`의 첫 Image는 `httpd:alpine3.23`이었다.

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: deploy-basic
spec:
  replicas: 5
  selector:
    matchLabels:
      develop: spring-boot
  template:
    metadata:
      labels:
        name: pod-basic
        app: web
        develop: spring-boot
    spec:
      containers:
        - name: web-containers
          image: httpd:alpine3.23
          ports:
            - containerPort: 80
```

```console
$ kubectl apply -f deployment-basic.yml
deployment.apps/deploy-basic created
```

생성 직후 상태는 5/5였다.

```text
NAME          READY  UP-TO-DATE  AVAILABLE  IMAGE
deploy-basic  5/5    5           5          httpd:alpine3.23
```

Pod 다섯 개도 모두 `httpd:alpine3.23`을 사용했다.

## 3. Deployment가 만든 하위 Object

사용자는 Deployment 하나를 생성했지만 Cluster에서는 다음 계층이 만들어졌다.

```text
Deployment deploy-basic
└─ ReplicaSet deploy-basic-65c6c974d4
   └─ Pod 5개
```

ReplicaSet과 Pod에는 같은 `pod-template-hash=65c6c974d4`가 붙었다. 이 Hash는 Deployment가 서로 다른 Pod Template Revision의 ReplicaSet을 구분하는 데 사용한다.

ReplicaSet을 직접 만들었던 이전 실습과 달리, 여기서는 Deployment Controller가 ReplicaSet을 생성하고 Scale했다.

## 4. Image를 `3.23→3.24`로 변경

Manifest의 Pod Template Image를 변경했다.

```yaml
image: httpd:alpine3.24 # httpd:alpine3.23 -> httpd:alpine3.24
```

```console
$ kubectl apply -f deployment-basic.yml
deployment.apps/deploy-basic configured
```

ReplicaSet 직접 실습에서는 Template을 바꿔도 기존 Pod가 그대로였다. Deployment는 변경된 Template을 위한 새 ReplicaSet을 생성했다.

```text
Revision 1: deploy-basic-65c6c974d4  httpd:alpine3.23
Revision 2: deploy-basic-5b8cb8c465  httpd:alpine3.24
```

## 5. Rolling Update 중간 상태

Image를 변경한 직후 Pod를 조회하자 신·구 Version이 잠시 함께 보였다.

```text
httpd:alpine3.24 × 5
httpd:alpine3.23 × 1
```

조금 뒤 다시 조회했을 때는 신 Version 다섯 개만 남았다.

```text
httpd:alpine3.24 × 5
```

이는 한순간에 기존 Pod를 모두 삭제한 것이 아니라 새 Pod를 먼저 준비하면서 기존 Pod를 순차 종료했다는 증거다.

```text
Update 중간:
구 Version Pod + 신 Version Pod 공존

Update 완료:
신 Version Pod 5개
구 Version Pod 0개
```

## 6. 두 ReplicaSet과 Revision

Rollout 완료 후 Deployment 아래에는 ReplicaSet 두 개가 남았다.

```text
NAME                       REVISION  DESIRED  READY  IMAGE
deploy-basic-5b8cb8c465    2         5        5      httpd:alpine3.24
deploy-basic-65c6c974d4    1         0        0      httpd:alpine3.23
```

구 Version ReplicaSet은 Pod 수만 0으로 내려가고 Object는 남았다. 이 Revision 기록이 이후 Rollback의 기반이 된다.

```console
$ kubectl rollout history deployment/deploy-basic
REVISION  CHANGE-CAUSE
1         <none>
2         <none>
```

`CHANGE-CAUSE`가 `<none>`인 것은 Revision이 없다는 뜻이 아니라 별도 변경 사유 Annotation을 기록하지 않았다는 뜻이다.

## 7. `kubectl describe deployment` 해석

```console
$ kubectl describe deployment deploy-basic
```

### 현재 상태

```text
Replicas: 5 desired | 5 updated | 5 total | 5 available | 0 unavailable
```

- `desired`: 목표 Pod 수
- `updated`: 현재 최신 Template Revision을 사용하는 Pod 수
- `total`: Deployment가 관리하는 전체 Pod 수
- `available`: Traffic을 받을 수 있는 상태로 판단된 Pod 수
- `unavailable`: 아직 사용 가능하지 않은 Pod 수

### 기본 배포 전략

Manifest에 Strategy를 직접 쓰지 않았지만 API Server가 기본값을 적용했다.

```text
StrategyType: RollingUpdate
RollingUpdateStrategy: 25% max unavailable, 25% max surge
```

- `maxSurge`: 목표 수를 초과해 임시로 추가할 수 있는 새 Pod 한도
- `maxUnavailable`: Update 중 동시에 사용 불가능해도 되는 Pod 한도

이 값은 PDF p.88-p.90에서 별도로 다루는 개념이다. 이번 Runtime에서는 기본 전략이 적용된 사실과 신·구 Version 공존을 확인했지만, 값을 직접 변경하는 실습은 아직 하지 않았다.

### Condition

```text
Available   True  MinimumReplicasAvailable
Progressing True  NewReplicaSetAvailable
```

- 필요한 최소 Pod가 사용 가능하다.
- 새 ReplicaSet을 이용한 Rollout이 정상 진행·완료됐다.

### Event에 기록된 실제 교대

```text
구 Revision 1: 5→4→3→2→1→0
신 Revision 2: 0→2→3→4→5
```

Event에는 다음과 같은 `ScalingReplicaSet` 기록이 남았다.

```text
Scaled up replica set deploy-basic-5b8cb8c465 from 0 to 2
Scaled down replica set deploy-basic-65c6c974d4 from 5 to 4
Scaled up replica set deploy-basic-5b8cb8c465 from 2 to 3
...
Scaled down replica set deploy-basic-65c6c974d4 from 1 to 0
```

이 순서는 Deployment가 새 ReplicaSet을 늘리고 기존 ReplicaSet을 줄이는 방식으로 Rolling Update를 수행했다는 직접 증거다.

## 8. 저장 전 Apply와 Revision 3

`deployment-basic.yml`의 Image를 `unoh03/boot:latest`로 편집했지만, 처음에는 파일을 저장하지 않고 Apply했다.

```console
$ kubectl apply -f deployment-basic.yml
deployment.apps/deploy-basic unchanged
```

`kubectl apply`는 Editor 화면의 미저장 내용을 읽지 않고 Disk에 실제 저장된 Manifest를 읽는다. 파일에는 여전히 `httpd:alpine3.24`가 있었으므로 Cluster의 현재 상태와 차이가 없었다.

파일을 저장한 뒤 다시 Apply하자 변경이 반영됐다.

```console
$ kubectl apply -f deployment-basic.yml
deployment.apps/deploy-basic configured
```

새 Pod Template으로 Revision 3 ReplicaSet이 생성됐다.

```text
Revision 1  deploy-basic-65c6c974d4  httpd:alpine3.23    0/0
Revision 2  deploy-basic-5b8cb8c465  httpd:alpine3.24    0/0
Revision 3  deploy-basic-d6c756b96   unoh03/boot:latest  5/5
```

```console
$ kubectl rollout history deploy deploy-basic
REVISION  CHANGE-CAUSE
1         <none>
2         <none>
3         <none>
```

같은 Manifest를 다시 Apply한 `unchanged`는 새 Revision을 만들지 않았고, Pod Template Image가 실제로 변경된 `configured`에서만 Revision 3이 생겼다.

## 9. 직전 Revision Rollback

현재 Revision 3에서 별도 Revision 번호를 지정하지 않고 Rollback했다.

```console
$ kubectl rollout undo deploy deploy-basic
deployment.apps/deploy-basic rolled back
```

`--to-revision`을 생략하면 직전 Pod Template으로 되돌린다. 이 환경에서는 Revision 2의 `httpd:alpine3.24`가 대상이었다.

> [!tip] `--to-revision`이란?
> `kubectl rollout undo deployment/deploy-basic --to-revision=1`처럼 사용하며, 직전 상태가 아니라 **지정한 Revision의 Pod Template**으로 Rollback한다. 숫자는 `kubectl rollout history deployment/deploy-basic`에서 먼저 확인한다. Rollback 후에는 그 Template이 다시 현재 상태가 되면서 새로운 Revision으로 기록된다.

```console
$ kubectl get deploy -o wide
NAME          READY  UP-TO-DATE  AVAILABLE  IMAGE
deploy-basic  5/5    5           5          httpd:alpine3.24
```

Deployment는 Revision 2에서 사용했던 기존 ReplicaSet을 다시 Scale Up하고 Revision 3 ReplicaSet을 Scale Down했다.

```text
deploy-basic-5b8cb8c465  httpd:alpine3.24    0→5
deploy-basic-d6c756b96   unoh03/boot:latest  5→0
```

Rollback 후 최종 상태:

```text
Revision 1 RS  deploy-basic-65c6c974d4  0/0  httpd:alpine3.23
현재 RS        deploy-basic-5b8cb8c465  5/5  httpd:alpine3.24
이전 RS        deploy-basic-d6c756b96   0/0  unoh03/boot:latest
```

History는 다음처럼 바뀌었다.

```console
$ kubectl rollout history deploy deploy-basic
REVISION  CHANGE-CAUSE
1         <none>
3         <none>
4         <none>
```

Rollback은 “Revision 번호를 3에서 2로 낮추는 것”이 아니다. Revision 2의 Pod Template을 다시 현재 상태로 채택하는 **새 Rollout**이므로 현재 Revision은 4가 된다. 기존 `deploy-basic-5b8cb8c465` ReplicaSet을 재사용하지만 그 Template이 최신 Revision 4로 승격되어 History에서 2 대신 4로 표시된다.

> [!warning] Manifest와 Cluster의 현재 상태가 다름
> Rollback은 Cluster의 Deployment를 `httpd:alpine3.24`로 되돌렸지만 Bastion의 `deployment-basic.yml`에는 여전히 `unoh03/boot:latest`가 저장돼 있다. 이 파일을 그대로 다시 Apply하면 Rollback을 덮어쓰고 `unoh03/boot:latest`로 다시 Rollout될 수 있다. 원하는 최종 상태에 맞게 Manifest도 정렬해야 한다.

## 10. Change Cause Annotation

현재 Revision 4에 변경 이유를 기록했다.

```console
$ kubectl annotate deploy deploy-basic kubernetes.io/change-cause="3.24"
deployment.apps/deploy-basic annotated

$ kubectl rollout history deploy deploy-basic
REVISION  CHANGE-CAUSE
1         <none>
3         <none>
4         3.24
```

같은 Annotation의 값을 `unoh03`으로 다시 지정하자 Revision 번호는 그대로이고 설명만 바뀌었다.

```console
$ kubectl annotate deploy deploy-basic kubernetes.io/change-cause="unoh03"
deployment.apps/deploy-basic annotated

$ kubectl rollout history deploy deploy-basic
REVISION  CHANGE-CAUSE
1         <none>
3         <none>
4         unoh03
```

`annotate`는 Pod Template을 바꾸지 않으므로 새 ReplicaSet이나 새 Rollout을 만들지 않았다. 여기서는 현재 Revision 4의 `CHANGE-CAUSE` 설명만 갱신됐으며, 같은 Key를 다시 지정한 마지막 값이 보였다.

> [!example] Git으로 비유하면
> `commit`이나 `push` 없이 배포 Revision에 설명 메모를 붙이는 것에 가깝다. 다만 Git의 Commit Message를 고치는 것과는 다르다. Git Commit Message 수정은 Commit 자체를 다시 만들어 Hash가 바뀌지만, Kubernetes Annotation 수정은 Workload 내용과 Revision 번호를 그대로 둔 채 Resource의 부가 Metadata만 바꾼다.

## 11. 시행착오와 해석

| 증상 | 원인 | 결과·조치 |
|---|---|---|
| `kubectl apply -f dp`가 실패 | `dp`라는 파일·Directory가 없음 | 정확한 파일명 `dp-basic.yml` 사용 |
| `kubectl get deploy -o wide \| grep IMAGES:` 출력 없음 | 실제 Header는 `IMAGES`이며 Colon이 없음 | 전체 출력을 보거나 `grep IMAGES` 사용 |
| `show event too!`가 `command not found` | 공유 tmux에서 Codex에게 남긴 문장을 Shell도 명령으로 해석 | Cluster 영향 없음; `kubectl describe deployment deploy-basic`으로 Event 확인 |
| Update 중 Image가 여섯 줄 표시 | 구 Version 1개와 신 Version 5개가 일시 공존 | Rolling Update와 Surge 과정의 정상 중간 상태 |
| Image 편집 후 첫 Apply가 `unchanged` | Editor에서 변경했지만 파일을 저장하지 않음 | 저장 후 다시 Apply해 Revision 3 생성 |
| `kubectl get deploy -o -wide` 오류 | 출력 형식은 `-wide`가 아니라 `wide` | `kubectl get deploy -o wide` 사용 |

## 검증 완료와 미완료

### 완료

- `deploy-basic` 생성과 최초 `httpd:alpine3.23` Pod 5개 확인
- Deployment가 Revision 1 ReplicaSet과 Pod를 생성한 관계 확인
- `httpd:alpine3.23 → httpd:alpine3.24` Template Image 변경
- Rolling Update 중 구·신 Version Pod 공존 확인
- Revision 2 ReplicaSet 5개와 Revision 1 ReplicaSet 0개 확인
- Rollout History Revision 1·2 확인
- `kubectl describe deployment`에서 기본 RollingUpdate Strategy·Condition·Scaling Event 확인
- 최종 `READY 5 / UP-TO-DATE 5 / AVAILABLE 5`
- 저장 전 Apply는 `unchanged`, 저장 후 Apply는 `configured`가 되는 차이 확인
- `unoh03/boot:latest` Revision 3 생성과 세 ReplicaSet 계보 확인
- `kubectl rollout undo`로 직전 `httpd:alpine3.24` Template Rollback
- Rollback 시 기존 Revision 2 ReplicaSet을 재사용하면서 현재 Revision 4가 되는 동작 확인
- Rollback 후 `READY 5 / UP-TO-DATE 5 / AVAILABLE 5`
- `kubernetes.io/change-cause` Annotation을 변경해 Revision 4의 `CHANGE-CAUSE`가 바뀌고 새 Revision은 생기지 않는 동작 확인

### 미완료·추가 증거 필요

- 특정 Revision을 지정한 Rollback
- `Recreate` 전략 Runtime 비교
- `maxUnavailable`·`maxSurge` 값을 직접 변경한 Rolling Update
- PDF p.86 이후 특정 Revision Rollback·Strategy·Namespace 실습
- Rollback 결과와 `deployment-basic.yml`의 원하는 Image 정렬
- 오늘 사용한 `00_eks` Terraform Destroy와 잔존 Resource 확인

## 다음 재시작 지점

1. `kubectl rollout history deployment/deploy-basic`에서 Revision 1·3·4를 확인한다.
2. 현재 Cluster Image `httpd:alpine3.24`와 Manifest Image `unoh03/boot:latest`의 차이를 인지한다.
3. `--to-revision`으로 특정 Revision Rollback을 검증한다.

## 관련 노트

- [[Lab_EKS ReplicaSet 기초 실습]]
- [[04_Kubernetes Pod와 ReplicaSet]]
- [[Source Digest/Kubernetes - Source Digest 05 Deployment]]

## 공식 참고

- [Deployments](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/)
- [kubectl rollout](https://kubernetes.io/docs/reference/kubectl/generated/kubectl_rollout/)
- [kubectl rollout undo](https://kubernetes.io/docs/reference/kubectl/generated/kubectl_rollout/kubectl_rollout_undo/)
- [kubectl annotate](https://kubernetes.io/docs/reference/kubectl/generated/kubectl_annotate/)
