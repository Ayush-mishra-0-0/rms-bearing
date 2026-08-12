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
    timeout=300,
)
cur = conn.cursor()

print("=== signal RDSOJson: is 42728 present, and what's its date range? ===")
cur.execute("SELECT COUNT_BIG(*) FROM dbo.Lotus_loco_process_signals_RDSOJson WITH (NOLOCK) WHERE LocoId='42728'")
print("42728 signal-RDSOJson rows:", cur.fetchone()[0])

# date range for 42728 if present
cur.execute("SELECT MIN(DeviceTime), MAX(DeviceTime) FROM dbo.Lotus_loco_process_signals_RDSOJson WITH (NOLOCK) WHERE LocoId='42728'")
r = cur.fetchone()
print("42728 signal-RDSOJson range:", r)

# overall freshness of signal RDSOJson
cur.execute("SELECT MAX(DeviceTime) FROM dbo.Lotus_loco_process_signals_RDSOJson WITH (NOLOCK)")
print("signal-RDSOJson global max DeviceTime:", cur.fetchone()[0])
cur.execute("SELECT COUNT_BIG(*) FROM dbo.Lotus_loco_process_signals_RDSOJson WITH (NOLOCK) WHERE DeviceTime BETWEEN '2026-08-07' AND '2026-08-11'")
print("signal-RDSOJson rows 07-11 Aug 2026 (any loco):", cur.fetchone()[0])

print("\n=== which locos report faults in the failure window? (sample) ===")
cur.execute("""
SELECT TOP 30 LocoId, COUNT_BIG(*) AS n
FROM dbo.Lotus_LocoFaultData_RDSOJson WITH (NOLOCK)
WHERE FaultTime BETWEEN '2026-08-07' AND '2026-08-11'
GROUP BY LocoId ORDER BY n DESC
""")
for r in cur.fetchall():
    print("  ", r)
conn.close()
