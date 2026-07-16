---
type: concept
status: active
created: "2026-07-16"
topic: linux-process-session
parent_moc: "[[10_학습 노트/리눅스(우분투)/00_리눅스_목차]]"
source: "GNU Bash Reference Manual 5.3; GNU Coreutils 9.11"
reviewed_on: "2026-07-16"
---

# Bash 세션과 백그라운드 작업

> `&`는 쉘이 기다리지 않게 할 뿐이고, 로그아웃 뒤에도 작업을 유지하는 문제는 세션·신호·입출력을 별도로 처리해야 한다.

## 범위

- 설명하는 것: foreground/background, SSH 종료와 `SIGHUP`, 일회성 `nohup`, 로그와 종료 상태
- 다루지 않는 것: 백업 도구 자체, 정기 스케줄러 설계, 장기 서비스의 완전한 systemd unit

## 핵심 구조

```text
SSH 연결
→ 제어 터미널
→ 대화형 Bash
→ job / process
```

프로세스의 사용자 소유권과 SSH 세션과의 연결은 다른 문제다. 백그라운드로 보내도 실행 사용자는 그대로이며, 터미널 입출력과 shell job table, 종료 시 전달될 수 있는 `SIGHUP` 관계가 자동으로 사라지는 것은 아니다.

### `&`가 하는 일

```bash
./backup.sh &
```

- Bash가 명령 종료를 기다리지 않고 다음 prompt를 표시한다.
- 프로세스를 서비스로 등록하지 않는다.
- 표준 입력·출력·오류를 터미널에서 자동 분리하지 않는다.
- 로그아웃 뒤 생존을 보장하는 단독 수단이 아니다.

## 목적에 따른 선택

| 상황 | 우선 검토할 방식 | 이유 |
|---|---|---|
| 짧은 일회성 비대화형 작업 | `nohup` + 명시적 redirection + `&` | hangup을 무시하고 터미널 입출력을 분리할 수 있다. |
| 화면을 다시 붙여 조작해야 하는 작업 | terminal multiplexer | 세션을 분리했다가 다시 연결하는 용도다. 설치 여부를 먼저 확인한다. |
| 중요하거나 반복되는 장기 작업 | systemd service/timer | 실행 사용자, 재시작, 로그, 종료 상태와 중복 실행을 서비스 관리자가 통제한다. |

운영 중요도가 높을수록 임시 shell job보다 서비스 관리 방식을 택한다.

## 일회성 작업 예시

다음은 동작 구조를 보여주는 예시다. 실행 경로와 쓰기 권한을 먼저 확인한다.

```bash
nohup sh -c '
  ./backup.sh
  printf "%s\n" "$?" > backup.exit
' >> backup.log 2>&1 < /dev/null &

printf "%s\n" "$!" > backup.pid
```

- `nohup`: hangup 신호를 무시하도록 실행한다.
- `>> backup.log`: 표준 출력을 로그에 추가한다.
- `2>&1`: 표준 오류를 현재 표준 출력과 같은 곳으로 보낸다.
- `< /dev/null`: 터미널 표준 입력에 기대지 않게 한다.
- `$!`: 방금 시작한 background wrapper의 PID다.
- `backup.exit`: `backup.sh`가 정상적으로 끝났다면 종료 상태가 기록된다. `0`은 일반적으로 성공이다.

### 로그 redirection 구분

```bash
# 표준 오류만 누적
./command 2>> error.log

# 표준 출력과 표준 오류를 한 파일에 누적
./command >> all.log 2>&1
```

`2>&1`은 “현재 1번 출력이 가는 곳으로 2번 오류도 보낸다”는 뜻이라 순서가 중요하다.

## 확인 순서

```bash
ps -p "$(cat backup.pid)" -o pid,stat,etime,cmd
tail -n 100 backup.log
cat backup.exit
```

- PID가 보이면 wrapper가 아직 실행 중인지 확인한다.
- PID가 없고 `backup.exit`가 `0`이면 정상 종료 후보이며, 실제 백업 산출물도 확인한다.
- PID와 `backup.exit`가 모두 없으면 비정상 종료나 기록 실패 가능성을 로그에서 찾는다.
- prompt가 돌아왔다는 사실은 성공 증거가 아니다.

중복 실행이 손상을 일으킬 수 있다면 ad-hoc 실행을 반복하지 말고 lock 또는 systemd의 단일 unit으로 통제한다.

## Bash 시작 파일 오판 방지

- interactive login Bash는 `/etc/profile`을 읽고, `~/.bash_profile`, `~/.bash_login`, `~/.profile` 중 처음 존재하고 읽을 수 있는 하나를 읽는다.
- interactive non-login Bash는 `~/.bashrc`를 읽는다.
- profile이 `.bashrc`를 직접 source할 수 있으므로 실제 실행 흐름은 파일 내용과 호출 방식까지 확인한다.
- 따라서 `/etc/profile`, `/etc/bash.bashrc`, `~/.profile`, `~/.bashrc`가 항상 고정 순서로 모두 실행된다고 단정하지 않는다.

## 오판하기 쉬운 지점

- 오해: background process는 소유자가 달라진다.
  - 정확한 설명: 실행 사용자는 그대로다. 달라지는 것은 shell의 대기 방식이며 세션·신호·입출력 관계는 별도로 처리한다.
- 오해: `nohup`만 쓰면 자동 background가 된다.
  - 정확한 설명: GNU `nohup`은 자동으로 background로 보내지 않으므로 필요하면 `&`를 별도로 붙인다.
- 오해: 로그 파일이 있으면 작업 성공이 증명된다.
  - 정확한 설명: 종료 상태와 실제 산출물까지 확인해야 한다.

## 공식 근거

- [GNU Bash - Signals](https://www.gnu.org/software/bash/manual/html_node/Signals)
- [GNU Bash - Job Control](https://www.gnu.org/software/bash/manual/html_node/Job-Control.html)
- [GNU Bash - Startup Files](https://www.gnu.org/software/bash/manual/html_node/Bash-Startup-Files)
- [GNU Coreutils - nohup](https://www.gnu.org/software/coreutils/manual/html_node/nohup-invocation.html)

## 관련 노트

- [[10_학습 노트/리눅스(우분투)/우분투#기초|우분투 legacy - 기초]]
- [[10_학습 노트/리눅스(우분투)/00_리눅스_목차|리눅스 목차]]
