---
type: project-doc
status: draft
created: 2026-08-03
project: 3차 프로젝트
project_moc: "[[20_팀 프로젝트/3차 프로젝트/00_3차프로젝트_목차]]"
---

# 보안 관측과 조치 전후 검증 — 성과 시각화

IAM-01·WEB-01의 2026-08-02 Runtime 결과를 한눈에 비교하기 위한 독립형 사례 페이지다.

## 기준 산출물

- 편집 기준: `content.json`, `template.html`, `render_showcase.py`
- 생성 결과: `운호_공격은_어디에_흔적을_남기는가.html`
- 미리보기: `preview-desktop.png`, `preview-mobile.png`
- 서드파티 고지: `THIRD_PARTY_NOTICES.txt`

생성된 HTML에는 CSS와 JavaScript가 포함되므로 별도 Asset이나 인터넷 연결 없이 열 수 있다.

## 재생성

```powershell
python .\render_showcase.py
```

## 근거와 판정 경계

- canonical 문서: `관측성_As-built_및_Runtime_검증.md`, `보안_실험_시나리오_계약.md`, `멘토 상담용 관측성 진행 보고 초안.md`
- Runtime Evidence: 지정된 IAM-01 2개, WEB-01 3개, Athena 4개 Bundle
- 2026-08-03 재검증: 위 9개 Bundle의 SHA-256 536개 중 불일치·누락 0
- IAM-01은 조치 전 S3 Canary 접근과 권한 제거 뒤 동일 조건 실패까지 검증 완료로 표시한다.
- WEB-01은 Application Event와 Alarm 상태 전이까지만 검증 완료로 표시한다.
- WAF BLOCK·HTTP 403과 SNS 외부 수신은 미검증으로 표시한다.
- Request/Response Body, Secret, DB SQL, Container syscall·RCE, 파일 내용은 현재 Blind Spot으로 표시한다.
- IAM-01·WEB-01은 팀이 확정한 본편이 아니라 관측 Pipeline의 후보 검증이다.

## 오픈소스 구성

- Tabler Core 1.4.0: 반응형 UI 기반
- Mermaid 11.16.0: 흐름도 렌더링
- PrismJS 1.30.0: 코드 강조

라이선스 원문과 출처는 `vendor/licenses/`와 `THIRD_PARTY_NOTICES.txt`에 보존한다.
