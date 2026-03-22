[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$UpstreamUrl,

    [Parameter(Mandatory = $true)]
    [ValidatePattern('^[a-zA-Z0-9._-]+$')]
    [string]$Name,

    [string]$Branch = 'main',
    [string]$VendorRoot = 'vendor'
)

$ErrorActionPreference = 'Stop'

function Invoke-Git {
    param(
        [Parameter(Mandatory = $true)]
        [string[]]$Args
    )

    & git @Args
    if ($LASTEXITCODE -ne 0) {
        throw "git command failed: git $($Args -join ' ')"
    }
}

if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    throw 'git is required but was not found in PATH.'
}

$repoRoot = (& git rev-parse --show-toplevel 2>$null)
if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($repoRoot)) {
    throw 'Run this script inside a git repository.'
}

Push-Location $repoRoot
try {
    $vendorPathRelative = Join-Path $VendorRoot $Name
    $vendorPathAbsolute = Join-Path $repoRoot $vendorPathRelative

    if (-not (Test-Path $VendorRoot)) {
        New-Item -ItemType Directory -Path $VendorRoot | Out-Null
    }

    if (Test-Path $vendorPathAbsolute) {
        throw "Target path already exists: $vendorPathRelative"
    }

    Invoke-Git -Args @('submodule', 'add', '--name', $Name, '--branch', $Branch, $UpstreamUrl, $vendorPathRelative)
    Invoke-Git -Args @('submodule', 'update', '--init', '--recursive', '--', $vendorPathRelative)

    $upstreamCommit = (& git -C $vendorPathAbsolute rev-parse HEAD).Trim()
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to resolve submodule commit for $vendorPathRelative"
    }

    $metadataDir = Join-Path $repoRoot '.upstreams'
    if (-not (Test-Path $metadataDir)) {
        New-Item -ItemType Directory -Path $metadataDir | Out-Null
    }

    $patchesRoot = Join-Path $repoRoot 'patches'
    if (-not (Test-Path $patchesRoot)) {
        New-Item -ItemType Directory -Path $patchesRoot | Out-Null
    }

    $patchDir = Join-Path $patchesRoot $Name
    if (-not (Test-Path $patchDir)) {
        New-Item -ItemType Directory -Path $patchDir | Out-Null
    }

    $metadataPath = Join-Path $metadataDir "$Name.json"
    $metadata = [ordered]@{
        name = $Name
        upstream_url = $UpstreamUrl
        tracked_branch = $Branch
        submodule_path = ($vendorPathRelative -replace '\\', '/')
        baseline_commit = $upstreamCommit
        added_utc = [DateTime]::UtcNow.ToString('o')
        patch_directory = ("patches/$Name")
    }
    ($metadata | ConvertTo-Json -Depth 4) | Set-Content -Path $metadataPath -Encoding UTF8

    Write-Host "Added submodule $Name at $vendorPathRelative" -ForegroundColor Green
    Write-Host "Baseline commit: $upstreamCommit"
    Write-Host "Metadata: $($metadataPath.Replace($repoRoot + '\\', ''))"
    Write-Host "Patch queue: patches/$Name"
    Write-Host ''
    Write-Host 'Recommended next steps:'
    Write-Host '1) Keep upstream code in the submodule untouched.'
    Write-Host "2) Place Forge-specific adapters in src/ that call into $vendorPathRelative."
    Write-Host "3) If a direct upstream patch is unavoidable, store patch files in patches/$Name."
    Write-Host "4) Commit .gitmodules, the gitlink, and .upstreams/$Name.json together."
}
finally {
    Pop-Location
}
