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
- 현재 실습: [[Lab_EKS Service 기초 실습]]
- 현재 수업 범위: Chapter 06 Service의 ClusterIP Runtime까지
- 확인됨: `delivery` Namespace의 `cluster-svc`가 selector와 일치하는 Pod 3개를 EndpointSlice에 등록했다. ClusterIP와 같은 Namespace의 DNS 이름으로 `HTTP 200`을 받았고, 반복 요청에서 복수 Backend가 응답했다.
- 다음 재시작: PDF p.121 흐름에 따라 다른 Namespace에서 `cluster-svc.delivery` 또는 FQDN 접근을 확인한 뒤 p.122 NodePort로 진행한다.

## 실습 계보

- p.13-p.30 Pod 기본·Network·Label: [[Lab_EKS 첫 접속과 Pod 기초 실습]]
- p.31-p.51 Scheduling·Node 운영: [[Lab_EKS Pod Scheduling과 Node 운영 실습]]
- p.52-p.73 ReplicaSet: [[Lab_EKS ReplicaSet 기초 실습]]
- p.74-p.85 Deployment·Rolling Update·직전 Revision Rollback: [[Lab_EKS Deployment 기초와 Rolling Update 실습]]
- Chapter 06 ClusterIP Service: [[Lab_EKS Service 기초 실습]]

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
