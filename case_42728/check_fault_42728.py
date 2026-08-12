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

# 1. schema of fault RDSOJson
cur.execute("SELECT TOP 0 * FROM dbo.Lotus_LocoFaultData_RDSOJson")
cols = [d[0] for d in cur.description]
print("Lotus_LocoFaultData_RDSOJson cols:", cols)

# 2. rows for 42728 in the fault window
cur.execute("SELECT COUNT_BIG(*) FROM dbo.Lotus_LocoFaultData_RDSOJson WITH (NOLOCK) WHERE LocoId='42728'")
print("42728 all-time fault rows:", cur.fetchone()[0])

cur.execute("SELECT COUNT_BIG(*) FROM dbo.Lotus_LocoFaultData_RDSOJson WITH (NOLOCK) WHERE LocoId='42728' AND FaultTime BETWEEN '2026-08-01' AND '2026-08-31'")
print("42728 fault rows Aug2026:", cur.fetchone()[0])

# 3. sample of rows around the failure
cur.execute("""
SELECT TOP 20 * FROM dbo.Lotus_LocoFaultData_RDSOJson WITH (NOLOCK)
WHERE LocoId='42728' ORDER BY FaultTime
""")
rows = cur.fetchall()
print(f"sample rows: {len(rows)}")
for r in rows:
    print("  ", r)
conn.close()
