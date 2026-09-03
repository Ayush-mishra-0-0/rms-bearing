"""Find healthy-control candidates: dense Dec-2024 telemetry, excluding known failures.
Loads monitoring/.env. Excludes locos in ground_truth_failure_registry.csv
plus 42728 (2026 case). Reports top locos by row count 01-10 Dec 2024 and
37282's own Nov-2024 coverage for the same-loco control.
Run: rms\\Scripts\\python.exe scripts\\find_healthy_controls.py
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
    print(f'excluded failure locos: {len(bad)}')
    cs = ("DRIVER={ODBC Driver 17 for SQL Server};"
          f"SERVER={os.getenv('DB_SERVER')};DATABASE={os.getenv('DB_NAME')};"
          f"UID={os.getenv('DB_USERNAME')};PWD={os.getenv('DB_PASSWORD')};"
          "TrustServerCertificate=yes;")
    c = pyodbc.connect(cs, timeout=30)
    c.timeout = 300
    cur = c.cursor()
    cur.execute("SELECT locoid, COUNT_BIG(*) FROM dbo.Lotus_loco_process_signals WITH (NOLOCK) "
                "WHERE devicetime>=? AND devicetime<? GROUP BY locoid ORDER BY COUNT_BIG(*) DESC",
                "2024-12-01 00:00:00", "2024-12-10 05:00:00")
    rows = cur.fetchall()
    print(f'distinct locos 01-10 Dec: {len(rows)}')
    shown = 0
    picks = []
    for loco, n in rows:
        loco = str(loco)
        tag = 'EXCLUDE-failed' if loco in bad else 'candidate'
        if tag == 'candidate' and len(picks) < 5:
            picks.append((loco, n))
        if shown < 15:
            print(f'  {loco}: {n} {tag}')
            shown += 1
    print('top candidates:', picks)
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
