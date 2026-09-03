"""Find healthy-control candidates via indexed per-loco counts (no full scans).
Pool: Loco_Process_Signals_LocoNumber master list. Excludes registry failures.
Reports per-loco Dec 01-10 rows + 37282 Nov coverage.
Run: rms\\Scripts\\python.exe scripts\\find_healthy_controls2.py
"""
import csv
import os
from dotenv import load_dotenv

load_dotenv('C:/Users/CRIS/Desktop/ayush/rms-bearing/monitoring/.env')

REG = 'C:/Users/CRIS/Desktop/ayush/rms-bearing/data/processed/ground_truth_failure_registry.csv'


def failed_locos():
    out = set()
    with open(REG, newline='', encoding='utf-8-sig') as fh:
        for r in csv.DictReader(fh):
            for k in ('Loco', 'Locoid', 'locoid', 'LOCO'):
                if r.get(k):
                    out.add(str(r[k]).strip())
    out.add('42728')
    return out


def main():
    import pyodbc
    bad = failed_locos()
    cs = ("DRIVER={ODBC Driver 17 for SQL Server};"
          f"SERVER={os.getenv('DB_SERVER')};DATABASE={os.getenv('DB_NAME')};"
          f"UID={os.getenv('DB_USERNAME')};PWD={os.getenv('DB_PASSWORD')};"
          "TrustServerCertificate=yes;")
    c = pyodbc.connect(cs, timeout=30)
    c.timeout = 120
    cur = c.cursor()
    cur.execute("SELECT TOP 60 LocoNumber FROM dbo.Loco_Process_Signals_LocoNumber WITH (NOLOCK)")
    pool = [str(r[0]) for r in cur.fetchall()]
    print(f'pool: {len(pool)}')
    scored = []
    for loco in pool:
        if loco in bad:
            continue
        try:
            cur.execute("SELECT COUNT_BIG(*) FROM dbo.Lotus_loco_process_signals WITH (NOLOCK) "
                        "WHERE locoid=? AND devicetime>=? AND devicetime<?",
                        loco, "2024-12-01 00:00:00", "2024-12-10 05:00:00")
            n = cur.fetchone()[0]
        except Exception as ex:
            print(f'  {loco}: probe failed {type(ex).__name__}')
            continue
        scored.append((loco, n))
    scored.sort(key=lambda x: -x[1])
    print('top 10 by Dec rows:')
    for loco, n in scored[:10]:
        print(f'  {loco}: {n}')
    for loco, s, e in (('37282', '2024-11-01 00:00:00', '2024-11-10 05:00:00'),):
        cur.execute("SELECT COUNT_BIG(*), MIN(devicetime), MAX(devicetime) "
                    "FROM dbo.Lotus_loco_process_signals WITH (NOLOCK) "
                    "WHERE locoid=? AND devicetime>=? AND devicetime<?",
                    loco, s, e)
        n, mn, mx = cur.fetchone()
        print(f'{loco} Nov [{s} .. {e}]: rows={n} min={mn} max={mx}')
    c.close()


if __name__ == '__main__':
    main()
