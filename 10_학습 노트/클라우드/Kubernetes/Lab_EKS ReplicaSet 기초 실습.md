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
> 첫 환경에서는 Scheduling 불가로 `DESIRED 5 / CURRENT 5 / READY 0`까지 확인했다. 다음 환경에서는 잘못된 Image와 Directory 전체 Apply 때문에 의도하지 않은 상태를 겪었지만, 그 과정에서 기존 Pod 편입·Cascade 삭제·ReplicaSet Self-Healing을 관찰하고 Image를 보정해 최종 `READY 5`를 확인했다.

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
- `00_eks` Destroy: 84개 Resource 삭제, State 0
- `00_eks` 주요 EKS·VPC·EC2·ASG·ENI·IAM·OIDC 잔존 없음

### 미완료·추가 증거 필요

- 개별 `rs-basic` Pod 하나를 삭제한 뒤 대체 Pod 1개가 생성되는 최소 Self-Healing 실험
- Scale Up·Down과 Template 변경·수동 Rollback
- 오늘 사용한 현재 `00_eks` 환경의 Terraform Destroy·State 0·주요 잔존 Resource 확인
- AWS 계정 전체 Region·서비스의 비용 Resource 전수 확인

## 다음 재시작 지점

1. `rs-basic`이 계속 `DESIRED 5 / CURRENT 5 / READY 5`인지 확인한다.
2. `rs-basic-*` Pod 한 개만 삭제한다.
3. 새로운 이름의 대체 Pod 한 개가 생성되어 다시 `READY 5`가 되는지 확인한다.
4. 강의 순서에 따라 Scale과 Template Update 실습으로 진행한다.

## 관련 노트

- [[Lab_EKS 첫 접속과 Pod 기초 실습]]
- [[Lab_EKS Pod Scheduling과 Node 운영 실습]]
- [[04_Kubernetes Pod와 ReplicaSet]]
- [[Source Digest/Kubernetes - Source Digest 04 Pod and ReplicaSet]]

## 공식 참고

- [ReplicaSet](https://kubernetes.io/docs/concepts/workloads/controllers/replicaset/)
- [kubectl apply](https://kubernetes.io/docs/reference/kubectl/generated/kubectl_apply/)
