---
title: IaC MOC
created: 2026-07-06
updated: 2026-07-21
status: active
type: moc
scope: AWS 수업 자료와 Terraform AWS 실습
parent_moc: "[[10_학습 노트/클라우드/AWS/00_AWS_목차]]"
tags:
  - 과목/AWS
  - 주제/IaC
  - 주제/Terraform
---

# IaC MOC

> AWS 수업 자료와 Terraform 기반 AWS 실습을 연결하는 탐색 지도다. 일반 IaC 전체의 완전한 목록이나 실습 진행 로그로 사용하지 않는다.

## 상위 경로

- [[10_학습 노트/클라우드/AWS/00_AWS_목차|AWS 목차]]

## 현재 재시작 지점

- 기본 Terraform 실습 흐름: [[Terraform AWS CLI 초기 설정 실습 v6.3]]
- 누적 Terraform 인프라 실습: [[Terraform RDS 인프라 구성 실습 v9.0]]
  - v7.1 WEB-RDS 기능·TLS 검증은 보류 중이다.
- 현재 누적 실습: [[Terraform External Module 활용 실습 v17.1]]
  - v17.0의 Apply·Runtime·Destroy 근거에 강사 답지 정적 비교를 추가한 최신 안정본이다.
  - 우리 구현은 전체 수명주기를 검증했지만, 강사 답지의 `init`·`validate`·`plan`·`apply`는 미수행이다.
  - 다음 수업은 새 진도 폴더와 강사 요구사항을 확인한 뒤 별도 Version으로 시작한다.
- 이전 검증 이정표: [[Terraform Module 종합 구성 실습 v15.0]]
  - Launch Template·ASG 전환과 Stage apply·health·destroy를 검증한 legacy 누적본이다.
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
- [[Terraform RDS 인프라 구성 실습 v9.0]] - RDS 전환, Root Module과 State 분리, 종합 웹 서비스 아키텍처와 파일 분할까지 누적한 실습
- [[Terraform Module 구성 실습 v11.0]] - VPC와 Subnet을 Local Child Module로 분리하고 Stage/Prod Root Module에서 입력·출력 Interface로 재사용하는 실습
- [[Terraform Module 종합 구성 실습 v15.0]] - Networks·S3·Servers·ELB 조립을 Launch Template·ASG 구조로 확장하고 Stage Apply·Health·Destroy까지 검증한 이전 누적 실습
- [[Terraform External Module 활용 실습 v17.1]] - v17 전체 수명주기 검증과 강사 답지의 흐름·보안·운영 차이를 분리한 최신 누적 안정본

## 원자료 / RAW / 검증

- [[IaC PDF Obsidian 노트화 계획 v2]]
- [[IaC - Source Digest v2]]
- [[IaC - 공식 검증 노트]]
- [[raw 노트]]

## 정리 대기

- [ ] [[Terraform RDS 초기화 방식 비교와 S3 schema.sql 설계 메모|v7.1 RDS 초기화·S3 schema.sql 설계 초안]]의 WEB-RDS 기능·TLS 검증
- [ ] `07_networks` / `07_servers` 실제 apply·destroy 검증
- [ ] v10.1 반복문·조건문 인프라의 `validate`·`plan`·`apply` 검증
- [ ] v11.0 Stage/Prod Local Module의 `validate`·`plan`·`apply` 검증
- [ ] v14.0 강사 답지 전체의 `validate`·`plan`·`apply`와 ALB·Route 53 동작 검증
- [ ] Terraform Remote Backend(S3)와 State locking 실습
- [ ] Terraform 실습 통합 로그 분리 여부 결정
- [ ] AWS 프로젝트에 Terraform 적용하기
