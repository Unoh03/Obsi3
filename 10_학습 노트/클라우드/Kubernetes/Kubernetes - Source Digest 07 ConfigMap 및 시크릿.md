---
type: source-digest
status: draft
created: 2026-07-21
parent_moc: "[[10_학습 노트/클라우드/Kubernetes/00_Kubernetes MOC]]"
source: "[[40_자료/강의 자료/Kubernetes.pdf]]"
source_pages: 135-160
digest_role: chapter
digest_index: "[[10_학습 노트/클라우드/Kubernetes/Kubernetes - Source Digest v1]]"
chapter: ConfigMap and Secret
source_hash: F97666865E22749C47640689B5C41DEE38476A40312A53915F60B4F6A4330D24
source_version: "PowerPoint PDF; 266 pages; metadata created 2024-07-18"
coverage_status: partial
extraction_method: "pdfplumber 0.11.9 text extraction + pypdfium2 render visual review"
---

# Kubernetes Source Digest 07 — ConfigMap and Secret

> 원자료 `Kubernetes.pdf` p.135-160을 페이지 단위로 옮긴 무손실 구조화 사본이다. 원자료의 명령·출력·실습용 자격증명과 시각적 취소선을 그대로 보존하고, 불일치는 별도로 표시한다.

## Coverage

| 범위 | Text | Visual | 원본 대조 | 상태 |
|---|---|---|---|---|
| p.135-160 | 완료 | 완료 | 완료 | 이 장 변환 완료 |

## PDF p.135

### 원자료 내용

- 장 표지: `Kubernetes ConfigMap & Secret`.

## PDF p.136

### 원자료 내용

- Kubernetes Cluster 운영 환경에서는 App 설정 정보나 인증 정보 같은 민감 정보를 Pod 내부에서 보관·관리하지 않는다.
- App 설정 정보는 ConfigMap, 인증 정보 같은 민감 정보는 Secret 오브젝트로 관리한다.
- ConfigMap과 Secret은 Namespace 단위로 적용되며, 같은 Namespace에 배포된 Pod에서 참조한다.
- Pod는 ConfigMap과 Secret을 다음 방식으로 참조할 수 있다.
  - FileSystem에 mount
  - 환경변수(`ENV`)로 참조

### 도식 의미

- Kubernetes Cluster 안에 `Test Namespace`와 `Prod Namespace`가 분리되어 있다.
- 각 Namespace의 Application이 해당 Namespace의 ConfigMap과 Secret을 사용하는 관계를 보여 준다.

## PDF p.137

### 원자료 내용

#### ConfigMap 특징

- Application 설정 정보를 `KEY = Value` 형식으로 정의한다.
- 컨테이너는 Key로 값을 참조하므로 Value를 자유롭게 변경할 수 있다고 설명한다.
- 주요 저장 예시:
  - DB 접속 정보
  - 모니터링 서비스 연결 정보
  - 다른 App의 IP 주소와 Port
- Namespace 단위로 관리할 수 있다. 예: 개발 환경 DB 접속 정보와 운영 환경 DB 접속 정보 분리.
- Directory 또는 File을 데이터로 정의할 수 있다. 파일 이름은 Key, 파일 내용은 Value가 된다.
- Apache나 Nginx 같은 서버 프로그램의 설정 파일 전체를 데이터로 정의할 수 있다.
- Image 설정값이 바뀔 때 Image를 다시 Build해야 하는 문제를 줄일 수 있다고 설명한다.
- ConfigMap 갱신 시:
  - 환경변수 참조: 변경이 Pod에 자동 반영되지 않는다.
  - Volume mount 참조: 변경이 Pod의 파일에 자동 반영된다.

#### Secret 특징

- SSH Key, SSL/TLS 인증서, Service Account Token 같은 민감 정보를 Namespace 단위로 관리한다.
- Secret이 생성된 Namespace에서만 사용할 수 있고 다른 Namespace에서는 참조할 수 없다.
- 데이터는 Base64로 인코딩해 저장하며 Pod가 참조할 때 디코딩되어 메모리에서 사용된다고 설명한다.
- ConfigMap과 같은 방법으로 사용할 수 있고, 크기는 `1MB` 미만이어야 한다고 적혀 있다.
- Pod가 특정 Secret 사용을 명시했다면 해당 Secret이 존재해야 Pod를 생성할 수 있다고 설명한다.

## PDF p.138

### 원자료 내용

- Literal 값으로 ConfigMap을 생성한다.

```bash
kubectl create configmap my-cm --from-literal=NAME=“Kube" \
  --from-literal=MESSAGE="Hello Kubernetes" -n delivery
kubectl get cm -n delivery
kubectl get cm -o yaml -n delivery
```

- 출력:

```yaml
apiVersion: v1
items:
  - apiVersion: v1
    data:
      MESSAGE: Hello Kubernetes
      NAME: Kube
    kind: ConfigMap
```

- `--from-literal=KEY=VALUE` 형식을 사용한다고 설명한다.

> [!note] 원자료 문자
> `NAME=“Kube"`는 여는 따옴표가 곡선형이고 닫는 따옴표가 직선형이다. 실행 가능한 문법으로 임의 교정하지 않고 원자료 표기를 보존했다.

## PDF p.139

### 원자료 내용

- `cm-pod-env-valuefrom.yml` 예시이다.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: pod-valuefrom
  labels:
    app: cm-test
  namespace: delivery
spec:
  containers:
    - name: my-pod
      image: chlzzz/kube-image:debug
      env:
        - name: NAME
          valueFrom:
            configMapKeyRef:
              name: my-cm
              key: NAME
        - name: MESSAGE
          valueFrom:
            configMapKeyRef:
              name: my-cm
              key: MESSAGE
      command: ['sh','-c','tail -f /dev/null']
```

### 도식 의미

- ConfigMap `my-cm`의 `NAME`, `MESSAGE` 값을 `env.valueFrom.configMapKeyRef`로 하나씩 Pod 환경변수에 연결한다.
- 도식의 ConfigMap 예시 값은 `NAME: Your Name`, `MESSAGE: Hello Kubernetes`이다.

## PDF p.140

### 원자료 내용

```bash
kubectl apply -f ./cm-pod-env-valuefrom.yml
kubectl get pod -n delivery
kubectl exec pod-valuefrom -n delivery -- env
```

- `pod-valuefrom`은 `1/1 Running`이다.
- 환경변수 출력에서 다음을 확인한다.

```text
NAME=Your Name
MESSAGE=Hello Kubernetes
```

- 다음 실습을 위해 Pod를 삭제한다.

```bash
kubectl delete pod pod-valuefrom -n delivery
```

## PDF p.141

### 원자료 내용

- `cm-pod-env-envfrom.yml` 예시이다.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: pod-envfrom
  labels:
    app: cm-test
  namespace: delivery
spec:
  containers:
    - name: my-pod
      image: chlzzz/kube-image:debug
      envFrom:
        - configMapRef:
            name: my-cm
      command: ['sh','-c','tail -f /dev/null']
```

### 도식 의미

- ConfigMap `my-cm` 전체 데이터를 `envFrom.configMapRef`로 Pod 환경변수에 연결한다.
- ConfigMap 예시 값은 `NAME: Your Name`, `MESSAGE: Hello Kubernetes`이다.

## PDF p.142

### 원자료 내용

```bash
kubectl apply -f configmap_secret/cm-pod-env-envfrom.yml
kubectl get pod -n delivery
kubectl exec pod-envfrom -n delivery -- env
```

- `pod-envfrom`은 `1/1 Running`이다.
- 환경변수 출력:

```text
NAME= Your Name
MESSAGE=Hello Kubernetes
```

- 원자료 출력에는 `NAME=` 뒤에 공백이 있다.
- 다음 실습을 위해 Pod와 ConfigMap을 삭제한다.

```bash
kubectl delete pod pod-envfrom -n delivery
kubectl delete cm my-cm -n delivery
```

## PDF p.143

### 원자료 내용

- 파일 기반 ConfigMap을 만들기 위해 디렉터리와 파일 2개를 생성한다.

```bash
mkdir configmap_secret/config
echo “Your Name" > configmap_secret/config/NAME
echo "Hello Kubernetes" > configmap_secret/config/MESSAGE
tree configmap_secret/config
```

```text
configmap_secret/config
├── MESSAGE
└── NAME
```

```bash
kubectl create configmap my-cm \
  --from-file=configmap_secret/config -n delivery
kubectl get cm -n delivery
```

- 파일 이름이 Key, 파일 내용이 Value가 된다.
- 디렉터리를 `--from-file=<file or dir>`에 지정하면 그 아래 파일 전체를 데이터로 사용한다고 설명한다.
- 출력에는 `my-cm`의 `DATA`가 `2`로 표시된다.

## PDF p.144

### 원자료 내용

```bash
kubectl get cm my-cm -o yaml -n delivery
```

```yaml
apiVersion: v1
data:
  MESSAGE: |
    Hello Kubernetes
  NAME: |
    Your Name
```

- 앞서 사용한 `envFrom` Pod로 파일 기반 ConfigMap을 테스트한다.

```bash
kubectl apply -f configmap_secret/cm-pod-env-envfrom.yml
kubectl exec pod-envfrom -n delivery -- env
```

```text
NAME=Your Name
MESSAGE=Hello Kubernetes
```

- 테스트 후 Pod와 ConfigMap을 삭제한다.

```bash
kubectl delete pod pod-envfrom -n delivery
kubectl delete cm my-cm -n delivery
```

## PDF p.145

### 원자료 내용

- MySQL 5.7 Pod를 관리자 비밀번호 없이 실행한다.

```bash
kubectl run mysql-pod --image=mysql:5.7 -n delivery
kubectl get pod mysql-pod -n delivery
kubectl logs mysql-pod -n delivery
```

- Pod 상태는 `0/1 CrashLoopBackOff`이다.
- Log의 핵심 오류:

```text
[ERROR] [Entrypoint]: Database is uninitialized and password option is not specified
You need to specify one of the following:
  - MYSQL_ROOT_PASSWORD
  - MYSQL_ALLOW_EMPTY_PASSWORD
  - MYSQL_RANDOM_ROOT_PASSWORD
```

- MySQL 컨테이너는 관리자 비밀번호 관련 환경변수가 필요하며, 현재는 정의하지 않아 실행할 수 없다고 설명한다.
- Pod를 삭제한다.

```bash
kubectl delete pod mysql-pod -n delivery
```

## PDF p.146

### 원자료 내용

- 명령에 관리자 비밀번호 환경변수를 직접 적어 Pod를 실행한다.

```bash
kubectl run mysql-pod --env=MYSQL_ROOT_PASSWORD=root \
  --image=mysql:5.7 -n delivery
kubectl get pod mysql-pod -n delivery
kubectl describe pod mysql-pod -n delivery
```

- Pod는 `1/1 Running`이다.
- `describe` 출력에 다음 값이 직접 표시된다.

```text
Environment:
  MYSQL_ROOT_PASSWORD: root
```

- 관리자의 비밀번호가 그대로 노출되며 외부에 노출되어서는 안 된다고 설명한다.
- 테스트 후 Pod를 삭제한다.

## PDF p.147

### 원자료 내용

- 실습용 값 `root`를 가진 Generic Secret을 생성한다.

```bash
kubectl create secret generic mysql-pass \
  --from-literal MYSQL_ROOT_PASSWORD=root -n delivery
kubectl get secret -n delivery
```

- `mysql-pass`의 type은 `Opaque`, `DATA`는 `1`이다.
- 일반 Secret은 Generic 형식을 사용하며 데이터 종류에 따라 type이 달라질 수 있다고 설명한다. 예: SSL/TLS type `tls`.

```bash
kubectl get secret mysql-pass -n delivery -o yaml
```

```yaml
apiVersion: v1
data:
  MYSQL_ROOT_PASSWORD: cm9vdA==
kind: Secret
```

- 원자료가 사용하는 관계는 다음과 같다.
  - 입력한 실습 값: `root`
  - YAML에 저장되어 표시된 Base64 값: `cm9vdA==`

## PDF p.148

### 원자료 내용

- `secret-pod-env-envfrom.yml` 예시이다.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: mysql-pod
  labels:
    app: secret-test
  namespace: delivery
spec:
  containers:
    - name: my-pod
      image: mysql:5.7
      envFrom:
        - secretRef:
            name: mysql-pass
```

### 도식 의미

- `mysql-pass` Secret의 `MYSQL_ROOT_PASSWORD: cm9vdA==` 데이터를 `envFrom.secretRef`로 Pod에 연결한다.
- Pod 생성 전에 참조하는 Secret이 반드시 존재해야 한다고 강조한다.

## PDF p.149

### 원자료 내용

```bash
kubectl apply -f configmap_secret/secret-pod-env-envfrom.yml
kubectl get pod -n delivery
kubectl describe pod mysql-pod -n delivery
```

- `mysql-pod`은 `1/1 Running`이다.
- `describe` 출력:

```text
Environment Variables from:
  mysql-pass  Secret  Optional: false
Environment: <none>
```

- Secret에서 가져온 환경변수의 실제 값이 `describe`에 직접 표시되지 않는 것을 확인한다.

> [!note] 원자료 출력 불일치
> 적용 직후 출력은 `pod/pod-envfrom created`이지만 이어지는 조회·설명 대상은 `mysql-pod`이다.

## PDF p.150

### 원자료 내용

```bash
kubectl exec -it mysql-pod -n delivery -- sh
env | grep MYSQL_ROOT_PASSWORD
```

```text
MYSQL_ROOT_PASSWORD=root
```

- Secret 값은 컨테이너에서 실제 참조할 때 Base64 디코딩되어 환경변수로 보인다고 설명한다.
- MySQL에 접속한다.

```bash
mysql –u root –p
```

- 입력한 비밀번호는 `root`이며 MySQL `5.7.38` 접속 성공 출력이 표시된다.
- `exit` 후 Pod와 Secret을 삭제한다.

```bash
kubectl delete pod mysql-pod -n delivery
kubectl delete secret mysql-pass -n delivery
```

## PDF p.151

### 원자료 내용

- Nginx SSL/TLS 설정 파일을 작성한다.

```bash
vi ~/configmap_secret/config/tls.conf
```

```nginx
ssl_protocols TLSv1 TLSv1.1 TLSv1.2;
server {
  listen 443 ssl;
  ssl_certificate /etc/cert/tls.crt;
  ssl_certificate_key /etc/cert/tls.key;

  location / {
    root /usr/share/nginx/html;
    index index.html;
  }
}
```

- OpenSSL package를 확인한다.

```bash
rpm -qa | grep openssl
```

```text
openssl-1.0.2k-24.amzn2.0.7.x86_64
openssl-libs-1.0.2k-24.amzn2.0.7.x86_64
```

- SSL/TLS 통신에는 사이트 인증서와 개인 Key가 필요하며, 생성에 OpenSSL을 사용한다고 설명한다.

## PDF p.152

### 원자료 내용

```bash
openssl req -new -newkey rsa:4096 -days 365 -nodes -x509 \
  -keyout cert.key -out cert.crt
```

- 4096 bit RSA private key를 생성한다.
- 입력 예시:

```text
Country Name: KR
State or Province Name: Seoul
Locality Name: Gangnam
Organization Name: Cloud
Organizational Unit Name: CloudTeam
Common Name: Enter(생략)
Email Address: Enter(생략)
```

```bash
ls cert*
```

```text
cert.crt  cert.key
```

- 인증서와 개인 Key 파일이 생성됐는지 반드시 확인하라고 안내한다.

## PDF p.153

### 원자료 내용

- `tls.conf` 전체를 ConfigMap 데이터로 생성한다.

```bash
kubectl create configmap tls-config \
  --from-file=configmap_secret/config/tls.conf -n delivery
kubectl describe cm tls-config -n delivery
```

- `describe` 출력의 `tls.conf`에는 p.151의 `ssl_protocols`, `server`, 인증서 경로, `location` 설정이 들어 있다.

## PDF p.154

### 원자료 내용

- 인증서와 Key로 TLS type Secret을 생성한다.

```bash
kubectl create secret tls tls-secret \
  --cert=cert.crt --key=cert.key -n delivery
kubectl describe secret tls-secret -n delivery
```

```text
Type: kubernetes.io/tls
Data
====
tls.crt: 1960 bytes
tls.key: 3272 bytes
```

```bash
kubectl get cm,secret -n delivery
```

- `configmap/tls-config`: `DATA 1`
- `secret/tls-secret`: `kubernetes.io/tls`, `DATA 2`
- Pod를 만들기 전에 ConfigMap과 Secret이 생성됐는지 확인하라고 안내한다.

## PDF p.155

### 원자료 내용

- `cm-secret-deploy-volume.yml`의 일부이다. Deployment 전체 내용은 TXT 교안을 참조하라고 적혀 있다.

```yaml
apiVersion: v1
kind: Service
metadata:
  name: nginx-svc
  labels:
    app: my-nginx
  namespace: delivery
spec:
  type: LoadBalancer
  selector:
    app: my-nginx
  ports:
    - port: 443
      targetPort: 443
```

```yaml
spec:
  volumes:
    - name: tls-config-volume
      configMap:
        name: tls-config
    - name: tls-secret-volume
      secret:
        secretName: tls-secret
  containers:
    - name: my-nginx
      image: nginx:latest
      ports:
        - containerPort: 443
      volumeMounts:
        - name: tls-config-volume
          mountPath: /etc/nginx/conf.d/
        - name: tls-secret-volume
          mountPath: /etc/cert/
```

- ConfigMap과 Secret을 각각 Volume으로 만들고 컨테이너 디렉터리에 mount한다.
- Service와 container port는 모두 `443`이다.

## PDF p.156

### 원자료 내용

```bash
kubectl apply -f configmap_secret/cm-secret-deploy-volume.yml
kubectl get pod,svc,deploy -n delivery
```

- 생성 출력:

```text
service/nginx-svc created
deployment.apps/my-deployment created
```

- Pod 2개가 `1/1 Running`, Deployment는 `2/2`이다.
- `nginx-svc`:
  - type: `LoadBalancer`
  - ClusterIP: `10.100.171.59`
  - External IP 표기: `amazonaws.com`
  - port: `443:30339/TCP`
- Local PC에서 ELB Endpoint로 HTTPS 연결을 시험한다.
- 자체 생성 인증서이므로 안전하지 않은 사이트 메시지가 표시된다고 설명한다.
- 정확한 테스트를 위해 Browser cache를 삭제하라고 안내한다.

## PDF p.157

### 원자료 내용

```bash
kubectl exec my-deployment-588d6fb885-lbtxc -n delivery \
  -- cat /etc/nginx/conf.d/tls.conf
```

- 출력에는 p.151의 Nginx SSL/TLS 설정이 표시된다.
- ConfigMap 변경 테스트를 위해 해당 설정 파일을 담은 ConfigMap을 수정하려 한다.

## PDF p.158

### 원자료 내용

```bash
kubectl edit cm tls-config -n delivery
```

- ConfigMap의 `tls.conf`에서 다음 줄을 삭제한다.

```nginx
ssl_protocols TLSv1 TLSv1.1 TLSv1.2;
```

- 나머지 `server`, 인증서 경로, `location` 설정은 유지한다.
- 원자료는 편집 지시에서 삭제 대상 뒤에 문자 그대로 `\n`을 표시한다.
- 잘못 삭제했다면 ConfigMap을 다시 생성한 뒤 테스트하라고 안내한다.

## PDF p.159

### 원자료 내용

```bash
kubectl exec my-deployment-588d6fb885-lbtxc -n delivery \
  -- cat /etc/nginx/conf.d/tls.conf
```

- ConfigMap 변경 후 컨테이너 안의 설정 파일도 변경되는 것을 확인하며, 반영에는 지연 시간이 필요하다고 설명한다.
- 파일 변경이 실행 중인 프로세스에 자동으로 적용되는 것은 아니라고 강조한다.
- 실행 중인 프로세스는 시작 시 읽은 기존 설정을 계속 사용하므로, 변경 반영에는 재시작 또는 reload가 필요하다고 설명한다.
- 제시한 반영 방법:
  - Sidecar가 변경을 감지하고 Service Container에 `SIGHUP` 전송
  - Application 자체가 설정 파일 변경을 감지하고 reload
  - 설명에는 컨테이너 재시작 예로 `systemctl restart`도 적혀 있다.

### 시각 정보

- 텍스트 추출 결과에는 `ssl_protocols TLSv1 TLSv1.1 TLSv1.2;`가 남지만, 렌더링된 페이지에서는 해당 줄에 취소선이 그어져 있다.
- 취소선은 p.158에서 삭제한 줄이 더 이상 유효한 설정 내용이 아님을 나타낸다.

## PDF p.160

### 원자료 내용

- ConfigMap의 `tls.conf` 전체를 다음 값으로 바꾼다.

```bash
kubectl edit cm tls-config -n delivery
```

```yaml
apiVersion: v1
data:
  tls.conf: "KEY\n"
kind: ConfigMap
```

- 컨테이너의 파일 내용을 확인하면 `Key`가 출력된다.

```bash
kubectl exec my-deployment-588d6fb885-lbtxc -n delivery \
  -- cat /etc/nginx/conf.d/tls.conf
```

- 실제 파일 내용은 바뀌었지만 실행 중인 Nginx가 이전 설정을 사용해 SSL/TLS 연결은 계속 동작한다고 설명한다.
- 실습 리소스를 삭제한다.

```bash
kubectl delete -f configmap_secret/cm-secret-deploy-volume.yml
kubectl delete cm tls-config -n delivery
kubectl delete secret tls-secret -n delivery
```

## 원자료 외 보충

- 없음. 이 문서는 PDF 원자료의 설명과 실습 결과를 보존한다.

## 누락·검토 대기

- 원자료가 참조한 TXT manifest 전체는 제공 범위에 없어 PDF에 보이는 부분만 옮겼다.
- p.138·p.143의 곡선형 따옴표, p.149의 Pod 생성 출력명, p.159의 `systemctl restart` 예시는 원자료 표기이며 이 문서에서는 실행 검증하지 않았다.
