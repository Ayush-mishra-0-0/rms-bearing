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
    timeout=120,
)
cur = conn.cursor()

cur.execute("SELECT * FROM dbo.Locofault WITH (NOLOCK) WHERE locoid='42728'")
rows = cur.fetchall()
print("Locofault 42728 rows:", len(rows))
for r in rows:
    print("  ", r)

# sample to see what it holds
cur.execute("SELECT TOP 10 * FROM dbo.Locofault WITH (NOLOCK)")
print("\nsample:")
for r in cur.fetchall():
    print("  ", r)

conn.close()
