---
type: concept
status: active
created: "2026-07-16"
topic: ubuntu-network-netplan
parent_moc: "[[10_학습 노트/리눅스(우분투)/00_리눅스_목차]]"
source: "Ubuntu Server documentation; Netplan documentation"
reviewed_on: "2026-07-16"
---

# Ubuntu 네트워크 진단과 Netplan

> 현재 상태를 계층별로 확인한 뒤 Netplan의 병합 설정을 읽고, 원격 접속을 끊지 않는 검증 절차로 변경한다.

## 범위

- 설명하는 것: interface·주소·route·DNS·listening socket 진단, Netplan 확인과 안전 적용
- 다루지 않는 것: 특정 실습 토폴로지의 고정 IP, router 설정, BIND authoritative server 구축

## 진단 순서

```text
link
→ IP address
→ route
→ DNS resolver
→ listening socket
→ application request
```

```bash
ip -br link
ip -br addr
ip route
resolvectl status
sudo ss -lntup
```

- interface가 내려가 있으면 상위 계층 진단보다 link 상태를 먼저 본다.
- 주소가 있어도 default route가 없으면 외부 network에 도달하지 못할 수 있다.
- `ping` 실패만으로 host가 죽었다고 단정하지 않는다. ICMP가 차단됐을 수 있다.
- `ss`의 listening socket은 firewall이나 외부 도달 가능성을 증명하지 않는다.

애플리케이션과 같은 이름 해석 경로를 확인하려면 다음처럼 NSS 결과와 실제 요청을 함께 본다.

```bash
getent ahosts example.com
curl -I https://example.com
```

## Ubuntu의 DNS 설정 경계

Ubuntu Server에서는 Netplan이 `systemd-networkd` 또는 `NetworkManager`용 설정을 만들고, `systemd-resolved`가 resolver 구성을 담당하는 경우가 일반적이다. 그러나 실제 renderer와 `/etc/resolv.conf` 연결 상태는 설치 환경마다 확인한다.

```bash
readlink -f /etc/resolv.conf
resolvectl status
sudo netplan get
```

- `/etc/resolv.conf`를 직접 덮어쓰는 방식은 generated symlink 구성에서 지속되지 않을 수 있다.
- `resolvectl dns <interface> <server>`는 즉시 per-link DNS를 바꾸는 용도로 쓸 수 있지만, network 재구성 뒤에도 유지할 영구 정책은 Netplan이나 현재 renderer 설정에 둔다.

## Netplan 파일을 읽는 방법

Netplan은 `/lib/netplan`, `/etc/netplan`, `/run/netplan`의 여러 YAML을 병합할 수 있다. 파일 하나만 보고 전체 유효 설정이라고 단정하지 않는다.

```bash
sudo netplan get
ls -l /etc/netplan
```

`netplan get`은 병합된 현재 YAML view를 보여준다. 기존 파일을 통째로 `tee`로 덮어쓰면 interface, route, renderer, cloud-init 설정을 잃을 수 있으므로 먼저 병합 결과와 파일 출처를 확인한다.

## YAML 구조 예시

아래는 문법 구조 예시이며 interface 이름과 DNS 주소를 현재 환경에 맞게 바꿔야 한다.

```yaml
network:
  version: 2
  ethernets:
    ens33:
      dhcp4: true
      nameservers:
        addresses:
          - 192.168.42.133
          - 1.1.1.1
```

- `addresses:` 뒤에는 YAML sequence가 와야 한다.
- DHCP가 제공하는 DNS와 수동 DNS의 결합·우선순위는 renderer와 `dhcp4-overrides` 설정을 확인한다.
- 기존 route나 match 규칙을 모른 채 이 예시로 파일 전체를 교체하지 않는다.

## 안전한 변경 절차

1. out-of-band console 또는 복구 경로가 있는지 확인한다.
2. `netplan get`과 기존 YAML을 보존한다.
3. 기존 파일을 최소 범위로 수정한다.
4. 적용 없이 backend config를 생성해 오류를 확인한다.

```bash
sudo netplan generate
```

5. SSH 원격 작업이라면 timeout 뒤 rollback하는 시험 적용을 우선 검토한다.

```bash
sudo netplan try
```

6. prompt에서 유지 여부를 확인하고, 실제 주소·route·DNS·SSH 연결을 다시 검증한다. `netplan try`도 rollback 상태를 별도로 확인해야 하는 알려진 제약이 있다.
7. console에서 직접 적용하거나 시험 적용 대신 의도적으로 반영할 때만 다음을 사용한다.

```bash
sudo netplan apply
```

`netplan apply`는 running system의 interface를 실제로 변경하므로 SSH 세션 단절 가능성이 있다.

## 오판하기 쉬운 지점

- 오해: `/etc/netplan/00-installer-config.yaml`이 항상 유일한 설정 파일이다.
  - 정확한 설명: 파일명과 개수는 환경마다 다르고 여러 위치의 YAML이 병합될 수 있다.
- 오해: `dhclient`가 모든 현대 Ubuntu interface 관리의 표준 명령이다.
  - 정확한 설명: 현재 renderer와 DHCP client 구성을 먼저 확인한다.
- 오해: DNS 조회 성공은 application 통신 성공과 같다.
  - 정확한 설명: route, firewall, TLS, proxy와 application 상태는 별도로 검증한다.
- 오해: `netplan generate`가 running network를 바꾼다.
  - 정확한 설명: backend configuration을 생성하지만 적용하지 않는다.

## 공식 근거

- [Ubuntu Server - Configuring networks](https://documentation.ubuntu.com/server/explanation/networking/configuring-networks/)
- [Netplan - YAML configuration](https://netplan.readthedocs.io/en/latest/netplan-yaml/)
- [Netplan - get](https://netplan.readthedocs.io/en/latest/netplan-get/)
- [Netplan - generate](https://netplan.readthedocs.io/en/latest/netplan-generate/)
- [Netplan - try](https://netplan.readthedocs.io/en/latest/netplan-try/)
- [Netplan - apply](https://netplan.readthedocs.io/en/latest/netplan-apply/)

## 관련 노트

- [[10_학습 노트/리눅스(우분투)/우분투#🌐네트워크 관리 및 트러블슈팅 도구 (L3~L7)|우분투 legacy - 네트워크 도구]]
- [[10_학습 노트/리눅스(우분투)/마지막 총정리 문제#1. IP 설정|마지막 총정리 문제 legacy - IP 설정]]
- [[10_학습 노트/리눅스(우분투)/00_리눅스_목차|리눅스 목차]]
