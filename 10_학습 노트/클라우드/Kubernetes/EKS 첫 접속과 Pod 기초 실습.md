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
verified_on: 2026-07-21
---

# EKS 첫 접속과 Pod 기초 실습

> [!summary]
> Terraform으로 EKS와 Bastion을 구성하고, Cluster 연결을 확인한 뒤 첫 Pod를 생성했다. 이 과정에서 IAM Credential 재생성, AWS CLI Profile 혼동, 빈 YAML, Resource 이름 오타, Pod 불변 필드, Jib 실행 위치, VS Code Remote-SSH 고착을 겪었다.

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
| VS Code dynamic forwarding 실패 | SSH Server가 배너를 보내지 못함 | Bastion Resource·Swap·VS Code Server 점검 |
| Docker Hub Image 삭제 | AWS 과금 Resource로 오인 | 필요 시 Jib로 다시 Push |

## 11. Terraform Destroy와 잔존 확인

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
- `00_eks` Destroy: 84개 Resource 삭제, State 0
- `00_eks` 주요 EKS·VPC·EC2·ASG·ENI·IAM·OIDC 잔존 없음

### 미완료·추가 증거 필요

- Bastion 내부 AWS CLI Profile의 실제 STS Identity는 삭제 전 확인하지 못함
- Jib Image 재Push 성공과 Docker Hub Tag 존재
- `my-pod`의 최종 `Running`·Log·HTTP 응답
- `ubuntu-pod` Apply와 실행 상태
- Ubuntu Container의 `kubectl exec` 결과
- p.19 환경변수 Manifest의 Server-side dry run·Apply·`exec env` 결과
- AWS 계정 전체 Region·서비스의 비용 Resource 전수 확인

## 다음 재시작 지점

1. 다음 실습 전에 `00_eks`를 다시 Apply하고 EKS·Worker Node·Bastion 상태를 확인한다.
2. p.19 환경변수 Manifest는 먼저 Server-side dry run으로 들여쓰기와 Schema를 검사한다.
3. Apply 후 `get -o wide`와 `exec env`로 Node·Namespace·Node IP·Pod IP 주입 결과를 확인한다.
4. Spring Boot 실행이 목적이면 `command`를 제거하고, 환경변수 실습이 목적이면 현재 `sleep` 명령을 사용한다.
5. 확인된 출력만 이 노트에 추가하고 수업 종료 후 다시 Destroy한다.

## 관련 노트

- [[Kubernetes Pod와 ReplicaSet]]
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
