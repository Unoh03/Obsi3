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
            # Descriptions may contain gameplay effects, so preserve them.
            if ($Key -match '(^|_)(icon|image)$' -or $Key -in @('item_shape','item_shape_name','medal_shape') -or
                $Key -match '^((world_share_)?pet_[123])_appearance$') { continue }
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
        $Dates[$Section] = $InputSection.date
        $Value = Remove-MaplePresentation $InputSection
        if ($Value -is [System.Collections.IDictionary]) {
            $Value.Remove('date')
            if ($Section -ne 'basic') { $Value.Remove('character_class'); $Value.Remove('character_gender') }
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
                foreach ($Row in $InputSection.final_stat) {
                    if (-not $Row.stat_name -or $Stats.Contains($Row.stat_name)) { throw 'final_stat에 이름 누락/중복이 있습니다. 원본 확인 필요.' }
                    $Stats[$Row.stat_name] = $Row.stat_value
                }
                $Value.Remove('final_stat')
                $Value.values = $Stats
            }
        }
        $Actual[$Section] = $Value
    }
    return [ordered]@{
        schema_version = 3
        metadata = [ordered]@{
            character_name = $Data.metadata.character_name
            collected_at = $Data.metadata.collected_at
            collection_finished_at = $Data.metadata.collection_finished_at
            source = $Data.metadata.source
            source_url = $Data.metadata.source_url
        }
        reading_guide = @(
            'NEXON API가 반환한 캐릭터 상태입니다. 실시간 접속 상태나 환산 결과를 뜻하지 않습니다.',
            'actual.stat.values는 API의 최종 스탯입니다. 장비/링크/유니온 효과를 여기에 다시 더하지 마세요.',
            '미수집/실패/불완전(partial)은 quality에 표시하며 0 또는 미장착으로 해석하지 않습니다. date=null이면 데이터 기준 시각 미확인입니다.',
            'actual은 현재 상태, presets는 저장된 대안 설정입니다. presets는 API 섹션/원래 필드명으로 찾으며 번호·남은 포인트·null·빈 배열도 보존합니다. 보스용/사냥용이라는 용도는 임의로 추정하지 마세요.',
            '이미지 URL·외형 필드는 생략했습니다. 현재 상태와 저장 프리셋의 수치·옵션·효과·설명·null·0·배열 순서는 보존하며 전체 응답은 raw에 있습니다.',
            '숫자처럼 보이는 문자열도 API 타입 그대로입니다. diff는 정상 수집된 섹션만 비교하며 변화의 원인을 단정하지 않습니다.'
        )
        quality = [ordered]@{
            section_status = $States
            unavailable_sections = @($Unavailable.ToArray())
            errors = $Errors
            validation_issues = $ValidationIssues
            data_dates = $Dates
        }
        actual = $Actual
        presets = $Presets
    }
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

Export-ModuleMember -Function Get-MapleEndpoints,Read-MapleJson,Write-MapleJson,New-MapleSummary,New-MapleDiff,Get-MaplePublishedSet,Publish-MapleSnapshot
