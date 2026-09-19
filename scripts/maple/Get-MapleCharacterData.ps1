<#
.SYNOPSIS
Collect MapleStory character data from NEXON Open API and save it as JSON.

.DESCRIPTION
- Defaults to character "우노03".
- Prompts for the NEXON Open API key as a SecureString.
- Does not persist the API key.
- Saves generated JSON under scripts/maple/output/ by default.
- Throttles requests for development-stage NEXON Open API keys.
- Retries HTTP 429 responses with exponential backoff.
- Continues when an optional endpoint fails and records the error in the output.
- Supports an explicit pause-on-exit mode for double-click launchers.

Data based on NEXON Open API.
https://openapi.nexon.com/ko/game/maplestory/
#>

#requires -Version 7.5
[CmdletBinding()]
param(
    [Parameter()]
    [ValidateNotNullOrEmpty()]
    [string]$CharacterName = "우노03",

    [Parameter()]
    [string]$OutputPath,

    [Parameter()]
    [ValidateRange(200, 5000)]
    [int]$RequestIntervalMs = 250,

    [Parameter()]
    [ValidateRange(0, 10)]
    [int]$MaxRetries = 5,

    [Parameter()]
    [ValidateRange(5, 300)]
    [int]$TimeoutSeconds = 30,

    [Parameter()]
    [switch]$NoPause,

    [Parameter()]
    [switch]$PauseOnExit
)

$ErrorActionPreference = "Stop"
$BaseUrl = "https://open.api.nexon.com/maplestory/v1"
$ScriptDir = Split-Path -Parent $PSCommandPath
Import-Module (Join-Path $ScriptDir 'MapleSnapshot.psm1') -Force
$script:LastRequestAt = [DateTimeOffset]::MinValue

if ([string]::IsNullOrWhiteSpace($OutputPath)) {
    $OutputDir = Join-Path $ScriptDir "output"
    New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null
    $SafeCharacter = $CharacterName -replace '[\\/:*?"<>|]', '_'
    $OutputPath = Join-Path $OutputDir "$SafeCharacter-maple-api.json"
}
else {
    $OutputPath = [IO.Path]::GetFullPath($OutputPath)
    $ParentDir = Split-Path -Parent $OutputPath
    if ($ParentDir) {
        New-Item -ItemType Directory -Path $ParentDir -Force | Out-Null
    }
}

function Test-LaunchedFromExplorer {
    try {
        $CurrentProcess = Get-CimInstance Win32_Process -Filter "ProcessId=$PID" -ErrorAction Stop
        $ParentProcess = Get-Process -Id $CurrentProcess.ParentProcessId -ErrorAction Stop
        return $ParentProcess.ProcessName -ieq "explorer"
    }
    catch {
        return $false
    }
}

function ConvertFrom-SecureStringPlainText {
    param(
        [Parameter(Mandatory)]
        [Security.SecureString]$SecureString
    )

    $Ptr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($SecureString)
    try {
        return [Runtime.InteropServices.Marshal]::PtrToStringBSTR($Ptr)
    }
    finally {
        [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($Ptr)
    }
}

function Wait-NexonRequestSlot {
    if ($script:LastRequestAt -eq [DateTimeOffset]::MinValue) {
        return
    }

    $ElapsedMs = ([DateTimeOffset]::UtcNow - $script:LastRequestAt).TotalMilliseconds
    if ($ElapsedMs -lt $RequestIntervalMs) {
        $WaitMs = [Math]::Ceiling($RequestIntervalMs - $ElapsedMs)
        Start-Sleep -Milliseconds $WaitMs
    }
}

function Invoke-NexonApi {
    param(
        [Parameter(Mandatory)]
        [string]$Path,

        [Parameter()]
        [hashtable]$Query = @{}
    )

    $Pairs = foreach ($Key in $Query.Keys) {
        $EncodedKey = [uri]::EscapeDataString([string]$Key)
        $EncodedValue = [uri]::EscapeDataString([string]$Query[$Key])
        "$EncodedKey=$EncodedValue"
    }

    $Uri = "$BaseUrl/$Path"
    if ($Pairs.Count -gt 0) {
        $Uri += "?" + ($Pairs -join "&")
    }

    for ($Attempt = 0; $Attempt -le $MaxRetries; $Attempt++) {
        Wait-NexonRequestSlot
        $script:LastRequestAt = [DateTimeOffset]::UtcNow

        try {
            return Invoke-RestMethod -Method Get -Uri $Uri -Headers $script:Headers -TimeoutSec $TimeoutSeconds
        }
        catch {
            $StatusCode = $null
            if ($null -ne $_.Exception.Response -and $null -ne $_.Exception.Response.StatusCode) {
                $StatusCode = [int]$_.Exception.Response.StatusCode
            }

            if ($StatusCode -ne 429 -or $Attempt -ge $MaxRetries) {
                throw
            }

            $DelaySeconds = [Math]::Min(8, [Math]::Pow(2, $Attempt))
            Write-Warning "429 Too Many Requests - ${DelaySeconds}초 후 재시도 ($($Attempt + 1)/$MaxRetries)"
            Start-Sleep -Seconds $DelaySeconds
        }
    }
}

$ShouldPauseOnExit = $PauseOnExit -or ((-not $NoPause) -and (Test-LaunchedFromExplorer))
$SecureKey = $null
$ApiKey = $null
$Headers = $null

try {
    $SecureKey = Read-Host "NEXON Open API Key 입력" -AsSecureString
    $ApiKey = ConvertFrom-SecureStringPlainText -SecureString $SecureKey
    $Headers = @{
        "x-nxopen-api-key" = $ApiKey
    }

    Write-Host "[$CharacterName] OCID 조회 중..."
    $IdResult = Invoke-NexonApi -Path "id" -Query @{ character_name = $CharacterName }
    $Ocid = $IdResult.ocid

    if ([string]::IsNullOrWhiteSpace($Ocid)) {
        throw "OCID를 얻지 못했습니다. 캐릭터명과 API Key를 확인하세요."
    }

    Write-Host "OCID 확인 완료."

    $Endpoints = Get-MapleEndpoints

    $Data = [ordered]@{
        metadata = [ordered]@{
            character_name = $CharacterName
            collected_at   = (Get-Date).ToString("o")
            source         = "Data based on NEXON Open API"
            source_url     = "https://openapi.nexon.com/ko/game/maplestory/"
            ocid           = $Ocid
        }
    }

    foreach ($Name in $Endpoints.Keys) {
        Write-Host "$Name 조회 중..."

        try {
            $Data[$Name] = Invoke-NexonApi -Path $Endpoints[$Name] -Query @{ ocid = $Ocid }
        }
        catch {
            $Failure = $_
            $StatusCode = $null
            if ($null -ne $Failure.Exception.Response.StatusCode) { $StatusCode = [int]$Failure.Exception.Response.StatusCode }
            $ApiCode = $null
            try {
                $ErrorPayload = $Failure.ErrorDetails.Message | ConvertFrom-Json -ErrorAction Stop
                if ($ErrorPayload.error.name -cmatch '^[A-Z0-9_]+$') { $ApiCode = $ErrorPayload.error.name }
            } catch { }
            $Data[$Name] = [ordered]@{
                error   = $true
                message = $Failure.Exception.Message
                http_status = $StatusCode
                api_error_code = $ApiCode
            }
            Write-Warning "$Name 조회 실패 - 계속 진행합니다."
        }
    }

    $Data.metadata.collection_finished_at = (Get-Date).ToString('o')
    Write-MapleJson $Data $OutputPath

    Write-Host ""
    Write-Host "완료:"
    Write-Host $OutputPath
}
finally {
    $ApiKey = $null
    $Headers = $null
    $SecureKey = $null

    if ($ShouldPauseOnExit) {
        Write-Host ""
        [void](Read-Host "Enter를 누르면 창을 닫습니다")
    }
}
