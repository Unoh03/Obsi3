---
type: source-digest
status: draft
created: 2026-07-21
parent_moc: "[[10_학습 노트/클라우드/Kubernetes/00_Kubernetes MOC]]"
source: "[[40_자료/강의 자료/Kubernetes.pdf]]"
source_pages: "251-261"
digest_role: chapter
digest_index: "[[10_학습 노트/클라우드/Kubernetes/Kubernetes - Source Digest v1]]"
chapter: "15 AutoScaling"
source_hash: F97666865E22749C47640689B5C41DEE38476A40312A53915F60B4F6A4330D24
source_version: "PowerPoint PDF; 266 pages; metadata created 2024-07-18"
coverage_status: partial
extraction_method: "pdfplumber 0.11.9 text extraction + pypdfium2 render visual review"
---

# Kubernetes - Source Digest 15 AutoScaling

> [!purpose]
> `Kubernetes.pdf` p.251–p.261의 의미 있는 정보를 페이지별로 보존한 Chapter Digest이다. 원자료의 기술적 정확성을 현재 지식으로 검증하거나 몰래 교정하지 않는다.

## Source 식별

- 원자료: [[40_자료/강의 자료/Kubernetes.pdf|Kubernetes.pdf]]
- 대상 범위: PDF p.251–p.261
- 전체 원자료: 266 pages
- SHA-256: `F97666865E22749C47640689B5C41DEE38476A40312A53915F60B4F6A4330D24`
- 추출·검수: `pdfplumber 0.11.9` Text Layer + `pypdfium2` Rendering
- Chapter 경계: HPA·VPA·CA 개요, Metrics Server, HPA, EKS Cluster Autoscaler

## Coverage

| PDF 범위 | Text | YAML·명령·표 | Visual | 원본 대조 | 상태 |
|---|---|---|---|---|---|
| p.251–p.261 | 완료 | 완료 | 전체 렌더 검토 | 페이지별 대조 | 상세 변환 완료 / 기술 내용 외부 검증 미수행 |

## 변환 경계

- 아래 고정폭 Transcript는 PDF Text Layer의 Page 배치를 최대한 보존한다.
- YAML·명령·출력은 Rendering으로 기호와 배치를 대조했다. 원자료의 오탈자·잠재적 명령 오류는 임의로 수정하지 않는다.
- Visual 관계는 Text Layer 밖의 화살표·번호·공간 배치를 별도 설명한다.
- `status: draft`는 원자료 변환이 누락됐다는 뜻이 아니라, 전체 Index 통합 검수와 외부 기술 검증이 아직 끝나지 않았다는 뜻이다.

## AutoScaling

## PDF p.251

- 원본: [[40_자료/강의 자료/Kubernetes.pdf#page=251|Kubernetes.pdf p.251]]
- 정보 유형: Cover
- PowerPoint outline: slide 261 (PDF page와 불일치)

### 원자료 내용

~~~text
Kubernetes                          AutoScaling
~~~

### 판독 불확실성

- PDF p.251 = PowerPoint outline slide 261. PDF p.246 앞에서 내부 slide 247–255가 생략된 번호 체계를 이어받는다.

## PDF p.252

- 원본: [[40_자료/강의 자료/Kubernetes.pdf#page=252|Kubernetes.pdf p.252]]
- 정보 유형: Text
- PowerPoint outline: slide 262 (PDF page와 불일치)

### 원자료 내용

~~~text
         Kubernetes         AutoScaling         Summary





◎  Kubernetes  Pod AutoScaling

   Pod AutoScaling : Pod의 자원 사용률에   따라  Pod나  Worker Node의 수를 자동으로    늘리고   줄이는   기능을   의미한다.

   Pod AutoScaling을 구현하기위해서는     Metrics-Server 기능이  반드시  필요하다.    ( Resource의 자원  사용량을   수집   )
   Pod AutoScaling 동작 지표  : HPA 기준 [ CPU / Memory / Packets-Per-Seconds(Pod) / Request-Per-Seconds(Ingress) ]

   Public Cloud의 경우 서비스   이용시간    및 사용률에    따른  따른  비용이   달라지기    때문에   비용  최적화에   많은   도움이  된다.

◎  Kubernetes  AutoScaling  HPA & VPA & CA


   Kubernetes AutoScaling 종류 : 수평 파드  오토스케일러(HPA),    수직   파드  오토스케일러(VPA),    클러스터    오토  스케일러(CA)
   HPA : Pod의 자원  사용률을   감시하여    Pod의 Replicas 수를 증가   혹은  감소  시키는   것을  말한다.   ( Scale-IN / Scale-OUT )

   VPA : Pod의 자원  사용률을   감시하여    Pod의 Resource 할당을  증가  혹은  감소   시키는   것을  말한다.   ( Scale-UP / Scale-DOWN )

   CA : Node의 추가증설이    필요한   경우   Public Cloud API와 연동하여  K8s에  새로운  Worker Node를 추가하는것을     말한다.
※  참고  : AutoScaling 우선순위  [ VPA > HPA > CA ] / VPA의 경우 자원  사용률을    미리  예측해야하는     어려움이   있다.


◎  HPA ( Horizontal  Pod AutoScaler  ) 동작과정

   HPA는 Metrics-Server를 이용하여   현재  구성  된  Pod의 CPU 사용률을   수집한다.    ( Metrics-Server Addon 설치 )

   수집  된 Pod의  CPU 사용률  정보를   바탕으로    HPA에서  지정  된 Pod의  목표  CPU 평균  사용률을   만족하기위해     Replicas 수를  조정한다.
   HPA는 Replicas 수정 작업을   30초  주기로  진행하며,    Replicas의 변경사항이    필요한   경우에만   수정작업을     진행한다.

   Replicas 수정 작업  주기는   kubecontroller-manager의 속성으로  정의되어있다.     ( horizontal-pod-autoscaler-sync-period )

   HPA는 급격한   Pod 오브젝트의    개수  변화를   방지하기위해     Pod 확장 / Pod 축소에   대한  약간의   대기  시간을   갖는다.
~~~

### 판독 불확실성

- PDF p.252 = PowerPoint outline slide 262. PDF p.246 앞에서 내부 slide 247–255가 생략된 번호 체계를 이어받는다.

## Horizontal Pod AutoScaler

## PDF p.253

- 원본: [[40_자료/강의 자료/Kubernetes.pdf#page=253|Kubernetes.pdf p.253]]
- 정보 유형: Text, 명령/출력, 표형 정보
- PowerPoint outline: slide 263 (PDF page와 불일치)

### 명령·출력

~~~text
           Kubernetes         AutoScaling         (  Horizontal       Pod    AutoScaler         )






▣  [ Metrics-Server  Install ]

$ kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml


▣ Metrics-Server는 Kubernetes Cluster 전체의 Resource 사용 Data를 수집한다.  ( Node의 kubelet을 이용하여  Resource 사용량을  수집  )

▣ Kubernetes Cluster 구성 시 자동으로   구성되지  않으며  별도의   설치작업이   필요하다.
▣ Metrics-Server를 구성하는  방법은  Kubernetes 공식 Git-Hub에서 Metrics-Server Components.yaml을 이용하여 간단하게   설치가  가능하다.


$ kubectl  get pod -n kube-system

NAME                                        READY  STATUS   RESTARTS  AGE
aws-load-balancer-controller-8684f5455c-2gkzd 1/1  Running  0         5d21h

aws-load-balancer-controller-8684f5455c-mrzsw 1/1  Running  0         10d

metrics-server-8cc45cd8d-5xvt7              1/1    Running  0         2m58s

$ kubectl  top node

NAME                                           CPU(cores)  CPU%   MEMORY(bytes) MEMORY%
ip-192-168-10-147.ap-northeast-2.compute.internal 64m      3%     1124Mi        15%

ip-192-168-20-156.ap-northeast-2.compute.internal 39m      2%     897Mi         12%

▣ 모든  설정을  완료  후  정상적으로   Metrics-Server의 역할을 수행하는   Pod 오브젝트가   Running 상태인지  확인한다.

▣ kubectl top node 명령어가  정상적으로   실행 될  경우  Metrics-Server 구성이 완료 된  상태.
~~~

### 판독 불확실성

- Text Layer가 `-f`의 hyphen을 Unicode dash로 반환했으나 Rendering은 ASCII `-f`로 확인했다.

## PDF p.254

- 원본: [[40_자료/강의 자료/Kubernetes.pdf#page=254|Kubernetes.pdf p.254]]
- 정보 유형: Text, YAML/설정
- PowerPoint outline: slide 264 (PDF page와 불일치)

### YAML·설정

~~~text
           Kubernetes         AutoScaling         (  Horizontal       Pod    AutoScaler         )



                                                               spec:
< 작업대상    : hpa-autoscaling.yml  >
                                                                 replicas: 1

apiVersion: v1                                                   selector:
kind: Service                                                      matchLabels:

metadata:                                                           app: scale-app

  name: scale-svc                                                template:
  namespace: delivery                                              metadata:

spec:                                                               labels:

  type: ClusterIP                                                     app: scale-app
  selector:                                                        spec:

    app: scale-app                                                  containers:

  ports:                                                              - name: scale-app
  - port: 80                                                            image: chlzzz/kube-image:hpa

    targetPort: 80                                                    resources:

---                                                                     limits:
                                                                          memory: 100Mi

# Service의 Type은 내부 연결을  통해  TEST할 예정이므로   ClusterIP로 정의                  cpu: 200m

# Resources 속성의 Request와 Limit의 값은 동일하게   설정                            requests:
# Guaranteed Class : Memory:100Mi, CPU:200M                               memory: 100Mi

                                                                          cpu: 200m
~~~

### Visual 의미

- 여러 열에 배치된 Manifest·설명은 Text Layer의 선형 순서만으로 읽지 않는다. Rendering의 좌→우 배치, 들여쓰기와 연결선을 함께 기준으로 한다.

### 판독 불확실성

- PDF p.254 = PowerPoint outline slide 264. PDF p.246 앞에서 내부 slide 247–255가 생략된 번호 체계를 이어받는다.

## PDF p.255

- 원본: [[40_자료/강의 자료/Kubernetes.pdf#page=255|Kubernetes.pdf p.255]]
- 정보 유형: Text, YAML/설정, 명령/출력, 표형 정보
- PowerPoint outline: slide 265 (PDF page와 불일치)

### YAML·설정 및 명령·출력

~~~text
           Kubernetes         AutoScaling         (  Horizontal       Pod    AutoScaler         )




< 작업대상    : hpa-test.yml  >

apiVersion: autoscaling/v2

kind: HorizontalPodAutoscaler
metadata:

  name: my-hpa
                              $  kubectl apply  -f autoscaling/
  namespace: delivery
                              service/scale-svc created
spec:
                              deployment.apps/scale-deploy created
  scaleTargetRef:
                              horizontalpodautoscaler.autoscaling/my-hpa created
    apiVersion: apps/v1
                              $  kubectl get hpa  -n delivery
    kind: Deployment
                              NAME    REFERENCE               TARGETS  MINPODS   MAXPODS  REPLICAS  AGE
    name: scale-deploy
                              my-hpa  Deployment/scale-deploy 0%/10%   1         5        1         21s
  minReplicas: 1
  maxReplicas: 5
                              ▣  HPA를 정의  후 hpa 오브젝트  정보를   확인 TARGETS의 데이터는   몇분이  흐른  뒤 다시확인한다.
  metrics:
                              ▣  현재 HPA를  구성한  Deployment의 파드 전체의  CPU 사용량을   수집하는데   시간이  필요하다.
  - type: Resource
    resource:
     name: cpu
     target:
       type: Utilization

       averageUtilization: 10
~~~

### Visual 의미

- 여러 열에 배치된 Manifest·설명은 Text Layer의 선형 순서만으로 읽지 않는다. Rendering의 좌→우 배치, 들여쓰기와 연결선을 함께 기준으로 한다.

### 판독 불확실성

- PDF p.255 = PowerPoint outline slide 265. PDF p.246 앞에서 내부 slide 247–255가 생략된 번호 체계를 이어받는다.

## PDF p.256

- 원본: [[40_자료/강의 자료/Kubernetes.pdf#page=256|Kubernetes.pdf p.256]]
- 정보 유형: Text, 명령/출력, 표형 정보
- PowerPoint outline: slide 266 (PDF page와 불일치)

### 명령·출력

~~~text
           Kubernetes         AutoScaling         (  Horizontal       Pod    AutoScaler         )






[ 1번  Terminal ]  : Pod 오브젝트    부하도   증가  작업

$ kubectl  run -i --tty --rm  debug --image=chlzzz/kube-image:debug   --restart=Never   -n delivery --  sh

▣ Debug 전용  Pod를 하나 생성  후  생성 된  Pod 내부 Container로 접속

/ # while  true; do wget  -q -O - $SCALE_SVC_SERVICE_HOST:$SCALE_SVC_SERVICE_PORT    >  /dev/null; done

▣ 무한으로   wget 명령어를  이용하여   Pod 오브젝트의   부하도를  증가시킨다.

▣ 목표  평균  CPU 사용률을  만족  한 경우  작업을   중지한다.


[ 2번  Terminal ]  : HPA 모니터링    작업  ( 30초  주기로   HPA  오브젝트의    정보를   확인   )

$ while true;  do kubectl  get hpa -n delivery;  sleep 30;  done

NAME    REFERENCE               TARGETS   MINPODS  MAXPODS  REPLICAS  AGE

my-hpa  Deployment/scale-deploy  0%/10%   1        5        1         10m

NAME    REFERENCE               TARGETS   MINPODS  MAXPODS  REPLICAS  AGE
my-hpa  Deployment/scale-deploy  0%/10%   1        5        1         10m

NAME    REFERENCE               TARGETS   MINPODS  MAXPODS  REPLICAS  AGE

my-hpa  Deployment/scale-deploy 100%/10%  1        5        3         11m

▣ 부하도가   증가함에   따라서  Pod 오브젝트의   수가  함께 증가되는   것을  확인  ( 다음 페이지에서    계속 )
~~~

### 판독 불확실성

- PDF p.256 = PowerPoint outline slide 266. PDF p.246 앞에서 내부 slide 247–255가 생략된 번호 체계를 이어받는다.

## PDF p.257

- 원본: [[40_자료/강의 자료/Kubernetes.pdf#page=257|Kubernetes.pdf p.257]]
- 정보 유형: Text, 명령/출력, 표형 정보
- PowerPoint outline: slide 267 (PDF page와 불일치)

### 명령·출력

~~~text
           Kubernetes         AutoScaling         (  Horizontal       Pod    AutoScaler         )






NAME    REFERENCE               TARGETS  MINPODS  MAXPODS  REPLICAS  AGE

my-hpa  Deployment/scale-deploy 57%/10%  1        5        5         11m

NAME    REFERENCE               TARGETS  MINPODS  MAXPODS  REPLICAS  AGE
my-hpa  Deployment/scale-deploy 58%/10%  1        5        5         12m

NAME    REFERENCE               TARGETS  MINPODS  MAXPODS  REPLICAS  AGE

my-hpa  Deployment/scale-deploy 58%/10%  1        5        5         12m

================ [ 목표 평균 CPU 사용률  만족  ( Pod 부하도 증가  작업  중지  ) ] ================


NAME    REFERENCE               TARGETS  MINPODS  MAXPODS  REPLICAS  AGE
my-hpa  Deployment/scale-deploy 0%/10%   1        5        1         14m

NAME    REFERENCE               TARGETS  MINPODS  MAXPODS  REPLICAS  AGE
my-hpa  Deployment/scale-deploy 0%/10%   1        5        1         15m


▣ REPLICAS의 수가  "5"까지 증가  ( 목표  평균  CPU 사용률 만족  ) / 부하도  작업  중지  후 REPLICAS의 수가  감소하는  것을  확인
▣ Pod 오브젝트   목록도  함께  확인  ( kubectl get pod -n delivery / Pod 확장 (3분) / Pod 축소 (5분) )


$ kubectl  delete -f autoscaling/

▣ 다음  TEST를 위해  HPA TEST에서 사용  한 HPA, Deployment 오브젝트를  삭제한다.
~~~

### 판독 불확실성

- Text Layer가 `-n`의 hyphen을 Unicode dash로 반환했으나 Rendering은 ASCII `-n`으로 확인했다.

## Cluster Autoscaler

## PDF p.258

- 원본: [[40_자료/강의 자료/Kubernetes.pdf#page=258|Kubernetes.pdf p.258]]
- 정보 유형: Text, 도식
- PowerPoint outline: slide 268 (PDF page와 불일치)

### 원자료 내용

~~~text
         Kubernetes         AutoScaling         (  Cluster     AutoScaler        )





◎  EKS Cluster  AutoScaler  동작과정

1. HPA에의한  수평확장이     최대치에   도달하면    Pod는 배포  Node를 배정   받지  못한  Unscheduled Pod ( Pendding ) 상태가 된다.

2. CA는 이러한   Pod들의  상태를   지속  감시하면서    Pendding 상태가  유지   될 경우  Node Group의 ASG Desired Capacity 값을 수정한다.
3. Node Group의 ASG Desired Capacity 값이 증가 될  경우  새로운   Worker Node가 생성되며   Pod를 배포  할  준비를   한다.

4. 새롭게   추가  된 Worker Node의 모든  배포  준비가   완료   될 경우  "kube-scheduler"가 새롭게  추가   된 Node에 Pod를  할당한다.
※  Cluster AutoScaler 단점으로는  AWS ASG 서비스의   의존도가   높아   높은  대기  시간을   갖게된다.   / ( Karpenter 도입  고려  )




        Amazone  EKS                 ③  새로운   Worker Node 생                ②  ASG Desired 수
                                               성                                  정


                                                                                             Cluster
             Worker  Node               Worker Node  (New)      Auto scaling
                                                                                            AutoScaler

                                                       ④   Pod 할당




                                                                      Kube-Scheduler   Pendding Pod


                                                             ①   Node Resource Limit ( Unscheduled Pod )
~~~

### Visual 의미

- Pending Pod 감지 → ASG Desired 조정 → 새 Worker Node 생성 → Pod 할당의 1–4단계 Cluster Autoscaler 흐름이다.

### 판독 불확실성

- PDF p.258 = PowerPoint outline slide 268. PDF p.246 앞에서 내부 slide 247–255가 생략된 번호 체계를 이어받는다.

## PDF p.259

- 원본: [[40_자료/강의 자료/Kubernetes.pdf#page=259|Kubernetes.pdf p.259]]
- 정보 유형: Text, YAML/설정
- PowerPoint outline: slide 269 (PDF page와 불일치)

### YAML·설정

~~~text
           Kubernetes         AutoScaling         (  Cluster     AutoScaler        )




< 작업대상    : ca-autoscaling.yml  >
                                                          template:

[ ※ ASG IRSA 설정 진행  후 TEST ]                                 metadata:
                                                               labels:
apiVersion: apps/v1
                                                                 app: scale-app
kind: Deployment
                                                             spec:
metadata:
                                                               containers:
  name: scale-deploy
                                                               - name: scale-pod
  namespace: delivery
                                                                 image: chlzzz/kube-image:hpa
spec:
                                                                 resources:
  replicas: 3
                                                                   limits:
  selector:
                                                                    memory: 100Mi
    matchLabels:
                                                                    cpu: 1000m
     app: scale-app
                                                                   requests:
                                                                    memory: 100Mi
# T3 Family는 Xlarge, 2Xlarge를 제외하고 전부  물리  1 코어를  지원                cpu: 1000m
# Pod에 할당  할 코어를  1 코어로  지정하여   총 3개  Pod를 배포
# Node 2EA: Running Pod : 2 / Pending Pod : 1
~~~

### Visual 의미

- 여러 열에 배치된 Manifest·설명은 Text Layer의 선형 순서만으로 읽지 않는다. Rendering의 좌→우 배치, 들여쓰기와 연결선을 함께 기준으로 한다.

### 판독 불확실성

- PDF p.259 = PowerPoint outline slide 269. PDF p.246 앞에서 내부 slide 247–255가 생략된 번호 체계를 이어받는다.

## PDF p.260

- 원본: [[40_자료/강의 자료/Kubernetes.pdf#page=260|Kubernetes.pdf p.260]]
- 정보 유형: Text, 명령/출력, 표형 정보
- PowerPoint outline: slide 270 (PDF page와 불일치)

### 명령·출력

~~~text
           Kubernetes         AutoScaling         (  Cluster     AutoScaler        )






$ kubectl  apply -f autoscaling/ca-autoscaling.yml

deployment.apps/scale-deploy created

$ kubectl  get pod -n delivery

NAME                         READY  STATUS    RESTARTS  AGE

scale-deploy-845778775d-ff6x2 1/1   Running   0         6s
scale-deploy-845778775d-k4wf2 1/1   Running   0         7s

scale-deploy-845778775d-zq2k9 0/1   Pending   0         6s

$ kubectl  logs cluster-autoscaler-6cb97f77b4-74crx   -n  kube-system |  grep Final

I0927 06:30:13.902533    1 scale_up.go:405] Final scale-up plan: [{eks-initial-8f5a-bfe1a6bc79d9 2->3 (max: 3)}]


$ kubectl  get nodes

NAME                                           STATUS   ROLES   AGE    VERSION
ip-192-168-10-147.ap-northeast-2.compute.internal Ready <none>  14d    v1.24.16-eks-8ccc7ba

ip-192-168-20-156.ap-northeast-2.compute.internal Ready <none>  14d    v1.24.16-eks-8ccc7ba

ip-192-168-20-158.ap-northeast-2.compute.internal Ready <none>  3m53s  v1.24.16-eks-8ccc7ba

▣ 최초  Running Pod : 2 / Pending Pod : 1 / 새로운 Worker Node 생성 로그 확인 및 생성  된 Worker Node "Ready" 상태 확인

▣ AWS 콘솔에서   ASG Group의 Desired Capacity의 값 "2"에서 "3"으로 변경 확인
~~~

### 판독 불확실성

- PDF p.260 = PowerPoint outline slide 270. PDF p.246 앞에서 내부 slide 247–255가 생략된 번호 체계를 이어받는다.

## PDF p.261

- 원본: [[40_자료/강의 자료/Kubernetes.pdf#page=261|Kubernetes.pdf p.261]]
- 정보 유형: Text, 명령/출력, 표형 정보
- PowerPoint outline: slide 271 (PDF page와 불일치)

### 명령·출력

~~~text
           Kubernetes         AutoScaling         (  Cluster     AutoScaler        )






$ kubectl  get pod -n delivery

NAME                         READY  STATUS    RESTARTS  AGE
scale-deploy-845778775d-ff6x2 1/1   Running   0         86s

scale-deploy-845778775d-k4wf2 1/1   Running   0         87s

scale-deploy-845778775d-zq2k9 1/1   Running   0         86s

$ kubectl  delete -f autoscaling/ca-autoscaling.yml

deployment.apps "scale-deploy" deleted

$ kubectl  logs cluster-autoscaler-6cb97f77b4-74crx   -n  kube-system |  grep Scale-down

I0927 06:49:59.766657    1 actuator.go:161] Scale-down: removing empty node "ip-192-168-20-158"


$ kubectl  get nodes

NAME                                           STATUS   ROLES   AGE    VERSION
ip-192-168-10-147.ap-northeast-2.compute.internal Ready <none>  14d    v1.24.16-eks-8ccc7ba

ip-192-168-20-156.ap-northeast-2.compute.internal Ready <none>  14d    v1.24.16-eks-8ccc7ba

▣ 배포한   Pod를 삭제 후  약 10분정도의   대기시간을   갖고  Worker Node의 목록을 확인한다.

▣ 새롭게   추가 된  Worker Node가 제거가 된  것을  확인 할  수 있다.
~~~

### 판독 불확실성

- PDF p.261 = PowerPoint outline slide 271. PDF p.246 앞에서 내부 slide 247–255가 생략된 번호 체계를 이어받는다.

## 누락·검토 대기

- 선언한 PDF Page 범위의 Text·YAML·명령·출력·Visual 확인은 완료했다.
- 원자료의 Kubernetes·AWS Version과 기술 내용에 대한 최신 공식 문서 검증은 이 Chapter Digest의 범위 밖이다.
- 전체 Index의 Chapter Link와 전 범위 Gap·Overlap 검증은 Index 갱신 단계에서 수행한다.

## 완료 검증

- [x] PDF p.251–p.261 모든 Page를 포함했다.
- [x] Text Layer와 Rendering을 함께 확인했다.
- [x] YAML·명령·표형 출력의 기호와 배치를 원본과 대조했다.
- [x] 도식·삽입 이미지의 관계를 별도 기록했다.
- [x] 판독 불확실성과 원자료 오류 가능성을 숨기지 않았다.
- [ ] 전체 Source Digest Index 통합 검수와 외부 기술 검증
