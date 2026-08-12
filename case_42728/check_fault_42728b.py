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

# is 42728 present in fault RDSOJson at all? scan by LocoId (slow but one-shot)
cur.execute("SELECT COUNT_BIG(*) FROM dbo.Lotus_LocoFaultData_RDSOJson WITH (NOLOCK) WHERE LocoId='42728'")
print("42728 all-time fault rows:", cur.fetchone()[0])

cur.execute("SELECT COUNT_BIG(*) FROM dbo.Lotus_LocoFaultData_RDSOJson WITH (NOLOCK) WHERE LocoId='42728' AND FaultTime BETWEEN '2026-08-07' AND '2026-08-11'")
print("42728 fault rows 07-11 Aug 2026:", cur.fetchone()[0])

cur.execute("""
SELECT TOP 20 * FROM dbo.Lotus_LocoFaultData_RDSOJson WITH (NOLOCK)
WHERE LocoId='42728' AND FaultTime BETWEEN '2026-08-07' AND '2026-08-11'
ORDER BY FaultTime
""")
rows = cur.fetchall()
print("sample rows:", len(rows))
for r in rows:
    print("  ", r)
conn.close()
