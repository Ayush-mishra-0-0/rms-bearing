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

# column types
cur.execute("""
SELECT c.name, ty.name, c.max_length
FROM sys.columns c JOIN sys.types ty ON c.user_type_id=ty.user_type_id
WHERE c.object_id=OBJECT_ID('dbo.Lotus_LocoFaultData')
""")
print("Lotus_LocoFaultData columns:")
for r in cur.fetchall():
    print("  ", r)

# is the table actually populated in the 6-8 Aug window for ANY loco?
cur.execute("""
SELECT COUNT_BIG(*) FROM dbo.Lotus_LocoFaultData WITH (NOLOCK)
WHERE faulttime BETWEEN '2026-08-06' AND '2026-08-09'
""")
print("\nfault rows for ALL locos 06-09 Aug:", cur.fetchone()[0])

# try numeric 42728
cur.execute("SELECT COUNT_BIG(*) FROM dbo.Lotus_LocoFaultData WITH (NOLOCK) WHERE locoid=42728")
print("numeric locoid=42728:", cur.fetchone()[0])

# top locos by fault count in window (to see who HAS data)
cur.execute("""
SELECT TOP 10 locoid, COUNT_BIG(*) AS n
FROM dbo.Lotus_LocoFaultData WITH (NOLOCK)
WHERE faulttime BETWEEN '2026-08-06' AND '2026-08-09'
GROUP BY locoid ORDER BY n DESC
""")
print("\ntop locos by fault count 06-09 Aug:")
for r in cur.fetchall():
    print("  ", r)

conn.close()
