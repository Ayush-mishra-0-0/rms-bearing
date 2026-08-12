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

# 1. what's the max/min devicetime in Lotus_loco_process_signals?
for t in ["Lotus_loco_process_signals", "Lotus_loco_process_signals_sma", "Lotus_loco_process_signals_snap",
          "Lotus_loco_process_signals_5", "Lotus_LocoFaultData", "RMSProcessEventData",
          "RMSProcessAnalogEventsData", "RMSGlobalAnalogEventData"]:
    try:
        cur.execute(f"SELECT MIN(devicetime), MAX(devicetime), COUNT(*) FROM dbo.[{t}]")
        mn, mx, n = cur.fetchone()
        print(f"{t}: count={n} min={mn} max={mx}")
    except Exception as e:
        # maybe no devicetime column
        try:
            cur.execute(f"""
            SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME=? ORDER BY ORDINAL_POSITION
            """, t)
            cols = [r[0] for r in cur.fetchall()]
            dc = [c for c in cols if 'time' in c.lower() or 'date' in c.lower()]
            print(f"{t}: cols timeish={dc}")
        except Exception as e2:
            print(f"{t}: err {e2}")

# 2. is there ANY 2026 data for loco 42728 in Lotus_loco_process_signals?
try:
    cur.execute("""
    SELECT MIN(devicetime), MAX(devicetime), COUNT(*) FROM dbo.Lotus_loco_process_signals
    WHERE loconumber=42728 AND devicetime >= '2026-01-01'
    """)
    mn, mx, n = cur.fetchone()
    print(f"\nLotus_loco_process_signals for 42728 in 2026: count={n} min={mn} max={mx}")
except Exception as e:
    print("err checking 2026 rows:", e)

# 3. locate the loco-number column name in Lotus_loco_process_signals
try:
    cur.execute("SELECT TOP 1 * FROM dbo.Lotus_loco_process_signals")
    cols = [d[0] for d in cur.description]
    print("\nLotus_loco_process_signals cols:", cols)
except Exception as e:
    print("err:", e)
