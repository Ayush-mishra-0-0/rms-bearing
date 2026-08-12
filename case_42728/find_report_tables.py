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

cur.execute("""
SELECT TABLE_SCHEMA, TABLE_NAME FROM INFORMATION_SCHEMA.TABLES
WHERE TABLE_TYPE='BASE TABLE'
ORDER BY TABLE_NAME
""")
tabs = [f"{s}.{t}" for s, t in cur.fetchall()]
print(f"Total tables: {len(tabs)}")

keywords = ["report", "incident", "failure", "fault", "alert", "event", "case", "slam", "owner", "doc", "complaint", "loco", "tm", "axle", "log", "occur", "register", "issue", "complaint"]
for k in keywords:
    hits = [t for t in tabs if k.lower() in t.lower()]
    if hits:
        print(f"\n[{k}] {len(hits)}:")
        for h in hits[:20]:
            print("   ", h)
