param(
    [string]$VaultPath = "",
    [string]$Host = "127.0.0.1",
    [int]$Port = 8008,
    [string]$FastModel = "",
    [string]$HeavyModel = ""
)

$ErrorActionPreference = "Stop"

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $repoRoot

$querySrcPath = Join-Path $repoRoot "external resources\local-knowledge-model\local-llm-wiki-query\src"
if (-not (Test-Path $querySrcPath)) {
    throw "Local wiki query source folder not found at: $querySrcPath"
}

if ([string]::IsNullOrWhiteSpace($VaultPath)) {
    $VaultPath = Join-Path $repoRoot "external resources\local-knowledge-model\my-obsidian-wiki"
}

if (-not (Test-Path $VaultPath)) {
    throw "Vault path not found: $VaultPath"
}

$env:LWQ_VAULT_PATH = (Resolve-Path $VaultPath).Path
$env:LWQ_API_PORT = [string]$Port

if (-not [string]::IsNullOrWhiteSpace($FastModel)) {
    $env:LWQ_FAST_MODEL = $FastModel
}
if (-not [string]::IsNullOrWhiteSpace($HeavyModel)) {
    $env:LWQ_HEAVY_MODEL = $HeavyModel
}

Write-Host "Starting local knowledge gateway..."
Write-Host "  LWQ_VAULT_PATH=$env:LWQ_VAULT_PATH"
Write-Host "  Host=$Host Port=$Port"

python -m uvicorn local_wiki_query.api:create_app --factory --host $Host --port $Port --app-dir "$querySrcPath"
