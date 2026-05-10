param(
    [string]$BindHost = "127.0.0.1",
    [int]$Port = 3000,
    [string]$ApiBaseUrl = "http://127.0.0.1:8008/v1",
    [string]$ApiKey = "ollama"
)

$ErrorActionPreference = "Stop"

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $repoRoot

$env:OPENAI_API_BASE_URL = $ApiBaseUrl
$env:OPENAI_API_KEY = $ApiKey

if (Get-Command open-webui -ErrorAction SilentlyContinue) {
    Write-Host "Starting Open WebUI from PATH on http://${BindHost}:$Port"
    open-webui serve --host $BindHost --port $Port
    exit $LASTEXITCODE
}

$candidateExe = Join-Path $repoRoot "external resources\local-knowledge-model\local-llm-wiki-query\.venv\Scripts\open-webui.exe"
if (Test-Path $candidateExe) {
    Write-Host "Starting Open WebUI from local-wiki-query virtual environment on http://${BindHost}:$Port"
    & $candidateExe serve --host $BindHost --port $Port
    exit $LASTEXITCODE
}

Write-Error "Open WebUI is not installed. Install it with: python -m pip install open-webui"
exit 1
