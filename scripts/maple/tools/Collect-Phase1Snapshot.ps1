[CmdletBinding()]
param([string]$CharacterName = '우노03')
$ErrorActionPreference = 'Stop'
$MapleRoot = Split-Path -Parent $PSScriptRoot
$PythonPath = Join-Path $MapleRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $PythonPath)) { throw 'Install the Phase 1 virtual environment first.' }
& (Join-Path $MapleRoot 'Get-MapleCharacterData.ps1') -CharacterName $CharacterName -NoPause
$Source = Join-Path $MapleRoot "output\$CharacterName-maple-api.json"
& (Join-Path $MapleRoot 'Build-MapleSnapshot.ps1') -SourcePath $Source
$Bundle = Join-Path $MapleRoot ('fixtures\maplescouter\nexon-' + (Get-Date -Format 'yyyyMMdd-HHmmss-fff'))
& $PythonPath (Join-Path $PSScriptRoot 'maple_phase1.py') snapshot $Source --out $Bundle
if ($LASTEXITCODE -ne 0) { throw 'Snapshot freeze failed.' }
$Bundle | Set-Content -LiteralPath (Join-Path $MapleRoot '.runtime\latest-frozen-snapshot.txt') -Encoding utf8
Write-Host 'Fresh NEXON snapshot is frozen. Tell Codex when the Scouter settings are ready.'
