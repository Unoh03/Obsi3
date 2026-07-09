---
type: curation-checklist
status: active
created: 2026-07-02
scope: repo-wide navigation and retrieval audit
---

# Vault Curation Checklist

이 문서는 vault 전체를 다시 쓰기 위한 파일 목록이 아니다.
목표는 보안 교육 이후에도 이 vault를 장기 보조기억으로 쓰기 위해, `current / stable / raw / source / legacy / archived` 경계를 점검하는 작업 큐다.

## 사용 방법

1. 새 루프는 먼저 `Current priority override`를 확인하고, 아래 작업 큐에서 해당 영역의 P0/P1을 하나만 고른다.
2. 먼저 `Home → 영역 MOC → 주제/프로젝트 MOC`를 따라가며 실제 상태를 확인한다.
3. 현재진행 영역은 대공사하지 않는다. `draft`, `raw`, `source` 표시와 최소 진입점만 유지한다.
4. 완료·구버전 영역은 현재 재시작점처럼 보이면 MOC에서 격하하거나 경고한다.
5. 수정 후에는 `git diff --check`, targeted diff, wiki-link target check, table pipe check를 수행한다.

## Current priority override

사용자 확인 기준 현재 우선순위는 `10_학습 노트/`와 `90_템플릿/`이다.
Goal 재개 시 프로젝트 P0를 자동으로 이어가기보다, 먼저 학습 노트와 템플릿의 장기 회상 구조를 점검한다.

현재 우선순위:

1. `10_학습 노트/`: concept / lab / RAW / source / restart 경계
2. `90_템플릿/`: 이후 새 노트가 같은 구조를 유지하게 하는 작성 틀
3. `20_팀 프로젝트/`: 이미 처리 중인 P0나 오판 위험이 큰 경우에만
4. `40_자료/`: source 확인용, 필요할 때만

## Non-goals

- 모든 파일을 MOC에 넣지 않는다.
- 전체 파일 본문을 매번 읽지 않는다.
- 물리 삭제, 이동, 이름 변경은 별도 승인 없이는 하지 않는다.
- `LLM_AGENT_INDEX.md`를 실제 MOC 경로의 대체물로 쓰지 않는다.
- 현재진행 공식 Arc 과정은 수업 종료 전까지 안정 MOC로 과하게 정리하지 않는다.

## Current scan snapshot

- 기준 시점: 2026-07-02
- `rg --files`: 912개
- 파일 확장자 상위: `.png` 431개, `.md` 197개, `.sh` 50개, `.webp` 38개, `.pdf` 33개
- 핵심 MOC/control 파일: `Home.md`, `LLM_AGENT_INDEX.md`, `Vault_Retrieval_Architecture_v1.md`, 각 영역·주제·프로젝트 `00_*_목차.md`
- 가장 큰 영역: `40_자료/` 444개, `10_학습 노트/` 202개, `20_팀 프로젝트/` 196개
- 생성 시점 worktree note: 이 checklist 파일은 신규 파일이고, `Home.md`에는 이 파일로 가는 링크가 추가되었다.
- Arc 모듈 1 source digest의 현재 tracked 경로는 `40_자료/강의 자료/AWS Arc/모듈 1 아키텍팅 기본 사항 Source Digest.md`이다. 예전 `- 정리본` 경로는 현재 `git ls-files` 출력에 없다.

## Global completion gates

- [ ] `Home → 영역 MOC → 주제/프로젝트 MOC → 실제 노트` 경로가 주요 영역에서 유지된다.
- [ ] `RAW/source`가 `stable` 정리본처럼 보이는 주요 경로가 없다.
- [ ] 완료·구버전 자료가 현재 재시작점처럼 보이는 주요 경로가 없다.
- [ ] 현재진행 영역은 최소 진입점과 `draft/raw/source` 표시만 있고, 과한 정규화가 없다.
- [ ] 주요 프로젝트는 결과·증거·스크립트·원문 로그를 구분한다.
- [ ] 새 wiki link는 존재가 확인되어 있다.
- [ ] 마지막 검증에서 `git diff --check`, targeted diff, wiki-link target check, table pipe check가 통과한다.

## P0 - 현재 우선순위: 학습 노트와 템플릿

- [ ] 학습 노트 전체 라우팅 점검
  - Start: [[10_학습 노트/00_학습노트_목차]]
  - Scope: 시스템보안, 웹보안, 클라우드/AWS, 네트워크, 리눅스 등 주요 학습 영역의 concept / lab / RAW / source / restart 경계.
  - Risk: 오래된 MOC가 현재 재시작 지점처럼 보이거나, source/RAW가 안정 정리본처럼 보이면 장기 회상과 AI 검색이 동시에 흔들린다.
  - 2026-07-02 loop result: 상위 학습노트 MOC에 stable note, RAW/source, restart point, legacy/stale 경계를 추가했다. 하위 MOC 전수 점검은 남아 있다.
  - 2026-07-02 loop result: 네트워크, 리눅스, Spring/Java 웹 도구 MOC에 restart point와 RAW/source/legacy 주의를 추가했다. 시스템보안 세부와 웹보안 재시작점 평가는 남아 있다.
  - 2026-07-09 loop result: 시스템보안 하위 재시작 경계는 웹보안 source coverage와 네트워크보안 DHCP Snooping / IP Source Guard / Wireshark 필터 위치 판정까지 닫았다.
  - 2026-07-09 loop result: 네트워크보안 MITM 흐름은 ARP Spoofing, DNS Spoofing, 평문 관찰/변조, SSH 비교/응용, L2 방어 순서로 복구하도록 MOC에 연결했다.
  - Next check: 먼저 학습노트 MOC와 주요 하위 MOC를 읽고, 실제 노트 전수 수정 전에 경계가 무너진 지점만 목록화한다.

- [x] 템플릿 구조 점검
  - Start: [[90_템플릿/00_템플릿_목차]]
  - Scope: 개념정리, 실습기록, 트러블슈팅, 명령어정리, 인덱스/MOC 템플릿.
  - Risk: 템플릿이 현재 vault의 `concept / lab / RAW / source / restart` 경계를 반영하지 못하면 새 노트가 계속 같은 혼선을 만든다.
  - 2026-07-02 loop result: 핵심 학습 템플릿에 상위 MOC, 원자료/RAW, 재시작 용도, 검증 환경 경계를 추가했다. 프로젝트·자격증 템플릿 적용 여부는 남아 있다.
  - 2026-07-06 loop result: 오답노트와 ACL 정책 템플릿에 상위 MOC, source/evidence 경계를 추가했다. 템플릿의 빈 bullet/blockquote/표 셀은 작성 자리표시자로 분류하고, 변경분은 `git diff --check`로 검증하는 운영 기준을 남겼다.
  - 2026-07-06 loop result: 프로젝트 RAW 로그, 일일 로그, 프로젝트 문서, 회의록 템플릿에 RAW/source/digest/stable 문서 역할 경계를 추가했다.
  - Next check: 템플릿 사용 예시와 Properties 필드 표준화만 남긴다.

## P1 - 학습 노트 세부 후보

- [x] 웹보안 stable / RAW / PDF source 경계 점검
  - Start: [[10_학습 노트/시스템보안/웹보안/00_웹보안_목차]]
  - Current state: PDF source, 구조 지도, 종합 복습 프로젝트, RAW 작업 메모가 분리되어 있음.
  - 2026-07-02 loop result: 웹보안 현재 재시작 지점을 `SQL Injection 방어`와 `세션과 쿠키` 중심으로 좁혔고, PDF 구조 지도·SQL Injection source-digest·프로젝트 RAW 작업 메모를 stable note로 오인하지 않도록 MOC에 경계를 추가했다.
  - 2026-07-06 loop result: 웹보안 MOC의 `PDF 정리 예정`을 `PDF/source coverage backlog`로 격하하고, `SQL Injection 방어`는 미작성 stable note 후보로 source와 주의점을 명시했다.
  - 2026-07-06 loop result: `SQL Injection 방어` stable concept note를 작성하고 웹보안 MOC에 연결했다. PDF p.132의 대응책은 보존하되 OWASP 공식 cheat sheet 근거로 Prepared Statement / Parameterized Query를 1차 방어로 보강했다.
  - 2026-07-06 loop result: `세션과 쿠키` stable concept note를 작성하고 웹보안·시스템보안 MOC에 연결했다. PDF p.49-61과 OWASP/MDN 공식 자료를 근거로 session token, cookie 저장 방식, Secure/HttpOnly/SameSite 경계를 정리했다.
  - 2026-07-07 loop result: `기초 웹 인증 방식 - Basic, Anonymous, Form` stable concept note를 작성하고 웹보안·시스템보안 MOC에 연결했다. PDF p.44-48과 MDN/RFC 7617 근거로 Basic의 Base64/HTTPS 경계, Anonymous 접근 권한, Form 인증과 세션 연결을 정리했다.
  - 2026-07-07 loop result: `웹 문서와 실행 위치` stable concept note를 작성하고 웹보안·시스템보안 MOC에 연결했다. PDF p.24-34, 렌더링 확인 p.26-27, MDN/Microsoft/PHP/Jakarta 공식 문서 근거로 HTML/DOM/JavaScript와 ASP/PHP/JSP 같은 서버 측 기술의 실행 위치를 구분했다.
  - 2026-07-07 loop result: [[10_학습 노트/시스템보안/웹보안/HTML 인코딩|HTML 인코딩]]을 p.35-43 전체 `웹 인코딩` active concept note로 확장했다. 기존 파일명은 유지하고 URL Encoding, Unicode/UTF-8, Base64를 본문에 흡수했다.
  - 2026-07-08 loop result: [[10_학습 노트/시스템보안/웹보안/OWASP Top 10 2025|OWASP Top 10 2025]] stable concept note를 작성하고 웹보안·시스템보안 MOC에 연결했다. PDF p.62-72는 강의식 진단 질문으로 보존하고, 공식명과 2025 변경점은 OWASP 공식 자료 기준으로 맞췄다.
  - 2026-07-08 loop result: [[10_학습 노트/시스템보안/웹보안/웹 진단 기초 - Spidering과 Client-side Validation 우회|웹 진단 기초 - Spidering과 Client-side Validation 우회]] stable concept note를 작성하고 웹보안·시스템보안 MOC에 연결했다. PDF p.73-76과 MDN 근거로 spidering 한계와 client/server validation 신뢰 경계를 정리했다. 기존 [[10_학습 노트/시스템보안/웹보안/Client-side Validation 우회와 Server-side Validation 실습|Client-side Validation 우회와 Server-side Validation 실습]]은 Paros 우회 실습 증거로 유지한다.
  - 2026-07-08 loop result: [[10_학습 노트/시스템보안/웹보안/로그인 Brute Force와 계정 보호|로그인 Brute Force와 계정 보호]] stable concept note를 작성하고 웹보안·시스템보안 MOC에 연결했다. PDF p.77-79, 기존 [[10_학습 노트/시스템보안/웹보안/Hydra 로그인 Brute Force 실습|Hydra 로그인 Brute Force 실습]], OWASP/NIST 근거로 반복 로그인 시도, 실패 메시지 제한, lockout/throttling/MFA 기준을 정리했다.
  - 2026-07-08 loop result: 기존 [[10_학습 노트/시스템보안/웹보안/Web Session Hijacking|Web Session Hijacking]]을 PDF p.80-82의 stable concept note로 검토 완료했다. 세션 구조는 [[10_학습 노트/시스템보안/웹보안/세션과 쿠키|세션과 쿠키]], XSS 기반 탈취 실습 증거는 [[10_학습 노트/시스템보안/웹보안/XSS를 이용한 Session Token 탈취 실습|XSS를 이용한 Session Token 탈취 실습]], Sniffing/평문 HTTP 노출은 [[10_학습 노트/시스템보안/네트워크보안/HTTP 로그인 평문 노출|HTTP 로그인 평문 노출]]에 두도록 라우팅했다.
  - 2026-07-08 loop result: 기존 [[10_학습 노트/시스템보안/웹보안/XSS|XSS]]를 PDF p.83-97의 stable concept note로 검토 완료했다. Cookie Stealing과 세션 재사용 증거는 [[10_학습 노트/시스템보안/웹보안/XSS를 이용한 Session Token 탈취 실습|XSS를 이용한 Session Token 탈취 실습]], 실무 방어 기준은 [[10_학습 노트/시스템보안/웹보안/실무형 XSS 방어|실무형 XSS 방어]], 인코딩 세부는 [[10_학습 노트/시스템보안/웹보안/HTML 인코딩|HTML 인코딩]]에 두도록 라우팅했다.
  - 2026-07-08 loop result: 기존 [[10_학습 노트/시스템보안/웹보안/CSRF|CSRF]]를 PDF p.98-106의 stable concept note로 검토 완료했다. 회원정보 변경과 게시글 작성 CSRF 재현 증거는 [[10_학습 노트/시스템보안/웹보안/CSRF를 이용한 회원정보 변경 실습|CSRF를 이용한 회원정보 변경 실습]]에 두고, OWASP/MDN 기준으로 CSRF token, SameSite, Origin/Referer, Fetch Metadata 보강 경로를 명시했다.
  - 2026-07-08 loop result: 기존 [[10_학습 노트/시스템보안/웹보안/SQL Injection을 위한 SQL 기초|SQL Injection을 위한 SQL 기초]]를 PDF p.107-114의 stable prerequisite note로 검토 완료했다. SQL 전체 문법이 아니라 SQL Injection 이해에 필요한 `SELECT`, `WHERE`, `UNION`, `INSERT`, `UPDATE`, `DELETE`만 담당하도록 라우팅했다.
  - 2026-07-08 loop result: 기존 [[10_학습 노트/시스템보안/웹보안/SQL Injection 개념과 인증 우회|SQL Injection 개념과 인증 우회]]를 PDF p.115-121의 stable concept note로 검토 완료했다. 실제 `care` 로그인 코드와 Paros 요청 조작 증거는 [[10_학습 노트/시스템보안/웹보안/SQL Injection 인증 우회 실습|SQL Injection 인증 우회 실습]]에 두고, 정보 추출과 방어는 별도 stable note로 분리했다.
  - 2026-07-08 loop result: 기존 [[10_학습 노트/시스템보안/웹보안/SQL Injection Error와 UNION 기반 정보 추출과 Schema 파악|SQL Injection Error와 UNION 기반 정보 추출과 Schema 파악]]을 PDF p.122-131의 stable concept note로 검토 완료했다. 실제 Error-based payload, `group_concat()`, `LIMIT`, `sqlmap` 재검증 증거는 [[10_학습 노트/시스템보안/웹보안/SQL Injection Error 기반 DB명 정보 추출 실습|SQL Injection Error 기반 정보 추출 실습]]에 두고, source-digest와 민감 dump 값을 stable concept note로 옮기지 않도록 라우팅했다.
  - 2026-07-08 loop result: 기존 [[10_학습 노트/시스템보안/웹보안/SQL Injection 방어|SQL Injection 방어]]를 PDF p.132의 stable defense note로 검토 완료했다. PDF의 서버 검증·필터링·에러 제한·WAF는 보존하되, OWASP 공식 cheat sheet 기준으로 Prepared Statement / Parameterized Query를 1차 방어로 둔다.
  - 2026-07-09 loop result: 기존 [[10_학습 노트/시스템보안/웹보안/File Upload와 Webshell|File Upload와 Webshell]], [[10_학습 노트/시스템보안/웹보안/Directory Listing 취약점|Directory Listing 취약점]], [[10_학습 노트/시스템보안/웹보안/웹쉘 Upload 및 실행 실습|웹쉘 Upload 및 실행 실습]]을 PDF p.133-136의 stable/lab 경계로 검토 완료했다. File Upload와 Directory Listing은 concept note로 분리하고, `Webshell.php` 업로드·실행 증거는 lab note에 둔다. Apache 차단 설정 런타임 검증은 lab note의 남은 확인으로 유지한다.
  - Completed scope: `5-20_웹보안.pdf` p.1-136 기준 source coverage 후보는 현재 한 바퀴 닫힘.

- [x] 시스템보안 전체 재시작 지점 점검
  - Start: [[10_학습 노트/시스템보안/00_시스템보안_목차]]
  - Risk: 웹보안과 네트워크보안의 다음 재시작 지점이 너무 넓거나 오래되면 AI가 RAW/PDF로 바로 뛰어들 수 있다.
  - 2026-07-02 loop result: 시스템보안 상위 MOC의 웹보안 재시작점을 source 근거가 있는 최소 후보로 풀어썼고, 네트워크보안 후보의 출발점을 Dynamic ARP Inspection으로 표시했다.
  - 2026-07-06 loop result: 네트워크보안 MOC에 DHCP Snooping / IP Source Guard, Wireshark 필터, MITM 실습 흐름의 실제 출발 노트를 추가했다. 독립 stable note가 아직 없는 항목은 source/lab 경계로 명시했다.
  - 2026-07-09 loop result: DHCP Snooping / IP Source Guard는 [[10_학습 노트/시스템보안/네트워크보안/Dynamic ARP Inspection|Dynamic ARP Inspection]] 안에서 관리하고, Wireshark 필터는 프로토콜별 lab/concept note에서 관리하는 것으로 판정했다. 새 stable note는 실제 장비 설정 실습, 장비별 명령 비교, 또는 반복 필터 누적이 생길 때만 만든다.
  - 2026-07-09 loop result: MITM 실습 흐름은 새 노트 없이 [[10_학습 노트/시스템보안/네트워크보안/00_네트워크보안_목차|네트워크보안 목차]]의 현재 재시작 지점에서 단계별 복구 경로로 연결했다.
  - 2026-07-09 loop result: frontmatter가 없던 시스템보안 content note 중 [[10_학습 노트/시스템보안/서론(이라쓰고 빠르게 휘갈겨 쓴거)|서론 raw 메모]]는 `type: raw`, [[10_학습 노트/시스템보안/네트워크보안/칼리리눅스|칼리리눅스]]는 `type: lab-support`로 분류했다.
  - Completed scope: 시스템보안 상위 MOC 기준 웹보안/네트워크보안의 현재 재시작 지점 오판 위험은 1차로 닫힘. 남은 metadata 후보는 content note가 아니라 MOC frontmatter 표본 통일이다.

- [ ] 클라우드/AWS 후속 정리 후보는 재사용 시점까지 보류
  - Start: [[10_학습 노트/클라우드/00_클라우드_목차]]
  - Current state: AWS기초는 완료/legacy, 공식 Arc는 현재진행 RAW/source.
  - Next check: 수업 종료 또는 재사용 시점에만 공식 Arc 안정 MOC 또는 source catalog 확장 여부를 결정한다.

## P2 - 프로젝트 오판 방지

- [x] AWS기초 완료 흐름과 공식 Arc 현재진행 흐름 분리
  - Evidence: [[10_학습 노트/클라우드/00_클라우드_목차]], [[10_학습 노트/클라우드/AWS/00_AWS_목차]], [[40_자료/강의 자료/AWS Arc/개요,목차]]
  - Current state: AWS기초는 완료/legacy 흐름, 공식 Arc는 현재진행 RAW/source 흐름으로 분리됨.
  - Remaining rule: 공식 Arc는 현재진행이므로 수업 종료 전 대공사하지 않는다.

- [x] 26. 4. 22 팀플 최종·구버전 스크립트 경계 추가 점검
  - Start: [[20_팀 프로젝트/26. 4. 22 팀플/00_팀플_목차]]
  - Current state: `webCompZzinFinal.sh`는 사용자 확인 기준 마지막 WEB 통합 스크립트이고, `web-comp_final.sh`와 5.9 계열은 이전 후보 또는 보존본이다.
  - Result: 복구 문서와 시크릿 문서의 존재하지 않는 `web.sh` / top-level `db.sh` 기준을 제거하고, DB/log/email 관련 구버전·테스트 스크립트는 현재 운영 기준으로 단정하지 않도록 표시했다.

- [ ] 26. 6. 8 팀플 결과·증거·RAW 경계 점검
  - Start: [[20_팀 프로젝트/26. 6. 8 팀플/00_팀플_목차]]
  - Evidence MOCs: [[20_팀 프로젝트/26. 6. 8 팀플/웹 서비스 보안 모음/00_웹서비스보안_목차]], [[20_팀 프로젝트/26. 6. 8 팀플/웹 앱 보안 모음/00_웹앱보안_목차]], [[20_팀 프로젝트/26. 6. 8 팀플/쉘 스크립트/00_쉘스크립트_목차]], [[20_팀 프로젝트/26. 6. 8 팀플/일일 로그/00_일일로그_목차]]
  - Risk: 후보표, 분류표, 보고서, dashboard, proof 파일, RAW 로그가 같은 위상처럼 보이면 최종 판단을 오판한다.
  - Next check: 최종 보고서와 evidence collector, proof 파일, RAW 로그가 MOC에서 충분히 분리되어 있는지 확인한다.

## P3 - 구조 품질과 토큰 절약

- [ ] `40_자료/` source catalog 과밀도 점검
  - Start: [[40_자료/00_자료_목차]]
  - Evidence: `40_자료/`가 444개로 가장 큰 영역이고, 이미지와 PDF가 많다.
  - Next check: PDF/source digest와 캡처 창고가 MOC에서 충분히 구분되는지 확인한다.

- [ ] `tmp/`와 루트 단독 파일 처리 기준 점검
  - Evidence: `tmp/` 50개, 루트 단독 `모듈 1 Coverage Map v0.1.md` 존재.
  - Next check: 실제 작업 중 필요한 임시 산출물인지, source digest에 흡수된 뒤 archive/ignore 후보인지 판단한다.
  - Boundary: 삭제·이동은 별도 승인 전까지 하지 않는다.

- [ ] frontmatter 표본 통일
  - Start: 핵심 MOC와 stable concept/lab 노트 표본
  - Risk: 전수 통일을 바로 하면 비용이 크다.
  - 2026-07-09 loop result: 시스템보안 content note 중 frontmatter가 없던 `서론 raw 메모`, `칼리리눅스`만 최소 metadata를 추가했다. MOC frontmatter는 아직 별도 표본 통일 후보로 남긴다.
  - Next check: `type`, `status`, `source`, `parent_moc`는 핵심 노트 몇 개에서만 표본 적용 후 확장 여부를 판단한다.

## P4 - 사람 눈에 보이는 정돈

- [ ] 템플릿 사용 예시 보강
  - Start: [[90_템플릿/00_템플릿_목차]]
  - Current state: P0 템플릿 구조 점검 이후, 사람 눈에 보이는 사용 예시를 보강할지 결정한다.

- [ ] 자격증 복습 경로 보강
  - Start: [[30_자격증/00_자격증_목차]]
  - Current state: 네트워크관리사와 오답노트 템플릿만 연결됨.
  - Next check: 보안 교육 vault 정비보다 우선순위는 낮다.

## Per-loop report template

각 루프가 끝나면 아래 형식으로 보고한다.

```text
이번 루프 범위:
확인한 파일과 근거:
바꾼 것:
안 바꾼 것:
오판 가능성 감소:
남은 위험 / 다음 후보:
검증 수준:
```

## Goal completion check

이 checklist 자체가 완료가 아니다.
최소 1차 완료로 보려면 다음이 현재 파일과 검증 출력으로 입증되어야 한다.

- P0 항목이 모두 처리되었거나, 현 상태에서 더 건드리면 현재진행 영역을 과하게 정리한다는 이유로 명시 보류되어 있다.
- 주요 P1 항목의 시작 MOC가 `RAW/source/stable/restart` 경계를 충분히 표시한다.
- 남은 P2/P3는 오판 위험이 낮은 개선 후보로 분류되어 있다.
- 마지막 전체 링크/표/diff 검증이 통과한다.
