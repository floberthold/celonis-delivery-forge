#Requires -Version 5.1
param(
    [ValidateSet("start", "start-fast", "status", "stop-all", "reset", "repo-cleanup-scan", "repo-cleanup-clean", "test-smoke", "test-celonis", "test-all", "lint")]
    [string]$Action = "start",
    [switch]$SkipDependencyInstall
)

$ErrorActionPreference = "Stop"

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$startScript = Join-Path $repoRoot "START.ps1"
$cleanupScript = Join-Path $repoRoot "scripts\repo_cleanup.ps1"

if (-not (Test-Path $startScript)) {
    Write-Host "ERROR: START.ps1 not found. Run from repository context." -ForegroundColor Red
    exit 1
}

function Invoke-StartScript {
    param(
        [string]$Mode,
        [switch]$SkipDependencies
    )

    $args = @("-NoProfile", "-ExecutionPolicy", "Bypass", "-File", $startScript, "-Mode", $Mode)
    if ($SkipDependencies) {
        $args += "-SkipDependencyInstall"
    }

    & powershell.exe @args
    return $LASTEXITCODE
}

function Stop-ForgeProcesses {
    param([string]$RepoPath)

    $killed = @()
    $candidates = Get-CimInstance Win32_Process | Where-Object {
        ($_.Name -match "^(python|python3|pythonw|uvicorn|powershell|cmd)\\.exe$") -and
        ($_.CommandLine -match "foundry\\.api\\.main:app|START\\.ps1|start_tool_hub\\.ps1|foundry\\.desktop\\.app") -and
        ($_.CommandLine -match [regex]::Escape($RepoPath))
    }

    foreach ($proc in $candidates) {
        try {
            Stop-Process -Id $proc.ProcessId -Force -ErrorAction Stop
            $killed += [pscustomobject]@{
                pid = $proc.ProcessId
                name = $proc.Name
            }
        }
        catch {
            Write-Host "WARN: Could not stop PID $($proc.ProcessId): $($_.Exception.Message)" -ForegroundColor Yellow
        }
    }

    return $killed
}

function Show-ForgeStatus {
    param([string]$RepoPath)

    $statePath = Join-Path $RepoPath ".orchestration\tool-hub\state.json"
    if (-not (Test-Path $statePath)) {
        Write-Host "Tool hub state file not found: $statePath" -ForegroundColor Yellow
        return
    }

    $raw = Get-Content -Path $statePath -Raw
    if ([string]::IsNullOrWhiteSpace($raw)) {
        Write-Host "Tool hub state file is empty." -ForegroundColor Yellow
        return
    }

    $state = $raw | ConvertFrom-Json
    $tools = @($state.tools)
    if ($tools.Count -eq 0) {
        Write-Host "No running tool processes recorded." -ForegroundColor Yellow
        return
    }

    $rows = @()
    foreach ($tool in $tools) {
        $proc = Get-Process -Id $tool.pid -ErrorAction SilentlyContinue
        $rows += [pscustomobject]@{
            id = $tool.id
            pid = $tool.pid
            running = ($null -ne $proc)
            repo_path = $tool.repo_path
            log_file = $tool.log_file
        }
    }

    $rows | Format-Table -AutoSize
}

Push-Location $repoRoot
try {
    switch ($Action) {
        "start" {
            $exitCode = Invoke-StartScript -Mode "hub" -SkipDependencies:$SkipDependencyInstall
            exit $exitCode
        }
        "start-fast" {
            $exitCode = Invoke-StartScript -Mode "api-fast" -SkipDependencies:$SkipDependencyInstall
            exit $exitCode
        }
        "status" {
            Show-ForgeStatus -RepoPath $repoRoot
            exit 0
        }
        "stop-all" {
            $stopExitCode = Invoke-StartScript -Mode "stop"
            $killed = Stop-ForgeProcesses -RepoPath $repoRoot

            if ($killed.Count -eq 0) {
                Write-Host "No additional Forge processes found." -ForegroundColor Gray
            }
            else {
                Write-Host "Stopped additional Forge processes:" -ForegroundColor Cyan
                $killed | Format-Table -AutoSize
            }

            exit $stopExitCode
        }
        "reset" {
            $stopExitCode = Invoke-StartScript -Mode "stop"
            $killed = Stop-ForgeProcesses -RepoPath $repoRoot
            if ($killed.Count -eq 0) {
                Write-Host "No additional Forge processes found." -ForegroundColor Gray
            }
            else {
                Write-Host "Stopped additional Forge processes:" -ForegroundColor Cyan
                $killed | Format-Table -AutoSize
            }

            if (Test-Path $cleanupScript) {
                powershell.exe -NoProfile -ExecutionPolicy Bypass -File $cleanupScript -Mode scan
            }

            exit $stopExitCode
        }
        "repo-cleanup-scan" {
            if (-not (Test-Path $cleanupScript)) {
                Write-Host "ERROR: repo_cleanup.ps1 not found." -ForegroundColor Red
                exit 1
            }
            powershell.exe -NoProfile -ExecutionPolicy Bypass -File $cleanupScript -Mode scan
            exit $LASTEXITCODE
        }
        "repo-cleanup-clean" {
            if (-not (Test-Path $cleanupScript)) {
                Write-Host "ERROR: repo_cleanup.ps1 not found." -ForegroundColor Red
                exit 1
            }
            powershell.exe -NoProfile -ExecutionPolicy Bypass -File $cleanupScript -Mode clean
            exit $LASTEXITCODE
        }
        "test-smoke" {
            python -m pytest tests/test_celonis_user_token_api.py tests/test_celonis_ui_route_presence.py -q
            exit $LASTEXITCODE
        }
        "test-celonis" {
            python -m pytest tests/test_celonis_user_token_api.py tests/test_celonis_tool_hub_ui.py -q
            exit $LASTEXITCODE
        }
        "test-all" {
            python -m pytest tests -q
            exit $LASTEXITCODE
        }
        "lint" {
            python -m ruff check src tests
            exit $LASTEXITCODE
        }
    }
}
finally {
    Pop-Location
}
