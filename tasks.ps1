# Windows tasks (PowerShell 5.1). Run from rms-bearing root.
# Usage: powershell -ExecutionPolicy Bypass -File tasks.ps1 setup
param([string]$Task = "help")
switch ($Task) {
  "setup" { pip install -e ".[dev]"; Copy-Item ".env.example" ".env" -ErrorAction SilentlyContinue }
  "test" { pytest -q }
  "lint" { ruff check src pipelines tests }
  "extract-37282" { python pipelines/01_extract_windows.py --loco 37282 --start "2024-12-03 05:00:00" --end "2024-12-10 05:00:00" }
  default { Write-Host "tasks: setup | test | lint | extract-37282" }
}
