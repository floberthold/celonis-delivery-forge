#Requires -Version 5.1
param(
    [ValidateSet("start", "dry-run", "status", "stop")]
    [string]$Mode = "start",
    [string]$RegistryPath = ".\agentic\tool-hub\tool_hub_registry.json",
    [string]$ProfilesPath = ".\agentic\tool-hub\tool_hub_profiles.json",
    [string]$Profile = "full",
    [switch]$IncludeAutoDiscovered,
    [switch]$SkipDependencyInstall
)

$ErrorActionPreference = "Stop"

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$registryAbsolutePath = Join-Path $repoRoot $RegistryPath
$profilesAbsolutePath = Join-Path $repoRoot $ProfilesPath
$runtimeRoot = Join-Path $repoRoot ".orchestration\tool-hub"
$statePath = Join-Path $runtimeRoot "state.json"
$catalogPath = Join-Path $runtimeRoot "catalog.json"
$logRoot = Join-Path $runtimeRoot "logs"

function Ensure-Directory {
    param([string]$Path)
    if (-not (Test-Path $Path)) {
        New-Item -ItemType Directory -Path $Path -Force | Out-Null
    }
}

function Read-Json {
    param([string]$Path)
    if (-not (Test-Path $Path)) {
        return $null
    }
    return Get-Content -Path $Path -Raw | ConvertFrom-Json
}

function Write-Json {
    param(
        [Parameter(Mandatory = $true)]$InputObject,
        [Parameter(Mandatory = $true)][string]$Path
    )
    $InputObject | ConvertTo-Json -Depth 12 | Set-Content -Path $Path -Encoding UTF8
}

function Get-SubmodulePaths {
    $gitmodulesPath = Join-Path $repoRoot ".gitmodules"
    if (-not (Test-Path $gitmodulesPath)) {
        return @()
    }

    $paths = @()
    foreach ($line in (Get-Content -Path $gitmodulesPath)) {
        if ($line -match "^\s*path\s*=\s*(.+?)\s*$") {
            $paths += $matches[1].Trim()
        }
    }
    return $paths
}

function Get-RelativePath {
    param([string]$AbsolutePath)
    $uriRoot = New-Object System.Uri(($repoRoot.TrimEnd('\\') + "\\"))
    $uriTarget = New-Object System.Uri($AbsolutePath)
    $relative = $uriRoot.MakeRelativeUri($uriTarget).ToString()
    return [System.Uri]::UnescapeDataString($relative).Replace("/", "\\")
}

function New-AutoTool {
    param(
        [string]$Id,
        [string]$DisplayName,
        [string]$RepoPath,
        [string]$Shell,
        [string]$Command,
        [string]$Source,
        [string]$Notes
    )

    return [pscustomobject]@{
        id = $Id
        display_name = $DisplayName
        repo_path = $RepoPath
        shell = $Shell
        command = $Command
        enabled = $false
        install_editable = $false
        health_probe = [pscustomobject]@{ type = "process" }
        source = $Source
        notes = $Notes
    }
}

function Get-AutoDiscoveredTools {
    $auto = @()
    $repoPaths = @(".") + (Get-SubmodulePaths)

    foreach ($repoPath in $repoPaths) {
        $absoluteRepoPath = Join-Path $repoRoot $repoPath
        if (-not (Test-Path $absoluteRepoPath)) {
            continue
        }

        if ($repoPath -eq ".") {
            continue
        }

        $repoName = Split-Path $absoluteRepoPath -Leaf
        $repoRelativePath = $repoPath

        $startPs1 = Join-Path $absoluteRepoPath "START.ps1"
        if (Test-Path $startPs1) {
            $toolId = "auto-" + (($repoName -replace "[^A-Za-z0-9]+", "-").Trim("-").ToLower()) + "-start-ps1"
            $auto += New-AutoTool -Id $toolId -DisplayName "$repoName START.ps1" -RepoPath $repoRelativePath -Shell "powershell" -Command ".\\START.ps1" -Source "auto-start-script" -Notes "Auto-discovered START.ps1 script."
        }

        $startBat = Join-Path $absoluteRepoPath "START.bat"
        if (Test-Path $startBat) {
            $toolId = "auto-" + (($repoName -replace "[^A-Za-z0-9]+", "-").Trim("-").ToLower()) + "-start-bat"
            $auto += New-AutoTool -Id $toolId -DisplayName "$repoName START.bat" -RepoPath $repoRelativePath -Shell "cmd" -Command "call START.bat" -Source "auto-start-script" -Notes "Auto-discovered START.bat script."
        }

        $manifestPath = Join-Path $absoluteRepoPath "tools_manifest.json"
        $mcpServerModulePath = Join-Path $absoluteRepoPath "celonis_data_agent\server.py"
        if ((Test-Path $manifestPath) -and (Test-Path $mcpServerModulePath)) {
            $toolId = "auto-" + (($repoName -replace "[^A-Za-z0-9]+", "-").Trim("-").ToLower()) + "-mcp-server"
            $auto += New-AutoTool -Id $toolId -DisplayName "$repoName MCP server" -RepoPath $repoRelativePath -Shell "powershell" -Command "python -m celonis_data_agent.server" -Source "auto-mcp-manifest" -Notes "Auto-discovered from tools_manifest.json and server module."
        }
    }

    return $auto
}

function Resolve-ToolPath {
    param($Tool)
    $path = Join-Path $repoRoot $Tool.repo_path
    if (Test-Path $path) {
        return (Resolve-Path $path).Path
    }
    return $null
}

function Get-ToolCatalog {
    $registry = Read-Json -Path $registryAbsolutePath
    if ($null -eq $registry) {
        throw "Registry file not found: $registryAbsolutePath"
    }

    $profilesConfig = Read-Json -Path $profilesAbsolutePath
    $selectedProfile = $null
    if ($null -ne $profilesConfig -and $profilesConfig.PSObject.Properties.Name -contains "profiles") {
        $selectedProfile = @($profilesConfig.profiles) | Where-Object { $_.id -eq $Profile } | Select-Object -First 1
        if ($null -eq $selectedProfile) {
            throw "Profile '$Profile' not found in $profilesAbsolutePath"
        }
    }

    $manualTools = @($registry.tools)
    $autoTools = @()
    if ($IncludeAutoDiscovered) {
        $autoTools = @(Get-AutoDiscoveredTools)
    }

    $catalog = @()
    foreach ($tool in $manualTools + $autoTools) {
        $toolPath = Resolve-ToolPath -Tool $tool
        $startable = ($null -ne $toolPath) -and (-not [string]::IsNullOrWhiteSpace($tool.command))
        $domain = if ($tool.PSObject.Properties.Name -contains "domain") { $tool.domain } else { "unassigned" }

        $profileAllowsTool = $true
        if ($null -ne $selectedProfile) {
            $includeDomains = @()
            $includeToolIds = @()
            $excludeToolIds = @()

            if ($selectedProfile.PSObject.Properties.Name -contains "include_domains") {
                $includeDomains = @($selectedProfile.include_domains)
            }
            if ($selectedProfile.PSObject.Properties.Name -contains "include_tool_ids") {
                $includeToolIds = @($selectedProfile.include_tool_ids)
            }
            if ($selectedProfile.PSObject.Properties.Name -contains "exclude_tool_ids") {
                $excludeToolIds = @($selectedProfile.exclude_tool_ids)
            }

            $allowsAllDomains = $includeDomains -contains "*"
            $domainAllowed = $allowsAllDomains -or ($includeDomains.Count -eq 0) -or ($includeDomains -contains $domain)
            $explicitToolIncluded = ($includeToolIds -contains $tool.id)
            $toolExcluded = ($excludeToolIds -contains $tool.id)

            $profileAllowsTool = ($domainAllowed -or $explicitToolIncluded) -and (-not $toolExcluded)
        }

        $enabled = [bool]$tool.enabled -and $profileAllowsTool

        $catalog += [pscustomobject]@{
            id = $tool.id
            display_name = $tool.display_name
            repo_path = $tool.repo_path
            absolute_repo_path = $toolPath
            domain = $domain
            shell = $tool.shell
            command = $tool.command
            enabled = $enabled
            install_editable = [bool]$tool.install_editable
            startable = $startable
            source = if ($tool.PSObject.Properties.Name -contains "source") { $tool.source } else { "registry" }
            notes = $tool.notes
            health_probe = $tool.health_probe
        }
    }

    return $catalog
}

function Install-EditableIfConfigured {
    param($Tool)
    if ($SkipDependencyInstall) {
        return
    }

    if (-not $Tool.install_editable) {
        return
    }

    $pyprojectPath = Join-Path $Tool.absolute_repo_path "pyproject.toml"
    if (-not (Test-Path $pyprojectPath)) {
        return
    }

    Write-Host "Installing editable package for $($Tool.id)..." -ForegroundColor Yellow
    Push-Location $Tool.absolute_repo_path
    try {
        python -m pip install -q -e .
        if ($LASTEXITCODE -ne 0) {
            throw "pip install failed for $($Tool.id)"
        }
    }
    finally {
        Pop-Location
    }
}

function Start-Tool {
    param($Tool)

    if (-not $Tool.startable) {
        return [pscustomobject]@{
            id = $Tool.id
            status = "skipped"
            reason = "not-startable"
            pid = $null
            log_file = $null
        }
    }

    if (-not $Tool.enabled) {
        return [pscustomobject]@{
            id = $Tool.id
            status = "skipped"
            reason = "disabled"
            pid = $null
            log_file = $null
        }
    }

    Install-EditableIfConfigured -Tool $Tool

    $safeId = ($Tool.id -replace "[^A-Za-z0-9._-]", "_")
    $logFile = Join-Path $logRoot "$safeId.log"

    if (Test-Path $logFile) {
        try {
            Remove-Item -Path $logFile -Force -ErrorAction Stop
        } catch {
            # If log file is locked by another process, append a separator and continue
            # This happens when the previous process is still running and has the log file open
            Add-Content -Path $logFile -Value "`n================================ NEW SESSION ================================`n" -ErrorAction SilentlyContinue
        }
    }

    $process = $null
    if ($Tool.shell -eq "powershell") {
        $wrappedCommand = "& { $($Tool.command) } *>> '$logFile'"
        $process = Start-Process -FilePath "powershell.exe" -ArgumentList @("-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", $wrappedCommand) -WorkingDirectory $Tool.absolute_repo_path -PassThru
    }
    elseif ($Tool.shell -eq "cmd") {
        $cmdLine = "$($Tool.command) >> `"$logFile`" 2>&1"
        $process = Start-Process -FilePath "cmd.exe" -ArgumentList @("/c", $cmdLine) -WorkingDirectory $Tool.absolute_repo_path -PassThru
    }
    else {
        return [pscustomobject]@{
            id = $Tool.id
            status = "failed"
            reason = "unsupported-shell"
            pid = $null
            log_file = $null
        }
    }

    return [pscustomobject]@{
        id = $Tool.id
        status = "started"
        reason = ""
        pid = $process.Id
        log_file = $logFile
    }
}

function Get-State {
    $state = Read-Json -Path $statePath
    if ($null -eq $state) {
        return [pscustomobject]@{
            started_at_utc = $null
            tools = @()
        }
    }
    return $state
}

function Save-State {
    param($State)
    Write-Json -InputObject $State -Path $statePath
}

Ensure-Directory -Path $runtimeRoot
Ensure-Directory -Path $logRoot

$catalog = Get-ToolCatalog
Write-Json -InputObject ([pscustomobject]@{
    generated_at_utc = (Get-Date).ToUniversalTime().ToString("o")
    mode = $Mode
    profile = $Profile
    include_auto_discovered = [bool]$IncludeAutoDiscovered
    tools = $catalog
}) -Path $catalogPath

if ($Mode -eq "dry-run") {
    Write-Host "Tool Hub dry-run complete." -ForegroundColor Cyan
    Write-Host "Catalog written to: $catalogPath" -ForegroundColor Gray
    Write-Host "Profile: $Profile" -ForegroundColor Gray
    $catalog |
        Select-Object id, domain, enabled, startable, source, repo_path |
        Format-Table -AutoSize
    exit 0
}

if ($Mode -eq "status") {
    $state = Get-State
    if ($state.tools.Count -eq 0) {
        Write-Host "No running state found." -ForegroundColor Yellow
        Write-Host "State path: $statePath" -ForegroundColor Gray
        exit 0
    }

    $rows = @()
    foreach ($tool in $state.tools) {
        $proc = Get-Process -Id $tool.pid -ErrorAction SilentlyContinue
        $rows += [pscustomobject]@{
            id = $tool.id
            pid = $tool.pid
            running = ($null -ne $proc)
            log_file = $tool.log_file
        }
    }
    $rows | Format-Table -AutoSize
    exit 0
}

if ($Mode -eq "stop") {
    $state = Get-State
    if ($state.tools.Count -eq 0) {
        Write-Host "No running tool processes recorded." -ForegroundColor Yellow
        exit 0
    }

    foreach ($tool in $state.tools) {
        $proc = Get-Process -Id $tool.pid -ErrorAction SilentlyContinue
        if ($null -ne $proc) {
            Stop-Process -Id $tool.pid -Force
            Write-Host "Stopped $($tool.id) (PID $($tool.pid))" -ForegroundColor Green
        }
        else {
            Write-Host "Already stopped: $($tool.id) (PID $($tool.pid))" -ForegroundColor Gray
        }
    }

    Save-State -State ([pscustomobject]@{
        started_at_utc = $null
        tools = @()
    })
    exit 0
}

$results = @()
foreach ($tool in $catalog) {
    $results += Start-Tool -Tool $tool
}

$startedTools = @()
foreach ($result in $results) {
    if ($result.status -eq "started") {
        $toolInfo = $catalog | Where-Object { $_.id -eq $result.id } | Select-Object -First 1
        $startedTools += [pscustomobject]@{
            id = $result.id
            pid = $result.pid
            repo_path = $toolInfo.repo_path
            log_file = $result.log_file
        }
    }
}

Save-State -State ([pscustomobject]@{
    started_at_utc = (Get-Date).ToUniversalTime().ToString("o")
    tools = $startedTools
})

Write-Host "Tool Hub startup summary" -ForegroundColor Cyan
$results | Select-Object id, status, reason, pid | Format-Table -AutoSize
Write-Host "Catalog: $catalogPath" -ForegroundColor Gray
Write-Host "State:   $statePath" -ForegroundColor Gray
Write-Host "Logs:    $logRoot" -ForegroundColor Gray