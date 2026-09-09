# ML Training Review and Remediation Plan

**Repository:** `Ayush-mishra-0-0/rms-bearing`  
**Reviewed:** 2026-09-09  
**Scope:** Arm A training, calibration, scoring, alarm evaluation, and committed run artifacts

## Executive assessment

The project is moving in the correct research direction. Healthy-only anomaly learning, separate healthy calibration, failure-locomotive exclusion, reproducible run manifests, and false-alarm gating are appropriate choices for a dataset with very few confirmed failures.

However, the current detection and lead-time results must be treated as **provisional**. There are implementation defects in sequence construction and alarm evaluation, and the named MLSTM–Isolation Forest pipeline does not currently contain an Isolation Forest stage. These issues should be corrected before tuning thresholds, comparing model arms, or claiming validated performance.

## What is already correct

- The LSTM is trained only on nominal/healthy telemetry.
- Known failure locomotives `37282`, `30532`, and `30751` are explicitly rejected from training and calibration inputs.
- Training, healthy calibration, failure tests, and unseen-healthy FAR evaluation are conceptually separated.
- Imputation and scaling parameters are learned from the training set and saved for inference parity.
- The 40-minute lookback and six-minute forecast horizon form a reasonable predictive-maintenance baseline.
- Alarm thresholds are derived from held-out healthy calibration data rather than fitted to the failure cases.
- Configuration, seed, Git SHA, feature order, scaler, calibration sample, and model checkpoint are recorded.
- Candidate, warning, and critical alarms are intended to be reported separately.
- The protocol correctly makes false-alarm rate a hard deployment gate.

## Critical findings

### 1. Sequences can cross locomotive boundaries

**Affected code:** `pipelines/02_train_mlstm.py`, `src/rms_mlstm/model_mlstm.py`

The loader concatenates all input files into one dataframe and invokes `make_sequences()` once on the resulting matrix. Sequence generation has no locomotive or continuous-segment identifier.

The committed `armA_healthy2_full50` manifest records:

- `train_rows = 14869`
- `train_seqs = 14824`
- lookback = 40
- horizon = 6

For a single continuous array, the sequence count is:

```text
14869 - 40 - 6 + 1 = 14824
```

This exact match indicates that all training rows were handled as one continuous time series. At a locomotive boundary, an input window may contain telemetry from two different locomotives and use the second locomotive's future temperature as its target.

Rolling features such as gradients and electrical volatility can also cross boundaries because feature calculation occurs before any grouping by locomotive.

**Impact:** training, calibration residuals, thresholds, and downstream alarms can all be distorted.

**Required correction:**

1. Require `locoid` and `devicetime` for production training inputs.
2. Sort by `locoid, devicetime`.
3. Compute rolling/difference features independently per locomotive.
4. Split each locomotive into continuous telemetry segments.
5. Generate sequences within each `(locoid, segment_id)` group only.
6. Reject any window that contains a timestamp discontinuity or disallowed data-quality gap.
7. Save per-locomotive row and sequence counts in the run manifest.

### 2. The current Arm A pipeline does not use Isolation Forest

**Affected code:** `pipelines/03_score_iforest.py`

Despite the pipeline name and `iforest` configuration, scoring currently performs:

```text
LSTM forecast
→ absolute temperature residual
→ EWMA smoothing
→ healthy ECDF calibration
→ percentile-based alarm
```

No `IsolationForest` is fitted, saved, loaded, or used for inference.

This residual-percentile approach is a valid and useful baseline, but it should not be described as MLSTM–Isolation Forest.

**Required decision:**

- Rename the current model to **MLSTM–EWMA–ECDF**, and evaluate it as the simplest Arm A baseline; or
- implement Isolation Forest using healthy-only residual-derived features, persist it as an artifact, and compare it against the ECDF baseline.

Recommended approach: preserve the simpler ECDF model as a baseline and add Isolation Forest as a separate frozen variant. Do not assume Isolation Forest will perform better.

### 3. Alarm persistence and hysteresis are incomplete

**Affected code:** `src/rms_mlstm/evaluate.py`

The function `find_onset()` accepts `M_min` but does not use it. It also counts rows rather than verified elapsed minutes. Scores inside the hysteresis band preserve the accumulated run indefinitely, so qualifying observations separated by a long period can be treated like consecutive minutes.

The current evaluator returns only the first onset. It does not enumerate alarm episodes, which is required for a defensible false-alarm rate.

**Required correction:**

- enforce persistence using timestamps and elapsed duration;
- require the configured number of genuinely consecutive minutes;
- break or invalidate runs across telemetry gaps;
- implement reset behavior using `reset_thr` and `M_min`;
- enumerate distinct candidate, warning, and critical alarm episodes;
- define suppression/cooldown behavior;
- calculate FAR from alarm episodes and actual observable loco-time;
- add unit tests for gaps, hysteresis bands, resets, irregular timestamps, and repeated episodes.

### 4. Training volume and model selection are insufficient

The full50 manifest contains only 14,869 one-minute rows, equivalent to approximately 10.3 aggregate loco-days. Across 50 locomotives, this averages roughly five hours per locomotive.

That is limited coverage for a three-layer LSTM expected to generalize across operating modes, vendors, seasons, loads, routes, and ambient conditions.

Training also lacks:

- chronological healthy validation loss;
- early stopping;
- best-checkpoint restoration;
- learning curves;
- a simple baseline comparison;
- documented coverage by locomotive, vendor, operating mode, and time period.

**Required correction:**

- expand healthy training exposure substantially;
- retain locomotive-disjoint calibration and unseen-healthy test sets;
- create a chronological validation slice inside the healthy training population;
- select checkpoints using validation loss;
- record training and validation curves;
- compare against persistence, rolling mean, linear/ridge, and simple tree-based predictors.

A complex LSTM should only advance if its residual quality and alarm behavior materially beat the simpler baselines.

## Additional risks to address

### Missingness and outages

Median imputation currently allows sequence construction to continue through missing measurements. A long outage can therefore become an apparently valid model window.

Add explicit continuity checks and either reject gap-crossing windows or provide a tested masking strategy. Observable healthy time used in FAR calculations must exclude periods in which the model could not have produced a valid decision.

### Dataset identity

Path-name and known-ID guards are useful but not sufficient proof of split integrity. Manifests should contain the actual unique locomotive IDs, date ranges, source hashes, row counts, valid sequence counts, and overlap checks for every split.

### Test-set reuse

Failure cases that have already been repeatedly inspected are development cases, not untouched blind tests. Thresholds, features, persistence rules, and model selection must not be adjusted using their outcomes.

Case `42728`, which has already informed precursor analysis, should be labeled exploratory/retrospective unless a decision protocol was frozen before scoring it.

## Recommended execution order

### Phase 1 — Correctness before tuning

1. Implement locomotive-aware, time-sorted, gap-safe feature and sequence generation.
2. Add tests proving that no sequence crosses a locomotive or telemetry-segment boundary.
3. Correct timestamp-based alarm persistence, reset logic, episode counting, and FAR.
4. Decide whether to rename the present ECDF pipeline or add a real Isolation Forest variant.

### Phase 2 — Retrain Arm A

1. Rebuild Gold data after the sequence corrections.
2. Expand healthy training coverage.
3. Add chronological healthy validation and early stopping.
4. Train simple prediction baselines and the LSTM under the same split.
5. Fit calibration only on the held-out healthy-calibration locomotives.
6. Freeze model, scaler, calibrator, alarm rules, and configuration.

### Phase 3 — Locked evaluation

1. Evaluate FAR once on `healthy_50_unseen`.
2. Require `FAR < 2 / 1000 loco-days` using clearly defined alarm episodes.
3. Evaluate the frozen system on each failure case.
4. Report candidate, warning, and critical onset, lead time, duration, persistence, and data-quality coverage separately.
5. Advance only configurations that pass the healthy FAR gate.

### Phase 4 — Bake-off

After Arm A is trustworthy:

1. Build Arms B and C on the same frozen data contract.
2. Apply equivalent calibration and alarm semantics.
3. Compare only models that pass the FAR gate.
4. Evaluate fixed fusion after individual arms are frozen.
5. Select the Pareto-best deployable model and run ablations/cross-vendor checks.

## Acceptance criteria for trustworthy Arm A results

Arm A should not be considered validated until all of the following are true:

- [ ] No training, calibration, or scoring sequence crosses a locomotive boundary.
- [ ] No valid sequence crosses an unacceptable telemetry gap.
- [ ] Rolling features reset at locomotive and continuous-segment boundaries.
- [ ] Actual locomotive IDs and date windows are recorded for every split.
- [ ] Train, validation, calibration, and test locomotive sets have zero overlap.
- [ ] Validation loss and best-checkpoint selection are recorded.
- [ ] The ECDF and/or Isolation Forest implementation is named accurately.
- [ ] `M_min` reset behavior is implemented and unit-tested.
- [ ] FAR counts defined alarm episodes over observable loco-time.
- [ ] Alarm thresholds are frozen before failure-test evaluation.
- [ ] Unseen-healthy FAR passes the hard gate.
- [ ] Failure-case reports include data coverage and uncertainty.
- [ ] The LSTM is compared with simple forecasting baselines.

## Bottom line

The architecture of the experiment is promising and should be continued. The strongest parts are the healthy-only learning strategy, split philosophy, calibration discipline, and reproducibility scaffolding.

The immediate priority is not further threshold tuning or additional model arms. It is to repair sequence construction and alarm evaluation, then retrain Arm A from scratch. Until that is done, existing detection and lead-time outputs are useful debugging signals but should not be presented as validated predictive-maintenance performance.
