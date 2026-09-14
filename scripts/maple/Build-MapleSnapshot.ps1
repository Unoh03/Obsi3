<#
Post-process a full MapleStory Open API JSON snapshot into compact analysis files.
#>

[CmdletBinding()]
param(
    [Parameter()]
    [string]$SourcePath = (Join-Path $PSScriptRoot "output\우노03-maple-api.json")
)

$ErrorActionPreference = "Stop"
$SourcePath = [IO.Path]::GetFullPath($SourcePath)
$OutputDir = Split-Path -Parent $SourcePath
$RawDir = Join-Path $OutputDir "raw"
$LatestPath = Join-Path $OutputDir "latest.json"
$SummaryPath = Join-Path $OutputDir "summary.json"
$DiffPath = Join-Path $OutputDir "diff.json"

New-Item -ItemType Directory -Path $RawDir -Force | Out-Null

function Is-Error($Value) {
    return ($null -eq $Value -or $Value.error -eq $true)
}

function Write-Json($Value, [string]$Path, [int]$Depth = 50) {
    $Value | ConvertTo-Json -Depth $Depth | Set-Content -Path $Path -Encoding utf8
}

function Get-Stat($Data, [string]$Name) {
    if (Is-Error $Data.stat) { return $null }
    $Row = @($Data.stat.final_stat) | Where-Object stat_name -eq $Name | Select-Object -First 1
    if ($null -eq $Row) { return $null }
    return $Row.stat_value
}

function New-Summary($Data) {
    $Hyper = [ordered]@{ error = $true; entries = @() }
    if (-not (Is-Error $Data.hyper_stat)) {
        $No = [string]$Data.hyper_stat.use_preset_no
        $Property = "hyper_stat_preset_$No"
        $Entries = foreach ($Row in @($Data.hyper_stat.$Property)) {
            if ([int]$Row.stat_level -gt 0) {
                [ordered]@{ type = $Row.stat_type; level = $Row.stat_level; increase = $Row.stat_increase }
            }
        }
        $Hyper = [ordered]@{ use_preset_no = $No; entries = @($Entries) }
    }

    $Ability = [ordered]@{ error = $true; entries = @() }
    if (-not (Is-Error $Data.ability)) {
        $Entries = foreach ($Row in @($Data.ability.ability_info)) {
            [ordered]@{ no = $Row.ability_no; grade = $Row.ability_grade; value = $Row.ability_value }
        }
        $Ability = [ordered]@{
            use_preset_no = $Data.ability.preset_no
            grade = $Data.ability.ability_grade
            entries = @($Entries)
        }
    }

    $Equipment = [ordered]@{ error = $true; items = @() }
    if (-not (Is-Error $Data.item_equipment)) {
        $Items = foreach ($Item in @($Data.item_equipment.item_equipment)) {
            [ordered]@{
                slot = $Item.item_equipment_slot
                name = $Item.item_name
                starforce = $Item.starforce
                potential_grade = $Item.potential_option_grade
                potential = @($Item.potential_option_1, $Item.potential_option_2, $Item.potential_option_3)
                additional_grade = $Item.additional_potential_option_grade
                additional = @($Item.additional_potential_option_1, $Item.additional_potential_option_2, $Item.additional_potential_option_3)
                special_ring_level = $Item.special_ring_level
                expires = $Item.date_expire
            }
        }
        $Equipment = [ordered]@{ use_preset_no = $Data.item_equipment.preset_no; items = @($Items) }
    }

    $Symbols = @()
    if (-not (Is-Error $Data.symbol_equipment)) {
        $Symbols = @(
            foreach ($Symbol in @($Data.symbol_equipment.symbol)) {
                [ordered]@{
                    name = $Symbol.symbol_name
                    level = $Symbol.symbol_level
                    force = $Symbol.symbol_force
                    growth = $Symbol.symbol_growth_count
                    required = $Symbol.symbol_require_growth_count
                }
            }
        )
    }

    $Hexa = @()
    if (-not (Is-Error $Data.hexamatrix)) {
        $Hexa = @(
            foreach ($Core in @($Data.hexamatrix.character_hexa_core_equipment)) {
                [ordered]@{
                    name = $Core.hexa_core_name
                    type = $Core.hexa_core_type
                    level = $Core.hexa_core_level
                    event_level = $Core.hexa_core_event_level
                }
            }
        )
    }

    $Links = [ordered]@{ equipped = @(); owned = $null }
    if (-not (Is-Error $Data.link_skill)) {
        $Links.equipped = @(
            foreach ($Skill in @($Data.link_skill.character_link_skill)) {
                [ordered]@{ name = $Skill.skill_name; level = $Skill.skill_level; effect = $Skill.skill_effect }
            }
        )
        if ($null -ne $Data.link_skill.character_owned_link_skill) {
            $Owned = $Data.link_skill.character_owned_link_skill
            $Links.owned = [ordered]@{ name = $Owned.skill_name; level = $Owned.skill_level; effect = $Owned.skill_effect }
        }
    }

    $Union = [ordered]@{ profile = $null; raider_preset = $null }
    if (-not (Is-Error $Data.union)) {
        $Union.profile = [ordered]@{
            level = $Data.union.union_level
            grade = $Data.union.union_grade
            artifact_level = $Data.union.union_artifact_level
            artifact_exp = $Data.union.union_artifact_exp
            artifact_point = $Data.union.union_artifact_point
        }
    }
    if (-not (Is-Error $Data.union_raider)) {
        $Union.raider_preset = $Data.union_raider.use_preset_no
    }

    $Ring = $null
    if (-not (Is-Error $Data.ring_reserve)) {
        $Ring = [ordered]@{
            name = $Data.ring_reserve.special_ring_reserve_name
            level = $Data.ring_reserve.special_ring_reserve_level
        }
    }

    $Basic = [ordered]@{ error = $true }
    if (-not (Is-Error $Data.basic)) {
        $Basic = [ordered]@{
            world = $Data.basic.world_name
            class = $Data.basic.character_class
            level = $Data.basic.character_level
            exp = $Data.basic.character_exp
            exp_rate = $Data.basic.character_exp_rate
            guild = $Data.basic.character_guild_name
        }
    }

    return [ordered]@{
        metadata = [ordered]@{
            character_name = $Data.metadata.character_name
            collected_at = $Data.metadata.collected_at
            source = $Data.metadata.source
        }
        basic = $Basic
        stats = [ordered]@{
            combat_power = Get-Stat $Data "전투력"
            STR = Get-Stat $Data "STR"
            damage = Get-Stat $Data "데미지"
            boss_damage = Get-Stat $Data "보스 몬스터 데미지"
            final_damage = Get-Stat $Data "최종 데미지"
            ignore_defense = Get-Stat $Data "방어율 무시"
            critical_rate = Get-Stat $Data "크리티컬 확률"
            critical_damage = Get-Stat $Data "크리티컬 데미지"
            arcane_force = Get-Stat $Data "아케인포스"
            authentic_force = Get-Stat $Data "어센틱포스"
            attack_power = Get-Stat $Data "공격력"
            additional_exp = Get-Stat $Data "추가 경험치 획득"
        }
        hyper_stat = $Hyper
        ability = $Ability
        equipment = $Equipment
        symbols = $Symbols
        hexa = $Hexa
        links = $Links
        union = $Union
        special_ring = $Ring
    }
}

function Comparable($Value) {
    if ($null -eq $Value) { return "<null>" }
    return ($Value | ConvertTo-Json -Depth 30 -Compress)
}

function Add-Change($List, [string]$Category, [string]$Key, $Before, $After) {
    if ((Comparable $Before) -eq (Comparable $After)) { return }
    $List.Add([pscustomobject][ordered]@{ category = $Category; key = $Key; before = $Before; after = $After })
}

function Keyed($Items, [string]$Property) {
    $Map = @{}
    foreach ($Item in @($Items)) {
        if ($null -eq $Item) { continue }
        $Key = [string]$Item.$Property
        if (-not [string]::IsNullOrWhiteSpace($Key)) { $Map[$Key] = $Item }
    }
    return $Map
}

function New-Diff($Before, $After, [string]$PreviousRaw, [string]$CurrentRaw) {
    if ($null -eq $Before) {
        return [ordered]@{
            initial_snapshot = $true
            message = "비교할 이전 raw 스냅샷이 없습니다. 다음 실행부터 변경분을 기록합니다."
            metadata = [ordered]@{ current_collected_at = $After.metadata.collected_at; current_raw = $CurrentRaw }
            changes = @()
        }
    }

    $Changes = [System.Collections.Generic.List[object]]::new()
    Add-Change $Changes "basic" "level" $Before.basic.level $After.basic.level

    foreach ($Name in @("combat_power", "STR", "damage", "boss_damage", "final_damage", "ignore_defense", "critical_rate", "critical_damage", "arcane_force", "authentic_force", "attack_power", "additional_exp")) {
        Add-Change $Changes "stat" $Name $Before.stats.$Name $After.stats.$Name
    }

    Add-Change $Changes "preset" "equipment" $Before.equipment.use_preset_no $After.equipment.use_preset_no
    Add-Change $Changes "preset" "hyper_stat" $Before.hyper_stat.use_preset_no $After.hyper_stat.use_preset_no
    Add-Change $Changes "preset" "ability" $Before.ability.use_preset_no $After.ability.use_preset_no
    Add-Change $Changes "preset" "union_raider" $Before.union.raider_preset $After.union.raider_preset
    Add-Change $Changes "hyper_stat" "active_entries" $Before.hyper_stat.entries $After.hyper_stat.entries
    Add-Change $Changes "ability" "active_entries" $Before.ability.entries $After.ability.entries
    Add-Change $Changes "special_ring" "reserve" $Before.special_ring $After.special_ring

    $CompareSets = @(
        [pscustomobject]@{ category = "equipment"; key_property = "slot" },
        [pscustomobject]@{ category = "symbol"; key_property = "name" },
        [pscustomobject]@{ category = "hexa"; key_property = "name" }
    )

    foreach ($Spec in $CompareSets) {
        $Category = $Spec.category
        $KeyProperty = $Spec.key_property
        $Left = if ($Category -eq "equipment") { Keyed $Before.equipment.items $KeyProperty } elseif ($Category -eq "symbol") { Keyed $Before.symbols $KeyProperty } else { Keyed $Before.hexa $KeyProperty }
        $Right = if ($Category -eq "equipment") { Keyed $After.equipment.items $KeyProperty } elseif ($Category -eq "symbol") { Keyed $After.symbols $KeyProperty } else { Keyed $After.hexa $KeyProperty }
        $Keys = @(@($Left.Keys) + @($Right.Keys)) | Sort-Object -Unique
        foreach ($Key in $Keys) { Add-Change $Changes $Category $Key $Left[$Key] $Right[$Key] }
    }

    return [ordered]@{
        initial_snapshot = $false
        change_count = $Changes.Count
        metadata = [ordered]@{
            previous_collected_at = $Before.metadata.collected_at
            current_collected_at = $After.metadata.collected_at
            previous_raw = $PreviousRaw
            current_raw = $CurrentRaw
        }
        changes = @($Changes)
    }
}

if (-not (Test-Path -LiteralPath $SourcePath -PathType Leaf)) {
    throw "Source JSON not found: $SourcePath"
}

$Data = Get-Content -LiteralPath $SourcePath -Raw -Encoding utf8 | ConvertFrom-Json -Depth 100
$Character = [string]$Data.metadata.character_name
if ([string]::IsNullOrWhiteSpace($Character)) { $Character = "character" }
$SafeCharacter = $Character -replace '[\\/:*?"<>|]', '_'

$PreviousRawFile = Get-ChildItem -Path $RawDir -Filter "$SafeCharacter-*.json" -File -ErrorAction SilentlyContinue | Sort-Object Name | Select-Object -Last 1
$Stamp = Get-Date -Format "yyyy-MM-dd-HHmmss-fff"
$RawPath = Join-Path $RawDir "$SafeCharacter-$Stamp.json"

Copy-Item -LiteralPath $SourcePath -Destination $RawPath -Force
Copy-Item -LiteralPath $SourcePath -Destination $LatestPath -Force

$Summary = New-Summary $Data
Write-Json $Summary $SummaryPath 40

$PreviousSummary = $null
$PreviousRawPath = $null
if ($null -ne $PreviousRawFile) {
    try {
        $PreviousData = Get-Content -LiteralPath $PreviousRawFile.FullName -Raw -Encoding utf8 | ConvertFrom-Json -Depth 100
        $PreviousSummary = New-Summary $PreviousData
        $PreviousRawPath = $PreviousRawFile.FullName
    }
    catch {
        Write-Warning "Previous raw snapshot could not be read. diff.json will be treated as an initial snapshot."
    }
}

$Diff = New-Diff $PreviousSummary $Summary $PreviousRawPath $RawPath
Write-Json $Diff $DiffPath 50

Write-Host ""
Write-Host "Snapshot files updated:"
Write-Host "RAW     : $RawPath"
Write-Host "LATEST  : $LatestPath"
Write-Host "SUMMARY : $SummaryPath"
Write-Host "DIFF    : $DiffPath"
