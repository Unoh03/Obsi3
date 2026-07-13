---
title: IaC MOC
created: 2026-07-06
updated: 2026-07-13
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
- 누적 Terraform 인프라 실습: [[Terraform RDS 인프라 구성 실습 v9.0]]
  - v7.1 WEB-RDS 기능·TLS 검증은 보류 중이다.
  - v7.2에서 `07_networks`와 `07_servers` Root Module 및 State 분리를 정리한다.
  - v8.0에서 S3, IAM, ALB, ACM, Route 53을 결합한 종합 웹 서비스 아키텍처를 정리한다.
  - v9.0에서 동일한 Root Module을 역할별 `.tf` 파일로 분할하는 구조를 정리한다.
- 현재 수업 진도: [[Terraform 반복문과 조건문]]
  - 반복문 실습 내용은 후속 버전에서 반영한다.
- 다음 독립 학습 후보:
  - [[Terraform Backend와 Remote State]]
  - [[Terraform Module]]

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
- [[Terraform RDS 인프라 구성 실습 v9.0]] - RDS 전환, Network/Server Root Module과 State 분리, 종합 웹 서비스 아키텍처, 동일 Root Module 내부의 역할별 파일 분할까지 누적한 실습

## 원자료 / RAW / 검증

- [[IaC PDF Obsidian 노트화 계획 v2]]
- [[IaC - Source Digest v2]]
- [[IaC - 공식 검증 노트]]
- [[raw 노트]]

## 정리 대기

- [ ] v7.1 WEB-RDS 기능·TLS 검증
- [ ] `07_networks` / `07_servers` 실제 apply·destroy 검증
- [ ] 반복문 실습 결과를 후속 버전에 반영
- [ ] Terraform Remote Backend(S3)와 State locking 실습
- [ ] Terraform Module 실습
- [ ] Terraform 실습 통합 로그 분리 여부 결정
- [ ] AWS 프로젝트에 Terraform 적용하기
