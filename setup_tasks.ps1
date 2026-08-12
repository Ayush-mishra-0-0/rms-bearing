$ErrorActionPreference = 'Stop'
# Installs two Windows scheduled tasks:
#   RMS_Monitor_Watch  -> every 5 minutes (data-flow alerts)
#   RMS_Monitor_Daily  -> daily 08:00 (deep report + optional digest email)
# Run from an elevated PowerShell:  powershell -ExecutionPolicy Bypass -File setup_tasks.ps1

$repo = (Resolve-Path (Join-Path $PSScriptRoot '.')).Path
$py = (Get-Command python -ErrorAction SilentlyContinue).Source
if (-not $py) { throw "python not found on PATH" }

function New-Task($name, $argsLine, $schedule) {
    $cmd = "cmd /c `"cd /d `"$repo`" && `"$py`" -m monitoring.$argsLine`""
    schtasks /Create /F /TN $name /TR $cmd $schedule | Out-Null
    Write-Output "created: $name  ->  python -m monitoring.$argsLine"
}

New-Task "RMS_Monitor_Watch" "watch"    "/SC MINUTE /MO 5"
New-Task "RMS_Monitor_Daily" "report --skip-slow" "/SC DAILY /ST 08:00"

Write-Output ""
Write-Output "Done. To test immediately:"
Write-Output "  python -m monitoring.watch --dry-run"
Write-Output "  python -m monitoring.report --skip-slow --no-email"
Write-Output "Remove with: schtasks /Delete /TN RMS_Monitor_Watch /F (and RMS_Monitor_Daily)"
