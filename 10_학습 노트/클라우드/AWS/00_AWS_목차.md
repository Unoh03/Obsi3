# AWS 목차

## 개요

`AWS기초.pdf` 기반 학원 AWS 수업의 완료/legacy 흐름, 개념 노트, 실습 노트, 운영 보조 기록을 연결하는 AWS 영역의 진입점이다.

현재진행 중인 공식 Arc 과정의 재시작 지점으로 사용하지 않는다.

개념 노트는 AWS 구조와 서비스 의미를 정리하고, 실습 노트는 실제 Console 조작, 명령, 오류, 검증 결과를 남긴다.

## 상위 경로

- [[00_index/Home|Home]]
- [[10_학습 노트/00_학습노트_목차|학습노트 목차]]
- [[10_학습 노트/클라우드/00_클라우드_목차|클라우드 목차]]

## 학원 AWS기초 완료 흐름

1. `AWS기초.pdf` p.84 구조 실습 기록은 [[10_학습 노트/클라우드/AWS/실습 노트/Web VPC와 RDS 연계 실습|Web VPC와 RDS 연계 실습]]에 남아 있다. RDS 대신 EC2 MariaDB를 사용한 변형 구성이다.
2. 대표 완료 범위는 [[10_학습 노트/클라우드/AWS/실습 노트/NAT Instance 실습|NAT Instance 실습]]과 Web VPC / DB 연계 실습이다.
3. `AWS기초.pdf` p.86 이후 Route 53, ELB / ALB, ACM, HTTPS 연결은 현재 수업 재시작점이 아니라 후속 정리 후보로 본다.

## 강의 자료와 RAW

- [[40_자료/강의 자료/AWS기초.pdf|AWS 기초]]
- [[10_학습 노트/클라우드/AWS/RAW 메모|RAW 메모]] - 학원 수업 중 빠르게 기록한 원자료. 정리본으로 단정하지 않는다.

> [!warning] 자료 기준 시점
> `AWS기초.pdf`는 `Copyright © 2018` 자료다. Console 화면, 비용, Free Tier, 서비스 권장 구성, 보안 기본값은 실제 실습 전에 AWS 공식 문서나 현재 Console 기준으로 다시 확인한다.

## 학습 범위 지도

| PDF 범위 | 학습 단위 | 현재 정리 상태 |
| --- | --- | --- |
| p.2-12 | 클라우드 유형, DevOps, Terraform, IaaS / PaaS / SaaS, AWS 이점 | [[클라우드 컴퓨팅과 AWS 입문]] |
| p.13-25 | EC2, 글로벌 인프라, Scale-up / Scale-out, EC2와 RDS 기본 구성 | [[EC2와 RDS 기본 구성 실습]] |
| p.25-30 | VPC, Subnet, Route Table, Security Group, Internet Gateway 기초 | [[VPC 네트워크 기초]] |
| p.31-65 | VPC Console 구성, Public / Private EC2, SSH 접근 검증 | [[VPC 실습]] |
| p.66-71 | Multi-AZ, Bastion Host, NAT, RDS 확장 구조 | [[Multi-AZ와 Bastion, NAT 구성 기초]] |
| p.72-81 | NAT Gateway / NAT Instance 조건, NAT Instance outbound 검증 | [[NAT Gateway와 NAT Instance 구성 기초]], [[NAT Instance 실습]] |
| p.82-85 | Web VPC, Bastion, NAT Instance, Web EC2, DB 연계 구조 | [[Web VPC와 RDS 연계 실습]] - RDS 범위를 EC2 MariaDB 구성으로 변형해 기록 |
| p.86-122 | Route 53, ELB / ALB, ACM, HTTPS, Target Group, DNS 연결 | 후속 정리 후보 |
| p.123-126 | Auto Scaling, S3, CloudFront, Multi-Region DR, CodePipeline | 후속 정리 후보 |

## 개념 노트

- [[10_학습 노트/클라우드/AWS/개념 노트/클라우드 컴퓨팅과 AWS 입문|클라우드 컴퓨팅과 AWS 입문]]
- [[10_학습 노트/클라우드/AWS/개념 노트/VPC 네트워크 기초|VPC 네트워크 기초]]
- [[10_학습 노트/클라우드/AWS/개념 노트/Multi-AZ와 Bastion, NAT 구성 기초|Multi-AZ와 Bastion, NAT 구성 기초]]
- [[10_학습 노트/클라우드/AWS/개념 노트/NAT Gateway와 NAT Instance 구성 기초|NAT Gateway와 NAT Instance 구성 기초]]

## 실습 노트

- [[10_학습 노트/클라우드/AWS/실습 노트/EC2와 RDS 기본 구성 실습|EC2와 RDS 기본 구성 실습]] - EC2에 Tomcat과 `boot.war`를 배포하고 RDS for MariaDB와 연결한 실습
- [[10_학습 노트/클라우드/AWS/실습 노트/VPC 실습|VPC 실습]] - VPC, Public / Private Subnet, Route Table, IGW, Public EC2 경유 Private EC2 SSH 접속 검증
- [[10_학습 노트/클라우드/AWS/실습 노트/NAT Instance 실습|NAT Instance 실습]] - NAT Instance의 IP forwarding과 MASQUERADE를 설정하고 Private EC2의 외부 ping 통신을 검증한 실습
- [[10_학습 노트/클라우드/AWS/실습 노트/Web VPC와 RDS 연계 실습|Web VPC와 RDS 연계 실습]] - p.84 이후 Web EC2와 DB 연계 구조를 구성한 실습. RDS 대신 EC2 MariaDB로 변형해 기록

## IaC / Terraform

- [[10_학습 노트/클라우드/AWS/IaC/00_IaC MOC|IaC MOC]] - AWS 수업 자료와 Terraform AWS 실습 중심의 active MOC. Source Digest, 공식 검증 노트, raw 노트, Terraform 개념·실습 노트를 이 경로에서 확인한다.

## 운영 / 보조 기록

- [[10_학습 노트/클라우드/AWS/서버_시퓨_100%_찍을_때|EC2 서버가 멈추거나 CPU 100% 찍을 때]]
- [[10_학습 노트/클라우드/AWS/ec2_tomcat_setup.sh|ec2_tomcat_setup.sh]]
- [[10_학습 노트/클라우드/AWS/ec2_mariadb_setup.sh|ec2_mariadb_setup.sh]]
- [[10_학습 노트/클라우드/AWS/ec2_rds_client_setup.sh|ec2_rds_client_setup.sh]]

## 후속 정리 후보

- [ ] [[10_학습 노트/클라우드/AWS/실습 노트/Web VPC와 RDS 연계 실습|Web VPC와 RDS 연계 실습]]을 다시 볼 때 p.84 이후 실제 구성, 오류, 검증 결과가 충분히 복구 가능한지 확인한다. RDS와 EC2 MariaDB 차이는 실습 관찰값 기준으로 구분한다.
- [ ] Route 53 / ALB / ACM / HTTPS 범위는 필요해질 때 PDF를 먼저 훑고 개념 노트와 실습 노트 경계를 정한다.
- [ ] p.123-126 확장 주제는 학원 AWS기초 흐름의 후속 후보로 남기며, 현재 공식 Arc 과정의 재시작 지점으로 단정하지 않는다.

## 운영 메모

- AWS MOC는 탐색용으로 유지한다. PDF 페이지 분석이나 실습 로그가 길어지면 별도 노트로 분리한다.
- 개념 노트와 실습 노트는 분리한다. 같은 PDF 범위라도 원리 설명은 개념 노트, 실제 명령과 검증은 실습 노트에 둔다.
- Public IPv4, Console UI, 보안 그룹 기본값, NAT / RDS / Free Tier 관련 내용은 바뀔 수 있으므로 성공 당시 관찰값과 현재 권장 구성을 구분해서 기록한다.
- 공식 Arc 과정의 현재진행 RAW와 이 목차의 학원 AWS기초 흐름을 섞지 않는다.
