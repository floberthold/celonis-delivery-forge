param(
    [string]$VaultPath = "$PSScriptRoot\my-obsidian-wiki",
    [switch]$BuildProjectBundle,
    [switch]$BuildAllBundles,
    [switch]$SkipBundleGeneration,
    [string]$ProjectQuestion = "what celonis projects do we have running at fuchs?"
)

$ErrorActionPreference = "Stop"

$obsidianRepo = Join-Path $PSScriptRoot "obsidian-llm-wiki-local"
$obsidianVenvPython = Join-Path $obsidianRepo ".venv\Scripts\python.exe"
$queryVenvPython = Join-Path $PSScriptRoot "local-llm-wiki-query\.venv\Scripts\python.exe"
$queryRepo = Join-Path $PSScriptRoot "local-llm-wiki-query"

if (-not (Test-Path $obsidianRepo)) {
    throw "Missing folder: $obsidianRepo"
}

if (-not (Test-Path $queryRepo)) {
    throw "Missing folder: $queryRepo"
}

if (-not (Test-Path $VaultPath)) {
    throw "Missing vault path: $VaultPath"
}

if (-not (Test-Path (Join-Path $VaultPath "wiki.toml"))) {
    throw "Expected wiki.toml in vault: $VaultPath"
}

if (Test-Path $obsidianVenvPython) {
    $pythonCmd = $obsidianVenvPython
} elseif (Test-Path $queryVenvPython) {
    $pythonCmd = $queryVenvPython
} else {
    $pythonCmd = "python"
}

$env:PYTHONPATH = Join-Path $obsidianRepo "src"

Write-Host "Updating wiki in: $VaultPath"
Write-Host "Using Python: $pythonCmd"
Write-Host "Showing live progress below..."

function Invoke-OlwStep {
    param(
        [string]$StepName,
        [string[]]$CliArgs
    )

    Write-Host ""
    Write-Host "=== $StepName ==="
    & $pythonCmd -u -m obsidian_llm_wiki.cli @CliArgs 2>&1 | ForEach-Object { $_ }
    if ($LASTEXITCODE -ne 0) {
        throw "Step failed: $StepName (exit code $LASTEXITCODE)"
    }
    Write-Host "=== $StepName done ==="
}

try {
    Invoke-OlwStep -StepName "Ingest" -CliArgs @("ingest", "--all", "--vault", $VaultPath)
    Invoke-OlwStep -StepName "Compile" -CliArgs @("compile", "--vault", $VaultPath)
    Invoke-OlwStep -StepName "Lint" -CliArgs @("lint", "--vault", $VaultPath)

    if ($BuildProjectBundle) {
        Write-Host ""
        Write-Host "=== Project Bundle ==="
        $env:OLW_UPDATE_VAULT = $VaultPath
        $env:OLW_UPDATE_QUERY_SRC = Join-Path $queryRepo "src"
        $env:OLW_UPDATE_QUESTION = $ProjectQuestion
        & $pythonCmd -u -c "import os, sys; from pathlib import Path; sys.path.insert(0, os.environ['OLW_UPDATE_QUERY_SRC']); from local_wiki_query.config import AppConfig; from local_wiki_query.service import KnowledgeService; vault = Path(os.environ['OLW_UPDATE_VAULT']); question = os.environ['OLW_UPDATE_QUESTION']; cfg = AppConfig(vault_path=vault, ollama_url='http://localhost:11434', fast_model='smollm2:135m', heavy_model='qwen3.6:35b-a3b', top_k=8, api_port=8008); result = KnowledgeService(cfg).answer(question, limit=8, use_ollama=False); print('Question:', question); print('Top citation:', result.citations[0].path if result.citations else '<none>')" 2>&1 | ForEach-Object { $_ }
        if ($LASTEXITCODE -ne 0) {
            throw "Step failed: Project Bundle (exit code $LASTEXITCODE)"
        }
        Write-Host "=== Project Bundle done ==="
    }

    if ($BuildAllBundles -or -not $SkipBundleGeneration) {
        Write-Host ""
        Write-Host "=== All Bundles (clients/apps/ideas) ==="
        $bundleScript = Join-Path $queryRepo "scripts\build_all_bundles.py"
        if (-not (Test-Path $bundleScript)) {
            throw "Missing script: $bundleScript"
        }
        & $pythonCmd -u $bundleScript --vault $VaultPath 2>&1 | ForEach-Object { $_ }
        if ($LASTEXITCODE -ne 0) {
            throw "Step failed: All Bundles (exit code $LASTEXITCODE)"
        }
        Write-Host "=== All Bundles done ==="
    }
} catch {
    Write-Error $_
    exit 1
}

Write-Host "Done. Wiki updated."
