---
type: control
status: active
created: 2026-09-18
scope: Maple Bridge 수집 및 Phase 1 도구
---

# 현재 구조

소스와 저장된 출력물을 직접 읽어 확인한 구조다. 기존 collector/snapshot 코드는 변경하지 않았다.

| 역할 | 구현 |
|---|---|
| 실행 진입점 | `Run-MapleCharacterData.cmd`: PowerShell 7 collector → snapshot |
| NEXON 수집 | `Get-MapleCharacterData.ps1`, `Invoke-NexonApi`: 20개 항목, 간격 제한, 429 재시도, 선택 endpoint 오류 기록 |
| 설정/키 | CLI 인자와 SecureString 입력. 별도 키 파일을 읽거나 기록하지 않음 |
| 정규화/요약 | `Build-MapleSnapshot.ps1`, `New-Summary` |
| raw/latest | `Build-MapleSnapshot.ps1`: 입력 원문 복사 |
| diff | `New-Diff`: 지정된 요약 항목/장비 slot/심볼·HEXA 이름 비교 |
| 출력 | `output/우노03-maple-api.json`, `latest.json`, `summary.json`, `diff.json`, `raw/` |

기존 diff는 임의 JSON contract 전체 비교용이 아니다. Phase 1에서는 DeepDiff를 별도 사용한다.

## Phase 1 추가 구성

- `tools/maple_phase1.py`: doctor/probe/snapshot/context-template/capture/storage/replay/diff CLI.
- `tools/phase1_core.py`: 필터링·원본 hash·스냅샷 고정·DeepDiff·HTTPX replay.
- `tools/phase1_cdp.py`: 요청/hop/ExtraInfo 연결, body 획득, fixture 저장.
- `tools/Start-ScouterCaptureBrowser.ps1`: 별도 Brave 프로필과 loopback 포트.
- `tools/Collect-Phase1Snapshot.ps1`: 기존 수집/후처리를 재사용하고 해당 결과를 고정.
- `requirements-phase1.lock.txt`: 설치 및 검증한 직접/간접 의존성 고정.
- `tests/`: 합성 이벤트 단위 테스트 및 실제 CDP/로컬 HTTP 스모크 테스트.

## 구현 경계

`actual`을 덮어쓰는 변환기는 아직 없다. 향후 계산용 상태에만 NEXON base → 검증된 Scouter preset → manual override를 적용한다. 요청 의미와 endpoint는 실제 캡처로 확인하며 제3자 예제를 사실로 하드코딩하지 않는다.

원본 키/인증정보·브라우저 프로필은 Git 산출물이 아니다. 공개 API 서버·MCP·MapleScouter 공식 재구현은 미구현이다.
