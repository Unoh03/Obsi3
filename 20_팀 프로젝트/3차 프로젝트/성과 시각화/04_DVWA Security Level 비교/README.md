---
type: project-doc
status: draft
created: 2026-08-03
project: 3차 프로젝트
project_moc: "[[20_팀 프로젝트/3차 프로젝트/00_3차프로젝트_목차]]"
---

# DVWA Security Level 비교 — 성과 시각화

BANK로 재조립한 DVWA 업무 기능 10개의 `Low`, `Medium`, `High`, `Impossible` Source 40개를 비교해, 우회 가능한 부분 방어와 근본 조치가 어떻게 다른지 보여 주는 독립형 페이지다.

## 기준 산출물

- 편집 기준: `content.json`, `template.html`, `render_showcase.py`
- 미리보기 생성: `render_previews.mjs`
- 생성 결과: `운호_Low부터_Impossible까지_무엇이_달라지는가.html`
- 미리보기: `preview-desktop.png`, `preview-mobile.png`
- 서드파티 고지: `THIRD_PARTY_NOTICES.txt`

생성된 HTML에는 CSS가 포함되므로 별도 Asset이나 인터넷 연결 없이 열 수 있다.

## 재생성

```powershell
python .\render_showcase.py
& 'C:\Users\Unoh\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe' .\render_previews.mjs
```

## 근거와 판정 경계

- `D:\DVWA\vulnerabilities\` 아래 BANK 연결 Module 10개의 `source\low.php`, `medium.php`, `high.php`, `impossible.php`를 직접 읽어 비교했다.
- BANK 업무명과 Route는 `../03_BANK 공격 표면 지도/content.json`의 현재 매핑을 사용했다.
- `High`라는 이름만으로 안전하다고 판정하지 않는다. 일부 Module은 문자열 결합, blacklist, 무제한 인증 시도를 남긴다.
- `Impossible`은 해당 실습 취약점에 대한 DVWA의 교육용 방어 예시다. 앱 전체의 Production 보안 수준을 뜻하지 않는다.
- 이 산출물은 Source 비교다. Level별 실제 공격 성공, WAF 반응, 로그, 조치 후 재검증을 모두 Runtime으로 증명했다는 뜻은 아니다.
- 이번 작업에서는 DVWA, Terraform, AWS Runtime을 변경하지 않았다.

## 오픈소스 구성

- Tabler Core 1.4.0: 반응형 UI 기반

라이선스 원문과 출처는 `vendor/licenses/`와 `THIRD_PARTY_NOTICES.txt`에 보존한다.
