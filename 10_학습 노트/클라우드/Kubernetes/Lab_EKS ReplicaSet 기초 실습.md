---
type: lab
status: active
created: 2026-07-22
lab_date: 2026-07-22
topic: kubernetes
parent_moc: "[[10_학습 노트/클라우드/Kubernetes/00_Kubernetes MOC]]"
source: "[[10_학습 노트/클라우드/Kubernetes/Source Digest/Kubernetes - Source Digest 04 Pod and ReplicaSet]]"
environment: "Amazon EKS ap-northeast-2; Kubernetes v1.35.6-eks-8f14419; Worker Node 2대"
evidence: "Bastion rs-basic.yml·kubectl/tmux 출력과 Local Terraform Destroy 출력"
verified_on: 2026-07-23
---

# EKS ReplicaSet 기초 실습

> [!summary]
> 첫 환경에서는 Scheduling 불가로 `DESIRED 5 / CURRENT 5 / READY 0`까지 확인했다. 다음 환경에서는 잘못된 Image와 Directory 전체 Apply 때문에 의도하지 않은 상태를 겪었지만, 그 과정에서 기존 Pod 편입·Cascade 삭제·ReplicaSet Self-Healing을 관찰하고 Image를 보정해 `READY 5`를 확인했다. 이후 `5→3→0→3`으로 Scale하며 Pod 삭제와 새 Pod 생성을 확인했다.

> [!info] 선행 실습
> EKS 접속·Pod 기본은 [[Lab_EKS 첫 접속과 Pod 기초 실습]], Node Scheduling·Drain은 [[Lab_EKS Pod Scheduling과 Node 운영 실습]]에 기록한다.

## 목표

- ReplicaSet의 Selector와 Pod Template Label 관계를 확인한다.
- `replicas` 희망 상태가 Pod Object 생성으로 이어지는 과정을 관찰한다.
- `READY 5`와 Pod 삭제 후 Self-Healing을 검증한다.

## ReplicaSet EX.1 — Basic

오늘 마지막으로 Bastion에 ReplicaSet 실습 Directory와 `rs-basic.yml`을 직접 만들었다.

```console
$ cd ~/kube-worksapce
$ mkdir replicaset
$ cd replicaset
$ vi rs-basic.yml
```

작성한 Manifest는 다음과 같다.

```yaml
apiVersion: apps/v1
kind: ReplicaSet
metadata:
  name: rs-basic
spec:
  replicas: 5
  selector:
    matchLabels:
      app: nginx-app
  template:
    metadata:
      labels:
        app: nginx-app
    spec:
      containers:
        - name: nginx-con
          image: nginx:latest
          ports:
            - containerPort: 80
```

`selector.matchLabels.app`과 `template.metadata.labels.app`은 모두 `nginx-app`으로 일치한다. ReplicaSet은 이 Label을 기준으로 자신이 관리할 Pod를 식별한다.

```console
$ kubectl apply -f .
replicaset.apps/rs-basic created
```

생성 직후 ReplicaSet은 원하는 Pod 수에 맞춰 Pod Object 5개를 만들었다.

```text
NAME       DESIRED   CURRENT   READY
rs-basic   5         5         0
```

```text
rs-basic-64zxk   0/1   Pending   IP=<none>   NODE=<none>
rs-basic-mq6dj   0/1   Pending   IP=<none>   NODE=<none>
rs-basic-ps4zs   0/1   Pending   IP=<none>   NODE=<none>
rs-basic-t8dkf   0/1   Pending   IP=<none>   NODE=<none>
rs-basic-tf99d   0/1   Pending   IP=<none>   NODE=<none>
```

이 `Pending`은 ReplicaSet Manifest 오류가 아니다. 직전 EX.8에서 Worker Node 2대를 모두 `cordon`한 상태였기 때문에 Scheduler가 선택할 Node가 없었다.

```text
0/2 nodes are available: 2 node(s) were unschedulable.
```

여기까지로도 ReplicaSet이 `replicas: 5`라는 희망 상태를 보고 Pod Object 5개를 즉시 생성한다는 점은 확인했다. 다만 실제 Container 실행과 `READY 5`, Pod 삭제 후 Self-Healing은 아직 검증하지 않았다.

`~/kube-worksapce/replicaset/rs-basic.yml`은 현재 Bastion에서 수동 생성한 파일이다. Terraform Destroy 시 Bastion과 함께 사라지므로 다음 환경에서는 이 기록을 바탕으로 다시 생성해야 한다. Local Terraform Source의 `user_data`에 반영된 설정만 새 Bastion 생성 때 자동 재현된다.

## 2026-07-23 재실습 — 엉킨 상태에서 확인한 ReplicaSet 동작

새 Bastion의 강의자료는 `~/kube-workspace/replicasets/`에 배치됐다. 이 Directory에는 다음 세 Manifest가 함께 있었다.

```text
pod-basic.yml
rs-basic.yml
rs-update-rollback.yml
```

### 1. Directory 전체를 Apply

파일 하나가 아니라 현재 Directory를 지정했다.

```console
$ kubectl apply -f .
pod/pod-basic created
replicaset.apps/rs-basic created
replicaset.apps/rs-rollback created
```

`-f .`은 현재 Directory의 적용 가능한 Manifest를 모두 읽는다. 따라서 ReplicaSet Basic만 실행하려던 상황에서 단독 Pod와 다음 Template Update 실습용 `rs-rollback`까지 함께 생성됐다. 한 파일만 적용하려면 `kubectl apply -f rs-basic.yml`처럼 파일명을 지정해야 한다.

### 2. 같은 Label의 기존 Pod 편입

`pod-basic.yml`과 `rs-basic.yml`은 모두 다음 Label을 사용했다.

```yaml
develop: spring-boot
```

`rs-basic`의 Selector도 `develop: spring-boot`였기 때문에, 먼저 생성된 단독 `pod-basic`이 ReplicaSet의 관리 대상에 편입됐다. 목표치는 5개였지만 ReplicaSet이 새로 만든 Pod는 4개였다.

```text
DESIRED  CURRENT  READY
5        5        1
```

- `CURRENT 5`: 기존 `pod-basic` 1개와 새 `rs-basic-*` Pod 4개
- `READY 1`: `pod-basic`만 정상 실행

이 결과는 ReplicaSet이 Pod 이름이 아니라 Selector와 Label을 기준으로 관리 대상을 센다는 것을 보여준다.

### 3. 강사 Image가 없어 발생한 `ImagePullBackOff`

`pod-basic.yml`은 사용자 Image를 사용했지만, `rs-basic.yml`의 Template에는 강사 Image가 남아 있었다.

```yaml
# pod-basic.yml
image: unoh03/boot:latest

# rs-basic.yml의 최초 상태
image: kys8502/boot:1.1
```

Registry에서 `kys8502/boot:1.1`을 찾을 수 없어 ReplicaSet이 만든 네 Pod는 실행되지 않았다.

```text
Failed to pull image "kys8502/boot:1.1"
docker.io/kys8502/boot:1.1: not found
ErrImagePull
ImagePullBackOff
```

ReplicaSet Controller와 Pod Object 생성은 정상이었고, 실패 지점은 Container Image Pull이었다.

### 4. Pod만 삭제하자 다시 생성됨

문제를 정리하려고 모든 Pod를 삭제했지만 `rs-rollback` ReplicaSet은 남아 있었다.

```console
$ kubectl delete pod --all
```

삭제 직후 `rs-rollback-*` Pod 세 개가 새로운 이름으로 다시 생성됐다. 이는 삭제 실패가 아니라 Controller가 `replicas: 3`이라는 희망 상태를 복구한 결과다.

```text
Pod 삭제
→ 현재 수 0 < 희망 수 3
→ ReplicaSet이 새 Pod 3개 생성
```

Pod의 부활을 멈추려면 Pod가 아니라 해당 ReplicaSet을 삭제하거나 `replicas: 0`으로 내려야 한다.

### 5. ReplicaSet 삭제 시 편입된 Pod도 함께 삭제됨

```console
$ kubectl delete rs rs-basic
replicaset.apps "rs-basic" deleted from default namespace
```

기본 Cascade 삭제로 `rs-basic-*`뿐 아니라 관리 대상으로 편입됐던 `pod-basic`도 함께 사라졌다. 이후 Pod 조회에는 `rs-rollback-*`만 남았다.

### 6. Image 보정 후 `READY 5`

`rs-basic.yml`의 Image를 사용자 Registry Image로 보정했다.

```yaml
image: unoh03/boot:latest
```

ReplicaSet을 다시 생성한 뒤 최종 상태는 다음과 같았다.

```text
NAME      DESIRED  CURRENT  READY  IMAGE
rs-basic  5        5        5      unoh03/boot:latest
```

다섯 Pod는 Worker Node 두 대에 분산되어 모두 `Running 1/1`이 됐다. 같은 시점에 너무 일찍 생성된 `rs-rollback`도 `DESIRED 3 / CURRENT 3 / READY 3` 상태로 남아 있었다.

### 7. `5→3→0→3` Scale과 새 Pod 생성

`rs-rollback`을 정리한 뒤 `rs-basic`만 남겨 Scale 동작을 확인했다.

먼저 희망 수를 5개에서 3개로 줄였다.

```console
$ kubectl scale rs rs-basic --replicas=3
replicaset.apps/rs-basic scaled
```

ReplicaSet은 초과한 Pod 두 개를 종료하고 세 개만 유지했다.

```text
rs-basic-46s7p   1/1   Running
rs-basic-fbqf4   1/1   Running
rs-basic-gkgb5   1/1   Running
```

다음으로 희망 수를 0으로 내렸다.

```console
$ kubectl scale rs rs-basic --replicas=0
replicaset.apps/rs-basic scaled

$ kubectl get pod -o wide
No resources found in default namespace.
```

Pod는 모두 사라졌지만 ReplicaSet Object 자체는 삭제되지 않았다. 다시 희망 수를 3으로 올리자 이전 Pod를 되살리는 대신 Template으로 새 Pod 세 개를 생성했다.

```console
$ kubectl scale rs rs-basic --replicas=3
replicaset.apps/rs-basic scaled
```

```text
NAME             READY  STATUS   IMAGE
rs-basic-6klxf   1/1    Running  unoh03/boot:latest
rs-basic-rfpcj   1/1    Running  unoh03/boot:latest
rs-basic-vcjn6   1/1    Running  unoh03/boot:latest
```

최종 ReplicaSet 상태는 다음과 같았다.

```text
DESIRED  CURRENT  READY
3        3        3
```

Pod 이름이 Scale Down 전과 달라졌으므로, Scale Up은 종료된 Pod Process를 다시 시작하는 동작이 아니라 새 Pod Object를 만드는 동작임을 확인했다.

### 8. `kubectl edit`으로 `replicas: 2` 저장

```console
$ kubectl edit rs rs-basic
Edit cancelled, no changes made.
```

처음 두 번은 저장하지 않고 종료되어 Object가 바뀌지 않았다. 세 번째 시도에서는 `spec.replicas`를 3에서 2로 바꾸고 저장했다.

```console
$ kubectl edit rs rs-basic
replicaset.apps/rs-basic edited
```

실제 조회에서도 Pod 한 개가 줄어 최종 상태가 일치했다.

```text
NAME      DESIRED  CURRENT  READY
rs-basic  2        2        2
```

```text
rs-basic-6klxf  1/1  Running
rs-basic-rfpcj  1/1  Running
```

`kubectl scale`은 명령 한 줄로 `spec.replicas`를 바꾸고, `kubectl edit`은 API Server에 저장된 Object YAML을 Editor에서 직접 수정한다. 입력 방식은 다르지만 이번 실습에서는 둘 다 같은 `spec.replicas` 희망 상태를 변경했다.

## ReplicaSet Template Update·수동 Rollback 해설 — PDF p.63-p.73

> [!warning] 검증 경계
> 아래 내용은 원본 PDF p.63-p.73과 현재 Bastion의 `rs-update-rollback.yml`을 대조해 정리한 강의 해설이다. 현재 Cluster에는 `rs-rollback`이 존재하지 않으므로 Apply·Image 변경·Pod 교체 결과는 아직 이 환경에서 실행 검증하지 않았다.

### 1. 이 실습에서 확인하려는 질문

```text
ReplicaSet의 Pod Template을 수정하면
이미 실행 중인 Pod도 자동으로 바뀌는가?
```

결론부터 말하면 **바뀌지 않는다.** ReplicaSet의 Template은 현재 Pod를 수정하는 명령서가 아니라, 앞으로 Pod가 부족할 때 새로 만들 Pod의 설계도다.

```text
기존 Pod = 만들어질 당시 Template을 유지
새 Pod   = 변경된 최신 Template으로 생성
```

### 2. PDF와 현재 강사 배포본의 차이

| 구분 | PDF p.63-p.73 | 현재 Bastion Manifest |
|---|---|---|
| ReplicaSet | `rs-rollback` | `rs-rollback` |
| replicas | `3` | `3` |
| Selector | `app=node-app` | `app=http-app` |
| Container | `node-con` | `web-container` |
| Image 변경 예시 | `node:16-alpine3.15 → node:18-alpine3.15` | 주석상 `httpd:alpine3.20 → httpd:alpine3.21` |
| 현재 파일 Image | PDF 단계에 따라 변경 | `httpd:alpine3.21` |

Image 이름은 달라도 학습 원리는 같다. 현재 Manifest는 다음 상태다.

```yaml
apiVersion: apps/v1
kind: ReplicaSet
metadata:
  name: rs-rollback
spec:
  replicas: 3
  selector:
    matchLabels:
      app: http-app
  template:
    metadata:
      labels:
        app: http-app
    spec:
      containers:
        - name: web-container
          image: httpd:alpine3.21
          ports:
            - containerPort: 80
```

### 3. Template Label을 바꿔도 기존 Pod는 그대로

PDF는 Template에 다음 Label을 추가한다.

```yaml
labels:
  app: node-app
  version: v1
  env: prod
```

Manifest를 다시 Apply해도 기존 Pod 세 개에는 새 Label이 생기지 않는다. 이후 기존 Pod 하나를 삭제하면 ReplicaSet이 최신 Template으로 대체 Pod 하나를 만들고, **그 새 Pod에만** `version=v1`, `env=prod`가 붙는다.

```text
기존 Pod 2개: app=node-app
새 Pod 1개:   app=node-app, version=v1, env=prod
```

이 때문에 하나의 ReplicaSet 안에서도 생성 시점에 따라 Pod의 부가 Label이나 Image가 서로 다를 수 있다.

### 4. Template Image를 바꿔도 기존 Pod는 그대로

PDF에서는 Image를 다음처럼 바꾼다.

```text
node:16-alpine3.15
→ node:18-alpine3.15
```

Apply 뒤 ReplicaSet 조회에는 새 Image가 보이지만, 이미 Running 중인 Pod를 `describe`하면 계속 이전 Image를 사용한다.

```text
ReplicaSet Template: node:18-alpine3.15
기존 Pod Image:      node:16-alpine3.15
```

새 Image를 모든 Pod에 적용하려고 PDF에서는 `replicas: 0`으로 기존 Pod를 전부 없앤 뒤 다시 `replicas: 3`으로 올린다.

```text
Scale 3→0: 기존 Pod 전부 종료
Scale 0→3: 최신 Template으로 새 Pod 3개 생성
```

이 방식은 이해하기 쉽지만, 실제 서비스에서는 Pod가 0개가 되는 중단 시간이 발생할 수 있다.

### 5. PDF의 Rollback은 자동 Rollback이 아니다

PDF는 `kubectl set image`로 ReplicaSet Template을 이전 Image로 되돌린다.

```bash
kubectl set image rs/rs-rollback node-con=node:16-alpine3.15
```

이 명령도 기존 Pod를 즉시 바꾸지 않는다. 그래서 기존 Pod의 Selector 핵심 Label을 다른 값으로 변경해 ReplicaSet 관리 대상에서 제외한다.

```text
기존 Pod: app=node-app
Label 변경: app=delay-app
```

ReplicaSet 관점에서는 관리 대상 Pod가 3개에서 0개로 줄어든다.

```text
현재 0 < 희망 3
→ 이전 Image가 들어 있는 최신 Template으로 새 Pod 3개 생성
```

그 뒤 `app=delay-app`으로 빠져나간 기존 Pod 세 개를 수동 삭제한다.

```text
Template을 이전 Image로 변경
→ 기존 Pod를 Selector 밖으로 분리
→ ReplicaSet이 이전 Image Pod를 새로 생성
→ 분리한 기존 Pod 삭제
```

강의자료에서는 이를 Rollback Test라고 부르지만, ReplicaSet이 Version History를 기억했다가 자동 복원한 것은 아니다. 사람이 이전 Image를 지정하고 Pod를 교체한 **수동 Rollback**이다. 실제 배포에서는 보통 Deployment가 ReplicaSet들을 관리하면서 Rolling Update와 Revision Rollback을 제공한다.

### 6. 이 구간에서 기억할 것

```text
ReplicaSet은 Pod 수를 유지한다.
ReplicaSet은 기존 Pod 내용을 자동 업데이트하지 않는다.
Template 변경은 이후 새로 생성되는 Pod부터 적용된다.
직접 ReplicaSet을 이용한 전체 교체는 서비스 중단이나 혼합 Version을 만들 수 있다.
```

> [!tip] 이번 시행착오의 핵심
> 성공한 Apply 한 번보다, Controller를 남긴 채 Pod만 삭제했을 때 다시 살아나는 과정을 통해 ReplicaSet의 역할을 더 직접적으로 확인했다. ReplicaSet을 다룰 때는 **Pod 상태뿐 아니라 어떤 Controller가 어떤 Selector와 희망 수를 가지고 있는지** 함께 확인해야 한다.

## 이전 환경의 Terraform Destroy와 잔존 확인

수업 종료 후 `D:\terraform\workspace\00_eks` Root Module을 대상으로 Destroy했다. 실행 전 Local State에는 Data Source를 포함해 104개 주소가 있었고, 새로 생성한 Destroy Plan은 다음과 같았다.

```text
Plan: 0 to add, 0 to change, 84 to destroy.
```

AWS Provider 인증은 `terra-user` Profile이 담당했다. `access_key`와 `access_secret_key` 변수는 Bastion `user_data` Template을 평가하기 위해서만 필요했으므로 Destroy Process 안에서 실제 Key 대신 `not-used` Placeholder를 사용했다. 이 값으로 AWS에 인증한 것은 아니다.

```powershell
$env:TF_VAR_access_key='not-used'
$env:TF_VAR_access_secret_key='not-used'
terraform destroy -auto-approve -input=false -no-color
```

실행 결과:

```text
Destroy complete! Resources: 84 destroyed.
```

- Managed Node Group 삭제: 약 8분 10초
- EKS Cluster 삭제: 약 2분 15초
- 종료 후 `terraform state list`: 0개
- Terraform Process와 State Lock: 없음
- EKS `my-eks`, VPC `vpc-0fa5cc261da197e7e`, 해당 VPC의 실행 중 EC2·ENI, Node Group ASG, Load Balancer, CloudWatch Log Group: 조회 결과 없음
- Cluster·Node IAM Role과 OIDC Provider: 조회 결과 없음
- Launch Template `lt-0861a0baf99fa9fee`: `InvalidLaunchTemplateId.NotFound`
- KMS Key `7314f765-1f86-4acd-9ba0-c9ae1265ff1d`: 즉시 물리 삭제되지 않고 `PendingDeletion`, 삭제 예정 `2026-08-20 18:26:07 KST`

이 검증은 `00_eks`가 만든 것으로 식별된 대상과 해당 State를 중심으로 했다. AWS 계정 전체의 모든 Region·모든 서비스에 대한 전수 비용 감사와는 구분한다.


## 오류와 해석 요약

| 증상 | 확인한 원인 또는 현재 판단 | 조치·다음 확인 |
|---|---|---|
| `rs-basic` Pod 5개가 모두 `Pending` | ReplicaSet은 정상 생성됐지만 두 Worker Node가 모두 `SchedulingDisabled` | 다음 환경에서 Node가 `Ready`인 상태로 다시 Apply해 `READY 5` 확인 |
| `rs-basic`이 `CURRENT 5 / READY 1` | 기존 `pod-basic` 1개를 Selector로 편입했고, 새 Pod 4개는 존재하지 않는 강사 Image를 사용 | `rs-basic.yml`을 `unoh03/boot:latest`로 보정하고 Controller를 재생성해 `READY 5` 확인 |
| `kubectl delete pod --all` 뒤 `rs-rollback-*`이 다시 생김 | `rs-rollback` Controller가 `replicas: 3`을 계속 유지 | 완전히 제거하려면 `kubectl delete rs rs-rollback` 또는 의도적으로 `replicas: 0` 사용 |
| Basic 실습 중 `rs-rollback`까지 생성됨 | `kubectl apply -f .`이 `replicasets/`의 세 Manifest를 전부 적용 | 실습 범위를 제한할 때는 정확한 파일명 지정 |
| 첫 두 `kubectl edit rs rs-basic` 뒤 변화 없음 | `Edit cancelled, no changes made`로 종료 | 세 번째 시도에서 `spec.replicas: 2`를 저장하고 `2/2/2` 확인 |

## 검증 완료와 미완료

### 완료

- ReplicaSet `rs-basic` 생성
- `DESIRED 5`, `CURRENT 5`, `READY 0` 확인
- ReplicaSet이 Pod Object 5개를 생성한 사실 확인
- `Pending` Event가 `2 node(s) were unschedulable`임을 확인
- Selector가 같은 기존 단독 Pod를 ReplicaSet이 관리 대상으로 편입하는 동작 확인
- 존재하지 않는 Image로 인한 `ErrImagePull`·`ImagePullBackOff` 확인
- Controller를 둔 채 Pod만 삭제하면 희망 수만큼 다시 생성되는 Self-Healing 확인
- 기본 ReplicaSet 삭제 시 관리 Pod가 함께 삭제되는 Cascade 동작 확인
- `unoh03/boot:latest` 보정 후 `DESIRED 5 / CURRENT 5 / READY 5` 확인
- `kubectl scale`로 `5→3→0→3` 변경 확인
- Scale Down 시 초과 Pod 삭제, Scale Up 시 새로운 이름의 Pod 생성 확인
- 최종 `DESIRED 3 / CURRENT 3 / READY 3` 확인
- `kubectl edit`으로 `spec.replicas: 2`를 저장하고 `DESIRED 2 / CURRENT 2 / READY 2` 확인
- PDF p.63-p.73 Template Update·수동 Rollback의 단계와 현재 강사 Manifest 차이 정리
- `00_eks` Destroy: 84개 Resource 삭제, State 0
- `00_eks` 주요 EKS·VPC·EC2·ASG·ENI·IAM·OIDC 잔존 없음

### 미완료·추가 증거 필요

- 개별 `rs-basic` Pod 하나를 삭제한 뒤 대체 Pod 1개가 생성되는 최소 Self-Healing 실험
- 현재 `rs-update-rollback.yml`을 이용한 Template 변경·수동 Rollback의 Runtime 검증
- 오늘 사용한 현재 `00_eks` 환경의 Terraform Destroy·State 0·주요 잔존 Resource 확인
- AWS 계정 전체 Region·서비스의 비용 Resource 전수 확인

## 다음 재시작 지점

1. `rs-basic`이 계속 `DESIRED 2 / CURRENT 2 / READY 2`인지 확인한다.
2. 강사 지시에 따라 Basic 실습 Resource를 정리한다.
3. `rs-update-rollback.yml`의 시작 Image와 변경 목표를 확인한다.
4. Template 변경 전후의 ReplicaSet Image와 기존 Pod Image를 각각 조회한다.

## 관련 노트

- [[Lab_EKS 첫 접속과 Pod 기초 실습]]
- [[Lab_EKS Pod Scheduling과 Node 운영 실습]]
- [[04_Kubernetes Pod와 ReplicaSet]]
- [[Source Digest/Kubernetes - Source Digest 04 Pod and ReplicaSet]]

## 공식 참고

- [ReplicaSet](https://kubernetes.io/docs/concepts/workloads/controllers/replicaset/)
- [kubectl apply](https://kubernetes.io/docs/reference/kubectl/generated/kubectl_apply/)
