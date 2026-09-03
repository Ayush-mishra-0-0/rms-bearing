# Bake-off Protocol — Gold v1, Fixed Fusion, Pareto Gate

Accepted review 2026-09-03. This doc freezes the corrections to the enterprise workflow.
No experiment without `run_manifest.json` containing all fields below is valid.

## 1. Data contract

- Gold v1 (`configs/experiment.yaml:gold_version=v1`), 1-min median, SAME table for A/B/C/D/Fusion.
- Implementation: `src/rms_mlstm/features.py:GOLD_FEATURES` (28), `resample_1min()` sets `dq_gap`.
- Splits (rigid):
  - TRAIN `healthy_50` — fitting only
  - CALIB `healthy_20` — q99/thresholds/FAR only, NO failure tuning
  - TEST `37282` dense / `30532` sparse / `30751` sequence + `healthy_50_unseen` FAR control — ONE final eval

## 2. Score calibration (Fix 1)

Raw arm scores differ (residual vs recon error vs elec resid). Before fusion:

```
raw -> HealthyCalibrator.fit(calib_healthy) -> ECDF -> 0-1 (src/rms_mlstm/calibrate.py)
```

Fusion (`src/rms_mlstm/fusion.py`): `0.40A + 0.30B + 0.15C + 0.05D + 0.10R`, frozen pre-test.
Learned/logreg fusion = `fusion_exploratory`, reported separately, never decides winner (Fix 2).

## 3. Alarm contract (Fix 5)

Per level (`alarm.candidate/warning/critical`): onset = first t with `score01>=thr` for `>=N` consecutive mins, hysteresis `reset_thr`, `M_min`.
Lead = `Owner_ts - onset`. Report candidate/warning/critical onsets + leads separately.

## 4. Per-case reporting (Fix 4)

| Case | Purpose | Extra check |
|---|---|---|
| 37282 dense | sensitivity + dq robustness | lead + persistence |
| 30532 sparse | sparse robustness | detection holds with gaps |
| 30751 sequence | cutout precursor | Rule Engine standalone hit? |
| 50 healthy | FAR | `far_per_1000_loco_days` |

Report Model + Rule + Fusion rows per case, never a single collapsed number.

## 5. Decision (Fix 6)

Hard gate: `FAR < 2 / 1000 loco-days`. Among passers compare Pareto:
primary `median_lead_time_critical_h`, secondary `detect_24h/48h, persistence, cross-vendor`.
Ship Pareto-best (may be A+Rules, not full fusion). Research detection first; `Critical->withdrawal` is a separate operational approval.

## 6. Ablation

Winner only: drop each GROUP (`ablation_groups`: thermal / electrical / kinematic_mode / status / exposure), re-eval. Expect A collapses w/o thermal, B w/o electrical — confirms 42728 lesson (thermal+electrical jointly carry precursor).

## 7. Run order

1. Gold+split freeze (done) 2. features+tests (done) 3. Arm A e2e 4. `evaluate.py` harness (done)
5. Arm B (LSTM-AE only first) 6. Arm C (per-mode thresholds) 7. Arm D (volatility proxy)
8. Rules (`rules.py` done) 9. Fixed fusion 10. Blind bake-off 11. Ablations+cross-vendor 12. Pareto winner -> shadow.

## 8. Manifest (required)

`git SHA, config SHA, gold_version, feature list, train/calib/test locos+windows, model params, calibrator quantiles, alarm thr/N/M, seed, artifacts (preds, scores01, onsets, FAR, plots)`.
