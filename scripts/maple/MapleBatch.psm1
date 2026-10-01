#requires -Version 7.5
Import-Module (Join-Path $PSScriptRoot 'MapleSnapshot.psm1')

function Initialize-MapleCharacterHistory([string]$Root, [string]$Character, [string]$Directory, [string]$PresetRolesPath) {
    $Legacy = Get-MaplePublishedSet $Root
    $Candidates = [System.Collections.Generic.List[object]]::new()
    foreach ($RawDir in @((Join-Path $Root 'raw'), (Join-Path $Directory 'raw'))) {
        if (-not (Test-Path -LiteralPath $RawDir)) { continue }
        foreach ($File in Get-ChildItem -LiteralPath $RawDir -File -Filter '*.json') {
            try {
                $Data = Read-MapleJson $File.FullName
                if ($Data.metadata.character_name -cne $Character) { continue }
                $Time = [DateTimeOffset]::Parse([string]$Data.metadata.collected_at)
            }
            catch { Write-Warning "이력 읽기 실패, 원본 보존: $($File.FullName)"; continue }
            $Candidates.Add(@{path=$File.FullName;time=$Time;hash=(Get-FileHash -LiteralPath $File.FullName).Hash})
        }
    }
    $LegacySource = $null
    if ($Legacy) {
        $Source = Join-Path $Legacy.directory 'latest.json'
        $Data = Read-MapleJson $Source
        if ($Data.metadata.character_name -ceq $Character) {
            $LegacySource = $Source
            $Candidates.Add(@{path=$Source;time=[DateTimeOffset]$Data.metadata.collected_at;hash=(Get-FileHash -LiteralPath $Source).Hash})
        }
    }
    # Validate all timestamps before copying anything; prefix similarity is irrelevant.
    $Seen = @{}
    foreach ($Candidate in $Candidates) {
        $TimeKey = $Candidate.time.UtcTicks.ToString()
        if ($Seen.ContainsKey($TimeKey) -and $Seen[$TimeKey] -cne $Candidate.hash) {
            throw "같은 수집 시각에 다른 원본이 있습니다: $Character / $($Candidate.time)"
        }
        $Seen[$TimeKey] = $Candidate.hash
    }
    $RawDir = Join-Path $Directory 'raw'
    New-Item -ItemType Directory -Path $RawDir -Force | Out-Null
    foreach ($Candidate in $Candidates) {
        $Hash = $Candidate.hash.ToLowerInvariant()
        $Name = "$Character-$($Candidate.time.ToString('yyyy-MM-dd-HHmmss-fffffff'))-$($Hash.Substring(0,12)).json"
        $Target = Join-Path $RawDir $Name
        if (-not (Test-Path -LiteralPath $Target)) { [IO.File]::Copy($Candidate.path, $Target, $false) }
        if ((Get-FileHash -LiteralPath $Target).Hash -cne $Candidate.hash) { throw "이력 복사 hash 불일치: $Target" }
    }
    if ($LegacySource -and -not (Test-Path -LiteralPath (Join-Path $Directory 'current.json'))) {
        & (Join-Path $PSScriptRoot 'Build-MapleSnapshot.ps1') -SourcePath $LegacySource -OutputDirectory $Directory -PresetRolesPath $PresetRolesPath -SkipExport -Quiet
        Write-Host "[$Character] 기존 정상 결과 복구 완료 (이번 API 수집 결과 아님)."
    }
    # Reject corrupt destination bundles before starting a new collection.
    $null = Get-MaplePublishedSet $Directory
}

function Invoke-MapleCharacterBatch {
    [CmdletBinding()]
    param(
        [string]$OutputRoot = (Join-Path $PSScriptRoot 'output'),
        [string]$PresetRolesPath = (Join-Path $PSScriptRoot 'preset-roles.json'),
        [ValidateRange(200,5000)][int]$RequestIntervalMs = 250,
        [ValidateRange(0,10)][int]$MaxRetries = 5,
        [ValidateRange(5,300)][int]$TimeoutSeconds = 30
    )
    $ErrorActionPreference = 'Stop'
    $OutputRoot = [IO.Path]::GetFullPath($OutputRoot)
    New-Item -ItemType Directory -Path $OutputRoot -Force | Out-Null
    $Lock = $null; $Key = $null
    $Results = [System.Collections.Generic.List[object]]::new()
    $Started = [DateTimeOffset]::Now.ToString('o')
    try {
        try { $Lock = [IO.File]::Open((Join-Path $OutputRoot '.batch.lock'), 'OpenOrCreate', 'ReadWrite', 'None') }
        catch { throw '다른 일괄 수집이 실행 중이거나 실행 잠금에 접근할 수 없습니다.' }
        $Key = Read-Host 'NEXON Open API Key 입력 (두 캐릭터 공통)' -AsSecureString
        $Index = 0
        foreach ($Character in @('우노03', '우노03레테')) {
            if ($Index++ -gt 0) { Start-Sleep -Milliseconds $RequestIntervalMs }
            $Result = [ordered]@{character=$Character;status='실패';collected_at=$null;attachment=$null;partial=$false;error=$null}
            $Stage = '준비'
            try {
                $Directory = Join-Path $OutputRoot "characters/$Character"
                Initialize-MapleCharacterHistory $OutputRoot $Character $Directory $PresetRolesPath
                $Source = Join-Path $Directory "$Character-maple-api.json"
                $Stage = '수집'
                & (Join-Path $PSScriptRoot 'Get-MapleCharacterData.ps1') -CharacterName $Character -OutputPath $Source -ApiKeySecure $Key -NoPause -RequestIntervalMs $RequestIntervalMs -MaxRetries $MaxRetries -TimeoutSeconds $TimeoutSeconds
                $Data = Read-MapleJson $Source
                if ($Data.metadata.character_name -cne $Character) { throw '수집 캐릭터 불일치' }
                $Result.collected_at = $Data.metadata.collected_at
                $Stage = '후처리'
                & (Join-Path $PSScriptRoot 'Build-MapleSnapshot.ps1') -SourcePath $Source -OutputDirectory $Directory -PresetRolesPath $PresetRolesPath -SkipExport -Quiet
                $Published = Get-MaplePublishedSet $Directory
                $Context = Read-MapleJson (Join-Path $Published.directory 'ai-context.json')
                if ($Context.metadata.raw_sha256 -cne (Get-FileHash -LiteralPath $Source).Hash.ToLowerInvariant()) { throw '이번 수집본과 완료 결과가 다릅니다.' }
                $Result.partial = @($Context.quality.section_status.Values | Where-Object { $_ -ne 'ok' }).Count -gt 0
                $Stage = '전달본'
                $Export = Export-MapleAIContext $Directory (Join-Path $OutputRoot 'exports')
                $Result.attachment = $Export.path
                $Result.status = if ($Result.partial) { '부분 성공' } else { '성공' }
            }
            catch {
                if ($Stage -eq '전달본') { $Result.status = '전달본 생성 실패' }
                $Result.error = "$Stage`: $($_.Exception.Message)"
                Write-Warning "[$Character] $($Result.error)"
            }
            $Results.Add($Result)
        }
        $Report = [ordered]@{
            started_at=$Started;finished_at=[DateTimeOffset]::Now.ToString('o')
            exit_code= [int](@($Results | Where-Object { $_.status -ne '성공' }).Count -gt 0)
            characters=@($Results.ToArray())
        }
        Write-MapleJson $Report (Join-Path $OutputRoot 'last-batch.json')
        Write-Host "`n이번 실행 결과"
        foreach ($Result in $Results) {
            Write-Host "$($Result.character): $($Result.status) / 수집 시각: $($Result.collected_at)"
            if ($Result.attachment) { Write-Host "  GPT에 첨부: $($Result.attachment)" }
            else { Write-Host '  이번에 전달할 파일 없음. 기존 파일은 새 수집본이 아닙니다.' }
        }
        return $Report
    }
    finally {
        if ($Key) { $Key.Dispose() }
        if ($Lock) { $Lock.Dispose() }
    }
}

Export-ModuleMember -Function Invoke-MapleCharacterBatch,Initialize-MapleCharacterHistory
