---
title: IaC MOC
created: 2026-07-06
updated: 2026-07-14
status: active
type: moc
scope: AWS 수업 자료와 Terraform AWS 실습
parent_moc: "[[10_학습 노트/클라우드/AWS/00_AWS_목차]]"
tags:
  - 과목/AWS
  - 주제/IaC
  - 주제/Terraform
  - 상태/active
---

# IaC MOC

> AWS 수업 자료와 Terraform 기반 AWS 실습을 연결하는 탐색 지도다. 일반 IaC 전체의 완전한 목록이나 실습 진행 로그로 사용하지 않는다.

## 상위 경로

- [[10_학습 노트/클라우드/AWS/00_AWS_목차|AWS 목차]]

## 현재 재시작 지점

- 기본 Terraform 실습 흐름: [[Terraform AWS CLI 초기 설정 실습 v6.3]]
- 누적 Terraform 인프라 실습: [[Terraform RDS 인프라 구성 실습 v10.1]]
  - v7.1 WEB-RDS 기능·TLS 검증은 보류 중이다.
  - v7.2에서 `07_networks`와 `07_servers` Root Module 및 State 분리를 정리한다.
  - v8.0에서 S3, IAM, ALB, ACM, Route 53을 결합한 종합 웹 서비스 아키텍처를 정리한다.
  - v9.0에서 동일한 Root Module을 역할별 `.tf` 파일로 분할하는 구조를 정리한다.
  - v10.0~v10.1에서 `for_each`, 조건식, 객체형 Map을 이용한 Public/Private 인프라 반복 구성을 정리한다.
- 현재 수업 진도: [[Terraform Module 종합 구성 실습 v12.0]]
  - v11.0에서 VPC와 Subnet을 Local Child Module로 분리하고 Input/Output 연결을 정리했다.
  - v12.0에서 기존 종합 인프라를 Networks와 Servers 책임 단위로 Module화한다.
  - Dev와 Prod Root Module이 같은 Child Module 구현을 서로 다른 환경값으로 재사용한다.
  - Networks Module Output을 Servers Module Input으로 전달해 전체 Dependency Graph를 조립한다.
  - 실제 `validate`, `plan`, `apply` 검증은 아직 보류 중이다.
- 다음 독립 학습 후보:
  - [[Terraform Backend와 Remote State]]

## 핵심 개념

### IaC 기초

- [[IaC 개념]]
- [[IaC 도구 분류]]

### Terraform 기초

- [[Terraform 개요]]
- [[Terraform Workflow]]
- [[Terraform Resource와 Data Source]]
- [[Terraform Variable과 Output]]
- [[Terraform 반복문과 조건문]]

### 구조화와 상태 관리

- [[Terraform Module]]
- [[Terraform Backend와 Remote State]]

## 대표 실습

- [[Terraform AWS CLI 초기 설정 실습 v6.3]] - AWS CLI와 Terraform 설치부터 VPC, EC2, NAT Instance, S3 Gateway Endpoint, Web-DB 연동까지 누적한 통합 실습
- [[Terraform RDS 인프라 구성 실습 v10.1]] - RDS 전환, Root Module과 State 분리, 종합 웹 서비스 아키텍처, 파일 분할, 반복문·조건문 기반 Public/Private 인프라 구성까지 누적한 실습
- [[Terraform Module 구성 실습 v11.0]] - VPC와 Subnet을 Local Child Module로 분리하고 Stage/Prod Root Module에서 입력·출력 Interface로 재사용하는 실습
- [[Terraform Module 종합 구성 실습 v12.0]] - Networks와 Servers 책임 경계로 기존 종합 인프라를 Module화하고 Dev/Prod Root Module에서 조립하는 실습

## 원자료 / RAW / 검증

- [[IaC PDF Obsidian 노트화 계획 v2]]
- [[IaC - Source Digest v2]]
- [[IaC - 공식 검증 노트]]
- [[raw 노트]]

## 정리 대기

- [ ] v7.1 WEB-RDS 기능·TLS 검증
- [ ] `07_networks` / `07_servers` 실제 apply·destroy 검증
- [ ] v10.1 반복문·조건문 인프라의 `validate`·`plan`·`apply` 검증
- [ ] v11.0 Stage/Prod Local Module의 `validate`·`plan`·`apply` 검증
- [ ] v12.0 Networks/Servers Module 종합 구성의 `validate`·`plan`·`apply` 검증
- [ ] Terraform Remote Backend(S3)와 State locking 실습
- [ ] Terraform 실습 통합 로그 분리 여부 결정
- [ ] AWS 프로젝트에 Terraform 적용하기
