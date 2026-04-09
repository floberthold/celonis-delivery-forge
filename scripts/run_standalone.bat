@echo off
setlocal
set "REPO_ROOT=%~dp0.."
set "APP=%REPO_ROOT%\dist\FoundryDesktop.exe"
set "PYW=%REPO_ROOT%\.venv\Scripts\pythonw.exe"

if exist "%APP%" (
  start "Celonis Delivery Forge" "%APP%"
  if not errorlevel 1 exit /b 0
)

if exist "%PYW%" (
  start "Celonis Delivery Forge" "%PYW%" -m foundry.desktop.app
  if not errorlevel 1 exit /b 0
)

echo [ERROR] Could not start Foundry.
echo Tried:
echo   1) %APP%
echo   2) %PYW% -m foundry.desktop.app
echo Check desktop log: %%LOCALAPPDATA%%\CelonisDeliveryForge\desktop.log
pause
exit /b 1
endlocal
