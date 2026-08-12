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

# RMSLocoMap - LomNumber column type?
cur.execute("SELECT COLUMN_NAME, DATA_TYPE FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME='RMSLocoMap'")
for r in cur.fetchall():
    print("RMSLocoMap col:", r)

# find 42728 as string
cur.execute("SELECT TOP 5 * FROM dbo.RMSLocoMap WITH (NOLOCK) WHERE CAST(LomNumber AS VARCHAR(20))='42728'")
for r in cur.fetchall():
    print("row:", r)

# Is there ANY data newer than 2025-10 in the whole table? check max devicetime (indexed on locoid+devicetime)
cur.execute("SELECT MAX(devicetime) FROM dbo.Lotus_loco_process_signals WITH (NOLOCK)")
print("global max devicetime:", cur.fetchone()[0])

# any rows for a known active loco? just check a sample of recent rows
cur.execute("SELECT TOP 5 locoid, devicetime FROM dbo.Lotus_loco_process_signals WITH (NOLOCK) ORDER BY devicetime DESC")
for r in cur.fetchall():
    print("recent:", r)
