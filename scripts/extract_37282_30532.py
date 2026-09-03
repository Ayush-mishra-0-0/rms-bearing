"""Extract cross-case telemetry for 37282 (Dec-2024) + 30532 (Apr-2024).
Loads monitoring/.env. Windows cover residual baselines through failure:
  37282: 2024-12-01 -> 2024-12-10 05:00 (axle-6 lock, EP withdrawal 05:00)
  30532: 2024-03-25 -> 2024-04-04 05:00 (DE bearing seize, failed ~05:00)
Table: dbo.Lotus_loco_process_signals (2024 LotusWireless 169-col feed).
Run: rms\\Scripts\\python.exe scripts\\extract_37282_30532.py
"""
import csv
import os
from dotenv import load_dotenv

load_dotenv('C:/Users/CRIS/Desktop/ayush/rms-bearing/monitoring/.env')

JOBS = [
    ("37282", "2024-12-01 00:00:00", "2024-12-10 05:00:00",
     "C:/Users/CRIS/Desktop/ayush/rms-bearing/data/interim/37282_10d.csv"),
    ("30532", "2024-03-25 00:00:00", "2024-04-04 05:00:00",
     "C:/Users/CRIS/Desktop/ayush/rms-bearing/data/interim/30532_11d.csv"),
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
