"""Median sampling cadence: 30532 vs 37282 (explains 0-match)."""
import csv
from datetime import datetime


def med(v):
    v = sorted(v)
    return v[len(v) // 2] if v else float('nan')


for name in ('30532_11d', '37282_10d'):
    p = f'C:/Users/CRIS/Desktop/ayush/rms-bearing/data/interim/{name}.csv'
    ts = []
    with open(p, newline='', encoding='utf-8') as fh:
        for r in csv.DictReader(fh):
            try:
                ts.append(datetime.strptime(str(r['devicetime'])[:19], '%Y-%m-%d %H:%M:%S'))
            except Exception:
                pass
    ts.sort()
    gaps = [(b - a).total_seconds() for a, b in zip(ts, ts[1:]) if 0 < (b - a).total_seconds() < 3600]
    print(f'{name}: n={len(ts)} med_gap={med(gaps):.1f}s p90_gap={sorted(gaps)[int(len(gaps)*0.9)]:.1f}s')
