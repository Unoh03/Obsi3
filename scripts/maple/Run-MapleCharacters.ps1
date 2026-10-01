#requires -Version 7.5
[CmdletBinding()]
param([string]$OutputRoot = (Join-Path $PSScriptRoot 'output'))
$ErrorActionPreference = 'Stop'
Import-Module (Join-Path $PSScriptRoot 'MapleBatch.psm1') -Force
try {
    $Report = Invoke-MapleCharacterBatch -OutputRoot $OutputRoot
    exit $Report.exit_code
}
catch {
    Write-Error $_ -ErrorAction Continue
    exit 1
}
