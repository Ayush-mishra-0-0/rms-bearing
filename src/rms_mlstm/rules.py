"""Deterministic Rule Engine. Sequence only — never a single spike.
Evaluated independently per FIX 4 (esp. 30751 bogie-cutout precursor).

Candidate IF:
  (Delta-T >20C LHB OR score01_resid > q99 for >30min)
  AND (bbur_any_off OR bstb_any_off OR mtrc isolated)
  AND repetition >=2 in 24h
  AND Cooling_Ineff high
=> Watch/Warning/Critical mapping; research detection reported separately from operational action.
"""
from __future__ import annotations
import pandas as pd

LHB_DELTA_T_CRIT = 20.0


def rule_score_row(delta_t_max: float, resid01: float, bbur_off: int, bstb_off: int,
                   mtrc_isolated: int, cooling_ineff: float, repeat_24h: int) -> float:
    """Returns 0-1 rule score (already calibrated scale for fusion R_rules)."""
    thermal = 1.0 if (delta_t_max or 0) > LHB_DELTA_T_CRIT else (0.7 if (resid01 or 0) >= 0.99 else 0.0)
    status = 1.0 if (bbur_off or bstb_off or mtrc_isolated) else 0.0
    persist = 1.0 if (repeat_24h or 0) >= 2 else (0.5 if (repeat_24h or 0) == 1 else 0.0)
    cooling = 1.0 if (cooling_ineff or 0) > 0 else 0.5
    # Sequence gate: thermal AND status AND persistence required for high score
    if thermal >= 0.7 and status == 1.0 and persist >= 0.5:
        return 0.9 if persist == 1.0 and cooling == 1.0 else 0.7
    if thermal >= 0.7 and persist == 1.0:
        return 0.5  # Watch: thermal repeating but no status corroboration
    return 0.0


def score_rules_df(gold: pd.DataFrame, resid01: pd.Series) -> pd.Series:
    """Vectorized wrapper over Gold v1 + calibrated residual 0-1."""
    out = []
    # repeat_24h approximated as count of prior thermal exceedances in trailing 1440 rows (1-min)
    deltas = pd.DataFrame({c: gold[c] for c in
                           ("Temp_Diff_Motor_1", "Temp_Diff_Motor_2", "Temp_Diff_Motor_3")
                           if c in gold.columns})
    dmax = deltas.max(axis=1) if len(deltas.columns) else pd.Series(0.0, index=gold.index)
    hot = (dmax > LHB_DELTA_T_CRIT).astype(int)
    repeat = hot.rolling(1440, min_periods=1).sum()
    for i in gold.index:
        mtrc_iso = 0
        if "mtrcctract1" in gold.columns:
            try:
                mtrc_iso = 1 if float(gold.at[i, "mtrcctract1"]) == 0 else 0
            except (TypeError, ValueError):
                mtrc_iso = 0
        out.append(rule_score_row(
            float(dmax.loc[i]) if pd.notna(dmax.loc[i]) else 0.0,
            float(resid01.loc[i]) if i in resid01.index else 0.0,
            int(gold.at[i, "bbur_any_off"]) if "bbur_any_off" in gold.columns else 0,
            int(gold.at[i, "bstb_any_off"]) if "bstb_any_off" in gold.columns else 0,
            mtrc_iso,
            float(gold.at[i, "Cooling_Ineff"]) if "Cooling_Ineff" in gold.columns else 0.0,
            int(repeat.loc[i])))
    return pd.Series(out, index=gold.index)
