$ErrorActionPreference = 'Stop'
# Installs two Windows scheduled tasks:
#   RMS_Monitor_Watch  -> every 5 minutes (data-flow alerts)
#   RMS_Monitor_Daily  -> daily 08:00 (deep report + optional digest email)
# Run from an elevated PowerShell:  powershell -ExecutionPolicy Bypass -File setup_tasks.ps1

$repo = (Resolve-Path (Join-Path $PSScriptRoot '.')).Path
$py = (Get-Command python -ErrorAction SilentlyContinue).Source
if (-not $py) { throw "python not found on PATH" }

function New-Task($name, $modArgs, $sched) {
    # schtasks /TR rejects shell operators (&&), so point the task at a wrapper .cmd
    $wrapper = Join-Path $repo ("run_" + $name + ".cmd")
    "@echo off`r`ncd /d `"$repo`"`r`n`"$py`" -m monitoring.$modArgs`r`n" | Set-Content -LiteralPath $wrapper -Encoding Ascii
    & schtasks /Create /F /TN $name /TR "`"$wrapper`"" @sched | Out-Null
    Write-Output "created: $name  ->  python -m monitoring.$modArgs"
}

New-Task "RMS_Monitor_Watch" "watch"    @("/SC","MINUTE","/MO","5")
New-Task "RMS_Monitor_Daily" "report" @("/SC","DAILY","/ST","08:00")  # full mode: feeds loco trend (~10 min)

# Board autostart on logon (no admin/password needed): a launcher in the
# user's Startup folder. The board itself never auto-restarts otherwise.
$startup = Join-Path $env:APPDATA 'Microsoft\Windows\Start Menu\Programs\Startup'
$board = Join-Path $startup 'RMS_Board.cmd'
"@echo off`r`ncd /d `"$repo`"`r`nstart `"RMS Board`" /min `"$py`" -m streamlit run monitoring/dashboard.py --server.port 8501 --server.headless true`r`n" | Set-Content -LiteralPath $board -Encoding Ascii
Write-Output "autostart: $board"

Write-Output ""
Write-Output "Done. To test immediately:"
Write-Output "  python -m monitoring.watch --dry-run"
Write-Output "  python -m monitoring.report --skip-slow --no-email"
Write-Output "Remove with: schtasks /Delete /TN RMS_Monitor_Watch /F (and RMS_Monitor_Daily)"
