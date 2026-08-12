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

# 1. any rows for this loco at all?
cur.execute("SELECT COUNT_BIG(*) FROM dbo.Lotus_LocoFaultData_RDSOJson WITH (NOLOCK) WHERE LocoId='42728'")
print("42728 all-time fault rows:", cur.fetchone()[0])

# 2. rows in the window of interest
cur.execute(
    "SELECT COUNT_BIG(*) FROM dbo.Lotus_LocoFaultData_RDSOJson WITH (NOLOCK) "
    "WHERE LocoId='42728' AND FaultTime BETWEEN '2026-08-06' AND '2026-08-09'"
)
print("42728 fault rows 06-09 Aug 2026:", cur.fetchone()[0])

conn.close()
