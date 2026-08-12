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

for t in ["RMSProcessEventData", "RMSProcessAnalogEventsData", "RMSGlobalAnalogEventData"]:
    print("=" * 60)
    print("TABLE:", t)
    try:
        cur.execute(f"SELECT TOP 0 * FROM dbo.[{t}]")
        print("  cols:", [d[0] for d in cur.description])
    except Exception as e:
        print("  schema err:", str(e)[:120]); continue
    try:
        cur.execute(f"SELECT COUNT_BIG(*) FROM dbo.[{t}] WITH (NOLOCK)")
        print("  total rows:", cur.fetchone()[0])
    except Exception as e:
        print("  count err:", str(e)[:120]); continue

# try to find rows for 42728 in whichever col name matches
for t in ["RMSProcessEventData", "RMSProcessAnalogEventsData", "RMSGlobalAnalogEventData"]:
    try:
        cur.execute(f"SELECT TOP 0 * FROM dbo.[{t}]")
        cols = [d[0] for d in cur.description]
        loco_col = next((c for c in cols if 'loco' in c.lower() or 'loc' in c.lower()), None)
        if loco_col:
            cur.execute(f"SELECT COUNT_BIG(*) FROM dbo.[{t}] WITH (NOLOCK) WHERE [{loco_col}]='42728'")
            print(f"  {t}[{loco_col}]=42728 rows:", cur.fetchone()[0])
    except Exception as e:
        print(f"  {t} query err:", str(e)[:120])

conn.close()
