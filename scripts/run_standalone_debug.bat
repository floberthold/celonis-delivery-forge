@echo off
setlocal
set "REPO_ROOT=%~dp0.."
set "EXE_PATH=%REPO_ROOT%\dist\FoundryDesktop.exe"
set "PY=%REPO_ROOT%\.venv\Scripts\python.exe"

if exist "%EXE_PATH%" (
  echo Starting "%EXE_PATH%" in this console...
  "%EXE_PATH%"
  echo.
  echo Process exited with code %ERRORLEVEL%.
  if "%ERRORLEVEL%"=="0" goto :done
)

if exist "%PY%" (
  echo EXE path failed or returned non-zero. Falling back to Python module run.
  "%PY%" -m foundry.desktop.app
  echo.
  echo Python fallback exited with code %ERRORLEVEL%.
  goto :done
)

echo [ERROR] Could not launch Foundry.
echo Missing EXE and python fallback unavailable.
echo Check desktop log: %%LOCALAPPDATA%%\CelonisDeliveryForge\desktop.log

:done
pause
endlocal
