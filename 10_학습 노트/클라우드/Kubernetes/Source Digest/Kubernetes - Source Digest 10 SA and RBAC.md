---
type: source-digest
status: stable
created: 2026-07-21
parent_moc: "[[10_학습 노트/클라우드/Kubernetes/00_Kubernetes MOC]]"
source: "[[40_자료/강의 자료/Kubernetes.pdf]]"
source_pages: "187-197"
digest_role: chapter
digest_index: "[[10_학습 노트/클라우드/Kubernetes/Source Digest/Kubernetes - Source Digest v1]]"
chapter: "10 SA and RBAC"
source_hash: F97666865E22749C47640689B5C41DEE38476A40312A53915F60B4F6A4330D24
source_version: "PowerPoint PDF; 266 pages; metadata created 2024-07-18"
coverage_status: complete
extraction_method: "pdfplumber 0.11.9 text extraction + pypdfium2 render visual review"
reviewed_on: 2026-07-21
---

# Kubernetes - Source Digest 10 SA and RBAC

> [!purpose]
> `Kubernetes.pdf` p.187–p.197의 의미 있는 정보를 페이지별로 보존한 Chapter Digest이다. 원자료의 기술적 정확성을 현재 지식으로 검증하거나 몰래 교정하지 않는다.

## Source 식별

- 원자료: [[40_자료/강의 자료/Kubernetes.pdf|Kubernetes.pdf]]
- 대상 범위: PDF p.187–p.197
- 전체 원자료: 266 pages
- SHA-256: `F97666865E22749C47640689B5C41DEE38476A40312A53915F60B4F6A4330D24`
- 추출·검수: `pdfplumber 0.11.9` Text Layer + `pypdfium2` Rendering
- Chapter 경계: ServiceAccount, Role·ClusterRole, User·Group, EKS 인증·인가, IRSA

## Coverage

| PDF 범위 | Text | YAML·명령·표 | Visual | 원본 대조 | 상태 |
|---|---|---|---|---|---|
| p.187–p.197 | 완료 | 완료 | 전체 렌더 검토 | 페이지별 대조 | 상세 변환 완료 / 기술 내용 외부 검증 미수행 |

## 변환 경계

- 아래 고정폭 Transcript는 PDF Text Layer의 Page 배치를 최대한 보존한다.
- YAML·명령·출력은 Rendering으로 기호와 배치를 대조했다. 원자료의 오탈자·잠재적 명령 오류는 임의로 수정하지 않는다.
- Visual 관계는 Text Layer 밖의 화살표·번호·공간 배치를 별도 설명한다.
- `status: draft`는 원자료 변환이 누락됐다는 뜻이 아니라, 전체 Index 통합 검수와 외부 기술 검증이 아직 끝나지 않았다는 뜻이다.

## SA & RBAC

## PDF p.187

- 원본: [[40_자료/강의 자료/Kubernetes.pdf#page=187|Kubernetes.pdf p.187]]
- 정보 유형: Cover

### 원자료 내용

~~~text
Kubernetes                          SA        &       RBAC
~~~

## PDF p.188

- 원본: [[40_자료/강의 자료/Kubernetes.pdf#page=188|Kubernetes.pdf p.188]]
- 정보 유형: Text, 도식

### 원자료 내용

~~~text
               Kubernetes         Service      Account       &   Role-Based        Access      Control





      ◎  Service  Account & Role-Based  Access Control


         Service Account는 Kubernetes Cluster 내에서 체계적인   권한관리를    위한  오브젝트로    Namespace별로  구분된다.
         Kubernetes Cluster 내부 모든 Namespace에는  "default Service Account"를 자동으로  생성  및  포함한다.

         Service Account에 특정 권한을   부여는하기    위해서는    Role 혹은 Cluster Role을 정의  후  Role Binding 작업을  수행해야한다.

         Role & Cluster Role은 Service Account에 부여할 권한이   무엇인지   정의하는    오브젝트   ( Role Binding : SA <-> Role )
         Role: Namespace 한정 Object ( Pod, Deploy ) 권한 정의 / Cluster Role: Cluster 전체 ( Node, Volume ) 권한 정의

         Cluster Role에서는 Namespace 한정  Object 권한 정의도   가능하며,    Cluster 내부의  모든  Object에 대한  권한   정의가   가능하다.


                Kubernetes   Cluster  (  K8s  )


                               Test  Namespace                           Prod  Namespace








External
 Client
~~~

### Visual 의미

- Kubernetes Cluster 안의 `Test Namespace`와 `Prod Namespace`에 각각 `RoleBinding(rb) → Role` 관계가 있고, `sa`·`user`·`group` Subject가 RoleBinding 아래에서 Pod 접근 권한을 받는 구조로 배치된다.
- Namespace 밖 Cluster 범위에는 `ClusterRole(c.role)`과 `ClusterRoleBinding(crb)`이 있으며, ClusterRoleBinding은 Namespace 안의 Subject와도 연결된다.
- 외부 Client의 `kubelet` 요청은 점선 화살표로 Test Namespace의 RoleBinding 방향을 가리킨다.
- Role/RoleBinding은 Namespace별 Pod 접근을, ClusterRole/ClusterRoleBinding은 Cluster 범위 연결을 나타내도록 두 층으로 구분되어 있다.

## EX.1 Role

## PDF p.189

- 원본: [[40_자료/강의 자료/Kubernetes.pdf#page=189|Kubernetes.pdf p.189]]
- 정보 유형: Text, YAML/설정, 도식

### YAML·설정

~~~text
           Kubernetes         Role-Based         Access      Control     (  EX.1    : Role    )






<작업대상:    rbac-role.yml  >
                                                       ---
apiVersion: v1                                         apiVersion: rbac.authorization.k8s.io/v1

kind: ServiceAccount                                   kind: RoleBinding

metadata:                                              metadata:
  name: my-sa                                           name: pod-viewer-role-rb

  namespace: delivery                                   namespace: delivery

---                                                    subjects:
apiVersion: rbac.authorization.k8s.io/v1               - kind: ServiceAccount

kind: Role                                              name: my-sa

metadata:                                               namespace: delivery
  name: pod-viewer-role                                roleRef:

  namespace: delivery                                   kind: Role

rules:                                                  apiGroup: rbac.authorization.k8s.io # Role Object API Group
- apiGroups: [""]             # Object API Group        name: pod-viewer-role

  resources: ["pods"]         # Object Name

  verbs: ["get","watch","list"] # Allow Permission
~~~

### Visual 의미

- 여러 열에 배치된 Manifest·설명은 Text Layer의 선형 순서만으로 읽지 않는다. Rendering의 좌→우 배치, 들여쓰기와 연결선을 함께 기준으로 한다.

- `my-sa` ServiceAccount와 `pod-viewer-role` Role이 `pod-viewer-role-rb` RoleBinding의 `subjects`·`roleRef`로 연결되는 화살표가 핵심이다.

## PDF p.190

- 원본: [[40_자료/강의 자료/Kubernetes.pdf#page=190|Kubernetes.pdf p.190]]
- 정보 유형: Text, 명령/출력, 표형 정보

### 명령·출력

~~~text
           Kubernetes         Role-Based         Access      Control     (  EX.1    : Role    )






$ kubectl  apply -f rbac/rbac-role.yml

$ kubectl  get sa,role,rolebindings  -n  delivery

NAME                   SECRETS  AGE
serviceaccount/my-sa   0        18s

NAME                                                  CREATED AT

role.rbac.authorization.k8s.io/pod-viewer-role        2023-09-21T08:44:57Z
NAME                                                  ROLE                 AGE

rolebinding.rbac.authorization.k8s.io/pod-viewer-role-rb Role/pod-viewer-role 18s

$ kubectl  describe rolebindings  pod-viewer-role-rb  -n  delivery

Name:        pod-viewer-role-rb

Role:

  Kind: Role
  Name: pod-viewer-role

Subjects:

  Kind          Name   Namespace
  ----          ----   ---------

  ServiceAccount my-sa delivery
~~~

## PDF p.191

- 원본: [[40_자료/강의 자료/Kubernetes.pdf#page=191|Kubernetes.pdf p.191]]
- 정보 유형: Text, 명령/출력, 표형 정보

### 명령·출력

~~~text
           Kubernetes         Role-Based         Access      Control     (  EX.1    : Role    )






$ kubectl  apply -f resources/resource-limit-request.yml

pod/res-pod created

▣ Resource Management에서 구성한  Manifast File을 이용하여  TEST Pod를 생성


$ kubectl  auth can-i get  pod -n delivery  --as system:serviceaccount:delivery:my-sa
$ kubectl  get pod -n delivery  --as system:serviceaccount:delivery:my-sa

NAME     READY  STATUS   RESTARTS   AGE

res-pod  1/1    Running  0          6m45s

$ kubectl  delete pod res-pod  -n delivery  --as system:serviceaccount:delivery:my-sa

Error from server (Forbidden): pods "res-pod" is forbidden: User "system:serviceaccount:delivery:my-sa"

cannot delete resource "pods" in API group "" in the namespace "delivery"

$ kubectl  delete pod res-pod  -n delivery

$ kubectl  delete -f rbac/rbac-role.yml


▣ "--as system:serviceaccount:delivery:mysa" 지정 된 Service Account를 이용하여 Kubectl 명령을 수행
▣ Role에서  정의  된 Pod 오브젝트에   대한  작업만  가능한  것을  확인  / 허용되지  않은  "delete" 작업은  Forbidden Error가 발생하는 것을  확인

▣ 다음  TEST를 위해  생성한  오브젝트를   삭제
~~~

## EX.2 ClusterRole

## PDF p.192

- 원본: [[40_자료/강의 자료/Kubernetes.pdf#page=192|Kubernetes.pdf p.192]]
- 정보 유형: Text, YAML/설정, 도식

### YAML·설정

~~~text
           Kubernetes         Role-Based         Access      Control     (  EX.2    : Cluster     Role    )






<작업대상:    rbac-cluster-role.yml  >

apiVersion: v1                                         ---

kind: ServiceAccount                                   apiVersion: rbac.authorization.k8s.io/v1

metadata:                                              kind: ClusterRoleBinding
  name: my-sa                                          metadata:

  namespace: delivery                                   name: node-viewer-role-rb

---                                                    subjects:
apiVersion: rbac.authorization.k8s.io/v1               - kind: ServiceAccount

kind: ClusterRole                                       name: my-sa

metadata:                                               namespace: delivery
  name: node-viewer-role                               roleRef:

rules:                                                  kind: ClusterRole

- apiGroups: [""]             # Object API Group        apiGroup: rbac.authorization.k8s.io # Role Object API Group
  resources: ["nodes"]        # Object Name             name: node-viewer-role

  verbs: ["get","watch","list"] # Allow Permission
~~~

### Visual 의미

- 여러 열에 배치된 Manifest·설명은 Text Layer의 선형 순서만으로 읽지 않는다. Rendering의 좌→우 배치, 들여쓰기와 연결선을 함께 기준으로 한다.

- ServiceAccount와 ClusterRole이 ClusterRoleBinding의 `subjects`·`roleRef`로 연결되는 관계를 좌우 화살표로 표시한다.

## PDF p.193

- 원본: [[40_자료/강의 자료/Kubernetes.pdf#page=193|Kubernetes.pdf p.193]]
- 정보 유형: Text, 명령/출력, 표형 정보

### 명령·출력

~~~text
           Kubernetes         Role-Based         Access      Control     (  EX.2    : Cluster     Role    )






$ kubectl  apply -f rbac/rbac-cluster-role.yml

$ kubectl  get clusterrole  node-viewer-role

NAME             CREATED AT
node-viewer-role 2023-09-21T09:39:05Z


$ kubectl  get clusterrolebinding  node-viewer-role-rb

NAME                ROLE                        AGE
node-viewer-role-rb ClusterRole/node-viewer-role 99s


$ kubectl  describe clusterrole  node-viewer-role

Name:        node-viewer-role
Labels:      <none>

Annotations: <none>

PolicyRule:
  Resources Non-Resource URLs Resource Names Verbs

  --------- ----------------- -------------- -----

  nodes     []               []             [get watch list]
~~~

## PDF p.194

- 원본: [[40_자료/강의 자료/Kubernetes.pdf#page=194|Kubernetes.pdf p.194]]
- 정보 유형: Text, 명령/출력, 표형 정보

### 명령·출력

~~~text
           Kubernetes         Role-Based         Access      Control     (  EX.2    : Cluster     Role    )






$ kubectl  auth can-i get  nodes --as system:serviceaccount:delivery:my-sa

$ kubectl  get nodes --as  system:serviceaccount:delivery:my-sa

NAME                                           STATUS   ROLES   AGE  VERSION
ip-192-168-10-147.ap-northeast-2.compute.internal Ready <none>  8d   v1.24.16-eks-8ccc7ba

ip-192-168-20-156.ap-northeast-2.compute.internal Ready <none>  8d   v1.24.16-eks-8ccc7ba


$ kubectl  cordon ip-192-168-20-156.ap-northeast-2.compute.internal     \

--as system:serviceaccount:delivery:my-sa

error: unable to cordon node "ip-192-168-20-156.ap-northeast-2.compute.internal":

nodes "ip-192-168-20-156.ap-northeast-2.compute.internal" is forbidden: User
"system:serviceaccount:delivery:my-sa" cannot patch resource "nodes" in API group "" at the cluster scope


$ kubectl  delete -f rbac/rbac-cluster-role.yml


▣ "--as system:serviceaccount:delivery:mysa" 지정 된 Service Account를 이용하여 Kubectl 명령을 수행

▣ ClusterRole에서 정의  된 Node에 대한  작업만  가능한   것을 확인  / 허용되지   않은  "cordon" 작업은 Forbidden Error가 발생하는  것을  확인
▣ 다음  TEST를 위해  생성한  오브젝트를   삭제
~~~

## EX.3 User & Group

## PDF p.195

- 원본: [[40_자료/강의 자료/Kubernetes.pdf#page=195|Kubernetes.pdf p.195]]
- 정보 유형: Text, YAML/설정

### YAML·설정

~~~text
           Kubernetes         Role-Based         Access      Control     (  EX.3    : User    &   Group      )






▣  Kubernetes User  & Group

>. User : Service Account를 지칭하는  고유한  이름  ["system:serviceaccount:<Namespace>:<ServiceAccountName>"]
>. Group : Kubernetes User를 모아놓은 집합  ["system:serviceaccounts(Group)"]

>. serviceaccounts Group은 Kubernetes Cluster 내부의 ServiceAccount를 모아놓은 Group이다.

>. ServiceAccount Group 처럼 Kubernetes에 의해 미리 정의되어  사용되는   Group의 접두어에는   "system:"을 사용한다.
>. Kubernetes User & Group은 RoleBinding Object의 Kind 속성의 값으로 사용이 가능하다.


[ User & Group  RoleBinding  Subjects Example  ]

subjects:                                         subjects:

- kind: User                                      - kind: Group

  name: devops                                     name: dev-group

subjects:                                         subjects:

- kind: User                                      - kind: Group
  name: system:serviceaccount:delivery:my-sa       name: system:serviceaccounts


subjects:                                         subjects:
- kind: Group                                     - kind: Group

  name: system:serviceaccounts:default             name: system:authenticated
~~~

### Visual 의미

- 여러 열에 배치된 Manifest·설명은 Text Layer의 선형 순서만으로 읽지 않는다. Rendering의 좌→우 배치, 들여쓰기와 연결선을 함께 기준으로 한다.

## EKS Authentication & Authorization

## PDF p.196

- 원본: [[40_자료/강의 자료/Kubernetes.pdf#page=196|Kubernetes.pdf p.196]]
- 정보 유형: Text, 도식

### 원자료 내용

~~~text
         Kubernetes         RBAC      ( EKS    Authentication           &   Authorization          )






 ◎  AWS EKS  Authentication  & Authorization

    IAM + "aws-auth" ( Authentication ) : 인증       ⑦  IAM Identity
    Kubernetes RBAC ( Authorization ) : 인가            Mapping Check       ⑤  STS:GetCallerIdentity

    EKS Authenticator & Authorization 실습 진행
                                                                          ⑥  IAM Identity Return
                                                                   AWS IAM                       AWS STS


                                                                  ConfigMap : aws-auth [ Authentication ]

①  K8s Action

                                                             ④  Token Review
                      ③ Action + Token

                      ⑨ Allow / Deny                ⑧  Role Checking

②  Get Token





       ~/.kube/kubeconfig
                                                           Role-Base Access Control

                                                              [ Authorization ]
~~~

### Visual 의미

- 사용자 Action부터 kubeconfig Token, API Server Token Review, aws-auth/IAM·STS 인증, RBAC Role 확인, Allow/Deny까지 1–9 순서의 흐름이다.

## EKS IAM Role for ServiceAccount

## PDF p.197

- 원본: [[40_자료/강의 자료/Kubernetes.pdf#page=197|Kubernetes.pdf p.197]]
- 정보 유형: Text, 도식

### 원자료 내용

~~~text
        Kubernetes         RBAC      ( EKS    Iam    Role    for   Service      Account       )






◎  AWS EKS  IRSA ( Iam  Role for Service  Account )

   K8s 내부  Service Account와 AWS IAM Role을 Mapping하여 K8s 내부에서  AWS Resource를 관리  할  수 있는  권한을   부여한다.
   IRSA를 구현하기    위해서는   K8s를 식별   OIDC(OpenID Connect)가 필요하며,  EKS Cluster 생성 시  함께  생성  ( 콘솔에서   확인   )

   EKS와 다른  AWS Resource를 통합  운영하기위해서는      IRSA 구성이   필요하며,   상황에   따라  EKS 추가기능까지     구성해야   한다.



                                   ③   IAM Role Trust Review



                                                                          ②  IAM Role ARN Review
                  EKS Cluster
                                    ①  JWT & IAM Role ARN
                 OpenID Connect
                                                                            Attach
                                                         AWS IAM
                                                                  IAM Role         IAM Policy
                                                                              ( AWS ALB Management )

                                         ④  Temporary
                                       Cedential Issuing



                            ( K8s Service Account IAM Role Mapping )


    ⑤  AWS ALB Create
~~~

### Visual 의미

- ServiceAccount, EKS OIDC, IAM Role Trust, STS 임시 자격증명과 AWS API 요청의 IRSA 흐름을 번호와 화살표로 표시한다.

## 누락·검토 대기

- 선언한 PDF Page 범위의 Text·YAML·명령·출력·Visual 확인은 완료했다.
- 원자료의 Kubernetes·AWS Version과 기술 내용에 대한 최신 공식 문서 검증은 이 Chapter Digest의 범위 밖이다.
- 전체 Index의 Chapter Link와 전 범위 Gap·Overlap 검증은 Index 갱신 단계에서 수행한다.

## 완료 검증

- [x] PDF p.187–p.197 모든 Page를 포함했다.
- [x] Text Layer와 Rendering을 함께 확인했다.
- [x] YAML·명령·표형 출력의 기호와 배치를 원본과 대조했다.
- [x] 도식·삽입 이미지의 관계를 별도 기록했다.
- [x] 판독 불확실성과 원자료 오류 가능성을 숨기지 않았다.
- [ ] 전체 Source Digest Index 통합 검수와 외부 기술 검증
