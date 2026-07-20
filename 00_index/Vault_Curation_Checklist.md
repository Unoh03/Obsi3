---
type: control
status: active
created: 2026-07-02
updated: 2026-07-20
scope: formal repo-wide navigation and retrieval baseline audit
---

# Vault Curation Checklist

이 문서는 평상시 작업 큐가 아니다. **정확한 현재 지식에 도달하고, 그 정확성을 유지하면서 성공한 작업 1회당 AI 토큰·한도 비용을 줄이는지** 정식 감사할 때만 사용한다.

일반 노트 작업과 세션 뒷정리는 이 문서를 읽지 않고 `AGENTS.md`의 read budget과 Git range 절차를 따른다.

## 판단 기준

```text
총비용 = 탐색 읽기 + 대상·근거 읽기 + 추론 + 오판 재작업 + 구조 유지비용
```

정확성을 희생한 비용 절감은 실패다. 라우팅 문서나 metadata를 추가했더라도 정확성이 같고 총비용이 줄지 않으면 개선으로 보지 않는다. 반대로 문서 수가 적어도 잘못된 노트에 도달해 재작업이 반복되면 충분히 얇은 구조가 아니다.

## 정식 감사 절차

1. `START_REF`, `END_REF`, 현재 worktree와 감사 범위를 기록한다.
2. 범위 안의 Home, 영역 MOC, 주제/프로젝트 MOC, status record, source catalog, RAW log, leaf note를 구분한다.
3. 다음 retrieval 유형을 실제 파일로 표본 검사한다.
   - 정확한 파일·경로
   - 알려진 주제
   - 넓고 불명확한 요청
   - current와 legacy 충돌
   - stable note와 RAW/source 충돌
   - 대형 노트의 section-level 접근
4. MOC 설명보다 대상 note와 runtime·diff·log 같은 1차 근거를 우선한다.
5. 오판이나 반복 읽기를 만드는 최소 지점만 수정한다.
6. 변경 범위에 맞춰 diff, frontmatter, wiki link와 필요한 runtime 검증을 수행한다.
7. 확인하지 않은 note body, PDF, 이미지, Git history 등은 완료 범위에서 제외한다.

## 완료 기준

- 정확한 대상은 직접, 알려진 주제는 가장 가까운 MOC, 넓은 요청만 Home에서 시작한다.
- current/restart point가 실제 최신 note와 일치하고 legacy/stale note를 현재로 오인하지 않는다.
- stable/active note와 RAW/source/evidence의 역할이 실제 파일에서 구분된다.
- 대형 노트는 필요한 H1/Part와 인접 문맥만 읽어 답할 수 있다.
- 변경된 frontmatter가 canonical schema와 validator를 통과한다.
- 새 wiki link의 target과 basename ambiguity가 확인된다.
- 불필요한 제어 문서·상위 MOC 역주행이 기본 경로에 없다.
- 검증 범위와 제외 범위를 함께 보고한다.

전체 note body를 읽지 않았다면 콘텐츠 품질이나 repo-wide 완료를 주장하지 않는다.

## 현재 운영 경계

- MOC는 route, restart point, RAW/source, legacy 경계만 관리하며 inventory나 완료 로그를 넣지 않는다.
- 전체 inventory는 문서로 유지하지 않고 필요할 때 `rg --files`로 만든다.
- 본문 템플릿은 선택 예시다. 새 note는 최소 frontmatter와 routing만 요구한다.
- legacy frontmatter는 현재 작업이나 routing이 의존할 때만 점진적으로 고친다.
- 대형 누적 note는 크기만으로 분리하지 않는다. section-level 접근이 반복해서 실패하거나 각 Part의 독립 수명주기가 생길 때만 분리를 검토한다.
- 기존 Obsidian plugin 추적 파일은 의도적 백업이므로 일반 감사에서 제외한다.
- 현재진행 RAW와 source는 완성형 구조로 과도하게 정리하지 않는다.
- 고정 retrieval benchmark는 gold set의 구조 유효성 보조 자료일 뿐 실제 LLM 토큰·정확도나 완료 gate가 아니다.

## 남은 불확실성

- legacy note 전체의 frontmatter와 본문 품질은 전수 검증하지 않았다.
- PDF, 이미지, 캡처와 Git history의 내용·보안·저작권은 이 checklist의 기본 범위가 아니다.
- 실제 모델의 총 토큰 소비는 고정 JSON 검사로 측정되지 않는다. 반복 작업의 read set과 재작업 발생 여부를 관찰해야 한다.
- MOC의 current/restart 설명은 후속 실습이 끝날 때 Git range 기반 뒷정리가 누락되면 다시 drift할 수 있다.

## 이력 요약

- 2026-07-02~09: 주요 MOC/control 26개 범위에서 Home-to-leaf, RAW/source, current/legacy 경계를 감사했다. 전체 note body, PDF와 이미지는 제외했다.
- 2026-07-16: 작업별 read budget, 선택형 template 정책, Git range cleanup과 frontmatter range validator를 기준선에 반영했다.
- 2026-07-20: 최상위 목적을 토큰·한도 절약으로 명시하고, IaC v17 완료 상태와 retrieval benchmark의 비권위성을 현재 파일에 반영했다.
- 2026-07-20: 운영 MOC/control metadata, AWS Arc 원본 PDF catalog, 3차 프로젝트 draft route, frontmatter·navigation validator와 CI 기준선을 정렬했다. 전체 note body·PDF·이미지는 제외했다.
- 세부 변경 이력과 당시 수치는 Git history에서 확인한다.

## 보고 형식

```text
범위와 Git 기준점:
확인한 실제 경로:
수정한 것 / 유지한 것:
줄어든 오판·불필요한 읽기:
검증 출력:
제외 범위와 남은 불확실성:
```
