보고서 쓸 때 첫 목차에서 '우리 조는 이런걸 했다!' 라고 확실하게 어필할 것. 안그러면 첫 인상이 비어보임.

# 오늘 한거
오전에 적는거 까먹었다. 근데 걍 디테일 한건 노션이던 폴더던 들어가서 봐.
## 사례 조사
## 수현 씨 테라폼 검토

### 14:51

- 수현 씨 팀 운영 계정이 아닌 장운호 개인 AWS 계정(`terra-user`)에서 Terraform 선행 통합 검증을 시작함.
- 계정·리전별 외부 선행 조건을 맞춘 뒤 Apply 진행 중: EC2 Key Pair 재등록, Route 53 사용자 Domain 경로 비활성화.
- 현재 결과는 미확정이며 팀 계정 배포 완료 증거로 사용하지 않음.
- Apply 완료 이후 실행 명령·오류·검증 결과를 이 RAW에 이어서 기록하되 자격증명과 Private Key는 기록하지 않음.

### 15:16

- 장운호 개인 AWS 계정에서 Terraform Apply 완료. Lock 없음, State 기준 317개 객체.
- 서울·도쿄 EKS `ACTIVE`, 서울 Multi-AZ MariaDB와 도쿄 Read Replica `available`, 양쪽 Bastion SSM `Online`, CloudFront `Deployed`.
- 서울 EKS는 Node 2대 `Ready`; Argo CD, AWS Load Balancer Controller, EFS CSI, Pod Identity Agent, Karpenter가 실행됨.
- 애플리케이션은 아직 없음: TargetGroupBinding은 `web/web-service:80`을 기다리고 있으며 `web` Service와 Argo CD Application은 0개. GitHub Actions IAM Role output도 생성되지 않음.
- 도쿄 EKS는 Node 1대 `Ready`; Karpenter 2개 중 1개가 Pod Anti-Affinity와 단일 Node 구성 때문에 `Pending`.

검증에 사용한 주요 명령:

```powershell
terraform output <output-name>
terraform state list
aws eks describe-cluster --profile terra-user --region <region> --name <cluster>
aws rds describe-db-instances --profile terra-user --region <region>
aws ssm describe-instance-information --profile terra-user --region <region>
aws cloudfront get-distribution --profile terra-user --id <distribution-id>
aws ecr describe-repositories --profile terra-user --region ap-northeast-2
```

SSM `AWS-RunShellScript`로 각 Bastion에서 실행한 읽기 전용 명령:

```bash
kubectl get nodes -o wide
kubectl get pods -A
helm list -A
kubectl get targetgroupbindings -A
kubectl get service -n web
kubectl get applications.argoproj.io -n argocd
kubectl describe pod -n kube-system <pending-karpenter-pod>
```

### 15:22

- `C:\Users\Unoh\.ssh\config`에 서울 Bastion 접속 별칭 `bas`를 설정하고 `ssh bas`로 직접 접속함.
- 접속 사용자 `ec2-user`, Bastion Hostname `ip-10-0-0-93.ap-northeast-2.compute.internal` 확인.
- 서울 EKS Node 2대가 `Ready`; Argo CD, AWS Load Balancer Controller, EFS CSI, Pod Identity Agent, Karpenter 등 주요 Pod가 `Running`.
- Helm Release `argocd`, `aws-load-balancer-controller`, `karpenter`가 모두 `deployed`.

```bash
whoami
hostname
kubectl get nodes -o wide
kubectl get pods -A
helm list -A
```

### 16:15

- GitHub Actions OIDC용 IAM Role과 ECR Push Policy를 Terraform으로 생성하고, `Uns-DVWA` Repository Variables에 `AWS_REGION`, `ECR_REPOSITORY`, `AWS_ROLE_ARN`을 등록함.
- Argo CD 웹 접속과 로그인까지 확인했으나 Application은 아직 0개임. Argo CD 설치만 완료된 상태이며 Repository 인증·Application·DVWA Helm 배포는 미구현임.
- 매일 `terraform destroy → apply`하는 운영을 고려해, AWS 내부의 수동 Kubernetes Secret·Argo Application에 의존하지 않고 GitHub에 남는 Workflow·Manifest·Secret을 기준으로 GitOps 구성을 자동 복원하기로 결정함.
- 목표 흐름: GitHub Actions가 DVWA Image를 ECR에 Push하고 immutable tag로 Helm 값을 갱신 → GitOps Bootstrap이 private Repository 인증과 Argo Application을 재생성 → Argo CD가 내부 `ClusterIP` Preview를 자동 배포함.
- 외부 `web-service`·ALB·CloudFront 연결은 첫 검증에서 제외함. `argocd-ui.ps1`은 SSH tunnel, 현재 admin 비밀번호 조회·Clipboard 복사, Argo 웹 관찰만 담당하도록 계획함.

### 17:27

- 보안 설계 검토에서 `AWS-StartPortForwardingSessionToRemoteHost`가 `host`·`portNumber`를 임의 지정하게 해 GitOps Role이 Bastion을 경유해 IMDS(`169.254.169.254:80`)나 RDS 등 내부 Endpoint에 Tunnel할 수 있는 권한 확대 경로를 발견함. 실제 악용은 수행하지 않았고 현재 Draft는 외부에 적용되지 않음.
- 영향: GitHub Workflow가 변조되면 Bastion Role의 임시 자격증명과 RDS Master Secret·EKS 관리자 권한으로 이어질 가능성이 있음.
- 보정 결정: Remote-host Document를 제거하고, Bastion의 `127.0.0.1:19443 → EKS API:443` 고정 Proxy와 Remote Port를 Literal로 고정한 Custom Session Document만 허용함. Workflow는 Local Port만 전달함.
- Kubernetes RBAC의 `create`는 `resourceNames`로 이름을 제한할 수 없어, Repo Secret·Application 1개만 생성하게 하려던 Draft 권한이 의도보다 넓어질 수 있음을 발견함. Named Placeholder를 관리자 Bootstrap에서 먼저 만들고 GitHub Role에는 Exact `get/patch/update`만 허용하는 보정을 검토 중임.
- 2026-07-15 이후 생성 GitHub Repository의 Immutable OIDC `sub`에 Owner·Repository Numeric ID가 포함되므로, 실제 ID 확인 전에는 IAM Trust를 추정하지 않고 Terraform Plan을 실패시키기로 함.

### 17:43

- `Uns-DVWA`의 기존 `.github/workflows/vulnerable.yml`에서 Repository Secret 전체를 JSON으로 가져온 뒤 Base64로 변환해 출력하는 경로를 확인함.
- 영향: GitHub Log Masking이 원문 Secret은 가리더라도 Base64 등으로 변환된 값은 그대로 노출될 수 있어, Workflow 실행 권한 탈취나 악성 Commit이 곧 Secret 유출로 이어질 수 있음.
- 조치: 해당 Workflow의 현재 삭제 상태를 유지하고 새 CI/CD 구성에 포함하지 않음. 실제 Secret 값 조회·실행·유출 검증은 수행하지 않음.

### 17:47

- 현재 `terraform.tfvars`에서 Bastion SSH 허용 CIDR이 `0.0.0.0/0`이며, Primary Bastion Role에는 EKS Cluster Admin과 RDS Master·DVWA DB Secret 접근 권한이 함께 부여돼 있음을 확인함.
- 영향: SSH Key 인증을 사용하더라도 Bastion이 인터넷 전체의 공격 표면에 놓이고, 침해 시 EKS와 DB Credential까지 이어지는 Blast Radius가 큼.
- 현재 경계: 기존 `bas` SSH와 Argo UI 운영을 임의로 중단하지 않기 위해 즉시 변경하지 않음. 외부 적용 전 사용자 IP `/32` 제한 또는 SSM-only 접속 전환을 별도 보안 결정으로 검토함.

### 17:48

- `enable_dr_compute`가 기본 `true`이고 DR ALB Security Group의 HTTP 80이 `0.0.0.0/0`에 열려 있으나, CloudFront Origin은 Primary ALB만 사용하도록 구성된 경계를 확인함.
- 영향: DR Backend를 연결한 뒤에도 현재 구성을 유지하면 DR ALB DNS로 CloudFront·WAF를 우회해 직접 접근할 수 있는 별도 공개 경로가 될 수 있음.
- 현재 경계: 이번 DVWA Preview는 Primary EKS의 내부 `ClusterIP`만 대상으로 하며 DR·ALB 공개 경로는 Goal 제외 범위라 수정하지 않음. 실제 DR Failover 설계 시 Origin 제한·접근 통제·검증 절차를 별도로 결정해야 함.

### 17:50

- 새 GitHub Workflow가 `actions/checkout@v6` 등 이동 가능한 Tag를 사용하고, Repository 설정의 `Require actions to be pinned to a full-length commit SHA`도 꺼져 있어 외부 Action 공급망 변조 위험을 확인함.
- 영향: Action Tag가 탈취·이동되면 OIDC Token, ECR Push 권한, Argo Deploy Key를 취급하는 Job에서 악성 코드가 실행될 수 있음.
- 조치: 각 공식 Action 저장소의 현재 Release Tag 대상 Commit을 직접 확인하고 Workflow의 `uses`를 Full-length SHA로 고정한 뒤 정적 검증하기로 함.

### 17:52

- DVWA Dockerfile의 Base Image가 `php:8-apache`, Composer Stage가 `composer:latest`처럼 이동 가능한 Tag를 사용함.
- 영향: ECR을 삭제한 뒤 동일한 Git Source SHA를 다시 빌드해도 Upstream Tag가 바뀌었다면 실제 Image Digest와 포함 Package가 달라질 수 있어, `sha-<commit>` Tag만으로 동일 Artifact 재현을 증명할 수 없음.
- 현재 경계: ECR 재생성과 DVWA 자동 복원 자체는 가능하지만 완전한 Reproducible Build는 아님. Base Image Digest 고정과 정기 갱신 절차는 호환성 검증이 필요한 후속 공급망 Hardening으로 분리함.

### 17:56

- DVWA 공식 README와 현재 Source를 대조해, Container 시작만으로 Table·기본 계정 데이터가 생성되지 않고 사용자가 `Setup DVWA → Create / Reset Database`를 실행해야 함을 확인함.
- `setup.php`는 로그인 없이 Session CSRF Token으로 실행할 수 있고, 내부 `MySQL.php`는 기존 Database를 먼저 `DROP`한 뒤 재생성함.
- 영향: DVWA가 외부 또는 신뢰하지 않는 내부 경로에 노출되면 Setup Endpoint를 통한 데이터 초기화·파괴 경로가 될 수 있음. 단순 `/login.php` HTTP 200과 Pod Ready만으로 DB가 온전하다고 판정할 수도 없음.
- 조치 방향: HTTP Setup Endpoint를 자동 호출하지 않고, 새 Database에서 필수 Table이 없을 때만 실행되는 비파괴적·Idempotent 초기화 Job과 Table 존재 검증을 사용함. Preview Service는 계속 내부 `ClusterIP`로 유지함.
