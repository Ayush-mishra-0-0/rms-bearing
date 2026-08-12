import os
import pyodbc
from dotenv import load_dotenv

load_dotenv()


def conn():
    return pyodbc.connect(
        f"DRIVER={{ODBC Driver 17 for SQL Server}};"
        f"SERVER={os.getenv('DB_SERVER')};"
        f"DATABASE={os.getenv('DB_NAME')};"
        f"UID={os.getenv('DB_USERNAME')};"
        f"PWD={os.getenv('DB_PASSWORD')};"
        f"TrustServerCertificate=yes;",
        timeout=60,
    )


c = conn()
cur = c.cursor()

print("--- Telemetry table schema: dbo.Lotus_loco_process_signals ---")
cur.execute(
    """SELECT COLUMN_NAME, DATA_TYPE, CHARACTER_MAXIMUM_LENGTH
       FROM INFORMATION_SCHEMA.COLUMNS
       WHERE TABLE_NAME='Lotus_loco_process_signals'
       ORDER BY ORDINAL_POSITION"""
)
cols = cur.fetchall()
for col in cols:
    print(f"  {col.COLUMN_NAME:<45} {col.DATA_TYPE:<15} {col.CHARACTER_MAXIMUM_LENGTH}")

print("\n--- Vendor(s) for loco 42728 ---")
cur.execute("SELECT DISTINCT Vendor FROM dbo.Lotus_loco_process_signals WITH (NOLOCK) WHERE locoid=?", "42728")
for r in cur.fetchall():
    print("  ", r)

c.close()
