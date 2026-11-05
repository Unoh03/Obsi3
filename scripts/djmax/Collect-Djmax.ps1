#requires -Version 7.5
[CmdletBinding()]
param(
    [string]$Nickname = 'Unoh03',
    [ValidateSet(4,5,6,8)][int]$Button = 4,
    [string]$OutputRoot = (Join-Path $PSScriptRoot 'output'),
    [string]$FixturePath
)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

function Read-Json([string]$Path) {
    Get-Content -LiteralPath $Path -Raw -Encoding utf8 |
        ConvertFrom-Json -AsHashtable -DateKind String -Depth 100
}
function Write-Json($Data, [string]$Path) {
    $Text = ConvertTo-Json -InputObject $Data -Depth 100 -WarningAction Stop
    [IO.File]::WriteAllText($Path, $Text + [Environment]::NewLine,
        [Text.UTF8Encoding]::new($false))
}
function Get-Api([string]$Url, [bool]$Required) {
    for ($Try = 1; $Try -le 3; $Try++) {
        try {
            $Response = Invoke-RestMethod -Method Get -Uri $Url -TimeoutSec 30 -ErrorAction Stop
            $Value = ConvertTo-Json -InputObject $Response -Depth 100 |
                ConvertFrom-Json -AsHashtable -DateKind String -Depth 100
            if ($Value.success -ne $true) { throw "API success=false: $Url" }
            return $Value
        } catch {
            if ($Try -lt 3) { Start-Sleep -Seconds $Try; continue }
            if ($Required) { throw }
            Write-Warning "Optional endpoint unavailable: $Url"
            return $null
        }
    }
}
function Key-Of($Record) { '{0}:{1}' -f $Record.title, $Record.pattern }

$SafeName = [uri]::EscapeDataString($Nickname)
$Url = "https://v-archive.net/api/v2/archive/$SafeName"
$CollectedAt = [DateTimeOffset]::UtcNow.ToString('o')
if ($FixturePath) {
    $Fixture = Read-Json $FixturePath
    $RecordsResponse = $Fixture.records_response
    $TierResponse = $Fixture.tier_response
    $ClassResponse = $Fixture.djclass_response
} else {
    # Sequential calls: V-ARCHIVE has request limits.
    $RecordsResponse = Get-Api "$Url/button/$Button" $true
    $TierResponse = Get-Api "$Url/tier/$Button" $false
    $ClassResponse = Get-Api "$Url/djClass/$Button" $false
}
if ($null -eq $RecordsResponse -or $RecordsResponse.success -ne $true -or
    $RecordsResponse.nickname -cne $Nickname -or [int]$RecordsResponse.button -ne $Button -or
    $RecordsResponse.records -isnot [System.Collections.IList] -or
    [int]$RecordsResponse.count -ne $RecordsResponse.records.Count) {
    throw 'Invalid or partial V-ARCHIVE response; previous state preserved.'
}
$Seen = [System.Collections.Generic.HashSet[string]]::new()
foreach ($R in $RecordsResponse.records) {
    if ($R -isnot [System.Collections.IDictionary] -or $null -eq $R.title -or
        $R.pattern -cnotin @('NM','HD','MX','SC') -or
        $null -eq $R.level -or $null -eq $R.score -or $R.maxCombo -isnot [bool] -or
        [double]$R.score -lt 0 -or [double]$R.score -gt 100 -or
        -not $Seen.Add((Key-Of $R))) {
        throw 'Record identity/field validation failed; previous state preserved.'
    }
}
$Records = @($RecordsResponse.records)
$ByPattern = [ordered]@{}
foreach ($Pattern in @('NM','HD','MX','SC')) {
    $Selected = @($Records | Where-Object { $_.pattern -ceq $Pattern })
    $ByPattern[$Pattern] = [ordered]@{
        registered = $Selected.Count
        max_level_registered = if ($Selected.Count) {
            ($Selected | Measure-Object -Property level -Maximum).Maximum
        } else { $null }
        max_combos = @($Selected | Where-Object { $_.maxCombo }).Count
    }
}
$ByLevel = [ordered]@{}
foreach ($Group in @($Records | Group-Object -Property level | Sort-Object { [int]$_.Name })) {
    $ByLevel[$Group.Name] = [ordered]@{
        registered = $Group.Count
        average_score = [math]::Round([double](($Group.Group | Measure-Object score -Average).Average),2)
    }
}
$TierName = $null; $TierPoint = $null; $DjClass = $null
if ($null -ne $TierResponse -and $TierResponse.success -eq $true) {
    if ($TierResponse.tier -is [System.Collections.IDictionary]) {
        $TierName = $TierResponse.tier.name
    }
    $TierPoint = $TierResponse.tierPoint
}
if ($null -ne $ClassResponse -and $ClassResponse.success -eq $true) {
    $DjClass = $ClassResponse.djClass
}
$Summary = [ordered]@{
    nickname = $Nickname; button = $Button; user_no = $RecordsResponse.userNo
    collected_at = $CollectedAt; registered_patterns = $Records.Count
    max_combos = @($Records | Where-Object { $_.maxCombo }).Count
    perfect_scores = @($Records | Where-Object { [double]$_.score -eq 100 }).Count
    average_registered_score = if ($Records.Count) {
        [math]::Round([double](($Records | Measure-Object score -Average).Average),2)
    } else { $null }
    by_pattern = $ByPattern; by_level = $ByLevel
    tier_name = $TierName; tier_point = $TierPoint; dj_class = $DjClass
}
$Latest = [ordered]@{
    metadata = [ordered]@{
        schema_version = 1; nickname = $Nickname; button = $Button
        collected_at = $CollectedAt; source = 'V-ARCHIVE (fan-made) OPEN API'
        source_url = "$Url/button/$Button"
    }
    records_response = $RecordsResponse
    tier_response = $TierResponse
    djclass_response = $ClassResponse
}
$OutputRoot = [IO.Path]::GetFullPath($OutputRoot)
[void](New-Item -ItemType Directory -Path $OutputRoot -Force)
$PointerPath = Join-Path $OutputRoot 'current.json'
$Old = $null; $OldSummary = $null
if (Test-Path -LiteralPath $PointerPath) {
    $Pointer = Read-Json $PointerPath
    if ($Pointer.schema_version -ne 1 -or $Pointer.nickname -cne $Nickname -or
        [int]$Pointer.button -ne $Button -or
        [string]$Pointer.snapshot -notmatch '^snapshots/[a-zA-Z0-9-]+/latest\.json$') {
        throw 'Existing current.json does not match identity or expected layout.'
    }
    $OldFile = Join-Path $OutputRoot $Pointer.snapshot
    $Old = Read-Json $OldFile
    $OldSummary = Read-Json (Join-Path (Split-Path -Parent $OldFile) 'summary.json')
}
$OldIndex = @{}; $NewIndex = @{}
if ($null -ne $Old) {
    foreach ($R in $Old.records_response.records) { $OldIndex[(Key-Of $R)] = $R }
}
$NewCharts = [System.Collections.Generic.List[object]]::new()
$Improvements = [System.Collections.Generic.List[object]]::new()
$Regressions = [System.Collections.Generic.List[object]]::new()
$NewCombos = [System.Collections.Generic.List[object]]::new()
foreach ($R in $Records) {
    $Key = Key-Of $R
    $NewIndex[$Key] = $R
    if (-not $OldIndex.ContainsKey($Key)) {
        if ($null -ne $Old) {
            $NewCharts.Add([ordered]@{
                key=$Key; name=$R.name; pattern=$R.pattern; level=$R.level
                score=$R.score; max_combo=$R.maxCombo
            })
            if ($R.maxCombo) {
                $NewCombos.Add([ordered]@{
                    key=$Key; name=$R.name; pattern=$R.pattern; level=$R.level
                })
            }
        }
        continue
    }
    $Prior = $OldIndex[$Key]
    $Delta = [math]::Round(([decimal]$R.score - [decimal]$Prior.score),2)
    if ($Delta -gt 0) {
        $Improvements.Add([ordered]@{
            key=$Key; name=$R.name; pattern=$R.pattern; level=$R.level
            before=$Prior.score; after=$R.score; delta_percentage_points=$Delta
            api_updated_at=$R.updatedAt
        })
    } elseif ($Delta -lt 0) {
        $Regressions.Add([ordered]@{
            key=$Key; name=$R.name; pattern=$R.pattern; level=$R.level
            before=$Prior.score; after=$R.score; delta_percentage_points=$Delta
        })
    }
    if (-not $Prior.maxCombo -and $R.maxCombo) {
        $NewCombos.Add([ordered]@{key=$Key; name=$R.name; pattern=$R.pattern; level=$R.level})
    }
}
$TierChange = $null
if ($null -ne $OldSummary -and $null -ne $OldSummary.tier_name -and
    $null -ne $TierName -and $OldSummary.tier_name -cne $TierName) {
    $TierChange = [ordered]@{ before=$OldSummary.tier_name; after=$TierName }
}
$Diff = [ordered]@{
    baseline = ($null -eq $Old)
    new_records = @($NewCharts.ToArray())
    score_improvements = @($Improvements.ToArray())
    score_decreases_or_corrections = @($Regressions.ToArray())
    newly_max_combo = @($NewCombos.ToArray())
    absent_from_current_api = @($OldIndex.Keys | Where-Object { -not $NewIndex.ContainsKey($_) } | Sort-Object)
    tier_change = $TierChange
}
$Quality = [ordered]@{
    records='ok'
    tier=if ($null -eq $TierResponse) {'unavailable'} else {'ok'}
    dj_class=if ($null -eq $ClassResponse) {'unavailable'} else {'ok'}
    notes=@(
        'Only records uploaded to V-ARCHIVE are observable.'
        'First run is a baseline, not newly played charts.'
        'updatedAt is an API record timestamp, not proven game play time.'
        'A missing or lower score could reflect a correction rather than lost ability.'
    )
}
$Context = [ordered]@{
    schema_version=1; metadata=$Latest.metadata; quality=$Quality
    current=$Summary; changes_since_previous=$Diff
    records=@($Records | Sort-Object { [int]$_.title }, pattern)
}
$Kst = [TimeZoneInfo]::ConvertTimeBySystemTimeZoneId([DateTimeOffset]::UtcNow,'Korea Standard Time')
$Stamp = $Kst.ToString('yyyyMMdd-HHmmss')
$Id = [guid]::NewGuid().ToString('N').Substring(0,8)
$Name = "$Stamp-$Id"
$Stage = Join-Path $OutputRoot ('.staging-' + $Name)
$Snapshot = Join-Path (Join-Path $OutputRoot 'snapshots') $Name
$Exports = Join-Path $OutputRoot 'exports'
foreach ($Dir in @($Stage, (Split-Path -Parent $Snapshot), $Exports)) {
    [void](New-Item -ItemType Directory -Force -Path $Dir)
}
try {
    Write-Json $Latest (Join-Path $Stage 'latest.json')
    Write-Json $Summary (Join-Path $Stage 'summary.json')
    Write-Json $Diff (Join-Path $Stage 'diff.json')
    Write-Json $Context (Join-Path $Stage 'ai-context.json')
    Move-Item -LiteralPath $Stage -Destination $Snapshot -ErrorAction Stop
    $ExportFile = Join-Path $Exports ('ai-context-{0}-{1}B-{2}.json' -f $Nickname,$Button,$Name)
    Copy-Item -LiteralPath (Join-Path $Snapshot 'ai-context.json') -Destination $ExportFile
    $Pointer = [ordered]@{
        schema_version=1; nickname=$Nickname; button=$Button; collected_at=$CollectedAt
        snapshot="snapshots/$Name/latest.json"
        ai_context="snapshots/$Name/ai-context.json"
        export="exports/$(Split-Path -Leaf $ExportFile)"
    }
    $TempPointer = Join-Path $OutputRoot ('current-' + $Id + '.tmp')
    Write-Json $Pointer $TempPointer
    [IO.File]::Move($TempPointer,$PointerPath,$true)
} finally {
    if (Test-Path -LiteralPath $Stage) { Remove-Item -LiteralPath $Stage -Recurse -Force }
}
Write-Host ('DJMAX {0}B: {1} records, {2} MAX COMBO' -f $Button,$Summary.registered_patterns,$Summary.max_combos)
Write-Host ('New: {0}; improved: {1}; new MAX COMBO: {2}' -f $Diff.new_records.Count,$Diff.score_improvements.Count,$Diff.newly_max_combo.Count)
Write-Host "AI attachment: $ExportFile"
