#requires -Version 7.0

[CmdletBinding()]
param(
    [switch]$CheckWorkingTree,
    [switch]$Json
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$scriptPath = Join-Path $PSScriptRoot "verify_mentor_note_append_only.py"
$argsList = @($scriptPath)

if ($CheckWorkingTree) {
    $argsList += "--check-working-tree"
}
if ($Json) {
    $argsList += "--json"
}

& python @argsList
exit $LASTEXITCODE
