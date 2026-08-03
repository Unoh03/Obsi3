# RAW 메모

<!-- 2026-08-03 11:14까지 일일 로그 반영 완료 -->

### 11:33

- 후순위: Daily 자동화 Script를 손으로 실행하고 Code를 읽으며 동작 원리를 이해한다.
- Application: 은행 Application을 겉에 만들고 DVWA의 취약점 Engine을 내부 부품으로 재조립해 은행다운 화면과 흐름을 구현한다.
- 관측성 문제: Log 수집은 작동하지만 사람이 실시간으로 읽고 해석하는 과정이 어렵다. 보기·검색·판정 방식을 보완해야 한다.

### 19:15

- Phase 0: Daily State 317개와 Foundation State 27개를 확인했다. 현재 Primary·DR EKS/RDS/NAT, 양쪽 Valkey·EFS가 실행 중인 `full` 상태다.
- 수명주기: 기존 Public Hosted Zone은 존재하지만 Global ACM Certificate와 GuardDuty Detector는 없으며, Domain·ACM은 현재 Daily State에도 없다.
- 관제 Review: Windows PowerShell 5.1이 UTF-8 BOM 없는 한글 Module을 해석하지 못한 Parser 오류를 BOM 보정으로 해결했다. 관련 정적 Test 6개와 Secret 서명 검사 통과.
- Git: 관제 시간창 Review 작업을 `5c14d1b`로 Commit하고 `origin/main`에 Push했다.
- Daily Down: 사용자 승인 `DESTROY DAILY`로 Full Runtime 제거를 시작했으며 진행 중이다.

### 19:48

- Daily Down 완료: 250개 제거, Daily State 0, 추적·Tag 기준 Daily 잔존 0. Foundation ECR·OIDC/IAM·보안 로그 보존 계층과 30일 Retention은 유지됐다.
- Evidence: Post-Destroy Bundle에서 CloudTrail 59개, CloudFront 1개, ALB 1개, VPC REJECT 21개, EKS 42,297개, DVWA 628개 Event를 수집했다. WAF·DR Application은 해당 시간창 0건으로 기록됐다.
- 정적 구현: `minimal / dr-test / full` Runtime Profile, Valkey·EFS Opt-in, HTTPS Redirect 안전 기본값과 HTTP 실험 Toggle, Watchdog On/Off를 추가했다.
- 수명주기: 기존 Route 53 Hosted Zone은 Foundation에서 조회하고 CloudFront ACM·DNS 검증을 Foundation이 소유하도록 분리했다. Foundation v2 출력이 없으면 Daily Up이 중단되도록 보강했다.
- 검증: `minimal` Plan 117개 생성에서 DR·Valkey·EFS·복제 0건, `dr-test` Plan 232개 생성에서 Valkey·EFS 0건을 확인했다. Foundation `unoh.click` Plan은 ACM·검증 Record 3개 생성, 변경·삭제 0이며 아직 Apply하지 않았다.
- 회귀 검사: Daily/Foundation `terraform validate`, Runtime·Watchdog·Daily 자동화·관측성 관련 Test와 `git diff --check`를 통과했다.
