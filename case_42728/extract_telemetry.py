import os
import pyodbc
import csv
from dotenv import load_dotenv

load_dotenv()

c = pyodbc.connect(
    f"DRIVER={{ODBC Driver 17 for SQL Server}};"
    f"SERVER={os.getenv('DB_SERVER')};"
    f"DATABASE={os.getenv('DB_NAME')};"
    f"UID={os.getenv('DB_USERNAME')};"
    f"PWD={os.getenv('DB_PASSWORD')};"
    f"TrustServerCertificate=yes;",
    timeout=120,
)
cur = c.cursor()

print("--- Other fault-ish tables for loco 42728 ---")
for tbl in ("dbo.Locofault", "dbo.RMSAlerts", "dbo.LocoStatus", "dbo.WheelData"):
    try:
        cur.execute(f"SELECT TOP 0 * FROM {tbl}")
        cols = [d[0] for d in cur.description]
        cur.execute(f"SELECT COUNT_BIG(*) FROM {tbl} WITH (NOLOCK) WHERE locoid=?", "42728")
        print(f"  {tbl}: rows={cur.fetchone()[0]} cols={cols[:12]}")
    except Exception as e:
        print(f"  {tbl}: {e}")

print("\n--- Full telemetry extraction to CSV ---")
cur.execute(
    "SELECT * FROM dbo.Lotus_loco_process_signals WITH (NOLOCK) WHERE locoid=? ORDER BY devicetime",
    "42728",
)
cols = [d[0] for d in cur.description]
out = "C:/Users/CRIS/Desktop/ayush/rms-bearing/case_42728/telemetry_42728_raw.csv"
n = 0
with open(out, "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(cols)
    while True:
        rows = cur.fetchmany(20000)
        if not rows:
            break
        w.writerows(rows)
        n += len(rows)
        print(f"  ...{n}")
print("DONE rows:", n)
c.close()
