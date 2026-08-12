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

# all-time range for 42728 in signal RDSOJson (uses IX_RMS_Loco)
cur.execute("SELECT COUNT_BIG(*), MIN(DeviceTime), MAX(DeviceTime) FROM dbo.Lotus_loco_process_signals_RDSOJson WITH (NOLOCK) WHERE LocoId='42728'")
r = cur.fetchone()
print("42728 signal-RDSOJson: rows=%s range=%s -> %s" % (r[0], r[1], r[2]))

# rows in the failure window
cur.execute("SELECT COUNT_BIG(*) FROM dbo.Lotus_loco_process_signals_RDSOJson WITH (NOLOCK) WHERE LocoId='42728' AND DeviceTime BETWEEN '2026-08-07' AND '2026-08-11'")
print("42728 signal-RDSOJson rows 07-11 Aug 2026:", cur.fetchone()[0])
conn.close()
