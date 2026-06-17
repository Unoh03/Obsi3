---
type: concept
topic: aws
source: AWS기초.pdf
source_pages:
  - 2
  - 3
  - 4
  - 5
  - 6
  - 7
  - 8
  - 9
  - 10
  - 11
  - 12
status: active
created: 2026-06-01
reviewed: 2026-06-05
aliases:
  - AWS 입문
  - 클라우드 컴퓨팅 입문
tags:
  - 🏷️과목/AWS
  - 🏷️주제/CloudComputing
  - 🏷️주제/DevOps
  - 🏷️주제/IaC
  - 🏷️상태/active
---

# 클라우드 컴퓨팅과 AWS 입문

## 한 줄 요약

클라우드 컴퓨팅은 서버를 직접 구매하고 유지하는 방식만 고집하지 않고, 필요한 IT 리소스를 네트워크를 통해 온디맨드로 사용하고 사용량에 따라 비용을 지불하는 방식이다. AWS는 이를 지원하는 Amazon의 클라우드 서비스 모음이다.

## 자료 범위와 읽는 기준

- 주 자료: [[40_자료/강의 자료/AWS기초.pdf|AWS 기초]], PDF viewer 기준 p.2-12
- 보조 자료: [[10_학습 노트/클라우드/AWS/RAW 메모|RAW 메모]]
- PDF는 `Copyright © 2018` 자료다. 서비스 명칭, 책임 범위, 비용 정책은 현재 공식 문서로 보정했다.
- p.5의 CSP 시장 그래프는 시점 의존 자료이므로 현재 점유율이나 순위를 설명하는 근거로 사용하지 않는다.

## 클라우드 컴퓨팅과 On-Demand
![[40_자료/캡쳐 창고/AWS기초.webp]]
[[AWS기초.pdf#page=2&rect=67,33,796,467|AWS기초, p.2]]
### On-Premises

On-Premises는 조직이 서버, 스토리지, 네트워크 같은 인프라를 직접 소유하거나 직접 통제하는 환경에 구축하고 운영하는 방식이다. 초기 구매, 용량 산정, 설치, 유지보수, 장애 대응을 조직이 맡는다.

### Cloud Computing의 On-Demand 사용 방식

AWS는 클라우드 컴퓨팅을 인터넷을 통한 IT 리소스의 온디맨드 제공과 사용량 기반 비용 지불로 설명한다. 필요한 시점에 리소스를 만들고 줄이거나 제거할 수 있으므로, 처음부터 최대 용량의 장비를 구매할 필요가 줄어든다.

> [!important] On-Premises와 On-Demand는 정확한 반대말이 아니다
> `On-Premises`는 인프라를 어디에서 어떤 운영 경계로 관리하는지에 가깝고, `On-Demand`는 리소스를 필요한 시점에 조달하고 사용하는 방식에 가깝다. 비교할 수는 있지만 같은 축의 용어로 단순화하면 안 된다.

## Public Cloud와 Private Cloud
![[40_자료/캡쳐 창고/AWS기초 1.webp]]
[[AWS기초.pdf#page=3&rect=72,87,873,462|AWS기초, p.3]]

| 구분 | Public Cloud | Private Cloud |
| --- | --- | --- |
| 사용 범위 | 여러 고객에게 제공되는 클라우드 서비스 | 한 조직 전용으로 제공되는 클라우드 환경 |
| 운영 형태 | 클라우드 제공업체가 공용 서비스 기반을 운영 | 조직 내부, 외부 관리형 환경, 가상 사설 환경 등으로 구성 가능 |
| 핵심 질문 | 제공업체 서비스를 어떻게 안전하게 사용할 것인가 | 전용 환경을 누가 구축하고 운영할 것인가 |

> [!important] 배포 모델과 서비스 모델을 섞지 않는다
> Public / Private Cloud는 배포 형태를 구분한다. IaaS / PaaS / SaaS는 어떤 범위의 서비스를 제공받는지를 구분한다.

### 질문: OpenStack은 Public Cloud인가, Private Cloud인가?

OpenStack은 Public Cloud 또는 Private Cloud라는 분류 자체가 아니다. Compute, Storage, Networking 리소스를 API로 제어할 수 있게 하는 오픈소스 클라우드 컴퓨팅 플랫폼이다. 조직은 OpenStack을 이용해 Private Cloud를 구축할 수 있고, 서비스 제공자는 Public Cloud 기반으로 활용할 수도 있다.

## Shared Responsibility Model

Public Cloud를 사용해도 보안 책임이 모두 제공업체로 넘어가지는 않는다. AWS는 책임을 `Security of the Cloud`와 `Security in the Cloud`로 구분한다.

| 구분 | AWS의 책임 | 사용자의 책임 |
| --- | --- | --- |
| 의미 | 클라우드 자체의 보안 | 클라우드 안에서 구성하고 올린 것의 보안 |
| 예시 | 물리 시설, 하드웨어, 네트워크, 가상화 계층 | 데이터, 애플리케이션, 접근 권한, 서비스 설정 |
| EC2 예시 | EC2를 제공하는 기반 인프라 | Guest OS 패치, 설치한 애플리케이션, Security Group 구성 |

> [!important] 클라우드에 올린다고 보안 책임이 사라지지 않는다
> 어떤 책임을 AWS가 맡고 어떤 책임을 사용자가 맡는지는 선택한 서비스에 따라 달라진다. EC2처럼 사용자가 직접 운영하는 범위가 넓은 서비스에서는 OS와 애플리케이션 관리 책임도 남는다.

## 클라우드의 장점과 주의점

| 개념 | 의미 | 오해 방지 |
| --- | --- | --- |
| 탄력성 | 수요 변화에 따라 리소스를 늘리거나 줄이는 능력 | 무조건 자동으로 조정되는 것은 아니다 |
| 확장성 | 더 많은 부하를 처리하도록 시스템 규모를 키울 수 있는 능력 | Scale-up과 Scale-out 설계가 필요하다 |
| On-Demand | 필요할 때 리소스를 생성하고 사용량을 기준으로 비용을 지불 | 사용하지 않는 리소스를 방치하면 비용이 남을 수 있다 |
| 고가용성 | 일부 장애가 발생해도 서비스를 계속 제공할 수 있도록 구성 | AWS 사용만으로 자동 완성되지 않는다 |
| 재해 복구 | 장애나 재해 이후 목표 시간과 데이터 손실 범위에 맞춰 복구 | 백업, 복제, 복구 절차와 검증이 필요하다 |
| 유지관리 단순화 | 물리 장비 관리 부담을 줄일 수 있음 | 애플리케이션과 선택한 서비스 설정 책임까지 사라지는 것은 아니다 |

AWS는 고가용성과 재해 복구를 구현할 기반을 제공하지만, 실제 결과는 다중화, 백업, 복구 목표, 복구 절차를 어떻게 설계하고 검증했는지에 달려 있다.
## AWS는 무엇이며 왜 등장했는가

AWS의 공식 명칭은 **Amazon Web Services**다. AWS는 컴퓨팅, 스토리지, 데이터베이스, 네트워크 등 다양한 IT 리소스를 제공하는 클라우드 서비스 모음이다.

### 질문: AWS는 남는 서버를 팔면서 시작했는가?

RAW 메모의 표현은 기억을 돕기 위한 단순화로는 이해할 수 있지만, 그대로 사실로 쓰기는 어렵다. AWS의 공식 origins 설명은 Amazon이 소매 사업을 운영하면서 확장 가능한 서비스를 구축하기 어렵다는 문제를 겪었고, 재사용 가능한 API와 플랫폼에 집중한 경험이 다른 조직도 빠르게 서비스를 시작할 수 있는 기반으로 이어졌다고 설명한다. 핵심은 유휴 서버 판매가 아니라 **반복 가능한 인프라 역량의 서비스화**다.

## 다음 학습에 연결되는 개념

### DevOps

DevOps는 개발과 운영을 단순히 한 팀으로 합치는 명칭이 아니다. AWS는 이를 조직이 애플리케이션과 서비스를 빠르게 전달할 수 있게 하는 문화적 철학, 실천 방식, 도구의 결합으로 설명한다. 클라우드에서는 인프라 구성, 배포, 모니터링을 자동화하는 흐름과 연결된다.

### Mutable / Immutable Infrastructure

Mutable Infrastructure는 운영 중인 서버를 직접 변경하며 유지하는 방식에 가깝다. Immutable Infrastructure는 배포한 인프라를 제자리에서 계속 수정하기보다, 변경 사항을 반영한 새 리소스로 교체하는 방식이다.

> [!important] Immutable은 데이터까지 변경 금지라는 뜻이 아니다
> 애플리케이션 서버와 배포 단위를 일관되게 교체 가능한 형태로 운영한다는 의미다. 데이터베이스나 사용자 데이터까지 변경하지 않는다는 뜻으로 해석하면 안 된다.

### Terraform과 Infrastructure as Code
![[40_자료/캡쳐 창고/AWS기초 2.webp]]
[[AWS기초.pdf#page=10&rect=71,44,808,458|AWS기초, p.10]]
Terraform은 인프라를 선언적인 설정 파일로 정의하고 관리하는 Infrastructure as Code 도구다. 입문 단계에서는 다음 흐름만 기억하면 된다.

1. `Write`: 원하는 인프라 구성을 작성한다.
2. `Plan`: 적용될 변경 사항을 미리 확인한다.
3. `Apply`: 확인한 변경을 실제 환경에 반영한다.
## IaaS / PaaS / SaaS
![[40_자료/캡쳐 창고/AWS기초 3.webp]]
[[AWS기초.pdf#page=11&rect=69,42,828,457|AWS기초, p.11]]

| 모델 | 제공받는 범위 | 사용자가 집중하는 범위 | 입문 관점 |
| --- | --- | --- | --- |
| IaaS | 컴퓨팅, 스토리지, 네트워크 같은 인프라 | OS, 애플리케이션, 데이터, 세부 설정 | 가상 서버와 네트워크를 직접 구성하는 쪽에 가깝다 |
| PaaS | 애플리케이션 실행을 위한 관리형 플랫폼 | 애플리케이션 코드와 데이터 | 기반 환경 관리 부담을 줄인다 |
| SaaS | 완성된 애플리케이션 | 서비스 사용과 계정·데이터 관리 | 소프트웨어를 직접 설치·운영하는 부담을 줄인다 |

## 실습 전 운영 원칙

> [!warning] 비용과 리소스 정리
> AWS 실습에서는 만든 리소스를 정리할 책임이 사용자에게 있다. 실습 종료 시 EC2 인스턴스뿐 아니라 RDS 데이터베이스, EBS 볼륨, 스냅샷, 스토리지, Public IPv4 주소 또는 Elastic IP, 이후 다룰 NAT Gateway처럼 남아서 비용이 발생할 수 있는 리소스를 확인한다.
>
> Free Tier 또는 credit 조건은 강의 자료가 아니라 현재 계정 상태와 현재 공식 정책을 기준으로 확인한다. AWS 공식 문서는 2025년 7월 15일 이후 생성된 신규 계정에 별도의 Free Tier 안내를 제공하므로, 과거 강의 자료의 무료 조건을 그대로 적용하면 안 된다.

## 다음 학습 연결

- EC2와 Region / Availability Zone
- VPC와 Subnet
- Public / Private EC2 접근 검증 실습

## 출처

- [[40_자료/강의 자료/AWS기초.pdf|AWS 기초]], PDF viewer 기준 p.2-12
- [AWS Overview: What is Cloud Computing?](https://docs.aws.amazon.com/whitepapers/latest/aws-overview/what-is-cloud-computing.html)
- [AWS Overview: Types of Cloud Computing](https://docs.aws.amazon.com/whitepapers/latest/aws-overview/types-of-cloud-computing.html)
- [AWS: What is Private Cloud?](https://aws.amazon.com/what-is/private-cloud/)
- [AWS Shared Responsibility Model](https://aws.amazon.com/compliance/shared-responsibility-model/)
- [AWS: Our Origins](https://aws.amazon.com/about-aws/our-origins/)
- [AWS: What is DevOps?](https://aws.amazon.com/devops/what-is-devops)
- [AWS Well-Architected Framework: Deploy changes with automation](https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/rel_tracking_change_management_immutable_infrastructure.html)
- [AWS Well-Architected Framework: Plan for Disaster Recovery](https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/rel_planning_for_disaster_recovery_dr.html)
- [AWS Free Tier](https://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/free-tier.html)
- [Avoiding unexpected charges after using AWS Free Tier](https://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/free-tier-charges.html)
- [Amazon VPC pricing](https://aws.amazon.com/vpc/pricing/)
- [OpenStack Installation Guide: Get started with OpenStack](https://docs.openstack.org/install-guide/get-started-with-openstack.html)
- [HashiCorp Terraform: What is Terraform?](https://developer.hashicorp.com/terraform/intro)
- [HashiCorp Terraform: Core workflow](https://developer.hashicorp.com/terraform/intro/core-workflow)
