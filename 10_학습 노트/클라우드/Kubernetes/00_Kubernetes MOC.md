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
- 현재 실습: [[EKS 첫 접속과 Pod 기초 실습]]
- 현재 수업 범위: `Kubernetes.pdf` p.19까지 기록
- 진행 중: Pod 기초 → Image·Manifest 보정 → 환경변수와 Downward API
- 다음 재시작: EKS 환경을 다시 만든 뒤 p.19 환경변수 Manifest를 Server-side dry run하고 `exec env` 결과를 확인한다.

## 핵심 개념

- [[컨테이너 오케스트레이션]]
- [[Kubernetes 아키텍처]]
- [[Kubernetes Pod와 ReplicaSet]]

## Source / RAW

- 원자료: [[40_자료/강의 자료/Kubernetes.pdf|Kubernetes.pdf]]
- Source Digest: [[Source Digest/Kubernetes - Source Digest v1]]
- 연계 실습 자료: `boot.zip` Spring Boot Source - 아직 Vault에 편입하지 않음
