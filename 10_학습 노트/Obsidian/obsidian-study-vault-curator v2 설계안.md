# obsidian-study-vault-curator v2 설계안

## 문서 목적

이 문서는 `obsidian-study-vault-curator` skill을 연구 결과와 실제 사용 방식에 맞춰 재설계하기 위한 실행 전 설계안이다.

현재 skill에 문장을 덧붙이는 보수적 패치가 아니다. 기존 파일에서 유효한 규칙만 회수하고, 사용 빈도가 높은 두 흐름을 중심으로 구조를 다시 짠다.

- 연구 근거와 교차검증 기록: [[10_학습 노트/Obsidian/AI 보조 Obsidian 학습 노트 Workflow 연구 대장|AI 보조 Obsidian 학습 노트 Workflow 연구 대장]]
- 현재 상태: `pilot implementation completed; live AWS validation pending`
- 작성일: `2026-06-02`

> [!important] 설계안과 구현 상태를 구분한다
> `C:\Users\Unoh\.codex\skills\obsidian-study-vault-curator\`에 pilot 구현을 반영했다. 구현 완료는 실제 수업 검증 완료를 의미하지 않는다.

## Implementation Status Update

- 확인 환경: `Codex local snapshot`
- 확인일: `2026-06-02`
- 상태: `pilot implementation completed; live AWS validation pending`
- thin router와 조건부 reference 구조를 현재 skill에 반영했다.
- `Live Lab Capture`, 내부 revision checkpoint, PDF Concept Note 작성, 외부 검증과 보충, 품질 검토, Lab Reconstruction, Vault Routing, 보조 노트 유형 처리를 각각 reference로 분리했다.
- 새 파일, source asset, wiki link, embed, frontmatter, folder path를 편집할 때만 `vault-map-and-routing.md`를 추가로 읽는 조건부 dependency를 반영했다.
- 사용자에게 수업 직후 별도 `Revision Bridge` 양식을 강제하지 않는다.
- 다음 검증은 실제 AWS 수업에서 수행한다. 실제 수업 검증 전에는 구조를 추가로 확대하지 않는다.

## 1. 재설계 결론

v2는 복잡한 절차를 사용자에게 강제하지 않는다.

핵심은 다음 두 흐름이다.

```text
실습 노트:
사용자가 직접 실습하며 러프하게 기록
-> AI가 중간 저장
-> checkpoint에서 전체 RAW를 다시 읽음
-> 실습 목적, 흐름, 증거, 시행착오를 파악
-> 결과 중심 Lab Note로 재구성

개념 노트:
MOC와 PDF 구조 확인
-> 같은 주제 페이지를 묶음
-> 범위와 learning spine 합의
-> PDF 내용을 흡수
-> 외부 자료로 보충하고 최신화
-> 초보자용 독립 Concept Note 작성
-> 품질 검토
```

라우팅, 트러블슈팅, 프로젝트, 자격증 노트는 필요하지만 보조 흐름으로 둔다.

## 2. 연구 결과를 적용하는 방식

연구 대장은 판단 근거다. skill은 실행 규칙이다. 연구 대장의 모든 내용을 skill에 복사하지 않고, 실제 작업 행동으로 변환한다.

| 연구 또는 관찰에서 얻은 판단 | v2에서 적용할 실행 규칙 | 상태 |
| --- | --- | --- |
| 실시간 포착과 사후 revision은 분리해야 한다 | 수업 중에는 RAW만 받고, checkpoint 뒤에 Lab Reconstruction을 수행한다 | 즉시 반영 |
| 사용자가 직접 남긴 질문과 관찰은 학습 흔적이자 실습 증거다 | AI가 관찰하지 않은 결과를 만들거나 사용자의 질문을 임의로 대체하지 않는다 | 즉시 반영 |
| 기술 실습은 명령어, 오류, 캡처, 설정값의 정확한 보존이 중요하다 | 러프 기록을 삭제하지 않고 결과 중심 구조 안에 증거와 디버깅 경로로 재배치한다 | 즉시 반영 |
| PDF 순서는 최종 학습 순서와 다를 수 있다 | PDF의 같은 주제 페이지를 묶고, 하나의 learning spine을 중심으로 다시 설명한다 | 즉시 반영 |
| 오래된 강의 자료는 현재 정보와 충돌할 수 있다 | 공식 문서로 최신 상태를 확인하고 레거시 정보와 현재 정보를 구분한다 | 즉시 반영 |
| 초보자에게는 mental model, 구성 요소 설명, worked example이 유용하다 | 정확한 용어보다 짧은 직관적 설명을 먼저 제시하고, 필요한 부연 설명과 예제를 추가한다 | 즉시 반영 |
| AI 자동 작성은 사용자의 관찰, 설명, 회상을 지울 수 있다 | AI Assistance Boundary와 사용자 승인 경계를 둔다 | 즉시 반영 |
| 회상 활동은 작성과 다른 학습 활동이다 | Review Activity는 안정화된 노트에서만 선택적으로 제안한다 | 선택적 후보 |
| 시각화는 관계를 이해할 때만 가치가 있다 | 표, Mermaid, Canvas, 이미지, callout을 조건부로 사용한다 | 즉시 반영 |
| 모든 노트에 하나의 형식을 강제할 근거는 없다 | 노트 유형에 따라 구조를 선택하고 고정 템플릿을 강제하지 않는다 | 즉시 반영 |

## 3. 실제 사용 방식

### 3.1 실습 중

사용자는 실습을 진행하면서 스크린샷, 설명, 명령어, 요청·응답, 오류, 질문을 러프하게 넣는다.

AI는 이 시점에 완성 노트를 만들지 않는다.

허용:

- 전달받은 RAW 기록 보존
- 짧은 설명과 질문 답변
- 다음 확인 지점 제안
- 사용자가 요청한 중간 저장
- 관찰한 사실, 해석, 미해결 질문의 최소 구분

금지:

- RAW 전체 구조를 임의로 개편
- 실습하지 않은 결과 작성
- 개념 노트 자동 생성
- MOC 갱신
- 주변 노트 수정

### 3.2 실습 checkpoint

다음 표현은 Lab Reconstruction을 검토할 신호다.

```text
중간 저장
기록 ㄱㄱ
종결
다듬자
쭉 읽어봐
```

표현 자체를 엄격한 명령어로 강제하지 않는다. 문맥상 같은 요청이면 동일하게 처리한다.

- `중간 저장`, `기록 ㄱㄱ`: RAW를 보존하고 현재까지 확인된 것만 최소 정리한다.
- `종결`, `다듬자`, `쭉 읽어봐`: 전체 RAW를 다시 읽고 결과 중심으로 재구성할 준비를 한다.

### 3.3 개념 노트 작성

사용자는 PDF 기반 Concept Note 작성을 AI에 맡긴다.

AI는 다음을 수행한다.

1. 관련 MOC와 주변 노트를 확인한다.
2. PDF 전체 구조를 거칠게 파악한다.
3. 같은 주제인 페이지를 묶는다.
4. 묶음별 learning spine과 포함·보류 범위를 제안한다.
5. 사용자 승인 뒤 PDF 내용을 흡수한다.
6. 인터넷에서 공식 문서와 필요한 관련 자료를 조사한다.
7. 레거시 정보, 최신 정보, 초보자에게 필요한 부연 설명, 실무 팁을 분류한다.
8. PDF를 다시 열지 않아도 이해할 수 있는 standalone Concept Note를 작성한다.
9. 가독성, 정확성, 범위, 출처를 검토한다.

## 4. 사용자 승인 경계

> [!warning] 제안과 실행을 구분한다
> AI는 구조와 개선안을 자유롭게 제안할 수 있다. 파일 편집과 범위 확장은 사용자의 승인 뒤에만 실행한다.

### 승인 없이 가능한 것

- 관련 파일 읽기
- 현재 상태 보고
- 구조, 범위, 파일명 후보 제안
- 외부 자료 조사 계획 제안
- diff를 만들지 않는 감사와 설명

### 별도 승인이 필요한 것

- 파일 생성 또는 본문 수정
- 파일 이동, 이름 변경, 분할, 병합
- MOC와 wiki link 갱신
- 주변 노트 수정
- template 생성
- skill 파일 수정
- commit, push, 배포

### 항상 지켜야 할 경계

- 사용자가 관찰하지 않은 실습 결과를 작성하지 않는다.
- 다른 AI의 답변을 근거로 취급하지 않는다.
- 외부 조사 결과의 검증 수준을 구분한다.
- 사용자가 요청하지 않은 범위로 노트를 확대하지 않는다.
- 실습 중 인지 부담을 늘리는 입력 양식을 강제하지 않는다.

## 5. 목표 파일 구조

```text
obsidian-study-vault-curator/
├── SKILL.md
├── agents/
│   └── openai.yaml
└── references/
    ├── vault-map-and-routing.md
    ├── live-lab-capture.md
    ├── lab-note-reconstruction.md
    ├── pdf-concept-note-authoring.md
    ├── source-verification-and-enrichment.md
    ├── note-quality-review.md
    └── secondary-note-types.md
```

### 파일별 책임

| 파일 | 책임 |
| --- | --- |
| `SKILL.md` | 요청을 작업 모드로 분류하고, 승인 경계를 확인하고, 필요한 reference만 읽게 하는 얇은 라우터 |
| `agents/openai.yaml` | skill 목록과 UI에 표시할 설명. 실제 `SKILL.md`와 의미가 맞는지 확인 |
| `vault-map-and-routing.md` | 폴더, MOC, source material, wiki link, frontmatter 규칙 |
| `live-lab-capture.md` | 수업 중 러프 기록, 중간 저장, 질문 대응, 내부 checkpoint 규칙 |
| `lab-note-reconstruction.md` | 전체 RAW를 다시 읽고 결과 중심 Lab Note로 재구성하는 규칙 |
| `pdf-concept-note-authoring.md` | PDF 구조 파악, 주제 묶음, learning spine, standalone Concept Note 작성 규칙 |
| `source-verification-and-enrichment.md` | 외부 조사, 공식 문서 우선순위, 레거시 보정, 최신 정보, 초보자 설명, 실무 팁 규칙 |
| `note-quality-review.md` | 가독성, 정확성, 범위, 정보 계층, Obsidian 표현, 출처 점검 |
| `secondary-note-types.md` | 트러블슈팅, 프로젝트, 자격증 노트와 기타 보조 유형 규칙 |

### `skill-creator` 기준

v2는 `skill-creator`의 progressive disclosure 원칙을 따른다.

| 기준 | 적용 방식 |
| --- | --- |
| `SKILL.md`는 짧게 유지 | 핵심 workflow 선택, 승인 경계, reference 안내만 둔다 |
| 상세 규칙은 `references/`로 분리 | 작업 모드별로 필요한 파일만 읽는다 |
| 중복 작성 금지 | 하나의 규칙은 `SKILL.md` 또는 하나의 reference에만 상세히 기록한다 |
| reference는 한 단계로 직접 연결 | 모든 reference를 `SKILL.md`에서 직접 안내한다. reference끼리 연쇄적으로 따라가게 만들지 않는다 |
| 긴 reference는 탐색 가능하게 구성 | 100줄을 넘는 reference에는 상단 목차를 둔다 |
| 불필요한 부속 문서 생성 금지 | skill 폴더에 `README.md`, changelog, 설치 안내서, 별도 연구 기록을 만들지 않는다 |
| script는 반복성과 결정성이 필요할 때만 추가 | 현재는 반복 실행 코드가 확인되지 않았으므로 `scripts/`를 만들지 않는다 |
| 연구 기록과 실행 지침 분리 | 연구 근거는 vault의 연구 대장에 남기고, skill에는 작업 행동만 기록한다 |

## 6. `SKILL.md` 라우팅 규칙

`SKILL.md`는 모든 세부 규칙을 담지 않는다. 요청을 분류한 뒤 필요한 reference만 읽는다.

| 사용자 상황 | 작업 모드 | 읽을 reference |
| --- | --- | --- |
| 수업 중 스크린샷, 설명, 오류, 명령어를 전달 | `Live Lab Capture` | `live-lab-capture.md` |
| 실습 기록을 중간 저장 | `Live Lab Capture` | `live-lab-capture.md` |
| 실습 노트를 종결하거나 다듬기 | `Lab Reconstruction` | `lab-note-reconstruction.md`, 필요 시 `note-quality-review.md` |
| PDF 범위를 분석하고 개념 노트를 설계 | `PDF Concept Planning` | `pdf-concept-note-authoring.md`, 필요 시 `vault-map-and-routing.md` |
| 합의한 범위로 개념 노트 작성 | `PDF Concept Authoring` | `pdf-concept-note-authoring.md`, `source-verification-and-enrichment.md`, `note-quality-review.md` |
| MOC 연결 또는 배치 판단 | `Vault Routing` | `vault-map-and-routing.md` |
| 트러블슈팅, 프로젝트, 자격증 노트 | `Secondary Note Type` | `secondary-note-types.md`, 필요 시 `note-quality-review.md` |

## 7. Lab Note Workflow

### 7.1 Live Lab Capture

```text
사용자가 직접 실습
-> 스크린샷, 설명, 명령어, 오류, 질문을 러프하게 투입
-> AI는 필요한 설명과 다음 확인 지점을 짧게 제안
-> 사용자가 원하면 현재까지 RAW를 중간 저장
```

RAW에 보존할 것:

- 실제 명령어와 payload
- 요청·응답과 설정값
- 스크린샷과 로그
- 성공 또는 실패 관찰
- 사용자 질문과 추측
- 강사 표현
- 환경 차이
- 시행착오

### 7.2 내부 Revision Checkpoint

기존 설계안의 `Revision Bridge`는 사용자에게 별도 양식을 요구하는 필수 단계에서 내린다.

대신 AI가 중간 저장이나 재구성 시 내부적으로 확인한다.

| 구분 | 확인할 것 |
| --- | --- |
| 관찰 | 실제로 화면, 로그, 응답에서 확인한 것은 무엇인가 |
| 해석 | 관찰을 바탕으로 어떤 의미를 추론했는가 |
| 실패 원인 후보 | 무엇이 아직 가설인가 |
| 미해결 질문 | 다음에 무엇을 확인해야 하는가 |
| 정리 상태 | RAW만 저장할지, 결과 중심 재구성이 가능한지 |

불명확한 정보는 추측으로 채우지 않고 질문 또는 남은 확인으로 둔다.

### 7.3 Lab Reconstruction

checkpoint 뒤에는 chronology append를 멈추고 전체 RAW를 다시 읽는다.

권장 구조:

1. 최종 판정과 무엇을 증명했는지
2. 핵심 증거
3. 한눈에 보는 흐름
4. 역할과 경계
5. 실제 실행 절차
6. 시행착오와 트러블슈팅
7. 보안, 인프라 또는 개발 관점의 의미
8. 남은 확인

고정 template로 강제하지 않는다. 실습의 성격에 맞춰 이름과 순서를 조정한다.

## 8. PDF Concept Note Workflow

### 8.1 범위 설계

```text
관련 MOC 확인
-> PDF 전체 구조 파악
-> 같은 주제 페이지 묶기
-> 묶음별 learner question과 learning spine 제안
-> core / bridge / appendix·TMI 분류
-> 노트 분할과 포함·보류 범위 합의
```

PDF는 범위 기준점이지 최종 heading 구조가 아니다.

노트를 분할하려면 부주제에도 독립적인 learner question, 설명 흐름, 재참조 가치가 있어야 한다. 슬라이드가 따로 있거나 정보가 많다는 이유만으로 분할하지 않는다.

### 8.2 외부 조사와 보충

PDF 내용을 읽은 뒤 필요한 곳을 외부 자료로 보충한다.

| 추가 정보 | 처리 |
| --- | --- |
| 오래된 UI, 가격, 서비스 상태, 표준, 보안 권장 | 공식 문서를 확인하고 현재 정보와 레거시 정보를 구분 |
| 초보자가 이해하기 어려운 연결 개념 | 짧은 mental model과 부연 설명 추가 |
| 실무에서 자주 마주치는 선택, 함정, 확인 방법 | `[!tip]`, `[!warning]`, 비교표 또는 하단 실무 메모로 추가 |
| PDF의 단순화 또는 부정확한 표현 | 의도한 의미, 정확한 개념, 한계를 구분하여 보정 |
| 주제와 직접 관련되지만 첫 읽기에 무거운 정보 | appendix·TMI로 시각적 무게를 낮춤 |
| 흥미롭지만 현재 주제를 벗어난 정보 | 별도 노트 후보 또는 보류 항목으로 제안 |

조사 우선순위:

1. 공식 문서, 표준, 원문
2. 신뢰할 수 있는 1차 자료
3. 필요한 경우 보조 자료

시점 의존 정보는 작성 시점에 다시 확인한다.

### 8.3 작성

최종 Concept Note는 PDF를 다시 열지 않아도 이해할 수 있어야 한다.

권장 설명 순서:

1. 한 줄 요약
2. 먼저 잡아야 할 핵심
3. 초보자용 mental model
4. 구성 요소, 흐름, 경계
5. 흔한 오해와 정확한 표현
6. 현재 정보와 레거시 정보
7. 실무 팁과 필요한 TMI
8. 관련 노트와 출처

주제에 맞지 않으면 구조를 조정한다. PDF 페이지 순서와 조사 checklist를 heading 구조로 복사하지 않는다.

## 9. 검증과 품질 검토

### 9.1 공통 검토

- 노트 상단만 읽어도 목적과 핵심을 파악할 수 있는가
- 사용자가 승인한 범위를 넘지 않았는가
- 관찰, 해석, 외부 근거가 섞이지 않았는가
- 초보자용 설명 뒤에 정확한 용어가 이어지는가
- 표, Mermaid, 이미지, callout이 장식이 아니라 이해를 돕는가
- wiki link 대상이 실제로 존재하는가
- MOC 변경이 별도 승인 범위에 포함되는가

### 9.2 Lab Note 추가 검토

- 실제 수행하지 않은 결과를 성공으로 쓰지 않았는가
- 스크린샷과 로그가 무엇을 증명하는지 설명했는가
- 중요한 시행착오를 삭제하지 않고 디버깅 경로로 정리했는가
- 결과, 증거, 흐름이 setup log보다 먼저 보이는가

### 9.3 Concept Note 추가 검토

- PDF 없이 읽히는가
- 같은 주제 페이지를 충분히 흡수했는가
- 최신 정보와 레거시 정보를 구분했는가
- 외부 조사로 주제 범위가 무한히 확장되지 않았는가
- core, bridge, appendix·TMI의 시각적 무게가 다른가
- 출처가 본문 흐름을 방해하지 않으면서 검증 가능하게 남았는가

## 10. 보조 흐름

### 10.1 Vault Routing

- `Home -> area MOC -> topic MOC -> concrete note` 경로를 따른다.
- 실제 존재하는 대상만 wiki link로 연결한다.
- MOC는 설명문 저장소가 아니라 얇은 탐색 계층으로 유지한다.
- 파일 생성, 이동, 분할, MOC 갱신은 각각 승인 범위를 확인한다.

### 10.2 Troubleshooting Note

증상, 영향, 환경, 가설, 확인, 원인, 해결, 검증, 예방 순서를 기본으로 삼는다.

### 10.3 Project Note

현재 운영 상태, 역할, 구성, 의존성, 실패 지점, 복구, 증거, 결정 로그를 우선한다.

### 10.4 Certification Note

틀린 문제, 오답 이유, 정확한 개념, 기억 장치, 관련 노트를 우선한다.

## 11. 선택적으로 시험할 후보

다음은 연구에서 가치가 있지만 모든 작업에 즉시 강제하지 않는다.

| 후보 | 시험 조건 | 즉시 강제하지 않는 이유 |
| --- | --- | --- |
| Review Activity | 안정화된 Concept Note에서 회상·적용 질문 2-5개를 별도 요청했을 때 | 작성과 복습을 섞지 않기 위해 |
| Routing Gate 세분화 | 작성과 MOC 갱신이 반복적으로 섞일 때 | 현재 승인 경계로 충분할 수 있음 |
| Canvas | 복잡한 아키텍처 또는 여러 노트의 관계를 비교할 때 | 모든 노트에 필요한 기능이 아님 |
| labeled Mermaid | 트래픽 흐름, 역할 경계, 상태 전이가 글보다 명확할 때 | 장식용 도식화를 피하기 위해 |
| 손필기 기반 복습 | 사용자가 개념 복습 방식으로 시험하고 싶을 때 | 기술 실습 RAW 보존과 역할이 다름 |

## 12. 기각할 보편 규칙

다음은 모든 노트와 모든 수업에 강제하지 않는다.

- 수업 직후 사용자가 별도 `Revision Bridge` 양식을 작성
- 모든 노트를 atomic file로 분리
- 모든 노트에 Mermaid, Canvas, 표, callout 삽입
- 모든 Concept Note에 회상 질문 자동 부착
- PDF를 입력하면 AI가 노트 분할, 본문 작성, MOC 갱신까지 자동 수행
- Progressive Summarization을 완성 Concept Note 작성법으로 대체
- 손필기 또는 타이핑 중 하나만 허용
- AI 제품 소개를 학습 효과 증거로 취급
- 오래된 Console screenshot을 현재 실습 절차로 복사

## 13. 기존 파일에서 회수할 내용

기존 skill을 그대로 유지하지 않는다. 유효한 내용만 새 책임 구조로 옮긴다.

| 기존 파일 | 회수할 내용 | 이동 대상 |
| --- | --- | --- |
| `SKILL.md` | Phase Gate의 핵심, standalone Concept Note, RAW 보존, hierarchy pass | 새 `SKILL.md`와 각 전용 reference |
| `note-type-playbooks.md` | Obsidian 표현 규칙, synthesis, concept depth control, 보조 노트 유형 | 전용 reference들로 분산한 뒤 제거 |
| `lab-note-reconstruction.md` | 결과 중심 구조, heading pass, 증거 처리, Mermaid, 초보자 설명 | 새 `lab-note-reconstruction.md`로 재작성 |
| `vault-map-and-routing.md` | vault 계층, MOC, wiki link, frontmatter 규칙 | 유지하되 중복 점검 |
| `agents/openai.yaml` | UI metadata | 새 `SKILL.md`와 일치 여부 확인 후 필요할 때만 갱신 |

## 14. 개편 후 검증

### 정적 검증

- `skill-creator`의 `quick_validate.py` 실행
- `SKILL.md` frontmatter 형식 확인
- UTF-8 BOM 없이 `---`로 시작하는지 확인
- reference 파일이 모두 `SKILL.md`에서 직접 연결되는지 확인
- 100줄을 넘는 reference에 상단 목차가 있는지 확인
- `agents/openai.yaml`이 새 skill 설명과 맞는지 확인
- `agents/openai.yaml`의 `default_prompt`가 `$obsidian-study-vault-curator`를 포함하는지 확인
- 중복 규칙과 끊어진 reference가 없는지 확인
- 불필요한 `README.md`, changelog, 설치 안내서가 생성되지 않았는지 확인

`quick_validate.py`가 환경 문제로 실행되지 않으면 실패 원인을 기록하고, frontmatter, BOM, metadata, reference 연결, 실제 작업 적합성을 수동 검증한다.

### task-shape 검증

| 입력 예시 | 기대 행동 |
| --- | --- |
| `수업 중이야. 이 스샷과 오류만 기록해줘.` | RAW만 보존하고 완성 노트나 MOC를 만들지 않음 |
| `지금까지 중간 저장해서 기록 가능?` | 현재까지 확인된 것만 최소 정리하고 불명확한 점을 남김 |
| `# 3 쭉 읽고 다듬고 종결 칠 준비 하자.` | 전체 RAW를 읽고 결과 중심 Lab Note 재구성을 제안 |
| `이 PDF에서 같은 주제 페이지를 묶어줘. 아직 파일은 만들지 마.` | 범위 지도와 후보 묶음만 제안 |
| `합의한 범위로 개념 노트 작성 ㄱㄱ.` | PDF를 중심으로 외부 자료를 보충하고 standalone Concept Note 하나를 작성 |
| `목차에도 연결해줘.` | 실제 파일 존재와 승인 범위를 확인한 뒤 최소 수정 |

### 독립 forward-test

가능하면 구현 뒤 별도 agent에게 최소 문맥과 RAW artifact만 전달하여 task-shape를 검증한다.

- 의도한 정답, 예상 실패, 설계 결론을 미리 알려주지 않는다.
- 실습 RAW 기록 요청과 PDF Concept Note 계획 요청을 분리하여 시험한다.
- 결과가 좋다는 이유만으로 채택하지 않고, 승인 경계와 phase 경계를 지켰는지 확인한다.
- 별도 agent를 사용할 수 없으면 실제 다음 작업에서 동일 기준으로 검증한다.

## 15. 다음 행동

1. 사용자가 이 설계안을 검토한다.
2. 승인 뒤 외부 skill 폴더를 재구성한다.
3. `agents/openai.yaml`을 새 `SKILL.md`와 대조하고 필요하면 갱신한다.
4. `quick_validate.py`와 수동 정적 검증을 수행한다.
5. 가능한 범위에서 독립 forward-test를 수행한다.
6. 실제 수업과 PDF Concept Note 작업에서 task-shape를 검증한다.
7. 반복 실패가 있을 때만 규칙을 추가한다.
