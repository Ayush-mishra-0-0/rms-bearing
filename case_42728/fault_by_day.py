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
    timeout=1200,
)
cur = conn.cursor()

print("== any rows at all for 42728 ==")
cur.execute("SELECT COUNT_BIG(*) FROM dbo.Lotus_LocoFaultData WITH (NOLOCK) WHERE locoid='42728'")
print("all-time:", cur.fetchone()[0])

print("\n== rows around the event (Aug 2026) ==")
cur.execute(
    "SELECT COUNT_BIG(*) FROM dbo.Lotus_LocoFaultData WITH (NOLOCK) "
    "WHERE locoid='42728' AND faulttime BETWEEN '2026-08-01' AND '2026-09-01'"
)
print("Aug 2026:", cur.fetchone()[0])

print("\n== fault text counts by day 06-09 Aug 2026 (top types) ==")
cur.execute("""
SELECT CONVERT(varchar(10), faulttime, 120) AS d, FaultText, COUNT_BIG(*) AS n
FROM dbo.Lotus_LocoFaultData WITH (NOLOCK)
WHERE locoid='42728' AND faulttime BETWEEN '2026-08-06' AND '2026-08-10'
GROUP BY CONVERT(varchar(10), faulttime, 120), FaultText
ORDER BY d, n DESC
""")
rows = cur.fetchall()
if not rows:
    print("  (none)")
for r in rows:
    print(f"  {r[0]}  n={r[2]:5d}  {r[1]}")

conn.close()
