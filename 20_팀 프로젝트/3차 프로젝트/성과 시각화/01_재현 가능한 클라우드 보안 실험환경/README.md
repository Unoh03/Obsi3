---
type: project-doc
status: draft
created: 2026-07-30
project: 3차 프로젝트
project_moc: "[[20_팀 프로젝트/3차 프로젝트/00_3차프로젝트_목차]]"
---

# 재현 가능한 클라우드 보안 실험환경 — 성과 시각화

이 폴더는 3차 프로젝트의 최종 보고서가 아니라, 검증된 대표 작업을 한눈에 평가할 수 있도록 만든 **독립형 사례 페이지의 첫 기준본**이다.

## 기준 산출물

- 편집 기준: `content.json`, `template.html`, `render_showcase.py`
- 생성 결과: `운호_매일_지워도_다시_살아나는_AWS_실험환경.html`
- 서드파티 고지: `THIRD_PARTY_NOTICES.txt`

생성 결과 HTML에는 CSS와 JavaScript를 전부 포함하므로 별도 Asset이나 인터넷 연결 없이 열 수 있다.

## 재생성

```powershell
python .\render_showcase.py
```

## 기록 경계

- 2026-07-30 `RAW_메모.md`와 일일 로그, 실제 자동화 Source를 근거로 작성한다.
- 최초 Runtime Up과 최초 Daily Down은 검증 완료로 표시한다.
- Down 이후 두 번째 Cold Up은 아직 검증되지 않았으므로 완료로 표시하지 않는다.
- 기존 팀 Terraform 전체를 개인 단독 성과로 표현하지 않는다.
- Access Key, Token, Password, Private Key, kubeconfig와 실제 Secret 값은 포함하지 않는다.

## 오픈소스 구성

- Tabler Core 1.4.0: 사례 페이지의 반응형 UI 기반
- Mermaid 11.16.0: 흐름도 렌더링
- PrismJS 1.30.0: PowerShell·HCL 코드 강조

각 라이선스 원문과 출처는 `vendor/licenses/` 및 `THIRD_PARTY_NOTICES.txt`에 보존한다.
