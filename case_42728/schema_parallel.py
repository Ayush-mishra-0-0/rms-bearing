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
    timeout=45,
)
cur = conn.cursor()

for t in ["Lotus_loco_process_signals_4L", "Lotus_loco_process_signals_5", "Lotus_loco_process_signals_sma",
          "Lotus_loco_process_signals_snap", "Lotus_loco_process_signals_RDSOJson",
          "Lotus_LocoFaultData_4L", "Lotus_LocoFaultData_RDSOJson",
          "loco_process_signals", "Loco_Process_Signals_LocoNumber"]:
    try:
        cur.execute(f"SELECT TOP 0 * FROM dbo.[{t}]")
        cols = [d[0] for d in cur.description]
        lc = [x for x in cols if 'loco' in x.lower()]
        tc = [x for x in cols if 'time' in x.lower() or 'date' in x.lower()]
        print(f"=== {t}")
        print(f"   ncols={len(cols)} loco={lc} timeish={tc}")
    except Exception as e:
        print(f"{t}: err {str(e)[:70]}")
conn.close()
