---
title: IaC MOC
created: 2026-07-06
status: legacy
type: moc
scope: 2026-07-06 이전 IaC MOC 스냅샷
parent_moc: "[[10_학습 노트/클라우드/AWS/IaC/00_IaC MOC]]"
source_context:
  - Iac.pdf
  - IaC - Source Digest v2.md
  - IaC - 공식 검증 노트.md
tags:
  - 과목/AWS
  - 주제/IaC
  - 주제/Terraform
---

# IaC MOC

> [!warning] Legacy
> 현재 탐색은 [[10_학습 노트/클라우드/AWS/IaC/00_IaC MOC|IaC MOC]]에서 시작한다. 이 파일은 이전 구조 비교를 위해 `references/`에 보존한 스냅샷이다.

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

- [[Terraform AWS CLI 초기 설정 실습 v6.3]]
  - AWS CLI/Profile/Terraform 설치
  - VPC/Subnet/EC2 최소 골격 실습
  - Public/Private 역할 Subnet 2개와 EC2 2대 배치 실습
  - PDF 27p Resource & Data Source 아키텍처 구현
  - Route Table과 Route Table Association 실습
  - Security Group 기본 연결 실습
  - NAT Instance 기반 Private EC2 외부 통신 실습
  - Private WEB EC2 outbound 검증 증적 포함
  - 강사님 정답지 `main.tf`와 내 구현 코드 비교
  - Public Web + Private DB + S3 Gateway Endpoint 실습
  - 격리된 Private DB 서버에서 S3 Gateway Endpoint를 통한 MariaDB 설치 원리
  - `user_data`를 `00-common.sh`, `10-db-install.sh`, `20-web-install.sh`로 분리한 리팩토링 기록
  - Apache httpd + PHP-FPM + PHP PDO 기반 Web → Private DB 연동 검증
  - 브라우저/PowerShell curl/WEB 내부/DB 내부 검증 증적 포함
  - Brave 브라우저 HTTPS 자동 전환 이슈와 HTTP 명시 접속 트러블슈팅
  - AWS 예약 IP 오류와 해결 과정 기록

## Completed in Lab Log

- NAT Instance 기반 Private EC2 outbound 검증
- S3 Gateway Endpoint 기반 격리 DB 서버 패키지 설치 검증
- `user_data` 파일 분리 리팩토링
- Public Web → Private DB 연동 검증

## Pending

- AWS 프로젝트에 Terraform 적용하기
- Terraform Resource 참조 심화 실습
- Terraform Data Source 실습
- Terraform Security Group 최소 권한화 실습
- Terraform 2AZ 전체 구조 확장 실습
- Terraform Bastion Host와 NAT Instance 역할 분리 실습
- Terraform Backend/Remote State 실습
- Terraform Module 실습
- Terraform 실습 통합 로그 분리
  - NAT Instance 노트
  - S3 Gateway Endpoint 노트
  - `user_data` Bootstrap 노트
  - Web DB 연동 노트
  - 실습 오류 모음 노트
- Terraform Module 실습
