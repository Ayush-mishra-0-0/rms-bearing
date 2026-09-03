"""Failure-day coverage probe for 37282 (10-Dec-2024 00:00-05:00) and 30532 (04-Apr-2024 00:00-05:00).
Run: rms\\Scripts\\python.exe scripts\\avail_failure_day.py
"""
import os
from dotenv import load_dotenv

load_dotenv('C:/Users/CRIS/Desktop/ayush/rms-bearing/monitoring/.env')

WINDOWS = [
    ("37282", "2024-12-10 00:00:00", "2024-12-10 05:00:00"),
    ("37282", "2024-12-09 00:00:00", "2024-12-10 00:00:00"),
    ("30532", "2024-04-04 00:00:00", "2024-04-04 05:00:00"),
    ("30532", "2024-04-01 00:00:00", "2024-04-04 00:00:00"),
]


def main():
    import pyodbc
    cs = ("DRIVER={ODBC Driver 17 for SQL Server};"
          f"SERVER={os.getenv('DB_SERVER')};DATABASE={os.getenv('DB_NAME')};"
          f"UID={os.getenv('DB_USERNAME')};PWD={os.getenv('DB_PASSWORD')};"
          "TrustServerCertificate=yes;")
    c = pyodbc.connect(cs, timeout=30)
    c.timeout = 120
    cur = c.cursor()
    for loco, s, e in WINDOWS:
        cur.execute("SELECT COUNT_BIG(*), MIN(devicetime), MAX(devicetime) "
                    "FROM dbo.Lotus_loco_process_signals WITH (NOLOCK) "
                    "WHERE locoid=? AND devicetime>=? AND devicetime<?",
                    loco, s, e)
        n, mn, mx = cur.fetchone()
        print(f"{loco} [{s} .. {e}]: rows={n} min={mn} max={mx}")
    c.close()


if __name__ == "__main__":
    main()
