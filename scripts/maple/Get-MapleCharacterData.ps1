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

Data based on NEXON Open API.
https://openapi.nexon.com/ko/game/maplestory/
#>

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
    [int]$MaxRetries = 5
)

$ErrorActionPreference = "Stop"
$BaseUrl = "https://open.api.nexon.com/maplestory/v1"
$ScriptDir = Split-Path -Parent $PSCommandPath
$script:LastRequestAt = [DateTimeOffset]::MinValue

if ([string]::IsNullOrWhiteSpace($OutputPath)) {
    $OutputDir = Join-Path $ScriptDir "output"
    New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null
    $OutputPath = Join-Path $OutputDir "$CharacterName-maple-api.json"
}
else {
    $OutputPath = [IO.Path]::GetFullPath($OutputPath)
    $ParentDir = Split-Path -Parent $OutputPath
    if ($ParentDir) {
        New-Item -ItemType Directory -Path $ParentDir -Force | Out-Null
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
            return Invoke-RestMethod -Method Get -Uri $Uri -Headers $script:Headers
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
            Write-Warning "429 Too Many Requests - $DelaySeconds초 후 재시도 ($($Attempt + 1)/$MaxRetries)"
            Start-Sleep -Seconds $DelaySeconds
        }
    }
}

$SecureKey = Read-Host "NEXON Open API Key 입력" -AsSecureString
$ApiKey = ConvertFrom-SecureStringPlainText -SecureString $SecureKey
$Headers = @{
    "x-nxopen-api-key" = $ApiKey
}

try {
    Write-Host "[$CharacterName] OCID 조회 중..."
    $IdResult = Invoke-NexonApi -Path "id" -Query @{ character_name = $CharacterName }
    $Ocid = $IdResult.ocid

    if ([string]::IsNullOrWhiteSpace($Ocid)) {
        throw "OCID를 얻지 못했습니다. 캐릭터명과 API Key를 확인하세요."
    }

    Write-Host "OCID 확인 완료."

    $Endpoints = [ordered]@{
        basic            = "character/basic"
        stat             = "character/stat"
        hyper_stat       = "character/hyper-stat"
        ability          = "character/ability"
        item_equipment   = "character/item-equipment"
        symbol_equipment = "character/symbol-equipment"
        set_effect       = "character/set-effect"
        pet_equipment    = "character/pet-equipment"
        link_skill       = "character/link-skill"
        vmatrix          = "character/vmatrix"
        hexamatrix       = "character/hexamatrix"
        hexamatrix_stat  = "character/hexamatrix-stat"
        dojang           = "character/dojang"
        other_stat       = "character/other-stat"
        ring_exchange    = "character/ring-exchange-skill-equipment"
        ring_reserve     = "character/ring-reserve-skill-equipment"
        union            = "user/union"
        union_raider     = "user/union-raider"
        union_artifact   = "user/union-artifact"
        union_champion   = "user/union-champion"
    }

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
            $Data[$Name] = [ordered]@{
                error   = $true
                message = $_.Exception.Message
            }
            Write-Warning "$Name 조회 실패 - 계속 진행합니다."
        }
    }

    $Data |
        ConvertTo-Json -Depth 100 |
        Set-Content -Path $OutputPath -Encoding utf8

    Write-Host ""
    Write-Host "완료:"
    Write-Host $OutputPath
}
finally {
    $ApiKey = $null
    $Headers = $null
    $SecureKey = $null
}
