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

for t in ["Locofault", "Lotus_LocoFaultData", "Lotus_LocoFaultData_4L"]:
    print("=" * 60)
    print("TABLE:", t)
    try:
        cur.execute(f"SELECT TOP 0 * FROM dbo.[{t}]")
        print("  cols:", [d[0] for d in cur.description])
    except Exception as e:
        print("  schema err:", str(e)[:120])
    try:
        cur.execute(f"SELECT COUNT_BIG(*) FROM dbo.[{t}] WITH (NOLOCK)")
        print("  total rows:", cur.fetchone()[0])
    except Exception as e:
        print("  count err:", str(e)[:120])

conn.close()
