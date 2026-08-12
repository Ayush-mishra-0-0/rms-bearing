"""Single-locomotive forensic audit: which telemetry table holds data, and how much.

Answers, for one loco and one incident day:
  1. Which candidate telemetry tables exist?
  2. For each existing table, how many rows, min/max timestamp, vendor(s)?
  3. How many rows fall inside the pre-failure probe window?
  4. Sampling continuity near the reference fault timestamp.

Never extracts full telemetry rows; prints the audit only.
"""
from __future__ import annotations

import argparse
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

TABLES = (
    "dbo.Lotus_loco_process_signals",
    "dbo.Lotus_loco_process_signals_4L",
    "dbo.Lotus_loco_process_signals_5",
    "dbo.Lotus_loco_process_signals_sma",
    "dbo.Locoprocessdata",
)


def main() -> None:
    load_dotenv()
    p = argparse.ArgumentParser()
    p.add_argument("--loco", default="30751")
    p.add_argument("--day", default="2024-12-16")
    p.add_argument("--fault-time", default="2024-12-16 17:30:00")
    p.add_argument("--lookback-hours", type=int, default=7)
    p.add_argument("--timeout", type=int, default=120)
    args = p.parse_args()

    incident = datetime.strptime(args.day, "%Y-%m-%d")
    fault_ts = datetime.strptime(args.fault_time, "%Y-%m-%d %H:%M:%S")
    probe_start = fault_ts - timedelta(hours=args.lookback_hours)

    import pyodbc
    conn = pyodbc.connect(
        f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={os.environ['DB_SERVER']};"
        f"DATABASE={os.environ['DB_NAME']};UID={os.environ['DB_USERNAME']};"
        f"PWD={os.environ['DB_PASSWORD']};TrustServerCertificate=yes;"
    )
    conn.timeout = args.timeout
    cur = conn.cursor()

    print(f"=== Forensic audit: loco {args.loco}, incident day {args.day} ===")
    print(f"Reference fault time: {fault_ts}   Probe window: {probe_start} .. {fault_ts}\n")

    print("--- 1. Existing tables ---")
    existing = []
    for table in TABLES:
        cur.execute(
            "SELECT CASE WHEN OBJECT_ID(?, 'U') IS NULL THEN 0 ELSE 1 END", table
        )
        if cur.fetchone()[0]:
            existing.append(table)
            print(f"  EXISTS  {table}")
        else:
            print(f"  MISSING {table}")
    if not existing:
        print("  No telemetry tables found. Audit stops.")
        return

    print("\n--- 2. Table-level availability for this loco (all history) ---")
    print(f"  {'table':<40} {'rows':>12} {'first_ts':<19} {'last_ts':<19} {'vendor(s)'}")
    coverage = {}
    for table in existing:
        if "Lotus_loco_process_signals_4L" in table:
            cur.execute(f"SELECT COUNT_BIG(*) FROM {table} WITH (NOLOCK) WHERE Locoid = ?", args.loco)
            rows = cur.fetchone()[0]
            coverage[table] = (rows, None, None)
            print(f"  {table:<40} {rows:>12} {'(no devicetime)':<19} {'':<19} n/a")
            continue
        cur.execute(
            f"""SELECT COUNT_BIG(*), MIN(devicetime), MAX(devicetime)
                FROM {table} WITH (NOLOCK)
                WHERE locoid = ?""",
            args.loco,
        )
        rows, first_ts, last_ts = cur.fetchone()
        vendors = []
        try:
            cur.execute(
                f"SELECT DISTINCT Vendor FROM {table} WITH (NOLOCK) WHERE locoid = ?",
                args.loco,
            )
            vendors = [r[0] for r in cur.fetchall()]
        except pyodbc.ProgrammingError:
            vendors = ["n/a"]
        coverage[table] = (rows, first_ts, last_ts)
        print(f"  {table:<40} {rows if rows is not None else 'NULL':>12} {str(first_ts):<19} {str(last_ts):<19} {','.join(str(v) for v in vendors)}")

    print("\n--- 3. Probe window (pre-failure) rows per table ---")
    print(f"  window = {probe_start} .. {fault_ts}")
    for table in existing:
        if "Lotus_loco_process_signals_4L" in table:
            print(f"  {table:<40} skipped (no devicetime column)")
            continue
        cur.execute(
            f"""SELECT COUNT_BIG(*), MIN(devicetime), MAX(devicetime)
                FROM {table} WITH (NOLOCK)
                WHERE locoid = ?
                  AND devicetime >= ? AND devicetime < ?""",
            args.loco, probe_start, fault_ts,
        )
        rows, first_ts, last_ts = cur.fetchone()
        print(f"  {table:<40} {rows if rows is not None else 'NULL':>12}  {str(first_ts):<19} .. {str(last_ts):<19}")

    print("\n--- 4. Sampling continuity (rows per hour) around fault time ---")
    for table in existing:
        if "Lotus_loco_process_signals_4L" in table:
            print(f"  {table}: skipped (no devicetime column)")
            continue
        cur.execute(
            f"""SELECT CONVERT(date, devicetime) AS d,
                       DATEPART(hour, devicetime) AS h,
                       COUNT_BIG(*) AS n
                FROM {table} WITH (NOLOCK)
                WHERE locoid = ?
                  AND devicetime >= DATEADD(hour, -8, ?)
                  AND devicetime < ?
                GROUP BY CONVERT(date, devicetime), DATEPART(hour, devicetime)
                ORDER BY d, h""",
            args.loco, fault_ts, fault_ts,
        )
        rows = cur.fetchall()
        if not rows:
            print(f"  {table}: no rows in the 8h window before fault time")
            continue
        print(f"  {table}:")
        for d, h, n in rows:
            print(f"    {d} {h:02d}:00-{h:02d}:59  {n}")

    conn.close()


if __name__ == "__main__":
    main()
