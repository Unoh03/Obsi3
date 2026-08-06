---
type: lab-note
status: verified
created: 2026-08-06
updated: 2026-08-06
scope: Grafana, Docker, Amazon Athena, AWS 자격증명, 장애 분석
parent_moc: "[[10_학습 노트/클라우드/00_클라우드_목차]]"
---

# Grafana 로컬 Docker에서 Amazon Athena 연결

## 1. 목적

Grafana Cloud에서 Amazon Athena 데이터 소스를 추가하는 즉시 플러그인 내부 오류가 발생했다. 브라우저 간섭 가능성을 제거해도 해결되지 않아, 로컬 Windows PC의 Docker Desktop에서 Grafana를 실행하고 기존 AWS CLI 프로필로 Athena에 연결했다.

최종 구조는 다음과 같다.

```text
Brave
└─ http://127.0.0.1:3000
   └─ Docker Desktop의 로컬 Grafana
      ├─ Amazon Athena 플러그인 3.2.0
      ├─ AWS credentials profile: terra-user
      └─ AWS API
         ├─ Athena
         ├─ Glue Data Catalog
         └─ S3 보안 로그 및 Athena 결과 경로
```

이 방식은 AWS 로그 전체를 PC에 내려받는 구조가 아니다. Grafana 컨테이너가 AWS API를 호출하고, Athena가 S3 데이터를 조회한 결과를 Grafana가 받아 시각화한다.

---

## 2. 최종 확인 환경

| 항목 | 확인값 |
|---|---|
| OS 셸 | PowerShell 7.6.4 |
| Docker Desktop | 4.84.0 |
| Docker Engine | 29.6.2, Linux/amd64 |
| Docker context | `desktop-linux` |
| Grafana 이미지 | `grafana/grafana:latest` |
| 당시 pull digest | `sha256:d177053ab62253815f130d81504f77063baf5fd4ca93299d6048453bd31e047a` |
| 컨테이너 이름 | `grafana-local` |
| 영속 볼륨 | `grafana-local-data` |
| 로컬 접속 주소 | `http://127.0.0.1:3000` |
| Athena 플러그인 | `grafana-athena-datasource@3.2.0` |
| Grafana 기능 플래그 | `datasourceLegacyIdApi` |
| AWS 프로필 | `terra-user` |
| AWS 계정 | `433048100798` |
| 기본 리전 | `ap-northeast-2` |
| Athena Catalog | `AwsDataCatalog` |
| Athena Database | `aws_topology_security` |
| Athena Workgroup | `primary` |

> [!important]
> `terra-user`의 Access Key와 Secret Key 값은 문서에 기록하지 않는다. Windows 사용자 홈의 `.aws` 디렉터리를 컨테이너에 읽기 전용으로 마운트한다.

---

## 3. 최종 성공 절차

### 3.1 Docker Desktop Engine 시작

```powershell
# Docker Desktop의 Linux Engine을 시작하고 최대 120초까지 기다린다.
docker desktop start --timeout 120

# Docker Desktop 자체 상태가 running인지 확인한다.
docker desktop status

# Client뿐 아니라 Server 섹션도 출력되는지 확인한다.
# Server가 나오면 Docker daemon과 정상 연결된 상태다.
docker version
```

정상 판정:

```text
Status: running

Server: Docker Desktop ...
 Engine:
  Version: ...
```

### 3.2 AWS CLI 프로필과 Athena 접근 검증

```powershell
# terra-user 프로필로 현재 AWS 주체와 계정을 확인한다.
aws sts get-caller-identity --profile terra-user

# terra-user 프로필로 서울 리전의 Athena Data Catalog 목록을 조회한다.
# 이 명령이 성공하면 최소한 자격증명, 리전, ListDataCatalogs 권한은 정상이다.
aws athena list-data-catalogs `
  --profile terra-user `
  --region ap-northeast-2 `
  --query "DataCatalogsSummary[].CatalogName" `
  --output table
```

확인된 정상 결과:

```text
--------------------
| ListDataCatalogs |
+------------------+
|  AwsDataCatalog  |
+------------------+
```

`terra-user`가 관리자라는 추정만으로 판단하지 않고, 실제 `athena:ListDataCatalogs` 호출 성공을 근거로 사용한다.

### 3.3 Grafana 데이터 볼륨 생성

```powershell
# Grafana 설정, 로컬 사용자, 데이터 소스, 대시보드를 보존할 Docker 볼륨을 생성한다.
# 같은 이름이 이미 존재해도 해당 이름을 반환하므로 반복 실행할 수 있다.
docker volume create grafana-local-data
```

이 볼륨을 유지하면 컨테이너를 삭제하고 다시 만들어도 Grafana 로그인 비밀번호와 설정이 보존된다.

### 3.4 기존 컨테이너 제거

설정 변경 시 컨테이너만 다시 만들고 볼륨은 유지한다.

```powershell
# 이름이 grafana-local인 모든 컨테이너를 조회한다.
$existingGrafana = docker ps -a `
  --filter "name=^/grafana-local$" `
  --format "{{.Names}}"

# 기존 grafana-local 컨테이너가 있을 때만 강제 삭제한다.
# Docker 볼륨 grafana-local-data는 삭제하지 않는다.
if ($existingGrafana -eq "grafana-local") {
    docker rm -f grafana-local
}
```

### 3.5 최종 성공한 Grafana 컨테이너 실행

아래는 실제 `docker run` 인수를 PowerShell 배열로 분리한 것이다. 각 줄에 주석을 붙여도 복사 실행이 깨지지 않는다.

```powershell
# docker 명령에 전달할 모든 인수를 순서대로 구성한다.
$dockerArgs = @(
    "run" # 새 컨테이너를 생성하고 실행한다.

    "-d" # 터미널을 점유하지 않고 백그라운드에서 실행한다.

    "--name" # 다음 값을 컨테이너 이름으로 사용한다.
    "grafana-local" # 컨테이너 이름을 grafana-local로 고정한다.

    "--restart" # 다음 값을 Docker 재시작 정책으로 사용한다.
    "unless-stopped" # 사용자가 명시적으로 중지하지 않았다면 Docker 재시작 후 자동 기동한다.

    "-p" # 다음 값으로 호스트와 컨테이너 포트를 연결한다.
    "127.0.0.1:3000:3000" # 호스트의 loopback 3000만 컨테이너 3000에 연결해 외부 공개를 막는다.

    "--mount" # 다음 값으로 Grafana 영속 데이터 볼륨을 연결한다.
    "type=volume,source=grafana-local-data,target=/var/lib/grafana" # Grafana DB, 설정, 플러그인 데이터를 보존한다.

    "--mount" # 다음 값으로 Windows의 AWS 설정 디렉터리를 연결한다.
    "type=bind,source=$env:USERPROFILE\.aws,target=/home/grafana/.aws,readonly" # AWS 자격증명을 Grafana HOME 아래에 읽기 전용으로 마운트한다.

    "-e" # 다음 값을 컨테이너 환경변수로 전달한다.
    "AWS_PROFILE=terra-user" # 기본으로 사용할 AWS 프로필을 terra-user로 지정한다.

    "-e" # 다음 값을 컨테이너 환경변수로 전달한다.
    "AWS_SDK_LOAD_CONFIG=1" # AWS SDK가 credentials뿐 아니라 config 파일도 읽도록 한다.

    "-e" # 다음 값을 컨테이너 환경변수로 전달한다.
    "AWS_SHARED_CREDENTIALS_FILE=/home/grafana/.aws/credentials" # 공유 자격증명 파일 경로를 명시한다.

    "-e" # 다음 값을 컨테이너 환경변수로 전달한다.
    "AWS_CONFIG_FILE=/home/grafana/.aws/config" # AWS config 파일 경로를 명시한다.

    "-e" # 다음 값을 컨테이너 환경변수로 전달한다.
    "GF_FEATURE_TOGGLES_ENABLE=datasourceLegacyIdApi" # 구형 숫자형 Data Source ID API를 임시 활성화한다.

    "-e" # 다음 값을 컨테이너 환경변수로 전달한다.
    "GF_PLUGINS_PREINSTALL=grafana-athena-datasource@3.2.0" # Athena 플러그인을 3.2.0으로 고정해 자동 설치한다.

    "grafana/grafana:latest" # Grafana 공식 Docker 이미지를 사용한다.
)

# 위 배열을 docker 명령에 그대로 전달해 컨테이너를 실행한다.
docker @dockerArgs
```

실제로 사용한 일반적인 멀티라인 표현은 다음과 동일하다.

```powershell
# Grafana 컨테이너를 백그라운드로 생성한다.
docker run -d `
  --name grafana-local `
  --restart unless-stopped `
  -p 127.0.0.1:3000:3000 `
  --mount "type=volume,source=grafana-local-data,target=/var/lib/grafana" `
  --mount "type=bind,source=$env:USERPROFILE\.aws,target=/home/grafana/.aws,readonly" `
  -e "AWS_PROFILE=terra-user" `
  -e "AWS_SDK_LOAD_CONFIG=1" `
  -e "AWS_SHARED_CREDENTIALS_FILE=/home/grafana/.aws/credentials" `
  -e "AWS_CONFIG_FILE=/home/grafana/.aws/config" `
  -e "GF_FEATURE_TOGGLES_ENABLE=datasourceLegacyIdApi" `
  -e "GF_PLUGINS_PREINSTALL=grafana-athena-datasource@3.2.0" `
  grafana/grafana:latest
```

> [!warning]
> PowerShell의 백틱 `` ` `` 은 줄의 마지막 문자여야 한다. 백틱 뒤에 공백이나 주석을 붙이면 줄 연속이 깨질 수 있다. 줄별 설명이 필요한 경우 위의 `$dockerArgs` 배열 방식을 사용한다.

### 3.6 컨테이너와 플러그인 기동 검증

```powershell
# grafana-local 컨테이너가 Up 상태인지 확인한다.
docker ps --filter "name=grafana-local"

# Grafana 시작 및 플러그인 설치 관련 최근 로그를 확인한다.
docker logs --tail 200 grafana-local 2>&1 |
  Select-String -Pattern "HTTP Server Listen|grafana-athena-datasource|Plugin successfully installed|error" `
    -CaseSensitive:$false
```

확인된 정상 로그:

```text
HTTP Server Listen address=[::]:3000
Plugin registered pluginId=grafana-athena-datasource
Plugin successfully installed pluginId=grafana-athena-datasource version=3.2.0
```

### 3.7 AWS 파일 마운트와 기능 플래그 검증

```powershell
# 컨테이너 내부에서 Grafana 사용자의 HOME과 AWS 관련 환경변수를 출력한다.
# Access Key와 Secret Key 값은 출력하지 않는다.
docker exec grafana-local sh -lc '
echo "HOME=$HOME"
printenv | grep -E "^AWS_(PROFILE|SDK_LOAD_CONFIG|SHARED_CREDENTIALS_FILE|CONFIG_FILE)="
'

# credentials와 config 파일이 Grafana 사용자에게 읽기 가능한지만 확인한다.
docker exec grafana-local sh -lc '
test -r /home/grafana/.aws/credentials && echo "credentials readable"
test -r /home/grafana/.aws/config && echo "config readable"
'

# 컨테이너에 datasourceLegacyIdApi 기능 플래그가 실제 전달됐는지 확인한다.
docker inspect grafana-local `
  --format '{{range .Config.Env}}{{println .}}{{end}}' |
  Select-String "GF_FEATURE_TOGGLES_ENABLE=datasourceLegacyIdApi"
```

정상 판정:

```text
HOME=/home/grafana
AWS_PROFILE=terra-user
AWS_SHARED_CREDENTIALS_FILE=/home/grafana/.aws/credentials
AWS_CONFIG_FILE=/home/grafana/.aws/config
credentials readable
config readable
GF_FEATURE_TOGGLES_ENABLE=datasourceLegacyIdApi
```

### 3.8 Grafana HTTP 상태 확인

```powershell
# 로컬 Grafana의 health API를 호출해 버전과 DB 상태를 확인한다.
Invoke-RestMethod http://127.0.0.1:3000/api/health |
  Format-List
```

### 3.9 Grafana 웹 UI 설정

브라우저에서 접속한다.

```text
http://127.0.0.1:3000
```

최초 기본 로그인은 `admin / admin`이다. 영속 볼륨을 재사용했다면 이전에 변경한 비밀번호가 유지된다.

이동 경로:

```text
Connections
→ Add new connection
→ Amazon Athena
→ Add new data source
```

설정값:

| 필드 | 값 |
|---|---|
| Authentication Provider | `Credentials file` |
| Credentials Profile Name | `terra-user` |
| Assume Role ARN | 비움 |
| External ID | 비움 |
| Endpoint | 비움 |
| Default Region | `ap-northeast-2` |
| Data source | `AwsDataCatalog` |
| Database | `aws_topology_security` |
| Workgroup | `primary` |

여기서 `Data source`는 IAM 사용자나 AWS 프로필이 아니라 **Athena Data Catalog**를 의미한다. `terra-user`는 위쪽의 `Credentials Profile Name`에 입력한다.

### 3.10 Athena Output Location 확인

`bank-security-lab-infra` 저장소 루트에서 실행한다.

```powershell
# Foundation Terraform state에서 보안 로그 버킷 이름을 읽는다.
$bucket = terraform -chdir=foundation output -raw security_log_bucket_name

# Grafana 전용 Athena 결과 경로를 완전한 S3 URI로 만든다.
$outputLocation = "s3://$bucket/athena-results/grafana/"

# Grafana UI에 복사할 값을 출력한다.
$outputLocation
```

출력된 전체 S3 URI를 Grafana의 `Output Location`에 입력하고 `Save & test`를 누른다.

---

## 4. 실패했던 경로와 오류 원인

### 4.1 Grafana Cloud에서 플러그인 설정 화면이 즉시 실패

증상:

```text
Connections
→ Add new data source
→ Amazon Athena
→ Add new data source
→ An error occurred within the plugin
```

오류는 Role ARN, External ID, Region 등을 입력하기 전 발생했다. 따라서 당시 오류를 IAM·S3 권한 문제로 볼 수 없었다.

Grafana Athena 공식 저장소에는 설정 화면을 열 때 동일한 `plugin.requestFailureError` 500 오류가 발생하는 공개 이슈가 있다.

- https://github.com/grafana/athena-datasource/issues/821

Brave 확장 프로그램과 Shields를 끄고 사이트 데이터를 초기화하는 시도도 했지만, 동일 단계에서 실패했다. 이에 Grafana Cloud를 계속 수정하지 않고 로컬 Docker Grafana로 전환했다.

### 4.2 Docker CLI는 있었지만 Docker Engine이 꺼져 있었음

증상:

```text
failed to connect to the docker API at
npipe:////./pipe/dockerDesktopLinuxEngine
The system cannot find the file specified.
```

해석:

- `docker version`의 Client는 출력됐다.
- `docker compose version`도 출력됐다.
- 그러나 Docker Desktop Linux Engine의 named pipe가 존재하지 않았다.
- 즉 CLI와 Compose 플러그인은 설치됐지만 Docker daemon은 실행되지 않은 상태였다.

해결 명령:

```powershell
# Docker Desktop Linux Engine을 시작한다.
docker desktop start --timeout 120

# Server 섹션이 나타나는지 확인한다.
docker version
```

### 4.3 AWS 디렉터리를 잘못된 컨테이너 경로에 마운트

첫 실행에서는 다음 경로를 사용했다.

```text
호스트: %USERPROFILE%\.aws
컨테이너: /usr/share/grafana/.aws
```

그러나 컨테이너에서 확인한 Grafana 사용자의 HOME은 다음이었다.

```text
HOME=/home/grafana
uid=472(grafana)
```

따라서 Credentials file 방식의 기본 경로와 일치하도록 다음으로 수정했다.

```text
/home/grafana/.aws
```

또한 경로 해석의 모호성을 없애기 위해 다음 환경변수를 명시했다.

```text
AWS_SHARED_CREDENTIALS_FILE=/home/grafana/.aws/credentials
AWS_CONFIG_FILE=/home/grafana/.aws/config
```

이 수정은 올바른 정리였지만, 이것만으로 `Data source: Not found`가 해결되지는 않았다.

### 4.4 호스트와 컨테이너 자격증명은 정상인데 Catalog가 Not found

직접 확인 결과:

- 호스트에서 `aws sts get-caller-identity --profile terra-user` 성공
- 호스트에서 `aws athena list-data-catalogs` 성공
- 컨테이너에서 credentials와 config가 읽기 가능
- Grafana에서 Catalog를 눌렀을 때 Docker 로그에 Athena, credential, AccessDenied 오류가 없음

이 조합은 요청이 AWS API에 도달하기 전 Grafana API 계층에서 실패하고 있음을 시사했다.

### 4.5 최종 해결: `datasourceLegacyIdApi` 활성화

Athena 플러그인 3.2.0의 설정 코드는 Data Source 숫자 ID를 이용해 다음 형태의 API를 호출한다.

```text
/api/datasources/{numeric-id}/resources/catalogs
/api/datasources/{numeric-id}/resources/databases
/api/datasources/{numeric-id}/resources/workgroups
```

플러그인 소스:

- https://github.com/grafana/athena-datasource/blob/v3.2.0/src/ConfigEditor.tsx

신형 Grafana에서는 구형 Data Source ID API가 기본 비활성화되는 변경이 있었다. 이를 임시 호환 플래그로 다시 켰다.

```text
GF_FEATURE_TOGGLES_ENABLE=datasourceLegacyIdApi
```

직접 확인된 사실은 다음이다.

```text
플래그 없음  → Data source: Not found
플래그 추가  → AwsDataCatalog 표시, 연결 절차 진행 성공
```

따라서 이 환경에서 최종 장애 원인은 **최신 Grafana 이미지와 Athena 플러그인 3.2.0 사이의 Legacy Data Source ID API 호환성 문제**로 판단한다.

> [!note]
> 당시 정확한 Grafana 버전 문자열은 실행 기록에 남기지 않았다. 다만 기능 플래그 추가 전후의 결과 차이는 직접 확인했다. 이후에는 `/api/health` 결과도 함께 기록한다.

### 4.6 `<SECURITY_LOG_BUCKET>` 플레이스홀더를 실제 ARN처럼 사용

Grafana Cloud용 IAM 인라인 정책 초안에서 다음 문자열이 그대로 남아 있었다.

```text
arn:aws:s3:::<SECURITY_LOG_BUCKET>
```

이 값은 실제 보안 로그 버킷 이름으로 교체해야 한다. 그대로 두면 나중에 Athena가 S3 로그를 읽거나 결과를 쓸 때 권한 오류가 난다.

다만 이 문제는 `ListDataCatalogs`나 로컬 Grafana의 `Not found` 직접 원인은 아니었다.

또한 최종 로컬 구성은 `terra-user`의 Credentials file을 직접 사용하므로, Grafana Cloud용 Role `aws-topology-grafana-cloud-read`는 현재 로컬 연결 경로에 사용되지 않는다.

### 4.7 Output Location을 `s3://`로만 입력

증상:

```text
InvalidRequestException: No output location provided
```

원인:

- `s3://`는 Bucket 이름과 Prefix가 없는 불완전한 URI다.
- `primary` Workgroup에도 강제 적용되는 기본 결과 경로가 없었으므로 Athena가 Query Result를 저장할 위치를 결정하지 못했다.

해결:

```powershell
# 실제 보안 로그 Bucket 이름을 Terraform output에서 조회한다.
$bucket = terraform -chdir=foundation output -raw security_log_bucket_name

# Bucket 이름과 Prefix가 모두 포함된 완전한 URI를 생성한다.
$outputLocation = "s3://$bucket/athena-results/grafana/"

# Grafana Output Location에 붙여넣을 값을 확인한다.
$outputLocation
```

완전한 S3 URI를 입력한 뒤 `Save & test`를 다시 실행하자 `Data source is working`이 표시됐다.

---

## 5. 오류 판별표

| 증상 | 주요 원인 | 확인 방법 |
|---|---|---|
| `dockerDesktopLinuxEngine` pipe 없음 | Docker Desktop Engine 중지 | `docker desktop status`, `docker version`의 Server 유무 |
| 컨테이너가 바로 종료 | Grafana 시작·마운트·환경변수 오류 | `docker ps -a`, `docker logs grafana-local` |
| Athena 플러그인이 없음 | 플러그인 설치 실패 | 로그에서 `Plugin successfully installed` 확인 |
| Credentials profile을 못 찾음 | `.aws` 마운트 또는 프로필명 오류 | 컨테이너 내부 파일 readable 확인 |
| `AccessDeniedException` | 자격증명은 읽었으나 IAM 권한 부족 | 오류의 Action과 User ARN 확인 |
| `Data source: Not found`, AWS 오류 로그 없음 | Grafana/플러그인 API 호환성 | `datasourceLegacyIdApi` 플래그 확인 |
| `catalogName must have length >= 1` | Catalog를 선택하지 않은 상태에서 Database 조회 | `Data source → Database → Workgroup` 순서 준수 |
| `No output location provided` | Output Location이 비었거나 `s3://`만 입력 | 완전한 `s3://bucket/prefix/` URI 입력 |
| S3 query result write 실패 | Output Location 또는 S3 PutObject 권한 오류 | 완전한 S3 URI와 IAM 정책 확인 |

---

## 6. 운영 명령

### 컨테이너 중지와 시작

```powershell
# Grafana 컨테이너를 정상 중지한다.
docker stop grafana-local

# 중지된 Grafana 컨테이너를 다시 시작한다.
docker start grafana-local

# 컨테이너를 한 번에 재시작한다.
docker restart grafana-local
```

### 상태와 로그 확인

```powershell
# 현재 실행 중인 Grafana 컨테이너 상태를 확인한다.
docker ps --filter "name=grafana-local"

# 최근 100줄의 Grafana 로그를 확인한다.
docker logs --tail 100 grafana-local

# 새 로그를 실시간으로 따라간다.
# 종료는 Ctrl+C이며 컨테이너는 계속 실행된다.
docker logs -f grafana-local
```

### 컨테이너만 삭제

```powershell
# 컨테이너만 삭제한다.
# grafana-local-data 볼륨은 남으므로 Grafana 설정은 보존된다.
docker rm -f grafana-local
```

### 완전 초기화

```powershell
# Grafana 컨테이너를 삭제한다.
docker rm -f grafana-local

# Grafana 영속 볼륨까지 삭제한다.
# 사용자, 비밀번호, 데이터 소스, 대시보드와 플러그인 데이터가 모두 사라진다.
docker volume rm grafana-local-data
```

---

## 7. 보안상 주의사항

1. 포트는 `127.0.0.1:3000:3000`으로 바인딩한다. `0.0.0.0:3000`이나 단순 `3000:3000`을 사용하면 다른 네트워크 인터페이스에서 접근 가능해질 수 있다.
2. `%USERPROFILE%\.aws`는 반드시 `readonly`로 마운트한다.
3. Access Key와 Secret Key를 Grafana UI, Markdown, Git 저장소, 스크린샷에 직접 기록하지 않는다.
4. `terra-user`가 광범위한 관리자 권한을 갖고 있다면 장기적으로는 Grafana 로컬 전용 최소 권한 프로필 또는 Role로 분리하는 것이 바람직하다.
5. `grafana/grafana:latest`는 변경 가능한 태그다. 재현성을 높이려면 정상 동작을 확인한 Grafana 버전 또는 이미지 digest를 고정한다.
6. `datasourceLegacyIdApi`는 호환용 임시 플래그다. Athena 플러그인이 신형 API로 수정되면 플래그 제거 여부를 재검증한다.

---

## 8. 근거 자료

- Grafana Docker 설치: https://grafana.com/docs/grafana/latest/setup-grafana/installation/docker/
- Grafana AWS 인증: https://grafana.com/docs/grafana/latest/datasources/aws-cloudwatch/aws-authentication/
- Grafana Athena 설정: https://grafana.com/docs/plugins/grafana-athena-datasource/latest/configure/
- Athena 플러그인 설정 화면 오류 이슈: https://github.com/grafana/athena-datasource/issues/821
- Athena 플러그인 3.2.0 ConfigEditor: https://github.com/grafana/athena-datasource/blob/v3.2.0/src/ConfigEditor.tsx
- Grafana Data Source API 변경 안내: https://grafana.com/whats-new/2026-04-14-deprecated-data-source-apis-disabled-by-default/

---

## 9. 최종 요약

```text
Grafana Cloud Athena 플러그인 설정 화면 오류
→ 로컬 Docker Grafana로 전환
→ Docker Desktop Engine 시작
→ AWS CLI terra-user와 AwsDataCatalog 접근 검증
→ Grafana 볼륨 생성
→ .aws를 /home/grafana/.aws에 readonly 마운트
→ Athena 플러그인 3.2.0 고정
→ datasourceLegacyIdApi 활성화
→ Credentials file / terra-user 선택
→ AwsDataCatalog / aws_topology_security / primary 선택
→ Athena 결과 S3 경로 입력
→ Save & test
→ Data source is working
```

---

## 10. 최종 연결 성공 화면

아래 화면은 로컬 Grafana에서 Amazon Athena 데이터 소스가 정상 연결된 최종 상태다.

![[10_학습 노트/클라우드/_assets/Grafana 로컬 Docker에서 Athena 연결/01_Athena_Data_Source_연결_성공.jpg]]

**그림 1. 로컬 Grafana Amazon Athena Data Source 연결 성공**

화면에서 확인되는 최종 설정은 다음과 같다.

| 항목 | 확인값 |
|---|---|
| Authentication Provider | `Credentials file` |
| Credentials Profile Name | `terra-user` |
| Assume Role ARN | 비움 |
| External ID | 비움 |
| Endpoint | 비움 |
| Default Region | `ap-northeast-2` |
| Data source | `AwsDataCatalog` |
| Database | `aws_topology_security` |
| Workgroup | `primary` |
| Output Location | 실제 보안 로그 Bucket 아래의 Athena 결과 Prefix |
| 최종 검증 | `Data source is working` |

> [!success]
> 초록색 `Data source is working` 메시지는 Grafana가 현재 자격증명과 Athena 설정으로 실제 테스트 Query를 실행하고 결과를 받을 수 있음을 확인한 직접 증거다.
