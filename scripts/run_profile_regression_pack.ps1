#Requires -Version 5.1
param(
    [string[]]$Profiles = @("pilot-core", "pilot-core-plus-knowledge", "integration-celonis", "full"),
    [string]$ReportPath = "",
    [switch]$SkipDependencyInstall,
    [switch]$SkipPytest
)

$ErrorActionPreference = "Stop"
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $repoRoot

if ($Profiles.Count -eq 1 -and $Profiles[0] -match ",") {
    $Profiles = @($Profiles[0].Split(",") | ForEach-Object { $_.Trim() } | Where-Object { -not [string]::IsNullOrWhiteSpace($_) })
}

$startScript = Join-Path $repoRoot "START.ps1"
if (-not (Test-Path $startScript)) {
    Write-Host "ERROR: START.ps1 not found at $startScript" -ForegroundColor Red
    exit 1
}

$timestamp = (Get-Date).ToUniversalTime().ToString("yyyyMMddTHHmmssZ")
if ([string]::IsNullOrWhiteSpace($ReportPath)) {
    $reportDir = Join-Path $repoRoot ".orchestration\test-runs\profile-regression"
    New-Item -ItemType Directory -Path $reportDir -Force | Out-Null
    $ReportPath = Join-Path $reportDir ("regression-pack-" + $timestamp + ".json")
}

$profileTests = @{
    "pilot-core" = @(
        "tests/test_foundry_admin_ui.py",
        "tests/test_tool_hub_profile_activation.py",
        "tests/test_tool_hub_startup_catalog.py"
    )
    "pilot-core-plus-knowledge" = @(
        "tests/test_tool_hub_profile_activation.py",
        "tests/test_tool_hub_startup_catalog.py",
        "tests/test_ui_domain_profile_gating.py"
    )
    "integration-celonis" = @(
        "tests/test_tool_hub_profile_activation.py",
        "tests/test_tool_hub_startup_catalog.py",
        "tests/test_ui_domain_profile_gating.py",
        "tests/test_celonis_data_agent_contracts.py",
        "tests/test_celonis_tool_hub_ui.py",
        "tests/test_celonis_user_token_api.py"
    )
    "full" = @(
        "tests/test_tool_hub_profile_activation.py",
        "tests/test_tool_hub_startup_catalog.py",
        "tests/test_ui_domain_profile_gating.py",
        "tests/test_celonis_data_agent_contracts.py",
        "tests/test_agentic_mcp_tools.py",
        "tests/test_mcp_stub_modules.py",
        "tests/test_celonis_tool_hub_ui.py",
        "tests/test_foundry_admin_ui.py",
        "tests/test_celonis_user_token_api.py",
        "tests/test_celonis_deployments_api.py"
    )
}

$results = @()
$overallOk = $true

foreach ($profile in $Profiles) {
    Write-Host "=== Regression pack profile: $profile ===" -ForegroundColor Cyan

    $profileResult = [ordered]@{
        profile = $profile
        dry_run_exit_code = $null
        status_exit_code = $null
        pytest_exit_code = $null
        pytest_tests = @()
        ok = $true
    }

    $dryRunArgs = @("-NoProfile", "-ExecutionPolicy", "Bypass", "-File", $startScript, "-Mode", "dry-run", "-Profile", $profile)
    if ($SkipDependencyInstall) {
        $dryRunArgs += "-SkipDependencyInstall"
    }
    & powershell.exe @dryRunArgs
    $profileResult.dry_run_exit_code = $LASTEXITCODE

    $statusArgs = @("-NoProfile", "-ExecutionPolicy", "Bypass", "-File", $startScript, "-Mode", "status", "-Profile", $profile)
    if ($SkipDependencyInstall) {
        $statusArgs += "-SkipDependencyInstall"
    }
    & powershell.exe @statusArgs
    $profileResult.status_exit_code = $LASTEXITCODE

    if (-not $SkipPytest) {
        if (-not $profileTests.Contains($profile)) {
            Write-Host "WARNING: No pytest matrix configured for profile '$profile'" -ForegroundColor Yellow
            $profileResult.pytest_exit_code = 0
        }
        else {
            $tests = @($profileTests[$profile])
            $profileResult.pytest_tests = $tests
            python -m pytest @tests -q
            $profileResult.pytest_exit_code = $LASTEXITCODE
        }
    }
    else {
        $profileResult.pytest_exit_code = 0
    }

    if (($profileResult.dry_run_exit_code -ne 0) -or ($profileResult.status_exit_code -ne 0) -or ($profileResult.pytest_exit_code -ne 0)) {
        $profileResult.ok = $false
        $overallOk = $false
    }

    $results += [pscustomobject]$profileResult
}

$report = [ordered]@{
    generated_at_utc = (Get-Date).ToUniversalTime().ToString("o")
    profiles = $Profiles
    skip_pytest = [bool]$SkipPytest
    skip_dependency_install = [bool]$SkipDependencyInstall
    overall_ok = $overallOk
    results = $results
}

$report | ConvertTo-Json -Depth 8 | Set-Content -Path $ReportPath -Encoding UTF8
Write-Host "Regression report written to: $ReportPath" -ForegroundColor Gray

if ($overallOk) {
    exit 0
}
exit 1
