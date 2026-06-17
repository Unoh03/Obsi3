---
type: concept
topic: aws
source: AWS기초.pdf
source_pages:
  - "72-85"
status: active
created: 2026-06-04
reviewed: 2026-06-05
aliases:
  - AWS NAT 기초
  - NAT Gateway와 NAT Instance
  - Private Subnet outbound
tags:
  - 🏷️과목/AWS
  - 🏷️주제/VPC
  - 🏷️주제/NAT
  - 🏷️주제/RouteTable
  - 🏷️주제/BastionHost
  - 🏷️상태/active
---

# NAT Gateway와 NAT Instance 구성 기초

## 한 줄 요약

NAT는 Private Subnet의 리소스가 외부로 나가는 연결을 시작할 수 있게 하되, 외부에서 Private Subnet 리소스로 직접 새 연결을 시작하지 못하게 하는 outbound 경로다.

## 먼저 잡아야 할 핵심

NAT Gateway와 NAT Instance의 기본 목적은 같다. 둘 다 Private Subnet의 instance가 internet 또는 VPC 밖의 서비스로 나갈 때 source address를 NAT 장치의 주소로 변환한다.

하지만 **결과가 완벽히 같다고 보면 안 된다.** 기본적인 web update, package download 같은 outbound 목적에서는 비슷한 결과를 만들지만, 운영 방식과 제약은 다르다.

| 구분 | NAT Gateway | NAT Instance |
| --- | --- | --- |
| 기본 목적 | Private Subnet outbound NAT | Private Subnet outbound NAT |
| 관리 주체 | AWS 관리형 | 사용자가 EC2 instance로 직접 관리 |
| Security Group | NAT Gateway 자체에는 연결 불가 | NAT Instance에 연결 가능 |
| 확장성 | 자동 확장, 높은 bandwidth | instance type 성능에 의존 |
| 고가용성 | AZ 안에서 redundant. AZ별 NAT Gateway 권장 | failover 직접 구성 필요 |
| 커스터마이징 | 제한적 | port forwarding, bastion 겸용 등 직접 구성 가능 |
| 현재 권장 | 일반적으로 권장 | 특수 요구나 실습, 비용 실험에서 검토 |

> [!important] 같은 목적, 다른 제품
> “Private EC2가 외부로 나가고 외부에서는 Private EC2로 직접 못 들어온다”는 큰 목적은 같다. 그러나 성능, 가용성, 보안 그룹 적용, timeout 동작, IP fragmentation 처리, 운영 책임이 다르므로 완전히 같은 결과라고 단정하면 안 된다.

## 자료 범위와 읽는 기준

- 주 자료: [[40_자료/강의 자료/AWS기초.pdf|AWS 기초]], PDF viewer 기준 p.72-85
- p.72는 NAT의 목적을 설명한다.
- p.73-81은 NAT Instance를 구성할 때 필요한 조건을 보여준다.
- p.82-85는 NAT Instance, Bastion Host, Web EC2, RDS를 묶은 후속 실습 구조다.
- PDF는 `Copyright © 2018` 자료다. 특히 p.73-75의 NAT AMI 검색 흐름과 p.77의 `All traffic / 위치 무관` 보안 그룹은 현재 AWS 공식 문서 기준으로 보정해서 읽는다.

## p.72: NAT가 필요한 이유

p.72는 NAT를 다음 상황에서 사용한다고 설명한다.

- Private Subnet의 instance가 software update, security patch, 외부 API 호출을 해야 한다.
- 그러나 외부 internet에서 해당 Private Subnet instance로 직접 접근할 필요는 없다.
- 내부 private IP를 외부에 보이는 public address 쪽으로 변환한다.

흐름은 이렇게 읽으면 된다.

```text
Private EC2
-> NAT Gateway or NAT Instance
-> Internet Gateway
-> Internet
```

응답은 같은 NAT 장치를 거쳐 원래 요청을 시작한 Private EC2로 돌아간다. 외부에서 임의로 Private EC2에 새 연결을 시작하는 경로는 아니다.

## p.73-81: NAT Instance를 만들 때 필요한 조건

PDF의 NAT Instance 실습 절차는 클릭 순서보다 “NAT Instance가 어떤 조건을 만족해야 하는가”를 보는 데 중요하다.

| PDF page | 설정 | 의미 |
| --- | --- | --- |
| p.73-75 | NAT AMI 검색과 선택 | NAT 역할을 수행할 EC2 image 선택 |
| p.76 | Public Subnet에 생성, Public IP 자동 할당 | NAT Instance가 internet으로 나갈 수 있어야 함 |
| p.77 | Security Group 설정 | NAT Instance가 받아 처리할 traffic 범위 제어 |
| p.78 | Source / Destination Check 중지 | 자기 자신이 목적지가 아닌 packet도 전달해야 함 |
| p.79-80 | Private Route Table에 `0.0.0.0/0 -> NAT Instance` 추가 | Private Subnet의 기본 outbound 경로를 NAT로 보냄 |
| p.81 | Bastion Host를 통해 Private EC2 접속 후 외부 통신 확인 | Private EC2가 직접 public으로 열리지 않아도 outbound가 되는지 검증 |

> [!warning] p.77의 `All traffic / 위치 무관`은 수업용 단순화로 본다
> 현재 AWS NAT Instance 절차는 HTTP/HTTPS는 Private Subnet CIDR에서만 받고, SSH는 관리자 네트워크 대역에서만 받는 식으로 source를 좁히는 구성을 제시한다. ping 검증이 필요하면 ICMP도 검증 목적에 맞게 별도 규칙으로 제한해서 추가한다.

> [!note] NAT AMI는 현재 그대로 따라갈 대상이 아니다
> AWS 문서는 기존 NAT AMI가 Amazon Linux AMI 2018.03 기반이며 지원 종료된 상태라고 설명한다. NAT Instance가 필요한 경우에는 현재 Amazon Linux 기반으로 직접 NAT AMI를 만들거나, 일반적으로는 NAT Gateway로 전환하는 방향을 먼저 검토한다.

> [!important] NAT Instance는 Public Subnet에 있어야 한다
> NAT Instance가 internet으로 packet을 내보내려면 Public Subnet의 route table이 IGW로 향해야 하고, NAT Instance에는 Public IPv4 또는 Elastic IP가 필요하다.

> [!important] Source / Destination Check를 꺼야 한다
> EC2 instance는 기본적으로 자기 자신이 source 또는 destination인 traffic을 처리한다고 가정한다. NAT Instance는 다른 instance의 packet을 대신 전달해야 하므로 Source / Destination Check를 중지해야 한다.

## NAT Gateway와 NAT Instance는 완전히 같은가

완전히 같지 않다. 단순한 학습 단계에서는 다음처럼 이해해도 된다.

```text
Private EC2 outbound internet 통신
= NAT Gateway로도 가능
= NAT Instance로도 가능
```

하지만 운영 관점에서는 차이가 크다.

| 차이 | 왜 중요한가 |
| --- | --- |
| NAT Gateway는 관리형이고 NAT Instance는 직접 운영 | patch, 장애 대응, instance size 선택 책임이 달라짐 |
| NAT Gateway는 Security Group을 붙일 수 없음 | NAT Gateway 자체가 아니라 뒤쪽 instance와 subnet의 NACL/SG로 제어해야 함 |
| NAT Instance는 Security Group과 OS 설정을 직접 제어 가능 | 더 유연하지만 잘못 열면 노출면이 커짐 |
| NAT Gateway는 port forwarding과 bastion server 용도를 지원하지 않음 | NAT Instance처럼 겸용 장비로 쓰기 어렵다 |
| NAT Gateway는 AZ별로 만들고 같은 AZ 자원이 쓰게 하는 구성이 권장됨 | 한 AZ의 NAT 장애가 다른 AZ의 outbound까지 끊지 않게 하기 위함 |
| timeout, fragmentation 처리 방식도 다름 | 대량 traffic, 특수 protocol, 장시간 연결에서 결과가 달라질 수 있음 |

> [!summary] 실습용 판단
> 지금 수업 범위에서는 “둘 다 Private Subnet outbound를 만든다”가 핵심이다. 다만 “가격과 작동 방식만 다르고 결과는 완벽히 같다”는 표현은 틀리다. 같은 목적을 수행하지만 운영 특성과 제약이 다른 NAT device다.

## p.82-85: 후속 실습 구조

p.82-85는 NAT만 따로 보는 단계에서, 웹 서버와 RDS까지 묶은 구조로 넘어간다.

| 구성요소 | 역할 |
| --- | --- |
| NAT Instance | Private Subnet 쪽 자원의 외부 통신 |
| Bastion Host | Private 자원 접근 경유지 |
| Web EC2 | 외부 브라우저가 접근할 웹 서버 |
| RDS MariaDB | Web Server가 사용할 database와 table |

p.85는 목표를 이렇게 정리한다.

```text
웹 브라우저
-> Web EC2
-> RDS MariaDB
```

이 구조에서는 NAT가 “웹 브라우저가 Web EC2에 들어오는 길”이 아니다. NAT는 Private Subnet의 리소스가 update나 외부 통신을 위해 밖으로 나가는 길이다.

## 다음 실습에서 확인할 것

| 확인 항목 | 성공 기준 |
| --- | --- |
| NAT Instance 위치 | Public Subnet에 있음 |
| NAT Instance public address | Public IPv4 또는 Elastic IP가 있음 |
| NAT Instance Security Group | 필요한 traffic만 Private Subnet CIDR 또는 관리자 IP 대역으로 제한 |
| Source / Destination Check | 중지되어 있음 |
| Private Route Table | `0.0.0.0/0` target이 NAT Instance |
| Private EC2 outbound | Private EC2에서 외부 주소로 요청 가능 |
| 외부 inbound 차단 | 외부에서 Private EC2로 직접 접근 불가 |

## 오해하기 쉬운 지점

| 오해 | 정확한 이해 |
| --- | --- |
| NAT가 있으면 Private EC2로 외부에서 접속할 수 있다 | NAT는 Private EC2가 시작한 outbound 연결의 응답을 돌려주는 장치다. |
| NAT Gateway와 NAT Instance는 완전히 같은 결과를 만든다 | 기본 outbound 목적은 같지만 운영, 성능, 보안 제어, 제약이 다르다. |
| NAT Instance는 아무 subnet에 있어도 된다 | internet으로 나가야 하므로 Public Subnet에 배치한다. |
| Route Table만 바꾸면 NAT Instance가 된다 | Source / Destination Check 중지와 instance 자체 NAT 설정이 필요하다. |
| NAT Instance가 Bastion Host와 같은 것이다 | 둘 다 Public Subnet에 놓일 수 있지만 목적은 다르다. NAT는 outbound 변환, Bastion은 관리 접속 경유다. |

## 관련 노트

- [[10_학습 노트/클라우드/AWS/개념 노트/VPC 네트워크 기초|VPC 네트워크 기초]]
- [[10_학습 노트/클라우드/AWS/개념 노트/Multi-AZ와 Bastion, NAT 구성 기초|Multi-AZ와 Bastion, NAT 구성 기초]]
- [[10_학습 노트/클라우드/AWS/실습 노트/VPC 실습|VPC 실습]]
- [[10_학습 노트/클라우드/AWS/실습 노트/NAT Instance 실습|NAT Instance 실습]]

## 참고 자료

- [[40_자료/강의 자료/AWS기초.pdf|AWS 기초 PDF]] - PDF viewer 기준 p.72-85
- [AWS 공식 문서 - NAT gateways](https://docs.aws.amazon.com/vpc/latest/userguide/vpc-nat-gateway.html)
- [AWS 공식 문서 - NAT gateway basics](https://docs.aws.amazon.com/vpc/latest/userguide/nat-gateway-basics.html)
- [AWS 공식 문서 - NAT instances](https://docs.aws.amazon.com/vpc/latest/userguide/VPC_NAT_Instance.html)
- [AWS 공식 문서 - Enable private resources to communicate outside the VPC](https://docs.aws.amazon.com/vpc/latest/userguide/work-with-nat-instances.html)
- [AWS 공식 문서 - Compare NAT gateways and NAT instances](https://docs.aws.amazon.com/vpc/latest/userguide/vpc-nat-comparison.html)
