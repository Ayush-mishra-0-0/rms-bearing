# RMS MLSTM-iForest runbook (enterprise pipeline inside rms-bearing)

Goal: traction-motor bearing early warning with 1Hz RMS + Owner registry. Only 2 usable positives (37282 dense, 30532 sparse) → healthy-only MLSTM temp predictor + iForest on deviation (Liu et al. 2020 Sensors 20(3):823). See `docs/PAPER_MLSTM_IFOREST.md` for column map.

## Reproducibility rules
1. No ad-hoc scripts in root. All runs via `pipelines/` + `configs/experiment.yaml`.
2. `data/raw/` never committed. Ground truth in `data/processed/` + `data/manifests/` is versioned.
3. Every run writes `experiments/<timestamp>_<run_name>/run_manifest.json` (config hash, seed).
4. Seed fixed in `configs/experiment.yaml`. DB access read-only via `.env`.

## Start
1. Copy `.env.example` → `.env`, fill DB_USERNAME/PWD (DB 10.77.36.103).
2. Verify ground truth: `data/manifests/bearing_failure_events_audit.csv`, `data/manifests/telemetry_extraction_manifest.csv`.
3. `python pipelines/01_extract_windows.py --loco 37282 --start "2024-12-03 00:00:00" --end "2024-12-10 00:00:00"`
4. `python pipelines/02_train_mlstm.py --config configs/experiment.yaml --train data/interim/<healthy>.parquet`
