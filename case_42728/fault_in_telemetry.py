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

# check telemetry RDSOJson table schema for 42728
cur.execute("SELECT TOP 0 * FROM dbo.Lotus_loco_process_signals_RDSOJson")
print("cols:", [d[0] for d in cur.description])

# get one payload for 42728 in the window
cur.execute("""
SELECT TOP 1 * FROM dbo.Lotus_loco_process_signals_RDSOJson WITH (NOLOCK)
WHERE LocoId='42728' AND DeviceTime BETWEEN '2026-08-07' AND '2026-08-08'
ORDER BY DeviceTime
""")
r = cur.fetchone()
if r:
    for c, v in zip([d[0] for d in cur.description], r):
        s = str(v)
        print(f"  {c}: {s[:400]}")
conn.close()
