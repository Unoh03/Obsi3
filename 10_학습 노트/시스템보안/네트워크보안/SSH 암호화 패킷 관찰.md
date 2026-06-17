---
type: lab
topic: network-security
source: lab-observation
status: complete
created: 2026-05-13
tags:
  - 🏷️과목/네트워크보안
  - 🏷️주제/SSH
  - 🏷️주제/MITM
  - 🏷️주제/Encryption
  - 🏷️상태/complete
---

# SSH 암호화 패킷 관찰

## 한 줄 요약

SSH는 ARP Spoofing으로 MITM 위치를 확보해도 Key Exchange 이후 패킷 내용이 암호화되어 Telnet처럼 로그인 정보가 평문으로 보이지 않는다.

---

> [!note] 노트 역할
> 이 노트는 PDF 65~78쪽 전체 요약이 아니라, 정상 SSH 연결에서 암호화 패킷이 어떻게 관찰되는지 정리한 별도 실습 노트다.
> SSH 구조, Downgrade 원리, Ettercap MITM 실습은 아래 노트를 참고한다.
>
> - [[SSH 보안 구조]]
> - [[SSH Downgrade Attack]]
> - [[SSH MITM 실습]]

---

## 실습 맥락

[[ARP 스푸핑]]으로 Windows Victim과 Router 사이의 트래픽을 Kali Attacker가 경유하도록 만든 뒤, Telnet 대신 SSH로 Router에 접속했다.

---

## SSH 접속 시도

처음 일반 SSH 접속은 실패했다.

```cmd
ssh unoh@172.16.0.254
```

오류:

```text
Unable to negotiate with 172.16.0.254 port 22: no matching key exchange method found.
Their offer: diffie-hellman-group1-sha1
```

원인은 라우터가 오래된 SSH 알고리즘인 `diffie-hellman-group1-sha1`만 제안했고, Windows OpenSSH 클라이언트가 이를 기본적으로 거부했기 때문이다.

---

## 실습용 호환 접속 명령

실습에서는 구형 알고리즘을 임시로 허용해서 접속했다.

```cmd
ssh -oKexAlgorithms=+diffie-hellman-group1-sha1 -oHostKeyAlgorithms=+ssh-rsa -oCiphers=+aes128-cbc,3des-cbc unoh@172.16.0.254
```

> [!warning] 운영 환경 주의
> `diffie-hellman-group1-sha1`, `ssh-rsa`, `aes128-cbc`, `3des-cbc`는 오래된 호환용 알고리즘이다. 실습 장비 접속 확인용으로만 사용하고, 운영 환경에서는 사용하지 않는다.

---

## Wireshark 관찰

Wireshark에서는 다음 흐름이 보였다.

```text
Client: Protocol (SSH-2.0-OpenSSH_for_Windows_8.1)
Server: Protocol (SSH-2.0-Cisco-1.25)
Client: Diffie-Hellman Key Exchange Init
Server: Diffie-Hellman Key Exchange Reply
Client: New Keys
Server: New Keys
Client: Encrypted packet
Server: Encrypted packet
```

관찰 포인트:

- SSH 배너와 Key Exchange 과정은 보인다.
- New Keys 이후에는 패킷이 `Encrypted packet`으로 표시된다.
- Telnet처럼 `Username`이나 `Password`가 평문으로 보이지 않는다.

---

## Telnet과 SSH 비교

| 항목 | [[Telnet 평문 노출|Telnet]] | SSH |
| --- | --- | --- |
| 포트 | TCP/23 | TCP/22 |
| 계정 정보 | Username/Password가 평문으로 보임 | Username/Password가 평문으로 보이지 않음 |
| Wireshark 관찰 | `User Access Verification`, `Username`, `Password` 확인 가능 | Key Exchange 이후 `Encrypted packet`으로 표시 |
| 보안 의미 | MITM에서 인증 정보 탈취 가능 | 패킷은 관찰되지만 내용 해석은 어려움 |

---

## 결론

ARP Spoofing으로 트래픽 경로를 장악하더라도, SSH처럼 암호화된 프로토콜을 사용하면 Telnet처럼 로그인 정보가 그대로 노출되지는 않는다.
평문 TCP에서 문자열이 실제로 바뀌는 흐름은 [[Ettercap Filter 패킷 변조 실습]]과 대비해서 보면 좋다.

---

## 관련 노트

- [[SSH 보안 구조]]
- [[SSH Downgrade Attack]]
- [[SSH MITM 실습]]
- [[Ettercap Filter 패킷 변조 실습]]
- [[ARP 스푸핑]]
- [[Telnet 평문 노출]]
- [[MITM]]
- [[Wireshark]]
