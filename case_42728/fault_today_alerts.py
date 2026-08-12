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

print("== temptoday_fault: any 42728 ==")
cur.execute("SELECT COUNT_BIG(*) FROM dbo.temptoday_fault WITH (NOLOCK) WHERE locoid='42728'")
print("  rows:", cur.fetchone()[0])
cur.execute("SELECT DISTINCT locoid FROM dbo.temptoday_fault WITH (NOLOCK)")
ids = [r[0] for r in cur.fetchall()]
print("  distinct locoids (sample):", ids[:20], "... total", len(ids))

print("\n== RMSAlerts: any 42728 around Aug 2026 ==")
cur.execute("SELECT COUNT_BIG(*) FROM dbo.RMSAlerts WITH (NOLOCK) WHERE LocoID='42728'")
print("  all-time:", cur.fetchone()[0])
cur.execute("SELECT COUNT_BIG(*) FROM dbo.RMSAlerts WITH (NOLOCK) WHERE LocoID='42728' AND DeviceTime BETWEEN '2026-08-01' AND '2026-09-01'")
print("  Aug 2026:", cur.fetchone()[0])

conn.close()
