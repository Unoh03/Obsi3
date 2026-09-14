@echo off
setlocal
cd /d "%~dp0"

where pwsh.exe >nul 2>&1 || goto :missing_pwsh

chcp 65001 >nul
pwsh.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0Get-MapleCharacterData.ps1" -PauseOnExit
set "EXIT_CODE=%ERRORLEVEL%"

if "%EXIT_CODE%"=="0" exit /b 0

echo.
echo PowerShell exited with code %EXIT_CODE%.
pause
exit /b %EXIT_CODE%

:missing_pwsh
echo PowerShell 7 pwsh.exe was not found in PATH.
echo Install PowerShell 7 or add pwsh.exe to PATH.
echo.
pause
exit /b 1
