import os
from dotenv import load_dotenv
import pyodbc

load_dotenv()
conn = pyodbc.connect(
    "DRIVER={ODBC Driver 17 for SQL Server};"
    f"SERVER={os.getenv('DB_SERVER')};"
    f"DATABASE=master;"
    f"UID={os.getenv('DB_USERNAME')};"
    f"PWD={os.getenv('DB_PASSWORD')}",
    timeout=30,
)
cur = conn.cursor()
cur.execute("SELECT name, create_date FROM sys.databases ORDER BY name")
for r in cur.fetchall():
    print(r)
conn.close()
