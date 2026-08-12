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

print("== rmslocolist 42728 ==")
for t in ["rmslocolist", "rmslocolist"]:
    try:
        cur.execute(f"SELECT TOP 0 * FROM dbo.[{t}]")
        print("  cols:", [d[0] for d in cur.description])
        cur.execute("SELECT * FROM dbo.[" + t + "] WHERE LocoNumber='42728' OR LocoNumber=42728 OR Locoid='42728' OR LocoId='42728'")
        for r in cur.fetchall():
            print("  row:", r)
    except Exception as e:
        print("  err:", str(e)[:100])

print("\n== temptoday_fault ==")
try:
    cur.execute("SELECT TOP 0 * FROM dbo.temptoday_fault")
    print("  cols:", [d[0] for d in cur.description])
    cur.execute("SELECT COUNT_BIG(*) FROM dbo.temptoday_fault WITH (NOLOCK)")
    print("  rows:", cur.fetchone()[0])
except Exception as e:
    print("  err:", str(e)[:100])

print("\n== AlertUserMessages22 sample ==")
try:
    cur.execute("SELECT TOP 0 * FROM dbo.AlertUserMessages22")
    print("  cols:", [d[0] for d in cur.description])
except Exception as e:
    print("  err:", str(e)[:100])

print("\n== RMSAlerts ==")
try:
    cur.execute("SELECT TOP 0 * FROM dbo.RMSAlerts")
    print("  cols:", [d[0] for d in cur.description])
except Exception as e:
    print("  err:", str(e)[:100])

conn.close()
