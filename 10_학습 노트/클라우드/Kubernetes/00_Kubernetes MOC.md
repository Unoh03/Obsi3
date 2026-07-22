---
type: moc
status: active
created: 2026-07-20
scope: Kubernetes와 EKS 학습 라우팅
parent_moc: "[[10_학습 노트/클라우드/00_클라우드_목차]]"
---

# Kubernetes MOC

## 개요

- 이 MOC는 Container Orchestration, Kubernetes Object, AWS EKS와 관련 실습을 라우팅한다.
- Terraform 자체의 문법·Module 계보는 [[10_학습 노트/클라우드/AWS/IaC/00_IaC MOC|IaC MOC]]에서 계속 관리한다.

## 현재 재시작 지점

- 원자료 지도: [[Source Digest/Kubernetes - Source Digest v1]]
- 현재 실습: [[Lab_EKS ReplicaSet 기초 실습]]
- 현재 수업 범위: `Kubernetes.pdf` p.52의 ReplicaSet 생성까지 기록
- 확인됨: `rs-basic`의 `DESIRED 5 / CURRENT 5 / READY 0`과 Pod Object 5개 생성
- 다음 재시작: Scheduling 가능한 새 EKS 환경에서 `rs-basic.yml`을 복원하고 `READY 5`와 Pod 삭제 후 Self-Healing을 확인한다.

## 실습 계보

- p.13-p.30 Pod 기본·Network·Label: [[Lab_EKS 첫 접속과 Pod 기초 실습]]
- p.31-p.51 Scheduling·Node 운영: [[Lab_EKS Pod Scheduling과 Node 운영 실습]]
- p.52-현재 ReplicaSet: [[Lab_EKS ReplicaSet 기초 실습]]

## 핵심 개념

- [[01_컨테이너 오케스트레이션]]
- [[02_Kubernetes 아키텍처]]
- [[03_AWS EKS]]
- [[04_Kubernetes Pod와 ReplicaSet]]

## 공식 문서

- [Kubernetes 공식 문서 한국어 홈](https://kubernetes.io/ko/docs/home/)

## Source / RAW

- 원자료: [[40_자료/강의 자료/Kubernetes.pdf|Kubernetes.pdf]]
- Source Digest: [[Source Digest/Kubernetes - Source Digest v1]]
- 연계 실습 자료: `boot.zip` Spring Boot Source - 아직 Vault에 편입하지 않음
