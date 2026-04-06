$ErrorActionPreference = "Stop"

python -m venv venv
& venv\Scripts\Activate.ps1
pip install -r requirements.txt
playwright install chromium

if (-not (Test-Path .env)) {
    Copy-Item .env.example .env
    Write-Host "Created .env from .env.example - fill in your credentials."
} else {
    Write-Host ".env already exists, skipping."
}

if (-not (Test-Path run.ps1)) {
    Copy-Item run.ps1.example run.ps1
    Write-Host "Created run.ps1 from run.ps1.example - adjust if needed."
} else {
    Write-Host "run.ps1 already exists, skipping."
}

Write-Host "Done! Edit .env, then run .\run.ps1"
