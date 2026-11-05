#requires -Version 7.5
$ErrorActionPreference = 'Stop'
$Collector = Join-Path (Split-Path -Parent $PSScriptRoot) 'Collect-Djmax.ps1'
$Root = Join-Path ([IO.Path]::GetTempPath()) ('djmax-test-' + [guid]::NewGuid().ToString('N'))
$Output = Join-Path $Root 'output'
[void](New-Item -ItemType Directory -Path $Root -Force)
function Assert([bool]$Condition, [string]$Label) {
    if (-not $Condition) { throw "FAIL: $Label" }
    Write-Host "PASS: $Label"
}
function Read-Json([string]$Path) {
    Get-Content -LiteralPath $Path -Raw -Encoding utf8 |
        ConvertFrom-Json -AsHashtable -DateKind String -Depth 100
}
function Publish-Fixture($Data) {
    $Path = Join-Path $Root 'fixture.json'
    $Data | ConvertTo-Json -Depth 30 | Set-Content -LiteralPath $Path -Encoding utf8
    & $Collector -FixturePath $Path -OutputRoot $Output
}
function Current-Files {
    $Pointer = Read-Json (Join-Path $Output 'current.json')
    $Folder = Split-Path -Parent (Join-Path $Output $Pointer.snapshot)
    return @{
        pointer=$Pointer
        diff=(Read-Json (Join-Path $Folder 'diff.json'))
        summary=(Read-Json (Join-Path $Folder 'summary.json'))
        context=(Read-Json (Join-Path $Folder 'ai-context.json'))
    }
}
try {
    $A = @{
        records_response = @{
            success=$true; nickname='Unoh03'; button=4; userNo=123; count=2
            records=@(
                @{ title=10; name='Example A'; pattern='MX'; level=13; score=90.00; maxCombo=$false; updatedAt='2026-11-02T00:00:00Z' },
                @{ title=11; name='Example B'; pattern='HD'; level=10; score=98.00; maxCombo=$true; updatedAt='2026-11-02T00:00:00Z' }
            )
        }
        tier_response = @{success=$true; tierPoint=23; tier=@{name='Iron II'}}
        djclass_response = @{success=$true; djClass='Example Class'}
    }
    Publish-Fixture $A
    $First = Current-Files
    Assert ($First.diff.baseline -eq $true -and $First.diff.new_records.Count -eq 0) 'initial import is baseline'
    Assert ($First.summary.registered_patterns -eq 2 -and $First.summary.max_combos -eq 1) 'summary counts'

    $A.records_response.records[0].score = 94.59
    $A.records_response.records[0].maxCombo = $true
    $A.records_response.records += @{title=12;name='Example C';pattern='SC';level=4;score=83;maxCombo=$false;updatedAt='2026-11-02T01:00:00Z'}
    $A.records_response.count = 3
    $A.tier_response.tier.name = 'Iron I'
    Publish-Fixture $A
    $Second = Current-Files
    Assert ($Second.diff.score_improvements.Count -eq 1 -and
        $Second.diff.score_improvements[0].delta_percentage_points -eq 4.59) 'score diff'
    Assert ($Second.diff.newly_max_combo.Count -eq 1) 'new MAX COMBO'
    Assert ($Second.diff.new_records.Count -eq 1) 'new chart'
    Assert ($Second.diff.tier_change.after -eq 'Iron I') 'tier change'
    Assert ($Second.context.records.Count -eq 3) 'AI export includes current charts'

    Publish-Fixture $A
    $Repeated = Current-Files
    Assert ($Repeated.diff.score_improvements.Count -eq 0 -and
        $Repeated.diff.new_records.Count -eq 0) 'repeat has no fake improvements'

    $Before = (Get-Content -LiteralPath (Join-Path $Output 'current.json') -Raw)
    $A.records_response.count = 999
    $Caught = $false
    try { Publish-Fixture $A } catch { $Caught = $true }
    $After = (Get-Content -LiteralPath (Join-Path $Output 'current.json') -Raw)
    Assert ($Caught -and $Before -ceq $After) 'invalid API response preserves pointer'
    Write-Host 'DJMAX collector offline tests passed.'
} finally {
    if (Test-Path -LiteralPath $Root) { Remove-Item -LiteralPath $Root -Force -Recurse }
}
