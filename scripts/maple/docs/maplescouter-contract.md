---
type: control
status: draft
created: 2026-09-18
scope: 우노03 은월 MapleScouter 관측 contract
---

# MapleScouter 관측 contract

## 현재 판정

**실제 MapleScouter 계산 contract는 아직 미확인이다.** 아래 도구 검증은 서비스 계산 결과의 재현 검증과 구분한다.

| 항목 | 상태/근거 |
|---|---|
| 검증 일자 | 2026-09-18 KST |
| 초기 페이지 | `https://maplescouter.com/ko` |
| Python / Playwright / HTTPX / DeepDiff | 3.14.3 / 1.63.0 / 0.28.1 / 9.1.0 |
| 전용 Brave CDP 연결 | 확인. Chromium 153.0.8010.48, 127.0.0.1:9222 |
| 테스트 | 단위 테스트 14개 통과. 실제 Brave CDP→로컬 HTTP observed/JSON replay 스모크 PASS |
| 실제 baseline A/B | 미확보 |
| 실제 endpoint/method | unknown |
| 필수 headers / auth/session 의존성 | unknown |
| request/response 관측 schema | unknown |
| UI ↔ response mapping | unknown |
| NEXON 기준 snapshot | 새 수집 완료 후 경로·SHA-256·collected_at 연결 예정 |
| NEXON 매핑 / manual-only / unknown 필드 목록 | 실제 요청 확보 후 작성 |
| 일반 stat / Scouter-only 변경 실험 | 미실행 |
| 설정 복구 | 미검증 |
| 호출 제한·이용정책 | 미확인 |
| A-CANDIDATE / A-VALIDATED / A-USABLE | 모두 미판정 |

로컬 스모크 증거는 ignored `.runtime/smoke-266cd3b5982e428f9e7292c826e6f423/smoke-result.json`에 있다. 이 테스트는 서비스에 계산 요청을 보내지 않았다.

## 판단 원칙과 한계

- baseline은 normal 두 건, 필요한 경우 forced-network 두 건을 별도 취급한다.
- 변동 관측 필드를 계산과 무관하다고 단정하지 않는다.
- 응답 구조 일치/바이트 일치와 UI의 핵심 결과 일치를 구분한다.
- 헤더·body의 자동 필터는 완전한 비밀 판별기가 아니다. 미검토 fixture는 Git에서 제외한다.
- 선택한 페이지 CDP에서 관측되지 않는 worker/OOPIF 경로와 로컬 계산 여부는 별도 조사 대상이다.
- 실패/비JSON/민감 body는 원문을 저장하지 않고 원인 종류만 기록한다. 완전한 캡처로 판정하지 않는다.
- 프런트엔드 JS asset identity는 backend 버전 증명이 아니다.
- 조사 완료와 A 채택을 구분한다. 캡처 replay 성공은 자동 builder의 정확성 증명이 아니다.

## 외부 참고 자료

- [CDP Network 정의](https://github.com/ChromeDevTools/devtools-protocol/blob/master/pdl/domains/Network.pdl)
- [Playwright connect_over_cdp](https://playwright.dev/python/docs/api/class-browsertype#browser-type-connect-over-cdp)
- [HTTPX 환경 변수](https://www.python-httpx.org/environment_variables/)
- [DeepDiff 옵션](https://zepworks.com/deepdiff/current/diff_doc.html)
- [MapleDoro 참고 코드](https://github.com/NotTsunami/mapledoro/blob/main/src/features/characters/scouter/scouterApi.ts): GMS 중심 기본값을 KMS에 그대로 적용하지 않음.
- [maplescouter-sync](https://github.com/tomerh2001/maplescouter-sync): 저장 schema 후보에 관한 제3자 자료. 현재 사이트 실측으로 확인 필요.
