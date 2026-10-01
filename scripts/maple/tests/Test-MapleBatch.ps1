#requires -Version 7.5
$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $PSScriptRoot
Import-Module (Join-Path $Root 'MapleSnapshot.psm1') -Force
Import-Module (Join-Path $Root 'MapleBatch.psm1') -Force
$Parent = [IO.Path]::GetFullPath((Join-Path $Root 'output'))
$Work = Join-Path $Parent "batch-test-$([guid]::NewGuid().ToString('N'))"
New-Item -ItemType Directory -Path $Work -Force | Out-Null
$script:Passed = 0
function Assert($Condition, $Message) { if (-not $Condition) { throw $Message } }
function Test($TestName, [scriptblock]$Body) { & $Body; $script:Passed++; Write-Host "PASS $TestName" }
$global:BatchTest = @{prompts=0;names=[System.Collections.Generic.List[string]]::new();waits=0;failName='';failPath='';requests=0}
function global:Read-Host {
    param($Prompt,[switch]$AsSecureString)
    if (-not $AsSecureString) { throw 'Key input not masked' }
    $global:BatchTest.prompts++
    return (ConvertTo-SecureString 'batch-test-secret' -AsPlainText -Force)
}
function global:Start-Sleep { param($Milliseconds,$Seconds); $global:BatchTest.waits++ }
function global:Invoke-RestMethod {
    param($Method,$Uri,$Headers,$TimeoutSec)
    if ($Headers['x-nxopen-api-key'] -cne 'batch-test-secret') { throw 'Key not reused' }
    $global:BatchTest.requests++
    $Decoded = [uri]::UnescapeDataString($Uri)
    $Character = ($Decoded -split '=')[-1]
    $global:BatchTest.currentCharacter = $Character
    $IsId = $Decoded -match '/id\?'
    if ($IsId) { $global:BatchTest.names.Add($Character) }
    if ($Character -ceq $global:BatchTest.failName -and $Decoded.Contains($global:BatchTest.failPath)) { throw 'Synthetic transport failure' }
    if ($IsId) { return @{ocid=$Character} }
    if ($Decoded -match '/character/stat\?') { return @{date=$null;final_stat=@(@{stat_name='전투력';stat_value='100'})} }
    if ($Decoded -match '/character/hyper-stat\?') { return @{date=$null;use_preset_no=1;hyper_stat_preset_1=@()} }
    if ($Decoded -match '/character/basic\?') { return @{date=$null;character_name=$Character;character_level=276} }
    return @{date=$null}
}
function Run-Batch($Out, $Roles = (Join-Path $Root 'preset-roles.json')) {
    Invoke-MapleCharacterBatch -OutputRoot $Out -PresetRolesPath $Roles -MaxRetries 0
}
function Current($Out,$Name) { Get-MaplePublishedSet (Join-Path $Out "characters/$Name") }
try {
    $Out = Join-Path $Work 'normal'
    Test 'one prompt, sequential characters, isolated exports and no secret persistence' {
        $Report = Run-Batch $Out
        Assert ($Report.exit_code -eq 0 -and $Report.characters.Count -eq 2) 'Batch failed'
        Assert ($global:BatchTest.prompts -eq 1) 'Key prompted more than once'
        Assert (($global:BatchTest.names -join ',') -ceq '우노03,우노03레테') 'Wrong order'
        Assert ($global:BatchTest.requests -eq 40 -and $global:BatchTest.waits -ge 1) 'Request sequence or spacing missing'
        foreach ($Result in $Report.characters) {
            $Set = Current $Out $Result.character
            $Context = Read-MapleJson (Join-Path $Set.directory 'ai-context.json')
            Assert ($Context.metadata.character_name -ceq $Result.character) 'Character mixed'
            Assert ((Get-FileHash $Result.attachment).Hash.ToLowerInvariant() -ceq $Set.manifest.files['ai-context.json']) 'Export byte mismatch'
            Assert ([IO.Path]::GetDirectoryName($Result.attachment) -ceq (Join-Path $Out 'exports')) 'Export not flat'
            Assert ([IO.Path]::GetFileName($Result.attachment).StartsWith("ai-context-$($Result.character)-")) 'Filename not identifiable'
            if ($Result.character -eq '우노03레테') { Assert (-not $Context.Contains('user_context')) 'Roles leaked' }
        }
        $Leak = Get-ChildItem $Out -File -Recurse -Filter '*.json' | Select-String -SimpleMatch 'batch-test-secret'
        Assert (-not $Leak) 'Secret persisted'
    }
    foreach ($Name in @('우노03','우노03레테')) {
        foreach ($FailurePath in @('/id?', '/character/basic?')) {
            Test "$Name $FailurePath failure retains old result and continues the other character" {
                $Old = (Current $Out $Name).directory
                $global:BatchTest.failName=$Name; $global:BatchTest.failPath=$FailurePath
                $Report = Run-Batch $Out
                $Failed = $Report.characters | Where-Object character -CEQ $Name
                $Other = $Report.characters | Where-Object character -CNE $Name
                Assert ($Report.exit_code -eq 1 -and $Failed.status -ceq '실패') 'Failure not reported'
                Assert ($null -eq $Failed.attachment -and $Other.status -ceq '성공') 'Stale attachment or other blocked'
                Assert ((Current $Out $Name).directory -ceq $Old) 'Failure replaced old result'
            }
        }
    }
    foreach ($Name in @('우노03','우노03레테')) {
    Test "$Name optional failure is partial and has a newly verified attachment" {
        $global:BatchTest.failName=$Name; $global:BatchTest.failPath='/ring-reserve-skill-equipment?'
        $Report = Run-Batch $Out
        $Partial = $Report.characters | Where-Object character -CEQ $Name
        Assert ($Report.exit_code -eq 1 -and $Partial.status -ceq '부분 성공') 'Partial hidden'
        Assert (Test-Path -LiteralPath $Partial.attachment) 'Partial attachment absent'
        $global:BatchTest.failName=''; $global:BatchTest.failPath=''
    }
    }
    foreach ($Name in @('우노03','우노03레테')) {
        Test "$Name postprocessing failure does not stop other character" {
            $ConfigPath = Join-Path $Work 'bad-roles.json'
            Write-MapleJson @{schema_version=1;characters=@{$Name=@{recorded_on='2026-10-02';preset_roles=@{unsupported=@{'1'='invalid'}}}}} $ConfigPath
            $Old = (Current $Out $Name).directory
            $Report = Run-Batch $Out $ConfigPath
            Assert (($Report.characters | Where-Object character -CEQ $Name).status -ceq '실패') 'Postprocess error hidden'
            Assert (($Report.characters | Where-Object character -CNE $Name).status -ceq '성공') 'Other character blocked'
            Assert ((Current $Out $Name).directory -ceq $Old) 'Bad postprocess replaced result'
        }
    }
    foreach ($Name in @('우노03','우노03레테')) {
        Test "$Name export failure continues the other character" {
            $global:BatchTest.failExportCharacter=$Name
            function global:New-Item {
                param($ItemType,$Path,[switch]$Force)
                if ((Split-Path $Path -Leaf) -eq 'exports' -and $global:BatchTest.currentCharacter -ceq $global:BatchTest.failExportCharacter) { throw 'Synthetic export filesystem failure' }
                Microsoft.PowerShell.Management\New-Item @PSBoundParameters
            }
            try {
                $Report=Run-Batch $Out
                $Failed=$Report.characters | Where-Object character -CEQ $Name
                Assert ($Failed.status -ceq '전달본 생성 실패' -and $null -eq $Failed.attachment) 'Export failure advertised attachment'
                Assert (($Report.characters | Where-Object character -CNE $Name).status -ceq '성공') 'Other character export stopped'
            }
            finally { Remove-Item Function:\New-Item }
        }
    }
    Test 'export failures keep character bundles but do not advertise old files' {
        $ExportOut = Join-Path $Work 'export-failure'
        New-Item -ItemType Directory -Path $ExportOut | Out-Null
        [IO.File]::WriteAllText((Join-Path $ExportOut 'exports'),'blocking file')
        $Report = Run-Batch $ExportOut
        Assert ($Report.exit_code -eq 1) 'Export error exit code wrong'
        foreach ($Result in $Report.characters) {
            Assert ($Result.status -ceq '전달본 생성 실패' -and $null -eq $Result.attachment) 'Export error misclassified'
            Assert ($null -ne (Current $ExportOut $Result.character)) 'Published result lost'
        }
    }
    Test 'run lock refuses a second batch before prompting for a key' {
        $Count = $global:BatchTest.prompts
        $Lock = [IO.File]::Open((Join-Path $Out '.batch.lock'),'Open','ReadWrite','None')
        $Failed=$false
        try { Run-Batch $Out | Out-Null } catch { $Failed=$true } finally { $Lock.Dispose() }
        Assert ($Failed -and $global:BatchTest.prompts -eq $Count) 'Overlapping run entered'
    }
    Test 'legacy migration exact names, hash preservation, repeat safety and baseline recovery' {
        $LegacyRoot = Join-Path $Work 'legacy'
        $Source = Join-Path $Work 'legacy-source.json'
        $SourceSet = Current $Out '우노03'
        $Data = Read-MapleJson (Join-Path $SourceSet.directory 'latest.json')
        $Data.metadata.collected_at='2026-09-27T16:00:00+09:00'
        Write-MapleJson $Data $Source
        & (Join-Path $Root 'Build-MapleSnapshot.ps1') -SourcePath $Source -OutputDirectory $LegacyRoot -SkipExport -Quiet
        $LegacyHash = (Get-FileHash (Join-Path $LegacyRoot 'current.json')).Hash
        $Other = Read-MapleJson $Source; $Other.metadata.character_name='우노03레테'
        Write-MapleJson $Other (Join-Path $LegacyRoot 'raw/wrong-prefix.json')
        [IO.File]::WriteAllText((Join-Path $LegacyRoot 'raw/broken.json'),'{broken')
        $Destination = Join-Path $LegacyRoot 'characters/우노03'
        $Roles = Join-Path $Root 'preset-roles.json'
        Initialize-MapleCharacterHistory $LegacyRoot '우노03' $Destination $Roles
        Initialize-MapleCharacterHistory $LegacyRoot '우노03' $Destination $Roles
        $Files = @(Get-ChildItem (Join-Path $Destination 'raw') -File)
        Assert ($Files.Count -eq 1 -and (Get-FileHash $Files[0].FullName).Hash -ceq (Get-FileHash $Source).Hash) 'Wrong history migrated or duplicates'
        Assert ($null -ne (Get-MaplePublishedSet $Destination)) 'Previous result not restored'
        Assert (-not (Test-Path (Join-Path $Destination 'exports'))) 'Migration advertised as fresh export'
        Assert ((Get-FileHash (Join-Path $LegacyRoot 'current.json')).Hash -ceq $LegacyHash) 'Legacy mutated'
        $global:BatchTest.failName=''; $global:BatchTest.failPath=''
        $Report = Run-Batch $LegacyRoot
        foreach ($Result in $Report.characters) {
            $Context = Read-MapleJson (Join-Path (Current $LegacyRoot $Result.character).directory 'ai-context.json')
            Assert ($Context.changes_since_previous.metadata.previous_collected_at -ceq '2026-09-27T16:00:00+09:00') 'Lost own historical baseline'
        }
        $Data.basic.character_level=277
        Write-MapleJson $Data (Join-Path $LegacyRoot 'raw/conflict.json')
        $Report = Run-Batch $LegacyRoot
        Assert ($Report.characters[0].status -ceq '실패' -and $Report.characters[1].status -ceq '성공') 'Timestamp conflict did not isolate failure'
    }
    Write-Host "Passed $script:Passed batch tests (offline; mocked NEXON)."
}
finally {
    Remove-Item Function:\Read-Host,Function:\Start-Sleep,Function:\Invoke-RestMethod -ErrorAction SilentlyContinue
    Remove-Variable BatchTest -Scope Global -ErrorAction SilentlyContinue
    $Resolved = [IO.Path]::GetFullPath($Work)
    if (-not $Resolved.StartsWith($Parent + [IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase)) { throw 'Unsafe test cleanup path' }
    Remove-Item -LiteralPath $Resolved -Recurse -Force
}
