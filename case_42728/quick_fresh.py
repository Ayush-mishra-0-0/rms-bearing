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

# Is there ANY data at all in Aug 2026 across the whole telemetry table?
cur.execute("SELECT COUNT_BIG(*) FROM dbo.Lotus_loco_process_signals WITH (NOLOCK) WHERE devicetime BETWEEN '2026-08-07' AND '2026-08-10'")
print("global rows 07-10 Aug 2026:", cur.fetchone()[0])

# fault tables for 42728
for t in ["Lotus_LocoFaultData", "Locofault"]:
    try:
        cur.execute(f"SELECT COUNT_BIG(*) FROM dbo.[{t}] WITH (NOLOCK) WHERE locoid=?", "42728")
        print(f"{t} for 42728:", cur.fetchone()[0])
    except Exception as e:
        print(f"{t}: err {str(e)[:90]}")

# event tables: count for 42728 if they have locoid
for t in ["RMSProcessEventData", "RMSProcessAnalogEventsData", "RMSGlobalAnalogEventData"]:
    try:
        cur.execute(f"SELECT TOP 0 * FROM dbo.[{t}]")
        cols = [d[0] for d in cur.description]
        lc = [x for x in cols if 'loco' in x.lower()]
        print(f"{t} cols(loco): {lc}")
    except Exception as e:
        print(f"{t}: {str(e)[:90]}")
conn.close()
