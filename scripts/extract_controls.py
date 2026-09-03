"""Extract healthy-control windows (frozen schema: SELECT * same table).
  37282-Nov : 2024-11-01 -> 2024-11-10 05:00 (same-loco control)
  30385-Dec : 2024-12-01 -> 2024-12-10 05:00 (healthy A, regime-matched)
  30380-Dec : 2024-12-01 -> 2024-12-10 05:00 (healthy B, regime-matched)
Run: rms\\Scripts\\python.exe scripts\\extract_controls.py
"""
import csv
import os
from dotenv import load_dotenv

load_dotenv('C:/Users/CRIS/Desktop/ayush/rms-bearing/monitoring/.env')

JOBS = [
    ("37282", "2024-11-01 00:00:00", "2024-11-10 05:00:00",
     "C:/Users/CRIS/Desktop/ayush/rms-bearing/data/interim/37282_Nov10d.csv"),
    ("30385", "2024-12-01 00:00:00", "2024-12-10 05:00:00",
     "C:/Users/CRIS/Desktop/ayush/rms-bearing/data/interim/healthyA_30385_10d.csv"),
    ("30380", "2024-12-01 00:00:00", "2024-12-10 05:00:00",
     "C:/Users/CRIS/Desktop/ayush/rms-bearing/data/interim/healthyB_30380_10d.csv"),
]


def main():
    import pyodbc
    cs = ("DRIVER={ODBC Driver 17 for SQL Server};"
          f"SERVER={os.getenv('DB_SERVER')};DATABASE={os.getenv('DB_NAME')};"
          f"UID={os.getenv('DB_USERNAME')};PWD={os.getenv('DB_PASSWORD')};"
          "TrustServerCertificate=yes;")
    c = pyodbc.connect(cs, timeout=120)
    c.timeout = 600
    cur = c.cursor()
    for loco, s, e, out in JOBS:
        os.makedirs(os.path.dirname(out), exist_ok=True)
        cur.execute("SELECT * FROM dbo.Lotus_loco_process_signals WITH (NOLOCK) "
                    "WHERE locoid=? AND devicetime>=? AND devicetime<? ORDER BY devicetime",
                    loco, s, e)
        cols = [d[0] for d in cur.description]
        n = 0
        with open(out, "w", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh)
            w.writerow(cols)
            while True:
                batch = cur.fetchmany(20000)
                if not batch:
                    break
                w.writerows(batch)
                n += len(batch)
                print(f"{loco}: ...{n}", flush=True)
        print(f"{loco}: DONE rows={n} -> {out}", flush=True)
    c.close()


if __name__ == "__main__":
    main()
