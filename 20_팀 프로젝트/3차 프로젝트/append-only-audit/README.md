# 현재 정리 문서 Append-only 보존 계약

## 목적

이 계약의 보존 대상은 분리 전 원본만이 아니라 **2026-08-20 현재 `master`에 정리되어 있는 문서들의 본문 전체**다.

기준은 엄격하다.

```text
허용
- 기존 파일의 맨 끝에 새 내용을 추가
- 새 파일 생성

금지
- 기존 문자·문장·문단 수정
- 요약·축약·재서술
- 삭제·치환·이동·재배열
- 제목·Frontmatter·표·코드 블록 수정
- 공백·들여쓰기·줄바꿈·인코딩 정규화
- 파일 삭제·이름 변경·경로 이동
```

요약·축약·표현 개선도 모두 기존 내용의 변질로 판정한다. 잘못된 내용이 발견되어도 기존 문장을 고치지 않고, 해당 파일의 끝에 날짜와 근거가 있는 정정 섹션을 추가한다.

## 기준점

```text
Repository: Unoh03/Obsi3
Baseline commit: 839d03a1dc632a74836bf90df4aa07353a8536b9
Baseline branch at capture: master
Policy: exact-prefix append-only
```

`exact-prefix append-only`는 현재 파일의 바이트 전체가 이후 버전의 정확한 접두부로 남아야 한다는 뜻이다.

```text
현재 파일 bytes
=
기준 파일 bytes
+
선택적인 추가 suffix bytes
```

따라서 기존 영역에서 한 바이트라도 달라지거나 빠지거나 위치가 바뀌면 실패한다.

## 보호 파일

- `8.19 멘토님과 상담.md`
- `8.19 멘토님과 상담 - 최신 판정.md`
- `Telemetry와 로그 지연 모델.md`
- `AWS 보안 Telemetry Route 비교.md`
- `멘토 상담 후 보고서·발표 반영.md`
- `8.19 멘토님과 상담 - 원본 기록 (SUPERSEDED).md`

정확한 경로·Git Blob SHA·크기는 `mentor-note-append-only-manifest.json`에 고정한다.

## 검증

```powershell
python "20_팀 프로젝트/3차 프로젝트/append-only-audit/verify_mentor_note_append_only.py"
```

PowerShell wrapper:

```powershell
pwsh -File "20_팀 프로젝트/3차 프로젝트/append-only-audit/Test-MentorNoteAppendOnly.ps1"
```

검증기는 다음을 확인한다.

1. Baseline commit이 현재 HEAD의 조상인지
2. 각 보호 경로가 그대로 존재하는지
3. Baseline commit의 Blob SHA가 Manifest와 같은지
4. 현재 Commit의 파일이 Baseline bytes로 정확히 시작하는지
5. Working tree 파일도 Baseline bytes로 정확히 시작하는지
6. 파일이 짧아지거나, 삭제·이름 변경·경로 이동·공백 변경된 적이 없는지
7. 추가된 내용이 있다면 오직 기존 bytes 뒤의 suffix인지

## CI와 실제 차단

`.github/workflows/mentor-note-append-only.yml`은 Pull Request와 `master` Push에서 검증을 실행한다.

다만 Repository의 `master`가 보호되지 않으면 직접 Push는 **사후 탐지**만 가능하다. 병합 자체를 막으려면 GitHub Branch protection에서 이 Workflow의 `verify` Check를 필수로 지정해야 한다.

## 이전 감사 브랜치

`docs/mentor-note-audit-provenance`는 분리 전 원본을 정본으로 삼은 다른 모델이다. 현재 요구사항의 기준과 맞지 않으므로 병합 대상으로 사용하지 않는다.

현재 요구사항에 맞는 브랜치는:

```text
docs/mentor-note-append-only
```

이다.
