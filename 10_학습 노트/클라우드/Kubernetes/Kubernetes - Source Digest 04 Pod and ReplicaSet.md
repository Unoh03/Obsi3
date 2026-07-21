---
type: source-digest
status: stable
created: 2026-07-21
parent_moc: "[[10_학습 노트/클라우드/Kubernetes/00_Kubernetes MOC]]"
source: "[[40_자료/강의 자료/Kubernetes.pdf]]"
source_pages: "13-73"
digest_role: chapter
digest_index: "[[10_학습 노트/클라우드/Kubernetes/Kubernetes - Source Digest v1]]"
chapter: "04 Pod and ReplicaSet"
source_hash: F97666865E22749C47640689B5C41DEE38476A40312A53915F60B4F6A4330D24
source_version: "PowerPoint PDF; 266 pages; metadata created 2024-07-18"
coverage_status: complete
extraction_method: "pdfplumber 0.11.9 text extraction + pypdfium2 render visual review"
reviewed_on: 2026-07-21
---

# Kubernetes - Source Digest 04 Pod and ReplicaSet

> [!purpose]
> [[40_자료/강의 자료/Kubernetes.pdf|Kubernetes.pdf]] p.13-p.73의 Pod·Scheduling·ReplicaSet 설명, Manifest, 명령, 출력과 도식 의미를 보존한 Chapter Digest다.

## Coverage

| 구간 | 주제 | Text·Code | Visual | 원본 대조 |
|---:|---|---|---|---|
| p.13-p.15 | Pod·ReplicaSet 개념 | 완료 | 완료 | 완료 |
| p.16-p.18 | Pod Basic | 완료 | 완료 | 완료 |
| p.19-p.20 | Environment Variable | 완료 | 완료 | 완료 |
| p.21-p.23 | Sidecar·Pod Network | 완료 | 완료 | 완료 |
| p.24-p.30 | Label·Selector | 완료 | 완료 | 완료 |
| p.31-p.36 | NodeSelector | 완료 | 완료 | 완료 |
| p.37-p.41 | NodeAffinity | 완료 | 완료 | 완료 |
| p.42-p.49 | Taints·Tolerations | 완료 | 완료 | 완료 |
| p.50-p.51 | cordon·drain | 완료 | 완료 | 완료 |
| p.52-p.62 | ReplicaSet Basic·Lifecycle | 완료 | 완료 | 완료 |
| p.63-p.70 | Template Update | 완료 | 완료 | 완료 |
| p.71-p.73 | Rollback Test | 완료 | 완료 | 완료 |

# Pod 기본·Network·Label - p.13-p.30

## p.13 - Kubernetes Pod & ReplicaSet 표지

- 원자료: [[40_자료/강의 자료/Kubernetes.pdf#page=13|Kubernetes.pdf p.13]]
- `Kubernetes Pod & ReplicaSet` Chapter의 표지다.
- 별도의 본문·Code·정보성 도식은 없다.

## p.14 - Pod와 ReplicaSet 개념

- 원자료: [[40_자료/강의 자료/Kubernetes.pdf#page=14|Kubernetes.pdf p.14]]

### 원자료 내용

**Kubernetes Pod**

- Worker Node에서 Application Container를 배포하는 기본 단위로 설명한다.
- Pod와 Container는 1:1 또는 1:N 관계가 될 수 있으며, 주로 Pod 하나에 Container 하나를 실행한다고 설명한다.
- 하나의 가상 Server처럼 동작하고 일회성 사용으로 설계되어 Pod IP는 실행 때마다 변경된다고 설명한다.
- Pod 내부 Container는 Pod의 Network 정보(IP)와 Volume 정보를 공유한다.
- 동일 Pod의 Container끼리는 `localhost`로 통신하며 Port 충돌에 주의해야 한다.
- Pod 내부 Container에는 같은 Cluster 안에서만 접근 가능하며 외부 접근에는 Service Object를 함께 사용한다고 설명한다.
- Pod는 단독 사용 가능하지만 주로 Service, Controller, Volume과 함께 사용한다고 설명한다.

**Kubernetes ReplicaSet**

- Pod 복제본을 생성·관리하고 Pod Self-Healing을 구현한다고 설명한다.
- 정의한 수만큼 Pod가 항상 유지되도록 관리한다.
- 자료는 ReplicaSet Object가 `Replication Controller`에 의해 관리·동작한다고 표현한다.
- Node 장애 시 장애 Node의 Pod 수만큼 대체 Node에서 Pod를 다시 생성한다고 설명한다.
- 관리자 개입 없는 Software Fault Tolerance 환경을 구성할 수 있다고 설명한다.
- 단독 생성 가능하지만 주로 Deployment에 포함해 사용한다고 설명한다.

## p.15 - Pod 접근·Sidecar·ReplicaSet Self-Healing 도식

- 원자료: [[40_자료/강의 자료/Kubernetes.pdf#page=15|Kubernetes.pdf p.15]]

### 도식·이미지 의미

- External Client에서 Pod IP로 직접 접근하는 경로는 `Access Denie`, Service를 거치는 경로는 `Access Allow`로 표시된다.
- 두 Pod의 IP 예시는 `224.1.1.2`, `224.1.1.3`이다.
- 한 Pod에는 Port 80과 Port 9090의 SideCar Container 두 개가, 다른 Pod에는 Port 80의 Single Container가 그려진다.
- `ReplicaSet (Replicas: 2)`가 Worker Node 1과 2에 Pod를 유지한다.
- Worker Node 1의 `Node Failure` 뒤 Worker Node 2에 `New Pod Create (Self-Healing)`가 일어나는 흐름을 그린다.

### 판독 불확실성

- `Access Denie`는 원자료 표기다.
- Pod IP 예시의 의미나 유효성은 PDF 밖에서 교정하지 않았다.

## p.16 - EX.1 Pod Basic Manifest

- 원자료: [[40_자료/강의 자료/Kubernetes.pdf#page=16|Kubernetes.pdf p.16]]

### Code·설명

작업 대상은 `pod-basic.yml`이다.

```yaml
apiVersion: v1                # API Resource Version
kind: Pod                     # 생성할 Object 종류
metadata:
  name: my-pod
spec:
  containers:
    - name: my-nginx-container
      image: nginx:latest
      ports:
        - containerPort: 80
          protocol: TCP
      resources:
        limits:
          memory: "100Mi"
          cpu: "500Mi"
```

- 원자료는 `metadata`를 Label·Annotation·Object Name 등의 Meta Data, `spec`을 Object 상세 정보로 설명한다.
- `resources`는 이후 생략한다고 쓰고 `RAM:100MB, CPU:0.5코어`라고 부연한다.

### 판독 불확실성

- `cpu: "500Mi"`는 원자료에 적힌 값을 그대로 보존했다. 실행 가능 여부는 교정하지 않았다.

## p.17 - Pod 생성·조회·상세 정보

- 원자료: [[40_자료/강의 자료/Kubernetes.pdf#page=17|Kubernetes.pdf p.17]]

```console
$ kubectl apply -f pod-basic.yml
pod/my-pod created

$ kubectl get pod
NAME    READY  STATUS   RESTARTS  AGE
my-pod  1/1    Running  0         7s

$ kubectl get pod -o wide
NAME    READY  STATUS   RESTARTS  AGE  IP             NODE    NOMINATED NODE  READINESS GATES
my-pod  1/1    Running  0         37m  192.168.10.58  node-1  <none>          <none>

$ kubectl describe pod my-pod
Name:        my-pod
Namespace:   default
Node:        ip-192-168-10-147.ap-northeast-2.compute.internal/192.168.10.147
Start Time:  Wed, 13 Sep 2023 13:32:16 +0900
Annotations: kubernetes.io/psp: eks.privileged
IP:          192.168.10.58
```

## p.18 - Debug Pod 통신 확인·삭제

- 원자료: [[40_자료/강의 자료/Kubernetes.pdf#page=18|Kubernetes.pdf p.18]]

```console
$ kubectl run -i --rm --tty debug --image=busybox -- sh
/ # wget 192.168.10.58
/ # cat index.html
<!DOCTYPE html>
<html>
<head>
<title>Welcome to nginx!</title>
</head>
<body>
<h1>Welcome to nginx!</h1>
... 생략 ...
/ # exit  # 원자료 설명: debug Pod Auto Delete

$ kubectl delete pod my-pod
pod "my-pod" deleted

$ kubectl get pod
No resources found in default namespace.
```

## p.19 - EX.2 Environment Variable Manifest

- 원자료: [[40_자료/강의 자료/Kubernetes.pdf#page=19|Kubernetes.pdf p.19]]

### Code·설명

작업 대상은 `pod-env.yml`이다. 원자료의 두 열을 하나의 YAML 흐름으로 재구성했다.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: env-pod
  labels:
    app: env-pod
spec:
  containers:
    - name: env-con
      image: ubuntu:bionic
      env:
        - name: MyName
          value: kube
        - name: HelloMessage
          value: Hello $(MyName)
        - name: NodeName
          valueFrom:
            fieldRef:
              fieldPath: spec.nodeName
        - name: NameSpace
          valueFrom:
            fieldRef:
              fieldPath: metadata.namespace
        - name: NodeIP
          valueFrom:
            fieldRef:
              fieldPath: status.hostIP
        - name: PodIP
          valueFrom:
            fieldRef:
              fieldPath: status.podIP
      command: ['sh', '-c', 'echo The app is running! && sleep 3600']
```

- 원자료는 `env`를 Container 환경변수 정의, `valueFrom`을 외부 참조, `fieldRef`를 Pod 생성 정보 참조라고 설명한다.
- 마지막 Command는 실행 Process가 없을 때 Container가 종료되는 것을 막기 위한 것으로 설명한다.

## p.20 - Environment Variable 확인

- 원자료: [[40_자료/강의 자료/Kubernetes.pdf#page=20|Kubernetes.pdf p.20]]

```console
$ kubectl apply -f ./pod-env.yml
pod/env-pod created

$ kubectl get pod -o wide
NAME     READY  STATUS   RESTARTS  AGE  IP             NODE    NOMINATED NODE  READINESS GATES
env-pod  1/1    Running  0         12s  192.168.10.14  node-1  <none>          <none>

$ kubectl exec env-pod -- env
PodIP=192.168.10.14
NodeIP=192.168.10.147
MyName=Kube
HelloMessage=Hello Kube

$ kubectl exec -it env-pod -- bash
root@env-pod:/# env | grep IP
PodIP=192.168.10.14

$ kubectl delete pod env-pod
pod "env-pod" deleted
```

## p.21 - EX.3 Sidecar·Network Manifest

- 원자료: [[40_자료/강의 자료/Kubernetes.pdf#page=21|Kubernetes.pdf p.21]]

### `pod-sidecar-net.yml`

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: pod-sidecar
  labels:
    name: pod-sidecar
spec:
  containers:
    - name: nginx-sidecar-app
      image: nginx:latest
      ports:
        - containerPort: 80
    - name: busybox-sidecar-app
      image: busybox:latest
      command: ['sh', '-c', 'echo The app is running! && sleep 3600']
```

### `pod-net.yml`

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: pod-net
  labels:
    name: pod-net
spec:
  containers:
    - name: nginx-app
      image: nginx:latest
      ports:
        - containerPort: 80
```

- 원자료는 BusyBox를 `Debugging Linux System`이라고 설명한다.

## p.22 - Sidecar·Network Pod 배포

- 원자료: [[40_자료/강의 자료/Kubernetes.pdf#page=22|Kubernetes.pdf p.22]]

```console
$ kubectl apply -f pod-sidecar-net.yml
pod/sidecar-pod created
$ kubectl apply -f pod-net.yml
pod/pod-net created

$ kubectl get pod -o wide
NAME         READY  STATUS   RESTARTS  AGE  IP              NODE    NOMINATED NODE  READINESS GATES
pod-net      1/1    Running  0         74m  192.168.20.181  node-1  <none>          <none>
pod-sidecar  2/2    Running  0         74m  192.168.10.58   node-2  <none>          <none>
```

- 원자료는 `pod-net`이 Node-1, `pod-sidecar`가 Node-2에 생성됐으며 Sidecar Pod의 READY가 `2/2`임을 확인한다.
- 실제 Node 이름 예시로 `ip-192-168-10-147.ap-northeast-2.compute.internal`을 제시한다.
- 생성 출력은 `pod/sidecar-pod`, 조회 이름은 `pod-sidecar`로 서로 다르게 표기돼 있다.

## p.23 - Pod 내부·Pod 간 통신

- 원자료: [[40_자료/강의 자료/Kubernetes.pdf#page=23|Kubernetes.pdf p.23]]

```console
$ kubectl exec -it pod-sidecar -c busybox-sidecar-app -- sh
/ # wget -Sq localhost:80
HTTP/1.1 200 OK
Server: nginx/1.23.0
Date: Tue, 12 Jul 2022 03:43:21 GMT

/ # rm –rf ./index.html

/ # wget -Sq 192.168.20.181:80
HTTP/1.1 200 OK
Server: nginx/1.23.0
Date: Tue, 12 Jul 2022 04:09:44 GMT

$ kubectl logs pod-net nginx-app
192.168.10.58 - - [12/Jul/2022:04:09:44 +0000] "GET / HTTP/1.1" 200 615 "-" "Wget" "-"

$ kubectl delete pod --all --namespace default
pod "pod-net" deleted
pod "pod-sidecar" deleted
```

- `localhost:80`은 같은 Pod의 `nginx-sidecar-app`, `192.168.20.181:80`은 다른 Pod의 `nginx-app` 통신으로 설명된다.

### 판독 불확실성

- `rm –rf`의 Dash는 원자료에 U+2013 EN DASH로 들어 있다. 실행용 ASCII `-`로 몰래 교정하지 않았다.

## p.24 - EX.4 Label Manifest 1·2

- 원자료: [[40_자료/강의 자료/Kubernetes.pdf#page=24|Kubernetes.pdf p.24]]

| 파일 | name | Labels | Container |
|---|---|---|---|
| `pod-label-test1.yml` | `label-app-1` | `group=web`, `app=app-1`, `version=v1`, `env=prod` | `webapp-1`, `nginx:latest`, Port 80 |
| `pod-label-test2.yml` | `label-app-2` | `group=web`, `app=app-2`, `version=v1`, `env=stage` | `webapp-2`, `nginx:latest`, Port 80 |

두 Manifest 모두 `apiVersion: v1`, `kind: Pod`를 사용한다.

## p.25 - EX.4 Label Manifest 3·4

- 원자료: [[40_자료/강의 자료/Kubernetes.pdf#page=25|Kubernetes.pdf p.25]]

| 파일 | name | Labels | Container |
|---|---|---|---|
| `pod-label-test3.yml` | `label-app-3` | `group=web`, `app=app-3`, `version=v1`, `env=test` | `webapp-3`, `nginx:latest`, Port 80 |
| `pod-label-test4.yml` | `label-app-4` | 없음 | `webapp-4`, `nginx:latest`, Port 80 |

두 Manifest 모두 `apiVersion: v1`, `kind: Pod`를 사용한다.

## p.26 - Label 조회

- 원자료: [[40_자료/강의 자료/Kubernetes.pdf#page=26|Kubernetes.pdf p.26]]

```console
$ kubectl apply -f label
pod/label-app-1 created / pod/label-app-2 created
pod/label-app-3 created / pod/label-app-4 created

$ kubectl get pod --show-labels
label-app-1 ... app=app-1,env=prod,group=web,version=v1
label-app-2 ... app=app-2,env=stage,group=web,version=v1
label-app-3 ... app=app-3,env=test,group=web,version=v1
label-app-4 ... <none>

$ kubectl get pod -L app,group,env
NAME         APP    GROUP  ENV
label-app-1  app-1  web    prod
label-app-2  app-2  web    stage
label-app-3  app-3  web    test
label-app-4  <none>
```

- 원자료는 `-f label`을 Directory의 Manifest 전체 선택, `-L`을 `--lable-columns`라고 설명한다.

## p.27 - Label 생성·갱신·삭제

- 원자료: [[40_자료/강의 자료/Kubernetes.pdf#page=27|Kubernetes.pdf p.27]]

```console
$ kubectl label pod label-app-4 app=app-4
LABELS: app=app-4

$ kubectl label pod label-app-4 app=app-test --overwrite
LABELS: app=app-test

$ kubectl label pod label-app-4 app-
LABELS: <none>
```

각 단계는 `kubectl get pod label-app-4 --show-labels`로 확인한다.

## p.28 - Label Selector 단일 조건

- 원자료: [[40_자료/강의 자료/Kubernetes.pdf#page=28|Kubernetes.pdf p.28]]

```console
$ kubectl get pod --selector env=prod
label-app-1

$ kubectl get pod --selector env=stage
label-app-2

$ kubectl get pod --selector env!=prod
label-app-2
label-app-3
label-app-4

$ kubectl get pod --selector '!env'
label-app-4
```

- 각각 값 일치, 값 불일치, Key 부재 Pod 조회로 설명한다.

## p.29 - Label Selector 복합 조건

- 원자료: [[40_자료/강의 자료/Kubernetes.pdf#page=29|Kubernetes.pdf p.29]]

```console
$ kubectl get pod --selector group=web,version=v1
label-app-1
label-app-2
label-app-3

$ kubectl get pod --selector env!=prod,group=web
label-app-2
label-app-3

$ kubectl get pod --selector 'env in (test,stage)'
label-app-2
label-app-3
```

- 앞의 두 Query는 AND, 마지막 `in`은 OR 조건 예시로 설명한다.

## p.30 - Label Selector Set 조건·정리

- 원자료: [[40_자료/강의 자료/Kubernetes.pdf#page=30|Kubernetes.pdf p.30]]

```console
$ kubectl get pod --selector 'env notin  (test,stage)'
label-app-1
label-app-4

$ kubectl get pod --selector 'group=web,version,env  in  (prod,stage)'
label-app-1
label-app-2

$ kubectl delete pod --all
pod "label-app-1" deleted
pod "label-app-2" deleted
pod "label-app-3" deleted
pod "label-app-4" deleted
```

- 두 번째 Query는 `group=web`, `version` Key 존재, `env`가 prod 또는 stage인 AND·OR 혼합 조건으로 설명한다.
- 원자료 설명에는 `stager`라는 표기가 있으며 이를 임의 수정하지 않았다.

# Pod Scheduling·Node 운영 - p.31-p.51

## p.31 - EX.5 NodeSelector: Node Label 확인

- 원자료: [[40_자료/강의 자료/Kubernetes.pdf#page=31|Kubernetes.pdf p.31]]

```console
$ kubectl get node
ip-192-168-10-147.ap-northeast-2.compute.internal  Ready  <none>  4h46m  v1.24.16-eks-8ccc7ba
ip-192-168-20-156.ap-northeast-2.compute.internal  Ready  <none>  4h46m  v1.24.16-eks-8ccc7ba

$ kubectl get node --show-labels
ip-192-168-10-147...  v1.19.16  kubernetes.io/hostname=ip-192-168-10-147...  # 생략
ip-192-168-20-156...  v1.19.16  kubernetes.io/hostname=ip-192-168-20-156...  # 생략
```

- Cluster Node 목록과 기본 Label을 확인한다.
- Node 식별 Label이 이미 정의돼 있고 실제 Label에는 Instance Type, AMI, Node Group 정보 등이 포함된다고 설명한다.
- 같은 Slide의 첫 출력은 v1.24.16, 두 번째 출력은 v1.19.16을 표시한다.

## p.32 - 사용자 지정 Node Label

- 원자료: [[40_자료/강의 자료/Kubernetes.pdf#page=32|Kubernetes.pdf p.32]]

```console
$ kubectl label node ip-192-168-10-147.ap-northeast-2.compute.internal project=django
$ kubectl label node ip-192-168-20-156.ap-northeast-2.compute.internal project=node

$ kubectl get node -L project
ip-192-168-10-147...  Ready  ...  v1.24.16-eks-8ccc7ba  django
ip-192-168-20-156...  Ready  ...  v1.24.16-eks-8ccc7ba  node
```

- Node 1에는 `project=django`, Node 2에는 `project=node`를 지정해 Pod가 생성될 Node를 직접 지정하는 데 사용한다.

## p.33 - `--overrides`를 이용한 NodeSelector

- 원자료: [[40_자료/강의 자료/Kubernetes.pdf#page=33|Kubernetes.pdf p.33]]

원자료는 아래 형식으로 `django-app-1`부터 `django-app-3`, `node-app-1`부터 `node-app-3`까지 여섯 Pod를 생성한다.

```console
$ kubectl run django-app-1 --labels="Framework=django" --image=nginx:latest ----
overrides='{ "spec":{ "nodeSelector":{ "project":"django" }}}'

$ kubectl run node-app-1 --labels="Framework=node" --image=nginx:latest ----
overrides='{ "spec":{ "nodeSelector":{ "project":"node" }}}'
```

- 각 Pattern을 이름의 1·2·3에 반복한다.
- 출력은 여섯 Pod가 생성됐다고 표시한다.
- `--overrides`를 JSON 형식 Object 속성 정의로 설명한다.

### 판독 불확실성

- `--image=nginx:latest` 뒤의 `----`와 다음 줄의 `overrides=`는 원자료 표기다. 실행 가능한 Line Continuation으로 교정하지 않았다.

## p.34 - NodeSelector 배치 결과

- 원자료: [[40_자료/강의 자료/Kubernetes.pdf#page=34|Kubernetes.pdf p.34]]

```console
$ kubectl get pod -o wide
NAME          READY  STATUS   RESTARTS  AGE  IP              NODE    NOMINATED NODE  READINESS GATES
django-app-1  1/1    Running  0         92s  192.168.10.149  node-1  <none>          <none>
django-app-2  1/1    Running  0         92s  192.168.10.156  node-1  <none>          <none>
django-app-3  1/1    Running  0         92s  192.168.10.58   node-1  <none>          <none>
node-app-1    1/1    Running  0         55s  192.168.20.181  node-2  <none>          <none>
node-app-2    1/1    Running  0         55s  192.168.20.169  node-2  <none>          <none>
node-app-3    1/1    Running  0         54s  192.168.20.179  node-2  <none>          <none>

$ kubectl delete pod --all
pod "django-app-1" deleted
pod "django-app-2" deleted
pod "django-app-3" deleted
pod "node-app-1" deleted
pod "node-app-2" deleted
pod "node-app-3" deleted
```

- `django-app`은 Node 1, `node-app`은 Node 2에 배치됐음을 확인하고 모두 삭제한다.

## p.35 - NodeSelector Manifest 두 개

- 원자료: [[40_자료/강의 자료/Kubernetes.pdf#page=35|Kubernetes.pdf p.35]]

### `nodeselector-test1.yml`

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: django-app
  labels:
    framework: django
spec:
  nodeSelector:
    project: django
  containers:
    - name: django-app
      image: nginx:latest
```

### `nodeselector-test2.yml`

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: node-app
  labels:
    framework: node
spec:
  nodeSelector:
    project: node
  containers:
    - name: node-app
      image: nginx:latest
```

## p.36 - NodeSelector 반복 확인·Label 삭제

- 원자료: [[40_자료/강의 자료/Kubernetes.pdf#page=36|Kubernetes.pdf p.36]]

```console
$ kubectl apply -f pod/nodeselector
$ kubectl get pod -o wide
django-app  ...  192.168.10.156  node-1
node-app    ...  192.168.20.117  node-2

$ kubectl delete pod --all
$ kubectl apply -f pod/nodeselector
$ kubectl get pod -o wide
django-app  ...  192.168.10.58   node-1
node-app    ...  192.168.20.179  node-2
$ kubectl delete pod --all

$ kubectl label node ip-192-168-10-147.ap-northeast-2.compute.internal project-
$ kubectl label node ip-192-168-20-156.ap-northeast-2.compute.internal project-
```

- 반복 배포해도 각 Pod가 지정 Node에 생성되는 것을 확인하고 사용자 지정 `project` Label을 삭제한다.

## p.37 - EX.6 NodeAffinity 개념·Node Zone Label

- 원자료: [[40_자료/강의 자료/Kubernetes.pdf#page=37|Kubernetes.pdf p.37]]

### 원자료 내용

- `requiredDuringSchedulingIgnoredDuringExecution`: Hard 조건, 반드시 만족하는 Node에 배치.
- `preferredDuringSchedulingIgnoredDuringExecution`: Soft 조건, 만족 Node를 우선하지만 다른 Node에도 배치 가능.
- 문서 URL: `https://kubernetes.io/docs/concepts/scheduling-eviction/assign-pod-node`

```console
$ kubectl get nodes --show-labels | grep failure-domain.beta.kubernetes.io/zone
ip-192-168-10-147... topology.kubernetes.io/zone=ap-northeast-2a
ip-192-168-20-156... topology.kubernetes.io/zone=ap-northeast-2c
```

- 이후 `topology.kubernetes.io/zone` Label `ap-northeast-2a`, `ap-northeast-2c`를 사용한다.

## p.38 - Required NodeAffinity 성공

- 원자료: [[40_자료/강의 자료/Kubernetes.pdf#page=38|Kubernetes.pdf p.38]]

```yaml
spec:
  affinity:
    nodeAffinity:
      requiredDuringSchedulingIgnoredDuringExecution:
        nodeSelectorTerms:
          - matchExpressions:
              - key: topology.kubernetes.io/zone
                operator: In
                values:
                  - ap-northeast-2a
```

```console
$ kubectl apply -f pod/nodeaffinity/nodeaffinity-test1.yml && kubectl get pod -o wide
node-app  1/1  Running  ...  192.168.10.231  ip-192-168-10-147
$ kubectl delete pod node-app
```

- Operator Option으로 `In`, `NotIn`, `Exists`, `DoesNotExist`, `Gt`, `Lt`를 열거한다.

## p.39 - Required NodeAffinity 실패

- 원자료: [[40_자료/강의 자료/Kubernetes.pdf#page=39|Kubernetes.pdf p.39]]

- p.38의 Required Manifest와 Operator 목록은 같고 `values`만 `ap-northeast-2a`에서 존재하지 않는 `ap-northeast-2b`로 바꾼다.

```console
$ kubectl apply -f pod/nodeaffinity/nodeaffinity-test1.yml && kubectl get pod -o wide
node-app  0/1  Pending  0  4s  <none>  <none>
$ kubectl delete pod node-app
```

- Hard 조건을 만족하는 Node가 없으면 Pod가 배포되지 않는다고 설명한다.

## p.40 - Preferred NodeAffinity 우선 배치

- 원자료: [[40_자료/강의 자료/Kubernetes.pdf#page=40|Kubernetes.pdf p.40]]

```yaml
preferredDuringSchedulingIgnoredDuringExecution:
  nodeSelectorTerms:
    - matchExpressions:
        - key: topology.kubernetes.io/zone
          operator: In
          values:
            - ap-northeast-2c
```

```console
node-app  1/1  Running  ...  192.168.20.185  ip-192-168-20-156
```

- Soft 조건을 만족하는 `ap-northeast-2c` Node에 배포하고 삭제한다.

## p.41 - Preferred NodeAffinity 대체 배치

- 원자료: [[40_자료/강의 자료/Kubernetes.pdf#page=41|Kubernetes.pdf p.41]]

- p.40의 Preferred Manifest·Operator 목록·실행 명령은 같고 `values`만 존재하지 않는 `ap-northeast-2b`로 바꾼다.

```console
node-app  1/1  Running  ...  192.168.10.169  ip-192-168-10-147
```

- Soft 조건을 만족하는 Node가 없어도 다른 Node에 Pod가 배포된다고 설명하고 Pod를 삭제한다.

## p.42 - EX.7 Taints·Tolerations 개념

- 원자료: [[40_자료/강의 자료/Kubernetes.pdf#page=42|Kubernetes.pdf p.42]]

### 원자료 내용

- Taint는 Node에 `<KEY>=<VALUE>:<EFFECT>`로 정의한다고 설명한다.
- Effect:
  - `NoSchedule`: Pod를 Scheduling하지 않음. 기존 Pod에는 영향 없음.
  - `NoExecute`: Pod 실행도 허용하지 않으며 기존 Pod를 강제 종료.
  - `PreferNoSchedule`: 가능하면 Scheduling하지 않음.
- Toleration은 Pod에 정의하며 `<KEY>/<VALUE>/<EFFECT>/<OPERATOR>`를 사용한다고 설명한다.
- Operator:
  - `Equal`: 지정 Taint 정보와 일치.
  - `Exists`: Key·Value·Effect에 대한 Wildcard로 설명.
- 예시 `KEY(X)/value(X)/EFFECT(NoSchedule)/Exists`는 `NoSchedule` Effect를 가진 모든 Node를 지정한다고 설명한다.

### 도식·이미지 의미

- Taint가 없는 Node는 Toleration이 없는 Pod와 연결된다.
- `Color=Green` Taint가 있는 Node는 `Color=Green` Toleration Pod만 허용하고 Toleration이 없는 Pod는 빨간 X로 거부한다.

## p.43 - Node에 Taint 설정

- 원자료: [[40_자료/강의 자료/Kubernetes.pdf#page=43|Kubernetes.pdf p.43]]

```console
$ kubectl get nodes
NAME                                                    STATUS  ROLES   AGE  VERSION
ip-192-168-10-147.ap-northeast-2.compute.internal      Ready   <none>  8d   v1.24.16-eks-8ccc7ba
ip-192-168-20-156.ap-northeast-2.compute.internal      Ready   <none>  8d   v1.24.16-eks-8ccc7ba

$ kubectl taint nodes ip-192-168-20-156.ap-northeast-2.compute.internal nodename=node2:NoSchedule
node/ip-192-168-20-156.ap-northeast-2.compute.internal tainted

$ kubectl describe nodes ip-192-168-20-156.ap-northeast-2.compute.internal | grep Taints
Name:              ip-192-168-20-156.ap-northeast-2.compute.internal
CreationTimestamp: Wed, 13 Sep 2023 01:07:38 +0000
Taints:            nodename=node2:NoSchedule
Unschedulable:     false
Addresses:
  InternalIP:  192.168.20.156
  Hostname:    ip-192-168-20-156.ap-northeast-2.compute.internal
  InternalDNS: ip-192-168-20-156.ap-northeast-2.compute.internal
```

## p.44 - Toleration 없는 Pod Manifest

- 원자료: [[40_자료/강의 자료/Kubernetes.pdf#page=44|Kubernetes.pdf p.44]]

두 파일 `taints-test1.yml`, `taints-test2.yml`은 각각 `node-app1`, `node-app` Pod를 정의한다.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: node-app1  # 다른 파일은 node-app
  labels:
    framework: node-app1  # 다른 파일은 node
spec:
  containers:
    - name: node-app1  # 다른 파일은 node-app
      image: nginx:latest
      resources:
        limits:
          memory: "100Mi"
          cpu: "500m"
```

## p.45 - Taint만 있을 때 배치 결과

- 원자료: [[40_자료/강의 자료/Kubernetes.pdf#page=45|Kubernetes.pdf p.45]]

```console
$ kubectl apply -f pod/taints
node-app1  1/1  Running  ...  192.168.10.169  ip-192-168-10-147
node-app2  1/1  Running  ...  192.168.10.156  ip-192-168-10-147
$ kubectl delete -f pod/taints
```

- 두 Pod 모두 Taint가 없는 첫 번째 Worker Node에 배치됐다고 설명한다.
- Manifest name과 출력 name(`node-app2`)은 서로 다르게 표시돼 있다.

## p.46 - `Equal` Toleration Manifest

- 원자료: [[40_자료/강의 자료/Kubernetes.pdf#page=46|Kubernetes.pdf p.46]]

두 Manifest의 `spec`에 같은 Toleration을 추가한다.

```yaml
tolerations:
  - key: nodename
    value: node2
    effect: NoSchedule
    operator: Equal
```

나머지 Container 정보는 p.44와 같다.

## p.47 - `Equal` Toleration 결과

- 원자료: [[40_자료/강의 자료/Kubernetes.pdf#page=47|Kubernetes.pdf p.47]]

```console
$ kubectl apply -f pod/taints
node-app1  1/1  Running  ...  192.168.20.117  ip-192-168-20-156
node-app2  1/1  Running  ...  192.168.20.169  ip-192-168-20-156
$ kubectl delete -f pod/taints
```

- 지정 Taint 조건과 일치하는 두 번째 Worker Node에 배치됐다고 설명한다.

## p.48 - `Exists` Toleration Manifest

- 원자료: [[40_자료/강의 자료/Kubernetes.pdf#page=48|Kubernetes.pdf p.48]]

두 Manifest의 Toleration을 다음처럼 바꾼다.

```yaml
tolerations:
  - effect: NoSchedule
    operator: Exists
```

- `key`와 `value`를 제거한다. 나머지 Container 정보는 p.44와 같다.

## p.49 - `Exists` 결과·정리

- 원자료: [[40_자료/강의 자료/Kubernetes.pdf#page=49|Kubernetes.pdf p.49]]

```console
$ kubectl apply -f pod/taints
node-app1  1/1  Running  ...  192.168.20.137  ip-192-168-20-156
node-app2  1/1  Running  ...  192.168.20.185  ip-192-168-20-156

$ kubectl delete -f pod/taints
$ kubectl taint nodes ip-192-168-20-156.ap-northeast-2.compute.internal nodename=node2:NoSchedule-
node/ip-192-168-20-156.ap-northeast-2.compute.internal untainted
```

- `Exists`와 `NoSchedule`을 사용해 해당 Effect의 Taint를 가진 Node에 배포한다고 설명한다.
- Test Pod와 Node Taint를 삭제한다.

## p.50 - EX.8 cordon·uncordon

- 원자료: [[40_자료/강의 자료/Kubernetes.pdf#page=50|Kubernetes.pdf p.50]]

- `cordon`은 Node Scheduling을 중단해 추가 Pod 배포를 막지만 이미 배포된 Pod는 정상 동작한다고 설명한다.

```console
$ kubectl cordon ip-192-168-20-156.ap-northeast-2.compute.internal
node/ip-192-168-20-156.ap-northeast-2.compute.internal cordoned

$ kubectl get nodes
ip-192-168-20-156...  Ready,SchedulingDisabled

$ kubectl uncordon ip-192-168-20-156.ap-northeast-2.compute.internal
node/ip-192-168-20-156.ap-northeast-2.compute.internal uncordoned
```

## p.51 - drain·uncordon

- 원자료: [[40_자료/강의 자료/Kubernetes.pdf#page=51|Kubernetes.pdf p.51]]

- `drain`은 Node를 비활성화해 Pod 배포를 막는다고 설명한다.
- Multiple Pod(`replicas: 2`)는 다른 활성 Node로 이동하고 Single Pod(`replicas: 1`)는 이동하지 않는다고 설명한다.

```console
$ kubectl drain ip-192-168-20-156.ap-northeast-2.compute.internal \
  --ignore-daemonsets --delete-emptydir-data
evicting pod kube-system/efs-csi-controller-5cf794bfc4-t9vdx
evicting pod kube-system/aws-load-balancer-controller-8684f5455c-jps7h
evicting pod kube-system/coredns-dc4979556-59xzb
evicting pod kube-system/coredns-dc4979556-75ldc

$ kubectl get nodes
ip-192-168-20-156...  Ready,SchedulingDisabled

$ kubectl uncordon ip-192-168-20-156.ap-northeast-2.compute.internal
node/ip-192-168-20-156.ap-northeast-2.compute.internal uncordoned
```

# ReplicaSet Basic·Lifecycle - p.52-p.62

## p.52 - ReplicaSet Basic Manifest

- 원자료: [[40_자료/강의 자료/Kubernetes.pdf#page=52|Kubernetes.pdf p.52]]

### Code·도식 의미

작업 대상은 `rs-basic.yml`이다. 원자료에서 좌우로 연결된 Manifest를 한 흐름으로 재구성했다.

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
      name: nginx-template
      labels:
        app: nginx-app
    spec:
      containers:
        - name: nginx-con
          image: nginx:latest
          ports:
            - containerPort: 80
```

- `replicas`는 복제 Pod 수를 정의한다.
- `selector`가 Label로 Pod Template을 선택하고 Pod를 생성한다고 설명한다.
- `matchLabels`와 Template Label은 반드시 일치해야 한다고 설명한다.
- 도식 화살표는 `selector.matchLabels.app=nginx-app`과 `template.metadata.labels.app=nginx-app`의 대응을 보여준다.

## p.53 - ReplicaSet 생성·조회

- 원자료: [[40_자료/강의 자료/Kubernetes.pdf#page=53|Kubernetes.pdf p.53]]

```console
$ kubectl apply -f replicaset/rs-basic.yml
replicaset.apps/rs-basic created

$ kubectl get rs rs-basic -o wide
NAME      DESIRED  CURRENT  READY  AGE  CONTAINERS  IMAGES        SELECTOR
rs-basic  5        5        5      94s  nginx-con   nginx:latest  app=nginx-app

$ kubectl get pod -o wide
rs-basic-c8w45  192.168.20.93   node-2
rs-basic-sfmtb  192.168.10.156  node-1
rs-basic-6zmhw  192.168.10.58   node-1
rs-basic-z6ns9  192.168.10.22   node-1
rs-basic-8pqhw  192.168.20.130  node-2
```

- `DESIRED`는 목표치, `CURRENT`는 현재 상태, `READY`는 준비 상태로 설명한다.
- ReplicaSet Pod Name을 `ReplicaSet Name + Hash Value`로 설명한다.
- Resource Shortname은 `kubectl api-resources`로 확인할 수 있다고 적는다.

## p.54 - ReplicaSet 상세 정보·삭제

- 원자료: [[40_자료/강의 자료/Kubernetes.pdf#page=54|Kubernetes.pdf p.54]]

```console
$ kubectl describe rs rs-basic
Name:        rs-basic
Selector:    app=nginx-app
Replicas:    5 current / 5 desired
Pods Status: 5 Running / 0 Waiting / 0 Succeeded / 0 Failed
Pod Template:
  Labels: app=nginx-app
Events:
  Normal SuccessfulCreate ... Created pod: rs-basic-c8w45
  Normal SuccessfulCreate ... Created pod: rs-basic-sfmtb
  Normal SuccessfulCreate ... Created pod: rs-basic-6zmhw
  Normal SuccessfulCreate ... Created pod: rs-basic-z6ns9
  Normal SuccessfulCreate ... Created pod: rs-basic-8pqhw

$ kubectl delete rs rs-basic
replicaset.apps "rs-basic" deleted
```

- `describe` 출력은 중요 부분만 남긴 생략본이라고 명시한다.

## p.55 - ReplicaSet 관리 영역에 기존 Pod 편입

- 원자료: [[40_자료/강의 자료/Kubernetes.pdf#page=55|Kubernetes.pdf p.55]]

```console
$ kubectl run nginx-pod --labels="app=nginx-app" --image=nginx:latest
pod/nginx-pod created

$ kubectl get pod --show-labels
nginx-pod  1/1  Running  ...  app=nginx-app

$ kubectl apply -f replicaset/rs-basic.yml
$ kubectl get pod -o wide
nginx-pod      ...  192.168.10.240  node-2
rs-basic-ffw5m ...  192.168.20.89   node-1
rs-basic-mk8x4 ...  192.168.10.58   node-2
rs-basic-pbxnz ...  192.168.20.169  node-1
rs-basic-tg5rr ...  192.168.10.156  node-1
```

- Selector와 같은 Label을 가진 기존 단독 Pod가 ReplicaSet의 다섯 Pod 중 하나로 포함되고, 새 Pod는 네 개만 생성된 상황을 보여준다.

## p.56 - 관리 영역 Events 확인

- 원자료: [[40_자료/강의 자료/Kubernetes.pdf#page=56|Kubernetes.pdf p.56]]

```text
Name: rs-basic
Selector: app=nginx-app
Replicas: 5 current / 5 desired
Pods Status: 5 Running
Events: SuccessfulCreate 4건
  99s  rs-basic-ffw5m
  99s  rs-basic-mk8x4
  99s  rs-basic-pbxnz
  99s  rs-basic-tg5rr
```

- 같은 Selector Label의 기존 Pod는 자동으로 ReplicaSet 관리 대상에 포함된다고 설명한다.
- ReplicaSet 구성 전 기존 운영 Pod의 Label을 확인해야 한다고 경고한다.

## p.57 - Pod 삭제 뒤 복구

- 원자료: [[40_자료/강의 자료/Kubernetes.pdf#page=57|Kubernetes.pdf p.57]]

```console
$ kubectl delete pod nginx-pod
$ kubectl describe rs rs-basic
Replicas:    5 current / 5 desired
Pods Status: 5 Running / 0 Waiting / 0 Succeeded / 0 Failed
Events:
  Normal SuccessfulCreate 99s ... Created pod: rs-basic-ffw5m
  Normal SuccessfulCreate 99s ... Created pod: rs-basic-mk8x4
  Normal SuccessfulCreate 99s ... Created pod: rs-basic-pbxnz
  Normal SuccessfulCreate 99s ... Created pod: rs-basic-tg5rr
  Normal SuccessfulCreate 49m ... Created pod: rs-basic-dcrkn
```

- 관리 대상 Pod 삭제 뒤 새 Pod를 생성해 요구치 5개를 유지한다.
- Worker Node 장애 때도 정상 Node에서 부족한 수만큼 새 Pod를 생성한다고 설명한다.

## p.58 - ReplicaSet과 Pod 동시 삭제

- 원자료: [[40_자료/강의 자료/Kubernetes.pdf#page=58|Kubernetes.pdf p.58]]

```console
$ kubectl delete rs rs-basic
replicaset.apps "rs-basic" deleted
$ kubectl get rs
No resources found in default namespace.
$ kubectl get pod
No resources found in default namespace.

$ kubectl apply -f replicaset/rs-basic.yml
replicaset.apps/rs-basic created
$ kubectl get rs
rs-basic  5  5  5  7s
```

- 기본 삭제에서는 관리 Pod도 함께 삭제된다고 설명하고 다음 Test를 위해 다시 생성한다.

## p.59 - `--cascade=false` 삭제

- 원자료: [[40_자료/강의 자료/Kubernetes.pdf#page=59|Kubernetes.pdf p.59]]

```console
$ kubectl delete rs rs-basic --cascade=false
replicaset.apps "rs-basic" deleted
$ kubectl get rs
No resources found in default namespace.
$ kubectl get pod
rs-basic-bthv6  Running
rs-basic-cgqvt  Running
rs-basic-gdhmg  Running
rs-basic-k78bn  Running
rs-basic-n7zh9  Running

$ kubectl delete pod --all
```

- `--cascade=false`로 ReplicaSet만 삭제되고 다섯 Pod는 남는 결과를 보여준 뒤 Pod를 모두 삭제한다.

## p.60 - Scale Down 시작

- 원자료: [[40_자료/강의 자료/Kubernetes.pdf#page=60|Kubernetes.pdf p.60]]

```console
$ kubectl apply -f replicaset/rs-basic.yml
replicaset.apps/rs-basic created
$ kubectl get pod
rs-basic-8g6df
rs-basic-8grsk
rs-basic-9n7fx
rs-basic-cx92w
rs-basic-rncrc

$ kubectl scale rs rs-basic --replicas 3
replicaset.apps/rs-basic scaled
```

- `kubectl scale`로 `replicas` 값을 바꾼다.
- Pod를 한 번에 모두 지우는 대신 수를 점차 줄이는 `GraceFully 삭제`로 설명한다.

## p.61 - Scale·Edit 결과

- 원자료: [[40_자료/강의 자료/Kubernetes.pdf#page=61|Kubernetes.pdf p.61]]

```console
$ kubectl get pod
rs-basic-8grsk  Running
rs-basic-9n7fx  Running
rs-basic-rncrc  Running

$ kubectl edit rs rs-basic
replicas: 2
replicaset.apps/rs-basic edited

$ kubectl get pod
rs-basic-9n7fx  Running
rs-basic-rncrc  Running
```

- Pod 수가 5→3→2로 줄어드는 것을 확인한다.
- `kubectl edit`은 생성된 Object 정보를 Vim Editor로 바꾸는 방식으로 설명한다.

## p.62 - Replica 0과 ReplicaSet 삭제

- 원자료: [[40_자료/강의 자료/Kubernetes.pdf#page=62|Kubernetes.pdf p.62]]

```console
$ kubectl scale rs rs-basic --replicas 0
replicaset.apps/rs-basic scaled
$ kubectl get pod
rs-basic-rncrc  0/1  Terminating  0  8m23s
$ kubectl get pod
No resources found in default namespace.
$ kubectl get rs
rs-basic  0  0  0  8m57s

$ kubectl delete rs rs-basic
replicaset.apps "rs-basic" deleted
$ kubectl get rs
No resources found in default namespace.
```

- Replica 0은 Pod를 모두 삭제하지만 ReplicaSet Object는 남기므로 마지막에 별도 삭제한다.

# ReplicaSet Template Update·Rollback - p.63-p.73

## p.63 - Update·Rollback 기본 Manifest

- 원자료: [[40_자료/강의 자료/Kubernetes.pdf#page=63|Kubernetes.pdf p.63]]

작업 대상은 `rs-update-rollback.yml`이다.

```yaml
apiVersion: apps/v1
kind: ReplicaSet
metadata:
  name: rs-rollback
spec:
  replicas: 3
  selector:
    matchLabels:
      app: node-app
  template:
    metadata:
      name: node-template
      labels:
        app: node-app
    spec:
      containers:
        - name: node-con
          image: node:16-alpine3.15
          command: ['sh', '-c', 'tail -f /dev/null']
```

- Template Update·Rollback Test용 Manifest다.
- Container 종료 방지를 위해 `tail -f /dev/null`을 사용한다고 설명한다.

## p.64 - 기본 ReplicaSet 생성

- 원자료: [[40_자료/강의 자료/Kubernetes.pdf#page=64|Kubernetes.pdf p.64]]

```console
$ kubectl apply -f replicaset/rs-update-rollback.yml
replicaset.apps/rs-rollback created
$ kubectl get rs -o wide
rs-rollback  3  3  3  15s  node-con  node:16-alpine3.15  app=node-app
$ kubectl get pod -o wide
rs-rollback-pqnlb  192.168.10.58   node-2
rs-rollback-rlczz  192.168.10.248  node-1
rs-rollback-znkmg  192.168.20.169  node-1
```

## p.65 - Pod Template Label 추가

- 원자료: [[40_자료/강의 자료/Kubernetes.pdf#page=65|Kubernetes.pdf p.65]]

p.63 Manifest의 `template.metadata.labels`에 두 Label을 추가한다.

```yaml
labels:
  app: node-app
  version: v1
  env: prod
```

- Selector `app: node-app`, Image `node:16-alpine3.15`는 유지한다.
- 도식 화살표는 변경된 Label 영역을 가리킨다.

## p.66 - Template Label 변경 결과

- 원자료: [[40_자료/강의 자료/Kubernetes.pdf#page=66|Kubernetes.pdf p.66]]

```console
$ kubectl apply -f replicaset/rs-update-rollback.yml
replicaset.apps/rs-rollback configured
$ kubectl get pod --show-labels
rs-rollback-pqnlb  app=node-app
rs-rollback-rlczz  app=node-app
rs-rollback-znkmg  app=node-app

$ kubectl delete pod rs-rollback-znkmg
pod "rs-rollback-f9j2x" deleted
$ kubectl get pod --show-labels
rs-rollback-pqnlb  app=node-app
rs-rollback-rlczz  app=node-app
rs-rollback-sxb46  app=node-app,env=prod,version=v1
```

- Template 수정은 기존 Pod에 반영되지 않고 삭제 후 새로 생성된 Pod에만 반영된다고 설명한다.
- 삭제 명령 대상과 삭제 출력 Pod 이름이 서로 다르게 적혀 있다.

## p.67 - Pod Template Image 변경

- 원자료: [[40_자료/강의 자료/Kubernetes.pdf#page=67|Kubernetes.pdf p.67]]

- p.63의 기본 Manifest와 p.65에서 추가한 `version: v1`, `env: prod` Label은 그대로 두고 Image만 다음처럼 바꾼다.

```yaml
image: node:18-alpine3.15
```

- 원자료는 개발팀이 새 Version Image를 배포한 상황이라고 설명한다.
- 변경 전후를 `node:16-alpine3.15 → node:18-alpine3.15`로 표시한다.

## p.68 - ReplicaSet Image 갱신과 기존 Pod

- 원자료: [[40_자료/강의 자료/Kubernetes.pdf#page=68|Kubernetes.pdf p.68]]

```console
$ kubectl apply -f replicaset/rs-update-rollback.yml
replicaset.apps/rs-rollback configured
$ kubectl get rs -o wide
rs-rollback  3  3  3  ...  node-con  node:18-alpine3.15  app=node-app

$ kubectl describe pod
Image: node:16-alpine3.15
Image: node:16-alpine3.15
Image: node:16-alpine3.15
```

- ReplicaSet Image는 바뀌었지만 기존 Pod Image는 이전 Version이라고 설명한다.
- 새 Image 적용을 위해 기존 Pod를 삭제하고 새 Pod가 생성되게 해야 한다고 설명한다.

## p.69 - Scale Down·Up으로 Pod 재생성

- 원자료: [[40_자료/강의 자료/Kubernetes.pdf#page=69|Kubernetes.pdf p.69]]

```console
$ kubectl scale rs rs-rollback --replicas=0
replicaset.apps/rs-rollback scaled
$ kubectl get pod -o wide
rs-rollback-pqnlb  Terminating  192.168.10.58   node-2
rs-rollback-rlczz  Terminating  192.168.10.240  node-1
rs-rollback-sxb46  Terminating  192.168.20.185  node-2

$ kubectl scale rs rs-rollback --replicas=3
$ kubectl get pod -o wide
rs-rollback-6gq7t  ContainerCreating  node-1
rs-rollback-drbx7  ContainerCreating  node-2
rs-rollback-vhtj8  ContainerCreating  node-1
```

- 기존 세 Pod를 Scale Down한 뒤 새 Image Pod 세 개를 Scale Up한다.

## p.70 - 새 Image 확인·Template Update 정리

- 원자료: [[40_자료/강의 자료/Kubernetes.pdf#page=70|Kubernetes.pdf p.70]]

```console
$ kubectl get pod -o wide
rs-rollback-6gq7t  Running  192.168.10.132  node-1
rs-rollback-drbx7  Running  192.168.20.169  node-2
rs-rollback-vhtj8  Running  192.168.20.179  node-1

$ kubectl describe pod
Image: node:18-alpine3.15
Image: node:18-alpine3.15
Image: node:18-alpine3.15
```

원자료의 Template Update 정리:

1. ReplicaSet Manifest를 변경해도 기존 Pod에는 영향을 주지 않는다.
2. 변경 사항을 적용하려면 새 Pod를 배포해야 한다.

## p.71 - `kubectl set image` Rollback Test

- 원자료: [[40_자료/강의 자료/Kubernetes.pdf#page=71|Kubernetes.pdf p.71]]

```console
$ kubectl get rs -o wide
rs-rollback  3  3  3  ...  node-con  node:18-alpine3.15  app=node-app

$ kubectl set image rs/rs-rollback node-con=node:16-alpine3.15
replicaset.apps/rs-rollback image updated

$ kubectl get rs -o wide
rs-rollback  3  3  3  ...  node-con  node:16-alpine3.15  app=node-app

$ kubectl describe pod
Image: node:18-alpine3.15
Image: node:18-alpine3.15
Image: node:18-alpine3.15
```

- Manifest 편집 대신 `kubectl set image`로 ReplicaSet Image를 이전 Version으로 바꾼다.
- 변경은 ReplicaSet에만 적용되고 기존 Pod는 바뀌지 않는다고 설명한다.

## p.72 - Label 변경으로 기존 Pod를 관리 대상에서 제외

- 원자료: [[40_자료/강의 자료/Kubernetes.pdf#page=72|Kubernetes.pdf p.72]]

```console
$ kubectl get pod --show-labels
rs-rollback-6gq7t  app=node-app,env=prod,version=v1
rs-rollback-drbx7  app=node-app,env=prod,version=v1
rs-rollback-vhtj8  app=node-app,env=prod,version=v1

$ kubectl label pod rs-rollback-6gq7t app=delay-app --overwrite
$ kubectl label pod rs-rollback-drbx7 app=delay-app --overwrite
$ kubectl label pod rs-rollback-vhtj8 app=delay-app --overwrite

$ kubectl get pod --show-labels
rs-rollback-6gq7t  app=delay-app,env=prod
rs-rollback-drbx7  app=delay-app,env=prod
rs-rollback-vhtj8  app=delay-app,env=prod
rs-rollback-qjbfl  app=node-app,env=prod
rs-rollback-swrjc  app=node-app,env=prod
rs-rollback-tt5rh  app=node-app,env=prod
```

- 기존 세 Pod의 `app` Label을 바꿔 ReplicaSet 관리 대상에서 제외한다.
- ReplicaSet은 `app=node-app`을 만족하는 새 Pod 세 개를 생성하며, 원자료는 이 새 Pod가 이전 Version Image를 갖는다고 설명한다.
- 출력의 새 Pod Label에는 `version=v1`이 표시되지 않는다.

## p.73 - 기존 Pod 삭제·Rollback 결과·정리

- 원자료: [[40_자료/강의 자료/Kubernetes.pdf#page=73|Kubernetes.pdf p.73]]

```console
$ kubectl delete pod rs-rollback-6gq7t
$ kubectl delete pod rs-rollback-drbx7
$ kubectl delete pod rs-rollback-vhtj8

$ kubectl describe pod
Image: node:16-alpine3.15
Image: node:16-alpine3.15
Image: node:16-alpine3.15

$ kubectl delete rs rs-rollback
replicaset.apps "rs-rollback" deleted
$ kubectl get rs
No resources found in default namespace.
$ kubectl get pod
No resources found in default namespace.
```

- 기존 Image Pod를 삭제하고 새 Pod의 Image가 `node:16-alpine3.15`임을 확인한다.
- Test에 사용한 ReplicaSet과 Pod를 삭제한다.

## 판독 불확실성·원자료 내부 불일치

- p.16 `cpu: "500Mi"`, p.23 U+2013 EN DASH, p.33 `---- overrides`는 원자료 표기를 보존했다.
- p.22의 생성 출력 `sidecar-pod`와 조회 이름 `pod-sidecar`, p.45의 Manifest 이름과 출력 `node-app2`, p.66의 삭제 명령·출력 Pod 이름이 서로 다르다.
- p.31은 한 Page 안에서 Kubernetes Version v1.24.16과 v1.19.16을 함께 표시한다.
- p.37의 `failure-domain.beta...` grep 명령과 출력의 `topology.kubernetes.io/zone` 관계는 원자료 그대로 기록했다.
- p.52 이후 동작 설명은 원자료의 실행 결과이며 현재 Kubernetes Version에서 재실행 검증한 결과가 아니다.

## 완료 검증

- [x] p.13-p.73 모든 Page를 Heading과 Coverage에 포함했다.
- [x] 두 열 YAML은 Rendering으로 분리해 들여쓰기와 대응 관계를 재구성했다.
- [x] 정보성 도식 p.15, p.42, p.52, p.63, p.65, p.67을 Rendering으로 검수했다.
- [x] 명령·Quote·Dash·Line Continuation을 원본과 대조했다.
- [x] 원자료 내부 오타·불일치를 임의로 교정하지 않고 표시했다.
- [x] 원자료 밖의 현재성 판단을 원자료 사실과 섞지 않았다.
- [x] 각 Page에서 PDF 원본으로 역추적할 수 있다.
