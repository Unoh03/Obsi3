---
type: lab
topic: aws
source:
  - AWS기초.pdf
  - lab-observation
source_pages:
  - "72-81"
status: active
created: 2026-06-04
reviewed: 2026-06-05
aliases:
  - NAT Instance outbound 실습
  - Private EC2 NAT 통신 실습
tags:
  - 🏷️과목/AWS
  - 🏷️주제/VPC
  - 🏷️주제/NAT
  - 🏷️주제/NATInstance
  - 🏷️주제/RouteTable
  - 🏷️상태/active
---

# NAT Instance 실습

## 실습 결과

> [!summary] Private EC2의 외부 통신 성공
> Public Subnet에 있는 Amazon Linux 2023 EC2를 NAT Instance처럼 설정했다. NAT Instance에서 IP forwarding과 `iptables` MASQUERADE 규칙을 적용한 뒤, Private EC2에 SSH로 접속해 `8.8.8.8` ping 통신이 되는 것을 확인했다.

이번 실습이 증명한 것은 다음 한 줄이다.

```text
Private EC2
-> NAT Instance
-> Internet Gateway
-> Internet
```

Private EC2는 외부에서 직접 들어오는 서버가 아니라, 내부에서 시작한 outbound traffic을 NAT Instance를 통해 밖으로 내보내는 서버로 동작했다.

## 확인한 구성

| 항목 | 값 또는 상태 |
| --- | --- |
| NAT Instance OS | Amazon Linux 2023 |
| NAT Instance 내부 주소 | `192.168.10.214` |
| Private EC2 내부 주소 | `192.168.20.115` |
| NAT outbound interface | `ens5` |
| NAT 규칙 | `POSTROUTING` chain에 `MASQUERADE` 적용 |
| AWS Console 조건 | Source/Destination Check 중지, Private Route Table 기본 경로를 NAT Instance로 지정 |
| 검증 | Private EC2에서 `8.8.8.8` ping 성공 |

> [!important] NAT Instance는 Linux 설정만으로 완성되지 않는다
> EC2 내부에서 IP forwarding과 `iptables`를 설정해야 하지만, AWS Console 쪽에서도 NAT Instance의 Source/Destination Check를 중지하고 Private Route Table의 기본 경로를 NAT Instance로 보내야 한다. Private EC2에서 외부 ping이 성공했다면 이 경로가 기능적으로 연결된 것이다.

## AWS Console 쪽 필수 조건

NAT Instance는 일반 EC2를 "중간에서 대신 내보내는 장비"처럼 쓰는 구성이다. 그래서 EC2 내부 Linux 설정 전에 AWS Console 쪽에서도 다음 두 조건이 맞아야 한다.

| 항목 | 필요한 설정 | 안 맞으면 생기는 현상 |
| --- | --- | --- |
| Source/Destination Check | NAT Instance에서 중지 | Private EC2의 packet을 NAT Instance가 대신 전달하지 못함 |
| Private Route Table | `0.0.0.0/0 -> NAT Instance` | Private EC2의 인터넷 목적지 traffic이 NAT Instance로 가지 않음 |

Source/Destination Check를 끄는 위치:

```text
EC2 Console
-> Instances
-> NAT Instance 선택
-> Actions
-> Networking
-> Change source/destination check
-> Stop
```

AWS CLI를 쓸 수 있는 환경이면 다음 명령으로도 끌 수 있다.

```bash
aws ec2 modify-instance-attribute --instance-id <NAT_INSTANCE_ID> --no-source-dest-check
```

> [!important] 왜 꺼야 하는가
> 기본 EC2는 자신이 source 또는 destination인 traffic만 처리한다고 가정한다. NAT Instance는 Private EC2가 만든 packet을 받아 밖으로 내보내고 응답을 다시 돌려줘야 하므로, source/destination check를 끄지 않으면 NAT 장비처럼 동작할 수 없다.

## NAT Instance 내부 설정

### 1. IP forwarding 활성화

```bash
sudo sysctl -w net.ipv4.ip_forward=1
```

확인된 출력:

```text
net.ipv4.ip_forward = 1
```

이 설정은 NAT Instance가 자기 자신을 목적지로 하는 packet만 처리하지 않고, Private EC2의 packet도 받아서 전달할 수 있게 한다.

재부팅 후에도 유지하려면 다음처럼 영구 적용한다.

```bash
echo 'net.ipv4.ip_forward = 1' | sudo tee /etc/sysctl.d/99-nat-instance.conf
sudo sysctl --system
sysctl net.ipv4.ip_forward
```

### 2. iptables service 설치

```bash
sudo yum install -y iptables-services
```

Amazon Linux 2023에서는 Ubuntu와 다르게 `yum`/`dnf` 계열로 package를 설치한다. 이번 실습에서는 `iptables-services`를 설치한 뒤 NAT table에 규칙을 추가했다.

### 3. MASQUERADE 규칙 추가

```bash
sudo iptables -t nat -A POSTROUTING -o ens5 -j MASQUERADE
```

이 규칙은 `ens5`를 통해 밖으로 나가는 packet의 source address를 NAT Instance의 외부 통신 가능한 주소로 바꿔준다.

이번 기록의 NAT Instance는 Amazon Linux 2023이므로, 재부팅 후에도 NAT 규칙을 유지하려면 `iptables-services` 기준으로 저장한다.

```bash
sudo iptables-save | sudo tee /etc/sysconfig/iptables >/dev/null
sudo systemctl enable --now iptables
```

Ubuntu로 NAT Instance를 만들었다면 `iptables-persistent`를 사용한다.

```bash
sudo apt-get update
sudo apt-get install -y iptables-persistent
sudo netfilter-persistent save
```

### 4. NAT 규칙 확인

```bash
sudo iptables -t nat -L
```

확인된 출력:

```text
Chain PREROUTING (policy ACCEPT)
target     prot opt source               destination

Chain INPUT (policy ACCEPT)
target     prot opt source               destination

Chain OUTPUT (policy ACCEPT)
target     prot opt source               destination

Chain POSTROUTING (policy ACCEPT)
target     prot opt source               destination
MASQUERADE  all  --  anywhere             anywhere
```

`POSTROUTING` chain에 `MASQUERADE`가 보이면 NAT 변환 규칙이 들어간 것이다.

## Private EC2에서 검증

Public Subnet 쪽 EC2에서 Private EC2로 SSH 접속했다.

```bash
ssh -i test-private1.pem ec2-user@192.168.20.115
```

Private EC2 접속 후 외부 주소로 ping을 실행했고, `8.8.8.8` 통신이 되는 것을 확인했다.

```bash
ping 8.8.8.8
```

> [!summary] 검증 의미
> Private EC2는 public IP 없이도 외부로 packet을 내보냈다. 이 결과는 Private Route Table의 기본 경로가 NAT Instance로 향하고, NAT Instance가 packet forwarding과 MASQUERADE를 수행한다는 것을 보여준다.

## 실습 중 분리한 문제

### VS Code Remote-SSH 멈춤

실습 중 VS Code Remote-SSH가 `VS Code 서버를 초기화하는 중` 상태로 멈추고 SSH 접속이 지연되었다. 이 문제는 NAT 설정 자체와 별개였다.

정리한 복구 명령은 [[10_학습 노트/클라우드/AWS/서버_시퓨_100%_찍을_때|EC2 서버가 멈추거나 CPU 100% 찍을 때]]에 따로 둔다.

### Swapfile 중복 실행

서버 부하를 줄이려고 swapfile을 추가하는 과정에서 이미 활성화된 `/swapfile`을 다시 만들려고 해서 `Text file busy`, `Device or resource busy`가 발생했다. 이 역시 NAT 구성 실패가 아니라 서버 운영 보조 작업의 중복 실행 문제였다.

## 다시 할 때 필요한 최소 순서

아래 명령은 즉시 통신 검증에 필요한 최소 흐름이다. 재부팅 후 유지까지 필요하면 다음 섹션의 남은 확인을 처리한다.

1. Public Subnet에 NAT Instance로 쓸 EC2를 둔다.
2. NAT Instance의 Source/Destination Check를 중지한다.
3. Private Route Table의 `0.0.0.0/0` target을 NAT Instance로 설정한다.
4. NAT Instance에서 IP forwarding을 켠다.
5. NAT Instance에서 `iptables` MASQUERADE 규칙을 추가한다.
6. Private EC2에서 외부 주소로 ping 또는 curl을 실행한다.

```bash
sudo sysctl -w net.ipv4.ip_forward=1
sudo yum install -y iptables-services
sudo iptables -t nat -A POSTROUTING -o ens5 -j MASQUERADE
sudo iptables -t nat -L
```

```bash
ssh -i test-private1.pem ec2-user@192.168.20.115
ping 8.8.8.8
```

## 남은 확인

이번 실습은 Private EC2의 즉시 outbound 통신 성공까지 확인했다. 다만 현재 기록된 `sysctl -w`와 `iptables -A` 명령은 재부팅 후 자동 유지까지 보장하지 않는다.

재부팅 후에도 NAT Instance로 계속 사용할 경우에는 별도로 다음 항목을 확인한다.

```bash
echo 'net.ipv4.ip_forward = 1' | sudo tee /etc/sysctl.d/99-nat.conf
sudo iptables-save | sudo tee /etc/sysconfig/iptables >/dev/null
sudo systemctl enable --now iptables
```

재부팅 후 확인:

```bash
sysctl net.ipv4.ip_forward
sudo iptables -t nat -L POSTROUTING -n -v
```

## 오해하기 쉬운 지점

| 오해 | 정리 |
| --- | --- |
| `iptables`만 설정하면 NAT Instance가 완성된다 | AWS Console에서 Source/Destination Check와 Private Route Table도 맞아야 한다. |
| Private EC2가 외부 ping에 성공했으니 외부에서 Private EC2로 접속할 수 있다 | 아니다. NAT는 Private EC2가 시작한 outbound 통신을 처리한다. |
| NAT Instance와 Bastion Host는 같은 역할이다 | Bastion Host는 관리 접속 경유지이고, NAT Instance는 Private Subnet outbound 변환 장치다. |
| VS Code Remote-SSH 멈춤은 NAT 문제다 | 이번 실습에서는 서버 부하/VS Code 서버 초기화 문제로 분리해서 다뤘다. |

## 관련 노트

- [[10_학습 노트/클라우드/AWS/개념 노트/NAT Gateway와 NAT Instance 구성 기초|NAT Gateway와 NAT Instance 구성 기초]]
- [[10_학습 노트/클라우드/AWS/개념 노트/Multi-AZ와 Bastion, NAT 구성 기초|Multi-AZ와 Bastion, NAT 구성 기초]]
- [[10_학습 노트/클라우드/AWS/실습 노트/VPC 실습|VPC 실습]]
- [[10_학습 노트/클라우드/AWS/서버_시퓨_100%_찍을_때|EC2 서버가 멈추거나 CPU 100% 찍을 때]]

## 참고 자료

- [AWS Docs, Work with NAT instances](https://docs.aws.amazon.com/vpc/latest/userguide/work-with-nat-instances.html) - NAT Instance는 Source/Destination Check를 중지하고 Private Route Table을 NAT Instance로 보내야 한다.
- [AWS Docs, NAT gateway use cases](https://docs.aws.amazon.com/vpc/latest/userguide/nat-gateway-scenarios.html) - Private Subnet의 instance가 외부로 나가되 인터넷에서 직접 시작한 연결은 받지 않는 NAT 흐름을 설명한다.
