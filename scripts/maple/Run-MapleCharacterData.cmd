@echo off
setlocal
cd /d "%~dp0"

where pwsh >nul 2>&1
if errorlevel 1 (
    echo PowerShell 7 (pwsh) was not found in PATH.
    echo Install PowerShell 7 or add pwsh.exe to PATH.
    echo.
    pause
    exit /b 1
)

chcp 65001 >nul
pwsh.exe -NoLogo -NoProfile -NoExit -ExecutionPolicy Bypass -File "%~dp0Get-MapleCharacterData.ps1" -NoPause
