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
    timeout=90,
)
cur = conn.cursor()

# Check other telemetry/fault tables for 42728
for t in ["Lotus_loco_process_signals_4L", "Lotus_loco_process_signals_5", "Lotus_loco_process_signals_sma",
          "Lotus_loco_process_signals_RDSOJson", "Lotus_LocoFaultData", "Lotus_LocoFaultData_4L",
          "Lotus_LocoFaultData_RDSOJson", "RMSProcessEventData", "RMSProcessAnalogEventsData",
          "RMSGlobalAnalogEventData", "RMSAlerts", "AlertUserMessages22", "Locofault"]:
    try:
        cur.execute(f"SELECT COUNT_BIG(*) FROM dbo.[{t}] WITH (NOLOCK) WHERE locoid=?", "42728")
        n = cur.fetchone()[0]
        if n:
            cur.execute(f"SELECT MIN(devicetime), MAX(devicetime) FROM dbo.[{t}] WITH (NOLOCK) WHERE locoid=?", "42728")
            print(f"{t}: rows={n} range={cur.fetchone()}")
        else:
            print(f"{t}: 0 rows")
    except Exception as e:
        print(f"{t}: err {str(e)[:80]}")

# overall freshness: count rows per year in main telemetry table (sample via range query on indexed col)
print("\n--- global per-year row counts (Lotus_loco_process_signals) ---")
for y in (2024, 2025, 2026, 2027):
    cur.execute("SELECT COUNT_BIG(*) FROM dbo.Lotus_loco_process_signals WITH (NOLOCK) WHERE devicetime >= ? AND devicetime < ?",
                f"{y}-01-01", f"{y+1}-01-01")
    print(f"  {y}: {cur.fetchone()[0]}")
