---
type: concept
topic: web-security
source:
  - 5-20_웹보안.pdf
  - OWASP SQL Injection Prevention Cheat Sheet
  - OWASP Query Parameterization Cheat Sheet
source_pages:
  - 132
status: active
created: 2026-07-06
aliases:
  - SQLi 방어
  - SQL Injection Prevention
  - Prepared Statement
  - Parameterized Query
tags:
  - 🏷️과목/웹보안
  - 🏷️주제/SQL
  - 🏷️주제/SQLInjection
  - 🏷️주제/Secure-Coding
  - 🏷️상태/active
---

# SQL Injection 방어

source:
- [[40_자료/강의 자료/5-20_웹보안.pdf|5-20 웹보안]], p.132
- [OWASP SQL Injection Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/SQL_Injection_Prevention_Cheat_Sheet.html)
- [OWASP Query Parameterization Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Query_Parameterization_Cheat_Sheet.html)

## 한 줄 요약

SQL Injection 방어의 중심은 **사용자 입력을 SQL 문자열에 붙이지 않고, SQL 구조와 입력 데이터를 분리하는 것**이다.

PDF p.132는 서버 측 검증, 위험 문자·키워드 필터링, 에러 메시지 제한, WAF를 대응책으로 제시한다. 이 내용은 보존하되, 최종 정리에서는 `Prepared Statement / Parameterized Query`를 1차 방어로 둔다.

---

## 먼저 잡아야 할 핵심

- Client-side validation은 우회될 수 있으므로 방어 기준점이 아니다.
- 서버는 사용자의 입력값을 다시 검증해야 한다.
- 하지만 검증과 필터링만으로 SQL Injection을 막는다고 보면 부족하다.
- 1차 방어는 SQL 문장 구조와 사용자 입력 데이터를 분리하는 `Prepared Statement / Parameterized Query`다.
- 위험 문자나 SQL 키워드 blocklist는 우회 가능성과 정상 입력 파손 위험이 있어 보조 방어로 본다.
- 에러 메시지 제한은 error-based SQL Injection의 정보 노출을 줄인다.
- WAF는 알려진 패턴 차단과 임시 완화에 도움을 줄 수 있지만, 취약한 애플리케이션 쿼리 코드를 대신 고쳐주지는 않는다.
- DB 계정 권한 최소화는 공격 성공 시 피해 범위를 줄이는 방어 심층화다.

---

## 취약한 구조

SQL Injection은 사용자가 값을 입력했다는 사실 때문에 생기는 것이 아니다. 서버가 그 값을 SQL 문자열 안에 그대로 이어 붙여, 입력값이 SQL 구문 구조를 바꿀 수 있게 만들 때 생긴다.

```text
사용자 입력
-> 서버가 입력값을 문자열로 이어 붙여 SQL 생성
-> 입력값 일부가 SQL 문법으로 해석됨
-> DB가 서버 의도와 다른 Query를 실행
```

위험한 생각은 다음과 같다.

```text
SELECT ... WHERE id = '사용자입력'
```

이 구조에서 서버가 `사용자입력`을 단순 문자열 데이터로 고정하지 못하면, 입력값이 조건식, 주석, 함수 호출, UNION 같은 SQL 구조에 영향을 줄 수 있다.

---

## 1차 방어 - Prepared Statement / Parameterized Query

`Prepared Statement / Parameterized Query`는 SQL 구조를 먼저 정하고, 사용자 입력은 나중에 값으로 바인딩하는 방식이다.

```text
SQL 구조: SELECT ... WHERE id = ?
입력 데이터: 사용자가 입력한 id 값
```

핵심은 `?`, `:name`, `@id` 같은 placeholder 자체가 아니라, DB 드라이버가 **SQL 코드와 입력 데이터를 분리해서 전달**한다는 점이다.

이 방식에서는 사용자 입력에 SQL처럼 보이는 문자가 들어와도 DB는 그것을 SQL 명령으로 실행하지 않고 값으로 취급해야 한다.

### 판단 기준

| 질문 | 안전한 방향 |
|---|---|
| 사용자 입력이 SQL 문자열에 직접 이어 붙는가? | 이어 붙이지 않는다. |
| SQL 구조가 입력값에 의해 바뀔 수 있는가? | 구조는 코드에서 고정한다. |
| 입력값은 어디에 들어가는가? | placeholder에 bind parameter로 들어간다. |
| INSERT, UPDATE, DELETE도 해당하는가? | 모두 해당한다. 조회뿐 아니라 모든 SQL에 적용한다. |

---

## 서버 측 입력 검증의 역할

입력 검증은 여전히 필요하다. 다만 역할을 정확히 나눠야 한다.

| 검증 대상 | 예시 | 역할 |
|---|---|---|
| 타입 | 숫자 ID, 날짜, boolean | 애플리케이션이 기대한 데이터 형태인지 확인 |
| 길이 | ID 길이, 검색어 길이 | 비정상적으로 긴 입력 제한 |
| 형식 | 이메일, 계정명, UUID | 업무 규칙 위반 입력 차단 |
| allowlist | 정렬 방향 `ASC/DESC`, 허용된 컬럼명 | bind parameter를 쓸 수 없는 SQL 식별자 선택 제한 |

서버 측 입력 검증은 “이 값이 애플리케이션 규칙에 맞는가”를 보는 방어다. 반면 parameterized query는 “이 값이 SQL 구조로 해석되지 않게 하는가”를 보장하는 방어다.

따라서 둘 중 하나를 고르는 문제가 아니다.

```text
서버 측 입력 검증
+ Prepared Statement / Parameterized Query
= 더 안전한 기본 구조
```

---

## 필터링과 escaping의 한계

PDF p.132에는 SQL Injection에 사용되는 문자와 키워드를 필터링하는 대응책이 나온다. 예를 들면 따옴표, 주석 기호, `select`, `union`, `drop` 같은 문자열을 막는 방식이다.

이 방식은 초급 실습에서 방어 사고를 시작하는 데는 도움이 된다. 하지만 실무 1차 방어로 두면 위험하다.

| 방식 | 문제 |
|---|---|
| 위험 문자 blocklist | 인코딩, DBMS 차이, 우회 표현 때문에 놓칠 수 있다. |
| SQL 키워드 blocklist | 정상 입력을 깨뜨릴 수 있고, 모든 문맥을 다 막기 어렵다. |
| escaping만 의존 | DBMS와 문자셋, 드라이버 동작에 영향을 많이 받는다. |

따라서 필터링은 “SQL과 데이터를 분리하지 못하는 구조를 보완하는 핵심 방어”가 아니라, **보조 방어 또는 과도기적 완화책**으로 보는 것이 맞다.

---

## 에러 메시지 제한

Error-based SQL Injection은 DB 에러가 사용자 화면에 그대로 노출될 때 더 쉽게 진행된다.

방어 방향은 다음과 같다.

- 사용자에게는 일반적인 오류 메시지만 보여준다.
- DB 에러, SQL 문장, 테이블명, 컬럼명, stack trace는 화면에 노출하지 않는다.
- 상세 에러는 서버 로그에 남기되, 접근 권한과 보관 정책을 관리한다.

에러 메시지 제한은 SQL Injection 자체를 막는 1차 방어가 아니다. 하지만 공격자가 schema, DB명, table명, column명을 추정하는 속도를 줄인다.

---

## WAF의 위치

WAF는 SQL Injection 패턴을 탐지하거나 알려진 공격 요청을 차단하는 데 도움을 줄 수 있다.

하지만 WAF는 다음을 대신하지 않는다.

- 취약한 SQL 문자열 결합 제거
- prepared statement 적용
- 서버 측 입력 검증
- DB 계정 권한 최소화
- 안전한 에러 처리

정리하면 WAF는 방어 심층화 계층이지, 애플리케이션 코드의 SQL Injection 취약점을 고치는 대체재가 아니다.

---

## DB 권한 최소화

SQL Injection이 완전히 막히지 않았을 때를 대비해 DB 권한도 줄여야 한다.

예를 들어 로그인 조회만 하는 기능에는 필요한 테이블의 필요한 컬럼을 읽을 권한만 주는 편이 낫다. 애플리케이션 계정에 DBA나 관리자 권한을 주면, SQL Injection이 한 번 성공했을 때 피해 범위가 커진다.

권한 최소화는 취약점을 없애는 방어가 아니라, 실패했을 때 피해를 줄이는 방어다.

---

## 방어 계층 정리

| 계층 | 역할 | 주의 |
|---|---|---|
| Prepared Statement / Parameterized Query | SQL 구조와 입력 데이터 분리 | SQLi 1차 방어로 둔다. |
| 서버 측 입력 검증 | 타입, 길이, 형식, 업무 규칙 확인 | 단독 SQLi 방어로 보지 않는다. |
| Allowlist | 컬럼명, 정렬 방향처럼 bind가 어려운 선택지 제한 | 사용자가 임의 식별자를 고르게 하지 않는다. |
| 에러 메시지 제한 | 내부 DB 정보 노출 감소 | 취약한 쿼리 구조 자체를 고치지는 않는다. |
| DB 권한 최소화 | 공격 성공 시 피해 범위 제한 | 예방보다 피해 제한에 가깝다. |
| WAF | 알려진 공격 패턴 차단, 임시 완화 | 코드 수정의 대체재가 아니다. |
| 문자·키워드 필터링 | 보조 완화 또는 실습용 방어 | 우회와 정상 입력 파손 위험이 있다. |

---

## 수업 표현을 정확한 개념으로 바꾸기

| 수업/PDF 표현 | 이 노트에서의 정리 |
|---|---|
| Client Side Script로 제한할 수 있으나 우회 가능 | 클라이언트는 신뢰 경계가 아니다. 서버에서 다시 검증해야 한다. |
| SQL Injection 문자를 필터링한다 | blocklist 필터링은 보조 방어다. 1차 방어는 parameterized query다. |
| 에러 메시지를 제한한다 | error-based 정보 노출을 줄이는 보조 방어다. |
| Web 방화벽을 사용한다 | WAF는 defense-in-depth 계층이다. 취약한 쿼리 코드를 대체하지 않는다. |

---

## 오해하기 쉬운 지점

- “따옴표만 막으면 된다”가 아니다. SQL Injection은 쿼리 구조 조작 문제다.
- “필터링을 빡세게 하면 된다”가 아니다. 모든 DBMS, 인코딩, SQL 문맥을 blocklist로 안전하게 덮기 어렵다.
- “Client-side validation이 있으니 괜찮다”가 아니다. 브라우저 제한은 프록시, 개발자 도구, 직접 요청으로 우회될 수 있다.
- “WAF가 있으니 코드는 안 고쳐도 된다”가 아니다. WAF는 보조 방어다.
- “SELECT만 조심하면 된다”가 아니다. `INSERT`, `UPDATE`, `DELETE`, stored procedure 내부 dynamic SQL도 입력값을 안전하게 다뤄야 한다.

---

## 관련 노트

- [[10_학습 노트/시스템보안/웹보안/SQL Injection을 위한 SQL 기초|SQL Injection을 위한 SQL 기초]]
- [[10_학습 노트/시스템보안/웹보안/SQL Injection 개념과 인증 우회|SQL Injection 개념과 인증 우회]]
- [[10_학습 노트/시스템보안/웹보안/SQL Injection Error와 UNION 기반 정보 추출과 Schema 파악|SQL Injection Error와 UNION 기반 정보 추출과 Schema 파악]]
- [[10_학습 노트/시스템보안/웹보안/SQL Injection 인증 우회 실습|SQL Injection 인증 우회 실습]]
- [[10_학습 노트/시스템보안/웹보안/SQL Injection Error 기반 DB명 정보 추출 실습|SQL Injection Error 기반 정보 추출 실습]]
- [[10_학습 노트/시스템보안/웹보안/Client-side Validation 우회와 Server-side Validation 실습|Client-side Validation 우회와 Server-side Validation 실습]]
- [[10_학습 노트/시스템보안/웹보안/웹 애플리케이션 구조|웹 애플리케이션 구조]]

---

## 확인 질문

- SQL Injection의 원인은 “나쁜 문자를 입력했다”인가, “입력값이 SQL 구조로 해석될 수 있는 쿼리 생성 방식”인가?
- Prepared Statement는 왜 위험 문자를 지우는 방식보다 근본적인가?
- 서버 측 입력 검증과 parameterized query는 각각 무엇을 담당하는가?
- 에러 메시지 제한은 SQL Injection 예방인가, 정보 노출 완화인가?
- WAF가 있어도 애플리케이션 쿼리 코드를 고쳐야 하는 이유는 무엇인가?

---

## 공식 보강 근거

| Source | Freshness | Reliability | Finding used |
|---|---|---|---|
| OWASP SQL Injection Prevention Cheat Sheet | Current checked, Date absent | Official OWASP cheat sheet | Prepared Statements / Parameterized Queries를 1차 방어로 두고, allow-list validation과 least privilege를 보조 방어로 설명한다. |
| OWASP Query Parameterization Cheat Sheet | Current checked, Date absent | Official OWASP cheat sheet | 여러 언어와 stored procedure에서 bind variable / parameterization으로 입력을 데이터로 취급하게 하는 예시를 제시한다. |
