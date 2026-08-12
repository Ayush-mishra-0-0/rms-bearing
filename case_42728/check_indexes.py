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
    timeout=60,
)
cur = conn.cursor()

cur.execute("""
SELECT i.name, i.type_desc, c.name AS col
FROM sys.indexes i
JOIN sys.index_columns ic ON i.object_id=ic.object_id AND i.index_id=ic.index_id
JOIN sys.columns c ON ic.object_id=c.object_id AND ic.column_id=c.column_id
WHERE i.object_id=OBJECT_ID('dbo.Lotus_LocoFaultData_RDSOJson')
ORDER BY i.name, ic.key_ordinal
""")
for r in cur.fetchall():
    print(r)

cur.execute("""
SELECT i.name, i.type_desc, c.name AS col
FROM sys.indexes i
JOIN sys.index_columns ic ON i.object_id=ic.object_id AND i.index_id=ic.index_id
JOIN sys.columns c ON ic.object_id=c.object_id AND ic.column_id=c.column_id
WHERE i.object_id=OBJECT_ID('dbo.Lotus_loco_process_signals')
ORDER BY i.name, ic.key_ordinal
""")
print("--- Lotus_loco_process_signals indexes ---")
for r in cur.fetchall():
    print(r)
conn.close()
