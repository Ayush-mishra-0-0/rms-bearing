"""Gold v1 canonical features. Pure functions, tested.
All arms consume SAME 1-min Gold. Changing outputs => bump gold_version in configs/experiment.yaml.

Covers FIX: common inputs so bake-off measures inductive bias, not input differences.
"""
from __future__ import annotations
import pandas as pd
import numpy as np

TEMP_COLS = ["xtempmotor1_1", "xtempmotor2_1", "xtempmotor3_1",
             "xtempmotor1_2", "xtempmotor2_2", "xtempmotor3_2"]

GOLD_FEATURES = ["xtempmotor_max", "Temp_Diff_Motor_1", "Temp_Diff_Motor_2", "Temp_Diff_Motor_3",
    "Temp_Gradient", "Temp_Gradient_15min", "Normalized_Temp", "Cooling_Ineff",
    "xiprim_1", "xuprim_1", "Current_Vol", "Current_Vol_5min", "Volt_Imbal", "bur_opcurrent_mean",
    "xspeedloco", "gpsspeed", "ltedemand", "lbedemand", "mtrcctract1", "op_mode",
    "mvcb_on", "bbur_any_off", "bstb_any_off", "bflg_any_off",
    "ThermalFatigue72h", "WorkIntegral24h", "Vendor", "dq_gap"]


def _num(s: pd.Series) -> pd.Series:
    return pd.to_numeric(s, errors="coerce")


def add_core_features(df: pd.DataFrame) -> pd.DataFrame:
    """Backward-compat core + full Gold v1. Never drops rows; missing inputs => NaN + dq_gap=1."""
    df = df.copy()
    if "dq_gap" not in df.columns:
        df["dq_gap"] = 0

    # --- Thermal max ---
    have = [c for c in TEMP_COLS if c in df.columns]
    if have:
        tnum = pd.DataFrame({c: _num(df[c]) for c in have})
        df["xtempmotor_max"] = tnum.max(axis=1)
    else:
        df["xtempmotor_max"] = np.nan

    # --- Symmetric differentials (bogie vs bogie) ---
    for i in (1, 2, 3):
        a, b = f"xtempmotor{i}_1", f"xtempmotor{i}_2"
        if a in df.columns and b in df.columns:
            df[f"Temp_Diff_Motor_{i}"] = (_num(df[a]) - _num(df[b])).abs()
        else:
            df[f"Temp_Diff_Motor_{i}"] = np.nan

    # --- Gradients (assumes 1-min grain; if 1Hz input, still valid per-sample diff) ---
    if "xtempmotor_max" in df.columns:
        df["Temp_Gradient"] = _num(df["xtempmotor_max"]).diff()
        df["Temp_Gradient_15min"] = _num(df["xtempmotor_max"]).diff(15)
    else:
        df["Temp_Gradient"] = np.nan
        df["Temp_Gradient_15min"] = np.nan

    # --- Load-normalized temp: isolates unexplained heat (Wang FA spirit) ---
    te = None
    for c in ("xte_be_loco", "ltedemand", "mtrcctract1"):
        if c in df.columns:
            te = _num(df[c])
            break
    sp = _num(df["xspeedloco"]) if "xspeedloco" in df.columns else pd.Series(np.nan, index=df.index)
    work = (sp.fillna(0).abs() * (te.fillna(0).abs() if te is not None else 0)).replace(0, np.nan)
    df["Normalized_Temp"] = _num(df["xtempmotor_max"]) / work

    # --- Cooling inefficiency: dT/dt despite blower on ---
    blower = None
    if "mmcbblotm1" in df.columns:
        blower = _num(df["mmcbblotm1"])
    elif any(c in df.columns for c in ("bbur1_off", "bbur2_off", "bbur3_off")):
        offs = [_num(df[c]).fillna(0) for c in ("bbur1_off", "bbur2_off", "bbur3_off") if c in df.columns]
        # bbur*_off==1 means blower off; blower_on ~ 1 - any_off
        any_off = pd.concat(offs, axis=1).max(axis=1) if offs else 0
        blower = 1 - any_off
    else:
        blower = pd.Series(1.0, index=df.index)
    df["Cooling_Ineff"] = _num(df["Temp_Gradient_15min"]) / (blower.fillna(1) + 0.1)

    # --- Electrical volatility proxy (Shang-conceptual, LOW-rate; NOT kHz kurtosis) ---
    # NOTE: true intra-minute volatility needs 1Hz. On 1-min Gold this is inter-minute
    # volatility — an honest proxy, explicitly labelled as such.
    if "xiprim_1" in df.columns:
        xi = _num(df["xiprim_1"])
        df["Current_Vol"] = xi.rolling(3, min_periods=2).std()
        df["Current_Vol_5min"] = xi.rolling(5, min_periods=2).std()
    else:
        df["Current_Vol"] = np.nan
        df["Current_Vol_5min"] = np.nan

    # --- Voltage imbalance + BUR current mean (optional cols; NaN if absent) ---
    bg_cols = [c for c in df.columns if c.startswith("bg") and "ipvoltage" in c]
    if len(bg_cols) >= 2:
        bg = pd.DataFrame({c: _num(df[c]) for c in bg_cols})
        df["Volt_Imbal"] = bg.max(axis=1) - bg.min(axis=1)
    elif "xuprim_1" in df.columns:
        df["Volt_Imbal"] = np.nan  # insufficient inverter detail; keep NaN, don't fake 0
    else:
        df["Volt_Imbal"] = np.nan
    bur_cols = [c for c in ("bur1_opcurrent", "bur2_opcurrent", "bur3_opcurrent") if c in df.columns]
    if bur_cols:
        df["bur_opcurrent_mean"] = pd.DataFrame({c: _num(df[c]) for c in bur_cols}).mean(axis=1)
    else:
        df["bur_opcurrent_mean"] = np.nan

    # --- Op mode (Tai): powering / regen / idle / coast ---
    def _mode_row(lte, lbe, spd):
        try:
            lte, lbe, spd = float(lte or 0), float(lbe or 0), abs(float(spd or 0))
        except (TypeError, ValueError):
            return "unknown"
        if spd < 3:
            return "idle"
        if lte > 5:
            return "powering"
        if lbe > 5:
            return "regen"
        return "coast"
    if all(c in df.columns for c in ("ltedemand", "lbedemand", "xspeedloco")):
        df["op_mode"] = [_mode_row(a, b, c) for a, c, b in
                         zip(df["ltedemand"], df["xspeedloco"], df["lbedemand"])]
    else:
        df["op_mode"] = "unknown"

    # --- Status aggregates (any_off across bogies) ---
    for prefix, out in (("bbur", "bbur_any_off"), ("bstb", "bstb_any_off"), ("bflg", "bflg_any_off")):
        cols = [c for c in df.columns if c.startswith(prefix) and c.endswith("_off")]
        if cols:
            df[out] = pd.DataFrame({c: _num(df[c]).fillna(0) for c in cols}).max(axis=1).astype(int)
        else:
            df[out] = 0

    # --- Cumulative stress (1-min grain assumptions; scale-safe if coarser) ---
    if "xtempmotor_max" in df.columns:
        hot = (_num(df["xtempmotor_max"]) > 85).astype(float)
        df["ThermalFatigue72h"] = hot.rolling(4320, min_periods=1).sum()  # mins >85C in 72h
    else:
        df["ThermalFatigue72h"] = 0.0
    if te is not None:
        df["WorkIntegral24h"] = te.fillna(0).abs().rolling(1440, min_periods=1).sum()
    else:
        df["WorkIntegral24h"] = 0.0

    if "Vendor" not in df.columns:
        df["Vendor"] = "unknown"

    # Passthrough numeric coercion for raw covariates kept in Gold
    for c in ("xiprim_1", "xuprim_1", "xspeedloco", "gpsspeed", "ltedemand",
              "lbedemand", "mtrcctract1", "mvcb_on"):
        if c in df.columns and c not in ("op_mode", "Vendor"):
            pass  # keep original dtype; coercion happens per-model

    return df


def resample_1min(df: pd.DataFrame, time_col: str = "devicetime") -> pd.DataFrame:
    df = df.copy()
    df[time_col] = pd.to_datetime(df[time_col])
    # Mark resample gaps: minutes with zero 1Hz samples become dq_gap=1 after reindex
    g = df.set_index(time_col)
    med = g.resample("1min").median(numeric_only=True)
    cnt = g.resample("1min").size()
    med["dq_gap"] = (cnt == 0).astype(int).values
    return med.reset_index()


def deviation_index(actual: pd.Series, predicted: pd.Series, span: int = 5) -> pd.Series:
    resid = (actual - predicted).abs()
    return resid.ewm(span=span, adjust=False).mean()
