---
type: source-digest
status: stable
created: 2026-07-21
parent_moc: "[[10_학습 노트/클라우드/Kubernetes/00_Kubernetes MOC]]"
source: "[[40_자료/강의 자료/Kubernetes.pdf]]"
source_pages: 110-134
digest_role: chapter
digest_index: "[[10_학습 노트/클라우드/Kubernetes/Kubernetes - Source Digest v1]]"
chapter: Service Object
source_hash: F97666865E22749C47640689B5C41DEE38476A40312A53915F60B4F6A4330D24
source_version: "PowerPoint PDF; 266 pages; metadata created 2024-07-18"
coverage_status: complete
extraction_method: "pdfplumber 0.11.9 text extraction + pypdfium2 render visual review"
reviewed_on: 2026-07-21
---

# Kubernetes Source Digest 06 — Service Object

> 원자료 `Kubernetes.pdf` p.110-134를 페이지 단위로 옮긴 무손실 구조화 사본이다. 원자료의 오탈자·출력 불일치는 임의로 교정하지 않고 해당 페이지에 표시한다.

## Coverage

| 범위 | Text | Visual | 원본 대조 | 상태 |
|---|---|---|---|---|
| p.110-134 | 완료 | 완료 | 완료 | 이 장 변환 완료 |

## PDF p.110

- 원문: [[40_자료/강의 자료/Kubernetes.pdf#page=110|Kubernetes.pdf p.110]]

### 원자료 내용

- 장 표지: `Kubernetes Service Object`.

## PDF p.111

- 원문: [[40_자료/강의 자료/Kubernetes.pdf#page=111|Kubernetes.pdf p.111]]

### 원자료 내용

- Service 오브젝트는 Pod 집합에 접근하기 위한 네트워크 규칙을 정의한다.
- Pod IP는 영구적이지 않고 외부에서 직접 접근할 수 없는 사설 주소이므로, 외부 노출에는 Service가 필요하다.
- Service는 연결 대상 Pod의 `Endpoints`를 갱신하고, 요청을 Endpoint 중 하나로 전달한다.
- 생성된 Service는 Kubernetes Cluster DNS에 자동 등록된다.

### 도식 의미

- Client가 `port: 80`인 Service로 접근한다.
- Service selector는 `app: nginx`이고, Pod template label은 `app: nginx`, `env: production`이다.
- Service는 다음 Endpoint의 `containerPort: 8080`으로 요청을 전달한다.
  - `192.168.10.123:8080`
  - `192.168.10.124:8080`
  - `192.168.10.125:8080`
- 세 번째 Endpoint에는 취소선이 표시되어 있어, Pod 변경 시 Endpoint 집합에서 빠지는 상황을 나타낸다.

## PDF p.112

- 원문: [[40_자료/강의 자료/Kubernetes.pdf#page=112|Kubernetes.pdf p.112]]

### 원자료 내용

#### ClusterIP

- Cluster 내부에서만 접근할 수 있는 IP를 할당한다.
- Cluster 외부 Client는 ClusterIP Service에 직접 접근할 수 없다.

#### NodePort

- 모든 Node에서 동일한 포트를 열어 외부 접근을 허용한다.
- 도식에는 각 Node에 `30000` 포트가 열리고 외부 Client가 이를 통해 Service에 접근하는 흐름이 표시된다.

## PDF p.113

- 원문: [[40_자료/강의 자료/Kubernetes.pdf#page=113|Kubernetes.pdf p.113]]

### 원자료 내용

#### LoadBalancer

- 외부 Load Balancer를 통해 Service를 외부에 노출한다.

#### ExternalName

- Cluster 외부 Resource를 Domain 이름으로 연결한다.
- 도식의 외부 Resource 예시는 `RDS`, `S3`, `ElastiCache`이다.

## PDF p.114

- 원문: [[40_자료/강의 자료/Kubernetes.pdf#page=114|Kubernetes.pdf p.114]]

### 원자료 내용

- `svc-clusterip-list.yml`의 Service와 Deployment 예시이다.

```yaml
apiVersion: v1
kind: Service
metadata:
  name: list-svc
  labels:
    app: list-app
    project: delivery
  namespace: delivery
spec:
  type: ClusterIP
  selector:
    app: list-app
  ports:
    - port: 80
      targetPort: 8000
```

- 같은 파일의 Deployment는 다음 속성을 갖는다.
  - `replicas: 2`
  - selector와 Pod label: `app: list-app`
  - container name: `list-app`
  - image: `chlzzz/kube-image:list`
  - `containerPort: 8000`
- 원자료는 Deployment 전체 코드는 TXT 파일을 참고하라고 안내한다.

## PDF p.115

- 원문: [[40_자료/강의 자료/Kubernetes.pdf#page=115|Kubernetes.pdf p.115]]

### 원자료 내용

- `svc-clusterip-order.yml`의 Service와 Deployment 예시이다.

```yaml
apiVersion: v1
kind: Service
metadata:
  name: order-svc
  labels:
    app: order-app
    project: delivery
  namespace: delivery
spec:
  type: ClusterIP
  selector:
    app: order-app
  ports:
    - port: 80
      targetPort: 8000
```

- 같은 파일의 Deployment는 다음 속성을 갖는다.
  - `replicas: 2`
  - selector와 Pod label: `app: order-app`
  - container name: `order-app`
  - image: `chlzzz/kube-image:order`
  - `containerPort: 8000`
- 원자료는 Deployment 전체 코드는 TXT 파일을 참고하라고 안내한다.

## PDF p.116

- 원문: [[40_자료/강의 자료/Kubernetes.pdf#page=116|Kubernetes.pdf p.116]]

### 원자료 내용

```bash
kubectl create namespace delivery
kubectl get ns
kubectl apply -f service/
```

- `delivery` Namespace를 생성하고 확인한다.
- `service/` 디렉터리의 manifest를 적용한다.
- 출력에는 다음 리소스가 생성된다.

```text
service/list-svc created
deployment.apps/list-deploy created
service/order-svc created
deployment.apps/order-deploy created
```

## PDF p.117

- 원문: [[40_자료/강의 자료/Kubernetes.pdf#page=117|Kubernetes.pdf p.117]]

### 원자료 내용

```bash
kubectl get all -n delivery
```

- `list` Pod 2개와 `order` Pod 2개가 `Running` 상태이다.
- Service 출력:
  - `list-svc`: `ClusterIP`, `10.100.96.94`, `80/TCP`
  - `order-svc`: `ClusterIP`, `10.100.32.93`, `80/TCP`
- `list-deploy`, `order-deploy`는 모두 `2/2`이며 각 ReplicaSet도 `2`개를 유지한다.
- 필요한 종류만 볼 때 다음 명령을 사용할 수 있다고 설명한다.

```bash
kubectl get svc,pod -n delivery
```

## PDF p.118

- 원문: [[40_자료/강의 자료/Kubernetes.pdf#page=118|Kubernetes.pdf p.118]]

### 원자료 내용

- Pod IP:
  - `list`: `192.168.20.93`, `192.168.10.58`
  - `order`: `192.168.10.240`, `192.168.20.22`
- Service ClusterIP:
  - `list-svc`: `10.100.96.94`
  - `order-svc`: `10.100.32.93`

```bash
kubectl get pod -o wide -n delivery
kubectl get svc -n delivery
kubectl get endpoints -n delivery
```

- Endpoint:
  - `list-svc`: `192.168.10.58:8000,192.168.20.93:8000`
  - `order-svc`: `192.168.10.240:8000,192.168.20.22:8000`
- Service selector에 등록되지 않은 Pod에는 Service를 통해 접근할 수 없다.
- ClusterIP는 Cluster 내부에서만 접근할 수 있다.

## PDF p.119

- 원문: [[40_자료/강의 자료/Kubernetes.pdf#page=119|Kubernetes.pdf p.119]]

### 원자료 내용

- 같은 `delivery` Namespace에 Debug Pod를 실행한다.

```bash
kubectl run -it --rm debug \
  --image=chlzzz/kube-image:debug \
  --restart=Never -n delivery -- sh
```

```bash
env | grep LIST
env | grep ORDER
```

- 출력 예시:

```text
LIST_SVC_SERVICE_HOST=10.109.112.174
LIST_SVC_SERVICE_PORT=80
ORDER_SVC_SERVICE_HOST=10.110.132.242
ORDER_SVC_SERVICE_PORT=80
```

- 환경변수의 Service IP와 Port로 `curl`을 수행한다.

```bash
curl $LIST_SVC_SERVICE_HOST:$LIST_SVC_SERVICE_PORT
curl $ORDER_SVC_SERVICE_HOST:$ORDER_SVC_SERVICE_PORT
```

- 동일 Namespace의 Service 정보가 환경변수로 자동 등록된다고 설명한다.
- Service가 L4 Load Balancing을 수행하여 여러 Pod로 요청을 분산한다고 설명한다.

## PDF p.120

- 원문: [[40_자료/강의 자료/Kubernetes.pdf#page=120|Kubernetes.pdf p.120]]

### 원자료 내용

```bash
kubectl get service -n kube-system
```

- 출력의 `kube-dns` ClusterIP는 `10.100.0.10`이다.
- 이어지는 설명과 `/etc/resolv.conf` 예시에서는 DNS IP를 `10.96.0.10`으로 적는다.

```text
nameserver 10.96.0.10
search delivery.svc.cluster.local svc.cluster.local cluster.local
options ndots:5
```

- 같은 Namespace에서 다음 이름 형식을 사용할 수 있다고 설명한다.

```bash
curl list-svc.delivery.svc.cluster.local
curl list-svc.delivery:80
curl list-svc:80

curl order-svc.delivery.svc.cluster.local
curl order-svc.delivery:80
curl order-svc:80
```

> [!warning] 원자료 내부 불일치
> 같은 페이지의 실제 출력은 `10.100.0.10`, 설명과 `resolv.conf` 예시는 `10.96.0.10`이다. 어느 값이 해당 실습 Cluster의 실제 DNS IP였는지는 이 PDF만으로 확정하지 않는다.

## PDF p.121

- 원문: [[40_자료/강의 자료/Kubernetes.pdf#page=121|Kubernetes.pdf p.121]]

### 원자료 내용

- `default` Namespace에서 Debug Pod를 실행한다.
- `env | grep LIST`, `env | grep ORDER`는 출력이 없다.
- 다른 Namespace의 Service에는 Namespace를 포함한 DNS 이름으로 접근한다.

```bash
kubectl run -it --rm debug \
  --image=chlzzz/kube-image:debug \
  --restart=Never -- sh
env | grep LIST
env | grep ORDER
curl list-svc.delivery:80
curl order-svc.delivery:80
exit
```

- 테스트 후 `project=delivery` label을 가진 리소스를 삭제하고 남은 리소스가 없음을 확인한다.

```bash
kubectl delete all -l project=delivery -n delivery
kubectl get all -n delivery
```

## PDF p.122

- 원문: [[40_자료/강의 자료/Kubernetes.pdf#page=122|Kubernetes.pdf p.122]]

### 원자료 내용

- `svc-nodeport-list.yml` 예시이다. p.114의 manifest를 바탕으로 Service type을 `NodePort`로 바꾼다.

```yaml
apiVersion: v1
kind: Service
metadata:
  name: list-svc
  labels:
    app: list-app
    project: delivery
  namespace: delivery
spec:
  type: NodePort
  selector:
    app: list-app
  ports:
    - port: 80
      targetPort: 8000
      nodePort: 30001
```

- NodePort의 기본 범위는 `30000-32767`이다.
- `nodePort`를 생략하면 범위 안에서 자동 할당되고, 예시처럼 값을 직접 지정할 수도 있다.
- Deployment 전체 코드는 생략되어 있다.

## PDF p.123

- 원문: [[40_자료/강의 자료/Kubernetes.pdf#page=123|Kubernetes.pdf p.123]]

### 원자료 내용

- `svc-nodeport-order.yml` 예시이다.

```yaml
apiVersion: v1
kind: Service
metadata:
  name: order-svc
  labels:
    app: order-app
    project: delivery
  namespace: delivery
spec:
  type: NodePort
  selector:
    app: order-app
  ports:
    - port: 80
      targetPort: 8000
```

- 이 예시에는 `nodePort`를 명시하지 않아 자동 할당된다.
- Deployment는 `replicas: 2`, image `chlzzz/kube-image:order`, `containerPort: 8000`을 사용하며 전체 코드는 생략되어 있다.

## PDF p.124

- 원문: [[40_자료/강의 자료/Kubernetes.pdf#page=124|Kubernetes.pdf p.124]]

### 원자료 내용

```bash
kubectl apply -f service/svc-nodeport-list.yml
kubectl apply -f service/svc-nodeport-order.yml
kubectl get all -n delivery
```

- Service 출력:
  - `list-svc`: ClusterIP `10.100.62.50`, `80:30140/TCP`
  - `order-svc`: ClusterIP `10.100.80.181`, `80:32455/TCP`
- `list`와 `order` Pod는 각각 2개이며 Deployment와 ReplicaSet도 모두 목표 개수를 유지한다.

## PDF p.125

- 원문: [[40_자료/강의 자료/Kubernetes.pdf#page=125|Kubernetes.pdf p.125]]

### 원자료 내용

- Pod IP:
  - `list`: `192.168.20.169`, `192.168.10.58`
  - `order`: `192.168.10.132`, `192.168.20.181`
- Endpoint:
  - `list-svc`: `192.168.10.58:8000,192.168.20.169:8000`
  - `order-svc`: `192.168.10.132:8000,192.168.20.181:8000`
- NodePort:
  - `list-svc`: `30140`
  - `order-svc`: `32455`

```bash
kubectl get pod -n delivery -o wide
kubectl get endpoints -n delivery
kubectl get svc -n delivery
```

- Service의 NodePort가 모든 Worker Node에 열리고, Endpoint의 Pod port `8000`으로 전달되는 관계를 보여 준다.

## PDF p.126

- 원문: [[40_자료/강의 자료/Kubernetes.pdf#page=126|Kubernetes.pdf p.126]]

### 원자료 내용

- BastionHost의 Security Group에서 Worker Node 대상 다음 Inbound 규칙을 추가한다.
  - TCP `30000-32767`
  - ICMP
- 다음 Worker Node 주소와 NodePort 조합으로 외부 접근을 테스트한다.

```bash
curl 192.168.10.147:30140
curl 192.168.20.156:30140
curl 192.168.10.147:32455
curl 192.168.20.156:32455
```

- 테스트가 끝나면 Security Group 규칙을 제거한다.
- `project=delivery` label 리소스를 삭제하고 결과를 확인한다.

```bash
kubectl delete all -l project=delivery -n delivery
kubectl get all -n delivery
```

> [!note] 원자료 출력명
> 삭제 출력에는 `deployment.apps/deploy-svc`와 `deployment.apps/order-deploy`가 적혀 있다. 앞 페이지의 list Deployment 이름과 일치하지 않지만 원자료 표기를 보존한다.

## PDF p.127

- 원문: [[40_자료/강의 자료/Kubernetes.pdf#page=127|Kubernetes.pdf p.127]]

### 원자료 내용

- ExternalName 사용 시나리오를 설명한다.
  - 외부 Resource 예시: RDS, Route53
  - `delivery` Namespace의 Service를 다른 Namespace에서 외부 서비스처럼 참조하는 실습
- `delivery` Namespace에 ClusterIP Service와 Deployment를 다시 적용한다.

```bash
kubectl apply -f service/svc-clusterip-list.yml
kubectl apply -f service/svc-clusterip-order.yml
```

- 출력 예시:
  - `list-svc`: ClusterIP `10.100.241.80`
  - `order-svc`: ClusterIP `10.100.195.147`
  - `list-svc` Endpoint: `192.168.10.22:8000,192.168.20.89:8000`
  - `order-svc` Endpoint: `192.168.10.58:8000,192.168.20.179:8000`

## PDF p.128

- 원문: [[40_자료/강의 자료/Kubernetes.pdf#page=128|Kubernetes.pdf p.128]]

### 원자료 내용

- `svc-externalname.yml`에 두 ExternalName Service를 `---`로 구분해 정의한다.

```yaml
apiVersion: v1
kind: Service
metadata:
  name: externalname-list-svc
spec:
  type: ExternalName
  externalName: list-svc.delivery.svc.cluster.local
---
apiVersion: v1
kind: Service
metadata:
  name: externalname-order-svc
spec:
  type: ExternalName
  externalName: order-svc.delivery.svc.cluster.local
```

## PDF p.129

- 원문: [[40_자료/강의 자료/Kubernetes.pdf#page=129|Kubernetes.pdf p.129]]

### 원자료 내용

```bash
kubectl apply -f service/svc-externalname.yml
kubectl get svc -n default
```

- 두 Service의 type은 `ExternalName`이고 ClusterIP는 없다.
- `EXTERNAL-IP`에는 다음 대상 Domain이 표시된다.
  - `list-svc.delivery.svc.cluster.local`
  - `order-svc.delivery.svc.cluster.local`
- Debug Pod에서 다음 이름으로 접근한다.

```bash
curl externalname-list-svc
curl externalname-order-svc
```

### 도식 의미

- `default` Namespace의 Debug Pod가 ExternalName Service를 통해 `delivery` Namespace의 Service와 Pod로 연결된다.
- 원자료 도식에는 `deilvery`, `Namespcae` 오탈자가 있으나 의미는 위와 같다.

## PDF p.130

- 원문: [[40_자료/강의 자료/Kubernetes.pdf#page=130|Kubernetes.pdf p.130]]

### 원자료 내용

- `delivery` Namespace의 `project=delivery` 리소스를 삭제한다.
- `default` Namespace의 두 ExternalName Service도 삭제한다.
- 양쪽 Namespace에서 남은 리소스가 없음을 확인한다.

```bash
kubectl delete all -l project=delivery -n delivery
kubectl get all -n delivery
kubectl delete svc externalname-list-svc
kubectl delete svc externalname-order-svc
kubectl get all
```

## PDF p.131

- 원문: [[40_자료/강의 자료/Kubernetes.pdf#page=131|Kubernetes.pdf p.131]]

### 원자료 내용

- `svc-loadbalancer.yml` 예시이다.

```yaml
apiVersion: v1
kind: Service
metadata:
  name: list-svc
  labels:
    app: list-app
    project: delivery
  namespace: delivery
spec:
  type: LoadBalancer
  selector:
    app: list-app
  ports:
    - port: 80
      targetPort: 8000
```

- Deployment는 다음 속성을 갖는다.
  - `replicas: 3`
  - selector와 Pod label: `app: list-app`
  - image: `chlzzz/kube-image:list`
  - `containerPort: 8000`
- 원자료는 NodePort 예제 manifest를 바탕으로 작성하고 Deployment 전체 코드는 TXT를 참고하라고 안내한다.

## PDF p.132

- 원문: [[40_자료/강의 자료/Kubernetes.pdf#page=132|Kubernetes.pdf p.132]]

### 원자료 내용

```bash
kubectl apply -f service/svc-loadbalancer.yml
kubectl get pod -n delivery -o wide
kubectl get svc -n delivery
```

- Pod 3개의 IP 예시는 `192.168.10.187`, `192.168.10.58`, `192.168.20.205`이다.
- `list-svc`:
  - type: `LoadBalancer`
  - ClusterIP: `10.100.217.107`
  - External IP/DNS: `ap-northeast-2.elb.amazonaws.com`
  - port: `80:31186/TCP`
- Web Browser로 LoadBalancer에 반복 접근하면 응답하는 Pod IP가 바뀌는 것을 확인한다.
- Login, Cookie, 장바구니처럼 세션을 유지해야 하는 서비스에서 요청 대상 Pod가 바뀌면 세션이 끊길 수 있다고 설명하며 `Session Affinity`를 소개한다.

> [!note] 원자료 표시 범위
> 원자료의 LoadBalancer DNS는 화면에서 위와 같이 축약해 표시되어 있다. 전체 실제 DNS 이름을 추정해 보충하지 않는다.

## PDF p.133

- 원문: [[40_자료/강의 자료/Kubernetes.pdf#page=133|Kubernetes.pdf p.133]]

### 원자료 내용

- Session Affinity 방식:
  - Service: L3의 Client IP 기반
  - Ingress: L7의 Cookie 기반
- Service를 편집해 ClientIP Session Affinity를 설정한다.

```bash
kubectl edit svc list-svc -n delivery
```

```yaml
selector:
  app: list-app
sessionAffinity: ClientIP
sessionAffinityConfig:
  clientIP:
    timeoutSeconds: 10800
```

- `timeoutSeconds: 10800` 동안 같은 Client IP의 요청을 같은 Pod로 전달한다고 설명한다.

> [!warning] 원자료 출력 불일치
> 편집 대상은 `service/list-svc`인데 저장 출력은 `configmap/kube-proxy edited`로 적혀 있다. 원자료의 실제 명령과 출력이 서로 일치하지 않는다.

## PDF p.134

- 원문: [[40_자료/강의 자료/Kubernetes.pdf#page=134|Kubernetes.pdf p.134]]

### 원자료 내용

- Browser 화면의 `POD CONTAINER INFORMATION` 예시:
  - `POD IP Address`: `192.168.10.58`
  - `POD HostName`: `list-deploy-549c9bbb7-sdrcm`
  - `POD SVC Information`: `10.100.217.107:80`
- Session Affinity 적용 후 반복 접근해도 Pod 정보가 바뀌지 않는 것을 확인한다.
- Client IP와 Pod 연결은 설정된 timeout까지 유지된다고 설명한다.
- 실습 리소스를 삭제하고 남은 리소스가 없음을 확인한다.

```bash
kubectl delete -f service/svc-loadbalancer.yml
kubectl get all -n delivery
```

## 원자료 외 보충

- 없음. 이 문서는 PDF의 원자료 내용과 내부 불일치만 기록한다.

## 누락·검토 대기

- 원자료가 참조한 TXT manifest 파일은 이 변환 범위에 제공되지 않아, PDF에 표시된 부분만 옮겼다.
- p.120의 DNS IP와 p.126·p.133의 출력명 불일치는 원자료만으로 해소할 수 없다.
