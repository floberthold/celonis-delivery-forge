#Requires -Version 5.1
param(
    [ValidateSet("start", "dry-run", "status", "stop")]
    [string]$Mode = "start",
    [string]$RegistryPath = ".\agentic\tool-hub\tool_hub_registry.json",
    [switch]$IncludeAutoDiscovered,
    [switch]$SkipDependencyInstall
)

$targetScript = Join-Path $PSScriptRoot "..\agentic\tool-hub\start_tool_hub.ps1"
if (-not (Test-Path $targetScript)) {
    Write-Host "ERROR: Target tool hub script not found at $targetScript" -ForegroundColor Red
    exit 1
}

$args = @(
    "-NoProfile",
    "-ExecutionPolicy", "Bypass",
    "-File", $targetScript,
    "-Mode", $Mode,
    "-RegistryPath", $RegistryPath
)

if ($IncludeAutoDiscovered) {
    $args += "-IncludeAutoDiscovered"
}

if ($SkipDependencyInstall) {
    $args += "-SkipDependencyInstall"
}

& powershell.exe @args
exit $LASTEXITCODE
