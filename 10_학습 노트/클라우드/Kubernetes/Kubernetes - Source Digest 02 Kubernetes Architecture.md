---
type: source-digest
status: stable
created: 2026-07-21
parent_moc: "[[10_학습 노트/클라우드/Kubernetes/00_Kubernetes MOC]]"
source: "[[40_자료/강의 자료/Kubernetes.pdf]]"
source_pages: "4-7"
digest_role: chapter
digest_index: "[[10_학습 노트/클라우드/Kubernetes/Kubernetes - Source Digest v1]]"
chapter: "02 Kubernetes Architecture"
source_hash: F97666865E22749C47640689B5C41DEE38476A40312A53915F60B4F6A4330D24
source_version: "PowerPoint PDF; 266 pages; metadata created 2024-07-18"
coverage_status: complete
extraction_method: "pdfplumber 0.11.9 text extraction + pypdfium2 render visual review"
reviewed_on: 2026-07-21
---

# Kubernetes - Source Digest 02 Kubernetes Architecture

> [!purpose]
> [[40_자료/강의 자료/Kubernetes.pdf|Kubernetes.pdf]] p.4-p.7의 본문과 Architecture·Pod 생성 Sequence 도식을 보존한 Chapter Digest다.

## Coverage

| Page | Text | Visual | 원본 대조 | 정보 유형 |
|---:|---|---|---|---|
| p.4 | 완료 | 완료 | 완료 | Chapter 표지 |
| p.5 | 완료 | 완료 | 완료 | 설명·Cluster 도식 |
| p.6 | 완료 | 완료 | 완료 | Architecture·기능 도식 |
| p.7 | 완료 | 완료 | 완료 | Pod 생성 Sequence 도식 |

## p.4 - Kubernetes Architecture 표지

- 원자료: [[40_자료/강의 자료/Kubernetes.pdf#page=4|Kubernetes.pdf p.4]]
- `Kubernetes Architecture` Chapter의 표지다.
- 별도의 본문·Code·정보성 도식은 없다.

## p.5 - Kubernetes Container Orchestration Tool

- 원자료: [[40_자료/강의 자료/Kubernetes.pdf#page=5|Kubernetes.pdf p.5]]

### 원자료 내용

- Kubernetes를 Google이 2014년에 Open Source로 공개한 사실상의 표준 Container Orchestration 도구라고 소개한다.
- 자료는 Kubernetes에 Google의 Container 운영 노하우가 담겨 있다고 설명한다.
- MSA 구조의 Container 배포, Service 장애 복구 등 Container Service 운영 기능을 지원한다고 설명한다.
- Cloud 운영 기능·Component를 지원해 다른 Cloud 운영 도구와 연동하기 쉽고 확장성이 높다고 설명한다.
- Google·Red Hat 등이 Source Code 개발에 참여해 안정성과 신뢰성이 높다고 설명한다.
- Orchestration Component 대부분이 Kubernetes를 기준으로 개발·갱신된다고 설명한다.
- CNCF가 관리하는 Open Source로 소개하고 `https://landscape.cncf.io/`를 제시한다.

### 도식·이미지 의미

```text
Application 실행·배포 명세 [Manifest File]
→ Kubernetes Master Node
→ Worker Node 1 / 2 / 3
→ 각 Worker의 Docker Engine
→ Docker Container들
```

- Manifest File에서 Cluster로 전달되는 배포 흐름과 세 Worker Node의 Container 실행 구조를 그린다.
- 도식은 `Master Node`, `Docker Engine`, `Docker Container`라는 원자료 용어를 사용한다.

## p.6 - Control Plane·Worker Node Architecture

- 원자료: [[40_자료/강의 자료/Kubernetes.pdf#page=6|Kubernetes.pdf p.6]]

### 도식·이미지 의미

Kubernetes 기능으로 다음 여섯 항목을 배치한다.

- Service discovery and load balancing
- Storage Orchestration
- Secret and configuration management
- Automatic bin packing
- Self-healing
- Automated rollouts and rollbacks

Architecture 연결은 다음과 같다.

```text
UI (User Interface) / CLI (kubectl)
→ Kubernetes Master
   ├─ API Server
   ├─ Scheduler
   ├─ Controller-Manager
   └─ etcd
→ Worker Node 1 / Worker Node 2
   ├─ Pod 1 / Pod 2 / Pod 3
   ├─ 각 Pod 안의 1-3개 Container
   ├─ Docker
   ├─ Kubelet
   └─ Kube-proxy
```

- Worker Node 1의 Pod는 각각 Container `3/1/2`개, Worker Node 2의 Pod는 `2/3/1`개로 그려져 Pod와 Container가 항상 1:1은 아님을 시각화한다.
- 이 Page는 추출 Text가 구성 요소 Label 정도밖에 남지 않으므로 Rendering을 최종 기준으로 삼았다.

## p.7 - Pod 생성 Sequence

- 원자료: [[40_자료/강의 자료/Kubernetes.pdf#page=7|Kubernetes.pdf p.7]]

### 도식·이미지 의미

도식 Actor는 `Client·YAML`, `api`, `etcd`, `sched`, `kubelet`, `docker`다. 번호와 방향은 다음과 같다.

```text
1. Client·YAML → API: Create Pod
2. API → etcd: Write
3. API → Scheduler: New Pod
4. Scheduler → API: Bind Pod
5. API → etcd: Write
6. API → Kubelet: Bound Pod
7. Kubelet → Docker: Doker Run
8. Kubelet → API: Update Pod Status
9. API → etcd: Write
```

- 각 Write 뒤에는 etcd에서 API로 돌아오는 점선 응답이 그려져 있다.
- Create Pod 뒤 Client 방향, Bound Pod 뒤 API·Kubelet 사이, Docker Run 뒤 Kubelet 방향에도 점선 응답이 표시된다.

### 판독 불확실성

- 원자료의 7번 Label은 `Docker Run`이 아니라 `Doker Run`으로 표기돼 있다. 몰래 교정하지 않고 원문 표기를 보존했다.
- 이 Page에는 Sequence의 의미를 설명하는 별도 본문이 없으므로, 위 내용은 도식 Label과 화살표를 Text로 옮긴 것이다.

## 완료 검증

- [x] p.4-p.7 모든 Page를 Coverage에 포함했다.
- [x] p.6 Architecture의 기능·Component·Pod 배치를 원본과 대조했다.
- [x] p.7의 Actor, 1-9단계 Label, 화살표 방향을 대조했다.
- [x] 원자료 오타를 표시하고 임의 교정하지 않았다.
- [x] 각 Page에서 PDF 원본으로 역추적할 수 있다.
