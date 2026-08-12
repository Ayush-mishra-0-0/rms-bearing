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

cur.execute("SELECT TOP 0 * FROM dbo.Lotus_LocoFaultData_RDSOJson")
cols = [d[0] for d in cur.description]
print("COLS:", cols)

cur.execute("SELECT COUNT_BIG(*) FROM dbo.Lotus_LocoFaultData_RDSOJson WITH (NOLOCK)")
print("total rows:", cur.fetchone()[0])

cur.execute("SELECT MIN(FaultTime), MAX(FaultTime) FROM dbo.Lotus_LocoFaultData_RDSOJson WITH (NOLOCK)")
print("time range:", cur.fetchone())

conn.close()
