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

# 4L signal table
print("=== Lotus_loco_process_signals_4L (16 cols) ===")
try:
    cur.execute("SELECT TOP 3 * FROM dbo.Lotus_loco_process_signals_4L WITH (NOLOCK) WHERE Locoid='42728'")
    r = cur.fetchall()
    print(f"rows for 42728 (sample): {len(r)}")
    for row in r[:3]:
        print("  ", row)
except Exception as e:
    print("err:", str(e)[:90])

# RDSOJson signal table
print("\n=== Lotus_loco_process_signals_RDSOJson (6 cols) ===")
try:
    cur.execute("SELECT TOP 5 * FROM dbo.Lotus_loco_process_signals_RDSOJson WITH (NOLOCK) WHERE LocoId='42728'")
    r = cur.fetchall()
    print(f"rows for 42728 (sample): {len(r)}")
    for row in r[:5]:
        print("  ", row)
except Exception as e:
    print("err:", str(e)[:90])

# fault tables 4L / RDSOJson for 42728
print("\n=== Lotus_LocoFaultData_4L ===")
try:
    cur.execute("SELECT TOP 5 * FROM dbo.Lotus_LocoFaultData_4L WITH (NOLOCK) WHERE locoid='42728'")
    r = cur.fetchall()
    print(f"rows for 42728: {len(r)}")
    for row in r[:5]:
        print("  ", row)
except Exception as e:
    print("err:", str(e)[:90])

print("\n=== Lotus_LocoFaultData_RDSOJson ===")
try:
    cur.execute("SELECT TOP 5 * FROM dbo.Lotus_LocoFaultData_RDSOJson WITH (NOLOCK) WHERE LocoId='42728'")
    r = cur.fetchall()
    print(f"rows for 42728: {len(r)}")
    for row in r[:5]:
        print("  ", row)
except Exception as e:
    print("err:", str(e)[:90])

# any 2026 data in RDSOJson tables (any loco) - count by year quickly
print("\n=== RDSOJson 2026 rows (any loco) ===")
for t, dt in [("Lotus_loco_process_signals_RDSOJson", "DeviceTime"), ("Lotus_LocoFaultData_RDSOJson", "FaultTime")]:
    try:
        cur.execute(f"SELECT COUNT_BIG(*) FROM dbo.[{t}] WITH (NOLOCK) WHERE {dt} BETWEEN '2026-08-07' AND '2026-08-10'")
        print(f"{t} rows 07-10Aug2026:", cur.fetchone()[0])
    except Exception as e:
        print(f"{t}: {str(e)[:70]}")
conn.close()
