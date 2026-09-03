"""FIX 2: PRIMARY fusion = fixed weights frozen BEFORE test.
Exploratory learned fusion lives elsewhere and never decides the winner.
Inputs MUST already be calibrated 0-1 (see calibrate.py).
"""
from __future__ import annotations

FIXED_WEIGHTS = {"A_wang": 0.40, "B_ae": 0.30, "C_mode": 0.15, "D_elec": 0.05, "R_rules": 0.10}


def fuse_fixed(scores01: dict, weights: dict | None = None) -> float:
    w = weights or FIXED_WEIGHTS
    tot = sum(w.values())
    s = 0.0
    for k, wk in w.items():
        v = float(scores01.get(k, 0.0))
        s += (wk / tot) * min(max(v, 0.0), 1.0)
    return s


def fuse_series(df_scores01, weights: dict | None = None):
    """df with columns A_wang,B_ae,C_mode,D_elec,R_rules in 0-1 => Series fused 0-1."""
    return df_scores01.apply(lambda r: fuse_fixed(r.to_dict(), weights), axis=1)
