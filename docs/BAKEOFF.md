# Bake-off: 3 arms, one scoreboard, best (or best-mix) wins

Goal: run all three paper families on the SAME data/windows, then pick the winner or combine.

## Arms
- **A — MLSTM-iForest (Liu et al. 2020).** 40min → 6min temp prediction, EWMA deviation, iForest alarm. Scaffolded: `configs/experiment.yaml`, `pipelines/01→02→03`, `src/rms_mlstm/`. 1min resample.
- **B — Martinez 1Hz thermal (Martinez-Llop & Sanz-Bobi 2022).** Bearing temp + exterior temp + speed every second, anomaly up to 2d ahead. Keeps 1s resolution; maps to `Temp_Diff`, load-normalized temp. Cheapest; proves 1Hz thermal works.
- **C — CNN-LSTM SCADA (Zhang et al. 2023).** Correlation-select ~20 of 169 inputs, CNN spatial + LSTM temporal, RMSE health index. Catches what plain LSTM misses (cage/grease cases).
- **Combo — best-mix.** Stack/or arms under the rule layer (`Temp_Diff` + bogie-off + TM-isolated + repetition + withdrawal ≤24h, never a single alarm) to kill false alarms. Combo only wins if it beats the best single arm on the scoreboard.

## Shared anchors (fairness — same for all arms)
- `data/processed/failure_timestamp_overrides.csv` is authoritative. Current: `4635100 → 2024-12-10 05:00:00 EXACT` (axle-6 locked 04:42–04:46, EP withdrawal 05:00 per registry).
- 37282 windows from that anchor:
  - 7d: 12-03 05:00 → 12-10 05:00 | 3d: 12-07 05:00 → 12-10 05:00 | 24h: 12-09 05:00 → 12-10 05:00
  - 12h: 12-09 17:00 → 12-10 05:00 | 6h: 12-09 23:00 → 12-10 05:00 | 1h: 12-10 04:00 → 12-10 05:00
- Regen full manifest after any override change: `python src/rms_bearing/build_manifest.py` (then `match_fault_timestamps.py`, `check_telemetry_availability.py` per `sql/README.md`).
- Train: healthy fleet only (845 minus 37282/30532/30751). Validate: 37282 dense + 30532 sparse. 30751 fault-sequence only (gap 11–17 Dec). Auxiliary: 42728 residual-distribution check (overheat hr +22A/dT +15.5°C).
- Candidate next override (NOT added yet): 30532 `4145344 → 2024-04-04 05:00` (summary: "05/00 HRS LOCO DECLARE FAILED"). Confirm before adding.

## Scoreboard (same metrics, all arms)
| Metric | Definition | Paper reference |
|---|---|---|
| Missed % | failures with no alarm before anchor | A: 0%, B: detected 2d ahead |
| False-warning % | healthy-window alarms | A: 1.6% |
| Lead-time | anchor − first alarm (minutes) | A: 9min–2d |
| Cost | train/infer time, CPU-only | A: iForest 1.56s vs 0.14–0.17s baselines |

## Next steps
1. You run: `python src/rms_bearing/build_manifest.py` (picks up the 05:00 override) + extract 37282 7d (`tasks.ps1 extract-37282`, now 05:00→05:00).
2. I scaffold arm B + C configs/pipelines reusing `src/rms_mlstm` features + `data/interim`.
3. Fill scoreboard, then decide single winner vs combo.
