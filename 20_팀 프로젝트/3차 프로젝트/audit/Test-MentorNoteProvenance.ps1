#requires -Version 7.0

[CmdletBinding()]
param(
    [string]$ManifestPath = "20_팀 프로젝트/3차 프로젝트/audit/8.19-mentor-note-provenance.json",
    [switch]$WriteGenerated
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Invoke-GitText {
    param([Parameter(Mandatory)][string[]]$Arguments)

    $output = & git @Arguments 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "git $($Arguments -join ' ') failed:`n$($output -join [Environment]::NewLine)"
    }
    return (($output -join "`n").Trim())
}

function Export-GitBlob {
    param(
        [Parameter(Mandatory)][string]$BlobSha,
        [Parameter(Mandatory)][string]$Destination
    )

    $psi = [System.Diagnostics.ProcessStartInfo]::new()
    $psi.FileName = "git"
    $psi.UseShellExecute = $false
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError = $true
    [void]$psi.ArgumentList.Add("cat-file")
    [void]$psi.ArgumentList.Add("blob")
    [void]$psi.ArgumentList.Add($BlobSha)

    $process = [System.Diagnostics.Process]::Start($psi)
    if ($null -eq $process) {
        throw "Failed to start git cat-file."
    }

    $stream = [System.IO.File]::Create($Destination)
    try {
        $process.StandardOutput.BaseStream.CopyTo($stream)
    }
    finally {
        $stream.Dispose()
    }

    $stderr = $process.StandardError.ReadToEnd()
    $process.WaitForExit()
    if ($process.ExitCode -ne 0) {
        throw "git cat-file blob $BlobSha failed: $stderr"
    }
}

function Get-TextSha256 {
    param([Parameter(Mandatory)][string]$Text)

    $bytes = [System.Text.Encoding]::UTF8.GetBytes($Text)
    $hash = [System.Security.Cryptography.SHA256]::HashData($bytes)
    return [Convert]::ToHexString($hash).ToLowerInvariant()
}

function Add-MarkdownBlock {
    param(
        [Parameter(Mandatory)][System.Collections.Generic.List[string]]$Buffer,
        [Parameter(Mandatory)][int]$Start,
        [Parameter(Mandatory)][int]$End,
        [Parameter(Mandatory)][ref]$Counter,
        [Parameter(Mandatory)][System.Collections.Generic.List[object]]$Output
    )

    if ($Buffer.Count -eq 0) { return }

    $textValue = ($Buffer -join "`n").TrimEnd([char[]]"`r`n")
    if ([string]::IsNullOrWhiteSpace($textValue)) {
        $Buffer.Clear()
        return
    }

    $Counter.Value++
    $first = $Buffer[0].TrimStart()
    $type = if ($first -match '^#{1,6}\s') {
        'heading-section'
    }
    elseif ($first -match '^```|^~~~') {
        'fenced-code'
    }
    elseif ($first -match '^>\s?\[!') {
        'callout'
    }
    elseif ($first -match '^\|') {
        'table'
    }
    elseif ($first -match '^[-*+]\s|^\d+\.\s') {
        'list'
    }
    else {
        'paragraph'
    }

    $Output.Add([ordered]@{
        id = ('O-{0:d4}' -f $Counter.Value)
        start_line = $Start
        end_line = $End
        type = $type
        canonical_text_sha256 = Get-TextSha256 -Text $textValue
        first_line = $Buffer[0].TrimEnd("`r")
    })
    $Buffer.Clear()
}

function Get-MarkdownBlocks {
    param([Parameter(Mandatory)][string]$Text)

    $lines = [regex]::Split($Text, "`n")
    $blocks = [System.Collections.Generic.List[object]]::new()
    $current = [System.Collections.Generic.List[string]]::new()
    $counter = 0
    $startLine = 1
    $inFence = $false

    for ($i = 0; $i -lt $lines.Count; $i++) {
        $lineNumber = $i + 1
        $line = $lines[$i].TrimEnd("`r")
        $isFence = $line -match '^\s*(```|~~~)'
        $isHeading = (-not $inFence) -and ($line -match '^#{1,6}\s')
        $isBlank = (-not $inFence) -and [string]::IsNullOrWhiteSpace($line)

        if ($isHeading -and $current.Count -gt 0) {
            Add-MarkdownBlock -Buffer $current -Start $startLine -End ($lineNumber - 1) -Counter ([ref]$counter) -Output $blocks
            $startLine = $lineNumber
        }

        if ($isBlank) {
            if ($current.Count -gt 0) {
                Add-MarkdownBlock -Buffer $current -Start $startLine -End ($lineNumber - 1) -Counter ([ref]$counter) -Output $blocks
            }
            $startLine = $lineNumber + 1
            continue
        }

        if ($current.Count -eq 0) {
            $startLine = $lineNumber
        }
        $current.Add($line)

        if ($isFence) {
            $inFence = -not $inFence
            if (-not $inFence) {
                Add-MarkdownBlock -Buffer $current -Start $startLine -End $lineNumber -Counter ([ref]$counter) -Output $blocks
                $startLine = $lineNumber + 1
            }
        }
    }

    if ($current.Count -gt 0) {
        Add-MarkdownBlock -Buffer $current -Start $startLine -End $lines.Count -Counter ([ref]$counter) -Output $blocks
    }

    return $blocks
}

$repoRoot = Invoke-GitText -Arguments @("rev-parse", "--show-toplevel")
Push-Location $repoRoot
try {
    if (-not (Test-Path -LiteralPath $ManifestPath -PathType Leaf)) {
        throw "Manifest not found: $ManifestPath"
    }

    $manifest = Get-Content -Raw -LiteralPath $ManifestPath -Encoding UTF8 | ConvertFrom-Json -Depth 100
    $checks = [System.Collections.Generic.List[object]]::new()
    $failures = [System.Collections.Generic.List[string]]::new()

    function Add-Check {
        param(
            [Parameter(Mandatory)][string]$Name,
            [Parameter(Mandatory)][bool]$Passed,
            [Parameter(Mandatory)][string]$Detail
        )
        $checks.Add([ordered]@{ name = $Name; passed = $Passed; detail = $Detail })
        if (-not $Passed) { $failures.Add("$Name :: $Detail") }
    }

    $sourceSpec = "{0}:{1}" -f $manifest.source.commit, $manifest.source.path
    $sourceBlob = Invoke-GitText -Arguments @("rev-parse", $sourceSpec)
    Add-Check -Name "source blob pin" -Passed ($sourceBlob -eq $manifest.source.expected_git_blob_sha1) -Detail "actual=$sourceBlob expected=$($manifest.source.expected_git_blob_sha1)"

    $preservedSpec = "HEAD:{0}" -f $manifest.preserved_copy.path
    $preservedBlob = Invoke-GitText -Arguments @("rev-parse", $preservedSpec)
    Add-Check -Name "preserved blob equals source" -Passed ($preservedBlob -eq $sourceBlob) -Detail "source=$sourceBlob preserved=$preservedBlob"

    $sourceTemp = Join-Path ([System.IO.Path]::GetTempPath()) ("mentor-note-source-{0}.md" -f [guid]::NewGuid())
    $preservedTemp = Join-Path ([System.IO.Path]::GetTempPath()) ("mentor-note-preserved-{0}.md" -f [guid]::NewGuid())
    try {
        Export-GitBlob -BlobSha $sourceBlob -Destination $sourceTemp
        Export-GitBlob -BlobSha $preservedBlob -Destination $preservedTemp

        $sourceSha256 = (Get-FileHash -LiteralPath $sourceTemp -Algorithm SHA256).Hash.ToLowerInvariant()
        $preservedSha256 = (Get-FileHash -LiteralPath $preservedTemp -Algorithm SHA256).Hash.ToLowerInvariant()
        Add-Check -Name "source and preserved SHA-256" -Passed ($sourceSha256 -eq $preservedSha256) -Detail "source=$sourceSha256 preserved=$preservedSha256"

        $sourceText = [System.IO.File]::ReadAllText($sourceTemp, [System.Text.UTF8Encoding]::new($false))
        $blocks = @(Get-MarkdownBlocks -Text $sourceText)
        Add-Check -Name "source block manifest generated" -Passed ($blocks.Count -gt 0) -Detail "blocks=$($blocks.Count)"
    }
    finally {
        Remove-Item -LiteralPath $sourceTemp, $preservedTemp -Force -ErrorAction SilentlyContinue
    }

    & git diff --quiet -- $manifest.preserved_copy.path
    $preservedWorkingTreeClean = ($LASTEXITCODE -eq 0)
    Add-Check -Name "preserved source working tree clean" -Passed $preservedWorkingTreeClean -Detail "unstaged_change=$(-not $preservedWorkingTreeClean)"

    & git diff --cached --quiet -- $manifest.preserved_copy.path
    $preservedIndexClean = ($LASTEXITCODE -eq 0)
    Add-Check -Name "preserved source index clean" -Passed $preservedIndexClean -Detail "staged_change=$(-not $preservedIndexClean)"

    foreach ($view in $manifest.derived_views) {
        $viewSpec = "HEAD:{0}" -f $view.path
        $actualBlob = Invoke-GitText -Arguments @("rev-parse", $viewSpec)
        Add-Check -Name "derived view blob pin: $($view.path)" -Passed ($actualBlob -eq $view.expected_git_blob_sha1) -Detail "actual=$actualBlob expected=$($view.expected_git_blob_sha1)"

        & git diff --quiet -- $view.path
        $workingTreeClean = ($LASTEXITCODE -eq 0)
        Add-Check -Name "derived view working tree clean: $($view.path)" -Passed $workingTreeClean -Detail "unstaged_change=$(-not $workingTreeClean)"

        & git diff --cached --quiet -- $view.path
        $indexClean = ($LASTEXITCODE -eq 0)
        Add-Check -Name "derived view index clean: $($view.path)" -Passed $indexClean -Detail "staged_change=$(-not $indexClean)"
    }

    $actualIds = @($manifest.corrections | ForEach-Object { $_.id } | Sort-Object)
    $expectedIds = @(1..16 | ForEach-Object { 'C{0:d2}' -f $_ })
    $idSetPassed = (($actualIds -join ',') -eq ($expectedIds -join ','))
    Add-Check -Name "correction ID set C01-C16" -Passed $idSetPassed -Detail "actual=$($actualIds -join ',')"

    $duplicateIds = @($manifest.corrections | Group-Object id | Where-Object Count -ne 1)
    Add-Check -Name "correction IDs unique" -Passed ($duplicateIds.Count -eq 0) -Detail "duplicates=$($duplicateIds.Name -join ',')"

    foreach ($correction in $manifest.corrections) {
        foreach ($anchor in $correction.anchors) {
            if (-not (Test-Path -LiteralPath $anchor.path -PathType Leaf)) {
                Add-Check -Name "anchor $($correction.id)" -Passed $false -Detail "missing file: $($anchor.path)"
                continue
            }
            $content = Get-Content -Raw -LiteralPath $anchor.path -Encoding UTF8
            $found = $content.Contains([string]$anchor.contains, [System.StringComparison]::Ordinal)
            Add-Check -Name "anchor $($correction.id): $($anchor.path)" -Passed $found -Detail "contains=$($anchor.contains)"
        }
    }

    $result = [ordered]@{
        schema_version = 1
        checked_at_utc = [DateTime]::UtcNow.ToString('o')
        repository = $manifest.repository
        head = Invoke-GitText -Arguments @("rev-parse", "HEAD")
        source_blob_sha1 = $sourceBlob
        preserved_blob_sha1 = $preservedBlob
        source_sha256 = $sourceSha256
        preserved_sha256 = $preservedSha256
        source_block_count = $blocks.Count
        checks = $checks
        failures = $failures
        passed = ($failures.Count -eq 0)
    }

    if ($WriteGenerated) {
        $generatedDir = Join-Path (Split-Path -Parent $ManifestPath) "generated"
        New-Item -ItemType Directory -Path $generatedDir -Force | Out-Null

        $blockManifest = [ordered]@{
            schema_version = 1
            source_commit = $manifest.source.commit
            source_path = $manifest.source.path
            source_blob_sha1 = $sourceBlob
            source_sha256 = $sourceSha256
            block_hash_definition = "UTF-8 of block text joined with LF; full byte identity is verified separately"
            blocks = $blocks
        }
        $blockManifest | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath (Join-Path $generatedDir "8.19-original-blocks.json") -Encoding UTF8
        $result | ConvertTo-Json -Depth 30 | Set-Content -LiteralPath (Join-Path $generatedDir "8.19-provenance-result.json") -Encoding UTF8
    }

    $result | ConvertTo-Json -Depth 30
    if (-not $result.passed) {
        exit 1
    }
}
finally {
    Pop-Location
}
