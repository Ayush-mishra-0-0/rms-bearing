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
    timeout=900,
)
cur = conn.cursor()

# any LocoId containing '42728' in fault RDSO table?
cur.execute("""
SELECT COUNT_BIG(*) FROM dbo.Lotus_LocoFaultData_RDSOJson WITH (NOLOCK)
WHERE LocoId LIKE '%42728%'
""")
print("RDSO fault LocoId LIKE %42728%:", cur.fetchone()[0])

# how does 42728 appear in the main telemetry table LocoId (to compare formats)?
cur.execute("""
SELECT TOP 3 LocoId, DeviceTime FROM dbo.Lotus_loco_process_signals_RDSOJson WITH (NOLOCK)
WHERE LocoId LIKE '%42728%'
""")
print("\nsample 42728 rows in process signals:")
for r in cur.fetchall():
    print("  ", r)

# what are the dominant fault types for the fleet in 06-09 Aug (decoded from payload)?
print("\n== top fault types (payload) for ALL locos 06-09 Aug ==")
cur.execute("""
SELECT TOP 25 JSON_VALUE(JsonPayload, '$.faulttext') AS ft, COUNT_BIG(*) AS n
FROM dbo.Lotus_LocoFaultData_RDSOJson WITH (NOLOCK)
WHERE FaultTime BETWEEN '2026-08-06' AND '2026-08-09'
  AND JSON_VALUE(JsonPayload, '$.faulttext') IS NOT NULL
GROUP BY JSON_VALUE(JsonPayload, '$.faulttext')
ORDER BY n DESC
""")
for r in cur.fetchall():
    print(f"  n={r[1]:7d}  {r[0]}")

conn.close()
