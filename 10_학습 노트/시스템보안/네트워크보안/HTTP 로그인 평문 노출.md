---
type: lab
topic: network-security
parent_moc: "[[10_학습 노트/시스템보안/네트워크보안/00_네트워크보안_목차]]"
source: lab-observation
status: stable
created: 2026-05-14
tags:
  - 🏷️과목/네트워크보안
  - 🏷️주제/HTTP
  - 🏷️주제/Plaintext
  - 🏷️주제/MITM
  - 🏷️주제/Session
---

# HTTP 로그인 평문 노출

## 한 줄 요약

HTTP 로그인 요청은 암호화되지 않기 때문에 ARP Spoofing으로 MITM 위치를 확보하면 로그인 Form 데이터와 세션 식별자가 평문으로 관찰될 수 있다.

---

## 실습 맥락

[[ARP 스푸핑]]으로 Windows Victim과 Web Server 사이의 트래픽을 Kali Attacker가 경유하도록 만들었다.

```text
Windows Victim ↔ Kali Attacker ↔ Web Server
```

이후 Windows Victim에서 Web Server의 로그인 페이지에 접속하고 로그인 요청을 보냈다.

실습 환경:

| 장비      | 역할                    | IP             |
| ------- | --------------------- | -------------- |
| Windows | Victim / Client       | `172.16.0.100` |
| Web     | Victim 2 / Web Server | `172.16.0.150` |
| DB      | DB Server             | `172.16.0.50`  |
| Kali    | Attacker / Wireshark  | `172.16.0.200` |

---

## 관찰 패킷

Wireshark에서 `POST /boot/loginProc` 요청이 평문으로 관찰되었다.

```text
Frame: 11304
Src: 172.16.0.100
Dst: 172.16.0.150
Protocol: HTTP
Request: POST /boot/loginProc
Host: 172.16.0.150:8080
Content-Type: application/x-www-form-urlencoded
Cookie: JSESSIONID=<REDACTED>
Form: id=<REDACTED>, pw=<REDACTED>
```

Wireshark는 HTTP 요청 본문을 `urlencoded-form`으로 해석했고, Form field인 `id`와 `pw`를 그대로 보여주었다. 맨 밑에 있다.

```text
Protocols in frame: eth:ethertype:ip:tcp:http:urlencoded-form
HTML Form URL Encoded: application/x-www-form-urlencoded
Form item: "id" = "<REDACTED>"
Form item: "pw" = "<REDACTED>"
```

> [!warning] 실습 메모
> `JSESSIONID`, 로그인 ID, 비밀번호 원문은 노트에 저장하지 않는다. 중요한 것은 “HTTP 요청의 Cookie와 Form body가 암호화 없이 관찰된다”는 사실이다.

---

## Wireshark 필터

로그인 요청을 찾을 때 유용한 필터:

```wireshark
http.request.method == "POST"
```

로그인 경로를 직접 찾을 때:

```wireshark
http.request.uri contains "login"
```

세션 식별자를 볼 때:

```wireshark
http.cookie || http.set_cookie
```

본문에서 문자열을 찾을 때:

```wireshark
http contains "loginProc"
```

패킷을 고른 뒤에는 `Follow -> HTTP Stream`으로 요청과 응답 흐름을 이어서 볼 수 있다.

---

## 보안 의미

HTTP는 암호화가 없기 때문에 다음 정보가 네트워크에 평문으로 흐를 수 있다.

- 요청 경로
- Host와 Referer
- Cookie와 세션 식별자
- `application/x-www-form-urlencoded` Form body
- 로그인 ID와 비밀번호 같은 입력값

따라서 ARP Spoofing으로 트래픽 경로를 장악한 공격자는 HTTP 로그인 정보와 세션 식별자를 관찰할 수 있다.

같은 조건에서 평문 데이터는 관찰에 그치지 않고 변조될 수도 있다. 단순 문자열 변조 흐름은 [[Ettercap Filter 패킷 변조 실습]]에서 확인한다.

방어 관점에서는 로그인과 세션이 필요한 웹 서비스에 HTTPS를 적용해야 한다.

---

## Telnet / HTTP / SSH 비교

| 항목 | [[Telnet 평문 노출|Telnet]] | HTTP | [[SSH 암호화 패킷 관찰|SSH]] |
| --- | --- | --- | --- |
| 기본 포트 | TCP/23 | TCP/80 또는 웹 서버 포트 | TCP/22 |
| 관찰 가능 정보 | Username/Password | Cookie, Form body, 로그인 입력값 | Key Exchange 이후 암호화된 패킷 |
| Wireshark 표시 | `User Access Verification`, `Username`, `Password` | `POST`, `Cookie`, `HTML Form URL Encoded` | `New Keys`, `Encrypted packet` |
| 보안 의미 | 인증 정보 평문 노출 | 웹 인증/세션 정보 평문 노출 | 내용 해석이 어려움 |

---

## 관련 노트

- [[ARP 스푸핑]]
- [[Telnet 평문 노출]]
- [[Ettercap Filter 패킷 변조 실습]]
- [[SSH 암호화 패킷 관찰]]
- [[MITM]]
- [[Wireshark]]
