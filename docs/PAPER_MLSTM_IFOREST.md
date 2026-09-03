# MLSTM-iForest → RMS mapping (Liu et al. 2020 Sensors 20(3):823)

## Paper recipe
40min history of [bearing temp, ambient temp, carriage mass, motor traction power, train speed] → MLSTM predicts next 6min bearing temp → deviation index = smoothed |actual - predicted| → iForest unsupervised alarm. 98.4% acc, 1.6% false, 0% missed, 9min–2d lead vs EMU-ODS.

## RMS 1Hz column map (169 params, `Lotus_loco_process_signals`)
| Paper input | RMS columns | Notes / tech-debt |
|---|---|---|
| Bearing temp (target) | `xtempmotor1_1,xtempmotor2_1,xtempmotor3_1,xtempmotor1_2,xtempmotor2_2,xtempmotor3_2` → `xtempmotor_max` | Predict max; also keep per-motor + `Temp_Diff = |1_1-1_2|` physics feature |
| Train speed | `xspeedloco,gpsspeed` | Prefer `xspeedloco`, fallback `gpsspeed` |
| Traction power | `xiprim_1,xuprim_1,ltedemand,mtrcctract1,xte_be_loco` | No direct kW; use `xiprim_1*xuprim_1` + `ltedemand` as proxy |
| Ambient temp | NONE clean | Debt: use min of `xatmp*` / coolest motor at standstill, or weather API by lat/lon/time |
| Carriage mass | NONE | Debt: use `TE integral` + `lbedemand` workload proxy; log as limitation |

## Adaptations for our constraints
- Resample 1Hz → 1min median (40 steps in, 6 steps out). Windows CPU-friendly, matches paper horizons, kills sensor jitter.
- Train on healthy fleet only (845 locos minus 37282/30532/30751). Validate lead-time on 37282 dense + 30532 sparse. 30751 fault-sequence only (gap 11–17 Dec).
- Deviation EWMA span=5 to suppress transients (paper's false-alarm guard).
- Never train supervised classifier on 2 positives. iForest threshold from healthy val q99.
