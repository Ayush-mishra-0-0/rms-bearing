"""Build Arm-A 1-min Gold parquet from extracted interim CSVs (no DB needed).

Same transform as pipelines/01 (add_core_features -> resample_1min).
Split (smoke scale, documented):
  train: healthy 30385 + 30380, 01-07 Dec 2024 (healthy only)
  calib: healthy 30385 + 30380, 08-10 Dec 2024 (healthy only, held-out days)
  test_37282 / test_30532 / test_37282_Nov / test_healthyAB: full windows
Run with SYSTEM python (pandas/pyarrow):
  C:\\Users\\CRIS\\AppData\\Local\\Programs\\Python\\Python312\\python.exe scripts\\build_gold_A.py
"""
import os
import sys

sys.path.insert(0, "src")
import pandas as pd
from rms_mlstm.features import add_core_features, resample_1min

BASE = "C:/Users/CRIS/Desktop/ayush/rms-bearing"
IN = {
    "healthyA": f"{BASE}/data/interim/healthyA_30385_10d.csv",
    "healthyB": f"{BASE}/data/interim/healthyB_30380_10d.csv",
    "t37282": f"{BASE}/data/interim/37282_10d.csv",
    "t30532": f"{BASE}/data/interim/30532_11d.csv",
    "t37282nov": f"{BASE}/data/interim/37282_Nov10d.csv",
}
OUTDIR = f"{BASE}/data/gold_A"
CUT = "2024-12-08 00:00:00"


def gold(df):
    return resample_1min(add_core_features(df))


def main():
    os.makedirs(OUTDIR, exist_ok=True)
    parts_tr, parts_cb = [], []
    for key in ("healthyA", "healthyB"):
        df = pd.read_csv(IN[key])
        df["devicetime"] = pd.to_datetime(df["devicetime"])
        g = gold(df)
        tr = g[g["devicetime"] < CUT]
        cb = g[g["devicetime"] >= CUT]
        parts_tr.append(tr)
        parts_cb.append(cb)
        print(f"{key}: gold={len(g)} train={len(tr)} calib={len(cb)}", flush=True)
    tr = pd.concat(parts_tr, ignore_index=True)
    cb = pd.concat(parts_cb, ignore_index=True)
    tr.to_parquet(f"{OUTDIR}/train_healthy.parquet", index=False)
    cb.to_parquet(f"{OUTDIR}/calib_healthy.parquet", index=False)
    print(f"train rows={len(tr)} calib rows={len(cb)}", flush=True)
    for key in ("t37282", "t30532", "t37282nov"):
        df = pd.read_csv(IN[key])
        g = gold(df)
        g.to_parquet(f"{OUTDIR}/{key}.parquet", index=False)
        print(f"{key}: gold={len(g)}", flush=True)
    for key in ("healthyA", "healthyB"):
        df = pd.read_csv(IN[key])
        g = gold(df)
        g.to_parquet(f"{OUTDIR}/test_{key}.parquet", index=False)
        print(f"test_{key}: gold={len(g)}", flush=True)


if __name__ == "__main__":
    main()
