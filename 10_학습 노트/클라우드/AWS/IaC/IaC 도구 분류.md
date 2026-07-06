---
title: IaC 도구 분류
created: 2026-07-06
status: active
type: concept-note
source:
  - Iac.pdf
  - IaC - Source Digest v2.md
  - IaC - 공식 검증 노트.md
source_pages:
  - p.3-p.4
tags:
  - 과목/AWS
  - 주제/IaC
  - 주제/Terraform
  - 상태/active
  - 개념/IaC
---

# IaC 도구 분류

## Source Classification

| 내용 | 출처 분류 | 비고 |
|---|---|---|
| 강의자료 기반 핵심 내용 | PDF | `Iac.pdf`, `IaC - Source Digest v2.md` 기준 |
| Terraform 현재 동작 검증 | 인터넷 고신뢰 정보 | `IaC - 공식 검증 노트.md`와 HashiCorp 공식 문서 기준 |
| 설명 재구성 | 내장 지식 | PDF와 공식 검증 내용을 학습 노트 형태로 재배열 |
| 커뮤니티 의견 | 인터넷 비공식 고품질 의견 | 이 노트에서는 사용하지 않음 |

## 한 줄 정의

IaC 도구는 인프라의 어느 계층을 코드로 다루는지에 따라 **ad-hoc script, 구성 관리, 서버 템플릿, 오케스트레이션, 프로비저닝**으로 나눌 수 있다.

## PDF 기준 5가지 범주

| 범주 | 대표 도구 | 주된 역할 |
|---|---|---|
| 애드혹(ad-hoc) 스크립트 | Bash, Python | 단계별 작업을 스크립트로 자동화 |
| 구성 관리 도구 | Ansible, Chef, Puppet, SaltStack | 서버에 소프트웨어를 설치하고 설정 상태를 관리 |
| 서버 템플릿 도구 | Docker, Packer, Vagrant | 서버/애플리케이션 실행 이미지를 만든다 |
| 오케스트레이션 도구 | Kubernetes, AWS ECS | 이미지를 배포 전략에 맞게 실행·관리 |
| 프로비저닝 도구 | Terraform, AWS CloudFormation, OpenStack Heat | 서버, 네트워크, LB, DB 등 인프라 리소스 자체를 생성 |

## 1. 애드혹 스크립트

PDF 설명:

- 수행할 작업을 단계별로 나눈다.
- Bash, Python 같은 스크립트 언어로 각 단계를 코드화한다.
- 단순 자동화에 적합하다.
- 각 서버에서 수동 실행되는 형태로 설명된다.

한계:

- 대규모 인프라에 적용하기 어렵다.
- 스크립트 작성 형식이 정해져 있지 않다.
- 코드 탐색성과 표준화가 약하다.

## 2. 구성 관리 도구

PDF 설명:

- 관리 대상 서버에 소프트웨어를 설치하거나 운영하는 데 특화된다.
- 전용 API와 코드 작성 형식이 대체로 정해져 있다.
- 코드 탐색이 쉽다.
- 멱등성을 제공한다.
- 분산형 구조를 지원하여 원격으로 여러 서버를 동시에 관리할 수 있다.

핵심 개념:

```text
멱등성(idempotency)
= 같은 작업을 여러 번 실행해도 결과 상태가 같아야 한다는 성질
```

## 3. 서버 템플릿 도구

PDF 설명:

- 구성 관리 도구의 대안으로 사용된다.
- 운영체제, 소프트웨어, 파일 등 서버 운영에 필요한 구성요소를 이미지에 포함한다.
- 불변 인프라(Immutable Infrastructure)를 구현하는 핵심 요소다.
- 기존 서버를 직접 수정하지 않고 새 이미지를 만들어 새 서버를 배포한다.

도구별 용도:

| 도구 | PDF 기준 용도 |
|---|---|
| Docker | 개별 응용 프로그램 이미지 |
| Packer | AWS AMI |
| Vagrant | 개발 컴퓨터에서 실행되는 VirtualBox 이미지 |

주의:

- 새 서버를 매번 배포해야 하므로 배포 시간이 오래 걸릴 수 있다고 설명된다.
- PDF는 이 단점을 “컨테이너 가상화 X”라는 맥락으로 표시한다.

## 4. 오케스트레이션 도구

PDF 설명:

- 서버 템플릿 도구에서 만든 이미지를 배포 전략에 맞게 배포한다.
- 배포된 서버 또는 컨테이너를 관리한다.
- Kubernetes가 대표 예시다.
- Public Cloud 공급업체의 전용 서비스도 존재하며 AWS ECS가 예시로 언급된다.

## 5. 프로비저닝 도구

PDF 설명:

- 구성 관리 도구나 서버 템플릿 도구가 각 서버 내부에서 실행되는 코드를 정의한다면, 프로비저닝 도구는 서버 자체를 생성한다.
- 서버뿐 아니라 네트워크, LB, DB 등 인프라 구성 요소 대부분을 만들 수 있다.
- 대표 도구: Terraform, AWS CloudFormation, OpenStack Heat.

## Terraform의 위치

Terraform은 PDF 기준으로 **프로비저닝 도구**에 속한다.

즉 Terraform의 주된 관심사는 다음이다.

- VPC 생성
- Subnet 생성
- Security Group 생성
- EC2 생성
- ALB/ASG 생성
- DB, LB, 기타 클라우드 리소스 생성
- 상태 파일을 통한 현재 인프라와 코드의 비교

## 관련 노트

- [[IaC 개념]]
- [[Terraform 개요]]
- [[Terraform Resource와 Data Source]]
- [[Terraform Module]]
