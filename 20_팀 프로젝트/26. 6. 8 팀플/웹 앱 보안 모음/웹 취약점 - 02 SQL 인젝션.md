---
type: lab
topic: web-security
source: 주요정보통신기반시설 기술적 취약점 분석·평가 방법 상세가이드
source_pages:
  - 693
  - 694
  - 695
  - 696
  - 697
  - 698
  - 699
status: active
created: 2026-06-12
tags:
  - 🏷️과목/웹보안
  - 🏷️주제/SQL-Injection
  - 🏷️상태/active
---

# 웹 취약점 - 02 SQL 인젝션

source: [[40_자료/주요정보통신기반시설 기술적 취약점 분석·평가 방법 상세가이드.pdf|주요정보통신기반시설 기술적 취약점 분석·평가 방법 상세가이드]], p.693-699.

## 1. 개요

**SQL Injection**은 사용자 입력값이 SQL 쿼리 문자열에 삽입되면서, 입력값이 단순 데이터가 아니라 SQL 구문으로 해석되는 취약점이다.

공격자는 입력값에 SQL 조건식, 주석, 구분자, UNION 구문 등을 삽입하여 서버가 의도하지 않은 SQL을 실행하게 만들 수 있다.

주요 영향은 다음과 같다.

|영향|설명|
|---|---|
|인증 우회|로그인 조건을 참으로 만들어 비밀번호 검증 우회|
|데이터 조회|DB 내 사용자 정보, 계정 정보, 민감 정보 조회|
|데이터 변조|INSERT, UPDATE, DELETE 등을 통한 데이터 조작|
|에러 정보 노출|DBMS 에러 메시지로 테이블명, 컬럼명, 쿼리 구조 추정|
|추가 공격 확대|DBMS 기능, 권한, 설정에 따라 파일 접근 또는 명령 실행으로 확장 가능|

## 2. PDF p.693-699 기준 정리

### 점검 목적

웹 애플리케이션 입력값이 SQL 쿼리에 삽입되어 비인가 DB 접근이나 조작으로 이어지는지 확인한다.

판단 기준은 다음과 같이 정리할 수 있다.

|구분|판단|
|---|---|
|양호|임의 SQL 쿼리 입력이 검증되어 비정상 쿼리가 실행되지 않음|
|취약|임의 SQL 쿼리 입력 검증이 부족하여 비정상 쿼리가 실행됨|

### 점검 방법

PDF의 점검 흐름은 크게 두 단계다.

| 단계         | 내용                                    | 확인 포인트                    |
| ---------- | ------------------------------------- | ------------------------- |
| **Step 1** | 사용자 입력값에 참/거짓 SQL 쿼리를 삽입              | 응답 내용, 오류, 결과 수, 화면 변화 비교 |
| **Step 2** | 로그인·비밀번호 검증 등 인증 페이지에 참이 되는 SQL 쿼리 삽입 | 비밀번호를 몰라도 인증이 통과되는지 확인    |

**Step 1**은 SQL 구문이 실제 서버 쿼리에 반영되는지 보는 단계다. 참 조건과 거짓 조건을 넣었을 때 응답이 달라지면 SQL Injection 가능성을 의심할 수 있다.

**Step 2**는 인증 우회 확인 단계다. 로그인 조건이 항상 참이 되도록 조작하여 비밀번호를 몰라도 인증이 통과되는지 확인한다.

### 조치 방향

PDF p.693-699의 조치 방향은 다음으로 정리한다.

- SQL 쿼리에 사용되는 입력값의 유효성을 검증한다.
- `'`, `;`, `--`, `#`, `/* */` 같은 SQL 특수문자 입력을 제한한다.
- Prepared Statement를 사용하여 SQL 구문과 사용자 입력값을 분리한다.
- DBMS 에러 메시지와 에러 코드가 브라우저에 노출되지 않도록 예외 처리한다.
- 웹 방화벽에 SQL Injection 관련 룰셋을 적용한다.
- MyBatis에서는 `${}` 대신 `#{}`를 사용하여 파라미터 바인딩을 적용한다.
- PHP에서는 `addslashes`, `magic_quotes_gpc`에 의존하지 않고 PDO prepared statement 같은 구조를 사용한다.
- SQL Server에서는 필요하지 않은 `xp_cmdshell`을 비활성화한다.

## 3. CARE 실습 참고

관련 기존 노트: [[SQL Injection 인증 우회 실습]]

이전 CARE 실습은 PDF 흐름을 이해하기 위한 참고 사례로만 사용한다. 본 노트의 기준은 PDF p.693-699다.

CARE에서 확인했던 대표 구조는 로그인 처리 파일의 SQL 문자열 결합이다.

```php
$query = "SELECT * FROM member WHERE id='$id' and pw='$pw'";
```

Paros에서 `id`, `pw` 값을 다음처럼 조작하여 인증 우회를 확인했다.

```text
id=' OR '1'='1
pw=' OR '1'='1
```

이 입력값이 SQL 문자열에 그대로 결합되면 최종 조건은 대략 다음처럼 해석될 수 있다.

```sql
WHERE id='' OR '1'='1'
AND pw='' OR '1'='1'
```

`'1'='1'`은 항상 참이므로, 원래의 ID/PW 검증 조건이 우회될 수 있다.

이 실습은 PDF의 Step 2, 즉 **인증 페이지에 참이 되는 SQL 조건을 삽입하여 인증 우회 여부를 확인하는 단계**와 대응한다.

다만 이전 실습에서 수행한 `$num != 0` 변경이나 세션 저장 방식 조정은 PDF 기준 취약점의 본질이 아니라, 관찰을 쉽게 하기 위한 실습용 조정으로 본다.

## 4. PDF와 이전 실습 비교

| 비교 항목  | PDF p.693-699                           | 이전 CARE 실습               | 판단                 |
| ------ | --------------------------------------- | ------------------------ | ------------------ |
| 기준     | SQL Injection 점검·조치 기준                  | CARE 로그인 인증 우회 실습        | PDF를 기준으로 정리       |
| Step 1 | 참/거짓 SQL 삽입 후 응답 변화 확인                  | 별도 체계적 비교는 하지 않음         | 필요 시 추가 실습 후보      |
| Step 2 | 인증 페이지에 참 조건 삽입 후 우회 확인                 | `' OR '1'='1`로 로그인 우회 확인 | 대응됨                |
| 조치     | 입력 검증, Prepared Statement, 예외 처리, WAF 등 | 취약 구조 확인 중심              | 방어 구현은 PDF 기준으로 정리 |
| 후속 영향  | 비인가 DB 접근·조작 가능성                        | 세션 생성과 modify 페이지 영향 검토  | 참고 자료로만 사용         |

정리하면, 이전 CARE 실습은 PDF p.693-699 중 Step 2를 이해하는 데 유용한 사례다. 그러나 본 프로젝트 노트에서는 CARE 코드 전체를 다시 깊게 분석하지 않고, PDF 기준의 점검 방법과 조치 방안을 중심으로 정리한다.

## 5. 점검 과정

점검용으로 사용할 계정을 만들었다.

| ID     | PW, name, mobile, address, email |
| ------ | -------------------------------- |
| victim | 123                              |
### Step 1)


```
검색 : (아무거나)' OR '1'='1' -- 

검색 : (실제하는 글 제목)' OR '1'='2' -- 
```
### Step 2)

```
ID : victim'-- 
PW : (아무거나)
```

## 6. 조치 방안

SQL Injection 방어의 핵심은 사용자 입력을 SQL 구문으로 해석하지 않게 만드는 것이다.

현재 CARE 코드는 `mysqli`와 `care_db_connect()`를 사용하므로, 조치 예시도 `mysqli` 기준으로 작성한다.

### 6.1 로그인 처리 조치

현재 로그인 처리의 핵심 취약 코드는 다음 부분이다.

```php
$sql = "SELECT * FROM member WHERE id = '$id' AND pw = '$pw'";
$result = mysqli_query($link, $sql);
```

`$id`, `$pw`가 SQL 문자열에 직접 들어가기 때문에 `' OR '1'='1` 같은 입력값이 SQL 조건식으로 섞일 수 있다.

이 부분은 다음처럼 Prepared Statement로 바꾼다.

```php
$id = $_POST['id'];
$pw = $_POST['pw'];

require_once __DIR__ . '/../config.php';
$link = care_db_connect() or die('연결 실패');

$query = "SELECT * FROM member WHERE id = ? AND pw = ?";

$stmt = mysqli_prepare($link, $query);
mysqli_stmt_bind_param($stmt, "ss", $id, $pw);
mysqli_stmt_execute($stmt);

$result = mysqli_stmt_get_result($stmt);
$num = mysqli_num_rows($result);
```

여기서 핵심은 SQL 안에 사용자 입력을 직접 붙이지 않고 `?`를 사용하는 것이다.

```php
$sql = "SELECT * FROM member WHERE id = ? AND pw = ?";
```

`mysqli_stmt_bind_param($stmt, "ss", $id, $pw)`에서 `"ss"`는 바인딩하는 두 값이 모두 문자열이라는 뜻이다.

이 방식에서는 사용자가 다음 값을 넣어도,

```text
' OR '1'='1
```

DB는 이를 SQL 조건식이 아니라 **문자열 데이터**로 처리한다. 즉 `id` 값이 `"' OR '1'='1"`인 회원을 찾으려 할 뿐, `OR '1'='1'` 조건을 실행하지 않는다.

기존 로그인 코드 흐름에 맞추면 다음처럼 사용할 수 있다.

```php
$id = $_POST['id'];
$pw = $_POST['pw'];

require_once __DIR__ . '/../config.php';
$link = care_db_connect() or die('연결 실패');

$query = "SELECT * FROM member WHERE id = ? AND pw = ?";

$stmt = mysqli_prepare($link, $query);
mysqli_stmt_bind_param($stmt, "ss", $id, $pw);
mysqli_stmt_execute($stmt);

$result = mysqli_stmt_get_result($stmt);
$num = mysqli_num_rows($result);

session_start();

if ($num == 1) {
    $_SESSION['id'] = $id;

    $row = mysqli_fetch_assoc($result);
    $_SESSION['name'] = $row['name'];
    $_SESSION['mobile'] = $row['mobile'];
    $_SESSION['address'] = $row['address'];
    $_SESSION['email'] = $row['email'];
    $_SESSION['num'] = $row['num'];
} else {
?>
    <script>
        alert('로그인 실패');
        history.go(-1);
    </script>
<?php
    exit;
}

mysqli_stmt_close($stmt);
mysqli_close($link);
```

### 6.2 게시판 검색 조치

게시판 목록 검색의 취약 코드는 다음 부분이다.

```php
$query = "SELECT * FROM center WHERE $find like '%$data%'order by num desc";
```

여기서는 `$data`뿐 아니라 `$find`도 문제다.

`$data`는 검색어이므로 Prepared Statement로 바인딩하면 된다. 하지만 `$find`는 컬럼명이기 때문에 `?`로 바인딩하면 안 된다. 컬럼명은 `subject`, `content`, `id` 중 하나만 허용하는 화이트리스트 방식으로 제한한다.

```php
$mode = $_GET['mode'] ?? '';
$find = $_GET['find'] ?? 'subject';
$data = trim($_GET['data'] ?? '');

$allowedFind = ['subject', 'content', 'id'];

if (!in_array($find, $allowedFind, true)) {
    exit('invalid search field');
}

if ($mode == "search") {
    if ($data == "") {
?>
        <script>
            alert('검색어를 입력하세요');
            history.go(-1);
        </script>
<?php
        exit;
    }

    $query = "SELECT * FROM center WHERE {$find} LIKE ? ORDER BY num DESC";
    $keyword = '%' . $data . '%';

    $stmt = mysqli_prepare($link, $query);
    mysqli_stmt_bind_param($stmt, "s", $keyword);
    mysqli_stmt_execute($stmt);

    $result = mysqli_stmt_get_result($stmt);
} else {
    $query = "SELECT * FROM center ORDER BY num DESC";
    $result = mysqli_query($link, $query);
}
```

검색어인 `$data`는 `LIKE ?`에 바인딩되므로 SQL 코드로 실행되지 않는다. 검색 대상 컬럼인 `$find`는 바인딩하지 않고, 허용된 컬럼명인지 먼저 검사한다.

페이지 번호도 숫자로만 처리하는 편이 안전하다.

```php
$selectPage = isset($_GET['page']) ? (int)$_GET['page'] : 1;

if ($selectPage < 1) {
    $selectPage = 1;
}
```

### 6.3 추가 조치

Prepared Statement 외의 조치는 보조 방어로 본다.

| 조치 | 적용 방식 |
|---|---|
| SQL 사용 지점 점검 | 로그인, 검색, 게시글 조회, ID 중복 확인 등 SQL을 만드는 모든 입력 지점을 확인 |
| 입력값 길이 제한 | `if (strlen($id) > 30) exit('invalid input');`처럼 비정상적으로 긴 입력 차단 |
| 입력 형식 제한 | ID는 `preg_match('/^[a-zA-Z0-9_]+$/', $id)`처럼 허용 문자만 통과 |
| DB 에러 노출 차단 | 실제 오류는 `error_log()`에 남기고, 브라우저에는 일반 오류 메시지만 출력 |
| 최소 권한 DB 계정 사용 | 웹 계정에는 필요한 `SELECT`, `INSERT`, `UPDATE`만 부여 |
| WAF 룰셋 적용 | SQL Injection 탐지 룰을 보조 방어선으로 적용 |

정리하면 다음과 같다.

```text
로그인: id, pw를 Prepared Statement로 바인딩
검색어: data를 Prepared Statement로 바인딩
검색 컬럼: find는 subject, content, id만 허용
나머지: 입력값 길이·형식 제한, DB 에러 노출 차단, 최소 권한, WAF 적용
```

## 7. 증거
- 최초 http://172.168.10.10/center/list.php 의 모습
![[Pasted image 20260612152857.png]]
- 참 SQL 커리를 삽입한 모습과 결과
![[Pasted image 20260612152650.png]]
![[Pasted image 20260612153009.png]]
- 거짓 SQL 커리를 삽입한 모습과 결과
![[Pasted image 20260612153618.png]]
![[Pasted image 20260612153638.png]]
## 8. 판단

본 노트는 PDF p.693-699를 기준으로 SQL Injection을 정리한다.

이전 CARE 실습은 SQL Injection 인증 우회를 직접 확인한 사례이지만, 본 노트에서는 참고 자료로만 사용한다. 해당 실습은 PDF의 Step 2, 즉 인증 페이지에 참 조건을 삽입하여 인증 우회 여부를 확인하는 흐름과 대응한다.

이번 정리의 핵심은 다음 세 가지다.

```text
1. SQL Injection은 사용자 입력값이 SQL 문자열에 직접 결합될 때 발생할 수 있다.
2. PDF의 점검 흐름은 참/거짓 조건 응답 비교와 인증 우회 확인으로 나눌 수 있다.
3. 방어의 핵심은 Prepared Statement로 SQL 구문과 사용자 입력값을 분리하는 것이다.
```

SQL Injection은 이미 별도 개념 노트와 인증 우회 실습 노트가 있으므로, 본 프로젝트 노트에서는 PDF 기준 요약과 기존 실습의 참고 연결까지만 간결하게 정리한다.
