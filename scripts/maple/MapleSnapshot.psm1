#requires -Version 7.5
$script:Endpoints = [ordered]@{
    basic = 'character/basic'
    stat = 'character/stat'
    hyper_stat = 'character/hyper-stat'
    ability = 'character/ability'
    item_equipment = 'character/item-equipment'
    symbol_equipment = 'character/symbol-equipment'
    set_effect = 'character/set-effect'
    pet_equipment = 'character/pet-equipment'
    link_skill = 'character/link-skill'
    vmatrix = 'character/vmatrix'
    hexamatrix = 'character/hexamatrix'
    hexamatrix_stat = 'character/hexamatrix-stat'
    dojang = 'character/dojang'
    other_stat = 'character/other-stat'
    ring_reserve = 'character/ring-reserve-skill-equipment'
    union = 'user/union'
    union_raider = 'user/union-raider'
    union_artifact = 'user/union-artifact'
    union_champion = 'user/union-champion'
}
$script:Sections = @($script:Endpoints.Keys)
$script:PublishedFiles = @('summary.json','diff.json','latest.json','ai-context.json')
# Only observed presentation fields are eligible for URL omission. Unknown fields,
# nulls and structured values must survive even if their names end in icon/image.
$script:ImageFields = @(
    'character_image', 'item_icon', 'item_shape_icon', 'title_icon', 'title_shape_icon',
    'medal_shape_icon', 'medal_shape_changed_icon', 'symbol_icon', 'skill_icon',
    'skill_1_icon', 'skill_2_icon', 'special_ring_reserve_icon'
)
foreach ($Prefix in @('pet', 'world_share_pet')) {
    foreach ($Number in 1..3) {
        $script:ImageFields += "${Prefix}_${Number}_icon", "${Prefix}_${Number}_appearance_icon"
    }
}

function Get-MapleEndpoints {
    $Result = [ordered]@{}
    foreach ($Key in $script:Endpoints.Keys) { $Result[$Key] = $script:Endpoints[$Key] }
    return $Result
}

function Read-MapleJson([string]$Path) {
    # Keep API date strings as strings (PowerShell 7.5+ otherwise parses ISO dates).
    return (Get-Content -LiteralPath $Path -Raw -Encoding utf8 | ConvertFrom-Json -AsHashtable -Depth 100 -DateKind String)
}

function Write-MapleJson($Value, [string]$Path, [switch]$Compress) {
    $Json = ConvertTo-Json -InputObject $Value -Depth 100 -Compress:$Compress -WarningAction Stop
    $TempPath = "$Path.$([guid]::NewGuid().ToString('N')).tmp"
    try {
        [IO.File]::WriteAllText($TempPath, $Json + "`n", [Text.UTF8Encoding]::new($false))
        [IO.File]::Move($TempPath, $Path, $true)
    }
    finally { if (Test-Path -LiteralPath $TempPath) { Remove-Item -LiteralPath $TempPath } }
}

function Remove-MaplePresentation($Value) {
    if ($Value -is [System.Collections.IDictionary]) {
        $Result = [ordered]@{}
        foreach ($Key in $Value.Keys) {
            if ($Key -cin $script:ImageFields -and $Value[$Key] -is [string] -and
                $Value[$Key] -match '^https?://') { continue }
            $Result[$Key] = Remove-MaplePresentation $Value[$Key]
        }
        return $Result
    }
    if ($Value -is [System.Collections.IList]) {
        $Items = foreach ($Item in $Value) { ,(Remove-MaplePresentation $Item) }
        return ,@($Items)
    }
    return $Value
}

function Get-MapleSectionState($Data, [string]$Section) {
    if (-not $Data.Contains($Section) -or $null -eq $Data[$Section]) { return 'missing' }
    if ($Data[$Section] -is [System.Collections.IDictionary] -and $Data[$Section].error -eq $true) { return 'error' }
    return 'ok'
}

function Get-MapleRequiredFailures($Data) {
    foreach ($Section in @('basic', 'stat')) {
        $State = Get-MapleSectionState $Data $Section
        if ($State -ne 'ok') { "$Section ($State)" }
    }
}

function Test-MapleHyperEntries($Value) {
    if ($Value -isnot [System.Collections.IList]) { return $false }
    foreach ($Row in $Value) {
        if ($Row -isnot [System.Collections.IDictionary] -or
            [string]::IsNullOrWhiteSpace([string]$Row.stat_type) -or
            -not $Row.Contains('stat_level') -or $null -eq $Row.stat_level -or
            $Row.stat_level -is [bool]) { return $false }
        $Level = 0
        if (-not [int]::TryParse([string]$Row.stat_level, [ref]$Level) -or $Level -lt 0) { return $false }
    }
    return $true
}

function New-MapleSummary($Data) {
    $Actual = [ordered]@{}
    $Presets = [ordered]@{}
    $States = [ordered]@{}
    $Dates = [ordered]@{}
    $Errors = [ordered]@{}
    $ValidationIssues = [ordered]@{}
    $Unavailable = [System.Collections.Generic.List[string]]::new()
    $Sections = @($script:Sections) + @($Data.Keys | Where-Object { $_ -ne 'metadata' -and $_ -notin $script:Sections })
    foreach ($Section in $Sections) {
        $State = Get-MapleSectionState $Data $Section
        $States[$Section] = $State
        if ($State -ne 'ok') {
            $Unavailable.Add($Section)
            if ($State -eq 'error') { $Errors[$Section] = $Data[$Section] }
            continue
        }
        $InputSection = $Data[$Section]
        if ($InputSection -is [System.Collections.IDictionary] -and $InputSection.Contains('date')) {
            $Dates[$Section] = $InputSection.date
        }
        $Value = Remove-MaplePresentation $InputSection
        if ($Value -is [System.Collections.IDictionary]) {
            $Value.Remove('date')
            if ($Section -ne 'basic' -and $Data.basic -is [System.Collections.IDictionary]) {
                foreach ($Key in @('character_class', 'character_gender')) {
                    if ($Value.Contains($Key) -and $Data.basic.Contains($Key) -and
                        (ConvertTo-Json -InputObject $Value[$Key] -Depth 100 -Compress) -ceq
                        (ConvertTo-Json -InputObject $Data.basic[$Key] -Depth 100 -Compress)) {
                        $Value.Remove($Key)
                    }
                }
            }
            if ($Section -eq 'hyper_stat') {
                $ActiveKey = "hyper_stat_preset_$($InputSection.use_preset_no)"
                $Resolved = $InputSection.Contains($ActiveKey) -and (Test-MapleHyperEntries $InputSection[$ActiveKey])
                $Value.active_preset_resolved = $Resolved
                if ($Resolved) {
                    $Value.active_entries = $Value[$ActiveKey]
                    $Value.active_remain_point = $InputSection["${ActiveKey}_remain_point"]
                }
                else {
                    $States[$Section] = 'partial'
                    $Unavailable.Add($Section)
                    $ValidationIssues[$Section] = '사용 프리셋의 배분이 누락/null이거나 배열·항목 구조가 올바르지 않습니다. 현재 배분을 확정하지 않습니다. 저장된 값은 presets에 보존합니다.'
                }
                # Unknown active selector: retain the stored alternatives in presets.
            }
            # Move, never discard, stored configurations. Keep original API field names
            # and preset numbers, including null/empty presets and remaining points.
            # *_preset_no selectors remain in actual. Nested data is already sanitized.
            foreach ($Key in @($Value.Keys)) {
                if ($Key -match '(^|_)preset(?:_?\d+)?($|_)' -and
                    $Key -notmatch '(^|_)preset_no$' -and $Key -ne 'active_preset_resolved') {
                    if (-not $Presets.Contains($Section)) { $Presets[$Section] = [ordered]@{} }
                    $Presets[$Section][$Key] = $Value[$Key]
                    $Value.Remove($Key)
                }
            }
            if ($Section -eq 'stat' -and $InputSection.final_stat -is [System.Collections.IList]) {
                $Stats = [System.Collections.Specialized.OrderedDictionary]::new([StringComparer]::Ordinal)
                $CompactRows = $true
                foreach ($Row in $InputSection.final_stat) {
                    if (-not $Row.stat_name -or $Stats.Contains($Row.stat_name)) { throw 'final_stat에 이름 누락/중복이 있습니다. 원본 확인 필요.' }
                    if (-not $Row.Contains('stat_value')) { throw 'final_stat에 stat_value가 누락되었습니다. 원본 확인 필요.' }
                    if ($Row.Count -ne 2) { $CompactRows = $false }
                    $Stats[$Row.stat_name] = $Row.stat_value
                }
                # Preserve new row attributes instead of silently discarding them.
                if ($CompactRows) { $Value.Remove('final_stat') }
                $Value.values = $Stats
            }
        }
        $Actual[$Section] = $Value
    }
    return [ordered]@{
        schema_version = 3
        metadata = Read-MapleMetadata $Data.metadata
        reading_guide = @(
            'NEXON API가 반환한 캐릭터 상태입니다. 실시간 접속 상태나 환산 결과를 뜻하지 않습니다.',
            '먼저 metadata.collected_at과 raw_sha256을 확인하세요. 로컬 재수집은 이미 첨부한 파일을 갱신하지 않습니다.',
            'actual.stat.values는 API의 최종 스탯입니다. 장비/링크/유니온 효과를 여기에 다시 더하지 마세요.',
            '미수집/실패/불완전(partial)은 quality에 표시하며 0 또는 미장착으로 해석하지 않습니다. date=null이면 데이터 기준 시각 미확인입니다.',
            'actual은 현재 상태, presets는 저장된 대안 설정입니다. presets는 API 섹션/원래 필드명으로 찾으며 번호·남은 포인트·null·빈 배열도 보존합니다. 보스용/사냥용이라는 용도는 임의로 추정하지 마세요.',
            '유니온 상태 프리셋은 presets.union_raider.union_state_stat_preset을 우선 확인하세요. 구형 union_raider_preset_1~5의 null만으로 프리셋 전체가 없다고 판단하지 마세요.',
            'quality.section_status의 ok는 전체 필드 검증이나 섹션 간 동시 갱신을 보증하지 않습니다. 검증 범위와 미확인은 quality.assessment에 표시합니다.',
            '확인된 아이콘·이미지 필드의 URL만 생략합니다. 외형 이름·설명·OCID·알 수 없는 필드·null은 보존하며, 직업·성별은 basic과 같은 값만 중복 제거합니다. 전체 응답은 로컬 raw에 있습니다.',
            'changes_since_previous는 직전 비교 가능한 수집본과의 차이이며 누적 이력이 아닙니다. stat.final_stat이 함께 있으면 추가 속성 보존용 원문이므로 values와 중복 합산하지 마세요.',
            '숫자처럼 보이는 문자열도 API 타입 그대로입니다. diff는 정상 수집된 섹션만 비교하며 변화의 원인을 단정하지 않습니다.'
        )
        quality = [ordered]@{
            section_status = $States
            unavailable_sections = @($Unavailable.ToArray())
            errors = $Errors
            validation_issues = $ValidationIssues
            data_dates = $Dates
            assessment = [ordered]@{
                validation_scope = 'section_presence_and_error; stat_names_when_array; active_hyper_entries'
                complete_schema_validation = 'not_performed'
                cross_section_consistency = 'unverified'
                final_stats_preset_binding = 'unverified'
                sections_without_data_date = @($Sections | Where-Object { -not $Dates.Contains($_) -or $null -eq $Dates[$_] -or [string]::IsNullOrWhiteSpace([string]$Dates[$_]) })
                union_state_stat_preset = Get-MapleFieldState $Data.union_raider 'union_state_stat_preset'
            }
        }
        actual = $Actual
        presets = $Presets
    }
}

function Read-MapleMetadata($Metadata) {
    # Copy without narrowing to a fixed subset or mutating the source metadata.
    $Result = [ordered]@{}
    foreach ($Key in $Metadata.Keys) { $Result[$Key] = $Metadata[$Key] }
    return $Result
}

# Presence is not schema validity or proof that the preset is currently active.
function Get-MapleFieldState($Object, [string]$Name) {
    if ($Object -isnot [System.Collections.IDictionary] -or -not $Object.Contains($Name)) { return 'missing' }
    if ($null -eq $Object[$Name]) { return 'null' }
    if ($Object[$Name] -isnot [System.Collections.IList]) { return 'unexpected_type' }
    if ($Object[$Name].Count -eq 0) { return 'empty_array' }
    return 'array_present'
}

function New-MapleUserContext($Summary, $Config) {
    if ($Config -isnot [System.Collections.IDictionary] -or $Config.schema_version -ne 1 -or
        $Config.characters -isnot [System.Collections.IDictionary]) { throw 'Invalid preset-roles config' }
    $Character = [string]$Summary.metadata.character_name
    if (-not $Config.characters.Contains($Character)) { return $null }
    $Description = $Config.characters[$Character]
    if ($Description -isnot [System.Collections.IDictionary] -or
        $Description.preset_roles -isnot [System.Collections.IDictionary] -or
        [string]::IsNullOrWhiteSpace([string]$Description.recorded_on)) { throw 'Invalid character preset description' }
    $Prefixes = @{
        item_equipment = 'item_equipment_preset_'; hyper_stat = 'hyper_stat_preset_'
        ability = 'ability_preset_'; link_skill = 'character_link_skill_preset_'
    }
    $References = [System.Collections.Generic.List[object]]::new()
    foreach ($Section in $Description.preset_roles.Keys) {
        $Roles = $Description.preset_roles[$Section]
        if (-not $Prefixes.ContainsKey($Section) -or $Roles -isnot [System.Collections.IDictionary]) {
            throw "Unsupported preset role section: $Section"
        }
        foreach ($Number in $Roles.Keys) {
            if ([string]$Number -cnotmatch '^[1-3]$' -or $Roles[$Number] -isnot [string] -or
                [string]::IsNullOrWhiteSpace($Roles[$Number])) { throw 'Invalid preset number or label' }
            $Field = $Prefixes[$Section] + $Number
            $Value = $Summary.presets[$Section]
            $State = if ($Value -isnot [System.Collections.IDictionary] -or -not $Value.Contains($Field)) { 'missing' }
                elseif ($null -eq $Value[$Field]) { 'null' }
                else { 'present' }
            $References.Add([ordered]@{
                section = $Section; preset_no = [int]$Number; purpose = $Roles[$Number]
                data_path = "presets.$Section.$Field"; data_presence = $State
            })
        }
    }
    return [ordered]@{
        source = 'user_description'
        character_name = $Character
        recorded_on = $Description.recorded_on
        note = '사용자가 설명한 프리셋 용도입니다. 현재 적용·최종 스탯·설정의 최신성을 보증하지 않습니다. 미지정 프리셋의 용도는 추정하지 않습니다.'
        preset_roles = @($References.ToArray())
    }
}

function Export-MapleAIContext([string]$OutputDirectory, [string]$ExportDirectory) {
    $Published = Get-MaplePublishedSet $OutputDirectory
    if (-not $Published) { throw '완료된 결과 묶음이 없습니다.' }
    $Source = Join-Path $Published.directory 'ai-context.json'
    $Context = Read-MapleJson $Source
    $Collected = ([DateTimeOffset]$Context.metadata.collected_at).ToOffset([TimeSpan]::FromHours(9))
    $Character = [string]$Context.metadata.character_name -replace '[\\/:*?"<>|]', '_'
    $Hash = $Published.manifest.files['ai-context.json']
    $ExportDir = if ($ExportDirectory) { [IO.Path]::GetFullPath($ExportDirectory) } else { Join-Path $OutputDirectory 'exports' }
    New-Item -ItemType Directory -Path $ExportDir -Force | Out-Null
    $Path = Join-Path $ExportDir "ai-context-$Character-$($Collected.ToString('yyyy-MM-dd-HHmmss'))-KST-$($Hash.Substring(0,12)).json"
    if (-not (Test-Path -LiteralPath $Path)) { [IO.File]::Copy($Source, $Path, $false) }
    if ((Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant() -cne $Hash) {
        throw '전달용 파일 hash 불일치. 기존 파일을 덮어쓰지 않습니다.'
    }
    return [ordered]@{ path = [IO.Path]::GetFullPath($Path); collected_at = $Context.metadata.collected_at; sha256 = $Hash }
}

function Get-MapleArrayKey($Left, $Right) {
    foreach ($Key in @('item_equipment_slot','symbol_name','skill_name','hexa_core_name','slot_id','ability_no','stat_type','set_name')) {
        $Valid = $true
        foreach ($Items in @(@{ items = $Left }, @{ items = $Right })) {
            $Seen = [System.Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)
            foreach ($Item in $Items.items) {
                if ($Item -isnot [System.Collections.IDictionary] -or -not $Item.Contains($Key) -or
                    $null -eq $Item[$Key] -or -not $Seen.Add((ConvertTo-Json -InputObject $Item[$Key] -Compress))) {
                    $Valid = $false; break
                }
            }
            if (-not $Valid) { break }
        }
        if ($Valid) { return $Key }
    }
    return $null
}

function Compare-MapleValue($Before, $After, [string]$Path, $Changes, [bool]$BeforeExists = $true, [bool]$AfterExists = $true) {
    if ($BeforeExists -and $AfterExists) {
        if ($Before -is [System.Collections.IDictionary] -and $After -is [System.Collections.IDictionary]) {
            $Keys = [System.Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)
            foreach ($Key in @($Before.Keys) + @($After.Keys)) {
                if ($Keys.Add($Key)) { Compare-MapleValue $Before[$Key] $After[$Key] "$Path.$Key" $Changes ($Before.Contains($Key)) ($After.Contains($Key)) }
            }
            return
        }
        if ($Before -is [System.Collections.IList] -and $After -is [System.Collections.IList]) {
            $Key = Get-MapleArrayKey $Before $After
            if ($Key) {
                $Left = [System.Collections.Specialized.OrderedDictionary]::new([StringComparer]::Ordinal)
                $Right = [System.Collections.Specialized.OrderedDictionary]::new([StringComparer]::Ordinal)
                foreach ($Item in $Before) { $Left[(ConvertTo-Json -InputObject $Item[$Key] -Compress)] = $Item }
                foreach ($Item in $After) { $Right[(ConvertTo-Json -InputObject $Item[$Key] -Compress)] = $Item }
                $Ids = [System.Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)
                foreach ($Id in @($Left.Keys) + @($Right.Keys)) {
                    if ($Ids.Add($Id)) { Compare-MapleValue $Left[$Id] $Right[$Id] "$Path[$Key=$Id]" $Changes ($Left.Contains($Id)) ($Right.Contains($Id)) }
                }
            }
            else {
                for ($i = 0; $i -lt [Math]::Max($Before.Count, $After.Count); $i++) {
                    Compare-MapleValue $Before[$i] $After[$i] "$Path[$i]" $Changes ($i -lt $Before.Count) ($i -lt $After.Count)
                }
            }
            return
        }
        # Serialized comparison preserves string/number/bool/null distinctions.
        if ((ConvertTo-Json -InputObject $Before -Depth 100 -Compress) -ceq (ConvertTo-Json -InputObject $After -Depth 100 -Compress)) { return }
    }
    $Changes.Add([ordered]@{
        path = $Path
        kind = if (-not $BeforeExists) { 'added' } elseif (-not $AfterExists) { 'removed' } else { 'changed' }
        before_exists = $BeforeExists; after_exists = $AfterExists
        before = $Before; after = $After
    })
}

function New-MapleDiff($Before, $After) {
    $Changes = [System.Collections.Generic.List[object]]::new()
    $Skipped = [System.Collections.Generic.List[object]]::new()
    if ($null -ne $Before) {
        $Sections = [System.Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)
        foreach ($Section in @($Before.quality.section_status.Keys) + @($After.quality.section_status.Keys)) {
            if (-not $Sections.Add($Section)) { continue }
            $Left = $Before.quality.section_status[$Section]; $Right = $After.quality.section_status[$Section]
            if ($Left -eq 'ok' -and $Right -eq 'ok') {
                Compare-MapleValue $Before.actual[$Section] $After.actual[$Section] "`$.$Section" $Changes
                $LeftPresets = if ($Before.presets -and $Before.presets.Contains($Section)) { $Before.presets[$Section] } else { [ordered]@{} }
                $RightPresets = if ($After.presets -and $After.presets.Contains($Section)) { $After.presets[$Section] } else { [ordered]@{} }
                Compare-MapleValue $LeftPresets $RightPresets "`$.presets.$Section" $Changes
            }
            else { $Skipped.Add([ordered]@{ section = $Section; before_status = $Left; after_status = $Right }) }
        }
    }
    return [ordered]@{
        initial_snapshot = ($null -eq $Before)
        change_count = $Changes.Count
        changes = @($Changes.ToArray())
        not_compared = @($Skipped.ToArray())
    }
}

function Get-MaplePublishedSet([string]$OutputDirectory) {
    $Pointer = Join-Path $OutputDirectory 'current.json'
    if (-not (Test-Path -LiteralPath $Pointer)) { return $null }
    $Manifest = Read-MapleJson $Pointer
    if ($Manifest.directory -cnotmatch '^snapshots/[0-9a-f]{64}$') { throw 'Invalid snapshot manifest directory' }
    $Directory = Join-Path $OutputDirectory $Manifest.directory
    foreach ($Name in $script:PublishedFiles) {
        $File = Join-Path $Directory $Name
        if (-not (Test-Path -LiteralPath $File -PathType Leaf) -or
            (Get-FileHash -LiteralPath $File -Algorithm SHA256).Hash.ToLowerInvariant() -cne $Manifest.files[$Name]) {
            throw "완료된 결과 묶음의 파일/hash 검증 실패: $Name"
        }
    }
    return [ordered]@{ directory = $Directory; manifest = $Manifest }
}

function Copy-MapleFileAtomic([string]$Source, [string]$Destination) {
    $Temp = "$Destination.$([guid]::NewGuid().ToString('N')).tmp"
    try { [IO.File]::Copy($Source, $Temp); [IO.File]::Move($Temp, $Destination, $true) }
    finally { if (Test-Path -LiteralPath $Temp) { Remove-Item -LiteralPath $Temp } }
}

function Publish-MapleSnapshot($Summary, $Diff, $Context, [string]$RawPath, [string]$OutputDirectory) {
    $OutputDirectory = [IO.Path]::GetFullPath($OutputDirectory)
    $Lock = $null
    $Stage = Join-Path $OutputDirectory ('.publish-' + [guid]::NewGuid().ToString('N'))
    $Changed = [System.Collections.Generic.List[string]]::new()
    $Backups = @{}
    try {
        # The immutable bundle and current.json are the authoritative completed set.
        # Root files are convenience copies, rolled back on a caught publish failure.
        $Lock = [IO.File]::Open((Join-Path $OutputDirectory '.publish.lock'), 'OpenOrCreate', 'ReadWrite', 'None')
        $PreviousSet = Get-MaplePublishedSet $OutputDirectory
        if ($PreviousSet) {
            $PreviousContext = Read-MapleJson (Join-Path $PreviousSet.directory 'ai-context.json')
            if ($PreviousContext.metadata.character_name -ceq $Summary.metadata.character_name -and
                [DateTimeOffset]$PreviousContext.metadata.collected_at -gt [DateTimeOffset]$Summary.metadata.collected_at) {
                throw '이 결과보다 새로운 완료 묶음이 이미 있습니다.'
            }
        }
        New-Item -ItemType Directory -Path $Stage | Out-Null
        Write-MapleJson $Summary (Join-Path $Stage 'summary.json')
        Write-MapleJson $Diff (Join-Path $Stage 'diff.json')
        Write-MapleJson $Context (Join-Path $Stage 'ai-context.json') -Compress
        [IO.File]::Copy($RawPath, (Join-Path $Stage 'latest.json'))
        $Hashes = [ordered]@{}
        foreach ($Name in $script:PublishedFiles) {
            $Hashes[$Name] = (Get-FileHash -LiteralPath (Join-Path $Stage $Name) -Algorithm SHA256).Hash.ToLowerInvariant()
        }
        $Hasher = [Security.Cryptography.SHA256]::Create()
        try { $Id = [Convert]::ToHexString($Hasher.ComputeHash([Text.Encoding]::UTF8.GetBytes(($Hashes.Values -join ':')))).ToLowerInvariant() }
        finally { $Hasher.Dispose() }
        $Bundle = Join-Path $OutputDirectory "snapshots/$Id"
        New-Item -ItemType Directory -Path (Split-Path -Parent $Bundle) -Force | Out-Null
        if (-not (Test-Path -LiteralPath $Bundle)) {
            # Move only this freshly built stage, after verifying both absolute paths.
            if (-not $Stage.StartsWith($OutputDirectory + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase) -or
                -not $Bundle.StartsWith($OutputDirectory + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) { throw 'Unsafe publication path' }
            [IO.Directory]::Move($Stage, $Bundle)
            New-Item -ItemType Directory -Path $Stage | Out-Null
        }
        foreach ($Name in $script:PublishedFiles) {
            if ((Get-FileHash -LiteralPath (Join-Path $Bundle $Name) -Algorithm SHA256).Hash.ToLowerInvariant() -cne $Hashes[$Name]) { throw "Snapshot collision: $Name" }
        }
        $Manifest = [ordered]@{
            directory = "snapshots/$Id"
            collected_at = $Summary.metadata.collected_at
            raw_sha256 = $Summary.metadata.raw_sha256
            files = $Hashes
        }
        # Check all existing targets before replacing even the first root copy.
        foreach ($Name in @($script:PublishedFiles) + @('current.json')) {
            $Target = Join-Path $OutputDirectory $Name
            if (Test-Path -LiteralPath $Target) {
                $Probe = [IO.File]::Open($Target, 'Open', 'ReadWrite', 'None')
                $Probe.Dispose()
                $Backup = Join-Path $Stage "$Name.previous"
                $BackupSource = if ($PreviousSet -and $Name -ne 'current.json') { Join-Path $PreviousSet.directory $Name } else { $Target }
                [IO.File]::Copy($BackupSource, $Backup)
                $Backups[$Name] = $Backup
            }
        }
        foreach ($Name in $script:PublishedFiles) {
            Copy-MapleFileAtomic (Join-Path $Bundle $Name) (Join-Path $OutputDirectory $Name)
            $Changed.Add($Name)
        }
        # A reader loads this single pointer once, then reads only that immutable set.
        Write-MapleJson $Manifest (Join-Path $OutputDirectory 'current.json')
    }
    catch {
        $Failure = $_
        $RollbackErrors = [System.Collections.Generic.List[string]]::new()
        for ($i = $Changed.Count - 1; $i -ge 0; $i--) {
            $Name = $Changed[$i]
            try {
                $Target = Join-Path $OutputDirectory $Name
                if ($Backups.ContainsKey($Name)) { Copy-MapleFileAtomic $Backups[$Name] $Target }
                elseif (Test-Path -LiteralPath $Target) { Remove-Item -LiteralPath $Target }
            }
            catch { $RollbackErrors.Add($Name) }
        }
        if ($RollbackErrors.Count) { Write-Warning "복사본 복구 실패: $($RollbackErrors -join ', '). current.json이 가리키는 이전 완료 묶음을 사용하세요." }
        throw $Failure
    }
    finally {
        try {
            if (Test-Path -LiteralPath $Stage) {
                $Resolved = [IO.Path]::GetFullPath($Stage)
                if (-not $Resolved.StartsWith($OutputDirectory + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) { throw 'Unsafe staging cleanup path' }
                Remove-Item -LiteralPath $Resolved -Recurse -Force
            }
        }
        finally { if ($Lock) { $Lock.Dispose() } }
    }
}

Export-ModuleMember -Function Get-MapleEndpoints,Read-MapleJson,Write-MapleJson,New-MapleSummary,New-MapleDiff,Get-MaplePublishedSet,Publish-MapleSnapshot,Get-MapleRequiredFailures,Export-MapleAIContext,New-MapleUserContext
