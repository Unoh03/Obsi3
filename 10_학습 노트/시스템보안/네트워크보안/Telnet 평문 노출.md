---
type: lab
topic: network-security
parent_moc: "[[10_학습 노트/시스템보안/네트워크보안/00_네트워크보안_목차]]"
source: lab-observation
status: stable
created: 2026-05-13
tags:
  - 🏷️과목/네트워크보안
  - 🏷️주제/Telnet
  - 🏷️주제/Plaintext
  - 🏷️주제/MITM
---

# Telnet 평문 노출

## 한 줄 요약

Telnet은 암호화가 없기 때문에 ARP Spoofing으로 MITM 위치를 확보한 공격자가 Wireshark에서 로그인 계정과 비밀번호를 평문으로 관찰할 수 있다.

---

## 실습 맥락

[[ARP 스푸핑]]으로 Windows Victim과 Router 사이의 트래픽을 Kali Attacker가 경유하도록 만들었다.

```text
Windows Victim ↔ Kali Attacker ↔ Router
```

이후 Router에 Telnet 계정을 만들고 Windows에서 Router로 Telnet 접속을 수행했다.

---

## Wireshark TCP Stream 관찰

TCP Stream에서 관찰된 핵심:

```text
User Access Verification
Username:
unoh
Password:
<REDACTED>
R1>
```

Telnet은 암호화가 없기 때문에 Username과 Password가 네트워크에 그대로 흐른다.

Wireshark에서 글자가 중복되어 보일 수 있는데, 이는 Telnet 입력 문자와 서버 echo가 함께 잡히기 때문이다.

> [!warning] 실습 메모
> 비밀번호 원문은 노트에 저장하지 않는다. 실습 결과를 남길 때는 계정 정보 자체보다 “Telnet 인증 정보가 평문으로 노출된다”는 보안 의미를 기록하는 것이 중요하다.

---

## 보안 의미

- ARP Spoofing 자체는 트래픽 경로를 공격자 쪽으로 우회시키는 역할을 한다.
- Telnet은 인증 정보와 명령 입력이 평문으로 흐른다.
- 두 조건이 결합되면 MITM 위치의 공격자가 계정 정보를 탈취할 수 있다.
- 원격 장비 접속에는 Telnet 대신 [[SSH 암호화 패킷 관찰|SSH]]를 사용해야 한다.

---

## Telnet과 SSH 비교

| 항목 | Telnet | SSH |
| --- | --- | --- |
| 포트 | TCP/23 | TCP/22 |
| 계정 정보 | Username/Password가 평문으로 보임 | Username/Password가 평문으로 보이지 않음 |
| Wireshark 관찰 | `User Access Verification`, `Username`, `Password` 확인 가능 | Key Exchange 이후 `Encrypted packet`으로 표시 |
| 보안 의미 | MITM에서 인증 정보 탈취 가능 | 패킷은 관찰되지만 내용 해석은 어려움 |

---

## 관련 노트

- [[ARP 스푸핑]]
- [[SSH 암호화 패킷 관찰]]
- [[MITM]]
- [[Wireshark]]
