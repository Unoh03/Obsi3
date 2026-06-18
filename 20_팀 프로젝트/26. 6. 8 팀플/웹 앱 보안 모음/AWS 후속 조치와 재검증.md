# AWS 후속 조치와 재검증

관련 노트:

- [[웹 취약점 - 16 불충분한 세션 관리|웹 취약점 - 16 불충분한 세션 관리]]
- [[웹 취약점 - 17 데이터 평문 전송|웹 취약점 - 17 데이터 평문 전송]]

## 이 노트의 역할

이 노트는 VM/GNS 환경에서 끝까지 검증하지 못했거나, 가능은 하지만 AWS에서 하는 편이 더 자연스러운 웹 취약점 후속 조치를 모아두는 작업 노트다.

각 취약점 개별 노트에는 “VM에서 어디까지 했고 왜 AWS로 넘기는지”만 짧게 남긴다. 상세 절차, AWS 구성, 재검증 방법, 실패 시 확인 순서는 이 노트에 모은다.

현재 등록된 후속 항목은 다음과 같다.

| 번호 | 취약점 | VM/GNS에서 막힌 지점 | AWS에서 이어갈 이유 |
|---:|---|---|---|
| 16 | 불충분한 세션 관리 | `Secure` 쿠키 속성은 HTTPS 경로가 정상이어야 의미 있게 검증 가능 | ALB/ACM HTTPS 구성 후 `PHPSESSID` 속성 재검증 |
| 17 | 데이터 평문 전송 | self-signed HTTPS는 CLI 기준 부분 성공, 브라우저/Paros 증거 미완성 | ALB/ACM/Route 53 기반 HTTPS로 조치 후 재검증 |

후속 항목이 더 생기면 이 표에 추가하고, 아래에 항목별 섹션을 붙인다.

```text
17번 데이터 평문 전송
= HTTPS 전송구간 구성 후 로그인/회원정보 요청이 평문 HTTP로 노출되지 않는지 확인

16번 불충분한 세션 관리
= HTTPS 위에서 PHPSESSID 쿠키에 Secure / HttpOnly / SameSite 속성이 붙는지 확인
```

핵심은 17번 HTTPS 조치가 먼저다. `Secure` 쿠키는 HTTPS 경로가 정상 구성되어야 의미 있게 검증할 수 있다.

## 후속 항목별 현재 상태

### 17번 - 데이터 평문 전송

조치 전에는 HTTP 로그인 요청에서 `id`, `pw`가 평문으로 보이는 증거를 확보했다.

조치 시도는 다음까지 진행했다.

| 확인 항목 | 결과 |
|---|---|
| Apache SSL module | 활성화 |
| self-signed certificate | 생성 |
| Apache 443 VirtualHost | 생성 및 활성화 |
| Apache configtest | `Syntax OK` |
| 서버 내부 HTTPS 요청 | `HTTP/1.1 200 OK` |
| Windows TCP 443 연결 | 성공 |
| Windows `curl.exe` HTTPS 요청 | `HTTP/1.1 200 OK` |
| 브라우저 HTTPS 접속 | `ERR_EMPTY_RESPONSE`로 실패 |
| HTTP -> HTTPS redirect | 미구성 |
| Paros/Wireshark 조치 후 재검증 | 미완료 |

결론은 다음과 같다.

```text
취약 여부: 확인
조치 설계: 확인
VM self-signed HTTPS: CLI 기준 부분 성공
브라우저/Paros 조치 후 증거: 미완료
후속: AWS 환경에서 HTTPS 구성 후 재검증
```

### 16번 - 불충분한 세션 관리

16번은 현재 다음까지 확인했다.

| 항목 | 상태 |
|---|---|
| 로그인 성공 시 세션 ID 재발급 | 캡처로 확인 |
| 로그아웃 후 재로그인 시 세션 ID 변경 | 캡처로 확인 |
| 5분 세션 만료 코드 | `header.php` 기준 적용 |
| 5분 방치 후 만료 화면 캡처 | 미수집 |
| 쿠키 `HttpOnly`, `SameSite` | HTTP 상태에서도 확인 가능 |
| 쿠키 `Secure` | HTTPS 구성 이후 확인 필요 |

`Secure` 속성은 브라우저가 HTTPS 요청에서만 쿠키를 보내도록 하는 속성이다. 따라서 AWS에서 HTTPS를 정상 구성한 뒤 16번 쿠키 속성까지 다시 확인한다.

## 공통 AWS 실행 기준

### 권장 구조

권장 구조는 다음과 같다.

```text
사용자 브라우저
-> Route 53 도메인
-> ALB 443 HTTPS listener + ACM certificate
-> Target Group HTTP 80 또는 8080
-> EC2 WEB Apache/PHP CARE
```

이 구조에서는 TLS가 ALB에서 종료된다. 즉 브라우저와 ALB 사이의 외부 전송구간은 HTTPS로 암호화되고, ALB는 내부 VPC의 WEB 서버로 HTTP 요청을 전달한다.

이번 실습의 목적이 “사용자 브라우저에서 CARE까지 접근할 때 로그인 정보가 평문 HTTP로 노출되는가”를 확인하는 것이므로, 우선은 **ALB에서 TLS 종료**하는 방식으로 충분하다. 내부 VPC 구간까지 HTTPS로 묶는 end-to-end TLS는 필요하면 후속 고도화로 둔다.

### 사전 조건

#### 도메인

ACM public certificate를 쓰려면 도메인이 필요하다.

예시:

```text
care.example.com
```

ACM public certificate는 원칙적으로 DNS 이름을 대상으로 발급한다. EC2 public IP 자체에 대해 일반적인 브라우저 신뢰 인증서를 받는 방식은 실습 흐름에 맞지 않는다.

도메인이 없다면 EC2 self-signed 인증서 또는 imported certificate 방식으로도 실습은 가능하지만, 브라우저 경고와 신뢰 문제가 다시 생긴다. 가능하면 Route 53 또는 외부 DNS에 연결 가능한 도메인을 준비한다.

#### 보안 그룹

기본 방향은 다음과 같다.

| 대상 | 인바운드 | 소스 |
|---|---|---|
| ALB SG | TCP 80 | `0.0.0.0/0` |
| ALB SG | TCP 443 | `0.0.0.0/0` |
| WEB SG | TCP 80 또는 8080 | ALB SG |
| WEB SG | TCP 22 | 관리자 IP 또는 Bastion SG |

가능하면 WEB EC2의 public HTTP 직접 접근은 닫는다. 외부 사용자는 ALB를 통해서만 들어오게 해야 17번 조치 증거가 깔끔하다.

## 공통 AWS 조치 절차

### ACM 인증서 요청

AWS Console에서 다음 순서로 진행한다.

```text
AWS Certificate Manager
-> Request certificate
-> Request a public certificate
-> Domain name: care.example.com
-> Validation method: DNS validation
-> Request
```

요청 후 ACM이 CNAME 레코드를 제공한다. Route 53을 쓰고 있다면 `Create records in Route 53`로 바로 추가할 수 있고, 외부 DNS를 쓰면 해당 DNS 관리 화면에 CNAME을 직접 추가한다.

상태가 다음처럼 바뀔 때까지 기다린다.

```text
Status: Issued
```

### Target Group 준비

CARE가 Apache/PHP로 떠 있는 포트에 맞춰 Target Group을 만든다.

| 항목 | 값 |
|---|---|
| Target type | Instance |
| Protocol | HTTP |
| Port | CARE 실제 포트, 예: 80 또는 8080 |
| Health check path | `/` 또는 `/index.php` |

대상 EC2를 등록한 뒤 `Healthy`가 되는지 확인한다.

```text
Target Groups
-> Targets
-> Health status: Healthy
```

만약 `Unhealthy`면 먼저 다음을 확인한다.

| 증상 | 확인 |
|---|---|
| 502 / 504 | ALB SG -> WEB SG 포트 허용 여부 |
| Health check failed | Health check path가 실제 응답하는지 |
| Timeout | WEB 서버 방화벽, Apache 포트, 라우팅 |
| Connection refused | Apache/PHP 서비스가 해당 포트에서 안 뜸 |

### ALB HTTPS listener 추가

ALB에서 listener를 추가한다.

```text
EC2
-> Load Balancers
-> 대상 ALB 선택
-> Listeners
-> Add listener
```

설정값은 다음처럼 둔다.

| 항목 | 값 |
|---|---|
| Protocol | HTTPS |
| Port | 443 |
| Default action | Forward to CARE Target Group |
| Security policy | 기본 권장 TLS policy |
| Default SSL/TLS certificate | ACM에서 발급한 `care.example.com` 인증서 |

이 단계가 17번의 핵심 조치다. AWS 문서 기준 HTTPS listener에는 SSL server certificate가 필요하고, ALB가 프런트엔드 HTTPS 연결을 종료한 뒤 대상 그룹으로 요청을 전달한다.

### HTTP 80 -> HTTPS 443 redirect

HTTP listener 80은 서비스 유지용으로 열어두되, 실제 응답은 HTTPS로 넘긴다.

```text
ALB
-> Listeners
-> HTTP : 80
-> Edit default action
-> Redirect to HTTPS : 443
-> Status code: 301 또는 302
```

리다이렉트 목표는 다음처럼 잡는다.

```text
Protocol: HTTPS
Port: 443
Host: #{host}
Path: /#{path}
Query: #{query}
```

이렇게 하면 사용자가 `http://care.example.com/member/login.php`로 들어와도 HTTPS URL로 이동한다.

### Route 53 alias 연결

Route 53 hosted zone에서 레코드를 만든다.

| 항목 | 값 |
|---|---|
| Record name | `care` |
| Record type | `A` |
| Alias | Yes |
| Route traffic to | Application Load Balancer |
| Region | ALB가 있는 Region |
| Load balancer | 대상 ALB |

최종 접속 URL은 다음처럼 된다.

```text
https://care.example.com/
```

## 17번 - AWS 재검증

### HTTP 요청이 HTTPS로 넘어가는지 확인

WEB 서버 또는 로컬에서 확인한다.

```bash
curl -I http://care.example.com/member/login.php
```

기대 결과:

```text
HTTP/1.1 301 Moved Permanently
Location: https://care.example.com/member/login.php
```

301이 아니라 302여도 실습 증거로는 사용할 수 있다. 중요한 것은 HTTP 요청이 그대로 로그인 페이지를 처리하지 않고 HTTPS로 넘어가는지다.

### HTTPS 요청이 정상 응답하는지 확인

```bash
curl -I https://care.example.com/member/login.php
```

기대 결과:

```text
HTTP/2 200
```

또는 환경에 따라 다음처럼 보일 수 있다.

```text
HTTP/1.1 200 OK
```

브라우저에서는 주소창에 HTTPS가 표시되는 화면을 캡처한다.

### Paros 또는 Wireshark 증거

조치 전 증거는 HTTP 로그인 요청에서 `id`, `pw`가 평문으로 보이는 화면이다.

조치 후에는 다음 중 하나를 증거로 쓴다.

| 증거 | 의미 |
|---|---|
| HTTP 접속 시 HTTPS로 redirect되는 화면 | HTTP 평문 로그인 경로가 막힘 |
| HTTPS 로그인 요청 화면 | 브라우저 기준 암호화 연결 사용 |
| Paros에서 HTTP 요청이 redirect만 보이는 화면 | HTTP로 `id`, `pw`가 전송되지 않음 |
| Wireshark에서 HTTP POST 본문이 보이지 않는 화면 | 네트워크 평문 노출 감소 |

주의할 점이 있다. Paros나 Burp처럼 HTTPS interception을 수행하는 프록시를 사용하면, 프록시 내부 화면에서는 HTTPS 요청 본문이 보일 수 있다. 이 경우는 “네트워크에 평문으로 흘러간다”는 뜻이 아니라, 사용자가 테스트용 인증서를 신뢰시켜 중간자 프록시가 복호화한 것이다.

### 진단 스크립트 재실행

`kisa-webapp-checker`의 profile이 HTTP를 가리키고 있으면 17번은 계속 취약으로 나올 수 있다. AWS 조치 후에는 `profiles/care.yml`의 기준 URL을 HTTPS로 바꾼다.

```yaml
base_url: "https://care.example.com"
target_allowlist:
  - "care.example.com"
```

그 뒤 passive check를 실행한다.

```bash
python3 checker.py --profile profiles/care.yml --checks checks --mode passive
```

기대 방향:

| 항목 | 기대 |
|---|---|
| 17 데이터 평문 전송 | `not_vulnerable` 또는 조치 확인 가능한 상태 |
| 16 불충분한 세션 관리 | 쿠키 속성 확인 결과에 따라 판단 |

진단 스크립트가 여전히 17번을 취약으로 판단하면 먼저 profile의 `base_url`이 `http://`로 남아 있는지 확인한다.

## 16번 - AWS 세션 쿠키 조치

### 조치 기준

16번에서 AWS HTTPS가 필요한 부분은 쿠키 속성이다.

목표는 로그인 후 `Set-Cookie`에 다음 속성이 붙는 것이다.

```text
PHPSESSID=...; path=/; Secure; HttpOnly; SameSite=Lax
```

| 속성 | 의미 |
|---|---|
| `Secure` | HTTPS 요청에서만 쿠키 전송 |
| `HttpOnly` | JavaScript에서 세션 쿠키 접근 제한 |
| `SameSite=Lax` | 외부 사이트에서 온 요청에 쿠키가 자동 동봉되는 범위 축소 |

### PHP 코드에서 처리하는 방식

공통 세션 부트스트랩 파일을 둘 수 있으면 가장 명확하다.

예시:

```php
<?php
// PDF 16번 조치: 세션 쿠키 보안 속성 설정
if (session_status() === PHP_SESSION_NONE) {
    session_set_cookie_params([
        'lifetime' => 0,
        'path' => '/',
        'secure' => true,
        'httponly' => true,
        'samesite' => 'Lax',
    ]);
    session_start();
}
?>
```

주의점:

- `session_set_cookie_params()`는 `session_start()`보다 먼저 실행되어야 한다.
- CARE에는 여러 파일에 직접 `session_start()`가 있으므로, 공통 파일로 모으거나 모든 시작 지점에 같은 규칙을 적용해야 한다.
- HTTP로 직접 접속하면 `Secure` 쿠키가 전송되지 않는다. 따라서 HTTP는 ALB에서 HTTPS로 redirect되게 해야 한다.

### PHP 설정에서 처리하는 방식

실습에서는 전역 PHP 설정으로 잡는 편이 더 빠를 수 있다.

Apache mod_php 기준:

```bash
php --ini
sudo nano /etc/php/*/apache2/conf.d/99-care-session.ini
```

내용:

```ini
session.cookie_httponly = 1
session.cookie_samesite = Lax
session.cookie_secure = 1
session.use_strict_mode = 1
```

적용:

```bash
sudo systemctl reload apache2
```

PHP-FPM을 쓰는 환경이면 경로와 재시작 서비스가 달라진다.

```text
/etc/php/*/fpm/conf.d/99-care-session.ini
sudo systemctl reload php*-fpm
sudo systemctl reload apache2
```

현재 CARE VM 실습은 Apache/PHP 중심이므로, AWS에서도 같은 방식이면 Apache 경로를 먼저 확인한다.

## 16번 - AWS 재검증

HTTPS 접속 후 로그인 요청을 수행하고 쿠키를 확인한다.

CLI로는 다음처럼 시작할 수 있다.

```bash
curl -I https://care.example.com/member/login.php
```

다만 로그인 성공 후 세션 쿠키를 보려면 브라우저 개발자 도구가 더 편하다.

```text
F12
-> Application 또는 Storage
-> Cookies
-> https://care.example.com
-> PHPSESSID 확인
```

확인할 속성:

| 속성 | 기대 |
|---|---|
| `Secure` | 체크됨 |
| `HttpOnly` | 체크됨 |
| `SameSite` | `Lax` 또는 실습에서 정한 값 |

증거 스크린샷은 다음 2개가 있으면 충분하다.

| 증거 | 목적 |
|---|---|
| HTTPS 로그인 화면 | 16번 쿠키 검증이 HTTPS 위에서 수행됨 |
| `PHPSESSID` 속성 화면 | `Secure`, `HttpOnly`, `SameSite` 확인 |

## 증거 체크리스트

AWS에서 최종 캡처할 증거는 다음 순서로 모은다.

| 번호 | 증거 | 연결 항목 |
|---:|---|---|
| 1 | ACM certificate `Issued` 상태 | 17 조치 준비 |
| 2 | ALB HTTPS 443 listener와 ACM 인증서 연결 | 17 조치 |
| 3 | ALB HTTP 80 listener가 HTTPS 443으로 redirect | 17 조치 |
| 4 | Target Group `Healthy` | 17 조치 전제 |
| 5 | `http://care.example.com/...` 접속 시 HTTPS로 이동 | 17 조치 후 확인 |
| 6 | `https://care.example.com/...` 로그인 페이지 정상 표시 | 17 조치 후 확인 |
| 7 | 조치 후 로그인 요청에서 HTTP 평문 `id`, `pw`가 보이지 않음 | 17 재검증 |
| 8 | `PHPSESSID`에 `Secure`, `HttpOnly`, `SameSite` 표시 | 16 쿠키 속성 |
| 9 | `kisa-webapp-checker` passive 결과 | 16/17 보조 증거 |

## 실패 시 확인 순서

### ACM 인증서가 `Issued`가 되지 않음

| 원인 후보 | 확인 |
|---|---|
| DNS validation CNAME 누락 | ACM이 제공한 CNAME이 DNS에 들어갔는지 확인 |
| hosted zone 오류 | 실제 도메인의 authoritative DNS가 Route 53인지 확인 |
| 다른 Region 인증서 | ALB와 같은 Region에서 발급했는지 확인 |

### ALB가 502 또는 504를 반환함

| 원인 후보 | 확인 |
|---|---|
| Target Group port 불일치 | CARE가 80인지 8080인지 확인 |
| WEB SG가 ALB SG를 허용하지 않음 | WEB SG inbound source가 ALB SG인지 확인 |
| Apache 서비스 중단 | WEB 서버에서 `systemctl status apache2` |
| Health check path 오류 | `/` 또는 `/index.php`가 200을 주는지 확인 |

### HTTPS는 되는데 16번 `Secure` 쿠키가 없음

| 원인 후보 | 확인 |
|---|---|
| PHP 설정이 적용되지 않음 | `php --ini`, `phpinfo()` 또는 Apache reload 확인 |
| `session_start()`가 먼저 실행됨 | `session_set_cookie_params()` 위치 확인 |
| HTTP 직접 접속으로 테스트함 | 반드시 `https://care.example.com`에서 확인 |
| ALB 뒤에서 HTTPS 인식 로직이 꼬임 | 앱이 `$_SERVER['HTTPS']`에 의존하는지 확인 |

### 진단 스크립트가 여전히 17번을 취약으로 판단함

먼저 profile을 확인한다.

```yaml
base_url: "https://care.example.com"
```

`http://`로 남아 있으면 스크립트 입장에서는 아직 평문 전송 환경이다.

그다음 HTTP redirect를 확인한다.

```bash
curl -I http://care.example.com/member/login.php
```

HTTPS로 redirect되지 않고 `200 OK`가 나오면 17번 조치가 불완전하다.

## 출처

- [AWS: Create an HTTPS listener for your Application Load Balancer](https://docs.aws.amazon.com/elasticloadbalancing/latest/application/create-https-listener.html)
- [AWS: AWS Certificate Manager public certificates](https://docs.aws.amazon.com/acm/latest/userguide/gs-acm-request-public.html)
- [AWS: DNS validation for ACM certificates](https://docs.aws.amazon.com/acm/latest/userguide/dns-validation.html)
- [AWS: Routing traffic to an ELB load balancer](https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/routing-to-elb-load-balancer.html)
- [AWS: ALB listener rule action types](https://docs.aws.amazon.com/elasticloadbalancing/latest/application/rule-action-types.html)
