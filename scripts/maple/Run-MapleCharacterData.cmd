@echo off
setlocal
cd /d "%~dp0"

where pwsh >nul 2>&1
if errorlevel 1 (
    echo PowerShell 7 ^(pwsh^)을 찾을 수 없습니다.
    echo PowerShell 7 설치 또는 PATH 등록 상태를 확인하세요.
    echo.
    pause
    exit /b 1
)

pwsh -NoProfile -ExecutionPolicy Bypass -File "%~dp0Get-MapleCharacterData.ps1" -NoPause
set "EXIT_CODE=%ERRORLEVEL%"

echo.
if not "%EXIT_CODE%"=="0" (
    echo 실행이 오류 코드 %EXIT_CODE%로 종료되었습니다.
)

pause
exit /b %EXIT_CODE%
