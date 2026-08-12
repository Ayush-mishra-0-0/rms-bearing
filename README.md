# RMS Bearing Early-Warning Data Foundation

`data/processed/ground_truth_failure_registry.csv` is the sole authoritative event source. Build manifests from it before any telemetry request.

## Layout

- `data/processed/` — ground truth and timestamp overrides
- `data/manifests/` — deterministic extraction requests
- `src/rms_bearing/` — manifest and extraction programs
- `scripts/` — source-report ingestion
- `sql/` — read-only database investigation SQL
- `docs/` — supplied reports and reference material
- `configs/` — configuration guidance

Build the manifest: `python src/rms_bearing/build_manifest.py`. Reconcile RMS timestamps for manual review with `python src/rms_bearing/match_fault_timestamps.py`; then run the availability-only health report with `python src/rms_bearing/check_telemetry_availability.py`.

An event with a date but no verified incident time is deliberately marked `DATE_ONLY_ASSUMED_MIDNIGHT`; extraction is blocked unless an exact timestamp override is supplied or an operator explicitly accepts that assumption.
