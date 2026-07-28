---
type: project-doc
status: draft
created: 2026-07-28
project: 3차 프로젝트
project_moc: "[[20_팀 프로젝트/3차 프로젝트/00_3차프로젝트_목차]]"
---

# EKS 워크로드 IAM 권한 오용 경로 및 증적 기반 조치 검증

> [!info] 편집 기준본과 공유본
> 이 Markdown은 앞으로 내용을 수정할 **편집 기준본(canonical)**이다.
> 대응 DOCX는 `2026-07-28 11:32 KST`에 생성한 공유용 스냅샷이다.
> [[20_팀 프로젝트/3차 프로젝트/운호_EKS_워크로드_IAM_권한_오용_경로_및_증적_기반_조치_검증_계획서.docx|DOCX 공유본]]
> 두 파일을 독립적으로 동시에 편집하지 않고, 이후 DOCX가 필요하면 이 Markdown을 기준으로 다시 생성한다.

> [!warning]
> 팀 구성·강사 요구사항·멘토 검토 전의 조건부 제안서다. 실제 범위는 첫 주의 성립 여부 확인과 팀 합의를 거쳐 확정한다.

## 1. 프로젝트 개요

### 1.1 프로젝트 한 문장

침해된 것으로 가정한 EKS Pod가 IRSA를 통해 과도하게 부여된 IAM 권한을 사용하여 S3 테스트 데이터에 접근하는 과정을 재현하고, EKS Audit Log와 CloudTrail에서 공격 흔적을 확인한 뒤 최소 권한 조치와 동일 조건 재검증을 수행한다.

### 1.2 핵심 질문

> 애플리케이션이 실행되는 Pod가 침해됐을 때, 해당 workload에 부여된 AWS 권한은 어디까지 피해를 확산시킬 수 있으며, 그 과정은 어떤 로그에 남고 최소 권한 조치 후 어떻게 달라지는가?

### 1.3 프로젝트의 성격

이 프로젝트는 다음과 같이 부른다.

- EKS workload identity 공격 경로 검증
- 클라우드 권한 오용 시뮬레이션
- Assumed Breach 기반 보안 검증
- 공격–탐지–조치–재점검 프로젝트

다음 표현은 실제 범위를 과장하므로 사용하지 않는다.

- 컨테이너 탈출
- AWS 계정 전체 침해
- 완전 자동 모의해킹
- 실제 침해사고 재현
- AI 기반 이상탐지

## 2. 위협 모델과 범위

### 2.1 공격 시작점

공격자가 테스트용 Pod 내부에서 명령을 실행할 수 있는 상태를 가정한다. 필수 범위에서는 `kubectl exec`로 이 상태를 통제해서 재현한다.

> 애플리케이션 최초 침투 과정은 이번 실험의 전제이며, 취약점 발견이나 실제 RCE 성공을 의미하지 않는다.

웹 애플리케이션 RCE나 명령 주입은 필수 범위가 끝난 경우에만 선택적으로 추가한다.

### 2.2 보호 대상

- 테스트 전용 S3 버킷과 `canary.txt` 등 더미 객체
- EKS workload identity
- IAM Role과 Policy
- CloudTrail 및 EKS 감사 로그

### 2.3 핵심 오설정

애플리케이션은 본래 S3 객체를 읽을 필요가 없지만, Pod의 ServiceAccount에 연결된 IAM Role에 테스트 버킷의 `s3:GetObject` 권한이 과도하게 부여돼 있다.

> 핵심 취약점은 IRSA 자체가 아니라, 침해 가능한 workload에 업무상 불필요한 AWS 권한을 부여한 최소 권한 위반이다.

IRSA는 Pod의 OIDC token을 STS `AssumeRoleWithWebIdentity`와 교환해 임시 IAM 자격증명을 얻는다.

### 2.4 명시적 제외 범위

- 온프레미스와 AWS 이중 구축
- 실제 컨테이너 탈출
- RDS 데이터 접근
- 계정 전체 권한 상승
- 지속성 확보와 백도어
- 머신러닝 이상탐지
- QuickSight·OpenSearch·대형 SIEM
- 외부 시스템 공격
- 실제 개인정보와 실제 Secret
- 취약점 여러 종류의 나열

## 3. 공격 시나리오

```text
1. 테스트 Pod 내부 명령 실행 상태 확보
2. Pod에 연결된 workload identity 확인
3. aws sts get-caller-identity로 IAM Role 확인
4. 해당 Role로 테스트 S3 객체 접근
5. EKS Audit Log와 CloudTrail 증적 수집
6. IAM Policy와 Trust Policy 조치
7. 동일한 절차 재실행
8. S3 접근 거부와 로그 차이 확인
```

토큰과 임시 자격증명의 실제 값은 출력하거나 보고서에 저장하지 않는다.

## 4. 증적 설계

| 단계 | 확인할 사실 | 증적 |
|---|---|---|
| Pod 내부 진입 | 누가 언제 `exec`를 수행했는가 | EKS Audit Log의 `pods/exec` 관련 이벤트 |
| Role 획득 | 어떤 web identity가 어떤 Role을 사용했는가 | CloudTrail `AssumeRoleWithWebIdentity` |
| 데이터 접근 | 어떤 Role이 어떤 객체를 읽었는가 | CloudTrail S3 `GetObject` data event |
| 구성 변경 | 권한이 어떻게 축소됐는가 | Terraform plan·diff, IAM Policy 전후 |
| 재검증 | 같은 요청이 실제로 차단됐는가 | `AccessDenied` 응답과 조치 후 CloudTrail |
| 종료 | 실험 자원이 제거됐는가 | Terraform destroy 결과와 AWS 잔존 자원 확인 |

S3의 `GetObject`는 CloudTrail 기본 관리 이벤트만으로는 남지 않으므로, 테스트 버킷에 대한 **Read data event**를 명시적으로 활성화한다.

로그 연결은 모든 계층에 동일한 `request_id`를 억지로 넣지 않는다. 다음 정보를 이용해 공격 타임라인을 구성한다.

- Kubernetes 사용자와 ServiceAccount
- IAM Role ARN
- STS role session
- S3 bucket·object
- 발생 시각
- source IP와 user agent

## 5. 보안 조치

### 5.1 필수 조치

- 업무상 필요하지 않은 `s3:GetObject` 권한 제거
- S3 접근이 필요하다면 버킷과 prefix를 최소 범위로 제한
- workload마다 별도 ServiceAccount 사용
- IRSA Trust Policy의 `sub`를 정확한 namespace와 ServiceAccount로 제한
- `aud`를 `sts.amazonaws.com`으로 제한
- 테스트 Role이 다른 AWS 리소스로 확산되지 않도록 권한 상한 설정

### 5.2 선택 조치

- Pod를 non-root로 실행
- read-only root filesystem 적용
- 불필요한 Linux Capability 제거
- 불필요한 ServiceAccount token 자동 마운트 제한
- 예상하지 못한 `pods/exec`와 S3 접근에 대한 탐지 규칙 작성

## 6. 최소 완료 범위와 선택 범위

### 6.1 P0 — 반드시 완료

- EKS 클러스터
- 테스트 Pod 1개
- ServiceAccount와 IRSA Role
- 더미 S3 객체 1개
- CloudTrail과 EKS Audit Log
- 공격 경로 1개
- IAM 최소 권한 조치
- 동일 조건 재검증
- Terraform 배포·삭제
- 증적 기반 결과 보고서

### 6.2 P1 — P0 완료 후 선택

- Trust Policy에서 `sub` 조건을 제거한 별도 오설정 시나리오
- 다른 namespace의 ServiceAccount를 이용한 Role 접근 검증
- 간단한 CloudWatch Logs Insights 탐지 쿼리
- CloudWatch 경보 또는 EventBridge 알림
- 실제 취약 웹 애플리케이션을 통한 최초 진입

## 7. 팀 역할

| 역할 | 주요 업무 |
|---|---|
| 인프라·IAM | Terraform, EKS, IRSA, S3, IAM Policy 구성 |
| 공격·검증 | 위협 모델, 공격 절차, 성공·실패 기준, 조치 전후 재현 |
| 로그·탐지 | EKS Audit Log, CloudTrail, S3 data event 수집과 타임라인 |
| 증적·통합 | 테스트 케이스, 결과 장부, 보고서, 발표, 비용·삭제 검증 |

3명이라면 로그·탐지와 증적·통합 역할을 합친다. 역할은 새 팀원들의 경험과 희망을 확인한 뒤 확정한다.

> 장운호 우선 희망 역할 — 공격·검증 담당: 공격 가설과 성공 조건을 정의하고, 실제 명령 결과와 로그를 대조하여 취약 상태·조치 상태의 차이를 증명한다.

## 8. 4주 수행 일정

| 주차 | 핵심 목표 | 통과 조건 |
|---|---|---|
| 1주차 | 팀 역할·위협 모델 확정, 최소 EKS·IRSA·S3·로그 환경 구성 | Pod가 의도한 Role을 사용하고 EKS·CloudTrail·S3 data event가 실제 수집됨 |
| 2주차 | 과도한 IAM Policy 적용, 공격 절차 실행, 단계별 원본 증적 수집 | 각 단계에 명령·실제 결과·판정 기준·관련 로그·영향 범위가 존재함 |
| 3주차 | IAM 최소 권한 조치, 동일 공격 재실행, 탐지 쿼리 작성 | 취약 상태 성공과 조치 상태 `AccessDenied` 차이가 재현됨 |
| 4주차 | 새 환경 재배포·전체 재실행, 보고서·발표·destroy 검증 | 새 기능 없이 재현성·증적·개인 기여·자원 삭제가 확인됨 |

### 8.1 1주차 통과 조건

```text
Pod가 의도한 IAM Role을 사용한다.
EKS 로그와 CloudTrail이 실제로 수집된다.
테스트 S3 객체 접근 이벤트를 조회할 수 있다.
```

1주차 종료까지 이 조건을 충족하지 못하면 기능을 추가하지 않는다.

### 8.2 2주차 통과 조건

각 공격 단계마다 다음이 하나 이상 존재해야 한다.

```text
명령 또는 요청
실제 결과
성공 판정 기준
관련 로그
영향 범위
```

### 8.3 4주차 동결 조건

4주차에는 새로운 기술이나 시나리오를 추가하지 않는다.

## 9. 실패 대비 축소안

1주차 안에 EKS가 안정적으로 구성되지 않으면 EKS를 붙잡고 전체 프로젝트를 소모하지 않는다.

```text
EC2 또는 ECS workload 침해 가정
→ 과도한 Instance Role 또는 Task Role 사용
→ 테스트 S3 객체 접근
→ CloudTrail 증적 확인
→ IAM 최소 권한 조치
→ 동일 공격 재검증
```

Kubernetes 요소는 사라지지만 workload identity와 AWS IAM 권한 오용이라는 핵심 보안 질문은 유지된다.

로그 통합이 어려우면 SIEM이나 대시보드를 만들지 않고, 시각·Role ARN·ServiceAccount·S3 객체를 기준으로 한 공격 타임라인 표를 최종 산출물로 사용한다.

## 10. 성공 기준

- Terraform으로 실험 환경을 재현하고 삭제할 수 있다.
- 취약 상태에서 테스트 S3 객체 접근이 성공한다.
- EKS Audit Log에서 통제된 Pod 진입 증거를 찾는다.
- CloudTrail에서 `AssumeRoleWithWebIdentity`를 확인한다.
- S3 `GetObject` data event를 확인한다.
- 조치 후 같은 접근이 실패한다.
- 취약·조치 상태의 IAM Policy 차이를 설명할 수 있다.
- 각 단계에서 무엇이 증명됐고 무엇이 증명되지 않았는지 구분한다.
- 실제 Secret과 개인정보가 보고서·Git·로그에 남지 않는다.
- 실험 종료 후 AWS 자원이 제거됐음을 확인한다.

## 11. 주요 산출물

1. 프로젝트 범위와 위협 모델
2. 시스템 아키텍처
3. Terraform 코드
4. 공격 테스트 케이스
5. 공격 실행 절차서
6. 단계별 증적 장부
7. CloudTrail·EKS Audit Log 조회 쿼리
8. IAM Policy 조치 전후 비교
9. 동일 조건 재점검 결과
10. 비용 및 자원 삭제 확인
11. 팀 기여와 개인 기여 문서
12. 최종 발표 자료

## 12. 멘토에게 확인할 질문

1. `kubectl exec`로 최초 침해를 가정하고 이후의 workload IAM 권한 오용을 검증하는 것이 신입 프로젝트에서 정직하고 유효한 범위인가요? 실제 애플리케이션 RCE까지 구현해야 의미가 있나요?
2. `Pod 침해 → IRSA Role 사용 → 테스트 S3 객체 접근 → CloudTrail/EKS Audit Log 확인 → 최소 권한 조치와 재검증`이 4주·3~4명 팀에 적절한 클라우드 보안 범위인가요?
3. 이 시나리오에서 반드시 남겨야 할 로그와 증적, 반대로 과감히 제외해야 할 부분은 무엇인가요?

## 13. 기술 근거

- [AWS EKS IAM 모범 사례](https://docs.aws.amazon.com/eks/latest/best-practices/identity-and-access-management.html)
- [AWS IAM·STS CloudTrail 연동](https://docs.aws.amazon.com/IAM/latest/UserGuide/cloudtrail-integration.html)
- [AWS EKS Control Plane Logging](https://docs.aws.amazon.com/eks/latest/userguide/control-plane-logs.html)
- [AWS S3 CloudTrail Data Events](https://docs.aws.amazon.com/AmazonS3/latest/userguide/enable-cloudtrail-logging-for-s3.html)
- [HashiCorp Terraform S3 Backend](https://developer.hashicorp.com/terraform/language/backend/s3)
