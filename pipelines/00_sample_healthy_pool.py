"""00: sample deterministic healthy pool (train_50 / calib_20 / unseen_30) from DB master list.

Excludes EVERY loco appearing in owner_failure_classification.csv (122 failed locos),
ranks remaining by telemetry density in a fixed healthy window (Nov 2024, same season
as the Dec incidents), seed-shuffles, splits 50/20/30.

Writes: data/manifests/healthy_pool.csv (loco, rows_win, density, split, vendor)
Usage (rms venv, needs pyodbc+pandas only):
  $env:PYTHONPATH='C:\\Users\\CRIS\\AppData\\Local\\Programs\\Python\\Python312\\Lib\\site-packages'
  .\\rms\\Scripts\\python.exe pipelines/00_sample_healthy_pool.py
"""
from __future__ import annotations
import os
import pandas as pd
from dotenv import load_dotenv

MASTER_TABLE = "dbo.Loco_Process_Signals_LocoNumber"
SIGNAL_TABLE = "dbo.Lotus_loco_process_signals"
WIN_START, WIN_END = "2024-11-01 00:00:00", "2024-12-01 00:00:00"  # full-Nov pool-selection; extraction uses Nov1-4 3d
EXPECTED = 30 * 86400
MIN_DENSITY = 0.15
SEED = 42


def main() -> None:
    load_dotenv()
    import pyodbc
    conn = pyodbc.connect(
        "DRIVER={ODBC Driver 17 for SQL Server};"
        f"SERVER={os.environ['DB_SERVER']};DATABASE={os.environ['DB_NAME']};"
        f"UID={os.environ['DB_USERNAME']};PWD={os.environ['DB_PASSWORD']};"
        "TrustServerCertificate=yes;", timeout=120)
    cur = conn.cursor()

    fail = pd.read_csv("data/processed/owner_failure_classification.csv")
    loco_col = "Loco" if "Loco" in fail.columns else fail.columns[1]
    excluded = set(fail[loco_col].astype(str).str.strip())
    print(f"excluded failure locos: {len(excluded)}")

    cols = [r[0] for r in cur.execute(
        "SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS "
        "WHERE TABLE_NAME='Loco_Process_Signals_LocoNumber' ORDER BY ORDINAL_POSITION").fetchall()]
    print("master cols:", cols)
    num_col = "LocoNumber" if "LocoNumber" in cols else cols[0]
    master = [str(r[0]).strip() for r in cur.execute(
        f"SELECT DISTINCT {num_col} FROM {MASTER_TABLE} WITH (NOLOCK)").fetchall()]
    master = [m for m in master if m and m.isdigit() and m not in excluded]
    print(f"candidates after exclusion: {len(master)}")

    rows = cur.execute(
        f"SELECT locoid, COUNT_BIG(*) FROM {SIGNAL_TABLE} WITH (NOLOCK) "
        "WHERE devicetime>=? AND devicetime<? GROUP BY locoid",
        WIN_START, WIN_END).fetchall()
    print(f"active locos in window: {len(rows)}", flush=True)
    df = pd.DataFrame([(str(l).strip(), int(n)) for l, n in rows],
                      columns=["loco", "rows_win"])
    df = df[df["loco"].str.isdigit() & ~df["loco"].isin(excluded)]
    print(f"after digit+exclusion filter: {len(df)}", flush=True)
    df["density"] = df["rows_win"] / EXPECTED
    conn.close()
    df = df[df["density"] >= MIN_DENSITY].sort_values("rows_win", ascending=False).reset_index(drop=True)
    print(f"pool density>={MIN_DENSITY}: {len(df)} locos "
          f"(rows_win range {df['rows_win'].min()}..{df['rows_win'].max()})", flush=True)
    assert len(df) >= 100, f"only {len(df)} dense healthy locos, need >=100"

    # Deterministic shuffle then fixed split (documented, seed in manifest).
    pool = df.sample(frac=1.0, random_state=SEED).reset_index(drop=True)
    pool["split"] = (["train"] * 50 + ["calib"] * 20 + ["unseen"] * 30)[:len(pool)]
    pool = pool.head(100)
    print(pool["split"].value_counts().to_string())
    pool.to_csv("data/manifests/healthy_pool.csv", index=False)
    print("Wrote data/manifests/healthy_pool.csv (seed=42)")


if __name__ == "__main__":
    main()
