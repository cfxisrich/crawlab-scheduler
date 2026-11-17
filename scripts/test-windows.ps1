#Requires -Version 7.4
param([string]$Python = "python")

$ErrorActionPreference = "Stop"
$PSNativeCommandUseErrorActionPreference = $true
Set-Location (Split-Path $PSScriptRoot -Parent)
& $Python -c "import sys; assert sys.version_info[:2] == (3, 12), 'Use Python 3.12 for this project'"
& $Python -m venv .venv
& .\.venv\Scripts\python.exe -m pip install -r backend/requirements-dev.txt
Push-Location backend
& ..\.venv\Scripts\python.exe -m pytest -q
Pop-Location
& .\.venv\Scripts\python.exe -m unittest discover -s examples -p 'test_*.py' -v
$env:FLOWHARBOR_PYTHON = (Resolve-Path .venv/Scripts/python.exe).Path
Push-Location frontend
pnpm install --frozen-lockfile
pnpm build
pnpm exec playwright install chromium
pnpm exec playwright test
Pop-Location
Write-Host "Windows source and browser checks passed. Engine acceptance is separate: docs/windows.md"
