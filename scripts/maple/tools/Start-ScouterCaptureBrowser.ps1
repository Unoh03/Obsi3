[CmdletBinding()]
param(
    [string]$BravePath = 'C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe',
    [ValidateRange(1024,65535)][int]$Port = 9222
)
$ErrorActionPreference = 'Stop'
$MapleRoot = Split-Path -Parent $PSScriptRoot
$ProfileDir = Join-Path $MapleRoot '.runtime\brave-cdp'
if (-not (Test-Path -LiteralPath $BravePath -PathType Leaf)) { throw 'Brave executable not found.' }
if (Get-NetTCPConnection -State Listen -LocalPort $Port -ErrorAction SilentlyContinue) {
    throw "Port $Port is already in use. Inspect it before reusing; no process was stopped."
}
New-Item -ItemType Directory -Path $ProfileDir -Force | Out-Null
$BrowserArgs = @("--remote-debugging-port=$Port", '--remote-debugging-address=127.0.0.1', "--user-data-dir=`"$ProfileDir`"", '--no-first-run', '--no-default-browser-check', 'https://maplescouter.com/')
# This is the explicitly requested interactive browser, not a background helper.
$BrowserProcess = Start-Process -FilePath $BravePath -ArgumentList $BrowserArgs -WindowStyle Normal -PassThru
for ($Try = 0; $Try -lt 40; $Try++) {
    Start-Sleep -Milliseconds 250
    $Listeners = @(Get-NetTCPConnection -State Listen -LocalPort $Port -ErrorAction SilentlyContinue)
    if ($Listeners.Count -gt 0) { break }
}
if ($Listeners.Count -eq 0) { throw 'CDP listener was not observed. Inspect the new browser.' }
if (@($Listeners | Where-Object { $_.LocalAddress -notin @('127.0.0.1','::1') }).Count -gt 0) {
    Stop-Process -Id $BrowserProcess.Id -ErrorAction SilentlyContinue
    throw 'Non-loopback CDP listener detected; launched process stopped.'
}
$Record = [ordered]@{ created_at=(Get-Date).ToString('o'); launcher_pid=$BrowserProcess.Id; profile=$ProfileDir; port=$Port; listeners=@($Listeners | Select-Object LocalAddress,LocalPort,OwningProcess) }
$Record | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $MapleRoot '.runtime\browser-launch.json') -Encoding utf8
Write-Host "Brave ready. CDP: http://127.0.0.1:$Port"
Write-Host 'Use only this dedicated window for the experiment. Closing it ends remote debugging.'
