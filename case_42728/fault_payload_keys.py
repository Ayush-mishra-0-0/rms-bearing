import os, json
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

# all keys in a sample payload
cur.execute("""
SELECT TOP 1 JsonPayload FROM dbo.Lotus_loco_process_signals_RDSOJson WITH (NOLOCK)
WHERE LocoId='42728' AND DeviceTime BETWEEN '2026-08-07' AND '2026-08-08'
ORDER BY DeviceTime
""")
p = json.loads(cur.fetchone()[0])
print("payload keys:", len(p))
for k in sorted(p.keys()):
    v = p[k]
    print(f"  {k}: {str(v)[:60]}")

conn.close()
