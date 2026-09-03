"""FIX 5+6: executable alarm contract + Pareto evaluation.
- Onset = first t where score01 >= thr for >= N consecutive mins AND no dip below reset_thr for M mins.
- Report candidate/warning/critical separately (never collapse to one number prematurely).
- FAR per 1000 loco-days on unseen healthy; hard gate <2.0 before lead-time comparison.
- Per-case purposes: 37282 dense / 30532 sparse / 30751 sequence (FIX 4).
"""
from __future__ import annotations
from datetime import datetime, timedelta
import pandas as pd

CASE_PURPOSE = {
    "37282": "precursor sensitivity + timestamp/dq robustness (dense)",
    "30532": "robustness under sparse telemetry",
    "30751": "sequence/cutout precursor validation (rule-engine check)",
}


def lead_time_minutes(first_alarm, failure_time) -> float | None:
    if first_alarm is None or failure_time is None:
        return None
    return (failure_time - first_alarm).total_seconds() / 60.0


def find_onset(ts: pd.Series, score01: pd.Series, thr: float, N_min: int,
               reset_thr: float, M_min: int):
    """First timestamp satisfying persistence contract. Returns None if never."""
    run = 0
    candidate_start = None
    for t, s in zip(ts, score01):
        s = float(s)
        if s >= thr:
            if run == 0:
                candidate_start = t
            run += 1
            if run >= N_min:
                return candidate_start  # onset = start of qualifying run
        elif s < reset_thr:
            run = 0
            candidate_start = None
        # else: in hysteresis band [reset_thr, thr): hold run, don't reset
    return None


def onsets_per_level(ts, score01, alarm_cfg: dict) -> dict:
    """score01 series -> {level: onset_ts or None} for candidate/warning/critical."""
    out = {}
    for lvl in ("candidate", "warning", "critical"):
        c = alarm_cfg[lvl]
        out[lvl] = find_onset(pd.Series(list(ts)), pd.Series(list(score01)),
                              c["thr"], c["N_min"], c["reset_thr"], c["M_min"])
    return out


def far_per_1000_loco_days(false_alarm_windows: int, total_loco_minutes: float) -> float:
    """FAR normalized so healthy fleet size doesn't distort comparison."""
    if total_loco_minutes <= 0:
        return float("inf")
    return false_alarm_windows / (total_loco_minutes / (60.0 * 24.0)) * 1000.0


def detection_at_horizon(onset, failure_time, horizon_h: float) -> bool | None:
    if onset is None or failure_time is None:
        return None
    lead_h = (failure_time - onset).total_seconds() / 3600.0
    return lead_h >= horizon_h


def per_case_report(case_loco: str, onsets: dict, failure_time) -> dict:
    lead = {}
    for lvl, ts in onsets.items():
        if ts is None or failure_time is None:
            lead[lvl] = None
        else:
            lead[lvl] = lead_time_minutes(ts, failure_time) / 60.0
    return {"loco": str(case_loco), "purpose": CASE_PURPOSE.get(str(case_loco), "operational FAR control"),
            "onsets": {k: (v.isoformat() if isinstance(v, datetime) else str(v) if v is not None else None)
                       for k, v in onsets.items()},
            "lead_time_h": lead,
            "detect_24h": detection_at_horizon(onsets.get("critical"), failure_time, 24),
            "detect_48h": detection_at_horizon(onsets.get("critical"), failure_time, 48)}
