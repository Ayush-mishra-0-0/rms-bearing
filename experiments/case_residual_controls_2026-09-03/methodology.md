# Pre-bake-off evidence: frozen residual case study (2026-09-03)

## Method (FROZEN — do not modify to fit cases)

- Scripts: `case_42728/residual_distribution_42728.py` (42728),
  `scripts/residual_distribution_case.py` (all others, same logic).
- `Ihat = median(I | speed-bin, accel-bin)`, own-loco pooled baseline,
  traction-active only (`ltedemand=1`).
- Bins: V = 0/10/20/30/40/50+ km/h;
  A = -inf/-0.3/-0.1/+0.1/+0.3/+inf m/s2.
- Acceleration from consecutive-row pairs with `0 < dt <= 5s` only.
- Thermal decoupling `dT = suspect-TM minus mean of other five motors`,
  channels reading `>= 75.99` excluded from the other-five mean
  (stuck-76C artifact rule, same as 42728).
- Per-period `r_t = I_obs - Ihat(v,a)` distribution: med/p10-p90/IQR/tails,
  two-sample KS-D vs pooled baseline (D only, no p-value), dT alongside,
  hourly rolling med/IQR. BASELINE row is in-sample reference, not a test.
- Stdlib only. Preprocessing, features, and thresholds identical everywhere.

## Windows

- 42728: baseline 27-Jul..03-Aug 2026; test 06/07/08-Aug 2026;
  suspect `xtempmotor1_2` (axle 04). Failure 08-08 19:26 (in telemetry gap).
- 37282: baseline 01–07 Dec 2024; test 08/09/10-Dec (pre-fail to 05:00);
  suspect `xtempmotor3_2` (axle 6). Failure 10-12 05:00 EP withdrawal.
- 37282-Nov (same-loco control): baseline 01–07 Nov; test 08/09/10-Nov
  (window-end 05:00, no failure; label is window end only).
- Healthy A 30385 / B 30380 (regime-matched, no registry/owner record):
  baseline 01–07 Dec; test 08/09/10-Dec (window-end, no failure).
- 30532: baseline attempted 25–31 Mar then 02-Apr (in-data);
  untestable — median sampling gap 15s (p90 60s) vs the <=5s pair rule.

## Interpretation (frozen with the numbers)

- 42728: credible **case-specific** precursor (event-hour KS-D 0.563,
  med +22.0, IQR 5.9, dT +15.5; cold decoupling pre-fail dT -21.8).
- 37282: genuine dense-data **negative replication** (pre-fail KS-D 0.173,
  dT +0.5, no excursion). Stays a validation case for all bake-off arms.
- Controls: ordinary variation KS-D <= 0.150, no coupled excursion.
- 30532: cadence-blocked — neither success nor failure.
- Gate: the signature is **not** demonstrated to be a general 1 Hz
  bearing precursor. Bake-off arms A/B/C/D (+fusion) proceed on
  mechanism/feasibility terms; 37282 must remain in the scoreboard.

## Reproduction

Per-case `output.txt` files are verbatim stdout captures. Rerun commands
are recorded at the top of each `output.txt` invocation (see shell
history): same scripts, same flags, same CSVs as `manifest.json`.
