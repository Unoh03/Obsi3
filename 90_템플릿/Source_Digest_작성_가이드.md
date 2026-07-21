---
type: control
status: stable
created: 2026-07-20
scope: source-digest-authoring
---

# Source Digest 작성 가이드

## 목적

Source Digest는 PDF·강의자료를 반복해서 해석할 때 발생하는 비용을 줄이기 위한 **원자료 대체 계층**이다.

```text
원자료를 한 번만 추출·렌더링·검수
→ 의미 있는 정보 전체를 Markdown으로 구조화
→ 이후에는 Index와 필요한 Chapter만 선택해서 읽음
→ 불확실성이나 원본 증거가 필요할 때만 PDF로 돌아감
```

짧은 요약을 만드는 것이 목적이 아니다. 원자료의 의미 있는 정보를 손실 없이 옮기되, AI가 전체 원자료를 다시 읽지 않고 필요한 구간에 도달할 수 있게 만드는 것이 목적이다.

## 무손실의 의미

여기서 무손실은 PDF의 바이트·글꼴·장식까지 복제한다는 뜻이 아니다. 다음 정보 요소를 빠뜨리지 않고 재구성한다는 뜻이다.

- 제목·본문·목록·각주·경고·조건·예외
- 표의 행·열 관계와 셀 내용
- Code·명령어·설정·수식·들여쓰기·기호
- Quiz의 문제·보기·정답·해설
- 도식·Screenshot의 개체 수, 색상, 범례, 방향, 연결 관계, 상태 전이와 중간 단계
- Page 순서와 원자료 위치
- 중복·빈 Page·판독 불가 영역의 존재
- 원자료 내부에서 서로 맞지 않는 값·Hash·시간·본문·도식의 존재

장식만 있는 요소는 생략할 수 있지만 해당 Page의 Coverage에는 `정보성 내용 없음`으로 기록한다. 반복 내용은 전문을 다시 복사하지 않고 원문 위치와 반복 관계를 기록할 수 있다.

원자료 내부의 모순도 보존 대상이다. 서로 다른 값을 하나로 몰래 교정하거나 자연스럽게 이어 붙이지 말고, 원문 값을 그대로 기록한 뒤 `원자료 내부 불일치`로 명시한다. 원인 추정은 원자료 사실과 분리하고, 해당 자료만으로 관계를 확정할 수 없으면 그 한계를 함께 남긴다.

## 원자료와 보충 정보의 경계

PDF에서 확인한 내용과 AI가 추가한 설명을 같은 문단에 섞지 않는다.

```markdown
### 원자료 내용

### 표·Code·명령어

### 도식·이미지 의미

### 판독 불확실성

### 원자료 외 보충
```

원자료는 `[[파일명.pdf]] p.N`처럼 위치를 표시한다. 강의자료는 그 자료에 무엇이 적혀 있는지를 확인하는 기준이지만, 내용이 현재도 정확하거나 공식 권고라는 뜻은 아니다.

원자료 밖의 정보를 추가할 때는 다음 출처를 구분한다.

1. **Local primary evidence**: Runtime Output, Repository State, Diff, Log, 실제 실행 증거
2. **Authoritative external evidence**: 공식 문서, 표준, Specification, Primary Paper, Release Note
3. **Informal external evidence**: Community Report, Blog, 사용자 경험
4. **Parametric knowledge**: 별도 근거를 현재 확인하지 않은 모델 지식

보충 정보가 필요하지 않으면 해당 Section을 만들지 않는다. Source Digest는 외부 지식으로 원자료를 몰래 교정하거나 대체하지 않는다.

## 대형 원자료의 파일 구조

원자료가 방대하면 하나의 거대 파일에 계속 누적하지 않고 논리적 Chapter 단위로 나눈다. 분할은 정보를 줄이기 위한 것이 아니라 읽기 단위를 제한하기 위한 것이다.

```text
주제 Source Digest Index
├─ Chapter 01 Source Digest (p.1-p.12)
├─ Chapter 02 Source Digest (p.13-p.73)
├─ Chapter 03 Source Digest (p.74-p.109)
└─ ...
```

### Index 역할

- 원자료 식별 정보와 전체 Page 범위
- Chapter별 Page 범위와 처리 상태
- Chapter Digest Link
- 누락·중복·검수 대기 구간
- 현재 수업 또는 변환 재시작 지점

Index는 전체 내용을 다시 요약하지 않는다.

### Chapter Digest 역할

- 자기 `source_pages` 범위의 의미 있는 정보 전체 보존
- Page·구간별 원자료 내용과 Visual 의미
- 불확실성·외부 검증 필요 사항
- Index로 돌아가는 `digest_index` Link

Chapter 경계는 PDF의 논리적 목차를 우선한다. 한 Chapter가 지나치게 크면 학습 주제나 실습 단위로 한 번 더 나눈다. Page 범위에는 설명 없는 Gap이 없어야 하며, 의도적인 Overlap은 이유를 기록한다.

## MOC와의 관계

MOC는 모든 Chapter 파일을 나열하는 Inventory가 아니다.

- MOC는 Source Digest Index와 현재 필요한 Chapter 또는 재시작 지점만 연결한다.
- 전체 Chapter 목록과 Coverage는 Source Digest Index가 관리한다.
- 내용 변환과 MOC 수정은 분리한다. 변환 작업이 임의로 MOC를 확장하지 않는다.
- 실제 파일이 생기기 전에는 Placeholder wiki link를 만들지 않는다.
- 운영 정리 단계에서 route, restart point, RAW/source, legacy 경계가 바뀌었을 때만 MOC를 갱신한다.

권장 탐색 순서는 다음과 같다.

```text
MOC
→ Source Digest Index
→ 필요한 Chapter Digest
→ 필요한 H1/H2 구간
→ 불확실성·도식 원본 확인이 필요할 때만 PDF
```

## Frontmatter

모든 Source Digest는 다음 필드를 가진다.

```yaml
type: source-digest
status: draft
created:
parent_moc:
source:
source_pages:
```

다음 필드는 자료 규모와 검수 상태에 따라 사용한다.

```yaml
digest_role: index | chapter | single
digest_index:
chapter:
source_hash:
source_version:
coverage_status: partial | complete
extraction_method:
reviewed_on:
```

- `source_pages`: Index는 전체 범위, Chapter는 자기 범위
- `source_hash`: 원본 교체를 감지하기 위한 SHA-256
- `coverage_status`: Page와 정보 요소의 처리 범위
- `reviewed_on`: 원자료 대조 검수를 마친 날짜

## 변환 절차

1. 원자료 파일명, Page 수, Version, SHA-256을 확인한다.
2. PDF 목차와 Page 흐름을 기준으로 Index와 Chapter 경계를 정한다.
3. Text Layer를 추출하되 결과를 원문으로 단정하지 않는다.
4. 정보성 Page를 Rendering하여 표·도식·Screenshot·강조 정보를 확인한다.
5. 원자료 내용과 Visual의 개체 수·상태 전이·중간 단계까지 Chapter Digest에 기록한다.
6. Code·명령어·설정은 기호·공백·들여쓰기를 원본과 대조한다.
7. Coverage에서 모든 Page의 처리 상태를 기록한다.
8. 판독 불가·내부모순·현재성 문제는 몰래 교정하거나 추측으로 메우지 않고 원자료의 상태와 판단 한계를 표시한다.
9. 원자료 밖 보충이 필요하면 출처 등급과 함께 별도 Section에 기록한다.
10. Chapter별 검수와 전체 Coverage 검수를 통과한 뒤 상태를 안정화한다.

## 상태와 완료 판정

- `draft`: 변환 또는 원본 대조가 진행 중
- `active`: 현재 수업·변환에서 계속 갱신하는 운영본
- `stable`: 선언한 `source_pages` 범위의 무손실 변환과 검수가 완료됨
- `stale`: 원본 Hash·Version이 달라져 현재 원자료를 대표하는지 재검토가 필요함
- `legacy`: 새 Source Digest가 누적 계승하거나 대체한 이전판
- `archived`: 참고만 남기고 운영 경로에서 제외한 기록

`stable source-digest`는 **해당 원자료를 충실하게 옮겼다**는 뜻이다. 원자료의 기술 내용이 현재도 맞거나 공식적으로 검증됐다는 뜻은 아니다.

## 완료 검증

다음 조건을 모두 만족해야 선언한 범위를 무손실 변환했다고 판정한다.

- [ ] 원자료 파일·Page 수·Version·Hash를 식별했다.
- [ ] 모든 Page가 Coverage에 포함됐다.
- [ ] 본문·표·Code·명령어·Quiz·각주를 확인했다.
- [ ] 정보성 Page를 Rendering하여 개체 수·색상·방향·상태 전이·중간 단계를 검수했다.
- [ ] 원자료 내부의 값·Hash·시간·본문·도식 불일치를 보존하고 명시했다.
- [ ] 판독 불가·누락 가능성·OCR 오류를 표시했다.
- [ ] 원자료와 외부 보충 설명을 분리했다.
- [ ] Chapter 사이의 Gap과 의도하지 않은 Overlap이 없다.
- [ ] 원자료 Page로 역추적할 수 있다.
- [ ] 실제 자격증명·개인정보를 공개 문서에 복사하지 않았다.
- [ ] 공개 저장소에 올릴 자료의 재배포 허용 범위를 확인했다.
- [ ] 새 wiki link의 Target이 실제로 존재한다.

검증 명령은 변경 범위에 맞게 사용한다.

```powershell
python scripts/validate_frontmatter.py --changed
python scripts/validate_navigation.py
git diff --check
```

Navigation 검사는 MOC·Index route를 수정했을 때 실행한다. Frontmatter·Link·Gap/Overlap 같은 구조 검사가 통과해도 의미적 무손실이 증명되지는 않는다. `stable` 판정에는 구조 검사와 별도로 Page Rendering 및 원본 내용 대조를 완료해야 한다.

## 보안·권리 예외

실제 Password, Token, Cookie, Private Key, 개인정보는 공개 Markdown에 그대로 복사하지 않는다.

```text
[REDACTED: Registry credential, 원본 p.42]
```

처럼 정보의 존재·종류·위치는 보존하고 값은 제거한다. 원본 자체를 공개 저장소에 둘 수 없는 경우에도 Source Digest가 재배포 허용 범위를 넘지 않는지 확인한다.
