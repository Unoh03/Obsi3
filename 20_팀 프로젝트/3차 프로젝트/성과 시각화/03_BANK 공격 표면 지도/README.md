---
type: project-doc
status: draft
created: 2026-08-03
project: 3차 프로젝트
project_moc: "[[20_팀 프로젝트/3차 프로젝트/00_3차프로젝트_목차]]"
---

# BANK 공격 표면 지도 — 성과 시각화

BANK로 재구성한 DVWA의 업무 기능과 취약점 Engine을 연결하고, 각 Route의 정상 목적·공격 표면·관측 지점·현재 검증 상태를 한눈에 보여 주는 독립형 페이지다.

## 기준 산출물

- 편집 기준: `content.json`, `template.html`, `render_showcase.py`
- 미리보기 생성: `render_previews.mjs`
- 생성 결과: `운호_BANK는_어디서_공격받을_수_있는가.html`
- 미리보기: `preview-desktop.png`, `preview-mobile.png`
- 서드파티 고지: `THIRD_PARTY_NOTICES.txt`

생성된 HTML에는 CSS와 JavaScript가 포함되므로 별도 Asset이나 인터넷 연결 없이 열 수 있다.

## 재생성

```powershell
python .\render_showcase.py
& 'C:\Users\Unoh\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe' .\render_previews.mjs
```

## 근거와 판정 경계

- 2026-08-03 BANK Application에 로그인한 뒤 홈과 주요 10개 업무 Route를 읽기 전용으로 확인했다.
- 이번 화면 탐색에서는 공격성 입력을 전송하지 않았다.
- SQLi·XSS·반복 로그인 관련 Runtime 판정은 `2026-08-03_일일_로그.md`, `관측성_As-built_및_Runtime_검증.md`, `보안_실험_시나리오_계약.md`를 근거로 한다.
- Route가 존재한다는 사실과 해당 취약점의 악용·탐지·조치가 검증됐다는 사실을 분리한다.
- SQLi 데이터 추출, XSS Browser 실행, Command Injection부터 Pod Identity·S3까지의 End-to-End 공격, 대부분 Module의 조치 전후는 미검증으로 표시한다.
- TalentHook 확장안은 실제 사건의 그대로인 재현이 아니라 Storage 접근 권한 문제를 EKS Workload Identity 환경으로 확장한 후보 시나리오다.

## 오픈소스 구성

- Tabler Core 1.4.0: 반응형 UI 기반
- Mermaid 11.16.0: 공격 표면 관계도 렌더링

라이선스 원문과 출처는 `vendor/licenses/`와 `THIRD_PARTY_NOTICES.txt`에 보존한다.
