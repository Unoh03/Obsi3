#requires -Version 7.5
Import-Module (Join-Path $PSScriptRoot 'MapleSnapshot.psm1')

function New-MapleOwnedLinks($Data, $Config, [string]$OutputDirectory) {
    if ($Config.schema_version -ne 1 -or $Config.groups -isnot [System.Collections.IList]) {
        throw 'Invalid owned-link-skills config'
    }
    $Character = [string]$Data.metadata.character_name
    $World = [string]$Data.basic.world_name
    $Groups = @($Config.groups | Where-Object { $Character -cin $_.characters -and $World -ceq $_.world_name })
    if ($Groups.Count -eq 0) { return $null }
    if ($Groups.Count -ne 1) { throw 'Ambiguous owned link group' }
    $Group = $Groups[0]
    $Verified = [DateTimeOffset]::MinValue
    if ([string]$Group.verified_on -cnotmatch '^\d{4}-\d{2}-\d{2}$' -or
        -not [DateTimeOffset]::TryParse("$($Group.verified_on)T00:00:00+09:00", [ref]$Verified) -or
        $Group.skills -isnot [System.Collections.IList] -or $Group.source -cne 'user_verified' -or
        $Group.verified_from_character -cnotin $Group.characters) { throw 'Invalid owned link verification' }
    $Skills = [System.Collections.Specialized.OrderedDictionary]::new([StringComparer]::Ordinal)
    foreach ($Skill in $Group.skills) {
        if ([string]::IsNullOrWhiteSpace($Skill.skill_name) -or $Skills.Contains($Skill.skill_name) -or
            $Skill.level -isnot [int] -and $Skill.level -isnot [long] -or $Skill.level -lt 1) {
            throw 'Invalid or duplicate verified link skill'
        }
        $Skills[$Skill.skill_name] = [ordered]@{
            skill_name=$Skill.skill_name; level=$Skill.level; source='user_verified'
            observed_levels=@(); observations=@(); level_review_required=$false
        }
    }
    $SeedNames = @($Skills.Keys)
    $Cutoff = [DateTimeOffset]$Data.metadata.collected_at
    $Records = [System.Collections.Generic.List[object]]::new()
    $Warnings = [System.Collections.Generic.List[string]]::new()
    $Records.Add($Data)
    $Directories = [System.Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)
    $null = $Directories.Add((Join-Path $OutputDirectory 'raw'))
    # Shared observations are restricted to explicitly registered characters.
    # Explicit/custom output layouts continue to work with their own raw history.
    $Parent = [IO.Directory]::GetParent([IO.Path]::GetFullPath($OutputDirectory))
    if ($Parent.Name -ceq 'characters') {
        foreach ($Member in $Group.characters) {
            if ($Member -cnotmatch '^[^\\/:*?"<>|.]+$') { throw 'Invalid owned link character path' }
            $null = $Directories.Add((Join-Path $Parent.FullName "$Member/raw"))
        }
    }
    foreach ($Directory in ($Directories | Sort-Object)) {
        if (-not (Test-Path -LiteralPath $Directory)) { continue }
        foreach ($File in Get-ChildItem -LiteralPath $Directory -File -Filter '*.json' | Sort-Object Name) {
            try {
                $Record = Read-MapleJson $File.FullName
                $null = [DateTimeOffset]::Parse([string]$Record.metadata.collected_at)
                $Records.Add($Record)
            }
            catch { $Warnings.Add("보유 링크 이력 읽기 실패: $($File.Name)") }
        }
    }
    # Latest observation per character/field/level; keep levels separate, never max().
    $Observations = @{}
    foreach ($Record in $Records) {
        $Time = [DateTimeOffset]$Record.metadata.collected_at
        if ($Time -gt $Cutoff -or $Record.metadata.character_name -cnotin $Group.characters -or
            $Record.basic.world_name -cne $World -or $Record.link_skill -isnot [System.Collections.IDictionary] -or
            $Record.link_skill.error -eq $true) { continue }
        foreach ($Field in @('character_link_skill','character_owned_link_skill',
            'character_link_skill_preset_1','character_link_skill_preset_2','character_link_skill_preset_3',
            'character_owned_link_skill_preset_1','character_owned_link_skill_preset_2','character_owned_link_skill_preset_3')) {
            foreach ($Row in @($Record.link_skill[$Field])) {
                if ($null -eq $Row) { continue }
                if ($Row -isnot [System.Collections.IDictionary] -or [string]::IsNullOrWhiteSpace($Row.skill_name) -or
                    ($Row.skill_level -isnot [int] -and $Row.skill_level -isnot [long]) -or $Row.skill_level -lt 1) {
                    $Warnings.Add("보유 링크 항목 검증 실패: $($Record.metadata.character_name)/$Field")
                    continue
                }
                # A newer full user verification supersedes older unlisted observations.
                # Test the immutable seed, not the map populated during this scan.
                if ($Time -lt $Verified -and $Row.skill_name -cnotin $SeedNames) { continue }
                if (-not $Skills.Contains($Row.skill_name)) {
                    $Skills[$Row.skill_name] = [ordered]@{
                        skill_name=$Row.skill_name; level=$null; source='api_observed'
                        observed_levels=@(); observations=@(); level_review_required=$false
                    }
                }
                $Key = ConvertTo-Json -InputObject @($Row.skill_name,$Row.skill_level,$Record.metadata.character_name,$Field) -Compress
                if (-not $Observations.ContainsKey($Key) -or $Time -gt [DateTimeOffset]$Observations[$Key].collected_at) {
                    $Observations[$Key] = [ordered]@{
                        skill_name=$Row.skill_name; level=$Row.skill_level
                        character_name=$Record.metadata.character_name; field=$Field
                        collected_at=$Record.metadata.collected_at
                    }
                }
            }
        }
    }
    $Names = $SeedNames + @($Skills.Keys | Where-Object { $_ -cnotin $SeedNames } | Sort-Object -CaseSensitive)
    foreach ($Name in $Names) {
        $Skill = $Skills[$Name]
        # Scriptblock keys read dictionary entries; bare property names do not
        # reliably sort OrderedDictionary records across PowerShell processes.
        $Skill.observations = @($Observations.Values | Where-Object skill_name -CEQ $Name |
            Sort-Object { $_.character_name }, { $_.field }, { $_.level })
        $Skill.observed_levels = @($Skill.observations.level | Sort-Object -Unique)
        if ($Skill.source -ceq 'api_observed' -and $Skill.observed_levels.Count -eq 1) { $Skill.level=$Skill.observed_levels[0] }
        $Recent = @($Skill.observations | Where-Object { [DateTimeOffset]$_.collected_at -ge $Verified })
        $Skill.level_review_required = if ($Skill.source -ceq 'user_verified') {
            @($Recent | Where-Object level -NE $Skill.level).Count -gt 0
        } else { $Skill.observed_levels.Count -ne 1 }
    }
    return [ordered]@{
        skills=@($Names | ForEach-Object { $Skills[$_] })
        info=[ordered]@{
            group_id=$Group.id; world_name=$World; characters=$Group.characters
            verified_on=$Group.verified_on; verified_from_character=$Group.verified_from_character
            evidence=$Group.evidence; api_observations_through=$Data.metadata.collected_at
            verification_newer_than_snapshot=($Verified -gt $Cutoff)
            warnings=@($Warnings | Select-Object -Unique)
            rules=@(
                '현재 세팅 추천은 owned_link_skills의 이름을 후보로 사용합니다. 목록 밖은 보유 미확인/육성 후보로 분리합니다.',
                '공통 보유 목록은 장착 목록이 아닙니다. 본인 링크·장착·효과·프리셋은 각 캐릭터의 actual.link_skill과 presets.link_skill을 확인합니다. 본인 링크를 전수 슬롯에 중복 추천하지 마세요.',
                'level은 사용자 확인값 또는 단일 API 관측값입니다. 레벨 차이는 observations와 level_review_required로 확인하며 최대 레벨·캐릭터별 적용 효과를 추정하지 않습니다.',
                'API에서 안 보인다는 이유로 삭제하지 않습니다. 전체 목록 검증은 verified_on 시점이며 이후 소실·최신성은 보증하지 않습니다. 오래된 관측은 현재 장착/레벨 증거가 아닙니다.'
            )
        }
    }
}

Export-ModuleMember -Function New-MapleOwnedLinks
