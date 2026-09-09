"""Pool sampling v2: same logic as 00_sample_healthy_pool.py but per-loco count queries
(batched IN lists over the indexed (locoid, devicetime) window) to avoid the full-table
GROUP BY that times out.

Nov-2024 window, excludes the 122 owner-failure locos, density >= 0.15, deterministic
seed-42 split 50 train / 20 calib / 30 unseen.
"""
from __future__ import annotations
import os
import pandas as pd
from dotenv import load_dotenv

MASTER_TABLE = "dbo.Loco_Process_Signals_LocoNumber"
SIGNAL_TABLE = "dbo.Lotus_loco_process_signals"
WIN_START, WIN_END = "2024-11-01 00:00:00", "2024-12-01 00:00:00"
EXPECTED = 30 * 86400
MIN_DENSITY = 0.15
SEED = 42


def main() -> None:
    load_dotenv(__file__.rsplit("\\", 2)[0] + r"\monitoring\.env")
    import pyodbc
    conn = pyodbc.connect(
        "DRIVER={ODBC Driver 17 for SQL Server};"
        f"SERVER={os.environ['DB_SERVER']};DATABASE={os.environ['DB_NAME']};"
        f"UID={os.environ['DB_USERNAME']};PWD={os.environ['DB_PASSWORD']};"
        "TrustServerCertificate=yes;", timeout=300)
    cur = conn.cursor()

    fail = pd.read_csv("data/processed/owner_failure_classification.csv")
    loco_col = "Loco" if "Loco" in fail.columns else fail.columns[1]
    excluded = set(fail[loco_col].astype(str).str.strip())
    print(f"excluded failure locos: {len(excluded)}")

    master = [str(r[0]).strip() for r in cur.execute(
        f"SELECT DISTINCT LocoNumber FROM {MASTER_TABLE} WITH (NOLOCK)").fetchall()]
    master = [m for m in master if m and m.isdigit() and m not in excluded]
    print(f"candidates after exclusion: {len(master)}")

    rows_win = {}
    B = 40
    for bi in range(0, len(master), B):
        batch = master[bi:bi + B]
        inlist = ",".join(f"'{m}'" for m in batch)
        q = (f"SELECT locoid, COUNT_BIG(*) FROM {SIGNAL_TABLE} WITH (NOLOCK) "
             f"WHERE devicetime>=? AND devicetime<? AND locoid IN ({inlist}) "
             f"GROUP BY locoid OPTION (RECOMPILE)")
        for l, n in cur.execute(q, WIN_START, WIN_END).fetchall():
            rows_win[str(l).strip()] = int(n)
        print(f"  batch {bi//B + 1}/{(len(master)+B-1)//B}: cum locos with rows={len(rows_win)}", flush=True)
    conn.close()

    df = pd.DataFrame(sorted(rows_win.items()), columns=["loco", "rows_win"])
    df = df[df["loco"].str.isdigit() & ~df["loco"].isin(excluded)]
    df["density"] = df["rows_win"] / EXPECTED
    df = df[df["density"] >= MIN_DENSITY].sort_values("rows_win", ascending=False).reset_index(drop=True)
    print(f"pool density>={MIN_DENSITY}: {len(df)} locos "
          f"(rows_win range {df['rows_win'].min()}..{df['rows_win'].max()})")
    assert len(df) >= 100, f"only {len(df)} dense healthy locos, need >=100"

    pool = df.sample(frac=1.0, random_state=SEED).reset_index(drop=True)
    pool["split"] = (["train"] * 50 + ["calib"] * 20 + ["unseen"] * 30)[:len(pool)]
    pool = pool.head(100)
    print(pool["split"].value_counts().to_string())
    pool.to_csv("data/manifests/healthy_pool.csv", index=False)
    print("Wrote data/manifests/healthy_pool.csv (seed=42)")


if __name__ == "__main__":
    main()
