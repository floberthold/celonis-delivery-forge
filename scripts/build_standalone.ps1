$ErrorActionPreference = "Stop"

$venvPython = Join-Path $PSScriptRoot "..\.venv\Scripts\python.exe"
$fallbackPython = Join-Path $env:LOCALAPPDATA "Microsoft\WindowsApps\python.exe"

if (Test-Path $venvPython) {
  $python = $venvPython
} else {
  $python = $fallbackPython
}

& $python -m pip install --upgrade pip
& $python -m pip install pyinstaller
& $python -m pip install -e .

if (Test-Path "dist") { Remove-Item "dist" -Recurse -Force }
if (Test-Path "build") { Remove-Item "build" -Recurse -Force }

& $python -m PyInstaller `
  --noconfirm `
  --clean `
  --name "FoundryDesktop" `
  --onefile `
  --windowed `
  --add-data "docu;docu" `
  --collect-submodules fastapi `
  --collect-submodules starlette `
  --collect-submodules uvicorn `
  --collect-submodules sqlmodel `
  --collect-submodules sqlalchemy `
  --collect-submodules pydantic `
  --hidden-import foundry.api.main `
  --hidden-import foundry.desktop.app `
  src/foundry/desktop/app.py

Write-Host "Standalone build created: dist/FoundryDesktop.exe"
