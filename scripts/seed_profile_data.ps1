#Requires -Version 5.1
param(
    [Parameter(Mandatory = $true)]
    [string]$Profile,
    [string]$PlanPath = ".\config\profile_seed_plan.json",
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $repoRoot

$planAbsolutePath = Join-Path $repoRoot $PlanPath
if (-not (Test-Path $planAbsolutePath)) {
    Write-Host "ERROR: seed plan not found at $planAbsolutePath" -ForegroundColor Red
    exit 1
}

$plan = Get-Content -Path $planAbsolutePath -Raw | ConvertFrom-Json
if ($null -eq $plan -or $null -eq $plan.profiles) {
    Write-Host "ERROR: invalid seed plan format" -ForegroundColor Red
    exit 1
}

$profilePlan = $plan.profiles.$Profile
if ($null -eq $profilePlan) {
    Write-Host "ERROR: profile '$Profile' not found in seed plan" -ForegroundColor Red
    exit 1
}

$commands = @($profilePlan.commands)
Write-Host "Profile seed strategy" -ForegroundColor Cyan
Write-Host "Profile: $Profile" -ForegroundColor Gray
Write-Host "Description: $($profilePlan.description)" -ForegroundColor Gray
Write-Host "Plan: $PlanPath" -ForegroundColor Gray

if ($commands.Count -eq 0) {
    Write-Host "No seed commands configured for this profile." -ForegroundColor Yellow
    exit 0
}

foreach ($command in $commands) {
    if ([string]::IsNullOrWhiteSpace([string]$command)) {
        continue
    }

    Write-Host "Seed step: $command" -ForegroundColor Cyan
    if ($DryRun) {
        continue
    }

    & powershell.exe -NoProfile -ExecutionPolicy Bypass -Command $command
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: seed step failed: $command" -ForegroundColor Red
        exit $LASTEXITCODE
    }
}

Write-Host "Profile seed run complete." -ForegroundColor Green
exit 0
