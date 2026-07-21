---
type: source-digest
status: draft
created: 2026-07-21
parent_moc: "[[10_학습 노트/클라우드/Kubernetes/00_Kubernetes MOC]]"
source: "[[40_자료/강의 자료/Kubernetes.pdf]]"
source_pages: "172-186"
digest_role: chapter
digest_index: "[[10_학습 노트/클라우드/Kubernetes/Kubernetes - Source Digest v1]]"
chapter: "09 Resource Management"
source_hash: F97666865E22749C47640689B5C41DEE38476A40312A53915F60B4F6A4330D24
source_version: "PowerPoint PDF; 266 pages; metadata created 2024-07-18"
coverage_status: partial
extraction_method: "pdfplumber 0.11.9 text extraction + pypdfium2 render visual review"
---

# Kubernetes - Source Digest 09 Resource Management

> [!purpose]
> `Kubernetes.pdf` p.172–p.186의 의미 있는 정보를 페이지별로 보존한 Chapter Digest이다. 원자료의 기술적 정확성을 현재 지식으로 검증하거나 몰래 교정하지 않는다.

## Source 식별

- 원자료: [[40_자료/강의 자료/Kubernetes.pdf|Kubernetes.pdf]]
- 대상 범위: PDF p.172–p.186
- 전체 원자료: 266 pages
- SHA-256: `F97666865E22749C47640689B5C41DEE38476A40312A53915F60B4F6A4330D24`
- 추출·검수: `pdfplumber 0.11.9` Text Layer + `pypdfium2` Rendering
- Chapter 경계: Resource 개념·OOM·QoS, Limit/Request, ResourceQuota·LimitRange

## Coverage

| PDF 범위 | Text | YAML·명령·표 | Visual | 원본 대조 | 상태 |
|---|---|---|---|---|---|
| p.172–p.186 | 완료 | 완료 | 전체 렌더 검토 | 페이지별 대조 | 상세 변환 완료 / 기술 내용 외부 검증 미수행 |

## 변환 경계

- 아래 고정폭 Transcript는 PDF Text Layer의 Page 배치를 최대한 보존한다.
- YAML·명령·출력은 Rendering으로 기호와 배치를 대조했다. 원자료의 오탈자·잠재적 명령 오류는 임의로 수정하지 않는다.
- Visual 관계는 Text Layer 밖의 화살표·번호·공간 배치를 별도 설명한다.
- `status: draft`는 원자료 변환이 누락됐다는 뜻이 아니라, 전체 Index 통합 검수와 외부 기술 검증이 아직 끝나지 않았다는 뜻이다.

## Resource Management

## PDF p.172

- 원본: [[40_자료/강의 자료/Kubernetes.pdf#page=172|Kubernetes.pdf p.172]]
- 정보 유형: Cover

### 원자료 내용

~~~text
Kubernetes                          Resource                     Management
~~~

## PDF p.173

- 원본: [[40_자료/강의 자료/Kubernetes.pdf#page=173|Kubernetes.pdf p.173]]
- 정보 유형: Text

### 원자료 내용

~~~text
         Kubernetes         Resource        Management






◎  Kubernetes  Resource Management

   Kubernetes는 Cluster를 구성하는   여러대의   서버의   컴퓨팅   자원(CPU,RAM)을  하나로   묶어  Resource Pool로 사용  할  수 있다.

   Kubernetes에서는  Cluster 내부에  생성되는   컨테이너의    컴퓨팅   자원   사용량  제한을   통해   효과적인   컴퓨팅   자원  사용이   가능하다.
   Kubernetes에서는  자원  사용량   제한을   Pod 단위로  제어하며    Request, Limit을 이용하여   컴퓨팅  자원   사용량을   제한한다.

   Request는 컨테이너가    최소한으로    보장받아야하는     자원   사용량을   정의하며,    Pod가 생성  될  Node를 선택하는   기준이   된다.

   Request에서 정의  된  최소한의    자원  사용량을   충족  시킬   수 없는   Node에서는  Pod가 생성되지    않는다.
   OverCommit은 컨테이너가   Request에 정의   된 자원  사용량을    넘어서는   자원을   사용하고    상태를   의미한다.

   Limit은 컨테이너가    최대로   사용  할  수 있는  자원   사용량을   정의하며,    OverCommit의 실질적인   제한값으로    사용된다.


◎  Kubernetes  Resource OverCommit  EX

   Node-1에서 현재  사용가능    한  물리  메모리   용량  1000M

   A 컨테이너   : Request (500M) / Limit ( 700M ) / B 컨테이너 : Request (300M) / Limit ( 500M )

   A 컨테이너,   B 컨테이너를    시작  후  Node-1에 남은  메모리용량    : 200M
   A 컨테이너에서    추가  메모리   할당이   필요한   경우  남은   메모리용량    내에서   최대  Limit까지  추가  메모리   할당  ( OverCommit )

   B 컨테이너에서도     추가  메모리   할당이   필요한   경우  메모리   점유  경합이   발생한다.   ( Out Of Memory 처리 진행  )

※  OverCommit을 사용하지   않을경우   OOM 처리  문제가   발생하지    않아  OverCommit을 사용하는   환경보다    안정적인   운영이   가능하다.

※  CPU 사용률  경합의   경우  컨테이너    자체적으로    CPU 사용률을   낮추는   처리를   진행하여   우선순위    비교작업을    수행하지    않는다.
~~~

## PDF p.174

- 원본: [[40_자료/강의 자료/Kubernetes.pdf#page=174|Kubernetes.pdf p.174]]
- 정보 유형: Text, 표형 정보, 도식

### 원자료 내용

~~~text
         Kubernetes         Resource        Management






◎  Kubernetes  OOM (Out Of  Memory)

   Kubernetes OOM 처리는 Pod의 우선순위를     비교하여   우선  순위가   낮은  Pod를  종료  후  다른  Node로 이동시킨다.

   Pod의 우선순위를    비교하기    위해  Kubernetes는 3가지  QOS 클래스를   사용  한다.  ( Guaranteed / BestEffort / Burstable )
   Guaranteed : Limit, Request 값이 동일하게  설정  된  경우  적용  ( OverCommit 사용 안  함 )

   BestEffort : Limit, Request 값이 설정되지  않은  경우  적용   ( Container Resource 정의가 없는  경우  )

   Burstable : Limit, Request 값이 다르게  설정  된  경우  적용  ( OverCommit 사용  )
   우선순위   : 1순위(Guaranteed), 2순위(Burstable or BestEffort), 3순위(Burstable or BestEffort)

   Burstable과 BestEffort의 경합의  경우  메모리   사용량이    더 많은  파드가   우선순위가    낮아진다.
~~~

### Visual 의미

- BestEffort·Burstable·Guaranteed 세 QoS Class를 Request/Limit 메모리 막대로 비교하고, 아래 화살표로 reclamation 후보 방향을 표시한다.

## EX.1 Limit & Request

## PDF p.175

- 원본: [[40_자료/강의 자료/Kubernetes.pdf#page=175|Kubernetes.pdf p.175]]
- 정보 유형: Text, 명령/출력, 표형 정보

### 명령·출력

~~~text
           Kubernetes         Resource        Management            ( EX.1:    Limit    &   Request       )






$ kubectl  label node ip-192-168-10-147.ap-northeast-2.compute.internal     resource=node-1

$ kubectl  get node -L resource

NAME                                           STATUS   ROLES   AGE   VERSION              RESOURCE
ip-192-168-10-147.ap-northeast-2.compute.internal Ready <none>  2d4h  v1.24.16-eks-8ccc7ba node-1

ip-192-168-20-156.ap-northeast-2.compute.internal Ready <none>  2d4h  v1.24.16-eks-8ccc7ba

$ kubectl  describe nodes  ip-192-168-10-147.ap-northeast-2.compute.internal

Conditions:

  Type               Status LastHeartbeatTime LastTransitionTime Reason

  ----               ------ ----------------- ------------------ ------
  MemoryPressure     False  Fri,              Wed,              KubeletHasSufficientMemory


Allocated resources:
  Resource         Requests   Limits

  --------         --------   ------

  cpu              125m (6%) 0 (0%)
  memory           0 (0%)    0 (0%)


▣ Node-1의 상세정보를   확인한다.   ( Conditions 영역, Allocated resources 영역)
▣ MemoryPressure의 상태가  True로 변경  될 경우  OOM 처리를  진행한다.  ( Node의 가용  메모리  공간이  100Mi 이하일  때  True로 변경 )
~~~

## PDF p.176

- 원본: [[40_자료/강의 자료/Kubernetes.pdf#page=176|Kubernetes.pdf p.176]]
- 정보 유형: Text, YAML/설정

### YAML·설정

~~~text
           Kubernetes         Resource        Management            ( EX.1:    Limit    &   Request       )






< 작업대상:    resource-limit-request.yml   >

spec:

  nodeSelector:               ※ [ Pod 오브젝트  전체  내용은   TXT 교안을 참조  ]

    resource: node-1
  containers:

  - name: res-con

    image: chlzzz/kube-image:debug
    command: ['sh', '-c', 'echo The app is running! && sleep 3600']

    resources:                # Pod의 Resource 제한 정의 영역

     limits:                  # Limit 속성 정의  ( Memory, CPU 자원 최대 사용량  )
       memory: "500Mi"        # Memory 최대 사용  : 500M

       cpu: "500m"            # CPU 최대 사용  : 0.5 코어

     requests:                # Request 속성 정의 ( Memory, CPU 자원 최소  사용량  ) / 생략  할 경우  Limit 값이 자동  설정
       memory: "500Mi"        # Memory 최소 사용  : 500M

       cpu: "500m"            # CPU 최소 사용  : 0.5 코어

▣ Pod는 nodeSelector에의해  node-1에서 생성  되며  컨테이너는   최소 500Mi 메모리와   0.5코어의  사용을  보장받는다.   ( Request )

▣ 현재  Request와 Limit의 값이  동일하므로   Guaranteed QOS 클래스가 지정된다.   ( Request와 Limit이 동일 할 경우  Request는 생략가능   )

▣ CPU 제한시  제어  단위는  밀리코어(M)   단위를  사용한다.   ( 1코어 = 1000M )
~~~

## PDF p.177

- 원본: [[40_자료/강의 자료/Kubernetes.pdf#page=177|Kubernetes.pdf p.177]]
- 정보 유형: Text, 명령/출력, 표형 정보

### 명령·출력

~~~text
           Kubernetes         Resource        Management            ( EX.1:    Limit    &   Request       )






$ kubectl  apply -f resources/resource-limit-request.yml

pod/res-pod created

$ kubectl  get pod -n delivery  -o wide

NAME     READY  STATUS   RESTARTS   AGE   IP             NODE    NOMINATED NODE READINESS GATES

res-pod  1/1    Running  0          2m8s  192.168.10.156 node-1  <none>         <none>

$ kubectl  describe pod res-pod  -n delivery

Containers:

    Limits:
     cpu:     500m

     memory:  500Mi

    Requests:
     cpu:     500m

     memory:  500Mi

QoS Class:     Guaranteed


▣ Pod의 상세정보를    확인한다.  ( Limits 영역, Requests 영역 )
~~~

## PDF p.178

- 원본: [[40_자료/강의 자료/Kubernetes.pdf#page=178|Kubernetes.pdf p.178]]
- 정보 유형: Text, 명령/출력, 표형 정보

### 명령·출력

~~~text
           Kubernetes         Resource        Management            ( EX.1:    Limit    &   Request       )






$ kubectl  describe nodes  ip-192-168-10-147.ap-northeast-2.compute.internal

Non-terminated Pods:
  Namespace    Name      CPU Requests CPU Limits Memory Requests Memory Limits AGE

  ---------    ----      ------------ ---------- --------------- ------------- ---

  delivery     res-pod   500m (50%)   500m (50%) 500Mi (7%)      500Mi (7%)   4m26s

Allocated resources:

  (Total limits may be over 100 percent, i.e., overcommitted.)
  Resource                 Requests    Limits

  --------                 --------    ------

  cpu                      625m (60%)  500m (60%)
  memory                   550Mi (7%)  500Mi (7%)

  ephemeral-storage        0 (0%)     0 (0%)

  hugepages-1Gi            0 (0%)     0 (0%)
  hugepages-2Mi            0 (0%)     0 (0%)

  attachable-volumes-aws-ebs 0        0

▣ Node-1의 상세정보를   확인한다.   ( Non-terminated Pods영역, Allocated resources 영역)

▣ 새롭게   생성 된  Pod의 자원  사용 현황이   Request에 정의 된  값 만큼  사용되고있는   것을  확인한다.
~~~

## PDF p.179

- 원본: [[40_자료/강의 자료/Kubernetes.pdf#page=179|Kubernetes.pdf p.179]]
- 정보 유형: Text, YAML/설정

### YAML·설정

~~~text
           Kubernetes         Resource        Management            ( EX.1:    Limit    &   Request       )






< 작업대상:    resource-overpod.yml  >

spec:

  nodeSelector:               ※ [ Pod 오브젝트  전체  내용은   TXT 교안을 참조  ]

    resource: node-1
  containers:

  - name: res-con

    image: chlzzz/kube-image:debug
    command: ['sh', '-c', 'echo The app is running! && sleep 3600']

    resources:                # Pod의 Resource 제한 정의 영역

     limits:                  # Limit 속성 정의  ( Memory, CPU 자원 최대 사용량  )
       memory: "500Mi"        # Memory 최대 사용  : 500M

       cpu: "2000m"           # CPU 최대 사용  : 2 코어

     requests:                # Request 속성 정의 ( Memory, CPU 자원 최소  사용량  ) / 생략  할 경우  Limit 값이 자동  설정
       memory: "500Mi"        # Memory 최소 사용  : 500M

       cpu: "2000m"           # CPU 최소 사용  : 2 코어


▣ node-1 에서 보장할   수 없는  Resource 요청을 갖는  Pod 생성을  정의한다.   ( TEST Pod )

▣ Pod는 nodeSelector에의해  node-1에서 생성  되며  컨테이너는   최소 500Mi 메모리와   2코어의  사용을  보장받는다.   ( Request )
~~~

## PDF p.180

- 원본: [[40_자료/강의 자료/Kubernetes.pdf#page=180|Kubernetes.pdf p.180]]
- 정보 유형: Text, 명령/출력, 표형 정보

### 명령·출력

~~~text
           Kubernetes         Resource        Management            ( EX.1:    Limit    &   Request       )






$ kubectl  apply -f resources/resource-overpod.yml

pod/over-pod created

$ kubectl  get pod -o wide

NAME      READY  STATUS   RESTARTS  AGE     IP      NODE    NOMINATED NODE  READINESS GATES

over-pod  0/1    Pending  0         2m24s   <none>  <none>  <none>          <none>


$ kubectl  describe pod over-pod

Events:
  Type    Reason          Age   From             Message

  ----    ------          ----  ----             -------

  Warning FailedScheduling 90s  default-scheduler 0/2 nodes are available: 1 Insufficient cpu, 1 node(s)
                                                 didn't match Pod's node affinity/selector. preemption: 0/2 nodes

                                                 are available: 1 No preemption victims found for incoming pod,

                                                 1 Preemption is not helpful for scheduling.

▣ 최소  500Mi 메모리와  0.5코어의  사용을   보장하는  새로운  Pod를  node-1을 선택하여  추가로  생성한다.   ( default NameSpace )

▣ 현재  node-1의 경우  최소  500Mi 메모리와  0.5코어의  사용을  보장  할 수  없으므로  해당  파드는  Pending 상태가  지속된다.
~~~

## PDF p.181

- 원본: [[40_자료/강의 자료/Kubernetes.pdf#page=181|Kubernetes.pdf p.181]]
- 정보 유형: Text, 명령/출력, 표형 정보

### 명령·출력

~~~text
           Kubernetes         Resource        Management            ( EX.1:    Limit    &   Request       )






$ kubectl  delete pod over-pod

pod "over-pod" deleted

$ kubectl  delete pod res-pod  -n delivery

pod "res-pod" deleted

$ kubectl  describe nodes  node-1

Allocated resources:

  (Total limits may be over 100 percent, i.e., overcommitted.)

  Resource                 Requests  Limits
  --------                 --------  ------

  cpu                      100m (10%) 100m (10%)

  memory                   50Mi (5%) 50Mi (5%)
  ephemeral-storage        0 (0%)    0 (0%)

  hugepages-1Gi            0 (0%)    0 (0%)

  hugepages-2Mi            0 (0%)    0 (0%)
  attachable-volumes-aws-ebs 0       0


▣ 다음  테스트를   위하여  Pod 오브젝트를   삭제  후 Node-1의 자원  사용  현황을  확인한다.  ( Allocated Resources 영역 )
~~~

## EX.2 Quota & Range

## PDF p.182

- 원본: [[40_자료/강의 자료/Kubernetes.pdf#page=182|Kubernetes.pdf p.182]]
- 정보 유형: Text, YAML/설정

### YAML·설정

~~~text
           Kubernetes         Resource        Management            ( EX.2:    Quota      &   Range      )






▣  [ Resource Quota  & Limit Range  Object ]

-. Resource Quota: Cluster의 NameSpace 별 Pod 오브젝트의  자원  사용량   제한설정   및  특정  오브젝트의    최대,   최소  범위지정   오브젝트

-. Limit Range: Cluster의 NameSpace 별 Pod 오브젝트의  자원  할당  기본값   지정   오브젝트

-. 운영환경,   테스트환경,    개발환경    등의  NameSpace를 분리하여   각  NameSpace의 자원  사용량   제한을   통해  효과적인   자원   운용을  지원

< 작업대상:    resource-quota.yml  >


apiVersion: v1
kind: ResourceQuota           # ResourceQuota 오브젝트
                                                                        ▣  [ Kubernetes Resource 수 제한 설정 ]
metadata:
                                                                        # count/pods: 10
  name: resource-quota
                                                                        # count/deployments: 3
  namespace: delivery         # ResourceQuota 오브젝트 적용  NameSpace 정의
                                                                        # count/services.nodeports: 10
spec:
                                                                        # count/services.loadbalancers: 3
  hard:
                                                                        # count/secrets: 5
    requests.cpu: "500m"      # Request 속성에서  사용 할  Quota 값 정의
                                                                        # count/configmaps: 5
    requests.memory: "500Mi"
    limits.cpu: "700m"        # Limit 속성에서  사용  할 Quota 값 정의
    limits.memory: "700Mi"
~~~

### Visual 의미

- 여러 열에 배치된 Manifest·설명은 Text Layer의 선형 순서만으로 읽지 않는다. Rendering의 좌→우 배치, 들여쓰기와 연결선을 함께 기준으로 한다.

## PDF p.183

- 원본: [[40_자료/강의 자료/Kubernetes.pdf#page=183|Kubernetes.pdf p.183]]
- 정보 유형: Text, YAML/설정, 명령/출력, 표형 정보

### YAML·설정 및 명령·출력

~~~text
           Kubernetes         Resource        Management            ( EX.2:    Quota      &   Range      )






$ kubectl  apply -f resources/resource-quota.yml

resourcequota/resource-quota created

$ kubectl  get resourcequota  -n delivery

NAME           AGE   REQUEST                                      LIMIT

resource-quota 19s   requests.cpu: 0/500m, requests.memory: 0/500Mi limits.cpu: 0/700m, limits.memory: 0/700Mi

< 작업대상:    resource-overpod.yml  >

metadata:

  namespace: delivery
    resources:                # Pod의 Resource 제한 정의 영역

     limits:                  # Limit 속성 정의  ( Memory, CPU 자원 최대 사용량  )

       memory: "1000Mi"       # Memory 최대 사용  : 500M
       cpu: "500m"            # CPU 최대 사용  : 2 코어

     requests:                # Request 속성 정의 ( Memory, CPU 자원 최소  사용량  ) / 생략  할 경우  Limit 값이 자동  설정

       memory: "1000Mi"       # Memory 최소 사용  : 500M
       cpu: "500m"            # CPU 최소 사용  : 2 코어


▣ Over-Pod 정의 Manifast File 수정 ( 배포  Namespace 지정, 최소, 최대  메모리  용량부분을   수정  )
~~~

### Visual 의미

- 여러 열에 배치된 Manifest·설명은 Text Layer의 선형 순서만으로 읽지 않는다. Rendering의 좌→우 배치, 들여쓰기와 연결선을 함께 기준으로 한다.

## PDF p.184

- 원본: [[40_자료/강의 자료/Kubernetes.pdf#page=184|Kubernetes.pdf p.184]]
- 정보 유형: Text, 명령/출력

### 명령·출력

~~~text
           Kubernetes         Resource        Management            ( EX.2:    Quota      &   Range      )






$ kubectl  apply -f resources/resource-overpod.yml

Error from server (Forbidden): error when creating "resources/resource-overpod.yml": pods "over-pod" is forbidden:
exceeded quota: resource-quota, requested: limits.memory=1000Mi,requests.memory=1000Mi, used:

limits.memory=0,requests.memory=0, limited: limits.memory=700Mi,requests.memory=500Mi

▣ Resource Quota에서 정의한  최대  사용  메모리의  용량을   초과하는  Pod 오브젝트   생성  실패를  확인한다.

▣ NameSpace에 정의  된 Resource Quota Limit의 값을 초과하는  Pod 오브젝트는   사용이  불가능하다.


[ Over-Pod의  Resources  영역을   수정하며    TEST ]
1. resources 영역에서 limits, request 주석 후 TEST ( Forbidden: resources -> Required )

2. resources 영역에서 limits 영역 주석,  request 영역 CPU 500m, Memory 500Mi 수정 후 TEST ( Forbidden: limits 정의 X )

3. resources 영역에서 limits 영역 Memory 500Mi, request 영역 Memory 500Mi 수정 후 TEST ( Forbidden: CPU 정의 X )
4. resources 영역에서 limits 영역 CPU 500m, Memory 500Mi, request영역 CPU 500m, Memory 500Mi 수정 후 TEST ( 생성 성공 )


▣ Resource Quota가 정의 된  NameSpace에서 Pod 오브젝트를  생성  할  때에는  반드시  Resource 제한 설정을  필수로   함께  정의해야한다.
▣ Resource Quota에서 정의되는   모든 항목(Request, Limit)을 반드시   함께 설정해야   한다.  ( BestEffort 클래스를 갖는  Pod는 생성  불가  )

▣ Resource Quota 오브젝트  생성 시  Requests 혹은 Limits만 사용가능하며,   CPU & Memory 또한 선택적  사용이  가능하다.

$ kubectl  delete pod over-pod  -n delivery

pod "over-pod" deleted
~~~

## PDF p.185

- 원본: [[40_자료/강의 자료/Kubernetes.pdf#page=185|Kubernetes.pdf p.185]]
- 정보 유형: Text, YAML/설정

### YAML·설정

~~~text
           Kubernetes         Resource        Management            ( EX.2:    Quota      &   Range      )






< 작업대상:    resource-limitrange.yml  >

apiVersion: v1

kind: LimitRange              # LimitRange 오브젝트

metadata:
  name: resource-limitrange

  namespace: delivery         # LimitRange 오브젝트 적용  NameSpace 정의

spec:
  limits:

    - default:                # default 영역에서  Limit의 기본값을  정의한다.

       memory: 700Mi
       cpu: 700m

     defaultRequest:          # defaultRequest 영역에서 Request의 기본값을  정의한다.

       memory: 500Mi
       cpu: 500m

     type: Container          # LimitRange 적용 단위를  컨테이너로   정의한다.


$ kubectl  apply -f resources/resource-limitrange.yml

limitrange/resource-limitrange created
~~~

## PDF p.186

- 원본: [[40_자료/강의 자료/Kubernetes.pdf#page=186|Kubernetes.pdf p.186]]
- 정보 유형: Text, 명령/출력, 표형 정보

### 명령·출력

~~~text
           Kubernetes         Resource        Management            ( EX.2:    Quota      &   Range      )






$ kubectl  get limitrange  -n delivery

NAME                CREATED AT
resource-limitrange 2023-09-15T06:52:41Z


$ kubectl  run over-pod --image=nginx  -n  delivery

$ kubectl  describe pod over-pod  -n delivery

Limits:
  cpu: 700m, memory: 700Mi

Requests:

  cpu: 500m, memory: 500Mi

▣ Resource 제한 설정없이   Pod 오브젝트를   생성  후 생성  된 Pod의 Resource 제한 설정값을   확인한다.

▣ 별도의   지정 값을  이용하여   Pod 오브젝트를   생성하는  것도  가능하며,   Resource 제한 설정값을   지정하지  않았을   경우에만  기본  설정값을   적용한다.

$ kubectl  delete pod over-pod  -n delivery

$ kubectl  delete resourcequota  resource-quota  -n delivery

$ kubectl  delete limitrange  resource-limitrange  -n delivery

▣ 다음  TEST를 위해  생성  한 Pod 및 Resource Quota, Limit Range 오브젝트 삭제 작업을  진행한다.
~~~

## 누락·검토 대기

- 선언한 PDF Page 범위의 Text·YAML·명령·출력·Visual 확인은 완료했다.
- 원자료의 Kubernetes·AWS Version과 기술 내용에 대한 최신 공식 문서 검증은 이 Chapter Digest의 범위 밖이다.
- 전체 Index의 Chapter Link와 전 범위 Gap·Overlap 검증은 Index 갱신 단계에서 수행한다.

## 완료 검증

- [x] PDF p.172–p.186 모든 Page를 포함했다.
- [x] Text Layer와 Rendering을 함께 확인했다.
- [x] YAML·명령·표형 출력의 기호와 배치를 원본과 대조했다.
- [x] 도식·삽입 이미지의 관계를 별도 기록했다.
- [x] 판독 불확실성과 원자료 오류 가능성을 숨기지 않았다.
- [ ] 전체 Source Digest Index 통합 검수와 외부 기술 검증
