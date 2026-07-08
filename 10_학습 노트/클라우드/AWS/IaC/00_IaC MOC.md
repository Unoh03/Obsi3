---
title: IaC MOC
created: 2026-07-06
status: active
type: moc
source_context:
  - Iac.pdf
  - IaC - Source Digest v2.md
  - IaC - 공식 검증 노트.md
tags:
  - 과목/AWS
  - 주제/IaC
  - 주제/Terraform
  - 상태/active
---

# IaC MOC

> 현재 이 폴더의 IaC 노트는 일반 IaC 전체가 아니라, AWS 수업 자료와 Terraform AWS 실습을 중심으로 정리한 묶음이다.

## Source

- [[IaC PDF Obsidian 노트화 계획 v2]]
- [[IaC - Source Digest v2]]
- [[IaC - 공식 검증 노트]]
- [[raw 노트]]

## Concept Notes

- [[IaC 개념]]
- [[IaC 도구 분류]]
- [[Terraform 개요]]
- [[Terraform Workflow]]
- [[Terraform Resource와 Data Source]]
- [[Terraform Variable과 Output]]
- [[Terraform 반복문과 조건문]]
- [[Terraform Module]]
- [[Terraform Backend와 Remote State]]

## Lab Notes

- [[Terraform AWS CLI 초기 설정 실습 v5]]
  - AWS CLI/Profile/Terraform 설치
  - VPC/Subnet/EC2 최소 골격 실습
  - Public/Private 역할 Subnet 2개와 EC2 2대 배치 실습
  - PDF 27p Resource & Data Source 아키텍처 구현
  - Route Table과 Route Table Association 실습
  - Security Group 기본 연결 실습
  - NAT Instance 기반 Private EC2 외부 통신 실습
  - Private WEB EC2 outbound 검증 증적 포함
  - AWS 예약 IP 오류와 해결 과정 기록

## Pending

- AWS 프로젝트에 Terraform 적용하기
- Terraform Resource 참조 심화 실습
- Terraform Data Source 실습
- Terraform Security Group 최소 권한화 실습
- Terraform 2AZ 전체 구조 확장 실습
- Terraform Bastion Host와 NAT Instance 역할 분리 실습
- Terraform Backend/Remote State 실습
- Terraform Module 실습
