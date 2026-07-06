---
title: IaC 개념
created: 2026-07-06
status: active
type: concept-note
source:
  - Iac.pdf
  - IaC - Source Digest v2.md
  - IaC - 공식 검증 노트.md
source_pages:
  - p.1-p.2
  - p.5
tags:
  - 과목/AWS
  - 주제/IaC
  - 주제/Terraform
  - 상태/active
  - 개념/IaC
---

# IaC 개념

## Source Classification

| 내용 | 출처 분류 | 비고 |
|---|---|---|
| 강의자료 기반 핵심 내용 | PDF | `Iac.pdf`, `IaC - Source Digest v2.md` 기준 |
| Terraform 현재 동작 검증 | 인터넷 고신뢰 정보 | `IaC - 공식 검증 노트.md`와 HashiCorp 공식 문서 기준 |
| 설명 재구성 | 내장 지식 | PDF와 공식 검증 내용을 학습 노트 형태로 재배열 |
| 커뮤니티 의견 | 인터넷 비공식 고품질 의견 | 이 노트에서는 사용하지 않음 |

## 한 줄 정의

**Infrastructure as Code(IaC)**는 인프라의 생성, 배포, 수정, 정리 작업을 사람이 콘솔에서 반복 조작하는 대신 **코드로 정의하고 실행하는 방식**이다.

## PDF 기반 핵심

`Iac.pdf`는 IaC를 다음처럼 설명한다.

- 코드 작성 후 실행으로 인프라를 생성, 배포, 수정, 정리한다.
- 하드웨어 관리 및 운영 관리에 관한 작업을 코드 형태로 관리한다.
- 서버, 네트워크, DB, APP, 자동화된 테스트 및 배포 등의 기능을 구현한다.
- DevOps의 핵심 요소로 설명된다.
- 대표 도구로 Terraform, Ansible, Kubernetes 등이 언급된다.

## IaC가 해결하려는 문제

수동 인프라 운영은 다음 문제가 생기기 쉽다.

| 문제 | IaC 관점의 해결 |
|---|---|
| 사람이 직접 콘솔에서 설정 | 코드로 선언하고 실행 |
| 작업자가 바뀌면 절차가 달라짐 | 코드와 버전 관리로 절차 표준화 |
| 변경 이력 추적 어려움 | Git 같은 VCS로 변경 추적 |
| 장애 시 원인 추적 어려움 | 변경 diff와 이전 버전으로 분석 |
| 같은 환경 재현 어려움 | 코드 재사용으로 반복 배포 |

## IaC의 장점

PDF p.5는 IaC의 장점을 다섯 가지 축으로 정리한다.

| 장점 | 의미 |
|---|---|
| 자급식 배포(Self-Service) | 소수 관리자만 하던 배포를 자동화하여 개발자가 필요 시 직접 배포 가능 |
| 속도와 안정성(Speed and Safety) | 자동화된 배포는 빠르고 반복 가능하며 수동 작업보다 오류가 적음 |
| 문서화(Documentation) | 인프라 상태가 소스 파일 형태로 남아 조직 구성원이 이해 가능 |
| 버전 관리(Version Control) | 인프라 변경 이력이 코드에 남아 문제 원인 추적과 롤백에 유리 |
| 유효성 검증과 재사용성(Validation & Reuse) | 코드 변경 시 검증과 자동화 테스트를 수행하고, 모듈로 재사용 가능 |

## 중요한 구분

IaC는 단순히 “스크립트로 자동화한다”와 같지 않다.

- 스크립트 자동화는 절차를 코드화한다.
- IaC는 인프라의 목표 상태, 구성, 배포 방식을 코드로 관리한다.
- Terraform 같은 도구는 state를 통해 현재 상태와 목표 상태를 비교한다.

## 프로젝트 적용 관점

AWS 프로젝트에서는 IaC가 다음 영역과 연결된다.

- VPC, Subnet, Route Table, Security Group 생성
- EC2, ALB, ASG 구성
- S3 backend를 통한 state 관리
- stage/prod 환경 분리
- 실습 결과 재현성 확보
- 보안 설정 변경 이력 관리

## 주의

- IaC 코드는 인프라 권한을 가진 실행 파일에 가깝다.
- 잘못 작성된 코드는 잘못된 인프라를 빠르게 대량 생성하거나 삭제할 수 있다.
- 실습에서는 `plan`으로 변경 사항을 확인하고, 비용 발생 리소스는 종료 절차를 반드시 포함해야 한다.

## 관련 노트

- [[IaC 도구 분류]]
- [[Terraform 개요]]
- [[Terraform Workflow]]
- [[Terraform Backend와 Remote State]]
