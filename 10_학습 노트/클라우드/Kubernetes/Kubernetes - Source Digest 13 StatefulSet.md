---
type: source-digest
status: draft
created: 2026-07-21
parent_moc: "[[10_학습 노트/클라우드/Kubernetes/00_Kubernetes MOC]]"
source: "[[40_자료/강의 자료/Kubernetes.pdf]]"
source_pages: "235-245"
digest_role: chapter
digest_index: "[[10_학습 노트/클라우드/Kubernetes/Kubernetes - Source Digest v1]]"
chapter: "13 StatefulSet"
source_hash: F97666865E22749C47640689B5C41DEE38476A40312A53915F60B4F6A4330D24
source_version: "PowerPoint PDF; 266 pages; metadata created 2024-07-18"
coverage_status: partial
extraction_method: "pdfplumber 0.11.9 text extraction + pypdfium2 render visual review"
---

# Kubernetes - Source Digest 13 StatefulSet

> [!purpose]
> `Kubernetes.pdf` p.235–p.245의 의미 있는 정보를 페이지별로 보존한 Chapter Digest이다. 원자료의 기술적 정확성을 현재 지식으로 검증하거나 몰래 교정하지 않는다.

## Source 식별

- 원자료: [[40_자료/강의 자료/Kubernetes.pdf|Kubernetes.pdf]]
- 대상 범위: PDF p.235–p.245
- 전체 원자료: 266 pages
- SHA-256: `F97666865E22749C47640689B5C41DEE38476A40312A53915F60B4F6A4330D24`
- 추출·검수: `pdfplumber 0.11.9` Text Layer + `pypdfium2` Rendering
- Chapter 경계: StatefulSet·Headless Service·MySQL·Persistent Volume

## Coverage

| PDF 범위 | Text | YAML·명령·표 | Visual | 원본 대조 | 상태 |
|---|---|---|---|---|---|
| p.235–p.245 | 완료 | 완료 | 전체 렌더 검토 | 페이지별 대조 | 상세 변환 완료 / 기술 내용 외부 검증 미수행 |

## 변환 경계

- 아래 고정폭 Transcript는 PDF Text Layer의 Page 배치를 최대한 보존한다.
- YAML·명령·출력은 Rendering으로 기호와 배치를 대조했다. 원자료의 오탈자·잠재적 명령 오류는 임의로 수정하지 않는다.
- Visual 관계는 Text Layer 밖의 화살표·번호·공간 배치를 별도 설명한다.
- `status: draft`는 원자료 변환이 누락됐다는 뜻이 아니라, 전체 Index 통합 검수와 외부 기술 검증이 아직 끝나지 않았다는 뜻이다.

## StatefulSet

## PDF p.235

- 원본: [[40_자료/강의 자료/Kubernetes.pdf#page=235|Kubernetes.pdf p.235]]
- 정보 유형: Cover

### 원자료 내용

~~~text
Kubernetes                          Statefulset
~~~

## PDF p.236

- 원본: [[40_자료/강의 자료/Kubernetes.pdf#page=236|Kubernetes.pdf p.236]]
- 정보 유형: Text, 도식

### 원자료 내용

~~~text
         Kubernetes         Statefulset       Controller       ( Pod     +  Persistent       Volume       )






◎  Kubernetes  Statefulset  Controller

   Statefulset은 Data 보관이  필요한  Pod와  Persistent Volume을 조합하여  배포하기위한     Controller ( Deployment : Stateless )

   Statefulset은 Replica에서 지정한   수 만큼  Pod 오브젝트가    생성되며    각 Pod에  대응하는   Persistent Volume이 함께  생성된다.
   Statefulset에서는 Pod와  그에  대응하는    Persistent Volume을 하나의  관리  단위로   취급한다.

   Statefulset 제거 시 Pod는  삭제되지만    그에  대응하는    Persistent Volume은 삭제되지  않는다.



                                Kubernetes    Cluster
                                                                      Statefulset  Controller
                                                                    ( Pod,  PVC Object Deploy  )

  External   Storage


                                                                                  ClusterIP:  None
                                                                                   Headless Mode





  Storage
  Server
~~~

### Visual 의미

- StatefulSet Controller가 순번이 있는 Pod와 각 PVC/PV를 대응시키고, Headless Service와 외부 Storage를 연결하는 구조이다.

## EX.1 MySQL DBMS 배포

## PDF p.237

- 원본: [[40_자료/강의 자료/Kubernetes.pdf#page=237|Kubernetes.pdf p.237]]
- 정보 유형: Text, 명령/출력

### 명령·출력

~~~text
           Kubernetes         Statefulset       Controller       ( EX.1    : MySQL        DBMS       배포     )






$ kubectl  create namespace  mysql

$ kubectl  get ns mysql

NAME   STATUS  AGE
mysql  Active  10s


$ kubectl  create secret  generic mysql-secret  --from-literal  MYSQL_ROOT_PASSWORD=root   -n mysql

$ kubectl  get secret -n  mysql

NAME                TYPE                               DATA  AGE
mysql-secret        Opaque                             1     8s


▣ 새로운   NameSpace mysql을 생성 후 MySQL DBMS Statefulset 배포 작업을 진행한다.
▣ MySQL 관리자  패스워드   환경변수는   Secret 오브젝트를  정의하여   작업을  진행한다.   ( MySQL 관리자  패스워드  : root 지정  )


$ kubectl  get sc

NAME          PROVISIONER           RECLAIMPOLICY  VOLUMEBINDINGMODE    ALLOWVOLUMEEXPANSION AGE
ebs-sc        ebs.csi.aws.com       Delete         WaitForFirstConsumer false                3s

gp2 (default) kubernetes.io/aws-ebs Delete         WaitForFirstConsumer false                7d5h

▣ Pod 오브젝트가   사용  할 Volume은 EBS Dynamic Provisioning을 사용 할 예정

▣ EBS StorageClass 오브젝트가  존재하는지   확인한다.   ( SC 오브젝트가  존재하지   않을  경우  반드시  새로  생성  )
~~~

### 판독 불확실성

- 원자료는 Demo용 MySQL Root Password를 `root`로 명시한다. 실제 운영 자격증명으로 해석하지 않는다.

## PDF p.238

- 원본: [[40_자료/강의 자료/Kubernetes.pdf#page=238|Kubernetes.pdf p.238]]
- 정보 유형: Text, YAML/설정

### YAML·설정

~~~text
           Kubernetes         Statefulset       Controller       ( EX.1    : MySQL        DBMS       배포     )




< 작업대상    : sts-mysql.yml  >
                                                       apiVersion: apps/v1
                                                       kind: StatefulSet
apiVersion: v1
                                                       metadata:
kind: Service
                                                         name: mysql-app
metadata:
  name: mysql-service # Service 이름정의  ( DNS 등록이름  )      namespace: mysql
                                                       spec:
  labels:
                                                         selector:
    app: mysql-sts
                                                           matchLabels:
  namespace: mysql
                                                            app: mysql-sts # Pod Template 이름 정의
spec:
                                                         serviceName: mysql-service # Pod와 연결 할 Service 이름 정의
  ports:
                                                         replicas: 2
  - port: 3306
                                                         volumeClaimTemplates: # PVC Template 정의
    name: mysql
                                                         - metadata:
  clusterIP: None     # ClusterIP Headless Mode
                                                            name: pvc # PVC 오브젝트   이름 정의
  selector:
    app: mysql-sts    # Statefulset Pod Template 연결        spec:
                                                            storageClassName: ebs-sc # StorageClass 이름 정의
                                                            accessModes: [ "ReadWriteOnce" ] # 단일 Node에서만 접근  허용
                                                            resources:
                                                              requests:
                                                                storage: 5Gi # Volume Size 정의
~~~

### Visual 의미

- 여러 열에 배치된 Manifest·설명은 Text Layer의 선형 순서만으로 읽지 않는다. Rendering의 좌→우 배치, 들여쓰기와 연결선을 함께 기준으로 한다.

## PDF p.239

- 원본: [[40_자료/강의 자료/Kubernetes.pdf#page=239|Kubernetes.pdf p.239]]
- 정보 유형: Text, YAML/설정

### YAML·설정

~~~text
          Kubernetes         Statefulset       Controller       ( EX.1    : MySQL        DBMS       배포     )



[ ※ Spec 영역에  이어서  작성  ]

                                                              volumeMounts:              # Container Mount 영역

 template:                    # Template 영역 ( ★ )             - name: pvc                # PVC 오브젝트   이름 정의
   metadata:                                                    mountPath: /var/lib/mysql # Container Mount Point

    labels:

      app: mysql-sts          # Teamplate 이름 정의               livenessProbe:
   spec:                                                        exec:

    containers:                                                   command:

    - name: mysql             # Container 이름 정의                   - ls
      image: mysql:5.7        # Container 이미지 정의                  - /var/lib/mysql

      args:                                                     initialDelaySeconds: 10

        - "--ignore-db-dir=lost+found"                          periodSeconds: 10
      ports:                                                    successThreshold: 1

      - containerPort: 3306   # Container Port번호 지정             failureThreshold: 3

        name: mysql                                             timeoutSeconds: 5
      envFrom:                # Container 환경변수  정의

                                                         # EXEC 핸들러  정의  ( "/var/lib/myslq" 디렉터리가 존재하는지   확인  )
        - secretRef:
            name: mysql-secret # Secret 오브젝트의 이름지정       # Pod 배포  후 10초 뒤  실행 ( 실행  주기  : 10초 )
                                                         # 5번 연속  상태검사에   실패했을   경우  Container 재시작

                                                         # 상태  검사  성공  시 실패횟수는   초기화
~~~

### Visual 의미

- 여러 열에 배치된 Manifest·설명은 Text Layer의 선형 순서만으로 읽지 않는다. Rendering의 좌→우 배치, 들여쓰기와 연결선을 함께 기준으로 한다.

## PDF p.240

- 원본: [[40_자료/강의 자료/Kubernetes.pdf#page=240|Kubernetes.pdf p.240]]
- 정보 유형: Text, 명령/출력, 표형 정보

### 명령·출력

~~~text
           Kubernetes         Statefulset       Controller       ( EX.1    : MySQL        DBMS       배포     )






$ kubectl  apply -f statefulset/sts-mysql.yml

service/mysql-service created
statefulset.apps/mysql-app created


$ kubectl  get all -n mysql

NAME            READY   STATUS   RESTARTS  AGE
pod/mysql-app-0 1/1     Running  1         41s

pod/mysql-app-1 1/1     Running  0         31s


NAME                                       TYPE       CLUSTER-IP     EXTERNAL-IP  PORT(S)   AGE

service/mysql-service                      ClusterIP  None           <none>       3306/TCP  41s


NAME                      READY   AGE
statefulset.apps/mysql-app 2/2    41s


▣ CLUSTER-IP가 할당되지  않은  Service 오브젝트  확인  ( mysql-service )

▣ Pod의 이름은   statfulset의 이름 + 순서번호로   정의된다.

▣ Statefulset Controller에 의해 관리되는  Pod는 순차적으로    생성되므로   약간의  대기  시간이  필요하다.
~~~

## PDF p.241

- 원본: [[40_자료/강의 자료/Kubernetes.pdf#page=241|Kubernetes.pdf p.241]]
- 정보 유형: Text, 명령/출력, 표형 정보

### 명령·출력

~~~text
           Kubernetes         Statefulset       Controller       ( EX.1    : MySQL        DBMS       배포     )






$ kubectl  get pv,pvc -n  mysql

NAME                        CAPACITY ACCESS MODES RECLAIM POLICY  STATUS  CLAIM                 STORAGECLASS
persistentvolume/pvc-19922090 5Gi   RWO           Delete          Bound   mysql/pvc-mysql-app-1 ebs-sc

persistentvolume/pvc-eeaa80d5 5Gi   RWO           Delete          Bound   mysql/pvc-mysql-app-0 ebs-sc

NAME                                STATUS     VOLUME             CAPACITY  ACCESS MODES STORAGECLASS

persistentvolumeclaim/pvc-mysql-app-0 Bound    pvc-eeaa80d5-ed52  5Gi       RWO          ebs-sc

persistentvolumeclaim/pvc-mysql-app-1 Bound    pvc-19922090-6f32  5Gi       RWO          ebs-sc

▣ Statefulset Controller에의해 생성 된  PV, PVC 오브젝트를  확인


$ kubectl  exec -it mysql-app-0  -n mysql  -- bash
bash-4.2# mysql -u root -p mysql / Enter password: root

mysql> create database StatefulSet_DB;

mysql> show databases;
+--------------------+

| StatefulSet_DB   |

+--------------------+

▣ Statefulset에 의해 관리되는   Pod의 컨테이너로   접속하여   새로운  데이터베이스를    생성  후  확인
~~~

## PDF p.242

- 원본: [[40_자료/강의 자료/Kubernetes.pdf#page=242|Kubernetes.pdf p.242]]
- 정보 유형: Text, 명령/출력, 표형 정보

### 명령·출력

~~~text
           Kubernetes         Statefulset       Controller       ( EX.1    : MySQL        DBMS       배포     )






$ kubectl  delete -f statefulset/sts-mysql.yml

service "mysql-service" deleted
statefulset.apps "mysql-app" deleted



$ kubectl  get pv,pvc -n  mysql
NAME                        CAPACITY ACCESS MODES RECLAIM POLICY  STATUS  CLAIM                 STORAGECLASS

persistentvolume/pvc-19922090 5Gi   RWO           Delete          Bound   mysql/pvc-mysql-app-1 ebs-sc

persistentvolume/pvc-eeaa80d5 5Gi   RWO           Delete          Bound   mysql/pvc-mysql-app-0 ebs-sc

NAME                                STATUS     VOLUME             CAPACITY  ACCESS MODES STORAGECLASS

persistentvolumeclaim/pvc-mysql-app-0 Bound    pvc-eeaa80d5-ed52  5Gi       RWO          ebs-sc
persistentvolumeclaim/pvc-mysql-app-1 Bound    pvc-19922090-6f32  5Gi       RWO          ebs-sc



$ kubectl  apply -f statefulset/sts-mysql.yml
service/mysql-service created

statefulset.apps/mysql-app created

▣ Statefulset 오브젝트의  Persistent Volume 영속성 유지  테스트를   위해 Statefulset 오브젝트를   삭제

▣ Statefulset 오브젝트를  삭제하여도    Persistent Volume은 삭제되지 않는  것을  확인한다.
~~~

## PDF p.243

- 원본: [[40_자료/강의 자료/Kubernetes.pdf#page=243|Kubernetes.pdf p.243]]
- 정보 유형: Text, 명령/출력, 표형 정보

### 명령·출력

~~~text
           Kubernetes         Statefulset       Controller       ( EX.1    : MySQL        DBMS       배포     )






$ kubectl  exec -it mysql-app-0  -n mysql  -- bash

bash-4.2# mysql -u root -p mysql
Enter password: root


mysql> show databases;
+--------------------+

| Database         |

+--------------------+
| information_schema |

| StatefulSet_DB   |

| mysql            |
| performance_schema |

| sys              |

+--------------------+
5 rows in set (0.01 sec)


▣ Statefulset 오브젝트를  재  배포  후 Pod의 컨테이너로   접속  후 DB 목록을  확인한다.   ( Persistent Volume 데이터 유지 )
▣ mysql-app-1 Pod가 연결하는  Persistent Volume에는 물리적으로   서로 다른  Volume이므로  해당  DB정보가  존재하지   않는다.

▣ 동기화   작업을  구현하기  위해서는   MQ 서비스를   사용하거나   DBMS Replication 등을 추가로 구현해야한다.
~~~

## PDF p.244

- 원본: [[40_자료/강의 자료/Kubernetes.pdf#page=244|Kubernetes.pdf p.244]]
- 정보 유형: Text, 명령/출력
- PowerPoint outline: slide 245 (PDF page와 불일치)

### 명령·출력

~~~text
           Kubernetes         Statefulset       Controller       ( EX.1    : MySQL        DBMS       배포     )






/ # ping mysql-app-0.mysql-service.mysql    -c 4

PING mysql-service.mysql (10.244.1.191): 56 data bytes
64 bytes from 192.168.10.231: seq=0 ttl=62 time=0.529 ms

64 bytes from 192.168.10.231: seq=1 ttl=62 time=0.375 ms

64 bytes from 192.168.10.231: seq=2 ttl=62 time=0.347 ms
64 bytes from 192.168.10.231: seq=3 ttl=62 time=0.398 ms


/ # ping mysql-app-1.mysql-service.mysql    -c 4

PING mysql-service.mysql (10.244.2.202): 56 data bytes
64 bytes from 192.168.20.51: seq=0 ttl=64 time=0.371 ms

64 bytes from 192.168.20.51: seq=1 ttl=64 time=0.089 ms

64 bytes from 192.168.20.51: seq=2 ttl=64 time=0.165 ms
64 bytes from 192.168.20.51: seq=3 ttl=64 time=0.080 ms


▣ Service 오브젝트와   연결  된 Pod의 이름을  직접  지정  할 경우  지정  된 Pod와 고정적인   통신이가능하다.
▣ Statefulset에의해  관리되는  Pod의 경우  Pod 재시작이   진행되어도   항상  동일한  이름부여  규칙에따라    고정 된  Pod이름을  부여받는다.

▣ 고정  된 Pod의  이름을  사용  할 경우  Pod로 요청처리를   진행하는   클라이언트는   항상  동일한  Service 오브젝트  이름으로   요청  처리를  진행  할 수  있다.

▣ EX: DBMS를 운영하는   Pod의 접근  이름이  달라질  경우  해당  DBMS Pod를 사용하는  Application의 소스코드를   수정해야하는   상황이   발생한다.
~~~

### 판독 불확실성

- PDF page와 PowerPoint outline slide 번호가 처음 어긋난다: PDF p.244 = slide 245. 내부 slide 244는 PDF에 없다.

## PDF p.245

- 원본: [[40_자료/강의 자료/Kubernetes.pdf#page=245|Kubernetes.pdf p.245]]
- 정보 유형: Text, 명령/출력
- PowerPoint outline: slide 246 (PDF page와 불일치)

### 명령·출력

~~~text
           Kubernetes         Statefulset       Controller       ( EX.1    : MySQL        DBMS       배포     )






$ kubectl  delete -f statefulset/sts-mysql.yml

service "mysql-service" deleted
statefulset.apps "mysql-app" deleted


$ kubectl  get all -n mysql

No resources found in mysql namespace.

$ kubectl  delete secret  mysql-secret -n  mysql

secret "mysql-secret" deleted

$ kubectl  delete pvc pvc-mysql-app-0  -n  mysql

persistentvolumeclaim "pvc-mysql-app-0" deleted


$ kubectl  delete pvc pvc-mysql-app-1  -n  mysql

persistentvolumeclaim "pvc-mysql-app-1" deleted

$ kubectl  get pv,pvc -n  mysql

No resources found

$ kubectl  delete namespace  mysql

▣ TEST에 사용한   Statefulset, Secrt, PV, PVC, namespace 오브젝트 삭제를 진행한다.
~~~

### 판독 불확실성

- PDF p.245 = PowerPoint outline slide 246.

## 누락·검토 대기

- 선언한 PDF Page 범위의 Text·YAML·명령·출력·Visual 확인은 완료했다.
- 원자료의 Kubernetes·AWS Version과 기술 내용에 대한 최신 공식 문서 검증은 이 Chapter Digest의 범위 밖이다.
- 전체 Index의 Chapter Link와 전 범위 Gap·Overlap 검증은 Index 갱신 단계에서 수행한다.

## 완료 검증

- [x] PDF p.235–p.245 모든 Page를 포함했다.
- [x] Text Layer와 Rendering을 함께 확인했다.
- [x] YAML·명령·표형 출력의 기호와 배치를 원본과 대조했다.
- [x] 도식·삽입 이미지의 관계를 별도 기록했다.
- [x] 판독 불확실성과 원자료 오류 가능성을 숨기지 않았다.
- [ ] 전체 Source Digest Index 통합 검수와 외부 기술 검증
