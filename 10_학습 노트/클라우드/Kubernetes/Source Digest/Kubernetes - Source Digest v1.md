---
type: source-digest
status: stable
created: 2026-07-20
parent_moc: "[[10_학습 노트/클라우드/Kubernetes/00_Kubernetes MOC]]"
source: "[[40_자료/강의 자료/Kubernetes.pdf]]"
source_pages: "1-266"
digest_role: index
source_hash: "F97666865E22749C47640689B5C41DEE38476A40312A53915F60B4F6A4330D24"
source_version: "PowerPoint PDF; 266 pages; metadata created 2024-07-18"
coverage_status: complete
extraction_method: "pdfplumber text extraction + pypdfium2 rendering and visual review"
reviewed_on: 2026-07-21
tags:
  - 과목/클라우드
  - 주제/Kubernetes
  - 주제/EKS
---

# Kubernetes - Source Digest v1

> [!purpose]
> `Kubernetes.pdf`를 반복 해석하지 않고 필요한 범위만 읽기 위한 Source Digest Index다. 원자료 내용은 Chapter Digest에 보존하며, 이 파일은 전체 범위·처리 상태·Chapter 경로만 관리한다.
>
> 작성·검수 기준: [[90_템플릿/Source_Digest_작성_가이드|Source Digest 작성 가이드]]

## Source 식별

| 항목 | 값 |
|---|---|
| 원자료 | [[40_자료/강의 자료/Kubernetes.pdf|Kubernetes.pdf]] |
| PDF Page | p.1-p.266 |
| 파일 크기 | 3,055,505 bytes |
| SHA-256 | `F97666865E22749C47640689B5C41DEE38476A40312A53915F60B4F6A4330D24` |
| 원본 Metadata | PowerPoint presentation, 작성자 최종운, 2024-07-18 15:30:10+09 |
| 변환 방식 | `pdfplumber` Text 추출 + `pypdfium2` Page Rendering + 원본 대조 |
| 외부 최신성 검증 | 수행하지 않음 |

## Chapter Coverage

| Chapter | PDF Page | 처리 상태 | Chapter Digest |
|---:|---:|---|---|
| 01 Container Orchestration | p.1-p.3 | 변환·원본 대조 완료 | [[Kubernetes - Source Digest 01 Container Orchestration]] |
| 02 Kubernetes Architecture | p.4-p.7 | 변환·원본 대조 완료 | [[Kubernetes - Source Digest 02 Kubernetes Architecture]] |
| 03 AWS EKS | p.8-p.12 | 변환·원본 대조 완료 | [[Kubernetes - Source Digest 03 AWS EKS]] |
| 04 Pod and ReplicaSet | p.13-p.73 | 변환·원본 대조 완료 | [[Kubernetes - Source Digest 04 Pod and ReplicaSet]] |
| 05 Deployment | p.74-p.109 | 변환·원본 대조 완료 | [[Kubernetes - Source Digest 05 Deployment]] |
| 06 Service Object | p.110-p.134 | 변환·원본 대조 완료 | [[Kubernetes - Source Digest 06 Service Object]] |
| 07 ConfigMap and Secret | p.135-p.160 | 변환·원본 대조 완료 | [[Kubernetes - Source Digest 07 ConfigMap 및 시크릿]] |
| 08 Pod Health Check | p.161-p.171 | 변환·원본 대조 완료 | [[Kubernetes - Source Digest 08 Pod Health Check]] |
| 09 Resource Management | p.172-p.186 | 변환·원본 대조 완료 | [[Kubernetes - Source Digest 09 Resource Management]] |
| 10 ServiceAccount and RBAC | p.187-p.197 | 변환·원본 대조 완료 | [[Kubernetes - Source Digest 10 SA and RBAC]] |
| 11 Ingress Network | p.198-p.212 | 변환·원본 대조 완료 | [[Kubernetes - Source Digest 11 Ingress Network]] |
| 12 Volume Management | p.213-p.234 | 변환·원본 대조 완료 | [[Kubernetes - Source Digest 12 Volume Management]] |
| 13 StatefulSet | p.235-p.245 | 변환·원본 대조 완료 | [[Kubernetes - Source Digest 13 StatefulSet]] |
| 14 DaemonSet | p.246-p.250 | 변환·원본 대조 완료 | [[Kubernetes - Source Digest 14 DaemonSet]] |
| 15 AutoScaling | p.251-p.261 | 변환·원본 대조 완료 | [[Kubernetes - Source Digest 15 AutoScaling]] |
| 16 Related Tools | p.262-p.266 | 변환·원본 대조 완료 | [[Kubernetes - Source Digest 16 Related Tools]] |

Chapter 범위의 합은 p.1-p.266을 Gap·Overlap 없이 한 번씩 덮는다.

## Page 번호 경계

- Coverage와 역추적의 기준은 PDF Viewer의 실제 Page 번호다.
- PDF p.172-p.243에서는 내부 Slide 번호가 PDF Page 번호와 일치한다. p.1-p.171도 역추적 기준은 내부 번호가 아니라 PDF Page 번호다.
- PDF p.244-p.245는 내부 Slide p.245-p.246으로 표시된다.
- PDF p.246-p.266은 내부 Slide p.256-p.276으로 표시된다.
- 내부 Slide 244와 247-255는 원본 PDF에 없으므로 누락으로 추정해 복원하지 않는다.

## 사용 방법

```text
Kubernetes MOC
→ 이 Index에서 주제와 PDF Page 범위 확인
→ 필요한 Chapter Digest만 읽기
→ Chapter 안의 필요한 Page Heading만 읽기
→ 판독 불확실성이나 원본 증거가 필요할 때만 PDF Page 확인
```

- Chapter Digest의 `원자료 내용`은 PDF에 실린 내용을 보존한다.
- `도식·이미지 의미`는 렌더링에서 확인되는 관계를 Text로 옮긴 것이다.
- 원자료의 오타·모순·시점 의존 정보는 임의로 교정하지 않고 표시한다.
- 원자료 밖의 최신 정보나 실행 결과는 출처를 분리하지 않으면 이 계층에 넣지 않는다.
- `stable`은 해당 PDF 범위를 충실하게 옮겼다는 뜻이며, 기술 내용의 현재 정확성을 보증하지 않는다.

## 전체 검수 상태

- [x] 원자료 파일·Page 수·SHA-256 식별
- [x] Chapter 경계 확정
- [x] p.1-p.266 Chapter 파일 생성
- [x] Chapter 사이 Gap·Overlap 없음
- [x] 모든 Chapter의 Page별 Text·Visual 원본 대조 완료
- [x] 모든 Chapter Frontmatter와 Link 검증 완료
- [x] 판독 불가·원자료 내부 충돌 최종 검토
- [x] 전체 범위 `coverage_status: complete` 판정
