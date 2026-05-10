param(
    [string]$BindHost = "127.0.0.1",
    [int]$Port = 3000,
    [string]$ApiBaseUrl = "http://127.0.0.1:8008/v1",
    [string]$ApiKey = "ollama"
)

$ErrorActionPreference = "Stop"

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $repoRoot

$parsedApiBaseUrl = $null
if (-not [System.Uri]::TryCreate($ApiBaseUrl, [System.UriKind]::Absolute, [ref]$parsedApiBaseUrl)) {
    throw "ApiBaseUrl must be an absolute URL. Received: $ApiBaseUrl"
}
$apiHost = ""
if ($parsedApiBaseUrl -and $parsedApiBaseUrl.Host) {
    $apiHost = $parsedApiBaseUrl.Host.ToLowerInvariant()
}
$isLocalApiHost = @("localhost", "127.0.0.1", "::1") -contains $apiHost
if (-not $isLocalApiHost) {
    throw "ApiBaseUrl must target a local endpoint for sensitive local wiki usage. Received host: $apiHost"
}

$openWebUiDataDir = Join-Path $repoRoot ".orchestration\open-webui\data"
New-Item -ItemType Directory -Path $openWebUiDataDir -Force | Out-Null

$env:OPENAI_API_BASE_URL = $ApiBaseUrl
$env:OPENAI_API_KEY = $ApiKey
$env:DATA_DIR = $openWebUiDataDir
$env:FROM_INIT_PY = "true"
$env:ENABLE_PERSISTENT_CONFIG = "false"
$env:ENABLE_OPENAI_API = "true"
$env:ENABLE_OLLAMA_API = "false"
$env:DEFAULT_MODELS = "local-wiki-query/smollm2:135m"
$env:OLLAMA_BASE_URL = ""
$env:OLLAMA_BASE_URLS = ""

$openWebUiLaunch = ""
$openWebUiExecutable = ""
$siblingPython = Resolve-Path (Join-Path $repoRoot "external resources\local-knowledge-model\obsidian-llm-wiki-local\.venv\Scripts\python.exe") -ErrorAction SilentlyContinue

if (Get-Command open-webui -ErrorAction SilentlyContinue) {
    $openWebUiLaunch = "open-webui"
}
elseif ($siblingPython) {
    $openWebUiLaunch = "sibling-python"
}
else {
    $candidateExecutables = @()

    $localWikiQueryVenvExe = Join-Path $repoRoot "external resources\local-knowledge-model\local-llm-wiki-query\.venv\Scripts\open-webui.exe"
    if (Test-Path $localWikiQueryVenvExe) {
        $candidateExecutables += $localWikiQueryVenvExe
    }

    $obsidianWikiVenvExe = Join-Path $repoRoot "external resources\local-knowledge-model\obsidian-llm-wiki-local\.venv\Scripts\open-webui.exe"
    if (Test-Path $obsidianWikiVenvExe) {
        $candidateExecutables += $obsidianWikiVenvExe
    }

    if ($candidateExecutables.Count -gt 0) {
        $openWebUiLaunch = "exe-path"
        $openWebUiExecutable = ($candidateExecutables | Select-Object -First 1)
    }
}

if (-not $openWebUiLaunch) {
    Write-Error "Open WebUI is not installed or not available in PATH. Install it with: python -m pip install open-webui"
    exit 1
}

if ($openWebUiLaunch -eq "open-webui") {
    Write-Host "Starting Open WebUI from PATH on http://${BindHost}:$Port"
    open-webui serve --host $BindHost --port $Port
    exit $LASTEXITCODE
}

if ($openWebUiLaunch -eq "sibling-python") {
    $siblingPythonPath = $siblingPython.Path
    Write-Host "Starting Open WebUI from obsidian-llm-wiki-local virtual environment on http://${BindHost}:$Port"
    $pythonCode = @"
import sys
import open_webui
sys.argv = ['open-webui', 'serve', '--host', '$BindHost', '--port', '$Port']
open_webui.app()
"@
    & $siblingPythonPath -c $pythonCode
    exit $LASTEXITCODE
}

Write-Host "Starting Open WebUI from executable on http://${BindHost}:$Port"
& $openWebUiExecutable serve --host $BindHost --port $Port
exit $LASTEXITCODE
