---
type: moc
status: active
created: 2026-08-24
scope: 3차 프로젝트 Wazuh 구현·학습·운영·증거 라우팅
parent_moc: "[[20_팀 프로젝트/3차 프로젝트/00_3차프로젝트_목차]]"
---

# Wazuh MOC

## 개요

이 MOC는 3차 프로젝트의 Wazuh 관련 구현과 설명 자료를 연결한다. Wazuh 구현은 `wazuh-docker`, `bank-security-lab-infra`, `Uns-DVWA`에 나뉘어 있으므로 한 저장소만 보고 전체 시스템을 판단하지 않는다.

팀원이 GitHub 저장소에서 실제 구현을 읽을 때의 정본은 [`PROJECT-WAZUH-MOC.md`](https://github.com/Unoh03/wazuh-docker/blob/main/PROJECT-WAZUH-MOC.md)다. 이 Obsidian MOC는 상세 학습·검증·발표 자료로 이동하는 내부 지도다.

## 저장소 경계

| 저장소 | 원본 책임 | 대표 위치 |
|---|---|---|
| `Unoh03/wazuh-docker` | Wazuh Runtime, Manager 입력, Rule, Rule 단위 테스트 | `single-node/config/`, `single-node/tests/` |
| `Unoh03/bank-security-lab-infra` | AWS 수집 자원, Push Bridge, Dashboard, Shuffle 연결, 운영 자동화 | `foundation/wazuh*.tf`, `observability/wazuh/`, `observability/shuffle/`, `tools/`, `automation/` |
| `Unoh03/Uns-DVWA` | 탐지 뒤 실행되는 고정 애플리케이션 조치와 GitOps 배포 | GitHub Actions Workflow, 배포 설정 |

## 핵심 경로

- 설치·Docker·AWS 입력: [[20_팀 프로젝트/3차 프로젝트/와주/와주 설치|Wazuh 설치와 AWS 로그 수집 연동]]
- 수집·탐지·Dashboard·Evidence 해석: [[20_팀 프로젝트/3차 프로젝트/와주/Wazuh SIEM 로그 분석과 대응|Wazuh SIEM 로그 분석과 대응]]
- 보존 Event를 읽는 실습: [[20_팀 프로젝트/3차 프로젝트/와주/Wazuh 대시보드 미니 실습|Wazuh 대시보드 미니 실습]]
- Wazuh Alert 이후 SOAR: [[20_팀 프로젝트/3차 프로젝트/셔플/Shuffle SOAR 구축과 Wazuh 연동|Shuffle SOAR 구축과 Wazuh 연동]]
- Push와 Poll 수집 경로 비교: [[20_팀 프로젝트/3차 프로젝트/DVWA Push와 5-Source Poll 최종 해석|DVWA Push와 5-Source Poll 최종 해석]]
- 전체 Telemetry 경로: [[20_팀 프로젝트/3차 프로젝트/AWS 보안 Telemetry Route 비교|AWS 보안 Telemetry Route 비교]]
- 실제 구성과 Runtime 검증 경계: [[20_팀 프로젝트/3차 프로젝트/관측성_As-built_및_Runtime_검증|관측성 As-built 및 Runtime 검증]]
- 시연 화면별 구현 근거: [[20_팀 프로젝트/3차 프로젝트/시연 장면별 근거 파일|시연 장면별 근거 파일]]

## Rule 빠른 지도

Rule 조건의 정본은 `D:\Wazuh\wazuh-docker\single-node\config\wazuh_cluster\rules\capital_one_rules.xml`이다.

| Rule | 현재 의미 | 경로 |
|---|---|---|
| `100102` | 안전한 Push 검증 Event가 Wazuh까지 도착 | Push |
| `100110` | DVWA `low` 상태에서 IMDS Credential endpoint 결과 반환 | Push |
| `100111` | 지정 Node Role로 보호 S3 Object 읽기 성공 | Poll |

`100110`과 `100111`은 서로 다른 원본 Event를 판정한다. 수집 성공, Rule 탐지, Shuffle 실행, 최종 자동 조치는 별도 단계로 기록한다.

## 무엇을 어디서 수정하는가

- Rule·Level·Manager Poll 설정: `D:\Wazuh\wazuh-docker`
- AWS IAM·S3·CloudWatch Logs·Lambda·SQS: `D:\terraform\aws_terraform_build_code\foundation`
- Push Bridge·Wazuh Override·Dashboard: `D:\terraform\aws_terraform_build_code\observability\wazuh`
- Shuffle Payload·App·Workflow 계약: `D:\terraform\aws_terraform_build_code\observability\shuffle`
- Daily/SOC 기동·종료·복구: `D:\terraform\aws_terraform_build_code\tools`, `automation`, 루트 운영 스크립트
- 실제 DVWA 조치와 GitOps 상태: `Unoh03/Uns-DVWA`

Rule ID나 Alert Field를 바꾸면 두 저장소의 Dashboard Query, Shuffle Routing, Schema와 테스트까지 함께 확인한다.

## 현재 재시작 지점

- 새 조원 인수인계: GitHub의 `PROJECT-WAZUH-MOC.md`부터 읽는다.
- Wazuh 자체 설정 수정: `wazuh-docker`의 Rule·Manager 설정과 단위 테스트를 먼저 본다.
- 전체 시연 복구: 인프라 저장소의 Operator Handoff와 현재 Git·Runtime 상태를 다시 확인한다.
- Runtime 상태는 변동되므로 파일 존재만으로 수집·탐지·자동 대응 성공을 주장하지 않는다.

## 공유 금지

AWS Credential, Wazuh 비밀번호, Shuffle Webhook·API Key, GitHub PAT, Kubernetes Secret과 원문 Credential 응답은 Vault·Git·Screenshot에 남기지 않는다.

