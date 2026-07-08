---
type: concept
topic: web-security
source:
  - 5-20_웹보안.pdf
  - OWASP Top 10:2025
source_pages:
  - 62
  - 63
  - 64
  - 65
  - 66
  - 67
  - 68
  - 69
  - 70
  - 71
  - 72
status: active
created: 2026-07-07
reviewed: 2026-07-07
aliases:
  - OWASP Top 10
  - OWASP TOP 10
  - OWASP Top 10:2025
  - 웹 애플리케이션 보안 위험 Top 10
tags:
  - 🏷️과목/웹보안
  - 🏷️주제/OWASP
  - 🏷️주제/취약점분류
  - 🏷️상태/active
---

# OWASP Top 10 2025

source:

- [[40_자료/강의 자료/5-20_웹보안.pdf|5-20 웹보안]], p.62-72
- [OWASP Top 10:2025](https://owasp.org/Top10/2025/)

## 한 줄 요약

OWASP Top 10은 웹 애플리케이션에서 자주 중요하게 다뤄야 하는 보안 위험을 묶은 awareness 문서다. 2025 목록은 “취약점 이름 10개 외우기”보다, 앱을 볼 때 어떤 질문을 던져야 하는지 정리하는 기준으로 쓰는 편이 맞다.

이 노트에서는 PDF p.62-72의 강의식 진단 질문을 OWASP 공식 2025 목록과 맞춰 둔다. 공식 영문명은 OWASP를 기준으로 하고, PDF 표현은 수업용 해석으로 본다.

---

## 공식 2025 목록과 진단 질문

| 순위 | 공식 항목 | 수업식 진단 질문 | vault 연결 |
|---|---|---|---|
| A01 | Broken Access Control | 이 기능을 이 사용자가 해도 되는가? | [[CSRF]], [[Web Session Hijacking]] |
| A02 | Security Misconfiguration | 개발·운영 기본값이 그대로 남아 있는가? | [[Directory Listing 취약점]], [[웹보안 LAMP 실습 환경 구축]] |
| A03 | Software Supply Chain Failures | 이 앱은 남의 코드·빌드·배포 체인 위에 서 있는가? | 후속 정리 후보 |
| A04 | Cryptographic Failures | 민감 정보가 보호되고 있는가, 보관만 되고 있는가? | [[HTTP 로그인 평문 노출]], [[기초 웹 인증 방식 - Basic, Anonymous, Form]] |
| A05 | Injection | 입력이 데이터로 끝나는가, 명령이 되는가? | [[SQL Injection 개념과 인증 우회]], [[SQL Injection 방어]], [[XSS]] |
| A06 | Insecure Design | 시스템이 공격을 전제로 설계되었는가? | 후속 정리 후보 |
| A07 | Authentication Failures | 시스템은 누가 누구인지 끝까지 확인하는가? | [[기초 웹 인증 방식 - Basic, Anonymous, Form]], [[세션과 쿠키]], [[Hydra 로그인 Brute Force 실습]] |
| A08 | Software or Data Integrity Failures | 변조되면 알 수 있는가? | 후속 정리 후보 |
| A09 | Security Logging and Alerting Failures | 공격이 발생했을 때 확인하고 알림을 받을 수 있는가? | 후속 정리 후보 |
| A10 | Mishandling of Exceptional Conditions | 정상 입력이 아닐 때 시스템은 어떻게 반응하는가? | 후속 정리 후보 |

PDF와 공식 문서의 표현 차이:

- PDF p.70은 `Software & Data Integrity Failures`라고 쓰지만, 공식명은 `Software or Data Integrity Failures`다.
- PDF p.71은 `Logging & Alerting Failures`라고 줄여 쓰지만, 공식명은 `Security Logging and Alerting Failures`다.
- PDF p.72의 A10은 2025 신규 항목으로 소개된다.

---

## 2025에서 특히 봐야 할 변화

OWASP 공식 Introduction은 2025판에 새 범주 2개와 통합 1개가 있다고 설명한다.

| 변화 | 의미 |
|---|---|
| A03 Software Supply Chain Failures | 2021의 `Vulnerable and Outdated Components`보다 넓다. 라이브러리 취약점뿐 아니라 build, distribution, CI/CD, third-party trust까지 본다. |
| A10 Mishandling of Exceptional Conditions | 2025 신규 항목이다. 에러 처리, 비정상 흐름, fail-open, 논리 오류를 별도 위험으로 본다. |
| SSRF가 A01 Broken Access Control 쪽으로 흡수됨 | 접근 통제 실패 범위를 단순 URL/권한 체크보다 넓게 봐야 한다. |
| A02 Security Misconfiguration 상승 | 설정 기반 동작이 늘면서 기본값, 디버그, 불필요 포트/서비스 같은 운영 설정 위험이 더 중요해졌다. |

이 변화 때문에 오래된 `OWASP Top 10 2021` 표를 그대로 현재 기준처럼 쓰면 오판한다.

---

## 수업 메모 흡수

raw 메모에는 “1, 3, 5, 7, 8, 10은 우리가 인지해야 하는 문제”라고 남아 있다. 이 문장은 공식 순위 변경이 아니라 수업에서 특히 의식하라는 표시로 보는 편이 안전하다.

해석:

- A01은 권한과 리소스 접근을 확인하는 기본 질문이다.
- A03은 현대 앱이 외부 라이브러리, build pipeline, 배포 인프라 위에서 동작하기 때문에 중요하다.
- A05는 SQL Injection, command injection, XSS 같은 기존 웹보안 실습과 직접 연결된다.
- A07은 로그인, 세션, token 재사용, brute force와 연결된다.
- A08은 software artifact와 data가 변조됐는지 확인하는 문제다.
- A10은 에러와 예외 흐름에서 정보 노출이나 인증 우회가 생기는지 보는 문제다.

---

## 이 vault에서 쓰는 법

OWASP Top 10은 세부 실습 노트를 대체하지 않는다. 이 노트는 “어느 위험 범주로 생각할지”를 정하는 지도다.

실제로 복습할 때는 이렇게 쓴다.

```text
증상 또는 실습 발견
-> OWASP Top 10 범주로 분류
-> 관련 stable concept note 확인
-> 필요하면 lab note 또는 source note로 내려감
```

예:

- 로그인 시도 제한이 없다면 A07 Authentication Failures로 보고 [[Hydra 로그인 Brute Force 실습]]과 [[세션과 쿠키]]를 본다.
- `id=2` 같은 값만 바꿔 다른 사용자의 리소스에 접근한다면 A01 Broken Access Control로 본다.
- SQL payload가 명령으로 해석되면 A05 Injection으로 보고 [[SQL Injection 개념과 인증 우회]]와 [[SQL Injection 방어]]를 본다.
- 디버그 모드와 stack trace가 노출되면 A02 Security Misconfiguration 또는 A10 Mishandling of Exceptional Conditions를 함께 의심한다.

---

## 오해하기 쉬운 지점

| 오해 | 정정 |
|---|---|
| OWASP Top 10은 취약점 10개 목록이다 | 정확히는 여러 CWE와 위험을 묶은 awareness category다. |
| 순위가 낮으면 덜 중요하다 | 앱의 구조와 노출면에 따라 낮은 순위 항목이 더 치명적일 수 있다. |
| PDF 표만 보면 최신 기준을 알 수 있다 | PDF는 강의용 요약이다. 최신 기준은 작성 시점의 OWASP 공식 문서로 확인한다. |
| A03은 라이브러리 버전만 보면 된다 | 2025 기준 A03은 supply chain 전체, 즉 dependency, build, distribution, CI/CD, third-party trust를 포함한다. |
| A10은 단순 에러 메시지 숨기기다 | 예외 흐름에서 fail-open, 인증 우회, 내부 상태 노출이 생기는지까지 본다. |

---

## 근거 요약

| 근거 | 이 노트에서 사용한 판단 |
|---|---|
| PDF p.62-72 | 강의 자료는 2025 항목별 진단 질문을 한 페이지씩 요약한다. |
| OWASP Top 10:2025 Home | 2025 공식 목록과 공식 영문명 기준이다. |
| OWASP Top 10:2025 Introduction | 2025판의 변경점과 방법론을 확인하는 기준이다. |
| raw 메모 p.62 | 수업 중 추가로 참고하라고 남긴 OWASP Seoul 자료 URL과 강조 항목을 보존한다. |

---

## 확인 질문

1. OWASP Top 10은 scanner rule 목록인가, awareness category인가?
2. A01 Broken Access Control을 볼 때 “이 사용자가 이 기능을 해도 되는가?”라는 질문이 왜 중요한가?
3. A03 Software Supply Chain Failures가 단순 “오래된 라이브러리”보다 넓은 이유는 무엇인가?
4. A05 Injection과 기존 SQL Injection/XSS 노트는 어떻게 연결되는가?
5. A07 Authentication Failures와 세션/쿠키/Brute Force 실습은 어떻게 연결되는가?
6. A10 Mishandling of Exceptional Conditions가 단순 에러 페이지 문제가 아닌 이유는 무엇인가?
