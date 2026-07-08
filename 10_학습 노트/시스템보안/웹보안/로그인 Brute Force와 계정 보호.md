---
type: concept
topic: web-security
source:
  - 5-20_웹보안.pdf
  - OWASP Authentication Cheat Sheet
  - OWASP Credential Stuffing Prevention Cheat Sheet
  - NIST SP 800-63B
source_pages:
  - 77
  - 78
  - 79
status: active
created: 2026-07-08
reviewed: 2026-07-08
aliases:
  - ID/PW Brute Forcing
  - 로그인 Brute Force
  - Brute Force 방어
  - 계정 보호 대책
  - 로그인 시도 제한
tags:
  - 🏷️과목/웹보안
  - 🏷️주제/BruteForce
  - 🏷️주제/Authentication
  - 🏷️주제/AccountLockout
  - 🏷️상태/active
---

# 로그인 Brute Force와 계정 보호

source:

- [[40_자료/강의 자료/5-20_웹보안.pdf|5-20 웹보안]], p.77-79
- [OWASP Authentication Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html)
- [OWASP Credential Stuffing Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Credential_Stuffing_Prevention_Cheat_Sheet.html)
- [NIST SP 800-63B](https://pages.nist.gov/800-63-4/sp800-63b.html)

## 한 줄 요약

로그인 Brute Force는 ID/PW 조합을 반복 시도하고 실패/성공 응답 차이로 유효한 계정을 판별하는 공격이다. 방어의 핵심은 실패 메시지 정보 노출을 줄이고, 서버가 계정 기준 실패 횟수와 속도를 기억하며, 지연·잠금·MFA·모니터링을 조합하는 것이다.

---

## PDF p.77-79 구조

| 범위 | 주제 | 핵심 판단 |
|---|---|---|
| p.77 | ID/PW Brute Forcing | ID와 password 조합을 반복 입력하고, 실패/성공 응답 차이로 유효성을 판별한다. |
| p.78 | Hydra 실습 | `hydra`는 반복 로그인 시도를 자동화하는 실습 도구다. 도구 자체보다 요청 구조와 판별 문자열 이해가 중요하다. |
| p.79 | 대응책 | 실패 메시지 제한, 계정 잠금, 로그인 지연, IP 기반 동시접속 제어를 다룬다. |

이 범위는 공격 도구 사용법을 외우는 단원이 아니라, 로그인 시도 자동화가 왜 가능한지와 서버가 무엇을 기억해야 하는지를 정리하는 단원이다.

---

## 공격 구조

로그인 Brute Force는 보통 다음 조건이 맞을 때 잘 작동한다.

| 조건 | 의미 |
|---|---|
| 반복 요청 가능 | 서버가 같은 ID 또는 같은 출발지의 로그인 시도를 충분히 제한하지 않는다. |
| 실패/성공 구분 가능 | 실패 응답과 성공 응답의 문자열, redirect, status, body 차이가 뚜렷하다. |
| 후보 생성 또는 사전 사용 가능 | password 후보를 규칙으로 만들거나 dictionary file에서 읽을 수 있다. |
| 서버 상태 추적 부족 | 실패 횟수, 잠금 시간, 요청 속도, IP/device 신호를 서버가 충분히 기록하지 않는다. |

실습에서는 [[Hydra 로그인 Brute Force 실습]]이 이 구조를 보여준다. Hydra 명령은 핵심이 아니라, `어떤 URL에 어떤 form field를 보내고 어떤 응답 문자열로 실패/성공을 판별하는가`가 핵심이다.

---

## 방어 기준

| 방어 축 | 목적 | 주의점 |
|---|---|---|
| 실패 메시지 일반화 | 계정 존재 여부와 password 오류 여부를 분리해서 알려주지 않는다. | UX는 조금 나빠질 수 있지만 계정 enumeration을 줄인다. |
| 계정 기준 시도 제한 | 특정 계정에 대한 연속 실패를 서버가 기억한다. | IP만 기준으로 잡으면 분산 요청에 약하고, 계정만 기준으로 잡으면 잠금 DoS 위험이 있다. |
| 지연 또는 단계적 lockout | 반복 실패가 누적될수록 다음 시도를 늦추거나 잠근다. | 고정 lockout만 쓰면 공격자가 다른 사용자의 계정을 잠그는 DoS로 악용할 수 있다. |
| IP/device/risk 신호 | 출발지, device, 지리 정보, 요청 패턴을 함께 본다. | NAT/공용망에서는 정상 사용자를 같이 막을 수 있으므로 단독 기준으로 과신하지 않는다. |
| MFA | password가 맞아도 추가 인증을 요구한다. | Brute Force와 credential stuffing의 피해를 줄이는 강한 보강책이다. |
| 로그와 알림 | 반복 실패, lockout, 비정상 패턴을 추적한다. | 방어가 작동했는지 확인하려면 로그/DB 상태 증거가 필요하다. |

OWASP Authentication Cheat Sheet는 automated attack 방어로 MFA, login throttling, account lockout 등을 제시한다. NIST SP 800-63B도 온라인 추측 공격을 막기 위해 실패 인증 시도에 rate limiting을 적용해야 한다고 설명한다.

---

## 이 vault에서 쓰는 법

이 노트는 방어 기준을 빠르게 복구하기 위한 stable concept note다.

```text
로그인 반복 시도/계정 보호 개념이 가물가물함
-> 이 노트에서 실패 메시지, lockout, throttling, MFA 기준 확인
-> [[Hydra 로그인 Brute Force 실습]]에서 실제 Hydra 명령, Paros 관찰, DB 기반 방어 시행착오 확인
-> [[기초 웹 인증 방식 - Basic, Anonymous, Form]], [[세션과 쿠키]], [[OWASP Top 10 2025]]와 연결
```

역할 구분:

| 파일 | 역할 |
|---|---|
| 이 노트 | p.77-79의 개념과 방어 기준을 짧게 회상한다. |
| [[Hydra 로그인 Brute Force 실습]] | Hydra 명령 구조, 실행 결과, 계정 잠금 구현 시행착오, 강사님 코드 비교를 보존한다. |
| [[OWASP Top 10 2025]] | A07 Authentication Failures 관점에서 어디에 속하는지 확인한다. |

---

## 실습용 구현과 실무형 구현의 차이

실습에서는 짧은 숫자 password, 실습 서버, 단순 응답 문자열, Hydra를 사용한다. 이것은 구조를 보기 위한 환경이다.

실무형 구현에서는 최소한 아래가 함께 필요하다.

- password hash 저장과 안전한 비교
- SQL Injection 방지를 위한 parameterized query
- TLS
- 서버 측 rate limiting과 lockout 상태 저장
- MFA
- 로그/알림
- 계정 잠금이 DoS로 악용되지 않도록 복구 흐름 설계

따라서 `계정 잠금` 하나만으로 로그인 보안이 끝났다고 보면 안 된다.

---

## 근거 요약

| 근거 | 이 노트에서 사용한 판단 |
|---|---|
| PDF p.77 | Brute Force는 ID/PW 조합 반복과 실패/성공 응답 차이를 이용한다. |
| PDF p.78 | Hydra는 HTTP form 기반 반복 로그인을 자동화하는 실습 도구다. |
| PDF p.79 | 실패 메시지 제한, 계정 잠금, 로그인 지연, IP 기반 동시접속 제어를 대응책으로 둔다. |
| OWASP Authentication Cheat Sheet | automated attack 방어에는 login throttling, account lockout, CAPTCHA, MFA 등이 포함된다. |
| OWASP Credential Stuffing Prevention Cheat Sheet | IP 기반 제한만으로는 proxy/distributed 요청에 우회될 수 있으므로 추가 신호와 단계적 대응이 필요하다. |
| NIST SP 800-63B | 온라인 추측 공격 방어를 위해 실패 인증 시도에 rate limiting을 적용해야 한다. |
| [[Hydra 로그인 Brute Force 실습]] | 실습 환경에서 Hydra 명령, 실패 판별 문자열, DB 기반 실패 횟수 저장, 강사님 코드 비교를 보존한다. |

---

## 확인 질문

1. Hydra가 로그인 성공/실패를 구분하려면 어떤 응답 차이가 필요했는가?
2. 실패 메시지를 `ID 또는 비밀번호가 맞지 않습니다`처럼 일반화하는 이유는 무엇인가?
3. 세션 기반 실패 횟수 제한이 Brute Force 방어로 약한 이유는 무엇인가?
4. 계정 기준 lockout과 IP 기준 rate limiting은 각각 어떤 장단점이 있는가?
5. 계정 잠금 정책이 오히려 DoS가 될 수 있는 경우는 언제인가?
