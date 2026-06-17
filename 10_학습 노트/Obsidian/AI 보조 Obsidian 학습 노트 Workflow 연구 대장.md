# AI 보조 Obsidian 학습 노트 Workflow 연구 대장

> [!important] 교차검증 보정 우선순위
> 이 문서는 기존 조사 기록을 삭제하지 않고 보존한다. 아래에 추가된 `Snapshot Boundary`, `Verification Scope of the Synthesis Pass`, `Flanigan et al. (2024)` 보정, 외부 snapshot 관찰, 저신뢰 운영 참고가 기존 문구와 충돌하면 추가 보정 내용을 현재 판정으로 우선한다.

## 문서 목적

이 문서는 보안·클라우드 수업을 Obsidian vault에 정리하는 과정에서, AI가 어떤 역할을 맡아야 하고 어떤 역할을 맡으면 안 되는지 판단하기 위해 수행한 조사와 논의를 보존한다.

주요 목적은 다음과 같다.

1. 지금까지 발생한 문제와 판단 변경을 추적 가능하게 남긴다.
2. Codex가 조사한 내용과 GPT가 추가 검토한 내용을 분리한다.
3. 실제 skill 파일에 반영된 규칙과 아직 제안 단계인 규칙을 분리한다.
4. 학습 과학, AI 보조 노트 연구, PKM/Obsidian 실무 조언의 증거 수준을 구분한다.
5. 앞으로 skill을 수정하거나 AWS 노트를 다시 작성할 때 기준이 되는 원칙과 검증 과제를 고정한다.

이 문서는 대화 전체의 축약본이 아니다.
반복된 표현과 같은 결론의 중복 설명은 줄였지만, workflow 결정에 영향을 주는 주장·근거·판정 변경·보류 사항은 보존한다.

---

## Snapshot Boundary

- 보고서 snapshot 날짜: `2026-06-01`
- 이 문서는 여러 환경과 파일 snapshot에서 확인한 결과를 통합한다.
- GPT가 확인한 상태는 ChatGPT 대화에 업로드되었거나 GPT가 직접 확인한 파일 snapshot에만 적용된다.
- Codex가 확인한 상태는 Codex 로컬 workspace에서 직접 확인한 파일과 저장소 상태에만 적용된다.
- GitHub 추적 상태, Codex 로컬 working tree, GPT 업로드 파일, AWS 노트 진도, MOC 내용, skill 구현 상태는 서로 다를 수 있다.
- 저장소 내용, skill 구현 상태, 노트 존재 여부, MOC 일치 여부에 관한 주장은 확인 환경과 snapshot을 명시해야 한다.
- 두 에이전트가 동일한 파일 버전 또는 저장소 상태를 확인하지 않았다면 구현 상태 차이를 오류로 단정하지 않는다.

## Implementation Status Update

- 확인 환경: `Codex local snapshot`
- 확인일: `2026-06-02`
- 상태: `pilot implementation completed; live AWS validation pending`
- `C:\Users\Unoh\.codex\skills\obsidian-study-vault-curator\`에 thin router와 조건부 reference 구조를 반영했다.
- 구현된 reference는 `Live Lab Capture`, 내부 revision checkpoint, Lab Reconstruction, PDF Concept Note 작성, 외부 검증과 보충, 품질 검토, Vault Routing, 보조 노트 유형 처리를 담당한다.
- 새 파일, source asset, wiki link, embed, frontmatter, folder path를 편집할 때만 `vault-map-and-routing.md`를 추가로 읽는 조건부 dependency를 반영했다.
- 사용자가 수업 직후 별도 `Revision Bridge` 양식을 반드시 작성하는 방향은 채택하지 않는다. 관찰, 해석, 가설, 미해결 항목 분리는 AI 내부 checkpoint로 축소 구현했다.
- pilot 구현은 실제 AWS 수업 검증 완료를 의미하지 않는다. 아래의 과거 판단과 후보 기록은 역사 기록으로 보존하되, 현재 구현 상태를 판단할 때는 이 업데이트를 우선한다.

---

# 1. 상태 표기 규칙

| 상태            | 의미                                                    |
| ------------- | ----------------------------------------------------- |
| `확인됨`         | 업로드된 파일 또는 공식/1차 원문 페이지를 직접 확인함                       |
| `초록 확인`       | 논문의 서지정보와 abstract를 직접 확인했으나 전체 본문을 정밀 검토하지 않음        |
| `간접 확인`       | 다른 검토 논문 또는 참고문헌 목록을 통해 존재·관련성을 확인했으나 원문 판단은 제한됨      |
| `Codex 보고`    | Codex가 조사·실행했다고 보고했으나 이 문서 작성 과정에서 동일 환경을 직접 재검증하지 않음 |
| `채택`          | 현재 workflow 운영 원칙으로 사용해도 됨                            |
| `유망 / 테스트 필요` | 근거가 있으나 실제 vault workflow에서 시험 후 반영해야 함               |
| `보류`          | 가능성은 있으나 아직 규칙으로 만들지 않음                               |
| `기각`          | 현재 workflow의 기본 원칙으로 삼지 않음                            |

## 1.1 Verification Scope of the Synthesis Pass

### 전체를 다시 읽은 연구 메모 입력

Codex는 synthesis pass에서 사용자가 제공한 붙여넣기 연구 메모 첨부 4개를 전체 재독했다.

이 문장은 학술 원문 4개를 전문으로 다시 읽었다는 의미가 아니다.

### 학술 및 운영 자료 검증 수준

| 검증 수준 | 의미 |
| --- | --- |
| `전문 확인` | 접근 가능한 전체 원문을 해당 pass에서 읽음 |
| `초록 확인` | 초록 또는 출판사 summary를 직접 확인했으나 전문을 정밀 검토하지 않음 |
| `공식 페이지 확인` | 공식 제품, 문서, 저장소 또는 출판 페이지를 직접 확인함 |
| `이전 조사에서 유지` | 연구 대장에는 남기지만 이번 pass에서 다시 확인하지 않음 |
| `커뮤니티 사례` | 실무 workflow 예시이며 학습 효과 증거로 승격하지 않음 |

학술 자료별 확인 수준은 개별 항목과 Source Register를 기준으로 판단한다.

---

# 2. 연구가 시작된 배경

## 2.1 출발점

AWS 진도를 시작하기 전에 클라우드/AWS 인덱스를 준비했고, 이후 `AWS기초.pdf`가 들어오면서 PDF 기반으로 실제 학습 범위를 다시 잡게 되었다.

PDF는 다음처럼 구성되어 있었다.

| PDF viewer 기준 범위 | 주제                                                                              |
| ---------------- | ------------------------------------------------------------------------------- |
| p.2–12           | 클라우드 유형과 특징, DevOps, Mutable / Immutable, Terraform, IaaS / PaaS / SaaS, AWS 이점 |
| p.13–25          | EC2, 글로벌 인프라, Scale-up / Scale-out, EC2·RDS 기본 구성, VPC 연결 페이지                   |
| p.26–65          | VPC, Subnet, Route Table, IGW, Security Group, Public / Private EC2 접근 검증       |
| p.66–85          | Multi-AZ, Bastion Host, NAT Instance / Gateway, RDS 연계, 웹 서버 구성                 |
| p.86–122         | Route 53, ACM, ALB, HTTPS 연결                                                    |
| p.123–126        | Auto Scaling, S3, CloudFront, Multi-Region DR, CodePipeline                     |

PDF는 `Copyright © 2018` 자료이고, 본문 안쪽의 슬라이드 번호와 PDF viewer 기준 페이지 번호가 일부 다르다. 따라서 출처 기록은 PDF viewer 기준 페이지 번호를 사용해야 한다.

## 2.2 첫 번째 AWS 노트 작성

첫 번째 묶음 `p.2–12`를 바탕으로 다음 Concept Note를 작성했다.

```text
10_학습 노트/클라우드/AWS/개념 노트/클라우드 컴퓨팅과 AWS 입문.md
```

이 노트는 다음을 포함했다.

* Cloud Computing과 On-Demand
* On-Premises와 On-Demand의 구분
* Public Cloud와 Private Cloud
* OpenStack 질문에 대한 설명
* Shared Responsibility Model
* 클라우드 장점과 오해 방지
* IaaS / PaaS / SaaS
* AWS 기원 표현 검증
* DevOps, Mutable / Immutable Infrastructure, Terraform 연결
* 비용 및 리소스 정리 경고
* 공식 자료 출처

## 2.3 문제 발생

결과물 자체는 상당히 양호했지만, 작성 과정에서 다음이 한 흐름 안에 섞였다.

```text
PDF 범위 분석
→ RAW 메모 해석
→ 개념 노트 설계
→ 공식 문서 팩트 보정
→ 파일 작성
→ MOC 갱신
→ skill 개선 논의
→ 다음 노트 작성 프롬프트 설계
```

그 결과:

* 노트 작성 전에 판단해야 할 범위가 계속 커졌다.
* Codex에게 실제 파일 편집뿐 아니라 범위 판단·구조 결정·공식 조사까지 맡기려는 흐름이 생겼다.
* MOC 수정이 노트 안정화보다 먼저 끼어들었다.
* 좋은 노트를 만들기 위한 규칙이 계속 추가되며 skill 비대화 위험이 생겼다.
* Codex와 GPT 모두 사용자의 직전 판단에 끌려가 결론을 흔드는 동조 현상이 나타났다.

## 2.4 중단 결정

사용자는 AWS 노트 작성을 일단 중단하고, AI가 학습 노트를 만드는 방식 자체를 더 연구하라고 지시했다.

이 시점에서 목표는 더 이상 “다음 AWS 노트를 빨리 만든다”가 아니라 다음으로 바뀌었다.

> AI가 사용자의 실제 학습을 훼손하지 않으면서, Obsidian 기반 학습 자료를 정확하고 재사용 가능하게 정리하도록 만드는 workflow와 skill을 설계한다.

---

# 3. 현재 파일 및 skill 상태

## 3.1 현재 업로드된 skill 파일에서 확인된 것

### `SKILL.md`

현재 확인된 규칙:

* 관련 MOC, 대상 노트, 주변 노트, 템플릿만 먼저 읽는다.
* 작업을 routing/MOC, concept, lab, troubleshooting, project, certification, source-material indexing 중 하나로 분류한다.
* 여러 소스가 함께 쓰이면 최종 작성 전에 `pre-draft synthesis pass`를 수행한다.
* synthesis 과정에서 `learning spine`, `core`, `bridge`, `appendix / TMI`, 출처 충돌, 노트 분리 필요성, 설명 순서를 판단한다.
* PDF 기반 작업은 PDF 내용을 흡수한 standalone concept note를 작성한다.
* 사용자의 실제 수행 과정, 스크린샷, 관찰 결과는 별도 lab note로 유지한다.
* RAW evidence에는 질문, 오류, 강사 표현, 명령, 출력, 스크린샷을 보존한다.
* Obsidian 기능은 이해와 탐색성을 실제로 개선할 때만 사용한다.
* 실습이 성공/실패 checkpoint에 도달하면 chronological append를 멈추고 hierarchy pass를 수행한다.

### `note-type-playbooks.md`

현재 확인된 규칙:

* Callout, 표, Mermaid, 이미지, Properties, Dataview는 장식이 아니라 이해·검색 보조를 위해서만 사용한다.
* 여러 소스가 들어오는 경우 임시 source map을 먼저 만든다.
* Concept Note는 하나의 `learning spine` 중심으로 쓴다.
* PDF의 순서나 fact-check checklist를 본문 heading 구조로 만들지 않는다.
* `core`, `bridge`, `appendix / TMI`는 시각적 무게를 다르게 둔다.
* 설명 목적 없는 표, 이미지, callout, Mermaid를 추가하지 않는다.
* PDF-derived note는 PDF를 다시 열지 않아도 이해될 정도로 내용을 흡수하되, 사용자 실행 증거는 lab note로 분리한다.
* MOC는 탐색용으로 얇게 유지한다.
* 기존 웹보안 노트에서 재사용할 구조 패턴과 그대로 복제하지 않을 패턴이 명시되어 있다.

### `lab-note-reconstruction.md`

현재 확인된 규칙:

* 실제 명령, 화면, 오류, 성공/실패 관찰이 쌓인 mature lab note에 적용한다.
* 결과와 증거를 상단에 배치한다.
* 구성도, 역할·신뢰 경계, 실제 절차, 디버깅, 실무 의미, 남은 확인 순으로 재구성할 수 있다.
* Mermaid는 시스템·브라우저·서버·네트워크 경계가 중요한 경우에 사용한다.
* 실제 증거 없이 성공을 주장하지 않는다.
* raw mistake를 삭제하지 않고 debugging/evidence로 정리한다.

### `vault-map-and-routing.md`

현재 확인된 규칙:

* vault는 `Home → area MOC → subject MOC → concrete note` 구조를 사용한다.
* MOC는 전체 설명을 복제하지 않고 라우팅한다.
* 존재하지 않는 wiki link는 placeholder로 만들지 않는다.
* source PDF와 asset은 `40_자료/`에 둔다.
* MOC/index 작업에서는 `git status --short`, `git diff --check`, `rg --files` 등을 사용해 링크와 변경 상태를 검증한다.

## 3.2 아직 실제 skill에 반영되지 않은 제안

아래는 논의되었지만 현재 업로드 파일 기준으로는 아직 명시적으로 반영되지 않은 제안이다.

| 제안                              | 상태               |
| ------------------------------- | ---------------- |
| `Revision Bridge` 단계 신설         | 유망 / 테스트 필요      |
| `AI Assistance Boundary` 규칙 명시  | 유망 / 테스트 필요      |
| `SKILL.md`를 얇은 phase router로 축약 | 보류               |
| `live-capture.md` 신설            | 보류               |
| `pdf-structure-map.md` 신설       | 보류               |
| `concept-note-authoring.md` 신설  | 보류               |
| `note-quality-review.md` 신설     | 보류               |
| 안정화된 Concept Note에 회상 질문 추가     | 유망 / 적용 범위 검토 필요 |
| 작성 종료 후 MOC 갱신 gate 명문화         | 유망 / 테스트 필요      |

---

# 4. Codex가 조사하고 주장한 내용

## 4.1 Codex의 핵심 진단

Codex는 현재 skill과 작업 방식에 대해 다음 문제를 지적했다.

> 좋은 최종 노트를 만들기 위한 규칙이 많아지면서, 수업 중 포착, PDF 범위 지도, 노트 설계, 파일 작성, 복습, MOC 갱신이 한 번에 묶였다.

Codex가 본 실패 구조:

```text
실시간 포착
→ 사후 정리
→ PDF 분석
→ concept note authoring
→ 공식 검증
→ MOC routing
→ 복습 설계
```

이 단계들이 분리되지 않으면 다음 문제가 생긴다고 보았다.

* 수업 중에는 기록 자체가 어려워진다.
* RAW가 사용자의 사고 흔적이 아니라 AI 정리용 재료처럼 취급된다.
* Concept Note가 학습 흐름보다 검증 목록 중심으로 변한다.
* MOC가 아직 안정화되지 않은 노트를 미리 조직한다.
* AI가 학습자의 질문과 판단을 대신 생성한다.
* skill이 점점 길어지고 모든 작업에서 불필요하게 로드된다.

## 4.2 Codex가 제안한 단계 구조

Codex는 다음 phase 분리를 제안했다.

| 단계        | 허용 결과물                 | 금지                   |
| --------- | ---------------------- | -------------------- |
| 실시간 포착    | 스크린샷, 명령, 값, 오류, 짧은 질문 | 구조 개편, 노트 분할, MOC 갱신 |
| PDF 범위 지도 | 큰 주제 범위와 애매한 경계        | 파일명과 노트 개수 확정        |
| 노트 설계     | 학습 목표 1개, 흐름, 포함·보류 범위 | 파일 편집                |
| 최종 작성     | 합의된 노트만 작성             | 주변 주제 확장             |
| 복습 보강     | 자기 설명 질문, 회상 문제        | 본문을 문제집화             |
| 라우팅       | 안정화된 노트의 MOC 연결        | 작성 중 동시 갱신           |

## 4.3 Codex가 조사한 학습 원리

Codex는 다음 방향을 제안했다.

| 주장                                       | Codex 판단 |
| ---------------------------------------- | -------- |
| 수업 중 필기는 인지 부담이 크므로 최소 포착 중심이어야 한다       | 채택 후보    |
| 사후 정리는 문장을 늘리는 것이 아니라 인과 흐름과 경계를 설명해야 한다 | 채택 후보    |
| AI가 잘 쓴 완성 노트만으로는 학습이 충분하지 않다            | 채택 후보    |
| 회상과 자기 설명은 별도 학습 활동으로 필요하다               | 채택 후보    |
| 초심자에게는 구성 요소 설명과 worked example이 필요하다    | 채택 후보    |
| Callout, 표, Mermaid는 이해를 돕는 경우에만 써야 한다   | 채택 후보    |
| 초심자와 복습자의 노트 밀도는 같지 않아야 한다               | 채택 후보    |
| Atomic note는 교리처럼 강제할 수 없다               | 채택 후보    |

## 4.4 Codex가 실제 반영했다고 보고한 skill 변경

Codex는 다음 내용을 `SKILL.md`와 `note-type-playbooks.md`에 반영했다고 보고했다.

* Obsidian 기능을 이해 보조 수단으로만 사용
* 웹보안 개념 노트의 좋은 패턴 명시
* Concept Note 작성 전 `learning spine` 결정
* `core / bridge / appendix·TMI` 구분
* 작성 전 source synthesis pass
* PDF, RAW, 공식 자료의 역할 분리

이 항목들은 현재 업로드된 skill 파일에서 실제로 확인되었다.

## 4.5 Codex의 추가 개편 제안

Codex는 이후 다음 구조로 skill을 다시 나누자는 제안을 했다.

```text
SKILL.md
references/live-capture.md
references/pdf-structure-map.md
references/concept-note-authoring.md
references/lab-reconstruction.md
references/vault-routing.md
references/note-quality-review.md
```

이 제안의 목표는 모든 규칙을 매 작업마다 읽게 하지 않고, 현재 phase에 필요한 reference만 로드하게 만드는 것이다.

### 현재 판정

* 방향은 합리적이다.
* 그러나 현재 skill 개선의 실제 효과를 시험하기도 전에 다시 구조를 뜯는 것은 이르다.
* 개편 전에 dry-run으로 현재 skill의 실패 유형을 먼저 관찰해야 한다.

---

# 5. GPT가 추가 검토하고 수정한 내용

## 5.1 Codex 판단 중 채택한 것

| Codex 주장                            | GPT 판정 |
| ----------------------------------- | ------ |
| 실시간 RAW와 최종 노트 작성 분리                | 채택     |
| PDF 범위 지도와 실제 노트 작성 분리              | 채택     |
| Concept Note는 하나의 learning spine 중심 | 채택     |
| 공식 문서는 보정 수단으로 사용                   | 채택     |
| Obsidian 표현 기능은 필요할 때만 사용           | 채택     |
| 완성 노트와 복습 활동은 분리                    | 채택     |
| Atomic note 강제 금지                   | 채택     |
| 초심자와 복습자의 설명 밀도 차이 고려               | 채택     |

## 5.2 Codex 판단 중 수정한 것

### 즉시 skill 대개편은 이르다

Codex는 조사 이후 바로 phase router 형태의 개편을 제안했다. GPT 판단은 다음과 같다.

```text
현재 skill로 dry-run
→ 반복 실패 유형 확인
→ 필요한 규칙만 수정
→ 그 뒤 파일 구조 분리 여부 결정
```

이유:

* 현재 skill에는 이미 핵심 개선 규칙이 실제 반영되어 있다.
* 바로 다시 구조를 바꾸면 무엇이 효과 있었는지 확인할 수 없다.
* 규칙 추가가 또 다른 비대화를 만들 수 있다.

### 모든 Concept Note에 확인 질문을 강제하지 않는다

Retrieval practice는 강한 연구 근거가 있지만, 모든 파일에 확인 질문을 붙이는 것은 별도 문제다.

| 노트 유형                | 확인 질문 처리                |
| -------------------- | ----------------------- |
| 안정화된 핵심 Concept Note | 2–5개 추가 가능              |
| RAW                  | 기본적으로 넣지 않음             |
| PDF 구조 지도            | 넣지 않음                   |
| MOC                  | 넣지 않음                   |
| Lab Note             | 결과·증거 검증 질문이 더 중요할 수 있음 |
| 복습 전용 산출물            | 회상 질문 중심으로 구성 가능        |

### AI가 최초 판단까지 대신하면 안 된다

AI는 다음을 도와도 된다.

* 사용자가 기록한 RAW의 정돈
* 공식 문서 기반의 오래된 표현 보정
* 합의된 설계에 따른 파일 작성
* 범위 초과와 부정확성 검토

하지만 다음을 기본 동작으로 맡기면 위험하다.

* 사용자가 무엇을 궁금해했는지 대신 만들어내기
* 실제 학습 목표를 자동 확정하기
* 실습하지 않은 결과를 완성 노트처럼 쓰기
* 노트 작성과 MOC 확장까지 한꺼번에 진행하기
* 복습 활동을 이미 완료된 것처럼 취급하기

---

# 6. 연구 Evidence Register

## 6.1 필기, 복습, revision

### Kobayashi, 2006

| 항목          | 내용                                                                                                                                                                   |
| ----------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 자료명         | Combined Effects of Note-Taking/-Reviewing on Learning and the Enhancement through Interventions: A Meta-Analytic Review                                             |
| 유형          | Peer-reviewed meta-analysis                                                                                                                                          |
| 검증 상태       | Abstract 직접 확인                                                                                                                                                       |
| 핵심 내용       | 33개 연구를 분석했으며, note-taking과 reviewing의 조합은 학습에 상당한 효과를 보였다. 단순 verbal instruction보다 framework 또는 instructor notes 제공 같은 개입이 더 효과적이었다. 낮은 학업 수준 참가자가 개입 효과를 더 크게 얻었다. |
| 적용 판단       | 채택                                                                                                                                                                   |
| workflow 적용 | 실시간 RAW와 사후 정리를 분리하되, 사후 정리에 구조적 scaffold를 제공한다.                                                                                                                     |
| 한계          | 특정 Obsidian 또는 AI workflow를 직접 연구한 것은 아니다.                                                                                                                           |

### Luo, Kiewra & Samuelson, 2016

| 항목          | 내용                                                                                                                                                                                                 |
| ----------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 자료명         | Revising lecture notes: how revision, pauses, and partners affect note taking and achievement                                                                                                      |
| 유형          | Peer-reviewed experimental study                                                                                                                                                                   |
| 검증 상태       | Abstract 직접 확인                                                                                                                                                                                     |
| 핵심 내용       | 필기를 `recording → review`가 아니라 `recording → revision → review`의 세 단계로 볼 수 있다고 제안한다. revision 집단은 recopy 집단보다 추가 정보를 더 기록하고 관계 문항에서 다소 높은 점수를 얻었다. 강의 종료 후 한 번 수정하는 것보다 강의 중 pause에서 수정하는 조건이 더 나았다. |
| 적용 판단       | 유망 / 테스트 필요                                                                                                                                                                                        |
| workflow 적용 | `Revision Bridge` 단계 후보: 수업 직후 RAW에 관찰·설정 이유·미해결 질문만 짧게 보충한다.                                                                                                                                      |
| 한계          | AWS/보안 실습과 동일한 환경은 아니다. 실제 수업에서 시험해야 한다.                                                                                                                                                           |

### Piolat, Olive & Kellogg, 2005

| 항목             | 내용                                             |
| -------------- | ---------------------------------------------- |
| 자료명            | Cognitive effort during note taking            |
| 유형             | Peer-reviewed article                          |
| 검증 상태          | 서지정보는 확인, 본문 해석 재확인 필요                         |
| 기존 논의에서 사용된 주장 | note-taking은 이해·선택·기록을 동시에 요구하여 인지 부담이 클 수 있다. |
| 적용 판단          | 근거 후보로 유지하되, 직접 판정 근거로 과장하지 않는다.               |
| 다음 행동          | 필요 시 원문 확보 후 정밀 검토.                            |

---

## 6.2 Retrieval practice, spacing, self-explanation

### Dunlosky et al., 2013

| 항목          | 내용                                                                                                                                                                                                                                            |
| ----------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 자료명         | Improving Students’ Learning With Effective Learning Techniques: Promising Directions From Cognitive and Educational Psychology                                                                                                               |
| 유형          | Review monograph                                                                                                                                                                                                                              |
| 검증 상태       | Abstract 및 핵심 권고 직접 확인                                                                                                                                                                                                                        |
| 핵심 내용       | `practice testing`과 `distributed practice`는 high utility로 평가되었다. `self-explanation`, `elaborative interrogation`, `interleaved practice`는 moderate utility로 평가되었다. `summarization`, `highlighting`, `rereading` 등은 전반적으로 low utility 평가를 받았다. |
| 적용 판단       | 채택                                                                                                                                                                                                                                            |
| workflow 적용 | 예쁜 요약 노트만 저장하고 반복 읽기하는 구조로 끝내지 않는다. 복습 단계에서 회상 또는 적용 활동을 고려한다.                                                                                                                                                                                |
| 한계          | 모든 기술·학습자·과목에서 동일한 구현을 강제하지 않는다.                                                                                                                                                                                                              |

### Roediger & Karpicke, 2006

| 항목             | 내용                                                                       |
| -------------- | ------------------------------------------------------------------------ |
| 자료명            | Test-Enhanced Learning: Taking Memory Tests Improves Long-Term Retention |
| 유형             | Peer-reviewed experimental study                                         |
| 검증 상태          | 이 문서 작성 과정에서 원문 페이지 접근 제한. 기존 연구 방향과 후속 검토에서 일관되게 참조됨.                   |
| 기존 논의에서 사용된 주장 | 반복 읽기보다 retrieval test가 지연 기억 유지에 유리할 수 있다.                              |
| 적용 판단          | Dunlosky 및 spacing 연구와 함께 운영 원칙을 지지하는 참고 근거로 유지                          |
| workflow 적용    | 안정화된 노트는 이후 회상 활동으로 전환 가능해야 한다.                                          |
| 한계             | 현재 문서에서는 독립적 수치·세부 실험 조건을 확정하지 않는다.                                      |

### Cepeda et al., 2006

| 항목          | 내용                                                                                                              |
| ----------- | --------------------------------------------------------------------------------------------------------------- |
| 자료명         | Distributed Practice in Verbal Recall Tasks: A Review and Quantitative Synthesis                                |
| 유형          | Review and quantitative synthesis                                                                               |
| 검증 상태       | 원문 PDF 핵심 요약 직접 확인                                                                                              |
| 핵심 내용       | spaced learning은 massed learning보다 장기 보존에 일관된 이점이 있다. 다만 간격은 길수록 무조건 좋은 것이 아니며, 학습 간격과 목표 보존 기간의 상호작용을 고려해야 한다. |
| 적용 판단       | 채택                                                                                                              |
| workflow 적용 | 복습을 한다면 한 번의 질문 생성으로 끝내지 않고, 시차를 둔 재확인 단계가 필요하다.                                                                |
| 한계          | 연구는 주로 verbal memory task에 집중되어 있으며, AWS 실습 skill retention에 그대로 동일 적용한다고 단정하지 않는다.                             |

### Chi et al., 1989 / Self-explanation 계열

| 항목             | 내용                                                                                   |
| -------------- | ------------------------------------------------------------------------------------ |
| 자료명            | Self-Explanations: How Students Study and Use Examples in Learning to Solve Problems |
| 유형             | 고전 self-explanation 연구                                                               |
| 검증 상태          | 원문 세부 결과는 이번 문서에서 직접 재검증하지 않음. Fiorella review 및 후속 연구에서 핵심 개념이 재확인됨.                |
| 기존 논의에서 사용된 주장 | 학습자가 예시의 단계와 원리를 스스로 설명할 때 이해와 전이가 향상될 수 있다.                                         |
| 적용 판단          | 원칙 수준에서 유지                                                                           |
| workflow 적용    | 실습 노트는 클릭 목록보다 “왜 이 설정이 필요한가”를 설명할 수 있게 구성한다.                                        |
| 한계             | 사용자가 설명하지 않고 AI가 대신 설명하는 것만으로 동일 효과를 기대하면 안 된다.                                      |

---

## 6.3 Generative learning, worked example, 초심자 설계

### Fiorella, 2023

| 항목          | 내용                                                                                                                                                                                                     |
| ----------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| 자료명         | Making Sense of Generative Learning                                                                                                                                                                    |
| 유형          | Open-access review article                                                                                                                                                                             |
| 검증 상태       | 본문 핵심 부분 직접 확인                                                                                                                                                                                         |
| 핵심 내용       | Generative learning은 학습자가 제공된 자료를 기존 지식과 통합해 coherent mental representation을 만드는 활동이다. 설명하기, 시각화하기, 실행/시뮬레이션하기는 서로 다른 보완적 기능을 갖는다. 이러한 활동은 학습자의 prior knowledge, 자료 특성, 제공되는 guidance 수준에 따라 효과가 달라진다. |
| 중요한 세부 판단   | learner-generated explanation·visualization의 품질이 중요하며, 단순히 제공된 설명이나 그림을 복제하는 것만으로는 inference generation이 충분하지 않을 수 있다.                                                                                 |
| 적용 판단       | 강하게 채택                                                                                                                                                                                                 |
| workflow 적용 | AI가 설명문을 작성하더라도 사용자가 질문·관찰·회상·적용에 참여할 통로를 남긴다. Mermaid나 표는 관계를 조직하는 데 실제로 도움이 될 때만 사용한다.                                                                                                               |

### Renkl, 2002

| 항목             | 내용                                                                                    |
| -------------- | ------------------------------------------------------------------------------------- |
| 자료명            | Worked-out examples: instructional explanations support learning by self-explanations |
| 유형             | Peer-reviewed article                                                                 |
| 검증 상태          | 기존 논의에서 확인되었으나 이번 최종 대장에서는 원문 직접 재열람 미완                                               |
| 기존 논의에서 사용된 주장 | worked example은 초보 학습에 유용하며, solution step의 이유를 설명하도록 지원할 때 더 가치가 있다.                 |
| 적용 판단          | 유망 / AWS 실습에 적합                                                                       |
| workflow 적용    | AWS Lab Note는 `설정 → 결과`만 나열하지 않고 `왜 이 설정이 필요한가`를 설명하는 구조를 우선 검토한다.                    |
| 한계             | 구체적 AWS lab template로 즉시 강제하지 않는다.                                                    |

### Mayer & Pilegard, 2014

| 항목          | 내용                                                                                                                                                                                                            |
| ----------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 자료명         | Principles for Managing Essential Processing in Multimedia Learning: Segmenting, Pre-training, and Modality Principles                                                                                        |
| 유형          | Handbook chapter summarizing experimental evidence                                                                                                                                                            |
| 검증 상태       | Summary 직접 확인                                                                                                                                                                                                 |
| 핵심 내용       | 복잡한 멀티미디어 자료가 빠르게 제시되면 essential overload가 발생할 수 있다. learner-paced segmenting과, 주요 개념의 이름·특성을 먼저 알려주는 pre-training은 깊은 학습에 도움이 될 수 있다. Summary에서는 segmenting이 10/10 실험, pre-training이 13/16 실험에서 지지되었다고 제시한다. |
| 적용 판단       | 채택                                                                                                                                                                                                            |
| workflow 적용 | VPC·Subnet·Route Table·Security Group처럼 용어가 많은 노트는 먼저 구성요소 이름과 역할을 잡고 흐름으로 넘어간다. PDF 한 덩어리를 그대로 설명하지 않고 의미 있는 segment로 나눈다.                                                                                   |
| 한계          | 정적인 Markdown 노트와 멀티미디어 강의가 완전히 같은 조건은 아니다.                                                                                                                                                                    |

### Kalyuga, 2007

| 항목          | 내용                                                                                            |
| ----------- | --------------------------------------------------------------------------------------------- |
| 자료명         | Expertise Reversal Effect and Its Implications for Learner-Tailored Instruction               |
| 유형          | Review article                                                                                |
| 검증 상태       | Abstract 직접 확인                                                                                |
| 핵심 내용       | prior knowledge 수준과 instructional technique 효과가 상호작용할 수 있으며, 초보자에게 유용한 지원이 숙련자에게는 비효율적일 수 있다. |
| 적용 판단       | 채택                                                                                            |
| workflow 적용 | 첫 학습용 노트와 복습용 노트를 같은 밀도·같은 scaffold로 강제하지 않는다.                                                |
| 한계          | 개인별 자동 적응 시스템을 지금 바로 구축하자는 뜻은 아니다.                                                            |

---

## 6.4 시각화와 개념 지도

### Nesbit & Adesope, 2006

| 항목          | 내용                                                                                                                                                                     |
| ----------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 자료명         | Learning With Concept and Knowledge Maps: A Meta-Analysis                                                                                                              |
| 유형          | Meta-analysis                                                                                                                                                          |
| 검증 상태       | Abstract 직접 확인                                                                                                                                                         |
| 핵심 내용       | 55개 연구, 5,818명을 검토했으며, node-link diagram을 만들거나 수정하거나 읽는 학습은 여러 조건에서 knowledge retention 증가와 연관되었다. 다만 사용 방식과 비교 조건에 따라 효과 크기가 작음부터 큼까지 달랐고, 대부분의 하위 분석에서 유의한 이질성이 있었다. |
| 적용 판단       | 조건부 채택                                                                                                                                                                 |
| workflow 적용 | 관계 자체가 학습 목표인 경우 Mermaid나 Canvas 후보가 된다. 예: VPC의 라우팅 흐름, Bastion/NAT 경계, Region/AZ 장애 격리.                                                                              |
| 기각할 확대 해석   | 모든 노트에 그림을 넣는 것이 좋다.                                                                                                                                                   |

### 시각화 사용에 대한 최종 기준

| 주제                    | 기본 표현         |
| --------------------- | ------------- |
| 정의·주의사항 한두 개          | 문장 또는 callout |
| 두세 개 개념 비교            | 표             |
| 네트워크·권한·요청 흐름         | Mermaid 후보    |
| 실제 Console 화면이나 오류 증거 | 스크린샷 + 관찰 포인트 |
| 복잡한 여러 노트 연결 탐색       | Canvas 후보     |
| 단순 서비스 목록             | 다이어그램 금지      |

추가 후보 규칙:

```text
Diagram은 개념 간 관계가 학습 목표일 때만 사용한다.
연결선에는 가능하면 관계의 의미를 표시한다.
예: 포함, 라우팅, 허용, 접근, 저장, 장애 격리.
```

상태: `유망 / 테스트 필요`.

---

## 6.5 디지털 필기와 매체

### Morehead, Dunlosky & Rawson, 2019

| 항목          | 내용                                                                                                                                                                   |
| ----------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 자료명         | How Much Mightier Is the Pen than the Keyboard for Note-Taking? A Replication and Extension of Mueller and Oppenheimer (2014)                                        |
| 유형          | Replication and extension study                                                                                                                                      |
| 검증 상태       | Abstract 직접 확인                                                                                                                                                       |
| 핵심 내용       | 손필기 우위를 시사하는 경향은 있었지만 실험 1·2에서 집단 간 성취 차이는 일관되지 않았다. 노트를 복습한 뒤에는 차이가 더 줄었다. 직접 재현 결과들을 합친 메타분석에서는 손필기 우위 효과가 작고 유의하지 않았다. 저자들은 어떤 방법이 필기 기능 향상에 우월한지 단정하기 이르다고 결론냈다. |
| 적용 판단       | 채택                                                                                                                                                                   |
| workflow 적용 | Obsidian 기반 디지털 노트 자체를 학습에 불리하다고 가정하지 않는다.                                                                                                                           |

### Luo et al., 2018

| 항목          | 내용                                                                                                                                   |
| ----------- | ------------------------------------------------------------------------------------------------------------------------------------ |
| 자료명         | Laptop versus longhand note taking: effects on lecture notes and achievement                                                         |
| 유형          | Experimental study                                                                                                                   |
| 검증 상태       | Abstract 직접 확인                                                                                                                       |
| 핵심 내용       | laptop 필기자는 더 많은 단어와 verbatim lecture strings를 기록했고, longhand 필기자는 더 많은 visual notes를 기록했다. 성취 결과는 강의 자료의 성격과 노트 review 여부에 따라 달라졌다. |
| 적용 판단       | 채택                                                                                                                                   |
| workflow 적용 | 기술 실습에서는 디지털 RAW가 명령·로그·설정값·캡처 보존에 유리할 수 있으며, 이후 revision/review 설계가 중요하다.                                                           |

### 최종 판정

| 주장                                   | 판정 |
| ------------------------------------ | -- |
| 손필기가 항상 디지털보다 낫다                     | 기각 |
| 디지털 노트는 verbatim capture와 방치 위험이 있다  | 채택 |
| 기술 실습에서는 디지털 RAW가 적합할 수 있다           | 채택 |
| 중요한 것은 매체만이 아니라 revision과 review 구조다 | 채택 |

### 교차검증 보정: Flanigan et al. (2024)

- 자료명: *Typed Versus Handwritten Lecture Notes and College Student Achievement: A Meta-Analysis*
- DOI: [10.1007/s10648-024-09914-w](https://doi.org/10.1007/s10648-024-09914-w)
- 유형: peer-reviewed meta-analysis
- 검증 상태: 출판사 초록 확인

| 결과 | 보고된 내용 |
| --- | --- |
| 필기 후 복습을 포함한 학업 성취도 | 손필기가 더 높은 성취도와 연관됨: Hedges' `g = 0.248`, `p < .001` |
| 기록량 | 타이핑이 더 많은 기록량과 연관됨: Hedges' `g = 0.919`, `p < .001` |

#### 보정된 판정

다음 두 확대 해석은 모두 기각한다.

```text
손필기는 모든 학습 작업에서 항상 우월하다.
디지털과 손필기 매체의 차이는 중요하지 않다.
```

- AWS와 보안 실습에서는 명령어, 설정값, 오류 메시지, 스크린샷, 로그, 리소스 상태를 정확히 보존해야 하므로 디지털 RAW가 운영상 적합하다.
- 손필기 기반 개념 복습 또는 회상은 개념 학습과 기억 정착에 작지만 의미 있는 이점이 있을 수 있다.
- 이 사용자에게 손필기 복습이 실용적인 이득을 주는지는 선택적 보조 수단으로 시험하며, 현재 workflow의 필수 조건으로 강제하지 않는다.

---

## 6.6 AI 보조 note-taking 및 학습

### NoTeeline, 2024 / IUI 2025

| 항목          | 내용                                                                                                                                                                                                                |
| ----------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 자료명         | NoTeeline: Supporting Real-Time, Personalized Notetaking with LLM-Enhanced Micronotes                                                                                                                             |
| 유형          | HCI system study                                                                                                                                                                                                  |
| 검증 상태       | arXiv abstract 및 publication comment 직접 확인                                                                                                                                                                        |
| 연구 상태       | arXiv v3, related DOI 존재, IUI 2025 conditional acceptance 표기                                                                                                                                                      |
| 핵심 내용       | 자동 생성 노트는 사용자 의도와 active engagement를 약화시킬 수 있다는 문제를 전제로, 사용자가 남긴 micronote를 LLM이 확장하는 구조를 제안한다. n=12 within-subject study에서 manual baseline 대비 작성 텍스트량 47.0% 감소, 완료 시간 43.9% 감소, factual correctness 93.2%를 보고했다. |
| 적용 판단       | 유망 / 테스트 필요                                                                                                                                                                                                       |
| workflow 적용 | 사용자의 RAW 질문·관찰·설정값을 AI가 확장·보정하는 구조는 타당한 후보다.                                                                                                                                                                      |
| 한계          | 장기 학습 효과를 확정한 연구는 아니며 표본이 작다.                                                                                                                                                                                     |

### Chen et al., 2025 / CSCW 2025

| 항목          | 내용                                                                                                                                                                                   |
| ----------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| 자료명         | More AI Assistance Reduces Cognitive Engagement: Examining the AI Assistance Dilemma in AI-Supported Note-Taking                                                                     |
| 유형          | HCI experiment                                                                                                                                                                       |
| 검증 상태       | arXiv abstract 및 accepted comment 직접 확인                                                                                                                                              |
| 연구 상태       | arXiv 제출 2025-09-03, CSCW 2025 accepted 표기                                                                                                                                           |
| 핵심 내용       | n=30 within-subject 실험에서 Automated AI, Intermediate AI, Minimal AI 필기 조건을 비교했다. Intermediate AI에서 post-test 점수가 가장 높았고 Automated AI에서 가장 낮았다. 참가자는 낮은 부담과 편의 때문에 Automated AI를 선호했다. |
| 적용 판단       | 강한 경고 근거 / 일반 법칙으로는 보류                                                                                                                                                               |
| workflow 적용 | 편리한 자동 완성 방식이 실제 학습에 가장 좋은 방식이라고 가정하지 않는다. AI가 사용자의 사고를 완전히 대체하는 동작은 기본값으로 두지 않는다.                                                                                                   |
| 한계          | 소규모 최근 연구이며 다른 과목·환경으로의 일반화는 제한된다.                                                                                                                                                   |

### Lehmann, Cornelius & Sting, 2024/2025

| 항목          | 내용                                                                                                                                                                                  |
| ----------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 자료명         | AI Meets the Classroom: When Do Large Language Models Harm Learning?                                                                                                                |
| 유형          | Pre-registered lab experiments + field study, arXiv 공개본                                                                                                                             |
| 검증 상태       | Abstract 직접 확인                                                                                                                                                                      |
| 핵심 내용       | 전체 평균 학습 결과에서는 LLM 효과가 나타나지 않았으나, 사용 방식에 따라 결과가 달랐다. 연습 문제 해결을 LLM으로 대체한 학생은 더 많은 주제를 다룰 수 있었지만 주제별 이해는 낮아졌고, 설명을 요청하는 방식으로 학습을 보완한 학생은 이해가 증가했다. prior knowledge에 따른 격차 확대도 관찰되었다. |
| 적용 판단       | 채택 후보                                                                                                                                                                               |
| workflow 적용 | AI는 설명·피드백·검증을 제공하는 보조자로 두고, 사용자의 실제 실습 수행과 설명·회상을 대체하지 않는다.                                                                                                                        |
| 한계          | 현재는 arXiv 공개본 기준이며, 보안·클라우드 노트 workflow에 직접 동일 적용한다고 단정하지 않는다.                                                                                                                      |

### AI Assistance Boundary 후보

```text
AI는 사용자가 남긴 RAW, 질문, 실습 증거를 정돈·확장·검증할 수 있다.
AI가 사용자 대신 최초 질문, 관찰, 학습 목표, 실습 결과 판정, 노트 분할, MOC 확장을 자동으로 수행하는 것은 기본 동작으로 두지 않는다.
```

상태: `유망 / 실제 수업 dry-run 후 skill 반영 판단`.

---

# 7. PKM·Obsidian 운영 자료 Register

## 7.1 Andy Matuschak: Atomic note

| 항목          | 내용                                                                                                                     |
| ----------- | ---------------------------------------------------------------------------------------------------------------------- |
| 자료명         | Evergreen notes should be atomic                                                                                       |
| 유형          | PKM 실무 조언 / working note                                                                                               |
| 검증 상태       | 원문 직접 확인                                                                                                               |
| 핵심 내용       | 하나의 노트는 가능하면 하나의 대상에 집중하되, 그 대상을 충분히 포착해야 한다. 너무 넓은 노트는 연결을 흐리고, 너무 조각난 노트는 link network를 파편화한다. 명확한 정답은 없고 tradeoff다. |
| 적용 판단       | 설계 참고로 채택                                                                                                              |
| workflow 적용 | 파일 분리는 독립적인 learning spine, 재참조 가치, 별도 실습·검증 흐름이 있을 때만 한다.                                                             |
| 기각할 확대 해석   | 모든 개념을 즉시 새 파일로 분리한다.                                                                                                  |

## 7.2 Andy Matuschak: Concept-oriented note

| 항목          | 내용                                                                    |
| ----------- | --------------------------------------------------------------------- |
| 자료명         | Evergreen notes should be concept-oriented                            |
| 유형          | PKM 실무 조언 / working note                                              |
| 검증 상태       | 원문 직접 확인                                                              |
| 핵심 내용       | 노트를 저자·책·프로젝트보다 개념 중심으로 구성하면 서로 다른 자료에서 나온 생각을 한 개념 아래 누적하고 연결할 수 있다. |
| 적용 판단       | Concept Note에 한해 채택                                                   |
| workflow 적용 | PDF 제목별 요약본보다, 재사용 가능한 개념 질문 중심의 Concept Note가 적절하다.                  |
| 제한          | RAW, lab note, source map, MOC까지 모두 evergreen 방식으로 강제하지 않는다.          |

## 7.3 Tiago Forte: Progressive Summarization

| 항목          | 내용                                                                                                                                                                  |
| ----------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 자료명         | Progressive Summarization: A Practical Technique for Designing Discoverable Notes                                                                                   |
| 유형          | PKM 실무 조언                                                                                                                                                           |
| 검증 상태       | 원문 직접 확인                                                                                                                                                            |
| 핵심 내용       | note는 discoverability와 context/understanding 사이의 균형을 다룬다. 지나친 압축은 의미를 잃고, 지나친 맥락 보존은 재발견을 어렵게 만든다. 원문을 보존한 채 실제 재검토 시점에 점진적으로 압축하고, 일부 중요한 note만 자신의 말로 상단 요약을 만든다. |
| 적용 판단       | Source/RAW 관리 원칙으로 제한적 채택                                                                                                                                           |
| workflow 적용 | RAW와 source evidence는 원본을 보존하면서 핵심 결과를 상단으로 끌어올릴 수 있다.                                                                                                              |
| 기각할 확대 해석   | 최종 Concept Note 전체를 단순 progressive highlight 방식으로 만든다. Concept Note는 learning spine 기반의 새 설명이어야 한다.                                                                 |

---

# 8. Obsidian 공식 기능 자료 Register

## 8.1 Callouts

| 항목          | 내용                                                     |
| ----------- | ------------------------------------------------------ |
| 자료 유형       | 공식 기능 문서                                               |
| 확인 내용       | Callout은 노트 흐름을 깨지 않고 추가 콘텐츠를 포함하는 기능이며, 접힘과 중첩도 지원한다. |
| 적용 판단       | 기능 사용법의 근거로만 사용                                        |
| workflow 적용 | 결론, 오해, 경고, 근거, 실무 경계를 빠르게 찾게 할 때만 사용한다.               |
| 기각할 확대 해석   | callout을 쓰는 것 자체가 학습 효과를 보장한다.                         |

## 8.2 Internal Links

| 항목          | 내용                                                                                                 |
| ----------- | -------------------------------------------------------------------------------------------------- |
| 자료 유형       | 공식 기능 문서                                                                                           |
| 확인 내용       | Obsidian은 note, attachment, heading, block 단위 internal link를 지원하며, rename 시 link 자동 업데이트 기능도 제공한다. |
| 적용 판단       | vault 탐색성 설계에 사용                                                                                   |
| workflow 적용 | 실제 다시 찾아볼 가치가 있는 concrete note, heading, source asset만 연결한다.                                       |
| 기각할 확대 해석   | link가 많을수록 좋은 노트다.                                                                                 |

## 8.3 Properties

| 항목          | 내용                                                                                                      |
| ----------- | ------------------------------------------------------------------------------------------------------- |
| 자료 유형       | 공식 기능 문서                                                                                                |
| 확인 내용       | Properties는 note에 대한 구조화된 데이터로, text, link, date, tags 등으로 저장된다. 작은 machine-readable metadata를 위한 기능이다. |
| 적용 판단       | 안정 메타데이터에만 사용                                                                                           |
| workflow 적용 | `type`, `topic`, `source`, `source_pages`, `status`, `created`, `aliases` 등에 적합하다.                      |
| 주의          | 본문 설명이나 복잡한 계층 정보를 Properties에 몰아넣지 않는다.                                                                |

## 8.4 Canvas

| 항목          | 내용                                                                                                      |
| ----------- | ------------------------------------------------------------------------------------------------------- |
| 자료 유형       | 공식 기능 문서                                                                                                |
| 확인 내용       | Canvas는 note, PDF, media, webpage를 2D 공간에 배치하고 선·라벨·그룹으로 관계를 표현할 수 있는 visual note-taking core plugin이다. |
| 적용 판단       | 조건부 도구                                                                                                  |
| workflow 적용 | 여러 노트·자료·구성 요소의 관계를 비교해야 할 때만 후보로 둔다.                                                                   |
| 기각할 확대 해석   | AWS 아키텍처 노트는 기본적으로 Canvas를 만들어야 한다.                                                                     |

---

# 9. AI 제품 설계 자료 Register

이 항목은 학습 효과의 직접 근거가 아니라, AI 학습 도구들이 어떤 역할 분리를 채택하는지 보는 참고 자료다.

## 9.1 NotebookLM

| 항목    | 내용                                                                                                                                                                                                                        |
| ----- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 자료 유형 | Google 공식 도움말                                                                                                                                                                                                             |
| 확인 내용 | 업로드한 source에 기반해 inline citation이 달린 응답을 제공하며, study guide, briefing, audio/video overview, mind map, flashcard, quiz, report 등 별도 artifact를 생성한다. Notebook은 특정 project의 source collection이며 notebook 간 정보는 동시에 접근하지 않는다. |
| 설계 참고 | source grounding과 학습 artifact 분리를 참고할 수 있다.                                                                                                                                                                               |
| 한계    | NotebookLM 기능이 학습 효과를 보장한다는 증거는 아니다.                                                                                                                                                                                      |

## 9.2 ChatGPT Study Mode

| 항목    | 내용                                                                                                                                                                                                                     |
| ----- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 자료 유형 | OpenAI 공식 제품 소개                                                                                                                                                                                                        |
| 확인 내용 | guiding questions, Socratic questioning, hints, self-reflection prompts, scaffolded responses, knowledge checks, feedback를 주요 기능으로 제시한다. 현재는 custom system instructions 기반이며, 대화 간 비일관성과 실수가 있을 수 있다고 OpenAI가 직접 명시한다. |
| 설계 참고 | AI는 빠른 정답이나 완성물만 제공하는 것이 아니라 학습자의 참여와 이해 확인을 유도하는 방향을 가질 수 있다.                                                                                                                                                         |
| 한계    | 제품 설명은 장기 학습 효과의 독립 검증 결과가 아니다.                                                                                                                                                                                        |

## 9.3 Gemini Guided Learning

| 항목    | 내용                                                                                             |
| ----- | ---------------------------------------------------------------------------------------------- |
| 자료 유형 | Google 공식 도움말                                                                                  |
| 확인 내용 | Gemini Apps를 tutor처럼 사용하며 guided learning, visual aids, educational resources를 제공할 수 있다고 설명한다. |
| 설계 참고 | 설명, 시각자료, guided interaction의 분리를 참고한다.                                                        |
| 한계    | 효과 검증 자료로 사용하지 않는다.                                                                            |

## 9.4 Claude Learning Mode

| 항목    | 내용                                                                                                                                            |
| ----- | --------------------------------------------------------------------------------------------------------------------------------------------- |
| 자료 유형 | Anthropic 공식 제품 소개                                                                                                                            |
| 확인 내용 | 학생의 reasoning process를 guide하며, 즉시 답을 제공하기보다 질문하고, Socratic questioning을 사용하고, core concepts를 강조하고, study guide·outline template을 제공한다고 설명한다. |
| 설계 참고 | AI가 답안 생성기보다 reasoning guide 역할을 할 수 있다는 제품 방향 참고.                                                                                            |
| 한계    | 효과 증거가 아니라 제품 설계 설명이다.                                                                                                                        |

---

# 10. AWS 자료와 첫 노트 사례에서 얻은 실무 교훈

## 10.1 AWS기초.pdf의 자료 성격

`AWS기초.pdf`는 하나의 균일한 개념 교재가 아니다.

| PDF 내용                              | 성격                 | 적합한 처리                  |
| ----------------------------------- | ------------------ | ----------------------- |
| p.2–12의 클라우드·AWS 입문 개념              | Concept material   | Concept Note 작성 가능      |
| p.13 이후 서비스 설명                      | Concept + bridge   | 범위별 설계 필요               |
| Console screenshot                  | 오래된 UI 자료          | 현재 절차로 직접 복사 금지         |
| `Public Access: 예`, `Anywhere` 허용 등 | 수업 예시 또는 위험 설정     | 현재 권장과 분리 검토            |
| NAT Instance 실습                     | 레거시 가능성이 큰 구성      | Current-vs-Legacy 검토 필요 |
| 명령·접속 화면                            | 사용자가 직접 수행한 증거가 아님 | 실제 Lab Note와 분리         |

## 10.2 첫 AWS Concept Note의 성공점

`클라우드 컴퓨팅과 AWS 입문.md`는 다음 점에서 성공했다.

* PDF 페이지 순서가 아닌 개념 흐름으로 정리했다.
* RAW 질문을 본문 내 오해 교정과 질문 해설로 흡수했다.
* Shared Responsibility Model을 추가해 보안 학습 연결성을 확보했다.
* Callout과 표를 비교·경고·오해 방지 용도로 제한했다.
* 오래된 PDF를 공식 문서로 보정한다는 기준을 명시했다.

## 10.3 첫 AWS Concept Note의 수정 후보

| 항목                                      | 판정                        |
| --------------------------------------- | ------------------------- |
| AWS 기원 설명에서 공식 직접 진술과 해석이 섞임            | 수정 필요                     |
| 비용 warning이 후속 서비스까지 넓어짐                | 밀도 조정 후보                  |
| Public / Private 비교표에 배포·비용 부담이 약하게 반영됨 | 보완 후보                     |
| `tags` 추가 여부                            | AWS 영역 태그 규칙 확정 후 판단      |
| MOC가 노트 작성과 함께 수정됨                      | 결과는 문제없지만 workflow상 분리 권장 |

## 10.4 다음 AWS 노트 작성이 중단된 이유

`p.13–25`는 다음이 섞여 있다.

* EC2와 Region/AZ 개념
* Scale-up / Scale-out
* EC2와 RDS의 기본 관계
* 오래된 EC2/RDS Console 화면
* 현재 기준에서 재검토해야 하는 Free Tier와 Public Access 예시
* 다음 VPC 파트로 넘어가는 연결 페이지

따라서 바로 파일 작성 프롬프트로 넘기면, concept note와 오래된 절차 설명과 위험 설정 검토가 다시 섞일 가능성이 있다.

현재 판정:

```text
AWS 다음 노트 작성은 보류한다.
실제 수업에서 RAW와 Revision Bridge를 먼저 시험한 뒤 작성 workflow를 다시 적용한다.
```

## 10.5 External Snapshot Observation: Codex Local AWS Workspace

상태:

- Codex 로컬 workspace snapshot에서 직접 확인한 관찰이다.
- GPT가 확인한 업로드 snapshot의 현재 상태를 덮어쓰지 않는다.
- 이 관찰만으로 과거 서술을 조용히 수정하지 않는다.

Codex 로컬 workspace snapshot에서는 다음이 확인됐다.

- `10_학습 노트/클라우드/AWS/실습 노트/EC2와 RDS 기본 구성 실습.md`가 존재하고 Git에 추적되어 있다.
- `10_학습 노트/클라우드/AWS/00_AWS_목차.md`의 `## 실습 기록`에는 여전히 `아직 작성된 노트 없음`이라고 적혀 있다.
- 추가 검증:
  - Codex는 로컬 Git index에서 동일한 불일치를 독립 확인했다.
  - GPT는 `2026-06-01`에 검토한 GitHub 추적 snapshot에서도 동일한 불일치를 확인했다고 보고했다.

정리 후보:

- 동일한 저장소 snapshot을 기준으로 AWS MOC 설명과 실제 추적된 실습 노트 상태를 나중에 맞춘다.

---

# 11. 현재 채택 원칙

## 11.0 결정 유형

연구가 지지하는 제약과 이 vault에서 선택한 운영 규칙, 아직 시험해야 할 설계 후보를 구분한다.

| 결정 유형 | 의미 |
| --- | --- |
| 근거 기반 제약 | 연구가 학습상의 제약이나 위험을 지지함. 정확한 vault 구현 방식은 별도 판단 |
| 현재 vault 운영 규칙 | 이 vault에서 이미 선택한 정리 방식. 보편적 최적해라고 주장하지 않음 |
| 후보 운영 규칙 | 사용자 승인, dry-run 또는 반복 이득 확인 후 채택할 수 있음 |
| 기각할 보편 규칙 | 근거가 부족하거나 관리 비용이 커서 모든 작업에 강제하지 않음 |

### Canonical 분류표

| 원칙 | 결정 유형 | 현재 상태 |
| --- | --- | --- |
| 실시간 포착과 최종 작성 분리 | 근거 기반 제약 | 유지 |
| RAW 증거 보존 | 현재 vault 운영 규칙 | 유지 |
| Concept Note와 Lab Note 분리 | 현재 vault 운영 규칙 | 유지 |
| MOC를 얇은 탐색 계층으로 유지 | 현재 vault 운영 규칙 | 유지 |
| Review Activity를 작성과 분리 | 후보 운영 규칙 | 테스트 필요 |
| Routing Gate | 후보 운영 규칙 | 테스트 필요 |
| `Revision Bridge` | 후보 운영 규칙 | dry-run 필요 |
| `AI Assistance Boundary` | 후보 운영 규칙 | dry-run 필요 |
| 모든 노트에 Canvas, Mermaid, 회상 질문, atomic split 강제 | 기각할 보편 규칙 | 기각 |

## 11.1 강하게 채택

| 원칙                                       | 근거                                          | skill 반영 여부        |
| ---------------------------------------- | ------------------------------------------- | ------------------ |
| Live Capture와 최종 Authoring은 분리한다         | 필기/review 연구 + 실제 실패                        | 일부 반영, 강화 후보       |
| PDF는 범위 기준점이며 최종 heading 구조가 아니다         | 실제 노트 품질 + current skill                    | 반영됨                |
| RAW는 질문·강사 표현·실제 증거를 보존한다                | 실제 workflow + AI 연구 방향                      | 반영됨                |
| Concept Note는 하나의 learning spine 중심으로 쓴다 | current skill + generative learning 방향      | 반영됨                |
| Lab Note는 실제 수행 증거가 있을 때만 쓴다             | 정확성 원칙 + current skill                      | 반영됨                |
| 공식 문서는 PDF의 부정확성·오래된 정보 보정용이다            | AWS 사례                                      | 반영됨                |
| Callout·표·Mermaid·이미지는 이해를 개선할 때만 쓴다     | multimedia/visualization 근거 + current skill | 반영됨                |
| MOC는 안정화된 note의 탐색 경로로 얇게 유지한다           | vault 구조 + PKM 설계                           | 반영됨                |
| 완성 노트와 retrieval/review 활동은 분리한다         | Dunlosky/Cepeda/관련 연구                       | 아직 workflow 명문화 미완 |
| 디지털 노트 자체를 낮게 평가하지 않는다                   | Morehead/Luo                                | 운영 판단으로 채택         |
| Atomic note를 교리처럼 강제하지 않는다               | Matuschak + 실제 workflow                     | 운영 판단으로 채택         |

## 11.2 유망하지만 실제 시험 후 반영

| 원칙 후보                            | 근거                                     | 시험 방법                       |
| -------------------------------- | -------------------------------------- | --------------------------- |
| `Revision Bridge` 단계 추가          | Luo et al., 2016                       | 다음 실제 수업 직후 5분 보강 기록 실행     |
| `AI Assistance Boundary` 명시      | NoTeeline, Chen et al., Lehmann et al. | AI가 RAW 없이 자동 확장하는지 dry-run |
| 안정화된 Concept Note에 회상 질문 2–5개 추가 | retrieval/spacing 연구                   | 작성 단계가 아닌 Review 단계에서 시험    |
| 관계 중심 AWS 노트에 labeled Mermaid 사용 | concept map 연구 + Fiorella              | VPC 실습 노트에서 시험              |
| 작성 완료 후 별도 MOC routing gate      | 실제 scope creep 문제                      | note 작성과 MOC 수정 요청을 분리하여 시험 |

## 11.3 보류

| 제안                                                    | 이유                            |
| ----------------------------------------------------- | ----------------------------- |
| 현재 skill을 즉시 phase router 구조로 재작성                     | 기존 개선 규칙의 효과를 아직 시험하지 않음      |
| 모든 Concept Note에 확인 질문을 강제                            | authoring과 review가 다시 섞일 수 있음 |
| Canvas를 AWS 아키텍처 노트의 기본 기능으로 채택                       | 실제 이득 미검증                     |
| Progressive Summarization을 최종 Concept Note 작성 규칙으로 채택 | source 관리와 설명 작성은 다름          |
| 자동으로 tag 체계를 확장                                       | AWS 영역의 실제 검색·운영 요구 미확인       |

## 11.4 기각

| 제안                                   | 기각 이유                    |
| ------------------------------------ | ------------------------ |
| AI가 PDF만 받고 노트 분할·본문·MOC를 전부 자동 생성   | 사용자의 질문·관찰·학습 참여를 지울 위험  |
| 모든 노트를 atomic file로 분리               | 연결망 파편화와 관리 비용           |
| 모든 노트에 Mermaid·표·callout을 넣음         | 장식과 정보 과잉                |
| 손필기만 학습에 적합하다고 단정                    | 후속 연구가 단순 우위를 지지하지 않음    |
| 제품 소개를 학습 효과 증거로 취급                  | 설계 설명과 효과 검증은 다름         |
| 오래된 Console screenshot을 현재 실습 절차로 복사 | AWS UI·가격·보안 권장이 바뀔 수 있음 |
| 작성 중 MOC를 자동으로 개편                    | scope creep 재발 위험        |

---

# 12. 후보 Workflow

## 12.1 현재 가장 타당한 단계 구조

| 단계                 | 목적              | 사용자 역할             | AI 역할                              | 허용 결과물                      | 금지                 |
| ------------------ | --------------- | ------------------ | ---------------------------------- | --------------------------- | ------------------ |
| 1. Live Capture    | 수업 중 증거와 질문 보존  | 직접 관찰·기록           | 정리 보조 최소화                          | RAW, 스크린샷, 명령, 값, 오류, 질문    | 완성 노트, MOC, 대규모 조사 |
| 2. Revision Bridge | 당일 의미 보충        | 무엇을 했고 왜 했는지 짧게 설명 | 빠진 항목 질문, 문장 정돈                    | 관찰·이유·미해결 질문·정리 상태          | 구조 개편, 공식 조사, MOC  |
| 3. PDF Map         | 자료의 큰 범위와 경계 파악 | 범위 확인              | 페이지 분석·경계 제안                       | 큰 묶음, 경계 페이지, 레거시 후보        | 파일명·노트 개수 자동 확정    |
| 4. Note Design     | 한 노트의 중심 질문 확정  | 포함·보류 승인           | learning spine, core/bridge/TMI 정리 | 작성 명세                       | 파일 편집              |
| 5. Authoring       | 합의된 노트 작성       | 결과 검토              | 지정 파일만 작성                          | Concept Note 또는 Lab Note 1개 | 주변 파일 확장           |
| 6. Quality Review  | 정확성·범위·학습 흐름 점검 | 수정 승인              | 오류·과잉·누락 지적                        | 패치 목록                       | 새 범위 작성            |
| 7. Review Activity | 기억과 적용 확인       | 직접 답변·설명           | 질문·피드백 제공                          | 회상 질문, 적용 문제                | 본문 무단 재작성          |
| 8. Routing         | 탐색 경로 연결        | 링크 승인              | 최소 MOC 편집                          | MOC link 추가                 | 목차 전면 재설계          |

## 12.2 아직 확정하지 않은 점

* `Revision Bridge`를 반드시 모든 수업에서 할지
* Review Activity를 Obsidian note 안에 넣을지, 별도 note/Anki 등으로 분리할지
* Codex skill 파일을 phase별 reference로 실제 분리할지
* AI가 Live Capture 단계에서 질문을 적극적으로 할지, 최소 개입만 할지

---

# 13. Dry-run 테스트 설계

현재 skill을 다시 뜯기 전에 아래 테스트로 실제 실패 여부를 확인한다.

## Test 1. Live Capture 경계

### 입력

```text
오늘 AWS 수업 중 찍은 Console 캡처와 짧은 메모가 있다. 정리 도와줘.
```

### 기대 동작

* RAW를 보존한다.
* 값, 오류, 질문, 관찰을 분류한다.
* 실습 결과가 확인되지 않으면 성공을 쓰지 않는다.
* Concept Note나 MOC를 만들지 않는다.

### 실패 판정

* 즉시 완성 노트를 생성한다.
* 노트 분리와 MOC 수정까지 제안한다.
* 실제 관찰 없이 결과를 추론한다.

---

## Test 2. Revision Bridge

### 입력

```text
방금 수업 끝났다. RAW에서 오늘 실제로 한 것, 왜 한 것 같은지, 막힌 것, 정리 확인만 보충하자.
```

### 기대 동작

* 짧은 보강 질문만 한다.
* 관찰과 해석과 미해결 질문을 나눈다.
* 비용 리소스 정리 상태를 확인한다.
* 최종 노트 작성으로 넘어가지 않는다.

### 실패 판정

* 공식 문서 조사와 완성 note authoring으로 확장한다.
* MOC 수정까지 수행한다.

---

## Test 3. PDF Map

### 입력

```text
이 PDF 범위를 큰 학습 묶음으로 나누고 경계 페이지만 표시해줘. 파일 수정은 하지 마.
```

### 기대 동작

* 큰 범위와 애매한 전환 페이지만 정리한다.
* 오래된 UI·레거시 가능성만 표시한다.
* 파일명이나 실제 note split은 확정하지 않는다.

### 실패 판정

* 자동으로 note 파일명을 대량 추천하고 작성 순서를 고정한다.
* MOC에 바로 쓰려 한다.

---

## Test 4. Concept Note Authoring

### 입력

```text
확정된 learning spine과 포함·보류 범위대로 지정 파일 하나만 작성해줘.
```

### 기대 동작

* 지정 파일만 작성한다.
* PDF/RAW/공식 문서 역할을 분리한다.
* 공식 검증 목록이 heading을 점령하지 않는다.
* 실제 실습 결과를 만들지 않는다.

### 실패 판정

* 주변 주제를 확대한다.
* MOC나 RAW를 임의 수정한다.
* 모든 보정 항목을 동급 heading으로 확장한다.

---

## Test 5. Lab Reconstruction

### 입력

```text
실제 VPC 실습 RAW와 결과 화면이 있다. 결과 중심으로 재구성해줘.
```

### 기대 동작

* 실제 결과와 증거를 상단에 둔다.
* 설정 목적과 트래픽 흐름을 설명한다.
* 오류와 혼동을 debugging/evidence로 보존한다.
* PDF 이론을 과도하게 복사하지 않는다.

### 실패 판정

* 실제 결과 없이 성공을 단정한다.
* 실습보다 이론 노트를 새로 작성한다.

---

## Test 6. Review Activity

### 입력

```text
이 노트 복습용으로 내가 직접 답할 질문을 만들어줘. 본문은 수정하지 마.
```

### 기대 동작

* learning spine 중심 질문 2–5개를 만든다.
* 적용 또는 설명 질문을 포함할 수 있다.
* 본문 파일은 수정하지 않는다.

### 실패 판정

* 노트를 다시 작성한다.
* 문제집 수준으로 과도하게 확장한다.

---

## Test 7. MOC Routing

### 입력

```text
검토 완료된 새 노트를 AWS 목차에 연결해줘. 최소 수정만 해.
```

### 기대 동작

* 실제 존재하는 note link만 추가한다.
* 기존 구조를 필요 이상으로 다시 쓰지 않는다.
* placeholder link를 만들지 않는다.

### 실패 판정

* 학습 지도·정리 대기·전체 목차까지 재설계한다.
* 아직 없는 노트를 대량으로 링크한다.

---

# 14. Skill 개편 판단 기준

## 14.1 바로 수정하지 않는 이유

현재 skill에는 이미 상당한 개선이 들어가 있다. 지금 즉시 다시 쪼개면 다음을 알 수 없다.

* 현 규칙이 실제로 실패하는지
* 실패가 rule 부족인지, 프롬프트 범위 과다인지
* phase 분리가 필요한지, 단순한 금지 문장 하나면 충분한지
* 토큰 절감과 품질 개선이 실제로 생기는지

## 14.2 개편을 시작해도 되는 조건

아래 중 하나가 실제 dry-run 또는 실수에서 반복적으로 나타날 때만 수정한다.

| 반복 실패                                  | 개편 후보                                 |
| -------------------------------------- | ------------------------------------- |
| RAW 요청인데 AI가 계속 완성 노트로 확장함             | `live-capture.md` 분리 또는 phase rule 강화 |
| PDF Map 요청인데 파일명/본문까지 확정함              | `pdf-structure-map.md` 분리             |
| Concept Note가 계속 검증 checklist 형태로 변함   | `concept-note-authoring.md` 보강        |
| Lab Note가 실제 evidence보다 이론 중심으로 흐름     | `lab-reconstruction.md` 강화            |
| 작성과 MOC 갱신이 반복적으로 섞임                   | Routing gate 명시                       |
| skill description/참조가 너무 길어 컨텍스트 비용이 큼 | thin router 구조 검토                     |

---

# 15. 남아 있는 조사 과제

## 15.1 아직 충분히 조사하지 못한 것

| 영역                         | 현재 상태          | 필요 시 조사할 질문                                                                            |
| -------------------------- | -------------- | -------------------------------------------------------------------------------------- |
| 보안·클라우드 실습 교육 특화 연구        | 미조사            | configuration lab, cybersecurity lab reflection, troubleshooting notebook에 특화된 구조가 있는가 |
| Obsidian 학생 사용자 커뮤니티 사례    | 부분 미확보         | 실제 학생·기술 학습자는 RAW, MOC, Canvas, flashcard를 어떻게 운영하는가                                   |
| Spaced repetition 연동       | 미결정            | Obsidian 안에서 할지, Anki 등 별도 시스템으로 보낼지                                                   |
| Canvas / Excalidraw 실사용 효과 | 미검증            | AWS 네트워크 구성에서 실제로 reread/review에 도움이 되는가                                               |
| Revision Bridge 실제 효용      | 연구 근거는 있으나 미실험 | 네 수업 직후 수행 가능하고 노트 품질에 도움이 되는가                                                         |
| AI 자동화 경계                  | 최근 연구 기반 후보    | 실제 네 workflow에서 어느 수준이 가장 편하고 학습에도 유리한가                                                |

## 15.2 추가 조사를 바로 하지 않는 이유

현재 핵심 workflow를 결정할 근거는 충분히 확보했다. 이후 조사는 실제 실패나 필요가 생긴 지점에 한정하는 편이 낫다.

```text
문헌 추가
→ 규칙 추가
→ skill 비대화
```

가 되지 않도록, 앞으로의 조사는 다음 조건 중 하나가 있을 때만 수행한다.

* 실제 AWS 수업에서 새로운 문제 발생
* dry-run에서 반복 실패 확인
* 안전·비용·보안 정확성 문제가 발생
* 복습 시스템을 실제로 도입하기로 결정
* Canvas, Anki, Dataview 등 특정 도구 사용 여부를 판단해야 함

---

# 16. 최종 운영 원칙

## 16.1 AI의 역할

AI는 다음을 한다.

* 사용자가 포착한 RAW를 정돈한다.
* PDF의 범위와 경계를 분석한다.
* 공식 문서로 오래되거나 부정확한 표현을 보정한다.
* 합의된 learning spine에 따라 지정 파일을 작성한다.
* 노트의 범위 초과, 사실 오류, 과잉 장식을 비판적으로 검토한다.
* 복습 단계에서 질문과 피드백을 제공할 수 있다.
* 안정화된 노트를 MOC에 최소 변경으로 연결할 수 있다.

AI는 기본적으로 다음을 하지 않는다.

* 사용자의 질문과 관찰을 대신 만들어낸다.
* 실제 수행하지 않은 실습 결과를 적는다.
* RAW 요청을 곧바로 완성 노트 작성으로 확대한다.
* Note Design과 Authoring과 Routing을 한 요청에서 임의로 합친다.
* PDF만 보고 모든 note split과 MOC 구조를 자동 확정한다.
* 복습 질문을 붙였다는 이유로 학습이 완료됐다고 취급한다.

## 16.2 사용자의 역할

사용자는 다음을 유지한다.

* 수업 중 실제 관찰, 질문, 오류, 설정값, 화면을 포착한다.
* AI가 보정한 설명이 자신의 질문과 맞는지 검토한다.
* 실습 결과가 무엇을 의미하는지 최종 승인한다.
* 안정화된 노트를 읽은 뒤 직접 설명하거나 적용하거나 회상한다.
* skill 개편 여부와 vault 구조 변경을 승인한다.

## 16.3 노트 유형별 목적

| 노트 유형             | 목적           | 핵심 내용                                |
| ----------------- | ------------ | ------------------------------------ |
| RAW Memo          | 학습 현장의 원본 보존 | 질문, 명령, 값, 캡처, 오류, 강사 표현             |
| Revision Bridge   | 수업 직후 의미 보강  | 무엇을 했는지, 왜 했는지, 막힌 것, 정리 상태          |
| PDF Structure Map | 범위와 경계 확인    | 큰 묶음, 전환 페이지, 레거시 후보                 |
| Concept Note      | 독립적인 이해 자료   | learning spine, mental model, 경계, 보정 |
| Lab Note          | 실제 수행 증거 보존  | 결과, 증거, 구성, 절차, 실패, 검증               |
| Review Artifact   | 회상과 적용       | 질문, 적용 문제, 피드백                       |
| MOC               | 재탐색과 재시작     | 안정화된 노트 링크와 최소 상태 정보                 |

---

# 17. 현재 결론

## 확정된 결론

1. AWS 노트 작성 중단 판단은 적절했다.
2. 현재 문제는 노트를 못 쓰는 것이 아니라, 서로 다른 학습 단계를 한꺼번에 처리하려 한 데 있다.
3. 현재 skill에는 이미 상당히 좋은 원칙이 들어가 있으므로 즉시 대개편할 필요는 없다.
4. AI는 사용자의 RAW·질문·실습 증거를 확장하고 검증하는 역할에 두는 것이 가장 타당하다.
5. AI가 완성 노트와 MOC를 자동으로 확장하는 방식은 기본값으로 두지 않는다.
6. 다음 실제 수업에서는 `Live Capture → Revision Bridge`까지만 먼저 시험하는 것이 가장 가치 있다.
7. 그 결과를 본 뒤에야 skill 개편, AWS 다음 노트 작성, 복습 시스템 도입을 판단한다.

## 아직 확정하지 않은 결론

1. `Revision Bridge`를 skill의 공식 phase로 넣을지.
2. `AI Assistance Boundary`를 어느 파일에 어떤 강도로 명시할지.
3. skill을 thin router + phase별 reference 구조로 분리할지.
4. Concept Note에 회상 질문을 넣을지 별도 Review Note로 둘지.
5. Canvas, Anki, Dataview 등을 실제 AWS 학습 workflow에 넣을지.

---

# 18. Source Register

## 18.1 학습 과학·필기·복습

| 자료                                                                                                                | 상태                   | 식별자                                           |
| ----------------------------------------------------------------------------------------------------------------- | -------------------- | --------------------------------------------- |
| Kobayashi, 2006, Combined Effects of Note-Taking/-Reviewing on Learning and the Enhancement through Interventions | Abstract 확인          | ERIC EJ722157 / DOI 10.1080/01443410500342070 |
| Dunlosky et al., 2013, Improving Students’ Learning With Effective Learning Techniques                            | Abstract·핵심 권고 확인    | DOI 10.1177/1529100612453266                  |
| Cepeda et al., 2006, Distributed Practice in Verbal Recall Tasks                                                  | 원문 PDF 핵심 summary 확인 | DOI 10.1037/0033-2909.132.3.354               |
| Roediger & Karpicke, 2006, Test-Enhanced Learning                                                                 | 이번 문서에서 원문 재확인 제한    | DOI 10.1111/j.1467-9280.2006.01693.x          |
| Chi et al., 1989, Self-Explanations                                                                               | 이번 문서에서 원문 재확인 제한    | 기존 self-explanation 연구                        |
| Piolat, Olive & Kellogg, 2005, Cognitive Effort During Note Taking                                                | 서지 확인, 본문 재확인 필요     | DOI 10.1002/acp.1086                          |
| Luo, Kiewra & Samuelson, 2016, Revising Lecture Notes                                                             | Abstract 확인          | DOI 10.1007/s11251-016-9370-4                 |
| Morehead, Dunlosky & Rawson, 2019, How Much Mightier Is the Pen than the Keyboard                                 | Abstract 확인          | DOI 10.1007/s10648-019-09468-2                |
| Luo et al., 2018, Laptop versus Longhand Note Taking                                                              | Abstract 확인          | DOI 10.1007/s11251-018-9458-0                 |
| Flanigan et al., 2024, Typed Versus Handwritten Lecture Notes and College Student Achievement                     | 출판사 초록 확인       | DOI 10.1007/s10648-024-09914-w                |

## 18.2 이해·시각화·초심자 설계

| 자료                                                                        | 상태          | 식별자                               |
| ------------------------------------------------------------------------- | ----------- | --------------------------------- |
| Fiorella, 2023, Making Sense of Generative Learning                       | 본문 핵심 확인    | DOI 10.1007/s10648-023-09769-7    |
| Renkl, 2002, Worked-out Examples                                          | 본문 재확인 필요   | DOI 10.1016/S0959-4752(01)00030-5 |
| Kalyuga, 2007, Expertise Reversal Effect                                  | Abstract 확인 | DOI 10.1007/s10648-007-9054-3     |
| Mayer & Pilegard, 2014, Segmenting, Pre-training, and Modality Principles | Summary 확인  | DOI 10.1017/CBO9781139547369.016  |
| Nesbit & Adesope, 2006, Learning With Concept and Knowledge Maps          | Abstract 확인 | DOI 10.3102/00346543076003413     |

## 18.3 AI 보조 학습·노트 작성

| 자료                                                           | 상태                      | 식별자                                                    |
| ------------------------------------------------------------ | ----------------------- | ------------------------------------------------------ |
| Huq et al., NoTeeline                                        | Abstract·게시 상태 확인       | arXiv:2409.16493 / related DOI 10.1145/3708359.3712086 |
| Chen et al., More AI Assistance Reduces Cognitive Engagement | Abstract·accepted 표기 확인 | arXiv:2509.03392 / related DOI 10.1145/3757632         |
| Lehmann et al., AI Meets the Classroom                       | Abstract 확인             | arXiv:2409.09047                                       |
| OpenAI, ChatGPT Study Mode                                   | 공식 제품 설명 확인             | OpenAI product page, 2025-07-29                        |
| Google, NotebookLM                                           | 공식 도움말 확인               | NotebookLM Help                                        |
| Google, Gemini Guided Learning                               | 공식 도움말 확인               | Gemini Apps Help                                       |
| Anthropic, Claude for Education / Learning Mode              | 공식 제품 설명 확인             | Anthropic News, 2025-04-02                             |

## 18.4 PKM·Obsidian 운영 참고

| 자료                                                         | 상태       | 식별자                                    |
| ---------------------------------------------------------- | -------- | -------------------------------------- |
| Andy Matuschak, Evergreen notes should be atomic           | 원문 확인    | Working notes                          |
| Andy Matuschak, Evergreen notes should be concept-oriented | 원문 확인    | Working notes                          |
| Tiago Forte, Progressive Summarization                     | 원문 확인    | Forte Labs article, updated 2023-05-16 |
| Obsidian Help, Callouts                                    | 공식 문서 확인 | Obsidian Help                          |
| Obsidian Help, Internal Links                              | 공식 문서 확인 | Obsidian Help                          |
| Obsidian Help, Properties                                  | 공식 문서 확인 | Obsidian Help                          |
| Obsidian Help, Canvas                                      | 공식 문서 확인 | Obsidian Help                          |

## 18.5 Low-Confidence Operational References

다음 자료는 실무 workflow 예시로만 보존한다. 학습 과학 증거나 보편 설계 규칙으로 승격하지 않는다.

### OSCP Notes Template

- 출처: [Twigonometry/OSCP-Notes-Template](https://github.com/Twigonometry/OSCP-Notes-Template)
- 검증 상태: 공개 저장소 문서 확인
- 보존할 운영 패턴:
  - 문제 해결 중 포착과 사후 정리를 분리할 수 있다.
  - 개념·도구 중심의 짧은 노트와 서술형 lab writeup이 공존할 수 있다.
  - 관계가 복잡한 자료에서는 조건부로 Canvas 형태의 표현을 고려할 수 있다.
- 해석 경계: 공개된 사이버보안 학습 workflow 예시이며, 이 vault에서 동일 구조가 더 높은 학습 성과를 만든다는 실증 근거는 아니다.

### Obsidian Forum Discussion on MOCs

- 출처: [How do you decide what's a MOC?](https://forum.obsidian.md/t/how-do-you-decide-whats-a-moc/37539)
- 검증 상태: 커뮤니티 논의 확인
- 보존할 운영 패턴:
  - MOC 사용은 맥락 의존적이다.
  - 계층형 탐색이 유용하다는 사용자도 있고, MOC가 과도한 조직화라고 보는 사용자도 있다.
  - 커뮤니티 사용기만으로 MOC를 전역 강제하면 안 된다.
- 해석 경계: 이 vault의 얇은 MOC는 로컬 라우팅 규칙으로 유지하며 보편 최적해라고 주장하지 않는다.

---

# 19. 다음 행동

지금 즉시 할 일은 AWS 노트 작성이나 skill 수정이 아니다.

## 다음 실제 수업 전

* 현재 skill은 그대로 둔다.
* 이 문서를 Codex에도 공유해 판단 기준을 고정한다.
* RAW 작성 방식과 Revision Bridge 시험용 최소 질문만 준비한다.

## 다음 실제 수업 중

```text
- 실제 생성한 리소스
- 실제 설정값
- 실제 성공/실패 화면
- 실제 오류
- 이해되지 않은 질문
- 종료·삭제·비용 확인 상태
```

만 RAW에 남긴다.

## 수업 직후 시험할 것

```text
오늘 실제 한 것:
왜 한 것 같은지:
확인된 결과:
막힌 점:
아직 모르는 점:
비용·리소스 정리 상태:
```

를 5분 내에 보충한다.

## 그다음 판단

* Revision Bridge가 실제로 유용했는지 평가한다.
* AI가 phase 경계를 지켰는지 본다.
* 반복 실패가 있으면 그때 skill 수정 범위를 결정한다.
* 노트 작성은 그 이후에만 재개한다.

---

# 최종 한 문장

AI가 만들어야 하는 것은 사용자를 대신한 완성 학습물이 아니라, 사용자가 실제로 포착하고 이해하고 다시 꺼내 쓸 수 있는 학습 흔적을 정확하게 보존·보정·연결하는 시스템이다.

## 검증 메모

이 문서는 **연구 대장 초안**으로 사용할 수 있는 수준으로 정리했다. 다만 다음 자료는 원문 전체의 세부 결과까지 재독한 상태가 아니라, 현재 문서 안에서도 그 제한을 표시해두었다.

* `Piolat et al., 2005`
* `Roediger & Karpicke, 2006`
* `Chi et al., 1989`
* `Renkl, 2002`

따라서 Codex에 넘길 때는 이 문서를 **skill 즉시 개편 명령서**가 아니라, `채택된 원칙 / 테스트할 후보 / 아직 원문 확인이 부족한 자료`를 분리한 연구 기준 문서로 취급하는 게 맞다.

[1]: https://eric.ed.gov/?id=EJ722157 "ERIC - EJ722157 - Combined Effects of Note-Taking/-Reviewing on Learning and the Enhancement through Interventions: A Meta-Analytic Review, Educational Psychology, 2006-Jun"
[2]: https://journals.sagepub.com/doi/10.1177/1529100612453266 "Improving Students’ Learning With Effective Learning Techniques - John Dunlosky, Katherine A. Rawson, Elizabeth J. Marsh, Mitchell J. Nathan, Daniel T. Willingham, 2013 "
[3]: https://doi.org/10.1007/s11251-016-9370-4 "Revising lecture notes: how revision, pauses, and partners affect note taking and achievement | Instructional Science"
[4]: https://doi.org/10.1007/s10648-019-09468-2 "How Much Mightier Is the Pen than the Keyboard for Note-Taking? A Replication and Extension of Mueller and Oppenheimer (2014) | Educational Psychology Review | Springer Nature Link"
[5]: https://doi.org/10.1007/s11251-018-9458-0 "Laptop versus longhand note taking: effects on lecture notes and achievement | Instructional Science | Springer Nature Link"
[6]: https://doi.org/10.3102/00346543076003413 "Learning With Concept and Knowledge Maps: A Meta-Analysis - John C. Nesbit, Olusola O. Adesope, 2006 "
[7]: https://link.springer.com/article/10.1007/s10648-023-09769-7 "Making Sense of Generative Learning | Educational Psychology Review | Springer Nature Link"
[8]: https://doi.org/10.1007/s10648-007-9054-3 "Expertise Reversal Effect and Its Implications for Learner-Tailored Instruction | Educational Psychology Review"
[9]: https://www.cambridge.org/core/books/abs/cambridge-handbook-of-multimedia-learning/principles-for-managing-essential-processing-in-multimedia-learning-segmenting-pretraining-and-modality-principles/DD24C2F48B9B1277CE59F78276110258 "Principles for Managing Essential Processing in Multimedia Learning: Segmenting, Pre-training, and Modality Principles (Chapter 13) - The Cambridge Handbook of Multimedia Learning"
[10]: https://arxiv.org/abs/2409.16493 "[2409.16493] NoTeeline: Supporting Real-Time, Personalized Notetaking with LLM-Enhanced Micronotes"
[11]: https://arxiv.org/abs/2509.03392 "[2509.03392] More AI Assistance Reduces Cognitive Engagement: Examining the AI Assistance Dilemma in AI-Supported Note-Taking"
[12]: https://arxiv.org/abs/2409.09047 "[2409.09047] AI Meets the Classroom: When Do Large Language Models Harm Learning?"
[13]: https://support.google.com/notebooklm/answer/16164461?hl=en "Learn about NotebookLM - Computer - NotebookLM Help"
[14]: https://support.google.com/notebooklm/answer/16206563?hl=en "Create a notebook in NotebookLM - NotebookLM Help"
[15]: https://openai.com/index/chatgpt-study-mode/ "Introducing study mode | OpenAI"
[16]: https://support.google.com/gemini/answer/16448384 "Use learning tools in Gemini Apps - Computer - Gemini Apps Help"
[17]: https://www.anthropic.com/news/introducing-claude-for-education "Introducing Claude for education \ Anthropic"
[18]: https://notes.andymatuschak.org/Evergreen_notes_should_be_atomic "Evergreen notes should be atomic"
[19]: https://notes.andymatuschak.org/Evergreen_notes_should_be_concept-oriented "Evergreen notes should be concept-oriented"
[20]: https://fortelabs.com/blog/progressive-summarization-a-practical-technique-for-designing-discoverable-notes/ "Progressive Summarization: A Practical Technique for Designing Discoverable Notes - Forte Labs"
[21]: https://help.obsidian.md/callouts "Callouts - Obsidian Help"
[22]: https://help.obsidian.md/links "Internal links - Obsidian Help"
[23]: https://help.obsidian.md/properties "Properties - Obsidian Help"
[24]: https://help.obsidian.md/plugins/canvas "Canvas - Obsidian Help"
