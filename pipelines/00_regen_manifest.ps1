# 00: regenerate data/manifests/telemetry_extraction_manifest.csv from ground truth + overrides.
# PowerShell mirror of src/rms_bearing/build_manifest.py (same columns, order, horizons, formats).
# Usage: powershell -ExecutionPolicy Bypass -File pipelines/00_regen_manifest.ps1
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$registry = Join-Path $root "data/processed/ground_truth_failure_registry.csv"
$overridesPath = Join-Path $root "data/processed/failure_timestamp_overrides.csv"
$out = Join-Path $root "data/manifests/telemetry_extraction_manifest.csv"

$overrides = @{}
if (Test-Path $overridesPath) {
  foreach ($r in (Import-Csv -LiteralPath $overridesPath -Encoding UTF8)) {
    if ($r.FailureTimestamp) { $overrides[$r.FailureID] = [datetime]$r.FailureTimestamp }
  }
}

$horizons = @(
  @("7d", 168, "Long-term degradation"),
  @("3d", 72, "Medium-term degradation"),
  @("24h", 24, "Short-term warning"),
  @("12h", 12, "Operational alert horizon"),
  @("6h", 6, "Immediate warning"),
  @("1h", 1, "Near-failure behaviour")
)

$rows = New-Object System.Collections.Generic.List[object]
foreach ($e in (Import-Csv -LiteralPath $registry -Encoding UTF8)) {
  if ($overrides.ContainsKey($e.FailureID)) {
    $ts = $overrides[$e.FailureID]; $precision = "EXACT"
  } else {
    $ts = [datetime]::ParseExact($e.Date.Trim(), "dd/MM/yyyy", $null); $precision = "DATE_ONLY_ASSUMED_MIDNIGHT"
  }
  foreach ($h in $horizons) {
    $rows.Add([pscustomobject]@{
      FailureID = $e.FailureID; Loco = $e.Loco; FailureDate = $e.Date
      FailureTimestamp = $ts.ToString("yyyy-MM-dd HH:mm:ss"); TimestampPrecision = $precision
      Label = $e.Label; Confidence = $e.Confidence; Window = $h[0]; HorizonHours = $h[1]
      WindowStart = $ts.AddHours(-$h[1]).ToString("yyyy-MM-dd HH:mm:ss")
      WindowEnd = $ts.ToString("yyyy-MM-dd HH:mm:ss"); Purpose = $h[2]
    })
  }
}
$dir = Split-Path -Parent $out
if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir | Out-Null }
# Minimal quoting like Python csv module (quote only on comma/quote/newline) so diffs stay clean.
function Format-CsvField([string]$v) {
  if ($v -match '[",\r\n]') { return '"' + ($v -replace '"', '""') + '"' }
  return $v
}
$sb = New-Object System.Text.StringBuilder
$cols = @("FailureID","Loco","FailureDate","FailureTimestamp","TimestampPrecision","Label","Confidence","Window","HorizonHours","WindowStart","WindowEnd","Purpose")
[void]$sb.AppendLine(($cols -join ","))
foreach ($r in $rows) {
  $vals = foreach ($c in $cols) { Format-CsvField ([string]$r.$c) }
  [void]$sb.AppendLine(($vals -join ","))
}
[System.IO.File]::WriteAllText($out, $sb.ToString(), (New-Object System.Text.UTF8Encoding $false))
Write-Output ("Wrote {0} rows to {1} ({2} EXACT overrides applied)" -f $rows.Count, $out, $overrides.Count)
