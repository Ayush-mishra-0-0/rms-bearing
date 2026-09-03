"""Paper inputs + physics features + deviation index. Pure functions, tested."""
from __future__ import annotations
import pandas as pd

TEMP_COLS = ["xtempmotor1_1","xtempmotor2_1","xtempmotor3_1",
             "xtempmotor1_2","xtempmotor2_2","xtempmotor3_2"]

def add_core_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    have = [c for c in TEMP_COLS if c in df.columns]
    df["xtempmotor_max"] = df[have].max(axis=1) if have else None
    if "xtempmotor1_1" in df and "xtempmotor1_2" in df:
        df["Temp_Diff_Motor_1"] = (df["xtempmotor1_1"] - df["xtempmotor1_2"]).abs()
    if "xspeedloco" in df and "xtempmotor_max" in df:
        df["Temp_Gradient"] = df["xtempmotor_max"].diff()
    return df

def resample_1min(df: pd.DataFrame, time_col: str = "devicetime") -> pd.DataFrame:
    df = df.copy()
    df[time_col] = pd.to_datetime(df[time_col])
    return df.set_index(time_col).median(numeric_only=True).resample("1min").median(numeric_only=True).reset_index()

def deviation_index(actual: pd.Series, predicted: pd.Series, span: int = 5) -> pd.Series:
    resid = (actual - predicted).abs()
    return resid.ewm(span=span, adjust=False).mean()
