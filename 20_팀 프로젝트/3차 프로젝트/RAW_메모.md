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
