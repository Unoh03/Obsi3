---
type: source-digest
status: stable
created: 2026-07-21
parent_moc: "[[10_학습 노트/클라우드/Kubernetes/00_Kubernetes MOC]]"
source: "[[40_자료/강의 자료/Kubernetes.pdf]]"
source_pages: "262-266"
digest_role: chapter
digest_index: "[[10_학습 노트/클라우드/Kubernetes/Kubernetes - Source Digest v1]]"
chapter: "16 Related Tools"
source_hash: F97666865E22749C47640689B5C41DEE38476A40312A53915F60B4F6A4330D24
source_version: "PowerPoint PDF; 266 pages; metadata created 2024-07-18"
coverage_status: complete
extraction_method: "pdfplumber 0.11.9 text extraction + pypdfium2 render visual review"
reviewed_on: 2026-07-21
---

# Kubernetes - Source Digest 16 Related Tools

> [!purpose]
> `Kubernetes.pdf` p.262–p.266의 의미 있는 정보를 페이지별로 보존한 Chapter Digest이다. 원자료의 기술적 정확성을 현재 지식으로 검증하거나 몰래 교정하지 않는다.

## Source 식별

- 원자료: [[40_자료/강의 자료/Kubernetes.pdf|Kubernetes.pdf]]
- 대상 범위: PDF p.262–p.266
- 전체 원자료: 266 pages
- SHA-256: `F97666865E22749C47640689B5C41DEE38476A40312A53915F60B4F6A4330D24`
- 추출·검수: `pdfplumber 0.11.9` Text Layer + `pypdfium2` Rendering
- Chapter 경계: K9s·Lens·kubectx·kubens, Helm, ECR, Karpenter

## Coverage

| PDF 범위 | Text | YAML·명령·표 | Visual | 원본 대조 | 상태 |
|---|---|---|---|---|---|
| p.262–p.266 | 완료 | 완료 | 전체 렌더 검토 | 페이지별 대조 | 상세 변환 완료 / 기술 내용 외부 검증 미수행 |

## 변환 경계

- 아래 고정폭 Transcript는 PDF Text Layer의 Page 배치를 최대한 보존한다.
- YAML·명령·출력은 Rendering으로 기호와 배치를 대조했다. 원자료의 오탈자·잠재적 명령 오류는 임의로 수정하지 않는다.
- Visual 관계는 Text Layer 밖의 화살표·번호·공간 배치를 별도 설명한다.
- `status: draft`는 원자료 변환이 누락됐다는 뜻이 아니라, 전체 Index 통합 검수와 외부 기술 검증이 아직 끝나지 않았다는 뜻이다.

## Related Tools

## PDF p.262

- 원본: [[40_자료/강의 자료/Kubernetes.pdf#page=262|Kubernetes.pdf p.262]]
- 정보 유형: Cover
- PowerPoint outline: slide 272 (PDF page와 불일치)

### 원자료 내용

~~~text
Kubernetes                          Related                  Tools
~~~

### 판독 불확실성

- PDF p.262 = PowerPoint outline slide 272. PDF p.246 앞에서 내부 slide 247–255가 생략된 번호 체계를 이어받는다.

## PDF p.263

- 원본: [[40_자료/강의 자료/Kubernetes.pdf#page=263|Kubernetes.pdf p.263]]
- 정보 유형: Text
- PowerPoint outline: slide 273 (PDF page와 불일치)

### 원자료 내용

~~~text
         Kubernetes         Related      Tools    (  K9s    / Lens    /  kubectx       &   kubens      )






◎  Kubernetes  Related Tools

▣  K9s

   K9s : Kubernetes Object관리를 위한  TUI 기반의  유틸리티    ( Linux TOP 명령어와  유사한   형태로   Kubernetes Object를 관리 )

   K9s는 오픈소스이며     구성이   간편하고   Kubernetes Cluster 관리작업을   직관적으로    수행  할  수 있는  장점이   있다.
   K9s URL: https://k9scli.io/


▣  Lens

   Lens : Kubernetes Object관리를 위한  Desktop App ( Desktop APP 형식으로 Kubernetes Object를 관리 )

   Lens의 경우  2022년 유료화가    되었으며   OpenLens 형식의  무료버전을     사용  할 수  있다.
   Lens는 Kubernetes Cluster 관리작업을  직관적으로     수행  할 수  있는  장점이   있다.

   Lens URL: https://k8slens.dev/


▣  Kubectx & kubens

   kubectx : kubectl의 Context 전환을 쉽게  할  수 있도록   도움을   주는  도구  ( Kubenetes Cluster 환경 전환  )
   kubens : Kubernetes Cluster 내부의 Namespace 간 전환을   쉽게  할 수  있도록   도움을   주는  도구  ( 작업  Namespace 전환  )

   kubectx & kubens URL: https://github.com/ahmetb/kubectx
~~~

### 판독 불확실성

- PDF p.263 = PowerPoint outline slide 273. PDF p.246 앞에서 내부 slide 247–255가 생략된 번호 체계를 이어받는다.

## PDF p.264

- 원본: [[40_자료/강의 자료/Kubernetes.pdf#page=264|Kubernetes.pdf p.264]]
- 정보 유형: Text, 도식
- PowerPoint outline: slide 274 (PDF page와 불일치)

### 원자료 내용

~~~text
         Kubernetes         Related      Tools    (  Helm     )






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

- Helm Repository의 Chart가 Helm Command를 통해 Kubernetes Cluster에 배포되는 패키지 관리 구조이다.

### 판독 불확실성

- PDF p.264 = PowerPoint outline slide 274. PDF p.246 앞에서 내부 slide 247–255가 생략된 번호 체계를 이어받는다.

## PDF p.265

- 원본: [[40_자료/강의 자료/Kubernetes.pdf#page=265|Kubernetes.pdf p.265]]
- 정보 유형: Text, 도식, 삽입 이미지
- PowerPoint outline: slide 275 (PDF page와 불일치)

### 원자료 내용

~~~text
         Kubernetes         Related      Tools    (  AWS     ECR     )





◎  AWS ECR  ( Elastic Container  Registry  )

   AWS에서  제공하는   완전  관리형   Container Registry 서비스 ( AWS EKS 환경을  사용하는    경우  대부분   ECR 서비스를   함께  사용   )

   AWS ECR은 각 계정  별  Registry 공간을  부여받게    되며  해당  Registry에 실제  이미지를    저장  할 수  있는  Repository를 구성한다.
   AWS ECR은 이미지를   사용하는    사용자를   식별하기    위한  사용자   권한  토큰을   사용한다.   ( Image Push, Pull 권한 )

   AWS ECR은 이미지의   수명주기를    관리하고,    외부  Public Registry를 Cache 할 수 있으며,   저장  된 이미지의    SW 취약점을   검사한다.

   Amazon ECR Public Gallery : https://gallery.ecr.aws/ ( ECR 공개 저장소로 다양한 이미지를    내려받아   사용가능    )
~~~

### Visual 의미

- Code 작성 → ECR Image 저장·압축·암호화·수명주기 관리 → ECS/EKS/On-premises에서 Image Pull·실행으로 이어지는 AWS 인포그래픽이다.

### 판독 불확실성

- 하단 AWS 인포그래픽의 작은 Label과 연결선은 Text Layer만으로 완전 복원되지 않아 Rendering을 기준으로 설명했다.

## PDF p.266

- 원본: [[40_자료/강의 자료/Kubernetes.pdf#page=266|Kubernetes.pdf p.266]]
- 정보 유형: Text, 도식
- PowerPoint outline: slide 276 (PDF page와 불일치)

### 원자료 내용

~~~text
         Kubernetes         Related      Tools    (  Karpenter       )





◎  Karpenter

   Karpenter : AWS에서 개발한 Kubernetes의 Worker Node 자동 확장 기능을   수행하는  오픈소스   프로젝트   ( JIT: Just In-Time 배포 )
   Karpenter는 AWS Resource 의존성 없이  JIT 배포를   수행하므로    기존  Cluster AutoScaler 보다 빠른  확장성을    제공한다.

1. HPA에의한  수평확장이     최대치에   도달하면    Pod는 배포  Node를 배정   받지  못한  Pendding ( Unscheduled Pod ) 상태가 된다.

2. Karpenter는 이러한  Pod들의  상태를   지속  감시하면서     Pendding 상태가  유지  될  경우  직접  새로운   Node를 추가한다.

3. Worker Node의 모든  배포  준비가   완료  될 경우   "kube-scheduler" 대신 Kapenter가 새롭게  추가  된  Node에 Pod를  할당한다.



        Amazone  EKS
                                              ②  새로운   Worker Node를 직접  생성



             Worker  Node               Worker Node  (New)


                                                  ③  Pod 할
                                                     당



                                                                      Kube-Scheduler   Pendding Pod


                                                             ①   Node Resource Limit ( Unscheduled Pod )
~~~

### Visual 의미

- Pending Pod 감지 후 Karpenter가 새 Worker Node를 직접 생성하고 Pod를 배치하는 1–3단계 구조이다.

### 판독 불확실성

- PDF p.266 = PowerPoint outline slide 276. PDF p.246 앞에서 내부 slide 247–255가 생략된 번호 체계를 이어받는다.

## 누락·검토 대기

- 선언한 PDF Page 범위의 Text·YAML·명령·출력·Visual 확인은 완료했다.
- 원자료의 Kubernetes·AWS Version과 기술 내용에 대한 최신 공식 문서 검증은 이 Chapter Digest의 범위 밖이다.
- 전체 Index의 Chapter Link와 전 범위 Gap·Overlap 검증은 Index 갱신 단계에서 수행한다.

## 완료 검증

- [x] PDF p.262–p.266 모든 Page를 포함했다.
- [x] Text Layer와 Rendering을 함께 확인했다.
- [x] YAML·명령·표형 출력의 기호와 배치를 원본과 대조했다.
- [x] 도식·삽입 이미지의 관계를 별도 기록했다.
- [x] 판독 불확실성과 원자료 오류 가능성을 숨기지 않았다.
- [ ] 전체 Source Digest Index 통합 검수와 외부 기술 검증
