# Data contract v0

- Source of truth: `data/processed/ground_truth_failure_registry.csv` (68 events) + `data/manifests/bearing_failure_events_audit.csv` (41 bearing subset). Record sha in run_manifest per run; never edit in place.
- Extraction: read-only `dbo.Lotus_loco_process_signals` via `.env`. `DATE_ONLY_ASSUMED_MIDNIGHT` blocked unless override in `data/processed/failure_timestamp_overrides.csv` (see `configs/README.md`).
- Resampled window schema (`data/interim/<loco>_<window>.parquet`): `t, xtempmotor_max, xspeedloco, xiprim_1, xuprim_1, ltedemand, Temp_Diff_Motor_1, Cooling_Inefficiency` at 1min.
- No `data/raw/*.csv` committed. Every artifact lists `loco, window_start, window_end, rows, missing_pct, vendor`.
