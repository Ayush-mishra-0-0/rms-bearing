import os
from dotenv import load_dotenv
import pyodbc
import json
import csv

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

# date distribution first (cheap): group by day for 42728 in this table
cur.execute("""
SELECT CONVERT(char(10), DeviceTime, 120) AS d, COUNT_BIG(*)
FROM dbo.Lotus_loco_process_signals_RDSOJson WITH (NOLOCK)
WHERE LocoId='42728' AND DeviceTime BETWEEN '2025-01-01' AND '2026-12-31'
GROUP BY CONVERT(char(10), DeviceTime, 120)
ORDER BY d
""")
print("=== day-wise row counts for 42728 (RDSOJson signal) ===")
for r in cur.fetchall():
    print("  ", r)

conn.close()
