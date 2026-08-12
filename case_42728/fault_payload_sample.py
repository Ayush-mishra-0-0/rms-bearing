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

# sample one payload to see its structure
cur.execute("""
SELECT TOP 1 LocoId, FaultTime, JsonPayload FROM dbo.Lotus_LocoFaultData_RDSOJson WITH (NOLOCK)
WHERE FaultTime >= '2026-08-06' AND FaultTime <= '2026-08-09'
ORDER BY FaultTime
""")
r = cur.fetchone()
if r:
    print("LocoId:", r[0], "FaultTime:", r[1])
    print("Payload len:", len(r[2]) if r[2] else None)
    print("Payload:", (r[2] or "")[:600])
else:
    print("no rows in window")

conn.close()
