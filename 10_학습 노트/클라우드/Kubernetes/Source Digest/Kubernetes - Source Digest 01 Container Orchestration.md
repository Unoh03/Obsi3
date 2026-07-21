---
type: source-digest
status: stable
created: 2026-07-21
parent_moc: "[[10_학습 노트/클라우드/Kubernetes/00_Kubernetes MOC]]"
source: "[[40_자료/강의 자료/Kubernetes.pdf]]"
source_pages: "1-3"
digest_role: chapter
digest_index: "[[10_학습 노트/클라우드/Kubernetes/Source Digest/Kubernetes - Source Digest v1]]"
chapter: "01 Container Orchestration"
source_hash: F97666865E22749C47640689B5C41DEE38476A40312A53915F60B4F6A4330D24
source_version: "PowerPoint PDF; 266 pages; metadata created 2024-07-18"
coverage_status: complete
extraction_method: "pdfplumber 0.11.9 text extraction + pypdfium2 render visual review"
reviewed_on: 2026-07-21
---

# Kubernetes - Source Digest 01 Container Orchestration

> [!purpose]
> [[40_자료/강의 자료/Kubernetes.pdf|Kubernetes.pdf]] p.1-p.3의 본문과 도식 의미를 보존한 Chapter Digest다. 원자료 밖의 현재성 판단은 포함하지 않는다.

## Coverage

| Page | Text | Visual | 원본 대조 | 정보 유형 |
|---:|---|---|---|---|
| p.1 | 완료 | 완료 | 완료 | Chapter 표지 |
| p.2 | 완료 | 완료 | 완료 | 설명·배포 흐름 도식 |
| p.3 | 완료 | 완료 | 완료 | 설명·가상화 계층 비교 도식 |

## p.1 - Container Orchestration 표지

- 원자료: [[40_자료/강의 자료/Kubernetes.pdf#page=1|Kubernetes.pdf p.1]]
- `Container Orchestration` Chapter의 표지다.
- 별도의 본문·표·Code·정보성 도식은 없다.

## p.2 - 컨테이너 오케스트레이션

- 원자료: [[40_자료/강의 자료/Kubernetes.pdf#page=2|Kubernetes.pdf p.2]]

### 원자료 내용

- Container Orchestration은 복잡하게 구성된 다양한 형태의 Container를 Server 관리자 대신 관리 작업 Code로 관리하는 것으로 설명된다.
- 지원 기능으로 Server 자원 Clustering, Container 배포 관리, Service 탐색·접근, 부하 처리, 장애 복구 자동화를 제시한다.
- 구현 도구 예시는 Docker Swarm과 Kubernetes이며, 자료는 Kubernetes를 `실질적인 표준`이라고 표현한다.
- 일반적인 Container 가상화만 사용하는 경우 배포·운영 관리 Resource 소모가 많아 효율적인 관리가 어렵다고 설명한다.
- Orchestration을 사용하면 Clustered Server를 중앙 집중식으로 관리하여 관리 Resource를 줄일 수 있다고 설명한다.
- 자동 배포·Scaling, Rollout·Rollback, Container 복구 작업을 구현할 수 있다고 설명한다.

### 도식·이미지 의미

원자료의 예시는 다음 반복 작업을 보여준다.

```text
Developer
→ Build & Push
→ Docker Hub
├─ Pull → Test Server → docker run x 20
└─ Pull → Prod Server → docker run x 20
```

- 핵심은 Image Build·Push 뒤 Test와 Prod Server에서 각각 Pull과 다수의 `docker run`을 반복하는 수동 배포 흐름이다.
- 도식 안의 `Build & Push`, `Pull`, `docker run x 20`은 명령 전문이 아니라 단계 Label이다.

## p.3 - Container Virtualization Summary

- 원자료: [[40_자료/강의 자료/Kubernetes.pdf#page=3|Kubernetes.pdf p.3]]

### 원자료 내용

- 초기 Traditional Service 환경에서는 각 Application의 Library Version 충돌 등으로 독립성이 보장되지 않는 문제가 있었다고 설명한다.
- 이를 해결하기 위해 가상화가 발전했고, Application별 독립된 운영 환경을 제공한다고 설명한다.
- Hypervisor 가상화는 VM마다 Guest OS를 설치하며, 자료는 이를 `HW 자원의 비효율적 사용`이라고 부연한다.
- Container 가상화는 별도 VM·Guest OS 없이 Host OS Kernel 기능을 사용해 독립 환경을 구성한다고 설명한다.
- Container 구현 기술 예시로 Docker, OpenVZ, LXC를 제시한다.
- 자료는 Docker를 사실상의 Container 가상화 표준으로 표현한다.
- Container 활용 기술이 Docker를 기준으로 개발·갱신되며 예시로 Kubernetes를 제시한다.

### 도식·이미지 의미

도식은 동일 Hardware 위의 세 계층을 비교한다.

```text
Traditional
Hardware → Operating System → App별 Bin/Library → App

Virtual Machine
Hardware → Operating System → Hypervisor
→ VM별 Guest OS → Bin/Library → App

Container
Hardware → Operating System → Container Runtime
→ Container별 Bin/Library → App
```

- VM은 각 Virtual Machine마다 Operating System 층이 반복된다.
- Container는 Host Operating System과 Container Runtime 위에서 Application별 Bin/Library를 분리하는 형태로 그려진다.

## 판독 불확실성

- p.2-p.3의 `사실상의 표준`, 효율성 평가는 원자료의 주장으로만 보존했다.
- 이 Chapter에는 원자료 밖의 현재성 검증이나 보충 설명을 추가하지 않았다.

## 완료 검증

- [x] p.1-p.3 모든 Page를 Coverage에 포함했다.
- [x] 본문과 도식 Label을 확인했다.
- [x] 정보성 Page를 Rendering하여 Visual 의미를 검수했다.
- [x] 원자료 밖 설명을 원자료 사실에 섞지 않았다.
- [x] 각 Page에서 PDF 원본으로 역추적할 수 있다.
