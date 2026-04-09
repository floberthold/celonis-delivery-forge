[CmdletBinding()]
param(
    [ValidateSet('status', 'init', 'pull', 'push')]
    [string]$Mode = 'status',

    [switch]$Recursive
)

$ErrorActionPreference = 'Stop'

function Invoke-Git {
    param(
        [Parameter(Mandatory = $true)]
        [string[]]$Args,
        [string]$WorkingDirectory = $null
    )

    if ([string]::IsNullOrWhiteSpace($WorkingDirectory)) {
        & git @Args
    }
    else {
        & git -C $WorkingDirectory @Args
    }

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

$targets = @(
    [pscustomobject]@{
        Name = 'pyCelonis-tools'
        Path = 'external resources/Code by Florian/pyCelonis-tools'
        Branch = 'main'
    },
    [pscustomobject]@{
        Name = 'pyCelonis-for-Fuchs'
        Path = 'external resources/Code by Florian/pyCelonis%20-%20for%20Fuchs'
        Branch = 'main'
    },
    [pscustomobject]@{
        Name = 'pyCelonis-OCPM-migration-tool'
        Path = 'external resources/Code by Florian/pyCelonis%20-%20OCPM%20migration%20tool'
        Branch = 'main'
    }
)

Push-Location $repoRoot
try {
    if ($Mode -eq 'init') {
        foreach ($target in $targets) {
            Write-Host "Initializing $($target.Path)"
            Invoke-Git -Args @('submodule', 'update', '--init', '--', $target.Path)
            if ($Recursive) {
                Invoke-Git -Args @('submodule', 'update', '--init', '--recursive', '--', $target.Path)
            }
        }
        Write-Host 'Submodule init complete.' -ForegroundColor Green
        return
    }

    if ($Mode -eq 'status') {
        foreach ($target in $targets) {
            $absPath = Join-Path $repoRoot $target.Path
            Write-Host "`n=== $($target.Name) ==="
            if (-not (Test-Path $absPath)) {
                Write-Host "Missing path: $($target.Path)" -ForegroundColor Yellow
                continue
            }

            $head = (& git -C $absPath rev-parse --short HEAD).Trim()
            if ($LASTEXITCODE -ne 0) {
                throw "Unable to resolve HEAD for $($target.Path)"
            }

            $branch = (& git -C $absPath branch --show-current).Trim()
            $dirty = (& git -C $absPath status --short)
            $remote = (& git -C $absPath remote get-url origin).Trim()

            Write-Host "Path:    $($target.Path)"
            Write-Host "Branch:  $branch"
            Write-Host "HEAD:    $head"
            Write-Host "Origin:  $remote"
            if ($dirty) {
                Write-Host 'State:   dirty' -ForegroundColor Yellow
                $dirty | ForEach-Object { Write-Host "  $_" }
            }
            else {
                Write-Host 'State:   clean' -ForegroundColor Green
            }
        }
        return
    }

    foreach ($target in $targets) {
        $absPath = Join-Path $repoRoot $target.Path
        if (-not (Test-Path $absPath)) {
            throw "Missing path: $($target.Path). Run with -Mode init first."
        }

        Write-Host "`n=== $($target.Name) ($Mode) ==="

        if ($Mode -eq 'pull') {
            Invoke-Git -Args @('fetch', 'origin') -WorkingDirectory $absPath
            Invoke-Git -Args @('checkout', $target.Branch) -WorkingDirectory $absPath
            Invoke-Git -Args @('pull', '--ff-only', 'origin', $target.Branch) -WorkingDirectory $absPath
            if ($Recursive) {
                Invoke-Git -Args @('submodule', 'update', '--init', '--recursive') -WorkingDirectory $absPath
            }
        }
        elseif ($Mode -eq 'push') {
            $dirty = (& git -C $absPath status --short)
            if ($dirty) {
                Write-Host "Cannot push $($target.Path): working tree is dirty." -ForegroundColor Yellow
                $dirty | ForEach-Object { Write-Host "  $_" }
                continue
            }
            Invoke-Git -Args @('push', 'origin', 'HEAD') -WorkingDirectory $absPath
        }
    }

    Write-Host "`nCompleted mode '$Mode'." -ForegroundColor Green
    if ($Mode -eq 'pull') {
        Write-Host 'If HEAD changed in submodules, commit the updated gitlinks in the parent repository.'
    }
}
finally {
    Pop-Location
}
