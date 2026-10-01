@echo off
setlocal
cd /d "%~dp0"

where pwsh.exe >nul 2>&1 || goto :missing_pwsh

chcp 65001 >nul
pwsh.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0Run-MapleCharacters.ps1"
if errorlevel 1 goto :batch_failed

echo.
echo Maple API collection and snapshot build completed.
echo Give the dated JSON path shown above to your AI chat.
pause
exit /b 0

:batch_failed
echo.
echo Some characters failed or have incomplete data. Check the per-character results above.
pause
exit /b 1

:missing_pwsh
echo PowerShell 7 pwsh.exe was not found in PATH.
echo Install PowerShell 7 or add pwsh.exe to PATH.
echo.
pause
exit /b 1
