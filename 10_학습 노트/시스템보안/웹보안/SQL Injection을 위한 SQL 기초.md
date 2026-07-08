---
type: concept
topic: web-security
source: 5-20_웹보안.pdf
source_pages:
  - 107
  - 108
  - 109
  - 110
  - 111
  - 112
  - 113
  - 114
status: active
created: 2026-05-28
reviewed: 2026-07-08
aliases:
  - SQL 기초
  - SQL Basics for SQL Injection
tags:
  - 🏷️과목/웹보안
  - 🏷️주제/SQL
  - 🏷️주제/SQLInjection
  - 🏷️상태/active
---

# SQL Injection을 위한 SQL 기초

source: [[40_자료/강의 자료/5-20_웹보안.pdf|5-20 웹보안]], p.107-114

## 한 줄 요약

SQL Injection을 이해하려면 SQL 전체를 깊게 배울 필요보다, **웹 애플리케이션이 사용자 입력으로 SQL을 만들고 DB가 그 SQL을 실행한다**는 흐름을 먼저 잡아야 한다.

이 노트는 SQL 일반론이 아니라, 뒤의 [[10_학습 노트/시스템보안/웹보안/SQL Injection 개념과 인증 우회|SQL Injection 개념과 인증 우회]]를 이해하는 데 필요한 SQL 문법만 정리한다.

---

## 먼저 잡아야 할 핵심

- SQL은 Database에 명령을 내리는 언어다.
- 웹 애플리케이션은 로그인, 검색, 게시글 조회 같은 기능에서 SQL을 만들어 DB에 보낸다.
- SQL Injection에서 가장 먼저 중요한 문법은 `SELECT`, `WHERE`, `UNION`이다.
- `INSERT`, `UPDATE`, `DELETE`는 SQL Injection의 영향이 조회를 넘어 데이터 추가, 수정, 삭제로 확장될 수 있음을 이해하는 데 필요하다.
- 집계함수와 `GROUP BY / HAVING`은 SQLi 초반 핵심은 아니지만, PDF에 포함된 SQL 조회 문법이므로 짧게 알아둔다.

---

## SQL의 역할

SQL은 `Structured Query Language`의 약자로, Database를 다루기 위한 언어다.

| 분류 | 의미 | 예시 |
|---|---|---|
| `DDL` | 데이터 정의어 | 테이블 생성, 구조 변경 |
| `DML` | 데이터 조작어 | 조회, 추가, 수정, 삭제 |
| `DCL` | 데이터 제어어 | 권한 제어 |

SQL Injection 실습에서는 주로 `DML`, 특히 `SELECT`가 먼저 중요하다. 하지만 SQL Injection의 영향은 조회에만 머물지 않을 수 있으므로 `INSERT`, `UPDATE`, `DELETE`도 기본 의미는 알아야 한다.

---

## SELECT와 WHERE

`SELECT`는 DB에서 데이터를 조회하는 명령이다.

```sql
SELECT <필드명> FROM <테이블명> WHERE <조건>
```

의미는 다음과 같다.

- `<테이블명>`에서 데이터를 찾는다.
- `WHERE <조건>`에 맞는 레코드만 고른다.
- 그중 `<필드명>`에 해당하는 값만 출력한다.

PDF 예시:

```sql
SELECT * FROM member WHERE name='이명수'
```

여기서 `*`는 모든 필드를 뜻한다. 실습에서는 편하지만, 실무에서는 보통 필요한 필드만 조회하는 편이 낫다.

SQL Injection에서 `WHERE`가 중요한 이유는 로그인 쿼리가 보통 이런 형태를 갖기 때문이다.

```sql
SELECT * FROM member WHERE id='입력값' AND pw='입력값'
```

서버가 사용자 입력을 그대로 `WHERE` 조건 안에 넣으면, 입력값이 단순 데이터가 아니라 SQL 조건식으로 해석될 수 있다.

---

## 조회 결과와 집계함수

집계함수는 여러 레코드를 대상으로 계산 결과를 만든다.

```sql
SELECT 집단함수(<필드명>) FROM <테이블명>
```

| 함수 | 의미 | SQLi 이해에서의 비중 |
|---|---|---|
| `COUNT` | 반환 레코드의 개수 | 중간. 레코드 존재 여부를 이해하는 데 도움이 됨 |
| `SUM` | 값의 합계 | 낮음 |
| `AVG` | 값의 평균 | 낮음 |
| `MAX` | 값의 최대값 | 낮음 |
| `MIN` | 값의 최소값 | 낮음 |

PDF 예시:

```sql
SELECT COUNT(*) FROM member
```

`COUNT(*)`는 조건에 맞는 행이 몇 개인지 세는 대표적인 형태다. 로그인 로직이 꼭 `COUNT(*)`를 쓰지 않더라도, 내부 판단은 결국 “조건에 맞는 사용자 레코드가 존재하는가”와 연결된다.

---

## GROUP BY와 HAVING

`GROUP BY`는 같은 값을 가진 레코드를 그룹으로 묶고, `HAVING`은 그룹화된 결과에 조건을 거는 문법이다.

```sql
SELECT 집단함수(<필드명>) FROM <테이블명>
GROUP BY <필드명> HAVING <조건>
```

PDF 예시:

```sql
SELECT age, count(age) FROM member GROUP BY age HAVING age<=30
```

`WHERE`와 `HAVING`은 둘 다 조건처럼 보이지만 위치가 다르다.

| 문법 | 조건이 걸리는 대상 |
|---|---|
| `WHERE` | 개별 레코드 |
| `HAVING` | 그룹화된 결과 |

이 문법은 SQL Injection 초반 인증 우회와 직접 연결되지는 않는다. 다만 SQL 조회 결과를 그룹 단위로 다룰 때 쓰이는 기본 문법이므로, PDF의 SQL 기초 범위 안에서 짧게 알아둔다.

---

## UNION

`UNION`은 두 `SELECT` 결과를 합쳐서 반환하는 문법이다.

```sql
SELECT <필드명> FROM <테이블명> WHERE <조건>
UNION
SELECT <필드명> FROM <테이블명> WHERE <조건>
```

PDF 예시:

```sql
SELECT name, age FROM member
UNION
SELECT strname, intReadno FROM board
```

정상적인 `UNION`이 되려면 합쳐지는 결과의 **필드 개수와 타입이 맞아야 한다.**

이 조건은 뒤의 정보 추출 파트에서 중요해진다. 공격자가 원래 애플리케이션의 `SELECT` 뒤에 다른 `SELECT`를 붙이려면, 원래 쿼리의 컬럼 개수와 타입을 맞춰야 하기 때문이다. 그래서 `UNION`은 단순 SQL 문법이 아니라 SQL Injection 정보 추출의 핵심 기초다.

---

## INSERT, UPDATE, DELETE

SQL Injection의 입문 예시는 보통 `SELECT`를 이용한 로그인 우회지만, SQL은 데이터를 조회만 하지 않는다. 데이터 추가, 수정, 삭제도 SQL로 수행한다.

| 명령 | 기본 의미 | SQLi 관점 |
|---|---|---|
| `INSERT` | 테이블에 레코드를 추가 | 저장값 조작, 데이터 오염 가능성 |
| `UPDATE` | 조건에 맞는 레코드 값을 변경 | 회원정보, 권한, 게시글 내용 변조 가능성 |
| `DELETE` | 조건에 맞는 레코드를 삭제 | 데이터 손실, 파괴 가능성 |

### INSERT

```sql
INSERT INTO <테이블명> (컬럼명, ) VALUES (값, )
```

PDF 예시:

```sql
INSERT INTO member (user_id, user_pw, name, nickname, age)
VALUES ('hacker', 'hacker', 'hacker', 'hacker', 1)
```

`INSERT`는 회원가입, 게시글 작성, 댓글 작성처럼 새 데이터를 저장하는 기능과 연결된다.

### UPDATE

```sql
UPDATE <테이블>
SET <필드명>=<값>
WHERE <조건>
```

PDF 예시:

```sql
UPDATE member SET name='박명수' WHERE name='이명수'
```

`UPDATE`에서는 `SET`이 무엇을 바꿀지 정하고, `WHERE`가 어떤 레코드를 바꿀지 정한다. `WHERE` 조건이 없거나 조작되면 의도한 한 행이 아니라 여러 행이 바뀔 수 있다.

### DELETE

```sql
DELETE FROM <테이블명>
WHERE <조건>
```

PDF 예시:

```sql
DELETE FROM member WHERE name='tester'
```

`DELETE` 역시 `WHERE` 조건이 삭제 범위를 결정한다. SQL Injection의 피해가 단순 조회를 넘어 DB 조작이나 파괴로 이어질 수 있다는 점을 이해하는 데 필요하다.

---

## 헷갈리기 쉬운 지점

- `SQL 기초`라고 해서 SQL 전체를 다루는 노트가 아니다. 이 노트는 SQL Injection 이해에 필요한 SQL만 다룬다.
- `SELECT / WHERE / UNION`은 뒤의 SQL Injection 흐름과 직접 연결되므로 비중이 높다.
- 집계함수, `GROUP BY / HAVING`은 SQLi 초반 핵심도는 낮지만 PDF 내용이므로 삭제하지 않고 짧게 정리한다.
- `WHERE`는 조회 조건만이 아니라 `UPDATE`, `DELETE`의 영향 범위도 결정한다.
- SQL Injection은 SQL 문법을 무조건 깨뜨리는 공격이 아니라, 서버가 만든 SQL을 공격자에게 유리한 유효한 SQL로 바꾸는 흐름에 가깝다.

---

## 이 vault에서 쓰는 법

- 이 노트는 `5-20_웹보안.pdf` p.107-114의 stable prerequisite note로 쓴다.
- SQL 전체 문법이나 DB 설계를 다루지 않는다. SQL Injection 이해에 필요한 `SELECT`, `WHERE`, `UNION`, `INSERT`, `UPDATE`, `DELETE`만 담당한다.
- 로그인 우회 흐름은 [[10_학습 노트/시스템보안/웹보안/SQL Injection 개념과 인증 우회|SQL Injection 개념과 인증 우회]]에서 본다.
- Error/UNION 기반 정보 추출은 [[10_학습 노트/시스템보안/웹보안/SQL Injection Error와 UNION 기반 정보 추출과 Schema 파악|SQL Injection Error와 UNION 기반 정보 추출과 Schema 파악]]에서 본다.
- 방어 기준은 [[10_학습 노트/시스템보안/웹보안/SQL Injection 방어|SQL Injection 방어]]에서 본다.
- [[10_학습 노트/시스템보안/웹보안/SQL Injection 페이지별 분해 기록|SQL Injection 페이지별 분해 기록]]은 source-digest/draft로 보고, 복습 진입은 이 노트와 위 stable concept note들을 우선한다.

---

## 관련 노트

- [[10_학습 노트/시스템보안/웹보안/SQL Injection 개념과 인증 우회|SQL Injection 개념과 인증 우회]]
- [[10_학습 노트/시스템보안/웹보안/SQL Injection Error와 UNION 기반 정보 추출과 Schema 파악|SQL Injection Error와 UNION 기반 정보 추출과 Schema 파악]]
- [[10_학습 노트/시스템보안/웹보안/SQL Injection 방어|SQL Injection 방어]]

## 확인 질문

- `SELECT`, `FROM`, `WHERE`가 각각 무엇을 의미하는가?
- 로그인 쿼리에서 `WHERE` 조건이 왜 인증 성공/실패와 연결되는가?
- `COUNT(*)`가 레코드 존재 여부와 어떻게 연결될 수 있는가?
- `UNION`에서 필드 개수와 타입이 맞아야 하는 이유는 무엇인가?
- `UPDATE`와 `DELETE`에서 `WHERE` 조건이 조작되면 왜 위험한가?
