#Requires -Version 5.1
param(
    [ValidateSet("hub", "api-only", "api-fast", "status", "stop", "dry-run")]
    [string]$Mode = "hub",
    [string]$Profile = "full",
    [switch]$IncludeAutoDiscovered,
    [switch]$SkipDependencyInstall
)

Write-Host "================================" -ForegroundColor Cyan
Write-Host "Celonis Delivery Forge - Startup" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

if (-not (Test-Path ".\pyproject.toml")) {
    Write-Host "ERROR: Please run this script from the project root directory" -ForegroundColor Red
    exit 1
}

if ($Mode -eq "api-only" -or $Mode -eq "api-fast") {
    Write-Host "Mode: $Mode" -ForegroundColor Yellow
    if (-not $SkipDependencyInstall) {
        Write-Host "Checking dependencies..." -ForegroundColor Yellow
        $foundryInstalled = python -c "import foundry" 2>&1 | Select-String "ModuleNotFoundError"

        if ($foundryInstalled) {
            Write-Host "  Installing packages (this may take a minute)..." -ForegroundColor Gray
            python -m pip install -q --upgrade pip 2>&1 | Out-Null
            python -m pip install -q -e . 2>&1 | Out-Null
            Write-Host "  Dependencies installed" -ForegroundColor Green
        }
        else {
            Write-Host "  Dependencies already installed" -ForegroundColor Green
        }
    }
    else {
        Write-Host "Skipping dependency installation checks" -ForegroundColor Gray
    }

    Write-Host ""
    Write-Host "Starting API server on http://127.0.0.1:8000" -ForegroundColor Yellow
    $env:PYTHONPATH = "src"

    if ($Mode -eq "api-fast") {
        # Fast mode avoids file-watch reload overhead for quicker cold starts.
        python -m uvicorn foundry.api.main:app --host 127.0.0.1 --port 8000
    }
    else {
        python -m uvicorn foundry.api.main:app --reload --host 127.0.0.1 --port 8000
    }
    exit $LASTEXITCODE
}

$hubScript = ".\agentic\tool-hub\start_tool_hub.ps1"
if (-not (Test-Path $hubScript)) {
    Write-Host "ERROR: Tool hub script not found at $hubScript" -ForegroundColor Red
    exit 1
}

$hubMode = switch ($Mode) {
    "status" { "status" }
    "stop" { "stop" }
    "dry-run" { "dry-run" }
    default { "start" }
}

Write-Host "Mode: tool hub ($hubMode)" -ForegroundColor Yellow

$hubArgs = @(
    "-NoProfile",
    "-ExecutionPolicy", "Bypass",
    "-File", $hubScript,
    "-Mode", $hubMode,
    "-Profile", $Profile
)

if ($IncludeAutoDiscovered) {
    $hubArgs += "-IncludeAutoDiscovered"
}

if ($SkipDependencyInstall) {
    $hubArgs += "-SkipDependencyInstall"
}

& powershell.exe @hubArgs
exit $LASTEXITCODE
