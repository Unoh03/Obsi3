@echo off
chcp 65001 >nul
where pwsh.exe >nul 2>&1
if errorlevel 1 (
    echo PowerShell 7.5 or newer is required.
    pause
    exit /b 1
)
pwsh.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0Collect-Djmax.ps1"
if errorlevel 1 (
    echo DJMAX collection failed. The prior published snapshot should remain available.
    pause
    exit /b 1
)
echo.
pause
