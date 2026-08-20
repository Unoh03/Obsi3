# 8.19 멘토 노트 Audit Pack

이 디렉터리는 `[[../8.19 멘토님과 상담 - 감사 정본]]`의 기계 검증 파일을 보관한다.

## 구성

| 파일 | 역할 |
|---|---|
| `8.19 멘토 노트 - 승인 교정 원장 C01-C16.md` | 승인된 교정의 사람이 읽는 원장 |
| `8.19-mentor-note-provenance.json` | Source·Blob Pin·교정 Anchor의 기계 판독 Manifest |
| `verify_mentor_note_provenance.py` | 주 검증기. Python 문법 검사와 Block Parser Smoke Test 완료 |
| `Test-MentorNoteProvenance.ps1` | PowerShell 7용 동등 검증기 |
| `8.19 멘토 노트 - 검증 보고서.md` | 보장 범위와 현재 확인 결과 |
| `generated/` | 검증 실행 시 생성되는 Block Manifest와 결과 JSON |

## 권장 실행

Repository Root에서:

```powershell
python "20_팀 프로젝트/3차 프로젝트/audit/verify_mentor_note_provenance.py" --write-generated
```

PowerShell 구현을 사용할 경우:

```powershell
pwsh -File "20_팀 프로젝트/3차 프로젝트/audit/Test-MentorNoteProvenance.ps1" -WriteGenerated
```

기대 결과:

```text
passed: true
failures: []
```

## 검증 의미

- 원본 Source Commit의 Git Blob이 예상값과 같은지 확인
- 현재 SUPERSEDED 보존본이 같은 Git Blob인지 확인
- 두 Blob의 SHA-256이 같은지 확인
- 네 개 파생 View가 검토 시점 Blob에서 Drift하지 않았는지 확인
- C01~C16이 누락·중복 없이 존재하는지 확인
- 각 교정의 필수 Anchor가 대상 문서에 있는지 확인
- 원본 Markdown을 Block ID·Line Range·SHA-256으로 전수 분해
- 각 원문 Block이 파생 View에 그대로 존재하는 경우 `verbatim_in`으로 기록

`verbatim_in`이 비어 있다고 원문이 유실된 것은 아니다. 전체 원문은 불변 Source 파일에 보존된다. 해당 값은 파생 View에서 **그대로 복사된 Block만** 식별하며, 자유 요약·재서술을 동일 문장으로 오인하지 않기 위한 보수적 분류다.
