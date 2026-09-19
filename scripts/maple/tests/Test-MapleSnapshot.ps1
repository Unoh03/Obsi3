#requires -Version 7.5
$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $PSScriptRoot
Import-Module (Join-Path $Root 'MapleSnapshot.psm1') -Force
$script:Passed = 0
function Assert([bool]$Condition, [string]$Message) { if (-not $Condition) { throw $Message } }
function Test([string]$Name, [scriptblock]$Body) { & $Body; $script:Passed++; Write-Host "PASS $Name" }
function Copy-Data($Value) {
    $Text = ConvertTo-Json -InputObject $Value -Depth 100 -Compress
    return ($Text | ConvertFrom-Json -AsHashtable -Depth 100 -DateKind String)
}
function New-Data {
    $Data = [ordered]@{ metadata = [ordered]@{
        character_name = '테스트'; collected_at = '2026-09-18T10:00:00+09:00'; source = 'synthetic fixture'; source_url = 'test'
    } }
    foreach ($Name in (Get-MapleEndpoints).Keys) { $Data[$Name] = [ordered]@{ date = $null } }
    $Data.basic.character_level = 276
    $Data.basic.character_image = 'https://example.invalid/icon'
    $Data.stat.final_stat = @(
        @{ stat_name = 'INT'; stat_value = '123' },
        @{ stat_name = '전투력'; stat_value = '456' },
        @{ stat_name = '재사용 대기시간 감소 (%)'; stat_value = '0' }
    )
    $Data.item_equipment.item_equipment = @(
        @{ item_equipment_slot = '반지1'; item_name = '리스트레인트 링'; special_ring_level = 3; item_icon = 'image'; item_total_option = @{str='0'; attack_power='10'} },
        @{ item_equipment_slot = '무기'; item_name = '무기'; starforce = '17' }
    )
    $Data.item_equipment.item_equipment_preset_1 = @(@{ item_name = '다른 프리셋' })
    $Data.hyper_stat.use_preset_no = 2
    $Data.hyper_stat.hyper_stat_preset_1 = @(@{ stat_type = 'STR'; stat_level = 1 })
    $Data.hyper_stat.hyper_stat_preset_2 = @(@{ stat_type = 'INT'; stat_level = 7 })
    $Data.hyper_stat.hyper_stat_preset_2_remain_point = 100
    $Data.link_skill.character_link_skill = @(@{ skill_name='링크'; skill_level=2; skill_effect='효과' })
    $Data.hexamatrix_stat.character_hexa_stat_core = @(@{ slot_id='0'; main_stat_level=5 })
    $Data.union_artifact.union_artifact_effect = @(@{ name='보공'; level=5 })
    $Data.vmatrix.character_v_core_equipment = @()
    $Data.other_stat.other_stat = $null
    return $Data
}

Test 'current stats, detailed options and arrays survive; source is untouched' {
    $Data = New-Data
    $Before = ConvertTo-Json -InputObject $Data -Depth 100 -Compress
    $Summary = New-MapleSummary $Data
    Assert ($Summary.actual.stat.values.INT -ceq '123') 'Non-STR stats missing'
    Assert ($Summary.actual.stat.values.'전투력' -is [string]) 'API type changed'
    Assert ($Summary.actual.item_equipment.item_equipment[0].item_total_option.str -ceq '0') 'Zero missing'
    Assert ($Summary.actual.hyper_stat.active_entries.Count -eq 1) 'Active preset missing'
    Assert ($Summary.actual.hyper_stat.active_entries[0].stat_type -ceq 'INT') 'Wrong preset'
    Assert (-not $Summary.actual.item_equipment.Contains('item_equipment_preset_1')) 'Backup preset leaked'
    Assert (-not $Summary.actual.basic.Contains('character_image')) 'Image retained'
    Assert ($Summary.actual.vmatrix.character_v_core_equipment -is [array]) 'Empty array became null'
    Assert ($Summary.actual.link_skill.character_link_skill -is [array]) 'Single-element array collapsed'
    Assert ($Summary.actual.other_stat.Contains('other_stat') -and $null -eq $Summary.actual.other_stat.other_stat) 'Null lost'
    Assert ($Before -ceq (ConvertTo-Json -InputObject $Data -Depth 100 -Compress)) 'Input mutated'
}

Test 'unrecognized hyper preset is preserved instead of guessed' {
    $Data = New-Data; $Data.hyper_stat.use_preset_no = 9
    $Summary = New-MapleSummary $Data
    Assert ($Summary.presets.hyper_stat.Contains('hyper_stat_preset_2')) 'Unresolved presets discarded'
    Assert (-not $Summary.actual.hyper_stat.active_preset_resolved) 'Unresolved active preset not flagged'
    Assert (-not $Summary.actual.hyper_stat.Contains('active_entries')) 'Invented active entries'
}

Test 'null and malformed active hyper data is partial, while empty arrays are valid' {
    $Good = New-Data
    foreach ($BadValue in @(@{v=$null}, @{v='invalid'}, @{v=@{}}, @{v=@($null)}, @{v=@(@{stat_type='INT'})}, @{v=@(@{stat_type='INT';stat_level=-1})})) {
        $Data = Copy-Data $Good
        $Data.hyper_stat.hyper_stat_preset_2 = $BadValue.v
        $Summary = New-MapleSummary $Data
        Assert (-not $Summary.actual.hyper_stat.active_preset_resolved) 'Invalid preset marked resolved'
        Assert (-not $Summary.actual.hyper_stat.Contains('active_entries')) 'Invalid active entries published'
        Assert ($Summary.quality.section_status.hyper_stat -ceq 'partial') 'Partial status missing'
        Assert ($Summary.quality.validation_issues.Contains('hyper_stat')) 'Validation reason missing'
        Assert ($Summary.presets.hyper_stat.Contains('hyper_stat_preset_2')) 'Original preset dropped'
        $Diff = New-MapleDiff (New-MapleSummary $Good) $Summary
        Assert ($Diff.change_count -eq 0) 'Incomplete data became a character change'
        Assert (@($Diff.not_compared | Where-Object section -eq 'hyper_stat').Count -eq 1) 'Incomplete comparison not recorded'
    }
    $Good.hyper_stat.hyper_stat_preset_2 = @()
    $Summary = New-MapleSummary $Good
    Assert ($Summary.actual.hyper_stat.active_preset_resolved -and $Summary.actual.hyper_stat.active_entries -is [array]) 'Empty array rejected'
}

Test 'retired ring endpoint is not expected, but legacy raw remains readable' {
    Assert (-not (Get-MapleEndpoints).Contains('ring_exchange')) 'Retired endpoint still collected'
    $Data = New-Data
    Assert (-not (New-MapleSummary $Data).quality.section_status.Contains('ring_exchange')) 'Retired endpoint counted as missing'
    $Data.ring_exchange = @{date='2026-03-18';ring='legacy'}
    Assert ((New-MapleSummary $Data).actual.ring_exchange.ring -ceq 'legacy') 'Legacy ring data lost'
}

Test 'HEXA, link, artifact and equipment changes are found at leaf fields' {
    $Before = New-Data; $After = Copy-Data $Before
    $After.hexamatrix_stat.character_hexa_stat_core[0].main_stat_level = 6
    $After.link_skill.character_link_skill[0].skill_level = 3
    $After.union_artifact.union_artifact_effect[0].level = 6
    $After.item_equipment.item_equipment[0].special_ring_level = 4
    $Diff = New-MapleDiff (New-MapleSummary $Before) (New-MapleSummary $After)
    Assert ($Diff.change_count -eq 4) "Expected four changes, got $($Diff.change_count)"
    Assert (@($Diff.changes | Where-Object path -Like '*.special_ring_level').Count -eq 1) 'Ring change missing'
}

Test 'failed/missing sections never become item removal or zero' {
    $Before = New-Data; $After = Copy-Data $Before
    $After.item_equipment = @{ error=$true; message='HTTP failure'; http_status=429 }
    $After.Remove('link_skill')
    $Summary = New-MapleSummary $After
    $Diff = New-MapleDiff (New-MapleSummary $Before) $Summary
    Assert ($Diff.change_count -eq 0) 'Failure became a character change'
    Assert ($Diff.not_compared.Count -eq 2) 'Comparison gaps missing'
    Assert ($Summary.quality.section_status.item_equipment -ceq 'error') 'Failure not recorded'
    Assert ($Summary.quality.section_status.link_skill -ceq 'missing') 'Missing not recorded'
    $Reverse = New-MapleDiff $Summary (New-MapleSummary $Before)
    Assert ($Reverse.change_count -eq 0 -and $Reverse.not_compared.Count -eq 2) 'Recovery invented additions'
}

Test 'equipment array reorder is not a change; duplicate IDs are not dropped' {
    $Before = New-Data; $After = Copy-Data $Before
    $After.item_equipment.item_equipment = @($After.item_equipment.item_equipment[1], $After.item_equipment.item_equipment[0])
    $Diff = New-MapleDiff (New-MapleSummary $Before) (New-MapleSummary $After)
    Assert ($Diff.change_count -eq 0) 'Equipment ordering noise'
    $Before.link_skill.character_link_skill = @(@{skill_name='a';skill_level=1},@{skill_name='a';skill_level=2})
    $After = Copy-Data $Before
    $After.link_skill.character_link_skill[1].skill_level = 3
    $Diff = New-MapleDiff (New-MapleSummary $Before) (New-MapleSummary $After)
    Assert ($Diff.change_count -eq 1 -and $Diff.changes[0].before -eq 2) 'Duplicate ID overwritten'
}

Test 'null/missing, bool/number/string and object/array remain distinct' {
    $Before = New-Data; $After = Copy-Data $Before
    $Before.other_stat.sample = [ordered]@{ a=1; b=$false; c=$null; d=@{}; e=@(); f='Case' }
    $After.other_stat.sample = [ordered]@{ a='1'; b=0; d=@(); e=@{}; f='case'; g=$null }
    $Diff = New-MapleDiff (New-MapleSummary $Before) (New-MapleSummary $After)
    Assert ($Diff.change_count -eq 7) "Type/missing distinctions lost: $($Diff.change_count)"
    $Removed = @($Diff.changes | Where-Object path -eq '$.other_stat.sample.c')[0]
    Assert ($Removed.before_exists -and -not $Removed.after_exists -and $null -eq $Removed.before) 'Missing vs null lost'
}

Test 'ordinary array insertion and reordering are compared by index' {
    $Before = New-Data; $After = Copy-Data $Before
    $Before.other_stat.sample = @('a','b','c'); $After.other_stat.sample = @('a','x','b','c')
    $Diff = New-MapleDiff (New-MapleSummary $Before) (New-MapleSummary $After)
    Assert ($Diff.change_count -eq 3) 'Array insertion semantics changed'
    Assert ($Diff.changes[0].path -ceq '$.other_stat.sample[1]') 'Bad array path'
    $After.other_stat.sample = @('b','a','c')
    Assert ((New-MapleDiff (New-MapleSummary $Before) (New-MapleSummary $After)).change_count -eq 2) 'Array order ignored'
}

Test 'new sections survive and duplicate stat names fail explicitly' {
    $Data = New-Data; $Data.future_section = @{ date=$null; value=42 }
    Assert ((New-MapleSummary $Data).actual.future_section.value -eq 42) 'Future section dropped'
    $Data.stat.final_stat += @{stat_name='INT';stat_value='999'}
    $Failed = $false
    try { $null = New-MapleSummary $Data } catch { $Failed = $true }
    Assert $Failed 'Duplicate stat silently overwrote a value'
}

Test 'all stored preset families survive separately, including empty and null' {
    $Data = New-Data
    $Data.ability.preset_no = 1
    $Data.ability.ability_preset_2 = @{ ability_info=@(@{ability_value='아이템 드롭률 18%'}) }
    $Data.item_equipment.title_preset3 = @{title_name='칭호';title_icon='remove';date_expire=$null}
    $Data.item_equipment.item_equipment_preset_2 = @(@{item_name='대안';item_icon='remove';item_total_option=@{str='123'}})
    $Data.link_skill.character_link_skill_preset_2 = @(@{skill_name='대안 링크';skill_icon='remove';skill_level=2})
    $Data.link_skill.character_owned_link_skill_preset_3 = $null
    $Data.vmatrix.character_v_core_equipment_preset_5 = @()
    $Data.hexamatrix_stat.preset_hexa_stat_core = @(@{slot_id='1';main_stat_level=10})
    $Data.hexamatrix_stat.preset_hexa_stat_core_2 = @()
    $Data.union_raider.union_raider_preset_1 = $null
    $Data.union_raider.union_state_stat_preset = @(@{preset_no=2;union_state_stat=@('보공 20%')})
    $Data.pet_equipment.world_share_pet_1_equipment_preset_no = 3
    $Data.pet_equipment.world_share_pet_equipment_preset = @(@{preset_no=3;item=@{item_icon='remove';scroll_upgrade=10}})
    $BeforeText = ConvertTo-Json -InputObject $Data -Depth 100 -Compress
    $Summary = New-MapleSummary $Data
    Assert ($Summary.presets.Count -eq 8) 'A preset family is missing'
    Assert ($Summary.presets.hyper_stat.hyper_stat_preset_1[0].stat_level -eq 1) 'Inactive hyper preset lost'
    Assert ($Summary.presets.hyper_stat.hyper_stat_preset_2_remain_point -eq 100) 'Remaining points lost'
    Assert ($Summary.actual.ability.preset_no -eq 1) 'Active selector moved'
    Assert ($Summary.presets.ability.ability_preset_2.ability_info[0].ability_value -ceq '아이템 드롭률 18%') 'Ability lost'
    Assert ($Summary.presets.item_equipment.item_equipment_preset_2[0].item_total_option.str -ceq '123') 'Equipment option lost'
    Assert (-not $Summary.presets.item_equipment.title_preset3.Contains('title_icon')) 'Preset icon leaked'
    Assert ($Summary.presets.link_skill.character_link_skill_preset_2.Count -eq 1) 'Link preset array collapsed'
    Assert ($Summary.presets.link_skill.Contains('character_owned_link_skill_preset_3') -and $null -eq $Summary.presets.link_skill.character_owned_link_skill_preset_3) 'Null preset lost'
    Assert ($Summary.presets.vmatrix.character_v_core_equipment_preset_5 -is [array]) 'Empty preset lost'
    Assert ($Summary.presets.hexamatrix_stat.preset_hexa_stat_core[0].slot_id -ceq '1') 'Stored HEXA slot lost'
    Assert ($Summary.presets.union_raider.union_state_stat_preset[0].preset_no -eq 2) 'Union preset number lost'
    Assert ($Summary.presets.pet_equipment.world_share_pet_equipment_preset[0].item.scroll_upgrade -eq 10) 'Pet preset lost'
    Assert ($Summary.actual.pet_equipment.world_share_pet_1_equipment_preset_no -eq 3) 'Pet active selector lost'
    Assert ($BeforeText -ceq (ConvertTo-Json -InputObject $Data -Depth 100 -Compress)) 'Preset extraction mutated raw'
}

Test 'inactive preset edits, additions and failures are compared separately' {
    $Before = New-Data; $After = Copy-Data $Before
    $After.hyper_stat.hyper_stat_preset_1[0].stat_level = 9
    $After.item_equipment.item_equipment_preset_2 = @()
    $After.vmatrix.character_v_core_equipment_preset_5 = $null
    $Diff = New-MapleDiff (New-MapleSummary $Before) (New-MapleSummary $After)
    Assert ($Diff.change_count -eq 3) 'Inactive changes lost or treated as active'
    Assert (@($Diff.changes | Where-Object path -NotLike '$.presets.*').Count -eq 0) 'Preset change confused with actual'
    $After.hyper_stat = @{error=$true;message='failure'}
    $Diff = New-MapleDiff (New-MapleSummary $Before) (New-MapleSummary $After)
    Assert ($Diff.change_count -eq 2) 'Failed section generated preset removals'
    Assert (@($Diff.not_compared | Where-Object section -eq 'hyper_stat').Count -eq 1) 'Preset comparison gap hidden'
}

$TestParent = [IO.Path]::GetFullPath((Join-Path $Root 'output'))
$Work = Join-Path $TestParent "test-$([guid]::NewGuid().ToString('N'))"
New-Item -ItemType Directory -Path $Work -Force | Out-Null
try {
    Test 'real file pipeline preserves bytes, history and repeat diff' {
        $Source = Join-Path $Work 'source.json'
        $Out = Join-Path $Work 'result'
        $Data = New-Data
        Write-MapleJson $Data $Source
        $Hash1 = (Get-FileHash -LiteralPath $Source).Hash
        & (Join-Path $Root 'Build-MapleSnapshot.ps1') -SourcePath $Source -OutputDirectory $Out
        $First = Read-MapleJson (Join-Path $Out 'ai-context.json')
        Assert ($First.changes_since_previous.initial_snapshot) 'First snapshot not marked'
        Assert ($First.schema_version -eq 3 -and $First.presets.hyper_stat.hyper_stat_preset_1.Count -eq 1) 'Preset not exported to ai-context'
        $Published = Get-MaplePublishedSet $Out
        Assert ($null -ne $Published) 'Completed bundle pointer missing'
        Assert ((Read-MapleJson (Join-Path $Published.directory 'ai-context.json')).metadata.raw_sha256 -ceq $First.metadata.raw_sha256) 'Published bundle differs'
        $SummaryFile = Read-MapleJson (Join-Path $Out 'summary.json')
        Assert ((ConvertTo-Json -InputObject $First.presets -Depth 100 -Compress) -ceq (ConvertTo-Json -InputObject $SummaryFile.presets -Depth 100 -Compress)) 'Summary and context presets differ'
        Assert ($First.metadata.collected_at -ceq '2026-09-18T10:00:00+09:00') 'Date string changed'
        Assert ($First.metadata.raw_sha256 -ceq $Hash1.ToLowerInvariant()) 'Wrong hash identity'
        Assert ((Get-FileHash (Join-Path $Out $First.metadata.raw_file)).Hash -ceq $Hash1) 'Raw bytes changed'
        $Data.metadata.collected_at = '2026-09-19T10:00:00+09:00'; $Data.basic.character_level = 277
        Write-MapleJson $Data $Source
        $Hash2 = (Get-FileHash -LiteralPath $Source).Hash
        & (Join-Path $Root 'Build-MapleSnapshot.ps1') -SourcePath $Source -OutputDirectory $Out
        $DiffHash = (Get-FileHash (Join-Path $Out 'diff.json')).Hash
        & (Join-Path $Root 'Build-MapleSnapshot.ps1') -SourcePath $Source -OutputDirectory $Out
        Assert (@(Get-ChildItem (Join-Path $Out 'raw') -File).Count -eq 2) 'Duplicate raw on rebuild'
        Assert ((Get-FileHash (Join-Path $Out 'diff.json')).Hash -ceq $DiffHash) 'Rebuild changed diff'
        Assert ((Get-FileHash $Source).Hash -ceq $Hash2) 'Source modified'
        Assert ((Get-FileHash (Join-Path $Out 'latest.json')).Hash -ceq $Hash2) 'Latest differs from source'
        $Final = Read-MapleJson (Join-Path $Out 'ai-context.json')
        Assert ($Final.changes_since_previous.change_count -eq 1) 'File pipeline lost change'
        Assert ($Final.actual.basic.character_level -eq 277) 'Current state stale'

        # A corrupt history file is reported; filename ordering does not pick it.
        [IO.File]::WriteAllText((Join-Path $Out 'raw/테스트-zzz.json'), '{broken')
        & (Join-Path $Root 'Build-MapleSnapshot.ps1') -SourcePath $Source -OutputDirectory $Out
        $Final = Read-MapleJson (Join-Path $Out 'ai-context.json')
        Assert ($Final.changes_since_previous.history_warnings.Count -eq 1) 'Corrupt history warning missing'

        $OldRejected = $false
        try { & (Join-Path $Root 'Build-MapleSnapshot.ps1') -SourcePath (Join-Path $Out $First.metadata.raw_file) -OutputDirectory $Out } catch { $OldRejected = $true }
        Assert $OldRejected 'Old snapshot overwrote latest'

        $Data.basic.character_level = 278
        Write-MapleJson $Data $Source
        $ConflictRejected = $false
        try { & (Join-Path $Root 'Build-MapleSnapshot.ps1') -SourcePath $Source -OutputDirectory $Out } catch { $ConflictRejected = $true }
        Assert $ConflictRejected 'Conflicting same-time snapshot accepted'
    }

    Test 'locked output and mid-publish failure preserve the completed set' {
        $Source = Join-Path $Work 'publish-source.json'
        $Out = Join-Path $Work 'publish-result'
        $Data = New-Data
        Write-MapleJson $Data $Source
        & (Join-Path $Root 'Build-MapleSnapshot.ps1') -SourcePath $Source -OutputDirectory $Out
        $Names = @('summary.json','diff.json','latest.json','ai-context.json','current.json')
        $Hashes = @{}
        foreach($Name in $Names) { $Hashes[$Name] = (Get-FileHash (Join-Path $Out $Name)).Hash }
        $OldBundle = (Get-MaplePublishedSet $Out).directory
        $Data.metadata.collected_at='2026-09-19T10:00:00+09:00'; $Data.basic.character_level=277
        Write-MapleJson $Data $Source
        $Lock = [IO.File]::Open((Join-Path $Out 'diff.json'), 'Open', 'Read', 'Read')
        $Failed=$false
        try { & (Join-Path $Root 'Build-MapleSnapshot.ps1') -SourcePath $Source -OutputDirectory $Out } catch { $Failed=$true } finally { $Lock.Dispose() }
        Assert $Failed 'Locked output accepted'
        foreach($Name in $Names) { Assert ((Get-FileHash (Join-Path $Out $Name)).Hash -ceq $Hashes[$Name]) "Lock failure changed $Name" }

        # Inject a failure after a root copy has actually been replaced.
        $Module = Get-Module MapleSnapshot
        & $Module {
            $script:OriginalCopy = (Get-Item Function:Copy-MapleFileAtomic).ScriptBlock
            function script:Copy-MapleFileAtomic($Source,$Destination) {
                if ([IO.Path]::GetFileName($Destination) -eq 'diff.json') { throw 'Injected publication failure' }
                & $script:OriginalCopy $Source $Destination
            }
        }
        try {
            $Summary=New-MapleSummary $Data
            $Summary.metadata.raw_sha256=(Get-FileHash $Source).Hash.ToLowerInvariant()
            $Context=@{metadata=$Summary.metadata;actual=$Summary.actual}
            $Failed=$false
            try { Publish-MapleSnapshot $Summary @{} $Context $Source $Out } catch { $Failed=$true }
            Assert $Failed 'Injected publish failure did not happen'
            foreach($Name in $Names) { Assert ((Get-FileHash (Join-Path $Out $Name)).Hash -ceq $Hashes[$Name]) "Rollback failed for $Name" }
        }
        finally { Import-Module (Join-Path $Root 'MapleSnapshot.psm1') -Force }
        Assert ((Get-MaplePublishedSet $Out).directory -ceq $OldBundle) 'Failed publication advanced current pointer'

        # Fail at the final commit after every root copy has been changed.
        $Module=Get-Module MapleSnapshot
        & $Module {
            $script:OriginalWrite = (Get-Item Function:Write-MapleJson).ScriptBlock
            function script:Write-MapleJson($Value,[string]$Path,[switch]$Compress) {
                if ([IO.Path]::GetFileName($Path) -eq 'current.json') { throw 'Injected commit failure' }
                & $script:OriginalWrite $Value $Path -Compress:$Compress
            }
        }
        try {
            $Failed=$false
            try { Publish-MapleSnapshot $Summary @{} $Context $Source $Out } catch { $Failed=$true }
            Assert $Failed 'Commit failure did not happen'
            foreach($Name in $Names) { Assert ((Get-FileHash (Join-Path $Out $Name)).Hash -ceq $Hashes[$Name]) "Commit rollback failed for $Name" }
        }
        finally { Import-Module (Join-Path $Root 'MapleSnapshot.psm1') -Force }
        & (Join-Path $Root 'Build-MapleSnapshot.ps1') -SourcePath $Source -OutputDirectory $Out
        Assert ((Get-MaplePublishedSet $Out).directory -cne $OldBundle) 'Successful publication did not advance pointer'
        Assert ((Read-MapleJson (Join-Path $OldBundle 'ai-context.json')).actual.basic.character_level -eq 276) 'Old completed set modified'
    }

    Test 'collector transport: masked input, timeout, retry, errors and fatal failure' {
        $global:MapleTestTransport = @{
            Calls = [System.Collections.Generic.List[object]]::new()
            RateLimited = $false
            IdFailure = $false
        }
        function Read-Host {
            param($Prompt, [switch]$AsSecureString)
            Assert $AsSecureString 'Key prompt must use SecureString'
            return (ConvertTo-SecureString 'synthetic-key-for-test' -AsPlainText -Force)
        }
        function Start-Sleep { param($Milliseconds, $Seconds) }
        function Invoke-RestMethod {
            param($Method, $Uri, $Headers, $TimeoutSec)
            Assert ($Headers['x-nxopen-api-key'] -ceq 'synthetic-key-for-test') 'Missing API header'
            $global:MapleTestTransport.Calls.Add(@{ uri=$Uri; timeout=$TimeoutSec })
            if ($Uri -match '/id\?') {
                if ($global:MapleTestTransport.IdFailure) { throw 'Synthetic ID failure' }
                return @{ocid='synthetic-ocid'}
            }
            $Status = $null
            if ($Uri -match '/character/basic\?' -and -not $global:MapleTestTransport.RateLimited) {
                $global:MapleTestTransport.RateLimited = $true; $Status = 429
            }
            if ($Uri -match '/ring-reserve-skill-equipment\?') { $Status = 400 }
            if ($Status) {
                $Exception = [Exception]::new('Synthetic HTTP failure')
                $Exception | Add-Member -NotePropertyName Response -NotePropertyValue @{StatusCode=$Status}
                $Record = [Management.Automation.ErrorRecord]::new($Exception, 'TestHttp', 'NotSpecified', $null)
                $Record.ErrorDetails = [Management.Automation.ErrorDetails]::new('{"error":{"name":"OPENAPI_TEST"}}')
                throw $Record
            }
            return @{ date=$null }
        }
        $CollectorOut = Join-Path $Work 'collector.json'
        & (Join-Path $Root 'Get-MapleCharacterData.ps1') -CharacterName '테스트' -OutputPath $CollectorOut -NoPause -MaxRetries 1 -TimeoutSeconds 17
        $Collected = Read-MapleJson $CollectorOut
        Assert ($global:MapleTestTransport.Calls.Count -eq 21) 'Unexpected request/retry count'
        Assert (@($global:MapleTestTransport.Calls | Where-Object uri -Match 'ring-exchange').Count -eq 0) 'Retired endpoint called'
        Assert (@($global:MapleTestTransport.Calls | Where-Object timeout -ne 17).Count -eq 0) 'Timeout not applied'
        Assert ($Collected.ring_reserve.http_status -eq 400) 'HTTP status missing'
        Assert ($Collected.ring_reserve.api_error_code -ceq 'OPENAPI_TEST') 'API error code missing'
        Assert ($Collected.ring_reserve.message -ceq 'Synthetic HTTP failure') 'Error message lost'
        Assert ($null -ne $Collected.metadata.collection_finished_at) 'Completion time missing'
        Assert (-not (Get-Content $CollectorOut -Raw).Contains('synthetic-key-for-test')) 'Key persisted'
        $BeforeHash = (Get-FileHash $CollectorOut).Hash
        $global:MapleTestTransport.IdFailure = $true
        $Failed = $false
        try { & (Join-Path $Root 'Get-MapleCharacterData.ps1') -OutputPath $CollectorOut -NoPause } catch { $Failed = $true }
        Assert $Failed 'Fatal ID failure swallowed'
        Assert ((Get-FileHash $CollectorOut).Hash -ceq $BeforeHash) 'Fatal failure overwrote previous source'
    }
}
finally {
    Remove-Variable -Name MapleTestTransport -Scope Global -ErrorAction SilentlyContinue
    $Resolved = [IO.Path]::GetFullPath($Work)
    if (-not $Resolved.StartsWith($TestParent + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) { throw 'Unsafe test cleanup path' }
    Remove-Item -LiteralPath $Resolved -Recurse -Force
}
Write-Host "Passed $script:Passed tests (offline; no API key required)."
