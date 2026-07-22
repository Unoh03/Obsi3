---
type: lab
status: active
created: 2026-07-21
lab_date: 2026-07-21
topic: kubernetes
parent_moc: "[[10_학습 노트/클라우드/Kubernetes/00_Kubernetes MOC]]"
source: "[[10_학습 노트/클라우드/Kubernetes/Source Digest/Kubernetes - Source Digest 04 Pod and ReplicaSet]]"
environment: "Amazon EKS ap-northeast-2; Kubernetes v1.35.6-eks-8f14419; Bastion Amazon Linux t3.micro"
evidence: "사용자 제공 Terminal 출력과 Local AWS read-only 진단"
verified_on: 2026-07-22
---

# EKS 첫 접속과 Pod 기초 실습

> [!summary]
> Terraform으로 EKS와 Bastion을 구성하고, Cluster 연결을 확인한 뒤 첫 Pod·Sidecar·Label Selector 실습을 수행했다. 이 과정에서 IAM Credential 재생성, AWS CLI Profile 혼동, 빈 YAML, Resource 이름 오타, Pod 불변 필드, Jib 실행 위치, VS Code Remote-SSH 고착을 겪었다.

> [!warning] Secret 기록 경계
> 실제 AWS Access Key·Secret Access Key, Docker Hub 비밀번호·Access Token, Public IP는 기록하지 않는다. 이 노트의 명령에는 Placeholder만 사용한다.

## 목표

- EKS Cluster와 Worker Node가 정상인지 확인한다.
- YAML Manifest로 Pod를 생성하고 Server-side dry run과 실제 Apply의 차이를 확인한다.
- Pod의 Image·Container·Port 관계를 확인한다.
- 실패와 오타도 다음 실습에서 재사용할 수 있도록 원인과 조치를 남긴다.

## 환경과 확인된 상태

| 항목 | 값 | 근거 |
|---|---|---|
| AWS Region | `ap-northeast-2` | Terraform·EKS Context |
| EKS Cluster | `my-eks` | Bastion cloud-init의 kubeconfig 생성 출력 |
| Kubernetes | `v1.35.6-eks-8f14419` | `kubectl get nodes` |
| Worker Node | 2대, 모두 `Ready` | `kubectl get nodes` |
| Bastion | Amazon Linux, `t3.micro` | EC2 read-only 조회 |
| IAM 사용자 | `terra-user` | Local `aws sts get-caller-identity --profile terra-user` |
| Spring Project | `D:\sts-5.1.1.RELEASE\workspace\boot` | Local Workspace 확인 |
| Spring Boot | 3.4.5, Java 17 | `boot/pom.xml` |
| Jib | Maven Plugin 3.5.2 | `boot/pom.xml` |
| Application Port | 80 | `application.properties`의 `server.port=80` |

## 1. EKS 환경을 다시 만든 이유

이전 `00_eks` Destroy 도중 IAM 사용자를 먼저 삭제해 Credential 흐름이 꼬였다. 기존 환경은 별도 점검에서 Terraform State 0과 관련 유료 Resource 잔존 0을 확인했다.

복습을 겸해 IAM 사용자를 다시 만들고 Terraform Apply를 처음부터 수행했다.

- 실제 IAM 사용자명은 소문자 `terra-user`다.
- Terraform 변수에는 새 사용자의 Access Key ID와 그 Key에 대응하는 Secret Access Key를 넣었다.
- Secret 값은 이 노트에 기록하지 않는다.
- Region은 가용영역 문자열이 아니라 `ap-northeast-2`를 사용했다.

Terraform Apply는 최종 성공했고 Bastion에 SSH로 접속했다.

## 2. Cluster 연결 확인

### 확인된 성공

```console
$ kubectl get nodes
NAME                                               STATUS   ROLES    AGE   VERSION
ip-172-28-11-136.ap-northeast-2.compute.internal   Ready    <none>   10m   v1.35.6-eks-8f14419
ip-172-28-31-185.ap-northeast-2.compute.internal   Ready    <none>   10m   v1.35.6-eks-8f14419
```

두 Worker Node가 `Ready`이므로 다음 경로는 작동했다.

```text
Bastion의 kubeconfig
→ EKS API Server 인증
→ Kubernetes API 조회
→ Worker Node 두 대 확인
```

### AWS CLI Profile 혼동

```console
$ aws sts get-caller-identity
Unable to locate credentials.
```

Browser Login을 시도하는 `aws login`은 Bastion SSH 환경에 맞지 않아 중단했다.

```console
$ aws configure list --profile terra-user
The config profile (terra-user) could not be found
```

IAM 사용자명과 Bastion의 AWS CLI Profile 이름은 반드시 같지 않다. 이전 User data에서는 별도 Profile 이름을 사용할 수 있으므로 다음 순서로 확인해야 한다.

```bash
aws configure list-profiles
aws sts get-caller-identity --profile <실제-profile-name>
```

이 단계에서 Bastion의 실제 Profile 이름과 STS 결과는 별도로 확인하지 못했다. 단, `kubectl get nodes`는 성공했으므로 kubeconfig가 사용하는 EKS 인증 경로는 동작했다.

## 3. 첫 `pod-basic.yml` 시행착오

### 파일이 없었음

```console
$ kubectl apply -f pod-basic.yml
error: the path "pod-basic.yml" does not exist
```

### 빈 파일을 Apply함

파일을 만들었지만 Object 내용을 넣지 않아 다음 오류가 났다.

```console
$ kubectl apply -f pod-basic.yml
error: no objects passed to apply
```

`kubectl`로 최소 Manifest를 자동 생성할 수 있다.

```bash
kubectl run my-pod \
  --image=nginx:latest \
  --port=80 \
  --dry-run=client \
  -o yaml > pod-basic.yml
```

### Resource 이름 오타

```console
$ kubectl get podes
error: the server doesn't have a resource type "podes"
```

올바른 Resource 이름은 `pods` 또는 단수형 `pod`다.

```bash
kubectl get pods
kubectl get pod
```

## 4. Spring Boot Image 준비와 Jib

Spring Tool Suite의 `boot` Project에서 Jib Maven Plugin으로 Docker Hub Image를 만들고 Push하는 흐름을 사용했다.

```text
compile jib:build
-Dimage=docker.io/<Docker-ID>/boot:latest
-Djib.to.auth.username=<Docker-ID>
-Djib.to.auth.password=<Docker-Hub-Access-Token>
```

의미는 다음과 같다.

```text
Spring Boot Source
→ Maven Compile
→ Jib가 Container Image 구성
→ Docker Hub에 boot:latest Push
→ EKS Worker가 Image Pull
```

Docker Hub Image가 AWS 과금 Resource라고 오인해 한 번 삭제했다. Public Repository의 학습용 Image 자체는 AWS Resource가 아니며, 이후 Pod에서 사용하려면 다시 Push해야 한다.

### Maven Build 실패

```text
BUILD FAILURE
No plugin found for prefix 'jib' in the current project
```

실제 `boot/pom.xml`에는 다음 Plugin이 존재했다.

```text
com.google.cloud.tools:jib-maven-plugin:3.5.2
```

따라서 Source나 Plugin 누락보다 STS Maven Run Configuration이 다른 Project의 `pom.xml`을 본 것이 가장 유력했다.

```text
Base directory: ${workspace_loc:/boot}
Goals: compile jib:build ...
```

Jib Push가 이후 최종 성공했는지는 아직 출력으로 재확인하지 않았다.

## 5. Pod Image와 Manifest 보정

처음 작성한 Image 경로는 다음과 같았다.

```yaml
image: unoh03/latest
```

Docker Hub Image의 기본 형식은 `사용자/Repository:Tag`이므로 `boot` Repository를 사용한다면 다음 형식이어야 한다.

```yaml
image: unoh03/boot:latest
```

Spring Application은 `server.port=80`이므로 다음 Port 선언은 Project 설정과 일치한다.

```yaml
ports:
  - containerPort: 80
```

`containerPort`는 Container가 사용하는 Port를 문서화하는 필드이며, 이것만으로 외부 접속 경로가 생기지는 않는다.

### 이 실습에서 내가 판단해야 할 것

명령어와 YAML 형식은 필요할 때 도구의 도움을 받아도 된다. 대신 프로젝트에서는 다음 흐름과 판단 기준을 알고 있어야 한다.

```text
이미 만들어진 범용 프로그램
→ Docker Hub에서 신뢰할 수 있는 Image를 찾음
→ 정확한 Repository와 Version을 고름
→ Pod·Deployment에서 사용

우리 애플리케이션
→ Source를 Container Image로 Build
→ Docker Hub·ECR 같은 Registry에 Push
→ Pod·Deployment에서 해당 Image를 사용
```

Image를 선택할 때 확인할 것은 다음과 같다.

- `Docker Official Image`나 `Verified Publisher`처럼 출처를 신뢰할 수 있는가?
- 대상 Node의 CPU Architecture와 호환되는가?
- 학습 편의를 제외하면 `latest` 대신 명시적인 Version Tag 또는 Digest를 고정했는가?
- Public Image인가, 인증이 필요한 Private Image인가?
- 비밀번호·Access Token 같은 Secret을 Image나 Manifest에 넣지 않았는가?
- 실행 후 `get`, `describe`, `logs`로 실제 상태를 검증했는가?
- 외부 접속이 필요하다면 Pod의 `containerPort` 외에 Service·Ingress 등의 경로를 설계했는가?

#### 정보 출처 분류

1. **Local primary evidence**: 이번 실습에서 `ubuntu:26.04`를 Manifest에 지정했고, 자체 Spring Boot 애플리케이션은 Jib로 `boot` Image를 만들어 Docker Hub에 Push하는 흐름을 사용했다.
2. **Authoritative external evidence**: Docker 공식 문서는 기존 Image를 찾아 실행하고 이를 기반으로 자체 Image를 만들어 공유하는 흐름을 안내한다. Kubernetes 공식 문서는 애플리케이션 Image를 Registry에 Push한 뒤 Pod에서 참조하는 방식을 기본 사용 모델로 설명한다.
3. **Informal external evidence**: 이번 판단에는 Community 게시물이나 Blog를 근거로 사용하지 않았다.
4. **Parametric knowledge·추론**: 강사의 요점이 “프로젝트에서 기존 Image를 재사용하고 자체 Image를 배포하는 법을 익힌다”는 것이라는 해석은 수업 흐름과 공식 사용 모델에 근거한 추론이며, 강사의 직접 발언으로 확인한 사실은 아니다.

## 6. 기존 Pod의 불변 필드와 재생성

기존 `my-pod`에는 `my-pod`라는 Container와 `nginx:latest` Image가 있었다. 새 Manifest는 Container 이름을 `unoh-pod`로 바꾸었다.

```console
$ kubectl apply --dry-run=server -f pod-basic.yml
The Pod "my-pod" is invalid: spec: Forbidden: pod updates may not change fields ...
-   "Name": "my-pod",
+   "Name": "unoh-pod",
```

Pod의 Container 이름은 생성 후 변경할 수 없는 필드다. 실습 Pod를 삭제한 뒤 새 Manifest를 적용했다.

```bash
kubectl delete pod my-pod
kubectl wait --for=delete pod/my-pod --timeout=60s
kubectl apply --dry-run=server -f pod-basic.yml
kubectl apply -f pod-basic.yml
```

### Server-side dry run과 실제 Apply

```console
$ kubectl apply --dry-run=server -f pod-basic.yml
pod/my-pod created (server dry run)

$ kubectl apply -f pod-basic.yml
pod/my-pod created
```

- `--dry-run=server`: API Server의 검증·기본값·권한·Admission 처리는 거치지만 Object를 저장하지 않는다.
- 실제 `apply`: Object를 저장하고 Scheduler와 kubelet이 실제 Pod 생성을 진행한다.

`created` 출력은 API Object 접수 성공이다. Image Pull과 Application 실행 성공은 다음 명령으로 별도 확인해야 한다.

```bash
kubectl get pod my-pod -o wide
kubectl describe pod my-pod
kubectl logs my-pod
```

현재 대화에는 `my-pod`의 최종 `Running`과 Spring HTTP 응답 결과가 남아 있지 않다.

## 7. 로컬 브라우저 접속 후보

Pod가 `Running`일 때 Bastion의 `kubectl port-forward`와 Local SSH Tunnel을 함께 사용하면 Internet에 Port를 공개하지 않고 접속할 수 있다.

```powershell
ssh -L 8080:127.0.0.1:8080 bas "kubectl port-forward pod/my-pod 8080:80"
```

```text
http://localhost:8080
```

이 경로는 안내만 했으며 실제 HTTP 응답은 아직 검증하지 않았다.

## 8. VS Code Remote-SSH 고착

Bastion에 Kubernetes Extension을 설치한 직후 VS Code에서 다음 증상이 발생했다.

```text
Failed to set up dynamic port forwarding connection over SSH
VS Code 서버를 초기화하는 중
```

Local PowerShell의 일반 SSH도 응답하지 않았다. Read-only 진단 결과는 다음과 같았다.

- Public IP의 TCP 22 연결 성공
- EC2 Instance 상태 `running`
- EC2 System Status와 Instance Status 모두 `ok`
- SSH는 TCP 연결 후 `Connection timed out during banner exchange`
- Bastion Instance Type은 `t3.micro`

Network나 Security Group 차단보다는 작은 Bastion에서 VS Code Server와 Extension이 실행되며 Resource가 부족해졌을 가능성이 높다고 추정했다. Memory 사용량은 CloudWatch Agent가 없어 직접 확인하지 못했다.

관련 복구 절차는 [[10_학습 노트/클라우드/AWS/서버_시퓨_100%_찍을_때|EC2 서버가 멈추거나 CPU 100% 찍을 때]]에 있다.

후속 재접속은 성공했으나 실제로 Reboot·Swap 추가·VS Code Server 삭제 중 어떤 조치가 적용됐는지는 기록하지 못했다.

## 9. 현재 진도: Ubuntu Pod

강사가 제시한 현재 Manifest는 다음과 같다.

```yaml
apiVersion: v1
kind: Pod
metadata:
  labels:
    app.kubernetes.io/name: ubuntu
  name: ubuntu-pod
spec:
  containers:
    - image: ubuntu:26.04
      name: ubuntu-container
      ports:
        - containerPort: 80
      resources: {}
  dnsPolicy: ClusterFirst
  restartPolicy: Always
status: {}
```

- `ubuntu:26.04`는 Docker Hub의 Canonical 관리 Official Image Tag로 현재 존재한다.
- `status`는 Kubernetes가 관리하는 영역이므로 작성용 Manifest에서는 제거할 수 있다.
- `resources: {}`는 빈 설정이므로 제거할 수 있다.
- Ubuntu Base Image에 장시간 실행되는 Main Process가 없으면 Container가 종료되고 `restartPolicy: Always`에 따라 재시작할 수 있다.
- 이 Manifest의 실제 Apply·Pod 상태·`kubectl exec` 결과는 아직 확인하지 않았다. 강의 결과를 보기 전에 임의로 `command`를 추가하지 않는다.

실행 뒤 확인할 명령은 다음과 같다.

```bash
kubectl apply --dry-run=server -f ubuntu-pod.yml
kubectl apply -f ubuntu-pod.yml
kubectl get pod ubuntu-pod -w
kubectl describe pod ubuntu-pod
kubectl logs ubuntu-pod
```

Pod가 `Running`을 유지한다면 Container 내부 진입은 다음과 같다.

```bash
kubectl exec -it ubuntu-pod -c ubuntu-container -- sh
```

## 10. p.19 Container 환경변수와 Downward API

PDF p.19의 `pod-env.yml`은 Container에 직접 값을 넣는 일반 환경변수와, Kubernetes가 생성한 Pod 정보를 환경변수로 주입하는 `fieldRef`를 함께 연습한다.

원자료와 현재 작성본의 차이는 다음과 같다.

| 항목 | PDF p.19 | 현재 작성본 |
|---|---|---|
| Pod·Label | `env-pod`, `app: env-pod` | `pod`, `app: boot` |
| Image | `ubuntu:bionic` | `unoh03/boot:latest` |
| 직접 입력 환경변수 | `MyName=kube`, `HelloMessage=Hello $(MyName)` | `ENV1=ENV1` |
| Resource | 지정 없음 | VS Code 경고를 보고 학습용 예시값 추가 |
| Pod 정보 환경변수 | Node·Namespace·Node IP·Pod IP | 동일 구조 사용 |

현재 작성한 Manifest를 주석과 올바른 들여쓰기로 정리하면 다음과 같다. 아직 실제 Apply 결과는 확인하지 않았다.

```yaml
apiVersion: v1 # Core API의 v1 규칙 사용
kind: Pod # 생성할 Kubernetes Object 종류
metadata: # Object의 이름·Label 같은 식별 정보
  labels:
    app: boot # Pod Label. 나중에 Selector로 같은 역할의 Pod를 찾을 수 있음
  name: pod # Pod 이름
spec: # Pod의 원하는 실행 상태
  containers: # 이 Pod에서 함께 실행할 Container 목록
    - image: unoh03/boot:latest # Docker Hub의 unoh03/boot Repository에서 latest Tag 사용
      name: unoh-pod # Container 이름. Pod 이름이나 환경변수 이름과는 별개
      ports:
        - containerPort: 80 # Container가 사용하는 Port를 문서화하며 외부 공개 기능은 아님
      resources: # PDF에는 없고 VS Code의 Resource 경고를 해소하려고 추가한 학습용 예시
        requests: # Scheduler가 배치 판단에 사용하는 요구량
          cpu: "100m" # CPU Core의 0.1개에 해당
          memory: "128Mi"
        limits: # Container가 사용할 수 있는 상한
          cpu: "500m"
          memory: "512Mi" # 초과하면 OOMKilled가 발생할 수 있음
      env: # Container Process에 전달할 환경변수 목록
        - name: ENV1 # 환경변수 이름이며 Container 이름이 아님
          value: "ENV1" # 사용자가 직접 지정한 고정값
        - name: NodeName
          valueFrom: # 고정 문자열 대신 다른 정보에서 값을 가져옴
            fieldRef: # Downward API로 현재 Pod의 Field 참조
              fieldPath: spec.nodeName # Pod가 배치된 Node 이름
        - name: NameSpace
          valueFrom:
            fieldRef:
              fieldPath: metadata.namespace # Pod가 속한 Namespace
        - name: NodeIP
          valueFrom:
            fieldRef:
              fieldPath: status.hostIP # Pod를 실행하는 Node의 IP
        - name: PodIP
          valueFrom:
            fieldRef:
              fieldPath: status.podIP # Kubernetes가 Pod에 할당한 IP
      command: ['sh', '-c', 'echo The app is running! && sleep 3600'] # Image 기본 시작 명령을 덮어쓰고 PID 1을 한 시간 유지
  dnsPolicy: ClusterFirst # Cluster DNS를 우선 사용
  restartPolicy: Always # Main Process 종료 시 kubelet이 Container 재시작
status: {} # Kubernetes가 실제 상태를 기록하는 영역으로 작성용 Manifest에서는 제거 가능
```

`fieldRef`로 Pod 정보를 Container에 전달하는 방법은 Kubernetes Downward API의 한 형태다. 애플리케이션이 Kubernetes API를 직접 호출하지 않아도 자신이 실행 중인 Node·Namespace·IP를 환경변수로 읽을 수 있다.

현재 `command`는 `unoh03/boot:latest`의 원래 시작 명령을 덮어쓰므로 Spring Boot 애플리케이션은 실행되지 않고 `echo`와 `sleep`만 실행된다. 이번 목적이 환경변수 확인이라면 사용할 수 있지만, Spring Boot 실행이 목적이라면 `command`를 제거해야 한다.

Apply 후 확인할 명령은 다음과 같다.

```bash
kubectl apply --dry-run=server -f pod-basic.yml
kubectl apply -f pod-basic.yml
kubectl get pod pod -o wide
kubectl exec pod -- env | grep -E 'ENV1|NodeName|NameSpace|NodeIP|PodIP'
```

## 11. p.21-p.23 Sidecar와 Pod Network 실습

### Manifest 구성

`pod-sidecar-net.yml`에는 하나의 Pod 안에 Nginx와 BusyBox Container를 함께 정의했다.

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
      command: ["sh", "-c", "echo The app is running! && sleep 3600"]
```

`pod-net.yml`에는 Pod 간 통신을 비교할 Nginx Container 하나를 정의했다.

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

### 명령 오타와 배포

처음에는 `--dry-run`을 `--dryrun`으로 잘못 입력했다.

```console
$ kubectl apply --dryrun -f pod-sidecar-net.yml
error: unknown flag: --dryrun
```

이번에는 도움말에서 올바른 Flag를 확인했지만, Server-side dry run을 다시 실행하지 않고 실제 Apply로 진행했다.

```console
$ kubectl apply -f pod-sidecar-net.yml
pod/pod-sidecar created

$ kubectl apply -f pod-net.yml
pod/pod-net created
```

두 Pod는 생성 직후 잠시 `ContainerCreating`이었고, 이후 다음 상태가 됐다.

```console
$ kubectl get pods -o wide
NAME          READY   STATUS    RESTARTS   IP              NODE
pod-net       1/1     Running   0          172.28.31.170   ip-172-28-31-206.ap-northeast-2.compute.internal
pod-sidecar   2/2     Running   0          172.28.11.84    ip-172-28-11-97.ap-northeast-2.compute.internal
```

- `pod-sidecar`의 `2/2`는 같은 Pod 안의 Nginx와 BusyBox가 모두 Ready라는 뜻이다.
- 두 Container는 별도 Container IP가 아니라 `pod-sidecar`의 Pod IP `172.28.11.84`를 공유한다.
- `pod-net`은 다른 Node에 배치됐고 별도의 Pod IP `172.28.31.170`을 받았다.

조회 명령에서도 숫자 `0`을 영문 소문자 `o` 대신 입력하는 오타가 있었다.

```console
$ kubectl get pods -0 wide
error: unknown shorthand flag: '0' in -0
```

올바른 Output Flag는 `-o wide`다.

### Pod IP와 같은 Pod 내부 통신 확인

Bastion에서 두 Pod IP에 직접 요청했고 양쪽 모두 Nginx Welcome Page를 반환했다.

```console
$ curl 172.28.11.84
<h1>Welcome to nginx!</h1>

$ curl 172.28.31.170
<h1>Welcome to nginx!</h1>
```

이어 `pod-sidecar`의 BusyBox Container에 들어가 `localhost:80`으로 같은 Pod의 Nginx에 접근했다.

```console
$ kubectl exec -it pod-sidecar -c busybox-sidecar-app -- sh
/ # wget -Sq localhost:80
HTTP/1.1 200 OK
Server: nginx/1.31.3
```

이 결과로 이번 환경에서 확인된 것은 다음과 같다.

```text
하나의 Pod
├─ nginx-sidecar-app : 80번 Port에서 HTTP 응답
└─ busybox-sidecar-app : localhost:80으로 Nginx 접근
```

즉 같은 Pod의 Container는 Network Namespace와 Pod IP를 공유하므로 `localhost`로 서로 통신할 수 있다. 서로 다른 Pod에는 각각 별도의 Pod IP가 있으며, Bastion에서는 두 Pod IP에 직접 접근할 수 있었다. 다만 Pod IP는 재생성 시 바뀔 수 있으므로 고정된 서비스 진입점으로 사용하지 않는다.

### 아직 확인하지 않은 p.23 단계

- BusyBox Container에서 다른 Pod인 `pod-net`의 IP로 직접 요청
- `kubectl logs pod-net nginx-app`에서 요청 Source 확인

## 12. p.24-p.30 Label과 Selector 실습

### Label이 다른 Pod 생성

`labels/` Directory에는 다음 네 Manifest가 있었다.

| Pod | 직접 정의한 Label | 실제 Image |
|---|---|---|
| `label-app-1` | `group=web`, `app=app-1`, `version=v1`, `env=prod` | `httpd:latest` |
| `label-app-2` | `group=web`, `app=app-2`, `version=v1`, `env=stage` | `httpd:latest` |
| `label-app-3` | `group=web`, `app=app-3`, `version=v1`, `env=test` | `httpd:latest` |
| `label-app-4` | 없음 | `httpd:latest` |

PDF p.24-p.25의 Image는 `nginx:latest`지만, 이번에 실제 사용한 배포 자료는 `httpd:latest`였다. Label과 Selector의 동작을 확인하는 목적에는 영향을 주지 않는다.

현재 위치가 이미 `labels/`였기 때문에 하위 `label` 경로는 존재하지 않았다.

```console
$ kubectl apply -f label
error: the path "label" does not exist

$ kubectl apply -f .
pod/label-app-1 created
pod/label-app-2 created
pod/label-app-3 created
pod/label-app-4 created
```

`--show-labels`와 `-L`로 Label 전체와 선택한 Label Column을 확인했다.

```console
$ kubectl get pod -L app,group,env
NAME          APP     GROUP   ENV
label-app-1   app-1   web     prod
label-app-2   app-2   web     stage
label-app-3   app-3   web     test
label-app-4
```

이번 EKS 출력에는 Manifest에 직접 쓰지 않은 `topology.kubernetes.io/region`과 `topology.kubernetes.io/zone` Label도 Pod에 추가돼 있었다. 추가 주체와 목적은 이번 실습에서 조사하지 않았다.

### Label 추가·덮어쓰기·삭제

처음 Label이 없던 `label-app-4`를 대상으로 동일한 Key의 생명주기를 확인했다.

```console
$ kubectl label pod label-app-4 app=app-4
pod/label-app-4 labeled

$ kubectl label pod label-app-4 app=app-test --overwrite
pod/label-app-4 labeled

$ kubectl label pod label-app-4 app-
pod/label-app-4 unlabeled
```

- `app=app-4`: Label 추가
- `--overwrite`: 기존 `app` 값 변경
- `app-`: `app` Key 삭제

### Selector 결과

```console
$ kubectl get pod -l env=prod
label-app-1

$ kubectl get pod -l 'group=web,version=v1'
label-app-1
label-app-2
label-app-3

$ kubectl get pod -l 'env in (test,stage)'
label-app-2
label-app-3

$ kubectl get pod -l 'env notin (test,stage)'
label-app-1
label-app-4
pod-net
pod-sidecar
```

`env!=prod`도 `label-app-2`, `label-app-3`뿐 아니라 `env` Key가 없는 `label-app-4`, `pod-net`, `pod-sidecar`를 선택했다. `!env`는 `env` Key 자체가 없는 네 Pod만 선택했다.

이 실습에서 확인한 Selector 의미는 다음과 같다.

| Selector | 의미 |
|---|---|
| `env=prod` | `env` 값이 정확히 `prod` |
| `group=web,version=v1` | 두 조건을 모두 만족하는 AND |
| `env in (test,stage)` | 지정한 값 집합 중 하나와 일치 |
| `env notin (test,stage)` | 지정한 값이 아니거나 `env` Key가 없음 |
| `!env` | `env` Key 자체가 없음 |

### 현재 정리 상태

Label 실습이 끝난 뒤 먼저 네 Label Pod를 이름으로 지정해 삭제했다.

```console
kubectl delete pod label-app-1 label-app-2 label-app-3 label-app-4
pod "label-app-1" deleted from default namespace
pod "label-app-2" deleted from default namespace
pod "label-app-3" deleted from default namespace
pod "label-app-4" deleted from default namespace
```

이후 사용자 승인에 따라 `pod-net`과 `pod-sidecar`도 삭제했다. `pod-sidecar`는 잠시 `Terminating` 상태였지만 강제 삭제하지 않고 정상 종료를 기다렸다.

```console
$ kubectl delete pod pod-net pod-sidecar
pod "pod-net" deleted from default namespace
pod "pod-sidecar" deleted from default namespace

$ kubectl get pods
No resources found in default namespace.
```

## 13. EX.5 NodeSelector 실습

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

## 14. EX.6 NodeAffinity 실습

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

## 15. EX.7 Taints와 Tolerations 실습

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

## 오류와 해석 요약

| 증상 | 확인한 원인 또는 현재 판단 | 조치·다음 확인 |
|---|---|---|
| `path ... does not exist` | YAML 파일 없음 | 파일 생성 또는 `kubectl --dry-run=client -o yaml` 사용 |
| `no objects passed to apply` | 파일이 비었거나 유효 Object 없음 | `cat -n`으로 내용 확인 |
| `resource type "podes"` | `pods` 오타 | `kubectl get pods` |
| `Unable to locate credentials` | Bastion 기본 AWS CLI Profile 없음 | `aws configure list-profiles` 후 명시적 Profile 사용 |
| `aws login`이 Browser 대기 | Remote SSH 환경에 부적합 | 취소하고 기존 Credential Profile 확인 |
| `No plugin found for prefix 'jib'` | 잘못된 Maven Base directory 가능성이 높음 | `${workspace_loc:/boot}` 확인 |
| Pod Update `Forbidden` | Container 이름은 Pod 불변 필드 | 실습 Pod 삭제 후 재생성 |
| `unknown flag: --dryrun` | `--dry-run`의 Hyphen 누락 | `--dry-run=server`로 입력 |
| `unknown shorthand flag: '0' in -0` | 숫자 `0`과 영문 소문자 `o` 혼동 | `kubectl get pods -o wide` 사용 |
| `path "label" does not exist` | 현재 위치가 이미 `labels/`라 하위 `label` Directory가 없음 | 현재 Directory 전체는 `kubectl apply -f .` |
| `ubectl: command not found` | `kubectl`의 첫 글자 누락 | 명령어를 다시 입력 |
| Boot·Nginx Pod 6개 `Pending` | Node의 `project=melong`이 Pod의 `project=boot/nginx` Selector와 불일치 | Node Label을 `project=boot --overwrite`로 보정 |
| Required NodeAffinity Boot Pod `Pending` | `key: melong`, `operator: Exists`지만 어떤 Node에도 `melong` Key가 없음 | 필수 조건과 Node Label을 일치시키거나 Soft 조건 사용 |
| `NoExecute` 적용 후 Pod 두 개가 사라짐 | `test` Toleration이 `nodename` Taint와 일치하지 않아 Taint Manager가 축출 | 의도된 결과이며 Event의 `TaintManagerEviction`으로 확인 |
| Zone Selector 변경 Apply가 Boot Pod만 실패 | 기존 Boot Pod의 `nodeSelector`는 생성 후 변경 불가 | 기존 Pod 삭제 후 새 Manifest로 재생성 |
| `cd ..\node_selectors` 실패 | Linux에서 Windows식 경로 구분자 사용 | `cd ../node_selectors` |
| VS Code dynamic forwarding 실패 | SSH Server가 배너를 보내지 못함 | Bastion Resource·Swap·VS Code Server 점검 |
| Docker Hub Image 삭제 | AWS 과금 Resource로 오인 | 필요 시 Jib로 다시 Push |

## 16. 이전 환경의 Terraform Destroy와 잔존 확인

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

## 검증 완료와 미완료

### 완료

- Terraform Apply 성공과 Bastion SSH 접속
- EKS API 조회
- Worker Node 2대 `Ready`
- `pod-basic.yml` Server-side dry run 통과
- `my-pod` API Object 생성
- `boot` Project의 Jib Plugin·Application Port 확인
- `ubuntu:26.04` Official Image Tag 존재 확인
- PDF p.19의 환경변수·`fieldRef` 예제 시각 대조
- Required·Preferred NodeAffinity의 Hard·Soft 배치 차이
- `NoExecute`와 Toleration 일치 여부에 따른 생존·축출 비교
- `00_eks` Destroy: 84개 Resource 삭제, State 0
- `00_eks` 주요 EKS·VPC·EC2·ASG·ENI·IAM·OIDC 잔존 없음

### 미완료·추가 증거 필요

- Bastion 내부 AWS CLI Profile의 실제 STS Identity는 삭제 전 확인하지 못함
- Jib Image 재Push 성공과 Docker Hub Tag 존재
- `my-pod`의 최종 `Running`·Log·HTTP 응답
- `ubuntu-pod` Apply와 실행 상태
- Ubuntu Container의 `kubectl exec` 결과
- p.19 환경변수 Manifest의 Server-side dry run·Apply·`exec env` 결과
- BusyBox에서 다른 Pod IP로 요청하고 `pod-net`의 Nginx Log에서 Source 확인
- 현재 2c Node의 `nodename=node2:NoExecute`와 살아남은 `boot-pod-1` 정리
- AWS 계정 전체 Region·서비스의 비용 Resource 전수 확인

## 다음 재시작 지점

1. EX.7이 끝나면 2c Node의 `nodename=node2:NoExecute`와 `boot-pod-1`을 정리한다.
2. 다음 범위인 EX.8 cordon·drain 실습으로 이어간다.
3. 더 이상 사용하지 않는 사용자 지정 `project` Node Label을 정리한다.
4. p.23의 다른 Pod 직접 통신·Log 확인이 필요하면 Pod 두 개를 다시 생성해 수행한다.
5. 수업 종료 후 `00_eks`를 Destroy한다.

## 관련 노트

- [[04_Kubernetes Pod와 ReplicaSet]]
- [[Source Digest/Kubernetes - Source Digest 04 Pod and ReplicaSet]]
- [[10_학습 노트/클라우드/AWS/서버_시퓨_100%_찍을_때|EC2 서버가 멈추거나 CPU 100% 찍을 때]]

## 공식 참고

- [Ubuntu Official Image](https://hub.docker.com/_/ubuntu)
- [Docker Hub Quickstart](https://docs.docker.com/docker-hub/quickstart/)
- [Docker Hub Search와 Trusted Content](https://docs.docker.com/docker-hub/image-library/search/)
- [Kubernetes Images](https://kubernetes.io/docs/concepts/containers/images/)
- [Kubernetes Pods](https://kubernetes.io/docs/concepts/workloads/pods/)
- [kubectl apply](https://kubernetes.io/docs/reference/kubectl/generated/kubectl_apply/)
- [kubectl exec](https://kubernetes.io/docs/reference/kubectl/generated/kubectl_exec/)
