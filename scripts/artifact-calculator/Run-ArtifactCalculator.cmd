@echo off
setlocal
chcp 65001 >nul
set "PYTHONUTF8=1"
if not exist "%~dp0.venv\Scripts\python.exe" goto :missing
"%~dp0.venv\Scripts\python.exe" "%~dp0calculator.py" %*
set "calculator_exit=%errorlevel%"
if "%calculator_exit%"=="0" exit /b 0
echo.
echo Exit code: %calculator_exit%. See the message above.
pause
exit /b %calculator_exit%
:missing
echo Local Python environment is missing. Follow README.md setup instructions.
pause
exit /b 1
