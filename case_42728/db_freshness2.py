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

# latest plausible telemetry overall (skip the 2044 garbage rows)
cur.execute("SELECT MAX(devicetime) FROM dbo.Lotus_loco_process_signals WITH (NOLOCK) WHERE devicetime < '2026-01-01'")
print("main table latest pre-2026:", cur.fetchone()[0])
cur.execute("SELECT MAX(devicetime) FROM dbo.Lotus_loco_process_signals WITH (NOLOCK) WHERE devicetime < '2027-01-01' AND devicetime >= '2026-01-01'")
print("main table max in 2026:", cur.fetchone()[0])
cur.execute("SELECT MAX(devicetime) FROM dbo.Lotus_loco_process_signals WITH (NOLOCK) WHERE devicetime BETWEEN '2026-08-01' AND '2026-08-31'")
print("main table max Aug2026:", cur.fetchone()[0])

cur.execute("SELECT MAX(FaultTime) FROM dbo.Lotus_LocoFaultData_RDSOJson WITH (NOLOCK)")
print("fault RDSOJson max FaultTime:", cur.fetchone()[0])
cur.execute("SELECT COUNT_BIG(*) FROM dbo.Lotus_LocoFaultData_RDSOJson WITH (NOLOCK) WHERE FaultTime BETWEEN '2026-08-07' AND '2026-08-10'")
print("fault RDSOJson rows 07-10Aug2026 (any loco):", cur.fetchone()[0])

# per-month counts for 2025-09 to 2025-12 to see when data flow stops
for m in ["2025-09", "2025-10", "2025-11", "2025-12", "2026-01", "2026-08"]:
    cur.execute("SELECT COUNT_BIG(*) FROM dbo.Lotus_loco_process_signals WITH (NOLOCK) WHERE devicetime >= ? AND devicetime < ?",
                m + "-01", (m + "-01") and (str(int(m[5:7]) + 1).zfill(2) if m[5:7] != "12" else "01"))
    print(f"main table rows {m}: {cur.fetchone()[0]}")
conn.close()
