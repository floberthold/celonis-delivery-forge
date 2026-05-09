#Requires -Version 5.0
<#
.SYNOPSIS
    Easy startup script for Celonis Delivery Forge
.DESCRIPTION
    Installs dependencies (if needed) and starts the API server with auto-reload.
    The UI dashboard will be available at http://127.0.0.1:8000
#>

Write-Host "================================" -ForegroundColor Cyan
Write-Host "Celonis Delivery Forge - Startup" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

# Check if running from the correct directory
if (-not (Test-Path ".\pyproject.toml")) {
    Write-Host "ERROR: Please run this script from the project root directory" -ForegroundColor Red
    exit 1
}

# Step 1: Install dependencies (if not already installed)
Write-Host "Step 1: Checking dependencies..." -ForegroundColor Yellow
$foundryInstalled = python -c "import foundry" 2>&1 | Select-String "ModuleNotFoundError"

if ($foundryInstalled) {
    Write-Host "  Installing packages (this may take a minute)..." -ForegroundColor Gray
    python -m pip install -q --upgrade pip 2>&1 | Out-Null
    python -m pip install -q -e . 2>&1 | Out-Null
    Write-Host "  ✓ Dependencies installed" -ForegroundColor Green
}
else {
    Write-Host "  ✓ Dependencies already installed" -ForegroundColor Green
}

# Step 2: Start the server
Write-Host ""
Write-Host "Step 2: Starting API server..." -ForegroundColor Yellow
Write-Host "  Server starting on http://127.0.0.1:8000" -ForegroundColor Gray
Write-Host "  Press Ctrl+C to stop the server" -ForegroundColor Gray
Write-Host ""

uvicorn foundry.api.main:app --reload --host 127.0.0.1 --port 8000
