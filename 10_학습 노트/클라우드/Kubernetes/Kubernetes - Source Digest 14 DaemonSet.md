---
type: source-digest
status: draft
created: 2026-07-21
parent_moc: "[[10_학습 노트/클라우드/Kubernetes/00_Kubernetes MOC]]"
source: "[[40_자료/강의 자료/Kubernetes.pdf]]"
source_pages: "246-250"
digest_role: chapter
digest_index: "[[10_학습 노트/클라우드/Kubernetes/Kubernetes - Source Digest v1]]"
chapter: "14 DaemonSet"
source_hash: F97666865E22749C47640689B5C41DEE38476A40312A53915F60B4F6A4330D24
source_version: "PowerPoint PDF; 266 pages; metadata created 2024-07-18"
coverage_status: partial
extraction_method: "pdfplumber 0.11.9 text extraction + pypdfium2 render visual review"
---

# Kubernetes - Source Digest 14 DaemonSet

> [!purpose]
> `Kubernetes.pdf` p.246–p.250의 의미 있는 정보를 페이지별로 보존한 Chapter Digest이다. 원자료의 기술적 정확성을 현재 지식으로 검증하거나 몰래 교정하지 않는다.

## Source 식별

- 원자료: [[40_자료/강의 자료/Kubernetes.pdf|Kubernetes.pdf]]
- 대상 범위: PDF p.246–p.250
- 전체 원자료: 266 pages
- SHA-256: `F97666865E22749C47640689B5C41DEE38476A40312A53915F60B4F6A4330D24`
- 추출·검수: `pdfplumber 0.11.9` Text Layer + `pypdfium2` Rendering
- Chapter 경계: DaemonSet 개념과 Fluentd Agent 배포

## Coverage

| PDF 범위 | Text | YAML·명령·표 | Visual | 원본 대조 | 상태 |
|---|---|---|---|---|---|
| p.246–p.250 | 완료 | 완료 | 전체 렌더 검토 | 페이지별 대조 | 상세 변환 완료 / 기술 내용 외부 검증 미수행 |

## 변환 경계

- 아래 고정폭 Transcript는 PDF Text Layer의 Page 배치를 최대한 보존한다.
- YAML·명령·출력은 Rendering으로 기호와 배치를 대조했다. 원자료의 오탈자·잠재적 명령 오류는 임의로 수정하지 않는다.
- Visual 관계는 Text Layer 밖의 화살표·번호·공간 배치를 별도 설명한다.
- `status: draft`는 원자료 변환이 누락됐다는 뜻이 아니라, 전체 Index 통합 검수와 외부 기술 검증이 아직 끝나지 않았다는 뜻이다.

## DaemonSet

## PDF p.246

- 원본: [[40_자료/강의 자료/Kubernetes.pdf#page=246|Kubernetes.pdf p.246]]
- 정보 유형: Cover
- PowerPoint outline: slide 256 (PDF page와 불일치)

### 원자료 내용

~~~text
Kubernetes                          DaemonSet
~~~

### 판독 불확실성

- PDF p.246 = PowerPoint outline slide 256. 내부 slide 247–255는 PDF에 없다.

## PDF p.247

- 원본: [[40_자료/강의 자료/Kubernetes.pdf#page=247|Kubernetes.pdf p.247]]
- 정보 유형: Text, 도식
- PowerPoint outline: slide 257 (PDF page와 불일치)

### 원자료 내용

~~~text
         Kubernetes         DaemonSet          Controller




◎  Kubernetes  DaemonSet


   Kubernetes DaemonSet Controller는 K8s 내부 모든 Worker Node에 동일한  Pod를 생성하는    오브젝트
   DaemonSet Controller는 주로 Logging, Monitering, Networking 등을 위한 Agent를 각 Worker Node에 구성  할 때  사용된다.

   K8s를 구성  시  Worker Node에서 생성되는   "Kube-Proxy"가 가장  대표적인    DaemonSet Controller에 의해 관리되는   Pod이다.

   DaemonSet에의해  관리되는   Pod는 Node 장애시   다른  Node로 퇴거되지    않아야   한다,  이를  위해  자동으로    Toleration 설정이  포함된다.


         Kubernetes   Cluster   ( K8s  )


                    Worker  Node-1              Worker  Node-2              Worker  Node-3
~~~

### Visual 의미

- 각 Worker Node에 하나씩 Agent Pod가 배포되고 공통 수집 대상으로 연결되는 DaemonSet 배치 구조이다.

### 판독 불확실성

- PDF p.247 = PowerPoint outline slide 257. PDF p.246 앞에서 내부 slide 247–255가 생략된 번호 체계를 이어받는다.

## EX.1 Fluentd Pod 배포

## PDF p.248

- 원본: [[40_자료/강의 자료/Kubernetes.pdf#page=248|Kubernetes.pdf p.248]]
- 정보 유형: Text, YAML/설정
- PowerPoint outline: slide 258 (PDF page와 불일치)

### YAML·설정

~~~text
           Kubernetes         DaemonSet          Controller       (  EX.1    : Fluentd      Pod    배포      )




< 작업대상    : daemonset-test.yml  >
                                                           spec:
                                                            containers:
apiVersion: apps/v1
                                                            - name: fluentd-elasticsearch
kind: DaemonSet
                                                              image: quay.io/fluentd_elasticsearch/fluentd:v2.5.2
metadata:
                                                              resources:
  name: fluentd-elasticsearch
                                                                limits:
  namespace: logging
                                                                  cpu: 100m
  labels:
                                                                  memory: 200Mi
    k8s-app: fluentd-logging
                                                                requests:
spec:
                                                                  cpu: 100m
  selector:
                                                                  memory: 200Mi
    matchLabels:
                                                              volumeMounts:
     name: fluentd-elasticsearch
                                                              - name: varlog
  template:
                                                                mountPath: /var/log
    metadata:
                                                            volumes:
     labels:
                                                            - name: varlog
       name: fluentd-elasticsearch
                                                              hostPath:
# Deployment Controller 배포작업과 유사한  구조를  갖는다.                    path: /var/log
# NodeAffinity / Tolerations 설정도 가능하다.
~~~

### Visual 의미

- 여러 열에 배치된 Manifest·설명은 Text Layer의 선형 순서만으로 읽지 않는다. Rendering의 좌→우 배치, 들여쓰기와 연결선을 함께 기준으로 한다.

### 판독 불확실성

- PDF p.248 = PowerPoint outline slide 258. PDF p.246 앞에서 내부 slide 247–255가 생략된 번호 체계를 이어받는다.

## PDF p.249

- 원본: [[40_자료/강의 자료/Kubernetes.pdf#page=249|Kubernetes.pdf p.249]]
- 정보 유형: Text, 명령/출력, 표형 정보
- PowerPoint outline: slide 259 (PDF page와 불일치)

### 명령·출력

~~~text
           Kubernetes         DaemonSet          Controller       (  EX.1    : Fluentd      Pod    배포      )






$ kubectl  create namespace  logging

$ kubectl  apply -f daemonset/daemonset-test.yml

daemonset.apps/fluentd-elasticsearch created

▣ DaemonSet Controller를 활용하여  전체 Worker Node에 Fluentd Agent Pod를 배포한다.

▣ Fluentd : OpenSource Data(Log) Collector Program ( K8s에서 Worker Node의 로그를 수집하는데 자주사용  된다.  )

$ kubectl  get ds -n logging

NAME                  DESIRED  CURRENT  READY  UP-TO-DATE  AVAILABLE  NODE SELECTOR  AGE

fluentd-elasticsearch 2        2        2      2           2          <none>         70s

▣ DaemonSet Controller의 DESIRED / CURRENT / READY 확인 ( 현재 Worker Node는 2개가 운영중인 상태  )

$ kubectl  get pod -n logging  -o wide

NAME                       READY   STATUS   RESTARTS  AGE  IP              NODE              NOMINATED NODE

READINESS GATES

fluentd-elasticsearch-h2xkn 1/1    Running  0         39s  192.168.10.156  ip-192-168-10-147 <none> <none>
fluentd-elasticsearch-pzqmq 1/1    Running  0         39s  192.168.20.51   ip-192-168-20-156 <none> <none>


▣ Fluentd Agent Pod가 운영중인  각 Worker Node에 배포된것을   확인한다.
~~~

### 판독 불확실성

- PDF p.249 = PowerPoint outline slide 259. PDF p.246 앞에서 내부 slide 247–255가 생략된 번호 체계를 이어받는다.

## PDF p.250

- 원본: [[40_자료/강의 자료/Kubernetes.pdf#page=250|Kubernetes.pdf p.250]]
- 정보 유형: Text, 명령/출력
- PowerPoint outline: slide 260 (PDF page와 불일치)

### 명령·출력

~~~text
           Kubernetes         DaemonSet          Controller       (  EX.1    : Fluentd      Pod    배포      )






$ kubectl  exec -it fluentd-elasticsearch-h2xkn   -n logging  -- sh

# tail /var/log/messages

Sep 25 11:27:42 ip-192-168-10-147 kubelet: I0925 11:27:42.7726732955 kubelet.go:2132]
Sep 25 11:28:30 ip-192-168-10-147 dhclient[2165]: XMT: Solicit on eth0, interval 108760ms.

Sep 25 11:30:18 ip-192-168-10-147 dhclient[2165]: XMT: Solicit on eth0, interval 115230ms.

Sep 25 11:31:54 ip-192-168-10-147 dhclient[2130]: DHCPREQUEST on eth0 to 192.168.10.1 port 67 (xid=0xb741a3d)
Sep 25 11:31:54 ip-192-168-10-147 dhclient[2130]: DHCPACK from 192.168.10.1 (xid=0xb741a3d)

Sep 25 11:31:54 ip-192-168-10-147 NET: dhclient: Locked /run/dhclient/resolv.lock

Sep 25 11:31:54 ip-192-168-10-147 dhclient[2130]: bound to 192.168.10.147 -- renewal in 1692 seconds.
Sep 25 11:32:14 ip-192-168-10-147 dhclient[2165]: XMT: Solicit on eth0, interval 123400ms.

Sep 25 11:34:17 ip-192-168-10-147 dhclient[2165]: XMT: Solicit on eth0, interval 130780ms.

Sep 25 11:36:28 ip-192-168-10-147 dhclient[2165]: XMT: Solicit on eth0, interval 113760ms.

▣ Fluentd Agent Pod에 접속 후 수집  된  Messages Log 기록을 확인한다.

▣ Fluentd Agent에서 수집  된 Log는 CloudWatch, Elasticsearch 등으로 전송하여  통합  로그  모니터링  환경을   구축 할  수도  있다.

$ kubectl  delete -f daemonset/daemonset-test.yml

daemonset.apps "fluentd-elasticsearch" deleted

▣ TEST에 사용한   Daemonset 오브젝트 삭제를   진행한다.
~~~

### 판독 불확실성

- PDF p.250 = PowerPoint outline slide 260. PDF p.246 앞에서 내부 slide 247–255가 생략된 번호 체계를 이어받는다.

## 누락·검토 대기

- 선언한 PDF Page 범위의 Text·YAML·명령·출력·Visual 확인은 완료했다.
- 원자료의 Kubernetes·AWS Version과 기술 내용에 대한 최신 공식 문서 검증은 이 Chapter Digest의 범위 밖이다.
- 전체 Index의 Chapter Link와 전 범위 Gap·Overlap 검증은 Index 갱신 단계에서 수행한다.

## 완료 검증

- [x] PDF p.246–p.250 모든 Page를 포함했다.
- [x] Text Layer와 Rendering을 함께 확인했다.
- [x] YAML·명령·표형 출력의 기호와 배치를 원본과 대조했다.
- [x] 도식·삽입 이미지의 관계를 별도 기록했다.
- [x] 판독 불확실성과 원자료 오류 가능성을 숨기지 않았다.
- [ ] 전체 Source Digest Index 통합 검수와 외부 기술 검증
