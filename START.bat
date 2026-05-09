@echo off
setlocal enabledelayedexpansion

echo.
echo ================================
echo Celonis Delivery Forge - Startup
echo ================================
echo.

REM Check if running from correct directory
if not exist "pyproject.toml" (
    echo ERROR: Please run this script from the project root directory
    pause
    exit /b 1
)

REM Step 1: Install dependencies
echo Step 1: Checking dependencies...
python -c "import foundry" >nul 2>&1
if errorlevel 1 (
    echo   Installing packages (this may take a minute)...
    python -m pip install -q --upgrade pip >nul 2>&1
    python -m pip install -q -e . >nul 2>&1
    echo   [OK] Dependencies installed
) else (
    echo   [OK] Dependencies already installed
)

REM Step 2: Start the server
echo.
echo Step 2: Starting API server...
echo   Server starting on http://127.0.0.1:8000
echo   Press Ctrl+C to stop the server
echo.

uvicorn foundry.api.main:app --reload --host 127.0.0.1 --port 8000

endlocal
