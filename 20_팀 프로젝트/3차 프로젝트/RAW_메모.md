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

### 18:17

- Bastion User Data가 `kubectl`의 최신 Patch와 고정 Version의 Helm 압축 파일을 HTTPS로 내려받아 `root` 권한으로 설치하지만, 현재 Script에는 SHA-256 또는 서명 검증이 없음.
- 영향: Download 경로·배포 Artifact가 변조되면 EKS 관리자 권한을 가진 Bastion에 임의 Code가 설치될 수 있고, 같은 Terraform Source를 다시 Apply해도 다른 `kubectl` Patch가 설치되어 환경 재현성이 달라질 수 있음.
- 현재 경계: GitHub Actions의 외부 Action과 Session Manager Plugin은 SHA로 고정·검증했지만 Bastion CLI 공급망은 아직 같은 수준으로 닫히지 않음.
- 후속 조치: 검증된 Version과 공식 Checksum을 함께 고정하고, Update 시 Version·Checksum을 명시적으로 갱신하는 방식으로 Hardening할 후보로 기록함.

### 18:21

- GitOps Runtime 검증용 Kubernetes RBAC에 `dvwa-db` Secret의 `get`을 허용하면, Workflow는 Type만 조회하더라도 탈취된 GitOps Role이 API 응답의 실제 DB 자격증명까지 읽을 수 있음을 확인함.
- `kubectl exec` 기반 DB 확인도 `pods/exec create` 권한을 요구해, 같은 Role이 DVWA Container에서 임의 명령을 실행하거나 환경변수의 Secret을 꺼낼 수 있는 권한 상승 경계가 됨.
- 조치: Secret 조회와 `pods/exec` 권한을 모두 제거하고, Deployment Ready와 DB 초기화 Init Container의 정상 종료 상태를 읽기 전용으로 확인하여 Secret 전달·Schema 초기화 성공을 증명하도록 보정함.

### 19:27

- DVWA Repository의 Commit·Push를 기준으로 GitHub Actions가 Image Build·ECR Push·GitOps Revision 갱신을 수행하고, Argo CD가 Pod를 자동 배포하는 구성을 구현함.
- 매일 전체 환경을 `destroy → apply`하면 ECR Image·EKS·Argo CD·AWS 측 IAM 연결이 사라지는 문제를 확인해, `apply-and-bootstrap.ps1`이 Terraform Apply 뒤 Build와 GitOps Bootstrap을 다시 호출하는 방향을 설계함. `workflow_dispatch`, `paths-ignore`, `[skip ci]`, `GITHUB_TOKEN` 재귀 방지는 중복 실행 대책일 뿐 Resource 재생성 문제의 해결책은 아니었음.
- 시행착오: “완전 복구”를 기존 DB 데이터 보존까지 포함한다고 과대 해석해 RDS 유지·Snapshot·Backup/Restore·State 분리를 검토했으나, 사용자는 비용 절약용 DVWA Lab의 DB 데이터 보존을 원하지 않았음. 최종 결정은 Primary RDS·DR Replica와 데이터를 매일 삭제하고 Snapshot·Backup·Restore 없이 다음 Apply에서 빈 DB와 DVWA 기본 Schema·Seed를 자동 생성하는 것임.
- 비용·수명주기 경계는 GitHub OIDC Provider·IAM Role·ECR 최신 Image·GitHub Secret/Variable/Deploy Key만 보존하고, VPC·EKS·Node·Bastion·Argo CD·ALB·NAT·RDS·DR Replica 등 실행 환경은 삭제하는 방향으로 보정함. ECR Image 저장비 외에는 보존 계층의 지속 비용이 거의 없음.
- 현재 상태: `D:\DVWA`의 CI/CD·Helm·GitOps 변경은 Staged 상태이며 Commit·Push 및 Runtime 검증 전임. `D:\terraform\aws_terraform_build_code`는 Git Repository가 아닌 로컬 변경본이고, 현재 RDS Code의 `deletion_protection = true`, `skip_final_snapshot = false`는 위 최종 결정에 아직 맞추지 않았음.
- 수현 씨가 전달한 원본 후보 `aws_terraform_build_code.zip`은 32개 Entry, SHA-256 `EC61DD604EBC5F3D45356F515FAB0350B76EB9BFA86AA31085AFAB3E92B55020`으로 확인함. 현재 작업본을 덮어쓰지 않고 별도 기준선 폴더에만 압축 해제해 Diff할 예정임.

### 20:19

- 공식 DVWA 원본의 `.github/workflows/vulnerable.yml`은 `master` push 시 GitHub Secrets·Variables를 JSON과 Base64 형태로 출력하도록 작성된 의도적 취약 예제임.
- 현재 작업 브랜치는 `main`이므로 자동 실행 조건에는 해당하지 않지만, `master` 사용·Trigger 변경·Workflow 재사용 시 Secret 노출 경로가 될 수 있음.
- 신규 DVWA CI/CD Workflow는 이 파일을 호출하거나 재사용하지 않으며, GitHub OIDC 임시 자격증명과 ECR 최소 권한 Role만 사용하기로 함.

### 23:44

- CI/CD Goal 중간 점검: `D:\DVWA`는 `origin/main`보다 3 Commit 앞서 있으며, Foundation/Daily State 분리·DVWA Database 자동 초기화·`daily-up.ps1`·`daily-down.ps1` 정적 구현과 검증은 완료됐다. AWS Foundation Apply, E2E 배포, Down→Up 2회 재현은 아직 미검증이다.
- GitHub CLI 2.96.0은 공식 배포본 Hash 검증 후 설치·인증됐으나 현재 실행 중인 Codex Process는 갱신된 User PATH를 아직 보지 못한다. GitHub Repository Variables는 남아 있지만 대응하는 AWS OIDC·ECR·IAM Role은 현재 없고 Deploy Key도 아직 없다.
- 신뢰성 결함 후보: SSM Association을 1회만 조회함, Daily State가 비었을 때 EKS·RDS만 Drift 확인함, `daily-down.ps1`이 빈 State에서 과금 잔존 Resource 확인 없이 종료함, Argo CD 첫 Sync의 일시 실패에 같은 Commit 재시도 정책이 없음.
- 다음 정적 보정: `gh` 경로 자동 해석, SSM bounded polling, Project Tag·Name 기반 Daily 과금 Resource Drift/잔존 검사, Argo CD bounded retry. 알 수 없는 Resource는 자동 삭제하지 않고 ID를 보고한 뒤 중단한다.
- 팀 노트북·팀 AWS 계정 이전 시 Source만 이전하고 개인 계정 State·Credential·Private Key는 복사하지 않는다. 팀 계정에서 AWS 인증, Foundation, Deploy Key, GitHub Variables를 1회 재생성해야 하며 Account·Path Parameter화가 끝나야 간편한 인계가 가능하다.

### 2026-07-30 00:24

- Daily Script 신뢰성 보정: User·Machine PATH 자동 갱신, SSM Association 최대 20분 bounded polling, 빈 State의 Project Tag 기반 AWS Runtime 검사, Destroy 후 State 기반·Tag 기반 이중 잔존 검사를 반영했다.
- Tag API가 종료된 EC2와 `PendingDeletion` KMS도 잠시 반환하는 것을 확인해, 각 Service의 실제 활성 상태를 다시 조회한 Resource만 Drift·잔존으로 판정하도록 보정했다. 현재 개인 계정의 활성 `aws-topology` Daily Runtime 판정은 0개다.
- Argo CD Application에 동일 Revision의 일시적 첫 Sync 실패를 위한 최대 5회 exponential backoff retry와 새 Revision refresh를 추가했다.
- 팀 계정 이식성을 위해 AWS Profile·Account·Project·Region·EC2 Key Pair 이름을 Wrapper에서 Terraform Plan으로 전달하고, Source만 이전하며 State·Credential·Private Key를 새 노트북에 복사하지 않는 절차를 Runbook에 추가했다.
- Gitleaks는 기존 공식 DVWA의 `vulnerabilities/csrf/help/help.php` 54행 예제 문자열 1건을 `generic-api-key`로 탐지했다. 해당 파일은 이번 변경 및 `origin/main` 대비 변경되지 않았으며, 새 Credential 유입 증거는 아니다.
- Foundation Preview는 ECR Repository·Lifecycle Policy·GitHub OIDC Provider·ECR Push 전용 IAM Role·Inline Policy의 `5 create / 0 change / 0 destroy`로 확인됐다. AWS·GitHub 변경은 아직 수행하지 않았고 `SETUP FOUNDATION` 승인 대기 상태다.

### 00:34

- GitHub 실제 설정에서 Repository가 Private이며 immutable OIDC prefix가 `repo:Unoh03@67749487/Uns-DVWA@1315708638`, `use_default: true`로 확인됐고 Foundation의 `main` Branch Subject와 일치했다.
- 새 노트북에서 이전 Private Key를 복사하지 않아도 되도록 `setup-foundation.ps1`에 명시적 `-RotateDeployKey` 경계를 추가했다. 현재 GitHub Deploy Key는 0개다.
- Managed Sandbox 안의 Plan은 local State lock 파일 쓰기 권한 때문에 `Access is denied`로 실패했고, AWS·GitHub 변경 없는 Plan 재실행은 정상 통과했다.
- 최신 Foundation Plan은 다시 `5 create / 0 change / 0 destroy`이며 Apply·Deploy Key 등록·GitHub Variable 갱신은 아직 수행하지 않았다.
- `ssh-keygen` 일회용 Probe로 Script의 무암호 ED25519 Deploy Key 생성 인자를 검증했고 Probe Key는 즉시 삭제했다.

### 00:49

- Foundation 첫 Apply에서 ECR Repository와 Lifecycle Policy는 생성됐지만 IAM OIDC Provider 생성이 `HTTP 302 / UnknownError`로 일시 실패했다. State에는 성공한 Resource만 기록됐다.
- State 기준 재계획은 `3 create / 0 change / 0 destroy`였고 재시도에서 OIDC Provider·GitHub Actions IAM Role·ECR Push Inline Policy가 생성됐다.
- GitHub Deploy Key 목록이 비어 있을 때 StrictMode가 `null.title`을 읽는 오류를 발견해 빈 배열 처리를 보정했다. 이후 Terraform `0/0/0`, read-only Deploy Key 등록, `AWS_REGION`·`ECR_REPOSITORY`·`AWS_ROLE_ARN` 갱신이 완료됐다.
- DVWA `main` Push 뒤 GitHub Actions Run `30467506262`가 EKS Cluster 0개 상태에서도 OIDC 인증·ECR 로그인·Image Build/Push·GitOps Commit을 모두 성공했다.
- ECR에는 `sha-a737dca315311f08c22309d4463d42db55aebadf` Image가 생성됐고, GitOps Bot Commit `b73cd025`가 같은 Repository와 Tag를 `deploy/dvwa/values.yaml`에 기록했다.
- Bot Commit은 `[skip ci]`를 사용해 추가 Workflow 실행 없이 종료됐으며 로컬 `main`도 `origin/main`으로 fast-forward 동기화했다.

### 10:26

- Daily Runtime 최초 Apply `249 create / 0 change / 0 destroy`가 완료됐고, EKS·RDS·Bastion·Argo CD 등 개인 Account Runtime이 생성됐다.
- 시행착오: Windows 임시 Secret 파일 ACL의 Account 문자열 오류, MariaDB 11.8의 `require_secure_transport=ON`에 따른 `ERROR 3159`, Argo CD CRD가 거부한 `spec.syncPolicy.retry.refresh`, ALB→Kubernetes Node 80/TCP SG 누락으로 인한 Target Timeout·CloudFront 504를 확인했다.
- 조치: 정확한 Windows Identity ACL, RDS Global CA Bundle 기반 TLS, 비지원 Argo 필드 제거, Primary·DR ALB에서 Node SG 80/TCP로 가는 Ingress Rule을 반영했다.
- GitHub Actions Run `30502223778`에서 Image Build·ECR Push·GitOps Commit이 성공했고, Image `sha-1231eb8b091e4911868dddb0c5290e1edf2b1cde`가 배포됐다.
- 최종 업 검증: DVWA Database·전용 User·Kubernetes Secret·Schema 준비, Argo CD `Synced / Healthy`, DVWA Pod `Running / Ready`, 외부 URL 응답까지 확인했다. 마지막 `daily-up.ps1`은 1.3분에 완료됐고 요청에 따라 `daily-down`은 실행하지 않았다.
- 추가 관찰: EKS Managed Node Group `release_version`이 `1.35.6-20260724 → 1.35.6-20260728`로 자동 Drift해 의도하지 않은 Rolling Update가 발생했고 앞선 재실행 시간이 크게 늘었다.

### 10:35

- EKS Module의 `use_latest_ami_release_version` 기본 동작 때문에 Plan 시 최신 권장 AMI Release를 따라가는 것이 자동 Drift의 원인으로 확인됐다.
- 현재 Primary와 DR의 Release가 서로 달라 단일 Version으로 고정하지 않고, 추후 지역별 `ami_release_version` 입력으로 각각 고정하는 방향을 검토한다.
- 지금은 Argo CD와 DVWA Runtime 확인을 위해 Terraform Source·AWS Runtime을 변경하지 않고 후속 작업으로 보류한다.
