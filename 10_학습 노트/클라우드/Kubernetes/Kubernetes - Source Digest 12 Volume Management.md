---
type: source-digest
status: stable
created: 2026-07-21
parent_moc: "[[10_학습 노트/클라우드/Kubernetes/00_Kubernetes MOC]]"
source: "[[40_자료/강의 자료/Kubernetes.pdf]]"
source_pages: "213-234"
digest_role: chapter
digest_index: "[[10_학습 노트/클라우드/Kubernetes/Kubernetes - Source Digest v1]]"
chapter: "12 Volume Management"
source_hash: F97666865E22749C47640689B5C41DEE38476A40312A53915F60B4F6A4330D24
source_version: "PowerPoint PDF; 266 pages; metadata created 2024-07-18"
coverage_status: complete
extraction_method: "pdfplumber 0.11.9 text extraction + pypdfium2 render visual review"
reviewed_on: 2026-07-21
---

# Kubernetes - Source Digest 12 Volume Management

> [!purpose]
> `Kubernetes.pdf` p.213–p.234의 의미 있는 정보를 페이지별로 보존한 Chapter Digest이다. 원자료의 기술적 정확성을 현재 지식으로 검증하거나 몰래 교정하지 않는다.

## Source 식별

- 원자료: [[40_자료/강의 자료/Kubernetes.pdf|Kubernetes.pdf]]
- 대상 범위: PDF p.213–p.234
- 전체 원자료: 266 pages
- SHA-256: `F97666865E22749C47640689B5C41DEE38476A40312A53915F60B4F6A4330D24`
- 추출·검수: `pdfplumber 0.11.9` Text Layer + `pypdfium2` Rendering
- Chapter 경계: Local Volume(hostPath·emptyDir)와 Persistent Volume(EFS·EBS)

## Coverage

| PDF 범위 | Text | YAML·명령·표 | Visual | 원본 대조 | 상태 |
|---|---|---|---|---|---|
| p.213–p.234 | 완료 | 완료 | 전체 렌더 검토 | 페이지별 대조 | 상세 변환 완료 / 기술 내용 외부 검증 미수행 |

## 변환 경계

- 아래 고정폭 Transcript는 PDF Text Layer의 Page 배치를 최대한 보존한다.
- YAML·명령·출력은 Rendering으로 기호와 배치를 대조했다. 원자료의 오탈자·잠재적 명령 오류는 임의로 수정하지 않는다.
- Visual 관계는 Text Layer 밖의 화살표·번호·공간 배치를 별도 설명한다.
- `status: draft`는 원자료 변환이 누락됐다는 뜻이 아니라, 전체 Index 통합 검수와 외부 기술 검증이 아직 끝나지 않았다는 뜻이다.

## Local Volume

## PDF p.213

- 원본: [[40_자료/강의 자료/Kubernetes.pdf#page=213|Kubernetes.pdf p.213]]
- 정보 유형: Cover

### 원자료 내용

~~~text
Kubernetes                          Volume                   Management
~~~

## PDF p.214

- 원본: [[40_자료/강의 자료/Kubernetes.pdf#page=214|Kubernetes.pdf p.214]]
- 정보 유형: Text

### 원자료 내용

~~~text
         Kubernetes         Volume       Management            (  Local    Volume       )






◎  Kubernetes  Volume Management

   Kubernetes Volume : "Local Volume", "Persistent Volume" 2가지로 구분된다.

   Local Volume : k8s 내부에 Data 저장  경로를  정의하고    Data를 보관하는    방식  ( 노드  장애  발생  시  Data 사용  불가  )
   Persistent Volume : Network 연결이 가능 한  Storage Server의 Volume을 Mount하여 사용하는    방식

   Network 연결이  가능  한  Persistent Volume의 대표적인  종류  : AWS EBS, GCE Persistent Volume, NFS, GlusterFS 등


◎  Kubernetes  Local Volume  ( hostPath &  emptyDir )

▣  hostPath

-. Pod가 생성되는    Node의 FileSystem Directory와 Pod Container의 Directory를 Mount하여 Data를 저장하는  방식

-. hostPath에 저장되는   Data는 k8s 내부의   또 다른   Node에서  동작중인   Pod Container에서는  해당  Data를 사용   할 수  없다.

-. hostPath를 사용하는   Node에 장애   발생  시 내부   Pod가 다른  Node로 이동   될 경우  hostPath에 저장  된  Data는 사용이   불가능하다.
-. 보안성   및 Data 활용  측면에   부족한   부분이   많아  자주  사용되지    않는다.

▣  emptyDir

-. Pod의 Data를 영속적으로    보존하는것이     아닌   Pod 동작 중  필요한   휘발성   Data를 저장하는   임시저장    공간

-. emptyDir은 비어있는   Directory의 형태로   생성되며   Pod 오브젝트    삭제  시 함께   삭제되는   특징을   갖는다.

-. emptyDir은 동일  Pod 오브젝트   내부의   Container간 Data 공유에  사용  될  수 있다.
-. EX: Git Hub에 저장  된 Source Cod를 내려받아   운영   Container로 공유하는   Side-Car Container 구성
~~~

## EX.1 hostPath

## PDF p.215

- 원본: [[40_자료/강의 자료/Kubernetes.pdf#page=215|Kubernetes.pdf p.215]]
- 정보 유형: Text, 명령/출력, 표형 정보

### 명령·출력

~~~text
           Kubernetes         Volume       Management            (  EX.1    : hostPath       )






$ kubectl  get nodes

NAME                                           STATUS   ROLES   AGE   VERSION
ip-192-168-10-147.ap-northeast-2.compute.internal Ready <none>  6d1h  v1.24.16-eks-8ccc7ba

ip-192-168-20-156.ap-northeast-2.compute.internal Ready <none>  6d1h  v1.24.16-eks-8ccc7ba


$ kubectl  label node ip-192-168-10-147.ap-northeast-2.compute.internal     node=node-1
$ kubectl  label node ip-192-168-20-156.ap-northeast-2.compute.internal     node=node-2


$ kubectl  get nodes --show-labels

NAME                                           STATUS   ROLES   AGE   VERSION              LABELS

ip-192-168-10-147.ap-northeast-2.compute.internal Ready <none>  6d1h  v1.24.16-eks-8ccc7ba
kubernetes.io/os=linux,node.kubernetes.io/instance-type=t3.large,node=node-1,topology.kubernetes.io/region=ap-northeast-

2,topology.kubernetes.io/zone=ap-northeast-2a

ip-192-168-20-156.ap-northeast-2.compute.internal Ready <none>  6d1h  v1.24.16-eks-

kubernetes.io/os=linux,node.kubernetes.io/instance-type=t3.large,node=node-2,topology.kubernetes.io/region=ap-northeast-

2,topology.kubernetes.io/zone=ap-northeast-2c

▣ HostPath Volume TEST를 위해 Worker Node에 추가 Label을 부여
~~~

## PDF p.216

- 원본: [[40_자료/강의 자료/Kubernetes.pdf#page=216|Kubernetes.pdf p.216]]
- 정보 유형: Text, YAML/설정

### YAML·설정

~~~text
           Kubernetes         Volume       Management            (  EX.1    : hostPath       )






< 작업대상    : local-hostpath-1.yml  >                              template:
                                                                   metadata:
apiVersion: apps/v1
                                                                    labels:
kind: Deployment
                                                                      app: hostpath-app
metadata:
                                                                   spec:
  name: hostpath-deploy-1
                                                                    nodeSelector:
  namespace: delivery
                                                                      node: node-1
spec:
                                                                    containers:
  selector:
                                                                    - name: hostpath-pod
    matchLabels:
                                                                      image: chlzzz/kube-image:debug
     app: hostpath-app
                                                                      volumeMounts:
                                                                      - name: hostpath-volume
                                                                        mountPath: /mnt
# Pod Template 영역에서 hostPath Type Volume 생성 ( hostpath-volume )
                                                                      command: ['sh','-c','tail -f /dev/null' ]
# Container 속성 영역에서  생성  된  Volume을 Mount 하도록 정의
                                                                    volumes:
# hostpath-volume은 Container의 "/mnt" Directory와 연결된다.
                                                                    - name: hostpath-volume
                                                                      hostPath:
                                                                        path: /tmp
~~~

### Visual 의미

- 여러 열에 배치된 Manifest·설명은 Text Layer의 선형 순서만으로 읽지 않는다. Rendering의 좌→우 배치, 들여쓰기와 연결선을 함께 기준으로 한다.

## PDF p.217

- 원본: [[40_자료/강의 자료/Kubernetes.pdf#page=217|Kubernetes.pdf p.217]]
- 정보 유형: Text, YAML/설정

### YAML·설정

~~~text
           Kubernetes         Volume       Management            (  EX.1    : hostPath       )






< 작업대상    : local-hostpath-2.yml  >                              template:
                                                                   metadata:
apiVersion: apps/v1
                                                                    labels:
kind: Deployment
                                                                      app: hostpath-app
metadata:
                                                                   spec:
  name: hostpath-deploy-2
                                                                    nodeSelector:
  namespace: delivery
                                                                      node: node-2
spec:
                                                                    containers:
  selector:
                                                                    - name: hostpath-pod
    matchLabels:
                                                                      image: chlzzz/kube-image:debug
     app: hostpath-app
                                                                      volumeMounts:
                                                                      - name: hostpath-volume
                                                                        mountPath: /mnt
# Pod Template 영역에서 hostPath Type Volume 생성 ( hostpath-volume )
                                                                      command: ['sh','-c','tail -f /dev/null' ]
# Container 속성 영역에서  생성  된  Volume을 Mount 하도록 정의
                                                                    volumes:
# hostpath-volume은 Container의 "/mnt" Directory와 연결된다.
                                                                    - name: hostpath-volume
                                                                      hostPath:
                                                                        path: /tmp
~~~

### Visual 의미

- 여러 열에 배치된 Manifest·설명은 Text Layer의 선형 순서만으로 읽지 않는다. Rendering의 좌→우 배치, 들여쓰기와 연결선을 함께 기준으로 한다.

## PDF p.218

- 원본: [[40_자료/강의 자료/Kubernetes.pdf#page=218|Kubernetes.pdf p.218]]
- 정보 유형: Text, 명령/출력, 표형 정보

### 명령·출력

~~~text
           Kubernetes         Volume       Management            (  EX.1    : hostPath       )






$ kubectl  apply -f volume/

$ kubectl  get pod -n delivery  -o wide

NAME                              READY  STATUS   RESTARTS  AGE    IP             NODE
hostpath-deploy-1-5585f44566-g8wm9 1/1   Running  0         119s   192.168.10.184 node-1

hostpath-deploy-2-6cc4cb89b7-dhp5l 1/1   Running  0         119s   192.168.20.179 node-2

$ kubectl  exec -it hostpath-deploy-1-5585f44566-g8wm9    -n delivery -  sh

/ # touch /mnt/test.data

/ # ls -l /mnt/test.data

-rw-r--r--   1 root    root           0 Jul 27 04:44 /mnt/test.data

▣ 생성  된 Pod 오브젝트의   Node 정보를  확인,  현재  node-1에서 Pod 오브젝트가   생성  된 것을  확인  할 수 있다.

▣ Pod 오브젝트의   컨테이너로   접속  후 hostPath Local Volume과 연결 된 디렉터리   "/mnt" 디렉터리  내부에  테스트용   Data를 생성한다.

$ kubectl  exec -it hostpath-deploy-2-6cc4cb89b7-dhp5l    -n delivery -  sh

/ # ls -l /mnt/test.data

ls: /mnt/test.data: No such file or directory

▣ hostPath Volume은 Node의 실제 FileSystem과 연결되므로   Pod 오브젝트가   생성되는  Node가 변경  될  경우 기존  Data를 사용  할 수  없다.
~~~

### 판독 불확실성

- 추출문은 shell separator를 Unicode dash로 반환했다. Rendering에는 `- sh`처럼 단일 hyphen으로 보인다. 실행 가능한 `-- sh`로 몰래 교정하지 않고 원자료 표기를 보존한다.

## PDF p.219

- 원본: [[40_자료/강의 자료/Kubernetes.pdf#page=219|Kubernetes.pdf p.219]]
- 정보 유형: Text, 명령/출력

### 명령·출력

~~~text
           Kubernetes         Volume       Management            (  EX.1    : hostPath       )






$ kubectl  exec -it hostpath-deploy-1-5585f44566-g8wm9    -n delivery -  sh

/ # rm -rf /mnt/test.data
/ # ls -l /mnt/test.data

ls: /mnt/test.data: No such file or directory

▣ TEST에 사용한   데이터를  삭제



$ kubectl  delete -f volume/
deployment.apps "hostpath-deploy-1" deleted

deployment.apps "hostpath-deploy-2" deleted


$ kubectl  label node ip-192-168-10-147.ap-northeast-2.compute.internal     node-

$ kubectl  label node ip-192-168-20-156.ap-northeast-2.compute.internal     node-

▣ Deployment 삭제 및 Worker Node의 추가한  Label 삭제



$ kubectl  get nodes --show-labels
▣ Label 삭제  확인
~~~

### 판독 불확실성

- `kubectl exec`의 shell separator가 Rendering에서 `- sh`처럼 보인다. 원자료의 잠재적 명령 오류를 그대로 둔다.

## EX.1 emptyDir

## PDF p.220

- 원본: [[40_자료/강의 자료/Kubernetes.pdf#page=220|Kubernetes.pdf p.220]]
- 정보 유형: Text, YAML/설정

### YAML·설정

~~~text
           Kubernetes         Volume       Management            (  EX.1    : emptyDir       )





< 작업대상    : local-emptydir.yml  >                                  spec:

                                                                    containers:
apiVersion: apps/v1
                                                                    - name: emptydir-pod-write
kind: Deployment
                                                                      image: chlzzz/kube-image:debug
metadata:
                                                                      volumeMounts:
  name: emptydir-deploy
                                                                      - name: emptydir-volume
  namespace: delivery
                                                                        mountPath: /mnt
spec:
                                                                      command: ['sh','-c','tail -f /dev/null' ]
  selector:
                                                                    - name: emptydir-pod-read
    matchLabels:
                                                                      image: nginx:latest
     app: emptydir-app
                                                                      volumeMounts:
  template:
                                                                      - name: emptydir-volume
    metadata:
                                                                        mountPath: /usr/share/nginx/html
     labels:
                                                                      ports:
       app: emptydir-app
                                                                      - containerPort: 80
# Pod Template 영역에서 emptyDir Type Volume 생성 ( emptrydir-volume )
                                                                    volumes:
# emptydir-pod-write 컨테이너 : Data 생성 ( Side-Car 컨테이너  )
                                                                    - name: emptydir-volume
# emptydir-pod-read 컨테이너  : Data 사용 ( 운영  컨테이너  )
                                                                      emptyDir: {}
~~~

### Visual 의미

- 여러 열에 배치된 Manifest·설명은 Text Layer의 선형 순서만으로 읽지 않는다. Rendering의 좌→우 배치, 들여쓰기와 연결선을 함께 기준으로 한다.

## PDF p.221

- 원본: [[40_자료/강의 자료/Kubernetes.pdf#page=221|Kubernetes.pdf p.221]]
- 정보 유형: Text, 명령/출력, 표형 정보

### 명령·출력

~~~text
           Kubernetes         Volume       Management            (  EX.1    : emptyDir       )






$ kubectl  apply -f volume/local-emptydir.yml

$ kubectl  get pod -n delivery

NAME                            READY  STATUS   RESTARTS  AGE
emptydir-deploy-55964b46c4-v8kkz 2/2   Running  0         7s


$ kubectl  describe pod emptydir-deploy-55964b46c4-v8kkz    -n delivery

Status:      Running

IP:          192.168.10.21

Containers:
  emptydir-pod-write:

    Container ID: containerd://a185dd9278e85d12bc4f3a639ec1a08ce51d1912931d4ca9330d0acc1440006e

    Image:       chlzzz/kube-image:debug

  emptydir-pod-read:

    Container ID: containerd://eff2da2c7ac253613eb8e8f7b9c1cf9c92d1c1853092e3e972d1a357afb3a923
    Image:        nginx


▣ Pod 오브젝트   내부 컨테이너   2개가  정상적으로   동작중인지   확인한다.

▣ 하나의   Pod 오브젝트에서   여러  개의 컨테이너를    운영 할  경우  컨테이너  이름을   이용하여  구분한다.
~~~

## PDF p.222

- 원본: [[40_자료/강의 자료/Kubernetes.pdf#page=222|Kubernetes.pdf p.222]]
- 정보 유형: Text, 명령/출력

### 명령·출력

~~~text
           Kubernetes         Volume       Management            (  EX.1    : emptyDir       )






$ kubectl  exec -it emptydir-deploy-55964b46c4-v8kkz   -c  emptydir-pod-write  -n delivery  - sh

/ # echo "Empty Dir Test" > /mnt/index.html
/ # cat /mnt/index.html

Empty Dir Test

▣ 컨테이너   구분을  위한  "-c" 옵션을  함께  사용하여  emptydir-pod-write 컨테이너에  접근한다.

▣ nginx가 구동중인   emptydir-pod-read 컨테이너에서  사용  할 index.html 데이터를  생성  후 확인


$ kubectl  exec -it emptydir-deploy-55964b46c4-v8kkz   -c  emptydir-pod-write  -n delivery  - sh
# ls -l /usr/share/nginx/html

-rw-r--r-- 1 root root 15 Sep 19 03:01 index.html


$ kubectl  run -i --rm --tty  debug --image=chlzzz/kube-image:debug   --  sh

/ # curl 192.168.10.21
Empty Dir Test

▣ curl 명령어를   이용하여  emptydir-pod-read 컨테이너에서  동작중인   nginx WEB Server에게 페이지  요청을  진행한다.

$ kubectl  delete -f volume/local-emptydir.yml

▣ emptyDir Type의 Volume의 경우 Deployment 오브젝트에서   관리하는   Pod 오브젝트  삭제  시 함께  삭제된다.
~~~

### 판독 불확실성

- 첫 `kubectl exec`의 shell separator와 대상 Container 설명 사이에 원자료상 불일치 가능성이 있다. 명령과 설명을 임의로 교정하지 않는다.

## Persistent Volume

## PDF p.223

- 원본: [[40_자료/강의 자료/Kubernetes.pdf#page=223|Kubernetes.pdf p.223]]
- 정보 유형: Text, 도식

### 원자료 내용

~~~text
         Kubernetes         Volume       Management            (  Persistent      Volume       )






◎  Kubernetes  Persistent Volume

   Kubernetes Persistent Volume 사용방법은 2가지로   구분  될  수 있다.   ( Static Provisioning, Dynamic Provisioning )

   Static Provisioning: 외부 Storage Server에서 Kubernetes에게 공유  할 목적의   Volume을 미리  구성
   Dynamic Provisioning: 외부 Storage Server에서 Kubernetes PVC 오브젝트의  요구사항에    맞는  새로운   Volume을 생성

   Public Cloud 환경 : Volume Provisioning ( AWS EBS, GCE Persistent Volume )

   On-Premises 환경 : Static Provisioning ( NFS ) / Dynamic Provisioning ( Gluster FS )


                                       Kubernetes    Cluster




                                                         None
                                                                                               Static
                                                        Storage
                                                                                            Provisioning
  Storage                                                Class
             Static Volume
 Server(A)
                                                                                               Dynamic
                                                                                            Provisioning

  Storage                               External        Stroage       Pod Volume
            Dynamic  Volume
                                        Volume 연결      Server 정의      요구사항  정의
 Server(B)
~~~

### Visual 의미

- 외부 Storage Server의 Static/Dynamic Volume과 Kubernetes StorageClass·PV·PVC·Pod Volume의 대응 구조를 비교한다.

## EX.2 EFS Static Provisioning

## PDF p.224

- 원본: [[40_자료/강의 자료/Kubernetes.pdf#page=224|Kubernetes.pdf p.224]]
- 정보 유형: Text, YAML/설정, 도식

### YAML·설정

~~~text
           Kubernetes         Volume       Management            (  EX.2    : Persistent      Volume       )





< 작업대상    : efs-pv.yml  >                               < 작업대상    : efs-pvc.yml  >


apiVersion: v1                                          apiVersion: v1
kind: PersistentVolume                                  kind: PersistentVolumeClaim

metadata:                                               metadata:

  name: efs-pv                                            name: efs-claim
  labels:                                                 namespace: delivery

    name: efs-pv                                        spec:

spec:                                                     storageClassName: ""
  capacity:                                               resources:

    storage: 5Gi # Static Provisioning의 경우 구문만 작성           requests:

  volumeMode: Filesystem                                      storage: 5Gi # Static Provisioning의 경우 구문만 작성
  accessModes:                                            selector:

    - ReadWriteMany                                         matchLabels:

  storageClassName: ""                                        name: efs-pv
  persistentVolumeReclaimPolicy: Retain                   accessModes:

  csi:                                                      - ReadWriteMany

    driver: efs.csi.aws.com
    volumeHandle: fs-09c234fc747386d4d # EFS-ID
~~~

### Visual 의미

- 여러 열에 배치된 Manifest·설명은 Text Layer의 선형 순서만으로 읽지 않는다. Rendering의 좌→우 배치, 들여쓰기와 연결선을 함께 기준으로 한다.

- PV label `name: efs-pv`와 PVC selector `matchLabels.name: efs-pv`가 결합되는 관계를 화살표로 표시한다.

## PDF p.225

- 원본: [[40_자료/강의 자료/Kubernetes.pdf#page=225|Kubernetes.pdf p.225]]
- 정보 유형: Text, 명령/출력, 표형 정보

### 명령·출력

~~~text
           Kubernetes         Volume       Management            (  EX.2    : Persistent      Volume       )






$ kubectl  apply -f volume/efs-pv.yml

$ kubectl  get pv

NAME    CAPACITY  ACCESS MODES  RECLAIM POLICY STATUS    CLAIM              STORAGECLASS REASON   AGE
efs-pv  5Gi       RWX           Retain         Available                                          13m


▣ PV 오브젝트를   생성  후 확인,  Kubernetes 전체에서  사용되므로   NameSpace 지정이 필요  없다.

$ kubectl  apply -f volume/efs-pvc.yml

$ kubectl  get pvc -n delivery

NAME       STATUS  VOLUME  CAPACITY  ACCESS MODES  STORAGECLASS  AGE

efs-claim  Bound   efs-pv  5Gi       RWX                         13m

▣ PVC 오브젝트를   생성  후 확인,  PVC 오브젝트는   특정  NameSpace에서만 사용  가능하므로   NameSpace를 지정한다.

$ kubectl  get pv

NAME    CAPACITY  ACCESS MODES  RECLAIM POLICY STATUS    CLAIM              STORAGECLASS REASON   AGE

efs-pv  5Gi       RWX           Retain         Bound    delivery/efs-claim                       13m

▣ 현재  PV 및 PVC 오브젝트의   Status 정보가  Bound 상태인 것을  반드시  확인한다.   ( NFS 연결이  정상적으로   진행  된 상태  )
~~~

## PDF p.226

- 원본: [[40_자료/강의 자료/Kubernetes.pdf#page=226|Kubernetes.pdf p.226]]
- 정보 유형: Text, YAML/설정, 도식

### YAML·설정

~~~text
           Kubernetes         Volume       Management            (  EX.2    : Persistent      Volume       )





< 작업대상    : efs-deploy.yml  >                    spec:

                                                   containers:
apiVersion: apps/v1
                                                   - name: efs-pod
kind: Deployment
                                                     image: chlzzz/kube-image:debug
metadata:
                                                     volumeMounts:
  name: efs-deploy

                                                     - name: efs
  namespace: delivery
                                                       mountPath: /mnt
spec:
                                                     command: ['sh','-c','tail -f /dev/null' ]
  replicas: 2
                                                     resources:
  selector:
                                                       limits:
    matchLabels:
                                                         memory: "100Mi"
     app: efs-app
                                                         cpu: "500m"
  template:
                                                   volumes:
    metadata:

                                                   - name: efs
     labels:
                                                     persistentVolumeClaim:
       app: efs-app
                                                       claimName: efs-claim
~~~

### Visual 의미

- 여러 열에 배치된 Manifest·설명은 Text Layer의 선형 순서만으로 읽지 않는다. Rendering의 좌→우 배치, 들여쓰기와 연결선을 함께 기준으로 한다.

- Container `volumeMounts.name: efs`와 Pod `volumes.name: efs`가 같은 이름으로 연결되는 관계를 화살표로 표시한다.

### 판독 불확실성

- Text 추출에만 나타난 `ㅁ` 문자는 Rendering에 없는 Artifact라서 본문에서 제외했다.

## PDF p.227

- 원본: [[40_자료/강의 자료/Kubernetes.pdf#page=227|Kubernetes.pdf p.227]]
- 정보 유형: Text, 명령/출력, 표형 정보

### 명령·출력

~~~text
           Kubernetes         Volume       Management            (  EX.2    : Persistent      Volume       )






$ kubectl  apply -f volume/efs-deploy.yml

$ kubectl  get pod -n delivery  -o wide

NAME                      READY   STATUS   RESTARTS  AGE  IP              NODE    NOMINATED NODE  READINESS
GATES

efs-deploy-96b48c99b-g66zb 1/1    Running  0         17m  192.168.20.16   node-2  <none>          <none>

efs-deploy-96b48c99b-qp99v 1/1    Running  0         17m  192.168.10.182  node-1  <none>          <none>

$ kubectl  exec -it efs-deploy-96b48c99b-g66zb   -n delivery  -- sh

/ # touch /mnt/efs.data

/ # ls -l /mnt
-rw-r--r--   1 root    root           0 Sep 20 04:30 efs.data


$ kubectl  exec -it efs-deploy-96b48c99b-qp99v   -n delivery  -- sh

/ # ls -l /mnt

-rw-r--r--   1 root    root           0 Sep 20 04:30 efs.data

▣ EFS Persistent Volume을 사용하는  Pod내부에서  Test용 Data를 생성한다.

▣  서로  다른  Worker Node에서 생성 된  Pod간 공유  스토리지를   사용하는   것을 확인한다.
~~~

## PDF p.228

- 원본: [[40_자료/강의 자료/Kubernetes.pdf#page=228|Kubernetes.pdf p.228]]
- 정보 유형: Text, 명령/출력

### 명령·출력

~~~text
           Kubernetes         Volume       Management            (  EX.2    : Persistent      Volume       )






$ kubectl  delete deploy  efs-deploy -n  delivery

deployment.apps "efs-deploy" deleted

$ kubectl  delete pvc efs-claim  -n delivery

persistentvolumeclaim "efs-claim" deleted

$ kubectl  delete pv efs-pv

persistentvolume "efs-pv" deleted


$ kubectl  apply -f volume/efs-pv.yml

persistentvolume/efs-pv created


$ kubectl  apply -f volume/efs-pvc.yml

persistentvolumeclaim/efs-claim created

$ kubectl  apply -f volume/efs-deploy.yml

deployment.apps/efs-deploy created

▣ Retain TEST를위해  Deployment, PVC, PV 오브젝트 삭제 후  재 생성을  진행한다.
~~~

## PDF p.229

- 원본: [[40_자료/강의 자료/Kubernetes.pdf#page=229|Kubernetes.pdf p.229]]
- 정보 유형: Text, 명령/출력, 표형 정보

### 명령·출력

~~~text
           Kubernetes         Volume       Management            (  EX.2    : Persistent      Volume       )






$ kubectl  get pod -n delivery

NAME                      READY   STATUS   RESTARTS  AGE
efs-deploy-96b48c99b-k5xrf 1/1    Running  0         25s

efs-deploy-96b48c99b-t2pll 1/1    Running  0         25s


$ kubectl  exec -it efs-deploy-96b48c99b-k5xrf   -n delivery  -- sh
/ # ls -l /mnt

-rw-r--r--   1 root    root           0 Sep 20 04:30 efs.data

▣ PVC 오브젝트의   "ReclaimPolicy" = Retain 으로 정의 한 상태

▣ PV, PVC, POD 오브젝트가  재  생성되더라도   기존  Data는 유지된다.

$ kubectl  delete deploy  efs-deploy -n  delivery

deployment.apps "efs-deploy" deleted


$ kubectl  delete pvc efs-claim  -n delivery

persistentvolumeclaim "efs-claim" deleted

$ kubectl  delete pv efs-pv

persistentvolume "efs-pv" deleted

▣ 다음  TEST를 위하여  생성  된  Pod, Pvc, Pv 오브젝트 삭제를  진행한다.
~~~

## EX.3 EBS Dynamic Provisioning

## PDF p.230

- 원본: [[40_자료/강의 자료/Kubernetes.pdf#page=230|Kubernetes.pdf p.230]]
- 정보 유형: Text, YAML/설정, 명령/출력, 표형 정보

### YAML·설정 및 명령·출력

~~~text
           Kubernetes         Volume       Management            (  EX.3    : Persistent      Volume       )






▣  [ EBS Dynamic  Provisioning  ]


< 작업대상    : ebs-sc.yml  >
apiVersion: storage.k8s.io/v1           # ReclaimPolicy : 해당 볼륨의 재사용  상태를   지정

kind: StorageClass                       -. Retain : PVC 오브젝트  삭제  시 PV에 저장  된 내용을   유지

metadata:                                -. Delete : PVC 오브젝트  삭제  시 PV 오브젝트  함께  삭제  ( Dynamic 전용 )
  name: ebs-sc

provisioner: ebs.csi.aws.com

volumeBindingMode: WaitForFirstConsumer # volumeBindingMode : Dynamic Provisioning 수행 시기
reclaimPolicy: Delete                    -. Immediate : Volume 즉시 생성

parameters:                              -. WaitForFirstConsumer : 연결 Pod 생성 완료 후 Volume 생성

  type: gp2
  fsType: ext4


$ kubectl  apply -f volume/ebs-sc.yml

$ kubectl  get sc

NAME          PROVISIONER           RECLAIMPOLICY  VOLUMEBINDINGMODE    ALLOWVOLUMEEXPANSION AGE
ebs-sc        ebs.csi.aws.com       Delete         WaitForFirstConsumer false                22s

gp2 (default) kubernetes.io/aws-ebs Delete         WaitForFirstConsumer false                6d5h
~~~

### Visual 의미

- 여러 열에 배치된 Manifest·설명은 Text Layer의 선형 순서만으로 읽지 않는다. Rendering의 좌→우 배치, 들여쓰기와 연결선을 함께 기준으로 한다.

## PDF p.231

- 원본: [[40_자료/강의 자료/Kubernetes.pdf#page=231|Kubernetes.pdf p.231]]
- 정보 유형: Text, YAML/설정, 명령/출력, 표형 정보

### YAML·설정 및 명령·출력

~~~text
           Kubernetes         Volume       Management            (  EX.3    : Persistent      Volume       )






< 작업대상    : ebs-pvc.yml  >

apiVersion: v1

kind: PersistentVolumeClaim

metadata:
  name: ebs-claim

  namespace: delivery         # accessModes : 생성되는 Persistent Volume에 대한 접근  정책을  정의

spec:                          -. accessModes는 provisioner에 따라 지원하는  Mode가 다르다.
  accessModes:                 -. ReadOnlyMany : 다수의 Node에서  Mount 가능 한 Volume ( 읽기 전용  )

    - ReadWriteOnce            -. ReadWriteMany : 다수의 Node에서 Mount 가능 한 Volume ( AWS EFS )

  storageClassName: ebs-sc     -. ReadWriteOnce : 단일 Node에서만 Mount 가능 한 Volume ( AWS EBS )
  resources:

    requests:

     storage: 1Gi

$ kubectl  apply -f volume/ebs-pvc.yml

$ kubectl  get pvc -n delivery

NAME       STATUS   VOLUME  CAPACITY  ACCESS MODES  STORAGECLASS  AGE

ebs-claim  Pending                                  ebs-sc        61s
~~~

### Visual 의미

- 여러 열에 배치된 Manifest·설명은 Text Layer의 선형 순서만으로 읽지 않는다. Rendering의 좌→우 배치, 들여쓰기와 연결선을 함께 기준으로 한다.

## PDF p.232

- 원본: [[40_자료/강의 자료/Kubernetes.pdf#page=232|Kubernetes.pdf p.232]]
- 정보 유형: Text, YAML/설정, 도식

### YAML·설정

~~~text
           Kubernetes         Volume       Management            (  EX.3    : Persistent      Volume       )





< 작업대상    : ebs-deploy.yml  >                          spec:

                                                         containers:
apiVersion: apps/v1
                                                         - name: ebs-pod
kind: Deployment
                                                           image: chlzzz/kube-image:debug
metadata:
                                                           volumeMounts:
  name: ebs-deploy

                                                           - name: ebs
  namespace: delivery
                                                             mountPath: /mnt
spec:
                                                           command: ['sh','-c','tail -f /dev/null' ]
  replicas: 1
                                                           resources:
  selector:
                                                             limits:
    matchLabels:
                                                               memory: "100Mi"
     app: ebs-app
                                                               cpu: "500m"
  template:
                                                         volumes:
    metadata:

                                                         - name: ebs
     labels:
                                                           persistentVolumeClaim:
       app: ebs-app
                                                             claimName: ebs-claim
~~~

### Visual 의미

- 여러 열에 배치된 Manifest·설명은 Text Layer의 선형 순서만으로 읽지 않는다. Rendering의 좌→우 배치, 들여쓰기와 연결선을 함께 기준으로 한다.

- Container `volumeMounts.name: ebs`와 Pod `volumes.name: ebs`가 같은 이름으로 연결되는 관계를 화살표로 표시한다.

### 판독 불확실성

- Text 추출에만 나타난 `ㅁ` 문자는 Rendering에 없는 Artifact라서 본문에서 제외했다.

## PDF p.233

- 원본: [[40_자료/강의 자료/Kubernetes.pdf#page=233|Kubernetes.pdf p.233]]
- 정보 유형: Text, 명령/출력, 표형 정보

### 명령·출력

~~~text
           Kubernetes         Volume       Management            (  EX.3    : Persistent      Volume       )






$ kubectl  apply -f volume/ebs-deploy.yml

$ kubectl  get pod -n delivery

NAME                      READY   STATUS   RESTARTS  AGE
ebs-deploy-ff99546b5-wcjs2 1/1    Running  0         21s


$ kubectl  get pvc -n delivery

NAME       STATUS  VOLUME                                 CAPACITY  ACCESS MODES  STORAGECLASS  AGE
ebs-claim  Bound   pvc-29787f0a-728f-4d45-b02d-f3ac2658ea00 1Gi     RWO           ebs-sc        26s


▣ Pod의 모든  구성이  완료  된  후 PVC 정보를  확인  STATUS "Bound" 확인

$ kubectl  exec -it ebs-deploy-ff99546b5-wcjs2   -n delivery  -- sh


/ # df -h | grep /mnt
/dev/nvme1n1          973.4M    24.0K   957.4M  0% /mnt


/ # touch /mnt/test.data
/ # ls -l /mnt

-rw-r--r--   1 root    root           0 Sep 19 08:13 test.data

▣ Pod 내부로  접속하여   TEST Data를 생성
~~~

## PDF p.234

- 원본: [[40_자료/강의 자료/Kubernetes.pdf#page=234|Kubernetes.pdf p.234]]
- 정보 유형: Text, 명령/출력

### 명령·출력

~~~text
           Kubernetes         Volume       Management            (  EX.3    : Persistent      Volume       )






$ kubectl  delete pod ebs-deploy-ff99546b5-wcjs2   -n delivery

$ kubectl  get pod -n delivery

NAME                      READY   STATUS   RESTARTS  AGE
ebs-deploy-ff99546b5-cmcct 1/1    Running  0         93s


$ kubectl  exec -it ebs-deploy-ff99546b5-cmcct   -n delivery  -- sh

/ # ls -l /mnt
-rw-r--r--   1 root    root           0 Sep 19 08:13 test.data


▣ Persistent Volume의 데이터 영속성을   테스트하기   위해  현재  생성  된 Pod 오브젝트를   삭제  후 Pod 재배포  작업을  수행한다.
▣ 재배포   된 Pod 오브젝트로   접속하여  Persistent Volume 마운트 경로인  "/mnt" 디렉터리  하위에   테스트용  파일이   존재하는지   확인한다.

▣ Pod 오브젝트의   컨테이너는   1회성  사용(Stateless)이지만  Persistent Volume은 데이터의  영속성  보장(Stateful)한다.


$ kubectl  delete -f volume/ebs-deploy.yml

$ kubectl  delete -f volume/ebs-pvc.yml


▣ PVC 오브젝트를   삭제  할 경우  ReclaimPolicy가 "Delete"이므로 Persistent Volume이 함께 삭제 된다.
▣ StorageClass 오브젝트의  경우  Statefulset Controller에서 그대로 사용  할 예정이므로    삭제하지  않는다.
~~~

## 누락·검토 대기

- 선언한 PDF Page 범위의 Text·YAML·명령·출력·Visual 확인은 완료했다.
- 원자료의 Kubernetes·AWS Version과 기술 내용에 대한 최신 공식 문서 검증은 이 Chapter Digest의 범위 밖이다.
- 전체 Index의 Chapter Link와 전 범위 Gap·Overlap 검증은 Index 갱신 단계에서 수행한다.

## 완료 검증

- [x] PDF p.213–p.234 모든 Page를 포함했다.
- [x] Text Layer와 Rendering을 함께 확인했다.
- [x] YAML·명령·표형 출력의 기호와 배치를 원본과 대조했다.
- [x] 도식·삽입 이미지의 관계를 별도 기록했다.
- [x] 판독 불확실성과 원자료 오류 가능성을 숨기지 않았다.
- [ ] 전체 Source Digest Index 통합 검수와 외부 기술 검증
