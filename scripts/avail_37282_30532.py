"""Targeted availability for cross-case continuation (37282 Dec-2024, 30532 Apr-2024).
Loads monitoring/.env (DB route verified on this box), checks row counts in
dbo.Lotus_loco_process_signals for the 7d manifest windows + needed columns.
Run: rms\\Scripts\\python.exe scripts\\avail_37282_30532.py
"""
import os
from dotenv import load_dotenv

load_dotenv('C:/Users/CRIS/Desktop/ayush/rms-bearing/monitoring/.env')

WINDOWS = [
    ("37282", "2024-12-03 00:00:00", "2024-12-10 00:00:00"),
    ("30532", "2024-03-28 00:00:00", "2024-04-04 00:00:00"),
]

NEED = ["devicetime", "xspeedloco", "xiprim_1", "ltedemand",
        "xtempmotor1_1", "xtempmotor2_1", "xtempmotor3_1",
        "xtempmotor1_2", "xtempmotor2_2", "xtempmotor3_2"]


def main():
    import pyodbc
    cs = ("DRIVER={ODBC Driver 17 for SQL Server};"
          f"SERVER={os.getenv('DB_SERVER')};DATABASE={os.getenv('DB_NAME')};"
          f"UID={os.getenv('DB_USERNAME')};PWD={os.getenv('DB_PASSWORD')};"
          "TrustServerCertificate=yes;")
    c = pyodbc.connect(cs, timeout=30)
    c.timeout = 120
    cur = c.cursor()
    cur.execute("SELECT TOP 0 * FROM dbo.Lotus_loco_process_signals WITH (NOLOCK)")
    cols = {d[0].lower(): d[0] for d in cur.description}
    missing = [n for n in NEED if n.lower() not in cols]
    print("needed columns present:", len(NEED) - len(missing), "/", len(NEED))
    if missing:
        print("MISSING columns:", missing)
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
