#requires -Version 7.5
$ErrorActionPreference='Stop'
$Root = Split-Path -Parent $PSScriptRoot
Import-Module (Join-Path $Root 'MapleSnapshot.psm1') -Force
Import-Module (Join-Path $Root 'MapleOwnedLinks.psm1') -Force
function Assert($Condition, $Message) { if (-not $Condition) { throw $Message } }
$script:Passed=0
function Test($Name, [scriptblock]$Body) { & $Body; $script:Passed++; Write-Host "PASS $Name" }
function New-TestData($Name='A', $Time='2026-10-04T12:00:00+09:00', $World='test-world') {
    return [ordered]@{
        metadata=@{character_name=$Name;collected_at=$Time}
        basic=@{world_name=$World;character_name=$Name}
        stat=@{final_stat=@(@{stat_name='STR';stat_value='10'})}
        link_skill=@{character_link_skill=@();character_owned_link_skill=$null;character_link_skill_preset_1=@();character_link_skill_preset_2=@();character_link_skill_preset_3=@()}
    }
}
function Config {
    return @{schema_version=1;groups=@(@{
        id='test';world_name='test-world';characters=@('A','B');verified_on='2026-10-03'
        verified_from_character='A';source='user_verified';evidence='synthetic'
        skills=@(@{skill_name='seed';level=2},@{skill_name='not-equipped';level=6})
    })}
}
$Work = Join-Path $Root "output/owned-links-test-$([guid]::NewGuid().ToString('N'))"
New-Item -ItemType Directory -Path "$Work/characters/A/raw","$Work/characters/B/raw" -Force | Out-Null
$Out = "$Work/characters/A"
try {
    Test 'explicit group shares seed, preserves self links and rejects other worlds or names' {
        $A=New-TestData; $B=New-TestData 'B'; $B.link_skill.character_owned_link_skill=@{skill_name='self-B';skill_level=2}
        $Before=ConvertTo-Json $B -Depth 30 -Compress
        $First=New-MapleOwnedLinks $A (Config) $Out
        $Second=New-MapleOwnedLinks $B (Config) "$Work/characters/B"
        Assert ($First.skills.Count -eq 2 -and $Second.skills.Count -eq 3) 'Dynamic candidate addition failed'
        Assert ($Second.skills[2].source -ceq 'api_observed') 'Invented user verification'
        Assert ($Before -ceq (ConvertTo-Json $B -Depth 30 -Compress)) 'API state mutated'
        Assert ($null -eq (New-MapleOwnedLinks (New-TestData 'AB') (Config) $Out)) 'Prefix match leaked'
        Assert ($null -eq (New-MapleOwnedLinks (New-TestData 'A' '2026-10-04' 'other-world') (Config) $Out)) 'World mismatch leaked'
    }
    Test 'new names persist from raw history, peers contribute, future and pre-verification unlisted rows do not' {
        $Past=New-TestData 'B' '2026-10-04T09:00:00+09:00'
        $Past.link_skill.character_link_skill_preset_3=@(@{skill_name='new-link';skill_level=1})
        Write-MapleJson $Past "$Work/characters/B/raw/past.json"
        $Future=New-TestData 'B' '2026-10-05T00:00:00+09:00'
        $Future.link_skill.character_link_skill=@(@{skill_name='future';skill_level=2})
        Write-MapleJson $Future "$Work/characters/B/raw/future.json"
        $Old=New-TestData 'B' '2026-10-02T00:00:00+09:00'
        $Old.link_skill.character_link_skill=@(@{skill_name='old-unlisted';skill_level=2})
        Write-MapleJson $Old "$Work/characters/B/raw/old.json"
        $Result=New-MapleOwnedLinks (New-TestData) (Config) $Out
        Assert ($Result.skills.Count -eq 3) 'Lost seed/history or included future/obsolete observation'
        Assert ($Result.skills[2].skill_name -ceq 'new-link' -and $Result.skills[2].level -eq 1) 'Peer observation lost'
        $Again=New-MapleOwnedLinks (New-TestData) (Config) $Out
        Assert ((ConvertTo-Json $Result -Depth 30 -Compress) -ceq (ConvertTo-Json $Again -Depth 30 -Compress)) 'Not reproducible'
    }
    Test 'raw file order cannot change levels or resurrect pre-verification observations' {
        $History="$Work/permuted"
        New-Item -ItemType Directory -Path "$History/raw" -Force | Out-Null
        $Old=New-TestData 'A' '2026-10-02T00:00:00+09:00'
        $Old.link_skill.character_link_skill=@(@{skill_name='new-link';skill_level=1})
        $New=New-TestData 'A' '2026-10-04T09:00:00+09:00'
        $New.link_skill.character_link_skill=@(@{skill_name='new-link';skill_level=2})
        Write-MapleJson $Old "$History/raw/a.json"
        Write-MapleJson $New "$History/raw/b.json"
        $First=New-MapleOwnedLinks (New-TestData) (Config) $History
        Write-MapleJson $New "$History/raw/a.json"
        Write-MapleJson $Old "$History/raw/b.json"
        $Second=New-MapleOwnedLinks (New-TestData) (Config) $History
        Assert ((ConvertTo-Json $First -Depth 30 -Compress) -ceq (ConvertTo-Json $Second -Depth 30 -Compress)) 'History order changes inventory'
        $Link=@($Second.skills | Where-Object skill_name -EQ 'new-link')[0]
        Assert ($Link.level -eq 2 -and $Link.observed_levels.Count -eq 1 -and -not $Link.level_review_required) 'Pre-verification level resurrected'
    }
    Test 'dictionary observations have a canonical field order' {
        $Current=New-TestData
        $Current.link_skill.character_link_skill_preset_3=@(@{skill_name='seed';skill_level=2})
        $Current.link_skill.character_link_skill_preset_1=@(@{skill_name='seed';skill_level=2})
        $Current.link_skill.character_owned_link_skill=@{skill_name='seed';skill_level=2}
        $Current.link_skill.character_link_skill=@(@{skill_name='seed';skill_level=2})
        $Result=New-MapleOwnedLinks $Current (Config) "$Work/empty"
        $Fields=@($Result.skills[0].observations | ForEach-Object { $_.field })
        Assert (($Fields -join ',') -ceq 'character_link_skill,character_link_skill_preset_1,character_link_skill_preset_3,character_owned_link_skill') 'Dictionary fields are not sorted'
    }
    Test 'level disagreement is visible and never blindly promoted or downgraded' {
        $Current=New-TestData
        $Current.link_skill.character_link_skill=@(@{skill_name='seed';skill_level=3},@{skill_name='new-link';skill_level=2})
        $Result=New-MapleOwnedLinks $Current (Config) $Out
        $Seed=@($Result.skills | Where-Object skill_name -EQ seed)[0]
        $New=@($Result.skills | Where-Object skill_name -EQ new-link)[0]
        Assert ($Seed.level -eq 2 -and $Seed.level_review_required) 'Verified level silently changed'
        Assert ($null -eq $New.level -and $New.level_review_required -and $New.observed_levels.Count -eq 2) 'Maximum level guessed'
    }
    Test 'failed or malformed API data does not remove seed or invent ownership' {
        $Current=New-TestData; $Current.link_skill=@{error=$true;message='test'}
        $Result=New-MapleOwnedLinks $Current (Config) $Out
        Assert ($Result.skills.Count -eq 3) 'Failure erased history'
        $Current.link_skill=@{character_link_skill=@(@{skill_name='invalid';skill_level=$true})}
        $Result=New-MapleOwnedLinks $Current (Config) $Out
        Assert ($Result.skills.Count -eq 3 -and $Result.info.warnings.Count -eq 1) 'Malformed level accepted'
    }
    Test 'invalid seed fails; a later verification is explicitly dated when applied to old raw' {
        $Bad=Config; $Bad.groups[0].skills+=@{skill_name='seed';level=4}
        $Failed=$false
        try { $null=New-MapleOwnedLinks (New-TestData) $Bad $Out } catch {$Failed=$true}
        Assert $Failed 'Duplicate seed accepted'
        $Result=New-MapleOwnedLinks (New-TestData 'A' '2026-10-02T10:00:00+09:00') (Config) $Out
        Assert ($Result.info.verification_newer_than_snapshot -and $Result.skills.Count -eq 2) 'New verification masquerades as old API evidence'
    }
    Test 'publication adds context without changing actual, presets, diff or source bytes' {
        $ConfigPath="$Work/config.json"; Write-MapleJson (Config) $ConfigPath
        $Source="$Work/input.json"; Write-MapleJson (New-TestData) $Source
        $Hash=(Get-FileHash $Source).Hash
        & "$Root/Build-MapleSnapshot.ps1" -SourcePath $Source -OutputDirectory "$Work/plain" -PresetRolesPath '' -OwnedLinksPath '' -Quiet
        & "$Root/Build-MapleSnapshot.ps1" -SourcePath $Source -OutputDirectory "$Work/enriched" -PresetRolesPath '' -OwnedLinksPath $ConfigPath -Quiet
        $Plain=Read-MapleJson "$Work/plain/ai-context.json"
        $Rich=Read-MapleJson "$Work/enriched/ai-context.json"
        foreach ($Key in @('actual','presets','changes_since_previous')) {
            Assert ((ConvertTo-Json $Plain[$Key] -Depth 100 -Compress) -ceq (ConvertTo-Json $Rich[$Key] -Depth 100 -Compress)) "Changed API-derived $Key"
        }
        Assert ($Rich.user_context.owned_link_skills.Count -eq 2 -and -not $Rich.user_context.Contains('preset_roles')) 'Context contract incorrect'
        Assert ((Get-FileHash $Source).Hash -ceq $Hash) 'Raw modified'
        $Before=(Get-FileHash "$Work/enriched/current.json").Hash
        $Bad=Config; $Bad.groups[0].skills[0].level=0; Write-MapleJson $Bad $ConfigPath
        $Failed=$false
        try { & "$Root/Build-MapleSnapshot.ps1" -SourcePath $Source -OutputDirectory "$Work/enriched" -PresetRolesPath '' -OwnedLinksPath $ConfigPath -Quiet } catch {$Failed=$true}
        Assert ($Failed -and (Get-FileHash "$Work/enriched/current.json").Hash -ceq $Before) 'Bad config changed last good result'
    }
}
finally {
    $Allowed=[IO.Path]::GetFullPath((Join-Path $Root 'output')) + [IO.Path]::DirectorySeparatorChar
    $Resolved=[IO.Path]::GetFullPath($Work)
    if (-not $Resolved.StartsWith($Allowed,[StringComparison]::OrdinalIgnoreCase)) {throw 'Unsafe test cleanup'}
    Remove-Item -LiteralPath $Resolved -Recurse -Force
}
Write-Host "Passed $script:Passed owned link tests (offline)."
