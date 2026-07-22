---
type: lab
status: active
created: 2026-07-22
lab_date: 2026-07-22
topic: kubernetes
parent_moc: "[[10_학습 노트/클라우드/Kubernetes/00_Kubernetes MOC]]"
source: "[[10_학습 노트/클라우드/Kubernetes/Source Digest/Kubernetes - Source Digest 04 Pod and ReplicaSet]]"
environment: "Amazon EKS ap-northeast-2; Kubernetes v1.35.6-eks-8f14419; Worker Node 2대"
evidence: "Bastion rs-basic.yml·kubectl 출력과 Local Terraform Destroy 출력"
verified_on: 2026-07-22
---

# EKS ReplicaSet 기초 실습

> [!summary]
> `rs-basic` ReplicaSet을 생성해 희망 복제 수 5개에 맞춘 Pod Object 생성을 확인했다. 현재 검증 범위는 PDF p.52의 생성과 `DESIRED 5 / CURRENT 5 / READY 0`까지이며, 실제 실행과 Self-Healing은 다음 환경에서 이어간다.

> [!info] 선행 실습
> EKS 접속·Pod 기본은 [[Lab_EKS 첫 접속과 Pod 기초 실습]], Node Scheduling·Drain은 [[Lab_EKS Pod Scheduling과 Node 운영 실습]]에 기록한다.

## 목표

- ReplicaSet의 Selector와 Pod Template Label 관계를 확인한다.
- `replicas` 희망 상태가 Pod Object 생성으로 이어지는 과정을 관찰한다.
- 다음 환경에서 `READY 5`와 Pod 삭제 후 Self-Healing을 검증한다.

## EX.1 ReplicaSet Basic 시작

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

## 검증 완료와 미완료

### 완료

- ReplicaSet `rs-basic` 생성
- `DESIRED 5`, `CURRENT 5`, `READY 0` 확인
- ReplicaSet이 Pod Object 5개를 생성한 사실 확인
- ReplicaSet `rs-basic`: `DESIRED 5`, `CURRENT 5`, `READY 0`과 Pod Object 5개 생성 확인
- `Pending` Event가 `2 node(s) were unschedulable`임을 확인
- `00_eks` Destroy: 84개 Resource 삭제, State 0
- `00_eks` 주요 EKS·VPC·EC2·ASG·ENI·IAM·OIDC 잔존 없음

### 미완료·추가 증거 필요

- ReplicaSet Pod의 `READY 5`와 Self-Healing 동작
- Scale Up·Down과 Template 변경·Rollback
- 오늘 사용한 현재 `00_eks` 환경의 Terraform Destroy·State 0·주요 잔존 Resource 확인
- AWS 계정 전체 Region·서비스의 비용 Resource 전수 확인

## 다음 재시작 지점

1. 새 EKS 환경에서 이 노트의 `rs-basic.yml`을 복원한다.
2. Worker Node와 CoreDNS가 `Running`인지 확인한다.
3. `kubectl apply -f rs-basic.yml` 후 `READY 5`를 확인한다.
4. Pod 한 개를 삭제해 ReplicaSet Self-Healing을 확인한다.

## 관련 노트

- [[Lab_EKS 첫 접속과 Pod 기초 실습]]
- [[Lab_EKS Pod Scheduling과 Node 운영 실습]]
- [[04_Kubernetes Pod와 ReplicaSet]]
- [[Source Digest/Kubernetes - Source Digest 04 Pod and ReplicaSet]]

## 공식 참고

- [ReplicaSet](https://kubernetes.io/docs/concepts/workloads/controllers/replicaset/)
- [kubectl apply](https://kubernetes.io/docs/reference/kubectl/generated/kubectl_apply/)
