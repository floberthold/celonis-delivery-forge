$ErrorActionPreference = "Stop"

python -m pip install --upgrade pip
python -m pip install .

Write-Host "Starting Celonis Delivery Forge desktop mode..."
python -m foundry.desktop.app
