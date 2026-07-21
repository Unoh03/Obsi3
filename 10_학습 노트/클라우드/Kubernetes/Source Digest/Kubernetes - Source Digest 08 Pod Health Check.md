---
type: source-digest
status: stable
created: 2026-07-21
parent_moc: "[[10_학습 노트/클라우드/Kubernetes/00_Kubernetes MOC]]"
source: "[[40_자료/강의 자료/Kubernetes.pdf]]"
source_pages: 161-171
digest_role: chapter
digest_index: "[[10_학습 노트/클라우드/Kubernetes/Source Digest/Kubernetes - Source Digest v1]]"
chapter: Pod Health Check
source_hash: F97666865E22749C47640689B5C41DEE38476A40312A53915F60B4F6A4330D24
source_version: "PowerPoint PDF; 266 pages; metadata created 2024-07-18"
coverage_status: complete
extraction_method: "pdfplumber 0.11.9 text extraction + pypdfium2 render visual review"
reviewed_on: 2026-07-21
---

# Kubernetes Source Digest 08 — Pod Health Check

> 원자료 `Kubernetes.pdf` p.161-171을 페이지 단위로 옮긴 무손실 구조화 사본이다. Liveness와 Readiness에 관한 원자료 주석의 불일치는 임의로 교정하지 않고 해당 페이지에 표시한다.

## Coverage

| 범위 | Text | Visual | 원본 대조 | 상태 |
|---|---|---|---|---|
| p.161-171 | 완료 | 완료 | 완료 | 이 장 변환 완료 |

## PDF p.161

- 원문: [[40_자료/강의 자료/Kubernetes.pdf#page=161|Kubernetes.pdf p.161]]

### 원자료 내용

- 장 표지: `Kubernetes Pod Health-Check`.

## PDF p.162

- 원문: [[40_자료/강의 자료/Kubernetes.pdf#page=162|Kubernetes.pdf p.162]]

### 원자료 내용

#### Pod Health-Check

- Pod 내부 컨테이너의 Application이 정상적으로 동작하는지 확인하는 기능이다.
- Application 이상을 감지하면 컨테이너를 강제 종료하고 재시작하도록 구성할 수 있다.
- Kubelet이 `Liveness Probe`와 `Readiness Probe`를 사용해 수행한다.
- Handler 종류로 `EXEC`, `HTTP GET`, `TCP Socket`을 제시한다.
- Self-Healing을 구현하고 컨테이너 장애가 Client에 미치는 영향을 최소화할 수 있다고 설명한다.

#### Handler

- `EXEC`: 컨테이너 내부에서 명령을 실행한다. 종료 코드 `0`은 성공, 나머지는 실패이다.
- `HTTP GET`: 지정한 Web URI에 정기적으로 요청한다. HTTP 상태 코드 `200 이상 400 미만`은 성공, 나머지는 실패이다.
- `TCP Socket`: 지정 TCP port에 연결할 수 있으면 성공, 닫혀 있으면 실패이다.

#### Liveness와 Readiness

- Liveness: 컨테이너 Application이 정상 실행 중인지 검사하는 Self-Healing 구현체.
- Readiness: 컨테이너 Application이 Client 요청을 받을 준비가 됐는지 검사하며 `get` 명령의 `READY` 정보에 반영된다.
- Readiness는 새 Pod 배포 후 Application 준비 상태를 확인하는 용도로 주로 사용한다고 설명한다.

## PDF p.163

- 원문: [[40_자료/강의 자료/Kubernetes.pdf#page=163|Kubernetes.pdf p.163]]

### 원자료 내용

- Probe 공통 속성:
  - `initialDelaySeconds`: Pod 구성 후 지정 시간만큼 기다렸다가 Health Check를 시작한다.
  - `periodSeconds`: Liveness/Readiness Probe 수행 주기를 설정한다.
  - `successThreshold`: 실패 횟수를 초기화하기 위해 필요한 검사 성공 횟수를 지정한다.
  - `failureThreshold`: 연속 몇 번 실패했을 때 컨테이너를 초기화할지 정의한다.
  - `timeoutSeconds`: 상태 검사 응답을 기다리는 시간을 설정한다.

### 도식 의미

- Time 축에서 먼저 `InitialDelay`를 기다린 뒤 Probe를 시작한다.
- Probe 1은 `timeout` 안에 성공한다.
- 이후 `period` 간격의 Probe 2·3·4가 각각 `Fail 1`, `Fail 2`, `Fail 3`으로 연속 실패한다.
- 세 번째 연속 실패 뒤 `Pod restart` 화살표가 표시된다.
- 각 Probe마다 별도의 `timeout` 구간이 표시되어 있다.

## PDF p.164

- 원문: [[40_자료/강의 자료/Kubernetes.pdf#page=164|Kubernetes.pdf p.164]]

### 원자료 내용

- `liveness-probe.yml`의 일부이며 Pod 전체 내용은 TXT 교안을 참조하라고 적혀 있다.

```yaml
spec:
  containers:
    - name: my-app
      image: chlzzz/kube-image:list
      ports:
        - containerPort: 8000
      livenessProbe:
        httpGet:
          path: /liveness
          port: 8000
        initialDelaySeconds: 10
        periodSeconds: 3
        successThreshold: 1
        failureThreshold: 3
        timeoutSeconds: 5
```

- Handler는 `HTTP GET`이다.
- List App이 `/liveness` URI를 지원하지 않아 상태 검사가 실패하도록 만든 예제이다.
- Pod 배포 10초 후 시작하고 3초마다 검사한다.
- 성공 1회로 실패 횟수를 초기화하며 3회 연속 실패하면 컨테이너를 재시작한다.
- 5초 안에 응답하지 않으면 실패로 처리한다.

## PDF p.165

- 원문: [[40_자료/강의 자료/Kubernetes.pdf#page=165|Kubernetes.pdf p.165]]

### 원자료 내용

```bash
kubectl apply -f health_check/liveness-probe.yml
kubectl get pod -n delivery –w
```

- Watch 출력에서 `RESTARTS`가 `0 → 1 → 2 → 3`으로 늘어난다.
- 일정 시간이 지나면 Pod 상태가 `CrashLoopBackOff`로 바뀐다고 설명한다.

```bash
kubectl logs liveness-probe -n delivery
```

```text
[25/Jul/2022 19:19:26] "GET /liveness HTTP/1.1" 404 2171
Not Found: /liveness
[25/Jul/2022 19:19:29] "GET /liveness HTTP/1.1" 404 2171
Not Found: /liveness
```

- 지정 주기에 따라 Liveness Probe가 실행된다.
- `/liveness` page가 없어 `404`가 반환된다.
- HTTP `200 이상 400 미만`은 성공, 그 밖은 실패로 처리한다고 반복 설명한다.

> [!note] 원자료 문자
> Watch option은 원자료에서 ASCII hyphen이 아닌 `–w`로 표시된다. 실행 가능한 명령으로 임의 교정하지 않고 원자료 표기를 보존했다.

## PDF p.166

- 원문: [[40_자료/강의 자료/Kubernetes.pdf#page=166|Kubernetes.pdf p.166]]

### 원자료 내용

```bash
kubectl describe pod liveness-probe -n delivery
```

- Container 정보:

```text
Restart Count: 6
Liveness: http-get http://:8000/liveness delay=10s timeout=5s period=3s #success=1 #failure=3
```

- Event 핵심 내용:

```text
Normal  Scheduled  ...  Successfully assigned delivery/liveness-probe to node
Normal  Pulled     ...  Container image "chlzzz/kube-image:list" already ...
Normal  Created    ...  Created container my-app
Normal  Started    ...  Started container my-app
Normal  Killing    ...  Container my-app failed liveness probe, will be restarted
Warning Unhealthy  ...  Liveness probe failed: HTTP probe failed statuscode: 404
```

- `Restart Count`, Liveness 조건, Event list를 확인한다.

## PDF p.167

- 원문: [[40_자료/강의 자료/Kubernetes.pdf#page=167|Kubernetes.pdf p.167]]

### 원자료 내용

- 실패 예제 Pod를 삭제한다.

```bash
kubectl delete pod liveness-probe -n delivery
```

- 같은 manifest에서 Liveness URI를 App이 지원하는 `/list`로 바꾼다.

```yaml
spec:
  containers:
    - name: my-app
      image: chlzzz/kube-image:list
      ports:
        - containerPort: 8000
      livenessProbe:
        httpGet:
          path: /list
          port: 8000
        initialDelaySeconds: 10
        periodSeconds: 3
        successThreshold: 1
        failureThreshold: 3
        timeoutSeconds: 5
```

- 나머지 설정은 p.164와 같다.

## PDF p.168

- 원문: [[40_자료/강의 자료/Kubernetes.pdf#page=168|Kubernetes.pdf p.168]]

### 원자료 내용

```bash
kubectl apply -f health_check/liveness-probe.yml
kubectl get pod -n delivery –w
```

- Pod는 `1/1 Running`, `RESTARTS 0`을 유지한다.
- 정상 상태여서 컨테이너가 재시작되지 않는다고 설명한다.

```bash
kubectl logs liveness-probe -n delivery
```

```text
[25/Jul/2022 19:38:41] "GET /list HTTP/1.1" 301 0
[25/Jul/2022 19:38:41] "GET /list/ HTTP/1.1" 200 1923
[25/Jul/2022 19:38:44] "GET /list HTTP/1.1" 301 0
[25/Jul/2022 19:38:44] "GET /list/ HTTP/1.1" 200 1923
```

- `describe`의 Conditions:

```text
Ready           True
ContainersReady True
```

- 확인 후 Pod를 삭제한다.

```bash
kubectl delete pod liveness-probe -n delivery
```

## PDF p.169

- 원문: [[40_자료/강의 자료/Kubernetes.pdf#page=169|Kubernetes.pdf p.169]]

### 원자료 내용

- `readiness-probe.yml`의 일부이며 Pod 전체 내용은 TXT 교안을 참조하라고 적혀 있다.

```yaml
spec:
  containers:
    - name: my-app
      image: chlzzz/kube-image:list
      ports:
        - containerPort: 8000
      readinessProbe:
        exec:
          command:
            - ls
            - /usr/src/app/ready
        initialDelaySeconds: 10
        periodSeconds: 3
        successThreshold: 1
        failureThreshold: 3
        timeoutSeconds: 5
```

- Handler는 `EXEC`이며 `/usr/src/app/ready` 파일 존재 여부를 `ls`로 확인한다.

> [!warning] 원자료 주석 불일치
> YAML key는 `readinessProbe`인데 `initialDelaySeconds`와 `periodSeconds` 주석은 `Liveness Probe`라고 적혀 있다. `failureThreshold` 주석도 3회 실패 시 “컨테이너 재시작”이라고 적혀 있다. 이 설명은 다음 페이지의 실제 Readiness 결과(`Running`, `READY 0/1`, `RESTARTS 0`)와도 맞지 않으므로 원자료의 불일치로 보존한다.

## PDF p.170

- 원문: [[40_자료/강의 자료/Kubernetes.pdf#page=170|Kubernetes.pdf p.170]]

### 원자료 내용

```bash
kubectl apply -f health_check/readiness-probe.yml
kubectl get pod -n delivery –w
```

- Pod는 `Running`이지만 시간이 지나도 `READY 0/1`, `RESTARTS 0`이다.
- 원자료는 “Liveness Probe 검사는 통과했지만 Application이 사용자 요청을 받을 준비가 되지 않은 상태”라고 설명한다.

```bash
kubectl describe pod readiness-probe -n delivery
```

```text
Readiness: exec [ls /usr/src/app/ready] delay=10s timeout=5s period=3s #success=1 #failure=3
Conditions:
  Ready False
Events:
  Warning Unhealthy ... Readiness probe failed: ls: cannot access 'ready': No such file or directory
```

- Readiness Probe 조건, Conditions, Event list를 확인한다.

## PDF p.171

- 원문: [[40_자료/강의 자료/Kubernetes.pdf#page=171|Kubernetes.pdf p.171]]

### 원자료 내용

- Readiness 조건에 맞게 컨테이너 안에 `ready` 파일을 만들고 확인한다.

```bash
kubectl exec -it readiness-probe -n delivery -- touch /usr/src/app/ready
kubectl exec -it readiness-probe -n delivery -- ls /usr/src/app/ready
```

```text
/usr/src/app/ready
```

```bash
kubectl get pod readiness-probe -n delivery
```

```text
NAME             READY  STATUS   RESTARTS  AGE
readiness-probe  1/1    Running  0         5m32s
```

- Readiness 조건을 만족해 Client 요청을 받을 수 있는 상태가 됐다고 설명한다.
- 테스트 후 Pod를 삭제하고 `delivery` Namespace에 남은 리소스가 없음을 확인한다.

```bash
kubectl delete pod readiness-probe -n delivery
kubectl get all -n delivery
```

```text
No resources found in delivery namespace.
```

## 원자료 외 보충

- 없음. 이 문서는 PDF의 설명·manifest·실습 결과와 내부 불일치를 보존한다.

## 누락·검토 대기

- 원자료가 참조한 TXT manifest 전체는 제공 범위에 없어 PDF에 보이는 부분만 옮겼다.
- p.169의 Readiness 주석 불일치는 원자료 안에서 확인됐으며, 이 문서에서는 외부 공식 문서 대조를 수행하지 않았다.
