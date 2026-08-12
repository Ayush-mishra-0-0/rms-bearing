import os
from dotenv import load_dotenv
import pyodbc

load_dotenv()
conn = pyodbc.connect(
    "DRIVER={ODBC Driver 17 for SQL Server};"
    f"SERVER={os.getenv('DB_SERVER')};"
    f"DATABASE={os.getenv('DB_NAME')};"
    f"UID={os.getenv('DB_USERNAME')};"
    f"PWD={os.getenv('DB_PASSWORD')}"
)
cur = conn.cursor()

tables = ["RMSProcessEventData", "RMSGlobalAnalogEventData", "RMSProcessAnalogEventsData", "RMSAlerts", "LocoStatus", "AlertUserMessages22"]

for t in tables:
    # schema
    try:
        cur.execute(f"""
        SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_NAME=? ORDER BY ORDINAL_POSITION
        """, t)
        cols = [r[0] for r in cur.fetchall()]
        print(f"\n=== {t} columns: {', '.join(cols[:25])} ..." if len(cols) > 25 else f"\n=== {t} columns: {', '.join(cols)}")
    except Exception as e:
        print(f"\n=== {t}: schema error {e}")
        continue

    # look for loco-number columns and count rows for 42728
    loco_cols = [c for c in cols if any(k in c.lower() for k in ("loco", "number", "lno", "train"))]
    for c in loco_cols:
        try:
            cur.execute(f"SELECT COUNT(*) FROM dbo.[{t}] WHERE CAST([{c}] AS VARCHAR(20)) = '42728'")
            n = cur.fetchone()[0]
            print(f"    loco col [{c}]: rows for 42728 = {n}")
        except Exception as e:
            try:
                cur.execute(f"SELECT COUNT(*) FROM dbo.[{t}] WHERE [{c}] = 42728")
                n = cur.fetchone()[0]
                print(f"    loco col [{c}] (int): rows for 42728 = {n}")
            except Exception as e2:
                print(f"    loco col [{c}]: err {e2}")
    cur.execute(f"SELECT COUNT(*) FROM dbo.[{t}]")
    print(f"    total rows: {cur.fetchone()[0]}")
