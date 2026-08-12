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

# 1. full row-count / time range for loco 42728 in Lotus_loco_process_signals
cur.execute("SELECT COUNT_BIG(*), MIN(devicetime), MAX(devicetime) FROM dbo.Lotus_loco_process_signals WITH (NOLOCK) WHERE locoid=?", "42728")
print("Lotus_loco_process_signals 42728:", cur.fetchone())

# 2. any rows in 2026?
cur.execute("SELECT COUNT_BIG(*) FROM dbo.Lotus_loco_process_signals WITH (NOLOCK) WHERE locoid=? AND devicetime >= '2026-01-01'", "42728")
print("rows 2026+:", cur.fetchone()[0])
cur.execute("SELECT COUNT_BIG(*) FROM dbo.Lotus_loco_process_signals WITH (NOLOCK) WHERE locoid=? AND devicetime BETWEEN '2026-08-07' AND '2026-08-10'", "42728")
print("rows 07-10 Aug 2026:", cur.fetchone()[0])

# 3. RMSLocoMap entries for 42728
cur.execute("SELECT * FROM dbo.RMSLocoMap WITH (NOLOCK) WHERE LomNumber=42728")
for r in cur.fetchall():
    print("RMSLocoMap:", r)

# 4. is there another loco number mapping? check rmslocolist
try:
    cur.execute("SELECT TOP 3 * FROM dbo.rmslocolist WITH (NOLOCK) WHERE lomo_num=42728 OR loco_no=42728")
    for r in cur.fetchall():
        print("rmslocolist:", r)
except Exception as e:
    print("rmslocolist err:", e)
