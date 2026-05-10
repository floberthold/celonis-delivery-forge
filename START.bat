@echo off
setlocal

if not exist "START.ps1" (
    echo ERROR: START.ps1 not found in current directory.
    exit /b 1
)

powershell -NoProfile -ExecutionPolicy Bypass -File ".\START.ps1" %*
set "EC=%ERRORLEVEL%"

endlocal & exit /b %EC%
