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
    timeout=120,
)
cur = conn.cursor()

# sample a few rows in the failure window
cur.execute("""
SELECT TOP 5 Id, LocoId, DeviceTime, Vendor, LEFT(JsonPayload, 4000) AS payload
FROM dbo.Lotus_loco_process_signals_RDSOJson WITH (NOLOCK)
WHERE LocoId='42728' AND DeviceTime BETWEEN '2026-08-07' AND '2026-08-11'
ORDER BY DeviceTime
""")
for r in cur.fetchall():
    print("=" * 80)
    print("Id:", r[0], "| LocoId:", r[1], "| DeviceTime:", r[2], "| Vendor:", r[3])
    print("Payload[0:4000]:", r[4])
conn.close()
