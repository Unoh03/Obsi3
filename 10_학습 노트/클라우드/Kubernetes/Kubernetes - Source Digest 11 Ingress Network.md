---
type: source-digest
status: draft
created: 2026-07-21
parent_moc: "[[10_학습 노트/클라우드/Kubernetes/00_Kubernetes MOC]]"
source: "[[40_자료/강의 자료/Kubernetes.pdf]]"
source_pages: "198-212"
digest_role: chapter
digest_index: "[[10_학습 노트/클라우드/Kubernetes/Kubernetes - Source Digest v1]]"
chapter: "11 Ingress Network"
source_hash: F97666865E22749C47640689B5C41DEE38476A40312A53915F60B4F6A4330D24
source_version: "PowerPoint PDF; 266 pages; metadata created 2024-07-18"
coverage_status: partial
extraction_method: "pdfplumber 0.11.9 text extraction + pypdfium2 render visual review"
---

# Kubernetes - Source Digest 11 Ingress Network

> [!purpose]
> `Kubernetes.pdf` p.198–p.212의 의미 있는 정보를 페이지별로 보존한 Chapter Digest이다. 원자료의 기술적 정확성을 현재 지식으로 검증하거나 몰래 교정하지 않는다.

## Source 식별

- 원자료: [[40_자료/강의 자료/Kubernetes.pdf|Kubernetes.pdf]]
- 대상 범위: PDF p.198–p.212
- 전체 원자료: 266 pages
- SHA-256: `F97666865E22749C47640689B5C41DEE38476A40312A53915F60B4F6A4330D24`
- 추출·검수: `pdfplumber 0.11.9` Text Layer + `pypdfium2` Rendering
- Chapter 경계: Ingress·Controller·Helm, AWS Load Balancer Controller, routing·sticky session·TLS

## Coverage

| PDF 범위 | Text | YAML·명령·표 | Visual | 원본 대조 | 상태 |
|---|---|---|---|---|---|
| p.198–p.212 | 완료 | 완료 | 전체 렌더 검토 | 페이지별 대조 | 상세 변환 완료 / 기술 내용 외부 검증 미수행 |

## 변환 경계

- 아래 고정폭 Transcript는 PDF Text Layer의 Page 배치를 최대한 보존한다.
- YAML·명령·출력은 Rendering으로 기호와 배치를 대조했다. 원자료의 오탈자·잠재적 명령 오류는 임의로 수정하지 않는다.
- Visual 관계는 Text Layer 밖의 화살표·번호·공간 배치를 별도 설명한다.
- `status: draft`는 원자료 변환이 누락됐다는 뜻이 아니라, 전체 Index 통합 검수와 외부 기술 검증이 아직 끝나지 않았다는 뜻이다.

## Ingress Network

## PDF p.198

- 원본: [[40_자료/강의 자료/Kubernetes.pdf#page=198|Kubernetes.pdf p.198]]
- 정보 유형: Cover

### 원자료 내용

~~~text
Kubernetes                          Ingress                 Network
~~~

## PDF p.199

- 원본: [[40_자료/강의 자료/Kubernetes.pdf#page=199|Kubernetes.pdf p.199]]
- 정보 유형: Text

### 원자료 내용

~~~text
         Kubernetes         Ingress      Network       Management







◎  Kubernetes  Ingress Network  Management

   외부에서   내부로   유입되는   트래픽을    처리하는    네트워크를    의미하며   Ingress Network를 구현을  위해   Ingress 오브젝트를   사용한다.

   Ingress 오브젝트란   외부에서    K8s 내부로  들어오는    요청에   대한  처리를   어떻게   수행  할 것인지를    결정하는   오브젝트가     된다.

   Ingress 오브젝트는   요청에   대한  처리작업을    Layer 7 기반  트래픽   처리  작업을   수행한다.
   Ingress 오브젝트가   수행하는    외부요청   트랙픽   처리  : 외부  요청   라우팅  처리,   가상  호스트   기반  요청  처리,  SSL/TLS 요청  처리

 >. 외부  요청  라우팅   : "/list, /order" 등의 특정  경로에   대한  요청을   어떠한   서비스로   연결  할  것인지를    결정  한다.

 >. 가상  호스트   기반  요청  : "www", list" 등 서로  다른  호스트   네임에   따른  요청을   어떠한   서비스로   연결  할  것인지를    결정한다.
 >. SSL/TLS 요청 : 보안  연결을   위한  인증서   적용  ( 하나의   Ingress SSL/TLS 구성 vs 다수의   서비스별   SSL/TLS 구성  )


◎  Kubernetes  Ingress Controller


   Ingress Controller는 외부요청을   받아  Ingress 오브젝트에서    정의  된  규칙에   맞게  요청처리를    수행하는    서버를   의미한다.
   Ingress Network를 구현하기  위해서는    Ingress Controller 반드시 필요하며    다양한   Ingress Controller가 존재한다.

   Kong API GW, Nginx Ingress Controller, GKE Ingress Controller, AWS Load Balancer 등 ( 종류에 따라 기능의 차이가 존재  )

   TEST EKS 환경에서는   Helm을 이용하여    AWS Load Balancer Controller를 구성 후 Ingress Network Test를 진행한다.
~~~

## PDF p.200

- 원본: [[40_자료/강의 자료/Kubernetes.pdf#page=200|Kubernetes.pdf p.200]]
- 정보 유형: Text, 도식

### 원자료 내용

~~~text
         Kubernetes         Ingress      Network       Management






◎  Kubernetes  Ingress Network를   사용하는     이유

   서로  다른  서비스를    구성하는   Deployment 오브젝트가   다수   배포되어있을    경우   해당  Deployment 별 서비스  오브젝트를     연결해야   한다.

   클라이언트는    서비스   오브젝트별    Port 번호  혹은  External IP를 전부  기억하고    있어야   외부에서   접근이   가능하다.
   보안  연결  작업  시  각 서비스   오브젝트마다     SSL/TLS 구성을  전부   따로  해주어야하며,    인증서   관리작업에     어려움이   많아지게    된다.

   Ingress 오브젝트를   이용하여    클라이언트에게     단일  엔드포인트를     제공하고    해당  단일  엔드포인트로만      접근하도록    구성한다.

   단일  엔드포인트로     들어오는   외부요청에    처리규칙을     정의하여   적절한   서비스와   연결해주는     Service Discovery를 구현 할  수 있다.
   단일  엔드포인트가     구성  될 경우   해당  엔드포인트에     대한  SSL/TLS 보안연결   작업만   수행하면된다.


                                         Kubernetes   Cluster
        External  Network



                                                                                             List
                                                                                              App
                              SSL/TLS


              Client
                                             ALB Ingress
                                             Controller
                                                                                            Order
 [ URL: www.example.com/list    ]
                                                                                              App
 [ URL: www.example.com/order   ]
~~~

### Visual 의미

- 외부 Client가 SSL/TLS로 ALB Ingress Controller에 접근하고 List/Order App으로 경로 기반 분기되는 구조이다.

## PDF p.201

- 원본: [[40_자료/강의 자료/Kubernetes.pdf#page=201|Kubernetes.pdf p.201]]
- 정보 유형: Text, 도식, 삽입 이미지

### 원자료 내용

~~~text
Kubernetes         Ingress      Network       Management









    AWS Elastic
 Kubernetes Service









    AWS Elastic
   Load Balancing
~~~

### Visual 의미

- ALB Controller가 API Server 변화를 감시하고 Listener·Rule·TargetGroup을 구성해 NodePort/Pod로 전달하는 1–5단계 구조이다. 이 페이지는 의미 대부분이 도식에 있다.

### 판독 불확실성

- Text Layer는 도식의 일부 Label만 추출하므로 화살표·번호·색상 관계는 Rendering을 기준으로 기록했다.

## PDF p.202

- 원본: [[40_자료/강의 자료/Kubernetes.pdf#page=202|Kubernetes.pdf p.202]]
- 정보 유형: Text, 도식

### 원자료 내용

~~~text
         Kubernetes         Ingress      Network       Management






◎  Kubernetes  Package Manager  HELM

   Helm : Kubernetes Package Manager ( Linux OS: Package Manager와 동일한 역할 )

   Helm은 Kubernetes Cluster에서 배포되는   Application을 Chart(패키지)  형태로   제공한다.
   Chart 내부에는   Application이 가동되기   위한  모든  Resource를 포함하고    있다.  ( Deploy / ConfigMAP / Secret / Service )

   Helm은 Revision 관리를  진행하며   동일한   Chart를 여러번   설치가   가능하며,    각 설치  작업을   Revision 정보로  관리한다.



         Helm  Chart
                                                Kubernetes   Cluster   ( K8s  )








                                Helm

                               Command




       Helm Repository
~~~

### Visual 의미

- Helm Repository의 Chart와 YAML 묶음이 Helm Command를 거쳐 Kubernetes Cluster에 배포되는 관계를 나타낸다.

## Helm 및 AWS Load Balancer Controller 설치

## PDF p.203

- 원본: [[40_자료/강의 자료/Kubernetes.pdf#page=203|Kubernetes.pdf p.203]]
- 정보 유형: Text, 명령/출력

### 명령·출력

~~~text
           Kubernetes         Ingress      Network       Management






▣  [ Helm Install  ]

$ curl -fsSL  -o ~/get_helm.sh  https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3

$ chmod 700  ~/get_helm.sh

$ ~/get_helm.sh

Downloading https://get.helm.sh/helm-v3.9.1-linux-amd64.tar.gz
Verifying checksum... Done.

Preparing to install helm into /usr/local/bin

helm installed into /usr/local/bin/helm

▣ Helm을 설치를   위해 Curl 명령어를   이용해  Helm 공식 Git-Hub 저장소에  저장되어있는    Helm Install Script를 내려받는다.

▣ 내려받은   Helm Install Script에 실행 권한을  부여하고  "get_heml.sh" Shell Script 파일을 실행하여  설치  작업을  완료한다.
▣ Helm Install 완료 시 Helm Command가 BastionHost System에 구성되며 "heml" 명령어를  사용  할 수  있다.

▣ Helm Install 시 작업 Directory는 어떠한  곳이든  상관없다.   ( "~/kube" Directory에서 Helm Install 작업을 수행 )

$ chmod go-r  ~/.kube/config

$ helm version

version.BuildInfo{Version:"v3.12.3", GitCommit:"3a31588ad33fae6eaa5e", GitTreeState:"clean", GoVersion:"go1.20.7"}

▣ Helm Install 완료 후 helm 명령어를   이용하여  설치  된 Helm의  버전정보를   확인한다.
~~~

## PDF p.204

- 원본: [[40_자료/강의 자료/Kubernetes.pdf#page=204|Kubernetes.pdf p.204]]
- 정보 유형: Text, 명령/출력

### 명령·출력

~~~text
           Kubernetes         Ingress      Network       Management






▣  [ AWS Load Balancer  Controller  구성  ( Helm  Install ) ]

$ helm repo  add eks https://aws.github.io/eks-charts

$ helm repo  update eks

$ helm install  aws-load-balancer-controller   eks/aws-load-balancer-controller   \

-n kube-system  \

--set clusterName=my-eks   \

--set serviceAccount.create=false   \
--set serviceAccount.name=aws-load-balancer-controller


$ kubectl  get deployment  -n kube-system  aws-load-balancer-controller

NAME                        READY   UP-TO-DATE AVAILABLE  AGE

aws-load-balancer-controller 2/2    2          2          24s


▣ AWS Load Balancer Controller Install을 위한 EKS Repo 등록 및 업데이트
▣ "-n kube-system" : AWS Load Balancer Controller Pod 생성 NameSpace

▣ "--set clusterName=my-eks" : EKS Cluster Name

▣ "--set serviceAccount.create=false" : Service Account는 위에서 생성했으므로 False 정의
▣ "--set serviceAccount.name=aws-load-balancer-controller" : 위에서 생성한 EKS Service Account 이름 입력
~~~

## EX.1 Basic Ingress

## PDF p.205

- 원본: [[40_자료/강의 자료/Kubernetes.pdf#page=205|Kubernetes.pdf p.205]]
- 정보 유형: Text, YAML/설정

### YAML·설정

~~~text
           Kubernetes         Ingress      Network       Management            (  EX.1    : Basic    )






<작업대상:    ingress-singlehost.yml  >                               rules: # Ingress Routing Rule 정의
                                                                  - http:
apiVersion: networking.k8s.io/v1
                                                                     paths:
kind: Ingress       # Ingress API Version 정의
                                                                     - pathType: Prefix
metadata:           # Resource 종류 : Ingress 오브젝트
                                                                       path: /list
  name: my-ingress                                                                      # Client URI "/list" 요청
                                                                       backend:
  namespace: delivery                                                                   # list-svc 서비스와  연결
                                                                         service:
  annotations:
                                                                           name: list-svc
    kubernetes.io/ingress.class: alb
                                                                           port:
    alb.ingress.kubernetes.io/load-balancer-name: my-eks-alb
                                                                             number: 80
    alb.ingress.kubernetes.io/scheme: internet-facing
                                                                     - pathType: Prefix
    alb.ingress.kubernetes.io/target-type: instance
                                                                       path: /order
spec:                                                                                   # Client URI "/order" 요청
                                                                       backend:
  defaultBackend: # Default 값으로 연결  할 서비스  오브젝트   정의                                    # order-svc 서비스와 연결
                                                                         service:
    service:
                                                                           name: order-svc
     name: list-svc
                                                                           port:
     port:
                                                                             number: 80
       number: 80
~~~

### Visual 의미

- 여러 열에 배치된 Manifest·설명은 Text Layer의 선형 순서만으로 읽지 않는다. Rendering의 좌→우 배치, 들여쓰기와 연결선을 함께 기준으로 한다.

## PDF p.206

- 원본: [[40_자료/강의 자료/Kubernetes.pdf#page=206|Kubernetes.pdf p.206]]
- 정보 유형: Text, 명령/출력

### 명령·출력

~~~text
           Kubernetes         Ingress      Network       Management            (  EX.1    : Basic    )






$ kubectl  apply -f ingress/ingress-singlehost.yml

ingress.networking.k8s.io/my-ingress created

$ kubectl  get ingress -n  delivery

NAME        CLASS   HOSTS  ADDRESS               PORTS   AGE

my-ingress  <none>  *      k8s-delivery-myingres 80      43s

$ cp ~/kube/service/svc-nodeport-list.yml    ~/kube/ingress

$ cp ~/kube/service/svc-nodeport-order.yml    ~/kube/ingress


$ kubectl  apply -f ingress/svc-nodeport-list.yml

service/list-svc created
deployment.apps/list-deploy created


$ kubectl  apply -f ingress/svc-nodeport-order.yml

service/order-svc created
deployment.apps/order-deploy created

▣ Ingress Controller와 연결 할 Service 오브젝트  및  Deployment 오브젝트를  생성한다.

▣ Service 오브젝트와   Deployment 오브젝트는  Service 오브젝트  TEST에서 사용  한  Manifest File을 그대로 사용한다.
~~~

## PDF p.207

- 원본: [[40_자료/강의 자료/Kubernetes.pdf#page=207|Kubernetes.pdf p.207]]
- 정보 유형: Text, 명령/출력, 표형 정보

### 명령·출력

~~~text
           Kubernetes         Ingress      Network       Management            (  EX.1    : Basic    )






$ kubectl  get pod,svc -o  wide -n delivery

NAME                             READY  STATUS   RESTARTS  AGE   IP             NODE    NOMINATED  READINESS
pod/list-deploy-549c9bbb7-85s5x  1/1    Running  0         14s   192.168.10.14  node-1   <none>     <none>

pod/list-deploy-549c9bbb7-jh4dc  1/1    Running  0         14s   192.168.20.117 node-2   <none>     <none>

pod/order-deploy-7d6794d495-8d9md 1/1   Running  0         10s   192.168.10.187 node-2   <none>     <none>
pod/order-deploy-7d6794d495-zq8nb 1/1   Running  0         10s   192.168.20.130 node-1   <none>     <none>


NAME              TYPE       CLUSTER-IP      EXTERNAL-IP PORT(S)   AGE  SELECTOR
service/list-svc  ClusterIP  10.100.180.147  <none>      80/TCP    14s  app=list-app

service/order-svc ClusterIP  10.100.119.139  <none>      80/TCP    10s  app=order-app


$ kubectl  get endpoints  -n delivery
NAME       ENDPOINTS                             AGE

list-svc   192.168.10.14:8000,192.168.20.117:8000 28s

order-svc  192.168.10.187:8000,192.168.20.130:8000 24s

▣ Ingress 오브젝트에서   list-svc, order-svc 연결 규칙을  미리 정의  한  상태이며  각  Service 오브젝트에  연결되는   Endpoints 정보를 확인

▣ 로컬  PC에서  접속  테스트  [ http://alb-dns-name, http://alb-dns-name/list, / http://alb-dns-name/order ]

$ kubectl  delete -f ./ingress-singlehost.yml

ingress.networking.k8s.io "my-ingress" deleted
~~~

## PDF p.208

- 원본: [[40_자료/강의 자료/Kubernetes.pdf#page=208|Kubernetes.pdf p.208]]
- 정보 유형: Text, YAML/설정

### YAML·설정

~~~text
           Kubernetes         Ingress      Network       Management            (  EX.1    : Basic    )



                                                                  rules: # Ingress Routing Rule 정의 (가상 호스트  기반  )
<작업대상:    ingress-virtualhost.yml  >
                                                                  - host: list.mydevsecops.link
apiVersion: networking.k8s.io/v1                                    http:
                                                                                        # "list.mydevsecops.link"
kind: Ingress                                                        paths:
                                                                                        # list-svc 서비스와  연결
metadata:                                                            - pathType: Prefix
                    # Ingress API Version 정의
  name: my-ingress                                                     path: /
                    # Resource 종류 : Ingress 오브젝트
  namespace: delivery                                                  backend:
  annotations:                                                           service:
    kubernetes.io/ingress.class: alb                                       name: list-svc

    alb.ingress.kubernetes.io/load-balancer-name: my-eks-alb               port:

    alb.ingress.kubernetes.io/scheme: internet-facing                        number: 80
    alb.ingress.kubernetes.io/target-type: instance               - host: order.mydevsecops.link

    external-dns.alpha.kubernetes.io/hostname: mydevsecops.link     http:
                                                                                          # "order.mydevsecops.link"
spec:                                                                paths:
                                                                                          # order-svc 서비스와 연결
  defaultBackend:                                                    - pathType: Prefix
    service:        # Default 값으로 연결  할 서비스  오브젝트   정의                 path: /

     name: list-svc                                                    backend:
     port:                                                               service:

       number: 80                                                          name: order-svc

                                                                           port:
                                                                             number: 80
~~~

### Visual 의미

- 여러 열에 배치된 Manifest·설명은 Text Layer의 선형 순서만으로 읽지 않는다. Rendering의 좌→우 배치, 들여쓰기와 연결선을 함께 기준으로 한다.

## PDF p.209

- 원본: [[40_자료/강의 자료/Kubernetes.pdf#page=209|Kubernetes.pdf p.209]]
- 정보 유형: Text, 명령/출력

### 명령·출력

~~~text
           Kubernetes         Ingress      Network       Management            (  EX.1    : Basic    )






$ kubectl  apply -f ingress/ingress-virtualhost.yml

$ kubectl  get ingress -n  delivery

NAME        CLASS   HOSTS                                      ADDRESS            PORTS  AGE
my-ingress  <none>  list.mydevsecops.link,order.mydevsecops.link elb.amazonaws.com 80    14s


▣ [ 로컬  PC Web Browser (Chrome) 접속 테스트 ]
-. http://mydevsecops.link              [ list Main Page ]

-. http://list.mydevsecops.link         [ list Main Page ]

-. http://list.mydevsecops.link/list    [ list Menu Page ]
-. http://order.mydevsecops.link        [ order Main Page ]

-. http://order.mydevsecops.link/order  [ order Menu Page ]

▣ 접속  정보가  출력되는   Page에서  새로고침  작업을  통해  접속되는   Pod 오브젝트가   달라지는   것을 확인한다.   ( Session 유지 TEST )

▣ Ingress 오브젝트를   이용  한 Session 유지 작업을  정의하기위해서는     Ingress Controller Session Affinity 설정을 진행해야한다.

▣ Ingress Controller는 Service 오브젝트가  연결하고있는   Pod 오브젝트의   Endpoints 정보만 참조하여   직접  Pod 오브젝트에   접근한다.

$ kubectl  delete -f ingress/svc-nodeport-list.yml

$ kubectl  delete -f ingress/svc-nodeport-order.yml


▣ 다음  테스트를   위해  테스트에  사용한   오브젝트를   삭제한다.
~~~

## PDF p.210

- 원본: [[40_자료/강의 자료/Kubernetes.pdf#page=210|Kubernetes.pdf p.210]]
- 정보 유형: Text, YAML/설정, 명령/출력

### YAML·설정 및 명령·출력

~~~text
           Kubernetes         Ingress      Network       Management            (  EX.1    : Basic    )






▣  [ AWS Load Balancer  Controller  Sticky Session  TEST ]


$ kubectl  edit ingress my-ingress  -n delivery
annotations:

  kubernetes.io/ingress.class: alb

  alb.ingress.kubernetes.io/load-balancer-name: my-eks-alb
  alb.ingress.kubernetes.io/scheme: internet-facing

  alb.ingress.kubernetes.io/target-type: ip

  alb.ingress.kubernetes.io/target-group-attributes: stickiness.enabled=true,stickiness.lb_cookie.duration_seconds=300
  external-dns.alpha.kubernetes.io/hostname: mydevsecops.link


$ kubectl  apply -f ingress/svc-clusterip-list.yml

$ kubectl  apply -f ingress/svc-clusterip-order.yml

▣ AWS Load Balancer Controller에서 Sticky Session 기능을 활용하여 Clinet의 Session을 유지하도록   Annotations를 수정

▣ Sticky Session 기능을 사용하기위해    Target Type을 IP로 변경하고,  Pod와 연결되는   Service의 Type 또한 Cluster-IP 형식으로  변경한다.

▣ 로컬  PC Web Browser에서 (list or order) 접속 테스트를  진행하여   Session 유지기능이  정상적으로   동작하는지   확인한다.

$ kubectl  delete -f ingress/ingress-virtualhost.yml

▣ 다음  TEST를 위해  Ingress 오브젝트를  삭제한다.
~~~

## PDF p.211

- 원본: [[40_자료/강의 자료/Kubernetes.pdf#page=211|Kubernetes.pdf p.211]]
- 정보 유형: Text, YAML/설정

### YAML·설정

~~~text
           Kubernetes         Ingress      Network       Management            (  EX.1    : Basic    )






▣  [ AWS Load Balancer  Controller  SSL/TLS(ACM)  TEST ]          rules: # Ingress Routing Rule 정의
                                                                   - http:
<작업대상:    ingress-tls.yml  >
                                                                       paths:

                                                                       - pathType: Prefix
metadata:
                      # Ingress Object의 전체 Manifast File 내용은             path: /list
  name: my-ingress
                                                                                          # Client URI "/list" 요청
                        TXT 교안을  참고하여  작성                                backend:
  namespace: delivery
                                                                                          # list-svc 서비스와  연결
                                                                           service:
  annotations:
                                                                            name: list-svc
    kubernetes.io/ingress.class: alb
                                                                            port:
    alb.ingress.kubernetes.io/load-balancer-name: my-eks-alb
                                                                              number: 80
    alb.ingress.kubernetes.io/scheme: internet-facing
                                                                       - pathType: Prefix
    alb.ingress.kubernetes.io/target-type: ip
                                                                         path: /order
    external-dns.alpha.kubernetes.io/hostname: www.mydevsecops.link
                                                                                         # Client URI "/order" 요청
                                                                         backend:
    alb.ingress.kubernetes.io/listen-ports: '[{"HTTP": 80},
                                                                                         # order-svc 서비스와  연결
                                                                           service:
    {"HTTPS":443}]'
                                                                            name: order-svc
    alb.ingress.kubernetes.io/certificate-arn: "ACM ARN"
                                                                            port:
    alb.ingress.kubernetes.io/actions.ssl-redirect:
                                                                              number: 80
    '{"Type": "redirect", "RedirectConfig": { "Protocol": "HTTPS",
     "Port": "443", "StatusCode": "HTTP_301"}}'
~~~

### Visual 의미

- 여러 열에 배치된 Manifest·설명은 Text Layer의 선형 순서만으로 읽지 않는다. Rendering의 좌→우 배치, 들여쓰기와 연결선을 함께 기준으로 한다.

## PDF p.212

- 원본: [[40_자료/강의 자료/Kubernetes.pdf#page=212|Kubernetes.pdf p.212]]
- 정보 유형: Text, 명령/출력

### 명령·출력

~~~text
           Kubernetes         Ingress      Network       Management            (  EX.1    : Basic    )






$ kubectl  apply -f ingress/ingress-tls.yml

ingress.networking.k8s.io/my-ingress created

$ kubectl  get ingress -n  delivery

NAME        CLASS   HOSTS           ADDRESS            PORTS    AGE

my-ingress  <none>  *               elb.amazonaws.com  80       8s

▣ [ 로컬  PC Web Browser 접속 테스트  ]

-. http://www.mydevsecops.link           [ list Main Page ]
-. http://www.mydevsecops.link/list      [ list Menu Page ]

-. http://www.mydevsecops.link/order     [ order Menu Page ]

▣ http 프로토콜을   이용한  접속  시 자동으로   https Redirect가 진행되는  것을  확인한다.


$ kubectl  delete -f ingress/ingress-tls.yml

$ kubectl  delete -f ingress/svc-clusterip-list.yml

$ kubectl  delete -f ingress/svc-clusterip-order.yml


▣ 다음  TEST를 위해  Ingress TEST에서 사용  한 Ingress, Service, Deployment 오브젝트를 삭제한다.
~~~

## 누락·검토 대기

- 선언한 PDF Page 범위의 Text·YAML·명령·출력·Visual 확인은 완료했다.
- 원자료의 Kubernetes·AWS Version과 기술 내용에 대한 최신 공식 문서 검증은 이 Chapter Digest의 범위 밖이다.
- 전체 Index의 Chapter Link와 전 범위 Gap·Overlap 검증은 Index 갱신 단계에서 수행한다.

## 완료 검증

- [x] PDF p.198–p.212 모든 Page를 포함했다.
- [x] Text Layer와 Rendering을 함께 확인했다.
- [x] YAML·명령·표형 출력의 기호와 배치를 원본과 대조했다.
- [x] 도식·삽입 이미지의 관계를 별도 기록했다.
- [x] 판독 불확실성과 원자료 오류 가능성을 숨기지 않았다.
- [ ] 전체 Source Digest Index 통합 검수와 외부 기술 검증
