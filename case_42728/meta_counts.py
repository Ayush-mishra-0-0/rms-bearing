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

# fast metadata: row counts + last write from sys.dm_db_partition_stats
cur.execute("""
SELECT t.name,
       SUM(p.rows) AS [rowcount]
FROM sys.tables t
JOIN sys.partitions p ON p.object_id=t.object_id AND p.index_id IN (0,1)
WHERE t.name IN ('Lotus_loco_process_signals','Lotus_loco_process_signals_4L',
 'Lotus_loco_process_signals_5','Lotus_loco_process_signals_sma',
 'Lotus_loco_process_signals_snap','Lotus_loco_process_signals_RDSOJson',
 'Lotus_LocoFaultData','Lotus_LocoFaultData_4L','Lotus_LocoFaultData_RDSOJson',
 'loco_process_signals','Loco_Process_Signals_LocoNumber','Locofault','RMSAlerts')
GROUP BY t.name ORDER BY t.name
""")
for r in cur.fetchall():
    print(f"{r[0]:40s} rows={r[1]:>12}")

# when was the DB last modified/backed up?
cur.execute("SELECT name, create_date, state_desc FROM sys.databases WHERE name='SLAM_RDS_DB_26.04.2024'")
print("\ndb:", cur.fetchone())
conn.close()
