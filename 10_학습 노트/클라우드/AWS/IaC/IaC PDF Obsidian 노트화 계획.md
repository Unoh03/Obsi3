---
title: IaC PDF Obsidian 노트화 계획
created: 2026-07-06
status: active
type: workflow-note
source_pdf: Iac.pdf
purpose: ChatGPT/Codex가 맥락을 잃었을 때 IaC PDF 노트화 작업을 복구하기 위한 기준 노트
tags:
  - 과목/AWS
  - 주제/IaC
  - 주제/Terraform
  - 상태/active
---
# IaC PDF Obsidian 노트화 계획

## 0. 이 노트의 목적

이 노트는 `Iac.pdf`를 Obsidian 학습 노트로 전환하기 위한 **작업 기준서**다.

목적은 세 가지다.

1. PDF 내용을 반복해서 다시 읽지 않기 위한 텍스트화
2. Source Digest → Concept Note → MOC로 이어지는 안정적인 노트화
3. ChatGPT/Codex가 맥락을 잃었을 때 이 노트만 보고 작업을 재개할 수 있게 하기

---

## 1. 현재 기준 자료

| 항목 | 내용 |
|---|---|
| 대상 PDF | `Iac.pdf` |
| 주제 | Infrastructure as Code / Terraform |
| 분량 | 52쪽 |
| 성격 | IaC 개론 + Terraform 실습 중심 강의자료 |
| 우선 산출물 | `IaC - Source Digest.md` |
| Lab Note | 기본 생성하지 않음. 실제 명령어 실습이 필요한 부분만 선택 생성 |

---

## 2. 출처 분류 규칙

앞으로 이 프로젝트에서 정보 출처는 반드시 아래 네 가지로 구분한다.

| 분류 | 의미 | 사용 방식 |
|---|---|---|
| **내장 지식** | ChatGPT가 학습 과정에서 이미 알고 있는 일반 지식, 개념, 추론 | PDF 내용을 설명하기 위한 보조 설명에 사용 |
| **인터넷 고신뢰 정보** | 공식 문서, 표준, 논문, 벤더 문서, 보안 가이드, 전문가 자료 | Terraform/AWS 최신 동작, 명령어, 보안 기준 검증에 사용 |
| **인터넷 비공식 고품질 의견** | 공식은 아니지만 수준 높은 실무자 블로그, 커뮤니티, GitHub issue, 유저 경험 | 실무 관행, 함정, 트러블슈팅 참고에 사용 |
| **PDF** | 업로드된 강의 자료, KISA 가이드, 프로젝트 안내서 등 | Source Digest와 Concept Note의 1차 근거 |

### 원칙

- PDF에 없는 내용은 PDF 내용처럼 쓰지 않는다.
- 보충 설명은 `[내장 지식]`, `[인터넷 고신뢰 정보]`, `[인터넷 비공식 고품질 의견]`, `[해석]`, `[확인 필요]`로 구분한다.
- Terraform/AWS처럼 변경 가능성이 있는 내용은 가능한 한 공식 문서로 재검증한다.
- 강의자료의 오타는 원문을 존중하되, 실제 명령어가 다르면 `확인 필요` 또는 `정정`으로 표시한다.

---

## 3. 노트화 기본 구조

PDF를 바로 Concept Note로 만들지 않는다. 아래 3층 구조를 따른다.

```text
PDF 원문
→ Source Digest
→ Concept Note
→ MOC / 프로젝트 연결 노트
```

### 각 계층의 역할

| 계층 | 역할 | 작성 원칙 |
|---|---|---|
| **Source Digest** | PDF를 다시 열지 않아도 되게 만드는 원문 기반 압축본 | PDF 구조와 페이지 흐름 보존 |
| **Concept Note** | 학습 가능한 독립 개념 노트 | Source Digest에서 추출한 개념을 재구성 |
| **Lab Note** | 실제 실습·명령어·검증 절차 기록 | 필요한 경우에만 생성 |
| **MOC** | 관련 노트들을 탐색 가능하게 연결 | 설명 중복 없이 링크 중심 |

---

## 4. `Iac.pdf`의 큰 흐름

현재 정독 기준으로 `Iac.pdf`는 다음 흐름으로 구성된다.

```text
IaC 개념
→ IaC 구현 도구 분류
→ IaC 장점
→ Terraform 개요
→ Terraform Workflow
→ Resource / Data Source
→ Variable / Output
→ count / for_each / 조건문
→ Module
→ Backend / Remote State
→ 외부 Module + Local Module 실습
```

### 페이지 구간 초안

| 구간 | 주제 | 노트화 방향 |
|---:|---|---|
| p.1 | 표지 | Source Digest에만 반영 |
| p.2~5 | IaC 정의, 도구 범주, 장점 | `IaC 개념`, `IaC 도구 분류` 후보 |
| p.6~11 | Terraform 개요, 선언적 언어, Workflow, `main.tf`, `terraform init` | `Terraform 개요`, `Terraform Workflow` 후보 |
| p.12~28 | Resource, EC2 생성·수정·삭제, Security Group 참조, Data Source | `Terraform Resource와 Data Source` 후보 |
| p.29~37 | Variable Input / Output, VPC·ALB·ASG 예제 | `Terraform Variable과 Output` 후보 |
| p.38~41 | `count`, `for_each`, 조건문 | `Terraform 반복문과 조건문` 후보 |
| p.42~52 | Module, Registry 외부 모듈, Backend, Remote State, Local/External Module 실습 | `Terraform Module`, `Terraform Backend와 Remote State` 후보 |

---

## 5. 1차 산출물: Source Digest

### 파일명

```text
IaC - Source Digest.md
```

### 목적

`Source Digest`는 요약문이 아니라 **PDF 기반 구조화 텍스트**다.  
PDF를 다시 열지 않아도 다음 작업을 할 수 있을 정도로 페이지별 의미를 보존한다.

### 권장 템플릿

```markdown
# IaC - Source Digest

## Source
- file: Iac.pdf
- type: 강의자료
- pages: 1-52
- topic: Infrastructure as Code / Terraform
- status: digest

## Source Classification
- primary: PDF
- supplement: 내장 지식, 인터넷 고신뢰 정보
- unofficial opinion: 필요 시 별도 표시

## 핵심 흐름
1. IaC 개념
2. IaC 도구 범주
3. Terraform 개요
4. Resource / Data Source
5. Variable / Output
6. 반복문 / 조건문
7. Module
8. Backend / Remote State

---

## Page Digest

### p.1
- 표지: Infrastructure as Code

### p.2
- IaC 정의
- 코드 실행으로 인프라 생성, 배포, 수정, 정리
- 서버, 네트워크, DB, APP, 자동화 테스트 및 배포를 코드로 관리
- DevOps 핵심 요소
- Terraform, Ansible, Kubernetes 등 언급

...

---

## Coverage Map

| Page | 처리 상태 | 노트화 결과 | 확인 필요 |
|---:|---|---|---|
| p.1 | 완료/미완료 | 표지 | 없음 |
| p.2 | 완료/미완료 | IaC 정의 | 없음 |
| ... | ... | ... | ... |
```

---

## 6. 2차 산출물: Concept Note 후보

Source Digest 작성 후 아래 후보를 만든다.

```text
IaC 개념.md
IaC 도구 분류.md
Terraform 개요.md
Terraform Workflow.md
Terraform Resource와 Data Source.md
Terraform Variable과 Output.md
Terraform 반복문과 조건문.md
Terraform Module.md
Terraform Backend와 Remote State.md
AWS 프로젝트에 Terraform 적용하기.md
```

### Concept Note 공통 템플릿

```markdown
---
title: 노트 제목
status: active
type: concept-note
source:
  - Iac.pdf
source_pages:
  - p.xx-p.yy
tags:
  - 과목/AWS
  - 주제/IaC
  - 주제/Terraform
---

# 노트 제목

## 한 줄 정의

## 핵심 개념

## PDF 근거
- source: Iac.pdf
- pages: p.xx-p.yy

## 내장 지식 보충
- PDF에 직접 나오지 않은 일반 개념은 여기에 분리한다.

## 확인 필요
- 공식 문서 대조 필요 항목
- 명령어 오타 가능성
- 현재 Terraform/AWS 동작 변경 가능성

## 관련 노트
- 아직 실제 파일이 없으면 wiki link를 만들지 않는다.
```

---

## 7. Lab Note 생성 기준

Lab Note는 기본 생성하지 않는다.  
다음 조건을 만족할 때만 만든다.

### 생성 대상

- 실제 명령어 실행 절차가 있는 경우
- Terraform으로 AWS 리소스를 생성/수정/삭제하는 경우
- 검증 화면이나 에러 대응이 필요한 경우
- 프로젝트 보고서 증적과 연결될 가능성이 있는 경우

### 후보 Lab Note

```text
Terraform 설치와 초기화 실습.md
Terraform으로 EC2 생성 실습.md
Terraform Security Group 참조 실습.md
Terraform Data Source 실습.md
Terraform Variable과 Output 실습.md
Terraform Module 실습.md
Terraform Backend와 Remote State 실습.md
```

### Lab Note 템플릿

```markdown
# 실습 제목

## 목표

## 사용 개념

## 환경

## 절차

## 예상 결과

## 검증 방법

## 실패 시 확인할 항목

## 롤백

## Source
- Iac.pdf p.xx-p.yy
```

---

## 8. MOC 구성

### 파일명 후보

```text
IaC MOC.md
```

### 목적

`IaC MOC`는 설명 노트가 아니라 탐색 노트다.  
중복 설명을 최소화하고, Source Digest / Concept Note / Lab Note를 연결한다.

### MOC 초안

```markdown
# IaC MOC

## Source
- IaC - Source Digest

## Core Concepts
- IaC 개념
- IaC 도구 분류

## Terraform Basics
- Terraform 개요
- Terraform Workflow
- Terraform Resource와 Data Source
- Terraform Variable과 Output

## Terraform Advanced
- Terraform 반복문과 조건문
- Terraform Module
- Terraform Backend와 Remote State

## Lab Notes
- Terraform 설치와 초기화 실습
- Terraform으로 EC2 생성 실습
- Terraform Module 실습
- Terraform Backend와 Remote State 실습

## Project Application
- AWS 프로젝트에 Terraform 적용하기
```

### 링크 정책

- 실제 노트가 존재하기 전에는 `[[wiki link]]`를 만들지 않는다.
- 파일 존재 확인 후에만 wiki link로 바꾼다.
- 이름 충돌 가능성이 있으면 경로 기반 wiki link를 사용한다.

---

## 9. 작업 체크리스트

### A. 시작 전

- [ ] `Iac.pdf`가 현재 작업 대상인지 확인
- [ ] PDF 총 페이지 수 52쪽 확인
- [ ] 목표가 Source Digest인지, Concept Note인지, Lab Note인지 확인
- [ ] PDF 외부 정보 사용 여부 결정
- [ ] 출처 분류 규칙 확인
- [ ] 없는 노트에 wiki link를 만들지 않기로 확인

### B. Source Digest 작성

- [ ] p.1 표지 반영
- [ ] p.2~5 IaC 개념/도구/장점 반영
- [ ] p.6~11 Terraform 개요/Workflow 반영
- [ ] p.12~28 Resource/Data Source 반영
- [ ] p.29~37 Variable/Output 반영
- [ ] p.38~41 count/for_each/조건문 반영
- [ ] p.42~52 Module/Backend/Remote State 반영
- [ ] PDF에 없는 보충 설명은 분리 표기
- [ ] 이미지/도식은 의미 중심으로 텍스트화
- [ ] 명령어는 원문 표기를 보존
- [ ] 오타 가능성은 `확인 필요`로 표시
- [ ] Coverage Map 작성
- [ ] 최종 분리 후보 작성
- [ ] 확인 필요 항목 목록 작성

### C. Concept Note 작성

- [ ] Source Digest에서 개념 후보 추출
- [ ] `IaC 개념.md` 작성
- [ ] `IaC 도구 분류.md` 작성
- [ ] `Terraform 개요.md` 작성
- [ ] `Terraform Workflow.md` 작성
- [ ] `Terraform Resource와 Data Source.md` 작성
- [ ] `Terraform Variable과 Output.md` 작성
- [ ] `Terraform 반복문과 조건문.md` 작성
- [ ] `Terraform Module.md` 작성
- [ ] `Terraform Backend와 Remote State.md` 작성
- [ ] `AWS 프로젝트에 Terraform 적용하기.md` 작성 여부 판단
- [ ] 각 노트에 source_pages 추가
- [ ] 각 노트에 PDF 근거 / 내장 지식 / 확인 필요 구분

### D. Lab Note 판단

- [ ] 실습 명령어가 실제로 필요한지 판단
- [ ] 단순 개념 설명은 Lab Note로 만들지 않음
- [ ] 실제 AWS 리소스 생성 실습은 Lab Note 후보로 분리
- [ ] 실습 노트에는 목표/환경/절차/검증/실패 시 확인/롤백 포함
- [ ] Terraform 명령어는 실제 명령 기준으로 검증 필요 표시

### E. MOC 정리

- [ ] `IaC MOC.md` 생성
- [ ] Source Digest 연결
- [ ] Concept Note 목록 정리
- [ ] Lab Note 후보 정리
- [ ] Project Application 후보 정리
- [ ] 존재하지 않는 파일은 wiki link 금지
- [ ] 실제 파일 생성 후 링크 전환

### F. 검증

- [ ] PDF 전체 페이지가 Coverage Map에 포함되었는지 확인
- [ ] Source Digest와 Concept Note의 source_pages가 맞는지 확인
- [ ] PDF 원문과 다른 해석이 섞이지 않았는지 확인
- [ ] 최신성이 필요한 Terraform/AWS 명령은 공식 문서 대조 필요 표시
- [ ] 최종적으로 “확인 필요” 항목만 따로 모였는지 확인
- [ ] 다음 세션에서 이 노트만 보고 작업 재개 가능한지 확인

---

## 10. 맥락 복구용 프롬프트

새 세션에서 맥락이 꼬이면 아래 프롬프트를 사용한다.

```markdown
나는 `Iac.pdf`를 Obsidian 노트로 전환하는 작업 중이다.
아래 기준을 지켜라.

1. 바로 Concept Note를 만들지 말고 Source Digest부터 만든다.
2. PDF 원문 기반 내용과 보충 설명을 구분한다.
3. 출처는 네 가지로 분류한다:
   - 내장 지식
   - 인터넷 고신뢰 정보
   - 인터넷 비공식 고품질 의견
   - PDF
4. PDF에 없는 내용은 PDF 내용처럼 쓰지 않는다.
5. Source Digest에는 Coverage Map, 최종 분리 후보, 확인 필요 항목을 포함한다.
6. Lab Note는 기본 생성하지 않고, 실제 실습 절차가 의미 있을 때만 분리한다.
7. 없는 노트에 wiki link를 만들지 않는다.
8. 최종 목표는 Obsidian에서 재사용 가능한 AWS/IaC/Terraform 학습 위키 재료화다.

우선 `IaC - Source Digest.md`를 작성하라.
```

---

## 11. Definition of Done

이 작업은 다음 조건을 만족하면 완료로 본다.

- [ ] `IaC - Source Digest.md`가 생성됨
- [ ] PDF 1~52쪽이 Coverage Map에 모두 반영됨
- [ ] Concept Note 후보가 정리됨
- [ ] Lab Note 생성 여부가 판단됨
- [ ] 확인 필요 항목이 따로 분리됨
- [ ] 출처 분류 규칙이 적용됨
- [ ] `IaC MOC.md`에 연결 가능한 구조가 정리됨
- [ ] 다음 세션에서 이 노트만 보고 작업 재개 가능함
