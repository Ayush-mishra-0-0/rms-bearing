import os
from dotenv import load_dotenv
import pyodbc

load_dotenv()
conn = pyodbc.connect(
    "DRIVER={ODBC Driver 17 for SQL Server};"
    f"SERVER={os.getenv('DB_SERVER')};"
    f"DATABASE={os.getenv('DB_NAME')};"
    f"UID={os.getenv('DB_USERNAME')};"
    f"PWD={os.getenv('DB_PASSWORD')}",
    timeout=60,
)
cur = conn.cursor()

print("=== 42728 in newer/parallel signal tables ===")
for t in ["Lotus_loco_process_signals_4L", "Lotus_loco_process_signals_5", "Lotus_loco_process_signals_sma",
          "Lotus_loco_process_signals_snap", "Lotus_loco_process_signals_RDSOJson",
          "Lotus_LocoFaultData_4L", "Lotus_LocoFaultData_RDSOJson",
          "loco_process_signals", "Loco_Process_Signals_LocoNumber"]:
    try:
        cur.execute(f"SELECT TOP 0 * FROM dbo.[{t}]")
        cols = [d[0] for d in cur.description]
        lc = [x for x in cols if 'loco' in x.lower() or x.lower() in ('locoid','loconumber')]
        cur.execute(f"SELECT COUNT_BIG(*) FROM dbo.[{t}] WITH (NOLOCK) WHERE locoid=?", "42728")
        n = cur.fetchone()[0]
        extra = ""
        if n:
            cur.execute(f"SELECT MIN(devicetime), MAX(devicetime) FROM dbo.[{t}] WITH (NOLOCK) WHERE locoid=?", "42728")
            extra = f" range={cur.fetchone()}"
        print(f"{t}: rows={n}{extra} lococols={lc}")
    except Exception as e:
        print(f"{t}: err {str(e)[:70]}")

print("\n=== Is this DB live? latest plausible devicetime per table (no loco filter) ===")
for t in ["Lotus_loco_process_signals", "Lotus_loco_process_signals_4L", "Lotus_loco_process_signals_RDSOJson"]:
    try:
        cur.execute(f"SELECT MAX(devicetime) FROM dbo.[{t}] WITH (NOLOCK)")
        print(f"{t}: max devicetime = {cur.fetchone()[0]}")
    except Exception as e:
        print(f"{t}: {str(e)[:70]}")

print("\n=== any 2026 telemetry at all, for ANY loco (Lotus main table)? ===")
cur.execute("SELECT COUNT_BIG(*) FROM dbo.Lotus_loco_process_signals WITH (NOLOCK) WHERE devicetime >= '2026-01-01' AND devicetime < '2027-01-01'")
print("2026 rows (any loco):", cur.fetchone()[0])
conn.close()
