#Requires -Version 5.1
param(
    [ValidateSet("scan", "clean")]
    [string]$Mode = "scan",
    [switch]$IncludeLogs,
    [switch]$IncludeExternalResources
)

$ErrorActionPreference = "Stop"

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path

$excludedSegments = @(
    "\\.git\\",
    "\\external resources\\",
    "\\docs_site\\",
    "\\build\\",
    "\\dist\\"
)

if ($IncludeExternalResources) {
    $excludedSegments = $excludedSegments | Where-Object { $_ -ne "\\external resources\\" }
}

function Should-IncludePath {
    param([string]$FullPath)

    foreach ($segment in $excludedSegments) {
        if ($FullPath -like "*$segment*") {
            return $false
        }
    }
    return $true
}

$matches = @()

function Add-ItemIfIncluded {
    param([string]$FullPath)

    if (-not (Test-Path $FullPath)) {
        return
    }
    if (-not (Should-IncludePath -FullPath $FullPath)) {
        return
    }
    $script:matches += Get-Item -Path $FullPath -Force
}

function Add-CandidatePath {
    param([string]$Path)

    if (-not (Test-Path $Path)) {
        return
    }
    $resolved = (Resolve-Path $Path).Path
    if (Should-IncludePath -FullPath $resolved) {
        $script:matches += Get-Item -Path $resolved -Force
    }
}

$scanRoots = @(
    (Join-Path $repoRoot "src"),
    (Join-Path $repoRoot "tests"),
    (Join-Path $repoRoot "scripts"),
    (Join-Path $repoRoot "agentic")
) | Where-Object { Test-Path $_ }

foreach ($root in $scanRoots) {
    $cacheDirs = Get-ChildItem -Path $root -Directory -Filter "__pycache__" -Recurse -Force -ErrorAction SilentlyContinue
    foreach ($item in $cacheDirs) {
        if (Should-IncludePath -FullPath $item.FullName) {
            $script:matches += $item
        }
    }

    $compiledFiles = Get-ChildItem -Path $root -File -Recurse -Force -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -like "*.pyc" -or $_.Name -like "tmp_*.db" -or $_.Name -like "tmp_*_test.db" }
    foreach ($item in $compiledFiles) {
        if (Should-IncludePath -FullPath $item.FullName) {
            $script:matches += $item
        }
    }
}

Add-CandidatePath -Path (Join-Path $repoRoot ".pytest_cache")

if ($IncludeLogs) {
    $logsDir = Join-Path $repoRoot ".orchestration\tool-hub\logs"
    if (Test-Path $logsDir) {
        $logItems = Get-ChildItem -Path $logsDir -File -Filter "*.log" -Force -ErrorAction SilentlyContinue
        foreach ($item in $logItems) {
            if (Should-IncludePath -FullPath $item.FullName) {
                $script:matches += $item
            }
        }
    }
}

# De-duplicate by full path.
$matches = $matches | Sort-Object -Property FullName -Unique

if ($matches.Count -eq 0) {
    Write-Host "No cleanup candidates found." -ForegroundColor Green
    exit 0
}

$rows = @()
foreach ($item in $matches) {
    $rows += [pscustomobject]@{
        type = if ($item.PSIsContainer) { "dir" } else { "file" }
        size_kb = if ($item.PSIsContainer) { "-" } else { [Math]::Round($item.Length / 1KB, 1) }
        path = $item.FullName.Replace($repoRoot + "\\", "")
    }
}

Write-Host "Cleanup candidates ($($rows.Count))" -ForegroundColor Cyan
$rows | Format-Table -AutoSize

if ($Mode -eq "scan") {
    Write-Host "Scan only. Re-run with -Mode clean to delete listed files/folders." -ForegroundColor Yellow
    exit 0
}

$deleted = 0
foreach ($item in $matches | Sort-Object -Property FullName -Descending) {
    try {
        Remove-Item -Path $item.FullName -Recurse -Force -ErrorAction Stop
        $deleted += 1
    }
    catch {
        Write-Host "WARN: Could not remove $($item.FullName): $($_.Exception.Message)" -ForegroundColor Yellow
    }
}

Write-Host "Cleanup completed. Removed items: $deleted" -ForegroundColor Green
exit 0
