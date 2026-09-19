#requires -Version 7.5
[CmdletBinding()]
param(
    [string]$SourcePath = (Join-Path $PSScriptRoot 'output/우노03-maple-api.json'),
    [string]$OutputDirectory
)
$ErrorActionPreference = 'Stop'
Import-Module (Join-Path $PSScriptRoot 'MapleSnapshot.psm1') -Force
$SourcePath = (Resolve-Path -LiteralPath $SourcePath -ErrorAction Stop).Path
if (-not $OutputDirectory) { $OutputDirectory = Split-Path -Parent $SourcePath }
$OutputDirectory = [IO.Path]::GetFullPath($OutputDirectory)
$Data = Read-MapleJson $SourcePath
$Character = [string]$Data.metadata.character_name
$Collected = [DateTimeOffset]::MinValue
if (-not $Character -or -not [DateTimeOffset]::TryParse([string]$Data.metadata.collected_at, [ref]$Collected)) {
    throw 'metadata.character_name / collected_at이 유효한 NEXON 원본이 필요합니다.'
}
$Hash = (Get-FileHash -LiteralPath $SourcePath -Algorithm SHA256).Hash.ToLowerInvariant()
$RawDir = Join-Path $OutputDirectory 'raw'
$LatestPath = Join-Path $OutputDirectory 'latest.json'
$Published = Get-MaplePublishedSet $OutputDirectory
if ($Published) { $LatestPath = Join-Path $Published.directory 'latest.json' }
if (Test-Path -LiteralPath $LatestPath) {
    $Latest = Read-MapleJson $LatestPath
    if ($Latest.metadata.character_name -ceq $Character -and
        [DateTimeOffset]$Latest.metadata.collected_at -gt $Collected) {
        throw '더 오래된 수집본입니다. 과거 자료 재가공은 별도 -OutputDirectory를 지정하세요.'
    }
}
New-Item -ItemType Directory -Path $RawDir -Force | Out-Null
$SafeCharacter = $Character -replace '[\\/:*?"<>|]', '_'
$RawPath = $null
$Previous = $null
$PreviousPath = $null
$PreviousTime = [DateTimeOffset]::MinValue
$HistoryWarnings = [System.Collections.Generic.List[string]]::new()
# History is ordered by collection time, not by post-processing time.
foreach ($File in Get-ChildItem -LiteralPath $RawDir -File | Sort-Object Name) {
    if (-not $File.Name.StartsWith("$SafeCharacter-", [StringComparison]::Ordinal) -or $File.Extension -ne '.json') { continue }
    try {
        $Candidate = Read-MapleJson $File.FullName
        if ($Candidate.metadata.character_name -cne $Character) { continue }
        $Time = [DateTimeOffset]::Parse([string]$Candidate.metadata.collected_at)
        $CandidateHash = (Get-FileHash -LiteralPath $File.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
    }
    catch {
        $HistoryWarnings.Add("읽을 수 없는 과거 원본: $($File.Name)")
        continue
    }
    if ($CandidateHash -ceq $Hash) { if (-not $RawPath) { $RawPath = $File.FullName }; continue }
    if ($Time -eq $Collected) { throw "같은 collected_at에 내용이 다른 원본이 있습니다: $($File.Name)" }
    # Failed collections remain in raw, but are not a baseline for the next success.
    if (@(Get-MapleRequiredFailures $Candidate).Count -gt 0) { continue }
    if ($Time -lt $Collected -and $Time -gt $PreviousTime) {
        $Previous = $Candidate
        $PreviousPath = $File.FullName
        $PreviousTime = $Time
    }
}
if (-not $RawPath) {
    $RawPath = Join-Path $RawDir "$SafeCharacter-$($Collected.ToString('yyyy-MM-dd-HHmmss-fffffff'))-$($Hash.Substring(0,12)).json"
    [IO.File]::Copy($SourcePath, $RawPath, $false)
}
if ((Get-FileHash -LiteralPath $RawPath -Algorithm SHA256).Hash.ToLowerInvariant() -cne $Hash) {
    throw '보관 원본의 SHA-256이 입력과 다릅니다.'
}
$RequiredFailures = @(Get-MapleRequiredFailures $Data)
if ($RequiredFailures.Count -gt 0) {
    throw "필수 정보 수집 실패: $($RequiredFailures -join ', '). 원본은 $RawPath 에 보존했습니다. 완료 결과를 갱신하지 않습니다."
}
$Summary = New-MapleSummary $Data
$Summary.metadata.raw_file = [IO.Path]::GetRelativePath($OutputDirectory, $RawPath).Replace('\','/')
$Summary.metadata.raw_sha256 = $Hash
$Before = if ($null -ne $Previous) { New-MapleSummary $Previous } else { $null }
$Diff = New-MapleDiff $Before $Summary
$Diff.metadata = [ordered]@{
    previous_collected_at = if ($Previous) { $Previous.metadata.collected_at } else { $null }
    current_collected_at = $Data.metadata.collected_at
    previous_raw = if ($PreviousPath) { [IO.Path]::GetRelativePath($OutputDirectory, $PreviousPath).Replace('\','/') } else { $null }
    current_raw = $Summary.metadata.raw_file
    current_raw_sha256 = $Hash
}
$Diff.history_warnings = @($HistoryWarnings.ToArray())
$Context = [ordered]@{
    schema_version = $Summary.schema_version
    metadata = $Summary.metadata
    reading_guide = $Summary.reading_guide
    quality = $Summary.quality
    actual = $Summary.actual
    presets = $Summary.presets
    changes_since_previous = $Diff
}
Publish-MapleSnapshot $Summary $Diff $Context $RawPath $OutputDirectory
Write-Host "AI에 전달: $(Join-Path $OutputDirectory 'ai-context.json')"
Write-Host "원본 보관: $RawPath"
Write-Host "변경 $($Diff.change_count)건 / 수집 실패·누락 $($Summary.quality.unavailable_sections.Count)개"
foreach ($Warning in $HistoryWarnings) { Write-Warning $Warning }
