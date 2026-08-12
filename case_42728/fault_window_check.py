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
    timeout=600,
)
cur = conn.cursor()

print("== the 13 fault rows in Lotus_LocoFaultData 06-09 Aug ==")
cur.execute("""
SELECT locoid, faulttime, FaultText FROM dbo.Lotus_LocoFaultData WITH (NOLOCK)
WHERE faulttime BETWEEN '2026-08-06' AND '2026-08-09'
ORDER BY faulttime
""")
for r in cur.fetchall():
    print("  ", r)

print("\n== RDSOJson fault: which locos have rows 06-09 Aug (top 15) ==")
cur.execute("""
SELECT TOP 15 LocoId, COUNT_BIG(*) AS n
FROM dbo.Lotus_LocoFaultData_RDSOJson WITH (NOLOCK)
WHERE FaultTime BETWEEN '2026-08-06' AND '2026-08-09'
GROUP BY LocoId ORDER BY n DESC
""")
for r in cur.fetchall():
    print("  ", r)

print("\n== RDSOJson fault: total rows 06-09 Aug ==")
cur.execute("""
SELECT COUNT_BIG(*) FROM dbo.Lotus_LocoFaultData_RDSOJson WITH (NOLOCK)
WHERE FaultTime BETWEEN '2026-08-06' AND '2026-08-09'
""")
print("  ", cur.fetchone()[0])

conn.close()
