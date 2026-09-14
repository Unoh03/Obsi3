@echo off
setlocal
cd /d "%~dp0"

where pwsh.exe >nul 2>&1 || goto :missing_pwsh

chcp 65001 >nul
pwsh.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0Get-MapleCharacterData.ps1" -NoPause
if errorlevel 1 goto :collector_failed

pwsh.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0Build-MapleSnapshot.ps1"
if errorlevel 1 goto :snapshot_failed

echo.
echo Maple API collection and snapshot build completed.
pause
exit /b 0

:collector_failed
echo.
echo Maple API collector failed.
pause
exit /b 1

:snapshot_failed
echo.
echo Maple snapshot build failed.
pause
exit /b 1

:missing_pwsh
echo PowerShell 7 pwsh.exe was not found in PATH.
echo Install PowerShell 7 or add pwsh.exe to PATH.
echo.
pause
exit /b 1
